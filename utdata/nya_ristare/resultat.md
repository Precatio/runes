# Nya ristare – resultat 2026-11-23

Planer: `analysplaner/2026-11-23-nya-ristare-program.md` (sha f5ce4fe7) och `…-slutprov-1.md` (sha 081bf667, låst i 69c148d
innan provdelen öppnades). Korpus 510ebfb3.

## 1. Facit
- **Underlaget:** 225 ställen i SRI:s textband där utgivaren talar om "samme ristare", "samma hand" eller "samme mästare",
  och Runor 2020:s "samma som gjort X".
- **Utläsningen:** SRI-ställena lästes av två instanser av Anthropics språkmodell Claude (Claude Opus), en för varje halva.
- **Kontrollen:**
  - en tredje instans läste om 40 ställen och stämde i 30 (75 %), under kravet 85 %;
  - enligt planen lästes därför alla ställen om av nya instanser med en striktare regel (bara signum som står i texten), och
    det stämde i 194 av 225 ställen (86 %);
  - de 62 omstridda paren avgjordes för hand (motiveringar i `data/cache/hander/sri_avgorande_motiv.json`, utanför git).
  - De flesta oenigheterna gällde signum som en läsare hade räknat ut ur ortnamn eller Liljegrens nummer, och var ett
    yttrande hörde hemma vid artikelgränser.
- **Facit:** 409 länkar (Runor 2020: 230, SRI: 179), 118 grupper (84 par och 34 större grupper).
  - Delningen, med grupperna som enheter (frö 20261123): 59 grupper för utveckling (U), 59 för prov (P).
  - Dessutom 37 möjliga länkar, 27 avvisade och 23 där bara en annan forskare uttalar sig. De ingår inte i grupperna.

## 2. Beläggen per stenpar (`belagg.py`)
- **Stenarna:** 2 314 stenar och 312 550 stenpar inom 30 km.
- **Täckningen per belägg** (andel av paren):

  | Belägg | Andel av paren |
  |---|---|
  | Kortkvist | 100 % |
  | Bergart | 63 % |
  | Gemensamma namn | 57 % |
  | Skiljetecken (lika/olika) | 54 % |
  | Textdragens överskott | 46 % |
  | Preposition (*eftir*/*at*) | 45 % |
  | Korsets form (Lager, Runor 2020) | 23 % |
  | Stilgrupp | 22 % |
  | SRI:s runformsord | 12 % |
  | SRI:s ornamentord | 9 % |
- **Ett fel i de tidigare proven, upptäckt här:** de kategoriska språkdragen (skiljetecken, *eftir*/*þenna*-stavning,
  *ai*, *auk* …) är text i korpusen och blev noll när likheten räknades i `utdata/nya_hander`, `oppen_modell` och
  `stenar_som_hor_ihop`. Skiljetecknet var ändå den viktigaste variabeln i ristarmodellen K0. Här jämförs de som lika eller
  olika.

## 3. Parmodellen (utvecklingsdelen, `parmodell.py`)
- **Träningen:** gradient boosting på 41 192 par av säkra stenar (5 400 med samma ristare), med ristarna delade i fem vikter.
  Par inom facitgrupper och par som rör provdelens stenar ingår inte.
- **Måttet:** var runologernas partner hamnar bland alla stenar på samma avstånd. Percentil 1 betyder överst.

| Modell | AUC namngivna | Utvecklingsgrupper | Median | Andel ≥ 0,9 | Onämnda: grupper | Onämnda: median |
|---|---|---|---|---|---|---|
| M0 bara textdragens överskott | – | 17 | 0,83 | 24 % | 2 | 0,54 |
| **M1 alla belägg** | 0,76 | 27 | **0,94** | 59 % | 8 | **0,95** |
| M2 utan text | 0,72 | 27 | 0,90 | 48 % | 8 | 0,89 |
| M3 text + stil + kors | 0,77 | 27 | 0,90 | 52 % | 8 | 0,81 |
| M5 alla belägg, bara signerade | 0,66 | 27 | 0,66 | 30 % | 8 | 0,42 |

- **De gemensamma namnen** tillförde inget (före och efter: 0,90).
- **Lyftet från 0,90 till 0,94** kom från de kategoriska språkdragen.
- **Modellen tränad bara på signerade stenar** har för lite underlag.

## 4. Grupperna (`gruppering.py`)
**Metoden:** genomsnittlig länkning på M1:s sannolikheter, diameter ≤ 30 km.

