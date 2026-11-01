# Upptäcktsmotorn v3 – samspel mellan tre drag: resultat

Låst plan `analysplaner/2026-11-01-upptacktsmotorn-v3-samspel.md` (sha a641368c). Kört 2026-11-01 med `r/discovery_v3.R`
på korpus `e83202e01a5e6d27` (1 739 stenar, 124 binära drag); `resultat.json`, kandidatlistan `kandidater.json`
(frusen, `kandidater.sha256`).

## Avvikelse
Första körningen stannade när kandidatlistan skulle skrivas (en kolumn hade fel typ för JSON); ingen lista hann frysas
och ingenting prövades. Rättat (`as.character`), mellanlagring av steg 1 tillagd, allt kört om från början.

## Utfall: inga samspel håller
- **Huvudprovet (A hittar, B prövar):** hstats och pre gav 236 förslag (152 och 84); 151 klarade familje- och
  cellreglerna och prövades med glm i halva A; 9 hade samspel med p < 0,01 och frystes. **Inget bekräftades i halva B**
  (Holm 1 för alla). Bara 1 av 9 hade ens samma riktning i B.
- **Halvorna bytta (B hittar, A prövar):** 260 förslag, 18 kandidater, **inget bekräftat**; 7 av 16 prövbara hade samma
  riktning, alltså vad slumpen ger.
- Kandidaterna var mest kombinationer av skiljetecken, kors, ristarsignatur, material och läge, som i halva B ofta bytte
  tecken: brus i den halva där de hittades.

## Vad det betyder
Med 124 drag på 1 739 stenar finns inga samspel mellan tre drag som är starka nog att synas i båda halvorna. Runstenarnas
drag verkar i huvudsak var för sig, landskap och tid medräknade; parmönstren som redan är prövade döljer inga villkorade
undantag som metoderna kan se. Gränsen är styrkan: ungefär 870 stenar per halva räcker för samspel med stor effekt, inte
för små. Resultatet är ett negativt fynd och redovisas som sådant; inget införs i appen.
