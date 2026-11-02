# Analysplan: statistiken efter de gamla gränserna (IMPLEMENTATIONSPLAN 5.2)

Skriven och låst 2026-11-02, innan någon modul har räknats med den nya regionen. Viktor 2026-11-02: "jag vill att vi
fokuserar appen mer på de gamla gränserna" … "gör allt detta" … "du kan köra allt utan mina beslut".

## Regionen
`region_old` i korpusen (`src/regions.py`, `src/r_bridge.corpus_rows`): Upplands folkland (Tiundaland, Attundaland,
Fjädrundaland, Roden), Smålands små land, Gotlands tredingar (Nordertredingen, Medeltredingen, Sudertredingen; Wikipedia,
socknarna per ting), övriga landskap som egna land; stenar vars socken inte kan knytas behåller landskapets kod.
Fördelning före låsningen: Attundaland 499, Tiundaland 391, Fjädrundaland 157, Roden 80, U utan land 53, Njudung 36,
Finnveden 31, Vedbo 17, Värend 15, tredingarna 14/12/7, övriga små land 2–6; Sö 361, Ög 216, Öl 154, Vg 131.

## Vad som byts (och inget annat)
1. **Robusthetstrappan** (`r/robustness.R`, `src/robustness.py`): regiontermen i den justerade modellen och i alla steg
   som bygger på den, och steget *utan en region i taget* (regioner med minst 30 stenar), använder `region_old` i stället
   för landskapet. Halvorna (socken för socken inom landskapet) ändras inte.
2. **Genomsökningen av platserna** (`r/remains.R`): regionen läses ur korpusens `region_old` (samma indelning som sedan
   00e2f4e, nu också Gotland).
3. **Ordförrådet** (`r/words.R`): ordens skillnader mellan regioner räknas per gammal region i stället för per landskap
   (regioner med minst lika många daterade stenar som tröskeln i modulen; övriga slås ihop).
4. **Förändringen per region** (`r/change.R`, delen per landskap och dess halvprov): per gammal region.
Allt annat (landsdelar i Människorna och Budskapen, U- och Sö-specifika delprov, landhöjningen per landskap) är oförändrat.

## Jämförelsen (redovisas oavsett utfall)
Mot den senaste beräkningen med dagens landskap (korpus 605ba7cc):
- trappan: för varje mönster om det håller i alla steg, är bekräftat och har q_global < 0,05, före och efter; listan över
  mönster som ändrar status och vilket steg som ändras;
- ordförrådet: antalet ord–region-signaler som klarar justeringen och håller i båda halvorna, och vilka;
- genomsökningen: antalet som klarar justeringen.
Inga gränser för "lyckat": bytet görs av historiska skäl, och redovisningen säger vad det ändrar.

## Redovisning
`utdata/gamla_granser/jamforelse.py`, `jamforelse.json`, `resultat.md`; METHODS.md (avsnitten för trappan, ordförrådet,
förändringen och genomsökningen); nyhet i `web/content/news.json`.
