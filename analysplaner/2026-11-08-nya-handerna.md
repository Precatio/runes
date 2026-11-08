# Analysplan: nya, onämnda händer – grupper av runstenar som ingen känd ristare passar

Skriven och låst 2026-11-08, innan sökningen nedan har körts. Viktor 2026-11-08: "Om ingen känd passar, så leta mönster
som kan passa en ny grupp." Förutsättningen är prövad samma dag (`analysplaner/2026-11-08-textdrag-hand.md`, sha
add8ff31): textdragen bär en hand utöver geografin, också för runologernas onämnda händer (T håller, p 0,001), medan
ristarmodellen, som måste välja bland de namngivna, inte gör det.

## Likheten
Samma som i textdragsprovet: medel av cosinus i ortografisk stilometri (TF-IDF) och i korpusens språkdrag, formler och
innehållskategorier, utan geografi. **Överskottslikhet** för paret (A, B) = likheten minus medellikheten mellan A och
korpusens stenar på samma avstånd (d ± 25 %, minst ± 1 km), räknad åt båda hållen och medelvärdesbildad – det som är
likt utöver att stenarna är grannar.

## Länkregeln (bestäms på de namngivna ristarna, inte på facit)
Två stenar på högst 30 km avstånd länkas om överskottslikheten är minst t. Gränsen t väljs på stenpar inom 30 km där
båda stenarna har en säker ristare i Rundata: det t som ger störst skillnad mellan andelen länkade par med samma ristare
och andelen länkade par med olika ristare (Youdens J). Runor 2020:s grupper används inte för att välja t.

## Prov
**N1 (huvudprov).** Runologernas grupper i Runor 2020 ("samma som gjort X", par inom 30 km, båda stenarna med textdrag):
per grupp andelen länkade par, mot andelen länkade bland kontrollpar (A, C) där C ligger på samma avstånd från A, utanför
gruppen (999 dragningar). Grupperna som enheter, Wilcoxon ensidigt. **Håller** om p < 0,05 och positiv median.
**N2 (beskrivande).** Sökningen: bland stenar där ingen känd ristare passar (modellens "någon annan", `someone_else`, och
stenar utan förslag) bildar länkarna grupper (sammanhängande); grupper med minst tre stenar redovisas med stenar, plats,
datering (stilgrupp), länktäthet, Runor 2020:s ristarnotering och om någon sten är signerad eller tillskriven i Rundata.

## Beslut (bestämt nu)
Håller N1 hittar länkregeln runologernas händer oftare än grannar på samma avstånd, och grupperna i N2 läggs fram som
kandidater till onämnda händer – prövbara hypoteser för runologer, med N1 som stöd och litteraturen kontrollerad grupp för
grupp innan något publiceras. Håller N1 inte redovisas grupperna inte som händer.

## Redovisning
`utdata/nya_hander/`: `prov.py`, `resultat.json`, `resultat.md`.
