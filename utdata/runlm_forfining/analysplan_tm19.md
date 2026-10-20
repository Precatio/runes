# Analysplan: toleranslagret (textmodel-19-kandidat)

Skriven och låst 2026-10-20 innan några resultat tagits fram (METHODS.md 1x, ANALYSPLAN.md). Hash i
`analysis_plan_tm19.sha256`.

## 1. Fråga
Kan sannolikhetsmodellen nå ord vars huggna stavning inte är belagd i träningsmaterialet (rank-null: 194 av 354
missar i maskeringsprovet mask4, utdata/runlm_forfining/tolerans_diagnos.md), genom att attesterade stavningar
utökas med regelgenererade varianter till ett straff per regel – utan att säkra fel ökar?
Ja = fler hela ord och runor rätt i maskeringsprovet än textmodel-18 på samma luckor, dok5 inte sämre, antalet fel
bland ≥ 95 %-svaren inte större. Nej = något av det brister; då redovisas det som negativt och lagret förblir av.

## 2. Underlag
Samma provstenar, samma delning (fem veck, frö 2026/15) och samma dolda runor som mask4 (scripts/runlm_restore_test.py
--own_d --name_cands 40). Jämförelsen är parvis per lucka mot mask4_f*.json (textmodel-18). Dokumenterade luckor:
dok5 (361 på runstenar). Inga stenar utesluts utöver vad mask4 uteslöt.

## 3. Primärt mått och gräns
Parvis vinst/förlust per lucka (ordet rätt): fler vunna än förlorade i båda slagen (inne i ord, helt ord) över
alla fem veck, OCH andelen fel bland svar ≥ 95 % (kalibrerad) inte högre än i mask4 (20 fel). Sekundärt: runan
rätt (top1), dok5 rätt (249 av 361) och ≥ 95 %-fel (4).

## 4. Nollmodeller och kontroller
Basen är textmodel-18 på exakt samma luckor (ingen slump i jämförelsen). Artefaktrisk: kandidatexplosion ger falska
träffar på korta följder; kontrolleras av straffet, högst två regler per form, och att säkra fel räknas.

## 5. Regler och straff (bestämda nu)
Varianter av en belagd stavning s för ordet w: (a) slut-R/r bortfaller; (b) h- läggs till eller faller bort i
ordets början; (c) en obetonad vokal (a i u e o y, inte första runan) faller bort; (d) en vokal i/e/a skiftar till en
annan av de tre på en plats; (e) nasal n/m faller bort före k/t/b; (f) svarabhakti: i eller u skjuts in mellan två
konsonanter. Högst två regler per variant; straff λ per regel. λ väljs bland {0,02; 0,05; 0,1} på veck 0 enbart,
och resultatet rapporteras för veck 1–4 med det valda λ (veck 0 redovisas separat som urvalsveck).

## 6. Vad som INTE får göras
Inga fler regler efter att veck 1–4 setts. Ingen ändring av mask4:s luckor. Inga stenar bort. Om λ-valet på
veck 0 inte ger någon vinnare över noll avbryts lagret.

## 7. Redovisning
METHODS.md 8.1 (versionsnot), CHANGELOG, bristlistan; textmodel.VERSION flyttas bara om punkt 3 håller och
kalibreringen är omskattad (scripts/runlm_list_calibrate --write) med dok5 omkört. Annars negativt resultat i
tolerans_diagnos.md.
