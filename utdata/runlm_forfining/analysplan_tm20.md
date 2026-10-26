# Analysplan: variantkvoten (textmodel-20-kandidat)

Skriven och låst 2026-10-26 innan några resultat tagits fram (METHODS.md 1x, ANALYSPLAN.md). Hash i
`analysis_plan_tm20.sha256`.

## 1. Fråga
Textmodel-19:s toleranslager gör regelgenererade stavningsvarianter möjliga, men de når sällan kandidatlistan: de
rankas på P(runor | ord) × ordfrekvens med straffet λ ovanpå och trängs undan av vanligare ords stavningar
(tolerans_diagnos.md). Ger en egen kvot för varianterna – som namnkvoten i textmodel-18 – fler rätta ord utan att
säkra fel ökar?
Ja = fler hela ord och runor inne i ord rätt i maskeringsprovet än textmodel-19 på samma luckor, dok5 inte sämre,
antalet fel bland ≥ 95 %-svaren inte större. Nej = något av det brister; då redovisas det som negativt och kvoten
förblir av.

## 2. Underlag
Samma provstenar, samma delning (fem veck, frö 2026/15) och samma dolda runor som mask4 (textmodel-19 = tol02_f*:
scripts/runlm_restore_test.py --own_d --name_cands 40 --tolerance 0.02). Jämförelsen är parvis per lucka mot
tol02_f*.json, bara runstenar (som tm19_ab.py). Dokumenterade luckor: dok5 (361 på runstenar, textmodel-19: 252 rätt,
2 fel bland 158 svar ≥ 95 %).

**Kontroll före allt annat:** med kvoten 0 ska den ändrade koden ge exakt samma rader som tol02_f0.json. Gör den inte
det avbryts arbetet tills skillnaden är förklarad.

## 3. Mekanism (bestämd nu)
I `restore` (src/runlm.py) får de fyllnader som bara kommer från en toleransvariant (nyckeln finns i
`tol_variants` för ordet och är inte en belagd stavning av något ord) en egen rangordning: ordets frekvens ×
P(källstavningen | ordet), alltså utan straffet λ. De `var_cands` bästa av dem som inte redan är kandidater läggs
efter ordförrådets kandidater, före namnkvoten. Poängsättningen av hela texten är oförändrad: λ gäller där som förut,
så kvoten ändrar bara vilka fyllnader som prövas, inte hur de bedöms.

## 4. Primärt mått och gräns
Parvis vinst/förlust per lucka (ordet rätt) mot textmodel-19: fler vunna än förlorade i båda slagen (inne i ord,
helt ord) över veck 1–4, OCH fel bland svar ≥ 95 % (tm19:s kalibrering) inte fler än i tol02_f1–4. Sekundärt: runan
rätt (top1), dok5 rätt och ≥ 95 %-fel.

## 5. Val av kvot
`var_cands` väljs bland {10, 20, 40} på veck 0 enbart: den med störst netto (hela ord + inne i ord) utan fler säkra
fel; vid lika netto den minsta. Resultatet rapporteras för veck 1–4 med det valda värdet (veck 0 redovisas separat
som urvalsveck). Ger inget värde netto över noll på veck 0 avbryts kvoten.

## 6. Vad som INTE får göras
Inga ändringar av reglerna, λ eller mask4:s luckor. Inga stenar bort. Ingen ny kvotstorlek efter att veck 1–4 setts.

## 7. Redovisning
Utfallet skrivs i tolerans_diagnos.md. Håller punkt 4 körs valideringståget som för textmodel-19 (klass3, dokalts,
svart4, listkalibrering, dok5) i en egen mapp `tm20/`; `textmodel.VERSION` flyttas bara om dok5 ≥ 252 av 361 och
≥ 95 %-felen inte ökar. METHODS.md 8.1 (versionsnot), CHANGELOG, bristlistan och news.json uppdateras då. Annars
negativt resultat, kvoten av.
