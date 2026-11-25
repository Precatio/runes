# Plan: huvudmodulen – pilot för bättre täckning av huvudets drag (instrumentutveckling)

Skriven 2026-11-25 före piloten. Gräslundsspåret (`utdata/graslund/resultat.md`): finindelningen Pr1–Pr5 föll på att
nack- och läppflikar saknade konsensus för 75–95 % av Pr2–Pr5-stenarna. Använder inget facit om händer och inga stilgrupper
vid beslutet.

## Piloten
- 30 stenar ur SRI:s planscher med djurhuvud = ja och huvud i profil i v2-konsensus, nackflik utan konsensus, utanför alla
  facitgrupper (`utdata/nya_ristare/delning.json`, `facit.json`), slumpvis (frö 20261125).
- Steg 1: en lokaliserare per fem stenar hittar rundjurens huvuden och svans-/bandändar på planschsidan och sparar utsnitt i
  full upplösning (300 dpi) i cachen.
- Steg 2: två oberoende läsare kodar huvudmodulen (`utdata/graslund/huvud/kodbok_huvud.md`) ur utsnitten + hela bilden.
- Steg 3: för varje fält där de två inte är eniga (eller en är `osäkert`) kodar en tredje läsare fältet oberoende, utan att se
  de andras svar. Värdet = det som minst två av tre anger; annars saknas.

## Beslutsregel (bestämd nu)
Huvudmodulen körs på alla stenar med djurhuvud om, på pilotens 30 stenar:
- täckningen (andel stenar med värde) för nackflik och läppflik är minst **0,6** vardera (v2 gav 0 för nackflik på dessa
  stenar per urval), och
- kappa mellan läsare 1 och 2 (bland stenar där båda angav ett värde) är minst **0,6** för huvud_vy, oga, nackflik och
  läppflik, och
- överensstämmelsen med v2-konsensus för huvud_vy och oga (där båda finns) är minst 0,8.
Annars ändras kodboken eller utsnittsmetoden och en ny pilot görs på nya stenar.

## Utdata
`utdata/graslund/huvud/` (skript, sammanfattning); utsnitt och koder i `data/cache/hander/huvud/` (utanför git).

## Pilot 1 – utfall (2026-11-25): regeln höll inte
- Täckning: nackflik 0,37 och läppflik 0,40 (krav 0,6).
- Kappa: huvud_vy 0,0 trots 96 % lika (nästan alla i profil); öga 0,52; nackflik 0,67; läppflik 0,71.
- Öga mot v2: 0,33, eftersom det nya värdet `droppe` tog över från `mandel`. Det är ett fel i kodboken.
- Utsnitten var små (cirka 200–400 px), så flikarna syns men är svåra att tolka.

## Pilot 2 (bestämd före körningen)
- **Ändringar:**
  - Kodbok 3b: `droppe` borta (räknas som mandel), schematisk bild av ett profilhuvud, ögat hittas först.
  - Utsnitten förstoras till minst 1 000 px på den längsta sidan (LANCZOS) innan de läses.
- **Stenarna:** 30 nya stenar ur samma kandidatmängd, slumpvis (frö 20261126). Pilot 1:s stenar ingår inte.
- **Regeln:** samma som för pilot 1, med ett tillägg för fält där ett värde dominerar. Om minst 90 % av läsarnas par har
  samma värde räcker det att andelen lika är ≥ 0,9 i stället för kappa ≥ 0,6. Annars blir kappa meningslös.