| τ | Precision namngivna | Facitpar i samma grupp | Grannar i samma grupp | Grupper ≥ 3 |
|---|---|---|---|---|
| 0,9 | 0,85 | 21 % | 0,7 % | 106 |
| **0,8** | **0,77** | **34 %** | **2,9 %** | **228** |
| 0,7 | 0,69 | 40 % | 9,7 % | 293 |
| 0,6 | 0,58 | 47 % | 14,6 % | 240 |

τ = 0,8 valdes på utvecklingsdelen.

## 5. Slutprov 1 (provdelen, öppnad en gång): **håller**

| | Grupper | I samma grupp | Kontrollen | Median | Bättre / sämre | p |
|---|---|---|---|---|---|---|
| **S1 alla** | 42 | 0,42 | 0,07 | 0,10 | 23 / 8 | 0,00002 |
| **S2 onämnda händer** | 15 | 0,69 | 0,075 | 0,80 | 11 / 3 | 0,002 |

Det här är första gången en metod hittar runologernas händer, och särskilt de onämnda, långt oftare än grannstenarna på
samma avstånd. Vid samma prov höll tidigare inte de täta kärnorna (8 november), den öppna modellen och dagens första
kärnor.

## 6. Grupperna på hela korpusen (`grupper.json`)
- **Antal:** 228 grupper med minst tre stenar, 1 103 stenar.
- **Typerna:**
  - 95 *okänd hand*, där ingen sten har en säker ristare;
  - 91 *med X*, där alla säkra stenar har samma ristare;
  - 42 *blandade*.
- **Underlaget:** 23 grupper har svagt underlag. Det är nästan bara fragment på samma fyndplats, som Köpings kyrka på Öland
  och ATA-fragment i Uppland, och de hålls ihop av avståndet. De märks **svagt underlag**.
- **De 77 grupperna med okänd hand och gott underlag** (293 stenar), per landskap:

  | Landskap | Grupper |
  |---|---|
  | Östergötland | 24 |
  | Västergötland | 15 |
  | Södermanland | 10 |
  | Uppland | 10 |
  | Småland | 9 |
  | Öland | 5 |
- **Exempel som stämmer med runologerna utan att ha tränats på dem:**
  - **G015** (Ög 16, 18, 20, 33, 34, 234–237, Fv1959;249): Runor 2020 har gruppen Ög 234–235.
  - **G077** (U 910, 1018, 1024, 1042, 1046): Runors grupp U 1015–1024 delvis.
  - **G052** (Sö 46, 131, 134, 137, 319, 367, RAK): fyra av Kitzler Åhfeldts otillskrivna RAK-stenar (Sö 131, 137, 319,
    367). Hennes indelning ingår inte i facit. Det här kontrolleras mot hennes publikationer innan något sägs.

## Vad det betyder och inte betyder
- **Grupperna är förslag och prövbara hypoteser,** inte nya ristare. Varje grupp ska kontrolleras mot litteraturen innan
  något publiceras.
- **Precisionen är ungefär 77 %:** omkring tre av fyra par i samma grupp har samma ristare, mätt på namngivna ristare.
- **Facit och träningen** bygger delvis på samma slags drag som runologerna själva använde. Provet visar att metoden
  återskapar deras bedömningar, inte att bedömningarna är rätt.
- **Fragment och stenar med lite text** kan bara grupperas på stil, kors och plats. De har märkts svagt underlag.

## Tillägg 2026-11-23: runhöjd och stenhöjd (utvecklingsdelen, negativt)
Runhöjden (finns för 14 % av paren) och stenhöjden (23 %) ur `data/stone_dimensions.json`, som skillnad och kvot, lades
till M1 och prövades på utvecklingsdelen.

| | Median | Medel | Onämnda |
|---|---|---|---|
| Före | 0,944 | 0,856 | 0,946 |
| Efter | 0,944 | 0,859 | 0,928 |

De lades inte till, och modellen är oförändrad.

## 7. Litteraturen och slutprov 2 (2026-11-23–24): **håller**
Plan `analysplaner/2026-11-23-nya-ristare-slutprov-2-litteraturen.md` (sha 706be174), låst före jämförelsen.

**Läsningen** (arbetsflöde):
- 2 490 ställen i Fornvännen (1 018), Futhark (787) och åtta avhandlingar (685), där en ristare eller "samma hand" nämns nära
  ett signum;
