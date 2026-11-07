# Skala av vittringen provad på skanningar (utdata/skala_av/prova.py)

Samma inställningar som dialogen på 3D-sidan (src/peel.py): mätningens referensyta (stängning 20 mm), djup vinkelrätt mot ytan, vittringsnivå = 70:e percentilen per 60 mm-ruta. Antal spår (rostrött) och gropar (grått) vid fyra reglagelägen; *kvar* = andel av ytan som ligger djupare än nivån plus reglaget. Bilderna: <stem>.png (dagens djupbild överst, den avskalade under).

| Sten | Serie | mm/cell | Vittringsnivå mm (min–median–max) | −0,5 mm | 0 mm | +0,5 mm | +1 mm | Kvar vid 0 mm | Tid s |
|---|---|---|---|---|---|---|---|---|---|
| Gs 11 | asmund | 0.99 | 0.4–0.6–0.9 | 24 / 914 | 302 / 2350 | 50 / 334 | 100 / 231 | 26 % | 95 |
| U 1144 | asmund | 0.98 | 0.1–0.5–0.9 | 17 / 1290 | 336 / 2729 | 343 / 1797 | 192 / 1269 | 28 % | 122 |
| Ög 2 | gravmonument_og_sm | 0.81 | 0.1–1.2–1.8 | 29 / 322 | 68 / 386 | 87 / 388 | 87 / 384 | 28 % | 14 |
| Hs 14 | halsingland | 1.47 | 0.1–0.3–1.1 | 90 / 801 | 134 / 5116 | 128 / 957 | 108 / 805 | 26 % | 23 |
| M 3 | medelpad | 0.86 | 0.5–1.1–1.6 | 94 / 1189 | 311 / 1553 | 273 / 1511 | 162 / 1071 | 30 % | 47 |
| Sö 113 | sodermanland | 0.43 | 0.2–0.8–1.4 | 27 / 396 | 39 / 260 | 36 / 182 | 50 / 176 | 26 % | 42 |
| Sö 128 | sodermanland | 1.13 | 0.1–0.5–1.2 | 8 / 288 | 118 / 852 | 70 / 330 | 62 / 220 | 26 % | 8 |
| Sö 162 | sodermanland | 0.64 | 0.4–0.6–0.7 | 7 / 84 | 45 / 334 | 47 / 233 | 1 / 60 | 28 % | 6 |
| Sö 206 | sodermanland | 0.67 | 0.6–0.9–1.2 | 41 / 1012 | 123 / 866 | 150 / 733 | 94 / 616 | 29 % | 26 |
| Vg 103 | vastergotland | 0.86 | 0.1–0.4–0.8 | 14 / 260 | 153 / 1605 | 114 / 473 | 88 / 329 | 26 % | 15 |

Spår / gropar per reglageläge.

## Bedömning (2026-11-07, efter bilderna)

- **Mycket bra:** Gs 11 (runor och ornamentik nästan som en ritning), Sö 113, Vg 103, M 3 (korset och slingorna).
- **Bra men brusigt:** Sö 206 och Sö 162 – runorna tydliga, men vittringsfläckar i fälten mellan slingorna blir röda.
- **Fel att notera:** på Sö 128 blir en hel ramslinga grå – ett stort sammanväxt nät räknas som grop; i dialogen går det bara att klicka bort, inte att göra en grå fläck till spår.
- **Svagare:** U 1144 (splittrat) och gravhällen Ög 2 (ett tätt nät av ornamentik).
- **Fungerar inte:** Hs 14 (grovkornig yta, stavlösa runor) – som väntat.
- Bedömningen är gjord med ögat. Om bilden hjälper vid läsning är inte mätt; nästa steg är ett prov med kända runor.

## Skanningarna

- Gs 11 (Gs 11_1_4 thin05.stl): Skanning: Laila Kitzler Åhfeldt, Riksantikvarieämbetet, CC BY 4.0, doi:10.5281/zenodo.13347851
- U 1144 (U 1144 thin05 closed holes.stl): Skanning: Laila Kitzler Åhfeldt, Riksantikvarieämbetet, CC BY 4.0, doi:10.5281/zenodo.13347851
- Ög 2 (Og 2_thin03.stl): Skanning: Laila Kitzler Åhfeldt, None, CC BY 4.0, doi:10.5281/zenodo.17571537
- Hs 14 (HS_14_1mm_complete thin03.stl): Skanning: Laila Kitzler Åhfeldt och Henrik Zedig, Länsstyrelsen Västra Götalands län, CC BY 4.0, doi:10.5281/zenodo.15638873
- M 3 (M 3 Berga thin02.stl): Skanning: Laila Kitzler Åhfeldt och Henrik Zedig, Länsstyrelsen Västra Götalands län, CC BY 4.0, doi:10.5281/zenodo.14141222
- Sö 113 (So 113_1_4 thin_closed holes.stl): Skanning: Laila Kitzler Åhfeldt, Riksantikvarieämbetet, CC BY 4.0, doi:10.5281/zenodo.11951255
- Sö 128 (So 128_1_4 thin closed holes.stl): Skanning: Laila Kitzler Åhfeldt, Riksantikvarieämbetet, CC BY 4.0, doi:10.5281/zenodo.11951255
- Sö 162 (So 162_1_4_closed holes.stl): Skanning: Laila Kitzler Åhfeldt, Riksantikvarieämbetet, CC BY 4.0, doi:10.5281/zenodo.11951255
- Sö 206 (So 206_thin03_closed holes.stl): Skanning: Laila Kitzler Åhfeldt, Riksantikvarieämbetet, CC BY 4.0, doi:10.5281/zenodo.11951255
- Vg 103 (Vg 103 thin03 closed.stl): Skanning: Laila Kitzler Åhfeldt, Riksantikvarieämbetet, CC BY 4.0, doi:10.5281/zenodo.14046713
