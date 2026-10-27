# Analysplan v2: samlad datering med kalibrerade intervall (låst 2026-10-27, efter att v1 föll på täckningen)

**Bakgrund.** Version 1 (`analysplan.md`, bb06d292…) klarade felet och Uppland men intervallen var för breda (täckning
0,957 för nominella 80 %). Version 2 ändrar bara intervallen; modell, variabler, data och prövning är desamma.

**Ändring.** Konform kvantilregression (Romano m.fl. 2019): inom varje träningsdel delas socknarna slumpvis i en
träningshalva (70 %) och en kalibreringshalva (30 %). Skogen tränas på träningshalvan; på kalibreringshalvan beräknas
avvikelsen E = max(q10 − y, y − q90) för varje sten, och dess 80-percentil Q (konform korrektion, kan vara negativ).
Intervallet för en teststen blir [q10 − Q, q90 + Q]; punktskattningen är medianen ur skogen tränad på hela
träningsdelen. Allt annat som i v1 (femfaldig korsvalidering grupperad per socken, 3 upprepningar, seed 2026).

**Godkänt om alla tre gäller (samma gränser som v1):** medelabsolutfel ≤ 0,85 × landskapets median; täckning
0,75–0,88; Uppland högst 2 år sämre än seriationen.

**Om godkänt:** som i v1, med Q skattad på en kalibreringshalva av alla daterade stenar. **Om inte:** negativt i
`resultat.md`; ingen tredje version utan ny motivering.
