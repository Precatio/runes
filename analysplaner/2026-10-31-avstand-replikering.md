# Replikeringsplan: avståndet mellan runstenarna i Götaland

Skriven och låst 2026-10-31, innan någon analys av stenarnas platser i Östergötland, Västergötland eller Småland har
gjorts. Viktor, om rapporten om familjens plats: ”vi skriver Och huvudkörningen i steg 1 var ogiltig … Kan vi göra
detta på rätt sätt?”

## Varför
Steg 1 i familjens plats (`2026-10-28-avstand-mellan-stenar.md`) prövades i Uppland och Södermanland. Planens
bandbredd (2 km) visade sig ge en trasig skattning; metoden rättades i ett tillägg (`-tillagg.md`, låst 2026-10-29)
innan den nya körningen, som gav klumpat i båda landskapen. Eftersom metoden rättades efter en körning på samma stenar,
prövas den rättade metoden här **oförändrad** på stenar som inte har ingått i någon avståndsanalys. Det är den rena,
förregistrerade prövningen av steg 1.

## Data
Korpus `3f58e9339191761e` (samma som steg 1–4). Runstenar i Östergötland (Ög), Västergötland (Vg) och Småland (Sm) som
enligt Rundata står kvar på sin plats (moved = 0, lost = 0) och har känt läge: omkring 59, 56 och 52 stenar. Inga andra
landskap har tillräckligt många stenar på plats (nästa är Öland med 11).

## Metod (exakt som tillägget, inga nya val)
- Platser: stenar inom 25 m slås ihop.
- Fönster: unionen av 5 km runt alla landskapets stenar, skuret mot land (Natural Earth), som i steg 1.
- Täthet: kärnutjämning 10 km, lämna en ute, golv 5 % av medeltätheten; samma skattning för varje simulering.
- Test: DCLF på L(r) − r över 100–1 000 m mot 999 simuleringar av en inhomogen Poissonprocess, tvåsidigt; riktningen
  ur medelavvikelsen (över noll = klumpat).
- **Huvudtest:** de tre landskapen som **ett** mönster (ett fönster = unionen av de tre landskapens fönster).
- **Halvorna:** fönstret delat i en västlig och en östlig halva med lika många platser, var halva i sitt eget område,
  som i steg 1.
- **Beskrivande:** varje landskap för sig (för få stenar för att kräva signifikans).

## Vad som avgör
- **Replikerat:** huvudtestets p < 0,05 och riktningen klumpat, och samma riktning i båda halvorna med p < 0,05.
- **Delvis replikerat:** huvudtestet p < 0,05 och klumpat, men inte båda halvorna.
- **Inte replikerat:** annars. Det redovisas i rapporten om familjens plats som det är; steg 1 vilar då bara på Uppland
  och Södermanland och sägs gälla där.
- Inga parametrar ändras efter körningen. Två provkörningar med 19 simuleringar får göras för att hitta kodfel; de får
  inte styra något val och redovisas.

## Redovisning
`utdata/avstand/replikering.R`, `utdata/avstand/replikering.json`, `utdata/avstand/replikering_resultat.md`.
