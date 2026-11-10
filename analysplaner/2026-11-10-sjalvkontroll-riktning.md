# Analysplan: självkontroll av ristningens riktning – gamla vägar, länen och stenar som rests om

Skriven och låst 2026-11-10, innan något av proven nedan har räknats. Bakgrund: litteraturgenomgången av Fornvännen
gav tre invändningar mot det publicerade fyndet att runstenarnas ristningar vetter mot vägen (planen
`analysplaner/2026-10-29-ristningens-riktning.md`, robusthetsstegen `analysplaner/2026-10-31-riktning-trappan.md`,
rapporten *Runstenarna vände texten mot vägen*, `utdata/rapporter/rapport_riktning.json`, DOI 10.5281/zenodo.24004764).

## Påståendet som prövas
Publicerat: hälften av ristningarna vetter inom 45 grader från vägen, mot en fjärdedel väntat (H2 håller, Holm 0,0004,
båda halvorna). Invändningarna:
- **(a) Vägarnas ålder.** Vägarna i Kulturmiljöregistret är av blandad och oftast okänd ålder, och vägar och broar
  inventerades först efter 1943 års lag, län för län (Fornvännen 1944). Vägen i KMR-textens "X m S om väg" är oftast
  dagens väg (infartsväg, brukningsväg, traktorväg, landsväg); bara omkring sex av de vägord som står i stenarnas KMR-texter är "gammal" eller "gamla".
- **(b) Stenar som rests om.** Fram till 1941 hade över 311 runstenar lagats och återrests, och en återrest sten kan ha vänts.
- **(c) Vägar som saknas på kartorna.** Skoglund & Lagerås 2002: en förhistorisk väg fanns inte med på 1600- och
  1700-talens kartor.

## Vad som kan prövas och vad som inte kan
- **(a) kan prövas delvis.** K-samsöks KMR-poster för färdväg, färdvägssystem och bro har en fri beskrivning (sedd före
  låsningen; ingen undertyp eller datering i egna fält). Vägar av fornlämningstyp – hålväg, vägbank, vadställe,
  kavelbro – eller med uttrycklig förhistorisk eller medeltida datering kan väljas ut ur texten. Det gör dem *troligen*
  gamla, inte daterade: en hålväg kan vara från 1600-talet. Länet finns för varje väg och, via kommunen i Rundata, för
  210 av de 214 stenarna, så jämförelsen kan göras inom län.
- **(b) kan prövas så långt texterna räcker.** Flyttning och återresning står i KMR:s fält (Beskrivning, Placering,
  Skadestatus, Orientering), i Rundata (placement, other) och i Runor 2020 (original, current, placement,
  original_text, notes). En återresning som ingen skrev ner syns inte.
- **(c) kan inte prövas.** Vi har ingen källa till vägar som saknas både på kartorna och i registret. Det enda vi kan
  göra är att proven under (a) använder vägar som är kända som lämningar i marken (hålvägar, vägbankar), inte ur
  kartorna; men en del KMR-vägar är registrerade efter äldre kartor, och vägar som aldrig registrerats saknas helt.
  Invändningen står kvar som förbehåll.

## Data
- **Stenarna:** `utdata/riktning/stenar.csv` (219 rader från planen 2026-10-29). Sett före låsningen: fem stenar
  förekommer två gånger, eftersom två KMR-poster gäller samma sten (Sö 158, U 31, U 537, U 968, U Fv1971;209) – i alla
  fem med samma riktning. Här en rad per sten (214 stenar); har en av raderna en textväg används den. Med väg: 120
  stenar (inte 123).
- **Vägarna:** `data/raa/lamningar_vag.csv`, hämtad 2026-11-10 med `utdata/riktning/hamta_vagar.py` ur K-samsök
  (KMR): 9 758 färdvägar, 928 färdvägssystem, 3 629 broar och 15 828 vägmärken, med punkt, län, kommun, landskap och
  beskrivning.
- **Gammal väg** (bestämt nu; beskrivningen med gemener):
  typ färdväg, färdvägssystem eller bro, **och** beskrivningen innehåller
  `hålväg|vägbank|vadställe|kavelbro|förhistori|järnålder|vikingatid|bronsålder|medeltid`, **och** den innehåller inte
  `banvall|järnväg|fäbod|militärväg|valv` (järnvägsbankar, fäbodstigar, 1700–1800-talens stenvalvsbroar).
  Vägmärken räknas aldrig (milstolpar och väghållningsstenar, 1600-tal och senare). Sett före låsningen: 6 260 gamla
  vägar i landet; 40 av de 214 stenarna har en inom 500 m (26 inom 300 m, 65 inom 1 km). Klassningen av varje väg skrivs
  i `utdata/riktning/sjalvkontroll_vagklasser.csv` innan bäringarna räknas.
- **Länet:** stenens kommun i Rundata (`municipality`), översatt till län med kommunerna i `lamningar_vag.csv` (det län
  som flest vägposter i kommunen har). Stenar utan län (4 sedda) tas bort i S2.
