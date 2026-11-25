# Skrev och ritade samma hand? (2026-11-25)

Plan `analysplaner/2026-11-25-skrev-och-ritade.md` (sha 7ae43d01), låst före jämförelsen. Skript `skrev_ritade.py`, utfall
`skrev_ritade.json`.

## Data
- **Stenarna:** 580 med både ornamentkod (SRI:s planscher, minst tre eniga drag), stavningsprofil (minst tre ord) och en
  stilgrupp i Rundata.
- **Paren:** 6 748 par inom 30 km i samma stilgrupp. 6 387 av dem har minst tre jämförbara ornamentdrag.

## Prov enligt planen
- **P1, stavning mot ornamentik i stenpar:** **håller inte.**
  - Spearmans ρ är 0,022.
  - När ornamentkoderna blandas om inom härad och stilgrupp blir medelvärdet 0,011, och 95 % av omblandningarna ligger
    under 0,045. p = 0,29.
  - Ett samband större än omkring 0,05 utöver bygd och stilgrupp kan alltså uteslutas.
- **P3, inom Pr4 (3 485 par):** håller inte. ρ = 0,030 mot 0,026, p = 0,46.
- **P2, ristarna som enheter:** bara 4 signerade ristare har minst fem stenar med båda måtten: Öpir, Balle, Åsmund och
  Visäte. Enligt planen redovisas det bara beskrivande. Partiellt ρ = 0,83, p = 0,24, men med 4 ristare finns bara 6 par.
- **Beskrivande:**
  - Utan par från samma socken: ρ = 0,022, p = 0,27.
  - Per stilgrupp: Pr1 0,30 (109 par), Fp 0,15, Pr2 0,10, Pr3 0,04, Pr4 0,03, RAK −0,10 och Pr5 −0,12.
  - Planens "språkdrag" (`trait_*`, `cat_*`, `pm_*` behandlade som tal) mot ornamentik: ρ = 0,29 mot 0,10, p = 0,001.
    **Se rättelsen nedan:** måttet var i praktiken budskapet, inte språkdragen.

## Rättelse och utforskande kontroller (inte i planen)
- **Planens sekundära mått mätte budskapet.** `trait_*` är kategoriska ("ja"/"nej" med flera) och blev noll vid den
  numeriska omvandlingen. Måttet bestod därför bara av budskapskategorierna (`cat_*`, `pm_*`). Felet är känt från
  beläggen, där det åtgärdades med lika/olika-mått, men det följde med i planens formulering.
- **Språkdragen rätt behandlade** (andel lika värden mellan stenarna) mot ornamentik: ρ = 0,017 mot 0,036, p = 0,75.
  **Inget samband.**
- **Budskapet utan kors, kristna formler, själ, bön och hedniskt:** ρ = 0,19 mot 0,08, p = 0,005, 199 omblandningar.
  Budskapets typ (minne, bro och väg, färd, arv, ting med flera) följer alltså ornamentiken även utan det uppenbart
  korsrelaterade.

## Vad det betyder och inte betyder
- **Hur texten är skriven följer inte hur djuret är ritat.** Det gäller både stavning och språkdrag, när bygd och
  stilgrupp hålls konstanta.
- **Vad texten säger följer däremot bilden.** Fyndet är utforskande och behöver ett eget låst prov på ett oberoende urval.
- **Två tolkningar är möjliga:**
  - Text och bild kunde ha olika upphov (en arbetsdelning), medan budskap och bild bestämdes tillsammans, kanske av
    beställaren.
  - Båda måtten bär handen så svagt att deras gemensamma del inte syns. Ornamentiken bär en signal om handen (grinden G1),
    och det gör stavningen också (nya_hander N1). Men två svaga signaler ger en mycket svag samvariation.
- **Avgränsningen är ändå ett resultat:** samvariationen utöver bygd och stilgrupp är högst omkring 0,05.
- **P2 kunde inte prövas.** För få signerade ristare har stenar med båda måtten. Ristarnivån kräver fler signerade stenar
  med ornamentkod, till exempel genom huvudsläsningen och de förlorade stenarna.

## Bekräftande prov: följer budskapet bilden? (2026-11-25)
Plan `analysplaner/2026-11-25-budskap-och-bild.md` (sha 73c2c690), låst före analysen. Skript `budskap_bild.py`, utfall
`budskap_bild.json`.

### Urvalet
- **Ett oberoende urval:** 442 stenar som inte ingick i första urvalet.
  - Planschstenar utan stilgrupp: 274. Förlorade stenar ur teckningar: 132. Gotland, Öland, Hälsingland och Medelpad: 36.
  - Planen räknade med 456 stenar. Den räkningen tog med fält som inte är godkända. Med bara godkända fält, som planen
    föreskriver för måttet, blir det 442.
- **Paren:** 8 536 inom 30 km.

### Utfall
- **B1: håller.** Budskap (12 kategorier) mot ornamentik ger ρ = 0,227, mot 0,013 vid omblandning inom härad och källa.
  p = 0,001.
  - **Per källa:** planscher 0,19 (p = 0,002) och teckningar 0,28 (p = 0,002).
  - **I samma stilgrupp:** bara 83 par, ρ = 0,16, p = 0,09.
  - **De språkliga markörerna:** inget samband (0,031, p = 0,15).
- **Varje kategori utelämnad:** utan `pm_neutral` ("utan religiösa markörer i texten") faller ρ till **0,025**. Övriga
  kategorier ändrar nästan ingenting (0,226–0,251).

### Utforskande kontroll (inte i planen)
- **Ornamentiken utan fältet "kors":** budskapet ger ρ = 0,062 (p = 0,007).
- **Utan både korset och `pm_neutral`:** ρ = 0,040 (p = 0,14).

### Vad det betyder
- **B1 håller formellt, men sambandet är i huvudsak det kända.** En text med religiösa (kristna) markörer går ihop med ett
  kors i bilden. När korset tas bort återstår en liten rest, troligen tiden: texter utan religiösa markörer är ofta äldre
  och har annan stil.
- **Fyndet i första urvalet var alltså inget nytt samband mellan budskap och bild.** Det är det väntade sambandet mellan tro
  och kors.
- **Det är en validering av registret.** Läsarna kodade bara bilden, och deras koder fångar det samband mellan text och
  bild som borde finnas. Det stärker förtroendet för koderna.
- **Slutsatsen om skrivsättet står fast.** Stavning och språkdrag följer inte bilden utöver bygd och stilgrupp (P1).
