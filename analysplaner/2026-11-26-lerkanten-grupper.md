# Analysplan: lerkanten med stenarna i grupp som enhet (tillägg till K2 och K3)

Skriven och låst 2026-11-26, innan något av proven nedan har räknats. Tillägg till `analysplaner/2026-11-10-lerkanten-kontroller.md`
och samma regel som i `analysplaner/2026-11-19-sjalvkontroll-tillagg-grupper.md`: monument som ligger tätt ska prövas med
grupperna som enhet ([[spatial-clustering-units]]). Granskningen av rapporten "Fyra runstensfynd mot hundra års
invändningar" (2026-11-25) visade att K2 och K3 räknar varje sten som oberoende (`survival::clogit` utan klusterrobust fel).
K1, K4 och K5 vilar redan på blockbootstrap över 20 km och omfattas inte.

## Data
- **Punkterna:** samma som i K2 och K3, `utdata/palm_jordarna/kontroller_punkter.csv`. Varje sten (obs = 1) står mot sina
  50 slumpvisa platser i samma 2 km-ruta, och stenen är stratum.
- **Grupperna:** stenar inom 1 km från varandra länkas samman med `src.spatial_groups.link`, som i gravfältstillägget.
  Koordinaterna kommer från korpus 510ebfb3.

## Prov
- **G-K2:** samma modell som K2 (kanten och sand och grus inom 200 m), men med klusterrobust standardfel över grupperna
  (`clogit(... + cluster(grupp))`). **Håller** om kantens koefficient är större än 0 och robust ensidigt p < 0,05.
- **G-K3:** samma modell som K3 (även torv och gyttja inom 200 m), med klusterrobust standardfel. Håller på samma sätt.
- **Beskrivande:** en slumpvis sten per grupp, 1 000 dragningar (frö 20261126). För K2 och K3 redovisas medianen av kantens
  koefficient och andelen dragningar med ensidigt p < 0,05.

## Beslut (bestämt nu)
- **G-K2 och G-K3 håller:** lerkanten står också med grupperna som enhet, och rapporten säger det.
- **Någon av dem håller inte:** rapporten säger att lerkanten står sten för sten men försvagas med grupperna som enhet, på
  samma sätt som för gravfälten.

## Utdata
`utdata/palm_jordarna/grupper.py` och `grupper.R` → `grupper.json`.
