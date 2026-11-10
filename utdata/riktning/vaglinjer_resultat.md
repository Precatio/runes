# Ristningens riktning mot vägens linje – resultat för K, L0 och L1

Plan: `analysplaner/2026-11-10-riktning-vaglinjer.md` (låst 2026-11-10, SHA-256 `ecf9039e…`, commit ee90f3e).
Kod: `utdata/riktning/vaglinjer.py` (`--klassa` skrev `vaglinjer_l1_klasser.csv` innan någon bäring räknades; `--osm`
tog ut OSM-vägarna). Siffror: `vaglinjer.json`; per sten: `vaglinjer_stenar.csv`. Körd 2026-11-10. L2
(Häradsekonomiska kartan) väntar på Viktors avritning.

Data: OpenStreetMap via Geofabrik (`sweden-latest-free.shp.zip`, utdraget daterat 2026-11-10 01:28 UTC, hämtat
2026-11-10, SHA-256 `cf03608e…`; © OpenStreetMaps bidragsgivare, ODbL): 26 368 väglinjer inom 1,5 km från stenarna.
KMR-paketet (Riksantikvarieämbetet, CC0): 15 092 linjer för färdväg, färdvägssystem och bro, varav 9 183 linjer
(5 822 lämningar) gamla vägar enligt regeln.

Måttet: medel-cos mellan ristningens riktning och riktningen till närmaste punkt på vägens linje (1 = rakt mot vägen),
mot 9 999 omblandningar inom landskapet; andelen inom 45 grader ska jämföras med 25 procent om riktningen vore slumpvis.

## Prov

**K (metoden, utan ristningarna) – godkänd.** För alla 68 stenar med väg i registrets text (gon-rättad) ligger
riktningen till närmaste OSM-linje inom 45 grader från inventerarens vägriktning för 48 av 68, 70,6 procent (gränsen
70); medianskillnaden är 15 grader. Linjemetoden hittar alltså i regel samma väg som inventeraren skrev om, men med
liten marginal till gränsen.

**L0 (grinden, dagens vägar) – håller.** 213 stenar (en ligger närmare än 2 m från vägen och räknas bort): 50 procent
vetter inom 45 grader från närmaste väg, medel-cos 0,381 mot 0,011 väntat, p = 0,0001 (det minsta möjliga). Utan
flyttade och omresta stenar (122): 46 procent, 0,329 mot 0,003, p = 0,0001. Linjemetoden återger alltså det publicerade
sambandet (48–50 procent). Medianavståndet till närmaste väg är 23 m.

**L1 (registrets gamla vägar som linjer) – håller, oavsett L2.** 34 stenar har en gammal väg (hålväg, vägbank,
vadställe, kavelbro eller förhistorisk/medeltida datering) inom 500 m: 32 procent vetter inom 45 grader från den,
medel-cos 0,156 mot −0,053 väntat, p = 0,023. Holm över L1 och L2: L1:s korrigerade p är högst 2 × 0,0226 = 0,045 hur
L2 än blir, alltså under 0,05. Utan flyttade och omresta stenar (21, färre än 30, så bara riktningen krävs): 38 procent,
0,307 mot 0,031 (p = 0,010). I klartext: mot de gamla vägarnas linjer lutar ristningarna tydligt mot vägen, men svagare
än mot dagens väg – ungefär var tredje sten i stället för varannan. En så stor lutning uppstår av slump ungefär en gång
på 45.

## Beskrivande (inga krav)

- L1 vid 300 m: 24 stenar, 42 procent, p = 0,032; vid 1 km: 60 stenar, 25 procent, p = 0,38. Sambandet finns hos
  stenar nära en gammal väg och försvinner när vägar upp till en kilometer bort räknas.
- L1 bara hålvägar och vägbankar: 33 stenar, 33 procent, p = 0,015. Bara antikvarisk bedömning Fornlämning: 20 stenar,
  40 procent, p = 0,002. Utan linjer vars beskrivning nämner runsten: 28 stenar, 29 procent, p = 0,036.
- L0 vid 300 m: 207 stenar, 50 procent; vid 1 km som vid 500 m (alla stenar har en väg inom 500 m).
- L0 bara OSM-klasserna track, path och unclassified (skogsbilvägar, stigar, mindre vägar): 204 stenar, 30 procent,
  medel-cos 0,170, p = 0,0001.
- Gon-rättade ristningsriktningar ändrar inget: L0 50 procent (p = 0,0001), L1 32 procent (p = 0,023).
- Tvärs över eller längs vägen: L0 64 procent tvärs över (vinkelrätt ± 45 grader), L1 65 procent; slumpen ger 50.
- Av de 34 stenarna i L1 har 9 också en väg i registrets text, och 13 räknas som flyttade eller omresta.

## Tolkning enligt planen

Grinden håller och L1 håller (L2 inte prövad än). Enligt planen hävs då begränsningen från självkontrollen:
S1 föll på punktbäringen, inte på att de gamla vägarna gick någon annanstans. Rapporten får skriva att ristningen
vetter mot vägen också mot gamla vägar i registret (hålvägar, vägbankar), mätt mot vägens linje, och ska redovisa L2
när den är gjord. Håller också L2 hävs begränsningen helt (planens fall "L1 och L2 håller").

Svagheter som ska stå med: ingen av vägarna är daterad till vikingatiden; L1 bygger på 34 stenar; sambandet är svagare
mot de gamla vägarna (32 procent) än mot dagens (50 procent); Holm-gränsen klaras med liten marginal (0,045, och
omblandningarnas egen osäkerhet i p är omkring ± 0,003); och vid 1 km syns inget. K klarade gränsen med en sten.
