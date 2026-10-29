# Analysplan: Restes stengrupperna under en generation?

Låst 2026-10-29, innan något nedan har räknats. SHA-256 i `analysplaner/2026-10-29-en-generation.sha256`.
Kod `utdata/familjens_plats/generation.py`, resultat `utdata/familjens_plats/generation_resultat.md`.

## Bakgrund
I planen Familjens plats (analysplaner/2026-10-29-familjens-plats.md, resultat 64f2c7f) var test 14 ensidigt åt
”fler stilgrupper”. Utfallet gick åt motsatt håll: 42 grupper med 97 stildaterade stenar hade i medel 1,57 olika
stilgrupper mot 1,92 vid omblandning inom landskapet (nedre svansen p 0,0001, båda halvorna 0,001). Det är en
iakttagelse, inte ett fynd: stilgrupperna varierar geografiskt inom landskapen, så en grupp kan likna sig själv bara
för att bygden gjorde det. Den här planen prövar mot bygden i stället för landskapet. Inga lokala jämförelser har räknats.

## Material
- **Grupper:** som i Familjens plats – svenska runstenar på sin plats (`moved = 0`, `lost = 0`) med koordinater,
  korpus 3f58e9339191761e; sammanhängande stenar 25–500 m isär; gruppen räknas om minst två stenar är stildaterade
  (RAK, Fp, Pr1–Pr5). Bara de stildaterade stenarna ingår i statistiken.
- **Bygdens stenar (jämförelsepoolen) för en grupp:** alla stildaterade svenska runstenar med koordinater, också
  flyttade (ej försvunna), inom 10 km från någon av gruppens stenar, men inte gruppens egna stenar och inte stenar
  inom 500 m från någon av dem. En grupp ingår bara om poolen har minst 10 stenar.

## Test
Statistik: medelantalet olika stilgrupper per grupp. **Nollmodell:** för varje grupp dras lika många stenar som den har
stildaterade, utan återläggning, ur dess bygdepool; 9 999 dragningar. Ensidigt: p = (1 + antal dragningar med medel
≤ det observerade) / 10 000.
- **Håller:** p < 0,05 i alla grupper tillsammans och p < 0,05 i båda halvorna (grupperna efter sockenhalvan för
  gruppens första sten, socken för socken som i change.R).
- **Antydan:** p < 0,05 men inte i båda halvorna. Annars ingen skillnad påvisad.

## Robusthet (redovisas, ändrar inte utslaget)
1. Bygd 5 km och 20 km.
2. Poolen bara stenar på sin plats.
3. **Ristaren:** grupper där alla stildaterade stenar har samma säkra ristare tas bort (en ristare ger en stil).
4. Bara Uppland och Södermanland.
5. Statistiken ”andel grupper där alla stenar har samma stilgrupp” i stället för medelantalet.

## Beskrivning (prövas inte)
Gruppernas spännvidd i år (senaste stilgruppens mitt minus tidigaste), mot dragningarna; antal grupper per landskap.

## Förbehåll
Stilgrupperna är 25–50 år breda, så ”samma stilgrupp” betyder ungefär samma generation, inte samma år. Bara en
tredjedel av stenarna står på sin plats. Stilgrupperna bygger delvis på ristarna; prov 3 visar hur mycket av mönstret
som är en ristares eller verkstads stil.
