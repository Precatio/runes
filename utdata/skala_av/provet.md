# Provet: skiljer *Skala av vittringen* huggning från vittring bättre än dagens djupbild?

Låst plan `analysplaner/2026-11-07-skala-av-provet.md` (sha 380fccf4). Facit: Viktors granskade runslingor. 95 av 95 filer mätta.

Teknisk rättelse under körningen: 29 filer saknade djupbildens origo (a0, b0) i djupbildscachens metadata, så att `rune_bands.drawn_labels` inte kunde föra över slingorna och filen hoppades över. Origo fylldes i med samma funktion som studie 1b (`utdata/forskningsplan/s1b_klassning.grid_origin`, som kontrollerar att rutnätet blir djupbildens; `provet_a0.py`) och filerna kördes om. Den sista filen i listan föll först bort för att raden saknade radslut (rättat i `provet_kor.sh`). Inget i jämförelsen ändrades.

**Lyft** = andelen av det visade som ligger inne i slingorna, delat med slingornas andel av ytan (1 = som slumpen). A = dagens djupbild med en gemensam gräns som visar lika stor del av ytan som B; B = avskalat (reglaget 0 mm), alla fläckar; C = avskalat, bara spår.

## P1 (huvudprov): B mot A

- Median lyft A 1,30, B 1,23; medianskillnad B − A -0,069; B bättre på 16 % av filerna.
- Wilcoxon ensidigt (B > A): p = 1. **Håller inte.**

## P2 (beskrivande): C mot A

- Median lyft A 1,30, C 1,33; medianskillnad C − A 0,024; C bättre på 62 % av filerna; Wilcoxon ensidigt p = 0.00326. C visar mindre yta än A.

## Tillägg utöver planen (beskrivande): C mot A vid samma visade yta

Lagt till under körningen, efter de två första filerna och innan något sammanställts, eftersom C visar mindre yta än A i P2: A räknas om med en gemensam gräns som visar lika stor del av ytan som C. Inget prov är bestämt i förväg för detta; p-värdet är bara beskrivande.

- Median lyft A (samma yta som C) 1,34, C 1,33; medianskillnad -0,022; C bättre på 40 % av filerna; Wilcoxon ensidigt p = 0.996.

## Per serie

| Serie | Filer | Slingornas andel | Visat B (C) | Lyft A | Lyft B | Lyft C | B > A | C > A | Lyft A vid C:s yta | C > A vid samma yta | Täckning A / B / C |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Södermanland | 36 | 35 % | 28 % (24 %) | 1,27 | 1,21 | 1,31 | 8 % | 69 % | 1,31 | 39 % | 36 % / 34 % / 31 % |
| Västergötland | 18 | 24 % | 28 % (25 %) | 1,28 | 1,24 | 1,32 | 11 % | 56 % | 1,31 | 39 % | 36 % / 35 % / 32 % |
| Medelpad | 15 | 17 % | 26 % (22 %) | 1,56 | 1,43 | 1,50 | 7 % | 47 % | 1,65 | 20 % | 41 % / 38 % / 34 % |
| Hälsingland | 12 | 27 % | 27 % (23 %) | 1,32 | 1,24 | 1,46 | 33 % | 75 % | 1,38 | 58 % | 36 % / 34 % / 31 % |
| Gravmonument Ög/Sm | 11 | 20 % | 29 % (25 %) | 1,16 | 1,14 | 1,20 | 36 % | 45 % | 1,19 | 45 % | 33 % / 33 % / 30 % |
| Åsmund | 3 | 24 % | 27 % (24 %) | 1,48 | 1,37 | 1,50 | 33 % | 100 % | 1,55 | 67 % | 39 % / 36 % / 35 % |

Täckning = andelen av slingornas yta som visas. Medianer per serie.

## Per fil

