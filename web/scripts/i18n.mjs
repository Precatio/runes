// The English catalog (src/i18n/en.json): Swedish sentence templates → English, as src/i18n/core.ts looks them up.
//
//   node --experimental-strip-types scripts/i18n.mjs seed              pairs from src/lib/translations.ts
//   node --experimental-strip-types scripts/i18n.mjs merge FILE.json   add translated templates {sv: en}
//   node --experimental-strip-types scripts/i18n.mjs missing FILE.json templates in a crawl not yet in the catalog
//   node --experimental-strip-types scripts/i18n.mjs check             placeholders agree between sv and en
//
// The crawler (scripts/i18n_crawl.mjs) collects the templates the page could not translate.
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const CATALOG = join(here, "..", "src", "i18n", "en.json");
const core = await import(join(here, "..", "src", "i18n", "core.ts"));
core.setNames(JSON.parse(readFileSync(join(here, "..", "src", "i18n", "names.json"), "utf8")));
core.setTerms(JSON.parse(readFileSync(join(here, "..", "src", "i18n", "terms.json"), "utf8")));

const load = () => (existsSync(CATALOG) ? JSON.parse(readFileSync(CATALOG, "utf8")) : {});
const save = cat => {
  const sorted = Object.fromEntries(Object.entries(cat).sort(([a], [b]) => a.localeCompare(b, "sv")));
  writeFileSync(CATALOG, JSON.stringify(sorted, null, 0).replace(/","/g, '",\n"').replace(/^\{/, "{\n").replace(/\}$/, "\n}") + "\n");
  return Object.keys(sorted).length;
};
const placeholders = s => (s.match(/\{\d+\}/g) || []).sort().join(",");

const [cmd, file] = process.argv.slice(2);
if (cmd === "seed") {
  const { translations } = await import(join(here, "..", "src", "lib", "translations.ts"));
  const cat = load();
  const walk = (a, b) => {
    for (const k of Object.keys(a)) {
      if (typeof a[k] === "string") {
        if (b?.[k] && a[k] !== b[k]) {
          // Mask the Swedish and the English the same way, so that numbers and names line up
          const sv = core.mask(a[k]), en = core.mask(b[k]);
          if (sv.tokens.join("|") === en.tokens.join("|")) cat[sv.template] ??= en.template;
        }
      } else walk(a[k], b?.[k]);
    }
  };
  walk(translations.sv, translations.en);
  console.log(save(cat), "mallar");
} else if (cmd === "merge") {
  const add = JSON.parse(readFileSync(file, "utf8"));
  const cat = load();
  let bad = 0;
  for (const [sv, en] of Object.entries(add)) {
    if (typeof en !== "string") continue;
    if (placeholders(sv) !== placeholders(en)) { console.warn("platshållare skiljer:", sv, "→", en); bad++; continue; }
    cat[sv] = en;
  }
  console.log(save(cat), "mallar", bad ? `(${bad} avvisade)` : "");
} else if (cmd === "missing") {
  const crawl = JSON.parse(readFileSync(file, "utf8"));
  const cat = load();
  const out = Object.fromEntries(Object.entries(crawl.misses ?? crawl).filter(([t]) => cat[t] === undefined));
  process.stdout.write(JSON.stringify(out, null, 1) + "\n");
  console.error(Object.keys(out).length, "saknas");
} else if (cmd === "check") {
  const cat = load();
  const bad = Object.entries(cat).filter(([sv, en]) => placeholders(sv) !== placeholders(en));
  bad.forEach(([sv, en]) => console.log(sv, "→", en));
  console.log(Object.keys(cat).length, "mallar,", bad.length, "med fel platshållare");
} else {
  console.log("seed | merge FILE | missing FILE | check");
}
