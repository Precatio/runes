# Analysplan: ristningens riktning mot vägens linje – dagens vägar, registrets gamla vägar och 1800-talets karta

Skriven och låst 2026-11-10, innan något nedan har räknats: ingen bäring till en väglinje, ingen närmaste väg och ingen
jämförelse med ristningarnas riktning. Viktor 2026-11-10 (via samordnaren): provet ska köras innan något i
vägrapporten rättas.

## Varför
Självkontrollen (`analysplaner/2026-11-10-sjalvkontroll-riktning.md`, resultat i
`utdata/riktning/sjalvkontroll_resultat.md`) gav: S0, S2 och S3 håller, men S1 – bara vägar som troligen är gamla –
håller inte (40 stenar, 28 procent inom 45 grader, p = 0,16). S1 mätte bäringen till *en punkt* per registrerad väg,
inte till vägens linje. Redan den publicerade raden "bara registrerade färdvägar och vägmärken" (också punkter) var
svag (28 procent), medan vägarna ur registrets text, där inventeraren angav vägens håll från stenen, gav 62 procent.
S1 kan därför inte skilja mellan att de gamla vägarna gick någon annanstans och att punktbäringen är för grov. Här mäts
bäringen från stenen till närmaste punkt på vägens **linje**, i tre källor.

## Data
- **Stenarna:** de 214 stenarna med en riktning i `utdata/riktning/stenar.csv`, en rad per sten som i självkontrollen
  (vid två rader den med väg ur registrets text). Ristningens riktning som i S0–S3 (16 väderstreck, utan gon-rättelsen).
  Läget: Rundatas koordinat, omräknad till SWEREF 99 TM (`src/places._xy`).
- **Flyttade eller omresta:** kolumnen `flyttad` i `utdata/riktning/sjalvkontroll_stenar.csv` (regeln i
  självkontrollen; 91 av 214 stenar).
- **L0, dagens vägar (kalibrering):** OpenStreetMap, Geofabriks Sverigeutdrag (`sweden-latest-free.shp.zip`, skiktet
  `gis_osm_roads_free_1`, © OpenStreetMaps bidragsgivare, ODbL), hämtat en gång och sparat med datum och SHA-256 under
  `/Volumes/2TB/Antigrvity/Runes/geografi_kallor/osm/`. Bara vägarna inom 1,5 km från någon sten tas ut (ogr2ogr med
  rumsligt filter). Alla vägklasser räknas, utom `motorway`, `motorway_link`, `trunk_link`, `primary_link`,
  `secondary_link` och `tertiary_link` (påfarter och motorvägar, som inte är vägar man går förbi en sten på) samt
  `steps`, `bridleway`, `cycleway` och `footway` (gång- och cykelvägar i tätort). Om Viktor hellre vill använda
  Lantmäteriets *Topografi 10, vektor* (CC BY 4.0, kräver Geotorget) byts källan före körningen, inte efter.
- **L1, registrets gamla vägar som linjer:** Riksantikvarieämbetets KMR-paket
  `/Volumes/2TB/Antigrvity/Runes/geografi_kallor/raa/lamningar_sverige.gpkg`, vyn `lämningar_sverige_linestring`
  (SWEREF 99 TM). Sett före låsningen: 10 846 linjer för Färdväg (9 113 lämningar), 3 838 för Färdvägssystem (882) och
  408 för Bro (385). Bara de raderna läses (sqlite3, `lamningstyp IN ('Färdväg','Färdvägssystem','Bro')`), med
  geometrin ur GeoPackage-binären. **Gammal väg** med samma regel som S1: `beskrivning` med gemener innehåller
  `hålväg|vägbank|vadställe|kavelbro|förhistori|järnålder|vikingatid|bronsålder|medeltid` och inte
  `banvall|järnväg|fäbod|militärväg|valv`. Klassningen skrivs i `utdata/riktning/vaglinjer_l1_klasser.csv` innan någon
  bäring räknas.
