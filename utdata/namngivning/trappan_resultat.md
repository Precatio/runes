# Resultat: robusthetsstegen för namnleden i familjen (2026-10-31)

Plan: `analysplaner/2026-10-31-namnled-trappan.md` (4c62109, SHA-256 9d0247a8…, låst före körningen). Kod `trappa.py`
(paren och leddelningen kopierade oförändrade från `analys.py`), siffror `trappan.json`.

## Utfall – alla steg håller, för både H1 och H5
**H1 förälder–barn (1 292 par):** huvudtestet 5,3 % mot 2,8 %, p 0,0001; halva A 4,9 mot 2,4 % (p 0,0002), halva B
5,8 mot 3,4 % (p 0,0009); tiden konstant 5,3 mot 2,8 % (p 0,0001); ett par per sten (714) 5,6 mot 2,8 % (p 0,0001); utan
korta led 4,5 mot 2,5 % (p 0,0001); bara delade led, utan samma hela namn, 4,9 mot 2,3 % (p 0,0001). Utan ett landskap:
utan U (534 par, 41 % kvar, bara riktningen krävs) 4,5 mot 2,8 % (p 0,011); utan Sö, Ög, Sm, Vg alla p 0,0001.

**H5 syskon (1 066 par):** 6,7 % mot 2,9 %, p 0,0001; halva A 6,6 mot 3,1 % (p 0,0002), halva B 6,8 mot 3,3 % (p 0,0002);
tiden konstant 6,7 mot 3,3 % (p 0,0001); ett par per sten (488) 7,2 mot 2,5 % (p 0,0001); utan korta led 6,0 mot 2,7 %
(p 0,0001); bara delade led 6,7 mot 2,3 % (p 0,0001). Utan ett landskap: utan U (443, 42 %) 6,8 mot 3,1 %, utan Sö,
Ög, Vg alla p 0,0001.

Halvornas p-värden skiljer sig i sista decimalen från huvudkörningen 2026-10-29 (halva B för H1 0,0009 mot 0,0005)
eftersom slumpdragningarna kommer i en annan ordning; andelarna är desamma.

Fyndet kvalar som **Fullt prövat fynd** i rapportmallen version 4.

## Avvikelser
Inga.

## Explorativt, utanför planen: omblandning inom härad
Familjer i samma bygd delar ett lokalt namnförråd, så omblandning inom landskapet kan överskatta arvet. Med
omblandningen inom härad (`harad.py`, `harad.json`): **H1** 5,3 % mot 3,3 % väntat, p 0,0001 (113 härader) – håller;
**H5** 6,7 % mot 5,6 % väntat, p 0,053 (100 härader) – krymper och är inte signifikant. För syskonen är den
omblandningen dock skev uppåt: en sten med flera syskon ger många par, och i ett litet härad blir den slumpvisa
partnern ofta ett annat syskon i samma familj. Rapporten bygger påståendet på förälder–barn och redovisar syskonen med
det här förbehållet.
