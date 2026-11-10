# Vad svensk runforskning har missat – syntes av litteraturgenomgången

Arbetsdokument, 10 november 2026. Underlag: `fynd2/` (läsningarna), `pastaenden.jsonl` (de mätbara påståendena),
`FORSKNINGSIDEER.md` (alla idéer per tema), `blindflackar.json` (räkningen nedan), `kontroll/` (stickprovskontrollen).

## 1. Vad vi gjorde

Vi har läst 1 577 texter ur Fornvännen (1906–2023) och Futhark (alla nummer) med samma frågor till alla: vad påstår
texten som går att mäta mot Vitkis data, vad har den svenska runforskningen missat (perspektiv, antaganden, urval, metoder,
källor), och vad saknar Vitki? Läsningen gick i tre nivåer:

- **Runtexterna:** alla texter med runsignum eller runord, 482 texter.
- **De närliggande disciplinerna:** arkeologi, ortnamn, historia, konsthistoria och numismatik om vikingatid och tidig
  medeltid, 597 texter.
- **Resten av Fornvännen:** de texter som nämner perioden eller dess ämnen minst två gånger, 497 texter.

Kvar oläst är omkring 2 000 Fornvännen-texter om stenålder, bronsålder och senare konsthistoria utan koppling till perioden.

Ur läsningen kom:
- **4 555 påståenden som går att mäta**, med ordagrant citat och förslag på mätning; 1 244 av dem har prioritet 1;
- **2 241 idéer** till artiklar och rapporter.

**Täckning.** Kontrollerad i sökindexet (`sok.sqlite`, 3 674 texter): bara 14 olästa texter nämner två eller fler runsignum. Elva av dem är Futharks helvolymer, vars artiklar är lästa var för sig; de tre andra är ett register, en notis om en målare och en notis om plundring. En känd lucka finns: korta runnotiser som delar OCR-fil med en annan artikel (t.ex. Alsike 1948) lästes inte, eftersom läsarna bara läste den del som hörde till postens titel.

Varje citat är maskinellt kontrollerat mot källtexten. Om läsningen i övrigt stämmer prövas i ett stickprov (avsnitt 2).

## 2. Hur säkra är läsningarna?

**Stickprovskontrollen** (`kontroll/`, 10 november). Två oberoende kontrollanter granskade 30 slumpvis valda läsningar
mot originaltexten: 12 runtexter, 9 grannämnen och 9 ur tredje nivån.

- **Helhetsbetyg:**
  - 9 läsningar *goda*, 30 %;
  - 21 *användbara med förbehåll*, 70 %;
  - ingen *opålitlig*.
- **Sammanfattningarna:** pålitliga, med inga allvarliga fel.
- **Påståendena:** i del A bedömdes alla 118.
  - 90 är rätt, 76 %;
  - 18 är överdrivna, 15 %;
  - 6 har sakfel i detaljer, 5 %, till exempel fel signum eller fel fyndort;
  - 4 är läsarens egna slutsatser utan märkning, 3 %.
- **Mätförslagen med prioritet 1:** i del B höll 4 helt och 3 delvis. I del A överskattade några underlaget eller hur
  oberoende testet var.

**De systematiska felen:**
1. Blinda fläckar som är läsarens egna presenteras som textens, med ett citat om något annat som skenbart belägg. Det
   finns i nästan alla läsningar, och ibland säger texten emot. Wessén 1952 använder till exempel just de oberoende fasta
   punkter som läsaren påstår saknas.
2. Försiktiga formuleringar försvinner: ”låt oss anta”, ”perhaps”, ”övervägande sannolik”.
3. Enstaka fall generaliseras.
4. Enstaka påhittade uppgifter finns i fritextfälten (”hur”, ”följd”, ”utöver författaren”): verk, namn och tillskrivningar
   som inte står i texten. Citatkontrollen fångar inte dessa.

**Vad det betyder för användningen:**
- Påståendena och citaten är en god karta: tre av fyra stämmer, och resten pekar åt rätt håll.
- Inget påstående används i en studie eller artikel utan att det har kontrollerats mot originaltexten. Det är lätt, eftersom
  varje påstående har nyckel och ordagrant citat.
- De blinda fläckarna och fritextfälten är läsarnas bedömningar, inte författarnas ståndpunkter, och redovisas så.
- För de påståenden som går in i planerna A–F märks varje blind fläck ”text”, ”läsare” eller ”båda”, och egennamn, verk och
  siffror i fritextfälten kontrolleras maskinellt mot källtexten.

