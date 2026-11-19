# Tilläggsplan: självkontrollen med stenar i grupp som en enhet – gravfälten, riktningen och vägarnas linjer

Skriven och låst 2026-11-19, innan något av huvudproven nedan räknats (de oplanerade kontrollräkningarna står under
"Känt före låsningen"). Viktor 2026-11-19: "ja" till granskning och rättelse av rapportutkasten. Tillägg till de låsta planerna `2026-11-10-sjalvkontroll-gravfalt.md` (8fb876c2…),
`2026-11-10-sjalvkontroll-riktning.md` (3ef2c79f…) och `2026-11-10-riktning-vaglinjer.md` (ecf9039e…), som alla räknade
varje sten som en oberoende iakttagelse. Skälet är lärdomen från 2026-11-18: storhögarnas samband föll när högar i
grupper räknades som en enhet (`2026-11-18-hogarna-grupper.md`, 6870d6cd…), och METHODS.md 1å kräver nu steget
”Grupper som enhet” för rumsliga närhetsprov. Granskningen av rapportutkastet ”Fyra runstensfynd prövade mot hundra års
invändningar” (wgzazW4ZpKk7OVtuT32w, commit 9d438a5) redovisar gruppantalen men inget prov med grupperna som enhet.

## Känt före låsningen
Allt nedan räknades 2026-11-19 i en tillfällig mapp (scratchpad), utan plan, för att bedöma beroendet. Inget av det har
skrivits till repot eller till någon rapport, utom gruppantalen.

- **Gruppantalen** (enkel länkning vid 1 km, `src/spatial_groups.link`). De står i rapportutkastet och asserteras i
  `utdata/blogg/build/build_rapport_sjalvkontroll1.py`:
  - gravfälten: de 185 stenarna i grupp är 73 grupper, och de 472 ensamma är 472 grupper med en sten var;
  - riktningen S0: 120 stenar i 101 grupper;
  - vägarnas linjer L1: 34 stenar i 25 grupper.
- **Gravfälten.** Den låsta modellen (`utdata/familjens_plats/sjalvkontroll/analys.R`, funktionen `fit`) räknades om med
  klusterrobust standardfel per 1 km-grupp (`sandwich::vcovCL`, HC1). Standardfelet sattes aldrig under modellens eget,
  och p lästes tvåsidigt mot t med 72 frihetsgrader. Utfall:
  - originalet, alla gravfält med landskap: oddskvot 2,38, p 0,0055;
  - K1: 2,60, p 0,00089;
  - K2: 2,56, p 0,0051;
  - K3a: 2,33, p 0,0071;
  - K3b: 2,51, p 0,0051.

  Alltså p 0,0009–0,007. Ingen Holm-korrigering är gjord, och halvorna är inte räknade.
- **Riktningen S0.** Statistiken var medelvärdet över grupperna av gruppens medel-cos, mot 4 999 omblandningar av
  riktningarna mellan stenarna inom landskapet (slumpfrö 2026). För 120 stenar i 101 grupper gav det p 0,0002.
  Med samma räknesätt gav S1, gamla vägar som punkter, p 0,22 för 40 stenar i 30 grupper. Provet hade redan fallit.
- **Vägarnas linjer L1.** Med samma räknesätt gav 34 stenar i 25 grupper p ≈ 0,12 (0,1188); medel-cos 0,064.
  L0, dagens vägar, gav p 0,0002 för 213 stenar i 177 grupper.
- **En sten per grupp**, provets huvudmetod nedan för S0 och L1, är inte räknad.
- Gruppmedel med omblandning sten för sten, som ovan, tar inte hänsyn till att stenarna i en grupp ofta vetter åt samma
  håll. Det är skälet till att planen gör ”en sten per grupp” till huvudprov och gruppmedlet till beskrivning.

## Grupperna (bestämt nu)
- **Länkning:** enkel länkning vid 1 000 m mellan provets egna stenar, med `src/spatial_groups.link(xy, 1000.0)` och
  koordinater i SWEREF 99 TM (`places._xy`). Varje sammanhängande mängd är en grupp; en ensam sten är en egen grupp.
  1 000 m är 2 × provens radie 500 m, enligt METHODS.md 1å.
