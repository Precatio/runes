# Publicerings- och forskningsplan, november 2026 – december 2027

Byggd på litteraturgenomgången (`utdata/litteraturgenomgang/SYNTES.md`, `FORSKNINGSIDEER.md`, `pastaenden.jsonl`) och,
sedan 10 november 2026, på **frågelistan** `utdata/litteraturgenomgang/Forskningsfrågor_Fornvännen_Futhark.xlsx`: alla
4 555 påståenden samlade till 301 frågor, bedömda efter hur relevant Vitkis bidrag skulle vara för forskningen (22
avgörande, 65 betydande, 193 användbara, 21 begränsade). **Regel: 2027 ägnas åt alla avgörande frågor, samlade i låsta
studier; de betydande kommer 2028; de användbara är reservlistan.** Viktor 2026-11-10: ”gör som du föreslår”.
Datumen är förslag. Viktor publicerar artiklarna; allt annat följer Vitkis regler:
- planen låses (sha256 + commit) innan något räknas;
- varje låst test skrivs upp, också nollresultat (rapport);
- artiklar bara om fynd som håller;
- sv + en;
- korthetsruta;
- varje artikel får ett engelskt Bluesky-inlägg med engelsk delningsbild;
- varje synlig nyhet får en notis;
- **varje forskningsrapport** (Viktor 2026-11-10): Google Scholar-taggar på sidan (finns), PDF:en på vår egen webbplats
  med `citation_pdf_url` (`scripts/rapport_pdf_webb.py` efter varje ny Zenodo-version) och rapportens data som eget
  dataset på Zenodo med DOI, länkat till rapporten;
- **vad vi behåller** (Viktor 2026-11-10, ”JA”): hur varje fråga prövas (mått, data, slumpmodell), påståendedatabasen
  och relevansmotiveringarna stannar hos oss tills studien eller huvudrapporten är publicerad. Varje studies låsta
  analysplan läggs på Zenodo med datum och DOI när studien startar, så att ingen kan ifrågasätta att vi var först.

## Rytm

- **En studie i månaden.** Ordningen inom studien:
  1. Låst plan.
  2. Kontroll av de påståenden studien bygger på mot originaltexten (läsarkontrollen visade att det behövs).
  3. Körning.
  4. Rapport.
  5. Artikel.
- **Två till tre artiklar i månaden:** en ur månadens studie och en eller två ur utkasten som väntar (avsnitt 4).
- **Rapporter:** en per låst studie, i Vitkis rapportserie och på Zenodo med DOI.
- **Korpus fyra gånger om året:** mars, juni, september och december. Varje nummer består av:
  - tre artiklar ur kvartalets studier;
  - Verkstaden, som visar hur långt vi kommit i planen;
  - Metodhörnan;
  - ”Ett påstående från förr, prövat”;
  - **I appen** (Viktor 2026-11-10): en funktion i Vitki förklarad på en sida. Den visar vad funktionen gör med en
    skärmbild, hur man använder den i tre steg, vad den inte kan, och var man laddar ned appen och läser dokumentationen.

## 1. Kalender

Status per rad: planerad → plan låst → körd → rapport → artikel → publicerad. Uppdateras löpande.

