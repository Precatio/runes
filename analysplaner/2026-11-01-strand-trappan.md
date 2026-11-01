# Tilläggsplan: robusthetsstegen för runstenarna vid dåtidens vatten och vid gravfälten

Skriven och låst 2026-11-01, innan något av stegen nedan har räknats (utom de som redan står i
`utdata/strand/resultat.json` och anges som sådana). Viktor 2026-11-01: ”kör” (på förslaget att skriva strandens
resultatfil, rapporten och en låst trappa för att sikta på Fullt prövat fynd).

## Varför
H1 (stenarna står närmare vattnet år 1050 än slumppunkterna) och H3 (närmare gravfälten) i
`analysplaner/2026-10-23-strand-och-gravfalt.md` håller enligt planens kriterier, och båda håller i känslighetssteget T1
i `analysplaner/2026-10-31-strand-tillagg.md`. Projektets fasta känslighetsanalyser (METHODS 1v) är gjorda för samband
mellan två drag och passar inte rakt av för avstånd mot en lokal nollmodell. Här bestäms motsvarande steg för avstånd,
innan de körs. Håller alla steg för ett mått kvalar det måttet som Fullt prövat fynd i rapportmallen (version 4);
annars som Delvis prövat fynd med de steg som faller uppräknade. Rapportens nivå är det svagaste av de mått som står i
rubriken. H2 (dåtidens vatten mot dagens) och de sekundära proven ingår inte i trappan och redovisas bara enligt planen.

## Data och mått (oförändrade)
Samma 1 099 stenar och 10 990 slumppunkter som i `utdata/strand/resultat.json` (avstånden från steg 1 och 1b, gravfälten
som i `03_statistik.R`). Skriptet bygger upp stenarna och punkterna på samma sätt som `03_statistik.R` och kontrollerar
att stenarnas avstånd är desamma som i `utdata/strand/stenar.csv`; annars avbryts körningen. Måtten är desamma som i
huvudproven: d_then (vattnet år 1050) för H1 och d_grave för H3, Wilcoxons rangsummetest ensidigt (stenar närmare), AUC
och medianer.

**Punkterna till ett urval av stenar.** Varje slumppunkt hör till den närmaste stenen i samma landskap (samma regel som
för halvorna). När stenar tas bort i ett steg tas också deras punkter bort, så att nollmodellen förblir lokal kring de
stenar som prövas.

## Stegen (för H1 och för H3 var för sig)
1. **Halvorna** (redan räknade enligt planen): halva A och halva B var för sig.
2. **Utan ett landskap i taget**, för alla sex landskap (stenar och punkter tas bort). AUC över 0,5 krävs alltid; p < 0,05
   krävs bara där minst två tredjedelar av stenarna är kvar (samma regel som METHODS 1v).
3. **Socknen som enhet**: medianavståndet per socken (socken enligt den låsta korpusen; stenar utan socken var för sig)
   mot alla slumppunkter. Prövar att några socknar med många stenar inte bär fyndet.
4. **Socknen som slumpeffekt**: logistisk regression sten (1) mot slumppunkt (0) med −log2(avståndet + 250 m) och
   landskapet som fasta effekter och socknen som slumpeffekt (`lme4::glmer`, binomial); punkterna får den närmaste
   stenens socken. Effekten anges som oddskvoten när avståndet (plus 250 m) halveras. Prövar att stenarna står närmare än
   slumpmark *inom samma socken*.
5. **En sten per ristare**: av stenar med säker ristare (korpus `e83202e01a5e6d27`, `carvers_uncertain` = 0) behålls en
   per ristare, den första i signumordning; stenar utan säker ristare behålls alla.
6. **Utan återresta stenar**: stenar vars text i Kulturmiljöregistret (`data/raa/kmr_runstenar.json`: Beskrivning,
   Placering, Skadestatus, Orientering) eller Rundata (placering, övrigt) innehåller återrest, återupprest, rest upp,
   restes upp, uppsatt, uppställd, lagad, lagades, lagats eller reparerad tas bort (samma lista som i riktningens trappa).
   En återrest sten kan stå en bit från sin första plats.
7. **Utan flyttade stenar enligt Runor 2020** (`original = false`), för sig.
8. **Dagens flyttregel**: bara stenar som står kvar enligt korpus `e83202e01a5e6d27` (moved = 0, lost = 0), för sig.
   (Steg 7 och 8 tillsammans är T1, som redan är räknat och redovisas bredvid.)
9. **Tiden**: bland stenar med stilgruppsdatering i den låsta korpusen, de tidiga (mittår före 1050) och de sena (1050
   och senare) var för sig. Båda ska hålla.

Ett steg *håller* när AUC är över 0,5 och p < 0,05 (steg 2 med regeln ovan; steg 4 när oddskvoten är över 1 och
p < 0,05; steg 9 när båda delarna håller). Antalet stenar som tas bort redovisas i varje steg.

## Vad som inte får göras
Inga steg läggs till eller tas bort efter körningen, inga gränser ändras, och listan över ord för återresta stenar ändras
inte.

## Redovisning
`utdata/strand/05_trappa.R`, `utdata/strand/trappan.json` och ett eget avsnitt i `utdata/strand/resultat.md`.
