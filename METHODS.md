# Metodbeskrivning

Den här filen beskriver exakt hur Vitki räknar, så att resultat kan granskas, upprepas och citeras.
Alla beräkningar finns i `src/` (Python) och `r/` (R); testerna ligger i `tests/`. Varje analys sparar en **proveniens**
(programversion, mätmetodens version, SHA-256 för 3D-filen, alla parametrar och tidpunkt) som följer med i export och
rapporter.

**Avsnitten.** Avsnitt 1 är statistiken i R över hela korpusen – de 2 321 svenska vikingatida runstenarna i Rundata –
där appens mönster och hypoteser kommer ifrån. Avsnitt 2–13 beskriver hur en enskild sten mäts, läses och attribueras
(huggspår, ortografi, läsning mot Rundata, inskriftens syfte, bergart, bilder och runformer, och syntes), 14 forskningsluckorna och tolkningen av
fynden, 15 rapporterna och artiklarna, 16 jämförbarheten med tidigare forskning, 17 datakällorna och 18 metodens kända
brister.

## 1. Statistik i R

Källkod: `r/` (R-skripten), `src/r_bridge.py` (export, körning, cache), `src/r_findings.py` (fynd och mönster),
`src/r_report.py` (rapportavsnitt), `api/routers/rstats.py` (`/api/r/…`). Sidan **Statistik (R)** visar
resultaten; stenanalysen och stenrapporten använder dem för den enskilda stenen.

Statistiken i R står först eftersom appens mönster kommer härifrån: vad som är vanligt var, när och hos vilka ristare i
hela den svenska vikingatida korpusen. Forskningsluckor (avsnitt 14), stenanalysens jämförelser med korpusen och
artiklarna (15g) bygger på dem. Avsnitt 2–13 beskriver hur en enskild sten mäts, läses och attribueras; en del av det,
som språkdragen (avsnitt 9) och inskrifternas syfte (avsnitt 10), är också underlag för analyserna här. Hur ett mönster
ska läsas – vad som påstås och vad som bara föreslås – står i 1x, och begränsningarna i 1l.

**Underlag.** Alla svenska vikingatida runstenar i Rundata (2 321) exporteras till en CSV med plats, härad,
ristare (en säker ristare, annars tomt), stilgrupp och Gräslunds datering, kors, kortkvistrunor, de nio
innehållskategorierna (avsnitt 10), de tjugo språkdragen (avsnitt 9), läsbara ord och stavningsvarianter (ordform
parad med normaliseringen; egennamn utelämnade) och normaliseringen. Korpusanalyserna körs en gång per version
av data och skript (fingeravtryck) i en egen process (`python -m src.r_bridge <fingeravtryck>`) och sparas i
`data/cache/r/corpus/<fingeravtryck>/` med `sessionInfo()`. Sedan 2026-10-11 har varje modul också en egen
version (korpusen, `common.R`, modulens skript och versionerna av de moduler den läser); en modul med samma version
som i en tidigare fullständig körning kopieras därifrån i stället för att räknas om, så att en ändring i ett skript
bara räknar om den modulen och de som bygger på den (`reused` i `done.json`). Varje modul körs som
`Rscript --vanilla r/<modul>.R params.json utmapp` och skriver JSON och figurer. Sedan 2026-10-16 startar
analysmotorn körningen själv när den nuvarande versionen saknar resultat (`api/routers/rstats.py`, `autorun`), tio
minuter efter start. Väntan gör att en serie kodändringar, som var och en startar om motorn, inte ger en körning per
ändring. En misslyckad körning görs inte om av sig själv; den görs om med knappen på sidan. `R_AUTORUN=0` stänger av
funktionen. En ny Rundata läses in när motorn startas om.

| Modul | Paket | Vad den gör |
|---|---|---|
| `geography.R` | sf, leaflet | ristarnas tyngdpunkter, spridning och konvexa höljen (SWEREF 99 TM); permutationstest (499 urval ur samma landskap) av om ristaren arbetade inom ett mindre område än slumpen ger (Benjamini–Hochberg); avstånd till vatten mot slumpvisa punkter på land per landskap (Wilcoxon), också mot en modellerad strandlinje omkring år 1000 (se nedan); interaktiv karta |
| `clusters.R` | cluster, FactoMineR, factoextra | Gowers avstånd på stil, språkdrag, kors, kortkvistrunor och innehåll (kategorierna asymmetriskt binära), PAM med k = 2–10 efter silhuettbredd, stabilitet som Jaccard-likhet i 20 delurval om 80 % (Hennig 2007), MCA; ristare och landskap jämförs efteråt (justerat Rand-index) |
| `text.R` | tidytext, stringr | formler ur normaliseringen (resarformel, monument, ordföljd, ristarsignatur, bön) per ristare; stavning per ord mot ristare (χ² med simulerat p, Cramérs V); ordformer som utmärker en ristare (Fishers exakta test, BH); tf-idf; de 100 vanligaste runbigrammen som variabler till modellen |
| `attribution.R` | tidymodels, ranger | random forest (500 träd) på stenar med säker ristare, ristare med minst åtta stenar (i dag 18 ristare, 497 stenar); 5-faldig stratifierad korsvalidering upprepad 3 gånger, och grupperad per socken och härad; delmodeller med bara geografi, bara stil, bara språk och innehåll; kalibrering (andel rätt per sannolikhetsnivå, ECE); permutationsvikter; förslag för stenar utan ristare inom 25 km från en träningssten |
| `anonymous.R` | cluster, igraph | grupper av stenar utan ristare som liknar varandra lika mycket som en ristares stenar (Gowers avstånd på handens drag, länkade inom 30 km, Louvain); validering på stenar med känd ristare; jämförelse med kända ristare i närheten; arbetsnamn efter typstenens socken (se nedan) |
| `chronology.R` | ca | seriation (korrespondensanalys av språkdrag, formler, kors, kortkvistrunor och innehåll – utan stilgrupp) för Uppland, prövad mot Gräslunds stilkronologi (Spearman mot stilgruppens mittår, och partiell med latituden konstant); tidsskattning med 80 % prediktionsintervall och korsvaliderat medelfel; för hela korpusen redovisas vad de tre första dimensionerna följer (tid, geografi, ristare eller oförklarat) |
| `dialect.R` | stringdist | förväntat normerat Levenshtein-avstånd mellan häradernas stavning av vanliga ord; Mantel-test mot geografiskt avstånd (999 permutationer); grupper av härader (PAM); kartor över stavningen av "efter" och "sten" |
| `network.R` | igraph, tidygraph, ggraph | ord som står i samma inskrifter (positiv PMI), grupper med Louvain; släktorden i inskrifterna (fader, moder, son, broder, félagi …) före och efter ca 1050 och i kristna mot övriga inskrifter (Fisher, BH) |
| `change.R` | mgcv, sf | förändring i tid och rum för sexton drag (monoftong i ord med *æi* och i 'och', ʀ skrivet med r-runan, åsrunan för o-ljud, h-bortfall, nasal före konsonant, prepositionen *at*, stungna runor och stungen i, u och k, kristen bön, själsbön, kors, bro- och vägbygge, ristarsignatur): logistisk regression med utjämnad tidskurva, rumslig utjämning och ristaren som slumpeffekt; justerad andel över tid, karta, landskapen i mittperioden (omkring 1050; Holm över dragen, med observerade andelar, antal attribuerade ristare och samma test utan ristareffekten) och året då draget passerar hälften (bara för drag som stadigt ökar eller minskar); bro- och vägstenar mot kristna drag (se nedan) |
| `words.R` | mgcv, ca | ordförrådet per landskap och tid (1m): en logistisk modell per ord (landskap mot genomsnittet + stilgruppens mittår + textlängd, ristaren som slumpeffekt), BH-justering och sockenhalvprov; korrespondensanalys landskap × ord. Samma ordplockning som appens ordmoln; namn ingår inte |
| `remains.R` | sf | avstånd till närmaste gravfält, hög, färdväg, bro, fornborg och hamnanläggning i Kulturmiljöregistret mot slumpvisa punkter på land inom 5 km från stenarna (Wilcoxon, BH); närhet inom 500 m över tid, med kristna markörer och för brostenar (logistisk regression med landskapet konstant), prövat i korpusens två halvor; flyttade stenar räknas inte (se nedan) |
| `stone.R` | sf, cluster, tidymodels | en sten mot korpusen: modellens sannolikheter (korsvaliderade om stenen har ristare i Rundata), avstånd till kandidaternas tyngdpunkter och höljen, grupp och närmaste grannar (Gower), formler jämförda med kandidaternas inskrifter, läge i Upplands seriation |
| `landscape.R` | terra, gdistance | höjdmodell (ca 20 m), höjd, lutning, topografiskt positionsindex; strand vid vikingatiden som dagens höjd minus en grov landhöjning per landskap (t.ex. 5 m i Södermanland, 5,5 m i Uppland); sikt (viewshed, stenens topp 2 m, betraktare 1,6 m) mot slumpvisa platser; bästa vägar (Toblers vandringsfunktion, vatten tio gånger långsammare) mellan andra runstensplatser inom 12 km och stenens avstånd till dem mot slumpvisa punkter |
| `hotspots.R` | sf, spdep, smerc | var mönstren på mönsterkartan klustrar: Morans I per mönster, Getis-Ord Gi\* per sten och Kulldorffs rumsliga scanstatistik (999 simuleringar), Benjamini–Hochberg; varje kluster prövat i korpusens två halvor; kartbilder (se 1f) |
| `technique.R` | – | huggteknik sten för sten: avståndet från en sten till en ristares stenar i mätkorpusens mått, jämfört med ristarens egna stenar (lämna-en-ute) och andra ristares; permutationstest per mått på stennivå. Ingår inte i korpusanalysen utan körs med mätningar från `scripts/measure_stones.py` (se 1l) |
| `blogfig.R` | sf | figurer till artiklarna i stället för länkar in i appen: kartverktygets tidskarta för ett mönster (andelen stenar per sexkant om 20 km, före och efter omkring 1050), en punktkarta för sällsynta mönster och förändringsmodellens kurvor (se 15g) |

### 1b. Dåtidens strand

Källkod: `r/geography.R` (från 2026-10-12). Landhöjningen sedan omkring år 1000 har flyttat kusten: en
sten som stod vid en vik kan i dag stå långt in på land. Havet omkring år 1000 modelleras som land under landskapets
landhöjning sedan dess (grova värden i `r/common.R`, t.ex. 5,5 m i Uppland, 5 m i Södermanland, 1,5 m på Öland) på en
höjdmodell med omkring 300 m upplösning (Terrain Tiles, zoomnivå 9), tillsammans med dagens sjöar och vattendrag.
Stenarna och samma lokala slumppunkter som i jämförelsen med dagens vatten mäts mot den strandlinjen (Wilcoxon,
ensidigt). Beräkning 2026-10-12: stenarna står i median 3,6 km från dåtidens vatten mot 5,3 km för slumppunkterna
(p < 0,001; med dagens vatten 4,2 mot 5,6 km). Kvoten mellan stenarnas och slumppunkternas avstånd sjunker från 0,64
till 0,53 i Uppland, där landhöjningen är störst; skillnaden är signifikant i Uppland, Södermanland och på Öland men
inte i Östergötland, Småland, Västergötland, Västmanland eller på Gotland. Höjdmodellens noggrannhet (några meter) är
av samma storleksordning som landhöjningen, särskilt i flack terräng med liten landhöjning: Ölands stora förändring
(kvoten 0,57 till 0,18) kan delvis bero på det. Låglänt inland kan räknas som hav, och igenslamning och dämning ingår
inte. SGU:s strandförskjutningsmodell och Lantmäteriets höjdmodell skulle ge en säkrare strand.

### 1c. Lämningar runt stenarna

