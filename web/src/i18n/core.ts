// Translation of rendered Swedish text into English with a catalog of sentence templates.
//
// The app is written in Swedish, and much of its text is generated: findings, patterns and reports with numbers,
// signa, carver names and places in them. A sentence is therefore looked up as a template: numbers, carver names and
// place names are replaced by {0}, {1}, … before the lookup and put back afterwards (numbers in English form).
// Longer texts are split into sentences, so that a paragraph whose sentences vary independently still translates.
// Swedish is the original; a sentence that is not in the catalog stays Swedish and is recorded as missing.

export type Catalog = Record<string, string>;

// Words that need no translation: signum prefixes, units and statistical symbols
const PASSTHROUGH = new Set([
  "U", "Sö", "Ög", "Öl", "Vg", "Sm", "Gs", "Hs", "Vs", "Nä", "Hr", "Ån", "Bo", "Ds", "Lp", "DR", "N", "IS", "IM", "E",
  "GR", "Or", "D", "M", "J", "G", "km", "m", "cm", "mm", "p", "q", "n", "rho", "eta", "OR", "KI", "CI", "SD", "AUC",
  "RAK", "Fp", "Pr", "KB", "MB", "GB", "STL", "OBJ", "PLY", "PNG", "JPG", "PDF", "CSV", "JSON", "ZIP", "R", "API", "AI",
  "Vitki", "GitHub", "Rundata", "Wikidata", "Zenodo", "DOI", "LinkedIn", "Claude", "Gemini", "Anthropic", "Google",
  "OpenAI", "Plotly", "Leaflet", "OpenStreetMap", "x", "y", "z", "mgcv", "Holm", "Wilcoxon", "Gräslund", "Axelson",
  // Signum series (U Fv1972;272, U ATA365/61A, Sö SB1965;19)
  "ATA", "Fv", "SD", "SB", "NOR", "IR", "KJ", "BN", "Sc", "Br", "Vr", "NIyR", "DK", "MJy", "Ka", "Kg", "RR", "SHM",
  "Sb", "SvK", "MÖLM", "RS", "Plansch",
  ..."ABCDEFGHIJKLMNOPQRSTUVWXYZ",
]);

const NUMBER = /\d+(?:[   ]\d{3})*(?:,\d+)?/g;
// Latin letters: runic characters, symbols and numbers alone need no translation
const LETTER = /[A-Za-zÅÄÖåäöÆØæøÉéÜüÞþÐð]/;

let names: Set<string> = new Set();
let terms: Set<string> = new Set();
let maxWords = 1;

const longest = (list: string[]) => Math.max(1, ...list.map(n => n.split(/\s+/).length));

/** Carver and place names from Rundata, kept as they are. */
export function setNames(list: string[]) {
  names = new Set(list);
  maxWords = Math.max(longest(list), longest([...terms]));
}

/** Terms translated on their own inside a sentence (language traits and their values, rock types), so that one
 *  template serves every combination: "diftongen au i 'och' (auk: 28 % …)" → "{0} ({1}: {2} % …)". */
export function setTerms(list: string[]) {
  terms = new Set(list);
  maxWords = Math.max(longest([...names]), longest(list));
}

type Kind = "number" | "name" | "term";
type Masked = { template: string; tokens: string[]; kinds: Kind[] };

