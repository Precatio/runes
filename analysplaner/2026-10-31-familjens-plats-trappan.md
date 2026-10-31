# Tilläggsplan: robusthetstrappan för familjens plats

Skriven och låst 2026-10-31, innan någon av analyserna nedan har körts. Viktor: ”efter denna så kör vi rapport för
familjens plats.” Den låsta rapportmallen (utdata/rapporter/MALL.md) tar bara in fynd som har gått hela
robusthetstrappan (METHODS.md 1v). De fyra studierna bakom familjens plats (2026-10-28/29) är förregistrerade och
håller i sina egna robusthetsprov, men har inte gått trappans steg. Den här planen lägger trappans steg, där de passar,
på de två huvudtesten. Inga nya frågor ställs och inget i de fyra planerna ändras.

## Vad som redan är förregistrerat och prövat
- **Avståndet** (`analysplaner/2026-10-28-avstand-mellan-stenar.md` + tillägg): stenar på sin plats klumpar sig på
  100–1 000 m i Uppland och Södermanland (DCLF, p 0,004 och 0,003), båda halvorna, alla bandbredder.
- **Grannstenarna** (`2026-10-29-grannstenarna.md`), test B nedan: nära par (25–500 m) delar ett personnamn 7,9 gånger
  så ofta som jämförelsepar (2–10 km), p 0,0002, Holm 0,001.
- **Familjens plats** (`2026-10-29-familjens-plats.md`), test A nedan: stenar i grupp har gravfält inom 500 m oftare
  än ensamma stenar, OR 2,4, Holm 0,003, båda halvorna.
- **En generation** (`2026-10-29-en-generation.md`): grupperna har färre stilgrupper än bygdens stenar, p 0,0001,
  båda halvorna, också utan grupper med en enda ristare.

Trappans steg läggs på test A och B. Avståndet och generationen redovisas med sina egna förregistrerade prov; trappans
steg passar inte dem (punktmönster respektive omblandning inom bygd), och det står i rapporten.

## Data
Samma data som de ursprungliga testen: korpus `3f58e9339191761e`, `utdata/familjens_plats/stenar.csv` (test A) och
samma urval som `utdata/avstand/grannar.py` (test B). Flyttade stenar enligt Runor 2020: `src/robustness._runor_moved()`.
Sockenhalvorna som i alla projektets analyser: hela socknar växelvis inom landskapet efter medeldatering.

## Test A: gravfält inom 500 m, grupp mot ensam
Planens modell: logistisk regression y1_gravfalt ~ grupp + landskap + tidsskikt + lokal täthet (lt), landskap under
10 stenar sammanslagna. Stegen:
1. **Rått:** y1_gravfalt ~ grupp.
2. **Justerat:** planens modell (redan körd; räknas om här).
3. **Ristaren som slumpeffekt:** planens modell + (1 | ristare), stenar utan säker ristare grupperade per socken (lme4).
4. **Socknen som slumpeffekt:** planens modell + (1 | socken) (lme4).
5. **Platsen som yta:** planens modell + s(öst, nord, k = 30) i SWEREF 99 TM (mgcv), stenar med känt läge.
6. **Halvorna:** planens modell i var halva (redan körd; räknas om här).
7. **Utan ett landskap i taget:** planens modell utan vart och ett av landskapen med minst 30 stenar i urvalet.
8. **Utan flyttade stenar enligt Runor 2020.**

Ett steg håller när oddskvoten är över 1 och p < 0,05. I steg 7 måste riktningen hålla utan varje landskap; p < 0,05
krävs bara där minst två tredjedelar av stenarna är kvar. Om en modell inte konvergerar eller blir singulär redovisas
det, och steget räknas som inte prövat (inte som hållet).

## Test B: samma personnamn, nära par mot jämförelsepar
Planens mått: andelen nära par (25–500 m, samma landskap) som delar ett personnamn genom andelen jämförelsepar
(2–10 km), de 20 vanligaste namnen borträknade, p ur 9 999 omblandningar av stenarnas namn inom landskapet. Stegen:
1. **Rått/huvudmåttet:** planens mått (räknas om).
2. **Halvorna:** bara par där båda stenarna ligger i halva A, respektive B; omblandning inom landskap och halva.
3. **Varje landskap för sig** (motsvarar ”utan ett landskap i taget” med två landskap): Uppland, Södermanland.
4. **Utan par med samma säkra ristare:** nära par och jämförelsepar där båda stenarna har samma säkra ristare tas bort.
5. **Utan flyttade stenar enligt Runor 2020.**

Ett steg håller när kvoten är över 1 och p < 0,05. I steg 3 krävs p < 0,05 bara för landskap med minst två
tredjedelar av paren; riktningen måste hålla i båda. Ristaren och socknen som slumpeffekter passar inte ett parmått och
ersätts av steg 4; platsen som yta passar inte eftersom måttet självt är avstånd.

## Vad som avgör
- Håller test A och B i alla sina steg tas familjens plats in som forskningsrapport enligt mallen.
- Faller ett steg redovisas det i rapporten och för Viktor; rapporten skrivs då inte som bekräftat fynd utan som
  delresultat, eller väntar.
- Inga steg läggs till eller tas bort efter att utfallet är sett. Inga nya utfall prövas.

## Redovisning
`utdata/familjens_plats/trappan_resultat.md` och `trappan.json` (test A, `trappa.R`), `utdata/avstand/grannar_trappa.json`
(test B, `grannar_trappa.py`).
