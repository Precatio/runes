// Static checks of the interface's own texts, without a running app (scripts/i18n_crawl.mjs needs the dev servers and
// Chrome, so it cannot run in CI):
//
//  1. Swedish texts without an English template in src/i18n/en.json. The source files (web/src, .tsx) are read with the
//     TypeScript compiler, and the texts that the page translator (src/i18n/dom.ts) sees exactly as written are looked
//     up the way it does (src/i18n/core.ts translate): an element whose children are all plain text, a lone string
//     child ({"…"} or {a ? "…" : "…"}), and the attributes title, placeholder, aria-label and alt. Elements with
//     translate="no" are skipped. Text mixed with {expressions} is left to the crawler, since its runtime value is
//     unknown here. Texts already missing are listed in scripts/ui_texts_baseline.json, so that only new ones fail.
//  2. Gendered pronouns about carvers (han/hans/honom by ristare, he/his/him by carver) in the interface's texts – every
//     string and text in web/src – and in en.json, with the same rule as the article review (src/lib/articleLint.ts).
//
//   node --experimental-strip-types scripts/ui_texts.mjs              list both
//   node --experimental-strip-types scripts/ui_texts.mjs --baseline   write the missing translations as the new baseline
//
// The tests are in scripts/ui_texts.test.mjs (run in CI, .github/workflows/ci.yml).
import { readFileSync, readdirSync, statSync, writeFileSync } from "node:fs";
import { dirname, join, relative } from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";

const WEB = join(dirname(fileURLToPath(import.meta.url)), "..");
const SRC = join(WEB, "src");
export const BASELINE = join(WEB, "scripts", "ui_texts_baseline.json");

// Not translated: the catalog and translator themselves, the English editions (already English) and the editorial
// tool /redaktion, which only the founder uses, in Swedish
const SKIP = [join(SRC, "i18n"), join(SRC, "app", "en"), join(SRC, "app", "redaktion"),
  join(SRC, "components", "Redaktion.tsx"), join(SRC, "components", "RedaktionWeek.tsx"), join(SRC, "lib", "translations.ts")];
const ATTRS = new Set(["title", "placeholder", "aria-label", "alt"]);

export function sourceFiles(dir = SRC, ext = [".tsx"]) {
  const out = [];
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (SKIP.some(s => p === s || p.startsWith(s + "/"))) continue;
    if (statSync(p).isDirectory()) out.push(...sourceFiles(p, ext));
    else if (ext.some(e => p.endsWith(e))) out.push(p);
  }
  return out.sort();
}

