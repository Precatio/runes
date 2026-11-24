# Analysplan: liknar stenarna i samma grupp varandra i huggtekniken? (3D, nya ristare)

Skriven och låst 2026-11-24, innan huggspåren har jämförts per grupp. Programmet: `analysplaner/2026-11-23-nya-ristare-program.md`
(medel 4).

## Känt före låsningen
- **Varför det är svårt:** huggspårsmåtten speglar bergarten mer än handen (utdata/Rak, 2026-10-05 och 2026-10-20). Kitzler
  Åhfeldts grupper Rak 1 och Rak 2 gick inte att återskapa med våra mått.
- **Täckningen:** 36 av hennes skannade Södermanlandsstenar är mätta med groove-7 (`utdata/Rak/referenser_g7`, bara runorna).
  Sex av modellens grupper har minst två av dem:

  | Grupp | Typ | Skannade stenar |
  |---|---|---|
  | G039 | med Traen | Sö 161, 162, 164, 166 |
  | G052 | okänd hand | Sö 131, 134, 137, 319, 367 |
  | G055 | okänd hand | Sö 163, 165 |
  | G084 | med Tore 1 | Sö 143, 149, Fv1948;282 |
  | G097 | okänd hand | Sö 52, 75 |
  | G105 | blandad | Sö 206, 208 |

- **Sett beskrivande** (ingen huggteknik): hennes Rak 1 (Sö 131, 137, 166, 367, Fv1973;189) har 3 av 10 par i samma
  modellgrupp, och Rak 2 har 0 av 6.

## Måttet
- **Huggspåren:** varje sten får medelvärdet av de fyra måtten i `CORE4` (apexvinkel, spårdjup, spårbredd, bottenradie)
  ur `means` i referensfilen, standardiserade över de 36 stenarna.
- **Avståndet:** det euklidiska avståndet mellan två stenar.
- **Gruppvärdet:** medelavståndet mellan stenarna inom gruppen.
- **Provstorheten:** medel över de sex grupperna.

## Provet
- **Nollhypotesen:** gruppetiketterna blandas om 9 999 gånger, med frö 20261124.
  - En sten får bara byta etikett med en sten av samma bergart: sandsten, enligt listan `SAND` i `utdata/Rak/rak_analysis.R`,
    eller granit och gnejs.
  - Gruppernas storlek och sammansättning av bergarter behålls.
  - Stenar utanför grupperna kan dras in.
- **Ensidigt p:** andelen omblandningar med medelavstånd ≤ det observerade.
- **H3D håller** om p < 0,05.
- **Beskrivande:**
  - varje grupps avstånd mot dess egen omblandning;
  - bara de tre grupperna med okänd hand;
  - G052 för sig.

## Vad som inte skrivs
- Med sex grupper och 18 stenar har provet liten styrka. Att det inte håller betyder inte att grupperna är fel.
- Huggspåren är ett grovt mått på handen.

## Utdata
`utdata/nya_ristare/huggteknik.py` → `huggteknik.json`, och resultatet i `resultat.md`.
