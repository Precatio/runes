# Analysplan: täta kärnor – kandidater till onämnda händer

Skriven och låst 2026-11-08, innan någon gruppering nedan har räknats. Viktor 2026-11-08: "Om ingen känd passar, så leta
mönster som kan passa en ny grupp", och "ja gör detta du föreslår" om nästa steg: en låst plan för täta kärnor.

## Känt före låsningen
- Textdragen bär en hand utöver geografin (`analysplaner/2026-11-08-textdrag-hand.md`, sha add8ff31: K och T håller).
- Länkregeln i `analysplaner/2026-11-08-nya-handerna.md` (sha 9e0037d5) känner igen runologernas par i Runor 2020 (N1
  håller: 89 mot 33 %, p 0,0004), men sammanhängande länkar kedjade ihop stenarna till landskapsstora grupper (den
  största 645 stenar över 419 km), så inga grupper lades fram.
- Kalibreringen i `src/hand_links.py` (korpus 510ebfb3, 1 564 stenar): bland stenpar inom 30 km där båda har en säker
  ristare har 13 % samma ristare; vid överskottslikhet minst 0,5 är andelen 56 %, vid minst 0,6 68 %.
- Ingen klustring av stenarna har räknats.

## Data och likheten
Korpus 510ebfb3, samma stenar och samma överskottslikhet som i `src/hand_links.py` (`_features`, `excess_matrix`):
textdragen utan geografi (ortografisk TF-IDF och korpusens drag), minus medellikheten med stenar på samma avstånd (d ±
25 %, minst ± 1 km), åt båda hållen. Par längre isär än 30 km (och par utan grannar att jämföra med) räknas som helt
olika: de får den lägsta överskottslikheten i matrisen.

## Grupperingen
Medelkoppling (UPGMA) över alla stenar, med och utan ristare, på olikheten (största överskottslikheten minus
överskottslikheten). Vid gränsen c är en grupp en gren vars medelöverskottslikhet mellan grenens två delar är minst c,
vilket ger grupper där stenarna i medel är lika varandra, inte kedjor. En **tät kärna** är en grupp med minst tre stenar.

## Gränsen c (väljs på de namngivna ristarna, inte på Runor 2020)
För c = 0,00, 0,01 … 0,80: bland par av stenar med säker ristare i Rundata som hamnar i samma grupp, andelen med samma
ristare (precision). c\* = det lägsta c där precisionen är minst 0,70 och paren minst 30. Finns inget sådant c avbryts
planen.

## Prov
**C1 (huvudprov).** Runologernas grupper i Runor 2020 ("samma som gjort X", samma tolkning som
`utdata/nya_hander/prov.py`), par inom 30 km: per grupp andelen par i samma grupp vid c\*, mot andelen kontrollpar
(A, C) i samma grupp, där C dras på samma avstånd från A (d ± 25 %, minst ± 1 km, högst 30 km) utanför runologgruppen
(999 dragningar, frö 2026). Grupperna är enheterna. Wilcoxons teckenrangtest, ensidigt; skillnader som är noll räknas
inte (med stränga kärnor har många grupper varken par eller kontroller i samma grupp, så medianen säger lite). **Håller**
om p < 0,05 och fler grupper är bättre än sämre.
**C2 (krav på stabilitet).** Ristarna med säker ristare och minst två stenar delas slumpvis i två halvor (frö 2026). c
väljs som ovan på halva A (par där båda stenarnas ristare hör till A); precisionen vid det c mäts på halva B. **Håller**
om den är minst 0,50 (nästan fyra gånger grundnivån 13 %).
**C3 (beskrivande).** Kandidater: täta kärnor vid c\* där ingen sten har säker ristare i Rundata. För varje: stenarna,
socknarna, största avstånd, stilgrupperna, medelöverskottslikheten, Runor 2020:s ristarnotering, osäkra ristare i
Rundata och ristarmodellens förslag (hur ofta Öpir). Övriga kärnor räknas: med en enda namngiven ristare (rena), med en
namngiven ristare och stenar utan ristare (möjliga tillägg till den ristaren, bara antal), med flera namngivna ristare
(fel).

## Beslut (bestämt nu)
Håller C1 och C2 läggs kärnorna i C3 fram som kandidater till onämnda händer – prövbara hypoteser för runologer – och
litteraturen kontrolleras kärna för kärna innan något publiceras; därefter kan en forskningsrapport skrivas enligt
`utdata/rapporter/MALL.md`. Håller C1 men inte C2 redovisas kärnorna inte som händer (gränsen är inte stabil). Håller C1
inte redovisas de inte som händer.

## Redovisning
`utdata/tata_karnor/`: `prov.py`, `resultat.json`, `resultat.md`.