- 28 läsare gav 1 556 uttalanden: 879 signeringar, 472 tillskrivningar, 153 om samma hand och 52 om olika händer;
- 5 blinda kontrolläsare tog ett stickprov på 250 ställen, och 220 av dem (88 %) var identiska;
- läsarna hittade 21 av kontrollens 22 par om samma hand, men tog ut fler, främst ur långa listor.

**Granskningen:** två oberoende granskare per uttalande om samma hand, olika händer eller tillskrivning av en gruppsten. Ett
uttalande behölls bara om båda bekräftade det.

| Uttalanden | Behållna |
|---|---|
| Samma hand | 74 av 93 |
| Olika händer | 38 av 42 |
| Tillskrivningar | 131 av 168 |

Ungefär 25 miljoner tokens. Körningen avbröts av användningstaket, och de sista 15 uttalandena granskades efter
återstart.

**Slutprov 2:** 132 granskade par om samma hand, varav 63 nya mot facit 1, i 30 grupper.

| | Grupper | I samma grupp | Kontrollen | Bättre / sämre | p |
|---|---|---|---|---|---|
| **T1 alla** | 25 | 0,457 | 0,066 | 17 / 5 | 0,0004 |
| T2 onämnda | 7 | 0,262 | 0,055 | 4 / 1 | 0,06 (för få för slutsats) |

- **Olika händer:** av 14 par inom 30 km som forskare säger har olika händer ligger 1 i samma grupp.
- **Beslut enligt planen:** metoden är prövad mot två oberoende facit, och appen behåller grupperna.

**Litteraturens besked per grupp** (`grupper_litteratur.json`):

| Besked | Grupper |
|---|---|
| Stöds i litteraturen | 57 |
| Ny | 155 |
| Ej omnämnd | 15 |
| Motsagd | 1 (G074: U 43–U 79 olika händer enligt Stern 2013) |

- **De 77 grupperna med okänd hand och gott underlag:** 69 nya, 7 stöds och 1 ej omnämnd.
- **De 7 som stöds:**

  | Grupp | Stöd |
  |---|---|
  | G019 | Vg 100–Vg 101, Lagman 1990 |
  | G057 | Vg 2–Vg 4, Williams 1990 |
  | G067 | Sö 362, 363, 84, 85, Jansson 1958 |
  | G131 | Ög 231–Ög 232, Källström 2020 |
  | G164 | U 354–U 435, Källström 2010 |
  | G171 | U 644–U 654, Lagman och Williams 1990 |
  | G200 | G 207–G 208, Zilmer 2005 |

## 8. Kitzler Åhfeldts grupper och huggtekniken (2026-11-24)
**Kitzler Åhfeldts grupper** (beskrivande, ingick inte i något facit):
- Rak 1 (Sö 131, 137, 166, 367, Fv1973;189) har 3 av 10 par i samma modellgrupp. Sö 131, 137 och 367 ligger i G052, och
  Sö 166 i Traengruppen G039.
- Rak 2 har 0 av 6 par i samma grupp.
- Sö 134 ("Rak 1?" hos henne) ligger i G052, och likaså Sö 319, som hon räknar till Rak 4.

**3D-provet** (plan `analysplaner/2026-11-24-nya-ristare-3d.md`, sha ffb9b051): **håller inte.**
- **Underlaget:** sex modellgrupper med 18 skannade stenar (groove-7, bara runorna). Måttet var medelavståndet i fyra
  huggspårsmått, jämfört med 9 999 omblandningar inom bergart.
- **Resultatet:** 2,22 mot 2,49, p 0,24. Bara grupperna med okänd hand gav p 0,69.

| Grupp | Typ | Stenar | Avstånd mot omblandning | p |
|---|---|---|---|---|
| G055 | okänd hand | Sö 163, 165 | 0,76 mot 2,97 | 0,04 |
| G105 | blandad | Äsbjörns Sö 206, 208 | 0,45 mot 2,02 | 0,03 |
| G084 | Tore | | 2,02 mot 2,65 | 0,32 |
| G039 | Traen | | 2,57 mot 2,87 | 0,35 |
| G052 | okänd hand | | 2,60 mot 2,40 | 0,62 |
| G097 | okänd hand | Sö 52, 75 | 4,91 mot 2,02 | 0,98 |

Med så få stenar har provet liten styrka, och huggspårsmåtten har tidigare följt bergarten mer än handen. Huggtekniken
varken stöder eller fäller grupperna. G052 får alltså inget stöd av huggtekniken.

## 9. Rättelser efter granskningen av rapportutkastet (2026-11-24)
En oberoende granskning av rapportutkastet hittade följande. Allt är rättat innan något publicerades.