- **Gravfälten:** två stenar inom 500 m från samma gravfält ligger högst 1 000 m isär och hamnar alltid i samma grupp.
  Ingen extra länkning behövs. Koordinater ur `data/rundata.json` (lat, lon), som i rapportbyggaren.
- **S0:** vägen kommer ur registrets text (”X m S om väg”) och är inget registerobjekt, så bara 1 km-länkningen gäller.
  Koordinater ur `utdata/riktning/stenar.csv`.
- **L1:** dessutom länkas stenar vars närmaste gamla väg inom 500 m är samma registerobjekt (samma `fid` i
  `lämningar_sverige_linestring`), enligt METHODS.md 1å. Närmaste linje och dess `fid` räknas som i
  `utdata/riktning/vaglinjer.py` (funktionen `nearest`, samma segment och samma klassning av gamla vägar).
  Antalet grupper med och utan den extra länkningen redovisas.
- **Minst fem grupper** på varje sida som jämförs, annars ”kan inte prövas” (METHODS.md 1å).

## Proven

### G. Gravfälten (tillägg till 2026-11-10-sjalvkontroll-gravfalt.md)
**Data:** samma 657 stenar och samma utfall som i den låsta planen (`utdata/familjens_plats/sjalvkontroll/stenar_sk.csv`).

**Modell:** samma modell (`fit`: utfall ~ i grupp + landskap/län + tidsskikt + lokal täthet [+ gfdens]). Oddskvoten är
densamma. Bara osäkerheten räknas om:
- klusterrobust kovarians per grupp, `sandwich::vcovCL(m, cluster = ~grupp, type = "HC1")`;
- standardfelet för ”i grupp” sätts aldrig under modellens eget;
- p är tvåsidigt mot t med (antalet grupper på den mindre sidan − 1) frihetsgrader. Den mindre sidan är grupperna med
  stenar i grupp, alltså 73 − 1 = 72 i hela materialet.
- **I halvorna** används samma halvor som i den låsta planen (socken för socken inom landskapet). Grupperna är desamma;
  en grupp som delas mellan halvorna blir en grupp i varje halva. Frihetsgraderna räknas inom halvan.

**Prov:**
- **G0:** originalet, alla gravfält med landskap som fast effekt (det publicerade 82 mot 55 procent).
- **G-K1, G-K2, G-K3a, G-K3b:** som K1–K3b i den låsta planen.

**Står sig med grupperna som enhet:**
- **G0:** oddskvot > 1 och p < 0,05, och i båda halvorna oddskvot > 1 med p < 0,05. Det är originalets krav för att
  hålla. G0 är ett eget prov och Holm-korrigeras inte med K-proven.
- **G-K1–G-K3b:** som i den låsta planen, med de klusterrobusta p-värdena. Det kräver oddskvot > 1, Holm-p < 0,05 över
  de fyra, och i båda halvorna oddskvot > 1 med p < 0,05.
- **Det publicerade resultatet står sig med grupperna som enhet** om G-K1, G-K3a och G-K3b alla står sig, enligt den
  låsta planens tolkningsregel.
- Faller G0 eller något av G-K1, G-K3a och G-K3b, gäller den låsta planens regler för ”försvagas” och ”faller”, med de
  klusterrobusta p-värdena.

**Beskrivande:** antalet grupper i varje halva; designeffekten, alltså kvoten mellan den klusterrobusta variansen och
modellens; oddskvotens intervall med det klusterrobusta standardfelet.

### R. Riktningen S0 (tillägg till 2026-11-10-sjalvkontroll-riktning.md)
**Data:** de 120 stenarna med väg i `utdata/riktning/sjalvkontroll_stenar.csv` (kolumnen `vag`). Ristningens riktning och
bäringen till vägen är desamma som i S0.

**Huvudprov, en sten per grupp:**
1. Dra en sten ur varje grupp, slumpvis med lika sannolikhet.
2. Räkna S0:s prov oförändrat på de dragna stenarna: medel-cos mot 999 omblandningar av riktningarna mellan stenarna
   inom landskapet, ensidigt (fler än väntat mot vägen), med p = (1 + antal ≥ observerat) / 1 000.