- **Flyttad eller omrest sten** (bestämt nu): stenen räknas som flyttad eller omrest om något av följande gäller:
  1. Runor 2020 `original = false`;
  2. Runor 2020 har en `current`-punkt (nuvarande läge skilt från det äldsta kända);
  3. korpus `e83202e01a5e6d27` säger `moved != 0` eller `lost != 0`;
  4. texten i KMR (Beskrivning, Placering, Skadestatus, Orientering), Rundata (placement, other) eller Runor 2020
     (placement, original_text, notes) innehåller, utan hänsyn till versaler,
     `återrest|återupprest|rest upp|restes upp|rests upp|nyrest|rests på nytt|restes på nytt|uppsatt|uppställd|lagad|lagades|lagats|reparerad|restaurer|flyttad|flyttades|flyttats|tidigare stått|tidigare stod|ursprungligen stått|ursprungligen stod|påträffad|hittad|hittades|återfunnen|återfanns|låg tidigare|kullfallen|omkullfallen`
     – utom när något av orden `ej|inte|icke|aldrig|knappast|önskar` står bland de tre orden före träffen.
  Sett före låsningen (utan undantaget för nekande ord): 97 av 214 stenar, 49 av de 120 med väg; kvar 71 med väg.
  Listan är vidare än steg 5 i robusthetsstegen (den saknade *flyttad*, *påträffad*, *hittad* och Runor-fälten). Det
  exakta antalet med undantaget redovisas.

## Mått och nollmodell (som H2)
Medelvärdet av cos(ristningens riktning − bäringen från stenen till vägen), mot 9 999 omblandningar av riktningarna
mellan stenarna inom stratum (landskap, om inget annat sägs). Ensidigt (mer mot vägen): p = (1 + antal omblandningar
≥ observerat) / 10 000. Slumpfrö 2026. Andelen inom 45 grader redovisas med. Bäringen räknas till vägpostens punkt i
KMR (en punkt per lämning, inte linjen).

## Prov
**S0 (rättelse).** H2 på 214 stenar, en rad per sten (120 med väg), vägen som i planen 2026-10-29.
**S1 (invändning a, vägarnas ålder).** Bara gamla vägar: bäringen till närmaste gamla väg inom 500 m; stenar utan
gammal väg inom 500 m tas bort (vägarna ur KMR-texten används inte). Kräver minst 30 stenar; annars "kan inte prövas".
**S2 (invändning a, länen).** Vägen som i S0, men omblandningen sker inom län i stället för landskap.
**S3 (invändning b, omresta stenar).** Vägen som i S0, utan alla stenar som räknas som flyttade eller omresta enligt
regeln ovan.

Ett prov **håller** när medel-cos ligger över det väntade och p < 0,05. Ingen korrigering för flera prov: varje prov
är ett krav som fyndet ska klara, och fler prov gör det bara svårare att klara alla.

**Beskrivande (inga krav):** S1 och S3 tillsammans, inom län (troligen omkring 20 stenar; för litet för ett avgörande);
S1 med 300 m och 1 km; S1 utan vägar vars beskrivning nämner runsten eller runristning (där kan vägen vara registrerad
på grund av stenen); S1 bara hålvägar och vägbankar; S0–S3 halva för halva (halvorna från planen 2026-10-29).

## Tolkning (bestämd nu)
- **Alla fyra håller:** fyndet står, och rapporten får skriva att ristningarna vetter mot vägen också när bara vägar av
  fornlämningstyp räknas, när stenarna jämförs inom samma län och när alla stenar som texterna säger är flyttade,
  lagade eller återresta tas bort. Invändning (c) och oskrivna återresningar står kvar som förbehåll.
- **S0 håller inte:** dubbletterna bar fyndet; rapporten och artikeln rättas.
- **S1 håller inte (övriga håller):** fyndet gäller vägen i registret och i dag, inte bevisat den vikingatida.
  Rapporten och artikeln skrivs om till "mot vägen, som vägarna går i dag" och vägarnas ålder läggs fram som öppen
  fråga. Får S1 för få stenar: samma formulering, med skälet "för få kända gamla vägar nära stenarna".
- **S2 håller inte:** skillnader mellan länen (inventeringen eller vägnätet) kan bära fyndet; det dras tillbaka som
  fynd om vikingatiden tills ett bättre prov finns.
- **S3 håller inte:** fyndet kan vara ett spår av återresningarna (1800- och 1900-talens restaurerare ställde stenen
  mot vägen), inte av ristarna; det dras tillbaka som fynd om vikingatiden och redovisas så.
Faller ett prov uppdateras rapporten (ny version på Zenodo), artikeln och IMPLEMENTATIONSPLAN.md i samma tur, och
utfallet redovisas öppet oavsett hur det blir.

## Redovisning
`utdata/riktning/hamta_vagar.py` (vägarna), `utdata/riktning/sjalvkontroll.py`, `utdata/riktning/sjalvkontroll_vagklasser.csv`,
`utdata/riktning/sjalvkontroll.json`, `utdata/riktning/sjalvkontroll_resultat.md`. Inga parametrar ändras efter körningen.
