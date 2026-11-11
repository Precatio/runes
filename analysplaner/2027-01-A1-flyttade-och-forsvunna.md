# Analysplan A1: flyttade och försvunna runstenar – hur långt, hur många, var och varför

Skriven 2026-11-11 som fas 1: ingenting av det som prövas nedan har räknats. Bara fältens tillgång har räknats (antal
poster som har ett fält, se ”Tillgång”), inga samband och inga avstånd. Planen låses med sha256 och commit när Viktor har
granskat den, före körningen i början av januari 2027. Den läggs på Zenodo med datum och DOI när studien startar
(Viktors regel 2026-11-10).

Studie A1 i `PUBLICERINGSPLAN.md` (januari 2027). Den täcker frågelistans fem rader med studien ”jan 2027 – A1. Flyttade
och försvunna stenar” (`utdata/litteraturgenomgang/artikelkandidater/fragelista.jsonl`):
- ”Hur långt flyttades runstenarna – och hur många lägen är gissning?”
- ”Hur många runstenar odlade vi bort? Plogen, leran och åsarna”
- ”Hur många runstenar restes egentligen? Är bilden mättad?”
- ”Flyttades stenarna till kyrkan – eller stod de där redan?”
- ”Hur många runstenar är bara spöken? Dubbletter i korpusen”

## Varför
Alla Vitkis platsstudier förutsätter att stenen står där den restes, eller nära: lerkanten, gravfälten, vattnet, vägen
och klustringen på 100–1 000 m. Flyttfiltret rättades 2026-10-12, när omkring 420 kyrkstenar visade sig ha räknats som
orörda, och igen 2026-10-27. Med den nuvarande regeln (`src/r_bridge.is_moved`) är 1 223 av 2 321 stenar flyttade. Hur
långt stenarna flyttades, hur mycket som försvann och var, och hur många stenar som en gång stod, har aldrig mätts för
hela korpusen.

## Frågorna
- **P1.** Hur långt flyttades stenarna, och hur många står där de restes?
  - P1a: flyttsträckan;
  - P1b: lägesfelet i Vitkis koordinater;
  - P1c: andelen på ursprunglig plats;
  - P1d: Larssons antagande om socknen.
- **P2.** Försvann fler stenar på lera och silt, och på isälvsavlagringar (åsar), än på morän och berg?
- **P3.** Hur många stenar har stått synliga sedan 1600-talet, och har upptäckterna planat ut?
  - P3a: upptäcktskurvan;
  - P3b: uttagsmodellen;
  - P3c: återfunna stenar som fångst–återfångst.
- **P4.** Kyrkstenarna: hämtades de från ristarens vanliga trakt, och är stenarna vid kyrkorna yngre än de andra?
- **P5.** Spökstenar och dubbletter: har de försvunna stenarna fler nästan likadana texter i närheten än de bevarade har?

Konfirmatoriska prov (Holm över alla sex): P2-lera, P2-ås, P3a, P4a, P4b och P5. P1 och P3b–c är skattningar med gränser
som bestäms nu, utan p-värde.

## Litteraturen planen bygger på
Kontrollerad mot originaltexten 2026-11-11 i `downloads/tidskrifter/sok.sqlite` (OCR med blanksteg borttagna). Sidorna är
de tryckta.

**Kyrkstenarna och flyttningarna**
- **Larsson 1986**, Fornvännen 81, s. 99. Larsson skriver att man i de flesta fall kan anta att stenen ”i alla fall står
  kvar i ursprunglig socken”. Skälen är att landskapslagarna krävde ”stock och sten” till kyrkbygget, och att stenarna
  är tunga. Det prövas i P1d.
- **Jansson 1955**, Fornvännen 50, s. 223. Om Långtorastenarna, inlagda när kyrkan byggdes: ”Sannolikt har de
  ursprungliga platserna legat nära kyrkan.”
- **Svärdström 1970**, Fornvännen 65, s. 305. En sten i kyrkmur bör ”ha stått icke alltför långt från kyrkplatsen”.
- **Stille 2015** (Futhark 5, 2014), s. 140. Stenar inmurade i kyrkor kommer ”oftast ifrån närområdet”, men hur stort
  det är ”måste diskuteras från fall till fall”. På s. 141: av 165 medeltida kyrkor i Tiohärad har runstenar hittats
  vid omkring 10 procent.
- **Jansson 1946**, Fornvännen 41, s. 276–277. Motexemplet: Brunnastenen fördes till Svinnegarns kyrka, 10 km fågelväg
  och omkring 13 km landsväg bort. Jansson skriver att sådana ”onaturliga runstenstransporter” verkligen har ägt rum.