Källkod: `r/remains.R` (från 2026-10-12). Hur står runstenarna i det fornlämningslandskap som
Kulturmiljöregistret beskriver? För varje sten och för lika många slumpvisa punkter på land inom 5 km från stenarna i
samma landskap (samma lokala nollmodell som för vattnet) mäts avståndet till närmaste gravfält, hög, färdväg
(färdvägar och färdvägssystem), bro, fornborg och hamnanläggning; stenar och punkter jämförs med Wilcoxons test
(ensidigt, Benjamini–Hochberg över slagen). Närhet inom 500 m modelleras med logistisk regression med landskapet
konstant: mot stilgruppens mittår (per 50 år), mot kristna markörer (kors eller kristen formel, med tiden konstant) och
för brostenar, och varje samband prövas i korpusens två halvor (uppdelade per socken som i `change.R`). Stenar som
enligt Rundatas placering står vid eller i en kyrka, i en vägg, ett museum eller en samling räknas inte, eftersom de är
flyttade, och inte heller stenar vars plats i Rundata är en kyrka, kyrkogård, kyrkoruin, prästgård, ett kloster, slott,
en skola eller ett museum ("Frustuna kyrka", "Veta kyrkogård"), eftersom de inte kan skiljas från flyttade stenar.
Sedan 2026-10-27 räknas också stenar vars placering säger att de flyttats ("Flyttad 100 m åt N", "förd till
Eskilstuna") eller nämner en annan plats än fyndplatsen ("Vid Hummelsta, Stora Mellösa sn", "Står vid Sö 109"), men
inte när placeringen bara beskriver var på platsen stenen står (väderstreck och avstånd, gårdsplanen, byn, en väg)
eller när stenen förts tillbaka ("Återfördes till Brobybro 1955"); sex texter utan ortnamn är avgjorda för hand
(`src/placement.py`). Det gav 47 flyttade stenar till: 1 223 av 2 321 (kolumnen `moved` i korpusens CSV, `is_moved`
i `src/r_bridge.py`).

*Rättelse 2026-10-12.* Fram till den här dagen prövades bara placeringen, som oftast är tom för stenar vid kyrkor;
omkring 420 stenar vid kyrkor räknades därför som stående på sin ursprungliga plats. Det gav ett skenbart samband
mellan kristen bön och närhet till medeltida kyrkor (oddskvot 1,26 och replikerat med det gamla urvalet, 1,18 och inte
signifikant med det rättade) och gjorde sambandet mellan kors och centralortsnamn starkare än det är. Resultat från
korpusanalyser före fingeravtrycket 6e62df8f5ff9a4c0 som rör stenarnas omgivning (lämningar, ortnamn, kyrkor,
genomsökningen och hot spots) ska läsas med det i minnet.

Beräkning 2026-10-12 (1 563 stenar, 52 674 lämningar): 61 % av stenarna står inom 500 m från ett registrerat gravfält,
mot 21 % av slumppunkterna (median 0,36 mot 1,11 km); inom 500 m från en hög 33 % mot 9 %, från en färdväg 17 % mot 6 %.
Närheten till gravfält gäller i Uppland, Södermanland, Östergötland, Småland och Västergötland, ändras inte över tiden
(före omkring 1050 60 %, efter 66 %; oddskvot 0,81 per 50 år, q 0,44) och är lika stor för stenar med kristna markörer
(oddskvot 1,08, q 0,81). Brostenar står oftare nära en registrerad färdväg (oddskvot 1,91, q 0,03), men sambandet håller
inte i båda halvorna och redovisas därför som indikation. Att runstenar ofta står vid gravfält är känt; det nya är att
närheten mäts mot slumpen i hela korpusen och att den varken minskar med tiden eller för kristna stenar, vilket talar för
att gravfälten förblev släktens minnesplatser genom kristnandet. Reservationer: registret är olika väl inventerat i olika
trakter, en lämning är en punkt (mittpunkten för en yta), de flesta lämningar är odaterade, färdvägar och broar är ofta
medeltida eller yngre, och i enstaka fall kan ett gravfält ha registrerats just där en runsten står.

### 1d. Förkristna kultnamn och stenarnas budskap

Källkod: `r/remains.R` (från 2026-10-12). Är kristna budskap vanligare på stenar
nära platser som kan ha varit förkristna kultplatser? Ortnamnen kommer ur OpenStreetMap (© OpenStreetMap-bidragsgivare,
ODbL), där Lantmäteriets ortnamn från terrängkartan finns inlagda; bara by-, gårds- och ortnamn räknas, inte unga
stadsdelsnamn (`scripts/fetch_place_names.py`, `data/ortnamn/`). Namnen delas i tre nivåer. *Teofora namn* (A) är ett
gudanamn (Tor, Oden/Ons, Frö, Ull, Njärd/När, Härn, Dis) med en sakral eller typisk efterled (vi/ve/vid, harg, hov,
lunda, åker/åkra, sal/sala, tuna, sunda), t.ex. Torsvi, Odensala, Ullevi och Frösö – den gängse indikationen på en
kultplats (Vikstrand 2001); singularformen -lund räknas inte, eftersom den oftast är unga villanamn. *Sakrala namn utan
gudanamn* (B) är Vi, Ve, Viby, Harg, Hov, Hof, Hörg och Gudhem, osäkrare eftersom harg också kan betyda stenig mark och hov
gård eller höjd. *Centralortsnamn utan kult* (C), Husby och namn på -tuna utan gudanamn, är en jämförelse: teofora namn
markerar ofta centralorter, där eliten kan ha blivit kristen tidigt. Ett namn sägs vara nära en sten inom 2 km (valt i
förväg); flyttade stenar räknas inte. Kristen bön, kors och kristna markörer överlag modelleras med logistisk regression
med landskapet konstant, också med tiden konstant och med närheten till centralortsnamn konstant, prövas i korpusens två
halvor och med stenarna vid ett namn i taget utelämnade, och redovisas med 1 och 3 km som känslighetsprov. Medeltida
kyrkor (Wikidatas kyrkobyggnader i Sverige med ett uppförandeår före 1350, CC0, långt ifrån alla) jämförs med namnen:
ligger de teofora namnen oftare inom 1 km från en kyrka än andra ortnamn av samma slag inom 10 km från en runsten
(Fishers exakta test)?

Beräkning 2026-10-12 (1 563 stenar, 82 teofora namn, 66 sakrala, 128 centralortsnamn): kristen bön står på 28 % av de 74
stenarna nära ett teoforiskt namn mot 15 % av övriga (oddskvot 2,23, 1,30–3,81, q 0,014), håller i båda halvorna och
ligger mellan 1,89 och 2,55 när stenarna vid ett namn i taget utelämnas (20 namn). Vid centralortsnamn utan kult är bönen
inte vanligare (oddskvot 1,27), och med närheten till dem konstant består skillnaden (2,29); det talar emot att den bara
speglar elitens gårdar. Kristna markörer överlag (69 % mot 53 %) och kors pekar åt samma håll men håller inte i båda
halvorna, och vid de sakrala namnen utan gudanamn syns ingen skillnad. Med 1 km (25 stenar) blir oddskvoten 1,68 och med
3 km 1,37, åt samma håll men inte signifikant: resultatet hänger delvis på radien och redovisas som ett mönster att pröva.
Teofora namn ligger inom 1 km från en medeltida kyrka i 9 % av fallen mot 2,5 % för andra ortnamn (oddskvot 3,8,
p 0,007), en indikation med tanke på kyrkoregistrets luckor. Ortnamnen är belagda långt efter vikingatiden, och namnets
läge är dagens by eller gård, inte kultplatsen själv.

### 1e. Genomsökning av landskapet

Källkod: `r/remains.R` (från 2026-10-12). En systematisk sökning efter dolda mönster: varje
mönster på mönsterkartan (kolumnerna `pm_*` i korpusens CSV, samma definitioner som kartan, `src/pattern_map.py`)
prövas mot avståndet till varje sorts plats – teofora och sakrala ortnamn, centralortsnamn, medeltida kyrkor, gravfält,
högar, färdvägar, broar och fornborgar. Ingen radie väljs: modellen är en logistisk regression på log2 av avståndet
(plus 250 m, så att en sten vid själva platsen inte blir oändligt nära) med landskapet konstant, och effekten anges som
oddskvoten när avståndet halveras (över 1: vanligare närmare platserna). Kombinationer där mönstret finns på färre än
15 stenar eller saknas på färre än 15 prövas inte. Alla kombinationer justeras tillsammans (Benjamini–Hochberg), varje
prövas också i korpusens två halvor och med tiden konstant, och flyttade stenar räknas inte. Andelen inom 2 km (ortnamn,
kyrkor) eller 500 m (fornlämningar) redovisas bara som läshjälp. Kombinationer som klarar justeringen och håller i båda
halvorna blir mönster att pröva i Forskningsluckor (mönstret *utan religiösa markörer* utelämnas, eftersom det är
spegelbilden av de kristna markörerna); de som bara klarar justeringen sammanfattas som indikationer. På kartan visas
genomsökningen som ett rutnät med mönster mot platser.

Beräkning 2026-10-21 (117 kombinationer, 1 144 stenar på ursprunglig plats): ingen klarar justeringen (lägsta q
0,075). 20 har p under 0,05, där slumpen ensam väntas ge omkring 6, men flera prov mäter nästan samma sak (kristna
markörer, kors, utan religiösa markörer), så överskottet är osäkert. Starkast: kristna markörer och kors närmare
centralortsnamn (oddskvot 1,22 och 1,20 när avståndet halveras, q 0,07, inte i båda halvorna, svagare med tiden
konstant), bro- och vägbygge närmare medeltida kyrkor (1,37, med tiden konstant 1,47) och själsbön närmare teofora
ortnamn (1,31, i båda halvorna men q 0,09). Den tidigare beräkningen 2026-10-12 (tio klarade justeringen, fyra höll i
båda halvorna) gjordes före rättelsen av flyttade stenar (avsnitt 1c, *Rättelse 2026-10-12*) och gäller inte längre.

*Visningen* (kartsidan, *Alla samband i landskapet*, från 2026-10-27): först en sammanfattning i ord – hur många samband
som klarar justeringen och håller i båda halvorna, hur många som har p under 0,05 mot vad slumpen ger, och de starkaste
sambanden i tre nivåer (håller; bara i den ena halvan; starkast men inte säkra), vart och ett med andelarna inom
radien, oddskvoten med och utan tiden konstant och hur säkert det är. Därefter rutnätet, där antydningar (p under 0,05
men inte efter justeringen) har en blek ton och streckad kant.

### 1f. Hot spots och kluster

Källkod: `r/hotspots.R` (från 2026-10-12; R-paketen spdep och smerc). Var klustrar mönstren på
kartan mer än slumpen ger? För varje mönster (`pm_*`) och de stenar där det kan avgöras, utan flyttade stenar: *Morans
I* med de åtta närmaste stenarna som grannar (SWEREF 99 TM), Benjamini–Hochberg över mönstren – klustrar mönstret alls?
*Getis-Ord Gi\** för varje sten (grannarna och stenen själv) – ligger den i ett hett område, där mönstret är vanligare än
i landet, eller ett kallt? De lokala p-värdena justeras med Benjamini–Hochberg över stenarna. *Kulldorffs rumsliga
scanstatistik* (smerc) prövar alla cirklar runt varje sten som rymmer högst en tiondel av stenarna, med landets andel som
förväntat värde per sten (Poissonformen; den binomiala fungerar inte med en sten per plats) och 999 Monte
Carlo-simuleringar; bara kluster med p < 0,05 redovisas, och klustrens p-värden justeras med Benjamini–Hochberg över
mönstren. Varje kluster prövas också i korpusens två halvor, uppdelade per socken: är mönstret vanligare inne i klustret
än utanför i båda (Fishers exakta test)? Kluster som håller i båda halvorna blir mönster i Forskningsluckor – mönster att
pröva om de klarar justeringen över mönstren, annars indikationer. Ett kluster är en plats att titta närmare på (en
ristare, en verkstad eller en bygd), inte en förklaring.

*Kartbilder* (från 2026-10-12): för varje mönster som klustrar (Morans I, q < 0,05) och har heta eller kalla stenar eller ett kluster ritar `hotspots.R` en karta `hotspot_<mönster>.png`: andelen stenar med mönstret per sexkant om 25 km (minst 5 stenar), stenarna i heta och kalla områden (Gi*) och klustren (Kulldorff) som ringar, på Natural Earths land. Genomsökningen av landskapet ritas av `remains.R` som `landskap_genomsokning.png`. Figurerna kan användas i artiklarna (15g); en artikel får en egen kopia under figurens innehållshash (`src/blog_figures.py`, `/api/blog/figures/`), så att bilden finns kvar när korpusanalysen räknas om.

### 1g. Okända ristare

Källkod: `r/anonymous.R` (från 2026-10-11). Kan en gruppering i statistiken vara en ristare som ännu inte
har namn? Stenar med minst fem läsbara ord jämförs i *handens drag* – stilgrupp, kors, kortkvistrunor, språkdrag
(inklusive skiljetecken och bindrunor), formler och runbigram, men inte innehåll och plats – med Gowers avstånd. Gränsen
för att länka två stenar kalibreras på par av stenar med känd ristare (ristare med minst tre säkra stenar) inom 30 km:
par under gränsen ska vara minst tolv gånger vanligare bland samma ristares par än bland olika ristares. Stenar utan
ristare i Rundata länkas när de ligger inom 30 km och under gränsen, och grupperas med Louvain. En grupp redovisas om
den har minst fyra stenar och inte är mer utspridd än 90 % av de kända ristarna med minst fem stenar (median till
gruppens mitt; i dag 23 km). Förfarandet prövas på stenar med känd ristare, som om ristaren vore okänd: hur stor del av
en grupp är samma ristare, jämfört med grupper av lika många närliggande stenar? Avståndet och gränsen valdes efter
den valideringen (15–30 km, kvot 4–12), så träffsäkerheten kan vara något överskattad. Resultat (beräkning
2026-10-20): en grupp bestod i genomsnitt till 69 % av samma ristare, mot 43 % för bara
närliggande stenar, och 60 % av grupperna till minst tre fjärdedelar; av länkade par med känd ristare var 71 % samma
ristare. Bland stenarna utan ristare blev det 16 grupper, varav 8 möjliga okända ristare: Konungsundsristaren (28
stenar, Östergötland), Vibyristaren (14, Östergötland), Vetlandaristaren (14, Småland), Kölabyristaren (13,
Västergötland), Sättnaristaren (7, Medelpad), Leksbergsristaren och Husabyristaren (6 vardera, Västergötland) och
Dalumsristaren (5, Västergötland). Stabiliteten mäts som hur stor del av gruppen som återkommer (Jaccard) när en
femtedel av länkarna tas bort. Varje grupp jämförs med kända ristare inom 50 km: den räknas som lik en känd ristare när
ristarens stenar i genomsnitt ligger lika nära gruppen som två stenar av samma ristare brukar göra, eller när
attribueringsmodellen föreslår samma ristare med minst 50 % för hälften av gruppens stenar. Övriga grupper får ett
*arbetsnamn* efter typstenens socken (typstenen är den sten som i genomsnitt ligger närmast de andra), t.ex.
"Fröderydsristaren", efter samma bruk som för anonyma mästare i konsthistorien. Namnet görs unikt och får aldrig vara ett
ristarnamn i Rundata. I Uppland och Södermanland, där ristarna är väl kartlagda, liknar nästan alla grupper en känd
ristare; de möjliga okända ristarna finns främst i Östergötland, Västergötland, Småland och Medelpad, där få stenar är
attribuerade. Stenarna i dessa grupper redovisas som fynd i Forskningsluckor (metod "okänd ristare (R)").

**Prövning utanför det stöd gränsen justerats på (2026-10-20).** (1) *Hållet-utanför:* ristarna (inte stenarna) delas slumpvis
i tre delar, gränsen och största spridning tas fram på två och grupper bildas på den tredje; trettio upprepningar, samma
slumpfrö som skriptet `utdata/ristare/ristare_heldout.R`. Grupperna blev i genomsnitt 85 % samma ristare mot 69 % för lika
många närliggande stenar ur samma tredjedel (skillnad 16 procentenheter, osäkerhet 14–17, till gruppernas fördel i 30
av 30 upprepningar); utan de tidsberoende dragen 85 mot 68 %. Skillnaden är mindre än i den första valideringen (26), vars
gränsvärden justerats efter samma kontroll. p-värden över upprepningarna redovisas inte, eftersom samma stenar ingår i dem.
(2) *Robusthet:* varje grupp får en andel utan de tidsberoende dragen (stilgrupp, kors, stungna runor, böner, åsrunan,
signatur); grupper med minst 65 % räknas "hålla" (fem av åtta: Konungsund 83 %, Vetlanda 79 %, Leksberg 83 %, Husaby 83 %,
Kölaby 68 %; Viby 62 %, Sättna 57 % och Dalum 14 % håller delvis eller inte). (3) *Täckning:* de kända ristarna med minst tre
stenar är 35, varav 25 i Uppland och 8 i Södermanland och en i kandidatlandskapen (Östergötland, Småland, Västergötland,
Medelpad); där har 5, 2, 1 respektive 8 % av stenarna någon ristare i Rundata mot 70 % i Uppland (och 46 % i Södermanland). Att gränsen gäller i
kandidatlandskapen är därför inte prövat – flytt av gränsen mellan Södermanland och Uppland gav inget säkert resultat
(74 mot 61 %, `utdata/ristare/ristare_overforing.R`). Appen visar detta i en ruta ovanför tabellen. Att listade drag
skiljer gruppen från trakten är ingen validering, eftersom grupperna bildas på just de dragen.

### 1h. Förändring i tid och rum

Källkod: `r/change.R` (från 2026-10-11). Hur språkdrag, skrift och kristna drag förändras
över tid och skiljer sig mellan landskap – frågor om språk- och religionshistoria som inte handlar om vem som
ristade. För varje drag skattas en logistisk regression (mgcv::bam, fREML) bland stenar med stilgrupp: tiden
(stilgruppens mittår enligt Gräslund) som utjämnad kurva med k = 4, så att ett drag kan öka och minska igen; en
rumslig utjämning (tunnplattspline på SWEREF 99 TM), så att förändringen inte bara är en förskjutning mellan områden
med olika datering; och ristaren som slumpeffekt, så att stenar av samma ristare inte räknas som oberoende. Stenar
utan säker ristare grupperas per socken, eftersom de ofta är huggna av samma okända ristare eller verkstad (en egen
grupp per sten gav samma skattningar men tog tio gånger längre tid). Kurvan redovisas som *justerad andel*: alla
daterade stenar flyttas till varje år och modellens sannolikheter för en typisk ristare medelvärdesbildas, med 95 %
intervall ur 300 dragningar av koefficienterna. Den täcker stilgrupper med minst 20 stenar; ett drag med färre
daterade stenar (under 60, under tio med eller utan draget, eller mindre än 40 år mellan de stora stilgrupperna)
prövas inte. Eftersom stilgruppen är ett intervall och inte ett år räknas varje resultat om tio gånger med årtal
dragna jämnt inom intervallet; andelen omräkningar som också ger ett säkerställt samband redovisas. Rummet visas som
karta (samma modell utan tid, på alla stenar där draget kan bestämmas, inom ca 30 km från stenarna) och landskapen som
skattad andel omkring år 1050 (egen nivå per landskap, samma tidskurva; landskap med minst 25 daterade stenar;
skillnaden prövad med Wald-test). När draget ökar eller minskar stadigt anges också året då det passerar hälften av
stenarna, ur en modell med rak trend. Slutligen prövas om bro- och vägstenar oftare har kristen bön, själsbön och kors
än andra stenar, med samma kontroller – ett test av tolkningen av brobyggen som kristna själagåvor. p-värdena
Holm-justeras inom tidstesten respektive brotesten. Formler och kors räknas bara på inskrifter som är tolkningsbara nog
för att språkdragen ska kunna bestämmas.

Resultat (beräkning 2026-10-11; 1 008 daterade stenar, 804 med tolkningsbar text). Säkerställt efter Holm-justering
och i minst 70 % av omräkningarna: stungna runor ökar (justerad andel 35 % omkring 1000 till 85 % omkring 1115),
liksom stungen i (30 till 80 %), stungen u (11 till 47 %), o-runan för o-ljud (4 till 43 % omkring 1085) och
ristarsignaturer (6 till 28 %); stungen k förändras inte. Kristen bön och själsbön är vanligast omkring 1033 (28
respektive 24 %) och sällsynta på de sena stenarna (2 %), och kors är vanligast omkring 1028 (70 %). Monoftong i något
ai-ord *minskar* (69 till 22 %) med plats och ristare konstanta: den diftongiska stavningen sprids över tid, vilket
snarare tyder på en skrivnorm än på en ljudutveckling bakåt – ett mönster att pröva. Landskapen skiljer sig omkring
1050, mest för monoftong i ai-ord (84 % i Västergötland och 80 % i Östergötland, 55 % i Uppland, 35 % i Södermanland),
böner och kors. Stungen i passerar hälften av stenarna omkring 1014 i Östergötland, 1019 i Västergötland, 1051 i
Södermanland och 1069 i Uppland (stungna runor över lag 1000, 1005, 1020 och 1043) – en spridning från söder och väster
in mot Mälardalen att pröva mot litteraturen. Bro- och vägstenar har oftare själsbön än andra stenar (25 mot 15 %,
oddskvot 1,9, q 0,04), men inte oftare kristen bön i allmänhet eller kors.

### 1i. Korsvalidering och resultat i korpusen

**Grupperad korsvalidering** (från 2026-10-10). Vid slumpvis korsvalidering kan stenar från samma plats – ofta resta
av samma ristare samtidigt – hamna både i tränings- och testdata. Modellen utvärderas därför också med hela socknar
(164 grupper) respektive härader (69 grupper) utelämnade (`group_vfold_cv`, 5 delar, 3 upprepningar). En ristare vars
alla stenar ligger i det utelämnade området saknas då i träningen och räknas som fel. Resultat (beräkning
2026-10-10): rätt ristare först i 72 % slumpvis, 68 % med ny socken och 57 % med nytt härad (bland tre främsta
87, 85 och 78 %); geografi ensamt 44, 40 och 30 %, språk och innehåll ensamt 60, 56 och 47 %, mot 19 % om man
alltid gissar på den vanligaste ristaren. En del av träffsäkerheten kommer alltså från platsen, men modellen
fungerar också för platser den inte sett. Sannolikheterna för enskilda stenar kommer fortfarande från den
slumpvisa korsvalideringen, som motsvarar en ny sten på en känd plats. Med de nio nya språkdragen (2026-10-11): 72, 69 och 59 %; språk
och innehåll ensamt 62 %.

**Bergarten som nollnivå (från 2026-10-20).** Ristare och bergart hänger ihop (en ristare högg i traktens sten), så
modellen utvärderas också mot bergarten ensam: delmodellen "Bergart" (bergartsfamiljen ur Rundatas materialuppgift,
samma ordlistor som `src/geology.FAMILIES`) träffar 19 % – samma som att alltid gissa den vanligaste ristaren
(19 %) – eftersom 347 av 421 träningsstenar med känd bergart är granit. Den fulla modellens träff per bergartsfamilj
(utanför träningsdelarna): granit 74 % (347 stenar), sandsten 67 % (52), gnejs 67 % (21); 75 stenar saknar bergart.
Modellens träff kommer alltså inte från bergarten, till skillnad från huggspårsmåtten (avsnitt 13), där bergarten
ensam träffar lika bra som måtten. Resultatet står i `attribution.json` (`material`) och i Statistik.

**"Kanske någon annan" (från 2026-10-20).** Modellen känner bara de 18 ristarna med minst 8 säkra stenar, så en sten av
någon annan får ändå ett av deras namn. Den säger därför *kanske någon annan* när förstavalets sannolikhet är under en
gräns. Okända ristare efterliknas genom att varje ristare i tur och ordning lämnas utanför: en modell tränad på de
andras alla stenar gissar på den utelämnades. Gränsen väljs så att (andelen sådana stenar som flaggas) + (andelen
kända stenar som inte flaggas) − 1 blir störst, där de kända stenarnas sannolikheter är de korsvaliderade. Resultat
(korpusversion 5ebd6df1627127fd): gränsen blev 0,35; 80 % av de utelämnade ristarnas stenar flaggas, men också 41 % av
de kända ristarnas, och där modellen ger ett namn är det rätt i 87 % (mot 73 % för alla). Prövat på stenar som inte
användes när gränsen valdes – 139 stenar av 62 ristare med färre än 8 säkra stenar, inom 25 km från en träningssten –
flaggas 71 %. Medianen för förstavalet är 0,26 för dem och 0,39 för de kända. Under gränsen kan modellen alltså inte
skilja en okänd ristare från en sten den bara är osäker på, och flaggan betyder *kanske* någon annan. 608 av 923
förslag för stenar utan säker ristare får flaggan; i Forskningsluckor visas bara förslag utan flagga, och stenrapporten
säger till när förstavalet ligger under gränsen. Resultatet står i `attribution.json` (`open_set`).

**Resultat i korpusen (beräkning 2026-10-05).** Attribueringsmodellen hittar rätt ristare i 72 % av fallen
(87 % bland de tre främsta) mot 19 % om man alltid gissar på den vanligaste; språk och innehåll ensamt ger 60 %,
geografi ensamt 44 %. Sannolikheterna är försiktiga: vid minst 0,5 är förstavalet rätt i 93 % av fallen. 24 av 29
ristare arbetade inom ett tydligt mindre område än slumpen ger. I Uppland följer seriationen Gräslunds kronologi
(rho 0,55; 0,54 med latituden konstant), men tidsskattningen är bara något bättre än medelåret (medelfel 21 mot
25 år). Stavningsavståndet mellan härader växer med det geografiska (Mantel r 0,29). I hela korpusen följer den
första CA-dimensionen (kristen bön mot ingen bön) varken tid eller geografi – ett mönster att pröva.

### 1j. Statistiken förklarad

Källkod: `src/r_explain.py`. Sidan Statistik (R) börjar med en sammanfattning av vad statistiken säger sammantaget, med
förslag på nästa steg, och ett kort per analys för den som inte kan terminologin: frågan analysen besvarar och varför den
är intressant, svaret i korthet med ett nyckeltal, hur säkert det är, ett förslag till tolkning och vad resultatet *inte*
säger. Texterna räknas fram ur den senaste korpusanalysen, så att siffrorna alltid stämmer med beräkningen. Säkerheten
anges för analysen som helhet, i tre nivåer (enskilda mönster märks enligt 1x):

* *Säkert*: resultatet är prövat (korsvalidering, permutationstest) och stämmer med vad forskningen utgår från.
* *Troligt*: resultatet håller statistiskt men har viktiga reservationer, t.ex. att det inte är oberoende av
  attribueringarna.
* *Osäkert*: ett mönster att pröva – svag struktur, eller en hypotes som behöver granskas runologiskt.

Tolkningarna är förslag som följer reservationerna i 1l och reglerna i 1x, inte runologiska slutsatser.

### 1k. Reproducerbarhet

`GET /api/r/package` ger en zip med R-skripten, korpusens CSV, budskapens CSV (`messages.csv`),
resultaten, `sessionInfo()` och `KOR_OM.R`, som kör om alla korpusanalyser i R utan appen, i samma ordning som appen.
Lämningarna runt stenarna körs bara om Riksantikvarieämbetets och ortnamnens filer läggs i `data/` (lamningar.csv,
kultnamn.csv, platser.csv, kyrkor.csv), och avstånden till vatten bara om Natural Earths vattenlager läggs i
`naturalearth/`, eftersom de inte följer med paketet. Sidan Statistik (R) länkar till R-skripten
på GitHub. Paketen installeras med
`Rscript r/install.R` (sf kräver GDAL, GEOS, PROJ och udunits; ragg kräver fribidi och harfbuzz; nloptr kräver
cmake).

### 1l. Begränsningar och tolkning av mönstren

**Begränsningar.**
* Attribueringsmodellen väljer bara bland sina ristare; ett förslag för en sten utan ristare vägs därför med hur
  stor andel av landskapets attribuerade stenar modellens ristare står för. Signerade stenar av ristare utanför
  modellen räknas inte som motsägelser.
* Träningsdata är Rundatas attribueringar, i Mälardalen främst Axelsons (1993), som själv vägde in stil, stavning
  och geografi. Korsvalideringen mäter därför överensstämmelse med dessa bedömningar snarare än med en oberoende
  sanning.
* Natural Earths vattenlager saknar mindre vattendrag och våtmarker – därför står brostenarna "längre från vatten"
  i analysen, vilket visar lagrets gräns och inte broarnas läge.
* Landhöjningen är en grov skattning per landskap, höjdmodellen visar dagens markyta och vägarna är simulerade
  bästa vägar, inte belagda vikingatida vägar.
* Klustringen ger svag struktur (silhuett omkring 0,33); grupperna följer kors, stungna runor och bön, inte ristare.

**Tolkning av mönstren och reservationer.** Sidan Statistik (R) och fliken "Våra resultat mot forskningen" i
Forskningsluckor visar mönstren utan anteckningar; så här ska de läsas:

* *Ristarnas områden.* Att ristare var regionalt verksamma är en grund för Axelsons attribueringar; testet visar att
  det också gäller statistiskt, men är inte oberoende av attribueringarna.
* *Avstånd till vatten.* Att stenar restes vid färdleder, även vattenleder, är en etablerad tolkning. Vattenlagret är
  grovt (1:10 miljoner); att bro- och vägstenar står "längre från vatten" visar kartlagrets gräns, inte broarnas läge.
* *Attribueringsmodellen.* Se begränsningarna ovan och den grupperade korsvalideringen.
* *Stavning per ristare.* Att ristare har egna stavningsvanor är en grund för ortografisk attribuering – och därför
  inte oberoende av attribueringarna i Rundata.
* *Dialekt.* Stavning speglar både uttal, ristarens skrivvanor och tid. Eftersom ristare ofta arbetade inom ett
  område kan en geografisk stavningsgräns lika gärna vara en gräns mellan ristarverkstäder som mellan dialekter.
* *Klustring.* Grupperna speglar främst kors, stungna runor och bön, alltså tid och kristnande snarare än ristare.
* *Seriation.* Stöder Gräslunds kronologi oberoende av ornamentiken, men årtalen är osäkra (medelfel ca 21 år mot
  25 år utan modell).
* *Oförklarade dimensioner.* När en korrespondensdimension varken följer tid eller geografi kan mönstret vara
  ristarens eller beställarens val; appen känner ingen förklaring i litteraturen, och det bör prövas.
* *Släktord och formler över tid.* Tidsindelningen bygger på Gräslunds stilgrupper och gäller bara stenar med säker
  stilgrupp.
* *Okända ristare.* En grupp är stenar som liknar varandra i handens drag och ligger nära varandra. Det kan vara en
  ristare, en verkstad med flera ristare eller en lokal tradition som flera följde, och eftersom stil och formler också
  följer tid kan en grupp delvis vara en tidsperiod i ett område. Arbetsnamnet är en etikett för gruppen och inget
  påstående om en person. Gruppen kan redan vara beskriven i litteratur som appen inte har (t.ex. i *Sveriges
  runinskrifter* för landskapet).
* *Förändring i tid och rum.* Tiden är Gräslunds stilgrupper, som bygger på Upplands ornamentik och ger intervall
  snarare än år; de daterade stenarna finns främst i Uppland och Södermanland. Stavning speglar skrivtradition och
  ristarens skola lika mycket som uttal, så en ändrad stavning är inte säkert en ljudförändring. Att ett drag tidigt är
  vanligt i ett landskap kan betyda att förändringen började där, men också att en ristarskola där hade sina vanor.
  Den justerade kurvan kan skilja sig från de råa andelarna per stilgrupp när de sena stenarna står på andra platser
  eller är huggna av andra ristare än de tidiga; båda visas.
* *Huggteknik mot ristare* (`r/technique.R`). Få stenar per ristare, olika vittring och bergart och en annan
  mätmetod än Kitzler Åhfeldts Groove Measure; resultatet är en indikation, inte en attribuering.
* *Landskapet.* Höjddata visar dagens markyta; vägar är simulerade bästa vägar, inte belagda vikingatida vägar, och
  grannstenarna kan själva stå vid vägar, så vägnätet är inte oberoende av stenarnas lägen.

### 1m. Ordförrådet per landskap och tid

Källkod: `r/words.R` (från 2026-10-18). Vilka ord på runstenarna som bär regional och tidslig signal, med samma
ordplockning som appens ordmoln (api/routers/rundata.py): orden ur Rundatas normalisering, ett ord räknas per sten,
namn ingår inte (de följer familjer, inte trakter), skadade och osäkra ord hoppas över. För varje ord med belägg på
minst 20 stenar (högst de 120 vanligaste) skattas en logistisk modell (mgcv::bam) på de daterade stenarna: landskap
med sum-kontraster (varje landskap mot genomsnittet; landskap med färre än 40 daterade stenar läggs i "övriga"),
stilgruppens mittår och logaritmen av textens längd – långa texter rymmer fler ord – med ristaren som slumpeffekt
(stenar utan säker ristare grupperas per socken, som i `change.R`). P-värdena BH-justeras över alla ord × landskap
respektive alla tidslutningar, och varje signifikant landskapssignal prövas dessutom i två sockenhalvor (varannan
socken inom landskapet) med krav på samma riktning och p < 0,05 i båda. Landskapens ordprofiler jämförs med
korrespondensanalys (paketet ca) på tabellen landskap × ord och med chi²-avstånd.

Första körningen (972 daterade av 1 848 stenar med minst tre kärnord, 75 ord, landskapen Ög, Sö, U och Vg):
fjorton ord–landskapssignaler höll i båda halvorna, och de återupptäcker kända mönster ur råorden – prepositionen
*at* i Södermanland (55 mot 19 procent i resten av landet), tvåverbskonstruktionen *let/letu ræisa* i Uppland mot
enkelt *ræisti* i Götaland, *goðan dræng* i Västergötland och själabönens *and* i Uppland. Trettio ord ändras
tydligt över tid, bland dem *gærði* som försvinner och *risti* och *letu* som växer. Att ett ord är vanligare i ett
landskap skiljer inte dialekt från formelval och beställarsmak – bara från tid och textlängd; signalerna bör läsas
ihop med språkdragen i `change.R` och `dialect.R`.

### 1n. Odaterade stenar: multipel imputation prövad och inte införd (2026-10-20)

1 313 av 2 321 runstenar saknar säker stilgrupp och räknas därför inte i tidsfrågorna (Förändring, Ordförrådet,
tidsgränsen i Pröva en egen fråga). Om de kunde tas med genom multipel imputation av tidsskiktet prövades enligt en
analysplan som låstes innan några resultat fanns (`utdata/mi/analysplan_mi.md`, SHA-256 d97e20ba…): mice med ordnad
logistisk regression (polr, m = 20) på landskap, de 22 dragen, bergart, textlängd och socknens övriga daterade stenar,
med och utan sannolikhetsmodellens språkdatering som hjälpvariabel; 30 procent av de daterade stenarna maskerades i 20
upprepningar, med ett bortfall som efterliknade det verkliga (MAR) och slumpvis (MCAR). Mått: täckningen för 95
%-intervallet kring oddskvoten för varje drag från 1050 mot före 1050, justerad för landskap, och avvikelsen från värdet
med alla daterade stenar kända.

Utfallet blev nej. Under MAR täckte intervallen det rätta värdet i 88,8 procent (utan språkdatering) och 86,7 procent
(med), under planens gräns 90, och skattningarna låg längre från det rätta värdet än analysen med bara de daterade
stenarna (medelavvikelse 0,24 mot 0,16 för log-oddskvoten). Språkdateringen förbättrade gissningen av skiktet med 0,8
procentenheter. Täckningen föll för dragen vars tidsförändring skiljer sig mellan landskapen (kristna markörer 0,45,
ristare i Rundata 0,25), eftersom imputationsmodellen inte har samspel mellan landskap och drag. Analysen med bara de
daterade stenarna höll däremot sina intervall också med det realistiska bortfallet (täckning 0,99): bortfallet gör
tidsfrågorna mindre precisa men tycks inte snedvrida dem. Appen räknar därför som förut bara på daterade stenar.
Redovisning: `utdata/mi/resultat.md`, `utdata/mi/validering.json`. En imputation med samspel kräver en ny plan.

### 1o. Budskapen: vad stenarna berättar om den döde (2026-10-27)

Källkod: `src/messages.py` (klassningen), `r/messages.R` (modellen), fliken Budskap i Statistik (R). Varje svensk
vikingatida runsten klassas efter vad den berättar om den döde: om den säger hur eller var han dog, om han dog utanför
Norden, om den nämner en resa eller vistelse utanför Norden (och åt vilket håll), gäld, guld eller silver, arv, gård och
ägande, om stenen restes åt resaren själv i livstiden, och om den döde får beröm. En regel per budskap söker i Rundatas
engelska översättning; ett budskap räknas en gång per sten. Stenar med färre än fyra läsbara ord räknas inte (budskapet
är okänt); översättarens tillägg inom parentes, ordalternativ med snedstreck och namnfragment räknas inte som ord.
Regeln prövar inte att själva minnesformeln är bevarad, så ett fragment med fyra ord räknas som en sten utan budskapen.
Götalands läsbara stenar är oftare fragment: 159 av 490 (32 %) har färre än tio läsbara ord, mot 271 av 1 275 (21 %) i
Svealand. Varje test görs därför också bara på stenar med minst tio läsbara ord (samma test, kolumnen legible_words från
src/messages.py). Resa och död borta gäller resor utanför Norden: Gotland,
Danmark, Hedeby och Skåne räknas som Norden, Finland och Estland som utanför. En resa kräver ett mål eller en riktning
("for med Ingvar", "i Grekland"); "for" utan mål räknas inte, och namnet Ingvarr räknas bara i tågets egna formler,
inte när en man bara heter Ingvarr. Jerusalem, Jordan, Italien och Langobardernas land räknas som öst, eftersom
inskrifterna själva säger att vägen dit gick österut (Sö 65, Sö Fv1954;22, U 605). "Säger hur eller var han dog" kräver
ett sätt eller en plats: "här ligger", "begravd" och ett ensamt "dog" räknas inte; Rök (Ög 136) klassas bara på
minnesformeln, eftersom resten handlar om sagogestalter. Beröm räknas inte när den berömde är den som reste eller
ristade stenen (också i presens, "raises", och utan verb, "able lads in memory of"), och inte när berömmet gäller Gud,
Maria ("God's good maid"), minnesmärket ("the good landmark") eller ett bruk ("made good use of").

Reglerna jämförs med två handkodningar (`scripts/check_messages.py`): de 55 nordiska inskrifter som nämner en resa
västerut (`utdata/brittiska/hemma_kodning.csv`), där död borta stämmer i 50 av 51 fall (den enda avvikelsen, Sö 173,
är en man som var i väst men dog i öst, och där har regeln rätt), och 162 handkodade stenar om österfärder och
angränsande fall (`data/messages_facit_ost.csv`: alla 97 stenar som de tidigare reglerna räknade som österfärder, 32
svåra fall och 33 slumpvis dragna stenar), där resa stämmer i 161, död borta och dödsuppgift i alla 162 och riktningen
i 94 av 95. Österurvalet kodades medan reglerna rättades och är därför inte ett oberoende prov; det slumpvisa urvalet
(33 av 33 rätt) är närmare ett sådant. Övriga budskap (gäld, arv, gård, egen sten, beröm) är bara stickprovskontrollerade. Överensstämmelsen skrivs till
`data/messages_check.json` (med md5-summan av `src/messages.py`), som `r/messages.R` läser och fliken Budskap visar.

Modellen prövar varje budskap mot landsdel (Götaland, Svealand, Gotland, Norrland) med logistisk regression (mgcv),
tidsskikt efter stilgruppens mittår (odaterade stenar som eget skikt) och ristaren som slumpeffekt (stenar utan säker
ristare grupperade per socken, som i 1h). Som kontroll görs samma modell bara på daterade stenar, med mittåret som
jämn kurva. När ett budskap saknas helt i en landsdel går ingen oddskvot att skatta, och då redovisas Fishers exakta
test; det gör det också när budskapet är för sällsynt för modellen (färre än 15 stenar med budskapet, eller utan det, i
Götaland och Svealand tillsammans), och då redovisas Fishers oddskvot utan justering. Resestenarna prövas för sig:
bland stenar om en resa utanför Norden, säger stenen att mannen dog utanför Norden (budskapet "död utanför Norden"; en
död hemma eller i Norden, som Sö 55 och U 539, räknas inte)? Prövat mot landsdel och riktning (väst/öst) med exakt
Mantel–Haenszel med riktningen som skikt, samma test med riktning × tidsskikt som skikt (skikt där bara en landsdel
eller ett utfall finns bär ingen information och tas bort; resetesten gäller bara stenar med en enda riktning, så 7
resestenar med båda riktningarna eller ingen räknas inte: Vg 197 i Götaland, Sö 173, U 349, U 504, U 611, U 614 och
U 948 i Svealand), logistisk regression med riktning och tidsskikt, samma
modell med ristaren eller socknen som slumpeffekt, och en interaktion (likelihoodkvot) för om skillnaden mellan
landsdelarna skiljer sig mellan väst och öst, redovisad med kvoten mellan oddskvoterna och dess intervall. Ett högt
interaktions-p visar inte att skillnaden är densamma; med få götländska resestenar är testet svagt.

Resultat 2026-10-27 (efter rättade budskapsregler, samma dag):

* I Götaland säger 24 av 27 resestenar med en enda riktning att mannen dog utanför Norden (13 av 15 västerut, 11 av 12
  österut); med Vg 197 är det 25 av 28. I Svealand är det 62 av 102 (11 av 29 och 51 av 73).
* Med riktningen som skikt: oddskvot 7,9 (95 % KI 2,0–47), p 0,0008. Med riktning × tidsskikt som skikt: 5,9 (1,4–36),
  p 0,008, i 5 skikt med båda landsdelarna och båda utfallen, som rymmer 105 av 129 resestenar. Logistisk regression
  med tidsskikt: 6,9 (1,7–27), p 0,006. Bara stenar med minst tio läsbara ord, med riktningen som skikt: 10,4 (2,1–105),
  p 0,0008 (114 resestenar).
* Med ristaren eller socknen som slumpeffekt är skillnaden inte signifikant (oddskvot 8,7, 95 % KI 0,4–189, p 0,17),
  eftersom de götländska resestenarna är få och spridda över många socknar.
* Någon skillnad mellan väst och öst går inte att visa (interaktion p 0,64), men intervallet för kvoten mellan
  oddskvoterna (öst/väst 0,51, 95 % KI 0,03–7,9) är brett. Västerut ger Fishers exakta test oddskvot 10 (1,8–109),
  p 0,003, och modellen med tidsskikt 8,2 (1,4–47), p 0,019; österut Fisher 4,7 (0,6–213), p 0,17, och modellen 4,5
  (0,5–39), p 0,18.
* Arv (19 av 1 275 mot 0 av 490) och stenar resta åt sig själv (25 av 1 275 mot 0 av 490) finns i Svealand men inte i
  Götaland, också med minst tio ord (Fisher p 0,011 och 0,002).
* Götalandsstenarna berömmer den döde oftare: 92 av 490 mot 136 av 1 275, oddskvot 1,8 (p 0,003); med minst tio ord
  81 av 331 mot 129 av 1 004, oddskvot 1,8 (1,2–2,8), p 0,007.
* Götalandsstenarna nämner resor mer sällan: 28 av 490 mot 108 av 1 275, oddskvot 0,50 (0,30–0,83), p 0,007. Med minst
  tio ord håller skillnaden, men svagare: 25 av 331 mot 96 av 1 004, oddskvot 0,56 (0,32–0,98), p 0,04. Utan justering
  för tid och ristare är den inte signifikant (Fisher p 0,06 vid fyra ord, 0,32 vid tio).
* Att Götalandsstenarna mer sällan säger hur mannen dog (oddskvot 0,56, p 0,02) håller inte med minst tio ord (0,64,
  p 0,11).

Om skillnaden i resestenarna speglar en sed i hur man berättade eller att götländska resenärer oftare dog borta går
inte att skilja med de här stenarna. En sten som inte säger att mannen dog borta behöver inte gälla någon som kom hem
(levande resenärer, stenar resenären reste själv, fragment). Stenarna visar vad de efterlevande valde att berätta, inte
hur många som dog.

En granskning samma dag ändrade två saker. Reglerna rättades åt båda håll: namnet Ingvarr hade räknats som en resa
österut (11 stenar utan död borta föll bort), och nya ortnamn (Lombardiet, Lívland, Tafeistaland), matchning över
luckor och "dog med dem" lade till 8 dödsfall utanför Norden; att Gotland nu räknas till Norden påverkar inte
resestenarna. Utfallet byttes också, från "säger hur eller var han dog" till "dog utanför Norden", så att
en död hemma (Sö 55) eller i Norden (U 539) inte räknas. Före båda ändringarna var siffrorna 24 av 28 mot 58 av 106;
med de gamla reglerna och det nya utfallet 23 av 28 mot 55 av 106. Siffrorna ovan gäller efter båda ändringarna.

### 1p. Nya mönster märks (2026-10-27)

Källkod: `src/pattern_registry.py`, `data/pattern_registry.json`. Varje mönster i korpusanalyserna förs in i ett
register när det först dyker upp, med datum, och statusbyten (till exempel från "mönster att pröva" till "bekräftar")
förs in när de sker. Statistik (R) och Forskningsluckor märker mönstret **Nytt** de första 30 dagarna efter att det
dök upp och **Ändrat** de första 30 dagarna efter ett statusbyte, och Statistik (R) listar dem överst. Registret
såddes 2026-10-27 med de 40 mönster som fanns i körningen från 2026-10-21; de räknas som kända sedan tidigare. Nyckeln
är en per mönster och ändras inte med statusen (till exempel kinship:<relation> både som begränsning och som mönster att
pröva); korrespondensanalysens mönster har dimensionen i nyckeln (formula:<dim>, ca_unexplained:<dim>). Svaren från
Statistik (R) och Forskningsluckor sparas per dag och per version av fynd- och länkfilerna, så att märkningen följer
30-dagarsfönstret.

### 1q. Fynd per sten utöver attribueringen (2026-10-27)

Källkod: `src/stone_findings.py`. Listan Fynd per sten (Statistik (R) och Våra resultat i Forskningsluckor) tar
utöver ristar- och dateringsfynden med sådant om en enskild sten som inte står i Rundata, i samma form (stämmer, nytt,
motsäger, med belägg, nyhet och relevans):

* **Luckor i texten:** förlorade runor som sannolikhetsmodellen fyller i med minst 80 % kalibrerad säkerhet där Rundata
  inte återställt ordet (`data/textmodel_candidates.json`, avsnitt 8.1), bara på svenska vikingatida runstenar (andra
  föremål visas i fliken Luckor i texten med egna tal). Belägget är den kalibrerade sannolikheten. Raderna är
  kandidater att granska mot foto eller skanning, inte färdiga fynd, och får därför bedömningen "Kandidat att granska mot
  foto eller skanning" i stället för tumregelns etiketter.
* **Runor 2020:** stenar som Riksantikvarieämbetets nyare utgåva anger som inte stående på ursprunglig plats men som
  appens flyttregel (`src/r_bridge.is_moved`; Rundata har ingen flyttflagga, regeln läser Rundatas plats och placering)
  räknar som stående på plats: 154 runstenar, alla *motsäger*, med bedömningen "Uppgift i nyare källa – kontrollera
  platsen". Till och med 2026-10-27 var de 187; 30 av dem hade en placeringstext som redan säger att stenen står
  någon annanstans, och sedan flyttregeln läser placeringstexten (avsnitt 1c, `src/placement.py`) räknas de som
  flyttade och ger inget fynd. Dessutom läsningar där Runor har färre förlorade och
  fler säkert lästa runor än Rundata (runor inom parentes räknas inte), bara på svenska vikingatida runstenar (1: Sö 260;
  andra föremål redovisas för sig i `utdata/runor/jamforelse.json`). Runor matchas mot Rundata på exakt signum – i
  jämförelsen, i fynden och på inskriftssidan (`src/runor.py`) – så att Närkes Nä 11 inte blandas ihop med Norges N A11.
  Uppgifterna är en nyare källa, inte appens upptäckter, och får därför lågt nyhetsvärde (0,3) och en fast bedömning.
* **Samma familj (namnlänk):** länkarna ur avsnitt 1r utan motsägelser i släktskap eller tid (28 länkar). Varje länk
  står på båda stenarna, så de ger ett fynd på varje svensk runsten i länken (danska och norska stenar ingår i
  länkmodellen men får inga egna fynd; och fem av länkarna knyter Rundata redan ihop); i rubriktalet "sannolikt ny kunskap" räknas varje länk en gång. Länkar som Rundata redan gör – parstenar och stenar som Rundatas
  anmärkningar knyter ihop på annat sätt ("Utgör ett monument tillsammans med …") – räknas som *stämmer* (5 länkar).
* **Egna fynd:** det vi kommit fram till om en sten i artiklar och analyser, fört in för hand med källa och datum i
  `data/stone_findings.json`. En rad med okänt verdict (annat än stämmer, nytt, motsäger), utan signum eller text,
  eller med belägg eller nyhet utanför 0–1 hoppas över och loggas. Bara svenska vikingatida runstenar tas med; ett eget fynd om ett annat
  föremål eller en sten utanför Sverige hoppas över och loggas.

Fynden gäller en sten, inte en ristare. Relevansen räknas därför bara efter om stenen finns kvar (0,6) eller är
försvunnen (0,3), inte efter hur många stenar i landskapet som har ristare. De får ingen tolkningsnivå (avsnitt 14d).

### 1r. Samma familjer på flera stenar: länkmodellen (2026-10-27)

Källkod: `src/entities.py` (enheterna), `src/linking.py` (länkarna), `scripts/link_entities.py` → `data/links.json`.
Ur Rundatas engelska översättning läses varje runstens personer med roll (den som reser, den som minns, ristaren,
nämnd), släktskap ("Ketill, his son"; "Alríkr, Sigríðr's son"), gårdsnamn (namn efter in/at/from/on, och efter of när
namnet har en ortnamnsändelse) och händelser (resmålen utanför Norden, Ingvarståget, även "in Ingvarr's retinue", och
Knuts gäld, även "when Knútr attacked England"). Ett namn räknas bara när det motsvarar ett ord som normaliseringen
märker som namn, också när det är delvis kompletterat ("[Íg]ulfastr"). Satserna delas vid punkt, semikolon och utrop men
inte vid en lucka (...), så att den som reser och den som minns på en skadad sten hamnar i samma sats. Ett namn som efter en lucka står i en
annan utsaga räknas bara som nämnt, och ingen blir ristare över en lucka om han har ett eget verb före den. En medresare med
egen minnesformel ("…, and Heðindís in memory of her husbandman") räknas som resare, beställaren i "had the stone cut"
och "ordered Œpir to carve" som resare och den som får uppdraget som ristare. Ett sammansatt släktled ("his father's
father", "his brother's son") blir farfar, brorson och så vidare och räknas aldrig som förälder; ett pluralt släktord
gäller hela uppräkningen, både efter namnen ("Jafri and Vígr, his brothers") och före dem ("his sons Sveinn and
Hrœmingr"); "mother-in-law" räknas aldrig som mor, och "his wife's brother" blir svåger. Släktfakta ges till resarna i samma sats, men inte till en
resare med egen släktskap och aldrig en person till sig själv. Bara runstenar ingår. Extraktionen är prövad för hand på
två urval om 60 runstenar. Det första (frö 2026, 92 personer) användes medan reglerna rättades och är alltså ingen
oberoende prövning: rätt roll för 98 % av personerna (86 % före rättelserna). Det andra (frö 4242, 135 personer, 52
släktfakta) märktes blint, innan programmets svar setts: rätt roll för 90 % av personerna (81 % före rättelserna), rätt
släktskap för 78 % av de minnes som hittas, och 38 av 52 släktfakta (73 %) hittas, och av de 41 fakta programmet gav vid den blinda prövningen var 3 fel (efter en rättelse som urvalet visade på, att
pronomenet ska stämma med resarna, är 1 av 39 fel, men den siffran är inte längre blind). Rollerna blir alltså nästan alltid rätt, men ungefär vart fjärde släktband på stenen fångas inte. Det som oftast
missas är ett släktord som skiljs från namnet av ett komma eller ett ortnamn, släktskap utanför ordlistan och namn som
bara finns som fragment.

Två runstenar länkas när de delar minst två personnamn eller ett gårdsnamn (ristarna räknas inte), och minst ett av de
delade namnen står på högst 60 runstenar: par som bara delar de vanligaste namnen (Sveinn, Bjôrn, Þorsteinn, Ulfr)
prövas inte, varken i data eller i nollmodellen. Varje delat namn vägs efter hur ovanligt det är, log(N/n).
Nollmodellen blandar personnamnen mellan stenarna inom landskapet 2000 gånger; varje sten behåller sitt antal namn och
varje namn sitt antal stenar, och ingen sten får samma namn två gånger. Andelen falska länkar vid en viss styrka (q) är
antalet lika starka länkar i nollmodellen delat med antalet i data. Slumpfelet i q redovisas med ett intervall
(nollkörningarna dragna om 500 gånger) och med tre andra slumpfrön. Den strängare nollmodellen blandar inom häradet, så
att lokala namnseder inte ser ut som släkter. En länk avfärdas när stenarna motsäger varandra: olika fäder eller olika
mödrar för samma namn (en mor på den ena stenen och en far på den andra är ingen motsägelse; förälderns kön tas ur släktorden i hela
materialet, därefter ur pronomenet vid den dödes släktord, "his son" eller "her son", och sist ur namnets ändelse, som
stämmer för 661 av 729 namn vars kön materialet ger och motsäger 4), eller en person som är död
på en sten och reser en sten som enligt stilgrupperna är minst 30 år yngre. Tidsregeln gäller inte stenar på samma
plats (inom 1 km) eller stenar som Rundatas anmärkningar knyter ihop, eftersom stilgruppernas datering kan ha fel
ordning (U 845 och U 844). En motsägelse är därför ett skäl till tvivel, inte ett motbevis. En länk markeras som känd
i Rundata när någon av stenarnas anmärkning nämner den andra stenen ("Parsten till", "Utgör ett monument tillsammans
med", "Samma brödrakrets som nämns på"). Ett första försök med Fellegi–Sunter-länkning skattad med EM gav upp till en
fjärdedel av alla namnpar som träffar, eftersom modellen fångade "två stenar i Uppland med kända ristare" i stället för
identitet; den metoden används inte.

Resultat 2026-10-27 (efter granskningen samma dag): 420 par delar namn (63 par som bara delar de vanligaste namnen
prövas inte), slumpen ger omkring 365. 28 länkar håller med q under 0,1, lika många i alla omdragningar och med alla
fyra frön (23 med den strängare nollmodellen). De står i median 0,3 km isär, 89 % inom 10 km: familjerna som går att
följa över flera stenar höll sig i stort sett på samma plats. Fem av länkarna knyter Rundata redan ihop; de visas som
bekräftelser, inte som nya fynd. Ásfríðrs stenar i Hedeby (DR 2, DR 4) hittas. Jarlabankes fem stenar om Täby hittas
inte: de delar bara Jarlabanke och Täby, och q blir 0,107 (0,105–0,109 med slumpfelet), strax över gränsen. Ingen
länk över landskapsgränserna håller. Den första versionen (q 0,0986, 35 länkar, två länkar mellan Uppland och
Västmanland) byggde på en nollmodell som tappade namn när en sten drog samma namn två gånger, och på att ett namnord med
två läsningar blev två personer: Vs 22 har ett enda namnord, "Rúna", som Rundata översätter både "Runa" och "Runi's".
Nu bär varje citerad namngrupp i normaliseringen högst en person (förledet i ett sammansatt namn, "Hrafnunga-"Tófi, är
en egen namngrupp), och en person vars namnord också kan läsas som ett annat namn räknas som osäker och används inte
för att länka stenar. Av Rundatas 14 parstenar hittas 2; av de 12 som missas delar 5 inget läst namn alls, 3 bara ett
namn och 4 två eller fler utan att länken skiljer sig från slumpen. Två länkar mellan landskap som först såg starka ut
avfärdas av motsägelser i släktskapen (U 759–Vg 59: olika fäder; Hs 14–Sö 11). Länkarna visas som fynd per sten på de
svenska runstenarna och som mönstret i Statistik (R) under Formler och släkt.

### 1s. Samlad datering av odaterade stenar: prövad och inte införd (2026-10-27)

Om språkdrag, innehåll, kors, runtyp, seriationen och platsen tillsammans kan datera de 1 313 runstenarna utan
stilgrupp prövades i tre versioner, var och en med en plan låst före körningen (`utdata/datering/analysplan*.md`):
kvantilregressionsskog (v1), samma med konforma intervall (v2) och en sannolikhetsskog över tidsskikten (v3), alla med
femfaldig korsvalidering grupperad per socken. Kraven: medelfelet minst 15 % under landskapets median, en osäkerhet
som håller och ett medelfel i Uppland högst 2 år större än seriationens. Utfallet blev nej. Räknat över alla 1 008
daterade stenar daterar skogens median 25 % bättre än landskapets median (15,1 mot 20,2 år), och på de 501
upplandsstenar som har seriationsdatering bättre än seriationen (16,4 mot 20,6). Nästan hela vinsten ligger i
Uppland: på alla 560 upplandsstenar 17,4 år mot landskapets median 26,3. Utanför Uppland är modellen bara 4 % bättre
(12,1 mot 12,6), där i första hand genom platsen, och sämre än landskapets median i Sö, Öl, G, J och Vr; språkdrag
och innehåll ensamma slår inte medianen där. För texter på högst tre ord, som 57 % av de odaterade stenarna har, är
vinsten 7 %. Årsintervallen "täcker" 96 % i stället för 80 %, men det säger lite: stilgruppernas mittår har bara sex
värden, intervallens gränser hamnar på dem och 57 % av stenarna ligger exakt på en gräns, så kravet kan varken klaras
eller fällas på ett meningsfullt sätt (den konforma korrektionen blev 0). I v3 klarar den mest sannolika klassens
sannolikhet kalibreringskravet (fel 0,046), men sannolikheterna är något för försiktiga: i de mellersta facken träffar
modellen 6–10 procentenheter oftare än den anger. v3 föll på att planen tog det förväntade året (18,1 år) som
punktskattning; det drar mot mitten när sannolikheterna är utspridda. Sannolikheternas median ger 15,4 år, men det
syntes först efter körningen och kan inte prövas i en ny plan på samma 1 008 stenar, eftersom en sådan plan inte vore
låst före resultatet (avsnitt 1x). Enligt plan v3 är arbetet med samlad datering avslutat tills nya data finns: finare
facit (dendro- eller arkeologiska dateringar, uppdelade stilgrupper) eller nydaterade stenar som inte ingått i någon av
körningarna. Appen räknar som förut bara på daterade stenar (`utdata/datering/resultat.md`).

### 1t. Luckor i texten på danska och norska inskrifter: prövat och inte infört (2026-10-27)

Luckinventeringen (avsnitt 8.1, `scripts/runlm_gaps.py --countries dk,no`) kördes med tm19-inställningarna på de
vikingatida inskrifterna med signum DR och N, femfaldigt över stenarna, enligt en plan låst före körningen
(`utdata/runlm_forfining/tm19/analysplan_dkno.md`). Facit var de 81 luckor Rundata återställt. Modellen kom fram till
Rundatas ord i 43 % (Danmark 51 %, Norge 17 %) mot 75 % för de svenska, och bland förslag med kalibrerad sannolikhet
minst 0,8 i 67 % (svenska 95 %). Båda kraven föll, och Luckor i texten visar som förut bara svenska inskrifter. Modellen
har lärt sig språket främst av svenska inskrifter; för danska och norska krävs egna språkskikt och en kalibrering per
land (`dkno_resultat.md`). Andra länder söks aldrig igenom.

### 1u. Människorna: vem reste stenen och efter vem (2026-10-28)

`src/people.py` ger en rad per vikingatida runsten: antal resare och deras kön, antal döda och deras kön, den dödes
relation till resaren i grupper (barn, förälder, syskon, make/maka, annan släkt, utan släkt), om stenen restes åt
resaren själv, beröm (*drengr*, *þegn*, god/bäst), landsdel och budskapet ”dog utanför Norden” ur `src/messages.py`.
Personerna och relationerna kommer ur länkmodellens extraktion (`src/entities.py`, 1r); relationer utan namn (”in memory
of their father”) läses ur texten.

Könet bestäms i ordningen relation (mor, dotter, hustru … / son, far, bror …), en ensam resares possessiv i sin formel
(”her son”, ”his son”) och den som reser efter sin make eller hustru, ett namnlexikon byggt ur de stegen på alla
runstenar, och sist namnets ändelse (-laug, -hildr, -fríðr, -gerðr, -dís … eller -a för kvinnor; -r, -i, -n, -l för män).
Samma ordning som artikeln om kvinnorna, nu på entitetsmodellens personer.

Kontroll mot handkodning (`data/people_check.json`): urval 1, 60 slumpvisa läsbara svenska stenar som reglerna
justerades mot; urval 2, 40 nya stenar som reglerna aldrig sett, kodade före jämförelsen: kvinna bland resarna 39/40,
antal män bland resarna 38/40, relationsgrupp 38/40. Felen gäller stenar med luckor, där namn och relationer missas
snarare än läggs till.

`r/people.R` prövar sex frågor enligt den låsta planen `analysplaner/2026-10-28-manniskorna.md`: kvinna bland resarna
mot landsdel och mot tid; *drengr*, *þegn* och död utanför Norden mot om den döde (alla döda män) var son eller bror
eller far eller make; bro eller väg mot kvinna bland resarna. Logistisk regression (mgcv) med landsdel, tidsskikt och
ristaren som slumpeffekt (som 1o), Holm-korrigering över de sex testen, replikering i två halvor delade socken för
socken (som 1h) och fem robusthetsprov (minst tio läsbara ord, kön bestämt för alla resare, utan ristarens
slumpeffekt, bara Uppland, söner mot fäder). Status: bekräftar (Holm-p < 0,05 och p < 0,05 åt samma håll i båda
halvorna), mönster att pröva (Holm men inte båda halvorna), indikation (bara okorrigerat p < 0,05). Första körningen
(2026-10-28): kvinna bland resarna 31 % i Svealand mot 17 % i Götaland (bekräftar); söner och bröder dog utanför
Norden på 10 % mot 3 % av stenarna efter fäder och makar (bekräftar); *drengr* om söner och bröder och *þegn* om fäder
och makar (mönster att pröva); kvinnor bland resarna ökar över tid (indikation); bro eller väg är inte vanligare med
en kvinna bland resarna (ingen skillnad).

### 1v. Robusthetstrappan och den gemensamma justeringen (2026-10-29)

Mönstren i Statistik (R) kommer ur olika moduler med olika test, så det har inte gått att jämföra hur väl de håller.
`src/robustness.py` och `r/robustness.R` lägger samma kontroller på varje mönster som kan räknas om sten för sten. Varje
mönster blir då ett samband mellan ett utfall *y* (0/1) och en jämförelse *x*.

Jämförelserna per typ av mönster:

- Förändring: tiden i 50-årssteg (stilgruppens mittår), med 1000 mot 1100 som skillnad.
- Regional skillnad: det visade paret av landskap. Paret är utvalt.
- Samband: stentypen.
- Hot spot: inom klustrets radie mot utanför. Klustret valdes på hela korpusen, så trappan prövar inte själva valet.
- Kultnamn: bön inom 2 km från ett teoforiskt namn.
- Budskap: Götaland mot Svealand.
- Människorna: samma jämförelser som `r/people.R`.

Alla mönster använder samma tidsskikt som Pröva en egen fråga (1y). De justerade stegen kan därför skilja sig något från
modulens egen siffra.

Stegen:

1. **Rått:** logistisk regression *y ~ x*.
2. **Justerat:** för landskap och tidsskikt. Den justering som är själva jämförelsen tas bort. En landskaps- eller
   landsdelsskillnad justeras alltså inte för landskapet, och en tidsförändring inte för tidsskiktet.
3. **Ristaren som slumpeffekt** (lme4). Stenar utan säker ristare grupperas per socken.
4. **Socknen som slumpeffekt.** Här skiljs socken från region (punkt 2 i planen): håller en skillnad mellan landskap
   också när socknarna får variera sinsemellan, eller är den några socknars egenhet?
5. **Platsen som yta** (mgcv, *s(öst, nord)*), utan flyttade stenar. Steget görs inte där platsen är själva
   jämförelsen.
6. **Halvorna:** det justerade steget i var halva av korpusen. Hela socknar fördelas växelvis inom landskapet, som i
   `src/question.halves`. Halvorna bestäms en gång och oberoende av mönstren.
7. **Utan ett landskap i taget:** landskap med minst 30 stenar. Riktningen ska hålla utan vart och ett av dem. p < 0,05
   krävs bara där minst två tredjedelar av stenarna är kvar: utan Uppland försvinner ofta halva underlaget, och ett
   test på halva materialet kan inte krävas vara signifikant. Den sämsta utgången redovisas, liksom de landskap utan
   vilka riktningen vänder. Steget görs inte för hot spots, eftersom varje kluster ligger inom ett landskap.
8. **Utan flyttade stenar:** dels enligt Rundatas placering (1c), dels också enligt Runor 2020:s uppgift om
   ursprunglig plats (original = nej; punkt 7). Steget görs för mönster som hänger på platsen.

Ett steg håller när p < 0,05 och riktningen är densamma som i det justerade steget. Kortet visar ”Robust *k*/*n*”.

Till varje mönster läggs också:

- **Skillnaden i procentenheter** (marginaleffects::avg_comparisons på den justerade modellen, medelvärdet över
  stenarna som de är), med andelen på var sida. En ”typisk ristare” (re.form = NA) prövades först, men med en stark
  ristareffekt hamnar den vid skalans kant och döljer skillnader som syns tydligt i datan.
- **En modellkontroll** med DHARMa: residualernas fördelning, överspridning och kvarvarande rumsligt mönster.
- **Kodningsfelen**, där en regel kodar utfallet eller jämförelsen och det finns ett handkodat facit. Underlaget är
  budskapen resa och död utanför Norden (`data/messages_facit_ost.csv`, `utdata/brittiska/hemma_kodning.csv`) och
  en kvinna bland resarna (`data/people_check.json`, båda urvalen, 100 slumpvisa stenar). Ur facit räknas hur ofta
  regelns ja och regelns nej stämmer. I 200 omräkningar dras varje stens ”sanna” värde ur de andelarna (Jeffreys
  fördelning), och den justerade modellen räknas om. Resultatet är hur stor andel av omräkningarna där mönstret håller.
  Budskap utan facit (beröm, arv, gäld, gård, egen sten) märks som okontrollerade.

**Gemensam justering och bekräftelse (punkt 3).** Alla visade mönster får en gemensam Benjamini–Hochberg-justering
(*q_global*). Där trappan finns används dess justerade p, annars mönstrets eget p. Ett mönster som bara redovisar
q tas med som q, vilket är försiktigt. Där jämförelsen själv valdes ur datan – en hot spot, det landskapspar som skilde
sig mest – vet trappans p inget om valet. Där används det största av trappans p och mönstrets eget, till exempel
scanstatistikens p för ett kluster.

Ett mönster är bekräftat när det håller i båda halvorna och *q_global* < 0,05. Mönster utan trappa bedöms på sin egen
halvprovning. Mönsterregistret märker nu ett nytt mönster ”Nytt” först när det är bekräftat; innan dess märks det
”Nytt, obekräftat” (`src/pattern_registry.annotate`).

Trappan räknas sist i korpusjobbet och sparas som `robustness.json` i jobbets mapp. Nyckeln bygger på underlaget och
skriptet. Saknas trappan räknar API:t den i bakgrunden, och mönstren visas utan den så länge.

Mönster som prövas på annat sätt får ingen trappa och behåller sitt eget test. Det gäller avstånd mot slumppunkter,
attribueringsmodellen, seriationen, ristargrupperna, de okända ristarna och länkarna. Detsamma gäller budskap som bara
finns i en landsdel, eftersom en nollcell inte kan skattas med regression.

### 1x. Försiktighet i påståendena, djärvhet i hypoteserna

**Förregistrerade analysplaner (från 2026-10-20).** En artikel som gör ett nytt anspråk hänvisar till en analysplan som
skrevs och låstes (SHA-256) innan resultaten togs fram: fråga, underlag, primärt mått och gräns, nollmodeller,
känslighet och vad som inte får göras. Mallen är `ANALYSPLAN.md`; planen ligger i `utdata/<spår>/analysplan.md` med
hashen i `analysis_plan.sha256`, och hashen står i artikelns ruta "Så räknade vi". Rak-studien (2026-10-05) var den
första; toleranslagret (textmodel-19) och bytet till Runor 2020 är de nästa.

Appens uppgift är att hitta tydliga mönster som ingen sett tidigare. Det kräver två saker som lätt blandas ihop: stränghet
när något *påstås* och djärvhet när något *föreslås*. Sedan 2026-10-12 hålls de isär:

* **Varje mönster har tre delar.** *Vad vi ser* (påståendet, med signifikans och osäkerhet), *hypotes* (vad mönstret
  kan betyda, djärv med avsikt och märkt som hypotes) och *så kan den prövas* (vad vi borde se om hypotesen stämmer och vad
  som skulle fälla den). Förbehåll och kontroller ligger i en fällbar ruta så att de inte dränker idén. Två ordförråd:
  påståenden säger "visar" eller "är förenligt med", hypoteser säger "vi föreslår" eller "kan tyda på".
* **Upptäckt och bekräftelse har olika krav.** Ett mönster *upptäcks* när det klarar Benjamini–Hochberg (andelen falska
  upptäckter bland de redovisade under 5 %). Det kallas *bekräftar* (känt i forskningen) bara när det också klarar Holm
  (risken för ens ett falskt resultat under 5 %) och håller i båda halvorna av korpusen. Ett nytt mönster som håller i
  båda halvorna är ett *mönster att pröva*; ett som inte gör det är en *indikation* – en idé, synlig men med förbehåll.
* **Två halvor av korpusen** (r/change.R): socknar fördelas växelvis på två halvor inom varje landskap, i ordning efter
  sockenstenarnas medeldatering, så att båda halvorna täcker samma trakter och samma tid. Mönstret anpassas på nytt i
  varje halva; det håller om riktningen (eller toppen) är densamma och signifikant i båda. Signerade stenar används inte
  som facit: signaturer blir vanliga först sent (4 % av RAK-stenarna, 33 % av Pr5), så de skulle gynna de sena mönstren.
* **Kontroller som besvarar andra frågor fäller inte ett mönster.** En trend som syns mellan ristare men inte inom dem kan
  ha spridits genom generationsskifte – i sig en iakttagelse. Utan den tidigaste och senaste stilgruppen försvinner en
  stor del av tidsaxeln, så ett svagare resultat där är väntat. Landskapsjämförelser utanför Uppland och Södermanland kan
  bli mönster att pröva när skillnaden håller med dateringarna förskjutna 25 år åt båda håll. Små men stabila effekter
  (under 10 procentenheter) märks som små men redovisas som mönster. Sambandet mellan brostenar och själsbön kontrolleras
  med textlängden *utan* bro- och bönefraserna (brofrasen gör själv texten längre); hela textlängden redovisas också.
* **Regel för kritik** (också Runes instruktion): fel – siffror, nämnare, dubbelräkning, vilseledande ord – rättas alltid.
  Försiktighet ändrar formuleringen men tar aldrig bort ett ärligt märkt mönster.

### 1y. Pröva en egen fråga

Kortet *Pröva en egen fråga* på Statistik (R) (`src/question.py`, `POST /api/research/question`, sedan 2026-10-20) låter
en forskare ställa en egen fråga till korpusen med samma disciplin som R-modulerna: är draget A vanligare eller
ovanligare där B gäller? Ingen fri text och ingen AI; frågan byggs av två listor.

* **Underlag.** Samma rader som korpusanalyserna i R (`r_bridge.corpus_rows`): bara runstenar, 2 321 stycken. A är ett av
  46 drag: kartans mönster (tro, skrift, innehåll), språkdrag ur avsnitt 9 (*auk*, *at* i minnesformeln, h skrivet,
  nasal skriven, stungen e, y och g, det vanligaste skiljetecknet: kolon, punkt, kryss eller blandat), bindrunor,
  kortkvistrunor, bönens ordval (*and*, *sál*, *Guðs móðir*), *Guð*, England och Grekland, ordet *kumbl*, släktord och
  hedersord (fader, moder, broder, son, make, *drængR*, *þegn*), självminne, tre ristaruppgifter (ristare, osäker
  ristare, signerad) och om stenen är förlorad. Ord räknas i Rundatas normalisering och avgörs bara på stenar med minst
  tre kärnord, som i Ordförrådet (1m); namn räknas inte, utom där ordet självt är ett namn (Guð, Ænglandi, Grikkjum). B är ett annat drag, ett
  landskap (minst 15 stenar), en tidsgräns (1020, 1050 eller 1075 som på kartan, efter stilgruppens mittår) eller en
  bergartsfamilj (avsnitt 11). Stenar där A eller B inte kan avgöras räknas inte, och antalet redovisas.
* **Justering.** Mantel–Haenszel över skikt: landskap × tidsskikt (före 1020, 1020–1050, 1050–1075, 1075 och senare,
  odaterade stenar som ett eget skikt) för drag och bergart, bara tidsskikt för ett landskap och bara landskap för en
  tidsgräns. Oddskvoten har ett 95 %-intervall enligt Robins–Breslow–Greenland och testet är CMH med
  kontinuitetskorrektion. Andelarna visas råa med Wilsons intervall och skillnaden med Newcombes.
* **Halvprovet.** Halvorna är desamma för alla frågor och bestäms en gång: hela socknar växelvis inom varje landskap i
  ordning efter socknens medeldatering (odaterade sist), som i `r/change.R` och `r/hotspots.R`. Ett mönster *håller*
  bara om CMH-testet ger p < 0,05 i hela korpusen och samma riktning med p < 0,05 i båda halvorna; annars är det *bara i
  hela korpusen*. **Ristarprovet** räknar om frågan utan var och en av de fem ristare som har flest stenar i underlaget
  och redovisar den sämsta utgången.
* **Två kontroller i R** (`r/question.R`, sedan 2026-10-20). *Ristaren som slumpeffekt*: en logistisk blandad
  modell (lme4::glmer) med A som utfall, B, landskap och tidsskikt som fasta termer och handen – den säkra ristaren, för
  stenar utan säker ristare socknen, som i `r/words.R` – som slumpvis nivå, så att en flitig ristares stenar inte räknas
  som många oberoende belägg. *Platsen som yta*: en logistisk GAM (mgcv) med B, tidsskiktet och en tunnplåtsyta över
  stenarnas läge (s(öst, nord), k = 60) i stället för landskapsgränserna; flyttade stenar räknas inte, och kontrollen
  görs inte för landskapsfrågor, där platsen är själva jämförelsen. En kontroll *håller* när B:s koefficient har samma
  riktning som Mantel–Haenszel och p < 0,05 (Wald). Ett mönster som håller i halvorna men inte i den första kontrollen
  märks *beror på ristarna*, i den andra *kan vara platsen*. Svaret räknas en gång per korpusversion och fråga (några
  sekunder) och sparas. Exempel: kors är ovanligare på sandsten (oddskvot 0,35, båda halvorna, också med ristaren som
  slumpeffekt), men med platsen som yta blir oddskvoten 0,78 (p 0,58) – sandsten och färre kors hör hemma i samma trakter.
  De kända mönstren ovan håller i båda kontrollerna (`tests/test_question.py`).
* **Många frågor.** P-värdena för de frågor som ställts tidigare under besöket skickas med och justeras tillsammans med
  den nya (Benjamini–Hochberg). Ett mönster som håller i halvorna men inte efter justeringen märks så. Listan nollställs
  bara när användaren väljer det.
* **Spärrar.** Par där det ena draget ingår i det andras definition (kristna markörer och kristen bön, signatur och
  signerad m.fl.) prövas inte. Minst 10 stenar på var sida och minst 5 med och utan A krävs, och minst 5 stenar med och
  utan A ska vara väntade på den mindre sidan – annars kan provet inte se en skillnad ens om den finns, och "ingen
  skillnad" vore missvisande.
* **Prövat (`tests/test_question.py`).** En tabell ger samma oddskvot, intervall och p som läroboken (Woolf, Yates ×
  (n − 1)/n). Kända mönster håller: *at* i Södermanland (61 mot 17 procent), monoftong i Västergötland, stungna runor
  från 1075 och bönen som blir ovanligare från 1050 (*Bönen tystnade*). *r för ʀ* i Uppland syns i hela korpusen (p
  0,0009) men inte i ena halvan (p 0,40) och märks som bara i hela. Nollfallet: med draget omblandat mellan stenarna gav
  1 000 frågor p < 0,05 i hela korpusen i 3,3 procent och höll i båda halvorna i ingen.
* **Vad svaret inte är.** Ett samband, inte en orsak; stenar av samma ristare räknas var för sig (ristarprovet och
  halvorna skyddar men tar inte bort det); tidsskikten bygger på stilgruppen, som hälften av stenarna saknar. Ett svar
  som ska användas i en artikel kräver en analysplan (1x) som skrevs innan frågan ställdes – listan över besökets frågor
  visar hur många som prövats.
* **Spara som fynd.** Ett svar kan sparas med en anteckning (Firestore under användarens konto, med en lokal kopia):
  frågan, siffrorna och domen som de var, hur många frågor som föregick den under besöket och korpusens version. De
  sparade visas i Forskningsluckor → Våra resultat under *Egna frågor*. Beläggen räknas som högst *måttliga* – och
  bara om mönstret höll i båda halvorna och efter justeringen för besökets frågor – eftersom en fråga som valts under
  utforskandet inte kan bli starkare än så utan en analysplan. *Räkna om* ställer samma fråga på korpusen som den är
  nu, som enda fråga, och säger om korpusen har ändrats sedan.

## 2. Huggspårsmått (mätmetod `groove-6`)

Källkod: `src/slice_analysis.py`.

1. **Tvärsnitt.** Mesh-filen centreras på mittpunkten av sin omslutande låda (samma som i webbläsaren).
   Ett plan läggs vinkelrätt mot spårets riktning och skär nätet. Bara skärningspunkter inom ±25 mm från
   mätpunkten, i sidled och höjdled, tas med (fönster) – annars kommer stenens baksida och kanter med i
   snittet genom en sluten skanning. Profilen uttrycks i x (tvärs spåret) och z (längs ytans normal).
2. **Uppåtriktning.** Vid manuell mätning används medelvärdet av ytnormalen i de klickade punkterna, vid
   ett klick och automatisk analys den lokala ytnormalen (se avsnitt 2b och 2c).
3. **Jämnt punktavstånd.** Profilen interpoleras linjärt till 0,05 mm mellan punkterna (finare än någon skanning), så
   att alla fönster nedan kan anges i millimeter. Profilens ursprungliga punktavstånd sparas (`point_spacing_mm`).
4. **Apex.** Profilen jämnas ut med ett glidande medelvärde över 1 mm. Apex är den lägsta punkten.
5. **Spårkanter (axlar).** Från apex söks utåt tills lutningen |dz/dx| understiger 0,15 och profilen nått minst
   halvvägs upp mot stenytan på den sidan (annars hittas en flat spårbotten i stället för kanten).
6. **Väggar.** Varje vägg anpassas med linjär regression, men **bara mellan 20 % och 80 % av höjden** från
   botten till spårkanten. Den rundade botten och spårkantens läpp planar annars ut väggarna och ger för
   stor vinkel (minst tre punkter, annars används hela väggen).
7. **Mått:**

| Mått | Definition |
|---|---|
| V-vinkel (°) | Öppningsvinkeln mellan väggarnas regressionslinjer, mätt från apex. |
| Asymmetri (°) | \|arctan(1/\|k₁\|) − arctan(1/\|k₂\|)\|, skillnaden mellan väggarnas vinkel mot lodlinjen. |
| Spårdjup (mm) | Höjdskillnaden mellan högsta och lägsta punkt mellan kanterna. |
| Spårbredd (mm) | Avståndet mellan väggarnas linjer i höjd med stenytan precis utanför spårkanterna (medel av sidorna). |
| Djup/bredd | Spårdjup / spårbredd. |
| Bottenradie (mm) | 1/(2a) för en andragradskurva anpassad inom ±1 mm från apex. |
| Ytråhet (mm) | Medelabsolutavvikelsen från väggarnas regressionslinjer. |
| Väggpassning (R²) | Den sämre av väggarnas förklaringsgrad; används för kvalitetsgranskning. |

**Validering.** På syntetiska stenar med kända V-spår (öppningsvinkel 50–110°, djup 2–4 mm, välvd yta,
mätbrus 0,03 mm, `src/synthetic.py`) mäts vinkeln inom ±0,6° och bredden inom ±1 % (djup 4 mm). Testerna
körs automatiskt (`tests/`).

**Punkttäthet.** Öppet publicerade skanningar är förenklade i olika grad (0,33–1,11 mm mellan punkterna i
Kitzler Åhfeldts Södermanlandsserie). Samma syntetiska spår mätt vid 0,33 och 1,11 mm ger med `groove-4` samma
vinkel inom 1,5°, bredd inom 0,15 mm och bottenradie inom 0,1 mm; med `groove-3` växte bottenradien från 1,3 till
7,0 mm och vinkeln med 10° (`tests/test_slice_analysis.py`). För jämförelser mellan stenar kan den automatiska
analysen dessutom köras med fast rutnätsupplösning (`resolution_mm`) och med utjämning till en gemensam effektiv
upplösning (`harmonize_mm`); båda sparas bland parametrarna.

**Versionshistorik.**
* `groove-1` (före 2026-10-04) gav 180° minus den verkliga öppningsvinkeln.
* `groove-2` (2026-10-04) rättade vinkeln, men anpassade väggarna över hela höjden, mätte bredden mellan
  spårkanterna och tog med hela snittet genom nätet. På smala spår blev vinkeln ca 10° för stor.
* `groove-3` (2026-10-04): väggband 20–80 %, bredd vid stenytan och fönster runt mätpunkten.
  Mätningar med äldre versioner är inte direkt jämförbara och bör göras om.
* `groove-4` (2026-10-06): fönstren räknades i punkter i stället för millimeter, så måtten berodde på
  skanningens punkttäthet. Profilen räknas nu om till jämnt punktavstånd och alla fönster anges i mm;
  spårkanten måste ligga minst halvvägs upp mot stenytan. Jämförelser mellan stenar med olika punkttäthet
  gjorda med äldre versioner bör göras om.
* `groove-5` (2026-10-10): den automatiska analysen mäter bara spår som känns igen som runor (avsnitt 2c,
  steg 5), och bara små hål (< 10 mm²) i spårmasken fylls. Förut fylldes alla hål, så att ett slingband
  som stängs av runstavar – eller insidan av en runas båge – blev en enda yta som räknades som för bred
  och inte mättes (på Sö 113 65 700 mm² mot nu 1 900 mm²). Själva tvärsnittsmätningen är oförändrad från
  `groove-4`; mätningar med ett klick eller manuellt är jämförbara, automatiska analyser bör göras om.
* `groove-6` (2026-10-26): **runslingorna avgör vad som är runor** i den automatiska analysen (avsnitt 2c,
  *Runslingorna*). Den tidigare streckklassningen, som bedömde varje spår efter längd och form, visade sig fel åt
  båda hållen: mätt mot granskade slingor på 66 skanningar låg 26 % av det den kallade runor helt utanför
  textslingorna, och 24 % av det den kallade ornamentik var runor (Viktor Kvant 2026-10-24;
  `utdata/forskningsplan/resultat.md`, studie 1b). Själva tvärsnittsmätningen är oförändrad; vilka snitt som räknas
  som runor ändras, så automatiska analyser och korpusposter mätta med `groove-5` bör göras om.

*Andelar och modellkontroll (2026-10-27).* Båda kontrollerna i R ger också andelen med A när B finns och när det inte
finns, med övrigt som i datan (marginaleffects; ristarmodellen för en typisk ristare), och en modellkontroll med
simulerade residualer (DHARMa, 250 simuleringar): jämn fördelning, spridning och – för ristarmodellen, som inte har
platsen i sig – kvarvarande rumsligt mönster bland stenar på ursprunglig plats. Kontrollen ändrar inte domen; en varning
visas vid svaret.

### 2b. Ett klick per snitt

Källkod: `src/auto_grooves.py` (`auto_slice`). Användaren klickar en gång i ett spår.

1. Punkterna inom 15 mm runt klicket ger en lokal ytnormal (minsta variansriktningen), orienterad utåt med
   den klickade ytans normal. Normalen förfinas med lutningen hos en spårfri referensyta (avsnitt 2c, steg 2).
2. Ett lokalt höjdfält beräknas. Spårets riktning tas från höjdfältets Hessian (riktningen med minst
   krökning) på den skala (1–7,5 mm) där dalformen är tydligast (skalnormaliserad krökning).
3. Riktningen förfinas genom att spårets botten följs några millimeter åt båda hållen och en linje anpassas
   genom bottenpunkterna. Mätpunkten flyttas till botten.
4. Snitten mäts sedan exakt som i avsnitt 2. Hittas ingen dalform säger programmet till i stället för att mäta.

### 2c. Automatisk spåranalys

Källkod: `src/auto_grooves.py` (`analyze_grooves`). Användaren vrider den ristade sidan mot sig; kamerans
riktning blir ytans normal och kamerans upp-riktning orienterar granskningsbilden.

1. **Höjdfält:** alla hörn och triangelcentra projiceras på planet vinkelrätt mot normalen, i ett rutnät med
   skanningens medelkantlängd som upplösning (högst 6 miljoner celler). Den högsta punkten per cell väljs, så
   att baksidan inte kommer med.
2. **Referensyta:** morfologisk stängning (dilatation följd av erosion, 20 mm) fyller fördjupningar smalare
   än ca 20 mm men bevarar plana, lutande och svagt välvda ytor; en lätt gaussisk utjämning (1 mm) dämpar brus.
3. **Spår:** celler som ligger mer än `max(0,3 mm, k · brus)` under referensytan, där brus = 1,4826 · MAD av
   avvikelserna och k = 3 (känslighet "normal"). Partier inom 10 mm från skanningens kant, branta partier
   (> 45°) och små fläckar (< 10 mm²) utesluts. Små hål i spåren (< 10 mm², brus) fylls; större hål –
   t.ex. ett slingband mellan två stavar eller insidan av en runas båge – lämnas.
4. **Mittlinjer:** spåren tunnas ut till ett skelett. Punkter nära korsningar och ändar utesluts, liksom
   partier bredare än ett huggspår (standard 16 mm) – t.ex. sänkta fält eller avflagningar.
5. **Runor eller inte** (`classify_strokes`; standard, kan stängas av med `runes_only=false`). Naturliga
   sprickor, vittring och ornamentik har andra former än runor, och mäts de blir stenens medelvärden
   missvisande. Mittlinjerna delas därför i streck och bara streck som känns igen som runor mäts:
   * *Streck.* Mittlinjen bryts vid korsningar; en korsning räknas som hela området inom en halv spårbredd
     (median). Grenar som fortsätter i samma riktning (högst 25° ändring, högst en halv spårbredd i sidled)
     genom en korsning eller över ett avbrott på högst två spårbredder slås ihop till ett streck. En
     slingkant som runorna stöter emot blir då ett långt streck, medan runans stav och bistavar blir egna.
   * *Runstreck.* Rakt (avvikelse från rät linje ≤ max(2 mm, 4 % av längden), varje 10 mm-korda inom 20°
     från streckets riktning), 12–250 mm långt och jämnbrett (variationskoefficient för bredden ≤ 0,5).
   * *Ornamentik och slinglinjer.* Jämnt böjda streck; raka streck längre än 2,2 × 75:e percentilen av
     runstreckens längd (runorna i en inskrift är ungefär lika höga); raka bitar som fortsätter en sådan
     linje (spritt längs linjen); och streck som står vinkelrätt (± 20°) mot den tydligt dominerande
     riktningen bland runstrecken inom tre stavlängder och är minst en halv stavlängd långa – stavarna i en
     runrad är parallella och slinglinjerna går tvärs över dem, medan bistavarna sitter snett.
   * *Oregelbundna spår* (möjliga sprickor och vittring): kortare än 12 mm, ojämnt breda eller sicksackande
     (medianvridning mellan 5 mm-kordor > 25°, eller > 8° med växlande vridriktning i mer än 40 % av fallen –
     en ornamentbåge svänger åt samma håll, en spricka växlar).
   * *Runor.* Runstreck som sitter ihop är en runa. En runa godtas bara om en annan runa finns inom 2,5 × dess
     höjd (runor står i rader; ett ensamt rakt spår kan vara en spricka eller repa), och – på stenar med
     slinglinjer – om dess mitt ligger inom 0,75 × max(stavlängd, runans höjd) från en slinglinje (stavlängd =
     90:e percentilen av runstreckens längd), eftersom runorna står i banden.

   Varje snitt får strecktyp och runans nummer; snitt på andra streck redovisas som bortsorterade med skäl
   ("inte runa: …"). Igenkänningen är avsiktligt försiktig: det är bättre att en runa missas än att en
   spricka mäts. Missade runor kan mätas med ett klick (avsnitt 2b).

**Utvärdering mot facit** (`scripts/evaluate_rune_detection.py`). I 3D-vyns facit-läge mäts alla spår och inget
är förmärkt, så att programmets förslag inte styr bedömningen; forskaren märker punkterna som runa, ornamentik
(slinglinje eller ornament) eller utesluten (spricka, vittring) och sparar ett facit med positioner och märkning.
Skriptet läser in skanningen som appen gör, kör analysen på nytt med facitets parametrar, parar varje facitpunkt
med närmaste snitt (högst 2 mm) och redovisar precision (andel mätta streck som är runor), träffsäkerhet (andel
runor som hittas) och F1, med stenarna som reglerna justerades på (Sö 113, Sö 128) redovisade för sig. Eftersom
facitet bara innehåller positioner kan samma facit användas när reglerna ändras. Kedjan är prövad på en syntetisk
sten med känd geometri (precision 1,0, träffsäkerhet > 0,95); några handmärkta facit finns ännu inte.

**Jämförelse med Rundata.** Antalet igenkända runor på 19 skanningar ur Södermanlandsserien var i median 0,9 gånger
antalet runor i Rundatas translitterering (Spearman 0,58), men 0,3–1,5 på enskilda stenar: grunda, vittrade runor
faller sönder och sorteras bort (Sö 160, Sö 206), och korsarmar eller slinglinjer som brutits av vittring kan tas
för runor (Sö 143); på Sö 371, utan läsbara runor i Rundata, hittades sex. En igenkänd "runa" är en grupp
sammanhängande runstreck, så antalet är bara ett grovt mått.

**Sö 164 och tre förkastade regeländringar (2026-10-14).** I stenanalysen av Sö 164 (vittrad gråsten, brus 0,65 mm)
låg 18 av 67 igenkända runor i bildfältets skepp och kors, och 45 av de 49 i runbanden var en enda stav: bistavarna
är grundare och bryts loss av vittringen. Stenens medelvärden påverkades inte (V-vinkel 120,3° med bara bandens
runor mot 120,2° med alla). Tre ändringar prövades på Sö 45, 113, 128, 131, 160, 164 och 205: (1) gränsen för
ramlinjer räknad på 90:e i stället för 75:e percentilen av runstreckens längd, eftersom hela stavar på Sö 164
sorterades bort som ramlinjer när de flesta streck var korta brottstycken; (2) krav på att en runa har parallella
grannar bredvid sig i en rad om minst fyra, eller två intill en bandlinje, i stället för avståndet till närmaste
bandlinje; (3) båda. De minskade felen på vittrade stenar med stora figurfält (Sö 164: 58 runor i banden och 7 i
figurfältet mot 49 och 18; Sö 45) men tappade runor i glesa och starkt böjda band (Sö 128) och släppte in långa
parallella djurlinjer (Sö 205). Ingen infördes; reglerna ändras först när handmärkta facit finns. Granskningsvyn
låter forskaren märka figurfältet som ornamentik innan analysen används.

**Mätning utan manuellt urval.** Tidigare 3D-studier av huggteknik (Kitzler Åhfeldt 2002 och senare) mäter
också i 3D-modeller med programvara (Groove Measure), men forskaren väljer vilka spår som mäts och var proverna
tas – oftast de bäst bevarade spåren. Den automatiska analysen tar i stället med alla igenkända runor, med samma
regler och parametrar på varje sten. Urvalet beror alltså inte på vem som mäter och kan upprepas exakt av vem
som helst med samma skanning och metodversion. Det tar bort variationen mellan bedömare men inte all systematik:
reglerna är själva val, gjorda av utvecklarna och dokumenterade här, och de kan slå olika på olika bergarter
och vittringsgrader, och att alla runor tas med ger mer vittringsbrus än ett urval av välbevarade spår. Fördelen
är att felen är desamma för alla stenar och går att granska och rätta – inte att de saknas (se avsnitt 18).
6. **Mätning:** med jämna mellanrum (standard 3 mm) längs mittlinjerna tas riktningen från mittlinjen och
   förfinas genom att botten följs (som i 2b). Tvärsnittet mäts **genom mesh-filen** med samma metod som i
   avsnitt 2 – höjdfältet används bara för att hitta spåren.
7. **Kvalitetsgranskning:** snitt sorteras bort vid orimlig vinkel (≤ 15° eller ≥ 170°), väggpassning
   R² < 0,8, djup under tröskeln, ej funnen spårkant eller botten utanför mittlinjen. Skälen redovisas.
8. **Granskning:** forskaren ser alla mätpunkter på en reliefbild – godkända runsnitt är förvalda som runor –
   kan märka om eller utesluta områden, och väljer vilket urval som blir resultatet.

**Validering.** På de syntetiska stenarna ger den automatiska analysen samma noggrannhet som avsnitt 2
(t.ex. 70,0 ± 0,9° för spår på 70°, oberoende av hur stenen lutar). På skanningen av Sö 113 (6,1 miljoner
trianglar) godkändes ca 250 av 1 000 kandidatsnitt; ett klick på samma ställen gav i median 6° skillnad i
vinkel och 10° i spårriktning, vilket speglar hur oregelbundna verkliga, vittrade spår är. Resultaten bör
därför redovisas med spridning och, för jämförelser, med samma mätsätt för alla stenar.

Runigenkänningen prövas på en syntetisk runslinga (sex runor mellan två slingkanter, en ornamentbåge och
en sicksackande spricka): alla sex runor och bara de mäts (80,8° för spår på 80°), slingkanterna och bågen
blir ornamentik och sprickan oregelbunden (`tests/test_auto_grooves.py`). På Sö 113 och Sö 128 granskades
klassningen visuellt: slinglinjerna mellan raderna och i slingorna sorteras bort, liksom raka vittringsspår
i Sö 128:s mittfält; de som mäts är nästan bara stavar och bistavar. Svagt böjda eller avbrutna stavar
missas ibland. Igenkänningen är regelbaserad och inte validerad mot en handmärkt referens.

**Runslingorna (groove-6).** Vad som är runor avgörs av var runslingorna – banden som texten står i – går:
* **Slingorna:** för de öppna skanningarna används slingor som ritats och granskats för hand på sidan Runmodell
  (`data/runmodell/band/`), igenkända på filens SHA-256. De förs över från djupbildens rutnät till analysens genom
  stenens yta: varje ruta i analysen tas till sin punkt på ytan och slås upp i djupbilden, så att slingorna hamnar
  rätt även när stenen är vriden något annorlunda (högst 20° mellan normalerna). Knappen *Vänd ristade sidan mot mig*
  i 3D-vyn vrider vyn mot stenens tunnaste riktning (minsta spridningen av modellens punkter, vänd mot den sida där mest
  yta pekar; samma skattning som analysmotorn använder utan vy). Annars föreslår
  **slingmodellen** dem: ett litet U-nät (`data/runmodell/slingmodell.pt`, `src/rune_bands.py`) tränat på 95 granskade
  stenar, som på stenens djupbild (2,4 mm per pixel) markerar var slingorna går. På 24 stenar som hölls utanför
  träningen överlappade modellens slingor de ritade med i mitten 59 % (IoU; bäst Sö 333 0,83, sämst stavlösa Hs 14
  0,10).
* **Klassningen:** slingans riktning i varje punkt skattas ur en strukturtensor av den utjämnade slingmasken (fönster
  12 mm). Ett snitt är **runa** om det ligger inne i en slinga och spåret går mer än 25° från slingans riktning;
  **slingkant** om spåret går längs slingan, inne i den eller högst 8 mm utanför; **gräns** om det ligger högst 8 mm
  utanför och inte går längs den (runspetsar, korsningar); annars **utanför**. Spårets riktning tas ur mittlinjen
  kring punkten.
* **Vad som mäts:** *Runor* mäter snitten klassade som runa; *Ornamentik* mäter snitten utanför slingorna som
  streckklassningen ser som långa, jämna spår (ornamentik, ramar, kors), inte korta krokiga spår (möjliga sprickor).
  *Allt* (facit-läget) mäter alla spår.
* **Reserv:** finns inga slingor (ingen modell, ingen PyTorch eller inga slingor på stenen) används
  streckklassningen som förut, och analysen säger det. Granskningsbilden visar slingorna som ett ljusblått fält.
* **Begränsningar:** slingmodellen är tränad på öppna skanningar från två skannertyper och sex serier; stavlösa runor
  och små fragment hittar den dåligt. Slingorna är förslag som användaren ska granska i granskningsbilden.

**Stavlöst läge (2026-10-26, `src/staveless.py`).** Stavlösa runor (hälsingerunor, och r/u på en del medelpadska
stenar) har ingen huvudstav: en runa är ett eller några korta streck, ofta halva slinghöjden. Med slingorna mäts deras
snitt (rätt placerade slingor gav 1,4–3,5 runsnitt per runa i texten på de stavlösa stenarna, som på vanliga stenar),
men runindelningen bygger på streck som sitter ihop och är minst 12 mm långa, så nästan inga snitt fick en runa: Hs 15
197 runsnitt och 5 runor, Hs 12 303 och 16. I stavlöst läge delas runorna i stället efter var strecken står längs
slingan. Vilka snitt som mäts och deras mått är desamma som utan läget; bara runtillhörigheten (`rune_id`) ändras.
* **Slingorna var för sig:** ritade slingor behåller var sitt nummer (`rune_bands.drawn_labels`), så att rader som
  ritats sida vid sida inte flyter ihop där de möts (Hs 14:s fem slingor blev annars tre fält, Hs 15:s två ett);
  modellens slingor delas i sammanhängande fält. Slinghöjden räknas för varje slinga (två gånger 90:e percentilen av
  avståndet till kanten).
* **Koordinat längs slingan:** slingan skelettiseras på ett rutnät om 2 mm; avståndet längs skelettet från dess ena
  ände är koordinaten, och varje cell får värdet från närmaste skelettpunkt, så att koordinaten inte ändras tvärs
  över slingan. Slingans riktning är riktningen där koordinaten ökar.
* **Runstreck:** en gren av mittlinjen som till minst hälften ligger i slingan, högst 1,5 slinghöjder lång, högst 0,4
  slinghöjder utsträckt längs slingan och, om den är längre än en fjärdedel av slinghöjden, mer än 25° från slingans
  riktning (annars är den en bit slingkant).
* **Runor:** strecken ordnas längs slingan; ett streck hör till föregående runa om luckan dit är högst 0,15
  slinghöjder och runan då blir högst 0,45 slinghöjder bred längs slingan. Breddtaket hindrar att tätt ristade runor
  kedjas ihop.
* **Hur gränsen valdes:** två regler bestämdes före provet och föll. Den största relativa luckan i stenens sorterade
  avstånd landade antingen på några mm (för många runor) eller på 30–47 mm (Sö 164: 5 runor av 176). Runornas takt ur
  autokorrelationen av strecken längs slingan gav takter mellan 4 och 60 mm. Gränsen 0,15 och taket 0,45 slinghöjder
  valdes därefter, med textens runantal och fullstora granskningsbilder av Hs 15 och Hs 12 som stöd; de är alltså
  inte förhandsbestämda. Indelningen är ett ungefärligt förslag – den exakta görs med *Markera runorna* nedan.
* **Utan slingor:** streckklassningen med minsta runstreck 5 mm (i stället för 12) och grannavståndet 4 gånger runans
  höjd (i stället för 2,5).
* **Påslaget:** av användaren på 3D-sidan, och automatiskt när Rundata anger stavlösa runor och ingen annan runtyp för
  stenen (Hs 10, 12, 14, 15; 3D-sidan och stenanalysen). På blandade stenar (långkvist med stavlösa r och u: M 3, M 7,
  M 8) delade läget runorna för fint, så där lämnas valet till användaren. Av som standard.
* **Prövning** (`utdata/stavlosa/`: `matning.py`, `kor.sh`, `tabell.py`; 15 skanningar av stenar med stavlösa runor
  och 8 vanliga, Vitki-protokollet, ritade slingor där de finns). Runor med minst ett godkänt snitt, utan → med läget:
  Hs 12 16 → 60 (145 runor i texten), Hs 14 26 → 89 (267; skanningen av runpartiet), Hs 15 5 → 48 (84). Hs 10 har inga
  ritade slingor och slingmodellen hittar dem dåligt: de sex fragmenten gav 8–38 godkända snitt var och 5 → 39 runor
  sammanlagt. Antalet runor läget hittade mot textens: Hs 12 100 av 145, Hs 14 168 av 267, Hs 15 66 av 84. På blandade
  stenar och vanliga stenar delar läget runorna för fint (M 7 68 mot 33 i texten, M 8 92 mot 32, de vanliga i median
  1,45 gånger textens antal), eftersom stavarna där delas i flera streck längs slingan. Vilka snitt som mäts och deras
  mått är oförändrade (provat på en syntetisk sten i `tests/test_auto_grooves.py`).

**Runor markerade för hand.** Analysens egen runindelning (grupper av sammanhängande raka streck) är inte validerad.
I granskningen kan användaren i stället klicka en gång mitt på varje runa, i läsordning, utan att ange vilken runa
det är (`withMarkedRunes` i `web/src/lib/mesh.ts`). Varje godkänt snitt som är märkt som runa hör då till den närmaste
markeringen, om den ligger inom 1,5 gånger mediandistansen mellan två på varandra följande markeringar; snitt längre
bort hör inte till någon runa. Markeringarnas nummer blir `rune_id`, så medelvärden med runan som enhet (avsnitt 3),
jämförelser mellan stenar (avsnitt 4) och exporterna räknas på de markerade runorna. Varje snitt behåller sina mått,
och i proveniensen står antalet markeringar (`rune_marks`). Resultatpanelen visar då också måtten med runan som enhet
(`rune_summary` från `/api/stats/summarize`, när snitten bär minst två runnummer). Gränsen mellan två runor blir mittlinjen mellan deras
markeringar, så tätt ristade runor och bindrunor kan få snitt från grannen; markera då mitt i runans stav.

### 2d. Bilder ur skanningen

Källkod: `api/routers/threed.py` (`render_relief`), `src/stone_report.py` (`Surface`). Bilder för egen läsning,
fliken Bilder och runformer och rapporterna räknas direkt ur skanningen i stället för att fotografera skärmen:

* Ytan projiceras till ett höjdfält från den sida som vetter mot betraktaren i 3D-vyn (kamerans riktning och
  upp-riktning). Utan vy används stenens tunnaste riktning (minsta variansriktningen), vänd mot den sida där
  mest yta pekar.
* **Strykljus** från fyra riktningar (nordväst, nordost, sydost, sydväst) 20° över ytan.
* **Relief**: det mörkaste av de fyra strykljusen, så att varje spår blir mörkt oavsett riktning.
* **Djup** under en rekonstruerad stenyta (morfologisk stängning, 20 mm); kantzonen (10 mm), där
  referensytan är osäker, utelämnas.
* Bilderna har känd upplösning (mm per pixel) och påverkas inte av zoom eller skärmens belysning. Små
  skanningar skalas upp till minst 1 200 px för läsning.
* Bilderna kan laddas ned under Exportera (2f); för nedladdning används ytans eget rutnät utan uppskalning, och
  normalen väljs som i stenrapporten (analysens normal eller snittens riktning), så vyn används där bara när ingen
  analys finns.

### 2e. Robusthet

Källkod: `scripts/groove_robustness.py`, resultat i `utdata/groove_robustness/`. Åtta skanningar ur Kitzler Åhfeldts
Södermanlandsserie (Sö 113, 128, 134, 143, 161, 207, 319, Fv1948;282) mättes nio gånger: som standard (0,6 mm
rutnät, känslighet 3) och med rutnät 0,4 och 0,8 mm, ytnormalen lutad 5° åt två håll, känslighet 2,5 och 3,5,
och skanningen förenklad till hälften och en fjärdedel av trianglarna (som en glesare skanner).

| Ändring | Stenens V-vinkel, median (största) | Antal runor | Återkommande mätpunkter | Samma ställe: vinkel, djup |
|---|---|---|---|---|
| Rutnät 0,4 / 0,8 mm | 0,7° (2,8°) / 0,8° (3,3°) | −3 % / −15 % | 60 % / 73 % | 2,1° / 2,3°; 0,07–0,08 mm |
| Normal lutad 5° | 0,8–1,2° (4,8°) | −6 % till +10 % | 56 % | 2,3–2,6°; 0,17–0,37 mm |
| Känslighet 2,5 / 3,5 | 2,8° (4,9°) / 0,9° (3,0°) | +1 % / −6 % | 64–65 % | 1,8–2,0°; 0,07 mm |
| Hälften / en fjärdedel av trianglarna | 0,9° (4,2°) / 2,8° (9,1°) | −4 % / −12 % | 70 % / 43 % | 2,0° / 4,0°; 0,07–0,14 mm |

Stenens medelvärden (runan som enhet) stämmer väl överens över alla nio villkor: ICC(A,1) 0,98 för V-vinkel och
djup/bredd, 0,97 för djup, 0,95 för bredd och 0,93 för bottenradie; spridningen över villkoren är 13–19 % av
spridningen mellan stenar. Asymmetrin stämmer dåligt (ICC 0,40; 40 %). Vilka ställen som mäts ändras däremot
mycket (43–73 % av punkterna återkommer), och samma ställe skiljer i median ca 2° i vinkel – stenens resultat är
stabilt för att det är ett medelvärde över många runor, inte för att varje snitt är det. Djupet beror på
ytnormalen (0,37 mm på samma ställe vid 5° lutning) och glesa skanningar (en fjärdedel av trianglarna) ger
tydligt sämre resultat. **För jämförelser mellan stenar ska därför samma rutnät och känslighet användas, och
skanningar med mycket olika punkttäthet jämföras med försiktighet.** Studien är inte ett test–omtest med
oberoende skanningar av samma sten.

### 2f. Export från huggspårsanalysen

Källkod: `src/groove_export.py`, `api/routers/threed.py` (`POST /api/3d/export`, `GET /api/3d/export_items`,
`GET /api/3d/scan_credit`), `src/scan_sources.py` och `data/scan_files.json`. Under **Exportera** på 3D-sidan väljs
vilka filer som laddas ned. Inga mätvärden räknas om, och mätmetoden är fortfarande `groove-5`: tabellerna är
analysens snitt som de lagrats, och ristningskartan och granskningsbilden är analysens egna bilder. Bilderna ur
skanningen räknas fram ur 3D-modellen när filerna skapas, med stenrapportens funktioner, och i den automatiska
analysen räknas sammanfattningen och verktygstumregeln om för forskarens grupper (nedan). Filernas namn och förklaringar står på ett ställe (`ITEMS`), som både appens hjälptext och
README.txt i paketet läser.

* **Vilken analys och vilken mätform.** Den automatiska analysen exporteras när dess flik är öppen (eller när inget
  annat är mätt), annars mätningen som visas på sidan. Knappen *Exportera …* under en analys (den automatiska
  analysens granskning eller resultaten) väljer just den analysen, och när båda finns anger menyn vilken som
  exporteras, med ett val att byta. Mätformen (`auto`, `oneclick`, `manual`, `path`) och
  spårtypen läses ur analysens egen proveniens (`parameters.mode`, `feature_type`), inte ur vilken flik som är öppen.
* **Etiketterna i den automatiska analysen** används som stenrapporten läser dem (`fromSession` i
  `web/src/lib/stoneReport.ts`): godkända snitt utom de som märkts *uteslutna*, grupperade efter etikett (runa,
  ornamentik, okänt; ett snitt utan etikett räknas som okänt). Sammanfattningen räknas om för varje grupp med
  projektets egna funktioner (`summarize_slices`, och `summarize_by_rune` bara för gruppen runa och bara när
  analysen mätte enbart runor, `parameters.runes_only`; i de andra grupperna är `rune_id` den automatiska
  igenkänningens, som forskaren har avvisat), liksom verktygstumregeln; figurerna över snitten använder bara grupperna, i stenrapportens ordning. Mättabellen och
  JSON-filen har alla snitt med sin etikett, och analysens egen sammanfattning över alla godkända snitt finns kvar i
  JSON-filen.
* **Spårdjup som värmekarta** är stenrapportens figur 2 (`stone_report.depth_figure`), bildpunkt för bildpunkt,
  med en rad om skanningen under figuren. **Spårdjup som rådata** är samma tal som ett ESRI ASCII-rutnät: djupet är
  −residualen mot en referensyta (morfologisk stängning, 20 mm, utjämnad 1 mm), negativa värden satta till 0,
  kantzonen (10 mm) och ytan utanför skanningen som −9999. Referensytan ligger i nivå med ytan runt spåren och
  spårkanterna, inte på en tänkt ursprunglig stenyta. Cellen är ytans upplösning (`Surface.res`), som beror på
  skanningens täthet och stenens storlek (rutnätet har högst 1 800 rutor på längden). Första raden är bildens
  överkant. Koordinaterna är millimeter i ytans eget plan; en JSON-fil bredvid anger origo, basen (u, v, n) i den
  centrerade modellen, normalen och skanningens SHA-256.
* Tre olika normaliseringar av djupet används, och **bara värmekartan och rutnätet kan läsas i mm**. Värmekartans
  färgskala slutar vid stenens 99,5:e percentil, så att den djupaste halva procenten blir lika svart. Djupbilden i
  appens Bilder ur skanningen (`render_relief`) är svart vid 99:e percentilen av djupet utanför kantzonen.
  Ristningskartan från den automatiska analysen är svart vid 95:e percentilen av djupen i de rutor i analysens
  mätområde (`inner`: utanför kantzonen och inte brant) som ligger djupare än analysens tröskel; skalan (`groove_map_scale`: black_mm, threshold_mm, grid_mm, mm_per_px) sparas från
  och med nu med analysen och står i bildens metadata, och för äldre analyser står det att skalan inte sparades.
  Kantzonen – inom skanningen men utanför mätområdet, alltså nära skanningens kant och hål och där ytan är brant –
  ritas med en tredjedel av kontrasten (`EDGE_ZONE_CONTRAST`), så att kantfel inte kan se ut som ristning; den visas
  ändå, eftersom en runa kan nå ut i den. Svart betyder black_mm eller djupare. *Ändrat 2026-10-24:* tidigare räknades
  percentilen över hela rutnätet och kantzonen ritades med full kontrast, så svartpunkten sattes ofta av skanningens
  kant (Sö 371 8,5 mm, gravhällen Ög 5b 30 mm med uppskattad normal; nu 3,3 respektive 4,1 mm) och runorna blev
  mellangrå. Mätningarna påverkas inte (samma snitt och samma godkända snitt); bara kartans gråskala och black_mm
  ändras, och `groove_map_scale` har fått `black_from`, `edge_zone_mm`, `edge_zone_max_slope_deg` och
  `edge_zone_contrast`. Kartan och runrutorna som 2D-analysen får behåller läge och storlek. Gråtonerna i reliefen och ristningskartan kan inte jämföras
  mellan stenar.
* Tvärsnittens spårdjup är ofta 10–40 % större än kartans på samma ställe, ibland mindre. Tvärsnitten mäts i en tät profil från
  spårkanten till botten, medan kartan är ett grövre rutnät (varje ruta har den högsta punkten i sin ruta) där den
  smala botten i ett V-spår sällan träffas exakt. Spårdjup ska därför tas ur mättabellen; kartan visar formen. Branta partier innanför kantzonen, sprickor, vittringsgropar och borrhål kan se
  lika djupa ut som ristning.
* Relief och strykljus exporteras på ytans eget rutnät (en pixel per ruta, högst 1 800 px), inte uppskalade, och
  bara för dem (och för ristningskartan) anges mm per pixel i metadata. Värmekartan och figurerna över snitten är
  diagram med axlar och skalstock i mm; deras metadata anger rutnätets cellstorlek (`surface_cell_mm`) men ingen
  storlek per pixel. Granskningsbilden och ristningskartan är analysens egna bilder; under granskningsbilden läggs en
  teckenförklaring (spår, för breda ytor, V-vinkelskalan 30–130° och bortsorterade snitt) utan att bildens pixlar
  ändras, så att `img_x` och `img_y` i mättabellen fortfarande gäller. Granskningsbilden visar analysens egen
  sortering, inte forskarens etiketter.
* **Tvärsnittsprofilerna** ritas med höjden räknad från spårkanternas nivå (medel av de högsta punkterna strax
  utanför spårets båda kanter), samma nivå som spårbredden mäts vid; den streckade linjen är den nivån, inte en
  rekonstruerad stenyta. Väggarna anpassas om för figuren med analysens egen utjämning (`harmonize_mm`), och varje
  ruta har bokstaven för sin plats bland de valda snitten, samma som i figuren över snittens läge; en profil som inte
  kan ritas hoppar över sin bokstav. De lagrade måtten ändras inte. Stenrapportens bildtexter säger detsamma.
* **Normalen** för bilderna ur skanningen väljs med samma funktion som stenrapporten (`groove_export.view_normal`,
  som `api/routers/reports.py` också använder): analysens egen normal (den automatiska analysens; bilderna ligger då
  som ristningskartan), annars medelriktningen av snittens uppåtriktning. Bara när ingen analys finns används 3D-vyns
  riktning och därefter stenens tunnaste riktning. Valet står som `normal_source` (analys, snitt, vy, uppskattad) i
  filernas metadata och i kalla.json. Alla bilder i en export delar samma yta (`Surface`, högst 1 800 px), som i
  stenrapporten, så att bilderna för samma analys är stenrapportens figurer.
* **Koordinaterna**: tre system används. Tabellernas punkter och riktningar är millimeter i 3D-modellen centrerad på
  sin omslutande lådas mitt; förskjutningen (`centered_by`) står i tabellhuvudet, så att punkterna kan föras
  tillbaka till originalfilen. Rutnätet (.asc) är millimeter i stenytans eget plan (origo och bas i JSON-filen
  bredvid). `img_x`, `img_y` och `box_*` är pixlar i granskningsbilden, med origo uppe till vänster. I den
  automatiska analysen är `position_mm` provpunktens ordningsnummer över hela stenen gånger snittavståndet, inte
  ett avstånd längs ett spår.
* **Tabellerna** (CSV) har en rad per tvärsnitt för alla mätformer (även bortsorterade snitt i den automatiska
  analysen, med skäl; där är `label` snittets grupp och kolumnen `feature_type` tom), sammanfattningen per grupp,
  per snitt och per runa, runorna med kvalitetskontrollen,
  råprofilerna och längdprofilen. Talen skrivs som de lagrats eller räknats, utan avrundning. `fit_r2` är det sämre
  av de två väggarnas R²; bara den automatiska analysen sorterar bort snitt på den (under 0,8). ICC (envägs, ICC(1))
  kan bli negativ när snitten i en runa skiljer sig minst lika mycket som runorna sinsemellan, och läses då som ingen
  skillnad mellan runorna.
* **Krediteringen** av skanningen följer med i varje fil: som iTXt-text i PNG-filerna (Title, Author, Copyright,
  Source, Description, Software, Creation Time och en JSON-kommentar med normal, skanningsfil, skala och om
  skanningen känts igen), som en synlig rad under figurerna och granskningsbilden (råa rutnät som relief, strykljus
  och ristningskarta lämnas pixelexakta), som #-rader överst i tabellerna och i README.txt och kalla.json. Reliefen
  och ristningskartan har bara metadata, som bildprogram ofta tar bort, så de skickas alltid i en ZIP med
  README.txt, också när de laddas ned ensamma. PNG-filernas Author anger att bilden är beräknad i Vitki och vem som
  skannat (`Vitki (beräknad); skanning: …`). Den synliga raden anger datamängden med sin DOI; den korta referensen
  (Kitzler Åhfeldt 2024a) används bara i stenrapporten, som har en referenslista. En öppen
  datamängd krediteras **bara när filen känns igen** som en av datamängdens publicerade filer
  (`scan_sources.identify`): samma SHA-256 eller md5 som Zenodos fil (`data/scan_files.json`: Zenodos filnamn,
  storlek och md5 för seriernas STL-filer, och SHA-256 för de filer vars nedladdade kopia stämde med md5), annars
  samma filnamn och storlek. Ett filnamn utan storlek räcker inte, en annan kontrollsumma under ett publicerat namn
  räcker inte, och ett inskrivet signum räcker aldrig. Stenrapporten avgör krediteringen på samma sätt, ur analysens
  proveniens och den inlästa modellen. Den synliga raden anger vem som skannat, institutionen, projektet, licensen
  med länk och DOI, och datamängdens anmärkning (till exempel att bara inskriftsytorna är skannade). En fil som visar
  två stenar (Ög 240 och Ög 241 på samma gravhäll) anger båda. När
  filen inte känns igen används den exporterandes egen text, märkt som hens (också i PNG-filernas Author och Source),
  och annars en uppmaning att ange vem som skannat stenen.
* **Indata kontrolleras**: felaktiga fält (även `rune_id` och `stroke_id`, som måste vara heltal), analyser och
  etiketter ger 400, inbäddade bilder måste vara PNG (högst
  25 MB och 4 000 pixlar per sida), signumet rensas från styrtecken och får vara högst 100 tecken, och felaktigt
  formade sammanfattningar (`rune_summary.metrics`, `tool_heuristic.adjustments`) ger 400, inte ett serverfel. En
  analys från en annan skanning än den inlästa modellen avvisas när bilder ur skanningen ska räknas fram; tabeller
  och data, som inte behöver modellen, exporteras då med analysens egen skanningsfil och kreditering. Formuläret
  måste vara multipart/form-data, med Content-Length högst 125 MB och högst 20 fält, och bara en export körs åt
  gången: platsen tas innan formuläret läses, så en andra export får 429 utan att dess innehåll buffras. Exporten
  kan avbrytas i appen, och den avbryts av sig själv när en annan modell läses in eller den exporterade analysen
  byts.
* Flera filer skickas som en ZIP med README.txt (vad varje fil är, enheter, skalor, normal, etiketter,
  begränsningar, kreditering och citering) och kalla.json (proveniensen i maskinläsbar form). Begränsningarna i
  README.txt omfattar också de som gäller just den här stenen: för få mätta runor eller snitt per grupp
  (`limitations.specific`) och avvikelser från Vitki-protokollet och dess anmärkningar (`provenance.protocol`).
* `render_depth_map` är äldre och visar inte spårdjup: den färgar modellens globala Z-koordinat från lägsta till
  högsta punkt och visar därför stenens form och lutning. Den används inte i exporten.

## 3. Osäkerhet

Källkod: `src/stats.py`. För varje mått och sten redovisas medelvärde, standardavvikelse (n − 1),
antal snitt och 95 % konfidensintervall (t-fördelning). Spridningen mellan snitt säger hur stabilt måttet
är längs spåret – den fångar inte systematiska fel som skanningsupplösning eller vittring.

**Runan som enhet** (`summarize_by_rune`). Snitt i samma runa är inte oberoende – de delar slag, verktyg
och vittring – så ett konfidensintervall över alla snitt blir för smalt. När bara runor mäts redovisas
därför också stenens medelvärde av runornas medelvärden, med n = antal runor, konfidensintervall
(t-fördelning) och ICC(1) (andelen av spridningen som ligger mellan runor).

**Hur många runor?** (`scripts/rune_sample_size.py`). Den automatiska analysen kördes på 20 skanningar ur
Kitzler Åhfeldts Södermanlandsserie (0,6 mm rutnät, känslighet 3); 18 stenar fick minst 8 mätta runor (8–76,
median 6 snitt per runa). Spridningen delades i tre nivåer (envägs-ANOVA per sten):

| Mått | SD inom runa | SD mellan runor | ICC | SD mellan stenar |
|---|---|---|---|---|
| V-vinkel | 10,0° | 8,1° | 0,37 | 12,6° |
| Spårdjup | 0,62 mm | 0,73 mm | 0,49 | 0,99 mm |
| Spårbredd | 2,4 mm | 1,9 mm | 0,35 | 2,5 mm |
| Djup/bredd | 0,052 | 0,050 | 0,44 | 0,070 |
| Asymmetri | 6,4° | 3,4° | 0,14 | 2,4° |

Spridningen mellan runor är lika stor som inom en runa, så fler runor ger mer än fler snitt per runa.
95 % konfidensintervall för stenens V-vinkel: ± 11° med 5 runor, ± 6,5° med 10, ± 4,2° med 20 och ± 3,4° med
30 (spårdjup ± 0,96, 0,55, 0,36 och 0,29 mm). Med 20 runor per sten upptäcks en skillnad på en
SD mellan runor (ca 8° i vinkel, 0,7 mm i djup) mellan två stenar med 80 % styrka (α = 0,05). Utifrån n
slumpvis valda runor kändes en sten igen bland de 18 i 52 % av försöken med 5 runor, 63 % med 10 och 75 %
med 20 (jämfört mot medelvärdet av stenens andra hälft av runor). Asymmetrin är för osäker för att skilja
stenar åt (ICC 0,14; 30 runor ger tillförlitlighet 0,9).

Appen anger därför **minst 10 runor för att beskriva en sten och minst 20 för att jämföra stenar**; 5 räcker
inte. Gränserna gäller stenar med olika ristare *och* olika material; skillnaden mellan två ristare på samma
bergart är mindre (avsnitt 16 och replikationsstudien av Kitzler Åhfeldts grupper), så för attribuering
behövs fler – helst alla mätbara runor.

## 4. Jämförelse av två stenar

Källkod: `src/stone_compare.py`, `POST /api/stats/compare`; sidan **Jämför stenar**.

* **Runan som enhet.** Snitt i samma runa delar slag, verktyg och vittring och är inte oberoende; behandlas de som
  oberoende blir nästan varje skillnad mellan två stenar "signifikant". När minst 80 % av snitten bär runnummer
  (automatisk analys) jämförs därför runornas medelvärden, och permutationstestet flyttar hela runor mellan
  stenarna (5 000 permutationer). Utan runnummer jämförs snitten, med en varning om att p-värdena blir för små.
* **Per mått:** tvåsidigt permutationstest av skillnaden i medelvärde, Bonferroni-justerat, och Cohens d på
  enheterna. **Samlat:** permutationstest av avståndet mellan stenarnas standardiserade medelvektorer för de
  stabila måtten (V-vinkel, djup, bredd, djup/bredd); asymmetri och bottenradie redovisas men ingår inte
  (avsnitt 2e och 18).
* **Referensskala:** avståndet mellan stenarnas medelvärden (stabila mått, standardiserade med spridningen mellan
  korpusens stenar) jämförs med avstånden mellan alla stenpar i den delade mätkorpusen med samma spårtyp och
  mätmetod, och särskilt med par som har samma respektive olika ristare i Rundata (minst fem stenar).
* **Jämförbarhet:** samma spårtyp, samma mätmetod, båda enligt Vitki-protokollet, minst 20 runor per sten (avsnitt
  3), likartad punkttäthet (högst 1,5 gånger skillnad) och samma bergartsfamilj enligt Rundata. Det som inte
  uppfylls redovisas.
* **Mer än huggspår:** har båda stenarna signum jämförs Rundatas ristare, stilgrupp, datering, bergart och höjd,
  avståndet mellan platserna, stavningen (likheten mellan inskrifterna och hur stor andel av sten A:s jämförelser
  med andra inskrifter som är mindre lika) och språkdragen (hur många jämförbara drag som stämmer).
* **Tolkning:** p < 0,05 talar emot samma verktyg och hand, p ≥ 0,05 är *förenligt med* samma hand men bevisar den
  inte. Skillnader kan också bero på bergart, vittring och skanning, så slutsatsen läses tillsammans med
  jämförbarheten och de övriga beläggen. Testet med runan som enhet prövas på syntetiska stenar
  (`tests/test_compare.py`): när runorna kommer ur samma fördelning hittar det ingen skillnad, medan samma snitt
  behandlade som oberoende ger ett lägre p-värde.

## 5. Attribuering mot mätkorpusen

* Referensen är den delade korpusen (Firestore, CC BY 4.0). En stens ristare hämtas från Rundata och används
  bara om exakt **en säker signerad (S) eller attribuerad (A)** ristare anges. Stenen själv utesluts alltid.
* Måtten standardiseras; avståndet till varje ristares centroid är Mahalanobisavståndet med poolad
  inomgruppskovarians, krympt 20 % mot en diagonal (stabilt med få stenar).
* Ristare med färre än två uppmätta stenar tas inte med. Med för lite data avstår programmet och säger det.
* **Träffsäkerheten redovisas alltid** med lämna-en-ute-korsvalidering (andel stenar där rätt ristare hamnar
  först respektive bland de tre första, jämfört med slumpnivån).

### 5b. Vad som lagras i korpusen

* Varje post har mått per snitt, sammanfattning, proveniens (filens SHA-256, parametrar, metodversion) och
  valfritt **skanningsmetadata** (utrustning, upplösning, noggrannhet, datum, skannat av, länk/DOI, licens) och
  **stenens skick** (vittring, lav, ommålning).
* **Råa tvärsnittsprofiler** (x/z i mm, fyra decimaler) kan bifogas. De lagras i delar under
  `corpus/{id}/raw` och gör att en post kan **räknas om med en senare metodversion**
  (`POST /api/stats/recompute`). Omräkning av de lagrade profilerna återger de ursprungliga vinklarna inom
  0,01°. Bara bidragsgivaren kan ersätta sina mått med omräknade.
* **Runformer** från fliken Bilder och runformer (normaliserad form och särdragsvektor, se avsnitt 12) kan bifogas under
  `corpus/{id}/runeforms`, med spårmått för runan om den markerats på en ristningskarta från 3D-analysen.
* Andra forskare kan lägga till en **verifiering** (namn, institution, kommentar); den egna posten kan inte
  verifieras av bidragsgivaren. Kvalitetsmärken visar råprofiler, skanningsuppgifter, minst fem snitt, aktuell
  metodversion och verifiering.
* Korpusen kan exporteras som ett **datapaket** (JSON med licens, citering, bidragsgivare och alla poster,
  valfritt med råprofiler) för arkivering.

## 6. Klustring

Hierarkisk klustring med Wards metod och euklidiska avstånd på standardiserade medelvärden per sten –
samma upplägg som i Kitzler Åhfeldts analyser av huggteknik (se avsnitt 16).

## 7. Ortografisk stilometri

Källkod: `src/orthography.py`. Underlag: Rundatas vikingatida inskrifter med minst fem läsbara ord (1 719 st).

* **Särdrag:** tecken-2- och 3-gram i läsbara ord (TF-IDF), skiljeteckentyper och -täthet, andel bindrunor.
  Skadade ord (med `-` eller `...`) räknas inte.
* **Egennamn tas bort** (ord som normaliseras som namn i Rundata), så att ristarens signatur ("bali risti")
  inte avslöjar svaret och beställarnamn inte styr resultatet.
* **Likhet:** cosinuslikhet. **Ristarrangordning:** närmaste centroid bland ristare med minst fem säkra
  inskrifter.
* **Vad "likhet" betyder:** cosinuslikheten (0–1) mellan inskriftens särdragsvektor (TF-IDF, normerad) och
  ristarens medelvektor. Det är ett deskriptivt mått, inte en sannolikhet. Rangordningen är en
  närmaste-centroid-klassificerare.
* **Signifikans för likheten:** p = andelen av andra ristares säkra inskrifter som är minst lika lika
  ristarens profil (empirisk nollfördelning, (k + 1)/(n + 1)). Eftersom den mest lika av alla ristare väljs
  anges även ett justerat p med max-statistik (Westfall–Young): andelen inskrifter med känd ristare vars högsta
  likhet med en *annan* ristares profil är minst lika hög – samma urval som när förstavalet görs. Fram till
  2026-10-11 justerades i stället med Bonferroni (p × 27 ristare); med 459 inskrifter i nollfördelningen är det
  minsta möjliga p 1/460, så det justerade värdet kunde aldrig gå under 0,05 och ingen likhet kunde bli
  säkerställd. Med max-statistiken är 66 av 182 bekräftelser av Rundatas ristare, 20 av 53 nya förslag och 3 av 15
  motsägelser säkerställda (justerat p under 0,05). Dessutom anges hur typisk likheten är för ristarens egna
  inskrifter (lämna-en-ute). Formelspråket gör många inskrifter lika, så metodens samlade träffsäkerhet (nedan) är
  fortfarande ett viktigt mått vid sidan av p-värdet.
* **Utvärdering** (lämna-en-ute, 27 ristare, 459 inskrifter, Rundata 2014): rätt ristare först i 61 %,
  bland de tre första i 71 %; för enbart signerade inskrifter (n = 135) först i 60 %. Slumpnivå 4 %.
  Attribuerade inskrifter kan ha attribuerats just på grund av ortografin, därför redovisas siffran för
  signerade separat.
* **Godtycklig text:** samma modell kan rangordna ristare för en text utanför Rundata, t.ex. appens egen
  läsning eller ett nyfynd (`rank_text`). Egennamn tas bort via normaliseringen eller via namnformer kända
  från Rundata, och en sten som finns i modellen utesluts ur sin egen ristares profil.

## 8. Läsning mot Rundata (utan AI)

Källkod: `src/reading.py`, `api/routers/phonetics.py` (`POST /api/phonetics/compare`).

**Vitki läser inte runor med AI.** Fram till 2026-10-20 fanns sidan *Språk & Fonetik* med en blind AI-läsning
(språkmodellen fick bilden men inte signumet), normalisering, IPA, ljudlagar och uppläsning. Den togs bort, av två skäl
som båda är mätta. (1) I testet med Sö 113 gav tre blinda läsningar tre olika, trovärdiga men påhittade texter (6–24 %
av runorna stämde), en av dem Jellingestenens text (DR 42, 95 % lika): modellen återgav inlärda inskrifter. (2) Med
appens strikta instruktion ("läs bara det som syns, gissa aldrig") gav Claude Opus 2026-10-20 nästan bara streck för
oläsliga runor (U 935: enbart streck; U 124, Sö 52: enstaka tecken), träff 0 mot Rundata på de tre stenar som hann
provas innan provet stoppades (`utdata/stilgrupp_ai/lastest.py`). En genomgång av 42 anonymiserade foton i samma
session visade detsamma för läsning i allmänhet: det som går att "läsa" på ett foto är minnesformlerna (*stæin þansi*,
*æftiR*), och en träff mot Rundata på dem säger inte att bilden lästs. Normalisering och översättning finns i Rundata
för alla publicerade inskrifter, och sannolikhetsmodellens läsning (8.1) räknas utan AI. Det som var tillförlitligt på
sidan – jämförelsen mot Rundata, ordformerna, ortografin och valideringen – är beräkningar och står kvar som API och i
rapporterna, så att en egen läsning (en forskares läsning av en bild, ett nyfynd) kan prövas.

* **Jämförelse med Rundata:** translitterationerna jämförs ord för ord och runa för runa (difflib).
  *Överensstämmelse* = andelen av våra runor och ord som finns i Rundatas läsning, *täckning* = andelen av Rundatas
  text som vår läsning omfattar (en beskuren bild kan stämma helt men täcka lite). Bara sammanhängande träffar på
  minst tre runor räknas, skiljetecken och textkritiska tecken ignoreras och Rundatas oläsliga tecken redovisas
  separat.
* **Ordformer:** varje form i normaliseringen slås upp bland Rundatas normaliserade former i vikingatida inskrifter;
  obelagda former flaggas för granskning.
* **Ortografi för läsningen:** samma modell som i avsnitt 7, med stenen själv utesluten. Används i syntesen när Rundata
  saknar en användbar text (t.ex. nyfynd), med 30 % lägre tillförlitlighet.
* **Validering – får läsningen visas som stenens text?** (`src/reading.py`, `validate`): läsningen prövas utan AI
  mot (1) stenens text i Rundata, (2) alla kända inskrifter i Rundata (trigramfilter och samma
  överensstämmelsemått) och (3) andra läsningar av samma bild. Status: *bekräftad* (≥ 80 % av runorna i stenens
  läsning), *delvis* (50–80 %), *ej bekräftad* (< 50 %), *annan inskrift* (liknar en annan känd inskrift minst
  60 % och tydligt mer än stenens egen – texten är troligen en inlärd inskrift) eller *ej prövbar* (Rundata
  saknar text; då krävs att flera läsningar stämmer minst 80 % med varandra). En läsning med färre än 12 läsbara
  runor är alltid *ej prövbar*: ett kort ord som *sin* finns i de flesta inskrifter, så att det stämmer säger
  ingenting om att bilden är läst. Bara bekräftade, delvis bekräftade och samstämmiga läsningar visas som läsning,
  och bara de används som belägg i syntesen. I rapporter redovisas en obekräftad läsning aldrig som stenens text.
* **Bilder att läsa själv:** 2D-fliken på 3D-sidan visar foto, RTI-vy och reliefbilderna ur 3D-skanningen (strykljus
  från fyra riktningar, ett kombinerat relief där varje spår blir mörkt oavsett riktning, och djup under stenytan),
  räknade från den sida som vetter mot betraktaren i 3D-vyn (2d).

### 8.1 Sannolikhetsmodell för runtext

Källkod: `src/runlm.py` och `src/rungloss.py`; prov: `scripts/runlm_calibrate.py`, `scripts/runlm_compare.py`,
`scripts/runlm_dating.py`, `scripts/runlm_gloss_test.py` och `scripts/runlm_gloss_da_test.py`;
tillämpning på Maltstenen: `scripts/malt_decode.py`.

Modellen läser en inskrifts huggna grupper (runorna mellan stenens egna skiljetecken, utan Rundatas ordgränser)
och anger för varje möjligt ord hur sannolikt det är, utan att använda någon tolkning av inskriften.

* **Stavning:** varje normaliserad ordform har en regelbaserad mängd stavningar med 16 runor (a → a/ą, æ → a/i/e,
  au → au/u, nasal före klusil kan falla bort, inga dubbla runor …). Regelvalens sannolikheter skattas med EM ur
  16 479 par av huggna ord och Rundatas normaliserade form (1 479 inskrifter där orden går att para ihop).
  Ord med egna belägg får dessutom sina faktiska stavningar (vägt mot reglerna med κ = 2). Ord som bara finns i
  Eddan får också æ → ai (äldre diftong) och slut-r → ʀ med sannolikhet 0,3 respektive 0,5.
* **Språk:** ett ordbigram med absolut rabatt (Kneser–Ney, D = 0,75) över Rundatas normaliserade text för
  vikingatida inskrifter, blandat med Eddans och Snorres Eddas ordförråd (unigram, vikt 0,03) och ett okänt
  ord (vikt 0,01) vars runor skattas med ett trigram över runor i ord.
* **Skiljetecken:** en ordgräns med skiljetecken har sannolikheten d, en utan 1 − d, där d är andelen ordgränser
  med skiljetecken i träningsmaterialet (0,70). Radbyten är inte skiljetecken.
* **Avkodning:** framåt–bakåt-beräkning över alla sätt att dela grupperna i ord ger varje ords
  a posteriori-sannolikhet och textens totala sannolikhet. Former med samma nyckel (samma ord i olika
  normalisering: stæinn = sten = steinn, sin = sinn) slås ihop. Den redovisade läsningen är den väg som
  maximerar det väntade antalet rätt lästa runor.
* **Omstridda runor:** texten läses med varje kombination av de omstridda läsningarna; en lästs sannolikhet är dess
  andel av den totala sannolikheten, med lika förhandschans. Det är språkets omdöme, inte en mätning av stenen.
* **Prov och kalibrering:** femfaldig korsvalidering på de 808 inskrifter där Rundatas ord täcker den huggna
  texten exakt (10 669 ord). Modellen ger rätt ord (samma nyckel) i 81 % av fallen och rätt ordgränser i 92 %.
  Dess råa sannolikheter är för höga (säger 99 %, rätt i 93 %). De kalibreras med en logistisk regression på
  logit(p), ordets frekvens, om ordet bara finns i Eddan, ordets längd och stavningens sannolikhet, skattad
  på fyra delar och prövad på den femte; kalibreringsfelet (ECE) sjunker från 0,12 till 0,003. För sällsynta
  ord (högst två belägg) är den kalibrerade sannolikheten fortfarande något hög (säger 96 %, rätt i 89 %).
* **Begränsningar:** modellen känner bara ord som finns i Rundata eller Eddan, och namn i ovanlig stavning blir
  okända (t.ex. *uifrþuʀ* på Maltstenen). Sannolikheten för en hel läsning räknas som produkten av ordens
  kalibrerade sannolikheter och förutsätter oberoende; den är en storleksordning.
* **Steg 2 – fler ordpar (2026-10-15):** avsnitt där Rundatas ordantal i translittereringen och normaliseringen
  skiljer sig (skadade, återställda eller sammanskrivna ord) radas upp med dynamisk programmering (1:1, överhopp,
  2:1 och 1:2) över grova ljudklasser; ett par räknas bara om orden är runor och likheten minst 0,6 (`align`).
  Prövad på avsnitt där svaret är känt: precision 99,9 %, täckning 98,0 %. Ordparen ökar från 17 341 i 1 479
  inskrifter till 27 218 i 2 877. Rätt ord ökar med 0,84 procentenheter (95 % intervall med stenarna omdragna
  +0,56 till +1,12; 103 stenar bättre, 38 sämre, teckentest p = 4·10⁻⁸). Medeltida inskrifter som extra
  stavningsdata gav +0,07 procentenheter (ej skiljbart från slumpen) och används inte.
* **Steg 3 – epoker, trakt och ristare (2026-10-15):** varje inskrift får en plats i ett träd: era (vikingatid,
  medeltid) → fas (tidig: 800- och 900-talet; sen: 1000–1150) → epok (800-talet, 900-talet, 1000–1070, 1070–1150)
  → trakt (Danmark, Svealand, Götaland …) → landskap (signumets prefix) → ristare (`context`). Epoken tas ur Rundatas
  datering (spann över 120 år räknas som okänt) eller, för svenska stenar, ur stilgruppen (RAK, Fp, Pr1–Pr5).
  Stavningens regelval skattas för varje nod och dras mot noden ovanför (Dirichlet, α = 100); ordens faktiska
  stavningar per epok vägs mot hela vikingatiden (κ = 50); ordföljden per epok backar till fasen och hela
  vikingatiden med en dämpning h/(h + 200), där h är hur ofta föregående ord förekommer i epoken.
  När epoken inte är känd läses texten i alla fyra epokerna och läsningarna vägs efter hur sannolik texten är i
  varje epok (`decode_epochs`); det är också modellens datering. Ristaren används inte vid datering.
  * Läsning: med gissad epok 82,1 % rätt ord (−0,14 procentenheter mot steg 2, ej skiljbart från slumpen) och
    92,6 % rätta ordgränser (+0,27, p = 0,0002). Utan dämpningen blev orden 0,2–0,4 procentenheter sämre. En
    anpassning till den enskilda stenens stavning (EM på en första läsning) ändrade ingenting och används inte.
  * Datering (`scripts/runlm_dating.py`, femfaldigt prov på 2 046 daterade inskrifter med minst 10 läsbara runor):
    rätt epok i 58 % (att alltid gissa den vanligaste epoken ger 44 %), högst en epok fel i 93 %. Tidig mot sen
    vikingatid: balanserad träff 65–69 %. 800-talet har bara 16 provstenar och känns igen i 0 av 16 med
    epokernas andel som förhandschans och i 9 av 16 med lika förhandschanser. Dateringens säkerhet är för hög
    (säger 98 %, rätt i 81 %).
* **Namn (2026-10-15):** namn som ordförrådet saknar sätts ihop av namnled (`NameModel`): förled + efterled +
  ändelse (Ás-bjǫrn-aʀ) eller enkel stam + ändelse. Leden tas automatiskt ur namnen i träningstexterna (ord som
  Rundata märker med citattecken): ett led räknas om det förekommer i minst tre olika namn. Varje led stavas med
  stavningsmodellen. Ett sammansatt namn får sannolikheten λ · f(föregående ord) / f₀, där f är hur ofta ett namn
  följer ordet i träningen och f₀ andelen namn överlag; λ = 0,05 (prövat 0,005–0,4 på första delprovet).
  Felanalysen före namnmodellen: namn stod för 59 % av felen (25 % av namnen lästes fel, mot 8 % av vanliga ord).
  Med namnmodellen: 83,5 % rätt ord (+1,42 procentenheter mot steg 3, 95 %: +1,09 till +1,74; 150 stenar bättre,
  19 sämre) och 93,9 % rätta ordgränser (+1,32). Mot steg 1: +2,12 och +1,88 procentenheter.
* **Kalibrerad datering:** dateringens sannolikheter mjukas upp med en temperatur T, skattad så att
  logförlusten på dateringsprovet blir minst (`fit_temperature`, `epoch_posterior`), så att en angiven säkerhet
  motsvarar hur ofta dateringen stämmer.
* **Provets facit underskattar modellen något:** Rundata normaliserar samma ord olika i olika delar av materialet
  (*ræisti*/*resþi*, *þænsi*/*þannsi*, *hialpi*/*hiælpi*); när modellen väljer den andra formen räknas det som fel.
* **Översättningsutkast (2026-10-15, `src/rungloss.py`, prov `scripts/runlm_gloss_test.py`):**
  * **Ordlistan.** Den lärs ur Rundatas normaliserade texter och deras engelska översättningar med IBM-modell 1 (EM
    över vilka ord som står tillsammans i samma avsnitt och dess översättning, med ett tomt ord för engelska ord
    utan motsvarighet). Någon tryckt ordbok används inte. Ett ord räknas som namn om Rundata citatmärker det i
    minst hälften av beläggen. Utkastet är ord för ord.
  * **Resultat** (femfaldigt prov på de 808 provstenarna, mätt med de betydelsebärande engelska orden): från
    Rundatas normalisering är 81 % av utkastets ord med i Rundatas översättning, och utkastet får med 75 % av
    översättningens ord. Hela vägen från de huggna runorna är siffrorna 75 % respektive 69 %. Unika texter som
    Maltstenen översätts dåligt, eftersom deras ord saknas i ordlistan.
* **Svenska via danska (2026-10-16, prov `scripts/runlm_gloss_da_test.py`):**
  * **Källan.** Danske Runeindskrifter (runer.ku.dk, Nationalmuseet och Københavns Universitet) översätter de danska
    inskrifterna till danska. Tabellen kopierades för hand (utdata/Malt/kallor/runer_ku/, används internt med
    källangivelse). 596 översättningar paras med Rundata via Rundatas hänvisning till det danska numret (`load_danish`).
  * **Den danska ordlistan.** Den lärs mot Rundatas fornvästnordiska standardformer (`normalization_ows`), eftersom
    Rundata normaliserar danska och svenska stenar olika (*sten* resp. *stæin*, båda *stein*). En läsning förs över
    till standardformerna med en tabell lärd ur Rundatas två normaliseringar (`ows_map`).
  * **Vilket ord som går via danska.** Ett ord går den danska vägen när den danska ordlistan har sett det minst tre
    gånger och ger det danska ordet minst 40 % sannolikhet, när det danska ordet finns i den handgranskade listan
    `DA_SV`, och när den engelska ordlistan inte ger ett annat svenskt ord med högre sannolikhet. Namn tar den danska
    formen i svensk stavning (Thorbjørn → Torbjörn) om den liknar det fornnordiska namnet. Övriga ord går som förut
    via engelskan.
  * **Ordföljd.** Possessiv och demonstrativ som fornspråket sätter efter substantivet flyttas före det (*faður sinn*
    → *sin fader*, *stæin þennsi* → *denna sten*), med komma efter ett namn. Adjektiv flyttas på samma sätt (*drængʀ
    goðr* → *god dräng*). Numerus rättas efter substantivet (*denna/dessa*).
  * **Prov.** 215 vikingatida danska inskrifter, femfaldigt: ordlistorna lärs utan provdelen, och provdelen
    översätts från Rundatas normalisering. Facit är den danska översättningen överförd till svenska ord för ord.
  * **Resultat.** Andelen av utkastets betydelsebärande ord som finns i facit stiger från 41 % (via engelska) till
    48 % (via danska), och utkastet får med 43 % av facits ord i stället för 37 %. Andelen intilliggande ordpar som
    står så i facit stiger från 9 % till 25 % med enbart den svenska ordföljden och till 32 % med den danska vägen.
  * **Förbehåll.** Facit och den danska vägen använder samma ordlista, så vinsten i ordval är något överskattad.
    Vinsten i ordföljd gäller samma ord och är inte påverkad av det. Någon svensk översättning att pröva mot finns
    inte i Rundatas data.
  * **Räckvidd.** Den danska ordlistan känner 65 % av orden på de svenska vikingatida stenarna, främst formelorden.
* **Ifyllning med spår och ristare (2026-10-16):**
  * **Spår.** `restore(allowed=…)` begränsar varje förlorad runa till de runor som dess synliga rester tillåter.
    `scripts/rune_traces.py` räknar ut vilka runor som ser likadana ut i en bevarad halva eller tredjedel av runan:
    runorna ritas med typsnittet Apple Symbols, en tolerans på 5 % av runhöjden används, och ett bevarat streck räknas
    liksom en bevarad tom yta. I genomsnitt återstår 4,4 av 24 runor.
  * **Simulerat prov.** Samma 1 616 luckor som i maskeringsprovet, jämförda sten för sten:
    * halva runan synlig: hela ord 56 → 85 %, ord inne i luckor 72 → 84 %, hela namn 12 → 66 % (237 stenar bättre, 4 sämre)
    * blandat (inget, en tredjedel eller hälften lika ofta): hela ord 77 %, namn 49 %
    * spåren är rena typsnittsformer, så resultatet visar vad spåren är värda i bästa fall
  * **Ristaren.** Prövad på de 270 provstenarna med en enda säker ristare (540 luckor): stavning ner till landskapet,
    ristarens egen stavning och namnen i ristarens krets (`carver`, `lam_carver` 0,1). Ingen mätbar vinst: ord inne i
    luckor 81,1 → 81,1 %, hela ord 62,2 → 62,2 %. Ristarens stavning dras starkt mot landskapets (α = 100), och
    modellen har redan lärt sig ristarens övriga stenar.
* **Verkliga luckor, slutkörning (2026-10-16, `scripts/runlm_gaps_report.py`):**
  * **Omfattning.** 650 luckor som Rundatas utgivare har återställt. Inskrifter som Rundata inte tolkar alls är
    borttagna.
  * **Samma ord som Rundata.** 72 % räknat strikt och 79 % när samma ord i annan böjning eller normalisering räknas
    lika (`same_word`). Där modellen säger minst 95 % är det samma ord i 96 % av fallen (399 luckor).
  * **Facit.** Rundatas återställning av en runa som är förlorad på stenen är själv en utgivargissning, så måttet
    jämför två bedömningar. Bara maskeringsprovet har ett verkligt facit.
* **I appen (2026-10-16, `src/textmodel.py`, `/api/textmodel/`):**
  * **Panelen.** Inskriftssidans panel "Läsning och luckor" visar modellens läsning, de förlorade runorna (1–4 i följd)
    med förslag, dateringen ur språket (kalibrerad med temperaturen i `data/runlm_calibration.json`) och utkast på
    svenska och engelska.
  * **Ingen läcka.** En inskrift läses alltid av den av fem modeller som inte är tränad på den (delning efter signum,
    crc32 mod 5), så att Rundatas återställning inte läcker in.
  * **Spår från användaren.** Användaren kan markera vilka runor spåren i en lucka kan vara och få allt omräknat.
  * **Procenten för ifyllda ord.** För ett ord med ifyllda runor visas hur sannolikt ordet är i luckan, inte i läsningen
    där ifyllningen redan är given.
  * **Längre luckor och förlorad text.** Luckor med fler än fyra förlorade runor och text som förlorats i okänd
    omfattning lämnas öppna.
  * **Flera förlorade runor i samma ord.** Om det står högst tre bevarade runor mellan dem fylls de som en enda
    lucka (`?a??bi?rn`), och de bevarade runorna däremellan låses till sig själva. Fylls de en i taget tar varje lucka
    de andras bästa fyllning för given, och ordet ser säkrare ut än det är. På U 508 gav det *Gæiʀbjǫrn* 100 %;
    fyllda tillsammans blir det *Fastbjǫrn* 50 % och *Gæiʀbjǫrn* 50 %. Maskeringsprovet döljer bara en sammanhängande
    följd, så det har inte prövat detta. Rapporten över de verkliga luckorna (ovan) är räknad en lucka i taget och
    är därför för säker där flera luckor sitter i samma ord.
  * **Mjuka spår (2026-10-16).** Användarens spår räknas som troliga, inte säkra: en ifyllning som strider mot ett spår
    prövas ändå, med faktorn 0,05 per runa som inte stämmer. I ett simulerat prov med vart femte spår felläst (1 616
    luckor, fem delar) gav hårda spår 44 % rätta helord och 62 % rätt bland svar med minst 95 % säkerhet; mjuka spår gav
    73 % och 96 %. Med rätt lästa spår: 81 % (mjuka) mot 85 % (hårda). Bevarade runor inne i en sammanslagen lucka är
    låsta (`hard`).
  * **En lucka över två ord.** I en odelad grupp kan två luckor som fylls som en täcka slutet av ett ord och början
    av nästa (`af?fa?ur`, *aft faþur*). Varje position i luckan får därför sitt eget ord (`restore_all(positions=...)`).
    Panelens procent för ett ord räknas där ordet står, och luckrapporten ger varje lucka ordet på sin egen plats.
    Före rättelsen (2026-10-16) fick alla delar spannets första ord. På U 318 rapporterades då *æftiʀ* för luckan
    i *faður*, fast runan var rätt ifylld, och panelen kunde visa nästan 0 % för ett rätt ifyllt ord.
  * **Läsningen väger spåren som luckan (2026-10-16).** Efter ifyllningen väljs den bästa kombinationen av alla
    luckors förslag efter hur sannolik hela texten är. Det steget räknade tidigare varken med mjuka spår eller med namn
    från närliggande stenar, så panelens läsningsrad och "bästa fyllning" kunde visa ett ord som spåren talade emot,
    medan luckans ordlista gav ett annat. Nu vägs båda in där också (`restore_all`, `textmodel-8`). Valideringen
    ovan bygger på luckornas ordlistor och påverkas inte.
  * **Ordet i en lucka kalibreras per ordklass (2026-10-16).** Modellens sannolikhet för ordet i en lucka stämde
    för formelord (de 50 vanligaste orden) men var för hög för namn och andra ord. På 631 luckor som utgivarna har
    fyllt hade modellen rätt i 99 procent av formelorden när den sa minst 95 procent, men i 93 procent av namnen och
    90 procent av de andra orden. Förstavalet kalibreras därför per klass: P(rätt) = sigmoid(a_klass + b_klass·logit(p)
    + c·log(förlorade runor)). Klassen är formelord, namn (§ hos modellen eller skrivet som namn i Rundata) eller andra
    ord. Alternativen delar på resten i samma proportioner och får aldrig mer än förstavalet. Femdelad korsvalidering
    med hela stenar utanför: kalibreringsfelet sjönk från 5,9 till 1,5 procentenheter och Brier-poängen från 0,105
    till 0,099 (`scripts/runlm_gap_calibrate.py`, `gap_recal` i `data/runlm_calibration.json`, `textmodel-10`).
    Kalibreringen gäller luckor av det slag utgivarna redan har fyllt, inte öppna luckor (se kapitel 18).
  * **Namnleden stavas som på stenarna (2026-10-16).** Namn som ordförrådet saknar byggs av förled, efterled och
    ändelse. Leden stavades tidigare bara efter stavningsreglerna, och de saknade att g efter vokal ofta skrevs h:
    förledet Ragn- är huggen *rahn* 17 gånger i Rundata, men reglerna gav den stavningen nästan ingen chans.
    Kvinnonamn på *-ví/-vé* kunde inte byggas alls, eftersom ändelsen *-i* togs bort och efterledet då blev *v*. Nu
    lärs varje leds stavningar ur de huggna namnen (blandade med reglerna), efterled på två runor tillåts och *-ví/-vé*
    behåller sitt efterled. På U Fv1971;212B föll Víseti från 97 till 44 procent när *rahnui* blev Ragnví. På 624
    återställda luckor (samma prov som ovan) steg rätt namn från 75,7 till 78,4 procent, formelorden var oförändrade
    och andra ord sjönk från 51,1 till 49,6 procent (två luckor). Kalibreringen per ordklass är omskattad på den nya
    modellen (`textmodel-11`). Samma dag rättat: att tillåta alla efterled på två runor lät *-uð* ta platsen för *-guð*
    (Auðguðr), så nu är bara *-ví/-vé* så korta; och ett huggit namn lär bara ut stavningar om högst en av dess delar
    saknar stöd i reglerna, eftersom felaktigt delade namn annars gav skräpstavningar (*asluh* för *-laug*). På samma
    624 luckor: rätt namn 65,4 → 67,6 procent, andra ord och formelord oförändrade, 98,1 procent rätt när modellen sa
    minst 95. Maskeringsprovet oförändrat (inne i ord 72,3, helt ord 55,9 procent). Kalibreringen per ordklass görs nu
    med scikit-learn, och namnen i den känns igen också när Rundata skriver dem med hakparentes (”Alfdi[s]”)
    (`textmodel-12`).
  * **Ordkalibreringen omskattad (2026-10-16).** Läsningsprovet (808 inskrifter, 10 669 ord, fem delar) med modellen
    efter dagens ändringar: samma ord som Rundata 84,1 procent (81 den 14 oktober), rätt ordgräns 94,2 procent.
    Kalibreringsfelet för ordens sannolikhet sjönk från 8,7 till 0,6 procentenheter. Omräkningen skrivs nu av
    `scripts/runlm_calibrate.py --write_recal` (`textmodel-13`).
  * **Prövat mot färdiga bibliotek (2026-10-16).** Ordföljdens Kneser–Ney-bigram ger samma sannolikheter som NLTK:s
    (största skillnad 10⁻¹⁶ på 3 000 ordpar; testet ligger i tests/test_runlm.py). Rabatten 0,75 gav lägst perplexitet
    på inskrifter som modellen inte sett (57,5) jämfört med 0,5, 0,9 och modified Kneser–Ney (58,3). Den egna
    Newton-anpassningen av kalibreringen gav samma koefficienter som scikit-learn; isoton kalibrering per klass gav
    sämre Brier-poäng och log-förlust och används inte.
  * **Ordklasser (2026-10-16, används).** Ordföljd efter ordklass, där klasserna lärs ur texterna (grannord, PPMI,
    SVD och k-means med scikit-learn; `word_classes`), blandas med ordens bigram med vikten 0,2 och 200 klasser.
    Perplexiteten på inskrifter som modellen inte sett sjönk från 47,3 till 45,3. Maskeringsprovet: rätt ord inne i
    ord 72,3 → 73,0 procent (namn 49,1 → 51,4), hela ord 55,9 → 56,6. Luckprovet oförändrat (80,9 procent; 98,2
    procent rätt vid minst 95). Klasserna blir rimliga (genitiverna *hans, hennaR, sina, þæiRa* i en klass), men *þa*
    är för sällsynt och mångtydigt för att klassas rätt, så felet på Sö 280 kvarstår. Ord- och luckkalibreringen är
    omskattade med klasserna (`textmodel-14`).
  * **Ordgränser (2026-10-16).** I en text utan skiljetecken väljer modellen själv var orden börjar, och den kan låna
    runor från ett ord den inte känner. På U Fv1971;212B tog den *ui* från *rahnui* (Ragnví) och fyllde *uis??i* till
    *Víseti* (97 %). Panelen läser därför om texten med utgivarnas ordgränser (mellanrummen i Rundatas translitterering)
    när orden runt en lucka delas annorlunda än modellens. Det görs med huvudläsningen och, om den finns, med Rundatas
    alternativa läsning (§Q), förutsatt att runorna är desamma. Ändras luckans bästa ord visas båda förslagen
    (`_boundaries`, `textmodel-9`). På U Fv1971;212B ger alternativläsningen *s??i iok* Siggi 35 %, och 88 % med
    Källströms iakttagelse (k eller f).
  * **Snabbare luckfyllning (2026-10-17).** För varje kandidat i en lucka läste modellen om hela texten. Ett ord går
    aldrig över ett skiljetecken eller en förlorad runa, så texten före luckans grupp slutar i ett fast framåtläge och
    texten efter den i en fast bakåtfunktion av sista ordet. Båda räknas nu en gång per lucka, och varje kandidat läser
    bara sin grupp (`SplitText`). Resultatet är detsamma (största skillnad 10⁻¹⁴ på 12 stenar, test i
    tests/test_runlm.py) och 4,7 gånger snabbare. Stenar med mer än 256 kombinationer av luckornas förslag söks lucka
    för lucka (iterated conditional modes); på U 512 gav det samma bästa fyllning som den fullständiga genomgången.
  * **Ristarens egna skiljetecken (2026-10-17, `textmodel-15`).** Hur ofta en ordgräns markeras skiljer sig mycket
    mellan ristare: de flesta markerar nästan alla, några inga. Andelen för en sten skattas ur dess egna skiljetecken
    och de ordgränser modellen väntar sig inne i grupperna (två varv EM), dragen mot korpusens fördelning, en
    betafördelning (1,17; 0,54) skattad med momentmetoden (`stone_divider_rate`). Läsprovet på runstenar: rätt ordgräns
    95,1 → 95,4 procent (+0,31 procentenheter, 95 %: +0,12 till +0,49; 41 stenar bättre, 13 sämre), orden oförändrade.
    Luckprovet 82,0 → 82,3 procent.
  * **Dokumenterade luckor (2026-10-17).** Runor inom hakparentes i Rundata är förlorade men kända från äldre
    avbildningar. De har fallit bort av fysiska skäl, inte för att svaret var lätt, och liknar därför appens luckor
    bättre än de luckor som utgivarna har fyllt: utgivare fyller helst där svaret är givet. Varje sådan följd av 1–4
    runor inne i ett ord görs till en lucka (`scripts/runlm_documented_test.py`). På 361 luckor på runstenar gav
    modellen rätt ord i 67 procent, och när den sa minst 95 procent hade den rätt i 97. Men i mellanregistret var den
    för säker: med kalibreringen från de återställda luckorna var kalibreringsfelet 12,6 procentenheter. Felen gäller
    mest namn: fel namn (31 av 119 fel), namn i stället för ett vanligt ord (28), och namn som modellen satt ihop av
    namnled blev rätt i 4 av 22 dokumenterade luckor mot 21 av 31 återställda. En lägre vikt för sådana namn (0,3 och
    0,1) ändrade inte träffsäkerheten.
  * **Luckkalibreringen omskattad (2026-10-17, `textmodel-15`).** Kalibreringen skattas nu på tre källor tillsammans:
    de återställda luckorna, maskeringsprovet och de dokumenterade luckorna, var och en med en egen konstant. Appen
    använder de dokumenterade luckornas nivå. Namn som modellen satt ihop av namnled är en egen klass, och en lucka som
    omfattar ett helt ord har en egen term, lärd ur maskeringsprovet eftersom de dokumenterade luckorna alltid ligger
    inne i ett ord. Korsvaliderat på runstenar: de dokumenterade luckorna 2,5 procentenheters kalibreringsfel (Brier
    0,119 → 0,083), och påståenden om minst 95 procent stämde i 98,7 procent (155 luckor); maskeringsprovet 2,7 inne i
    ord och 4,3 för hela ord, minst 95 procent rätt i 96 och 97 procent. Det svåra maskeringsprovet, där bara ord
    utanför de 50 vanligaste döljs, ingick inte i skattningen: kalibreringsfelet inne i ord sjönk där från 17 till 4,5
    procentenheter, och minst 95 procent stämde i 93. För hela ord i det provet är modellen fortfarande för säker (12
    procentenheter), men sådana luckor fylls nästan aldrig rätt utan spår. `VALIDATION` räknas sedan textmodel-15 på
    runstenar (`utdata/runlm_forfining/validering_tm15.py`).
  * **Alternativens procent (2026-10-17, `textmodel-16`).** Bara luckans förstaval kalibreras. Förut delades det som
    förstavalet förlorade ut på alternativen i proportion, aldrig över förstavalet. På de dokumenterade luckorna, med
    alla förslag sparade, gav det alternativen sammanlagt 57 väntade rätt där 41 var rätt, och ett starkt alternativ
    blev lika stort som förstavalet (Sö 206 med ett tänkt þ-spår: *roðnir* och *Hrungnir* 43,5 procent var). Nu får
    ett alternativ högst sin egen sannolikhet: 44 väntade mot 41 rätt, lägst Brier-poäng och log-förlust av fyra
    prövade regler (`utdata/runlm_forfining/alt_kalib.py`). Det som inget ord får lämnas öppet, och orden visas i
    ordning efter sin kalibrerade procent. Ett alternativ kan då hamna över förstavalet när förstavalet är ett ord av
    en klass där modellen ofta har fel. I de 53 sådana luckorna hade förstavalet rätt i 8 procent och alternativet i
    30. Att också välja ordet efter den kalibrerade procenten gav korsvaliderat 69,3 → 73,6 procent rätt ord på de
    dokumenterade luckorna, men 85,4 → 84,3 på utgivarnas. Det kräver att läsningens fyllning följer det valda ordet
    och är inte infört ännu.
  * **Namnkandidaterna får en egen kvot (2026-10-18, `textmodel-18`).** Namn är modellens största felkälla: i de
    dokumenterade luckorna lästes 75 procent av namnen rätt mot 96 procent av formelorden, och i 76 av 113 missar
    saknades facitordet helt bland kandidaterna. Orsaken var att namnmatcharens kandidater (`Names.match` på de
    bevarade runorna) rankades i samma lista som ordförrådets med sin förhandsvikt (~10⁻⁸ mot ~10⁻⁴) och alltid
    skars bort av kandidattaket innan poängsättningen fick se dem. Nu behåller namnkandidaterna sin egen ordning
    och läggs efter ordförrådets med en egen kvot (`name_cands` = 40 i `FILL`); poängsättningen väger dem sedan med
    full styrka. Hela kalibreringsunderlaget regenererades och listkalibreringen skattades om
    (`utdata/runlm_forfining/tm18_pipeline.py`). A/B på samma maskeringsprov (698 helordsluckor, runstenar): 8 luckor
    vunna, ingen förlorad (*guðfastr* ur `kuþf`, *þormóð*, *huskarl*, *gamall* …); hela ord oförändrade. De
    dokumenterade luckorna: 248 → 249 rätt av 361, och ≥95-nivåns felantal oförändrat (korsvaliderat 98,7 procent på
    155 luckor). `VALIDATION` räknas nu ur mask4-generationen av maskeringsprovet
    (`utdata/runlm_forfining/validering_tm18.py`); textmodel-17 publicerade mask3-generationens siffror, så talen är
    inte jämförbara ett mot ett.
  * **Toleranslagret (2026-10-20, `textmodel-19`).** 194 av maskeringsprovets 354 missar var ord vars huggna
    stavning inte fanns i träningsmaterialet (`utdata/runlm_forfining/tolerans_diagnos.md`). Nu utökas varje belagd
    stavning med regelgenererade varianter – slut-R/r faller, h- läggs till eller faller, en obetonad vokal faller,
    i/e/a skiftar, nasal faller före k/t/b, svarabhakti-i/u skjuts in; högst två regler per form – och en variant
    poängsätts från sin källstavning i sitt sammanhang med straffet λ per regel (`Model(tolerance=λ)`,
    `spelling_variants`). Analysplanen låstes innan några resultat fanns (`analysplan_tm19.md`, hash
    `analysis_plan_tm19.sha256`, avsnitt 1x): λ valdes bland 0,02, 0,05 och 0,1 på veck 0 enbart (0,02 var det enda
    över noll; 0,05 och 0,1 förlorade luckor), och veck 1–4 var provet: parvis mot textmodel-18 på samma 1 118 luckor
    vann lagret 8 och förlorade 2 inne i ord, vann 5 och förlorade 3 hela ord, och felen bland svar ≥ 95 procent gick
    från 16 till 15 – vunnet är lagrets avsedda fall (*sigmundr* ur *…r*, *hakonaR* ur *aR*, *ræistu* ur *ristu*),
    förlorat är byten till vanligare ord (*broður* → *faður*). Hela kalibreringsunderlaget regenererades med lagret,
    listkalibreringen skattades om och de dokumenterade luckorna kördes om (`tm19_pipeline.py`, allt i
    `utdata/runlm_forfining/tm19/`): 252 rätt av 361 (textmodel-18: 249) och 2 fel bland 158 svar ≥ 95 procent (4).
    Det svåra maskeringsprovet var oförändrat (403 mot 407 rätt först, 30 mot 31 säkra fel av 163 mot 176). Effekten
    är alltså liten – omkring en lucka på hundra – men åt rätt håll och utan nya säkra fel, vilket var planens
    villkor. `VALIDATION` räknas ur tm19-generationen (`validering_tm19.py`); textmodel-18:s underlag ligger kvar på
    toppnivån i `utdata/runlm_forfining/`. Diagnosen kvarstår: varianterna når sällan kandidattaket och förlorar mot
    teckenmodellen, så en egen kvot för varianter (som namnkvoten) är nästa kandidat och kräver en ny plan. Det
    förregistrerade blindtestet (textmodel-17) upprepas inte: det var ett engångsprov enligt sitt protokoll.
  * **Alla förslag kalibreras tillsammans, och valet följer procenten (2026-10-17, `textmodel-17`).** Att bara
    kalibrera förstavalet gjorde ordningen i listan beroende av vilket ord som råkade stå först. Nu får varje förslag i
    en lucka poängen u = a_klass + b_klass · log p, förstavalet dessutom en konstant per klass (dess sannolikhet är för
    hög just för att det valdes – winner's curse), och "inget av förslagen" en egen poäng ur luckan som helhet
    (konstant, log(förlorade runor), helt ord, log(1 − största p), källans konstant); sannolikheterna är en softmax
    över alltihop (`scripts/runlm_list_calibrate.py`, största sannolikhet med scipy; `gap_list` i
    `data/runlm_calibration.json`). Skattad på utgivarnas, dokumenterade och maskerade luckor; appen läser på de
    dokumenterade luckornas nivå och väljer det ord som får högst kalibrerad procent (`calibrate_words`), med
    fyllningen efter ordet. Inom en ordklass vänder ordningen aldrig; mellan klasser kan den. Varianter prövades
    korsvaliderat (`utdata/runlm_forfining/lista_varianter.py`): log(1 − största p) och förstavalskonstanten behövdes,
    en marginalterm tillförde inget. Korsvaliderat på runstenar, valt ord mot förstavalet: utgivarnas luckor 85,6 mot
    85,4 procent (ECE 7,2), dokumenterade 69,9 mot 68,3 (ECE 2,9), maskerade inne i ord 75,7 (ECE 2,3), hela ord 59,7
    (ECE 5,8). Det svåra maskeringsprovet (utanför skattningen) i stort oförändrat; där håller "minst 95 procent" bara
    92 procent – känt sedan tidigare. Sö 206: *Guðlaug* står åter före *Gíslaug* också med systerstensmodellen, och i
    *ru?niR* följer listan modellens egen ordning (*Hrungnir* 25, *roðnir* 20 – textmodel-16:s omkastning var en
    artefakt av att bara förstavalet kalibrerades).
  * **Böjning är en liten del av felen (2026-10-17).** Av de ord som modellen läste med rätt ordgräns men i annan form
    än utgivarna (112 av 1 693 i en femtedel av läsprovet) var alla normaliseringsvarianter i Rundata (*sin/sinn*,
    *stæin/sten*, *ræisþi/resþi*). Verkliga kasusfel, mest namn i nominativ i stället för ackusativ, var omkring 19,
    drygt 1 procent av orden. En grammatikmodell kan därför vinna högst omkring en procentenhet; spår ur skanningarna
    väger tyngre (simulerat: hela ord 56 → 81 procent).

## 9. Språkdrag (fonetisk stil och språkbruk)

Källkod: `src/language_profile.py`, `GET /api/research/language/{signum}`. Dragen läses ur Rundata genom
att translitterationen paras ord för ord med normaliseringen:

| Grupp | Drag | Definition |
|---|---|---|
| Ljud | Diftongen ai i *sten* | stæinn skrivet ai/ia (bevarad) eller i/e (monoftongerad) |
| Ljud | Diftongen au i *och* | ok skrivet auk eller uk/ok/ak |
| Ljud | Nasal före konsonant | n/m utskrivet eller utelämnat (bonta mot buta, kumbl mot kubl) |
| Ljud | h-bortfall | h i hans, hialpi skrivet eller inte |
| Ljud | Stungna runor | e, g, d, y används |
| Bruk | *efter* | första vokal och slut i æftiR |
| Bruk | *denna* | þina, þino, þana, þena |
| Bruk | Kristen bön, själsbön | Guð hialpi …, and/sálu |
| Bruk | Ristarsignatur | risti, hjó, markaði … |
| Bruk | *runor* | runaR, runa, runar |
| Ljud | Diftongen ai i alla ord | alla ord med æi i normaliseringen (ræisa, stæinn, þæiR): diftong, monoftong eller båda |
| Ljud | ʀ skrivet med r | ord som slutar på ʀ (æftiR, þæiR, syniR) skrivna med ʀ-runan, med r-runan eller båda |
| Ljud | o-runan för o-ljud | o-ljudet i broður, bóndi, móður, sun, kona skrivet med o-runan (ᚬ), u-runan eller båda |
| Ljud | Stungen i, u, k | e, y respektive g var för sig (stungen t, d, finns på för få stenar) |
| Bruk | æftiR eller at | minnesformelns preposition (at räknas bara före ett namn) |
| Skrift | Skiljetecken | vanligaste tecknet mellan orden (punkt, kolon, kryss, apostrof, plus), minst tre tecken |
| Skrift | Bindrunor | om inskriften har bindrunor (^ i translittereringen) |

De nio sista dragen lades till 2026-10-11. ai i alla ord bygger på 1 091 runstenar mot 663 för *sten* ensamt; ʀ
med r finns på 147 av 938 stenar där det kan avgöras, o-runan för o-ljud på 141 av 618, at på 322 av 1 352.
Dubbelskrivna konsonanter prövades också men förekommer nästan aldrig och togs inte med. Kristen bön känns sedan
samma datum igen även i osäkra läsningar och som Kristr hjalpi, Guð biargi, Guð lætti och Guðs móðir.

Ett drag räknas bara där inskriften har ordet. Ristarens profil är fördelningen över dennes säkra
inskrifter (stenen själv utesluten). Stenen stämmer i ett drag när värdet är ristarens vanligaste eller
förekommer i minst hälften av ristarens inskrifter med ordet. Dragen påverkas också av dialekt, tid och
beställare. De redovisas som kontroll och vägs inte in i kandidaternas poäng, eftersom stavningsdragen
delvis överlappar den ortografiska jämförelsen.

**Mot landskapet och signifikans** (från 2026-10-11, efter en granskning av U 92). Att ett drag stämmer säger lite om
det är vanligt i hela landskapet (bevarat ai i *stain*, *uk*, *iftiR* och ʀ-runa är det i Uppland). Varje drag vägs
därför med en sannolikhetskvot: hur vanligt stenens värde är hos ristaren genom hur vanligt det är på övriga runstenar
i landskapet (utan ristarens och stenens egna; additiv utjämning 0,5 per värde). Drag som upprepar ett annat lämnas
utanför summan (stungna runor när stungen i, u och k finns, ai i *sten* när ai i alla ord finns, själsbön när bön
finns). Summan av logaritmerna är stenens poäng för ristaren, och det empiriska p-värdet är andelen av landskapets
övriga stenar (som inte är av ristaren) som får minst lika hög poäng. Språkdragen stöder ristaren när p är under 0,05
och kvoten över 1, talar emot när kvoten är högst 1/3, och avgör annars inte frågan – vilket redovisas med texten i
stället för som "kan inte prövas". När ristaren har valts ut av en metod som själv bygger på stavningen (ortografin,
modellen, samlade belägg, okända ristare) räknas språkdragen inte som ett oberoende stöd: de kan tala emot men inte för.
En justering för urvalet (t.ex. Šidák över landskapets omkring 40 ristare) prövades men kan inte gå under 0,05 med
omkring 600 jämförelsestenar, eftersom det minsta empiriska p-värdet är 1/601. Exempel: U 92 mot Öpir – 13 av 16 drag
stämmer men tio är lika vanliga på andra uppländska stenar; utmärkande är *iftiR*, *uk* och o-runan; sammantaget 15,6
gånger vanligare hos Öpir, p 0,009 bland 589 stenar – men Öpir är vald av ortografin, så det räknas inte som stöd. Skiljetecken kodas som *blandat* när det vanligaste tecknet står för mindre än tre fjärdedelar
(U 92 har ' i början och · från *kira*), och *brøðr* räknas inte till o-ljudsorden (vokalen är ø).

## 10. Inskrifternas syfte per ristare

Källkod: `src/inscription_types.py`, `GET /api/research/categories`. Varje vikingatida runsten med text
får en eller flera kategorier med regler på Rundatas normalisering, engelska översättning och
translitterering: minnesinskrift, självminne, bro- och vägbygge, kristen bön eller formel, utlandsfärd,
arv och ägande, ting och offentlighet, magisk eller rituell (Þórr vígi, vígi þessi kuml, siði Þórr,
förbannelser, futharkrader, alu) och gränsmärke. Gränsmärken finns i praktiken inte bland de svenska
runstenarna i Rundata; där översätts *merki* (minnesmärke) med "landmark", vilket inte är en gräns.

För ristare med minst fem säkra inskrifter testas varje kategori mot genomsnittet (tvåsidigt
binomialtest, Benjamini–Hochberg-justerat q). När en ristare saknar en kategori anges sannolikheten för 0
av en slump, (1 − basnivå)^n. För sällsynta typer (magiska inskrifter 0,5 %) är 0 därför väntat även för
ristare med många stenar. I syntesen flaggas en stens typ bara när ristarens frånvaro är osannolik
(sannolikhet för 0 under 5 %).

### 10b. Stenens storlek och syfte

Källkod: `src/stone_dimensions.py`, `scripts/build_stone_dimensions.py`, `src/stone_size.py`,
`GET /api/research/stone_size`; fliken *Storlek och syfte* i Forskningsluckor.

**Mått.** Rundata saknar mått. Runor (RAÄ, utgåva 2020) ger för varje inskrift id:t i Kulturmiljöregistret, och
lämningens beskrivning där – hämtad via K-samsök, CC0 – anger oftast mått, t.ex. "1,5 m h, 0,5-0,6 m br och
0,2-0,25 m tj. Runhöjd 6-8 cm". Höjd, bredd, tjocklek och runhöjd läses ut med reguljära uttryck (intervall ger
mittvärdet; värden utanför 0,05–6 m räknas som tolkningsfel). Beskriver lämningen flera föremål ("1) … 2) …")
används bara delen som nämner stenens signum, eller den enda delen som är en runsten; annars räknas måtten som
oklara. Fragment markeras och utesluts ur analysen. Av 2 321 vikingatida runstenar fick 1 384 mått (1 101 med höjd,
utan fragment); 395 saknar id i registret, 350 har en beskrivning utan mått och 192 kunde inte skiljas från andra
stenar i samma lämning (bygge 2026-10-10, `data/stone_dimensions.json`). Höjden är oftast höjden över mark.

**Analys.** Hypotesen är att stora stenar restes för större syften och av mäktigare personer. Höjden (logaritmisk
skala) jämförs med inskriftens syfte (avsnitt 10), med statusord i normaliseringen (þegn/þiagn, dræng-, styrimann,
skipari, kunung-, goði, landmann), med antalet namngivna personer (Rundata markerar namn med citattecken), med
textens längd och med ristare (minst tio stenar). Bergart och lokal sed påverkar storleken, så allt jämförs
**inom landskap**: skillnaden i medel-log-höjd viktas över landskapen och prövas med 5 000 permutationer av
etiketterna inom landskap (Benjamini–Hochberg över testen); korrelationer räknas på rangordning inom landskap,
med samma permutation. Antalet personer redovisas också med textens längd bortrensad (partiell rangkorrelation),
eftersom en stor sten har plats för en längre text.

**Resultat (2026-10-10, 1 101 stenar, median 1,6 m).** Minnesinskrifter är 24 % högre än övriga i samma landskap
(q 0,004) – men inskrifter där minnesformeln inte går att läsa är oftare skadade och därför lägre, så skillnaden
kan vara skenbar. Stenar med statusord är 19 % *lägre* (75 stenar, q 0,02), tvärt emot hypotesen; ordens
betydelse (t.ex. *drengr* som ung krigare) är omdiskuterad. Bro- och vägbygge, kristen bön, självminne,
utlandsfärd, arv och ting skiljer sig inte (q ≥ 0,47). Större stenar har fler namngivna personer (rho 0,26) och
längre text (rho 0,30), men med textens längd bortrensad är sambandet med antalet personer svagt (rho 0,06,
p 0,06). Åsmunds stenar är 30 % högre än andras i samma landskap (p 0,03) men inte efter korrektion för antalet
ristare (q 0,31). Runhöjden följer stenens höjd (rho 0,22), vilket talar för att måtten är rimliga.
Slutsatsen är att textens innehåll förklarar lite av stenens storlek; andra tecken på makt (läge, monument med
flera stenar, ornamentikens kvalitet) är inte mätta.

## 11. Bergart och berggrund

Källkod: `src/geology.py`, `GET /api/research/geology/{signum}`.

* Stenens material i Rundata (fältbenämningar som "röd granit", "gråsten", "kalksten") förs till
  bergartsfamiljer (granit och närstående, gnejs och migmatit, sandsten, kalksten och marmor, basiska,
  vulkaniska, kvartsit, metasediment). "Gråsten" räknas till både granit och gnejs.
* Berggrunden hämtas ur SGU:s berggrundskarta 1:50 000–1:250 000 (WMS GetFeatureInfo) på platsen och i
  ett rutnät med 2,5 km mellanrum inom 10 km (49 provpunkter). Svaren cachas.
* Utfall: samma familj **på platsen**, **i närheten** (andel provpunkter), **inte i närheten** eller okänt.
* Källkritik: runstenar är ofta flyttblock eller transporterade (t.ex. Öl 1 av smålandsporfyr på Ölands
  sand- och kalksten). En avvikelse är en ledtråd om stenens ursprung, inte ett fel. Kartan täcker bara
  Sverige.
* I syntesen och Forskningsluckor jämförs även stenens bergart med bergarterna på ristarens säkra stenar.

## 12. Bilder och runformer (fliken på 3D-sidan)

Källkod: `web/src/components/TwoDAnalysis.tsx`, `api/routers/twod.py` (`/extract_features`), `src/graphemes.py`.
Till 2026-10-20 en egen sida (*2D-bildanalys*) med AI-bedömning av stilgrupp; nu fliken **Bilder och runformer** på
3D-sidan utan AI, eftersom bilderna nästan alltid kommer ur skanningen (2d) och runutsnitten hör ihop med spåranalysen.

* **Stilgrupp ur bild: borttagen 2026-10-20.** AI-bedömningen av stilgrupp (Pr1–Pr5, RAK, Fp, "Osäker" med egen
  säkerhetsangivelse) prövades samma dag (`utdata/stilgrupp_ai/stilgrupp_test.py`, 57 svenska runstenar med säker
  stilgrupp i Rundata och fri bild i Wikidata, stratifierat urval, Claude Opus med appens instruktion): exakt
  stilgrupp 35 % (slump 14 %, majoritetsgissning 21 %), 39 % bland de 91 % där modellen inte svarade "Osäker"; rätt
  grov klass (RAK / Fp / Ringerike Pr1–2 / Urnes Pr3–5) 71 %; inom en grannstilgrupp 83 %. RAK 8 av 11 och Fp 5 av 8
  rätt, men Pr1 spreds över fem svar, Pr3 blev oftast Pr4 och Pr5 blev Pr4 i 7 av 8. Modellens säkerhetsangivelse
  ordnade svaren rätt (60–79 %: 71 % rätt; under 60 %: 26 %) men var inte kalibrerad. Eftersom Rundata har säker
  stilgrupp för 1 038 stenar och en gissning med 35 % träff inte tillför något för de övriga, togs funktionen bort
  (API `/api/2d/analyze`, syntesens stilkontroll, stenanalysens steg och rapportens avsnitt). Fliken visar i stället
  Rundatas stilgrupp bredvid bilden. Provet står kvar som mätning i `utdata/stilgrupp_ai/`.
* **Runformer** (`src/graphemes.py`, särdragsversion `grapheme-2`): utsnittet kontrastförstärks (CLAHE),
  binäriseras (Otsu; minoritetsklassen räknas som ristning), beskärs till ristningen och läggs i en kvadrat
  med bibehållna proportioner, 64 × 64 px. Särdrag: HOG, täthet i 4 × 4 zoner och logaritmerat
  höjd/bredd-förhållande. Likhet: cosinus.
* **Validering av runformerna:** på syntetiskt ritade runor (ᛁ ᛏ ᚴ ᚱ ᛋ med slumpad stavtjocklek, lutning och brus,
  `src/synthetic_runes.py`) hamnar närmaste granne på rätt runa i 85 % av fallen. Den tidigare metoden låg
  på slumpnivå. Resultatet är ett mått på **formlikhet**, inte på samma ristare; på riktiga stenar påverkas
  det av vittring, belysning och utsnittets noggrannhet, och det är inte prövat på riktiga stenar.
* Jämförelser görs bara mellan utsnitt med samma särdragsversion och, om angivet, samma runtyp
  (långkvist, kortkvist, stungen m.fl.).
* Bilder kan komma från uppladdning, K-samsök, en reliefbild räknad ur 3D-skanningen, RTI-visaren eller
  **ristningskartan** från den automatiska spåranalysen (residualdjup, djupt = mörkt). Ristningskartan har
  samma pixelkoordinater som analysens granskningsbild, så ett runutsnitt där kopplas till de uppmätta
  snitten inom utsnittet.
* **Automatiska runutsnitt** (knappen "Hitta runorna") finns bara för ristningskartan från 3D-analysen: runorna
  som analysen själv känt igen (spåren grupperade per runa, `classify_strokes`) får en ruta som omsluter runans
  spårmittlinjer med 4 mm och en tiondel av runans storlek som marginal. Analysen vet inte vilken runa det är, så
  utsnitten sparas som "obestämd runa" tills användaren anger det. Varje sparat utsnitt får samma formbeskrivning som
  ett manuellt, märks som automatiskt (`auto`: "3d") och får en mindre miniatyr (128 px) och formvektorn avrundad
  till tre decimaler, så att ett projekt med många utsnitt ryms inom gränsen på 1 MB; högst 40 sparas åt gången.
  AI-markeringen av runor i andra bilder (`/api/2d/detect_runes`, med en AI-translitterering per ruta) togs bort
  2026-10-20 tillsammans med AI-läsningen (avsnitt 8).
* **Vridning (2026-10-27, `web/src/lib/runeForms.ts`).** Formbeskrivningen (HOG) tar hänsyn till riktningen, så en
  runa i en slinga som lutar jämförs fel med upprätta runor. Ett utsnitt kan vridas innan det sparas (vridningen gäller
  nya utsnitt tills den ändras) och ett sparat utsnitt kan vridas i efterhand. Utsnittet vrids runt sin mitt på en duk
  som rymmer hela det vridna utsnittet; hörnen fylls med medianen av kantens gråton, så att de inte blir nya kanter.
  Formbeskrivningen räknas om på det vridna utsnittet; för ett sparat utsnitt görs det på miniatyren, som är det enda som
  sparas, så varje vridning som inte är en multipel av 90° omsamplar den. Vridningen sparas (`rotationDeg`, medurs
  positiv). I ett prov med syntetiska t-runor var en runa i 45° lutning 0,18 lik en upprätt runa av samma form, och
  0,82 efter vridningen.
* **Ändra runa och ta bort** ett sparat utsnitt, så att automatiska utsnitt sparade som obestämd runa kan anges senare.
* **Jämför med ristare** (`RuneCropDetail`): samma runa på stenar i användarens projekt, grupperade efter de ristare
  Rundata anger med säkerhet (signerad eller attribuerad, inte osäker), med formlikheten i medel mot utsnittet, antalet
  utsnitt och stenar. Raden *Samma sten* (utsnittets syskon på samma sten) är referensen: ristarens egen variation.
  Stenar utan säker ristare bildar en egen grupp. Få utsnitt ger stor osäkerhet; det är ett underlag, inte ett prov.
* **Jämför två stenar** (`RuneFormCompare`, avsnitt 4): för varje runa som båda stenarna har utsnitt av,
  formlikheten i medel över alla par mellan stenarna mot medelvärdet av likheten inom stenarna. Är likheten mellan
  stenarna minst lika stor som inom dem (marginal 0,02) skiljer formen inte stenarna åt. Liknar runorna på samma sten
  inte varandra (under 0,5) varnar sidan för olika vridning. Utsnitten kommer ur användarens projekt (efter signum) och,
  för en korpuspost, ur de runformer som delats med den.

### 12b. Referensbiblioteket för runformer (2026-10-27)

Källkod: `api/routers/runbibliotek.py`, sidan `/runbibliotek`. Ett bibliotek med runor på de öppna 3D-skanningarna
(avsnitt 17), märkta med vilken runa i Rundatas text de är och vilken ristare Rundata anger för stenen, så att ett
runutsnitt kan jämföras med en känd ristares runor.

* **Texten som runor:** Rundatas translitterering delas i runor i läsordning. Bokstäver är runor; en bokstav inom
  parentes är en osäker läsning; `-` är en förlorad runa och kan inte placeras; `[…]` (känt bara ur äldre uppteckningar,
  inte på stenen), `...`, avsnittsmärken (§A) och skiljetecken räknas inte.
* **Märkningen:** forskaren klickar mitt på varje runa på skanningens djupbild i läsordning; klick nummer k hör till
  textens runa nummer k. Runor som inte syns hoppas över. Klicken sparas i `data/runbibliotek/<serie>/<fil>.json`
  (koordinater i den visade bilden, 1,2 mm per pixel), med rutans storlek (som standard de ritade slingornas höjd,
  annars 50 mm) och status (utkast eller granskad). En placerad ruta kan flyttas och få egen bredd och höjd (längs och
  tvärs slingan, `w` och `h`); utsnittet följer då rutan.
* **Utsnitten:** varje runa klipps ur djupbilden i full upplösning (0,6 mm), med djupet normaliserat inom rutan (5:e–97:e
  percentilen, mörkt = djupt), och vrids upprätt efter läsriktningen där den står: den ritade slingans riktning vid
  runan (närmaste segment av närmaste slinga, inom slingans höjd; slingorna är ritade i läsriktning), så att klickens
  ordning inte spelar roll; utan slinga riktningen från runan före till runan efter, när de står inom tre rutor (annars
  vänster till höger). Runornas toppar ligger till vänster om
  läsriktningen. Längs läsriktningen smalnas utsnittet av till 0,6 av rutan (runor är högre än breda, och en kvadrat
  med slingans höjd når in i grannrunorna). Utsnittet får samma formbeskrivning som runutsnitten i appen (avsnitt 12).
* **Ristaren:** de ristare Rundata anger som signerade eller attribuerade och inte osäkra. Rundatas attribueringar
  bygger delvis på runformer, så när biblioteket prövas som stöd för attribuering är de **signerade** stenarna facit;
  annars blir provet cirkulärt.
* **Användning:** biblioteket visas per ristare och runa, och *Jämför med ristare* för ett runutsnitt (avsnitt 12) tar
  med bibliotekets runor av samma bokstav. Biblioteket bygger på djupbilder; ett utsnitt ur ristningskartan från
  3D-analysen jämförs därför bäst med det, ett foto ger andra kanter.
* **Inte prövat än:** att formlikheten pekar ut rätt ristare oftare än slumpen. Det prövas med en låst analysplan på
  signerade stenar när biblioteket har runor från flera ristare.

## 13. Syntes och attribuering

Källkod: `src/synthesis.py`, `api/routers/synthesis.py`. Kandidaterna räknas fram deterministiskt:

| Källa | Vikt |
|---|---|
| Rundata: signerad (S) | 4 (2 om osäker) |
| Rundata: attribuerad (A) | 2 (1 om osäker) |
| Rundata: parsten/liknar (P/L) | 1 |
| Ortografi plats 1 / 2–3 | 2 / 1 × tillförlitlighet |
| Huggteknik plats 1 / 2–3 | 2 / 1 × tillförlitlighet |

* **Ortografins tillförlitlighet** = modellens precision för den föreslagna ristaren (korsvaliderad,
  Laplace-utjämnad: (rätt + 1)/(förslag + 2)) × 0,5 om stenen ligger utanför ristarens kända landskap ×
  textlängd (1 vid ≥ 12 läsbara ord, 0,7 vid 8–11). Texter under 8 ord vägs inte in.
* **Huggteknikens tillförlitlighet** = korsvaliderad träffsäkerhet över den strängare av två nollnivåer,
  (träff − nivå)/(1 − nivå): slumpen (1/antal ristare) och *materialgissaren* – lämna-en-ute, den vanligaste
  ristaren bland de övriga referensstenarna i samma bergartsfamilj (`src/geology.FAMILIES` på Rundatas
  materialuppgift; `src/stats.material_baseline`). Ristare och bergart hänger ihop, så träffsäkerhet som en
  bergartsgissning också når säger inget om handen. Är metoden inte bättre än nivån vägs den inte in.
  Jämförelsen görs med den valda analysen (runor som standard), mot stenar med samma spårtyp och säker
  ristare; stenen själv ingår aldrig i referensen. Prövat 2026-10-20 på Kitzler Åhfeldts 36 skanningar
  (groove-5, `utdata/huggspar/material_kontroll.py`): med Rak-planens ristarlista (12 stenar, 5 ristare)
  58 % rätt mot 20 % slump men 50 % för materialgissaren; slumpade ristarnamn inom bergart når 34 %
  (p 0,10, 2 000 dragningar); bara granit/gnejs (10 stenar, 4 ristare) 50 % mot 40 %; med appens regel
  (exakt en säker ristare: 8 stenar, 3 ristare) 38 % mot 50 %. Tillförlitligheten blir 0,17 i stället för
  0,48 med slumpen som enda nivå, och 0 med appens eget urval. Den delade mätkorpusen var vid provet tom,
  så ingen syntes hade vägt in huggteknik.

Styrka: **stark** = summa ≥ 4 eller ≥ 3 från tre källor; **måttlig** = ≥ 2,5 eller ≥ 1,5 från två källor;
annars **svag**. Inga procentsatser anges.

De tre främsta kandidaterna prövas dessutom mot:

* **litteraturen** – stämmer, nytt (Rundata saknar ristare) eller motsäger,
* **geografi** – avstånd till ristarens närmaste säkra sten och ristarens kända landskap,
* **stilgrupper** – stilgrupperna på ristarens säkra stenar och den datering de motsvarar enligt Gräslund;
  avviker stenens stilgrupp flaggas det,
* **sten mot sten** – permutationstest av alla mått samtidigt mot var och en av kandidatens uppmätta
  stenar (upp till fem, 1 000 permutationer).

Motsägelser mellan källorna (t.ex. Rundata mot ortografi, ortografi mot huggteknik, geografi eller
stilgrupp som inte passar) och belägg som saknas redovisas uttryckligen. Utfallet mot litteraturen räknar
bara en oberoende källa som stöd när kandidaten kommer först där. AI-modellen (Claude som standard, Gemini som alternativ) får beläggen som
underlag och skriver bara löptext; utan AI ersätts texterna av framräknade formuleringar. Syntesen kan
sparas i projektet och blir då avsnittet "Attribuering" i stenrapporten.

**Verktygsklassning** (pik-/bredmejsel, tröskel 85°, +5° vid hög vittring, +2° vid måttlig vittring, +2° för
sandsten/kalksten) är en tumregel som inte är kalibrerad mot referensmaterial och redovisas som sådan.

Ytterligare kontroller för de tre främsta kandidaterna (redovisas, men vägs inte in i poängen):

* **bergart** – stenens material jämfört med bergarterna på ristarens säkra stenar (avsnitt 11),
* **språkdrag** – fonetisk stil och språkbruk jämfört med ristarens inskrifter (avsnitt 9),
* **inskriftstyp** – stenens kategorier jämfört med ristarens; frånvaro flaggas bara när den är osannolik
  (avsnitt 10),
* **berggrund på platsen** (SGU) för stenen som helhet (avsnitt 11).

Har projektet en egen läsning (sparad i ett äldre projekt, eller en läsning som skickas till syntesen och prövas mot
Rundata utan AI, avsnitt 8) används den som ortografiskt belägg när Rundata saknar användbar text, med 30 % lägre
tillförlitlighet, och läsningens överensstämmelse med Rundata redovisas.

## 14. Forskningsluckor

Källkod: `src/research_gaps.py`. Underlag: Rundatas svenska vikingatida runstenar (2 321).

* **Täckning** per landskap: andel med ristare, säker stilgrupp, datering, osäker tolkning, försvunna stenar
  och stenar i mätkorpusen. Ristaruppgifterna för Sö, U, Vs och Gs bygger främst på Axelson (1993); i andra
  landskap kan attribueringar finnas i litteraturen utan att stå i Rundata.
* **Ortografiska hypoteser:** stenar utan ristare i Rundata vars stavning liknar en ristares profil
  (cosinus ≥ 0,6, marginal ≥ 0,05 till nästa, minst åtta läsbara ord). Förslagen rangordnas efter den
  ristarens korsvaliderade träffsäkerhet × likhet, och nedvärderas om stenen ligger utanför ristarens
  kända landskap. Det är förslag att pröva, inte attribueringar.
* **Att ompröva:** attribuerade stenar där ortografin pekar på en annan ristare.
* **Mätprioriteringar:** ristare med många inskrifter men få uppmätta stenar (mål: fem per ristare), så att
  attribueringen mot mätkorpusen får ett underlag.
* **Klickbara siffror:** varje tal i landskapstabellen och nyckeltalen leder till inskrifterna bakom det
  (sökfilter med samma definitioner som översikten, `GET /api/rundata/search?gap=…&province=…`).
* Ortografiska hypoteser visas med likhet, p-värde (avsnitt 7), precision, bergart och språkdrag.
* **Luckor i texten** (från 2026-10-20, `GET /api/research/gaps/textmodel`, `scripts/textmodel_candidates.py` →
  `data/textmodel_candidates.json`): sannolikhetsmodellens (8.1) inventering av luckorna – de som Rundata lämnat
  oåterställda och där modellen fyller i ett känt ord med minst 50 % kalibrerad sannolikhet (bandet ≥ 80 % räknas
  för sig) – med stenens signum, Rundatas föremål, det huggna, ifyllnaden, ordet, kalibrerad och rå sannolikhet,
  näst bästa ord, modellens läsning och ett svenskt översättningsutkast. Runstenar visas som standard och andra
  föremål på begäran, med egna tal. Fliken visar modellversion, beräkningsdatum och Rundata-utgåva. Raderna är
  underlag att granska mot foto, skanning och utgåvornas kommentarer (panelen "Vad skannern ser"), inte fynd.
  * **Kalibreringen (rättad 2026-10-23).** Inventeringen ger modellens råa sannolikhet för ordet. Fram till
    2026-10-23 visade listan den råa siffran under rubriken kalibrerad, med gränsen 80 %; den är ofta mycket högre än
    den kalibrerade för namn och ovanliga ord (U 466 *viseti* 81 % rå mot 46 % kalibrerad, U 441 *arnill* 88 % mot
    43 %). Nu kalibreras varje rad med listkalibreringen (`gap_list`, `src/textmodel.calibrate_words`) på
    samma sätt som den anpassades på inventeringens återställda luckor (`scripts/runlm_list_calibrate.py`): ordet med
    inventeringens alternativ, antalet förlorade runor, inte ett helt ord. Med textmodel-19 når 7 av 112 öppna
    luckor på runstenar minst 80 % och 17 minst 50 %. Påståendet i artikeln *Runorna som fattas* (ingen av de 70
    öppna luckor som panelen fyller på runstenar når 95 % kalibrerat) gäller fortfarande: listan och panelen räknar
    luckorna olika (inventeringen fyller också sammanslagna luckor på fler än fyra runor och delar orden som Rundata),
    men ingen öppen lucka på en runsten når 95 % i någon av dem utom U 765 *hans* i listan (97 %), som panelen, med
    hela stenens övriga luckor ifyllda samtidigt, bara ger 36 %.
  * **Översättningsutkastet** kommer ur `src/rungloss.swedish` med ordlistan för stenens femtedel (samma väg som
    stenanalysens utkast) i strikt läge: ett ord vars engelska glosa saknar svensk motsvarighet står kvar på fornspråk
    i stället för att den engelska glosan släpps igenom, och namn står som de lästs.

### 14b. Våra resultat mot befintlig forskning

Källkod: `src/findings.py`, `POST /api/research/findings`. Appens resultat ställs mot Rundata, som får
representera den publicerade forskningen:

| Metod | Stämmer | Nytt | Motsäger |
|---|---|---|---|
| Ortografi (lämna-en-ute) | rätt ristare först | stark hypotes för sten utan ristare | attribuerad (A) ristare inte bland de tre första |
| Huggteknik (mätkorpusen, runor) | närmaste ristare = Rundatas | sten utan ristare får en närmaste ristare | närmaste ristare ≠ Rundatas |
| Stilgrupp (AI, bild) | samma som Rundata | Rundata saknar säker stilgrupp | annan stilgrupp |
| Statistisk modell (R, avsnitt 1) | stöder en osäker attribuering | förstaval ≥ 0,5 för sten utan ristare | korsvaliderat förstaval ≠ Rundatas (A) |
| Seriation (R, avsnitt 1) | – | sten utan stilgrupp bland de 15 % tidigaste eller senaste i Uppland | – |

Varje fynd får en **uppskattning** = belägg × nyhet × relevans (var och en 0–1, skälen redovisas):

* **Belägg**: ortografi – modellens korsvaliderade precision för den föreslagna ristaren, halverad utanför
  ristarens kända landskap, lägre för korta texter och liten marginal; huggteknik – korsvaliderad
  träffsäkerhet och avståndet till nästa ristare; AI-stilgrupp – högst 0,35 eftersom den är okalibrerad.
* **Nyhet**: bekräftelser lågt (0,05–0,3; en oberoende metod som huggteknik väger mer än ortografi,
  eftersom attribueringar kan bygga på ortografin), nya attribueringar högt (0,85 i Axelsons område,
  0,55–0,6 utanför, där attribueringar kan finnas i litteraturen utan att stå i Rundata), avvikelser mot
  attribuerade stenar 0,7 men mot signerade 0,05 – där talar avvikelsen mot metoden, inte mot ristaren.
* **Relevans**: andelen stenar med ristare i landskapet (lägre andel = större behov), ristarens antal
  säkra inskrifter, och om stenen finns kvar att undersöka. En sten utanför tabellen över ristartäckning (stenar utanför
  Sverige) får mittvärdet och skälet "ristartäckningen räknas bara för svenska runstenar", inte 0 %. Fynd per sten
  utöver attribueringen (avsnitt 1q) räknar relevansen bara efter om stenen finns kvar.

Bedömningen ("Sannolikt ny och relevant kunskap", "Värd en omprövning", "Oberoende bekräftelse" m.fl.)
är en tumregel för att prioritera fortsatt arbete, inte en granskning av forskningsläget.

**Avstämning mot nyare källor** (`src/crosscheck.py`, `POST /api/r/crosscheck`). Appens Rundata är version 3.1
(2018). Nya och motsägande förslag (ortografi och statistisk modell) stäms av mot **Runor** (Riksantikvarieämbetet,
utgåva 2020 av samma databas, `runor.raa.se`) och **Wikidata** (skapare, P170, för objekt med Rundata-ID, P1261).
Runors hänvisningar av typen "Samma som gjort U 1015, 1017–1024" följs till de stenarna. Utfallet:
*finns redan* (förslaget står i den nyare källan – inte nytt, men en bekräftelse av metoden; nyheten sätts till
0,05), *nämns* (ristaren nämns i en anmärkning, t.ex. "Tidigare tolkad som signerad av Traen"), *annan ristare*,
*samma som* (samma namnlösa ristare som en annan sten) och *saknas*. Runors litteraturhänvisningar för stenen
visas så att de kan kontrolleras. Svaren cachas i `data/cache/crosscheck/`. Avstämningen ersätter inte en
genomgång av litteraturen: Runor 2020 har inte heller alla senare attribueringar.

**Mönster i korpusen** (avsnitt 1) visas överst i fliken: "bekräftar" när de stämmer med vad forskningen redan
utgår från, "mönster att pröva" när appen inte kan knyta dem till tid, geografi eller något den känner till ur
litteraturen (appen känner bara Rundata, Axelson 1993 och Gräslund 1998).

### 14c. Översikt per sten

Källkod: `src/stone_overview.py`, `GET /api/research/overview` och `GET /api/research/overview/{signum}`; sidan
**Stenöversikt**. För varje svensk vikingatida runsten samlas vad sex metoder säger om vem som ristade den:
R-modellens sannolikhet (avsnitt 1; korsvaliderad för stenar med säker ristare, förslag för stenar utan ristare
inom 25 km från en träningssten), ortografin (avsnitt 7; minst åtta ord, stenen själv utelämnad), området
(ristarens landskap och högst 60 km till en säker sten av ristaren), stilgruppen, språkdragen (mot landskapet med
p-värde; avsnitt 9) och bergarten (avsnitt 11). Stilgruppen jämförs sedan 2026-10-11 med ristarens *kärna*, de
stilgrupper som finns på minst 10 % av ristarens säkra stenar: den stämmer om stenens stilgrupp hör till kärnan.
En stilgrupp utanför kärnan men inom dess tidsram enligt Gräslund avgör inte (sedan 2026-10-11, efter granskningen av
U 735: Pr3 finns på 2 av Öpirs 101 stenar och räknades tidigare som att stilen stämde); utanför tidsramen talar den
emot och glappet anges i år (en enstaka RAK-sten bland 25 gör inte RAK till ristarens stil). Tidsramen som anges för
en ristare är kärnans. Ett glapp på minst 25 år gör förslaget kronologiskt problematiskt, t.ex. U 92 (RAK, omkring
980–1015) mot Öpir (Pr4–Pr5, 55 år senare) och Visäte (Pr3–Pr4, 35 år senare).

* **Stöd** för Rundatas ristare (0–1): viktat medelvärde av de metoder som kan uttala sig – modellen med sin
  sannolikhet för ristaren (vikt 2), ortografin med 1 om ristaren kommer först, 0,6 bland de tre första och annars
  0 (vikt 1,5), område, stilgrupp och språkdrag med 1 eller 0 (vikt 1) och bergarten med 1 eller 0 (vikt 0,5).
* **Alternativ** (0–1): för varje annan ristare som modellen eller ortografin pekar på räknas
  1 − (1 − modellens sannolikhet)(1 − ortografins tillförlitlighet om ristaren kommer först), multiplicerat med
  0,5 + 0,5 × andelen kontroller (område, stilgrupp, språkdrag, bergart) ristaren klarar; det starkaste redovisas.
  Ortografins förstaval räknas fullt bara när det leder tvåan med minst 0,05 i likhet, annars i proportion till
  marginalen (sedan 2026-10-11; U 735: Öpir 1 0,66 mot Balle 0,64 gav tidigare styrkan 0,70 och status *omstridd*).
* **Status** för stenar med ristare: *kan vara felbedömd* (alternativ ≥ 0,4 och stöd < 0,4), *omstridd*
  (alternativ ≥ 0,4), *stöds* (stöd ≥ 0,6), annars *svagt underlag* – också när färre än två metoder kan uttala
  sig. Signerade stenar redovisas för sig. För stenar utan ristare: *nytt förslag* (alternativ ≥ 0,5), *möjligt
  förslag* (≥ 0,3), annars *inget förslag*.

Har Rundata flera ristare för stenen (två som signerat tillsammans, eller en signatur och en attribuering; 113
runstenar) räknas stödet för var och en, den bäst stödda redovisas och de övriga räknas inte som alternativ.

Resultat (2026-10-21, korpusversion 5fdfd1e095bfb6fb, sedan R-modulen inte längre kortar listan över modellens förslag
till 400 stenar): 9 stenar kan vara felbedömda, 26 är omstridda, 331 stöds och 159 har svagt underlag; 86 av 1 550
stenar utan ristare får ett nytt och 292 ett möjligt förslag (2026-10-11, efter granskningarna av U 92, U 1026 och
U 735 men före rättelsen: 330, 160, 80 och 251). **Kontroll:** av 246 signerade stenar – där ristaren är känd – får 35
(14 %) ett alternativ ≥ 0,4 och tre hamnar som "kan vara felbedömd". Före U 735-granskningen var det 57 (23 %): ett
förstaval i ortografin med liten marginal och en ovanlig stilgrupp inom kärnans tidsram gav många falsklarm. Kategorin
*omstridd* larmar fortfarande ofta i onödan, medan *kan vara felbedömd* sällan gör det. Måtten är index för att
sortera och prioritera,
inte sannolikheter; bara modellens sannolikhet är kalibrerad. Metoderna är inte oberoende av Rundata: ortografi,
område och stil kan ha legat till grund för attribueringarna (avsnitt 18). Profilen för en sten visar varje metods
besked med förklaring, de tre starkaste alternativen med sina kontroller, och stenens höjd, textlängd och antal
namn som percentil bland landskapets runstenar, med syfte, statusord, stilgrupp, seriation och grupp.

**Blindprov av förslagen** (2026-10-21; analysplanen `utdata/forslag/analysplan_forslag.md`, låst innan provet räknades,
SHA-256 i `analysis_plan_forslag.sha256`; `utdata/forslag/blindprov.py`, oberoende kontroll `kontroll.py`). För var och
en av de 769 runstenarna med säker ristare doldes attribueringen – ristarnas landskap, stil-, bergarts- och
språkprofiler räknades utan stenen, och modellens sannolikheter är de korsvaliderade – och statusen räknades som för en
sten utan ristare. *Nytt förslag* gavs för 302 stenar och var Rundatas ristare i 248 (82 %, Wilson 77–86 %). Regeln
*närmaste ristare* (ristarna bakom den närmaste andra stenen med säker ristare, alla vid lika avstånd) hade rätt på samma
stenar i 133 (44 %); på 132 hade bara förslaget rätt och på 17 bara regeln (McNemar exakt p = 3 · 10⁻²³). Signerade
stenar: 72 av 100 mot 42. *Möjligt förslag*: 108 av 195 (55 %) mot 66 (34 %). Styrka ≥ 0,7: 142 av 165 (86 %). Per
landskap: Uppland 227 av 270 (84 %) mot 43 %, Södermanland 17 av 28 (61 %) mot 46 % (p = 0,39, alltså ingen säker
skillnad). 133 stenar har en ristare utanför de 28 som kan föreslås; 23 av dem fick ändå ett nytt förslag och räknas
som fel. Inget nytt förslag i provet vilade på ortografin ensam, så sådana förslag är inte prövade. Externt prov mot
Runor 2020: 19 runstenar har en ristare där men inte i Rundata 3.1, åtta av dem en ristare som kan föreslås; inget fick
nytt förslag, och ett av tre möjliga förslag stämde. Resultat och avvikelser från planen: `utdata/forslag/resultat.md`.

*Landskapet runt stenen* (från 2026-10-12): stenprofilen visar närmaste teofora och sakrala ortnamn, centralortsnamn,
medeltida kyrka och fornlämning av varje slag, med namn, avstånd och länk till Kulturmiljöregistret eller Wikidata, och
om stenen är flyttad enligt Rundatas placering eller plats (`GET /api/research/landscape/{signum}`).

### 14d. Tolkning av fynden

Källkod: `src/interpretation.py`, `POST /api/research/interpret`. När man klickar på ett fynd i "Våra resultat mot
forskningen" visas ett resonemang i fem steg: vad fyndet säger; hur starkt belägget är (för ortografin likhet,
marginal, antal ord, p-värde och p-värde justerat för att den bästa av alla ristare valts, och metodens precision
för ristaren; för modellen sannolikheten och träffsäkerheten vid den nivån); vad de andra metoderna säger om samma
ristare (område, stilgrupp, språkdrag, bergart och – om fyndet kommer från en annan metod – modellen och ortografin,
samt stödet för Rundatas ristare i Stenöversikt); vad nyare källor säger (Runor 2020, Wikidata); och en slutsats med
vad som skulle kunna avgöra frågan (3D-mätning, litteratur, nyläsning, stilbedömning).

Slutsatsen visas redan i fyndlistan (kolumnen Tolkning, med filter per nivå); servern räknar den för alla fynd med samma regler och sparar den på disk tills data eller koden ändras.

Slutsatsen har sex nivåer: *redan känt* (förslaget finns i Runor 2020 eller Wikidata), *metodfel* (fyndet motsäger
en signerad sten), *bekräftelse* (stämmer med Rundata), *starkt* (belägg ≥ 0,5, minst två oberoende belägg för och inget
emot, och för ortografin justerat p < 0,05; före 2026-10-11 tre belägg), *måttligt* (belägg ≥ 0,35 och minst lika många belägg för som emot) och
*svagt* (övrigt, och när ett fynd som motsäger Rundata står mot ett stöd ≥ 0,6 för Rundatas ristare). Sedan
2026-10-11 blir slutsatsen också *svagt* när stilgruppen talar starkt emot (glapp på minst 25 år till ristarens
kärna), oavsett hur lik stavningen är. Ortografins belägg sänks när likheten inte håller efter justeringen för
urvalet (×0,75 vid justerat p 0,05–0,2, ×0,5 vid högre), och slutsatsen säger då uttryckligen att stavningen ensam inte
räcker för att attribuera stenen – ett negativt resultat som också kan pröva äldre attribueringar gjorda på samma
grund. När den föreslagna ristaren står för minst 10 % av landskapets attribuerade stenar påpekas att produktiva
ristare drar till sig förslag, och att träffsäkerheten för deras förslag mäter metoden i allmänhet snarare än stenen.

Nivåerna gäller ristarförslag. Fynd om en sten utan ristarförslag (luckor i texten, Runor 2020, släktlänkar och egna
fynd, avsnitt 1q) får ett eget kort resonemang i tre steg: vad fyndet säger, var uppgiften kommer ifrån och vad som
skulle kunna avgöra frågan. Deras nivå är *ej tillämplig*. De får ingen nivå i fyndlistan och sorteras inte efter nivå,
och regeln om metodfel vid en signerad sten gäller aldrig dem.

**Efter granskningen av U 1026** (2026-10-11). Attribueringsmodellen använder själv plats, stil och språkdrag, så när
den föreslår en ristare räknas område, stilgrupp och språkdrag inte som oberoende stöd; de visas, och de kan tala
emot. Modellens förslag bedöms *starkt* bara när träffsäkerheten vid den sannolikheten är väl underbyggd (nedre
gränsen i ett 95 % konfidensintervall enligt Wilson minst 80 %; t.ex. 20 av 20 stenar ger 84–100 %) och inget belägg
talar emot. Sannolikheten gäller under förutsättning att ristaren är en av modellens ristare.

**Signifikans för modellens förslag** (från 2026-10-11). Som för ortografin prövas förslaget med en max-statistik:
nollfördelningen är, för varje sten med känd ristare, den högsta sannolikhet som modellen – utan att ha sett stenen
(korsvalidering) – gav en *felaktig* ristare. p är andelen sådana stenar där en felaktig ristare fick minst lika hög
sannolikhet som förslaget, (1 + antal) / (1 + antal stenar), och stenen själv ingår aldrig i sin egen nollfördelning.
p-värdena justeras med Benjamini–Hochberg över alla modellens förslag (q), och *starkt* kräver också q under 0,05.
Testet gäller under samma förutsättning som sannolikheten (att ristaren är en av modellens) och säger inget om
stenar av ristare utanför modellen; att stenarna utan ristare kan skilja sig från träningsstenarna är en kvarstående
begränsning. I dag (497 stenar med känd ristare) är alla modellens förslag över 0,5 säkerställda: en felaktig ristare
får sällan så hög sannolikhet.

När Rundata anger att en
namnlös ristare har gjort stenen och andra stenar ("Samma som gjort U 1027"; 122 inskrifter, läses ur ristarfältet)
blir slutsatsen högst *måttligt* – en prövbar hypotes om vem den namnlösa ristaren var – och modellens förslag för de
kopplade stenarna visas (samma förslag stöder hypotesen, ett annat talar emot). Stenens *typikalitet* visas också:
hur stor del av ristarens egna stenar som liknar ristarens stavningsprofil mindre än stenen gör (under 10 % räknas som
emot – förslaget kan vara det minst dåliga valet bland modellens ristare). Bergarten räknas som neutral när
bergartsfamiljen är minst nästan lika vanlig på landskapets runstenar som hos ristaren (kvot under 1,5; granit finns
på 74 % av Upplands runstenar). Språkdragens "X av Y" räknar bara oberoende drag, och drag som avviker från ristarens
vanligaste form redovisas med både ristarens och landskapets andel – för U 1026 är monoftongen, avsaknaden av stungen i
och *at* inte ovanligare hos Öpir än i Uppland, medan apostrofen som skiljetecken är nästan fem gånger vanligare hos
honom. Länken "öppna i 3D-analysen" startar en mätning och betyder inte att stenen är mätt; tolkningen säger uttryckligen
när ingen huggteknik är mätt. Att Runor 2020
anger en annan ristare räknas som ett belägg emot. Fördelning 2026-10-11 före granskningen av U 92 (429 fynd): nya
förslag 32 starka, 138 måttliga, 35 svaga och 4 redan kända; motsägelser 5 måttliga, 15 svaga och 6 metodfel; 194
bekräftelser. Efter granskningen, med de nya språkdragen och fynden från okända ristare (516 fynd): nya förslag 21
starka (alla från attribueringsmodellen), 217 måttliga (varav 96 stenar i grupper av okända ristare och 81 från
seriationen), 54 svaga (alla ortografiska förslag, vars likhet inte håller efter justering) och 2 redan kända;
motsägelser 6 måttliga, 13 svaga och 5 metodfel; 198 bekräftelser. Reglerna är
fasta och kan granskas; tolkningen är en läshjälp, inte en runologisk bedömning.

### 14e. Mönsterkartan

Kartan (`/karta`, `GET /api/research/pattern-map`, `src/pattern_map.py`) visar var ett mönster finns som **andel**
av stenarna per område, inte som antal, så att Upplands täthet av runstenar inte döljer mönstret. Området är en
sexkant (10, 20 eller 40 km mellan motstående sidor) i en enkel kilometerprojektion kring 62° N; sexkanter med färre
än 5 stenar där mönstret kan avgöras visas grå. Färgerna är en sekventiell blå skala i fem steg (0–20 % … 80–100 %).
Kartan kan delas i före och efter omkring 1050 (stilgruppens mittår; RAK–Pr2 mot Pr3–Pr5), och bara stenar med säker
stilgrupp ingår då. Samma andelar per landskap finns som tabell under kartan.

Varje mönster är 1, 0 eller okänt för varje sten. Språkdragen kommer från avsnitt 9 (okänt när ordet saknas eller
texten är oläslig); innehållet från inskriftstyperna (avsnitt 10); korset från Rundatas ornamentik. *Kristna markörer*
är kors eller kristen bön eller formel. *Hedniska eller rituella markörer* är Torsåkallan (Þórr med dubbelt r i
normaliseringen, så att namn på Þór- och avbrutna Þor… inte räknas, eller Thor i Rundatas översättning), vígi-formler,
förbannelser (ræti, argi, seiðr), alu och Tormotiv i Rundatas anmärkningar (torshammare, Tors fiskafänge).
Futharkrader räknas inte, eftersom de också förekommer i kristna sammanhang, och inte heller Sigurdsbilder, eftersom
hjältesagan också används i kristen konst. *Utan religiösa markörer* är läsbara stenar med varken eller; en sten utan
kristna markörer är inte därmed hednisk. Bland 2 318 vikingatida runstenar med koordinater har 1 103 kristna markörer,
6 hedniska eller rituella (Ög 136, Sö 111, Sö 140, Sö 352, Vg 150, U 1161; Sö 86 med torshammare är ett jordfast block
och räknas inte som runsten, och Sö 102 läser salu, själen, inte alu) och 1 210 inga. De uttryckligt hedniska stenarna är alltså mycket få; den
stora gruppen är stenarna utan religiösa markörer, som kan vara hedniska, kristna utan att säga det eller
religiöst neutrala minnesmärken.

*Arbetsgången på kartan* (från 2026-10-12). Mönsterkartan är ordnad efter frågan: *Upptäck* visar de starkaste fynden
– kombinationer av mönster och platser och kluster som håller i båda halvorna – som kort som ställer in kartan med ett
klick; sidopanelen har tre steg (välj mönster, jämför med tid, platser eller kluster, och svaret i ord för exakt det
kartan visar), och platslagret för den valda jämförelsen visas av sig självt. Genomsökningens rutnät och andelarna per
landskap ligger hopfällda under kartan.

*Platser* (`src/places.py`, från 2026-10-12). Över sexkanterna kan platser visas: teofora och sakrala ortnamn,
centralortsnamn, medeltida kyrkor och Kulturmiljöregistrets gravfält, högar, färdvägar, broar och fornborgar – samma
data som korpusanalysens lämnings- och kultnamnsprov (avsnitt 1; `GET /api/research/places`). Varje sten har avståndet
till närmaste plats av varje slag (kd-träd i SWEREF 99 TM). *Nära en plats* jämför andelen stenar med det valda mönstret
inom 1, 2, 3 eller 5 km från en sorts plats med övriga stenar (`GET /api/research/place-test`): andelarna, oddskvoten
utan justering (Fishers exakta test) och med landskapet konstant (Mantel–Haenszel, CMH-test). Flyttade stenar räknas
inte, och kartan kan begränsas till stenarna nära platserna. Provet är utforskande: tiden hålls inte konstant, mönstret
prövas inte i två halvor och den som prövar många kombinationer av mönster, platser och radier hittar några skillnader
av en slump. Det fullständiga provet för kultnamnen redovisas i avsnitt 1.

### 14f. Danska, norska och svenska runstenar jämförda

Fliken *Jämför länder* på kartan (`GET /api/research/nordic`, `src/nordic.py`, från 2026-10-14) ställer Rundatas
vikingatida runstenar (period V, föremål runsten) i tre serier mot varandra: den danska (DR, 239 stenar, med Skåne,
Blekinge, Bornholm och Slesvig, som hörde till det danska riket), den svenska (2 321) och den norska (N, 66). Stenarna
grupperas efter serie eller efter riken och trakter omkring 1025, som i gränslagret (14g): Jylland och Slesvig, de danska
öarna, Skåne och Blekinge, Bornholm, Svitjod (Uppland, Södermanland, Västmanland, Närke), Dalarna och Norrland,
Götaland, Småland med Öland och Dalsland, Gotland, Jämtland, de omstridda Bohuslän och Värmland, och Norge.

*Jämförbara mönster.* Rundatas normalisering är olika i serierna – runsvensk för svenska stenar, runodansk för danska
(Guþ hialpi, kumbl þøsi) och fornvästnordisk för norska (reist rúnar) – så mönsterkartans språkdrag, som söker i
normaliseringen, missar danska och norska former. Jämförelsens mönster läser i stället den engelska översättningen och
translitterationen, som är gjorda på samma sätt i alla tre: kristen text (Gud, Kristus, själen, en helig), kristen bön,
hedniska eller rituella markörer (som i 14e), titlarna þegn och drængr, ordet kumbl, bro- och vägbygge, utlandsfärd, arv,
ristarsignatur (den som ristade, högg, målade eller märkte, inte beställaren som ”lät hugga” stenen), stungna runor
och monoftong i ordet sten (stin mot stain, bara där ordet finns). Kors ingår inte:
Rundata anger korsets form för 41 % av de svenska stenarna men för 12 % av de danska och 3 % av de norska, också där
korset är välkänt (Kristusbilden på Jellingstenen DR 42, Dynnastenen N 68), så en skillnad i kors vore en skillnad i
beskrivningen.

*Platser för danska stenar.* Rundata saknar koordinater för 66 av de danska stenarna, nästan alla i Nørrejylland och
Sydslesvig och många numera på museum. `scripts/fetch_dk_remains.py` ger dem fyndplatsen på sockennivå: sockenkyrkan
eller orten ur OpenStreetMap (Nominatim, ett anrop i sekunden), och om en runsten i Slots- og Kulturstyrelsens register
Fund og Fortidsminder ligger inom 3 km och inte redan hör till en sten med koordinater, den runstenens punkt. Registrets
egna poster nämner inte DR-numret, så kopplingen görs på plats. Utfallet (2026-10-14): 24 stenar fick registrets punkt,
35 sockenkyrkan och 6 orten; DR 351 med okänd fyndort fick ingen. Platserna används för kartan, inte för proven, som inte
bygger på läget. Samma nedladdning ger alla 326 550 registrerade anlägg med typ och datering (`data/dk/fortidsminder.csv`)
för en dansk motsvarighet till lämningsprovet i avsnitt 1c; registreringen skiljer sig från Kulturmiljöregistrets, så
antalen kan inte jämföras rakt av mellan länderna.

*Prov.* Andelen per grupp redovisas med ett 95 % Wilsonintervall. Skillnaden mellan grupperna prövas med χ² (grupper med
minst 10 stenar). Länderna jämförs parvis med oddskvot (Fishers exakta test) och med tiden konstant: Mantel–Haenszel
över tre perioder (före 1000, 1000–1050, 1050 och senare). Dateringarna är Rundatas och bygger på olika system:
stilgruppens mittår för svenska stenar (Gräslund), den danska indelningen för danska (Helnæs-Gørlev ca 825, för-Jelling
925, Jelling 970, efter-Jelling 1015, kristen efter-Jelling 1025) och annars årtal eller sekel; 220 danska, 1 066
svenska och bara 17 norska stenar är daterade. Provet är utforskande på samma sätt som platsprovet i 14e.

*Dansk prägel.* En logistisk regression (ridge, λ = 1, klassvikter) skiljer danska från svenska stenar på 13 drag i
minnesformelns ordval och i stavningen: satte, reste, lät resa, gjorde, kumbl, þegn och drængr, berömmande ord, sten med
monoftong eller diftong, æft med eller utan -iR, ristarsignatur och stungna runor. Tro (bön, själen, bro) och resor
ingår inte, så att måttet inte bara skiljer kristna eller sena stenar från de andra (från 2026-10-14; den första versionen
hade alla 17 drag). Modellen tränas bara på stenar från 970–1050 (147 danska och 576 svenska), så att den lär sig
skillnaden mellan danskt och svenskt bruk vid samma tid och inte skillnaden mellan tidiga och sena stenar; stenarna i
träningen får sin prognos ur femfaldig korsvalidering (fördelade efter signum). Den skiljer en dansk från en svensk sten
rätt i 82 av 100 par (AUC 0,82). Bara stenar med minst två av de 17 dragen får en prägel. *Kontroll:* modellen har inte
sett Rundatas anmärkningar, men de 8 danska stenar som anmärkningarna kallar svenskgjorda eller svenskpåverkade (DR 6,
DR 344, DR 229, DR 345, DR 365, DR 212, DR 144, DR 2) får dansk prägel 0,37 i genomsnitt mot 0,61 för de andra danska
stenarna (Mann–Whitney, ensidigt, p = 0,016); DR 6 och DR 344 hamnar på plats 1 och 2 av 174.

*Prövat i R.* Artikeln ”Västgötarna satte stenen som danskarna” (utkast 2026-10-14) räknade om modellen i R (mgcv,
ridge med straffet valt med REML) med samma resultat (AUC 0,82, kontrollen p = 0,015) och prövade fynden i båda
halvorna, där stenarna delas socken för socken och modellen tränas om i varje halva. Att den danska prägeln hos svear
och götar bleknar med stilgruppen (landskapet konstant) och att Västergötland är danskast (stilgruppen konstant) håller i
båda halvorna; att Skånes stenar är mindre danska än Jyllands vid samma tid, och att prägeln minskar med avståndet från
gränsen när tiden hålls konstant, håller bara i den ena. Med tro och resor inräknade blir Västergötland tydligare danskt,
men blekningen med tiden svag (p = 0,10): den ligger i formeln och stavningen.

*Gränsbältet* (artikeln, 2026-10-14). Runstenarna räknas i band om avståndet från riksgränsen omkring 1025 (gränslagret,
14g: Skåne, Halland och Blekinge mot Småland och Västergötland) och jämförs med gravfälten i Kulturmiljöregistret, som
täcker båda sidor om den medeltida gränsen. På danska sidan finns inom 50 km 446 gravfält men 3 runstenar (0,7 per 100
gravfält, ingen från omkring 970–1025), mot 31 per 100 längre in (Poissontest, p < 10⁻²¹; i båda halvorna p < 10⁻⁴);
på svenska sidan 11 per 100 inom 50 km, och vid gränsen mellan götar och svear 9–13 per 100. Stavningen (sten, efter)
och verbet (satte, reste, lät resa) ändras inte säkert vid riksgränsen; stavningen av sten ändras främst med tiden.

Resultaten redovisas per trakt, per stilgrupp och per ristare (Rundatas säkra signerade och attribuerade ristare med
minst tre stenar), med de tidigaste stenarna med dansk prägel hos svear och götar, de danska stenar som liknar svenska
mest, Rundatas anmärkningar om ett annat lands ristare eller språk och de texter som nämner ett annat nordiskt land.
Hög dansk prägel betyder att stenen är formulerad och stavad som en dansk sten, inte att ristaren var dansk; för stenar
äldre än 970, utanför modellens tid, kan likheten spegla ett äldre språk som danskan och de tidiga svenska stenarna
delar. Rundata har nästan inga ristarnamn för danska stenar (fem ristare) och inga norska, så ristare över gränserna
kan inte sökas på namn. De norska stenarna är för få för en egen modell.

### 14g. Rikenas gränser på kartan

Alla tre kartvyerna kan visa rikenas och folkens ungefärliga gränser omkring 890, 1025 och 1200
(`web/src/lib/realms.json`, från 2026-10-14). Varje område är en sammanslagning av dagens landskap och regioner och är
märkt som kärnområde, löst knutet eller osäkert, eller omstritt; varje område har en förklaring med källa. Omkring 890
bygger kartan på Ottars och Wulfstans berättelser i den fornengelska Orosius (Blekinge, Möre, Öland och Gotland hör
till svearna, Skåne och de danska öarna till Danmark, Bornholm har en egen kung), omkring 1025 på Adam av Bremen,
runstenarna själva (Jellingstenen, Frösöstenen) och senare medeltida gränser, och omkring 1200 på stiften och
landskapslagarna. Före medeltiden var gränserna zoner snarare än linjer, och inlandet är i regel okänt; samernas land i
norr och i fjällen ritas inte. Geometrin byggs av `scripts/build_realms.R` till `web/public/geo/riken.geojson`: de
svenska landskapen ur OpenStreetMap (de flesta som historiska gränser, resten ur län och kommuner), Danmark, Norge och
Slesvig ur Natural Earth, Slesvigs sydgräns ungefärligt vid Ejdern och Möre som en ruta i sydöstra Småland; allt
klipps mot Natural Earths land och förenklas till omkring 300 m.

### 14h. Tre nya källor prövade: runformer, fornsvenskan och Blekingestenarna (2026-10-21)

Analysplan `utdata/kallor/analysplan_kallor.md`, låst innan måtten räknades (SHA-256 i `analysis_plan_kallor.sha256`);
resultat och avvikelser i `utdata/kallor/resultat.md`.

* **Skåne: runformer mot stavning** (`skane_runformer.py`). RuneS-DB:s graftyper (runformen vid varje position) för
  de 43 runstenar i Skåne som har graftyper, DR-signum i Rundata och plats i stavningsmodellens index (2 837
  positioner, 21 tecken, 63 graftyper). Runformsavstånd = medelvärdet över gemensamma varierande tecken (minst två
  graftyper med minst fem positioner var) av totalvariationsavståndet mellan stenarnas graftypsandelar; stavningsavstånd
  = 1 − cosinus mellan modellens vektorer; Mantel (Spearman, 10 000 permutationer). Resultat: r = 0,42, p = 0,0001,
  oberoende av det geografiska avståndet (partiell Mantel r = 0,42). Utan skiljetecknet som varierande tecken r = 0,15,
  p = 0,017: skiljetecknets form bär större delen av sambandet, och det registreras av båda källorna.
* **Fornsvenskan** (`fornsvenska.py`). Runstenarnas 1 106 lemman (textmodellens lemma, namn uteslutna) mot de fyra
  ordböckernas 39 351 uppslagsord med en fast regellista (ʀ→r, ð→þ, þ→th/dh, æi→e, au→ö, ø→ö, æ→ä/e, slut-r→-er …).
  Belagda: 36 % av lemmana och 79 % av förekomsterna (45 % och 90 % när ordböckernas böjda former räknas). Hapax 29 %
  mot 60 % för lemman med minst fem förekomster (z = 7,3, p = 2 · 10⁻¹³; 37 mot 76 % med böjda former). Andelarna är
  nedre gränser (reglerna missar böjningar som *haggva*–hugga); skillnaden mellan klasserna är det bärande resultatet.
* **Blekinge** (`blekinge_tolkningar.py`). RuneS-DB:s tolkningar av Gummarp (7), Stentoften (19), Istaby (7) och
  Björketorp (12), publicerade 1944–2004: täckning och läsningsenighet per rad, parvis likhet mellan de engelska
  översättningarna (0,21–0,72) och andelen tolkningar som nämner död, förstörelse respektive förutsägelse/skada.
  Planens hypotes (död och förstörelse i minst 80 % på Björketorp och Stentoften) föll: 9 av 12 (75 %) och 9 av 19
  (47 %); förutsägelsen 5 av 12. Inga egna läsningar; tolkningarna är data om oenighet.
* **K-samsök**: prövat, ingen fyndplats i indexet för SHM:s vikingatida föremål (avsnitt 17).

## 15. Rapporter

Två rapporttyper, båda manusutkast där tabeller och figurer räknas fram ur data och AI-text märks.

### 15a. Korpusrapport (flera stenar)

Källkod: `src/academic.py`, `POST /api/reports/academic`. Rapporten byggs för ett urval av korpusen (en
ristare, ett landskap, valda stenar eller hela korpusen):

* **Material, metod, tabeller och figurer räknas fram ur data**: medelvärden och spridning per mått, per
  sten och per ristare, figurer över V-vinkel och Ward-dendrogram, samt metodversioner och referenser.
* AI kan skriva **sammanfattning, inledning och diskussion**, men får bara en faktatext med de framräknade
  resultaten som underlag. Dessa avsnitt märks som AI-text. Utan AI-nyckel lämnas de för författaren att
  skriva.
* Export: Markdown, LaTeX (med figurfilerna) och Word (.docx). Rapporten är ett manusutkast som måste
  granskas innan den används.

### 15b. Stenrapport (en sten)

Källkod: `src/stone_report.py`, `POST /api/reports/stone`. Uppläggningen följer två traditioner:

* **Runologisk presentation** som i *Sveriges runinskrifter* och i stilmallen för *Futhark: International
  Journal of Runic Studies*: signum utskrivet i sin helhet och utan kursiv, translitterering i **fetstil**,
  normalisering (runsvenska och fornvästnordiska) i *kursiv*, översättning inom citattecken, ristare med S/A,
  stilgrupp (Gräslund), datering och hänvisning till stenens utgåva i SRI. Allt hämtas ur Rundata.
* **Arkeometrisk redovisning**: material och metod med 3D-dokumentationens paradata (skanner,
  upplösning, noggrannhet, vem som skannat, modellens kontrollsumma, licens), analysparametrar,
  kvalitetskontroll (godkända och underkända snitt med skäl), resultat, diskussion, källkritik, data och
  reproducerbarhet, samt en bilaga med varje tvärsnitts mått.

Figurerna räknas direkt ur 3D-modellen och snittens råprofiler (inget är retuscherat):

1. digitalt strykljus från fyra riktningar (20° över ytan),
2. djup under en rekonstruerad stenyta (morfologisk stängning, 20 mm; kantzonen utelämnad),
3. tvärsnittens positioner färgade efter V-vinkel, med bokstäver som hänvisar till profilfiguren,
4. spårdjup, spårbredd och ytråhet per tvärsnitt över ytan,
5. representativa tvärsnitt (från minsta till största vinkel) med anpassade spårväggar i lika skala,
6. alla tvärsnitt överlagrade med median och interkvartilområde,
7. måttens fördelningar, 8. samband mellan bredd, djup och vinkel,
9. runor mot ornamentik (permutationstest), 10. jämförelse med stenar med säker ristare i mätkorpusen,

och, om det finns, bilden och runformerna från fliken Bilder och runformer. Figurerna 1–4 kräver att skanningen finns i
analysmotorns minne (samma fil inläst i 3D-vyn); annars utelämnas de och rapporten säger det. Snittens
positioner och råprofiler sparas med varje analys (automatisk, ett klick per snitt och spårbana).

Stenrapporten får dessutom, när underlaget finns:

* **berggrunden på platsen** (SGU) i avsnittet om stenen,
* **Läsning av bilden** – en egen läsning (äldre projekt, eller skickad med rapporten) som inskrift
  (fetstil/kursiv), jämförelsen med Rundata, skillnaderna ord för ord och kontrollen av ordformer,
* **Attribuering** – den sparade syntesen: utfallet mot litteraturen, kandidattabellen, kontrollerna
  (geografi, stilgrupper, bergart, språkdrag, sten mot sten), motsägelser och saknade belägg.

### 15c. Fullständig stenanalys (arbetsgång)

Sidan **Stenanalys** och skriptet `scripts/full_stone_analysis.py` kör hela kedjan för en skanning och ett
signum, med samma beräkningar som de enskilda verktygen:

1. Uppladdning och **bilder ur skanningen** (avsnitt 2d). Den ristade sidan skattas som stenens tunnaste
   riktning; den andra sidan kan väljas.
2. **Automatisk spåranalys** med flera känsligheter (standard 3 och 5). Den första är huvudanalysen, de övriga
   en känslighetsanalys som redovisas med granskningsbilder.
3. **Syntes och attribuering** med berggrund (avsnitt 11 och 13); med inloggning även mot mätkorpusen.
4. **Forskningsläge och syfte** (`GET /api/research/stone/{signum}`): det Forskningsluckor vet om stenen
   (landskapets täckning, stenens luckor i Rundata, om den finns bland ortografiska hypoteser, omprövningar
   eller mätprioriteringar och hur appens resultat bedöms mot forskningen), inskriftens syfte (avsnitt 10) och,
   för de tre troligaste ristarna, hur ofta de ristade i stenens stilgrupp och inskriftstyp.
5. **Statistik i R** (avsnitt 1): startar korpusanalyserna om de saknas och ställer stenen mot dem –
   attribueringsmodellen, kandidaternas områden, gruppen i klustringen, formlerna, Upplands seriation och
   landskapet (höjdmodell, strand, sikt, vägar).
6. **Stenrapport** (15b), med avsnitten "Inskriftens syfte" och "Stenen i forskningsläget", R-avsnitten (metod 3.4,
   modellen i attribueringen, "Stenen i korpusen", "Stenen i landskapet"), en tabell över
   kandidaternas stilgrupper och inskriftstyper, bilaga A (alla tvärsnitt) och bilaga B: arbetsgångens steg och utfall,
   känslighetsanalysen, granskningsbilder, relief och de fel eller begränsningar som uppstod. (Stilbedömningen och
   den blinda läsningen togs bort 2026-10-20, avsnitt 8 och 12.)

AI används bara för löptext i syntes och rapport, som tillval; utan nyckel eller med valet avstängt räknas texterna
fram. Misslyckas AI-texten (ingen nyckel, slut på krediter, tidsgräns) fortsätter arbetsgången med framräknad text,
och felet redovisas i bilaga B. Resultatet kan sparas i ett projekt.

Från terminalen (analysmotorn måste köras):

```bash
.venv/bin/python -m scripts.full_stone_analysis "skanning.stl" --signum "Sö 113" --out utdata/So113 \
    --stone Gråsten --weathering Medel --author "Namn" --sensitivity 3,5 --orientations 0,180
```

### 15d. Språkmodeller

Källkod: `api/llm.py`. Alla AI-anrop går genom ett gemensamt lager. Standard är **Claude** (Anthropic,
`claude-opus-5-5` för analys och text, `claude-haiku-4-5` för enkla uppgifter); **Gemini** kan väljas under
Inställningar. Strukturerade svar (t.ex. stilbedömning och läsning) begärs med ett schema – för Claude som
strukturerat svar (JSON-schema i `output_config`, sedan 2026-10-11; tidigare verktygsanrop), så att svaret alltid är
giltig JSON. Valet av modell ändrar inget i det som räknas fram:
mätningar, statistik, jämförelser och valideringen av läsningar görs utan AI, och AI-text märks.

### 15e. Beslutsunderlag om attribuering

Källkod: `src/attribution_report.py`, `POST /api/reports/attribution`; knappen *Skapa beslutsunderlag* i
stenprofilen i Stenöversikt. För en sten och en prövad ristare samlas allt i ett dokument för dem som förvaltar
Samnordisk runtextdatabas (Uppsala universitet) eller Runor (Riksantikvarieämbetet). Dokumentet ska kunna läsas av en
runolog som inte känner appen och ligga till grund för ett beslut (sedan 2026-10-11; tidigare en kort sammanfattning).

* **Slutsats och rekommendation först**, efter tolkningens nivå (14d): *starkt* ger ett förslag, *måttligt* ett
  underlag för granskning (ingen ändring i dag, en prövbar hypotes), *svagt* ingen ändring. **En sten som är
  signerad av någon annan får aldrig ett förslag**: signaturen väger tyngre än alla statistiska jämförelser.
  Beläggen sammanfattas i en tabell (talar för, emot, neutral). När modellen ensam är stark men det oberoende stödet
  saknas sägs det uttryckligen.
* **Varje metod förklarad**: vad den jämför, vilka data den bygger på och hur talen ska läsas. Modellens sannolikhet
  förklaras med kalibreringen ur korsvalideringen: hur ofta en ristare med ungefär samma sannolikhet (±0,05) var den
  rätta, och hur ofta en felaktig ristare fick minst lika hög sannolikhet. Ortografin visas för de fem närmaste
  ristarna och den prövade och Rundatas, med likhet, p, justerat p (max-statistik) och typikalitet. Område, stilgrupp,
  språkdrag (drag för drag med andel hos ristaren, i landskapet och kvot) och bergart visas för både den prövade
  ristaren och Rundatas.
* **Material** (vilka inskrifter, ristare och stenar som jämförs), **andra kandidater**, **litteratur och nyare
  källor** (Runor 2020 och Wikidata, avstämt när dokumentet skapas), **vad som skulle avgöra frågan** (med de närmaste
  säkra och signerade stenarna av båda ristarna), **källkritik** (cirkularitet mot Axelson, sluten mängd ristare, det
  metoderna inte mäter), **ordlista**, metod och versioner, och en bilaga med ristarnas jämförda stenar.

**Bedömningen räknar inget två gånger** (rättat 2026-10-11). Den samlade styrkan bygger på modellen och
ortografin; de räknas därför inte en gång till som "andra belägg". När modellen bidrar räknas område och stilgrupp inte
som oberoende stöd (modellen använder dem), och språkdragen aldrig (de bygger på samma stavning som ortografin); alla
tre kan tala emot. *Starkt* kräver att både modellen (förstaval med minst 0,5) och ortografin (förstaval med justerat
p under 0,05) pekar på ristaren och att inget talar emot. Före rättelsen kunde modellen och ortografin ensamma ge
*starkt*; av 1 003 alternativ i Stenöversikt blev 51 starka, nu 4.

**Jämförelsen med Rundatas ristare** (sedan 2026-10-11, efter granskningen av U 735). När dokumentet prövar en annan
ristare än Rundatas räknas det som talar för Rundatas ristare framför den prövade: modellen har Rundatas ristare som
förstaval och ger den mer än den prövade; språkdragen passar Rundatas ristare signifikant bättre än landskapets övriga
stenar men inte den prövade; Rundatas ristare har en sten minst tre gånger närmare (och den prövade minst 10 km bort);
stenens stilgrupp hör till kärnan hos Rundatas ristare men inte hos den prövade. Ett drag som redan talar emot den
prövade räknas inte igen. Beläggen är inte oberoende av varandra (modellen använder läge, stil och språkdrag), vilket
sägs i texten. Runor 2020 räknas inte som belägg emot förslaget när den anger samma ristare som Rundata – Runor är en
senare utgåva av samma databas. Ortografins förstaval räknas som neutralt när det leder tvåan med mindre än 0,05 i
likhet och inte är signifikant. Den samlade styrkan kallas inte stark eller måttlig utan förbehåll när modellen inte
stöder förslaget eller stavningslikheten inte är signifikant.

**Dokumenttyp.** *Starkt* och *måttligt* ger ett dokument till runtextdatabasen. *Svagt* ger ett internt
arbetsunderlag som inte bör skickas som förslag; talar minst två belägg för Rundatas ristare heter det "Prövning av
{signum}: Rundatas attribuering till {ristare} stöds". Dokumentet anger varifrån hypotesen kommer (Stenöversiktens
alternativ från modellen och ortografin). Jämförelsestenarna är de närmaste stenarna där ristaren är ensam ristare och
som finns kvar, med minst en signerad; närmare stenar med flera ristare eller som är försvunna nämns med skäl.
Källkritiken tar bara med de kända bristerna som gäller dokumentet (platsläckage i korsvalideringen, många test,
Rundatas utgåva), inte huggspårsmåtten eller stenarnas mått, som inte används.

Ristarnamn som enligt forskningen är grupper får en not (t.ex. "Traen"). Dokumentet exporteras som Word och Markdown;
mottagare fylls i av avsändaren och e-post hämtas ur kontoinställningarna (förvalt kontots adress). Ingen AI-text.

### 15f. Engelsk version

Källkod: `web/src/i18n/` (webbläsaren), `src/i18n.py` (rapporterna). Appen skrivs på svenska, och svenskan är
originalet. Med språket engelska översätts det som visas på plats mot en ordlista (`web/src/i18n/en.json`) med
meningsmallar, och rapporterna (Word, Markdown, LaTeX) översätts med samma ordlista när de skapas.

* **Mallar.** Siffror, ristarnamn och orter (ur Rundata, `web/src/i18n/names.json`) byts mot platshållare före
  uppslaget och sätts tillbaka efteråt, siffror i engelsk form (0,43 → 0.43; 1 101 → 1,101). Språkdrag, deras
  värden och bergarterna (`terms.json`) översätts var för sig inne i meningarna, så att en mall räcker för alla
  kombinationer. Längre texter delas i meningar, och korta ledord före kolon ("För:", "Stenen:") i egna delar.
  Listor av stenar och ortsangivelser översätts ord för ord när de bara består av signum, siffror, namn och några
  fasta ord (signerad, sn, hd, och).
* **Det som inte översätts:** translittereringar, normaliseringar, källtext ur Kulturmiljöregistret, ortnamn och
  Runes svar (Rune svarar direkt på engelska). En mening som saknas i ordlistan visas på svenska.
* **Samma regler överallt:** webbläsaren och rapporterna bygger mallarna på exakt samma sätt; `tests/test_i18n.py`
  jämför dem.
* **Översättningarna** är gjorda för hand (av Claude, granskade stickprovsvis) och inte maskinöversatta vid
  visningen. När svenska texter ändras samlar `web/scripts/i18n_crawl.mjs` in det som saknas, och
  `web/scripts/i18n.mjs merge` för in nya översättningar (se `scripts/README.md`).

### 15g. Artiklarna på vitkirunor.se

Källkod: `src/blog_topics.py` (ämnen och utkast), `src/blog_maps.py` och `r/blogfig.R` (figurer), `src/blog_figures.py`,
`src/commons.py` (foton), `src/site_export.py` (publicering), `api/routers/blog.py`. Artiklarna på vitkirunor.se är
populärvetenskapliga texter om mönster ur korpusanalysen (avsnitt 1), skrivna för läsare utan statistisk utbildning.
Webbplatsen har bara startsidan och artiklarna; appen körs på den egna datorn.

* **Ämnen.** Kandidaterna är korpusmönster som är *mönster att pröva* eller *bekräftar*, har en hypotes och håller i båda
  halvorna av korpusen där det går att pröva (1x). Ett utkast följer en fast mall – rubrik, ingress, "Kort sagt", vad vi
  ser, "Så säkra är vi", hypotesen, hur den kan prövas, förbehåll, "Se själv" och källor – och skrivs sedan om med egna
  ord: siffrorna och resonemangen kommer från analysen, berättelsen från skribenten. Räkningar som en artikel gör utöver
  korpusanalysen redovisas i artikeln med test, antal och nämnare.
* **Statistiken i klartext.** Varje statistiskt tal får en mening om vad det betyder. Ett värde justerat med
  Benjamini–Hochberg skrivs som andelen slumpfynd som väntas bland alla mönster som är minst lika tydliga ("högst omkring
  2 procent"), andra p-värden som hur sällan ett så tydligt mönster skulle uppstå av en ren slump ("ungefär ett fall av
  50"; `plain_significance`). En andel anges med sin nämnare – av hur många stenar där saken går att avgöra – och en
  hypotes skrivs som en hypotes: påståenden säger "visar", hypoteser "vi föreslår" (1x).
* **Bilder i stället för länkar.** En artikel visar kartverktygets bild i stället för att länka in i appen: tidskartan
  (andelen stenar med mönstret per sexkant om 20 km, före och efter omkring 1050), punktkartan (de få stenarna med ett
  sällsynt mönster) och förändringsmodellens kurvor (1h), ritade av `r/blogfig.R` på svenska och engelska. En figur som
  används fryses under sin innehållshash, så att en publicerad artikel behåller sin bild när korpusanalysen räknas om.
  Foton kommer ur Wikimedia Commons, bara med känd fri licens och med fotograf och licens i bildtexten.
* **Publicering.** Bara artiklar som har gått live exporteras till webbplatsens källkod (`web/content/articles.json` och
  figurerna i `web/public/figurer/`), eftersom repot är publikt; GitHub Pages bygger om webbplatsen när de pushas
  (`.github/workflows/site.yml`).


**Etiketter (2026-10-20).** Varje artikel bär en *typ* och ett eller flera *ämnen* ur en fast lista
(`src/blog_labels.py`, samma lista i `web/src/lib/labels.ts`; `tests/test_blog_labels.py` håller dem lika). Typerna
är Forskning, Metod, Så gör du, Pågående arbete och Personligt; ämnena Ristare, Språk och stavning, Formler och
syfte, Tro och magi, Kvinnor och barn, Norden, Datering och stil, Geografi, Kryptologi, Tolkning,
Sannolikhetsmodellen, Huggspår och 3D och Eddan. Admin sätter dem med knappar (en typ, högst fem etiketter
tillsammans), API:t avvisar etiketter utanför listan, och artikellistan på svenska och engelska filtrerar på dem
(`?etikett=…`; `components/LabelFilter.tsx`, `LabelChips.tsx`). Etiketterna följer med i exporten och i sökindexet.
*Så gör du*-artiklarna är handledningar steg för steg med skärmbilder ur appen, tagna med Playwright mot de lokala
dev-servrarna (`utdata/blogg/build/howto_huggspar_bilder.py`) och frysta i bloggens bildarkiv som andra figurer.

**Mest lästa (från 2026-10-21).** Exporten (`src/site_export.export`) lägger till `views` per artikel: antalet sidvisningar av
artikelns svenska och engelska sida i webbplatsens egen räkning (`site_views`, slaget view; `src/site_stats.views_by_slug`).
Listan kan sorteras efter dem (`?sortera=mest-lasta`, `web/src/components/SortToggle.tsx`); nyast först är standard och
veckans artikel ligger då först. Kan räkningen inte läsas behålls föregående antal. `src/site_export.refresh_views` kontrollerar
en gång om dygnet om ordningen "mest lästa" har ändrats och publicerar då webbplatsen om; annars inte. Antalen visas inte
för läsarna, bara ordningen.

## 16. Jämförbarhet med tidigare forskning

Laila Kitzler Åhfeldts metod (Arkeologiska forskningslaboratoriet, Stockholms universitet; Kitzler Åhfeldt
2002) mäter spårvariabler i högupplösta 3D-modeller med funktionen *Groove Measure* (DeskArtes), analyserar
runor och ornamentik separat, beskriver varje sten med medelvärden och använder bl.a. Wards klustring på
standardiserade variabler (t.ex. Kitzler Åhfeldt & Imer 2019, *Danish Journal of Archaeology* 8,
doi:10.7146/dja.v8i0.113226). Vitki följer samma upplägg (separata spårtyper, medelvärden per sten,
standardisering, Ward), men **måtten är inte verifierade som likvärdiga** med Groove Measure-variablerna.
Innan resultat jämförs direkt bör samma referensstenar mätas med båda metoderna.

## 17. Datakällor och licenser

**Runor 2020 bredvid Rundata 2018 (från 2026-10-20, `src/runor.py`).** Appens beräkningar bygger på Rundata 3.1 (2018).
Runor (RAÄ, utgåva 2020) är skördad i sin helhet (`scripts/fetch_runor.py` → `data/raa/runor_2020.json`, inte i git).
När filen finns visar inskriftssidan Runors uppgifter bredvid Rundatas: ursprunglig plats eller flyttad, bevarad,
datering, anteckningar och läsningen om den ändrats sedan 2018 (281 inskrifter, 77 av dem svenska vikingatida
runstenar; jämförelsen normaliserar ʀ/R, …/... och §P/§Q). Runor slås upp på exakt signum, så att Närkes Nä 1–34 inte
får Norges N A1–N A34. Inget räknas om på Runors uppgifter, och appen byter inte källa (IMPLEMENTATIONSPLAN.md 3.2,
struken 2026-10-26): ett byte skulle ha krävt en ny analysplan, eftersom 154 "in situ"-stenar är flyttade enligt Runor
och landskapsresultaten då ändras.

* **Samnordisk runtextdatabas** (Institutionen för nordiska språk, Uppsala universitet), version 2014 med
  RUNDATA.xls från 2018. Open Database License (databasen) / Database Contents License (innehållet).
  Källan ska anges: www.nordiska.uu.se/forskn/samnord.htm. `data/rundata.json` är en härledd databas och
  omfattas av samma licens. Svenska koordinater (RT90 2,5 gon V) räknas om till WGS 84 med pyproj.
* **Stilgrupper:** Gräslund, A.-S. 1998. Ornamentiken som dateringsgrund för Upplands runstenar.
  I: *Innskrifter og datering / Dating inscriptions*. Trondheim, s. 73–91. Dateringarna är ungefärliga.
* **Mätkorpusen:** bidrag publiceras under CC BY 4.0 med bidragsgivaren angiven.
* **Kartor:** © OpenStreetMap-bidragsgivare.
* **Berggrund:** Sveriges geologiska undersökning (SGU), Berggrund 1:50 000–1:250 000 (visningstjänst,
  WMS). Svaren cachas lokalt i `data/cache/geology.json` (ingår inte i repot).
* **Vatten och land:** Natural Earth 1:10 miljoner (kustlinje, sjöar, vattendrag, de europeiska tilläggen och land),
  public domain. Hämtas en gång till `data/cache/r/naturalearth/`.
* **Danska fornlämningar:** Fund og Fortidsminder (Slots- og Kulturstyrelsen), hela databasen som GeoPackage
  (`FF.zip`, uppdateras dagligen). Tjänsten är gratis och får användas utan styrelsens godkännande; webbplatsens sidor
  får inte skördas, så bara nedladdningen används (`scripts/fetch_dk_remains.py`, `data/dk/fortidsminder.csv`, ingår
  inte i repot).
* **Danska fyndplatser:** OpenStreetMap via Nominatim (© OpenStreetMap-bidragsgivare, ODbL), svaren sparade i
  `data/cache/dk/nominatim.json`; resultatet i `data/dk/runesten_koordinater.csv`.
* **Rikenas gränser** (14g): landskapen ur OpenStreetMap (© OpenStreetMap-bidragsgivare, ODbL); Danmark, Norge och
  Slesvig ur Natural Earth 1:10 miljoner (länder och regioner, public domain). Den byggda filen
  `web/public/geo/riken.geojson` är en härledd databas under ODbL.
* **Höjddata:** Terrain Tiles (Tilezen/Mapzen, Registry of Open Data on AWS), zoomnivå 12 per sten och zoomnivå 9
  för korpusens strandlinje. Hämtas till `data/cache/r/terrain/`.
* **Ortnamn:** OpenStreetMap (© OpenStreetMap-bidragsgivare, ODbL), med Lantmäteriets ortnamn från terrängkartan;
  Sveriges utdrag från Geofabrik, ortnamnen utplockade med GDAL (`scripts/fetch_place_names.py`, `data/ortnamn/`).
* **Medeltida kyrkor:** Wikidata (CC0), kyrkobyggnader i Sverige med uppförandeår före 1350.
* **Lämningar:** Kulturmiljöregistret (Riksantikvarieämbetet), hämtat via K-samsök (`serviceName=kmr_lamningar`):
  gravfält, högar, färdvägar och färdvägssystem, broar, fornborgar och hamnanläggningar, en punkt per lämning
  (`scripts/fetch_raa_remains.py`, `data/raa/lamningar.csv`, ingår inte i repot).
* **Runor** (Riksantikvarieämbetet), utgåva 2020 av Samnordisk runtextdatabas, och **Wikidata** (CC0), för
  avstämningen i 14b. Svaren cachas i `data/cache/crosscheck/`.
* **RuneS-DB** (Niedersächsische Akademie der Wissenschaften zu Göttingen, runesdb.de, beta): runfynd med graftyper –
  runformen position för position – samt tolkningar med litteratur; data CC BY-SA 4.0 (impressumet har också en klausul
  om vidareanvändning av bilder och texter, så inga skärmbilder eller bilder därifrån). Posterna för Skåne och Blekinge
  (259 inskrifter) hämtade 2026-10-21 till `data/raa/kallor/` (inte i git). Innehåller Kielprojektets material om den
  äldre futharken. Se 14h.
* **Språkbanken Text** (Göteborgs universitet), Karp v7: Söderwalls Ordbok öfver svenska medeltids-språket med
  supplement, Schlyters Ordbok till Samlingen af Sweriges Gamla Lagar och Fornsvensk lexikalisk databas; uppslagsord
  och artikel-XML hämtade 2026-10-21 (`data/raa/kallor/karp/`, inte i git). Se 14h.
* **K-samsök** (Riksantikvarieämbetet, kulturarvsdata.se): används för Kulturmiljöregistrets lämningar (ovan) och för
  fritext i 3D-vyn. Statens historiska museers 246 543 vikingatida föremål saknar fyndplats i indexet (prövat
  2026-10-21), så någon fyndkarta kring stenarna går inte att bygga därifrån.

## 18. Kända brister

Källkod: `src/limitations.py`, `GET /api/limitations`. Metodens kända brister förs i en enda förteckning
(version 2026-10-23) som följer med varje analys:

* **I appen** visas de brister som gäller sidan under varje analyssida (3D-analys, stenanalys, jämförelse,
  mätkorpus, syntes, statistik, forskningsluckor, inskrifter, karta, rapporter).
* **I rapporterna** har stenrapporten och korpusrapporten ett avsnitt "Kända brister och begränsningar", och varje
  publiceringsform tar med dem – fullständigt i vetenskapliga och antikvariska former, i populär form
  i blogginlägg, pressmeddelande och poster. Varningar för just analysen (t.ex. färre runor än riktvärdet) står först.
  AI som formulerar text får förteckningen och instrueras att inte tona ned den.
* **I proveniensen** som sparas med varje mätning och syntes står förteckningens version och vilka brister som
  gällde (`known_limitations`), så att det går att se i efterhand vad som var känt när mätningen gjordes.

När en brist åtgärdas ändras förteckningen och versionen höjs. Bristerna i dag:

| Brist | Gäller | Vad som behövs |
|---|---|---|
| Måtten är inte validerade som spår av ristarens hand | attribution, comparison, grooves | Stenar med känd ristare på samma bergart (i det enda referensmaterialet med kända ristare når huggtekniken inte över en gissning efter bergart, avsnitt 13), jämförelse med Groove Measure-data och gärna experimentella ristningar med kända ristare och verktyg. |
| Bottenradie och asymmetri är osäkra mått | comparison, grooves | Bättre bottenmodell och test på skanningar av samma sten med olika punkttäthet. |
| Ingen sten är mätt i oberoende skanningar | comparison, grooves | Test–omtest med oberoende skanningar av samma stenar, och manuell mot automatisk mätning; samma rutnät och känslighet för alla stenar som jämförs. |
| Inte jämförbart med tidigare 3D-studier utan kalibrering | comparison, grooves | Samma referensstenar mätta med båda metoderna. |
| Runigenkänningen är inte utvärderad | auto | Handmärkta facit för 8–10 stenar som inte använts för att justera reglerna (facit-läget i 3D-vyn, scripts/evaluate_rune_detection.py), med låsta regler. |
| Gränserna 10 och 20 runor är riktvärden | auto, comparison | Ny beräkning när test–omtest och stenar med känd ristare på samma bergart finns. |
| Attribueringen riskerar att bli cirkulär | attribution, statistics | Prövning på signerade stenar som inte använts i träningen och med variabler som inte låg bakom attribueringarna. |
| Träffsäkerheten beror på om platsen är känd | attribution, r, statistics | Grupperad korsvalidering även för mätkorpusens attribuering, när korpusen är stor nog. |
| Många utforskande test på samma data | attribution, research, statistics | Förregistrerade analysplaner för de hypoteser som ska publiceras. |
| Mer än hälften av runstenarna saknar datering | r, statistics | Fler säkra dateringar – i dag har 1 008 av 2 321 runstenar en stilgrupp med datering, och de övriga 1 313 (57 procent) räknas inte i tidsfrågorna (avsnitt 1n) – eller en imputation med samspel mellan landskap och drag prövad enligt en ny plan. |
| Stenarnas mått är ofullständiga och ojämna | research, rundata | Mått ur Sveriges runinskrifter eller nya mätningar för stenarna som saknas; hela höjden för resta stenar. |
| AI-text är okalibrerad och kan vara påhittad | ai | Granskning av AI-texten mot beläggen i varje rapport; AI-text förblir ett tillval och ersätter aldrig framräknad text. |
| Rundata är en äldre utgåva | attribution, research, rundata | Uppdatering till senaste utgåvan av Runor. |
| Sannolikhetsmodellen är inte prövad på öppna luckor | textmodel | Grammatisk kontroll (kasus och kongruens) och prövning mot luckor som fyllts i senare utgåvor eller med nya spår ur skanningar. |
| Modellen kan föreslå stavningar som inte är belagda | textmodel | Att varianten som ledde till förslaget visas, och att lagret prövas på öppna luckor som fylls i senare utgåvor (toleranslagret sedan `textmodel-19`, avsnitt 8.1). |
| Programvaran är under utveckling | attribution, comparison, grooves, software | Låst version med DOI (Zenodo) och extern granskning av koden. |

R-analysernas egna begränsningar (avsnitt 1) ingår när de används.
