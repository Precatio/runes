# Analysplan: samlad datering av runstenar utan stilgrupp (låst 2026-10-27, före resultat)

**Fråga.** Kan en modell som väger samman språkdrag, innehåll, kors och runtyp, seriationen och platsen datera de
svenska vikingatida runstenar som saknar stilgrupp, med en osäkerhet som håller?

**Data.** Korpusen i Statistik (R) (`corpus.csv`, 2 321 runstenar, version 76c2c44abc5d823a). Facit: stilgruppens
mittår enligt Gräslund (`style_from`, `style_to`), för de 1 008 stenar som har säker stilgrupp.

**Modell (primär, M1).** Kvantilregressionsskog (ranger, quantreg, 500 träd, seed 2026) med mittåret som utfall och
som förklarande variabler: alla `trait_*` och `cat_*` (faktorer, saknat värde som egen nivå), `cross`, `short_twig`,
`pagan`, `signed`, `n_words`, landskap, öst- och nordkoordinat (SWEREF 99 TM), och seriationens poäng
(`chronology_stones.csv`, `score`; saknas utanför Uppland, då 0 och en indikator). Stilgruppen, ristaren och dateringen
ingår inte. Prediktion: median och 10- och 90-percentil (80 %-intervall).

**Sekundär (M2), bara redovisad.** M1 plus sannolikhetsmodellens språkdatering (utanför-veckets log-likelihood per
epok ur `utdata/Malt/runlm_datering.json`, som andelar). M2 avgör inte utfallet.

**Prövning.** Femfaldig korsvalidering grupperad per socken (hela socknar lämnas utanför), upprepad 3 gånger med
olika indelning. Jämförelser:
- B1: landskapets median av mittåret (beräknad på träningsdelen).
- B2 (Uppland): seriationens datering (`est`, `lo`, `hi` i `chronology_stones.csv`).

**Godkänt om alla tre gäller (M1, alla svenska runstenar med stilgrupp):**
1. Medelabsolutfelet (år) är högst 0,85 × B1:s.
2. 80 %-intervallens täckning ligger mellan 0,75 och 0,88.
3. I Uppland är medelabsolutfelet högst 2 år större än seriationens (B2).

**Om godkänt:** M1 tränas på alla daterade stenar och daterar de odaterade; dateringen visas som fynd per sten
("datering (modell)") med 80 %-intervall, och metoden förs in i METHODS. **Om inte:** resultatet skrivs upp som
negativt i `utdata/datering/resultat.md`, och inget förs in i appen.
