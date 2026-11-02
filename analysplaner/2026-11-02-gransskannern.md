# Analysplan: gränsskannern (IMPLEMENTATIONSPLAN 5.5)

Skriven och låst 2026-11-02, innan skannern har körts. Viktor 2026-11-02: "gör allt detta" (Fas 5). Generalisering av
gränsprovet i `analysplaner/2026-11-01-upplands-folkland.md` (steg 3), där *at* skilde skarpt vid gränsen
Tiundaland–Attundaland.

## Data
De 27 dragen i folklandsplanen, ur `utdata/upptackt_v3/drag.csv` (korpus e83202e0). Regionen är `src/regions.old_region`
(folkland, små land, tredingar, övriga landskap). Socknarnas punkter ur `data/geo/socknar_land.csv` (för gränszonen);
för landskap utan indelning används stenarnas egna lägen.

## Steg
1. **Grannpar:** två regioner är grannar om någon sten i den ena står inom 10 km från någon sten i den andra. Par där båda
   har minst 40 stenar i dragtabellen prövas.
2. **Skillnad mellan regionerna** (för varje grannpar × drag med minst 10 stenar med draget i paret): logistisk regression
   drag ~ region + tidsskikt; kvotprov. Benjamini–Hochberg över alla prov. Skiljer: q < 0,05.
3. **Gränsprovet** (för de som skiljer): stenar inom 10 km från närmaste sten i den andra regionen, på var sida; Fishers
   exakta test ensidigt i hela parets riktning. **Skarp gräns:** p < 0,05; annars **gradient**.
4. **Halvorna** (för skarpa gränser): steg 2 i var halva (socknar varannan inom landskapet); håller om p < 0,05 och samma
   riktning i båda.
Gränsen *at* Tiundaland–Attundaland är känd i förväg och räknas med; den redovisas men räknas inte som ny.

## Redovisning
`utdata/granser/gransskannern.py`, `gransskannern.json`, `resultat.md`. Skarpa gränser som håller blir mönster att pröva.
