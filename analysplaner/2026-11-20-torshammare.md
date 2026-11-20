# Analysplan: torshammare i svensk jord – var, när, i vilket sammanhang, och i runstenarnas bygder?

Skriven och låst 2026-11-20, innan något nedan har räknats per landskap, härad, sammanhang eller period. Viktor
2026-11-20: frågan "hur många hedniska symboler som hittats i marken … var hittade man torshammar-smycken, och vilken ålder
är de från?"; efter källinventeringen "är det bättre att bara undersöka Sverige" → ja, "kör så". Norge och Danmark
räknas inte (deras material är av annat slag: Unimus har ~25–30 hängen med oklar metadatalicens, Danmark nästan bara
detektorfynd sedan 2018 per kommun). De nämns bara ur litteraturen (Nordeide 2006).

## Känt före låsningen
- Källinventeringen (2026-11-20) hämtade Statens historiska museers (SHM) samlingar via samlingar.shm.se (metadata
  CC0): sökorden och föremålsbenämningarna i `downloads/torshammare/shm/_totals.json` (t.ex. benämningen
  Torshammarring 380 poster, Torshammare 118, Torshammarhänge 5). Grovt uppskattat ~530 äkta poster; en brynsten låg
  bland träffarna. K-samsök gav ~50 poster utanför SHM (främst Gotlands museum).
- För att se fältens ordförråd tittade jag på benämningen Torshammare (118 poster): Tidsperiod mest "Vikingatid" (80)
  och "Järnålder" (24); Arkeologisk kontext t.ex. "Brandgrav, Grav, Hög", "Skattfynd", "Stensättning", "Husgrupp",
  "R-enhet, Ruta", tomt i 24. Inget annat är uppdelat.
- Ingen gjutform för torshammare finns i någon av databaserna. Litteraturen (Nordeide 2006, Staecker 1999): järnringar
  med små hammare i Mälardalens gravar 700–900-tal; enstaka hängen (silver, brons) i södra Skandinavien, oftare i
  skatter och lösfynd. Det är bakgrunden, inte något vi prövar.

## Underlaget (bestämt nu)
- **SHM-poster**: unionen av alla CSV-filer i `downloads/torshammare/shm/` (on_* och q_*), unik på Föremålsnummer.
  `on_Gjutform` och `on_Amulett`/`on_Amulettring`/`on_Hammare` ingår men gallras av regeln nedan.
- **Äkta torshammare** (regeln, i ordning):
  1. Benämningen innehåller Torshammar/Thorshammar, eller är "Miniatyr hammare" → med.
  2. Benämningen är Amulett, Amulettring, Amuletthänge, Hammare eller Gjutform → med bara om benämning + Titel +
     Beskrivning matchar `th?orshammar|hammarformad|hammarformat|hammarhänge|miniatyrhammare|med hammare|hammarhängen`.
  3. Bort: Tidsperiod som bara anger sten- eller bronsålder; text med "brynsten", "stenyxa", "yxa av sten";
     Material bara "Sten" (utom gjutform).
- **Typ**: *ring* om benämning/titel innehåller "ring" (torshammarring, amulettring med hammare); *gjutform* om
  benämningen är Gjutform; annars *hänge*.
- **Sammanhang** ur Arkeologisk kontext (om tom: Titel + Beskrivning + Fyndplats, Plats), första som träffar:
  *skatt* (skatt|depå); *grav* (grav|stensättning|hög|röse|skelett|kremering|urna|brandlager|kammargrav|båtgrav);
  *boplats* (hus|grop|kulturlager|boplats|stolphål|härd|svarta jorden|R-enhet|ruta|lager); *lösfynd*
  (lösfynd|detektor|påträffad i åker|plöj); annars *okänt*. "Hög" matchas bara som eget ord.
- **Period** = Tidsperiod som den står (Vendeltid, Vikingatid, Järnålder, Medeltid, flera, tom/Odaterad).
- **Material** = Material grovt: järn, silver, brons/kopparlegering, annat/tomt.
- **Enheter**: posten är huvudmåttet (en katalogpost kan ha flera hammare, och Antal används olika). Föremål
  (Antal, 1 om tomt) redovisas som känslighet.
- **Plats**: Fyndplats Landskap och Socken; socknen kopplas till härad och läge via `data/geo/socknar_harader.json`
  (Wikidata, CC0) på namn + landskap. Okopplade redovisas.
- **Gotland** redovisas för sig (SHM + K-samsöks poster från andra förvaltare, samma regel på itemName/itemLabel/desc;
  dubbletter mot SHM bort på föremålsnummer). Gotland ingår inte i testet T1 (egna museet, egen fyndbild).

## Kvalitetsgrind (före allt annat)
- Alla poster som kommer med via regel 2 bedöms för hand, och 50 slumpade (seed 20261120) via regel 1. Kräver ≥ 95 %
  riktiga i regel 1-provet; poster i regel 2 som bedöms fel tas bort och listas.
- Sammanhanget: 60 slumpade poster (seed 20261121) klassas för hand utan att se regelns svar; kräver ≥ 85 %
  överensstämmelse. Annars revideras orden en gång (tillägg) och provet görs om; klarar det inte heller det redovisas
  bara grav/ej grav.

## Beskrivande mått
- **D1** antal poster och föremål, per landskap och typ (ring/hänge/gjutform).
- **D2** sammanhang per typ och per landskap (andelar).
- **D3** period per typ.
- **D4** material per typ.
- **D5** karta per härad (antal poster), med runstenarna som eget lager.
- **D6** Mälardalens andel (Uppland, Södermanland, Västmanland, Närke) av ringar respektive hängen.
- **D7** de fem socknar med flest poster (en enda grävning kan fylla ett helt landskap, t.ex. Birka).

## Test T1 – hammare i runstenarnas bygder? (låst)
- Enhet: **härad** (de gamla gränserna; socknar är inte oberoende) utanför Gotland, med en exponering ≥ 5.
- **Exponering** = SHM-poster med benämningen Kam eller Spänne och Tidsperiod som innehåller "Vikingatid", per härad:
  ett mått på hur mycket vikingatida material som alls har grävts fram och registrerats där. Hämtas efter låsningen
  (CSV-export, ≤ 1 anrop/s), samma koppling socken → härad.
- **Runstenar** = svenska vikingatida runstenar (`src/research_gaps.is_runestone`) per härad, via socknens namn till samma
  Wikidata-härad.
- Modell (R, lme4): `glmer(hammare ~ log2(runstenar + 1) + offset(log(exponering)) + (1 | landskap) + (1 | härad),
  family = poisson)` (härad-nivåns slumpterm tar överspridning). Rapporteras: kvot per fördubbling av runstenarna med
  95 % intervall. Tvåsidigt; ingen riktning förutsägs.
- Ett samband sägs finnas bara om hela intervallet ligger på samma sida om 1, och det håller även **utan Adelsö socken
  (Birka)**. Sekundärt, utan egen slutsats: samma modell för ringar och hängen var för sig.
- Faller testet (intervallet täcker 1), står det i resultatet och artikeln: hammarna följer inte runstenarna när man
  tar hänsyn till hur mycket som har grävts.

## Vad som redovisas
Allt ovan, oavsett utfall, i `utdata/torshammare/resultat.md`. Enskilda fynd anges med socken, inte med finnare eller
exakt läge utöver vad SHM själv visar. Inga slutsatser om tro eller religion utöver vad fynden bär: en torshammare i en
grav visar en sed, inte vad den döde trodde. Källa krediteras: Statens historiska museer, samlingar.shm.se (CC0);
K-samsök/förvaltande museum för Gotlandsposterna.