**1. Kodfel om olika händer (beskrivande, inte i proven).**
- **Felet:** uttalanden om att en sten har en annan hand än flera andra delades upp i alla par. Stern (2013), som säger att
  U 855 inte är Arnfasts, blev "U 43 och U 79 har olika händer", fast hon tillskriver båda Arnfast.
- **Rättelsen:** nu används bara uttalanden om två stenar och listor över olika namnbärare. Fyra uttalanden räknas som
  tvetydiga.
- **Följden:** av de par om olika händer som ligger inom 30 km av varandra ligger nu 0 av 9 i samma grupp (tidigare 1 av
  14). G074 är inte längre motsagd.

**2. Litteraturbeskedet räknar nu också länkarna i SRI och Runor 2020** (`litteratur_besked.py`):

| Besked | Alla grupper |
|---|---|
| Kopplad tidigare | 75 |
| Ingen tidigare koppling | 138 |
| Ej omnämnd | 15 |
| Motsagd | 0 |

Av de 77 grupperna med okänd hand och gott underlag är 15 kopplade tidigare (11 i SRI eller Runor, 4 i övrig litteratur)
och 61 utan tidigare koppling. Den tidigare uppgiften "69 nya" var för stark.

**3. T2 i slutprov 2 höll inte**, i stället för obestämt. Planen kräver minst 5 grupper med skillnad, och det fanns 5.

**4. Kalibreringen** (`rapport_extra.py`): modellens värde är ett rangordningsmått, inte en sannolikhet. Andelen par med
samma ristare per värdeintervall:

| Värde | Samma ristare |
|---|---|
| under 0,2 | 4 % |
| 0,4–0,6 | 15 % |
| 0,8–0,9 | 46 % |
| över 0,9 | 73 % |

Grundnivån är 13 %. Täckningen vid τ 0,8 är 8,8 % av paren med samma ristare.

**5. Övrigt:**
- **Andelarna sammanslagna över paren:** slutprov 1 59 av 147 (40 %), slutprov 2 22 av 61 (36 %).
- **Per landskap:** Uppland 31 grupper (39 mot 5,4 %), Södermanland 7 (49 mot 10,7 %).
- **Holm-korrigering** över de fem proven ändrar inget utfall.
- **Stabiliteten:** 73 av 228 grupper helt stabila.
- **De 62 omstridda paren** i SRI avgjordes av språkmodellen, inte av en människa, och motiveringen är skriven för 31.
- **Den striktare regeln vid omläsningen** infördes efter att oenigheterna setts.
- **τ valdes** med alla namngivna par, också provdelens stenar med känd ristare.
- **Referenser:** Jansson 1958 heter "Runstensfynd i kyrkmurar" (Fornvännen 53, s. 241–257). Vitki-versionen är 3.1.0.

## 10. Ornamentiken ur SRI:s planscher (2026-11-24–25): **förbättrar inte grupperna**

Plan `analysplaner/2026-11-24-nya-ristare-ornamentik.md` (sha bec4b16b), låst före jämförelsen med facit. Andra användningen
av provdelen (en återstår).

### Kodningen
- **Underlaget:** 1 170 stenar som är avbildade på SRI:s planscher. Bilderna och koderna ligger utanför git.
- **Läsarna:** två oberoende läsare per sten (Claude Opus), med kodbok v2 (sha 97cf9214) och 468 läsningar.
  - 64 stenar hade ingen användbar bild.
  - 981 stenar har tillräckligt med eniga drag för att kunna jämföras, i 56 540 par inom 30 km.
- **Överensstämmelsen** (Cohens kappa) var hög:
  - djurhuvud 0,95, huvudets vy 0,93, öga 0,92, koppel 0,91;
  - läppflik 0,80, flätverk 0,79, nackflik 0,78, fötter 0,76, svans 0,72.
- **Täckningen** (andel stenar där båda angav ett värde): 0,35–0,62 för huvudets drag.
- **Strukna enligt regeln:**
  - `mun` (täckning 0,08);
  - `huvud_svans` (kappa 0,27);
  - `kontur` (ingen variation).
- **Läsarnas stilbedömning** stämmer med Rundatas stilgrupp i 478 av 744 fall (64 %). Den används inte som belägg.

### Grinden på utvecklingsdelen: håller
- **G1:** ornamentlikheten (överskott mot grannar på samma avstånd) för facitparen ligger i median på percentil 0,67.
  10 grupper, p = 0,002. Ornamentiken bär alltså en signal om handen.
