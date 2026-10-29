# Resultat: familjens plats (2026-10-29)

Plan: `analysplaner/2026-10-29-familjens-plats.md` (e3e7334, SHA-256 kontrollerad före körning). Kod `data.py`
(tabell + test 14–15) och `analys.R` (test 1–13, Holm), siffror `familjens_plats.json` och `inom_grupper.json`.
836 svenska runstenar på sin plats: 185 i grupp (annan sten 25–500 m bort), 472 ensamma (närmaste > 1 km), 179 däremellan.

## Utfall
- **Gravfält inom 500 m – håller.** 82 % av stenarna i grupp mot 55 % av de ensamma; oddskvot 2,4 [1,5–3,8] med
  landskap, tidsskikt och täthet kontrollerade, p 0,0002, Holm 0,003. Båda halvorna (2,3 och 2,5, p 0,009 och 0,011),
  ensam = 2 km (2,8), bara U+Sö (2,9), halverat avstånd 250 m (1,9).
- **Centralortsnamn inom 5 km – antydan, åt motsatt håll mot rådata.** Rått 39 % mot 33 %, men med tätheten
  kontrollerad oddskvot 0,53 [0,35–0,81], Holm 0,049; halva A p 0,016, halva B p 0,09. Vid halverat avstånd (2,5 km)
  ingen skillnad (1,0). Grupperna ligger inte vid Husby/-tuna när man tar hänsyn till att centralorterna ligger i
  stenrika bygder.
- **Medeltida kyrka inom 2 km – antydan** (34 % mot 17 %, OR 1,7, p 0,026, Holm 0,34).
- **Ingen skillnad påvisad:** gravhög, färdväg, gränsmärke, gammalt och ungt bebyggelsenamn, kultnamn, platsnamn i
  texten, arv/gård, hög sten, signerad. Gamla namn och kultnamn ger stora skillnader i halva B (2,9 och 3,5) men
  ingenting i halva A – inte stabilt.
- **14 Tidsdjup – ingen skillnad påvisad åt det prövade hållet** (fler stilgrupper): 42 grupper med 97 stildaterade
  stenar har i medel 1,57 olika stilgrupper mot 1,92 väntat; ensidigt p 1,0.
- **15 Kristet bredvid icke-kristet – ingen skillnad påvisad.** 23 % blandade par mot 31 % väntat, p 0,098 (134 par);
  bara 1 av 134 nära par har kristen markör på båda stenarna.

## Iakttagelse utanför planen (inte prövad enligt plan)
Test 14 var ensidigt (fler stilgrupper än slumpen). Utfallet gick kraftigt åt andra hållet: grupperna har *färre*
olika stilgrupper än slumpen, nedre svansen p 0,0001, i båda halvorna p 0,001 (1,68 mot 2,02 och 1,41 mot 1,78).
Grupperna är alltså stenar från en och samma tid – en generation – inte platser som brukades i sekler. Förbehåll:
omblandningen sker inom landskapet, och stilgrupperna varierar också geografiskt inom ett landskap (mode, verkstäder);
en ny plan med omblandning inom bygd (t.ex. 10 km) behövs innan det kan kallas ett fynd.

## Läsning
Familjernas stengrupper står vid gravfälten: där en familj reste flera stenar fanns nästan alltid (82 %) ett gravfält
inom ett par hundra meter, oftare än vid de ensamma stenarna i samma slags bygd. Det stöder läsningen att grupperna är
gårdarnas egna platser, vid gårdens gravfält, snarare än vid vägar, gränser eller maktens centralorter. Gränsmärkes-
och väghypoteserna får inget stöd i jämförelsen grupp mot ensam.

## Avvikelser från planen
- Landskap med under 10 stenar i respektive urval slogs ihop till ”övriga” i modellen (annars kan de inte skattas).
- Test 14–15: halvorna = grupperna/paren efter sockenhalvan för gruppens/parets första sten.
- I övrigt inga. Kod för robusthetsproven med halverade avstånd finns bara för landskapstesten 1–9 (stenens och textens
  egenskaper har inga avstånd).
