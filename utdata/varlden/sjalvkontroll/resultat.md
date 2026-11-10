# Självkontroll av ”runstenarna ser mot öster” – resultat

Körd 2026-11-10 efter den låsta planen `analysplaner/2026-11-10-sjalvkontroll-osterled.md` (sha256 656b0c99…, commit
4d00080; kontrollsumman stämde vid körningen). Kod: `ingvarsstenar.py`, `analys.py`, `tid.R`, `kurva.py`. Siffror:
`resultat.json`. Diagram: `tidskurva.png`.

## Domar enligt de låsta reglerna
- **P1 (Sindbæk, utan Ingvarståget): försvagat (obestämt).** Utan Ingvarsstenarna ligger 58 % av platserna i öster
  (95 %-intervall 49–67 %). Punktskattningen är över hälften, men intervallet omfattar 50 %.
- **P2 (Westin, förskjutning mot väster): för få träffar.** De sena stilgrupperna (Pr3–Pr5) har bara 18 platser
  (spärren var 20), med och utan Ingvarsstenarna. Därför finns bara den beskrivande kurvan.

## Ingvarsstenarna
26 kandidater, varav 25 kvar efter granskningen mot texten. Granskningen gjordes innan någon andel räknades
(`ingvarsstenar.csv`, motiveringen i `ingvarsstenar.py`):
- **Borttagen:** U 540. Där är Ingvarr en av resarna och den döde dog i Grekland. Texten har ingen koppling till tåget.
- **Kvar:** Ög 30, efter den breda definitionen. Stenen minns en son som hette Ingvarr och dog i öster.
- **Tre stenar med bara led b:** Ög 30, Sö 179 (”Ingvarr's brother”) och U 540.

Alla 25 har en östlig plats. De är 25 av de 90 stenar som nämner en plats i öster. Sindbæk skrev ”mer än 25” av 96.
Gruppen har 30 östliga platser och 1 västlig.

## P1 i siffror (olika platser per sten, ΣÖ/Σ(Ö + V), klusterbootstrap över stenar)

| | Stenar | Ö | V | Östandel | 95 %-intervall |
|---|---|---|---|---|---|
| Alla (den publicerade siffran) | 136 | 102 | 53 | 65,8 % | 57,8–73,5 |
| **Utan Ingvarsstenarna** | 111 | 72 | 52 | **58,1 %** | **48,8–67,2** |

Skillnaden är −7,7 procentenheter.

Beskrivande (ändrar inte domen):
- **Stenarnas andel** (stenar med en östlig plats bland stenar med en östlig eller västlig plats): 90/136 = 66,2 %
  (Wilson 57,9–73,6). Utan Ingvar: 65/111 = 58,6 % (49,3–67,3).
- **Träffmåttet**, det tidigare 68 %: 68,3 % (60,4–76,0). Utan Ingvar: 58,5 % (49,2–67,6).
- **Smal definition** (bara formeln, 23 stenar): 59,1 % (50,0–67,9).
- **Ingvarståget räknat som en text:** 58,6 % (49,6–67,4).
- **Utan Knutsstenarna** (U 194, U 344, Ög 111): 66,7 % (58,8–74,3).
- **Utan både Ingvar och Knut:** 59,0 % (50,0–68,1).
- **Jämfört med sagorna** (den publicerade analysen): fornaldarsagor 57,6 % (47–69), Heimskringla 39,2 % (31–48),
  islänningasagor 28,9 % (20–37). Utan Ingvar ligger runstenarna lika högt som fornaldarsagorna. De ligger fortfarande
  över Heimskringla och islänningasagorna, och intervallen överlappar inte med någon av dem.

I ord: ungefär hälften av runstenarnas övervikt mot öster (8 av de 16 procentenheterna över hälften) bärs av ett
enda tåg. Utan det ser stenarna fortfarande något oftare mot öster än mot väster, men inte tydligt nog att utesluta
lika ofta.

## P2 och tidskurvan
92 stenar har en plats och en enda säker stilgrupp. Landskapen fördelar sig så här: Uppland 34, Södermanland 30,
Östergötland 7, övriga 21.

| Stilgrupp (Gräslund) | Stenar | Östandel, alla | Östandel utan Ingvar |
|---|---|---|---|
| RAK 980–1015 | 24 | 40 % (20–60) | 36 % (15–56) |
| Fp 1010–1050 | 29 | 79 % (65–92) | 56 % (31–80) |
| Pr1 1010–1050 | 12 | 79 % (54–100) | 79 % (54–100) |
| Pr2 1020–1050 | 10 | 73 % (40–100) | 62 % (8 platser) |
| Pr3 1050–1080 | 10 | 40 % (10–70) | 40 % (10–70) |
| Pr4 1070–1100 | 5 | 6 av 6 | 6 av 6 |
| Pr5 1100–1130 | 2 | 2 av 2 | 2 av 2 |

Tidig mot sen: alla stenar 65 % (89 platser) mot 67 % (18 platser). Utan Ingvar 53 % mot 67 %.

Modellen redovisas bara beskrivande, eftersom spärren inte nåddes:
- **Huvudmodellen:** oddskvot sen mot tidig 0,88 (0,25–3,11) med Ingvar och 1,45 (0,40–5,20) utan.
- **Vida stilgrupper**, som når spärren med 24 sena platser: 0,90 (0,29–2,82). Det vore ”obestämt”.
- **Utan landskap:** 1,07 (0,33–3,41).
- **Utan Knut:** 1,33 (0,33–5,44).
- **Trend på mittåret:** oddskvot per 50 år 2,73 (0,98–7,62), tvåsidigt p 0,056. Utan Ingvar 2,68 (1,02–7,03),
  p 0,046. Den pekar *mot* Westin. Det beror på att RAK-stenarna, de äldsta och mest götaländska, oftast nämner väster
  (England). Som robusthetsprov ändrar den ingen dom.

I ord: runstenarna visar ingen förskjutning mot väster inom 1000-talet. De få sena stenarna räcker inte för någon dom.
Om något har de äldsta stenarna (RAK, omkring år 1000) mest väster, och Ingvarståget ger Fp-gruppen dess topp.

## Avvikelser från planen
- **Knutsstenarna:** i första körningen söktes händelsen med fel stavning (”Knuts gæld” i stället för `src/entities`
  ”Knuts gäld”), och listan blev tom. Felet rättades i koden innan något resultat användes. Det påverkar bara
  Knut-varianterna.
- I övrigt inga avvikelser.

## Förbehåll
Runstenarnas datering kommer från stilgruppen, inte från årtal. Stenarna minns främst dem som dog borta. Att en plats
nämns betyder inte att någon reste dit. Ingvarsdefinitionen är medvetet vid (Ög 30 kan vara en vanlig man som hette
Ingvarr). Med den smala definitionen blir andelen 59,1 % (50,0–67,9), alltså samma dom.
