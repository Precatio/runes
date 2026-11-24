# Analysplan: gör ornamentiken grupperna av stenar med samma hand bättre? (SRI-planscher, nya ristare)

Skriven och låst 2026-11-24, innan någon ornamentkod har jämförts med facit. Programmet: `analysplaner/2026-11-23-nya-ristare-program.md`
(medel 5, ornamentik). Det här blir den **andra** användningen av facits provdel (högst tre).

## Bakgrund
- Parmodellen M1 och grupperna vid τ = 0,8 håller i slutprov 1 (S1 och S2) och i slutprov 2 (T1).
- Modellen ser text, stavning, stilgrupp, korsform, SRI:s ornamentord, bergart och avstånd. Den ser nästan inget av hur
  rundjuret är ritat: huvud, flikar, svans, fötter och flätverk. Runologerna nämner just sådana drag när de säger att två
  stenar har samma hand.
- SRI:s planscher (RAÄ, Digitala Sveriges runinskrifter) avbildar 1 170 av korpusens 2 314 stenar (bildtexterna i
  textlagret, `utdata/nya_ristare/ornamentik/planscher.py`). Öland, Gotland, Hälsingland, Medelpad och Södermanlands
  första planschhäfte saknas.
  - I utvecklingsdelen har 26 facitgrupper minst ett par inom 30 km där båda stenarna är avbildade; 11 av dem är onämnda.
  - I provdelen gäller det 27 grupper, varav 9 onämnda.
- Planscherna är upphovsrättsligt skyddade: de läses och räknas bara. Varken bilderna eller koderna per sten läggs i git.

## Kodningen (instrumentet)
- **Kodboken:** `utdata/nya_ristare/ornamentik/kodbok.md`, version 2 (sha 97cf9214). Ingen ändring efter låsningen.
- **Piloterna (utanför facit):**
  - Två piloter på 12 och 20 stenar, alla utanför facitgrupperna. Pilot 2 användes för att ta fram version 2.
  - Ändringarna i version 2: rendering i 300 dpi, obligatorisk inzoomning, och fältet `upplagg` uppdelat i
    `djurhuvud` och `antal_djur`.
  - Utfallet i pilot 2:
    - de flesta fält har kappa 0,6–1,0;
    - `fotter` och `huvud_svans` har kappa 0;
    - läsarnas stilbedömning stämmer med Rundata i 4 av 14 fall.
  - Alla 1 170 stenarna kodas om med version 2; pilotkoderna används inte.
- **Läsarna:** varje avbildad sten kodas av två oberoende läsare (Anthropics språkmodell Claude, Claude Opus), fem stenar
  per läsare och omgång, i omvänd ordning för den andra läsaren. Läsaren ser bara planschsidorna och signum. Den uppmanas att
  inte använda kunskap om stenen, ristaren eller litteraturen.
- **Värdet per sten och fält:** bara när båda läsarna anger samma värde. Annars, eller vid `osäkert`, saknas värdet.
- **Fälten som får användas:** de med Cohens kappa ≥ 0,40 och täckning ≥ 0,30 (andel stenar där båda angav ett värde),
  räknat över alla kodade stenar med bild. Detta avgörs utan facit. `stil` används aldrig som belägg (den finns redan i
  Rundata); den används bara för att jämföra läsarna med Rundata.

## Parmåttet
- **Ornamentlikhet:** andelen lika värden bland de godkända fälten där båda stenarna har ett värde. Värdet saknas om färre
  än tre fält är jämförbara.
- **Överskottet `ex_orn`:** likheten minus medelvärdet för stenar på samma avstånd. Det räknas på samma sätt som
  överskottet i textdragen (`_excess` i `utdata/nya_ristare/belagg.py`).
- **Antalet jämförbara fält:** `orn_n`.

