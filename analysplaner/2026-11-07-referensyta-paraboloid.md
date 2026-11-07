# Analysplan: referensytan i huggspårsanalysen – fyrkantig stängning eller rullande paraboloid (kandidat `groove-8`)

Skriven och låst 2026-11-07, innan något av proven nedan har körts. Viktor 2026-11-07: "om vi förbättrar appen bör det
göras" (om att byta referensytan i huggspårsmätningen, inte bara i dialogen *Skala av vittringen*).

## Bakgrund och känt före låsningen
Huggspårsanalysen (`src/auto_grooves.reference_surface`, metodversion `groove-7`) räknar stenytan utan ristningar som en
morfologisk stängning med ett **fyrkantigt** fönster om 20 mm, utjämnad 1 mm. Två brister syntes när *Skala av
vittringen* byggdes (f5bb0e1): lutningskartan över Sö 206 visar trappsteg och rutor, och ett fyrkantigt fönster är
**riktningsberoende** (diagonalt 41 % bredare än längs axlarna), så att ett snett spår mäts mot en annan referens än ett
lodrätt. Dialogen använder i stället en rullande paraboloid (krökningsradie 50 mm, räckvidd 30 mm). Inga mått med
paraboloiden i huggspårsanalysen är räknade.

## Kandidaten
`reference_surface(..., kind="paraboloid")`: stängning med paraboloid (radie 50 mm, räckvidd 1,5 × skalan, alltså 30 mm vid
20 mm), därefter samma utjämning 1 mm. Allt annat i analysen är oförändrat (tröskel, slingor, snitt, mätningen i varje
tvärsnitt). Samma byte gäller klick-snittens lokala referens (`auto_slice`) och ytan för bilderna (`stone_report.Surface`).

## Prov
**S1 Riktningsberoende (konstgjort).** Ett plant höjdfält (0,5 mm per cell) med lätt brus (0,03 mm) och raka V-spår
(bredd 8 mm, djup 2 mm) i riktningarna 0°, 22,5°, 45° och 67,5°. Djupet under referensen mitt i varje spår, och
spårmaskens bredd vid tröskeln 0,3 mm. Mått: största skillnad mellan riktningarna och största avvikelse från det sanna
djupet. **Håller** om paraboloiden har både mindre skillnad mellan riktningarna och högst lika stor avvikelse från det sanna
djupet som den fyrkantiga.

**S2 Täckning (riktiga stenar).** De 35 KÅ-skanningarna från Södermanland (Kitzler Åhfeldt 2024, doi:10.5281/zenodo.11951255)
i djupbildscachen, med ritade slingor, protokollets parametrar och `measure="runes"`, en process per körning och
referensyta. Per sten: runor med minst ett godkänt snitt delat med textens runor (som `utdata/stavlosa/ka_tabell.py`).
**Håller** om medianen över stenar med minst tio textrunor med paraboloiden är minst medianen med den fyrkantiga minus
0,05.

**S3 Stabilitet.** Godkända snitt som ligger högst 1,5 mm från varandra i de två körningarna paras. **Håller** om
medianen av den absoluta skillnaden i V-vinkel över alla par är högst 2°, och stenens median-V-vinkel ändras högst 2°
på minst 90 % av stenarna (stenar med minst tio parade snitt).

**S4 Beskrivande.** Antal godkända snitt, mediandjup och medianbredd per sten, körtid.

## Beslut (bestämt nu)
Håller S1, S2 och S3 blir paraboloiden standard i en ny metodversion `groove-8` (api/config.py `METHOD_VERSION`,
METHODS 2 och 2c, ändringslogg, bristlistan, nyhet); korpusposter och referensmätningar med `groove-7` görs om. Håller
något av dem inte förblir den fyrkantiga stängningen standard, paraboloiden finns kvar som val, och utfallet redovisas
som negativt.

## Redovisning
`utdata/referensyta/jamfor.py` (en körning), `kor.sh` (alla), `sammanstall.py` → `resultat.json` och `resultat.md`.
