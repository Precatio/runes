# Lokala ornamenttraditioner (2026-11-26)

Plan `analysplaner/2026-11-26-lokala-ornamenttraditioner.md`, låst före analysen. Skript `data.py` och `traditioner.R`,
utfall `resultat.json`.

## Data
- **Stenarna:** 620 bevarade planschstenar med stilgrupp och härad.
- **Häraderna:** 98.
- **Modellen:** glmer med stilgrupp och landskap som kontroller, och härad och socken inom härad som slumpeffekter.

## Enligt planen
- **D6, kors:** ICC 0,11 (bootstrap 0–0,18). LRT-p = 0,0006, Holm-p = 0,005. **Lokal tradition.**
  - De härader som avviker mest är Trögd (färre kors), Åsunda (färre), Norunda (fler), Lyhundra (färre) och Håbo (fler).
- **D5, extra orm:** Holm-p = 2·10⁻⁵ enligt planens regel. **Modellen är dock degenererad** (se nedan). Resultatet räknas
  inte.
- **Inte lokala efter Holm:**
  - koppel: ICC 0,30, p = 0,017, Holm-p = 0,10;
  - flätverk 0,15 och svans i spiral 0,16, båda med Holm-p = 0,69;
  - mandelöga 0,03, huvud ovanifrån 0 och två eller fler djur 0.

## Kontroll (utforskande, inte i planen)
- **Extra orm:** variansen för socknar inom härad skattas till 547. Det betyder fullständig separation: draget finns nästan
  bara i vissa socknar, och modellen kan inte skatta variansen. Med enbart härad blir LRT 3,9 (p ≈ 0,02), och det klarar
  inte Holm. Det formella utslaget är en effekt av modellen och räknas inte.
- **Kors:** häradets varians 0,41 i båda modellformerna. LRT 10–13. Resultatet står.
- **Koppel:** häradets varians 1,58 (ICC ungefär 0,30). Med enbart härad blir LRT 8,7 (p ≈ 0,002), men i planens modell
  klarar det inte Holm. Det är en antydan och prövas med en egen plan om det ska användas.

## Jämförelse med skrivsättet (beskrivande)
De sex språkdrag med störst täckning gav ICC 0–0,07: skiljetecken 0,03, preposition 0,07 (p = 0,02), stungna runor 0,06,
bön 0, själ 0,05 och signatur 0.

## Vad det betyder och inte betyder
- **När stilgrupp och landskap hålls konstanta skiljer sig de flesta rundjursdrag lite mellan härader.** Huvudets vy, ögat
  och antalet djur följer stilen och inte bygden.
- **Korset varierar mellan bygder:** vissa härader har fler kors än stilen och landskapet förklarar. Det kan vara lokala
  vanor eller hur tidigt kristendomen syntes på stenarna i olika bygder.
- **Kopplet kan vara en lokal tradition,** men det är inte prövat.
- **Den indikation om regional skillnad som Gräslund 1 gav** (Södermanlands Pr3 och Fp) syns alltså inte som tydliga
  bygdetraditioner i de kodade dragen. Den ligger mellan landskapen, som modellen här håller konstant, och inte mellan
  härader.
- **Begränsningar:** urvalet är litet per härad, och flera modeller låg nära gränsen (singulära). Uppland dominerar.
