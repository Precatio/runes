# Analysplan: Avståndet mellan runstenarna – en sten per gård? (spatstat)

Låst 2026-10-28, innan något avstånd mellan stenar har räknats. SHA-256 i
`analysplaner/2026-10-28-avstand-mellan-stenar.sha256`. Resultat och avvikelser i `utdata/avstand/resultat.md`.

## Före låsningen
Bara koordinaternas kvalitet har setts: 836 svenska runstenar står kvar på sin plats (inte flyttade, inte förlorade) och
har koordinater, nästan alla med sex decimaler; fem punkter har mer än en sten. Uppland har 458, Södermanland 168. Inga
avstånd mellan stenar, inga närmaste grannar och inga parkorrelationer har räknats.

## Fråga och hypotes
Står runstenarna jämnare utspridda på kort avstånd än deras beroende av landskapet förklarar? Hypotesen ”en sten per
gård eller släkt” förutsäger färre stenpar på några hundra meters avstånd än slumpen ger, när den allmänna tätheten
(som följer vatten, gravfält och bygd) hålls konstant. Motsatsen – stenar som klumpar sig närmare varandra – vore ett
tecken på minnesplatser med flera stenar eller på att familjer reste stenar nära varandra.

## Material
- Svenska vikingatida runstenar som står kvar på sin plats (`moved = 0`, `lost = 0`) med koordinater, i SWEREF 99 TM.
- **Platser:** stenar inom 25 m från varandra slås ihop till en plats (par och monumentgrupper räknas som ett monument).
- **Huvudområden:** Uppland och Södermanland, var för sig.
- **Fönster:** det område där runstenar förekommer – unionen av 5 km runt alla runstenar i landskapet (också flyttade),
  på land (Natural Earths landlager).

## Mått och test
- **Tätheten** skattas med kärnutjämning (Gauss), bandbredd 2 km (huvudanalys), utan den egna punkten.
- **Statistik:** inhomogen L-funktion, L(r) − r, och inhomogen parkorrelation g(r), r från 0 till 3 km.
- **Test:** DCLF-test (Diggle–Cressie–Loosmore–Ford) på L(r) − r över r = 100–1 000 m mot 999 simuleringar av en
  inhomogen Poissonprocess med den skattade tätheten, tvåsidigt. Riktningen anges av medelavvikelsen över intervallet:
  under noll = jämnare än slumpen (regelbundet), över noll = klumpat.
- **Holm** över de två landskapen, α = 0,05.

## Tolkningsregler
- **Regelbundet på kort avstånd:** Holm-p < 0,05 och negativ avvikelse, och samma riktning med p < 0,05 i båda
  halvorna av landskapet (fönstret delat i en östlig och en västlig halva med lika många platser).
- **Klumpat:** samma med positiv avvikelse.
- **Mönster att pröva:** Holm-p < 0,05 men inte i båda halvorna.
- Annars: ingen avvikelse från slumpen påvisad.

## Robusthet (redovisas, ändrar inte utslaget)
1. Bandbredd 1 km och 4 km. 2. Tätheten ur en kovariatmodell (avstånd till vatten och till närmaste gravfält i
Kulturmiljöregistret) i stället för kärnutjämning. 3. Utan sammanslagning till platser. 4. Intervallet 100–500 m.
5. Global envelopp för g(r) (999 simuleringar) som figur.

## Beskrivande (inga test)
Fördelningen av avstånd till närmaste grannsten, och g(r) per landskap i en figur.

## Förbehåll som redovisas
Bara en tredjedel av stenarna står kvar på sin plats; om de flyttade och förlorade stenarna försvann oberoende av var
de stod påverkas inte g(r), men flyttningen kan ha varit vanligare där stenarna stod tätt (vid kyrkor och byar).
Kärnutjämningen med 2 km bandbredd tar upp en del av den lokala klumpningen; därför prövas 1 och 4 km. Ett regelbundet
mönster visar avstånd, inte ägande: ”en sten per gård” är en tolkning som kräver gårdsdata för att prövas.
