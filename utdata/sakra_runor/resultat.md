# Säkra runor mot hela slingan, och hur måtten tål sämre skanningar – resultat

Låst plan: `analysplaner/2026-11-19-sakra-runor-skanningskvalitet.md` (sha256 `fb4a444a…`). Tilläggsplan 1: `analysplaner/2026-11-19-sakra-runor-tillagg-1-annan-kalla.md` (sha256 `e7dd8b3d…`). Räknat av `utdata/sakra_runor/analys.py` ur `matningar/` och `matningar_zedig/` (groove-7, `kor.py`).

## Kontroll av kedjan (D0)

- Stenar där den sparade groove-7-mätningen använde samma slingor som i dag (ritade): 19; inom 0,5° och 0,1 mm: 19 av 19.
- Största avvikelse bland dem: 0,0000 (grader eller mm).
- Stenar vars sparade mätning (2026-11-03) använde slingmodellen eftersom djupbildens origo saknades (rättat 2026-11-08): 17. De mäts nu med de ritade slingorna, som planen kräver, och jämförs därför inte med de sparade värdena; deras D0 är dagens mätning.

## R1 – tål S sämre skanningar bättre än H? (Kitzler Åhfeldt)

- Stenar med H- och S-mått i alla fyra körningarna: 29.
- Medelskillnad ICC(S) − ICC(H) över 3 mått × 3 försämringar: **-0,006**, 95 %-intervall -0,020 till 0,003 (2000 omdragningar av stenar).
- Per mått (medel över D1–D3): V-vinkel (°) -0,024; spårdjup (mm) -0,012; spårbredd (mm) 0,017.
- **R1 håller inte** (villkor: intervallet över 0 och skillnaden positiv för minst två av tre mått; positiv för 1).

ICC(2,1) mellan originalet och den försämrade skanningen:

- V-vinkel (°): D1 H 0,984, S 0,959; D2 H 0,978, S 0,952; D3 H 0,985, S 0,964
- spårdjup (mm): D1 H 0,991, S 0,964; D2 H 0,992, S 0,984; D3 H 0,967, S 0,966
- spårbredd (mm): D1 H 0,972, S 0,966; D2 H 0,932, S 0,960; D3 H 0,952, S 0,982

## R2 – skiljer S ristarna åt minst lika bra som H? (Kitzler Åhfeldt, originalet)

- Stenar: 10 (Sö 112, Sö 129, Sö 143, Sö 149, Sö 160, Sö 162, Sö 164, Sö 211, Sö 333, Sö 45); par på samma bergart: 12 (6 med samma ristare, 6 med olika).
- Utan bergart i Rundata och därför utanför: Sö 206, Sö 208.
- S: avstånd samma ristare minus olika ristare -0,957 (z-enheter), p = 0,1021 (10000 omblandningar inom bergarten).
- H: avstånd samma ristare minus olika ristare -0,718 (z-enheter), p = 0,1021 (10000 omblandningar inom bergarten).
- **R2 håller inte för S.** H skiljer inte ristarna mer än S.
- R2 är litet: få ristare har två eller fler stenar i materialet, och bara par på samma bergart räknas. Omblandningen inom bergarten ger bara 10 olika värden av teststorheten, så p kan inte bli lägre än omkring 0,10: provet kunde inte hålla med det här materialet.

## R1z – samma prov på Zedigs skanningar (tilläggsplan 1)

- Filer med H- och S-mått i alla fyra körningarna: 16, från 16 stenar.
- Medelskillnad ICC(S) − ICC(H): **-0,011**, 95 %-intervall -0,030 till 0,009 (2000 omdragningar sten för sten).
- Per mått: V-vinkel (°) -0,008; spårdjup (mm) -0,029; spårbredd (mm) 0,005.
- **R1z håller inte** (positiv för 1 av 3 mått).
- ICC V-vinkel (°): D1 H 0,978, S 0,969; D2 H 0,982, S 0,982; D3 H 0,985, S 0,967
- ICC spårdjup (mm): D1 H 0,992, S 0,978; D2 H 0,982, S 0,969; D3 H 0,945, S 0,885
- ICC spårbredd (mm): D1 H 0,968, S 0,952; D2 H 0,917, S 0,960; D3 H 0,939, S 0,926
- R2 görs inte i tillägget. Ristare med flera stenar i Zedigs material: inga.

## Beslut

- Huvudplanens regel: **H** (R1 håller inte; R2 visar inte att S skiljer ristarna sämre).
- Tilläggets ändrade regel (R1 och R1z måste hålla): **H**. H behålls som appens förvalda stenmått, och S redovisas som ett alternativ med båda resultaten.

## Beskrivande – Kitzler Åhfeldt

