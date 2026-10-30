# Analysplan: de fornnordiska namnen som inte stod på runstenarna (2026-10-30)

Viktors fråga: många fornnordiska namn lever i dag utan att stå på runstenarna (Helge var hans exempel – det visade
sig stå på 14 stenar och rättade vår namnregel). Varifrån kommer de, och varför lever just personnamnen kvar?
Fortsättning på "Tor föll, hjälten blev dräng" (analysplaner/2026-10-30-namnen-och-orden-som-overlevde.md).

## Material
- **Dagens namn:** SCB:s tilltalsnamn med minst 10 bärare 1999 och 2020 (data/namn/scb_tilltalsnamn.json).
- **Fornnordiskt ursprung, oberoende av våra regler:** svenska Wiktionarys uppslag i Kategori:Svenska/Mansnamn och
  Kategori:Svenska/Kvinnonamn (hämtas efter att planen låsts). Ett namn räknas som fornnordiskt när etymologin härleder
  det ur fornnordiska, fornvästnordiska, runsvenska eller fornsvenska och inte vidare ur latin, grekiska, hebreiska
  eller tyska. Namn där etymologin saknas eller är oklar redovisas för sig. Kodningen görs med en regel och granskas för
  hand; varje namn får sin etymologirad i en tabell.
- **Runstenarna:** alla personnamn på svenska vikingatida runstenar (Rundata, oavsett antal stenar), översatta med
  reglerna i utdata/overlevde/namn.py (inklusive -i → -e för män) och medeltidslexikonet.
- **Övriga runinskrifter:** danska och norska inskrifter och svenska inskrifter som inte är runstenar, samma regler.
- **Mytologin:** namn vars etymologi i Wiktionary nämner en gud, gudinna, Eddan eller mytologin.

## Indelning (varje fornnordiskt namn i en grupp, i denna ordning)
1. **runsten** – finns på minst en svensk vikingatida runsten.
2. **annan runtext** – finns i någon annan runinskrift i Rundata men inte på svenska runstenar.
3. **myt** – finns inte i runtexterna och etymologin nämner gud, Eddan eller mytologin.
4. **övrigt** – resten (sagor, medeltid, senare bildningar ur fornnordiska ord).

## Prövningar (α 0,05, Holm över P2–P4)
- **P1 (beskrivande):** hur många av dagens fornnordiska namn som finns på svenska runstenar, och hur många bärare de har.
- **P2 Återupplivandet kommer ur litteraturen:** namn utanför runtexterna (grupp 3–4) har vuxit mer från 1999 till 2020
  än runstensnamnen (grupp 1). Mått: log((bärare 2020 + 5) / (bärare 1999 + 5)), där ett namn under 10 bärare 1999
  räknas som 0. Mann–Whitney, ensidigt.
- **P3 Gudarna:** mytnamnen (grupp 3) har vuxit mer än övriga fornnordiska namn. Mann–Whitney, ensidigt.
- **P4 Kvinnorna:** fornnordiska kvinnonamn har vuxit annorlunda än mansnamn. Mann–Whitney, tvåsidigt.

## Tolkning, bestämd i förväg
- P2 håller: dagens fornnordiska namnmode hämtar ur sagor och myter, inte ur runstenarna; stenarnas namn lever av arv.
- P2 faller: stenarnas namn och litteraturens namn följs åt.
- Det filosofiska avsnittet ("varför just namnen?") är tolkning och märks som det; det bygger på det vi har visat
  (gudanamnen, kedjan genom medeltidsbreven, namnarvet i SDHK) och säger tydligt vad som inte är prövat.

## Förbehåll, kända i förväg
- Wiktionary täcker inte alla namn; namn utan uppslag finns inte med.
- Etymologierna är Wiktionarys, inte vår forskning; en del är omstridda.
- SCB räknar tilltalsnamn med minst 10 bärare; mycket sällsynta namn syns inte.
