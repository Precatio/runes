# Analysplan: Upptäcktsmotorn, version 1 – parskanning i två steg

Låst 2026-10-28, innan motorn har körts. SHA-256 i `analysplaner/2026-10-28-upptacktsmotorn.sha256`. Kod:
`src/discovery.py` (dragen) och `r/discovery.R` (skanningen). Resultat i `utdata/upptackt/`.

## Syfte
Hitta samband mellan stenarnas drag som ingen har frågat efter, utan att lura sig själv: hypoteserna tas fram på ena
halvan av korpusen, fryses med en kontrollsumma och prövas sedan på den andra halvan, som upptäcktssteget inte sett.

## Material
Svenska vikingatida runstenar i korpusen (`corpus.csv`) med minst fyra läsbara ord (`n_words_core ≥ 4`). Halvorna:
socken för socken, växelvis inom varje landskap i sockenmedeldateringens ordning, som i change.R (halva A upptäcker,
halva B bekräftar).

## Dragen (binära, en kolumn per drag; saknas när draget inte går att avgöra)
- **Innehåll:** cat_sjalvminne, cat_bro_vag, cat_kristen, cat_fard, cat_arv, cat_ting, cat_magisk, pm_hednisk.
- **Tro i detalj:** pm_kors, pm_bon, pm_sjal.
- **Skrift och språk:** pm_stungna, trait_stungen_e, trait_stungen_y, trait_stungen_g, pm_monoftong, au_och monoftong,
  pm_o_runa, pm_r_for_R, nasal utelämnad, h saknas, prepositionen *at*, bindrunor, short_twig (kortkvistrunor), varje
  skiljetecken (punkt, kryss, kolon, apostrof, plus, blandat).
- **Ristaren:** pm_signatur, has_carver.
- **Budskap:** msg_dod_uppgift, msg_dod_borta, msg_resa, msg_gald, msg_gard, msg_berom.
- **Människorna:** kvinna bland resarna, kvinna ensam resare, flera resare, en kvinna bland de döda, rel_barn,
  rel_foralder, rel_syskon, rel_make, rel_slakt, rel_ej_slakt, drengr, thegn, god.
- **Landskap (stenar på plats):** inom 500 m från gravfält, hög, väg, bro, fornborg, kyrka; inom 1 km från vatten.
- **Monument:** höjd minst 1,6 m (medianen bland mätta hela stenar).

## Kontroller i varje modell
Landskap (faktor), tidsskikt (som messages.R, odaterad som eget skikt) och log(1 + antal läsbara ord).

## Steg 1: upptäcka (halva A)
För varje par av drag (a, b) som inte hör till samma familj (nedan): logistisk regression b ~ a + kontroller bland
stenar där båda dragen är kända. Paret prövas bara om båda dragen finns på minst 20 stenar och båda saknas på minst
20 stenar i halvan. Kandidat om Benjamini–Hochberg q < 0,05 och |oddskvot| ≥ 1,5 (eller ≤ 1/1,5). Högst 50
kandidater (minst q först). Kandidatlistan skrivs till `kandidater.json` och dess SHA-256 till `kandidater.sha256`
innan halva B läses.

**Familjer (par inom samma familj prövas inte, eftersom de hänger ihop genom hur dragen är definierade):**
kristen (cat_kristen, pm_kors, pm_bon, pm_sjal); stungna (pm_stungna, stungen_e, stungen_y, stungen_g);
egen (cat_sjalvminne); resa (cat_fard, msg_resa, msg_dod_borta, msg_dod_uppgift, msg_gald); arv (cat_arv, msg_gard);
ristare (pm_signatur, has_carver); beröm (msg_berom, drengr, thegn, god); resare (kvinna bland resarna, kvinna ensam,
flera resare); relation (alla rel_*); skiljetecken (alla); landskap (alla avstånd); hednisk (pm_hednisk, cat_magisk).

## Steg 2: bekräfta (halva B)
Varje kandidat prövas i halva B med samma modell plus ristaren som slumpeffekt (mgcv), ensidigt i den riktning steg
1 fann. **Bekräftad:** Holm-p < 0,05 över kandidaterna. **Mönster att pröva:** BH-q < 0,05 men inte Holm. Annars:
höll inte. Alla kandidater redovisas med oddskvot i båda halvorna, också de som inte höll.

## Sekundärt (redovisas, ändrar inget)
Samma två steg med halvorna bytta (B upptäcker, A bekräftar). Ett par som bekräftas åt båda håll redovisas som
särskilt stabilt.

## Efteråt
Bekräftade par som redan finns i mönsterregistret eller är kända i forskningen märks så i rapporten. Nya par blir
förslag till egna, låsta planer och läggs inte direkt i Statistik.
