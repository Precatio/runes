# Tilläggsplan: robusthetssteg för folklandsprovet (steg 1 i 2026-11-02-gamla-granser-nya-monster)

Skriven och låst 2026-11-02, efter att huvudprovet har körts (folklanden 360 mot median 183, p 0,001 i båda halvorna;
utan granit 318 mot 154) men innan något av stegen nedan har körts. Syfte: avgöra om fyndet når nivå 1 ("Fullt prövat")
i rapportmallen (utdata/rapporter/MALL.md v2) eller stannar på nivå 2.

## Samma prov, fyra urval
Exakt samma metod som steg 1 i huvudplanen med avvikelse 1 (32 härader, grannar inom 20 km, 999 sammanhängande
slumpindelningar med samma seed, χ²-summan över dragen med tidsskikt), men på dessa urval av Upplands stenar:
1. **Bara stenar på ursprunglig plats** (`moved` = 0 i korpusen 7b9061c9) – flyttade stenar kan ha hamnat i fel härad.
2. **Utan de fem flitigaste ristarna** (Öpir, Fot, Balle, Åsmund, Gunnar; säkra och osäkra attribueringar) – skillnaden
   får inte bäras av några få verkstäder.
3. **Bara daterade stenar** (stilgrupp känd) – tidsskiktet "odaterad" får inte bära något.
4. **Utan förlorade stenar** (`lost` = 0) – äldre avskrifter kan vara mindre säkra.

## Utfall
Varje steg håller om p < 0,05 (hela urvalet). Alla fyra håller → nivå 1. Faller något → nivå 2, och det steg som faller
nämns i rapportens första mening. Halvorna redovisas per steg men är inget villkor här (de är prövade i huvudprovet).

## Redovisning
`utdata/gamla_granser/monster_trappa.py`, `monster_trappa.json`, tillägg i `monster_resultat.md`.
