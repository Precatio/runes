# Tilläggsplan 2: *at* vid gränsen Tiundaland–Attundaland – utrymmet och robusthetstrappan

Skriven och låst 2026-11-01, innan proven nedan har räknats. Uppföljning till `analysplaner/2026-11-01-folkland-at-ristare.md`
(resultat 95ae8da: gränszonen OR 5,7, p 0,0016 med ristaren som slumpeffekt). En AI-sammanfattning av Peterson 1996 (inte
artikeln själv, ej citerbar) nämner tre andra förklaringar: skrivskolor (prövat), tid (konstant) och **utrymme** – att *at*
valdes när runslingan tog slut. Viktor 2026-11-01 tar fram artikeln.

## Data
Raderna i `utdata/folkland/at_rader.csv` (497 stenar, 109 i gränszonen) med tillägg: antalet runor i huvudläsningen
(`utdata/Malt/runrad_dubblering.stretches`), antalet namngivna personer på stenen utom ristare (`src/linking.stones`),
häradet och flyttad (korpus 605ba7cc, kolumnerna district och moved).

## Prov (sidans effekt, Tiundaland mot Attundaland, ensidigt; ristaren som slumpeffekt som i tilläggsplan 1)
1. **Utrymmet:** `prep_at ~ sida + log(runor) + namn + tidsskikt + (1 | ristare)`. Utrymmesförklaringen förutsäger
   positiva koefficienter för log(runor) och namn; de redovisas med p. Gränsen **står sig mot utrymmet** om sidans effekt
   har p < 0,05 i gränszonen.
2. **Socknen:** `(1 | ristare) + (1 | socken)`, gränszonen. Håller om p < 0,05.
3. **Ett härad i taget:** häraderna med minst 15 stenar i de två folklanden utelämnas ett i taget (båda folklanden, hela
   materialet). Håller om sidans effekt har samma riktning varje gång, och p < 0,05 där minst två tredjedelar av stenarna
   är kvar.
4. **Utan flyttade stenar** (moved = 1 utesluts), gränszonen. Håller om p < 0,05.
Fyndet är **fullt prövat inom planerna** om 1–4 håller.

## Redovisning
`utdata/folkland/at_trappa.R`, `at_trappa.json`, `at_trappa_resultat.md`.
