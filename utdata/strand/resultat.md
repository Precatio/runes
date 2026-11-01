# Resultat: runstenarna, dåtidens strand och gravfälten

Plan: `analysplaner/2026-10-23-strand-och-gravfalt.md` (SHA-256 4ddb7d6c…), tillägget med T1 `analysplaner/2026-10-31-strand-tillagg.md` och tilläggsplanen för robusthetsstegen `analysplaner/2026-11-01-strand-trappan.md` (SHA-256 2993273e…). Statistiken kördes 2026-10-31 22:17 (R version 4.6.1 (2026-06-24)), trappan 2026-11-01 08:44. Kod: `01_avstand.R`, `01b_marginal.R`, `02_r6.R`, `03_statistik.R`, `04_figurer.R`, `05_trappa.R`; siffror `resultat.json` och `trappan.json`; den här filen skrivs av `skriv_resultat.py`.

**Hur siffrorna läses.** *Median* är avståndet som hälften av stenarna (eller punkterna) ligger närmare än. *AUC* är sannolikheten att en slumpvis vald sten står närmare än en slumpvis vald slumppunkt; 0,5 betyder ingen skillnad, 0,63 betyder att stenen står närmare i 63 jämförelser av 100. *p* är sannolikheten att få en så stor skillnad om stenarna hade stått lika slumpvis som punkterna (Wilcoxons rangsummetest, ensidigt). *q* är p justerat för att flera landskap eller prov prövas samtidigt (Benjamini–Hochberg).

## Utfallet i korthet
- **H1 håller** enligt alla fem kriterierna i planen: stenarna står närmare vattnet år 1050 än marken runt dem.
- **H3 håller**: stenarna står närmare gravfälten än marken runt dem, och skillnaden är större än för vattnet.
- **H2: tydligare med dåtidens vatten**, men skillnaden är liten (AUC 0,629 mot dagens 0,620).
- **T1** (bara stenar som alla tre källorna räknar som kvar på platsen) och **alla steg i den låsta trappan** håller för både vattnet och gravfälten.

## Urvalet
- 1 099 vikingatida runstenar som inte är flyttade, i sex landskap: Uppland 623, Södermanland 234, Östergötland 89, Småland 69, Västergötland 64, Öland 20. Stenarna i övriga landskap prövas inte (45 stenar: Västmanland 13, Närke 9, Medelpad 7, Gästrikland 4, Gotland 3, Hälsingland 3, Bohuslän 2, Värmland 2, Dalarna 1, Jämtland 1).
- 10 990 slumppunkter, tio per sten, på land både år 1050 och år 1949, inom 5 km från landskapets stenar.
- Halva A 543 stenar, halva B 556 (hela socknar i samma halva). 935 platser när stenar inom 200 m från varandra slås ihop. 587 stenar har en stilgruppsdatering. 18 633 registrerade gravfält.
- **108 stenar står i vatten år 1050 enligt SGU:s modell** (Uppland 61, Södermanland 31, Östergötland 7, Småland 7, Västergötland 1, Öland 1) och 88 i vatten år 1949. En sten restes inte i vattnet; antalet visar hur grov modellen är nära stränderna (se Svagheter). Deras avstånd räknas som 0; R5 prövar utan dem.

