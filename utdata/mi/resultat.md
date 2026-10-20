# Multipel imputation av tidsskiktet – utfall 2026-10-20: nej

Analysplan: `analysplan_mi.md` (SHA-256 `d97e20ba6d2c5b96248a62cded09deb0e9df635d7ef956315e90a65225128b7b`, låst och
committad i 76da075 innan några resultat fanns). Skript: `aux_dating.py` (språkdateringen), `export.py` (tabellen),
`mi_validate.R` (maskeringsprovet; kräver R-paketet mice). Resultat: `validering.json`.

## Underlag
2 321 runstenar, varav 1 008 med säker stilgrupp (före 1020: 228, 1020–1050: 341, 1050–1075: 140, 1075 och senare:
299). Språkdateringen fanns för 1 918 stenar (2 046 ur dateringsprovet för alla slags inskrifter, 484 runstenar lästa
med modellen för alla daterade texter). Alla 22 drag gick att pröva. MAR-maskeringen maskerade i genomsnitt 30
procent, som planerat. Korpusens data är desamma som i version 47cc8cfb5fef8a05; versionsnumret ändrades till
5b1153fb66211f0a samma kväll bara för att en figurtext i r/attribution.R rättades.

## Utfall (20 upprepningar × 22 drag)

| Maskering | Analys | Täckning (95 %-intervall) | Medelavvikelse, log-oddskvot | Träff på skiktet |
|---|---|---|---|---|
| MAR (primär) | bara daterade (complete case) | 0,993 | 0,155 | – |
| MAR | MI arm A (utan språkdatering) | **0,888** | **0,237** | 0,576 |
| MAR | MI arm B (med språkdatering) | **0,867** | **0,233** | 0,584 |
| MCAR | bara daterade | 1,000 | 0,169 | – |
| MCAR | MI arm A | 0,876 | 0,281 | 0,588 |
| MCAR | MI arm B | 0,874 | 0,275 | 0,607 |

Planens gränser (punkt 4) under MAR: täckning minst 0,90 **och** mindre medelavvikelse än analysen med bara daterade
stenar. Ingen av armarna klarar någon av dem. Språkdateringen höjde träffen på skiktet med 0,8 procentenheter (gränsen
för att välja arm B var 2). **Beslut enligt planen: ingen imputation införs; appen räknar som förut bara på stenar med
säker stilgrupp.**

## Var det brister
Täckningen faller för de drag vars förändring över tiden skiljer sig mellan landskapen: kristna markörer (0,45 i båda
armarna), utan religiösa markörer (0,45), ristare i Rundata (0,25 och 0,15), signerad (0,75 och 0,60) och kors (0,80 och
0,70). Imputationsmodellen har landskap och drag som var för sig verkande prediktorer, men oddskvoten skattas inom
landskap: när sambandet mellan tid och drag inte är detsamma i alla landskap drar imputationen de imputerade stenarna
mot ett genomsnittligt samband, och den sammanvägda skattningen förskjuts. För språkdragen höll täckningen (0,99).

Det mest användbara resultatet är det oväntade: analysen med bara de daterade stenarna höll sina intervall också när
bortfallet efterliknade det verkliga (täckning 0,99 under MAR). Att hälften av stenarna saknar stilgrupp gör
tidsfrågorna mindre precisa, men det tycks inte snedvrida dem – inom landskap, och med de prediktorer som här styrde
bortfallet.

## Vad som inte prövades (kräver en ny plan)
Imputation med samspel mellan landskap och drag, eller med metoder som fångar samspel själva (t.ex. mice med `rf` eller
`cart`); imputation skiktad per landskap; andra skattningar än oddskvoten från 1050 mot före. Planens punkt 6 förbjuder
att pröva dem här, efter att utfallet setts.
