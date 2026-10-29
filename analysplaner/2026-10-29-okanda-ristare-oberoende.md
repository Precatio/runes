# Analysplan: De möjliga okända ristarna – delar grupperna något som inte ingår i likheten?

Låst 2026-10-29, innan något nedan har räknats. SHA-256 i `analysplaner/2026-10-29-okanda-ristare-oberoende.sha256`.
Kod `utdata/okanda_ristare/data.py` och `utdata/okanda_ristare/analys.py`, resultat `utdata/okanda_ristare/resultat.md`.

## Bakgrund
`r/anonymous.R` grupperar stenar utan ristare som liknar varandra i stilgrupp, kors, runtyp, stavning, skiljetecken,
formler och runbigram och ligger nära varandra. Fem kandidatgrupper är stabila också utan tidsdragen (korpus
3f58e9339191761e): Konungsund (Ög, 28 stenar), Vetlanda (Sm, 14), Kölaby (Vg, 13), Leksberg (Vg, 6), Husaby (Vg, 6).
Metoden är validerad på kända ristare (85 % mot 69 % för närliggande stenar), men bara i Uppland och Södermanland. Där
kandidaterna ligger har 1–5 % av stenarna en ristare, och grupperna kan lika gärna vara en lokal skrivsed eller en
familjs beställningar. Dragen som skiljer ut grupperna är de som grupperna bildats på, så de bevisar inget.

Frågan: delar gruppernas stenar egenskaper som **inte** ingår i likheten – bergart, storlek och personnamn – oftare än
stenar ur samma trakt och tid? Sett före låsningen: bara hur många stenar som har uppgifterna (bergart i Rundata eller
KMR: 22/28, 13/14, 11/13, 6/6, 5/6; höjd i KMR: 24, 14, 12, 0, 0). Inga värden är jämförda.

## Material
- **Bergart:** `src/geology.families` på Rundatas material; saknas det, på första bergartsordet i KMR-beskrivningen
  (data/raa/kmr_runstenar.json, poster som gäller en enda sten). Två stenar delar bergart när deras familjer
  överlappar (gråsten räknas som granit eller gnejs, som i geology.py).
- **Höjd:** KMR-höjden i data/stone_dimensions.json (status ok, ej fragment), log-skala.
- **Namn:** personnamn ur `src/entities.extract` (osäkra läsningar räknas inte), jämförda vikta (`entities.fold`).
  Två stenar delar namn när de har minst ett gemensamt namn.

## Nollmodell
För varje grupp: trakten = alla svenska runstenar i korpusen inom 30 km (metodens LINK_KM) från gruppens mitt som inte
hör till gruppen. 9 999 slumpvisa mängder av samma storlek dras ur trakten, med samma fördelning på stilgrupp (en sten
med stilgrupp X ersätts av en traktsten med X; finns ingen, av en slumpvis traktsten; stenar utan stilgrupp av stenar
utan stilgrupp). Statistiken räknas bara på stenar som har uppgiften, i gruppen och i varje slumpmängd.
- **S_berg:** andelen par som delar bergart (högre = mer lika).
- **S_höjd:** medelvärdet av |log(höjd_i) − log(höjd_j)| över paren (lägre = mer lika).
- **S_namn:** andelen par som delar ett personnamn.
p för en grupp = (1 + antal slumpmängder minst lika extrema) / 10 000, ensidigt. Grupper med färre än 4 stenar med
uppgiften räknas inte för den uppgiften.

## Test (Holm över H1–H3, α = 0,05)
De fem gruppernas p slås ihop med Fishers metod (grupperna ligger i skilda trakter).
- **H1 Bergart:** grupperna delar bergart oftare än trakten.
- **H2 Storlek:** grupperna är mer lika i höjd än trakten (bara Konungsund, Vetlanda, Kölaby har höjder).
- **H3 Namn:** grupperna delar personnamn oftare än trakten.

## Positiv kontroll (räknas först, avgör vad testen kan säga)
Samma statistik och nollmodell på de kända ristarna i Uppland och Södermanland med minst 5 säkra stenar (gruppen =
ristarens stenar). Fisher över ristarna. Om kontrollen inte ger p < 0,05 för en egenskap kan testet inte se en ristare
genom den egenskapen, och kandidaternas utfall för den egenskapen kallas **inte informativt**.

## Tolkning (bestämd före körningen)
- **Stöd för verkstad eller ristare:** H1 eller H2 håller (Holm-p < 0,05), kontrollen är positiv för samma egenskap,
  och H3 håller inte.
- **Familjens beställningar möjliga:** H3 håller (gruppen kan vara en släkts stenar snarare än en hand).
- **Annars:** ristare och lokal skrivsed går inte att skilja med de här uppgifterna; grupperna förblir möjliga.
Per grupp redovisas p för varje egenskap, men bara den sammanslagna prövningen avgör.

## Beskrivning (prövas inte)
Per grupp: bergarterna, höjderna och de delade namnen; Rundatas litteraturhänvisningar för gruppens stenar (vilka
SRI-volymer och sidor en runolog behöver läsa för att se om gruppen redan är beskriven).

## Förbehåll
Bergarten är ofta grovt angiven (gråsten), och den lokala berggrunden styr; därför jämförs med trakten. Många stenar är
fragment eller saknar mått. Namn delas också av slump i en bygd med vanliga namn. Medelpad (Sättna) prövas inte här;
3D-skanningarna jämförs i ett eget steg, eftersom Rak-studien visade att bergarten styr huggspårsmåtten.