3. Gör om 1 000 gånger. Slumpfröet tas ur de första 8 tecknen i planens SHA-256, tolkade som ett hexadecimalt tal.

**Håller:** medianen av medel-cos över dragningarna ligger över medianen av det väntade, och medianen av p är < 0,05.
Ingen korrigering, som i den låsta planen (”vart och ett är ett krav”).

**Beskrivande:**
- andelen dragningar med p < 0,05;
- medianen av andelen inom 45 grader;
- gruppmedelstatistiken från ”Känt före låsningen” med 9 999 omblandningar;
- samma huvudprov för S2 (inom län) och S3 (utan flyttade och omresta stenar), med samma länkning inom deras stenar.

### L. Vägarnas linjer L1 (tillägg till 2026-11-10-riktning-vaglinjer.md)
**Data:** de 34 stenarna med en gammal väg i registret inom 2–500 m (`utdata/riktning/vaglinjer_stenar.csv`, `kmr_dist`).
Bäringen till linjens närmaste punkt och ristningens riktning är desamma som i L1.

**Huvudprov:** en sten per grupp som under R, med grupperna enligt Grupperna ovan (1 km och samma registerobjekt).

**Håller:** medianen av medel-cos över medianen av det väntade, och 2 × medianen av p < 0,05. Det är den övre
Holm-gränsen över L1 och L2, eftersom L2 inte är räknat, som i den låsta planen. När L2 är räknat korrigeras L1 med Holm
över L1 och L2 med medianen av p.

**Beskrivande:**
- samma huvudprov utan flyttade stenar (L1b);
- samma huvudprov för L0, dagens vägar;
- gruppmedelstatistiken från ”Känt före låsningen”;
- antalet grupper med och utan länkningen på samma registerobjekt.

## Utanför denna plan
Rapporten om familjens plats har också ett namnparsprov: grannstenar 25–500 m delar personnamn åtta gånger oftare än par
2–10 km isär. Par inom samma grupp är inte oberoende heller där. Det prövas i en egen låst plan och berörs inte här.

## Vad som räknas som avvikelse
- Allt som inte står ovan.
- Om `fid` för L1 inte går att få fram utan att räkna om något annat än `nearest` för de 34 stenarna, görs L1 med bara
  1 km-länkningen, och det redovisas som avvikelse.

## Om ett prov inte håller
Faller ett prov gäller följande. Rättelserna görs först efter Viktors besked.
- **G-K1, G-K3a eller G-K3b faller:**
  - rapportutkastet ”Fyra runstensfynd …” ändrar titeln (”två står”) och avsnitt 5.2 och 5.5;
  - den publicerade rapporten ”Runstenarna samlas i familjegrupper vid gravfälten” (G7k7V4x6soJZ8eTHtHcy, DOI
    10.5281/zenodo.24004794) får en ny version med ändringslogg;
  - texterna som återger resultatet rättas (listade i granskningen 2026-11-19).
- **G0 faller men K-proven står sig, eller tvärtom:** båda utfallen redovisas, och rapporten säger vilket av dem den
  publicerade siffran 82 mot 55 procent vilar på.
- **S0 faller:**
  - rapportutkastets avsnitt 5.4 och 5.5;
  - den publicerade rapporten ”Runstenarna vände texten mot vägen” (GbfyMlDoiJf3azzZgPUQ, DOI 10.5281/zenodo.24004764)
    får en ny version med ändringslogg;
  - texterna som återger resultatet rättas.
- **L1 faller:** rapportutkastet stryker att ristningarna vetter mot de gamla vägarnas linjer, ur sammanfattningen,
  abstract (4), 5.4, 5.5 och diagrammet. Resultatet står inte i någon publicerad text.
- **Håller allt:** rapportutkastet skriver att sambanden håller också med grupperna som enhet, med siffrorna. Svaghet (2)
  i avsnitt 6 skrivs om.

## Utdata
- `utdata/sjalvkontroll_grupper/grupper.py`: grupperna, L1:s `fid` och proven R och L, skrivs till `resultat.json`.
- `utdata/sjalvkontroll_grupper/gravfalt.R`: prov G, skrivs till `gravfalt.json`.
- `resultat.md` med avsnittet ”Avvikelser från planen”, också när det är ”inga”.