- **Herschend 2017**, Fornvännen 112, s. 11. Överselö kyrka fungerar som ”en lokal magnet för traktens runstenar, som
  antingen flyttats dit eller ställts upp där från början”. Ytterselö kyrka gör det inte. Prövas för hela korpusen i P4b.

**Hur många som står kvar**
- **Klos 2009**, s. 57, återgiven av Stille 2015, s. 139 (Klos inte kontrollerad i original):
  - 2 654 runstenar i nuvarande Sverige;
  - 1 231 i sekundärt läge;
  - 693 med osäker placering;
  - 730 (28 %) på ursprunglig plats.

  Stille påpekar på samma sida att också stenar på ursprunglig plats kan ha vält och rests på nytt.
- **Stille 2008**, s. 75 f., återgiven av Stille 2015, s. 139 (inte kontrollerad i original). Det har funnits ”åtminstone
  dubbelt så många runstenar som de nu kända, men det kan röra sig om betydligt fler”.

**Spökstenar och dubbletter**
- **Lerche Nielsen 2010**, Futhark 1:
  - s. 225: omkring 20 % av de dokumenterade skandinaviska runstenarna räknas som förlorade;
  - s. 240: Lerche Nielsen är övertygad om att det finns fler dubbletter att hitta i Uppland;
  - s. 241–243: Ög 157 fördes troligen till Tingstad efter Hadorphs besök. Ög 158† och Ög 159† är troligen Ög 156 och
    Ög 157. Sex inskrifter kring Ög 157 (Ög 191†, Ög 195†, Ög 158†, Ög 159†, Ög 156 och Ög 157) ”could probably be
    reduced to a mere two”.
- **Lerche Nielsen 2003**, Fornvännen 98, s. 195. U 981† är ”nothing but a corrupt recording of U 980”.

**Bortfallet**
- **Söderberg, Lagerås och Björk 2021**, Fornvännen 116, s. 264. Åkerbruket på slätten har gett ”bortplöjning av
  förhistoriska gravar”, medan den låga uppodlingen på åsen har bevarat gravar och röjningsrösen. Obs: texten gäller
  gravar, inte runstenar. Frågelistan säger runstenar, och det stämmer inte med originalet.
- **Äijä 1985**, Fornvännen 80, s. 131. Gravfältet på rullstensåsen vid Åby skadades av järnvägsbygge, vägar, bebyggelse
  och sand- och grustäkt. Också det gäller gravar.
- **Gustavson och Brink Snædal 1980**, Fornvännen 75, s. 238. Ett runstensfragment som låg under markytan på en åker
  sprängdes sönder för att det skulle gå lättare att forsla bort.

**Upptäckterna och korpusutgåvorna**
- **Jansson 1954**, Fornvännen 49, s. 87. Flera av Köpingfragmenten på Öland har ingått i stenkistor. Antalet fragment är
  alltså inte antalet resta stenar.
- **Källström 2022** (Futhark 12, 2021):
  - s. 7–8: Bautil (Göransson 1750) är träsnitt av mer än 1 100 stenar, ritade under Hadorphs och Peringskiölds tid.
    Liljegrens *Run-urkunder* (1833) translittererar ”all the runic inscriptions known at that time”;
  - s. 20: nyfynden publicerades årligen i Fornvännen och sedan i *Nytt om runer*, med fynden till och med 2003. Därefter
    finns ingen årlig publicering;
  - s. 26: utgivningsåren för SRI-banden (tabellen under P3).
- **Wikell, Källström och Dahlin 2018**, Fornvännen 113, s. 8. ”Frånvaron av runstenar i Sevede beror på en
  forskningslucka.” Används i A2, nämns här för upptäcktskurvan.

## Underlag
- **Stenarna.** Svenska vikingatida runstenar enligt `research_gaps.is_runestone`, ur Rundata 2018 (`data/rundata.json`,
  byggd 2026-10-04). Fragment av runsten räknas. Försvunna runstenar är runstenar (`flags.lost`). Korpusens hash
  antecknas vid körningen.
  - Gravhällar, lösa föremål och ristade stenar utan runor ingår inte.
  - Danska och norska stenar ingår inte.
  - Skåne, Blekinge och Halland har DR-signum och ligger utanför, som i alla Vitkis studier.
- **Fasta ristningar (kontroll, redovisas för sig).** Berghällar, bergväggar och jordfasta stenblock (Rundatas objekt
  `berghäll`, `bergvägg`, `jordfast stenblock`). De kan inte ha flyttats och ger brusgolvet för koordinaterna i P1b.
