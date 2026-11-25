# Analysplan: skrev och ritade samma hand? Stavning och ornamentik på samma runstenar

Skriven och låst 2026-11-25, innan stavningsmåtten och ornamentmåtten har jämförts med varandra. Del av en forskningsrapport
som bygger på perspektivet att en mätning över hela korpusen med två oberoende mått är ett eget bidrag. Använder inget
facit om händer.

## Frågan
- **Frågan:** hänger det ihop hur en runsten är skriven och hur dess rundjur är ritat, mer än tid och plats förklarar?
- **Varför den är viktig:** runologin har länge diskuterat om text och ornament hade samma upphov, eller om arbetet var
  delat mellan en som skrev och en som ritade. Frågan har mest diskuterats sten för sten.
- **Om sambandet håller med tid och plats under kontroll** talar det för att skrift och bild lärdes och utfördes
  tillsammans, i samma hand eller verkstad.
- **Om det inte håller** talar det för att de kunde ha olika upphov. Utfallet ska redovisas oavsett riktning.

## Data
- **Ornamentiken:** konsensuskoderna ur SRI:s planscher (`data/cache/hander/ornamentik/orn_koder.json`, kodbok v2), de 14
  godkända fälten.
  - **Ornamentlikhet för ett par:** andelen lika värden bland fält som båda stenarna har. Kräver minst tre jämförbara fält.
  - Inga teckningar och inga utvidgningar (Gotland, Öland, Hälsingland, Medelpad) används, så att källan är enhetlig.
- **Stavningen:**
  - **Huvudmått:** den ortografiska profilen (TF-IDF över stavningsdrag, cosinuslikhet). Den räknas som i
    `utdata/nya_ristare/belagg.py`, för stenar med minst tre ord.
  - **Sekundärt mått:** språkdragen (`trait_*`, `cat_*`, `pm_*`), räknade på samma sätt.
- **Tid och plats:** Rundatas stilgrupp (RAK, Fp, Pr1–Pr5), härad (`district`), socken (`parish`) och koordinater
  (korpus 510ebfb3).

## Prov
- **P1, stenpar (huvudprov):**
  - **Paren:** båda stenarna har ornamentlikhet och stavningsprofil, samma stilgrupp och högst 30 km avstånd.
  - **Mått:** Spearmans rangkorrelation mellan stavningslikhet och ornamentlikhet över paren.
  - **Nollhypotes:** stenarnas ornamentkoder blandas om inom samma härad och stilgrupp, 999 gånger (frö 20261125). På så
    sätt behålls bygdens och tidens gemensamma drag.
  - **P1 håller** om korrelationen är större än 0 och ensidigt p < 0,05.
- **P2, ristarna som enheter:**
  - **Ristarna:** de med minst fem signerade stenar som har både ornamentkod och stavningsprofil. Bara signerade stenar
    används, eftersom tillskrivningar delvis bygger på samma drag.
  - **Profiler:** varje ristare får en stavningsprofil (medel av stenarnas vektorer) och en ornamentprofil (andel av
    varje värde per fält). Avstånd: 1 − cosinuslikhet.
  - **Provet:** partiellt Mantel-test (Spearman) mellan stavningsavstånd och ornamentavstånd, med avståndet mellan
    ristarnas medelpositioner borträknat. 9 999 omblandningar av ristarna.
  - **P2 håller** om p < 0,05 och sambandet är positivt.
  - Med färre än 8 ristare redovisas P2 bara beskrivande.
- **P3, inom en enda stilgrupp:** som P1, men bara par där båda stenarna är Pr4 (den största gruppen). P3 håller på samma
  sätt.
- **Beskrivande:**
  - P1 med språkdragen i stället för stavningen;
  - P1 utan par från samma socken;
  - korrelationen per stilgrupp;
  - för P2 de ristare vars plats i stavningen och plats i ornamentiken skiljer sig mest (rang efter rang).

## Vad som inte skrivs
- **Ett samband är inte bevis för att en enda person gjorde båda delarna.** En verkstad eller skola ger samma mönster.
- **Kontrollen är inte perfekt.** Den håller härad och stilgrupp konstanta, men inte socken eller årtionde, så en del av
  sambandet kan vara lokal tradition. Därför finns analysen utan par från samma socken.
- **Ornamentmåttet är grovt.** Flikarna saknas ofta, vilket gör sambandet svagare än det kan vara.
- **Uppland dominerar.** Resultat gäller främst Uppland om inte annat visas.

## Utdata
`utdata/graslund/skrev_ritade.py` → `skrev_ritade.json` och `skrev_ritade.md`.
