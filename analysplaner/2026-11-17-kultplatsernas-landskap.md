# Analysplan: kultplatsernas landskap – vad utmärkte socknarna med de heliga platserna? (upptäckt och bekräftelse)

Skriven och låst 2026-11-17, innan något av dragen nedan har räknats för kultplatssocknarna. Viktor 2026-11-17, efter att
proven med runstenarna i kultplatssocknarna inte höll: "leta vidare efter mönster".

## Känt före låsningen
- Kultplatsnamnen ur SOL (tillägg 1 till "Gudarna på kartan", f7b339ef): tätast i Mälarlanden, glesast i norr (C1
  håller). Runstenarna i kultplatssocknarna (planen 90e7af35): inte fler, inte säkert mer kristna, inte senare.
- **Tidigare prov med andra kultnamn**, som borde ha stått i planen 90e7af35 och står här: upptäcktsmotorn v2 (oktober)
  hade draget "nära kultnamn" (stamsökta namn ur `data/ortnamn/kultnamn.csv`, 2 km) bland 128 drag per runsten och fann
  inget par med det; provet "bön vid kultplatsen" (analysplaner/2026-10-29-bon-vid-kultplatsen.md) fann bön vanligare
  nära teofora namn med kyrkorna kontrollerade, men planens villkor för en artikel uppfylldes inte. Runstenarnas drag
  prövas därför inte igen här.
- Litteraturen säger allmänt att kultplatserna låg i de gamla centralbygderna (Vikstrand 2001, Brink). Det har inte
  mätts här, och ingen riktning förutsägs: detta är en upptäckt.

## Enheten och dragen
Enheten är en ISOF-socken (sockenmittpunkt) i landskap med minst tre kultplatssocknar. **Kultplatssocken** som i planen
90e7af35 (säkra och osäkra namn; de fyra samiska namnen utanför). Ett fornlämnings- eller ortnamnsläge räknas till den
socken vars mittpunkt ligger närmast, inom samma landskap (Voronoi-indelning; sockenpolygonerna är inte tillgängliga).
Dragen, var för sig:
1. gravfält (antal, log(1 + n)), 2. högar (log(1 + n)), 3. fornborg (finns), 4. hamnanläggning (finns),
5. färdväg eller färdvägssystem (log(1 + n)), 6. bro (finns) – alla ur Kulturmiljöregistret (`data/raa/lamningar.csv`);
7. medeltida kyrka före 1350 (`data/ortnamn/kyrkor.csv`, finns); 8. centralortsnamn (Husby, -tuna utan gudanamn;
`data/ortnamn/kultnamn.csv` nivå C, finns); 9. tingsnamn (SOL, tillägg 1, finns);
10–13. andelen lera/silt, sand/grus, morän och berg bland landcellerna inom 2 km från mittpunkten (SGU:s jordarter,
`utdata/palm_jordarna/jordart_100m.tif`; bara landskap där rastret täcker).
Kontroller i varje modell: landskapet och log(avståndet till närmaste andra sockenmittpunkt) – ett mått på sockens
storlek, eftersom stora socknar får fler lämningar.
**Inte med:** strandlinjen år 1050 (finns bara som avstånd för stenarna, inte som karta för socknarna), runstenarnas
drag (se ovan).

## Upptäckt och bekräftelse
Socknarna delas i två halvor: inom varje landskap, i ordning efter ISOF-id, varannan till A och varannan till B.
- **Upptäckt (A):** för varje drag en logistisk regression kultplatssocken ~ drag + landskap + log(närmaste avstånd).
  Kandidat: tvåsidigt p < 0,05. Listan fryses med en kontrollsumma innan B räknas.
- **Bekräftelse (B):** samma modell för kandidaterna; ensidigt p < 0,05 i A:s riktning, Holm över kandidaterna.
- **Bekräftat mönster:** Holm-justerat p < 0,05 i B, och samma riktning när bara socknar med ett *säkert* kultnamn
  räknas (hela materialet).
- **Halvorna bytta** (B upptäcker, A bekräftar) redovisas som robusthet; ett mönster som bara bekräftas åt ena hållet
  skrivs som svagare.

## Vad som skrivs
Bekräftade mönster beskrivs som samband: en kultplatssocken hade oftare X. Inte som orsak, och inte som att kultplatserna
*låg* vid X – mittpunkten är inte platsen. Ett mönster som inte bekräftas skrivs inte som ett fynd.

## Utdata
`utdata/asatro/landskap.py` (dragen, `landskap_drag.csv`) och `utdata/asatro/landskap.R` → `resultat_landskap.json`,
`kandidater_A.json` med `.sha256`.
