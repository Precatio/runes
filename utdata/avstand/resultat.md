# Resultat: avståndet mellan runstenarna (2026-10-29)

Plan: `analysplaner/2026-10-28-avstand-mellan-stenar.md` (fc620d6) och tillägget `-tillagg.md` (e587212), båda med
kontrollerad SHA-256 före körningen. Kod `avstand.R`, siffror `avstand.json`, figurer `g_U.png`, `g_Sö.png`.

## Utslag: klumpat – inte ”en sten per gård”
Runstenar som står kvar på sin plats står **närmare varandra** än slumpen ger på 100–1 000 meters avstånd, när
bygdernas täthet hålls konstant (kärnutjämning 10 km, golv 5 %). DCLF-test mot 999 simuleringar:

- **Uppland** (420 platser av 458 stenar): p 0,004, Holm 0,006; båda halvorna åt samma håll (väst p 0,044, öst p 0,012).
- **Södermanland** (149 platser av 168 stenar): p 0,003, Holm 0,006; båda halvorna (p 0,004 och 0,003).
- **Robusthet:** klumpat i alla prov – bandbredd 5 och 20 km, golv 1 och 10 %, utan sammanslagning till platser,
  100–500 m – med p mellan 0,001 och 0,005.

Hypotesen om jämnt utspridda stenar (en per gård eller släkt) får inget stöd. Stenarna samlas i grupper inom några
hundra meter, utöver att de följer vatten, gravfält och bygd. I Uppland ligger överskottet under ungefär 400 m.
Närmaste grannsten (median): 1,1 km i Uppland, 1,4 km i Södermanland; var tionde sten har en granne inom ungefär 200 m.

## Avvikelser från planen
1. **Huvudkörningen enligt planen var ogiltig.** Med 2 km bandbredd fick stenar utan grannar en täthet nära noll
   (ned till 1e-28), som dominerade beräkningen; g(r) låg på 0 i stället för omkring 1. En kalibrering på slumpmönster
   (utan att stenarnas egna avstånd användes) gav g(250–1 000 m) = 0,17–0,25 med 2 km och 0,87–1,15 med 10 km. Den
   körningens p-värden (0,44 och 0,34) är sparade som `avstand_OGILTIG_2km.json` och betyder ingenting. Tillägget
   (10 km, golv 5 %) låstes före den nya körningen.
2. Två provkörningar med 19 simuleringar gjordes för att hitta fel i koden; de styrde inget val.
3. Tekniskt i spatstat: simuleringarna skickas som en lista (uttryck utvärderas i fel miljö), `positive = TRUE` i
   täthetsskattningen, och den globala enveloppen fick 2 × 999 simuleringar.
4. Kovariatmodellen (robusthet 2 i planen) utgick enligt tillägget.
5. Södermanlands globala envelopp för g(r) blir mycket bred (±60) med 149 platser och säger lite; testet gäller L(r)
   över 100–1 000 m, som planen angav.

## Vad det kan betyda (att pröva)
Grupperna kan vara minnesplatser med flera stenar (vid vägar, broar och vadställen), släkters gravplatser eller
gårdar med flera generationers stenar. Nästa prov: står grannstenar inom 500 m oftare än slumpen efter **samma
ristare**, **samma familj** (länkmodellen, namnen) eller med **samma budskap** (bro, resa) än stenar längre bort?
Det skulle skilja ”familjens plats” från ”vägens plats”.
