# Analysplan: Gräslund 1 – bär de kodade dragen stilgrupperna, och hur ser gränserna ut?

Skriven och låst 2026-11-25, innan de kodade ornamentdragen har jämförts med stilgrupperna. Första steget i Gräslundsspåret:
att pröva och förfina Gräslunds indelning av rundjursstilen (RAK, Fp, Pr1–Pr5) med kodade drag över hela korpusen.

## Data
- **Dragen:** konsensuskoderna ur SRI:s planscher (`data/cache/hander/ornamentik/orn_koder.json`, kodbok v2). De 14
  godkända fälten (`utdata/nya_ristare/ornamentik/m2_utveckling.json`).
  - Varje värde blir en egen indikator. Saknat värde ger nollor, utan egen kategori, eftersom att ett drag saknas beror på
    bilden och inte på stilen.
- **Stenarna:** de med minst tre eniga drag och en stilgrupp i Rundata bland RAK, Fp, Pr1, Pr2, Pr3, Pr4 och Pr5 (korpus
  510ebfb3). KB och tomma tas inte med.
- **Läsarnas egna stilbedömningar** (`stil`) används inte.

## Frågor och prov
- **F1, bär dragen stilgruppen?**
  - **Modellen:** multinomial logistisk regression (L2, C = 1), med femfaldig korsvalidering grupperad på socken.
  - **Måttet:** träffsäkerheten utanför vikten, jämförd med att alltid gissa den vanligaste gruppen.
  - **Prov:** 999 omblandningar av stilgrupperna (frö 20261125).
  - **H1 håller** om p < 0,05.
  - Det väntas hålla, eftersom stilgrupperna sattes efter samma slags drag. Det intressanta är mönstret i felen.
- **F2, är stilgrupperna en ordnad följd?**
  - **Vilka fel som räknas:** de stenar bland Pr1–Pr5 som felklassas till en annan Pr-grupp.
  - **Måttet:** andelen fel till en grannklass (Pr n ± 1).
  - **Jämförelsen:** samma andel när de förutsagda klasserna blandas om bland de felklassade stenarna, 999 gånger.
  - **H2 håller** om p < 0,05: felen hamnar oftare hos grannen än slumpen ger. Det tyder på en glidande följd snarare än
    skarpt skilda grupper.
- **F3, vilka grupper finns i dragen själva?** Beskrivande, utan prov.
  - **Modellen:** latenta klasser (en blandning av kategoriska fördelningar, EM) med k = 2 … 9 och 20 starter per k.
  - **Valet av k:** lägsta BIC.
  - **Jämförelsen med Rundata:** korstabell och justerat Rand-index.
  - **Varje klass beskrivs** med dess vanligaste dragvärden.
- **F4, samma stil i olika landskap?** Beskrivande.
  - Modellen tränas på Uppland och prövas på Södermanland och Östergötland, per stilgrupp.
  - Det jämförs med träffsäkerheten inom Uppland.
- **F5, en sannolikhet per sten.** Beskrivande.
  - Korsvaliderade sannolikheter för varje stilgrupp skrivs per sten.
  - Andelen stenar med högsta sannolikhet ≥ 0,7 (typiska) och < 0,4 (gränsfall) redovisas, per stilgrupp.

## Vad som inte skrivs
- **Ingen kronologi.** Ordningen i tid prövas i en senare studie, mot datering som inte bygger på stilen.
- **Rundatas stilgrupp är inte facit.** Den är experternas tillämpning av Gräslunds kriterier. Avvikelser kan ligga hos
  koderna, hos tilldelningen eller i att indelningen inte passar.
- **Bilderna är en begränsning.** Koderna kommer från foton där läsarna ofta inte kunde se detaljerna. Bara hälften av
  stenarna har huvudets drag kodade.
- Resultaten skrivs som ett prov och en förfining av Gräslunds indelning, inte som ett underkännande.

## Utdata
- **Skript:** `utdata/graslund/graslund1.py` skriver `utdata/graslund/graslund1.json` och `resultat.md`.
- **Sannolikheter per sten:** `utdata/graslund/stil_sannolikhet.csv`. Den innehåller bara signum och sannolikheter, alltså
  ingen upphovsrättsskyddad text.