## Parmodellen M2
- **Bas:** M1:s belägg plus `ex_orn` och `orn_n`.
- **Träning:** samma träning, vikter och uteslutningar som M1 (`src/hand_groups.py`, `pair_probabilities`).
- **M1 i jämförelserna:** räknas med samma kod på samma belägg, utan ornamentmåtten (`utdata/nya_ristare/ornamentik/m2.py`).
  Då skiljer sig modellerna bara i ornamentiken. Om M1 räknad så ger andra grupper än de prövade redovisas det.
- **Grupperna:** samma UPGMA med diametern ≤ 30 km.
- **Gränsen τ₂:** väljs på utvecklingsdelen. Kandidaterna är 0,50, 0,55 … 0,95. Bland dem med precision ≥ 0,77 på
  namngivna par väljs den som ger störst täckning av utvecklingsdelens facitpar. Finns ingen sådan används 0,8.

## Grind på utvecklingsdelen (provdelen öppnas inte här)
- **G1, ornamentiken bär handen:** för utvecklingsdelens facitpar med `ex_orn` rangordnas b bland stenarna på samma avstånd
  från a (± 25 %, minst ± 1 km), utanför gruppen. Medel per grupp. Ensidigt Wilcoxon-test mot 0,5 över grupperna.
  Håller om p < 0,05 och medianen > 0,5.
- **G2, M2 tappar inget:** M2:s AUC på namngivna par (utanför vikten) ≥ M1:s.
- **Om G1 och G2 håller:** slutprovet görs. **Annars:** provdelen öppnas inte, och resultatet redovisas som negativt.

## Slutprovet (provdelen P, andra användningen)
- **O1, ornamentiken förbättrar grupperna:**
  - Gäller provdelens facitgrupper med minst ett avbildat par inom 30 km.
  - Per grupp räknas andelen av gruppens par inom 30 km som ligger i samma grupp: M2 (vid τ₂) minus M1 (vid 0,8).
  - Skriptet: `utdata/nya_ristare/ornamentik/slutprov3.py`, skrivet före öppningen.
  - Ensidigt Wilcoxon-test med tecken. Nollskillnader räknas inte.
  - **Håller** om p < 0,05 och medelskillnaden > 0. Med färre än 5 grupper med skillnad håller O1 inte.
- **O2, M2 står sig mot grannarna:** S1-provet ur slutprov 1 (`utdata/nya_ristare/slutprov.py`) med M2:s grupper, på alla
  provdelens grupper. **Håller** om p < 0,05 och medelandelen är större än kontrollens.
- **Beskrivande:**
  - O1 för de onämnda grupperna;
  - O1 på litteraturens facit 2;
  - granskade par om olika händer som hamnar i samma grupp, M2 mot M1;
  - antalet grupper och okända händer.
- **Loggning:** utfallet skrivs i `utdata/nya_ristare/provdelen_logg.md`.

## Beslut (bestämt nu)
- **O1 och O2 håller:** appen byter till M2 (groups-2). METHODS, nyheter och rapporten uppdateras.
- **Bara O2 håller:** ornamentiken mäts inte förbättra grupperna. Appen behåller M1, och resultatet redovisas.
- **O2 håller inte:** appen behåller M1.

## Vad som inte skrivs
- **Delvis cirkulärt:** runologerna använde ornamentiken när de bedömde samma hand. En förbättring betyder att modellen ser
  mer av det de såg, inte att den bekräftar dem oberoende.
- **Läsarna kan känna igen stenar.** Kända stenar kan läsas med förkunskap trots instruktionen. De onämnda grupperna är
  minst utsatta.
- **Avbildningen styr täckningen.** Stenar utan plansch får ingen ornamentkod, och det säger ingenting om stenen.

## Utdata
- **I repot:**
  - `utdata/nya_ristare/ornamentik/` (skript, kodbok, sammanfattningar);
  - `resultat.md`.
- **I cachen:** `data/cache/hander/ornamentik/` (koderna per sten, utanför git).