**Viktigt för hur siffrorna nedan ska läsas.** Läsarna hade samma underlag, med en lista över Vitkis data och frågor.
Räkningen mäter därför hur ofta en läsare fann en blind fläck relevant för en text. Det är inte detsamma som hur ofta
författaren själv tog upp den. En hög siffra betyder att frågan berör stora delar av litteraturen. Den betyder inte att
författarna klagade på den. Där det är författarnas egen kritik säger vi det och citerar.

## 3. De återkommande blinda fläckarna

Antal olika texter där läsaren tog upp fläcken, av 1 577, och spannet av år. Hela listan finns i `blindflackar.json`.

| # | Blind fläck | Texter | Andel | År |
|---|---|---|---|---|
| 1 | Placeringar prövas inte mot slumpen | 1 004 | 64 % | 1906–2025 |
| 2 | Dateringen är cirkulär: stilgrupper utan oberoende fasta punkter | 883 | 56 % | 1906–2025 |
| 3 | Bevarande och bortfall styr vilka stenar vi känner | 674 | 43 % | 1906–2025 |
| 4 | Flyttade, inmurade och återresta stenar | 658 | 42 % | 1906–2025 |
| 5 | Gravhällar, medeltida runor och lösföremål används inte | 521 | 33 % | 1906–2025 |
| 6 | Skattfynd, mynt och silver används inte | 516 | 33 % | 1906–2022 |
| 7 | Kvinnor och barn | 436 | 28 % | 1906–2025 |
| 8 | Stenens bergart och proveniens | 370 | 24 % | 1906–2025 |
| 9 | Korset läses som tro utan prövning; korstypologin oanvänd | 314 | 20 % | 1907–2022 |
| 10 | Stenarna läses som befolkning eller rikedom utan nämnare | 283 | 18 % | 1906–2024 |
| 11 | Ristartillskrivning utan basfrekvens | 272 | 17 % | 1906–2024 |
| 12 | Naturvetenskapliga metoder (isotoper, DNA, pollen, fosfat, LiDAR) | 240 | 15 % | 1909–2024 |
| 13 | Utgivare, antikvarier och dokumentationshistoria | 216 | 14 % | 1906–2025 |
| 14 | Sena källor (sagor, lagar, Adam av Bremen) som facit | 202 | 13 % | 1909–2022 |
| 15 | Forskarnas uppmärksamhet är ojämn | 200 | 13 % | 1906–2025 |
| 16 | Centralortsnamnen (Husby, Tuna, Hov) är oprövade | 189 | 12 % | 1906–2022 |
| 17 | Gravfältens ålder och samtidighet med stenen | 186 | 12 % | 1906–2025 |
| 18 | Norrland, samer och periferin | 181 | 11 % | 1906–2025 |
| 19 | Strandlinje, landhöjning och vattennivå | 165 | 10 % | 1906–2022 |
| 20 | Kyrkornas ålder: träkyrkor syns inte | 157 | 10 % | 1907–2022 |
| 21 | Fornminnesregistrets täckning är ojämn | 154 | 10 % | 1906–2024 |
| 22 | Vägarnas ålder och vintervägar | 135 | 9 % | 1908–2022 |
| 23 | Tingsplatserna är oprövade | 113 | 7 % | 1912–2024 |
| 24 | De ofria, tjänstefolket och hushållet saknas | 96 | 6 % | 1910–2025 |
| 25 | Uppland och Mälardalen som norm | 91 | 6 % | 1906–2025 |
| 26 | Socken-, härads- och landskapsgränser är yngre än stenarna | 81 | 5 % | 1913–2024 |
| 27 | Färg och ommålning | 67 | 4 % | 1907–2022 |
| 28 | Regional eftersläpning i stil och kristnande | 38 | 2 % | 1917–2021 |

Alla de stora fläckarna finns i varje decennium från 1900-talets början till i dag. Det är huvudfyndet. Det är inte nya
frågor som har dykt upp; det är gamla frågor som aldrig har prövats på hela materialet.

### De fem som bär mest

1. **Placeringar utan slumpjämförelse.** Påståenden som ”vid vägen”, ”vid gravfältet”, ”vid bron”, ”vid tinget”, ”vid
   leran”, ”vid vattnet” och ”vid kyrkan” bygger nästan alltid på exempel. Ett test mot slumpvis valda platser i samma bygd
   görs nästan aldrig. Det är Vitkis starkaste metodbidrag och kan göras för alla påståendena på en gång.
