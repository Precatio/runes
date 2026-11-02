# Nya mönster med den vikingatida indelningen – resultat (2026-11-02)

Plan: analysplaner/2026-11-02-gamla-granser-nya-monster.md (sha 054c87d5), avvikelse 1 (sha f0a42169, före resultat:
grannar mellan härader inom 20 km). Skript monster.py, data monster.json. 1 738 runstenar, alla med härad (ISOF).

## Steg 1 – Är de gamla gränserna särskilda?
**Uppland: ja, håller.** 32 härader, 841 stenar, 25 drag. De verkliga folklanden ger χ²-summan 360; 999 sammanhängande
slumpindelningar av samma härader i block av samma storlek ger median 183 och 95:e percentil 259. Ingen slumpindelning
når upp till folklanden: p 0,001 (provets golv), och lika i båda halvorna (237 mot median 129; 217 mot 125; båda p 0,001).
Antal drag som skiljer: 14 mot median 8 (p 0,026).

**Småland: nej.** 19 härader, 103 stenar, 14 drag: 199 mot median 183 (p 0,15; halvorna p 0,16 och 0,37). Stämmer med
den tidigare Smålandsstudien (utdata/smalanden/) – för få stenar, eller inga skillnader som följer landen.

Läsning: folklandens gränser fångar skillnader i 1000-talets stenar som andra lika stora grannblock inte fångar. Det talar
för att gränserna – eller något som föregick dem – fanns redan när stenarna restes, fast indelningen är känd först ur
1300-talets källor (sexårsgärden 1314, Upplandslagen 1296). Det är ett argument, inte ett bevis.

## Steg 2 – Vad utmärker varje del-region inom sitt landskap
114 prov, 27 med q < 0,05, **12 håller** (båda halvorna, utan regionens vanligaste ristare). 11 av dem fanns redan i
gränsskannern eller jämförelsen (kors, *at*, r för ʀ, monoftong, flera resare, granit, kristna formler i Roden).
Det enda nya: **Finnveden** reser nästan aldrig stenar av granit (4 % mot 66 % i resten av Småland) – det följer
berggrunden och säger inget om sed.

## Steg 3 – Häradsfickor
731 prov i 35 härader, 11 med q < 0,05, **6 håller**:
- **Redvägs härad (Vg): stungna runor på alla 13 stenar** där det kan avgöras, mot 36 % i resten av Västergötland.
  Ingen ristare har fler än fem stenar där. Starkaste nya fyndet.
- **Sotholms härad (Sö, Södertörn): nästan inga kristna formler** – 1 av 43 stenar, mot 20 % i resten av Södermanland.
  Håller utan Amunde (11 stenar).
- **Hagunda härad (Tiundaland): färre kors** – 40 % mot 68 % i resten av Tiundaland. Håller utan Åsmund.
- **Håbo härad (Tiundaland): fler stungna runor** – 70 % mot 57 %. Håller utan Arbjörn.
- Rönö härad (Sö) och Lyhundra härad (Attundaland): mindre granit – berggrund, inte sed.

**Kontroll mot litteraturen:** Vadsbo härad (Vg) skriver r för ʀ i 7 av 11 stenar mot 6 % i resten av Västergötland
(q 0,004) – precis den ficka Larsson 2002 (s. 170) pekar ut. Den klarar inte halvorna (för få stenar per halva) och räknas
därför inte som hållande, men att skannern hittar den på egen hand är ett gott tecken för metoden.

## Reservationer
- Granit (bergarten) ingår bland de 27 dragen och följer berggrunden. Känslighetsprov utan granit: se nedan.
- Fickorna bygger på 13–47 stenar per härad; de är mönster att pröva, inte slutsatser. Inget blir "Nytt" i appen förrän
  robusthetstrappan bekräftat det.
- Häradsindelningen är ISOF:s (sen medeltid/nyare tid); hundarena i Uppland kan ha sett annorlunda ut på 1000-talet.

## Känslighetsprov utan granit (utanför planen, 2026-11-02)
Steg 1 för Uppland utan draget mat_granit (24 drag, samma 999 slumpindelningar): folklanden 318 mot median 154 och 95:e
percentil 228, p 0,001; halvorna 202 mot 109 (p 0,001) och 201 mot 110 (p 0,002). 13 drag skiljer mot median 7.
Resultatet beror alltså inte på berggrunden. (monster_kanslighet.py, monster_kanslighet.json)