- **L2, Häradsekonomiska kartan** (1859–1934, 1:20 000, Lantmäteriet, CC0). Bladen hämtas utan inloggning ur
  Lantmäteriets *Historiska kartor*: sökning med `POST https://historiskakartor.lantmateriet.se/data/search-service/metadata/geosearch`
  (ruta i SWEREF 99 TM) och `POST …/RAK/metadata/searchbody?firstMatch=1&pageSize=2000` med dokumentgruppen
  "Häradsekonomiska kartan", bilden med `GET https://historiskakartor.lantmateriet.se/data/image-service/<bas>_<ktun>_1_1.tiff`
  (ktun = hex av "RAK_<id>", bas rak2; tjänsten kräver en Accept-rubrik, Python certifi). Inventeringen av vilka kartor
  som finns kring varje sten är `scripts/historiska_kartor_inventera.py` →
  `/Volumes/2TB/Antigrvity/Runes/geografi_kallor/historiska_kartor/inventering.json`; provbladet J112-74-18 Barva
  (5 940 × 4 455 px, 254 dpi, ca 2 m per pixel) ligger i `…/historiska_kartor/prov/`. Hämtas: blad vars utbredning
  täcker någon punkt inom 1 km från de 214 stenarna; finns flera upplagor av samma blad används den äldsta. Bladen
  sparas under `/Volumes/2TB/Antigrvity/Runes/geografi_kallor/haradsekonomiska/` (råfiler i `blad/`, utsnitt i
  `utsnitt/`, förteckning med bladnamn, kartår, SHA-256, hämtdatum och georefereringens fel i `blad.csv`). Kartan täcker
  bara delar av Götaland och Svealand; stenar utanför täckningen räknas bort och antalet redovisas.
- **Georefereringen av L2.** Skanningarna i Historiska kartor är *inte* georefererade. Vilken väg som används bestäms
  en gång för alla innan första utsnittet görs, och antecknas i `blad.csv`:
  (a) Lantmäteriets georefererade CC0-version från Geotorget, om Viktor har loggat in och beställt den; annars
  (b) egna stödpunkter: minst 6 per blad, spridda så att varje fjärdedel av bladet har minst en, på föremål som finns
  både på kartan och i dag (kyrkor, i första hand medeltida, vägkorsningar och broar som finns kvar), med dagens läge
  ur Lantmäteriets Topografiska webbkarta (CC BY 4.0) eller OpenStreetMap. Stödpunkterna väljs på hela bladet utan
  hänsyn till var stenarna står och av någon som inte ser stenarnas riktningar. Anpassning: affin (6 parametrar); med
  minst 10 punkter prövas också andra ordningens polynom, och den av de två med lägst fel väljs. Felet mäts som RMS
  med en punkt i taget utelämnad (leave-one-out), i meter. **Ett blad godtas om felet är högst 25 m**; blad över
  gränsen räknas bort med sina stenar, och antalet redovisas. Gäller (a) används Lantmäteriets georeferering som den
  är, och gränsen 25 m prövas på 6 egna kontrollpunkter per blad.
  Vägarna ritas av blint enligt protokollet nedan.

## Mått
För varje sten och källa: närmaste punkt på någon väglinje inom avståndet; **bäringen** från stenen till den punkten
(norr = 0°); och **linjens egen riktning** där (axial, 0–180°). Stenar som ligger närmare linjen än 2 m räknas bort i
den källan (bäringen är då obestämd) och antalet redovisas.
- **Huvudmått som tidigare:** medel-cos(ristningens riktning − bäringen till vägen) och andelen inom 45 grader (25
  procent väntat om riktningen vore slumpvis), mot 9 999 omblandningar av riktningarna mellan stenarna inom landskapet,
  ensidigt (mot vägen), slumpfrö 2026, p = (1 + antal ≥ observerat) / 10 000.
- **Beskrivande:** andelen stenar vars ristning vetter *tvärs över* vägen (inom 45 grader från vinkelrätt mot linjen,
  åt endera hållet) och andelen som vetter *längs* den.
- **Avstånd:** 500 m i huvudproven; 300 m och 1 km beskrivande.
- **Urval i varje prov:** (a) alla stenar med en väg i källan inom avståndet; (b) samma utan stenar med `flyttad`.
- **Minsta antal:** 30 stenar i (a); annars "kan inte prövas". I (b) krävs p < 0,05 bara om minst 30 stenar är kvar,
  annars bara att medel-cos ligger över det väntade.

## Prov
**K (kalibrering av metoden, utan ristningarna).** Bland stenarna med väg ur registrets text (68 stenar; vägens håll
med gon-rättelsen i `utdata/riktning/gon_kontroll.json`) och en OSM-väg inom 500 m: andelen där bäringen till närmaste
OSM-linje ligger inom 45 grader från registrets vägriktning. **K godkänd** om andelen är minst 70 procent. K säger om
linjemetoden hittar samma väg som inventeraren skrev om; ristningarnas riktning används inte.

