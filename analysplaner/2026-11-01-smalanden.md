# Analysplan: Smålands små land och deras runstenar

Skriven och låst 2026-11-01, innan något drag har jämförts mellan landen. Viktor 2026-11-01: "kan vi studera småland och
de små länderna där och deras runstenar. Vad är signifikativt för dessa?"

## Vad som är känt före låsningen
Landen och deras härader i `web/src/lib/historiska_land.json` (kartlagret, e3eeb9b). Antalet vikingatida runstenar
(`src/linking.stones`, projektets regel) per land, räknat genom stenens socken (Rundatas sockennamn mot Wikidatas
socknar inom 25 km, annars närmaste socken inom 15 km): Njudung 36, Finnveden 31, Vedbo 17, Värend 15, Möre 6, Tjust 5,
Tveta 3, Vista 3, Handbörd 3, Aspeland 2 (Sm, sammanlagt 121), Kinda 6 (Ög). Inga drag är jämförda.

## Huvudfrågan
Syns den gamla rättsliga gränsen på runstenarna? **Tiohärad** (Värend, Finnveden, Njudung – egen lag, Tiohärads lagsaga)
mot **de östra och norra landen** (Vedbo, Tveta, Vista, Tjust, Sevede, Aspeland, Handbörd, Möre, Mo – i Östgöta
lagsaga till 1559), bara stenar i Småland (Sm). Kinda (Ög) beskrivs för sig.

## Dragen (valda nu, ur `utdata/upptackt_v3/drag.csv`, korpus e83202e0)
Innehåll: cat_kristen, pm_kors, pm_bon, pm_hednisk, cat_magisk, cat_fard, msg_dod_borta, msg_berom, cat_bro_vag.
Människor: kvinna_resare, flera_resare, rel_barn, rel_foralder, rel_syskon, rel_make, rel_ej_slakt, drengr, thegn.
Ristning och plats: pm_signatur, ord_kumbl, mat_granit, nara_gravfalt. (22 drag; NA räknas inte.)

## Prov
1. **Huvudprov:** för varje drag Fishers exakta test, Tiohärad mot östra landen; Benjamini–Hochberg över de 22.
   Ett drag **skiljer** om q < 0,05.
2. **Halvorna:** socknarna i Småland delas varannan (i sockenmedeldateringens ordning, som i övriga planer); ett drag som
   skiljer redovisas med riktning och p i båda halvorna. Rapportgolvet (p < 0,05 i båda) redovisas som uppfyllt eller inte.
3. **Tiden konstant:** logistisk regression drag ~ grupp + tidsskikt bland daterade stenar, för de drag som skiljer.
4. **Beskrivande per land** (Njudung, Finnveden, Vedbo, Värend): andelen för varje drag mot resten av Småland, med
   Fishers p utan justering; stilgrupper och namngivna ristare per land. Inga slutsatser dras av enskilda land.

## Vad som inte får göras
Grupperna, dragen, testet och gränsen ändras inte efter körningen.

## Redovisning
`utdata/smalanden/smalanden.py`, `smalanden.json`, `resultat.md`.