## H1: vattnet år 1050
- **Alla sex landskapen:** 1 099 stenar mot 10 990 punkter: median 305 mot 555 m, inom 500 m 64 % mot 46 %, AUC 0,629, p = 9,1·10⁻⁴⁶. Inom 1 km 83 % mot 76 %. I klartext: hälften av stenarna står högst 305 m från dåtidens vatten, hälften av punkterna högst 555 m; nästan två av tre stenar står inom 500 m, mot knappt hälften av marken.
- Uppland: 623 stenar mot 6 230 punkter: median 305 mot 548 m, inom 500 m 66 % mot 46 %, AUC 0,633, p = 1,9·10⁻²⁸, q = 1,1·10⁻²⁷.
- Södermanland: 234 stenar mot 2 340 punkter: median 190 mot 447 m, inom 500 m 75 % mot 55 %, AUC 0,670, p = 3,7·10⁻¹⁸, q = 1,1·10⁻¹⁷.
- Östergötland: 89 stenar mot 890 punkter: median 445 mot 658 m, inom 500 m 53 % mot 39 %, AUC 0,587, p = 0,003, q = 0,005.
- Småland: 69 stenar mot 690 punkter: median 474 mot 715 m, inom 500 m 52 % mot 36 %, AUC 0,594, p = 0,005, q = 0,006.
- Västergötland: 64 stenar mot 640 punkter: median 602 mot 935 m, inom 500 m 42 % mot 29 %, AUC 0,614, p = 0,001, q = 0,003.
- Öland: 20 stenar mot 200 punkter: median 782 mot 1 111 m, inom 500 m 40 % mot 26 %, AUC 0,607, p = 0,057, q = 0,057.
- Halva A (190 socknar): 543 stenar mot 5 585 punkter: median 305 mot 577 m, inom 500 m 64 % mot 44 %, AUC 0,639, p = 4,4·10⁻²⁷. Halva B (187 socknar): 556 stenar mot 5 405 punkter: median 305 mot 530 m, inom 500 m 64 % mot 47 %, AUC 0,619, p = 1,0·10⁻²⁰.
- Platser i stället för stenar (R4, 935 platser): 935 stenar mot 10 990 punkter: median 316 mot 555 m, inom 500 m 63 % mot 46 %, AUC 0,626, p = 1,0·10⁻³⁷.
- Mönstret syns i fem landskap (q < 0,05): Uppland, Södermanland, Östergötland, Småland, Västergötland. Öland, med 20 stenar, går åt samma håll men räcker inte.

## Dagens vatten (år 1949, som jämförelse)
- Alla: 1 099 stenar mot 10 990 punkter: median 364 mot 601 m, inom 500 m 60 % mot 42 %, AUC 0,620, p = 1,4·10⁻³⁹.
- Per landskap: Uppland AUC 0,622; Södermanland AUC 0,660; Östergötland AUC 0,572; Småland AUC 0,601; Västergötland AUC 0,622; Öland AUC 0,580.

## H2: dåtidens vatten mot dagens
- AUC 0,629 mot dagens 0,620; skillnaden 0,009, 95 %-intervall 0,002 till 0,017 (2 000 bootstrapurval, stenarna dragna plats för plats). Kvoten mellan medianerna 0,55 mot 0,61. Hela intervallet ligger över 0, så enligt planen är närheten *tydligare* mot dåtidens vatten. I klartext: dåtidens strand stämmer något bättre med var stenarna står än dagens, men skillnaden är liten.
- Per landskap (AUC då / nu): Uppland 0,633 / 0,622; Södermanland 0,670 / 0,660; Östergötland 0,587 / 0,572; Småland 0,594 / 0,601; Västergötland 0,614 / 0,622; Öland 0,607 / 0,580. Dåtidens vatten passar bättre i Uppland, Södermanland, Östergötland och på Öland; i Småland och Västergötland passar dagens vatten lika bra eller något bättre.