- **Runor 2020.** Råposterna i `data/cache/runor/` (skördade 2026-10-16). Där finns:
  - ursprunglig plats (`original_location`);
  - nuvarande och äldsta kända läge (`position`);
  - härad (`provenance.hundred`);
  - artefakttyp, alternativa signum och källor.

  Posterna kopplas till Rundata som i `scripts/runor_compare.py`: exakt signum först, sedan vikt signum och alternativa
  signum. Runorstenar som saknas i Rundata räknas bara i P3, om Runor ger artefakten `runsten`, perioden V och landet SE.
  Antalet redovisas.
- **Jordarter.** SGU:s jordartskarta 1:25 000–1:100 000 (`geografi_kallor/sgu_jord/`, de 15 hämtade länen, CC BY 4.0).
  - Stenens punkt slås upp i vektorerna, ett län i taget.
  - Klasserna följer `utdata/palm_jordarna/jordartsklasser.csv`, med en ändring: jordartsnamn som börjar med
    ”Isälvssediment” blir en egen klass, **ås**. Övrig sand och grus blir **sand**.
  - Stenar utanför de 15 länen räknas bort och antalet redovisas.
- **Socknar.** ISOF:s sockenpunkter (`geografi_kallor/isof/parishes.json`, 2 538 socknar). Sockenpolygoner ur R-paketet
  histmaps används om paketet går att installera (behövs också i A2).
- **Ristarna.** `research_gaps.certain_carvers`: signerade och tillskrivna utan frågetecken.
- **Stilgrupperna.** Rundatas stilgrupp, bara när den är säker (`has_style`).
- **KMR:s runristningsposter** (`data/raa/runristning_lan.csv`). Används bara beskrivande, för fyndår ur fritexten.

## Tillgång (räknad 2026-11-11, bara antal poster med fältet)
**Rundata 2018, svenska vikingatida runstenar**

| Fält | Antal |
|---|---|
| Runstenar | 2 321 |
| Försvunna (`flags.lost`) | 415 |
| Med koordinat | 2 318 |
| Med härad | 2 200 |
| Med Bautil-nummer (B) | 1 023 |
| Med Liljegren-nummer (L) | 1 281 |
| Signum i SRI-form (landskap + nummer) | 1 973 |
| Senare signum | 348, varav 265 med ett årtal i signumet |
| Öl Köping-signum (utan årtal) | 68 |

**Runor 2020, svenska vikingatida runstenar enligt Runors artefakttyp (2 402)**
- `original`:
  - sant: 165;
  - falskt: 475;
  - tomt: 1 762.
- Både nuvarande och äldsta läge: 424. Av dem har 164 `original` falskt, 259 tomt och 1 sant.
- Bara äldsta läge: 1 974.
- Härad: 2 402.
- Fritext om ursprunglig plats: 35.
- Inte bevarade: 428.

Frågelistans ”606 ursprungliga platser” var ett äldre räknesätt. Mot Rundata matchade 623 med `original` angiven
(`utdata/runor/jamforelse.json`).

**Kyrkstenar** (Rundatas plats eller placering med kyrk- eller kapell-)
- 925 runstenar, varav 141 försvunna.
- 167 av dem har en säker ristare som har minst två orörda, bevarade stenar (35 ristare).
- Orörda och bevarade stenar totalt: 836.

**Försvunna stenar**
| Försvunna | Antal |
|---|---|
| Totalt | 415 |
| Vid kyrka | 141 |
| På koordinater som delas av minst tre stenar | 33 |
| Med B-nummer | 237 |
| Med minst 10 runor i translittereringen | 332 |

**Övrigt**
- Återfunna stenar med årtal i Rundatas anmärkning eller Runors noter: 48.
- Rundata har redan slagit ihop dubbletter. Fyra anmärkningar säger ”förd(a) hit”: U 235 (U 199 och U 234), U 796
  (U 760), Ög 206 och U 781. Tretton anmärkningar säger ”samma sten” eller liknande. Ög 191 och Ög 195 har anmärkningen
  om Lerche Nielsen 2010.
- Fasta ristningar: 59 berghällar, 15 bergväggar och 46 jordfasta stenblock.
- KMR:s runristningsposter: 2 383. Fyndår i fritexten: 256. ”Flytt-”: 311. ”Ursprunglig”: 198.

## P1. Flyttsträckan och de ursprungliga platserna (skattningar)

**P1a. Hur långt har stenarna flyttats sedan de först dokumenterades?**
- **Urval:** Runorstenar med både nuvarande och äldsta kända läge (424).
- **Mått:** avståndet (haversine, meter).
- **Klass efter destination.** Bestäms ur Runors `placement` och nuvarande plats, med regler som skrivs i
  `utdata/flyttade/destination_klasser.csv` innan något avstånd räknas:
  - **museum:** museum, SHM, magasin, samlingar;
  - **kyrka:** kyrk-, kapell, vapenhus, bogård;
  - **övrigt:** gård, park, väg, tomt och annat.
