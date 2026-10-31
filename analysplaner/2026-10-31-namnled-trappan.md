# Tilläggsplan: robusthetsstegen för namnleden i familjen

Skriven och låst 2026-10-31, innan något av stegen nedan har räknats (utom de som redan står i
`utdata/namngivning/resultat.md` och anges som sådana). Viktor 2026-10-31: ”gör alla saker du föreslår” (bland dem:
”namnleden kan gå samma väg som vägen”).

## Varför
H1 (förälder och barn delar namnled) och H5 (syskon delar namnled) i `analysplaner/2026-10-29-namngivning-i-familjen.md`
håller enligt planen: Holm 0,0005 och båda halvorna. Projektets fasta känslighetsanalyser (METHODS 1v) är byggda för
samband mellan två drag på en sten och passar inte rakt av för namnpar. Här bestäms motsvarande steg innan de körs.
Håller alla steg för både H1 och H5 kvalar fyndet som Fullt prövat fynd i rapportmallen (version 4); annars som Delvis
prövat fynd med de steg som faller uppräknade.

## Data och mått (oförändrade)
Samma par, samma leddelning och samma mått som `utdata/namngivning/analys.py`: andelen par med delat namnled (eller
samma namn) mot 9 999 omblandningar av det andra namnet bland paren inom landskapet, ensidigt. Korpus
`3f58e9339191761e`. Slumpfrö 2026.

## Stegen (för H1 och H5 var för sig)
1. **Halvorna** (redan räknade enligt planen).
2. **Utan ett landskap i taget**, för landskap med minst 30 par. Riktningen ska hålla utan vart och ett; p < 0,05
   krävs bara där minst två tredjedelar av paren är kvar (samma regel som METHODS 1v).
3. **Tiden konstant:** omblandning inom landskap × tidsskikt (tidig RAK–Pr2, sen Pr3–Pr5, odaterad), så att namnmodet
   i en period inte räknas som arv.
4. **Ett par per sten:** det första paret i ordningen i filen, så att stenar med många namn inte väger tyngre.
5. **Utan korta led:** led kortare än tre bokstäver, och de datadrivna skräpleden -ni, -bbi och -einn, räknas inte.
   (Räknat efter körningen 2026-10-29 som robusthet; låses här som steg och räknas om.)
6. **Bara delade led:** par där båda bär samma hela namn räknas inte som delat led, så att fyndet inte vilar på att
   sonen fick faderns namn.

Ett steg *håller* när andelen är större än den väntade och p < 0,05 (steg 2 med regeln ovan). Flyttade stenar påverkar
inte namnen och prövas därför inte.

## Redovisning
`utdata/namngivning/trappa.py`, `utdata/namngivning/trappan.json`, `utdata/namngivning/trappan_resultat.md`. Inga
parametrar ändras efter körningen.
