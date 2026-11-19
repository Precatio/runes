# Resultat: självkontrollen med stenar i grupp som en enhet (2026-11-19)

Plan: `analysplaner/2026-11-19-sjalvkontroll-tillagg-grupper.md`, låst i commit 4570096 innan huvudproven räknades,
SHA-256 c1e3d2ab… (kontrollerad av `grupper.py` före körningen). Slumpfrö 0xc1e3d2ab = 3252933291.

Kod och siffror:
- `grupper.py` gör grupperna, registerobjekten för L1 och proven R och L, och skriver `resultat.json` och `gravfalt_grupper.csv`.
- `gravfalt.R` gör prov G och skriver `gravfalt.json`.

Grupperna är enkel länkning vid 1 km (`src/spatial_groups.link`).

## Sammanfattning
| Prov | Planens dom |
|---|---|
| G0, det publicerade 82 mot 55 procent | **försvagas** (halva A p 0,055) |
| G-K1, bara granskade gravfält | **står sig** |
| G-K2, yngre järnålderns former | **försvagas** (halva A p 0,081) |
| G-K3a, län | **försvagas** (halva B p 0,070) |
| G-K3b, län och gravfältstäthet | **försvagas** (halva B p 0,057) |
| Gravfälten i helhet (K1, K3a, K3b) | **försvagas** |
| S0, riktningen mot vägen | **håller** |
| L1, de gamla vägarnas linjer | **håller inte** |

I klartext:
- **Gravfälten.** Med grupperna som enhet är sambandet fortfarande tydligt i hela materialet. Oddskvoterna är 2,3–2,6
  och p 0,0009–0,007. Osäkerheten växer med en faktor på omkring 1,3 (designeffekt 1,5–2,1). Det räcker för att den ena
  halvan i fyra av fem prov hamnar strax över 0,05. Bara K1, med de granskade gravfälten, klarar båda halvorna.
- **Riktningen.** Riktningen mot vägen (S0) påverkas inte.
- **De gamla vägarnas linjer.** L1 faller: med en sten per grupp är medianen av p 0,10, och Holms övre gräns är 0,20.

## G. Gravfälten
657 stenar: 185 i grupp i 73 grupper och 472 ensamma, som är egna grupper. Ingen grupp blandar stenar i grupp och
ensamma stenar.

Halvorna är desamma som i planen 2026-11-10:
- halva A: 334 stenar, 41 grupper med stenar i grupp, 233 ensamma;
- halva B: 323 stenar, 33 grupper med stenar i grupp, 239 ensamma.

En grupp delas mellan halvorna, därav 41 + 33 = 74.

Oddskvoten är modellens. Inom hakparentes står 95-procentsintervallet med det klusterrobusta standardfelet, mot t.
- **G0, alla gravfält, landskap:** OR 2,38 [1,30–4,36], p 0,0055 (modellen sten för sten: 0,00023), DE 1,66, df 72.
  - Halva A: OR 2,27, p 0,055 (df 40).
  - Halva B: OR 2,53, p 0,049 (df 32).
  - Dom: **försvagas**. Halva A når inte p < 0,05.
- **G-K1, granskade gravfält:** OR 2,60 [1,50–4,50], p 0,00089, Holm 0,0036, DE 1,69.
  - Halva A: OR 2,25, p 0,037.
  - Halva B: OR 3,21, p 0,0081.
  - Dom: **står sig**.
- **G-K2, yngre järnålderns former:** OR 2,56 [1,34–4,89], p 0,0051, Holm 0,015, DE 1,93.
  - Halva A: OR 2,29, p 0,081.
  - Halva B: OR 3,01, p 0,021.
  - Dom: **försvagas**.
- **G-K3a, län:** OR 2,33 [1,27–4,27], p 0,0071, Holm 0,015, DE 1,62.
  - Halva A: OR 2,42, p 0,046.
  - Halva B: OR 2,32, p 0,070.
  - Dom: **försvagas**.
- **G-K3b, län och gravfältstäthet 1–5 km:** OR 2,51 [1,33–4,75], p 0,0051, Holm 0,015, DE 1,71.
  - Halva A: OR 2,59, p 0,045.
  - Halva B: OR 2,46, p 0,057.
  - Dom: **försvagas**.

