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
