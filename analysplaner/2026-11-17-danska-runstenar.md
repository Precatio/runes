# Analysplan: de danska runstenarna – tron, platsen och resandet

Skriven och låst 2026-11-17, innan proven nedan har räknats. Underlag för en populärvetenskaplig fokusartikel om
de danska vikingatida runstenarna, som artikeln om Norge (Viktor 2026-11-17: "Vad utmärker dem, är fler hedniska, har
fler ett hedniskt budskap? Vad skiljer i var de står och hur de är resta?"). Sverige är huvudfokus (stående regel);
Danmark räknas här för sig och blandas aldrig in i de svenska talen.

## Känt före låsningen
- Rundata har 239 danska vikingatida runstenar enligt `nordic.is_runestone` (DR-signum: Jylland 106, Skåne 62,
  Bornholm 39, öarna 32) och 2 321 svenska. Fälten finns för: plats och socken 239, material 210, koordinat 173,
  placering 117 (ofta ett museum), ristare 50, korsform 28. Rundatas stil är för de danska stenarna oftast RAK (182),
  vilket är en standardkod och ingen datering (Tor-artikeln 2026-10-28). Tiden tas ur Rundatas danska perioder.
- **Tro:** Tor-artikeln ("Tor svarade korset – och tystnade", publicerad 2026-10-28) räknade hedniska eller rituella
  markörer: Danmark 8 av 239, Sverige 7, Mantel–Haenszel-oddskvot omkring 5 (p 0,004) vid samma tid; alla danska före
  1050. Det provas inte igen här, det redovisas.
- **Textmönster i appens Nordenvy** (`src/nordic.py`, PATTERNS): kristen text, bön, hednisk, titlarna þegn och drængr,
  ordet kumbl, bro, utlandsfärd, arv, signatur, stungna runor och monoftong har visats per land och period i appen
  sedan oktober. Verben *satte* och *lät resa* användes i artikeln "Västgötarna skrev som danskarna" (2026-10-14), och
  *lät resa* i Norgeplanen (Danmark omkring 12 %, Sverige 34 %, grovt). Dessa mönster är alltså sedda och provas inte
  som nya; de redovisas beskrivande (del A).
- **Inte räknat:** var stenarna står i dag (kyrka, museum, i landskapet), om inskriften nämner ett större monument än
  stenen, kvinnor som reser stenen, kungar i texten, materialet per land.

## Data
- Stenarna: Rundatas vikingatida runstenar enligt `nordic.is_runestone`, land enligt `nordic.land_of`: Danmark (DR,
  inklusive Skåne, Blekinge, Halland och Bornholm, som hörde till det danska riket), Sverige (alla svenska landskap).
  Delområden i Danmark: `nordic.realm_of` (Jylland, öarna, Skåne, Bornholm).
- Läsbar text: `nordic.features(rec)` är inte None.
- Tid: `nordic.year_of` och `nordic.bin_of`, tre skikt: före 1000, 1000–1050, 1050 och senare. Rundatas danska period
  "kristen efter-Jelling" är innehållsbestämd och hamnar i samma skikt som "efter-Jelling" (1000–1050); den används
  aldrig som egen period. Stenar utan år räknas bort ur proven, och antalet redovisas.

## Del A. Det kända, beskrivande
För mönstren kristen, bön, hednisk, titel, kumbl, bro, utlandsfärd och arv (`nordic.patterns`) och för verben
*satte* (placed), *reste* (raised) och *lät* (had … raised/made) (`nordic.features`): andel per land och tidsskikt med
Wilson-intervall, och Mantel–Haenszel-oddskvoten Danmark mot Sverige över tidsskikten med p-värde. Inga slutsatser
utöver "syntes redan i appen; med tiden hållen lika är skillnaden …". De hedniska stenarna listas en och en, med
signum, plats, period och vad som är hedniskt (Tor-artikelns kodning).

## Del B. Prov (nya, tvåsidiga)
Alla tre: Danmark mot Sverige, Mantel–Haenszel över tidsskikten (`nordic.mantel_haenszel`), tvåsidigt p. Holm över
B1–B3. Ett prov **håller** om Holm-p < 0,05. Det är **robust** om riktningen är densamma när Jylland och östra
Danmark (öarna, Skåne och Bornholm) jämförs med Sverige var för sig (ingen p-gräns, bara riktningen). Varje dansk
träff i B1–B3 listas och läses för hand innan resultatet används; fel kodning rättas inte i efterhand utan redovisas.

**B1 Kyrkan.** Stenens plats i dag är en kyrka eller kyrkogård. Kodning: Rundatas `place`, `placement` eller `other`
matchar `kyrk|kirke|kirche|vapenhus|våbenhus|kapell|kapel|kyrkogård|kirkegård|kirchhof|kirkedige`. Stenar vars
placering är ett museum räknas i nämnaren (deras fyndplats är okänd i fältet), och andelen museistenar redovisas per
land.
**B2 Monumentet.** Inskriften säger att minnesmärket är mer än stenen: ordet kumbl (`NORM_KUMBL`), eller
översättningen har `\bmounds?\b|\bthese stones\b|\bthose stones\b|\bboth stones\b|\bstone-setting|\bship\b[^.;]{0,20}\b(setting|stones)\b|\bmonuments?\b`.
Bara läsbara stenar.
**B3 Kvinnor som reser.** Minst en av resarna är kvinna enligt `src/people.py` (`people.stone`, lexikonet byggt på
alla runstenar som i appen). Bara stenar med minst en resare med bestämt kön.

## Del C. Beskrivande, inga prov
- Var stenarna står i dag: kyrka (B1), museum (`placement` med museum/museet/Museum/samling), annat; per land och per
  danskt delområde.
- Material: andel granit, sandsten och annat per land (Rundatas `material`).
- Kungar: stenar där översättningen har `\bking\b` eller normaliseringen `konungr|kunungr`, listade per land.
- Danska delområden: B1–B3 och de hedniska stenarna per Jylland, öarna, Skåne och Bornholm (antal och andel, inga prov).

## Tolkning (bestämd nu)
- B1 håller: de danska stenarna står oftare (eller mer sällan) vid kyrkor än de svenska. Det säger något om stenarnas
  senare öden, inte om var de restes. Danmark saknar en motsvarighet till SRI:s fyndhistorik i vår data, så den
  ursprungliga platsen prövas inte.
- B2 håller med Danmark högre: de danska stenarna ingick oftare i större minnesmärken (högar, skeppssättningar,
  kumbl), som inskriften själv nämner. Litteraturen om Jelling, Glavendrup och Bække ger exemplen.
- B3 håller: kvinnor reste stenar oftare (eller mer sällan) i Danmark än i Sverige vid samma tid.
- Ett prov som inte håller redovisas som att skillnaden inte går att visa med Rundatas danska stenar; med 239 stenar
  säger ett negativt utfall lite.
- Del A och C är beskrivande. Förklaringar (kungamakten, Jelling, kristnandet) tas ur litteraturen med sidhänvisningar
  och presenteras som tolkningar, inte som resultat.