const ENTITIES = { nbsp: "\u00a0", bull: "•", amp: "&", lt: "<", gt: ">", quot: "\"", apos: "'", ndash: "–", mdash: "—", hellip: "…", rarr: "→", larr: "←", middot: "·", times: "×" };
const decode = s => s.replace(/&(#\d+|#x[0-9a-f]+|[a-z]+);/gi, (m, e) => e[0] === "#"
  ? String.fromCodePoint(e[1] === "x" || e[1] === "X" ? parseInt(e.slice(2), 16) : Number(e.slice(1))) : ENTITIES[e] ?? m);

// The JSX text as React renders it: entities decoded, lines trimmed and joined with a space, empty lines dropped
function jsxText(raw) {
  raw = decode(raw);
  const lines = raw.split(/\r?\n/);
  if (lines.length === 1) return raw;
  return lines.map((l, i) => (i === 0 ? l.trimEnd() : i === lines.length - 1 ? l.trimStart() : l.trim()))
    .filter(Boolean).join(" ");
}

const stringsOf = expr => {
  if (!expr) return null;
  if (ts.isStringLiteral(expr) || ts.isNoSubstitutionTemplateLiteral(expr)) return [expr.text];
  if (ts.isParenthesizedExpression(expr)) return stringsOf(expr.expression);
  if (ts.isConditionalExpression(expr)) {
    const a = stringsOf(expr.whenTrue), b = stringsOf(expr.whenFalse);
    return a && b ? [...a, ...b] : null;
  }
  if (ts.isBinaryExpression(expr) && expr.operatorToken.kind === ts.SyntaxKind.AmpersandAmpersandToken) return stringsOf(expr.right);
  return null;
};

const noTranslate = el => {
  const attrs = (ts.isJsxElement(el) ? el.openingElement : el).attributes?.properties ?? [];
  return attrs.some(a => ts.isJsxAttribute(a) && a.name.getText() === "translate" && a.initializer
    && ts.isStringLiteral(a.initializer) && a.initializer.text === "no");
};

/** The texts the translator sees exactly as written, with their file and line. */
export function uiTexts(files = sourceFiles()) {
  const out = [];
  for (const file of files) {
    const sf = ts.createSourceFile(file, readFileSync(file, "utf8"), ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
    const add = (text, node) => {
      if (text && /\p{L}/u.test(text)) out.push({ text, file: relative(WEB, file), line: sf.getLineAndCharacterOfPosition(node.getStart()).line + 1 });
    };
    const visit = node => {
      if ((ts.isJsxElement(node) || ts.isJsxSelfClosingElement(node)) && noTranslate(node)) return;
      if (ts.isJsxElement(node)) {
        const kids = node.children.filter(c => !(ts.isJsxText(c) && c.containsOnlyTriviaWhiteSpaces));
        if (kids.length && kids.every(c => ts.isJsxText(c))) add(jsxText(kids.map(c => c.text).join("")).trim(), node);
        else if (kids.length === 1 && ts.isJsxExpression(kids[0])) for (const s of stringsOf(kids[0].expression) ?? []) add(s.trim(), kids[0]);
      }
      if (ts.isJsxAttribute(node) && ATTRS.has(node.name.getText()) && node.initializer) {
        const init = node.initializer;
        const vals = ts.isStringLiteral(init) ? [init.text] : ts.isJsxExpression(init) ? stringsOf(init.expression) ?? [] : [];
        for (const v of vals) add(v.trim(), node);
      }
      ts.forEachChild(node, visit);
    };
    visit(sf);
  }
  return out;
}

// A text that reads as Swedish (an English or neutral one needs no template)
const SWEDISH_WORDS = new Set(("och att det som för med inte är av på till den ett en har kan om vi du eller från när så alla " +
  "inga visa dölj stäng spara sök hämtar laddar välj sten stenar runor runa ristare artikel artiklar sida bild karta " +
  "eller också bara mer fler mindre än hur var vad vilka här där nu ny nytt nya tid år ingen inget ladda logga").split(" "));
export function looksSwedish(text) {
  if (/[åäöÅÄÖ]/.test(text)) return true;
  return text.toLowerCase().split(/[^\p{L}]+/u).some(w => SWEDISH_WORDS.has(w));
}

/** Swedish texts without an English template: {template: "file:line"}. */
export async function missingTranslations(texts = uiTexts(), catalogPath = join(SRC, "i18n", "en.json")) {
  const core = await import(join(SRC, "i18n", "core.ts"));
  core.setNames(JSON.parse(readFileSync(join(SRC, "i18n", "names.json"), "utf8")));
  core.setTerms(JSON.parse(readFileSync(join(SRC, "i18n", "terms.json"), "utf8")));
  const catalog = JSON.parse(readFileSync(catalogPath, "utf8"));
  const out = {};
  for (const { text, file, line } of texts) {
    if (!looksSwedish(text)) continue;
    const res = core.translate(text, catalog);
    for (const t of res.missing) if (!(t in out) && looksSwedish(t)) out[t] = `${file}:${line}`;
  }
  return out;
}

/** Gendered pronouns about carvers in every string of web/src and in en.json: [{where, text, finding}]. */
export async function carverPronouns() {
  const { checkPronouns } = await import(join(SRC, "lib", "articleLint.ts"));
  const hits = [];
  const check = (text, where) => {
    for (const sprak of ["sv", "en"]) {
      for (const f of checkPronouns(text, sprak)) if (f.niva === "FEL") hits.push({ where, text: text.slice(0, 200), finding: f.text });
    }
  };
  for (const file of sourceFiles(SRC, [".tsx", ".ts"])) {
    if (file.endsWith("articleLint.ts")) continue;  // its own rule texts
    const sf = ts.createSourceFile(file, readFileSync(file, "utf8"), ts.ScriptTarget.Latest, true,
      file.endsWith(".tsx") ? ts.ScriptKind.TSX : ts.ScriptKind.TS);
    const visit = node => {
      if (ts.isStringLiteral(node) || ts.isNoSubstitutionTemplateLiteral(node) || ts.isJsxText(node)
          || ts.isTemplateHead(node) || ts.isTemplateMiddle(node) || ts.isTemplateTail(node)) {
        const text = ts.isJsxText(node) ? jsxText(node.text) : node.text;
        if (/ristar|carver/i.test(text)) check(text, `${relative(WEB, file)}:${sf.getLineAndCharacterOfPosition(node.getStart()).line + 1}`);
      }
      ts.forEachChild(node, visit);
    };
    visit(sf);
  }
  // en.json: an English template that gives a carver a gender the Swedish one does not have. A Swedish template with
  // han/hans/honom is either no longer used (the source was corrected; the old entry stays in the catalog until it is
  // cleaned) or caught in the source above.
  const catalog = JSON.parse(readFileSync(join(SRC, "i18n", "en.json"), "utf8"));
  for (const [sv, en] of Object.entries(catalog)) {
    if (!/carver/i.test(en) || /(?<!\p{L})(han|hans|honom)(?!\p{L})/u.test(sv)) continue;
    check(en, `en.json (engelsk mall för): ${sv.slice(0, 60)}`);
  }
  return hits;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const missing = await missingTranslations();
  if (process.argv.includes("--baseline")) {
    const sorted = Object.fromEntries(Object.entries(missing).sort(([a], [b]) => a.localeCompare(b, "sv")));
    writeFileSync(BASELINE, JSON.stringify(sorted, null, 1) + "\n");
    console.log(Object.keys(sorted).length, "saknade mallar skrivna till", relative(WEB, BASELINE));
  } else {
    const base = JSON.parse(readFileSync(BASELINE, "utf8"));
    const fresh = Object.entries(missing).filter(([t]) => !(t in base));
    console.log(`${Object.keys(missing).length} svenska texter utan engelsk mall, varav ${fresh.length} nya:`);
    for (const [t, w] of fresh) console.log(`  ${w}  ${t}`);
    const pron = await carverPronouns();
    console.log(`${pron.length} könade pronomen om ristare:`);
    for (const h of pron) console.log(`  ${h.where}  ${h.text}`);
  }
}
