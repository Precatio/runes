# Analysplan – mall (METHODS.md 1x)

Kopiera den här filen till `utdata/<spår>/analysplan.md` **innan** några resultat tas fram, fyll i den och lås den:

    shasum -a 256 utdata/<spår>/analysplan.md > utdata/<spår>/analysis_plan.sha256

Hashen skrivs in i artikelns ruta "Så räknade vi" och i METHODS. Ändras planen efter att resultat setts, skrivs det
ut som en ändring med datum och skäl; den ursprungliga hashen står kvar. Rak-studien (utdata/Rak/rak_analysis.R,
2026-10-05) är förebilden.

## 1. Fråga
Vad ska prövas, i en mening. Vad vore ett ja och vad vore ett nej.

## 2. Underlag
Vilka stenar/inskrifter (filter: bara runstenar, period, region), vilken version av Rundata, vilka filer.
Antal som förväntas. Vad som utesluts och varför – bestämt nu, inte efter resultatet.

## 3. Primärt mått och test
Ett mått, ett test, en gräns för "håller" (t.ex. justerat p < 0,05, eller ett effektmått med intervall).
Vad som justeras för (period/stilgrupp, region, ristare som slumpeffekt, material).

## 4. Nollmodeller och kontroller
Slumpnivå, majoritetsgissning, permutation, hållet-utanför. Vilka artefakter som kan ge ett falskt ja
(refräng, utgåvans stavning, bergart, geografi) och hur de kontrolleras.

## 5. Känslighet
Vilka alternativa inställningar som körs (gränser, filter, mått) och hur resultatet redovisas om de skiljer sig.

## 6. Vad som INTE får göras
Inga nya mått efter att resultatet setts; inga delurval som inte står i punkt 2; ingen egen läsning av inskrifter.

## 7. Redovisning
Var resultatet publiceras (artikel, METHODS-avsnitt, bristlistan), även om det blir ett nej.
