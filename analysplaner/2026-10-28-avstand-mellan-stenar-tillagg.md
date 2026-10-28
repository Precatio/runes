# Tillägg till analysplanen: avståndet mellan runstenarna (korrigerad skattning)

Låst 2026-10-29, före körningen nedan. Gäller tillsammans med `analysplaner/2026-10-28-avstand-mellan-stenar.md`
(oförändrad); avvikelserna redovisas i `utdata/avstand/resultat.md`.

## Varför
Huvudkörningen enligt planen (999 simuleringar, 2026-10-28) gav p 0,44 (Uppland) och 0,34 (Södermanland), men
skattningen var trasig: (1) stenar utan grannar fick en lämna-en-ute-täthet nära noll (ned till 1e-28), som dominerade
de inhomogena funktionerna; figuren för g(r) låg på 0 i stället för omkring 1. (2) En kalibrering på slumpmönster ur
den skattade tätheten (utan att stenarnas egna avstånd användes) gav g(250–1 000 m) = 0,17–0,25 med 2 km bandbredd,
0,55–0,84 med 5 km och 0,87–1,15 med 10 km. Huvudkörningen redovisas därför som ogiltig, inte som ”ingen avvikelse”.

## Ändringar
- **Täthet:** kärnutjämning med **10 km** bandbredd (huvudanalys), lämna en ute, med ett **golv på 5 %** av
  medeltätheten i fönstret. Samma skattning för det observerade mönstret och för varje simulering.
- Allt annat som i planen: platser (25 m), fönster, DCLF på L(r) − r över 100–1 000 m mot 999 simuleringar, tvåsidigt,
  Holm över landskapen, halvorna, tolkningsreglerna.
- **Robusthet:** bandbredd 5 och 20 km; golv 1 % och 10 %; utan sammanslagning; 100–500 m. (Kovariatmodellen utgår:
  den gav en orimlig avvikelse i den trasiga körningen och kräver en egen kalibrering.)
- **Figur:** g(r) med global envelopp med samma skattning.
