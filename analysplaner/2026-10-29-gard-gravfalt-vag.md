# Analysplan: Gården, gravfältet och vägen

Låst 2026-10-29, innan något nedan har räknats. SHA-256 i `analysplaner/2026-10-29-gard-gravfalt-vag.sha256`.
Kod `utdata/gard_vag/analys.R` (tabell från `data.py`), resultat `utdata/gard_vag/resultat.md`.

## Bakgrund
Stengrupperna står vid gravfälten (OR 2,4) och restes inom en generation (analysplaner/2026-10-29-familjens-plats.md,
-en-generation.md); ristningarna vändes mot vägen (analysplaner/2026-10-29-ristningens-riktning.md). Nu finns
Kulturmiljöregistrets bytomter/gårdstomter (27 808), boplatser (42 008) och förhistoriska/medeltida husgrunder (3 705).
Frågan: stod familjens stenar vid gården, och stod stenarna som talar om arv och gård där – medan bro- och vägstenarna
stod vid vägen? Sett före låsningen: bara antalen lämningar per typ; inga avstånd till stenarna.

## Material
Svenska runstenar på sin plats (`moved = 0`, `lost = 0`) med koordinater, korpus 3f58e9339191761e. I grupp/ensam och
kontrollerna som i Familjens plats (landskap, tidsskikt, log(1 + runstenar inom 5 km)). **Ny kontroll för
inventeringen:** log(1 + antal lämningar av samma typ inom 5 km) – KMR är olika tätt inventerat i olika bygder.
Logistisk regression (glm).

## Test (Holm över H1–H4, α = 0,05)
1. **H1 Gården:** bytomt/gårdstomt inom 500 m, i grupp mot ensam. Förväntat: oddskvot över 1.
2. **H2 Den förhistoriska boplatsen:** boplats eller förhistorisk/medeltida husgrund inom 500 m, i grupp mot ensam.
   Förväntat: över 1.
3. **H3 Arvsstenarna vid gården:** bland alla stenar på plats, budskapet arv eller gård (`cat_arv` eller `msg_gard`)
   mot övriga: bytomt inom 500 m. Förväntat: över 1.
4. **H4 Bro- och vägstenarna vid vägen:** bland alla stenar på plats, `cat_bro_vag` mot övriga: registrerad färdväg,
   vägmärke eller bro (KMR) inom 200 m. Förväntat: över 1.
**Håller:** Holm-p < 0,05 och samma riktning med p < 0,05 i båda halvorna (socken för socken som i change.R).
**Antydan:** Holm-p < 0,05 utan halvorna, eller okorrigerat p < 0,05.

## Robusthet (redovisas)
Avstånden halverade och dubblerade (250 m/1 km; 100 m/400 m för H4); utan inventeringskontrollen; bara Uppland och
Södermanland; avståndet till närmaste bytomt som kontinuerligt mått (log meter, linjär regression) för H1 och H3.

## Förbehåll
Bytomterna är kända från 1600–1700-talens kartor; vikingatidens gårdar kan ha legat annorlunda. Boplatser är oftast
odaterade och kan vara stenålder. KMR:s vägar och broar är oftast yngre än stenarna.