- Säkra runor per sten (D0): median 37,0, från 3 till 115; S-mått för 34 av 36 (utan: Sö 205, Sö Fv1954;20).
- Runornas ICC för V-vinkel (°): median 0,34 (36 stenar, 0,06–0,61); Spearman–Brown, median över stenarna: 1 runa 0,34, 4 0,67, 8 0,80, 15 0,88, 30 0,94.
- Runornas ICC för spårdjup (mm): median 0,44 (36 stenar, 0,24–0,92); Spearman–Brown, median över stenarna: 1 runa 0,44, 4 0,76, 8 0,86, 15 0,92, 30 0,96.
- Runornas ICC för spårbredd (mm): median 0,32 (36 stenar, 0,07–0,77); Spearman–Brown, median över stenarna: 1 runa 0,32, 4 0,65, 8 0,79, 15 0,88, 30 0,93.
- Förflyttning H (medel D − D0, inom parentes medel av beloppet): D1: V-vinkel -1,54 (1,86), spårdjup 0,06 (0,10), spårbredd -0,42 (0,53); D2: V-vinkel 1,87 (1,89), spårdjup 0,10 (0,11), spårbredd 0,95 (0,95); D3: V-vinkel 0,64 (1,86), spårdjup 0,19 (0,23), spårbredd 0,64 (0,73).
- Förflyttning S (medel D − D0, inom parentes medel av beloppet): D1: V-vinkel -1,86 (2,73), spårdjup 0,05 (0,19), spårbredd -0,47 (0,51); D2: V-vinkel 1,70 (2,54), spårdjup 0,02 (0,13), spårbredd 0,59 (0,65); D3: V-vinkel 0,86 (2,41), spårdjup 0,09 (0,21), spårbredd 0,17 (0,41).
- Störst skillnad mellan H och S: Sö 137A (549 snitt, 39 säkra runor): V-vinkel (°) H 119,49 mot S 114,24, spårdjup (mm) H 5,61 mot S 6,19, spårbredd (mm) H 19,58 mot S 19,36.

## Beskrivande – Zedig

- Säkra runor per skanning (D0): median 22,0, från 0 till 132; S-mått för 20 av 27 (utan: HS_14_1mm_complete_thin03, HS_1A_thin02, HS_3_thin01, M_13_Oxsta_thin03, M_14_020_Byn_thin02, M_14_040_Byn_thin03, M_2_Svala_thin03).
- Runornas ICC för V-vinkel (°): median 0,26 (27 stenar, -0,09–0,62); Spearman–Brown, median över stenarna: 1 runa 0,26, 4 0,58, 8 0,74, 15 0,84, 30 0,91.
- Runornas ICC för spårdjup (mm): median 0,47 (27 stenar, 0,23–0,86); Spearman–Brown, median över stenarna: 1 runa 0,47, 4 0,78, 8 0,88, 15 0,93, 30 0,96.
- Runornas ICC för spårbredd (mm): median 0,36 (27 stenar, 0,06–0,92); Spearman–Brown, median över stenarna: 1 runa 0,36, 4 0,69, 8 0,82, 15 0,89, 30 0,94.
- Förflyttning H (medel D − D0, inom parentes medel av beloppet): D1: V-vinkel -2,31 (2,68), spårdjup 0,07 (0,15), spårbredd -0,50 (0,70); D2: V-vinkel 2,85 (3,04), spårdjup 0,08 (0,25), spårbredd 1,13 (1,24); D3: V-vinkel 1,91 (3,90), spårdjup 0,24 (0,38), spårbredd 1,19 (1,33).
- Förflyttning S (medel D − D0, inom parentes medel av beloppet): D1: V-vinkel -2,06 (2,77), spårdjup 0,10 (0,17), spårbredd -0,48 (0,57); D2: V-vinkel 2,18 (2,69), spårdjup 0,05 (0,18), spårbredd 0,74 (0,75); D3: V-vinkel -0,35 (2,82), spårdjup 0,21 (0,33), spårbredd 0,49 (0,58).
- Störst skillnad mellan H och S: M 4 (343 snitt, 31 säkra runor): V-vinkel (°) H 131,46 mot S 136,47, spårdjup (mm) H 2,37 mot S 2,27, spårbredd (mm) H 12,22 mot S 12,85.

## Vad som inte sägs

- Försämringarna efterliknar sämre skanningar men är inte riktiga skanningar med en annan skanner.
- Ett S som tål försämringen bättre betyder inte att det mäter ristarens hand.
- Två källor med olika stenar ger inget prov av samma sten i två skannrar; det kräver att någon sten skannas om.

## Avvikelser

- Kontrollen av kedjan (D0): planen jämför med de sparade groove-7-värdena. För de stenar vars sparade mätning (2026-11-03) använde slingmodellen, eftersom djupbildens origo saknades (felet rättades 2026-11-08), mäts D0 nu med de ritade slingorna, som planen kräver ("samma ritade slingor"). De kan inte jämföras med de sparade värdena, så kontrollen gjordes på stenarna vars sparade mätning använde de ritade slingorna. Kedjan ändrades inte.
- Sö 371 ingår inte: slingorna är märkta "överhoppad", inte granskade, och planen tar med stenar med ritade slingor. Materialet blir 36 skanningar i stället för 37.
- R2: "samma bergart" tolkas som samma uppsättning bergartsfamiljer ur Rundatas material (src/geology.families; gråsten ger gnejs och granit), och omblandningen görs inom den. "Samma ristare" betyder att stenarna delar minst en säker ristare (signerad eller attribuerad, inte osäker). Stenarna i R2 och z-skalningen är de med både H- och S-mått i originalet, så att S och H prövas på samma stenar. p är ensidigt (mindre avstånd vid samma ristare).
- Beskrivande, Spearman–Brown: en sten med negativ ICC för runorna räknas med ICC 0 (formeln är inte definierad för alla k när ICC är negativ). Det gäller bara den beskrivande kurvan, inget prov.
- Tilläggsplan 1: bruset i D1 och D3 har fröet ur tilläggets kontrollsumma (planen nämner tilläggets frö för omdragningen). D0 mäts med vyn som appen väljer för de öppna skanningarna (djupbildens normal och upp-riktning, rakt mot den ristade sidan, den vy slingorna är ritade i) och appens förval i övrigt (Vitki-protokollet; stavlöst läge på när Rundata bara anger stavlösa runor, vilket inte ändrar något när slingor finns).
