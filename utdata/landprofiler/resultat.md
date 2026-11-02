# Landprofiler – resultat (2026-11-02)

Plan: analysplaner/2026-11-02-landprofiler.md (sha eb59f631). Skript data.py, analys.py; kontrollen inom län (lanskontroll.py) ligger UTANFÖR planen och redovisas som sådan. Underlag: 1 710 runstenar, 131 107 gravar och gravfält ur fornlämningsregistret, 131 757 ortnamn (OpenStreetMap).

Före körningen rättades en kodningsregel i data.py: "hög" räknades först även som höjdangivelse ("1 m hög"); regeln kräver nu "högar" eller "1/en/ett hög".

## Antal prov

- språk: 776 prov, 42 med q < 0,05, 14 håller enligt planen
- sed: 478 prov, 21 med q < 0,05, 11 håller enligt planen
- plats: 234 prov, 18 med q < 0,05, 4 håller enligt planen
- natur: 52 prov, 12 med q < 0,05, 8 håller enligt planen
- gravskick: 2706 prov, 1080 med q < 0,05, 440 håller enligt planen; inom samma län: 373 håller, 58 håller inte, 9 kan inte prövas
- ortnamn: 1853 prov, 413 med q < 0,05, 146 håller enligt planen; inom samma län: 119 håller, 24 håller inte, 3 kan inte prövas

**Läsning av länskontrollen:** gravfältsbeskrivningarnas "kantkedja" är vanlig i hela Kalmar län (Tjust, Sevede, Möre) och faller inom länet – en inventeringsvana, inte en sed. Därför räknas bara fynd som håller inom länet nedan.

**Obs:** med den breda paletten (478 prov om sed) klarar Rodens färre kors och kristna formler inte korrektionen (q 0,07–0,08); i den smalare låsta jämförelsen (plan 054c87d5, steg 2) håller de.

## Profiler per gammalt land (fynd som håller; gravar och namn även inom länet)

### Attundaland (U)
- **Språket:** prep_at 12 mot 34 % (känt); skilj_kryss 29 mot 15 %; ord_at 19 mot 33 %; monoftong 43 mot 55 % (känt)
- **Seden:** i_grupp 41 mot 26 %
- **Bergarten:** mat_granit 73 mot 87 % (känt)
- **Gravskicket:** gf_oval 2 mot 5 %
- **Ortnamnen:** n_boda 3 mot 10 %; n_torp 6 mot 4 %; n_lunda 9 mot 6 %; n_sta 6 mot 4 %

### Finnveden (Sm)
- **Gravskicket:** gf_kantkedja 4 mot 41 %; form_treudd 5 mot 0 %; typ_hög 19 mot 3 %; form_rund 17 mot 48 %; gf_kvadratisk 4 mot 13 %; gf_stenkrets 5 mot 16 %; typ_grav_markerad_av_sten_block 11 mot 4 %; gf_oval 3 mot 8 %; gf_rest_sten 9 mot 19 %; form_kvadratisk 3 mot 7 %; typ_stensättning 40 mot 57 %
- **Ortnamnen:** n_boda 9 mot 5 %; n_torp 5 mot 8 %

### Fjädrundaland (U)
- **Språket:** r_for_R 52 mot 16 % (känt); skilj_plus 17 mot 4 %; ord_ræisti 9 mot 3 %; stungen_y 36 mot 20 %
- **Seden:** has_carver 90 mot 60 %; pm_kors 35 mot 61 % (känt); i_grupp 15 mot 34 %; flera_resare 44 mot 63 % (känt)
- **Bergarten:** mat_granit 93 mot 80 % (känt)
- **Gravskicket:** typ_röse 5 mot 11 %; typ_grav_markerad_av_sten_block 6 mot 3 %; gf_hogar 34 mot 45 %; form_rund 76 mot 67 %; gf_kantkedja 68 mot 62 %; typ_stensättning 79 mot 74 %
- **Ortnamnen:** n_sta 7 mot 4 %; n_by 9 mot 6 %

