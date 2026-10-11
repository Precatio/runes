# Ändringslogg

Versionsnumren följer [semantisk versionering](https://semver.org/lang/sv/). Mätmetodens version (`groove-N`)
anges separat, eftersom den avgör vilka mätningar som är jämförbara (METHODS.md, avsnitt 1).

## [Ej släppt]

### Mätmetod `groove-5`
- Den automatiska spåranalysen mäter bara spår som känns igen som runor; slinglinjer, ornamentik och möjliga
  sprickor sorteras bort med skäl (METHODS.md 1c, steg 5).
- Rättat: slingband som stängdes av runstavar fylldes och räknades som en enda för bred yta.
- Stenens medelvärden med runan som enhet (ICC); riktvärden 10 runor för att beskriva en sten och 20 för att
  jämföra stenar (`scripts/rune_sample_size.py`).

### Rapporter
- Elva publiceringsformer för stenrapporten: tidskriftsartikel, uppsats, avhandlingskapitel, runologisk utgåva,
  konferensabstract, poster, blogginlägg, pressmeddelande, antikvarisk rapport och dataartikel (METHODS.md 14e).

### Validering av huggspårsanalysen
- Facit-läge i 3D-vyn: alla spår mäts, inget förmärks, forskaren märker runor; `scripts/evaluate_rune_detection.py`
  mäter runigenkänningens precision och träffsäkerhet mot facit.
- `scripts/groove_robustness.py`: samma skanning mätt med ändrat rutnät, lutad normal, annan känslighet och
  förenklad skanning (METHODS.md 1e).
- Antalet igenkända runor jämfört med Rundatas translitterering (METHODS.md 1c).

### Statistik
- Attribueringsmodellen i R korsvalideras också grupperat per socken och härad (rätt ristare 72 % slumpvis,
  68 % på ny socken, 57 % i nytt härad), visat på sidan Statistik (R) och i fynden.
- Ny R-modul `change.R` och fliken Förändring: hur tio språkdrag, skriftdrag och kristna drag förändras över tid och
  skiljer sig mellan landskap, med plats och ristare konstanta (utjämnad tidskurva, rumslig utjämning, ristaren som
  slumpeffekt, omräkning med årtal dragna inom stilgruppens intervall), och om bro- och vägstenar oftare har
  kristna drag (METHODS.md 17).
- Ny R-modul `anonymous.R` och fliken Okända ristare: grupper av stenar utan ristare som liknar varandra lika mycket
  som en ristares stenar, validerade på stenar med känd ristare, jämförda med kända ristare i närheten och med
  arbetsnamn efter typstenens socken för grupper som inte liknar någon känd ristare; stenarna blir fynd i
  Forskningsluckor (METHODS.md 17).
- Nio nya språkdrag: ai i alla ord, ʀ skrivet med r, o-runan för o-ljud, stungen i, u och k var för sig, æftiR eller
  at, skiljetecken och bindrunor (METHODS.md 8). De ingår i attribueringsmodellen, klustringen och seriationen.
- Statistik (R) omgjord för den som inte kan terminologin: varje analys är en fråga med svaret i korthet, ett
  nyckeltal, säkerhetsnivå (säkert, troligt, osäkert), ett förslag till tolkning och vad resultatet inte säger
  (`src/r_explain.py`); översikten sammanfattar och tolkar alla frågor i en helhetsbild med förslag på nästa steg;
  detaljtabeller är hopfällbara, förändringstabellen har en minikurva per drag, och en ordlista samlar alla termer.
- Statistik (R): alla figurer kan förstoras (klick, full storlek, egen flik) och har en förklaring av hur de ska läsas;
  kolumnrubriker, nyckeltal, statusmärken och facktermer (q, Cramérs V, silhuettbredd, oddskvot …) förklaras när man
  hovrar eller trycker; Förändringens stora figurer visas i full bredd.
- Korpusanalyserna återanvänder resultaten från moduler som inte ändrats sedan en tidigare körning, så att en ändring
  i ett skript bara räknar om den modulen och de som bygger på den.
- Kristen bön känns igen även i osäkra läsningar (hakparenteser), som Kristr hjalpi, Guð biargi, Guð lætti och
  Guðs móðir (249 runstenar i stället för 214).

### Statistisk signifikans
- Varje mönster och fynd anger om det är statistiskt säkerställt (q eller p under 0,05, med test), inte säkerställt
  eller inte prövat med signifikanstest; märks tydligt på Statistik (R) – med en egen sektion för säkerställda
  upptäckter (25 av 30 prövade mönster) och en ruta per fråga – och i Forskningsluckor, där fynden kan filtreras.
- Ortografins justering för att den bästa av alla ristare valts görs med max-statistik i stället för Bonferroni,
  som med 459 inskrifter i nollfördelningen aldrig kunde gå under 0,05; nu är 66 av 182 bekräftelser, 20 av 53 nya
  förslag och 3 av 15 motsägelser säkerställda.
- Förklaringskomponenterna (förklaring vid hovring, hopfällbara detaljer, säkerhets- och signifikansmärken,
  förstoringsbara figurer) och ordlistan är gemensamma (`components/Explain.tsx`, `lib/glossary.ts`).

### Granskning av U 1026: sluten modell, namnlösa ristare och bergart
- Modellens förslag: plats, stil och språkdrag ingår i modellen och räknas inte som oberoende stöd; träffsäkerheten
  anges med antal stenar och 95 % konfidensintervall; *starkt* kräver en väl underbyggd träffsäkerhet och inget emot.
- Rundatas "Samma som gjort …" läses in (namnlösa ristarpar); sådana stenar får högst *måttligt*, och modellens förslag
  för de kopplade stenarna och stenens typikalitet för ristaren vägs in.
- Fynd från R-analyserna visar Rundatas material (tidigare "Rundata anger inget material"); en bergart som är lika
  vanlig i landskapet som hos ristaren räknas som neutral.
- Språkdragen räknar bara oberoende drag, listar alla avvikelser och visar både ristarens och landskapets andel.

### 2D-analys
- Automatiska runutsnitt ("Hitta runorna"): runorna som 3D-analysen känt igen klipps ut ur ristningskartan, och i
  andra bilder markerar AI varje runa med ruta och läsning för granskning; de valda sparas som runutsnitt med
  formbeskrivning (METHODS.md 11).

### Granskning av U 92: stil, språkdrag och signifikans
- Stilkontrollen jämför stenens stilgrupp med ristarens kärna (stilgrupper på minst 10 % av stenarna) och anger
  glappet i år enligt Gräslund; minst 25 år gör förslaget kronologiskt problematiskt och slutsatsen högst *svagt*.
- Språkdragen vägs mot övriga stenar i landskapet (sannolikhetskvot per drag) och prövas med ett empiriskt p-värde
  (andel av landskapets stenar som passar ristarens profil minst lika bra); när ristaren föreslagits av en metod
  som bygger på stavningen räknas de inte som oberoende stöd, och ett resultat som inte avgör visas med sin text.
- Ortografins belägg sänks när likheten inte håller efter justering för urvalet, och tolkningen säger då att
  stavningen ensam inte räcker; produktiva ristare får en notering om att de drar till sig förslag.
- Skiljetecken kodas som blandat när inget tecken står för tre fjärdedelar; brøðr räknas inte till o-ljudsorden.

### Jämför stenar
- Huggspåren jämförs runa mot runa (permutation av hela runor) i stället för snitt mot snitt; det samlade testet
  använder de stabila måtten. Referensskala ur mätkorpusen (par med samma och olika ristare), kontroll av
  jämförbarheten och, med signum, ristare, stil, avstånd, stavning och språkdrag (METHODS.md 3).
- 2D-bildsökets miniatyrer fungerar med arkivens TIFF-bilder.

### AI-analyser
- 2D-analysen, den fonetiska analysen och rapporternas AI-avsnitt fungerar med Claude Opus 5.5: strukturerade
  svar via `output_config` i stället för tvingat verktygsval (som modellen avvisar). För stora bilder skalas
  ned före anropet, och ett avklippt eller avböjt svar ger ett tydligt felmeddelande.

### Stenöversikt
- Ny sida Stenöversikt: varje runsten som en punkt efter hur väl sex metoder stöder Rundatas ristare och hur
  starkt det bästa alternativet är (kan vara felbedömd, omstridd, stöds, svagt underlag; nytt eller möjligt
  förslag för stenar utan ristare), med kontroll mot signerade stenar och en profil per sten (METHODS.md 13c).
- Reservationerna på korpussidorna flyttade till dokumentationen.
- Tolkning av varje fynd i Forskningsluckor: belägg, p-värde, språkdrag, bergart, nyare källor och de andra
  metodernas besked vägs samman i ett resonemang med en slutsats (METHODS.md 13d).
- Runologiskt arkiv ombyggt: runornas namn enligt runedikterna, ristare, syften och kända stenar ur data.
- Snabbare: R-kontrollen och Stenöversikten sparas på disk, och servern värmer de långsamma svaren vid start.
- Attribueringsförslag från stenprofilen: ett dokument med alla argument för en ristare att skicka till
  runtextdatabasen, avstämt mot Runor 2020 och Wikidata (METHODS.md 14f).

### Stenens storlek
- Mått (höjd, bredd, tjocklek, runhöjd) för 1 384 vikingatida runstenar ur Kulturmiljöregistret via Runor och
  K-samsök (CC0; `data/stone_dimensions.json`, `scripts/build_stone_dimensions.py`), visade i Inskrifter och
  stenrapporten med stenens plats bland landskapets stenar.
- Storlek mot syfte, statusord, antal personer, textens längd och ristare, prövat inom landskap
  (Forskningsluckor → Storlek och syfte; METHODS.md 9b).

### Protokoll och dokumentation
- Vitki-protokollet för automatisk huggspårsmätning (`PROTOCOL.md`, `src/protocol.py`), utkast: fasta parametrar,
  krav på skanningen, arbetsgång, minsta redovisning; varje automatisk analys kontrolleras mot protokollet.
- Webbsidan Metodik och beräkningar (Dokumentation → Metodik) visar METHODS.md, protokollet och alla moduler,
  skript och R-moduler direkt från koden (`/api/docs`).

### Transparens
- Förteckning över metodens kända brister som visas under varje analyssida, står i varje rapport och sparas i
  proveniensen för varje mätning (METHODS.md 18).

## [2.0.0] – 2026-10-04
- Första versionen under namnet Vitki: 3D-huggspårsanalys, Rundata, ortografisk stilometri, syntes och
  attribuering, mätkorpus, statistik i R, forskningsluckor och rapporter. Mätmetoden har sedan ändrats
  (`groove-2` till `groove-4`, se METHODS.md 1).