Enligt tolkningsregeln i den låsta planen 2026-11-10, med de klusterrobusta p-värdena: K1 står sig, men K3a och K3b
försvagas och inget faller. Det publicerade resultatet **försvagas** därmed med grupperna som enhet. Det som försvagar
det är inte en invändning ur litteraturen. Det är att stenarna i en grupp inte är oberoende, så att halvorna var för
sig blir för små. Riktningen är densamma i alla prov och alla halvor (OR 2,25–3,21).

## R. Riktningen S0, en sten per grupp
120 stenar i 101 grupper; 1 000 dragningar med 999 omblandningar var.
- **Huvudprovet:** median medel-cos 0,338 mot väntat 0,014. Medianen av p är 0,001, det minsta möjliga med 999
  omblandningar. p är under 0,05 i alla dragningar. Medianen av andelen inom 45 grader är 48 procent.
  Dom: **håller**.
- **Beskrivande, samma huvudprov:**
  - S2, inom län: 118 stenar i 100 grupper, median p 0,001.
  - S3, utan flyttade och omresta stenar: 75 stenar i 64 grupper, median p 0,001, 45 procent inom 45 grader.
- **Beskrivande, gruppmedel** (9 999 omblandningar sten för sten): S0 p 0,0001.

## L. Vägarnas linjer L1, en sten per grupp
34 stenar.
- Varje sten fick sin närmaste gamla väg (`fid`) med samma segment och samma klassning som `vaglinjer.py`. Avstånd och
  bäring stämmer på 10⁻⁶ med `vaglinjer_stenar.csv`.
- De 34 stenarna har 26 olika vägobjekt. Länkningen på samma registerobjekt ändrar inte grupperna: 25 grupper, både
  med och utan den.
- **Huvudprovet:** median medel-cos 0,089 mot väntat −0,099, median p 0,101 (kvartiler 0,084–0,144). p är under 0,05
  i ingen av dragningarna, och medianen av andelen inom 45 grader är 24 procent. Holms övre gräns (2 × median p) är
  0,20. Dom: **håller inte**.
- **Beskrivande:**
  - L1b, utan flyttade stenar: 21 stenar i 15 grupper, median p 0,074.
  - L0, dagens vägar: 213 stenar i 177 grupper, median p 0,001, 50 procent inom 45 grader.
  - Gruppmedel: L1 p 0,133, L1b p 0,087, L0 p 0,0001.

Att det väntade värdet är negativt (−0,099) kommer av att omblandningen sker inom landskapet bland få stenar. Därför
jämförs medel-cos med det väntade, inte med noll.

## Avvikelser från planen
Inga avvikelser i proven eller i domarna. Följande förtydliganden gäller sådant som planen inte bestämde:
1. **Slumpströmmarna.** Varje prov (S0, S2, S3, L1, L1b, L0 och gruppmedlen) startar en egen slumpström med samma frö
   ur planens SHA-256. Planen anger fröet men inte om proven delar ström.
2. **Kravet på minst fem grupper.** För S0 och L1 finns inga två sidor som jämförs, och kravet lästes som minst fem
   grupper totalt. Det uppfylls (101 respektive 25 grupper). För gravfälten gäller kravet båda sidorna i varje halva
   (minst 33 grupper), och den låsta planens krav på minst 20 stenar med och utan utfallet gäller också.
3. **Intervallen för gravfälten** räknas med t-kvantilen för provets frihetsgrader, inte 1,96. Planen säger bara
   ”med det klusterrobusta standardfelet”.
4. **En extra fil.** `gravfalt_grupper.csv` (gruppnumret per sten, ur `grupper.py`) är en mellanfil för `gravfalt.R`.
   Den står inte i planens utdatalista.
5. **L1:s registerobjekt.** De gick att få fram med `nearest` på de 34 stenarna utan andra omräkningar, så regeln om
   reservläget (bara 1 km-länkning) behövde inte användas.
6. **Gruppmedlet** räknades med 9 999 omblandningar, som planen anger. Under ”Känt före låsningen” användes 4 999 och
   ett annat frö. Därför skiljer sig L1 något: 0,133 här mot 0,119 där.

Rapporter och publicerade texter är inte ändrade. Rättelserna enligt planens avsnitt ”Om ett prov inte håller” väntar
på Viktors besked.
