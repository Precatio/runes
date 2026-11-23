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
