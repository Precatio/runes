# Analysplan: källkontroll – återger 1600- och 1700-talets teckningar rundjurets drag?

Skriven och låst 2026-11-25, innan någon teckning har kodats. Följer `analysplaner/2026-11-24-nya-ristare-ornamentik.md`
(kodbok v2, sha 97cf9214) och målet i Gräslundsspåret. Använder inget facit om händer.

## Frågan
Om en förlorad sten bara är känd från en teckning: vilka av rundjurets drag kan läsas från teckningen? Det prövas på
bevarade stenar som har både en teckning och ett planschfoto. Planschfotots kod är redan låst (konsensus av två läsare,
`data/cache/hander/ornamentik/orn_koder.json`).

## Urvalet
- **Vilka stenar:** bevarade stenar med en teckning från 1500–1700-talet i `data/cache/hander/plansch/teckningar.json` och minst tre
  eniga planschdrag.
- **Fyra typer, slumpvis (frö 20261125):**
  - Bautils träsnitt (Umeå-exemplaret): 40 stenar;
  - Rhezelius' teckningar som SRI återger: 40;
  - Peringskiölds teckningar eller träsnitt som SRI återger: 30;
  - övriga teckningar som SRI återger (Bureus, Aschaneus, Christofersson med flera): 30.
- **En teckning per sten:** den första av rätt typ. Finns färre stenar av en typ tas alla.

## Kodningen
- **Kodbok:** v2, oförändrad.
- **Läsarna:** två oberoende läsare per teckning (Claude Opus).
- **Vad läsarna ser:** bara teckningen och en not om att det är en teckning, med tecknaren angiven. De ser inte planschen
  eller dess koder.
- **Teckningens värde:** konsensus, på samma sätt som för planscherna.

## Måtten
- **Per fält och typ:** bland stenar där både teckningens och planschens konsensus har ett värde redovisas:
  - antalet stenar;
  - andelen lika värden;
  - Cohens kappa mellan teckning och plansch.
- **Samlat för alla teckningar:** samma tal.
- **Täckningen:** andelen teckningar med ett konsensusvärde.

## Regel (bestämd nu)
- **När ett fält får läsas från en typ av teckning:** när kappa mot planschen är ≥ 0,40 och minst 15 stenar kan jämföras.
- **Om typen har för få stenar:** då gäller det samlade värdet för alla teckningar.
- **Fält som inte klarar regeln** kodas inte från teckningar för de förlorade stenarna.
- **Märkning:** koder från teckningar märks alltid med källa och tecknare.

## Vad som inte skrivs
- Planschfotot är inte facit. Det är också en återgivning, ofta ifylld med färg. Måttet visar om de två återgivningarna
  stämmer överens.
- En låg överensstämmelse kan bero på tecknaren, på träsnidaren eller på att stenen har vittrat sedan 1600-talet.

## Utdata
- **Skript:** `utdata/nya_ristare/ornamentik/kallkontroll.py` skriver `kallkontroll.json`.
- **Koderna:** ligger i cachen.
