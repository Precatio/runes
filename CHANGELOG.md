# Ändringslogg

Versionsnumren följer [semantisk versionering](https://semver.org/lang/sv/). Mätmetodens version (`groove-N`)
anges separat, eftersom den avgör vilka mätningar som är jämförbara (METHODS.md, avsnitt 1).

## [Ej släppt]

### Stenarna i sitt landskap: nya källor
- Lämningar ur Kulturmiljöregistret (Riksantikvarieämbetet, via K-samsök): gravfält, högar, färdvägar, broar,
  fornborgar och hamnanläggningar, omkring 53 000 poster (`scripts/fetch_raa_remains.py`). Den nya korpusanalysen
  `remains.R` jämför stenarnas avstånd till lämningarna med slumpvisa punkter i samma trakter och prövar om närheten
  skiftar med tiden, med kristna markörer och för brostenar, i båda halvorna av korpusen. Flyttade stenar (vid kyrkor, i
  museer) räknas inte. Resultaten visas under Geografi i Statistik och som mönster i Forskningsluckor: 61 % av stenarna
  står inom 500 m från ett gravfält mot 21 % av slumppunkterna, lika ofta före som efter 1050 och för kristna stenar.
  Att brostenar står nära färdvägar håller inte i båda halvorna och är en indikation.
- Dåtidens strand: avståndet till vatten prövas också mot en modellerad strandlinje omkring år 1000 (dagens höjd under
  landskapets landhöjning, terrängmodell med omkring 300 m upplösning), med samma slumppunkter som för dagens vatten.
  Närheten blir tydligare (3,6 mot 5,3 km; i Uppland kvoten 0,64 → 0,53) och redovisas som mönster att pröva.
- Helhetsbilden i Statistik har ett stycke om landskapet, och själsbönen på brostenar räknas inte längre som nytt
  mönster när den inte håller i båda halvorna.
- Landningssidan har ett nytt avsnitt om de nya källorna och vad de tillför.

### Månadens fynd (blogg)
- En blogg på /blogg med ett inlägg i månaden om de mest intressanta mönstren och fynden. Inläggen skrivs och
  publiceras för hand i Admin; knappen "Utkast från månadens fynd" fyller i ett utkast med de mönster som är nya eller
  har ändrat status sedan förra publicerade inlägget, månadens största förskjutning i mönsterkartan och en engelsk
  version ur ordlistan. Inläggen kan ha en egen engelsk version.
- Inläggen ligger i Firestore-samlingen `posts`, som bara servern läser och skriver; regeln för webbläsarna är
  oförändrad (stängd), så ingen ändrad regel behöver driftsättas.

### Mönsterkarta
- Kartan öppnar med en mönsterkarta: sexkanter färgade efter hur stor andel av stenarna i området som har ett mönster –
  tro (kristna, hedniska eller rituella markörer, utan religiösa markörer, bön, själsbön, kors), skrift (stungna runor,
  monoftong, o-runan, r för ʀ, signatur) eller innehåll (bro, utlandsfärd, arv). Mönstret väljs med knappar, kartan kan
  delas i före och efter omkring 1050 och andelarna per landskap finns som tabell (METHODS.md 13e).
- Inskrifterna med filter ligger under fliken Punkter, med filtren fällda tills de behövs.
- Hedniska markörer är få: 7 av 2 318 runstenar (Torsåkallan, vígi-formler, förbannelser, alu, Tormotiv). Den stora
  gruppen är stenar utan religiösa markörer (1 203).

### Försiktiga påståenden, djärva hypoteser
- Varje mönster i Forskningsluckor och Statistik har nu tre delar: vad vi ser, en hypotes om vad det kan betyda och hur
  hypotesen kan prövas. Förbehållen ligger i en fällbar ruta.
- Upptäckt med Benjamini–Hochberg, bekräftelse med Holm och prövning i två halvor av korpusen (uppdelad per socken, alla
  stilgrupper i båda). Märket "Håller i båda halvorna" visar tydliga mönster. Signerade stenar används inte som facit,
  eftersom signaturerna är sena.
- Mindre stränga regler där de var för hårda: generationsskifte i stället för krav på trend inom ristare, utan ändgrupper
  som information, textlängd utan bro- och bönefraser, landskap utanför U/Sö när förskjutna dateringar håller, små
  effekter som mönster. Ny grupp "Indikationer" för idéer med förbehåll.
- Rune granskar som en kritisk vän: fel, för säkra ord och hypoteser hålls isär.

### Engelsk version
- Hela appen finns på engelska: språkknappen (i menyn och på landningssidan) översätter allt som visas –
  gränssnittet, forskningstexterna, fynd, mönster, tolkningar och tabeller – mot en ordlista med drygt 4 600
  meningsmallar. Siffror, ristare och orter hålls utanför mallarna och språkdrag och bergarter översätts var för
  sig, så att samma mall räcker för alla stenar. Svenskan är originalet; runtext och källtext översätts aldrig.
- Rapporterna (stenrapporten i alla publiceringsformer och beslutsunderlaget) skrivs på engelska när språket är
  engelska. Rune svarar på det valda språket. Språkvalet sparas.
- Verktyg för att hålla ordlistan aktuell när texter ändras (METHODS.md 14g, scripts/README.md).

### Gränssnitt
- Snabbknappen "Generera akademisk rapport för aktuellt arbetspass" i toppraden är borttagen, liksom avsnittet
  "Arbetsgång" på landningssidan. Kontoinställningarna har ett fält för e-post (förvalt kontots adress), och
  författarnamnet är inte längre förifyllt med grundarens namn för nya användare.
- Rättat: Rune-uppslaget tolkade andelar som "Vg 84 %" som signum (Vg 84).

### Beslutsunderlag om attribuering
- Förslaget till omprövning i Stenöversikt är nu ett fullständigt beslutsunderlag: slutsats och rekommendation först,
  varje metod förklarad (vad den jämför, vilka data, vad talen betyder och hur ofta den har rätt – t.ex. hur ofta en
  ristare med modellens sannolikhet var den rätta i korsvalideringen), den prövade ristaren mot Rundatas, språkdrag drag
  för drag, andra kandidater, vad som skulle avgöra frågan, källkritik, ordlista och bilaga (METHODS.md 14f).
- Ärlig rekommendation: *starkt* ger förslag, *måttligt* granskning, *svagt* ingen ändring; en signerad sten får
  aldrig ett förslag om en annan ristare (tidigare kunde t.ex. U 287, signerad av Öpir, få ett förslag om Fot 2 med
  sannolikheten 0,19).
- Rättat: bedömningen i beslutsunderlaget räknade modellen och ortografin två gånger (i styrkan och som andra belägg)
  och område och stilgrupp som oberoende fast de ingår i modellen; *starkt* kräver nu att modellen och ortografin
  (statistiskt säkerställd) båda pekar på ristaren och att inget talar emot (51 → 4 av 1 003 alternativ).
- Tydligare text: hur beläggen hänger ihop, stenar med flera ristare, träffsäkerheten också när hela socknar hålls
  utanför, att sannolikheten för stenar utan ristare inte är korsvaliderad, och bergartens jämförelse ("inte tydligt
  vanligare" i stället för "lika vanlig").
- Granskning av U 735 (Rune): ett svagt underlag är ett internt arbetsunderlag, inte ett förslag att skicka; när
  jämförelsen talar för Rundatas ristare heter dokumentet "Prövning av … : Rundatas attribuering till … stöds".
  Det som talar för Rundatas ristare framför den prövade räknas och redovisas (modellen föredrar den, språkdragen
  stöder den signifikant, den har stenar mycket närmare, stenens stilgrupp hör till dess kärna). Runor 2020 räknas
  inte som oberoende belägg när den anger samma ristare som Rundata. Hypotesens ursprung anges. Den samlade styrkan
  kallas inte stark när modellen inte stöder förslaget eller stavningslikheten inte är signifikant. Jämförelsestenarna
  är stenar där ristaren är ensam ristare och som finns kvar; närmare stenar med flera ristare eller som är försvunna
  nämns med skäl. Bara de begränsningar som gäller dokumentet. Kontaktraden får e-post ur kontoinställningarna.
- Ortografins förstaval räknas fullt i Stenöversiktens styrka bara när det leder tvåan med minst 0,05 i likhet
  (U 735: Öpir 1 0,66 mot Balle 0,64 räknas som oavgjort). En stilgrupp stämmer med ristaren bara om den hör till
  kärnan (minst en tiondel av stenarna); en ovanlig stilgrupp inom kärnans tidsram avgör inte. Tidsramen för en
  ristares stilgrupper är kärnans, i alla avsnitt. Språkdragen redovisas som för, emot och neutrala, och andelar på
  färre än tio inskrifter markeras som osäkra. En ristare som nämns två gånger i samma inskrift räknas en gång.
  Kontrollen på signerade stenar: falsklarmen (alternativ ≥ 0,4 för en signerad sten) minskar från 57 till 33 av 246;
  *omstridd* 49 → 26, *kan vara felbedömd* 15 → 9.

### Granskning av R-fynden (Rune, 2026-10-11)
- Tredje omgången: "Säkerställt" heter nu "Signifikant" i hela appen, och p-värdet förklaras som hur ovanligt ett så
  tydligt resultat vore utan ett verkligt samband – inte som sannolikheten att resultatet är sant. Landskap med färre
  än tio stenar från mittperioden (stenar vars stilgrupp omfattar år 1050) får ingen skattning utan redovisas som
  otillräckligt underlag. Formelvalets CA-dimension beskrivs i klartext (stenar utan bön mot stenar med bön).
  Sambandet själsbön–brostenar märks efter det kontrolltest som inte håller (textlängden), inte efter huvudmodellen.
  Avståndet till vatten får förbehåll för vikingatidens högre strandlinje och för parstenar.
- Andra granskningsomgången (stavning, runor, böner, broar, geografi, seriation, formelval): ordbaserade mått och
  rätt nämnare i stället för "minst en på stenen" (monoftongen per æi-ord och lexem, stungna runor per runa bland ord
  där de kan förväntas, ʀ och omvänd stavning, åsrunan för /o/ och för ą, 'och' som auk/uk/ok/ak, æftiʀ för sig);
  kontroller med bara signerade stenar, inom ristare, utan ändgrupperna, med textlängd, bevarade inskriftsslut och för
  Uppland och Södermanland var för sig; toppar vars intervall når periodens kant tolkas inte; flera toppar samma år
  märks som möjlig artefakt; landskapsjämförelser bara mellan landskap med tillräckligt underlag, alla landskap med
  intervall och märket för det visade paret; ristarnas koncentration också mot samma stilgrupp, samma härad och på
  signerade stenar (inte mer lokala än häradet); seriationen utan kors, utlandsfärder och föränderliga drag, inom
  härad och inom ristare; formelvalet med signerade stenar, utan själsbönen och på bevarade slut; stavningsavståndet
  inom Uppland, på stenar utan ristare och med tiden konstant. Själsbönen räknar inte längre brostenarnas avsiktsfras
  (fyrir and hans).
- Märket "Säkerställt men osäkert" när ett säkerställt test hör till en indikation, en svag effekt, ett cirkulärt
  resultat eller en måttlig/svag tolkning. Språkdragstabellen visar landskapets andel och vilka drag som inte räknas.
- Landskapsjämförelserna: q justerat med Holm över alla drag (tidigare p), observerade andelar i stenar från
  mittperioden bredvid modellens skattning, antal attribuerade ristare per landskap och samma test utan ristareffekten.
  Spridningsförlopp anges bara för drag som stadigt ökar eller minskar; annars är jämförelsen en ögonblicksbild.
  Jämförelser utanför Uppland och Södermanland, med få ristare eller få stenar, är *indikationer*. Kristen bön skiljer
  sig inte säkerställt mellan landskapen efter justeringen.
- Förbehållen följer dragets typ (stavning, ordval, runformer, formler, ornamentik) i stället för samma text för alla;
  förbehållet om ristarna nämner formulärbruk och ornamentik och att justeringen kan snedvrida åt båda hållen.
- Toppår anges med 95 % intervall (koefficientdragningar och omräkningar med nya årtal), aldrig som ett exakt år.
- Avstånd till vatten prövas mot en lokal nollmodell: slumpvisa punkter inom 5 km från runstenar (där folk bodde och
  rörde sig); jämförelsen mot hela landskapet finns kvar som kontroll. Resultatet håller (4,2 mot 5,3 km).
- Mönster som är kända i forskningen (stungna runor, signaturer, åsrunan, kristna formler, monoftongeringens geografi,
  brostenarnas själsböner, vattennärhet) märks *bekräftar*; säkerställda men små förändringar (under 10
  procentenheter) blir *svag effekt*, och förändringar som inte håller i minst 8 av 10 omräkningar *indikation*.
  Kors är en del av ornamentiken och därmed inte oberoende av dateringen (*begränsning*).
- Klustringens silhuett prövas mot omblandade data och ristarnas sammanhållning mäts direkt (i stället för bara
  justerat Rand-index).
- Korpusdimensionerna prövas mot tiden icke-linjärt (eta² mot stilgrupp, daterade stenar) och ristarens eta² mot
  omblandade etiketter: dimension 1 följer ristaren (27 %, slumpnivå 6 %) mer än tiden (6 %).
- Släktrelationerna före och efter 1050 prövas inom landskapen (Cochran–Mantel–Haenszel): skillnaden för 'broder'
  och 'partner/kamrat' försvinner – de sena stenarna är till 94 % uppländska.
- De okända ristargrupperna prövas utan tidsberoende drag (renhet 69 % även då; grupperna återkommer till 58 %), och
  texten anger entydigt att arbetsnamnen är appens etiketter för nya grupper.

### Konton, admin och säkerhet inför publicering
- Servern kontrollerar Firebase-inloggningen (ID-token, avstängda och återkallade konton) med Firebase Admin SDK
  (`api/auth.py`). Grundaren anges på servern med `ADMIN_UIDS` eller `ADMIN_EMAILS` – ingen inloggning står i koden.
- Admin-sidan (bara för grundaren): antal registrerade, nya och aktiva konton, registreringar per månad, avstängning
  och återöppning av konton, och meddelanden i appen till alla eller till ett konto (klockan i sidhuvudet).
- Avstängda konton kan inte logga in, deras inloggningar återkallas och Firestore-reglerna nekar dem direkt
  (`banned/{uid}`); meddelanden kan bara skrivas av servern.
- Rapporter: Stenrapport (fullständig) är öppen för alla; korpusrapporten och de övriga publiceringsformerna är bara
  för grundaren, också på servern.
- Serverns egna AI-nycklar används bara med `ALLOW_SERVER_AI_KEYS=1` (lokal utveckling); på en publik server använder
  varje användare sin egen nyckel. `.env` skriver inte längre över serverns miljövariabler.

### Mobil och surfplatta
- Sidomenyn är en utfällbar meny under 1024 px, öppnas med menyknappen i sidhuvudet och stängs när man väljer en
  sida; sidhuvudet, chatten, marginalerna och kartans filter är anpassade för små skärmar. Alla sidor är kontrollerade
  i 390 och 820 px bredd utan sidledsskroll.

### Karta
- Nya filter: fritext i inskriften (translitterering, normalisering, översättning, plats), landskap, innehåll (de nio
  kategorierna), ristarstatus, material, kors, språkdrag med värde, status i Stenöversikt och bara svenska
  vikingatida runstenar.
- Färg efter ristarstatus, material, innehåll, språkdrag eller status i Stenöversikt, utöver stilgrupp och period.
- Aktiva filter som etiketter, fördelning per landskap, kartan zoomar till det som syns, filtren sparas i adressen
  (delbar länk) och det som syns kan laddas ner som CSV.

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
- Statistiska modellens förslag har ett signifikanstest (max-statistik mot de sannolikheter felaktiga ristare får
  i korsvalideringen, Benjamini–Hochberg); *starkt* kräver q under 0,05 (METHODS.md 13d).
- Rättat: avstämningen mot Runor 2020 upprepade samma text i skälen varje gång Forskningsluckor laddades.
- Mönstren i hela korpusen visas som kort i två kolumner med filter (att pröva, bekräftar, begränsningar,
  säkerställda) och förklaring per mönster.
- Varje mönster och fynd anger om det är statistiskt säkerställt (q eller p under 0,05, med test), inte säkerställt
  eller inte prövat med signifikanstest; märks tydligt på Statistik (R) – med en egen sektion för säkerställda
  upptäckter (25 av 30 prövade mönster) och en ruta per fråga – och i Forskningsluckor, där fynden kan filtreras.
- Ortografins justering för att den bästa av alla ristare valts görs med max-statistik i stället för Bonferroni,
  som med 459 inskrifter i nollfördelningen aldrig kunde gå under 0,05; nu är 66 av 182 bekräftelser, 20 av 53 nya
  förslag och 3 av 15 motsägelser säkerställda.
- Förklaringskomponenterna (förklaring vid hovring, hopfällbara detaljer, säkerhets- och signifikansmärken,
  förstoringsbara figurer) och ordlistan är gemensamma (`components/Explain.tsx`, `lib/glossary.ts`).

### Forskningsluckor för den som inte kan terminologin
- Samma upplägg som Statistik (R): inledning på vardagsspråk med "Så läser du sidan" och ordlista, frågekort i stället
  för flikar (ny fråga: var saknas uppgifter?), och för varje fråga svaret i korthet, nyckeltal, förslag till tolkning
  och vad resultatet inte säger – framräknat ur data. Alla kolumnrubriker har förklaringar (ⓘ).
- Gemensamma komponenter för sidinledning, frågekort och svar (`components/Explain.tsx`).
- Stenöversikt, Jämför stenar, Syntes och Mätkorpus: inledning på vardagsspråk med läsanvisning och ordlista,
  förklaringar på mått och kolumner; Stenöversikt får en svarsruta med tolkning och kontrollen mot signerade stenar,
  Jämför stenar ett märke för om skillnaden i huggspår är statistiskt säkerställd.
- Tolkningens slutsats (starkt, måttligt, svagt, bekräftelse, redan känt, metodfel) syns direkt i fyndlistan, med
  filter per nivå; tidigare bara när raden öppnades.
- Fyndtabellen har fyra kolumner i stället för tretton (Sten, Fynd, Tolkning, Uppskattning) och skrollar inte i
  sidled; nyare källor, bergart och språkdrag visas som etiketter under fyndet, belägg, nyhet och relevans under
  uppskattningen, och en meny sorterar efter alla de tidigare kolumnerna.

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
- Landningssidan uppdaterad: arbetsgången i Fullständig stenanalys, Statistik i R, Stenöversikt och tolkningarna i
  Forskningsluckor, principerna om validering, signifikans och regional baslinje, Claude som standard för AI-stegen
  (egen nyckel), fler källor och upphovsangivelsen i licensen.
- Appen heter Vitki, utan "AI": AI är ett valfritt hjälpmedel för bilder och löptext, inte kärnan (mätning,
  statistik och validering görs utan AI). Firebase-projektets tekniska id (`vitki-ai`) är oförändrat.
- Appens adress är https://vitkirunor.se: rapporterna, korpusexporten och CITATION.cff hänvisar dit och till
  källkoden på GitHub (`src/about.py`).

### Transparens
- Förteckning över metodens kända brister som visas under varje analyssida, står i varje rapport och sparas i
  proveniensen för varje mätning (METHODS.md 18).

## [2.0.0] – 2026-10-04
- Första versionen under namnet Vitki: 3D-huggspårsanalys, Rundata, ortografisk stilometri, syntes och
  attribuering, mätkorpus, statistik i R, forskningsluckor och rapporter. Mätmetoden har sedan ändrats
  (`groove-2` till `groove-4`, se METHODS.md 1).
