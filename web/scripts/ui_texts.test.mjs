// The interface's own texts, checked without a running app (scripts/ui_texts.mjs): every Swedish text the page
// translator sees as written has an English template in src/i18n/en.json (texts missing before are listed in
// scripts/ui_texts_baseline.json; only new ones fail), and no interface text gives a carver a gender.
//   node --test scripts/ui_texts.test.mjs
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { BASELINE, carverPronouns, looksSwedish, missingTranslations, uiTexts } from "./ui_texts.mjs";

test("svenska gränssnittstexter har en engelsk mall", async () => {
  const base = JSON.parse(readFileSync(BASELINE, "utf8"));
  const missing = await missingTranslations();
  const fresh = Object.entries(missing).filter(([t]) => !(t in base));
  const solved = Object.keys(base).filter(t => !(t in missing)).length;
  if (solved) console.log(`${solved} mallar i ui_texts_baseline.json finns nu i en.json; kör scripts/ui_texts.mjs --baseline för att korta listan.`);
  assert.equal(fresh.length, 0, "Svenska texter utan engelsk mall (lägg dem i src/i18n/en.json):\n"
    + fresh.map(([t, w]) => `  ${w}  ${t}`).join("\n"));
});

test("inga könade pronomen om ristare i gränssnittet eller i en.json", async () => {
  const hits = await carverPronouns();
  assert.equal(hits.length, 0, hits.map(h => `  ${h.where}: ${h.text} – ${h.finding}`).join("\n"));
});

test("hjälpfunktionerna: vad som räknas som svensk text och vad som läses", () => {
  assert.ok(looksSwedish("Spara ändringar") && looksSwedish("Visa alla") && !looksSwedish("Download CSV"));
  const texts = uiTexts([new URL("../src/components/ArticleReview.tsx", import.meta.url).pathname]).map(t => t.text);
  assert.ok(texts.includes("Jag har läst felen och vill schemalägga ändå."));
  assert.ok(!texts.some(t => t.includes("{")));  // text mixed with expressions is left to the crawler
});
