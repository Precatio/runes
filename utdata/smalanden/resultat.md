# Smålands små land och deras runstenar – resultat

Låst plan `analysplaner/2026-11-01-smalanden.md` (sha 82ddb6e5). Kört 2026-11-01 med `utdata/smalanden/smalanden.py`; alla
tal i `smalanden.json`.

## Avvikelse
statsmodels finns inte i miljön; Benjamini–Hochberg och den logistiska regressionen (tiden konstant) är skrivna i numpy
och scipy. Steg 2 och 3 gällde bara drag som skiljer; inget gjorde det, så de kördes inte.

## Huvudprovet: Tiohärad mot de östra landen – inga skillnader
Av Smålands 121 vikingatida runstenar finns 103 i dragtabellen: 71 i Tiohärad (Värend, Finnveden, Njudung) och 32 i de
östra och norra landen. **Inget av de 22 dragen skiljer efter justering** (alla q = 1). Det minsta p gäller granit (38 mot
69 %, p 0,046), och det är berggrunden, inte seden. Kristna markörer (18 mot 16 %), kors (38 mot 31 %), bön, resor,
beröm, kvinnliga resare, släktband, *drengr* och *þegn*, ristarsignatur, ordet *kumbl* och närhet till gravfält skiljer
inte. **Den gamla rättsgränsen syns inte på runstenarna** – med reservationen att 32 stenar i öster bara räcker för att
se stora skillnader.

## Per land (beskrivande, p utan justering; 88 jämförelser, så några p under 0,05 väntas av slumpen)
- **Njudung** (31 stenar i tabellen, medelår ca 1008): stenar efter syskon 48 % mot 16 % i resten av Småland (p 0,009);
  ordet *kumbl* 6 mot 25 % (p 0,03). De flesta stenarna saknar stilgrupp.
- **Finnveden** (28, medelår ca 998): nästan aldrig granit (1 av 25 mot 63 %, p < 0,001) – berggrunden; inga
  brostenar (0 mot 15 %); *kumbl* 32 mot 15 %. 22 av 28 i den tidiga stilgruppen RAK.
- **Vedbo** (13, medelår ca 1048): nästan bara granit (8 av 9); det yngsta landet i materialet.
- **Värend** (12, medelår ca 1002): kristna markörer 42 mot 14 % (p 0,03); 10 av 12 i RAK. Den enda namngivna ristaren
  är Åsgöt.
- Kinda (Ög): 6 stenar, bara listade.

## Vad det betyder
Smålands runstenar är tidiga (medelår omkring 1000 i Tiohärad, mest stilgruppen RAK) och få per land. De små landen
skiljer sig inte på ett sätt som tål justering för antalet jämförelser; det som sticker ut per land är berggrunden
(Finnveden, Vedbo) och enstaka antydningar (syskon i Njudung, kristna markörer i Värend) som skulle behöva fler stenar
eller en egen låst plan för att prövas. Negativt huvudresultat.
