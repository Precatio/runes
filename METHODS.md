# Metodbeskrivning

Den här filen beskriver exakt hur Vitki räknar, så att resultat kan granskas, upprepas och citeras.
Alla beräkningar finns i `src/` (Python) och `r/` (R); testerna ligger i `tests/`. Varje analys sparar en **proveniens**
(programversion, mätmetodens version, SHA-256 för 3D-filen, alla parametrar och tidpunkt) som följer med i export och
rapporter.

**Avsnitten.** Avsnitt 1 är statistiken i R över hela korpusen – de 2 321 svenska vikingatida runstenarna i Rundata –
där appens mönster och hypoteser kommer ifrån. Avsnitt 2–13 beskriver hur en enskild sten mäts, läses och attribueras
(huggspår, ortografi, språk, inskriftens syfte, bergart, 2D-analys och syntes), 14 forskningsluckorna och tolkningen av
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
en skola eller ett museum ("Frustuna kyrka", "Veta kyrkogård"), eftersom de inte kan skiljas från flyttade stenar
(1 176 av 2 321; kolumnen `moved` i korpusens CSV, `is_moved` i `src/r_bridge.py`).

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

Beräkning 2026-10-12 (117 kombinationer): tio klarar justeringen och fyra håller i båda halvorna. Kristna markörer och
kors blir vanligare närmare centralortsnamn (oddskvot 1,24 respektive 1,23 när avståndet halveras), och kristen bön
närmare medeltida kyrkor (1,26); alla tre håller också med tiden konstant. Sambandet mellan bön och teofora namn är
svagare utan vald radie (1,26, q 0,047, bara i den ena halvan), vilket talar för att eliten och de tidiga kyrkorna
förklarar en del av det som syns vid kultnamnen.

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
2026-10-11, med de nya språkdragen): en grupp bestod i genomsnitt till 69 % av samma ristare, mot 43 % för bara
närliggande stenar, och 64 % av grupperna till minst tre fjärdedelar; av länkade par med känd ristare var 71 % samma
ristare. Bland stenarna utan ristare blev det 17 grupper, varav 8 möjliga okända ristare: Konungsundsristaren (30
stenar, Östergötland), Vibyristaren (15, Östergötland), Vetlandaristaren (14, Småland), Kölabyristaren (13,
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

`GET /api/r/package` (knappen på sidan Statistik) ger en zip med R-skripten, korpusens CSV,
resultaten, `sessionInfo()` och `KOR_OM.R`, som kör om allt i R utan appen. Paketen installeras med
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

### 1x. Försiktighet i påståendena, djärvhet i hypoteserna

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

## 2. Huggspårsmått (mätmetod `groove-5`)

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

### 2d. Bilder ur skanningen

Källkod: `api/routers/threed.py` (`render_relief`), `src/stone_report.py` (`Surface`). Bilder för läsning,
2D-analys och rapporter räknas direkt ur skanningen i stället för att fotografera skärmen:

* Ytan projiceras till ett höjdfält från den sida som vetter mot betraktaren i 3D-vyn (kamerans riktning och
  upp-riktning). Utan vy används stenens tunnaste riktning (minsta variansriktningen), vänd mot den sida där
  mest yta pekar.
* **Strykljus** från fyra riktningar (nordväst, nordost, sydost, sydväst) 20° över ytan.
* **Relief**: det mörkaste av de fyra strykljusen, så att varje spår blir mörkt oavsett riktning.
* **Djup** under en rekonstruerad stenyta (morfologisk stängning, 20 mm); kantzonen (10 mm), där
  referensytan är osäker, utelämnas.
* Bilderna har känd upplösning (mm per pixel) och påverkas inte av zoom eller skärmens belysning. Små
  skanningar skalas upp till minst 1 200 px för läsning.

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
* **Runformer** från 2D-analysen (normaliserad form och särdragsvektor, se avsnitt 12) kan bifogas under
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

## 8. Språk och läsning

Källkod: `api/routers/phonetics.py`, `src/reading.py`.

* **Blind läsning:** en språkmodell läser runorna från bilden utan att få signumet (steg 1). Även tolkningen
  (steg 2: normalisering till runsvenska, översättning, IPA, ljudlagar) görs utan signum, eftersom modellen
  annars återger den publicerade läsningen ur minnet i stället för det som syns på bilden. Translitterationen
  i resultatet är alltid den blinda läsningen.
* **Jämförelse med Rundata (utan AI):** translitterationerna jämförs ord för ord och runa för runa
  (difflib). *Överensstämmelse* = andelen av våra runor och ord som finns i Rundatas läsning, *täckning* =
  andelen av Rundatas text som vår läsning omfattar (en beskuren bild kan stämma helt men täcka lite). Bara
  sammanhängande träffar på minst tre runor räknas, skiljetecken och textkritiska tecken ignoreras och
  Rundatas oläsliga tecken redovisas separat.
* **Ordformer:** varje form i vår normalisering slås upp bland Rundatas normaliserade former i
  vikingatida inskrifter; obelagda former flaggas för granskning.
* **Ortografi för vår läsning:** samma modell som i avsnitt 7, med stenen själv utesluten. Används i
  syntesen när Rundata saknar en användbar text (t.ex. nyfynd), med 30 % lägre tillförlitlighet.
* **Validering – får läsningen visas som stenens text?** (`src/reading.py`, `validate`): läsningen prövas utan AI
  mot (1) stenens text i Rundata, (2) alla kända inskrifter i Rundata (trigramfilter och samma
  överensstämmelsemått) och (3) andra läsningar av samma bild. Status: *bekräftad* (≥ 80 % av runorna i stenens
  läsning), *delvis* (50–80 %), *ej bekräftad* (< 50 %), *annan inskrift* (liknar en annan känd inskrift minst
  60 % och tydligt mer än stenens egen – modellen har troligen återgett en inlärd text) eller *ej prövbar* (Rundata
  saknar text; då krävs att flera läsningar stämmer minst 80 % med varandra). En läsning med färre än 12 läsbara
  runor är alltid *ej prövbar*: ett kort ord som *sin* finns i de flesta inskrifter, så att det stämmer säger
  ingenting om att bilden är läst. Bara bekräftade, delvis bekräftade
  och samstämmiga läsningar visas som läsning, med normalisering och översättning, och bara de används som
  belägg i syntesen. I rapporter redovisas en obekräftad läsning aldrig som stenens text.
* **Erfarenhet:** i testet med Sö 113 gav tre blinda läsningar tre olika, trovärdiga men påhittade texter (6–24 %
  av runorna stämde), en av dem Jellingestenens text (DR 42, 95 % lika). Språkmodeller kan alltså inte läsa runor
  tillförlitligt; reliefbilderna är ett bättre underlag för en mänsklig läsning.
* Läsningen kan rättas för hand och jämföras igen; den märks då som rättad.
* **Bilder att läsa:** foto, 2D-analysens bild, RTI-vy eller reliefbilder ur 3D-skanningen (strykljus från
  fyra riktningar, ett kombinerat relief där varje spår blir mörkt oavsett riktning, och djup under
  stenytan), räknade från den sida som vetter mot betraktaren i 3D-vyn.
* **Uppläsning:** en modern talsyntes läser normaliseringen. Det är inte en rekonstruktion av uttalet;
  IPA-raden är modellens förslag och ljudlagarna är inte kontrollerade.

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

## 12. 2D-analys och runformer

* AI-bedömningen av en bild (stilgrupp Pr1–Pr5, RAK, Fp eller **Osäker**, runformer, translitterering) är en
  hypotes. Modellens säkerhet är dess egen skattning och **inte kalibrerad**. Om stenen har en stilgrupp i
  Rundata visas den bredvid, och syntesen redovisar om AI:n och Rundata är överens.
* **Runformer** (`src/graphemes.py`, särdragsversion `grapheme-2`): utsnittet kontrastförstärks (CLAHE),
  binäriseras (Otsu; minoritetsklassen räknas som ristning), beskärs till ristningen och läggs i en kvadrat
  med bibehållna proportioner, 64 × 64 px. Särdrag: HOG, täthet i 4 × 4 zoner och logaritmerat
  höjd/bredd-förhållande. Likhet: cosinus.
* **Validering:** på syntetiskt ritade runor (ᛁ ᛏ ᚴ ᚱ ᛋ med slumpad stavtjocklek, lutning och brus,
  `src/synthetic_runes.py`) hamnar närmaste granne på rätt runa i 85 % av fallen. Den tidigare metoden låg
  på slumpnivå. Resultatet är ett mått på **formlikhet**, inte på samma ristare; på riktiga stenar påverkas
  det av vittring, belysning och utsnittets noggrannhet.
* Jämförelser görs bara mellan utsnitt med samma särdragsversion och, om angivet, samma runtyp
  (långkvist, kortkvist, stungen m.fl.).
* Bilder kan komma från uppladdning, K-samsök, en reliefbild räknad ur 3D-skanningen, RTI-visaren eller
  **ristningskartan** från den automatiska spåranalysen (residualdjup, djupt = mörkt). Ristningskartan har
  samma pixelkoordinater som analysens granskningsbild, så ett runutsnitt där kopplas till de uppmätta
  snitten inom utsnittet.
* **Automatiska runutsnitt** (från 2026-10-11; knappen "Hitta runorna"). För en ristningskarta från 3D-analysen
  används runorna som analysen själv känt igen (spåren grupperade per runa, `classify_strokes`): rutan omsluter
  runans spårmittlinjer med 4 mm och en tiondel av runans storlek som marginal. Analysen vet inte vilken runa det är,
  så utsnitten sparas som "obestämd runa" tills användaren anger det. För andra bilder markerar AI varje runa med en
  ruta och en translitterering (`POST /api/2d/detect_runes`); rutorna och läsningen är okalibrerade och visas för
  granskning innan de sparas, och rutor där AI är mindre än 50 % säker är inte förvalda. Varje sparat utsnitt får samma
  formbeskrivning som ett manuellt, märks som automatiskt (`auto`: "3d" eller "ai") och får en mindre miniatyr (128 px)
  och formvektorn avrundad till tre decimaler, så att ett projekt med många utsnitt ryms inom gränsen på 1 MB; högst
  40 sparas åt gången. Rutor utan en tydlig runform hoppas över.

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
* **Huggteknikens tillförlitlighet** = korsvaliderad träffsäkerhet över slumpnivån,
  (träff − slump)/(1 − slump). Är metoden inte bättre än slumpen vägs den inte in. Jämförelsen görs med
  den valda analysen (runor som standard), mot stenar med samma spårtyp och säker ristare; stenen själv
  ingår aldrig i referensen.

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

Har projektet en egen läsning från Språk & Fonetik används den som ortografiskt belägg när Rundata saknar
användbar text, med 30 % lägre tillförlitlighet, och läsningens överensstämmelse med Rundata redovisas.

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
  säkra inskrifter, och om stenen finns kvar att undersöka.

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

Resultat (2026-10-11, efter granskningarna av U 92, U 1026 och U 735 – kronologisk stilkontroll, neutral bergart,
språkdrag mot landskapet, stilgruppens kärna och ortografins marginal): 9 stenar kan vara felbedömda, 26 är omstridda,
330 stöds och 160 har svagt underlag; 80 stenar utan ristare får ett nytt och 251 ett möjligt förslag. **Kontroll:**
av 246 signerade stenar – där ristaren är känd – får 33 (13 %) ett alternativ ≥ 0,4 och fyra hamnar som "kan vara
felbedömd". Före U 735-granskningen var det 57 (23 %): ett förstaval i ortografin med liten marginal och en ovanlig
stilgrupp inom kärnans tidsram gav många falsklarm. Kategorin *omstridd* larmar fortfarande ofta i onödan, medan *kan
vara felbedömd* sällan gör det. Måtten är index för att sortera och prioritera,
inte sannolikheter; bara modellens sannolikhet är kalibrerad. Metoderna är inte oberoende av Rundata: ortografi,
område och stil kan ha legat till grund för attribueringarna (avsnitt 18). Profilen för en sten visar varje metods
besked med förklaring, de tre starkaste alternativen med sina kontroller, och stenens höjd, textlängd och antal
namn som percentil bland landskapets runstenar, med syfte, statusord, stilgrupp, seriation och grupp.

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

och, om det finns, bilden och runformerna från 2D-analysen. Figurerna 1–4 kräver att skanningen finns i
analysmotorns minne (samma fil inläst i 3D-vyn); annars utelämnas de och rapporten säger det. Snittens
positioner och råprofiler sparas med varje analys (automatisk, ett klick per snitt och spårbana).

Stenrapporten får dessutom, när underlaget finns:

* **berggrunden på platsen** (SGU) i avsnittet om stenen,
* **Läsning av bilden** – appens blinda läsning som inskrift (fetstil/kursiv), jämförelsen med Rundata,
  skillnaderna ord för ord, kontrollen av ordformer och, märkta som AI, IPA och ljudlagar,
* **Attribuering** – den sparade syntesen: utfallet mot litteraturen, kandidattabellen, kontrollerna
  (geografi, stilgrupper, bergart, språkdrag, sten mot sten), motsägelser och saknade belägg.

### 15c. Fullständig stenanalys (arbetsgång)

Sidan **Stenanalys** och skriptet `scripts/full_stone_analysis.py` kör hela kedjan för en skanning och ett
signum, med samma beräkningar som de enskilda verktygen:

1. Uppladdning och **bilder ur skanningen** (avsnitt 2d). Den ristade sidan skattas som stenens tunnaste
   riktning; den andra sidan kan väljas.
2. **Automatisk spåranalys** med flera känsligheter (standard 3 och 5). Den första är huvudanalysen, de övriga
   en känslighetsanalys som redovisas med granskningsbilder.
3. **2D-bildanalys** av strykljuset från nordväst.
4. **Blind läsning** i en eller flera orienteringar (standard 0° och 180°), validerad mot Rundata, kända
   inskrifter och varandra (avsnitt 8).
5. **Syntes och attribuering** med berggrund (avsnitt 11 och 13); med inloggning även mot mätkorpusen.
6. **Forskningsläge och syfte** (`GET /api/research/stone/{signum}`): det Forskningsluckor vet om stenen
   (landskapets täckning, stenens luckor i Rundata, om den finns bland ortografiska hypoteser, omprövningar
   eller mätprioriteringar och hur appens resultat bedöms mot forskningen), inskriftens syfte (avsnitt 10) och,
   för de tre troligaste ristarna, hur ofta de ristade i stenens stilgrupp och inskriftstyp.
7. **Statistik i R** (avsnitt 1): startar korpusanalyserna om de saknas och ställer stenen mot dem –
   attribueringsmodellen, kandidaternas områden, gruppen i klustringen, formlerna, Upplands seriation och
   landskapet (höjdmodell, strand, sikt, vägar).
8. **Stenrapport** (15b), med avsnitten "Inskriftens syfte" och "Stenen i forskningsläget", R-avsnitten (metod 3.4,
   modellen i attribueringen, "Stenen i korpusen", "Stenen i landskapet"), en tabell över
   kandidaternas stilgrupper och inskriftstyper, bilaga A (alla tvärsnitt) och bilaga B: arbetsgångens steg och utfall,
   känslighetsanalysen, granskningsbilder, relief, 2D-motiveringen, alla läsningar med status och de fel
   eller begränsningar som uppstod.

Misslyckas ett AI-steg (ingen nyckel, slut på krediter, tidsgräns) fortsätter arbetsgången, och felet
redovisas i bilaga B. Resultatet kan sparas i ett projekt; bara en validerad läsning sparas som projektets
läsning.

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

## 16. Jämförbarhet med tidigare forskning

Laila Kitzler Åhfeldts metod (Arkeologiska forskningslaboratoriet, Stockholms universitet; Kitzler Åhfeldt
2002) mäter spårvariabler i högupplösta 3D-modeller med funktionen *Groove Measure* (DeskArtes), analyserar
runor och ornamentik separat, beskriver varje sten med medelvärden och använder bl.a. Wards klustring på
standardiserade variabler (t.ex. Kitzler Åhfeldt & Imer 2019, *Danish Journal of Archaeology* 8,
doi:10.7146/dja.v8i0.113226). Vitki följer samma upplägg (separata spårtyper, medelvärden per sten,
standardisering, Ward), men **måtten är inte verifierade som likvärdiga** med Groove Measure-variablerna.
Innan resultat jämförs direkt bör samma referensstenar mätas med båda metoderna.

## 17. Datakällor och licenser

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

## 18. Kända brister

Källkod: `src/limitations.py`, `GET /api/limitations`. Metodens kända brister förs i en enda förteckning
(version 2026-10-16) som följer med varje analys:

* **I appen** visas de brister som gäller sidan under varje analyssida (3D-analys, stenanalys, jämförelse,
  mätkorpus, syntes, statistik, forskningsluckor, inskrifter, karta, stilgrupper, 2D-analys, läsning, rapporter).
* **I rapporterna** har stenrapporten och korpusrapporten ett avsnitt "Kända brister och begränsningar", och varje
  publiceringsform tar med dem – fullständigt i vetenskapliga och antikvariska former, i populär form
  i blogginlägg, pressmeddelande och poster. Varningar för just analysen (t.ex. färre runor än riktvärdet) står först.
  AI som formulerar text får förteckningen och instrueras att inte tona ned den.
* **I proveniensen** som sparas med varje mätning och syntes står förteckningens version och vilka brister som
  gällde (`known_limitations`), så att det går att se i efterhand vad som var känt när mätningen gjordes.

När en brist åtgärdas ändras förteckningen och versionen höjs. Bristerna i dag:

| Brist | Gäller | Vad som behövs |
|---|---|---|
| Måtten är inte validerade som spår av ristarens hand | attribution, comparison, grooves | Stenar med känd ristare på samma bergart, jämförelse med Groove Measure-data och gärna experimentella ristningar med kända ristare och verktyg. |
| Bottenradie och asymmetri är osäkra mått | comparison, grooves | Bättre bottenmodell och test på skanningar av samma sten med olika punkttäthet. |
| Ingen sten är mätt i oberoende skanningar | comparison, grooves | Test–omtest med oberoende skanningar av samma stenar, och manuell mot automatisk mätning; samma rutnät och känslighet för alla stenar som jämförs. |
| Inte jämförbart med tidigare 3D-studier utan kalibrering | comparison, grooves | Samma referensstenar mätta med båda metoderna. |
| Sannolikhetsmodellen är inte prövad på öppna luckor | textmodel | Grammatisk kontroll (kasus och kongruens) och prövning mot luckor som fyllts i senare utgåvor eller med nya spår ur skanningar. |
| Runigenkänningen är inte utvärderad | auto | Handmärkta facit för 8–10 stenar som inte använts för att justera reglerna (facit-läget i 3D-vyn, scripts/evaluate_rune_detection.py), med låsta regler. |
| Gränserna 10 och 20 runor är riktvärden | auto, comparison | Ny beräkning när test–omtest och stenar med känd ristare på samma bergart finns. |
| Attribueringen riskerar att bli cirkulär | attribution, statistics | Prövning på signerade stenar som inte använts i träningen och med variabler som inte låg bakom attribueringarna. |
| Träffsäkerheten beror på om platsen är känd | attribution, r, statistics | Grupperad korsvalidering även för mätkorpusens attribuering, när korpusen är stor nog. |
| Många utforskande test på samma data | attribution, research, statistics | Förregistrerade analysplaner för de hypoteser som ska publiceras. |
| Stenarnas mått är ofullständiga och ojämna | research, rundata | Mått ur Sveriges runinskrifter eller nya mätningar för stenarna som saknas; hela höjden för resta stenar. |
| AI-resultat är okalibrerade och kan vara påhittade | ai | Kalibrering mot runologers läsningar av samma bilder. |
| Rundata är en äldre utgåva | attribution, research, rundata | Uppdatering till senaste utgåvan av Runor. |
| Programvaran är under utveckling | attribution, comparison, grooves, software | Låst version med DOI (Zenodo) och extern granskning av koden. |

R-analysernas egna begränsningar (avsnitt 1) ingår när de används.
