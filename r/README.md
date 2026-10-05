# Statistik i R

R-skripten som Vitki kör för korpusen och för en enskild sten. Metoderna beskrivs i
[METHODS.md](../METHODS.md), avsnitt 17.

```bash
Rscript r/install.R                                  # installerar paketen
Rscript --vanilla r/<modul>.R params.json utmapp      # kör en modul
```

`params.json` innehåller `corpus` (CSV:n från `src/r_bridge.py`), `corpus_dir` (där korpusmodulernas resultat
ligger), `water_dir` (Natural Earth, valfri) och `seed`; stenmodulerna dessutom `signum` och `candidates`.

| Modul | Körs | Resultat |
|---|---|---|
| `geography.R` | korpus | `geography.json`, `geography_stones.csv`, `geografi_*.png`, `ristare_karta.html` |
| `clusters.R` | korpus | `clusters.json`, `clusters_stones.csv`, `clusters_model.rds`, `kluster_*.png` |
| `text.R` | korpus | `text.json`, `text_features.csv`, `text_*.png` |
| `attribution.R` | korpus (efter geography och text) | `attribution.json`, `attribution_oof.csv`, `attribution_model.rds`, `modell_*.png` |
| `chronology.R` | korpus (efter text) | `chronology.json`, `chronology_stones.csv`, `seriation_*.png` |
| `dialect.R` | korpus | `dialect.json`, `dialekt_*.png` |
| `network.R` | korpus | `network.json`, `natverk_*.png` |
| `stone.R` | sten | `stone.json`, `sten_*.png` |
| `landscape.R` | sten | `landscape.json`, `landskap_*.png` |

Ordningen i korpusen är den i `MODULES` i `src/r_bridge.py`. Reproducerbarhetspaketet från appen innehåller
skripten, data och `KOR_OM.R`, som kör allt i rätt ordning.