- **Redovisas:**
  - median och kvartiler;
  - andelarna under 100 m, 100–499 m, 500–4 999 m och minst 5 km;
  - per destination och landskap;
  - 95 % bootstrapintervall (2 000 dragningar, slumpfrö 2026).
- **Huvudmått:** medianen för flyttningar som inte gick till museum.
- **Begränsning:** flyttningar *före* första dokumentationen syns inte här. Det gäller t.ex. de flesta stenar som murades
  in i medeltida kyrkor. Det skrivs ut.

**P1b. Hur stort är lägesfelet i Vitkis egna koordinater?**
- **Urval:** bevarade runstenar som `is_moved` räknar som orörda och som har ett Runorläge.
- **Mått:**
  - d = avståndet mellan Rundatas koordinat och Runors nuvarande läge, eller Runors äldsta läge när nuvarande saknas;
  - samma d för de fasta ristningarna (brusgolvet);
  - andelen d ≤ 100 m, ≤ 200 m och ≤ 500 m, med Wilson-intervall.
- **Gräns, bestämd nu.** ”Lägena bär 200-metersmåtten” om båda villkoren gäller:
  - minst 90 % av de orörda stenarna har d ≤ 200 m;
  - den andelen ligger högst 5 procentenheter under de fasta ristningarnas.
- **Om gränsen inte nås** skrivs en lista över de resultat som bygger på 200–500 m: lerkanten (`platsen.py`,
  `kontroller.py`), familjens plats, vattnet inom 500 m och vägen. De körs om med Runors läge i en egen låst kontroll.
  Den här studien rättar inget själv.
- **Precision:** Rundatas koordinaters precision (antal decimaler) räknas och redovisas först.

**P1c. Hur många bevarade stenar står där de restes?** Tre skattningar på alla bevarade runstenar:
- **snäv:** Runor anger `original` sant och `is_moved` säger orörd;
- **huvudskattning:** `is_moved` säger orörd och Runor anger inte `original` falskt;
- **vid:** `is_moved` säger orörd.

Varje andel får Wilson-intervall och redovisas per landskap. Dessutom:
- överensstämmelsen mellan `is_moved` och Runors `original`, där Runor anger något (Cohens kappa och korstabell);
- jämförelse med Klos 2009 (28 %, enligt Stille 2015, s. 139).

Om KMR:s Fornsök-poster för runristningar hämtas med D4 (fältet `ursprungligt_lage`) används de som tredje källa. Det
är bara en robusthetsrad.

**P1d. Står de flyttade stenarna kvar i socknen (Larsson 1986, s. 99)?**
- **Urval:** P1a:s flyttningar som inte gick till museum.
- **Mått:** andelen där båda ändpunkterna har samma närmaste ISOF-sockenpunkt i samma landskap. Med histmaps:
  sockenpolygonen.
- **Robusthet:** ”inom 3 km” och ”inom 5 km”.
- **Gränser, bestämda nu:**
  - **håller:** andelen är minst 0,80 och den nedre 95 %-gränsen minst 0,70;
  - **håller inte:** den övre gränsen ligger under 0,80;
  - **obestämd:** annars.
- **Användning:** resultatet styr A2. Håller antagandet inte, räknar A2 stenarna per socken bara med orörda stenar och
  med Runors äldsta läge.

## P2. Bortfallet per jordart (konfirmatoriskt)
**Bakgrund, inte prov.** Lerkantens kontroll K1 (`utdata/palm_jordarna/kontroller.json`, 2026-11-10) gav beskrivande
andelar försvunna inom bygderutorna: lera och silt 18 %, morän 18 %, berg 18 %, sand och grus 20 %. Den räknade utan
strata och utan att skilja åsen från annan sand. Den används här bara som bakgrund.

**Urval**
- Runstenar med ett fyndläge: Runors äldsta läge, annars Rundatas koordinat.
- **Räknas bort:**
  - fyndplats vid kyrka (Rundatas plats eller placering, eller Runors plats);
  - koordinater som delas av minst tre stenar (troligen sockenpunkt eller kyrka);
  - punkter utanför SGU-täckningen;
  - punkter på vatten eller klassen övrigt.

  Antalet i varje steg redovisas.

**Utfall:** försvunnen (Rundatas `flags.lost`).

**Förklaring:** jordklassen under fyndläget.
- Referens: morän och berg tillsammans.
- Kontraster:
  - **lera** (lera och silt) mot referensen;
  - **ås** (isälvssediment) mot referensen.
- Sand, torv och gyttja ingår i modellen men prövas inte.

**Modell och nollmodell**
- Villkorad logistisk regression (`survival::clogit`) med häradet som stratum (Runors `hundred`, annars Rundatas
  `district`). Det betyder att stenar jämförs bara med stenar i samma härad. Strata utan variation i utfallet faller
  bort, och antalet redovisas.
