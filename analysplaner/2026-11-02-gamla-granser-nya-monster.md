# Analysplan: nya mönster med den vikingatida indelningen

Skriven och låst 2026-11-02, innan något av proven har körts. Viktor 2026-11-02: "kan vi hitta några nya mönster som
sticker ut med den nya vikingatida geografiska indelningen". Bygger på Fas 5 (region_old, gränsskannern 7d22ff40,
jämförelsen 13084e18). Det som redan är prövat där räknas inte som nytt.

## Data
De 27 dragen i folklandsplanen (`utdata/folkland/folkland.py` FEATS) ur `utdata/upptackt_v3/drag.csv`; bara runstenar
(svenska landskap, som gränsskannern). Regionen är `src/regions.old_region`. Tidsskikt som i gränsskannern
(–1010, 1010–1040, 1040–1070, 1070–, odaterad). Halvorna: socknar varannan inom landskapet, ordnade efter medeldatering.

**Härad per sten** (nytt): stenens socken (Rundata) mot ISOF:s socknar (`geografi_kallor/isof/parishes.json`, samma namn
inom 25 km, annars närmaste ISOF-socken inom 15 km) → ISOF:s härad (`districts.json`, `district_id`). Stenar utan härad
utesluts bara ur steg 1 och 3.

## Steg 1 – Är de gamla gränserna särskilda? (huvudfrågan)
Om folklanden bara vore godtyckliga block av grannbygder skulle vilka block som helst skilja lika mycket, eftersom
grannstenar liknar varandra. Därför:
- Enheter: Upplands härader (och skeppslag) med minst en sten. Två härader är grannar om någon av deras ISOF-socknar
  ligger inom 10 km från varandra.
- Den verkliga indelningen: häradernas folkland (Attundaland, Tiundaland, Fjädrundaland, Roden) enligt historiska_land.json.
- **Slumpindelningar:** 999 sammanhängande indelningar av samma härader i fyra block med samma antal härader per block som
  de verkliga folklanden, byggda genom att fyra slumpvalda starthärader växer turvis till slumpvald granne (avslag och
  omtag om ett block inte kan växa).
- Mått: summan över de 27 dragen av kvottestets χ² för blocktermen (drag ~ tidsskikt + block, logistisk) bland Upplands
  stenar. Andramått: antal drag med p < 0,05.
- **Utfall:** de verkliga folklanden är särskilda om deras summa ligger över 95:e percentilen av slumpindelningarna
  (p = (1 + antal ≥ verklig) / 1000 < 0,05). I båda halvorna för sig redovisas samma rangtal (håller om p < 0,05 i båda).
- Samma prov för Småland (häraderna i de små landen, verkliga landen mot 999 sammanhängande slumpindelningar med samma
  blockstorlekar), redovisat som sekundärt eftersom stenarna är få.

## Steg 2 – Vad utmärker varje gammal region inom sitt landskap?
Varje del-region med minst 30 stenar (folkland, små land, tredingar) mot resten av sitt landskap, för varje drag med minst
10 stenar med och 10 utan draget: drag ~ tidsskikt + region (logistisk, kvotprov). BH över alla prov i steget.
**Håller:** q < 0,05, p < 0,05 med samma riktning i båda halvorna, och p < 0,05 med samma riktning när regionens
vanligaste ristare (fler än 5 stenar) tas bort. Fynd som redan finns i gränsskannern eller jämförelsen märks "känt".

## Steg 3 – Häradsfickor
Varje härad med minst 15 stenar mot resten av sin gamla region (för landskap utan indelning: resten av landskapet), för
varje drag med minst 5 stenar med draget i häradet+resten och minst 10 med och 10 utan totalt: drag ~ tidsskikt + härad.
BH över alla prov i steget. **Håller:** samma tre villkor som i steg 2 (q, båda halvorna, utan häradets vanligaste ristare).
Kända lokala fickor (þennsa söder om Mälaren, upptäcktsmotorn v2) märks "känt".

## Vad som inte görs
Inga nya drag, inga trösklar ändras efter körningen, inga andra avstånd. Om steg 1 inte håller sägs det rakt ut: då är
folklandens skillnader inte större än vilka grannblock som helst ger, och steg 2–3 beskriver bygder, inte gränser.

## Redovisning
`utdata/gamla_granser/monster.py`, `monster.json`, `monster_resultat.md`. Fynd som håller blir mönster att pröva i
robusthetstrappan; inget blir "Nytt" i appen förrän trappan bekräftar det.