// A name or term is marked with a private-use character (no digits, so the number masking cannot touch it)
const mark = (i: number) => `\u0001${String.fromCharCode(0xe000 + i)}\u0001`;
const LEAD = /^[(«"„”'“]*/u;
const TRAIL = /[.,;:!?)”"'’]+$/u;
const TRAIL_KEEP_QUOTE = /[.,;:!?)”"’]+$/u;
const TRAIL_KEEP_PAREN = /[.,;:!?]+$/u;

/** Replaces names, numbers and (with withTerms) terms by {0}, {1}, … in order of appearance. */
export function mask(text: string, withTerms = false): Masked {
  const tokens: string[] = [];
  const kinds: Kind[] = [];
  let out = text;
  if (names.size || (withTerms && terms.size)) {
    // The longest name or term first at each word
    const words = out.split(/(\s+)/);
    const res: string[] = [];
    for (let i = 0; i < words.length; i++) {
      const lead = words[i].match(LEAD)![0];
      const capital = /^\p{Lu}/u.test(words[i].slice(lead.length));
      let hit = 0;
      for (let k = Math.min(maxWords, Math.ceil((words.length - i) / 2)); k >= 1 && !hit; k--) {
        const cand = words.slice(i, i + 2 * k - 1).join("").slice(lead.length);
        // As written ("stungen u (y)"), without trailing punctuation, keeping a closing quote ("i 'och'") or a
        // closing parenthesis ("stungen i (e):")
        const cores = [cand, cand.replace(TRAIL, ""), cand.replace(TRAIL_KEEP_QUOTE, ""), cand.replace(TRAIL_KEEP_PAREN, "")];
        for (const core of cores) {
          const kind: Kind | null = capital && names.has(core) ? "name" : withTerms && terms.has(core) ? "term" : null;
          if (core && kind) {
            res.push(lead + mark(tokens.length) + cand.slice(core.length));
            tokens.push(core); kinds.push(kind);
            hit = 2 * k - 1;
            break;
          }
        }
      }
      if (hit) { i += hit - 1; continue; }
      res.push(words[i]);
    }
    out = res.join("");
  }
  out = out.replace(NUMBER, m => { tokens.push(m); kinds.push("number"); return `\u0000${tokens.length - 1}\u0000`; });
  // Renumber in order of appearance, so that the same sentence always gives the same template
  const order: number[] = [];
  out = out.replace(/\u0000(\d+)\u0000|\u0001([-])\u0001/g, (_, num, name) => {
    order.push(num !== undefined ? Number(num) : name.charCodeAt(0) - 0xe000);
    return `{${order.length - 1}}`;
  });
  return { template: out, tokens: order.map(i => tokens[i]), kinds: order.map(i => kinds[i]) };
}

/** A Swedish number in English form: 0,43 → 0.43; 1 101 → 1,101. */
export function englishNumber(s: string): string {
  if (!/^\d/.test(s)) return s;
  const [int, dec] = s.split(",");
  const digits = int.replace(/[   ]/g, "");
  const grouped = /[   ]/.test(int) ? Number(digits).toLocaleString("en-US") : digits;
  return dec !== undefined ? `${grouped}.${dec}` : grouped;
}

function unmask(template: string, m: Masked, catalog: Catalog, missing: string[]): string {
  return template.replace(/\{(\d+)\}/g, (_, i) => {
    const t = m.tokens[Number(i)];
    if (t === undefined) return "";
    if (m.kinds[Number(i)] === "term") {
      const hit = catalog[t];
      if (hit === undefined) missing.push(t);
      return hit ?? t;
    }
    return englishNumber(t);
  });
}

// Words with a fixed translation, used only when a segment consists of nothing else (lists of stones, place strings):
// "U 618 (29 km), U 23 (30 km, signerad)", "Torp, Sorunda sn, Sotholms hd"
const WORDS: Record<string, string> = {
  signerad: "signed", signerade: "signed", attribuerad: "attributed", försvunnen: "lost", och: "and", med: "with",
  tillsammans: "together", sn: "parish", hd: "hundred", nu: "now", numera: "now", kyrka: "church", kyrkan: "the church",
  kyrkogård: "churchyard", Vid: "At", vid: "at", socken: "parish", härad: "hundred", ungefär: "about",
};

/** True when nothing in the template needs translating (only numbers, names, signum prefixes, symbols). */
function needsNothing(template: string): boolean {
  const words = template.replace(/\{\d+\}/g, " ").split(/[^\p{L}²]+/u).filter(Boolean);
  return words.every(w => PASSTHROUGH.has(w) || w in WORDS);
}

/** The template with the fixed words translated (see WORDS). */
function plainWords(template: string): string {
  return template.replace(/\p{L}+/gu, w => WORDS[w] ?? w);
}

// Sentence boundaries (followed by a capital letter, a digit or an opening mark) and semicolons
const SPLIT = /(?<=[.!?])(\s+)(?=[\p{Lu}\d"”(«])|(?<=:)(\s+)(?=\p{Lu})|(;\s+)|(\n+)/u;

export function segments(text: string): string[] {
  // Keeps the separators, so that the text can be put back together exactly
  return text.split(SPLIT).filter(s => s !== undefined);
}

export type Lookup = { text: string; complete: boolean; missing: string[] };

/** A template with or without its final full stop. */
function find(catalog: Catalog, template: string): string | undefined {
  if (catalog[template] !== undefined) return catalog[template];
  if (template.endsWith(".") && !template.endsWith("..")) {
    const hit = catalog[template.slice(0, -1)];
    if (hit !== undefined) return hit.endsWith(".") ? hit : hit + ".";
  } else {
    const hit = catalog[template + "."];
    if (hit !== undefined) return hit.endsWith(".") ? hit.slice(0, -1) : hit;
  }
  return undefined;
}

// "För: …", "Stenen: granit." – a short label before a colon is its own segment
const LABEL = /^(\p{L}[\p{L}-]*(?: \p{L}[\p{L}-]*){0,2}(?: \([^)]{1,12}\))?:)(\s+)(?=\S)/u;

/** One sentence as a template: first with names and numbers only (the catalog's older entries), then with terms. */
function lookup(text: string, catalog: Catalog, missing: string[]): string | undefined {
  for (const withTerms of [false, true]) {
    const m = mask(text, withTerms);
    const hit = find(catalog, m.template);
    if (hit !== undefined) return unmask(hit, m, catalog, missing);
    if (needsNothing(m.template)) return unmask(plainWords(m.template), m, catalog, missing);
  }
  return undefined;
}

/** Translates a text: the whole text as one template, or sentence by sentence. */
export function translate(text: string, catalog: Catalog): Lookup {
  const lead = text.match(/^\s*/)![0], trail = text.match(/\s*$/)![0];
  const body = text.slice(lead.length, text.length - trail.length);
  if (!body || !LETTER.test(body)) return { text: lead + englishNumbers(body) + trail, complete: true, missing: [] };
  const missing: string[] = [];
  const whole = lookup(body, catalog, missing);
  if (whole !== undefined) return { text: lead + whole + trail, complete: missing.length === 0, missing };
  // One sentence: as a whole, or as a short label ("För:", "Stenen:") and the rest
  const one = (part: string): string => {
    const core = part.trim();
    if (!LETTER.test(core)) return part.replace(core, englishNumbers(core));
    const hit = lookup(core, catalog, missing);
    if (hit !== undefined) return part.replace(core, hit);
    const label = core.match(LABEL);
    if (label) {
      const head = lookup(label[1], catalog, missing);
      if (head === undefined) missing.push(mask(label[1], true).template);
      const rest = one(core.slice(label[0].length));
      return part.replace(core, (head ?? label[1]) + label[2] + rest.trim());
    }
    missing.push(mask(core, true).template);
    return part;
  };
  const parts = segments(body);
  const out = parts.length === 1 ? one(body) : parts.map(part => (LETTER.test(part) ? one(part) : part)).join("");
  return { text: lead + out + trail, complete: missing.length === 0, missing };
}

function englishNumbers(s: string): string {
  return s.replace(NUMBER, englishNumber);
}