- p-värdet för varje kontrast kommer från 9 999 omblandningar av försvunnen-flaggan mellan stenarna inom häradet
  (slumpfrö 2026), ensidigt mot oddskvot > 1. Litteraturen säger att plogen tog stenar på leran och täkterna på åsarna.

**Gränser, bestämda nu**
- **Större bortfall på X:** oddskvoten > 1 och Holm-p < 0,05.
- **Lika bortfall:** 95 %-intervallet för oddskvoten ligger helt inom 0,67–1,5.
- **Obestämt:** annars.
- **Kan inte prövas:** färre än 20 försvunna eller färre än 20 bevarade i klassen, i strata med variation.

**Robusthet (beskrivande)**
- Rundatas koordinat i stället för Runors.
- Majoritetsjordarten inom 250 m i stället för punkten.
- Landskap i stället för härad som stratum.
- Bara stenar med B-nummer, som alla dokumenterades på 1600-talet och har varit utsatta lika länge.
- Runors `extant` falskt som utfall.
- Utan fragment.
- Med en indikator för B-nummer i modellen.
- Med kyrkstenarna inräknade (bara beskrivande, eftersom kyrkans jord inte är fyndplatsens).

Period och stilgrupp kan inte justeras för, eftersom försvunna stenar oftast saknar stilgrupp. Det skrivs ut.

**P2b (beskrivande).** Överlever ”dyrare” stenar bättre (frågelistan)? Andel försvunna efter:
- textens längd i tredjedelar (ord i normaliseringen);
- kors eller inte;
- om ornamentik är känd (stilgrupp angiven).

Allt inom landskap (standardiserat per landskap). Bara beskrivande, eftersom utfallet och förklaringen hänger ihop:
försvunna stenars text är känd bara när någon tecknade dem.

## P3. Hur många stenar – upptäcktskurvan

**Första dokumentation (beräknas ur signum och alternativa signum innan något räknas):**
- **E1, 1600-talet:** B-nummer. Bautils träsnitt ritades under Hadorphs och Peringskiölds tid och trycktes 1750 (Källström
  2022, s. 8).
- **E2, 1700-talet till 1833:** L-nummer men inget B-nummer.
- **E3, före SRI-bandet:** signum i SRI-form utan B och L. Året sätts till bandets utgivningsår enligt Källström 2022,
  s. 26. För Uppland, Småland, Västergötland och Gotland, som har flera band eller häften, används det häfte där numret
  står, när det kan avgöras; annars bandets slutår.

  | Landskap | SRI-band | År |
  |---|---|---|
  | Öland | Ölands runinskrifter | 1900–06 |
  | Östergötland | Östergötlands runinskrifter | 1911–18 |
  | Södermanland | Södermanlands runinskrifter | 1924–36 |
  | Småland | Smålands runinskrifter | 1935–61 |
  | Västergötland | Västergötlands runinskrifter | 1940–70 |
  | Uppland | Upplands runinskrifter | 1940–58 |
  | Gotland | del 1 och 2 | 1962 och 1978 |
  | Västmanland | Västmanlands runinskrifter | 1964 |
  | Närke | Närkes runinskrifter | 1975 |
  | Värmland | Värmlands runinskrifter | 1978 |
  | Gästrikland | Gästriklands runinskrifter | 1981 |

- **E4, efter bandet:** senare signum. Året är årtalet i signumet: `Fv1953;263` → 1953, `ATA4684/43` → 1943,
  `NOR1997;30A` → 1997. Signum utan årtal (83, varav 68 Öl Köping) räknas inte i kurvan och redovisas för sig. Köping
  är en enda utgrävning med fragment ur stenkistor (Jansson 1954, s. 87).
- **Utan SRI-band:** Hälsingland, Medelpad, Jämtland, Dalarna och Bohuslän räknas inte i kurvan och redovisas för sig.
  Norrlands utgåvor saknas (Källström 2022, s. 10).
- **Runor-stenar som saknas i Rundata:** räknas in med årtalet i signumet.

**P3a. Har upptäckterna planat ut? (konfirmatoriskt)**
- **Utfall:** antalet nya stenar i E4 per landskap och decennium efter bandets slutår.
- **Modell:** Poissonregression med landskapet som fast effekt, decennier sedan bandet som linjär term, och log(antal
  år av decenniet som ligger i fönstret) som offset.
- **Huvudfönster:** till och med 2003. Därefter finns ingen årlig fyndpublicering (Källström 2022, s. 20), och senare
  fynd kan saknas i Rundata och Runor.
- **Planar ut:** lutningen < 0 med Holm-p < 0,05 (ensidigt). Överspridning prövas, och vid kvot > 1,5 används
  negativ binomial.