| Månad | Studie (låst plan) | Data | Rapport | Artiklar (förslag) | Korpus | Status |
|---|---|---|---|---|---|---|
| **Nov 2026** | Kontrollerna för lerartikeln: bortfall åt båda hållen, åsvägar, sjösänkning, flyttade gårdar, hävd, Malmers dos–respons | Har allt (SGU jord, strandlinje, KMR) | – | **17 nov:** ”Ingen på runstenarna hette Freja” (utkast Ji9gaIAEvK5GNB13yJHv, litteraturkontrollerat 10 nov) · **24 nov:** ”Varför står runstenarna vid lerans kant?” · reserv: ”De nämnde aldrig hemmet” | – | Körd 10 nov: K1–K5 håller (utdata/palm_jordarna/kontroller.md); lerartikeln och Freja-artikeln klara – väntar på Viktors publicering |
| **Dec 2026** | **B. Självkontroller:** 68 % österut utan Ingvar; vattnet mot äldre fornlämningar och strandlinjen ±1–3 m; gravfälten bara daterade; vägen bara gamla vägar | Har; kontroll av SDHK 1314-listan (D12) | **15 dec:** ”Vitki prövar sina egna resultat I” | **8 dec:** ”Var det bara Ingvar? Ett enda tåg bar halva österns övervikt” (utkast heW9W2pFX8bBiB0GCgPD klart 10 nov) · **17 dec:** Norge-artikeln (efter myntkontrollen) | – | Pågår: Ingvar-kontrollen körd 10 nov – försvagat (58 % utan Ingvar, 49–67); tillägget i den publicerade artikeln gjort 10 nov (Viktor GO). Vägen körd 10 nov: håller inom län och utan flyttade, faller mot gamla vägar (28 %, p 0,16) → ändring i rapport + Zenodo v5 väntar på Viktor. Gravfälten körda 10 nov: står sig (alla fyra prov, OR 2,3–2,6). Väglinjerna: plan skriven, historiska kartor inventeras |
| **Jan 2027** | **A1. Flyttade och försvunna stenar** (4 avgörande): hur långt stenarna flyttades (Runor 2020:s 606 ursprungliga platser) och hur många som står där de restes; förluster per jordart (lera och sand/ås); hur många stenar som restes (upptäcktskurva, fångst–återfångst över inventeringarna); kyrkstenarna; spökstenar och dubbletter | Har; KMR:s inventeringsår (D4) | **19 jan:** rapport 0 ”Hundra års runforskning – metod, läsarkontroll och frågelistan” (utkast kgZ9FeICLh8TrrntAfD1 klart 10 nov; före publicering: sätt TODAY i build_rapport0.py till publiceringsdagen, lägg in datasetets DOI) (öppen forskningsagenda: frågorna med titel och varför de spelar roll, de avgörande märkta ”Vitki prövar 2027”; utan metoddetaljer, påståendedatabas och relevansmotiveringar) + frågelistan som dataset på Zenodo · **26 jan:** ”Stenarna som flyttades och försvann” | **12 jan:** ”Stenarna som plogen och grustaget tog” · **26 jan:** ”Hur långt flyttades runstenarna?” | – | Planerad |
| **Feb 2027** | **A2. Registret och nämnaren** (4 avgörande): fornminnesregistrets ojämna täckning och inventeringsår; tomma platser – inga stenar eller ingen som letade (Dalarna, Sevede, ”Uppland bara mest letat”); stenar per gård, by, socken och hundare i stället för per ruta (SDHK 1314); var databasen är tom; befolkning eller minne | D4 (måste vara klar i januari); SDHK 1314 (har); ISOF (D3) | **23 feb:** ”Stenarna vi känner – registret, nämnaren och kartan” | **9 feb:** ”Fanns det inga stenar – eller letade ingen?” · **23 feb:** ett utkast ur avsnitt 4 | – | Planerad |
| **Mar 2027** | **C. Dateringen** (4 avgörande): dateringens kedja av ankare (hur många stenar har en datering som inte bygger på stilen); Ingvars år, 1020 eller 1040; stil mot språk som två klockor; prickarna och åsrunan som klocka; stilgrupp som tid, trakt eller hand | Har; ankarstenar sammanställs ur Rundata; Runor 2020:s termini är oftast schablon | **30 mar:** ”Hur mycket bär stilgrupperna?” | **9 mar:** ”Hur gamla är runstenarna – egentligen?” · **23 mar:** ”Prickarna, åsrunan och tiden” (utkast, med utgivarkontroll) | **Nr 2, 25 mar:** *Det vi inte ser* | Planerad |
| **Apr 2027** | **D. Platserna mot slumpen** (4 avgörande + 5 betydande), ett gemensamt slumptest inom bygd med KMR:s inventeringsår som kontroll: gravar, vägar eller gränser (debatten Klos 2009 – Larsson 2010); bron och vadet; gudarnas platser (kultnamn, kyrkor); tinget; Husby, Tuna och Hov; gränser och råmärken; äldre monument; handelsplatser eller spannmålsbygder. Vägen med väglinjerna och Häradsekonomiska kartan (D13) | Har (KMR); ISOF:s namn (D3); D13 | **27 apr** | **13 apr:** ”Gravar, vägar eller gränser?” · **27 apr:** ”Stod runstenarna vid tinget?” | – | Planerad |
| **Maj 2027** | **E. Korset och bönen** (1 avgörande + 6 betydande): var korset en bekännelse eller en prydnad; när korset nådde varje bygd; österifrån, västerifrån eller söderifrån; uppifrån eller underifrån; hedniskt och kristet på samma sten; tog kvinnorna kristendomen först | Har (Runor 2020:s korstypologi, Rundata) | **25 maj** | **11 maj:** ”Var korset en bekännelse?” · **25 maj:** ”Tegnar i söder, böner i norr” (utkast, efter referenskontroll) | – | Planerad |
| **Jun 2027** | **F. Människorna** (3 avgörande + 8 betydande): reste man sten för arvets skull (lagarna som facit); hur stor del av de döda och gårdarna som fick en sten; var det de rika som reste stenar (Malmers regel); hur många stenar kvinnor reste; trälarna; kvinnorna som flyttade; svearnas lag; stenar över tomma gravar | Har | **29 jun** | **15 jun:** ”Var det de rika som reste stenar?” · **29 jun:** ”Hur många av runstenarna reste kvinnor?” | **Nr 3, 24 jun:** *Människorna och tron* | Planerad |
| **Jul 2027** | **Gränserna** (betydande): götar och svear; Kolmården; folkland och hundare; samma karta eller olika (Kossinnatestet) | Har (histmaps, folklandspolygoner) | – (sommar) | **13 jul:** ”När blev götarna svear?” · **27 jul:** De gamla landen (två delar ur utkasten) | – | Planerad |
| **Aug 2027** | **R. Ristarna** (1 avgörande + 6 betydande): kännarskap mot slumpen – hur ofta har ristarforskarna rätt; ristarens fingeravtryck; Åsmund och Öpir – en man eller en skola; hur långt ristarna reste; samma man på två stenar | Har (attributionsspåret, Runor 2020:s samma-hand-grupper) | **31 aug** | **17 aug:** ”Kännarskap mot slumpen” · **31 aug:** ”Åsmund Kåreson – en man eller en skola?” | – | Planerad |
| **Sep 2027** | **V. Vattnet och landhöjningen** (1 avgörande + 3 betydande): vilket vatten stenarna stod vid (strandlinjen ±1–3 m, vattentyp, 64-procentsfyndet); landhöjningen som klocka; gårdsnamnens ålder; lera, ås eller kärr | **Höjdmodell och vattendrag (D2)** | **28 sep** | **14 sep:** ”Vilket vatten stod stenarna vid?” · **28 sep:** ”Hur högt över vattnet stod stenen? Landhöjningen som klocka” | **Nr 4, 23 sep:** *Platserna* | Planerad (väntar på D2) |
| **Okt 2027** | **S. Stenen och silvret** (betydande): vad en sten kostade och var den kom ifrån (berggrund, 3D-volym, lagarnas öre); silvret och stenarna; följer stenvågorna odlingen (pollen) | **Berggrund (D1)**, lagarnas priser (D11), **skattfynd (D5)**, pollen (D7) | **26 okt** | **12 okt:** ”Vad kostade en runsten?” · **26 okt:** ”Varför sten?” (utkast) – eller ”Silvret och stenarna” om D5 är klar | – | Planerad (väntar på D1, D5) |
| **Nov 2027** | **Huvudrapporten:** *Vad svensk runforskning har missat* v1 – genomgången, frågelistan och studierna 2027 med vad som höll och inte | – | **23 nov:** huvudrapporten (Zenodo, ny DOI) + påståendedatabasen (4 555 påståenden) som dataset på Zenodo | **9 nov:** ”Hundra år av antaganden – vad höll?” | – | Planerad |
| **Dec 2027** | **K. Kyrkorna** (betydande): inmurade stenar får terminus ante quem från kyrkans byggår eller dendro; gravhällarna som bönernas nya hem; träkyrkorna vi inte ser | **Kyrkornas byggår och dendro (D6)** | **14 dec** | **7 dec:** ”Kyrkorna som daterar stenarna” | **Nr 5, 14 dec:** årsnummer, *Ett år av prövade påståenden* | Planerad (väntar på D6) |

