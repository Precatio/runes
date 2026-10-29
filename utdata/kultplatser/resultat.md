# Resultat: bönen vid den gamla kultplatsen (2026-10-29)

Plan: `analysplaner/2026-10-29-bon-vid-kultplatsen.md` (d6ef19b, SHA-256 629d8a02… kontrollerad före körning). Kod
`data.py` och `analys.R`, siffror `kultplatser.json`. 1 097 svenska runstenar på sin plats; 56 inom 2 km från ett
teofort namn (18 namn). Grundmönstret återskapas exakt: bön 32 % mot 15 %, oddskvot 2,63 (1,44–4,80).

## Utfall (Holm över H1–H4, ensidigt)
- **H1 Kristnandets tidiga skede – faller.** Bönestenarna nära namnen har mittår 1035 mot 1037 för övriga
  bönestenar (6 år tidigare, p 0,20; 13 daterade bönestenar nära namnen). Robusthet: sambandet är starkare på stenar
  före 1050 (oddskvot 4,3, 1,5–12,4) än efter (1,4, 0,4–5,3), men skillnaden är inte säker (p 0,067).
- **H2 Platsen, inte gården – faller.** Bönestenarna står relativt närmare namnet än gården (median log2-kvot −0,13
  mot 0,64; 56 % mot 42 % står närmare namnet än närmaste gård), åt hypotesens håll men inte säkert (p 0,17; Fisher
  p 0,26). 56 stenar, 18 med bön.
- **H3 Inte kyrkan – håller.** Med avståndet till tidiga (≤ 1200) och sena kyrkor konstant är oddskvoten 2,56
  (1,40–4,68), Holm-p 0,0045; halva A 2,79 (p 0,009), halva B 2,35 (p 0,026). Kyrkotermerna själva är svaga (tidiga
  0,90 per fördubblat avstånd, p 0,11 tvåsidigt). Robusthet: med tiden konstant 2,57; ristaren som slumpeffekt 2,77;
  bara Uppland och Södermanland 2,60; utan Runor-flyttade 2,58; utan ett namn i taget 2,04–2,90 (lägst utan
  Ullevi). Radien: 1 km 2,84 (p 0,037, 15 stenar), 3 km 1,23 (p 0,20) – mönstret är fortfarande koncentrerat till
  de närmaste två kilometrarna.
- **H4 Andra heliga platser – faller.** Bön inom 2 km från en källa med tradition: 17,5 % mot 14,9 % (oddskvot
  1,17, p 0,23; 211 stenar); ingen halva, ingen radie och ingen kontroll ger ett samband.

## Läsning
Kyrkorna förklarar inte sambandet: bönen står nära de teofora namnen också när närheten till medeltida kyrkor hålls
konstant, och det håller i båda halvorna. Men inget av de tre testen av tolkningen bär den: bönestenarna vid namnen
är inte tidigare, står inte säkert närmare namnet än gården, och bön är inte vanligare vid andra heliga platser
(källor med tradition). Mönstret står kvar som ett samband mellan plats och budskap; att bönen sattes upp
demonstrativt vid den gamla kultplatsen är inte visat.

## Beskrivning
Torslunda (Uppland, flera orter med samma namn) har 18 av de 56 stenarna och 6 bönestenar; Ullevi (Ög, Sö) 3 av 3
med bön; Onslunda 2 av 2. Ingen KMR-offerplats ligger inom 2 km från något av de 18 namnen (närmast 3,3 km vid
Onslunda).

## Artikeln
Enligt planen skrivs ingen artikel: H3 håller men ingen av H1, H2 och H4 stöder.

## Avvikelser
- H2: landskap med färre än 5 stenar nära namnen (Nä, Ög, Vg, Vs) slogs ihop till ”övriga” för att modellen ska gå
  att skatta med 56 stenar.
- Utan ett namn i taget grupperar på namnet, så orter med samma namn (Torslunda, Närlunda, Ullevi) lämnas ut
  tillsammans.
