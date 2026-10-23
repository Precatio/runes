# Analysplan: runstenarna, dåtidens strand och gravfälten

Låst 2026-10-23, innan något av testerna nedan har körts. Planens SHA-256 står i
`analysplaner/2026-10-23-strand-och-gravfalt.sha256`. Planen ändras inte efter låsningen; avvikelser redovisas i
`utdata/strand/resultat.md` under rubriken *Avvikelser från planen*.

Före låsningen har bara följande gjorts: datakällorna har hämtats och lagerinnehållet listats (vilka tidssnitt och koder
som finns), antalet stenar per landskap har räknats och fördelningen av stilgruppernas mittår har tagits fram för att
välja tidssnitt (median 1035, kvartiler 1030–1085, 587 daterade stenar). Inga avstånd har räknats.

## Syfte
Pröva var vikingatidens runstenar restes i förhållande till sin egen tids vattenvägar och gravfält, med två svagheter i
korpusens nuvarande resultat `water_viking` åtgärdade:
- **Flyttade stenar.** `water_viking` (median 3,61 mot 5,31 km, 2 254 stenar) räknar med stenar som i dag står vid
  kyrkor, i murar och museer. Här räknas bara stenar som inte är flyttade, med samma definition som `r/remains.R`.
- **Strandlinjen.** `water_viking` räknar dagens höjd i en terrängmodell med omkring 300 m upplösning minus en grov
  landhöjning per landskap; höjdmodellens fel är av samma storlek som landhöjningen. Här används SGU:s
  strandförskjutningsmodell, som bygger på strandförskjutningskurvor över hela landet, en landhöjningsmodell och en
  svensk höjdmodell med 50 m upplösning.

Resultatet ska bära en populärvetenskaplig artikel på vitkirunor.se.

## Material
- **Runstenarna:** korpusens CSV med fingeravtryck `d6cffd1578418f74` (samma fil i den senaste körningen
  `5fdfd1e095bfb6fb`), SHA-256 `4fca4baf47867e5c294d4c97d7dd34496d7fcc07996f68efddec1261a2bcb5ba`. Den innehåller alla
  svenska vikingatida runstenar i Rundata (2 321; objekttypen runsten enligt `gaps.is_runestone`).
- **Urval:** stenar med koordinater som *inte* är flyttade (`moved` = 0, `src/r_bridge.is_moved`: Rundatas placering
  eller plats är kyrka, kyrkogård, vägg, museum, samling m.m.; METHODS 1c). Bara landskap med minst 20 sådana stenar
  prövas: **Uppland (U, 623), Södermanland (Sö, 234), Östergötland (Ög, 89), Småland (Sm, 69), Västergötland (Vg, 64)
  och Öland (Öl, 20)**, sammanlagt 1 099 stenar. SGU:s modell täcker hela Sverige, så alla sex ligger inom modellen. De
  45 stenarna i övriga landskap (Vs 13, Nä 9, M 7, Gs 4, Hs 3, G 3, Vr 2, Bo 2, D 1, J 1) prövas inte och anges bara
  till antalet.
- **Strand och sjöar:** SGU, *Strandförskjutningsmodell (öppna data)*, produktbeskrivning version 1.0 (2022-06-14),
  licens CC BY 4.0, modellen enligt Påsse & Daniels (2015). Filerna `strandforskjutning_1_900.gpkg` (SHA-256
  `c19d6f8eceb4d5337b8a855f76892745af51726ba3dea21f091f79ee0013915e`) och `strandforskjutning_1000_1900.gpkg`
  (`5905cf492effdf0ef61ea1ec7d32644bf165b56d7eba5dd30e9127d57630d2a5`), hämtade 2026-10-23 till
  `/Volumes/2TB/cache/strand/sgu/`. Lagren `issjohav_<BP>` är ytor i SWEREF 99 TM; kod 1 = hav, kod 4 = sjö (fyllda
  sänkor i den modellerade markytan, enligt SGU "ytterst ungefärliga").
  - **Huvudsnitt:** `issjohav_900` = år 1050. Valt för att det ligger närmast stenarnas datering (median av
    stilgruppernas mittår 1035, de flesta 1030–1085) av de tillgängliga snitten 1050 och 950.
  - **Dagens vatten:** `issjohav_1` = år 1949 i samma modell.
- **Gravfält:** Kulturmiljöregistret (RAÄ) via K-samsök, `data/raa/lamningar.csv` (hämtad 2026-10-12, 52 674 lämningar,
  SHA-256 `bbbabb88d1a3c16c0c2a2c0526467ee5689073e512e12a4109160ddecc4180c9`), typen `gravfält`.