**2028 (betydande frågor, i den ordningen):** språkets klockor (ʀ och r, monoftongeringen, epentesen, stavningen –
bygdens, tidens eller ristarens –, skiljetecknen, vers); när runstenarna tystnade och gravhällarna tog över; städernas
stenar; ortnamnens åldersskikt; Gotland; resten av de betydande frågorna i Excel-filen. Vintervägen (begränsad) och
silvret, om D5 dröjer, flyttas hit.

**Hur studierna väljs:** frågelistan (kolumnen ”Studie i planen”) visar vilken studie varje fråga hör till. En låst studie
besvarar flera frågor samtidigt. En fråga som flyttas uppdateras både här och i `bygg_fragelista.py`.

**Om en studie inte håller:** rapporten skrivs ändå. Artikeln byts mot ett utkast ur avsnitt 4. Ordningen kan flyttas om data dröjer (D5, D6).

## 2. Korpus

- **Nr 2, mars 2027 – *Det vi inte ser*.** Stenarna som plogen och grustaget tog; Hur långt flyttades runstenarna?;
  Hur gamla är runstenarna – egentligen? Verkstaden: frågelistan som öppen forskningsagenda. Metodhörnan: vad är
  fångst–återfångst? **I appen:** Luckor i texten – modellen som föreslår förlorade runor, och hur säker den är.