**L0 (grind).** Dagens vägar (OSM), 500 m. **Grinden håller** om L0 (a) håller (medel-cos över det väntade och
p < 0,05) **och** andelen inom 45 grader är minst 40 procent (publicerat 48–50 procent), och (b) går åt samma håll.
Håller grinden inte ersätter linjemetoden inte registrets text: L1 och L2 räknas och redovisas då bara beskrivande, och
begränsningen från självkontrollen står kvar. K avgör hur det redovisas: är K godkänd hittar metoden inventerarens väg,
och ristningarna följer då den vägen men inte dagens vägnät i stort; är K inte godkänd är närmaste-linje-bäringen själv
problemet.

**L1 (registrets gamla vägar som linjer).** Gamla vägar enligt regeln ovan, 500 m. **Håller** om (a) håller med
Holm-korrigerat p < 0,05 (över L1 och L2, eftersom vardera kan häva begränsningen) och (b) uppfyller regeln ovan.

**L2 (1800-talets vägar på Häradsekonomiska kartan).** Avritade vägar av klass 1 och 2 (se protokollet), 500 m.
**Håller** på samma sätt som L1 (Holm över L1 och L2), och bara om avritningen klarar tillförlitlighetsprovet; annars
räknas L2 som inte prövad och redovisas beskrivande.

**Beskrivande (inga krav):** varje prov vid 300 m och 1 km; L1 bara hålvägar och vägbankar; L1 bara antikvarisk
bedömning Fornlämning; L1 utan linjer vars beskrivning nämner runsten eller runristning; L2 bara klass 1, och klass 1–3;
L2 med stenens läge alltid från koordinaten (huvudprovet använder stenens tecken på kartan när det finns, se nedan); alla
prov med gon-rättade ristningsriktningar; andelen tvärs över och längs vägen; L0 bara OSM-klasserna `track`, `path` och
`unclassified`.

## Blint avritningsprotokoll för L2 (bestämt nu)
1. **Hämtning och georeferering.** Blad väljs bara efter stenarnas lägen (inom 1 km), aldrig efter riktningar, och
   georefereras enligt Data innan något utsnitt görs. Antalet stenar på hämtade och godtagna blad får räknas före
   avritningen.
2. **Utsnitt.** Utsnitten görs av ett skript. För varje sten ett utsnitt om 1,2 × 1,2 km kring stenens läge (omräknat
   till bladets pixlar med georefereringen), med kartans egen upplösning, sparat som PNG. Bara stenens läge markeras,
   med en liten ofylld ring (radie 10 m), och 500-meterscirkeln med en tunn linje. Utsnittet vrids slumpvis 0, 90, 180
   eller 270 grader (slumpfrö 2026), får en slumpad kod som filnamn och visas i slumpad ordning. Inget signum, ingen
   sockentext, ingen KMR-text och ingen riktning visas eller läggs till (kartans egna ortnamn står kvar). Nyckeln (kod →
   signum, vridning, pixel-till-SWEREF-transform) skrivs i `utsnitt/nyckel.csv`; dess SHA-256 antecknas i `blad.csv`
   innan avritningen börjar, och avritaren öppnar den inte.
3. **Verktyget.** En lokal HTML-sida utan nätverk visar ett utsnitt i taget. Avritaren klickar ut varje väg som syns
   inom 500-meterscirkeln (och en bit utanför), som en linje med så många punkter som behövs för att följa kurvorna, och
   anger klass: **1** allmän väg/landsväg (dubbel linje), **2** annan väg, byväg eller ägoväg (enkel heldragen linje),
   **3** gångstig, ridstig (streckad). Om kartan visar ett tecken eller en text för runsten (t.ex. "Runsten", "Rst",
   "R.") inom utsnittet klickar avritaren ut det. Avritaren kan också välja "ingen väg inom cirkeln" eller "kartan
   oläslig här". Resultatet sparas som JSON i pixelkoordinater per utsnitt.
4. **Avritarna.** Avritare A är Viktor, som ritar alla utsnitt (vid ett senare tillfälle). Den andra avritningen är ett
   slumpat urval om 25 procent av utsnitten, minst 30 (slumpfrö 2026), som Viktor ritar om tidigast sju dagar efter att
   han ritat klart första gången, med nya koder, ny vridning och ny ordning, utan att se sina första linjer. Den
   redovisas som en svagare kontroll (samma avritare). Blir en andra person tillgänglig före den andra avritningen ritar
   den personen urvalet i stället, oberoende av Viktor, och kontrollen redovisas då som mellan två avritare. Ingen
   avritare ser stenarnas riktningar, KMR-texterna eller resultat per sten. Claude och andra modeller ritar inte.
