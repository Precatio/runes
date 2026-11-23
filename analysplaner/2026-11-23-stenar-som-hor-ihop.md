# Analysplan: stenar som hör ihop – täta kärnor av en hand, också där ingen känd ristare passar

Skriven och låst 2026-11-23, innan grupperingen nedan har körts. Viktor 2026-11-23 om nästa steg: en modell som får säga
"ingen känd ristare, men de här stenarna hör ihop" – "detta gillar jag verkligen".

## Känt före låsningen
- **Textdragen bär en hand** (plan add8ff31): runologernas grupper i Runor 2020 är mer lika än grannar på samma avstånd i
  16 av 18 grupper.
- **Parregeln** (plan 9e0037d5, `utdata/nya_hander`): överskottslikhet ≥ t = −0,010 länkar 89 % av runologernas par mot
  33 % av grannparen (N1 höll). Men sammanhängande länkar kedjade ihop sig till landskapsstora grupper (645 stenar över
  419 km). Gränsen skiljer par åt men bildar inga grupper. Parvis är signalen svag: 67 % av paren med samma säkra ristare
  länkas, men också 43 % av paren med olika.
- **Den öppna modellen** (plan 091e6cba, `utdata/oppen_modell`, körd 2026-11-23): O1 höll inte (p 0,21; 4 grupper bättre,
  5 sämre), O2 höll (77 % av de rätta svaren behålls). Felet var att stenarna bedöms en och en: i en grupp får ofta den ena
  stenen en känd ristare och den andra "okänd hand". Frågan måste ställas om gruppen.
- Inget av proven nedan är räknat.

## Materialet
Samma 1 564 stenar och samma likhet som i `utdata/nya_hander/prov.py`: korpus 510ebfb3, stenar med koordinater, minst tre
läsbara ord, utom Bohuslän. Likheten är medel av cosinus i ortografisk stilometri (TF-IDF över tecken-n-gram,
skiljetecken och bindrunor) och i korpusens språkdrag, formler och innehållskategorier, utan geografi.
**Överskottslikheten** för ett par inom 30 km är likheten minus medellikheten med korpusens stenar på samma avstånd
(d ± 25 %, minst ± 1 km), räknad åt båda hållen och medelvärdesbildad. Ingen ny variabel läggs till.

## Grupperingen: täta kärnor
Genomsnittlig länkning (UPGMA) med två villkor, på alla 1 564 stenar och utan några ristarnamn:
1. Två grupper får slås ihop bara om **alla** par mellan dem ligger inom 30 km (gruppens diameter ≤ 30 km).
2. Medelvärdet av överskottslikheten över alla par mellan de två grupperna måste vara **minst τ**. Par där
   överskottslikheten inte går att räkna (ingen sten på samma avstånd) räknas inte i medelvärdet.

Det tillåtna paret med högst medelvärde slås alltid ihop först. Det upprepas tills inget tillåtet par når τ.
Medelvärdet över alla par, i stället för den starkaste länken, är det som hindrar kedjorna.
**En kärna** är en grupp med minst tre stenar.

## Val av τ (på de namngivna ristarna, inte på Runor)
- **Stenarna:** de med en säker ristare i Rundata (ristare angiven och inte osäker) bland de 1 564. Bara ristare med minst
  två sådana stenar räknas.
- **Uppdelningen:** ristarna delas slumpvis i två halvor, A och B (frö 20261123). Alla en ristares stenar hamnar i samma
  halva.
- **Gränserna som prövas:** 100 jämnt fördelade kvantiler (50–99,5 %) av överskottslikheten bland alla par inom 30 km.
- **Måtten på A:**
  - *precision* = andelen par av A-stenar i samma grupp som har samma ristare;
  - *täckning* = andelen par med samma A-ristare inom 30 km som hamnar i samma grupp.
- **Valet:** τ = den gräns som ger högst F0,5 (precisionen vägs dubbelt). Runor 2020 används inte.

## Prov
**H1 (de namngivna ristarna, halva B).**
- **Enheten:** varje grupp (oavsett storlek) med minst två B-stenar.
- **Gruppens skillnad:** precisionen för dess B-par minus kontrollen.
- **Kontrollen:** för varje B-par (a, b) i gruppen dras en B-sten c på samma avstånd från a (d ± 25 %, minst ± 1 km),
  utanför gruppen. Kontrollen är andelen där a och c har samma ristare, medel över 999 dragningar (frö 2026).
- **Testet:** ensidigt Wilcoxon-test över grupperna.
- **Håller** om p < 0,05 och medianskillnaden är positiv.
- **Känslighet** (utan egen slutsats): samma sak med bara signerade stenar (`signed` = 1), eftersom Rundatas
  tillskrivningar delvis bygger på stavningen (Axelson 1993) och gör H1 delvis cirkulärt.

**H2 (huvudprovet, externt facit: Runor 2020).**
- **Grupperna:** runologernas grupper ("samma som gjort X"), tolkade som i plan 32257107 (`utdata/samma_hand/prov.py`).
  Bara grupper med minst en onämnd hand tas med, och bara par inom 30 km där båda stenarna finns bland de 1 564.
- **Måttet:** per grupp andelen par som hamnar i samma grupp i grupperingen.
- **Kontrollen:** par (a, c), där c är en av de 1 564 stenarna på samma avstånd från a (d ± 25 %, minst ± 1 km, högst
  30 km), utanför gruppen. 999 dragningar, frö 2026.
- **Bortfall:** grupper utan kontrollstenar räknas inte.
- **Testet:** ensidigt Wilcoxon-test över grupperna.
- **Håller** om p < 0,05 och medianskillnaden är positiv.

## Beslut (bestämt nu)
- **H1 och H2 håller:** kärnorna läggs fram som **stenar som hör ihop**. De visas på /ristare som tydligt märkta förslag
  och beskrivs i ett rapportutkast. Varje kärna får en av tre typer:
  - *okänd hand* – ingen sten har en säker ristare;
  - *med X* – alla säkra stenar har samma ristare X;
  - *blandad* – säkra stenar av flera ristare. Den redovisas som ett tecken på metodens gränser.
  Inget publiceras som en ny ristare utan att litteraturen kontrolleras kärna för kärna.
- **H2 håller men inte H1:** kärnorna redovisas i resultatet, men inte i appen.
- **H2 håller inte:** kärnorna redovisas inte som händer.

## Beskrivande (utan prov)
- Hur många kärnor det blir, deras storlek och typ, och hur många stenar utan ristare som hamnar i en kärna, per landskap.
- Precisionen på alla säkra stenar, och på bara de signerade.
- Var runologernas grupp U 1015 och U 1017–1024 hamnar.
- För varje kärna:
  - stenarna, socknarna och diametern;
  - stilgrupperna;
  - de säkra och de signerade ristarna;
  - Runor 2020:s ristarnoteringar;
  - K0:s förslag;
  - medelöverskottet.

## Vad som inte skrivs
- En kärna är en prövbar hypotes, inte en ny ristare.
- Runor 2020:s grupper är runologernas bedömningar, inte säkra fakta.
- Stenar med färre än tre läsbara ord kan inte grupperas. Fragmenten saknas alltså.

## Utdata
`utdata/stenar_som_hor_ihop/prov.py` → `resultat.json`, `resultat.md` och `karnor.csv` (stenar och kärnor, utan
textutdrag).