- **Robusthet:** fönster till 2019; bara Uppland och Södermanland; utan fragment.

**P3b. Hur många okända stenar finns kvar att hitta? (skattning)**
- **Modell:** en uttagsmodell (removal/depletion, Zippin), som är fångst–återfångst för successiva uttag. Varje
  decennium hittar en andel p av de stenar som ännu inte hittats. Den gemensamma p skattas över landskapen, och ett
  N_kvar per landskap. Det ger antalet stenar som fanns att hitta vid bandets utgivning och som ännu inte hittats.
- **Intervall:** parametrisk bootstrap (2 000, slumpfrö 2026).
- **Robusthet:** p per landskap, där minst tre decennier har minst fem fynd.
- **Antagandet:** lika stor chans att hittas varje decennium. Det är svagt, eftersom fynden kommer i skurar vid
  kyrkrestaureringar och utgrävningar. Det skrivs ut, och skattningen redovisas som storleksordning.

**P3c. De återfunna stenarna som fångst och återfångst (skattning, villkorad)**
- **Märkta (M):** stenar dokumenterade före bandet som räknades som försvunna vid bandets utgivning. Det är de nu
  försvunna plus de som återfunnits efter bandets år.
- **Återfångade (m):** de återfunna, enligt årtal i Rundatas anmärkning eller Runors noter. Kodningen görs med en regel
  (”återfunn-”, ”återfann-” eller ”återupptäck-” med ett årtal efter bandets år), och listan skrivs innan skattningen
  räknas.
- **Fångade efter bandet (C):** alla nya stenar efter bandet (E4) plus m.
- **Skattning:** Lincoln–Petersen N̂ = M·C/m, med Chapmans korrektion och intervall.
- **Villkor:** räknas bara om m ≥ 20.
- **Antaganden, som skrivs ut:**
  - kända försvunna och aldrig kända stenar har samma chans att dyka upp;
  - eftersökning av kända stenar höjer m och ger för låg N̂;
  - stenar som förstörts helt sänker m och ger för hög N̂;
  - fritexten missar återfynd, vilket också ger för hög N̂.

**P3d. Klassisk fångst–återfångst över inventeringarna (villkorad)**
- **Varför den inte är huvudmodell:** Bautil, Liljegren, SRI och Runor är inte oberoende fångster. Varje senare utgåva tar
  upp allt som var känt före den. Liljegren translittererar alla då kända inskrifter (Källström 2022, s. 7), och SRI tar
  med också försvunna stenar ur äldre källor.
- **Kontroll som görs först:** hur stor andel av stenarna med B-nummer saknar L-nummer.
- **Villkor:** är andelen minst 10 %, är listorna delvis oberoende. Då skattas den synliga stenmängden 1600–1833 med en
  log-linjär modell med B×L-samspel (R-paketet Rcapture, installeras då). Den redovisas som en nedre gräns. Annars görs
  P3d inte, och skälet skrivs ut.

**Tolkning av P3 (bestämd nu)**
- Svaret på ”hur många som restes” är en **nedre gräns**: kända stenar (också försvunna) plus det skattade dolda lagret.
- Stenar som förstördes före 1600-talet syns inte i någon av metoderna. Därför kan Stilles ”åtminstone dubbelt så
  många” varken bekräftas eller avvisas med dessa data, bara jämföras med den nedre gränsen.
- **Bilden är mättad i ett landskap** om P3a planar ut och P3b:s skattade återstod är under 10 % av de kända stenarna.

## P4. Kyrkstenarna (konfirmatoriskt, två prov)

**Definitioner**
- **Kyrksten:** runsten vars plats eller placering i Rundata nämner kyrka, kapell, kyrkogård eller bogård, och som
  `is_moved` räknar som flyttad.
- **Orörd:** inte flyttad och inte försvunnen.

**P4a. Hämtades stenarna från ristarens vanliga trakt?**
- **Urval:**
  - stenar med säker ristare (signerade eller tillskrivna utan frågetecken) som har minst två orörda stenar;
  - kyrkstenar och orörda stenar av samma ristare.
- **Mått:** för varje sådan sten i, D_i = avståndet till närmaste orörda sten av samma ristare, utom stenen själv. För en
  kyrksten är det kyrkans läge.
- **Statistik:** T = medel av log D över kyrkstenarna minus medel av log D över de orörda, vägt per ristare.
- **Nollmodell:** etiketterna kyrksten och orörd blandas om inom varje ristare, 9 999 gånger (slumpfrö 2026). Det
  motsvarar att kyrkans läge vore utbytbart mot ett läge där ristaren annars ställde stenar.