- **Nr 3, juni 2027 – *Människorna och tron*.** Var det de rika som reste stenar?; Hur många av runstenarna reste
  kvinnor?; Var korset en bekännelse? Verkstaden: läsarkontrollen. Metodhörnan: slumpen inom bygden.
  **I appen:** Ristarna, en i taget – varje känd ristares fingeravtryck och modellens förslag (Människorna förklarades redan i nr 1).
- **Nr 4, september 2027 – *Platserna*.** Gravar, vägar eller gränser?; Stod runstenarna vid tinget?; Vilket vatten stod
  stenarna vid? Verkstaden: nya data (höjdmodell, historiska kartor). Metodhörnan: odds och oddskvoter.
  **I appen:** Kartan med de gamla landen, strandlinjen och jordarterna.
- **Nr 5, december 2027 – *Ett år av prövade påståenden*.** Kännarskap mot slumpen; Kyrkorna som daterar stenarna;
  Hundra år av antaganden – vad höll? Verkstaden: huvudrapporten. Metodhörnan: varför vi låser planen.
  **I appen:** Pröva en egen fråga – så testar läsaren själv ett påstående mot hela korpusen, med kontrollerna i R.

Nr 1 förklarade Människorna. Fler funktioner att förklara i senare nummer: 3D-huggspårsanalysen, Namn och släkt, Runbiblioteket, Stenanalys (allt i ett),
Jämför stenar och Forskningsrapporterna.

Varje nummer byggs med `utdata/tidskrift/bygg_tidskrift.py` (sv + en) och läggs upp på /tidskrift.

## 3. Dataplan

