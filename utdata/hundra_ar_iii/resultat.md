# Hundra år av runfrågor III – resultat

Plan: analysplaner/2026-11-20-hundra-ar-III.md (7e288d5c, c5a33b6), tillägg 1 (c2180a7f, 67477c4), tillägg 2
(0a5a4342, 9776420). Skript: omnamnanden.py → analys.py → analys_m4.R. Siffrorna nedan gäller efter tillägg 2.

## Kvalitetsgrind
100 omnämnanden (seed 20261121): 100 riktiga. Därefter hittades två slags felträffar som stickprovet inte fångade:
signum utanför huvudserien som mönstret inte kan hitta (tillägg 1: 193 stenar, 101 på Öland, räknas inte) och OCR med
uppdelade siffror ("U 1 29", tillägg 2). Ett extra stickprov om 30 omnämnanden av stenar med ett- eller tvåsiffriga
nummer efter tillägg 2 gav 27 riktiga (fel: "M 1 : 1" skala, "U 1, 3, 4" och "U 2 och 9" i en lista över kistor) – enstaka
felträffar finns kvar bland låga nummer. Före tillägg 1: 1 873 omnämnanden; före tillägg 2: 1 873; efter: 1 814.

## Underlaget
2 321 svenska vikingatida runstenar, varav 2 128 mätbara. 1 814 text–sten-par i 245 tidskriftstexter; 4 434
verk–sten-par i 8 indexerade avhandlingar (ofta förteckningar).

## M1 per årtionde (andel av omnämnandena; Uppland har 53 % av de mätbara stenarna, Östergötland 9,6 %)
- 1906–1949: 18 texter, 56 stenar; Sö 60 %, U 24 %.
- 1950-talet: 12 texter, 76 stenar; U 63 %, Ög 1 %.
- 1960-talet: 17 / 65; U 72 %, Ög 1 %.
- 1970-talet: 21 / 168; U 71 %, Ög 10 %.
- 1980-talet: 23 / 116; U 57 %, Sö 28 %, Ög 1 %.
- 1990-talet: 18 / 120; U 70 %, Ög 2 %.
- 2000-talet: 17 / 88; U 69 %, Ög 2 %.
- 2010-talet: 78 / 546; U 43 %, Sm 14 %, Ög 8 %.
- 2020-talet (–2025): 41 / 243; U 44 %, Ög 12 %.
738 omnämnanden före 2010, 783 på 2010-talet.

## M2
1 122 av 2 128 (53 %) nämns aldrig med signum i tidskrifterna; 1 006 nämns minst en gång, 582 bara en gång. De 106
mest nämnda (5 %) står för 29 % av omnämnandena. Tio i topp: Ög 136 Rök 24, Vg 119 Sparlösa 13, U 729 Ågersta 12,
U 1161 Altuna 11, U 323 Sälna 9, Ög 8 Kälvesten 8, Öl 1 Karlevi 8, Vs 15 Lilla Kyringe 7, Sö 179 Gripsholm 7,
U 127 Danderyd 7. Obs: Rök nämns med signum i bara två texter före 2010 – äldre texter skriver "Rökstenen".

## M3 aldrig nämnda (tidskrifter; tidskrifter + avhandlingar)
- Alla: 1 122 (53 %); 328 (15 %).
- Textlängd (runor; gränser 22, 42, 62): Q1 426/550 (77 %), Q2 301/532, Q3 251/522, Q4 144/524 (27 %); med avhandlingar
  Q1 244/550 (44 %), Q4 8/524 (2 %).
- Förlorad 272/408 (67 %) mot kvar 850/1 720 (49 %).
- Ristare 328/767 (43 %) mot ingen 794/1 361 (58 %); med avhandlingar 29 mot 299.
- Stilgrupp: ingen säker 659/1 097 (60 %); daterade 41–60 %.
- Landskap: se matt.json.

## M4 (glmer, 2 128 stenar, 605 socknar)
Oddskvoter (95 %): Sm 5,57 (3,26–9,52); Vs 2,26 (0,84–6,13); Ög 0,79 (0,52–1,20); Vg 0,73 (0,45–1,18); Sö 1,06;
Öl 1,38; G 1,18; Gs 0,66; övriga 0,95 – inget landskap mindre uppmärksammat än Uppland. Förlorad 0,59 (0,45–0,77).
Ristare 1,18 (0,92–1,51). Stilgrupper: alla intervall omfattar 1. log(längd+1) 2,56 (2,21–2,96), dvs. dubbel
textlängd ≈ 1,92 gånger oddsen. Småland: 79 av 164 omnämnanden kommer från en text (Stille 2015, Tiohärad).
Före tillägg 2 (tillägg 1): samma riktning och slutsatser (Sm 5,69; förlorad 0,56; längd 2,58).

## M5
58 härader med minst 10 mätbara stenar; bara Gräsgårds härad (Öland) har ≥ 80 % aldrig nämnda (9 av 10).

## M6
21 avhandlingar i litteraturregistret: 1970-talet 1, 1990-talet 7, 2000-talet 7, 2010-talet 4, 2020-talet 2.
