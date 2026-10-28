# Analysplan: Människorna på runstenarna (r/people.R)

Låst 2026-10-28, innan någon modell nedan har körts. SHA-256 i `analysplaner/2026-10-28-manniskorna.sha256`.
Resultat och avvikelser i R-modulens rapport (Statistik → Människorna) och i `utdata/manniskor/resultat.md`.

## Före låsningen
- Mätningen (`src/people.py`) byggdes och prövades mot handkodning (`data/people_check.json`): urval 1 (60 stenar, som
  reglerna justerades mot) och urval 2 (40 nya stenar, aldrig sedda av reglerna): kvinna bland resarna 39/40, antal män
  bland resarna 38/40, relationsgrupp 38/40. Felen gäller stenar med luckor.
- Sedda siffror (redovisas öppet): 391 läsbara svenska stenar har en kvinna bland resarna; en grov räkning 2026-10-25
  (svenska och danska stenar, utan modell) gav *drengr* på 8 % av stenarna efter söner och bröder mot 0,4 % efter fäder,
  och *þegn* på 5 % efter fäder mot 0,5 % efter söner. Inga modeller med region, tid eller ristare har körts.

## Material
- Svenska vikingatida runstenar (Rundatas svenska landskap), läsbara (`legible`), med personuppgifter ur `people.csv`
  (src/people.py) och korpusen (`corpus.csv`).
- **Landsdel** som i budskapsmodulen (Götaland, Svealand, Gotland, Norrland); huvudkontrasten är Götaland mot Svealand.
- **Tid:** tidsskikt som i messages.R (–1010, 1010–1040, 1040–1070, 1070–, odaterad).
- **Ristaren** som slumpeffekt (`carver_f` som i messages.R), logistisk regression i mgcv.
- **Den döde är ung i släkten** (`ung`): relationsgruppen är barn eller syskon och varken förälder eller make; **äldre**:
  förälder eller make och varken barn eller syskon. Stenar med båda eller ingen ingår inte i test 3–5. I test 3–5 bara
  stenar där alla döda är män (`doda_k = 0`, `doda_m ≥ 1`).

## Test (Holm-korrigerade tillsammans, tvåsidiga, α = 0,05)
1. **Kvinnor bland resarna, landsdel:** y = minst en kvinna bland resarna, bland stenar med minst en identifierad
   resare. y ~ landsdel + tidsskikt + s(ristare). Oddskvot Götaland mot Svealand.
2. **Kvinnor bland resarna, tid:** samma y, bland stilgrupps­daterade stenar: y ~ landsdel + t50 + s(ristare), där
   t50 = (årtal − 1050)/50. Koefficienten för t50.
3. **drengr och åldern:** y = *drengr* nämns. y ~ ung + landsdel + tidsskikt + s(ristare). Oddskvot ung mot äldre.
4. **þegn och åldern:** y = *þegn* nämns, samma modell.
5. **Dog borta och åldern:** y = dog utanför Norden (budskapsregeln `dod_borta`), bland stenar där budskapet är känt.
   Samma modell.
6. **Broar och kvinnor:** y = stenen nämner bro eller väg (`cat_bro_vag`). y ~ kvinna bland resarna + landsdel +
   tidsskikt + s(ristare), bland stenar med minst en identifierad resare. Oddskvot kvinna mot ingen kvinna.

Ett test körs bara om utfallet finns på minst 15 stenar (som MIN_EVENTS i messages.R); annars ”för få”.

## Tolkningsregler
- Varje test prövas också i två halvor av korpusen, delade socken för socken (som i de andra modulerna).
- **Bekräftar:** Holm-p < 0,05 och samma riktning med p < 0,05 i båda halvorna.
- **Mönster att pröva:** Holm-p < 0,05 men inte i båda halvorna.
- **Indikation:** okorrigerat p < 0,05 men Holm-p ≥ 0,05.
- Annars: ingen skillnad påvisad.

## Robusthet (redovisas, ändrar inte utslaget)
1. Bara stenar med minst tio läsbara ord. 2. Bara stenar där alla resares kön är bestämt (test 1, 2, 6).
3. Utan ristarens slumpeffekt (vanlig logistisk regression). 4. Bara Uppland. 5. Test 3–5 med ”ung” = bara söner
(barn), ”äldre” = bara fäder.

## Vad som redovisas oavsett utfall
Alla sex test med antal stenar, antal med utfallet, oddskvot med 95 % intervall, p, Holm-p, halvorna och
robusthetsproven, och andelarna enligt modellen (marginaleffekter) i klartext. Förbehåll: könet och relationen är
lästa ur Rundatas översättning med regler som har fel på omkring en sten av tjugo; luckor i texten gör att kvinnor och
relationer missas oftare än de läggs till; *drengr* och *þegn* kan betyda annat än ålder (ställning, följe).