| Serie | Signum | Fil | Slingornas andel | Lyft A | B | C | A vid C:s yta |
|---|---|---|---|---|---|---|---|
| Åsmund | Gs 11 | Gs_11_1_4_thin05 | 24 % | 1,48 | 1,37 | 1,50 | 1,55 |
| Åsmund | Gs 13 | Gs_13_1_4_thin04_closed_holes | 25 % | 1,49 | 1,38 | 1,60 | 1,60 |
| Åsmund | U 1144 | U_1144_thin05_closed_holes | 15 % | 1,15 | 1,16 | 1,23 | 1,18 |
| Gravmonument Ög/Sm | Ög 240 | Og_240_241_thin03 | 19 % | 1,16 | 1,19 | 1,20 | 1,18 |
| Gravmonument Ög/Sm | Ög 2 | Og_2_thin03 | 13 % | 1,16 | 1,17 | 1,25 | 1,18 |
| Gravmonument Ög/Sm | Ög 2 | Og_2b_thin03 | 9 % | 0,81 | 0,96 | 0,94 | 0,77 |
| Gravmonument Ög/Sm | Ög 5 | Og_5_thin03 | 19 % | 1,15 | 1,14 | 1,23 | 1,19 |
| Gravmonument Ög/Sm | Ög 5 | Og_5b_thin03 | 22 % | 0,92 | 0,93 | 0,88 | 0,92 |
| Gravmonument Ög/Sm | Ög 6 | Og_6_thin03 | 23 % | 1,39 | 1,27 | 1,38 | 1,48 |
| Gravmonument Ög/Sm | Ög Hov12;21 | Og_Hov12_21_thin03 | 19 % | 1,23 | 1,22 | 1,21 | 1,25 |
| Gravmonument Ög/Sm | Ög Hov14;22 | Og_Hov_14_22_thin03 | 29 % | 1,20 | 1,11 | 1,17 | 1,22 |
| Gravmonument Ög/Sm | Ög Hov15;22 | Og_Hov_15_22_thin03 | 21 % | 1,09 | 1,07 | 1,04 | 1,11 |
| Gravmonument Ög/Sm | Sm 124 | Sm_124_thin03 | 21 % | 1,38 | 1,33 | 1,38 | 1,43 |
| Gravmonument Ög/Sm | Sm 125 | Sm_125_thin03 | 20 % | 1,15 | 1,12 | 1,19 | 1,19 |
| Hälsingland | Hs 11 | HS_11_thin03 | 27 % | 1,29 | 1,37 | 1,54 | 1,33 |
| Hälsingland | Hs 12 | HS_12_thin03 | 29 % | 1,42 | 1,40 | 1,49 | 1,47 |
| Hälsingland | Hs 14 | HS_14_0_40_runes_thin03 | 22 % | 1,34 | 1,27 | 1,52 | 1,50 |
| Hälsingland | Hs 14 | HS_14_1mm_complete_thin03 | 29 % | 1,24 | 1,17 | 1,29 | 1,31 |
| Hälsingland | Hs 15 | HS_15_0_40_thin03 | 13 % | 1,37 | 1,21 | 1,23 | 1,42 |
| Hälsingland | Hs 16 | HS_16_thin03 | 58 % | 1,32 | 1,27 | 1,46 | 1,38 |
| Hälsingland | Hs 1 | HS_1A_thin02 | 83 % | 1,13 | 1,14 | 1,13 | 1,14 |
| Hälsingland | Hs 21 | HS_21_thin01 | 27 % | 1,32 | 1,22 | 1,38 | 1,39 |
| Hälsingland | Hs 2 | HS_2_thin01 | 16 % | 1,42 | 1,39 | 1,64 | 1,51 |
| Hälsingland | Hs 3 | HS_3_thin01 | 10 % | 1,16 | 1,20 | 1,66 | 1,16 |
| Hälsingland | Hs 6 | HS_6_thin03 | 36 % | 1,60 | 1,20 | 1,36 | 1,67 |
| Hälsingland | Hs 9 | HS_9_thin03 | 20 % | 1,27 | 1,28 | 1,45 | 1,35 |
| Medelpad | M 10 | M_10_Selånger_thin03 | 17 % | 1,45 | 1,38 | 1,50 | 1,52 |
| Medelpad | M 11 | M_11_Högom_thin03 | 24 % | 1,66 | 1,58 | 1,83 | 1,82 |
| Medelpad | M 13 | M_13_Oxsta_thin03 | 5 % | 2,35 | 1,89 | 0,00 | 3,51 |
| Medelpad | M 14 | M_14_020_Byn_thin02 | 17 % | 1,32 | 1,24 | 1,34 | 1,37 |
| Medelpad | M 14 | M_14_040_Byn_thin03 | 16 % | 1,41 | 1,29 | 1,40 | 1,49 |
| Medelpad | M 15 | M_15_Sköns_kyrka_thin02 | 34 % | 1,56 | 1,44 | 1,09 | 1,93 |
| Medelpad | M 16 | M_16_Sköns_kyrka_thin03 | 26 % | 1,64 | 1,38 | 1,40 | 1,64 |
| Medelpad | M 1 | M_1_Nolby_thin03 | 30 % | 1,35 | 1,30 | 1,43 | 1,39 |
| Medelpad | M 2 | M_2_Svala_thin03 | 13 % | 1,37 | 1,62 | 1,81 | 1,36 |
| Medelpad | M 3 | M_3_Berga_thin02 | 28 % | 1,31 | 1,19 | 1,26 | 1,34 |
| Medelpad | M 4 | M_4_Attmarby_thin02 | 22 % | 1,67 | 1,48 | 1,66 | 1,76 |
| Medelpad | M 5 | M_5_Attmar_thin02 | 15 % | 1,56 | 1,38 | 1,53 | 1,65 |
| Medelpad | M 6 | M_6_Målsta_thin02 | 14 % | 1,65 | 1,43 | 1,76 | 1,78 |
| Medelpad | M 7 | M_7_Tuna_kyrka_thin03 | 13 % | 1,69 | 1,51 | 1,71 | 1,82 |
| Medelpad | M 8 | M_8_Sköle_thin03 | 19 % | 1,75 | 1,58 | 1,74 | 1,83 |
| Södermanland | Sö 112 | So_112_1_4_thin_closed_holes | 17 % | 1,26 | 1,23 | 1,32 | 1,32 |
| Södermanland | Sö 113 | So_113_1_4_thin_closed_holes | 58 % | 1,22 | 1,20 | 1,26 | 1,23 |
| Södermanland | Sö 128 | So_128_1_4_thin_closed_holes | 29 % | 1,49 | 1,33 | 1,35 | 1,64 |
| Södermanland | Sö 129 | So_129_1_4_thin03_closed_holes | 25 % | 1,50 | 1,41 | 1,44 | 1,54 |
| Södermanland | Sö 131 | So_131_1_4_thin_closed_holes | 34 % | 1,25 | 1,17 | 1,29 | 1,30 |
| Södermanland | Sö 134 | So_134_1_4_thin_closed_holes | 53 % | 1,32 | 1,17 | 1,24 | 1,35 |
| Södermanland | Sö 137A | So_137A_1_4_thin05_closed_holes | 40 % | 1,40 | 1,32 | 1,44 | 1,48 |
| Södermanland | Sö 137B | So_137B_1_4_thin05_hela | 68 % | 1,12 | 1,08 | 1,12 | 1,13 |
| Södermanland | Sö 143 | So_143_1_4_thin_closed_holes | 29 % | 1,52 | 1,29 | 1,43 | 1,61 |
| Södermanland | Sö 149 | So_149_1_4_thin_closed_holes | 38 % | 1,06 | 1,10 | 1,20 | 1,13 |
| Södermanland | Sö 160 | So_160_1_4_thin05_closed_holes | 45 % | 1,29 | 1,19 | 1,27 | 1,33 |
| Södermanland | Sö 161 | So_161_1_4_thin04_closed_holes | 56 % | 1,12 | 1,09 | 1,14 | 1,15 |
| Södermanland | Sö 162 | So_162_1_4_closed_holes | 52 % | 1,23 | 1,18 | 1,26 | 1,25 |
| Södermanland | Sö 163 | So_163_1_4_thin05_closed_holes | 33 % | 1,21 | 1,14 | 1,15 | 1,23 |
| Södermanland | Sö 164 | So_164_1_4_thin_closed_holes | 29 % | 1,30 | 1,26 | 1,35 | 1,35 |
| Södermanland | Sö 165 | So_165_1_4_thin07_closed_holes | 39 % | 1,26 | 1,25 | 1,33 | 1,30 |
| Södermanland | Sö 166 | So_166_1_4_thin_closed_holes | 32 % | 1,22 | 1,14 | 1,21 | 1,26 |
| Södermanland | Sö 184 | So_184_thin03_closed_holes | 47 % | 1,14 | 1,12 | 1,17 | 1,15 |
| Södermanland | Sö 205 | So_205_thin03_closed_holes | 18 % | 1,32 | 1,20 | 1,33 | 1,41 |
| Södermanland | Sö 206 | So_206_thin03_closed_holes | 37 % | 1,29 | 1,30 | 1,36 | 1,31 |
| Södermanland | Sö 207 | So_207_thin03_closed_holes | 14 % | 1,89 | 1,71 | 2,03 | 2,14 |
| Södermanland | Sö 208 | So_208_thin03_closed_holes | 23 % | 1,27 | 1,28 | 1,37 | 1,34 |
| Södermanland | Sö 211 | So_211_thin03_closed_holes | 30 % | 1,58 | 1,49 | 1,61 | 1,63 |
| Södermanland | Sö 307 | So_307_1_4_thin_closed_holes | 22 % | 1,42 | 1,30 | 1,70 | 1,63 |
| Södermanland | Sö 319 | So_319_1_4_thin05_closed_holes | 36 % | 1,24 | 1,15 | 1,19 | 1,27 |
| Södermanland | Sö 333 | So_333_thin05_closed_holes | 41 % | 1,38 | 1,33 | 1,50 | 1,46 |
| Södermanland | Sö 360 | So_360_1_4_thin03_closed_holes | 21 % | 1,28 | 1,12 | 1,21 | 1,34 |
| Södermanland | Sö 367 | So_367_1_4_thin_closed_holes | 51 % | 1,19 | 1,16 | 1,19 | 1,20 |
| Södermanland | Sö 370 | So_370_1_4_thin05_closed_holes | 46 % | 1,01 | 0,96 | 1,00 | 1,02 |
| Södermanland | Sö 45 | So_45_1_4_thin_closed_holes | 18 % | 1,19 | 1,14 | 1,21 | 1,23 |
| Södermanland | Sö 52 | So_52_1_4_thin05_closed_holes | 37 % | 1,26 | 1,21 | 1,28 | 1,31 |
| Södermanland | Sö 75 | So_75_1_4_thin05 | 47 % | 1,12 | 1,11 | 1,14 | 1,13 |
| Södermanland | Sö Fv1948;282 | So_Fv1948_282_1_4_thin03_closed_holes | 22 % | 1,51 | 1,31 | 1,41 | 1,60 |
| Södermanland | Sö Fv1954;19 | So_Fv1954_19_1_4_thin05_closed_holes | 21 % | 1,23 | 1,21 | 1,35 | 1,26 |
| Södermanland | Sö Fv1954;20 | So_Fv1954_20_1_4_thin03_closed_holes | 33 % | 1,30 | 1,26 | 1,35 | 1,34 |
| Södermanland | Sö Fv1973;189 | So_Fv1973_189_1_4_thin_closed_holes | 38 % | 1,30 | 1,22 | 1,33 | 1,37 |
| Västergötland | Vg 102 | Vg_102_thin03_closed | 19 % | 1,50 | 1,40 | 1,59 | 1,61 |
| Västergötland | Vg 103 | Vg_103_thin03_closed | 49 % | 1,24 | 1,17 | 1,32 | 1,31 |
| Västergötland | Vg 105 | Vg_105_thin03_closed | 20 % | 1,31 | 1,30 | 1,56 | 1,45 |
| Västergötland | Vg 108 | Vg_108_thin03_closed | 48 % | 1,23 | 1,24 | 1,26 | 1,26 |
| Västergötland | Vg 22 | Vg_22_thin03_closed | 27 % | 1,27 | 1,23 | 1,33 | 1,31 |
| Västergötland | Vg 23 | Vg_23_thin03_closed | 25 % | 1,12 | 1,06 | 1,07 | 1,14 |
| Västergötland | Vg 30 | Vg_30_thin03_closed | 63 % | 1,05 | 1,04 | 1,05 | 1,05 |
| Västergötland | Vg 32 | Vg_32_thin03_closed | 24 % | 1,41 | 1,25 | 1,32 | 1,46 |
| Västergötland | Vg 33 | Vg_33_thin03_closed | 22 % | 1,47 | 1,38 | 1,50 | 1,53 |
| Västergötland | Vg 37 | Vg_37_thin03_closed | 40 % | 1,18 | 1,13 | 1,14 | 1,19 |
| Västergötland | Vg 40 | Vg_40_thin03_closed | 17 % | 1,49 | 1,30 | 1,44 | 1,55 |
| Västergötland | Vg 41 | Vg_41_Ljung99_Lundberg_30_thin03 | 24 % | 1,22 | 1,23 | 1,32 | 1,23 |
| Västergötland | Vg 50 | Vg_50_thin03_closed | 34 % | 1,44 | 1,20 | 1,37 | 1,55 |
| Västergötland | Vg 51 | Vg_51_del_2_thin03 | 25 % | 1,31 | 1,24 | 1,34 | 1,36 |
| Västergötland | Vg 51 | Vg_51_del_3_thin03 | 24 % | 1,29 | 1,24 | 1,29 | 1,31 |
| Västergötland | Vg 51 | Vg_51_del_4_thin03 | 50 % | 1,22 | 1,13 | 1,18 | 1,24 |
| Västergötland | Vg 53 | Vg_53_Ljung61_thin03 | 13 % | 1,38 | 1,31 | 2,06 | 1,68 |
| Västergötland |  | Vg_ATA322-4412-2011_Ljung80_thin03 | 7 % | 1,09 | 1,01 | 1,02 | 1,10 |