5. **Tillförlitlighet (utan ristningarna).** För varje utsnitt i urvalet jämförs den första och den andra avritningen: *överens* om båda finner en väg
   av klass 1–2 inom 500 m och bäringarna från stenen till närmaste avritade punkt skiljer högst 22,5 grader, eller om
   ingen av dem finner någon. **Godkänd** om minst 80 procent av urvalet är överens. Annars är L2 inte prövad.
6. **Analysen.** Pixlarna räknas tillbaka till SWEREF 99 TM med nyckeln (vridningen tas bort). Har avritaren märkt ut
   ett runstenstecken inom 150 m från koordinaten används det som stenens läge (kartans läge mot kartans väg, oberoende
   av georefereringens fel); annars koordinaten. Den första avritningen (A) används i huvudprovet.

## Tolkning (bestämd nu)
- **Grinden håller inte:** linjemetoden återger inte det publicerade sambandet med dagens vägar, och L1/L2 kan varken
  häva eller skärpa begränsningen. Rapporten skriver "mot vägen, som vägarna går i dag" (självkontrollens tolkning),
  med K:s besked om varför linjemetoden inte räckte.
- **Grinden håller, L1 och L2 håller:** begränsningen hävs. S1 föll på punktbäringen. Rapporten får skriva att
  ristningen vetter mot vägen också när vägen är en registrerad väg av fornlämningstyp eller 1800-talets väg, med
  förbehållet att ingen av vägarna är daterad till vikingatiden.
- **Grinden håller, L2 håller, L1 inte:** sambandet gäller vägen som den gick på 1800-talet, före det moderna vägbygget,
  men är inte visat för registrets gamla vägar. Rapporten skriver "mot vägen, som den gick redan på 1800-talets kartor".
  Det är inte vikingatiden, och återresningar från samma tid (S3 håller dock) nämns.
- **Grinden håller, L1 håller, L2 inte (eller inte prövad):** sambandet gäller också vägar av fornlämningstyp (hålvägar,
  vägbankar); S1:s utfall berodde på punktbäringen. Rapporten skriver "mot vägen, också mot gamla vägar i registret"
  och redovisar L2.
- **Grinden håller, varken L1 eller L2 håller:** begränsningen står och skärps. Ristningarna följer dagens vägnät men
  inte 1800-talets vägar eller registrets gamla vägar. Rapporten skriver att sambandet gäller dagens väg, och att det
  kan bero på att vägar har dragits om förbi stenarna eller att stenar har ställts mot nyare vägar, utöver det som
  syns i texterna (S3).
I alla fall redovisas L0–L2, K och tillförlitligheten öppet. Rapporten, artikeln och IMPLEMENTATIONSPLAN.md ändras först
när Viktor har sett utfallet, och en ny Zenodo-version görs bara på hans besked.

## Förbehåll
OSM-vägarna är 2020-talets och inte de vägar inventerarna såg på 1970–2000-talen. KMR-linjerna är inte daterade, och
regeln för gamla vägar är grov. Häradsekonomiska kartan är georefererad med varierande noggrannhet och visar 1800-talets
och det tidiga 1900-talets vägar, inte vikingatidens; Skoglund & Lagerås (2002) visar att en förhistorisk väg kan saknas
på kartorna (invändning c, fortfarande oprövad). Riktningarna anges i 16 väderstreck.

## Redovisning
`utdata/riktning/vaglinjer.py` (L0, L1, K och analysen av L2), `utdata/riktning/vaglinjer_l1_klasser.csv`,
`utdata/riktning/vaglinjer_utsnitt.py` (bladval och utsnitt), `utdata/riktning/vaglinjer_ritverktyg.html`,
`utdata/riktning/vaglinjer.json`, `utdata/riktning/vaglinjer_resultat.md`. Bladen, utsnitten, nyckeln och avritningarna
ligger under `/Volumes/2TB/Antigrvity/Runes/geografi_kallor/haradsekonomiska/`, OSM-utdraget under
`/Volumes/2TB/Antigrvity/Runes/geografi_kallor/osm/`. L0, L1 och K kan köras före L2; L2 räknas när avritningen och
tillförlitlighetsprovet är klara. Inga parametrar ändras efter körningen.