- **Oberoende höjdmodell (bara robusthet R6):** Copernicus DEM GLO-30 (ESA; © DLR e.V. 2010–2014 och © Airbus Defence
  and Space GmbH 2014–2018, tillhandahållen under COPERNICUS-programmet), 1 bågsekund (omkring 30 m), från AWS Open Data
  (`copernicus-dem-30m`), hämtad till `/Volumes/2TB/cache/strand/copernicus/`. Den är en ytmodell (skog och hus ingår).
- **Inte använd:** Lantmäteriets Markhöjdmodell (1 m, CC BY 4.0, STAC `dtm-cog`) kräver inloggning på Geotorget vid
  nedladdning (HTTP 401 från den här datorn) och används därför inte.
- **Programvara:** R 4.6.1 med sf och terra; skriptet sparas i `utdata/strand/`. Slumpfrö 2026.

## Mått
För varje sten och varje slumppunkt:
- **d_then:** avståndet (m) till närmaste vatten år 1050 (kod 1 eller 4 i `issjohav_900`); 0 om punkten ligger i
  vattnet.
- **d_now:** samma mot år 1949 (`issjohav_1`).
- **Andelen inom 500 m och inom 1 km** från vattnet år 1050 (och 1949, som jämförelse).
- **d_grave:** avståndet till närmaste registrerade gravfält, och andelen inom 500 m (som i `remains.R`).

Effektmått i klartext:
- medianerna och kvoten mellan stenarnas och slumppunkternas median;
- **sannolikheten att en slumpvis vald sten står närmare än en slumpvis vald slumppunkt** (AUC, lika avstånd räknas
  till hälften; 0,5 = ingen skillnad).

## Nollmodell
Samma lokala nollmodell som i korpusen: för varje landskap slumpvisa punkter, likformigt fördelade inom 5 km från
landskapets stenar (unionen av buffertar kring de icke flyttade stenarna). Punkter som ligger i vatten år 1050 eller år
1949 enligt SGU:s modell kastas, så att varje punkt är land både då och nu. **Tio punkter per sten** (10 990 punkter),
dragna en gång med fröet 2026. Samma punkter används för alla mått och prov utom R7.

## Delning i två halvor
Som i `remains.R` och `change.R`: inom varje landskap sorteras socknarna efter stenarnas medeldatering och delas
växelvis i halva A och B, så att hela socknar hamnar i samma halva. Varje slumppunkt får samma halva som den närmaste
stenen i samma landskap.

## Prov
**H1 (primärt): stenarna står närmare vattnet år 1050 än slumppunkterna.** Wilcoxons rangsummetest, ensidigt (stenar
närmare), på d_then över de sex landskapen sammantaget.
- Per landskap samma test, Benjamini–Hochberg över de sex landskapen.
- I halva A och halva B var för sig.

**H2: närheten är tydligare mot dåtidens vatten än mot dagens.** Skillnaden ΔAUC = AUC(d_then) − AUC(d_now), med 95 %
konfidensintervall ur 2 000 bootstrapurval (stenarna dras om per plats, se R4, inom landskapet; slumppunkterna dras om
inom landskapet). Tvåsidigt: "tydligare" sägs bara om hela intervallet ligger över 0, "svagare" bara om det ligger under.
Kvoten mellan medianerna redovisas för båda.

**H3: gravfälten, på samma urval.** Wilcoxon ensidigt på d_grave, och andelen inom 500 m för stenar och slumppunkter
(test av två andelar, ensidigt); per landskap med Benjamini–Hochberg över de sex; i båda halvorna.

**Sekundära prov** (en familj, Benjamini–Hochberg över de fem p-värdena):
- **S1, vatten och gravfält tillsammans:** logistisk regression sten (1) mot slumppunkt (0) med log2(d_then + 250 m) och
  log2(d_grave + 250 m) samt landskapet som förklaringsvariabler. Effekten anges som oddskvoten när avståndet halveras,
  för vattnet (S1a) och gravfälten (S1b). Frågan är om närheten till vatten finns kvar när närheten till gravfält
  hålls konstant, och tvärtom.
- **S2, tiden:** bland daterade stenar, logistisk regression av "inom 1 km från vattnet år 1050" på stilgruppens mittår
  (per 50 år) med landskapet konstant.
- **S3, kristna markörer:** samma utfall på kristna markörer (kors eller kristen formel, som i `remains.R`) med tiden och
  landskapet konstanta.
- **S4, bro- och vägstenar:** samma utfall på bro- och vägstenar (`cat_bro_vag`) med landskapet konstant; tvåsidigt.
  Medianavståndet för bro- och vägstenar och övriga redovisas. Broarna gick ofta över åar och våtmarker som inte finns i
  modellens vatten.

Varje sekundärt samband prövas också i båda halvorna och redovisas som replikerat bara om det är signifikant (p < 0,05)
åt samma håll i båda.

