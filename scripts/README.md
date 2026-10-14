# Manuella utvecklingsskript

Lösa skript för felsökning mot externa tjänster (Gemini, K-samsök) och benchmark.
De är inte automatiska tester – de riktiga testerna ligger i `tests/` och körs med `pytest`.

Kör från projektroten så att `api` och `src` kan importeras:

```bash
.venv/bin/python -m scripts.list_all_models
```

Skript som anropar Gemini läser nyckeln från miljövariabeln `GEMINI_API_KEY`.

## Engelsk översättning (METHODS.md 15f)

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

## Lämningar ur Kulturmiljöregistret (METHODS.md 1c)

Korpusanalysen `remains.R` jämför runstenarnas lägen med Riksantikvarieämbetets registrerade lämningar (gravfält,
högar, färdvägar, broar, fornborgar, hamnanläggningar). Lämningarna hämtas en gång via K-samsök (RAÄ:s öppna API,
omkring 53 000 poster, några minuter) till `data/raa/lamningar.csv`, som inte ingår i repot:

```bash
.venv/bin/python scripts/fetch_raa_remains.py            # alla slag som analysen använder
.venv/bin/python scripts/fetch_raa_remains.py fornborg   # bara ett slag
```

Utan filen hoppar `remains.R` över analysen och säger att lämningarna inte är hämtade.

## Ortnamn och medeltida kyrkor (METHODS.md 1d)

`remains.R` jämför också stenarnas budskap med ortnamn som kan tyda på förkristen kult. Ortnamnen plockas ur
OpenStreetMaps utdrag för Sverige (Lantmäteriets ortnamn, omkring 900 MB, hämtas en gång till `data/cache/osm/`) med GDAL,
och medeltida kyrkor hämtas från Wikidata. Kräver `ogr2ogr` (GDAL):

```bash
.venv/bin/python scripts/fetch_place_names.py      # data/ortnamn/kultnamn.csv, platser.csv, kyrkor.csv
```

## Rikenas gränser på kartan (METHODS.md 14g)

Kartans gränslager (`web/public/geo/riken.geojson`) byggs ur definitionerna i `web/src/lib/realms.json`. Skriptet läser
landskapen ur Sveriges OSM-utdrag (som `fetch_place_names.py` hämtar) och Danmark, Norge och Slesvig ur Natural Earth,
som hämtas vid behov:

```bash
Rscript --vanilla scripts/build_realms.R
```

Kör det igen när ett område i `realms.json` får andra byggstenar.

## Danska fornlämningar och fyndplatser (METHODS.md 14f)

Fund og Fortidsminder (Slots- og Kulturstyrelsen) laddas ner som en GeoPackage, och de danska runstenar som saknar
koordinater i Rundata får en plats via sockenkyrkan i OpenStreetMap (Nominatim) och registrets runstenar. Gratis,
utan konto; GDAL (ogr2ogr) måste finnas.

```bash
.venv/bin/python scripts/fetch_dk_remains.py            # hämtar registret (omkring 110 MB) och platserna
.venv/bin/python scripts/fetch_dk_remains.py platser    # bara platserna, med den fil som redan hämtats
```