## H3: gravfälten
- **Alla:** 1 099 stenar mot 10 990 punkter: median 304 mot 1 045 m, inom 500 m 66 % mot 24 %, AUC 0,784, p = 8,4·10⁻²¹³; andelen inom 500 m p = 1,3·10⁻²⁰³. I klartext: två av tre stenar står inom 500 m från ett registrerat gravfält, mot en av fyra punkter.
- Uppland: 623 stenar mot 6 230 punkter: median 274 mot 966 m, inom 500 m 73 % mot 26 %, AUC 0,816, p = 4,3·10⁻¹⁵⁰, q = 2,6·10⁻¹⁴⁹.
- Södermanland: 234 stenar mot 2 340 punkter: median 254 mot 1 003 m, inom 500 m 75 % mot 25 %, AUC 0,820, p = 3,7·10⁻⁵⁹, q = 1,1·10⁻⁵⁸.
- Östergötland: 89 stenar mot 890 punkter: median 479 mot 902 m, inom 500 m 53 % mot 27 %, AUC 0,675, p = 2,5·10⁻⁸, q = 3,7·10⁻⁸.
- Småland: 69 stenar mot 690 punkter: median 855 mot 1 674 m, inom 500 m 35 % mot 9 %, AUC 0,713, p = 2,7·10⁻⁹, q = 5,5·10⁻⁹.
- Västergötland: 64 stenar mot 640 punkter: median 839 mot 1 693 m, inom 500 m 34 % mot 6 %, AUC 0,698, p = 8,9·10⁻⁸, q = 1,1·10⁻⁷.
- Öland: 20 stenar mot 200 punkter: median 1 058 mot 1 050 m, inom 500 m 25 % mot 20 %, AUC 0,519, p = 0,39, q = 0,39.
- Halva A: 543 stenar mot 5 585 punkter: median 301 mot 1 113 m, inom 500 m 64 % mot 22 %, AUC 0,790, p = 1,5·10⁻¹¹⁰. Halva B: 556 stenar mot 5 405 punkter: median 310 mot 983 m, inom 500 m 69 % mot 25 %, AUC 0,778, p = 4,5·10⁻¹⁰⁴.
- Platser (R4, 935): 935 stenar mot 10 990 punkter: median 329 mot 1 045 m, inom 500 m 64 % mot 24 %, AUC 0,771, p = 1,9·10⁻¹⁶⁷.

## Sekundära prov (Benjamini–Hochberg över de fem)
- **S1a, Närmare vatten år 1050, med närheten till gravfält konstant (oddskvot när avståndet halveras):** oddskvot 1,72 (95 %-intervall 1,58–1,87), q = 2,1·10⁻³⁵; halva A 1,84, halva B 1,62, replikerat.
- **S1b, Närmare gravfält, med närheten till vatten år 1050 konstant (oddskvot när avståndet halveras):** oddskvot 3,46 (95 %-intervall 3,18–3,76), q = 4,6·10⁻¹⁸⁶; halva A 3,50, halva B 3,43, replikerat.
  I klartext: när avståndet till vattnet halveras blir oddsen för att platsen har en sten 1,7 gånger så stora, också med avståndet till gravfält lika; för gravfälten är talet 3,5. Vattnet är alltså inte bara ett tecken på gravfälten, och tvärtom.
- **S2, Inom 1 km från vatten år 1050 över tid (per 50 år):** oddskvot 0,66 per 50 år (0,42–1,05), p = 0,082, q = 0,10. Inom 1 km: tidiga 84 % (335 stenar), sena 84 % (252). Ingen förändring över tid.
- **S3, Kristna markörer och närhet till vatten år 1050 (tiden konstant):** oddskvot 0,83 (0,50–1,37), p = 0,47. Inom 1 km: med kristen markör 85 % (385), utan 83 % (202). Ingen skillnad.
- **S4, Bro- och vägstenar och närhet till vatten år 1050:** oddskvot 2,08 (0,97–4,45), p = 0,059, q = 0,10. 82 bro- och vägstenar, median 207 m mot 309 m för övriga; inom 1 km 90 % mot 83 %. Åt väntat håll men inte säkert.

