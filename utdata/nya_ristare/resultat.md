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
