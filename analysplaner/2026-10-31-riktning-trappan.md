# Tilläggsplan: robusthetsstegen för ristningens riktning mot vägen

Skriven och låst 2026-10-31, innan något av stegen nedan har räknats (utom de som redan står i
`utdata/riktning/resultat.md` och anges som sådana). Viktor 2026-10-31: ”gör alla saker du föreslår” (bland dem:
”vägrapporten: planen för robusthetsstegen kan låsas och köras redan nu”).

## Varför
H2 i `analysplaner/2026-10-29-ristningens-riktning.md` (ristningen vänd mot vägen) håller enligt planen: Holm 0,0004 och
båda halvorna. Projektets fasta känslighetsanalyser (METHODS 1v) är gjorda för samband mellan två drag och passar inte
rakt av för riktningar. Här bestäms motsvarande steg för riktningar, innan de körs. Håller alla steg kvalar fyndet som
Fullt prövat fynd i rapportmallen (version 4); annars som Delvis prövat fynd med de steg som faller uppräknade.

## Data och mått (oförändrade)
`utdata/riktning/stenar.csv` (219 stenar, 123 med väg), samma mått som H2: medelvärdet av cos(ristningens riktning −
vägens riktning), mot 9 999 omblandningar av riktningarna inom landskapet, ensidigt (mot vägen). Slumpfrö 2026.

## Stegen
1. **Halvorna** (redan räknade enligt planen): halva A och halva B var för sig.
2. **Utan ett landskap i taget**, för landskap med minst 10 stenar med väg (U, Sö, Ög). Riktningen ska hålla utan
   vart och ett; p < 0,05 krävs bara där minst två tredjedelar av stenarna är kvar (samma regel som METHODS 1v).
3. **Socknen som enhet**: ett värde per socken (medel-cos för sockens stenar), och måttet är medelvärdet över socknarna;
   omblandningen som i H2. Prövar att några socknar med många stenar inte bär fyndet.
4. **En sten per ristare**: av stenar med säker ristare (Rundata, utan frågetecken) behålls en per ristare, den första i
   signumordning; stenar utan säker ristare behålls alla.
5. **Utan återresta stenar**: stenar vars text i Kulturmiljöregistret eller Rundata innehåller återrest, återupprest,
   rest upp, restes upp, uppsatt, uppställd, lagad, lagades, lagats eller reparerad tas bort. (Kontrollen efter
   körningen den 29 oktober gav 58 stenar; antalet med den här listan redovisas.)
6. **Utan flyttade stenar enligt Runor 2020** (`original = false`).
7. **Dagens flyttregel**: bara stenar som står kvar enligt korpus `e83202e01a5e6d27` (moved = 0, lost = 0).
8. **Vägens källa** (redan räknade som robusthet): bara vägar ur Kulturmiljöregistrets text, och bara registrerade
   färdvägar och vägmärken inom 500 m.

Ett steg *håller* när medel-cos ligger över det väntade och p < 0,05 (steg 2 med regeln ovan).

## Redovisning
`utdata/riktning/trappa.py`, `utdata/riktning/trappan.json`, `utdata/riktning/trappan_resultat.md`. Inga parametrar
ändras efter körningen.