## Planens robusthetsprov (för H1, och H3 där det står)
- **R1, tidssnitt:** år 750 AUC 0,630, p = 1,6·10⁻⁴⁶; år 950 AUC 0,629, p = 7,8·10⁻⁴⁶; år 1150 AUC 0,626, p = 7,5·10⁻⁴⁴; år 1250 AUC 0,625, p = 4,6·10⁻⁴³; år 550 AUC 0,635, p = 1,1·10⁻⁴⁹; år 1550 AUC 0,621, p = 3,5·10⁻⁴⁰. Resultatet hänger inte på att just år 1050 valts; SGU anger en tidsosäkerhet på upp till 500 år.
- **R2, bara havet** (utan modellens sjöar): 1 099 stenar mot 10 990 punkter: median 2 975 mot 4 496 m, inom 500 m 19 % mot 12 %, AUC 0,566, p = 1,7·10⁻¹³. Per landskap: Uppland AUC 0,597, p = 4,8·10⁻¹⁶; Södermanland AUC 0,573, p = 1,2·10⁻⁴; Östergötland AUC 0,521, p = 0,26; Småland AUC 0,521, p = 0,28; Västergötland AUC 0,513, p = 0,37; Öland AUC 0,654, p = 0,012. I Östergötland, Småland och Västergötland ligger de flesta stenar och punkter mil från havet, så där säger provet inget; kriteriet gäller alla sex sammantaget.
- **R4, platser:** se H1 och H3.
- **R5, utan de 108 stenarna i vattnet:** 991 stenar mot 10 990 punkter: median 372 mot 555 m, inom 500 m 60 % mot 46 %, AUC 0,589, p = 7,4·10⁻²¹. Svagare men tydligt.
- **R6, Copernicus höjdmodell med landskapets landhöjning ±1 m:** δ = −1 m: median 335 mot 570 m, AUC 0,630, p = 2,4·10⁻⁴⁶; δ = 0 m: median 301 mot 560 m, AUC 0,637, p = 2,7·10⁻⁵¹; δ = +1 m: median 285 mot 552 m, AUC 0,645, p = 3,1·10⁻⁵⁷. Alla tre håller sammantaget, och i alla landskap utom Öland (AUC 0,58–0,59, p 0,09–0,11). Mönstret hänger alltså inte på SGU:s modell.
- **R7, nollmodellens radie:** 2 km: vattnet AUC 0,628 (p = 8,4·10⁻⁴⁵), gravfälten AUC 0,707 (p = 2,8·10⁻¹¹⁴); 10 km: vattnet AUC 0,627 (p = 4,9·10⁻⁴⁴), gravfälten AUC 0,829 (p = 6,2·10⁻²⁸⁵). Vattnet är nästan oberoende av radien; för gravfälten växer skillnaden med radien, troligen eftersom gravfälten ligger i bygderna och en större radie tar med mer obebyggd mark.

## T1: bara stenar som står kvar enligt alla tre källorna (tillägget 2026-10-31)
- 657 stenar kvar; bort: Uppland 274, Södermanland 90, Östergötland 31, Småland 27, Västergötland 11, Öland 9.
- Vattnet: 657 stenar mot 10 990 punkter: median 301 mot 555 m, inom 500 m 63 % mot 46 %, AUC 0,629, p = 5,1·10⁻²⁹. Gravfälten: 657 stenar mot 10 990 punkter: median 279 mot 1 045 m, inom 500 m 67 % mot 24 %, AUC 0,786, p = 5,5·10⁻¹³⁵. Båda **håller**.