| # | Data | Källa och tillgång | Behövs till | Hämtas | Arbete |
|---|---|---|---|---|---|---|
| D1 | Berggrundskarta | SGU, öppna data (vektor) | Stenens proveniens (sep) | jan 2027 | Litet |
| D2 | Höjdmodell och vattendrag | Lantmäteriet markhöjdmodell (öppna data); SMHI:s vattendragsregister | Strandlinje per sten, vadställen, vintervägar (dec), Tunaplatsernas vatten | feb 2027 | Medel (stora filer, bara för bygder med runstenar) |
| D3 | Centralorts- och tingsnamn | ISOF:s ortnamnsregister (CC BY) och vår platser.csv: Husby/Husaby, Tuna, Hov, Sala, Ting-, -vi, Galg-, Kungs- | D1 tinget (mar) | feb 2027 | Litet |
| D4 | Fornminnesregistrets inventeringsår | KMR-fälten först; annars en tabell över fornminnesinventeringen per län och period ur RAÄ:s dokumentation | A1–A2 (jan–feb, avgörande) och alla KMR-test | dec 2026 | Litet till medel |
| D5 | **Skattfynd med fyndplats** | SHM och Myntkabinettet via K-samsök (öppet API); CNS och Hårdhs katalog som kontroll; kodning per socken | Silvret (aug), Norge-artikeln, flera påståenden | mar–jun 2027 | **Stort.** TLS-fel mot K-samsök betyder Viktors VPN: pausa den |
| D6 | Kyrkornas byggår och dendrodateringar | RAÄ:s bebyggelseregister; *Sveriges kyrkor* (Arkivsök); dendrolistor (Lunds dendrolaboratorium); Wase 1995 för Gotland | Kyrkorna (okt), kyrkotester | jun–sep 2027 | Stort |
| D7 | Pollenserier | Neotoma (finns i geografi_kallor/neotoma) | Odlingsexpansion mot stenarna (valfri studie) | har | Litet |
| D8 | 1600-talets bykartor och fosfatkartor | Lantmäteriets historiska kartor; fosfat finns bara i tryck | Flyttade gårdar, lerkanten | 2028 (valfritt) | Mycket stort |
| D9 | Isotoper och aDNA | Publicerade tabeller (Birka, Sigtuna) | Rörlighet (valfritt) | 2028 | Medel |
| D10 | Runor 2020:s fält | Har (runor_2020.json). Kontrollera korstypologi, profilstil, fyndomständigheter, litteraturhänvisningar och första dokumentation; tpq är oftast schablon | A, C, E | dec 2026 | Litet |
| D11 | Landskapslagarnas priser | Utgåvor av landskapslagarna (öre för sten och arbete) | Vad kostade en runsten (sep) | aug 2027 | Litet |
| D13 | Häradsekonomiska kartan och äldre kartor runt stenarna | Lantmäteriets Historiska kartor (historiskakartor.lantmateriet.se): TIFF-blad laddas ned utan inloggning men är inte georefererade; geometriska kartor 1640-tal per by. Inventering per sten: `scripts/historiska_kartor_inventera.py` | Vägen (dec–apr), D | dec 2026 – feb 2027 | Medel (blad + georeferering + blind ritning) |
| D12 | 1314 års sexårsgärd | **Kontrollerad 10 nov 2026:** SDHK 2593 är daterad 1314 i själva brevet och gäller Uppsala ärkestift (Tiunda, Attunda …). Ljungs omdatering till 1279–82 gäller Strängnäs stifts lista, som vi inte använder. Inget publicerat påverkas. | – | klar | – |

## 4. Utkast som väntar

Utkasten är opublicerade. Varje utkast ska först kontrolleras mot de fynd i genomgången som gäller det. Föreslagen månad i
kalendern, eller fri lucka.

| Utkast | Kontroll innan publicering | Förslag |
|---|---|---|
| Varför står runstenarna vid lerans kant? (Palm, jordarna) | Lerkontrollerna (nov) | nov 2026 |
| Varför har Norge bara 66 runstenar? | Myntkvoten ur D5 eller utan den; Palm 1992 krediterad | dec 2026 |
| Prickarna, åsrunan och tiden | Utgivareffekt per SRI-band; studie C | mar 2027 |
| Tegnar i söder, böner i norr | Gräslund 2001-referensen; studie E | maj 2027 |
| Varför sten? | Studien om bergart och berggrund (S) | okt 2027 |
| Den som bryter denna sten (magi, Blekinge del 1) | Santessons påpekande att förbannelseformeln inte är arkaiserande | jul 2027 |
| De gamla landen (Skåne, Attundaland, Gotland, Värend, Möre, Finnveden) | Gränsresultaten (jul) | sommarluckor |
| Ingen på runstenarna hette Freja; Orden höll sig hemma | – | fria luckor |
| De nämnde aldrig hemmet (Utvandrarna); Brittiska | – | fria luckor |
| Tre källor utanför Rundata; Runorna som fattas; Stenar och stavar | – | fria luckor |
| Vem höll i mejseln? Kan statistiken föreslå en ristare? | Vänta: modellen klarar inte Runor 2020:s prov på samma hand; skrivs om efter attributionsspåret | senare |
| Sö 164; Sö 280 (luckartikeln) | Enskilda stenar; ger mindre för kursen mot hela korpusen | senare |

## 5. Risker

- **Data dröjer.** Skattfynd och kyrkornas byggår är de stora osäkerheterna. Silvret och kyrkorna kan byta plats med
  gränserna eller vägarna.
- **Nollresultat.** De blir rapporter, inte artiklar. Utkasten i avsnitt 4 fyller artikelluckorna.
- **Läsarnas fel.** Varje påstående kontrolleras mot originaltexten innan det byggs på (läsarkontrollen: 76 % av
  påståendena rätt).
- **Ett tungt jobb i taget** (16 GB-Macen). Höjdmodellen och skattfynden hämtas en i taget.
