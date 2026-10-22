// The English catalog for the public website: only the entries that the website's pages can show.
//
// The full catalog (en.json, with names.json and terms.json) covers the whole app, about 820 kB. The public website
// (NEXT_PUBLIC_SITE_MODE=public) has only the start page, the articles, the news and the contact page, so it loads
// en.public.json, names.public.json and terms.public.json instead (components/LanguageContext.tsx). They are written by
// this script from the full files and the website's own text: the source files reachable from the public pages
// (src/app without the app's pages and the API) and the content they are built from (content/*.json,
// public/artiklar-sok.json). An entry is kept when every piece of it outside the placeholders {0}, {1}, … occurs in that
// text (ignoring case and runs of white space; a piece also when its parts between punctuation do), a name or term when
// it occurs in it. Text that cannot be on the website
// cannot be translated there, so the result is the same as with the full catalog; the subset is generous, never tight.
//
// Run from web/: node src/i18n/public-catalog.mjs (npm run i18n:public). The public build in .github/workflows/site.yml
// (and scripts/build_site.sh) runs it before `next build`, so the website always gets a subset of the current catalog.
//
// The three files are generated, but kept in git: the app imports them too (LanguageContext names both catalogs, and the
// bundler resolves both), so a fresh clone needs them for `next build`, `next dev` and `tsc`. When they are missing,
// `npm run dev`, `npm run build` and `npm run local` write them first (--if-missing: nothing is done when all three exist).

import { readFileSync, writeFileSync, readdirSync, statSync, existsSync } from "node:fs";
import { dirname, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const WEB = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const SRC = join(WEB, "src");
const I18N = join(SRC, "i18n");
// The app's own pages and the API are not on the public website (site.yml deletes them before the build)
const NOT_PUBLIC = [join(SRC, "app", "(app)"), join(SRC, "app", "api")];
const EXTENSIONS = [".tsx", ".ts", ".mjs", ".js", ".json"];
const OUTPUTS = ["en.public.json", "names.public.json", "terms.public.json"];
if (process.argv.includes("--if-missing") && OUTPUTS.every(name => existsSync(join(I18N, name)))) process.exit(0);

function filesIn(dir) {
  const out = [];
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (NOT_PUBLIC.includes(p)) continue;
    if (statSync(p).isDirectory()) out.push(...filesIn(p));
    else if (EXTENSIONS.some(e => p.endsWith(e))) out.push(p);
  }
  return out;
}

function resolveImport(spec, from) {
  let base;
  if (spec.startsWith("@/")) base = join(SRC, spec.slice(2));
  else if (spec.startsWith(".")) base = resolve(dirname(from), spec);
  else return null;  // a package
  for (const cand of [base, ...EXTENSIONS.map(e => base + e), ...EXTENSIONS.map(e => join(base, "index" + e))]) {
    if (existsSync(cand) && statSync(cand).isFile()) return cand;
  }
  return null;
}

const IMPORT = /(?:\bfrom\s*|\bimport\s*\(\s*|\bimport\s+|\brequire\s*\(\s*)["']([^"']+)["']/g;

// The source files reachable from the public pages, and the JSON files they import
const seen = new Set();
const queue = filesIn(join(SRC, "app"));
while (queue.length) {
  const file = queue.pop();
  if (seen.has(file)) continue;
  // The catalog itself is not the website's text
  if (dirname(file) === I18N && file.endsWith(".json")) continue;
  seen.add(file);
  if (file.endsWith(".json")) continue;
  const code = readFileSync(file, "utf8");
  for (const m of code.matchAll(IMPORT)) {
    const target = resolveImport(m[1], file);
    if (target && !seen.has(target)) queue.push(target);
  }
}

// What the pages are built from, and the search index the article search fetches
const content = join(WEB, "content");
const data = [
  ...(existsSync(content) ? readdirSync(content).filter(n => n.endsWith(".json")).map(n => join(content, n)) : []),
  join(WEB, "public", "artiklar-sok.json"),
].filter(existsSync);

const strings = [];
function collect(value) {
  if (typeof value === "string") strings.push(value);
  else if (Array.isArray(value)) value.forEach(collect);
  else if (value && typeof value === "object") Object.values(value).forEach(collect);
}
for (const file of [...seen, ...data]) {
  const text = readFileSync(file, "utf8");
  if (file.endsWith(".json")) { collect(JSON.parse(text)); continue; }
  // JavaScript escapes as the browser renders them; JSX text is joined over its line breaks
  strings.push(text.replace(/\\u\{([0-9a-fA-F]+)\}|\\u([0-9a-fA-F]{4})/g, (_, a, b) => String.fromCodePoint(parseInt(a ?? b, 16)))
                   .replace(/\\(["'`])/g, "$1"));
}

const norm = s => s.replace(/[\s   ]+/g, " ").toLowerCase();
const corpus = norm(strings.join("\n"));
const has = s => { const n = norm(s).trim(); return !n || corpus.includes(n); };

const read = name => JSON.parse(readFileSync(join(I18N, name), "utf8"));
const catalog = read("en.json");
// A piece is also found when it is split at punctuation: the page may join two strings with a colon or a comma
// (`Sö 113: ${title.toLowerCase()}`), so that only the parts occur in the source
const piece = part => has(part) || norm(part).split(/[:;,.()"”“’«»–—!?]+/).every(p => !/\p{L}/u.test(p) || has(p));
const keep = Object.fromEntries(Object.entries(catalog).filter(([key]) =>
  key.split(/\{\d+\}/).every(part => !/\p{L}/u.test(part) || piece(part))));
const names = read("names.json").filter(has);
const terms = read("terms.json").filter(has);

const write = (name, value) => {
  const text = JSON.stringify(value) + "\n";
  writeFileSync(join(I18N, name), text);
  return text.length;
};
const sizes = [write("en.public.json", keep), write("names.public.json", names), write("terms.public.json", terms)];
console.log(`public catalog: ${Object.keys(keep).length} of ${Object.keys(catalog).length} entries, ${names.length} names, `
  + `${terms.length} terms (${sizes.map(s => `${Math.round(s / 1024)} kB`).join(" + ")}) from ${seen.size} source files`
  + ` and ${data.map(f => relative(WEB, f)).join(", ")}`);