2. **Cirkulär datering.** *(Obs. Många läsare föreslog Runor 2020:s termini som oberoende datering, men i vår skörd är tpq oftast schablonvärdet 725 eller en stildatering – fältet är inte oberoende. Dateringsplanen bygger därför på historiskt daterade ankarstenar och språkdrag.)* Stilgrupperna daterar stenarna, stenarna daterar metallföremålen, och metallföremålen daterar
   stilgrupperna.
   - Fasta punkter som hänger på en enda saga: Ingvar 1041, som Thulin 1985 kallar ”den fastaste punkten” i Upplands
     runstenskronologi.
   - Konsthistoriska dateringar som har vänts av dendrokronologin: Gotlands kyrkor och Wases tabell från 1995.
   - Mätbart nu: fasta punkter per stilgrupp; stilgrupp mot Runor 2020:s termini och profilstil; Ingvar ±10 år;
     språkdrag (monoftongering) som oberoende klocka.
3. **Bevarande och bortfall.**
   - Stenar på åker sprängdes bort, till exempel vid Alvastra.
   - Stenar på grus och åsar försvann i grustäkter och vid vägbyggen.
   - Stenar murades in i kyrkor; 1600-talets antikvarier valde vilka som kom med, och nya fynd görs fortfarande, som
     Alsike 1947.
   - Mätbart nu: borttappade, flyttade och fragmentariska stenar per jordart åt båda hållen (lera och sand/ås); en
     upptäcktskurva per landskap ur året för första dokumentation; fångst–återfångst över inventeringarna.
4. **Flyttade och inmurade stenar.**
   - Vitki har redan rättat flyttfiltret: omkring 420 kyrkstenar räknades som ”in situ”.
   - Läsningarna lägger till: inmurade stenar ger en senaste möjliga datering (terminus ante quem) när kyrkan är daterad;
     restaurering och återresning ändrar stenens riktning; tradition om platsen är inte ett belägg.
5. **Föremål utanför runstenarna.**
   - Runor 2020 har 7 189 inskrifter mot omkring 2 300 runstenar, bland dem 260 gravhällar, 139 mynt och lösa föremål.
   - Frågan om bönen flyttade från stenarna till gravhällarna har aldrig prövats.
   - Allt sådant redovisas alltid separat (Vitkis regel).

### Data som saknas och som många påståenden väntar på

- **Ett skattfyndsregister med koordinater.** Det nämns i över 500 texter och är den största enskilda luckan. Möjliga
  källor är SHM via K-samsök, Myntkabinettet och CNS.
- **Kyrkornas byggår och dendrodateringar.** De ger terminus ante quem för inmurade stenar.
- **SGU:s berggrundskarta.** Den behövs för stenens proveniens och transportsträcka.
- **ISOF:s centralortsnamn och tingsnamn.** Det gäller Husby, Tuna, Hov, Ting- och -vi. Vi har kultnamnen men inte dessa.
- **Socken- och häradsgränsernas ålder samt hundare- och ledungskartor.**
- **Höjdmodell och vattendrag**, för strandlinje per sten och för vadställen.
- **Fosfatkartor och 1600-talets bykartor**, för var gårdarna låg.

## 4. Kontroller av Vitkis egna resultat (görs innan resultaten används igen)

| Resultat | Kontroll | Varifrån |
|---|---|---|
| 66 % av platserna österut (publicerat; 68 % var det äldre träffmåttet) | **Körd 2026-11-10:** utan de 25 Ingvarsstenarna 58 % (49–67) = försvagat; ingen förskjutning mot väster över tid (för få sena stenar för en dom). `utdata/varlden/sjalvkontroll/` | Sindbæk 2003, Westin 1941 |
| 64 % inom 500 m från vattnet 1050 | Mot äldre fornlämningar vid sin tids strand; strandlinjen ±1–3 m; stenens egen datering; sjösänkningar | Stenberger 1942, Calissendorff 1991, Lindqvist 1928, Edberg |
| Stenar och gravfält vid lerans kant | Bortfall åt båda hållen (lera/sand, åsar); åsvägar; hävd och äng; flyttade gårdar; Malmers dos–respons (dyrare stenar på bättre jord) | Söderberg, Lovén, Myrdal 1982, Göransson, Malmer 1988, Arrhenius 1950 |
| Gravfält 82 mot 55 % | Bara daterade och verifierade gravar; gravfältets ålder; KMR:s inventeringsår per län; boplatser i stället för gravar | Häggström 2002, Ambrosiani 1968, Holmqvist 1957 |
| Texten vänder sig mot vägen | Bara vägar som fanns före 1100; återresta stenar bort; jämförelse inom län (vägarna inventerades efter 1943 års lag) | Skoglund & Lagerås 2002, 1941 års restaureringar, 1944_111 |
| Kultnamn och bön; avstånd till kyrkor | Träkyrkor syns inte; stenkyrkor dendrodaterade till omkring 1190–1225 | Frödin 1932, 2016_097 |
| Allt som bygger på ”1314 års sexårsgärd” | Kontrollera listan: för Strängnäs stift kan den vara 1279–82 | Gillingstam 1980 |
| Alla regionala jämförelser | Hur Rundatas fält är fyllda per landskap och dokumentationsår; om 3D-skanningarna är representativa | fvn_050 |