### Handbörd (Sm)
- **Gravskicket:** form_kvadratisk 2 mot 7 %
- **Ortnamnen:** n_boda 4 mot 6 %

### Mo (Sm)
- **Gravskicket:** typ_stenkrets_stenrad 24 mot 3 %; form_rund 12 mot 45 %; typ_stensättning 35 mot 55 %
- **Ortnamnen:** n_boda 20 mot 6 %; n_lunda 2 mot 5 %

### Möre (Sm)
- **Gravskicket:** gf_mittsten 18 mot 4 %; gf_rest_sten 41 mot 15 %; form_kvadratisk 2 mot 7 %; form_rund 66 mot 44 %
- **Ortnamnen:** n_hult 2 mot 7 %; n_nas 1 mot 3 %; n_vik 0 mot 1 %

### Njudung (Sm)
- **Gravskicket:** gf_kantkedja 6 mot 34 %; typ_röse 38 mot 31 %
- **Ortnamnen:** n_boda 4 mot 6 %; n_hult 5 mot 7 %

### Norder treding (G)
- **Gravskicket:** typ_grav_markerad_av_sten_block 4 mot 6 %

### Roden (U)
- **Språket:** stungen_e 22 mot 50 %
- **Platsen:** nara_centralort 20 mot 49 %
- **Gravskicket:** gf_rest_sten 6 mot 14 %; typ_grav_markerad_av_sten_block 1 mot 4 %; gf_fler_hogar 19 mot 8 %; form_rund 56 mot 70 %
- **Ortnamnen:** n_vik 4 mot 1 %; n_sta 2 mot 5 %; n_berga 1 mot 1 %; n_nas 3 mot 1 %; n_by 3 mot 7 %

### Sevede (Sm)
- **Gravskicket:** typ_stenkrets_stenrad 0 mot 4 %; typ_hög 1 mot 6 %; typ_stensättning 76 mot 51 %; typ_röse 20 mot 33 %
- **Ortnamnen:** n_hult 12 mot 6 %

### Suder treding (G)
- **Gravskicket:** typ_grav_markerad_av_sten_block 6 mot 4 %

### Tiundaland (U)
- **Språket:** ord_retta 21 mot 8 %; skilj_apostrof 27 mot 11 %; ord_hans 7 mot 17 %; ord_faður 53 mot 39 %
- **Seden:** rel_foralder 61 mot 45 % (känt); rel_barn 16 mot 26 % (känt); pm_kors 65 mot 53 % (känt)
- **Bergarten:** mat_sandsten 4 mot 12 %; mat_granit 90 mot 76 % (känt)
- **Gravskicket:** gf_treudd 2 mot 5 %; gf_skeppsformig 5 mot 3 %
- **Ortnamnen:** n_vik 1 mot 2 %; n_boda 12 mot 6 %

### Tjust (Sm)
- **Gravskicket:** typ_grav_markerad_av_sten_block 1 mot 6 %; typ_stensättning 73 mot 49 %; typ_röse 23 mot 33 %
- **Ortnamnen:** n_stad 3 mot 0 %; n_vik 4 mot 1 %; n_hem 5 mot 2 %; n_lunda 3 mot 5 %

### Tveta (Sm)
- **Gravskicket:** gf_stenkrets 49 mot 11 %; form_kvadratisk 26 mot 5 %; typ_stenkrets_stenrad 11 mot 3 %; form_rund 21 mot 46 %; gf_rest_sten 35 mot 15 %; typ_röse 21 mot 32 %
- **Ortnamnen:** n_ryd 6 mot 3 %; n_torp 11 mot 7 %

### Värend (Sm)
- **Gravskicket:** typ_röse 52 mot 27 %; typ_hög 3 mot 6 %
- **Ortnamnen:** n_boda 3 mot 7 %; n_lunda 7 mot 4 %

