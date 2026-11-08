# Analysplan: bär textdragen en hand? Förutsättningen för att hitta nya, onämnda ristare

Skriven och låst 2026-11-08, innan likheterna nedan har räknats. Viktor 2026-11-08: "i attributionen är det väl
sannolikt att nya ristare finns som inte är namngivna tidigare. Om ingen känd passar, så leta mönster som kan passa en ny
grupp."

## Känt före låsningen
Ristarmodellen ser inte runologernas "samma hand" i Runor 2020 bättre än geografin (`analysplaner/2026-11-08-samma-hand-runor.md`,
H1 håller inte: 50 mot 44 %, p 0,57). Den tidigare sökningen efter okända ristare (`r/anonymous.R`) gav grupper som
visade sig vara skrivmiljöer snarare än händer (METHODS 1g, 2026-10-29). Innan en ny sökning efter nya grupper byggs
prövas om textdragen alls skiljer en hand från grannarna.

## Data
- **Stenarna:** korpus 510ebfb3, svenska vikingatida runstenar med koordinater och Rundatas translitterering.
- **Textdragen (utan geografi):** Vitkis ortografiska stilometri (`src/orthography.features`): tecken-n-gram (2–3) i
  läsbara ord utan egennamn, skiljeteckenprofil och täthet, bindrunor; TF-IDF över korpusen. Därtill korpusens
  språkdrag, formler och innehållskategorier (`trait_*`, `cat_*`, `pm_*`), standardiserade. Stenens likhet med en annan =
  cosinuslikheten, medelvärdet av de två delarna.
- **Samma hand enligt runologerna:** länkarna från Runor 2020:s "samma som gjort X" (samma tolkning som
  `utdata/samma_hand/prov.py`, efter rättelsen), grupperade.
- **Samma säkra ristare (positiv kontroll):** stenpar med samma säkra ristare i Rundata, inom 30 km från varandra.

## Måttet och kontrollen
För varje par (A, B) på avståndet d: likheten mellan A och B, mot likheten mellan A och en kontrollsten C på avståndet
d ± 25 % (minst ± 1 km) från A, utanför gruppen (för den positiva kontrollen: utan samma ristare), medel över 999
dragningar. Per grupp (eller per ristare i den positiva kontrollen): medelskillnaden par − kontroll.

## Prov
**K (positiv kontroll, måste hålla).** Stenar av samma säkra ristare är mer lika än grannar på samma avstånd: Wilcoxon
ensidigt över ristarna (minst 3 stenar), p < 0,05 och positiv median. Håller K inte mäter likheten inte en hand, och T
tolkas inte.
**T (huvudprov).** Runologernas grupper: likheten inom gruppen minus kontrollens, grupperna som enheter, Wilcoxon
ensidigt. **Håller** om p < 0,05 och positiv median.

## Beslut (bestämt nu)
Håller K och T bär textdragen en hand utöver geografin, och en sökning efter nya grupper bland stenar där ingen känd
ristare passar byggs under en egen låst plan med runologernas grupper som facit. Håller K men inte T ser textdragen de
namngivna, produktiva ristarna men inte de onämnda händerna; nya ristare kan då inte hittas med dem, och det som behövs är
ornamentik och runformer. Håller K inte är måttet fel.

## Redovisning
`utdata/textdrag_hand/`: `prov.py`, `resultat.json`, `resultat.md`.
