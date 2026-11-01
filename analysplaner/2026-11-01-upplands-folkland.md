# Analysplan: Upplands folkland och deras runstenar

Skriven och låst 2026-11-01, innan något drag har jämförts mellan folklanden. Viktor 2026-11-01: "kan vi se några mönster
efter dessa nya indelningar av de gamla gränserna".

## Vad som är känt före låsningen
Folklanden och deras härader i `web/src/lib/historiska_land.json`; stenarnas land i `web/public/geo/sten_land.json`
(`scripts/assign_sten_land.py`, genom socknen). Antal vikingatida runstenar: Attundaland 499, Tiundaland 391,
Fjädrundaland 157 (varav 2 i Sö), Roden 80. Smålandsplanen (`analysplaner/2026-11-01-smalanden.md`) gav inga skillnader.
Inga drag är jämförda mellan folklanden.

## Data
Stenar i de fyra folklanden som finns i `utdata/upptackt_v3/drag.csv` (korpus e83202e0). **27 drag**, valda nu:
innehåll cat_kristen, pm_kors, pm_bon, pm_sjal, pm_hednisk, cat_fard, msg_dod_borta, msg_berom, cat_bro_vag;
människor kvinna_resare, kvinna_ensam, flera_resare, rel_barn, rel_foralder, rel_syskon, rel_make, drengr, thegn;
ristning och språk pm_signatur, ord_kumbl, mat_granit, pm_stungna, monoftong, r_for_R, o_runa, prep_at, ord_þennsa.
NA räknas inte. Tidsskikt som i v3 (odaterad som egen nivå).

## Steg 1 – skiljer folklanden? (konfirmatoriskt)
För varje drag: logistisk regression drag ~ folkland + tidsskikt mot drag ~ tidsskikt; kvotprov (likelihood ratio,
3 frihetsgrader). Benjamini–Hochberg över de 27. Ett drag **skiljer** om q < 0,05.

## Steg 2 – halvorna
Socknarna i de fyra folklanden delas varannan i sockenmedeldateringens ordning (som i övriga planer). Ett drag som skiljer
**håller** om kvotprovet har p < 0,05 i båda halvorna och folklandet med högst andel är detsamma i båda.

## Steg 3 – gränsprovet (för drag som håller)
För varje par av grannfolkland (A, B) där draget skiljer mest (högsta mot lägsta andel, om de gränsar till varandra; annars
de två grannar med störst skillnad): stenar i A och B vars socken har en socken i det andra landet inom 10 km
(socknarnas punkter i `data/geo/socknar_land.csv`). Fishers exakta test på gränsstenarna. Skillnaden **finns vid gränsen**
om p < 0,05 i samma riktning som i hela materialet; annars redovisas den som en gradient. Beskrivande: andelarna på
båda sidor i 10-kilometersbandet och längre in.

## Vad som inte får göras
Dragen, modellen, gränserna 0,05 och 10 km ändras inte efter körningen.

## Redovisning
`utdata/folkland/folkland.py`, `folkland.json`, `resultat.md`.
