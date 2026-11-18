# Tilläggsplan 2: runstenarna vid de stora högarna – högarnas grupper som enhet

Skriven och låst 2026-11-18, innan något av proven nedan har räknats. Tillägg till planerna "Kullarna" (089fcfb5) och
"robusthetstrappan" (53f11fa6). Viktor 2026-11-18: "är rapporten om storhögarna bra?" – svaret var att proven behandlar
varje hög som ett oberoende fall, fast högar ligger i grupper som delar samma runsten. Viktor: "ja" (lås och kör).

## Känt före låsningen
- Trappan (53f11fa6) höll i alla steg med högen som enhet: med stenar på sin plats oddskvot 2,98, inom socken 3,14 osv.
- Räknat efter trappan, för att bedöma beroendet (inga prov): de 47 stora högar som har en sten på sin plats inom 500 m
  har 34 olika stenar nära sig, och de ligger i 21 grupper av stora högar (stora högar inom 500 m från varandra sammanlänkade).
  De 356 mindre högarna med sten har 275 olika stenar. Inget prov med grupper som enhet är räknat.

## Data
Som i 53f11fa6: de 11 072 fristående högarna med angiven diameter, stenar på sin ursprungliga plats (`r_bridge.is_moved`),
landskap = närmaste ISOF-sockens landskap, medeltida kyrkor (Wikidata, före 1350), gravfält.

**Grupper:** högar som ligger inom 1 000 m från varandra länkas samman (enkel länkning, alla högar med diameter, stora
och små). Varje sammanhängande mängd är en grupp; en ensam hög är en egen grupp. 1 000 m väljs därför att två högar inom
1 000 m kan dela en sten inom 500 m.
**Exponering:** gruppen innehåller minst en hög som är minst 20 m bred.
**Utfall:** en runsten på sin plats inom 500 m från någon av gruppens högar (T6: 250 och 1 000 m).
**Gruppstorlek:** antalet högar i gruppen, i klasserna 1, 2–3, 4–9 och 10 eller fler.
**Gruppens landskap, socken, län och halva:** de som flest av gruppens högar har (vid lika: den första i namnordning).
Halvorna som i 089fcfb5 (socknarna växelvis A/B inom länet över alla högar).

## Prov
Mantel–Haenszels oddskvot, grupper med stor hög mot grupper utan, över strata; p tvåsidigt ur omblandning av exponeringen
mellan grupperna inom varje stratum, 10 000 gånger (G5: 2 000), slumpfrö ur denna plans kontrollsumma. Gruppstorleken
ingår i varje stratum.
- **G1.** Strata = landskap × gruppstorlek. Också i båda halvorna.
- **G2.** Som G1 utan grupper där någon hög ligger inom 1 km från en medeltida kyrka.
- **G3.** Strata = socken × gruppstorlek.
- **G4.** Strata = landskap × gruppstorlek × lokal täthet (runstenar på sin plats 1–5 km från gruppens närmaste hög, ”inga”
  eller ”några”, som i 53f11fa6) × gravfält inom 1 km från någon av gruppens högar.
- **G5.** G1 med vart och ett av de landskap som har minst 5 grupper med stor hög utelämnat.
- **G6.** G1 med radien 250 och 1 000 m.
- **Beskrivande:** ett 95-procentsintervall för trappans oddskvot T1 (högen som enhet) ur 2 000 omdragningar av hela
  grupper (klusterbootstrap, strata = landskap).

## När håller det?
Som i 53f11fa6: G1–G4 oddskvot > 1 och p < 0,05; G1 > 1 i båda halvorna med p < 0,05 i en halva med minst 20 grupper med
stor hög och sten; G5 > 1 med varje landskap utelämnat och p < 0,05 när minst två tredjedelar av grupperna med stor hög
är kvar; G6 > 1. Alla villkor ska uppfyllas.

## Om det inte håller
Rapporten (utkast 7hPALFd9lDot4uXbX2Ty) blir "Delvis prövat fynd" enligt mallen, med varje steg som faller uppräknat och
titeln avgränsad till det som håller, eller dras tillbaka om G1 faller. Den publicerade artikeln "Kullarna vid skogens
rand" säger att mönstret håller i alla kontroller; den meningen rättas i så fall efter Viktors besked.

## Utdata
`utdata/hogar/grupper.py` → `utdata/hogar/resultat_grupper.json`.
