# Analysplan: landprofiler – vad skilde de gamla landen åt? (bred palett)

Skriven och låst 2026-11-02, innan något av proven nedan har körts. Viktor 2026-11-02: "Kan vi hitta mer som skiljer landen
åt? Pratade de annorlunda, hade de andra seder? Vi behöver en lite bredare palett." Underlag för serien De gamla landen.
Tidigare körningar (häradsskannern 054c87d5, gränsskannern 7d22ff40) använde 27 drag; här prövas alla drag vi har, i fem
områden, och två nya källor: fornlämningsregistret och ortnamnen.

## Enheter och jämförelse
- **Gamla land:** Upplands folkland, Smålands små land, Gotlands tredingar (`src/regions.old_region`).
- **Härader:** ISOF:s härad för socknen (som i `utdata/gamla_granser/monster.py`), i alla landskap i Svealand och Götaland.
- Varje enhet jämförs med **resten av sitt landskap**; ett härad i ett indelat landskap (Uppland, Småland, Gotland) med
  resten av sitt gamla land. Samma landskap betyder i regel samma län och samma inventering, vilket minskar risken att
  skillnader i registreringen ser ut som skillnader i sed.
- Minsta storlek per område: runstenar 15 stenar i enheten; gravar 30 gravar/gravfält; ortnamn 50 namn.

## Områden och drag
**1 Språket (runstenar, `utdata/upptackt_v3/drag.csv`):** stavning och skrift – monoftong, au_monoftong, o_runa, r_for_R,
nasal_utelamnad, h_saknas, stungen_e, stungen_y, stungen_g, bindrunor, short_twig, skilj_punkt, skilj_kryss, skilj_kolon,
skilj_apostrof, skilj_plus, skilj_blandat, prep_at – och ordförrådet: alla kolumner `ord_*` (förekomst av ordet eller
ordformen i texten).
**2 Seden på stenarna:** cat_sjalvminne, cat_bro_vag, cat_kristen, cat_fard, cat_arv, cat_ting, cat_magisk, pm_hednisk,
pm_kors, pm_bon, pm_sjal, pm_stungna, pm_signatur, has_carver, msg_dod_uppgift, msg_dod_borta, msg_resa, msg_gald,
msg_gard, msg_berom, kvinna_resare, kvinna_ensam, flera_resare, kvinna_dod, rel_barn, rel_foralder, rel_syskon, rel_make,
rel_slakt, rel_ej_slakt, drengr, thegn, god, hog_sten, i_grupp.
**3 Stenens plats:** nara_gravfalt, nara_hog, nara_vag, nara_bro, nara_fornborg, nara_church, nara_vatten,
nara_gammalt_namn, nara_ungt_namn, nara_kultnamn, nara_centralort, pa_plats, lokal. (Bergarten mat_* redovisas separat som
"natur", inte som sed.)
Områdena 1–3: en sten är en enhet; logistisk regression drag ~ tidsskikt + enhet (tidsskikt som i häradsskannern).
**4 Gravskicket (Riksantikvarieämbetets fornlämningsregister, uttag i `geografi_kallor/raa/lamningar_sverige.gpkg`):**
a) gravfält (lämningstyp Gravfält) med beskrivning; drag = beskrivningen nämner högar, kvadratiska, rektangulära,
treuddiga, skeppsformiga respektive ovala stensättningar, domarringar/stenkretsar, resta stenar, mittsten, kantkedja,
samt "fler högar än stensättningar" när båda antal står; b) enskilda gravar (Hög, Stensättning, Röse, Grav markerad av
sten/block, Stenkrets/stenrad, Flatmarksgrav): drag = typen, och för stensättningar formen ur beskrivningen (rund,
kvadratisk, rektangulär, treudd, skeppsformig, oval). Läge = lämningens punkt eller ytans mittpunkt; socken → härad som
för stenarna (namnet inom 30 km, annars närmaste ISOF-socken inom 15 km).
**5 Ortnamnen (`data/ortnamn/platser.csv`, OpenStreetMap: hamlet, village, isolated_dwelling, farm, locality):** drag =
namnet slutar på -sta, -by, -inge/-inga/-unge, -tuna, -hem/-um, -vin, -lösa, -åker, -berga, -torp, -ryd/-red, -hult,
-boda/-bo, -säter/-sätra, -stad, -lunda/-lund, -hammar, -vik, -näs, -holm; samt Husby-namn och kultnamn (`kultnamn.csv`).
Områdena 4–5: en lämning eller ett namn är en enhet; logistisk regression drag ~ enhet (odaterat).

## Prov och villkor
Ett prov per enhet × drag med minst 10 med och 10 utan draget i jämförelsen och minst 5 med draget i enheten.
Benjamini–Hochberg inom varje område. **Håller:** q < 0,05; p < 0,05 med samma riktning i båda halvorna (socknar
varannan inom landskapet, som tidigare); och p < 0,05 med samma riktning när enhetens största bidragsgivare tas bort –
den vanligaste ristaren (områdena 1–3, om den har fler än 5 stenar) respektive den socken som bidrar med flest
lämningar eller namn med draget (områdena 4–5).
Fynd som redan finns i häradsskannern eller gränsskannern märks "känt".

## Vad som inte görs och reservationer
Inga drag läggs till efter körningen. Fornlämningarna är odaterade som grupp (gravformerna spänner över järnåldern och
längre), och registreringen skiljer mellan inventeringar; därför jämförs bara inom landskapet, och fynden beskrivs som
"landets gravskick under förhistorien", inte som vikingatida. Ortnamnen är dagens namn ur OpenStreetMap; deras ändelser
är gamla, men alla gårdar finns inte med.

## Redovisning
`utdata/landprofiler/` (data.py, analys.py, landprofiler.json, resultat.md). Profilerna blir underlag för artiklarna; fynd
som ska bära en artikel prövas vidare i en egen låst plan, som Sotholm.
