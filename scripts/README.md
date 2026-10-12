# Manuella utvecklingsskript

Lösa skript för felsökning mot externa tjänster (Gemini, K-samsök) och benchmark.
De är inte automatiska tester – de riktiga testerna ligger i `tests/` och körs med `pytest`.

Kör från projektroten så att `api` och `src` kan importeras:

```bash
.venv/bin/python -m scripts.list_all_models
```

Skript som anropar Gemini läser nyckeln från miljövariabeln `GEMINI_API_KEY`.

## Engelsk översättning (METHODS.md 14g)

När svenska texter har ändrats saknas de i den engelska ordlistan och visas på svenska i den engelska versionen.
Så synkas ordlistan:

```bash
.venv/bin/python scripts/i18n_names.py                 # namn och termer ur Rundata (vid ny Rundata eller nya språkdrag)
cd web && node scripts/i18n_crawl.mjs saknas.json      # går igenom appen på engelska (dev-servrarna måste vara igång)
node --experimental-strip-types scripts/i18n.mjs missing saknas.json > att_oversatta.json
# översätt värdena i att_oversatta.json (behåll {0}, {1} …) och för in dem:
node --experimental-strip-types scripts/i18n.mjs merge att_oversatta.json
node --experimental-strip-types scripts/i18n.mjs check # platshållarna stämmer mellan svenska och engelska
```

Rapporttexter som inte syns i appen samlas genom att skapa rapporter och köra varje mening genom
`src.i18n.translate`; det som saknas hamnar i `src.i18n.MISSING`.