## Robusthet (för H1, och för H3 där det står)
Var och en redovisas med medianer, AUC och p:
- **R1, tidssnitt:** år 750, 950, 1150 och 1250 (`issjohav_1200`, `_1000`, `_800`, `_700`; snittet år 850 saknas hos
  SGU). Fyra sekel motsvarar omkring ±1 m strandnivå i Mälardalen (landhöjning omkring 5 mm om året). Därtill år 550 och
  1550 (`_1400`, `_400`), SGU:s angivna tidsosäkerhet om upp till 500 år.
- **R2, bara havet:** d_then mot kod 1 utan de modellerade sjöarna.
- **R3, halvorna:** se H1.
- **R4, platser i stället för stenar:** stenar inom 200 m från varandra (enkel länkning, inom landskapet) slås ihop till
  en plats med medianavståndet; platserna mot slumppunkterna. Gäller H1 och H3.
- **R5, stenar i vattnet:** H1 utan stenar som enligt modellen står i vatten år 1050 (antalet redovisas).
- **R6, oberoende höjdmodell, landhöjningen ±1 m:** vattnet år 1050 som Copernicus-celler (omprojicerade till 30 m i
  SWEREF 99 TM) på höjd högst landskapets landhöjning i `r/common.R` (U 5,5, Sö 5, Ög 3, Vg 2,5, Sm 1,5, Öl 1,5 m) plus
  δ, för δ = −1, 0 och +1 m. Låg mark räknas som hav bara om den hänger samman (8-grannar) med havet år 1949 i SGU:s
  modell; SGU:s sjöar år 1949 läggs till. Samma slumppunkter, utom de som hamnar i vatten. Landhöjningsvärdena är
  projektets grova värden, inte avlästa ur en viss kurva; R6 prövar alltså att resultatet inte hänger på SGU:s modell
  och höjdmodell, inte att värdena är rätt.
- **R7, nollmodellens radie:** slumppunkter inom 2 km och inom 10 km i stället för 5 km (nya punkter, tio per sten,
  fröet 2026). Gäller H1 och H3.

## Kriterier
**H1 håller (bekräftat mönster)** om alla dessa är uppfyllda:
1. H1 sammantaget p < 0,05 och AUC > 0,5;
2. båda halvorna p < 0,05 åt samma håll;
3. R4 (platser) p < 0,05;
4. de fyra tidssnitten i R1 inom ±200 år (750, 950, 1150, 1250) alla p < 0,05;
5. R2 (bara havet) p < 0,05.

Om 1 är uppfyllt men något av 2–5 inte är det, redovisas H1 som *indikation*, med vad som föll. Om 1 inte är uppfyllt
redovisas H1 som *inte stött*. Ett landskap sägs visa mönstret om dess q < 0,05. R1 år 550/1550, R5, R6 och R7 avgör
inte utfallet men redovisas. Faller R6 för något δ står det i resultatet att mönstret hänger på SGU:s modell.

**H3 håller** om sammantaget p < 0,05, båda halvorna p < 0,05 och R4 p < 0,05.

Statistisk signifikans i sig säger inte att skillnaden är stor; AUC och andelarna anges alltid tillsammans med p.

## Jämförelse (beskrivande, inte ett prov)
- **D1:** samma mått med flyttade stenar medräknade (alla stenar med koordinater i de sex landskapen, nollmodellen kring
  dem), för att visa vad uteslutningen av flyttade stenar gör.
- **D2:** korpusens nuvarande `water_viking` och `remains.R`-resultat återges bredvid de nya.

## Figurer
Båda på svenska och engelska (PNG):
- **(a) Karta över Mälardalen** (U, Sö och Vs): dagens vatten (SGU år 1949), vattnet år 1050 (SGU) och de icke flyttade
  runstenarna.
- **(b) Per landskap:** andelen stenar och slumppunkter inom 1 km från vattnet år 1050, med antalet stenar.

Bildtexterna anger källorna: SGU (CC BY 4.0), Rundata, Kulturmiljöregistret (RAÄ) och, för R6, Copernicus DEM.

## Redovisning
Allt nedan redovisas oavsett utfall, i `utdata/strand/resultat.md` (på svenska, varje siffra förklarad i klartext),
`resultat.json` och figurerna:
- alla prov ovan med n, medianer, andelar, AUC, p (och q där det står), också de som inte är signifikanta;
- alla sex landskap, också de där mönstret inte syns;
- antalet stenar som enligt modellen står i vatten år 1050 och år 1949;
- avvikelser från planen.

Svagheterna anges:
- SGU:s modell är regional (50 m höjdmodell, tidsfel upp till 500 år, tröskelhöjder med fel under 5 m) och inte avsedd
  för detaljstudier; sjöarna är ungefärliga, och åar, bäckar och våtmarker saknas;
- en stens plats i Rundata kan avvika från den ursprungliga även när stenen inte räknas som flyttad;
- Kulturmiljöregistret är olika väl inventerat i olika trakter, och gravfälten är oftast odaterade;
- stenar som står i grupp är inte oberoende (därför R4);
- de små landskapen har få stenar.