- **G2:** M2:s AUC på namngivna par är 0,768, mot 0,764 för M1.
- **Gränsen:** τ₂ = 0,8, med precision 0,80. M1, räknad med samma kod, ger exakt de prövade grupperna.

### Slutprov 3 (provdelen)
- **O1, M2 mot M1:** **håller inte.**
  - Det gäller 25 grupper med minst ett avbildat par.
  - 19 grupper är oförändrade, 2 blev bättre och 4 sämre.
  - Medelandelen i samma grupp är 0,359 för M2 mot 0,403 för M1, p = 0,78.
  - För de onämnda grupperna (7) skiljer sig bara en, vilket är för få för ett prov.
- **O2, M2 mot grannarna:** håller. 42 grupper, 0,405 mot 0,075, p = 8e-5.
- **Beskrivande:**
  - Litteraturens facit 2: 0,472 för M2 mot 0,449 för M1.
  - Par som granskarna säger har olika händer: 0 av 9 i samma grupp för båda modellerna.
  - M2 ger 222 grupper (84 utan säker ristare) mot M1:s 228 (95).

### Beslut enligt planen
**Bara O2 höll.** Ornamentiken förbättrar inte grupperna mätbart, så appen behåller M1 (groups-1).

### Vad det betyder och inte betyder
- **Ornamentiken skiljer händer** (G1), men det den tillför täcks i stort sett redan av det modellen ser: text, stavning,
  stilgrupp, korsform och SRI:s ornamentord.
  - Bara hälften av stenarna är avbildade.
  - Huvudets detaljer finns på en tredjedel till hälften av dem.
  - De flesta facitgrupper förändras därför inte alls.
- **Provet säger inte att ornamentiken saknar värde.**
  - Koderna är ett nytt material för stilfrågor: målet är att pröva och förfina Gräslunds indelning.
  - Täckningen av huvudets detaljer kan förbättras: en egen läsning av utsnittet kring varje huvud, ett exempelblad och
    en tredje läsare som avgör vid oenighet.
- **Provdelen har en öppning kvar.** Den sparas tills en förbättrad version har visat sig på utvecklingsdelen.

## 11. Källkontroll: 1600- och 1700-talets teckningar mot planschfotona (2026-11-25)

Plan `analysplaner/2026-11-25-ornamentik-kallkontroll-teckningar.md`, låst före kodningen. Skript `ornamentik/kallkontroll.py`
och utfall `ornamentik/kallkontroll.json`.

### Urvalet och läsarna
- **Stenarna:** 140 bevarade stenar som har både en gammal teckning och en planschkod.
  - Bautils träsnitt 37, Rhezelius 37, Peringskiöld 28 och övriga tecknare 27, enligt urvalets typning.
- **Läsarna:** två oberoende läsare per teckning. De var lika samstämmiga som på fotona, med kappa 0,68–1,0.

### Teckning mot plansch, alla teckningar samlade (kappa)
- **Stämmer väl:**
  - människa eller mask 1,00, extra orm 0,94, fyrfota djur 0,90;
  - nackflik 0,88, djurhuvud 0,86, koppel 0,86, huvudets vy 0,83, kors 0,81;
  - flätverk 0,74, antal djur 0,73.
- **Stämmer måttligt:** svans 0,60 och öga 0,57.
- **Stämmer inte:** läppflik 0,30 och fötter 0,00 (nästan alltid "inga").

### Enligt regeln får teckningarna läsas för
djurhuvud, antal djur, huvudets vy, öga, nackflik, svans, koppel, flätverk, fyrfota djur, extra orm och kors. Människa eller
mask får dessutom läsas från Peringskiöld och övriga tecknare. Läppflik och fötter läses aldrig från teckningar.

### Vad det betyder och inte betyder
- **Tecknarna återgav rundjurets huvuddrag troget:** om det har huvud, hur huvudet är vänt, flikar i nacken, koppel och
  flätverk.
  - Det gäller också Bautils träsnitt, trots att de förenklar formerna.
  - Detaljerna i läppfliken gick förlorade i återgivningen.
- **Antalen per typ av teckning är små,** 5–17 jämförbara stenar per fält. För de flesta fält gäller därför det samlade
  värdet.
- **Planschfotot är inte facit.** Måttet visar att två återgivningar av samma sten stämmer överens.
- **Följden:** förlorade stenar som bara är kända från teckningar kan nu få ornamentkoder för de godkända fälten, och
  koderna märks med källa och tecknare.
