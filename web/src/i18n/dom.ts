// Translates the rendered page in place: text nodes and a few attributes, as React renders and updates them.
//
// Only the values of existing text nodes and attributes are changed, never the structure, so React keeps its own
// nodes. The original Swedish value of each node is remembered: when React writes a new value it is the new
// original, and switching back to Swedish restores the originals. Elements marked translate="no" (inscriptions,
// user content, chat answers already in English) are left alone.

import { type Catalog, type Lookup, translate as translateUncached } from "./core";

const ATTRS = ["title", "placeholder", "aria-label", "alt"];
const SKIP = new Set(["SCRIPT", "STYLE", "NOSCRIPT", "TEXTAREA", "CODE", "PRE", "INPUT"]);

const original = new WeakMap<Text, string>();
const written = new WeakMap<Text, string>();
const originalAttr = new WeakMap<Element, Record<string, string>>();
const writtenAttr = new WeakMap<Element, Record<string, string>>();

let catalog: Catalog | null = null;
// A text's translation depends only on the text and on the catalog, names and terms, which are fixed while the
// translator runs, so each distinct text is translated once: React re-renders and long tables repeat the same strings.
// Emptied by start() and stop(), and when it grows past MEMO_MAX texts. A hit returns the same missing list, which
// miss() records only once anyway.
const memo = new Map<string, Lookup>();
const MEMO_MAX = 50_000;
function translate(text: string, cat: Catalog): Lookup {
  let hit = memo.get(text);
  if (!hit) {
    hit = translateUncached(text, cat);
    if (memo.size >= MEMO_MAX) memo.clear();
    memo.set(text, hit);
  }
  return hit;
}
let observer: MutationObserver | null = null;
const touched = new Set<Text>();
const touchedAttr = new Set<Element>();

// Sentences not in the catalog, for the crawler that collects them (scripts/i18n_crawl.mjs)
type Misses = { misses: Record<string, string>; pages: Record<string, string> };
declare global { interface Window { __vitkiI18n?: Misses } }
function miss(templates: string[], example: string) {
  const store = (window.__vitkiI18n ??= { misses: {}, pages: {} });
  for (const t of templates) {
    if (!(t in store.misses)) { store.misses[t] = example.slice(0, 300); store.pages[t] = location.pathname; }
  }
}

function skipped(el: Element | null): boolean {
  for (let e = el; e; e = e.parentElement) {
    if (SKIP.has(e.tagName) || e.getAttribute("translate") === "no" || e.classList.contains("notranslate")
        || (e as HTMLElement).isContentEditable) return true;
  }
  return false;
}

function originalOf(node: Text): string {
  const v = node.nodeValue ?? "";
  if (written.get(node) === v && original.has(node)) return original.get(node)!;
  original.set(node, v);
  return v;
}

function write(node: Text, value: string) {
  touched.add(node);
  written.set(node, value);
  if (node.nodeValue !== value) node.nodeValue = value;
}

/** React renders "{n} av {m} stenar" as several adjacent text nodes; they are translated together. */
function translateElement(el: Element) {
  if (!catalog || skipped(el)) return;
  const kids = Array.from(el.childNodes);
  const texts = kids.filter((n): n is Text => n.nodeType === Node.TEXT_NODE);
  if (texts.length > 1 && texts.length === kids.length) {
    const originals = texts.map(originalOf);
    const joined = originals.join("");
    if (!joined.trim()) return;
    const res = translate(joined, catalog);
    if (res.missing.length) miss(res.missing, joined);
    if (res.text === joined) { texts.forEach((t, i) => write(t, originals[i])); return; }
    texts.forEach((t, i) => write(t, i === 0 ? res.text : ""));
    return;
  }
  for (const t of texts) translateText(t);
}

function translateText(node: Text) {
  if (!catalog) return;
  const orig = originalOf(node);
  if (!orig.trim()) return;
  const res = translate(orig, catalog);
  if (res.missing.length) miss(res.missing, orig);
  write(node, res.text);
}

function translateAttrs(el: Element) {
  // data-i18n-keep-attrs: the attributes hold source text (e.g. Kulturmiljöregistret's description in a tooltip)
  if (!catalog || skipped(el) || el.hasAttribute("data-i18n-keep-attrs")) return;
  for (const a of ATTRS) {
    const v = el.getAttribute(a);
    if (!v || !v.trim()) continue;
    const mine = writtenAttr.get(el) ?? {};
    const orig = originalAttr.get(el) ?? {};
    if (mine[a] !== v) orig[a] = v;  // a new value from React
    const res = translate(orig[a], catalog);
    if (res.missing.length) miss(res.missing, orig[a]);
    mine[a] = res.text;
    originalAttr.set(el, orig); writtenAttr.set(el, mine); touchedAttr.add(el);
    if (v !== res.text) el.setAttribute(a, res.text);
  }
}

function walk(root: Node) {
  if (root.nodeType === Node.TEXT_NODE) { if (root.parentElement) translateElement(root.parentElement); return; }
  if (root.nodeType !== Node.ELEMENT_NODE) return;
  const el = root as Element;
  if (skipped(el)) return;
  const tw = document.createTreeWalker(el, NodeFilter.SHOW_ELEMENT, {
    acceptNode: n => (SKIP.has((n as Element).tagName) || (n as Element).getAttribute("translate") === "no"
      ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT),
  });
  for (let n: Node | null = el; n; n = tw.nextNode()) {
    translateElement(n as Element);
    translateAttrs(n as Element);
  }
}

function onMutations(list: MutationRecord[]) {
  const elements = new Set<Element>();
  for (const m of list) {
    if (m.type === "characterData") {
      const t = m.target as Text;
      if (written.get(t) === t.nodeValue) continue;  // our own write
      if (t.parentElement) elements.add(t.parentElement);
    } else if (m.type === "attributes") {
      const el = m.target as Element;
      if ((writtenAttr.get(el) ?? {})[m.attributeName!] === el.getAttribute(m.attributeName!)) continue;
      translateAttrs(el);
    } else {
      m.addedNodes.forEach(n => (n.nodeType === Node.TEXT_NODE ? n.parentElement && elements.add(n.parentElement)
                                                               : walk(n)));
      if (m.target.nodeType === Node.ELEMENT_NODE && m.removedNodes.length) elements.add(m.target as Element);
    }
  }
  elements.forEach(translateElement);
}

/** Translates the page now and everything React renders from here on. */
export function start(cat: Catalog) {
  memo.clear();
  catalog = cat;
  walk(document.body);
  if (document.title) document.title = translate(document.title, cat).text;
  observer?.disconnect();
  observer = new MutationObserver(onMutations);
  observer.observe(document.body, { subtree: true, childList: true, characterData: true, attributes: true,
                                     attributeFilter: ATTRS });
}

/** Back to Swedish: every value written by the translator gets its original back. */
export function stop() {
  observer?.disconnect();
  observer = null;
  catalog = null;
  memo.clear();
  touched.forEach(t => { if (t.isConnected && written.get(t) === t.nodeValue) t.nodeValue = original.get(t) ?? t.nodeValue; });
  touchedAttr.forEach(el => {
    const mine = writtenAttr.get(el) ?? {}, orig = originalAttr.get(el) ?? {};
    for (const a of Object.keys(mine)) if (el.getAttribute(a) === mine[a] && orig[a] !== undefined) el.setAttribute(a, orig[a]);
  });
  touched.clear(); touchedAttr.clear();
}
