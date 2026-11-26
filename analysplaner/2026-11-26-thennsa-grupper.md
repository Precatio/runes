# Analysplan: formen þennsa kring södra Mälaren med stenarna i grupp som enhet

Skriven och låst 2026-11-26, innan provet har räknats. Tillägg till upptäcktsmotorn v2
(`analysplaner/2026-10-29-upptacktsmotorn-v2.md`, `r/discovery_lokal.R`). Bygdefyndet att formen *þennsa* är vanligare
inom 21 km från Sö 190 bekräftades i halva B: 7 stenar mot 2,2 väntade, p = 0,0047, Holm 0,047. Provet räknade stenar.
Enligt regeln om klustrade monument ska det prövas med grupperna som enhet innan fyndet används i andra texter.

## Data och modell
- **Underlaget:** som i `discovery_lokal.R`. `utdata/upptackt_v2/drag.csv`, de lokala stenarna (`lokal == 1`), samma
  indelning i halvor (socknar efter tid, varannan) och samma cirkel (centrum Sö 190, radien ur `lokala.json`).
- **Väntat per sten:** samma glm som i motorn (drag ~ landskap + tidsskikt + log ord), skattad på halvan.
- **Grupperna:** stenarna i halvan länkas inom 1 km (enkel länkning i SWEREF 99 TM, som `src.spatial_groups.link`).
  Bara stenarna innanför cirkeln räknas.

## Prov
- **TG (huvudprov, halva B):**
  - **Mått:** antalet grupper innanför cirkeln med minst en sten med *þennsa*.
  - **Väntat:** 9 999 simuleringar där varje sten får formen med sin modellsannolikhet; frö 20261126.
  - **Ensidigt p:** andelen simuleringar med minst lika många grupper.
  - **TG håller** om p < 0,05.
- **Beskrivande:** samma prov i halva A. Där upptäcktes cirkeln, så provet där är inte oberoende.

## Beslut (bestämt nu)
- **TG håller:** fyndet om formen kring södra Mälaren får användas i andra texter, med grupperna som enhet angivna.
- **TG håller inte:** fyndet beskrivs som ett mönster som kan bero på att stenarna ligger tätt, och används inte som fynd.

## Utdata
`r/discovery_lokal_grupper.R` → `utdata/upptackt_v2/thennsa_grupper.json`.