## Trappan (tilläggsplanen 2026-11-01)
**Vattnet år 1050: alla steg håller.**
- Halva A: 543 stenar mot 5 585 punkter: median 305 mot 577 m, inom 500 m 64 % mot 44 %, AUC 0,639, p = 4,4·10⁻²⁷.
- Halva B: 556 stenar mot 5 405 punkter: median 305 mot 530 m, inom 500 m 64 % mot 47 %, AUC 0,619, p = 1,0·10⁻²⁰.
- Socknen som enhet, 373 socknar: 373 stenar mot 10 990 punkter: median 336 mot 555 m, inom 500 m 62 % mot 46 %, AUC 0,607, p = 1,2·10⁻¹².
- En sten per ristare, 332 bort: 767 stenar mot 7 879 punkter: median 313 mot 570 m, inom 500 m 62 % mot 45 %, AUC 0,621, p = 8,4·10⁻²⁹.
- Utan återresta stenar, 101 bort: 998 stenar mot 9 941 punkter: median 307 mot 559 m, inom 500 m 63 % mot 45 %, AUC 0,628, p = 9,9·10⁻⁴¹.
- Utan flyttade stenar enligt Runor 2020, 177 bort: 922 stenar mot 9 139 punkter: median 305 mot 553 m, inom 500 m 64 % mot 46 %, AUC 0,630, p = 7,0·10⁻³⁹.
- Dagens flyttregel, 295 bort: 804 stenar mot 8 260 punkter: median 305 mot 562 m, inom 500 m 63 % mot 45 %, AUC 0,627, p = 4,3·10⁻³³.
- Tidiga stenar (före 1050): 335 stenar mot 3 543 punkter: median 276 mot 575 m, inom 500 m 65 % mot 44 %, AUC 0,646, p = 3,5·10⁻¹⁹.
- Sena stenar (1050 och senare): 252 stenar mot 2 527 punkter: median 336 mot 534 m, inom 500 m 64 % mot 47 %, AUC 0,619, p = 2,2·10⁻¹⁰.
- Socknen som slumpeffekt (373 socknar): oddskvot 1,82 när avståndet halveras (95 %-intervall 1,68–1,98), p = 3,1·10⁻⁴⁶. I klartext: också jämfört med marken i samma socken står stenarna närmare.
- Utan ett landskap i taget: utan Uppland (43 % kvar) AUC 0,624, p = 2,2·10⁻¹⁹; utan Södermanland (79 % kvar) AUC 0,620, p = 8,8·10⁻³²; utan Östergötland (92 % kvar) AUC 0,634, p = 6,0·10⁻⁴⁵; utan Småland (94 % kvar) AUC 0,631, p = 2,6·10⁻⁴⁴; utan Västergötland (94 % kvar) AUC 0,632, p = 4,6·10⁻⁴⁵; utan Öland (98 % kvar) AUC 0,631, p = 5,7·10⁻⁴⁶.

**Gravfälten: alla steg håller.**
- Halva A: 543 stenar mot 5 585 punkter: median 301 mot 1 113 m, inom 500 m 64 % mot 22 %, AUC 0,790, p = 1,5·10⁻¹¹⁰.
- Halva B: 556 stenar mot 5 405 punkter: median 310 mot 983 m, inom 500 m 69 % mot 25 %, AUC 0,778, p = 4,5·10⁻¹⁰⁴.
- Socknen som enhet, 373 socknar: 373 stenar mot 10 990 punkter: median 408 mot 1 045 m, inom 500 m 58 % mot 24 %, AUC 0,724, p = 1,8·10⁻⁴⁹.
- En sten per ristare, 332 bort: 767 stenar mot 7 879 punkter: median 320 mot 1 112 m, inom 500 m 64 % mot 22 %, AUC 0,778, p = 1,8·10⁻¹⁴³.
- Utan återresta stenar, 101 bort: 998 stenar mot 9 941 punkter: median 302 mot 1 028 m, inom 500 m 67 % mot 24 %, AUC 0,784, p = 3,9·10⁻¹⁹³.
- Utan flyttade stenar enligt Runor 2020, 177 bort: 922 stenar mot 9 139 punkter: median 296 mot 1 059 m, inom 500 m 67 % mot 23 %, AUC 0,788, p = 6,8·10⁻¹⁸⁴.
- Dagens flyttregel, 295 bort: 804 stenar mot 8 260 punkter: median 285 mot 1 098 m, inom 500 m 68 % mot 22 %, AUC 0,794, p = 1,1·10⁻¹⁶⁷.
- Tidiga stenar (före 1050): 335 stenar mot 3 543 punkter: median 285 mot 1 127 m, inom 500 m 65 % mot 21 %, AUC 0,782, p = 1,1·10⁻⁶⁵.
- Sena stenar (1050 och senare): 252 stenar mot 2 527 punkter: median 314 mot 972 m, inom 500 m 71 % mot 25 %, AUC 0,799, p = 1,0·10⁻⁵⁵.
- Socknen som slumpeffekt (373 socknar): oddskvot 3,57 när avståndet halveras (95 %-intervall 3,27–3,89), p = 7,2·10⁻¹⁸⁴. I klartext: också jämfört med marken i samma socken står stenarna närmare.
- Utan ett landskap i taget: utan Uppland (43 % kvar) AUC 0,745, p = 8,0·10⁻⁷⁰; utan Södermanland (79 % kvar) AUC 0,775, p = 6,0·10⁻¹⁵⁷; utan Östergötland (92 % kvar) AUC 0,793, p = 2,9·10⁻²⁰⁸; utan Småland (94 % kvar) AUC 0,791, p = 7,5·10⁻²¹⁰; utan Västergötland (94 % kvar) AUC 0,791, p = 7,6·10⁻²¹⁰; utan Öland (98 % kvar) AUC 0,788, p = 3,8·10⁻²¹⁵.

