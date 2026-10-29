# Analysplan: Upptäcktsmotorn, version 2 – bredare drag, lokala avvikelser och udda stenar

Låst 2026-10-29, innan motorn har körts. SHA-256 i `analysplaner/2026-10-29-upptacktsmotorn-v2.sha256`. Kod:
`src/discovery_v2.py` (dragen), `r/discovery_v2.R` (del 1), `r/discovery_lokal.R` (del 2 och 3). Resultat i
`utdata/upptackt_v2/`.

## Bakgrund
Version 1 (analysplaner/2026-10-28-upptacktsmotorn.md, 28b51bc) bekräftade 14 par, mest väntad familjestruktur och en
mätartefakt (o-runan × son). Viktor 2026-10-29: bredda sättet vi ser på datan. Version 2 gör tre saker: fler slags
drag (ord, material, ortnamnsmiljö, stengrupper), ett nytt sätt att leta (bygder där ett drag är vanligare än landskap
och tid förklarar) och en lista över udda stenar. Sett före låsningen: ordformernas frekvenser i korpusen och
materialfördelningen (granit 506, sandsten 122, gråsten 80 …); inga samband.

## Material
Som version 1: svenska vikingatida runstenar i korpus 3f58e9339191761e med minst fyra läsbara ord; halvorna socken för
socken som i change.R (A upptäcker, B bekräftar). Kontroller överallt: landskap, tidsskikt (odaterad eget skikt),
log(1 + läsbara ord).

## Dragen
Alla version 1:s drag, plus:
- **Ord:** ordformer i Rundatas normalisering, med samma regler som r/words.R (namn, skadade ord och lösa fragment
  ingår inte), som står på minst 30 stenar och högst hälften av stenarna; de 60 vanligaste av dem. Familj *ord*.
- **Material:** granit (alla material som innehåller ”granit”), sandsten, kalksten, gnejs; 1/0 bland stenar med
  angivet material. Familj *material*.
- **Ortnamnsmiljö** (stenar på sin plats, som analysplaner/2026-10-29-familjens-plats.md): gammalt bebyggelsenamn inom
  1 km, ungt inom 1 km, kultnamn (A eller B) inom 2 km, centralortsnamn inom 5 km. Familj *landskap*.
- **I grupp:** annan sten på sin plats 25–500 m bort (1) mot ingen (0), bland stenar på sin plats. Familj *landskap*.

**Familjer, rättade efter version 1:** resarnas drag och relationerna blir en familj (*familj*). Prövas inte:
- par inom samma familj (som version 1);
- ett *ord* mot något drag som läses ur texten: ord, familj, resa, arv, kristen, egen, beröm, hednisk, bro, ting,
  död kvinna, ristare (signatur), stungna och de ordbundna dragen;
- ett **ordbundet drag** (monoftong, au-monoftong, o-runa, r för ʀ, prepositionen *at*, h saknas, nasal utelämnad)
  mot ord, familj, resa, arv, kristen, egen, beröm, hednisk, bro, ting eller död kvinna.

## Del 1: bredare parskanning
Exakt version 1:s två steg (r/discovery.R): halva A, glm b ~ a + kontroller, båda dragen på minst 20 stenar och
saknas på minst 20; kandidat vid BH-q < 0,05 och oddskvot ≥ 1,5 åt något håll; högst 50 kandidater, frysta med SHA-256
innan halva B läses; halva B med ristaren som slumpeffekt (mgcv), ensidigt; **bekräftad** vid Holm-p < 0,05, **mönster
att pröva** vid BH-q < 0,05. Sekundärt med halvorna bytta. Par som redan bekräftades i version 1 märks så.

## Del 2: lokala avvikelser – bygder där ett drag är vanligare än väntat
**Stenar:** de som står på sin plats eller vid en kyrka (kyrkan i samma socken; definition som
analysplaner/2026-10-29-kyrkan-tog-over.md), inte i museum eller samling, med koordinater. **Drag:** alla utom familjerna
landskap och material (de är platsens egenskaper själva), med minst 30 fall och 30 icke-fall bland halvans stenar.
- **Förväntat:** för varje sten p = glm(drag ~ landskap + tidsskikt + log ord), skattad i samma halva.
- **Upptäcka (halva A):** cirklar runt varje sten med dess k närmaste stenar i halvan, k från 10 till 5 % av halvans
  stenar, radie högst 30 km. Kulldorffs statistik med förväntat = summan av p (bara överskott). Mest sannolika
  klustret per drag; p från 999 simuleringar där varje sten får draget med sin sannolikhet p. **Kandidat:** BH-q < 0,05
  över dragen och observerat/förväntat ≥ 1,5. Kandidaterna (drag, mittpunkt, radie) fryses med SHA-256.
- **Bekräfta (halva B):** samma cirkel (mittpunkt och radie i meter), halva B:s stenar i den, förväntat ur halva B:s
  egen modell; ensidigt p = andelen av 9 999 simuleringar med minst så många fall. **Bekräftad:** Holm-p < 0,05.
  **Mönster att pröva:** okorrigerat p < 0,05.

## Del 3: udda stenar (beskrivning, prövas inte)
För varje sten med minst tio kända drag (ej landskap och material): överraskningen = summan över dragen av
−log₂ P(stenens värde) minus den väntade summan, där P kommer ur samma glm som i del 2 men skattad på alla stenar.
De 25 mest överraskande stenarna redovisas med de tre drag som bidrar mest. Listan är förslag till närläsning, inget fynd.

## Efteråt
Bekräftade par och kluster som är kända (mönsterregistret, hotspots-modulen, forskningen) märks så. Nya blir förslag
till egna låsta planer och läggs inte direkt i Statistik.

## Förbehåll
Ordformer är stavningar: samma ord i olika former räknas var för sig. Ortnamnen är dagens. Lokala kluster kan vara en
ristares eller verkstads område; ristaren finns inte i del 2:s modell, så bekräftade kluster jämförs efteråt med
ristarna i cirkeln (redovisas).