- **Prov:** ensidigt mot T > 0, alltså att stenarna fördes längre än ristarens vanliga spridning.
- **Gränser, bestämda nu:**
  - **Längre transporter:** T > 0 med Holm-p < 0,05.
  - **Nära-antagandet stöds:** exp(T) har en övre 95 %-gräns på högst 1,5, alltså högst 50 % längre än ristarens vanliga
    avstånd mellan stenar.
  - **Obestämt:** annars.
  - **Kan inte prövas:** färre än 30 kyrkstenar.
- **Robusthet:**
  - bara signerade stenar, eftersom tillskrivningar ibland bygger på närhet och då gör provet cirkulärt;
  - ristare med minst fem orörda stenar;
  - bara Uppland;
  - de orörda utan Runors `original` falskt.

**P4b. Är stenarna vid kyrkorna yngre (Herschend 2017, s. 11)?**
- **Urval:** stenar med säker stilgrupp, kyrkstenar mot orörda.
- **Utfall:** stilgruppens mittår enligt Gräslunds dateringar i `src/styles.py`. KB saknar datering där och räknas bort
  (30 stenar med säker stilgrupp); antalet redovisas.
- **Mått:** Mann–Whitney-statistik stratifierad per landskap.
- **Nollmodell:** stilgrupperna blandas om mellan stenarna inom landskapet, 9 999 gånger.
- **Prov:** ensidigt mot att kyrkstenarna är yngre.
- **Gräns:** **yngre** om Holm-p < 0,05. Andelen Pr4–Pr5 i båda grupperna redovisas.
- **Tolkning:** ett ja stämmer med att en del stenar restes vid kyrkplatsen eller flyttades dit när kyrkan byggdes. Det
  avgör inte vilket.

**P4c (beskrivande).** Hur stor andel av socknarna har minst en runsten vid kyrkan, per landskap? Jämförs med Stilles
10 % för Tiohärad (Stille 2015, s. 141).

## P5. Spökstenar och dubbletter (konfirmatoriskt)
**Urval:** runstenar med minst 10 runor i translittereringen. Med de 415 försvunna blir det 332 försvunna.

**Kandidatpar.** Två stenar högst 15 km från varandra som uppfyller båda villkoren:
- **Länkade enligt släktnätverkets regel** (`src/linking.links`): de delar minst två personnamn eller ett gårdsnamn,
  minst ett delat namn står på högst 60 runstenar, och de har IDF-vikter.
- **Textlika:** likheten i translittereringen (1 − normaliserat Levenshteinavstånd på runföljden utan skiljetecken och
  parenteser, räknat på den kortare textens längd) ligger över τ.
  - τ = 99:e percentilen av likheten bland **länkade par av två bevarade stenar** i samma avståndsband (under 2 km,
    2–10 km och 10–15 km).
  - Bevarade stenar är verkligen olika stenar. τ skiljer alltså nästan likadana texter från släktstenar som bara delar
    namn och formler.

**Prov.**
- Andelen försvunna stenar som har en kandidatpartner, bevarad eller försvunnen, mot andelen bevarade stenar som har en
  bevarad kandidatpartner.
- Stratifierat per landskap (Cochran–Mantel–Haenszel). p-värdet kommer från 9 999 omblandningar av försvunnen-flaggan
  inom landskapet, ensidigt.
- **Gräns:** **fler dubbletter bland de försvunna** om oddskvoten > 1 med Holm-p < 0,05.
- **Skattning:** överskottet, alltså observerade minus väntade försvunna med partner, med intervall. Det är det skattade
  antalet spökstenar och dubbletter bland de försvunna som har text.

**Positiv kontroll.** Lerche Nielsens par som Rundata ännu inte slagit ihop: Ög 191 och Ög 157, och Ög 195 och Ög 157.
- Regeln ska fånga minst ett av dem. Gör den inte det är metoden för okänslig, och P5 redovisas som ”kan inte prövas
  med textlikhet”.
- U 199, U 234 och U 981 är redan sammanslagna i Rundata och kan inte användas.
- Ög 158† och Ög 159† har ingen text och syns inte med den här metoden. Det skrivs ut.

**Robusthet:**
- τ = 95:e och 99,5:e percentilen;
- 5 km och 30 km;
- bara Uppland, där Lerche Nielsen väntar flest dubbletter (2010, s. 240).

**Granskning.** Kandidatlistan skrivs i `utdata/flyttade/dubblettkandidater.csv`. Viktor granskar paren efter körningen,
men provet och skattningen ovan avgörs utan granskningen. Ingen egen läsning av inskrifterna görs.

**P5b (beskrivande).** Hur många signum som redan slagits ihop i Rundata (”förd(a) hit”, ”samma sten”), per landskap.