## 5. Nya spår ur läsningen

1. **Tingsplatserna.** Stenarnas avstånd till tingsplatser: KMR, ISOF:s Ting-namn och SDHK. Tagit upp av minst fyra
   oberoende källor, bland dem Nordén 1938 (Arkel) och Wildte 1926.
2. **Husby, Tuna och Hov** mot slumpen inom bygden. Varje text som tog upp det testade bara en plats.
3. **Högar och stenar.** Ersatte stenarna högarna, eller hamnade de på samma ställen? Socken för socken.
4. **Hushållet.** Ett hushåll var 7–10 personer med tjänstefolk och trälar, enligt Ringstedt 1989. Räkna hur många
   personer som nämns per sten, deras relationer, och orden för personer utanför familjen.
5. **Kvinnornas rörlighet.** Är kvinnonamnen mindre typiska för regionen än mansnamnen?
6. **Gränser som inte är landskapens.**
   - Kolmården mellan Mälardalen och Sydsverige.
   - Sagån och Fjädrundaland, efter Nerman 1963.
   - Svear mot götar som en gradient över 1000–1150, för att se när riket slogs ihop.
7. **Kossinnatestet.** Sammanfaller gränserna för stil, språk, formler, namn och kors, eller är det olika kartor?
8. **Vad en sten kostade.** Landskapslagarnas öre kombinerat med huggvolymen i 3D, och ett monumentindex.
9. **Vintervägar** över is och myr, som inte syns i KMR.
10. **Utgivarna och forskarnas uppmärksamhet.**
    - Följer läsningar och tillskrivningar SRI-bandet och utgivaren?
    - Litteraturhänvisningar per sten: 4 141 i Runor 2020.
    - Är det ”typiska” bara det mest beskrivna?

## 6. Förslag: de första låsta analysplanerna

Varje plan låses med sha256 och commit innan något räknas. Ordningen är ett förslag; de två första skyddar resten.

1. **Bevarandeplanen (A).**
   - Bortfall per jordart åt båda hållen.
   - Upptäcktskurva per landskap.
   - Fångst–återfångst över inventeringarna.
   - Fältfyllnad per landskap.
   - Ger korrektionen som de andra planerna använder.
2. **Självkontrollplanen (B).** Kontrollerna i avsnitt 4, i den ordningen. Varje resultat som inte håller rättas i
   artikeln och i IMPLEMENTATIONSPLAN.md (Vitkis regel).
3. **Dateringsplanen (C).**
   - Fasta punkter per stilgrupp.
   - Rundatas stilgrupp mot Runor 2020:s termini och profilstil (kappa).
   - Ingvar ±10 år.
   - Monoftongering som oberoende klocka.
   - Regional eftersläpning.
4. **Placeringsplanen (D).** Ett gemensamt slumptest inom bygd, med KMR:s inventeringsår som kontroll, för:
   - gravfält (bara daterade);
   - vägar (bara gamla);
   - bro och vad;
   - ting;
   - Husby, Tuna och Hov;
   - hällristningar;
   - högar.
5. **Kors- och bönplanen (E).**
   - Kors utan kristen text.
   - Korstyp öst mot väst mot färdriktning.
   - Konsekvens inom släkten.
   - Signatur och bön.
   - Ett kristnande som våg från Danmark, Sigtuna eller biskopssätena.
6. **Människoplanen (F).**
   - Hushåll och ofria.
   - Kvinnors rörlighet genom namn.
   - Ord för personer utanför familjen (félagi, drengr, gildi).

## 7. Rapporten

**Vad svensk runforskning har missat.** En forskningsrapport i Vitkis serie, med en ny version på Zenodo när
planerna A–C är gjorda:

1. Metod.
2. Läsarkontroll.
3. Fläckarna med antal och citat.
4. Kontrollerna av Vitkis egna resultat, också de som inte håller.
5. De första testade påståendena.
6. Påståendedatabasen öppet.

Vi tackar föregångarna: Palm 1992, Larsson 1999, Sawyer 2000 och Källström.