### Vedbo (Sm)
- **Gravskicket:** form_kvadratisk 24 mot 6 %; gf_hogar 48 mot 18 %; gf_stenkrets 33 mot 11 %; gf_rest_sten 38 mot 15 %; typ_stenkrets_stenrad 10 mot 3 %; gf_kvadratisk 25 mot 9 %
- **Ortnamnen:** n_holm 1 mot 2 %; n_torp 11 mot 7 %

### Vista (Sm)
- **Ortnamnen:** n_torp 13 mot 7 %

## Härader (fynd som håller; gravar och namn även inom länet), de 40 största skillnaderna

- Redvägs hd (Vg), sed: pm_stungna 100 mot 35 %
- Barne hd (Vg), gravskick: typ_flatmarksgrav 27 mot 1 %
- Östkinds hd (Ög), gravskick: form_kvadratisk 1 mot 20 %
- Färentuna hd (U), plats: nara_centralort 100 mot 45 %
- Gäsene hd (Vg), gravskick: form_rund 3 mot 47 %
- Lyhundra hd (attundaland), natur: mat_sandsten 63 mot 8 %
- Rönnebergs hd (Sk), gravskick: typ_hög 94 mot 48 %
- Listers hd (Bl), gravskick: typ_hög 15 mot 1 %
- Ås hd (Vg), gravskick: form_rund 5 mot 48 %
- Kullings hd (Vg), gravskick: form_rund 5 mot 48 %
- Lysings hd (Ög), ortnamn: n_ryd 5 mot 0 %
- Östkinds hd (Ög), gravskick: gf_kvadratisk 2 mot 26 %
- Bjäre hd (Sk), gravskick: gf_hogar 71 mot 14 %
- Herrestads hd (Sk), gravskick: typ_stensättning 3 mot 32 %
- Vemmenhögs hd (Sk), gravskick: typ_stensättning 3 mot 32 %
- Harjagers hd (Sk), gravskick: typ_hög 93 mot 48 %
- V. Göinge hd (Sk), gravskick: typ_hög 8 mot 53 %
- Kinds hd (Vg), gravskick: form_rund 8 mot 50 %
- Nås och Malungs d:a tg (D), ortnamn: n_boda 1 mot 12 %
- Björkekinds hd (Ög), gravskick: form_kvadratisk 2 mot 18 %
- Vadsbo hd (Vg), gravskick: form_kvadratisk 21 mot 3 %
- Dals hd (Ög), gravskick: typ_stensättning 46 mot 89 %
- Frösåkers hd (roden), gravskick: gf_skeppsformig 16 mot 2 %
- Ydre hd (Ög), gravskick: typ_röse 18 mot 2 %
- Medelstads hd (Bl), gravskick: gf_kantkedja 47 mot 8 %
- Ingelstads hd (Sk), gravskick: typ_stensättning 5 mot 32 %
- Nordmarks hd (Vr), ortnamn: n_torp 1 mot 7 %
- Vadsbo hd (Vg), gravskick: gf_kantkedja 62 mot 17 %
- Dals hd (Ög), gravskick: typ_hög 25 mot 4 %
- Lösings hd (Ög), gravskick: form_kvadratisk 3 mot 18 %
- Dals hd (Ög), gravskick: typ_grav_markerad_av_sten_block 19 mot 3 %
- Tönnersjö hd (Hl), gravskick: typ_röse 2 mot 15 %
- Höks hd (Hl), gravskick: typ_flatmarksgrav 5 mot 1 %
- Oxie hd (Sk), gravskick: typ_flatmarksgrav 26 mot 5 %
- Finspånga Läns hd (Ög), gravskick: form_treudd 9 mot 1 %
- Bjäre hd (Sk), gravskick: typ_flatmarksgrav 1 mot 6 %
- Ulleråkers hd (tiundaland), plats: nara_centralort 87 mot 43 %
- Skånings hd (Vg), gravskick: form_rund 86 mot 45 %
- Kinnefjärdings hd (Vg), gravskick: typ_flatmarksgrav 7 mot 1 %
- Hardemo hd (Nä), gravskick: form_rund 85 mot 43 %
