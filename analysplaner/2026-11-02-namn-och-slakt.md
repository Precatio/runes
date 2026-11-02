# Analysplan: Namn och släkt – ny modul i korpusanalysen (IMPLEMENTATIONSPLAN 5.4)

Skriven och låst 2026-11-02, innan modulen har räknats. Viktor 2026-11-02: sektion under Statistik (R) där vi studerar
namn och potentiella släktmönster, med de gamla gränserna ("gör allt detta plus släktleden").

## Känt före låsningen
Namnled i familjen (`analysplaner/2026-10-29-namngivning-i-familjen.md`, `utdata/namngivning/`): förälder–barn 5,3 mot
2,8 %, syskon 6,7 mot 2,9 %, båda halvorna (omblandning inom landskapet). Grannar delar namn ungefär 8 gånger oftare inom
1 km (`spatial-spacing`, odokumenterad i modul). Släktlänkarna (`data/links.json`, modell M2) och släkterna
(`utdata/slakt/steg2a.json`). Regionen `region_old` (plan 13084e18). Inga namn är prövade per gammal region.

## Data
`src/names_data.py` skriver per korpus `names_pairs.csv` (förälder–barn- och syskonpar ur `src/entities.extract`, som i
namngivningsanalysen, med stenens region_old, socken, halva, tidsskikt) och `names_stones.csv` (en rad per runsten:
signum, region_old, socken, halva, koordinater, namnnycklar utom ristare). Namnleden som i namngivningsanalysen
(datadriven delning; led kortare än tre bokstäver räknas inte). Vanliga namn: de 60 vanligaste namnnycklarna (som
länkmodellens COMMON) räknas inte i grannprovet.

## Prov (r/names.R; 9 999 omblandningar, frö 2026)
1. **Namnled i arv** (upprepning av den låsta planen med regionen som skikt): andelen par med delat namnled mot
   omblandning inom region_old; förälder–barn och syskon; båda halvorna.
2. **Grannar delar namn:** par av stenar inom samma region i avståndsbanden < 1, 1–5, 5–20 och 20–50 km; andelen par som
   delar minst ett ovanligt namn. Mått: kvoten mot bandet 20–50 km. Prov: andelen i < 1 km mot 20–50 km med omblandning
   av stenarnas namnlistor inom regionen. Båda halvorna.
3. **Namnens geografi:** namn på minst 10 stenar × regioner med minst 30 stenar: andelen stenar i regionen med namnet mot
   resten (Fishers exakta test), Benjamini–Hochberg över alla par; ett namn **hör till** en region om q < 0,05, oddskvoten
   > 1 och p < 0,05 i båda halvorna.
4. **Namnskicket per region:** överskottet av delat namnled (observerat minus väntat vid omblandning inom regionen) per
   region med minst 40 förälder–barn-par; skillnaden mellan regionerna prövas med omblandning av regionetiketterna
   (statistiken: variansen mellan regionernas överskott). Beskrivande per region.
5. **Släktmönster (beskrivande):** för släkterna i `steg2a.json` och de säkra länkarna i `data/links.json`: andelen
   länkade stenpar i samma socken, i samma region och avståndet (median, kvartiler); släkternas fördelning på regioner.

## Vad som inte får göras
Trösklarna (10, 30, 40, 60 vanliga namn, avståndsbanden) och omblandningarna ändras inte efter körningen.

## Redovisning
`r/names.R`, `src/names_data.py`, korpusens `names.json`; sektionen Namn och släkt i Statistik (R); METHODS.md; nyhet.
