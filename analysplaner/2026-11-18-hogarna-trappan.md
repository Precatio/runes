# Tilläggsplan: runstenarna vid de stora högarna – robusthetstrappan

Skriven och låst 2026-11-18, innan något av stegen nedan har räknats. Tillägg till planen "Kullarna" (089fcfb5), prov H3.
Viktor 2026-11-18 frågade om H3 räcker för en forskningsrapport; svaret var att det kräver att mönstret håller i en
trappa av kontroller, låst före räkningen (som för Familjens plats, ec4a17c5). Viktor: "ja".

## Känt före låsningen
- **H3 höll** (089fcfb5): bland de fristående högarna med angiven diameter har de minst 20 m breda oftare en runsten inom
  500 m (Mantel–Haenszel-oddskvot över landskapen ≈ 3,2; båda halvorna; gränserna 15 och 30 m). Uppland 44 mot 20 %,
  Södermanland 44 mot 13, Medelpad 24 mot 7, Västergötland 8 mot 3, Östergötland 9 mot 11.
- H3 räknade **alla** runstenar med koordinat, också de som flyttats, till exempel till kyrkor. Flera av artikelns
  exempel står vid kyrkor som ligger vid storhögar (Skalunda, Ledberg). Kyrkor byggdes ofta vid storhögar, och stenar
  flyttades långt senare till kyrkorna. Det är den misstanke trappan ska pröva. Inget av stegen nedan är räknat.
- Litteraturen: att runstenar ofta står vid gravfält är känt (Ekholm 1950, Zachrisson 1998, Klos 2009; vår rapport om
  familjens plats). Om stora och små högar jämförts är inte kontrollerat; det görs i texten innan något påstås.

## Data
Som i 089fcfb5: de 17 531 fristående högarna, stor = diameter minst 20 m, jämförelse = angiven diameter under 20 m,
landskap = närmaste ISOF-sockens landskap. Dessutom:
- **Stenar på sin plats:** Rundatas svenska vikingatida runstenar med koordinat som *inte* räknas som flyttade
  (`r_bridge.is_moved`: placeringen säger flyttad, platsen är en kyrka, ett slott, ett museum med mera, eller
  placeringstexten nämner en annan plats än fyndplatsen).
- **Medeltida kyrkor:** Wikidatas kyrkobyggnader med uppförandeår före 1350 (`places`, "church"); långt ifrån alla.
- **Gravfält:** Kulturmiljöregistrets gravfält (`places`, "gravfalt").
- **Socken:** registrets socken för högen, tillsammans med länet.
- **Täthet:** antalet runstenar på sin plats 1–5 km från högen (inte de närmaste 1 km, så att måttet inte innehåller
  utfallet).

## Teststorhet och p-värde
Mantel–Haenszel-oddskvoten (stor mot mindre hög, runsten inom radien eller inte) över strata; p tvåsidigt ur omblandning
av etiketten stor/mindre inom varje stratum, 10 000 gånger (LOPO: 2 000), slumpfrö ur denna plans kontrollsumma. Strata utan
både stora och mindre högar bidrar inte.

## Trappan
- **T0. Återgivning:** H3 som förut (alla stenar, strata = landskap). Ska ge samma oddskvot som 089fcfb5.
- **T1. Bara stenar på sin plats:** utfallet = en runsten på sin plats inom 500 m; strata = landskap. Också i båda
  halvorna (socknarna växelvis A/B inom länet, som förut).
- **T2. Utan kyrkorna:** som T1, men högar inom 1 km från en medeltida kyrka räknas bort.
- **T3. Inom socknen:** som T1, strata = socken (län + socken). Stora jämförs bara med mindre högar i samma socken.
- **T4. Täthet och gravfält:** som T1, strata = landskap × tredjedel av tätheten (runstenar på sin plats 1–5 km;
  tredjedelarna räknade över alla högar med diameter) × gravfält inom 1 km (ja/nej).
- **T5. Ett landskap i taget utelämnat:** T1 utan vart och ett av de landskap som har minst 10 stora högar.
- **T6. Radien:** T1 med 250 m och 1 000 m i stället för 500 m.

## När håller det?
Mönstret räknas som **robust** (och rapporten skrivs) när:
- T1, T2, T3 och T4 vart och ett har oddskvot > 1 och p < 0,05;
- T1 har oddskvot > 1 i båda halvorna, med p < 0,05 i en halva som har minst 50 stora högar;
- T5 har oddskvot > 1 med varje landskap utelämnat, och p < 0,05 när minst två tredjedelar av de stora högarna är kvar;
- T6 har oddskvot > 1 med båda radierna.
Stegen är villkor som alla ska uppfyllas, så ingen korrektion för flera prov görs. Varje steg redovisas, också de som
fallerar. Bär ett enda landskap mönstret (T5) sägs det i klartext.

## Om det inte håller
Faller T1 eller T2 förklaras H3 i första hand av flyttade stenar vid kyrkor, och artikeln "Kullarna vid skogens rand"
(opublicerad) skrivs om innan den publiceras. Faller T3 eller T4 men inte T1–T2 säger mönstret att storhögar och runstenar
ligger i samma bygder, inte att stenarna sökte sig till högarna; artikeln säger då det.

## Utdata
`utdata/hogar/trappan.py` → `utdata/hogar/resultat_trappan.json`.