Antal: 101 återresta stenar enligt ordlistan, 177 flyttade enligt Runor, 295 som dagens regel inte räknar som kvar, 67 säkra ristare med 399 stenar, 335 tidiga och 252 sena stenar.

## Jämförelser (beskrivande)
- **D1, med flyttade stenar:** 2 167 stenar (1 068 flyttade). Vattnet år 1050: AUC 0,650; bara de flyttade: median 285 m, AUC 0,659. De flyttade stenarna, som oftast står vid kyrkor, står ännu närmare dåtidens vatten än de som står kvar, så att räkna med dem hade gjort sambandet något starkare än det är.
- **D2, projektets tidigare mått** (Natural Earths grova vattenlager, landhöjningen som en grov höjdgräns på en höjdmodell med omkring 300 m upplösning, flyttade stenar med): 2 254 stenar, median 3,61 mot 5,31 km. Medianerna här är mycket kortare, eftersom SGU:s modell också har de mindre sjöarna; riktningen är densamma. Gravfälten i det tidigare måttet: 66 % mot 24 % inom 500 m.

## Avvikelser från planen
- **Tidsordningen.** Planen fick sin kontrollsumma 2026-10-23 kl. 17.23 och lades in i versionshanteringen kl. 19.30 (c0afbc8). Kl. 17.32 kördes en provkörning med en äldre version av skriptet; dess logg (`/Volumes/2TB/cache/strand/run.log`) visar bara förloppet (”H1 klart”), inga siffror, och den sparade inga resultat. Avstånden räknades kl. 20.14 (steg 1), R6 för Uppland, Södermanland, Östergötland och Öland samma kväll, R6 för Småland och Västergötland och statistiken först 2026-10-31 kl. 22.17, efter tillägget med T1.
- **T1** lades till i ett låst tillägg 2026-10-31, innan statistiken kördes, eftersom regeln för flyttade stenar hade rättats efter att planen låstes. Planens egna prov är oförändrade.
- **Trappan** lades till i en låst tilläggsplan 2026-11-01, efter att planens resultat var kända, för att pröva fyndet med projektets fasta känslighetsanalyser. Den ändrar inte planens utfall.
- **Genomförandet:** avstånden räknades i rutor med 25 m celler; 15 590 avstånd som nådde rutans marginal (nästan alla i R2, bara havet, långt inne i landet) räknades om på en raster med 100 m celler över hela landskapet (steg 1b). Planen anger ingen cellstorlek.
- I övrigt inga.

## Svagheter
- SGU:s modell är regional (höjdmodell med 50 m upplösning, tidsfel upp till 500 år, tröskelhöjder med fel under 5 m) och inte avsedd för detaljstudier; sjöarna är ungefärliga, och åar, bäckar och våtmarker saknas. Att 108 stenar hamnar i modellens vatten visar det.
- En stens plats i Rundata kan avvika från den ursprungliga även när stenen inte räknas som flyttad (därför T1 och stegen med återresta och flyttade stenar).
- Kulturmiljöregistret är olika väl inventerat i olika trakter, och gravfälten är oftast odaterade; en del av dem kan vara yngre eller äldre än stenarna.
- Stenar som står i grupp är inte oberoende (därför platserna och socknen som enhet).
- De små landskapen har få stenar; Öland visar inget säkert.
- Slumppunkterna ligger inom 5 km från stenarna, alltså i bygder där stenar restes. Provet visar var i bygden stenarna står, inte varför bygden ligger där den ligger.