## Vad som INTE får göras
- Inga nya mått, avståndsband eller jordklasser efter att resultaten setts.
- Inga delurval utöver robusthetsraderna ovan.
- Flyttfiltret (`is_moved`) ändras inte i den här studien. Föreslår resultatet en ändring skrivs den som ett förslag
  till Viktor, eftersom den flyttar alla platsresultat.
- Ingen egen läsning av inskrifter, och ingen bedömning av om ett kandidatpar ”verkligen” är samma sten i
  resultatet.
- Rapporten och artiklarna skrivs först efter körningen (skriv-i-förväg-regeln).

## Tolkning (bestämd nu)
**P1**
- **P1b når gränsen:** platsstudierna står på rätt lägen, och det skrivs i rapporten.
- **P1b når inte gränsen:** rapporten listar vilka resultat som måste köras om med Runors läge. Inget rättas förrän den
  kontrollen är körd.
- **P1d håller inte:** Larssons antagande om socknen kan inte bära stenar som flyttats efter att de dokumenterades.
  A2 räknar då socknar med orörda stenar.

**P2**
- **Större bortfall på lera:** kartans brist på stenar *på* leran (lerkanten) kan delvis vara bortfall. Lerartikeln
  och rapporten får ett tillägg med storleken. K1 räknade redan om kanten med de försvunna stenarna, och det tillägget
  står kvar.
- **Större bortfall på åsar:** stenar vid åsar och sand är underrepresenterade. Det skrivs in i vägresultatet, eftersom
  åsarna var vägar.
- **Lika bortfall:** bortfallet förklarar inte mönstret på kartan. Det stärker platsstudierna och skrivs ut.
- **Obestämt:** det skrivs som obestämt, inte som ”lika”.

**P3**
- **Utplanad kurva:** artikeln kan säga att bilden i landskapet är nära mättad för stenar som stått synliga.
- **Inte utplanad:** artikeln säger hur många nya stenar per decennium som väntas.
- **I båda fallen:** stenar som förstördes före 1600 syns inte i några data.

**P4**
- **P4a längre transporter:** kyrkstenarnas läge får inte användas som ungefärlig fyndplats på sockennivå utan
  förbehåll.
- **P4a nära-antagandet stöds:** kyrkans läge är en rimlig ersättning för fyndplatsen på ristarens skala. Det skrivs
  som stöd för Jansson 1955, Svärdström 1970 och Stille 2015, med Brunna (Jansson 1946) som undantaget.
- **P4b:** avgör bara om ”stod de där redan” får nämnas som möjligt för de sena stenarna.

**P5**
- **Ja:** antalet försvunna stenar, och kartor över försvunna stenar, ska läsas med det skattade överskottet som
  osäkerhet. Kandidatlistan går till Viktor.
- **Nej:** de försvunna stenarna med text är inte fler dubbletter än slumpen och släktskapen ger.

**Artiklarna**
- ”Stenarna som plogen och grustaget tog” (12 jan) skrivs bara om P2 ger *större* eller *lika* bortfall. Vid lika
  bortfall ändras vinkeln till att plogen tog lika mycket överallt. Vid obestämt bortfall byts artikeln mot ett utkast
  ur avsnitt 4 i publiceringsplanen.
- ”Hur långt flyttades runstenarna?” (26 jan) bygger på P1 och P4 och skrivs oavsett utfall, eftersom skattningar inte
  kan ”falla”.
- Rapporten ”Stenarna som flyttades och försvann” (26 jan) redovisar allt, också nollresultat.

## Redovisning
Allt i `utdata/flyttade/`:
- `data.py`: stenar, Runorkoppling, epoker, kyrkstenar och fasta ristningar → `stenar.csv`, med korpusens hash;
- `destination_klasser.csv` och `epoker.csv`, skrivna innan något räknas;
- skripten per fråga:
  - `flytt.py` (P1);
  - `jordarter_punkt.py` och `bortfall.R` (P2);
  - `upptackt.py` och `upptackt.R` (P3);
  - `kyrkstenar.py` (P4);
  - `dubbletter.py` (P5) och `dubblettkandidater.csv`;
- `resultat.json` och `resultat.md` (med planens sha256);
- figurerna: flyttsträckor, upptäcktskurvor per landskap och karta över bortfall per jordart.

**Rapport och artiklar**
- Rapport på Zenodo enligt MALL.md, med Scholar-taggar, PDF på webbplatsen och data som eget dataset med DOI.
- Utfallen förs in i rapporten och artiklarna först när Viktor har sett dem.

**Minne och körning (16 GB-Macen):** allt är små tabeller (under 10 000 rader). Det enda tunga steget är uppslagningen i
SGU:s vektorer, som görs ett län i taget som ett ensamt jobb. Inga parallella jobb.
