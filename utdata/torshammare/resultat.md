# Torshammare i svensk jord – resultat

Enligt `analysplaner/2026-11-20-torshammare.md` (låst 14a659e, sha256 096f3d07…). Räknat 2026-11-20 med
`utdata/torshammare/analys.py` och `analys_t1.R`; siffrorna i `matt.json` och `t1.csv`. Källa: Statens historiska
museer, samlingar.shm.se (metadata CC0). Rådata ligger utanför git.

## Det viktigaste förbehållet: "Sverige" betyder Statens historiska museers samlingar
Bara 5 poster kommer från Gotland och 7 från Skåne. Det beror inte på att torshammare saknas där. Gotlands museum och
Lunds universitets historiska museum förvaltar de flesta fynden från sina landskap, och de finns inte i SHM:s öppna
data. K-samsök gav ingen ersättning: en enda Gotlandspost från en annan förvaltare (ett depåfynd i När, inget föremål).
Kartan nedan är därför SHM:s karta, och den domineras av Mälardalen. Gotland och Skåne kan inte jämföras med den.

## Kvalitetsgrinden (klarad)
- **Regel 1** (benämningen säger torshammare): 49 av 50 slumpade poster riktiga (98 %, krav ≥ 95 %). Felet var en
  "miniatyr hammare" från Alvastra kloster, medeltid, troligen leksak eller verktyg. Den ligger kvar enligt planen,
  som bara tar bort fel i regel 2, och påverkar en post.
- **Regel 2** (amulettring o.d. vars text nämner hammare): 8 poster bedömda för hand; 2 bort som bara *möjliga*
  hammare (991854_HST, ett bärnstenshänge som "kan vara skaft till torshammare"; 35525_HST, "möjl fragmentarisk
  torshammare"). Listade i `grind_bort.txt`.
- **Sammanhanget**: 58 av 60 slumpade poster klassade blint likadant som regeln (97 %, krav ≥ 85 %). De två
  missarna var gravformer som saknas i ordlistan ("rektangulär stenram", "treudd"). Regeln **underskattar alltså
  gravarna något**.
- SHM:s typ "torshammarring" omfattar också ringar utan bevarade hängen (typbestämda efter formen). Vi följer museets
  klassning.

## D1 Antal
494 poster, 620 föremål (Antal). 398 ringar, 96 hängen, 0 gjutformar (ingen gjutform för torshammare finns i SHM:s
data). Per landskap (poster): Uppland 372, Södermanland 88, Östergötland 7, Skåne 7, Öland 5, Gotland 5,
Västmanland 3, Halland 2, Gästrikland 1, Dalarna 1, Småland 1, okänt 2.

## D2 Sammanhang
- **Ringarna** (398): grav 85 %, boplats 6 %, okänt 10 %, skatt 0.
- **Hängena** (96): boplats 33 % (främst Birkas svarta jord och Helgö), grav 31 %, okänt 24 %, skatt 12 %.
- Uppland: grav 277, boplats 53, okänt 42. Södermanland: grav 82, okänt 5, boplats 1.

## D3 Period (registrets egen uppgift)
Ringar: Vikingatid 60 %, bara "Järnålder" 22 %, Yngre järnålder 5 %, Vendeltid–Vikingatid 5 %, Vendeltid 2 %,
tom 5 %. Hängen: Vikingatid 58 %, "Järnålder" 25 %, tom 6 %, Medeltid 2 (en av dem miniatyrhammaren ovan). Registret
daterar grovt. Finare datering (700-, 800-, 900-tal) står inte i posterna och kräver gravarnas egna dateringar.

## D4 Material
Ringarna är av järn (99,5 %). Hängena: järn 71 %, silver 23 %, annat/tomt 5 %, brons 1 %. Alla 4 vikingatida
Gotlandsposter är av silver.

## D5 Härader (karta; antal poster, runstenar, exponering)
Flest hammare: Färentuna härad 187 (Adelsö med Birka, Ekerö, Lovö; 48 runstenar), Sollentuna 64 (74),
Danderyds skeppslag 53 (45), Svartlösa 38 (31), Öknebo 26 (18), Vallentuna 20 (119), Sotholm 11 (53),
Ärlinghundra 7 (75). Hela listan finns i `matt.json` (D5_harad).

## D6 Mälardalen
392 av 398 ringar (98,5 %) och 71 av 96 hängen (74 %) kommer från Uppland, Södermanland, Västmanland och Närke.

## D7 Socknar
Adelsö 82, Ekerö 56, Sollentuna 55, Lovö 48, Botkyrka 32: fem socknar runt Stockholm ger 55 % av alla poster.

## T1 Hammare i runstenarnas bygder (låst test)
Underlag: 57 härader utanför Gotland med minst 5 vikingatida kammar eller spännen i SHM (exponering; 6 394 poster);
423 hammarposter i dem; 1 306 runstenar. Kopplingen socken → härad: 446 av hammarposterna utanför Gotland och 2 169
av 2 279 runstenar fick ett härad. Okopplade är främst städer utan härad (Eskilstuna, Linköping, Sigtuna, Uppsala,
Stockholm, Västerås). Kopplingen gjordes på namn + landskap, med Wikidatas genitivform ("Vendels socken") och, där
Wikidata saknar härad, Rundatas härad för socknen. Det preciserades efter låsningen men innan T1 kördes. En första
körning gav häradet ett landskap från fel kolumn (Wikidatas små land), vilket rättades. Testets siffror blev
desamma.

| modell | härader | hammare | kvot per fördubbling av runstenarna | 95 % | p |
|---|---|---|---|---|---|
| huvud | 57 | 423 | 1,71 | 1,11–2,63 | 0,015 |
| utan Adelsö socken (Birka) | 57 | 341 | 1,79 | 1,13–2,81 | 0,012 |
| sekundär: ringar | 57 | 343 | 4,51 | 1,56–13,1 | 0,005 |
| sekundär: hängen | 57 | 80 | 1,17 | 0,77–1,78 | 0,46 |

**Utfall enligt planen: ett samband finns.** Härader med dubbelt så många runstenar har omkring 1,7 gånger så många
torshammare, räknat på lika mycket framgrävt vikingatida material. Det håller utan Birka. Landskapens slumpterm
skattas till noll (modellen är singulär i den termen). Häradets term tar all variation, och kvoten påverkas inte.

**Utforskande kontroller (inte låsta, inga egna slutsatser):** med landskap som fast effekt blir kvoten 1,78
(0,96–3,30). Bara Uppland (15 härader): 3,48 (1,31–9,27). Utanför Mälardalen (31 härader, 16 hammare): 1,14
(0,59–2,19). Sambandet bärs alltså av **ringarna** och av **Mälardalen**, framför allt bygderna runt nuvarande
Stockholm. Utanför Mälardalen finns för få hammare i SHM:s data för att säga något.

## Vad det betyder och inte betyder
- Ringarna är en gravsed i Mälardalen, och hängena är spridda och hamnar oftare på boplatser och i skatter. Det
  stämmer med litteraturen (Nordeide 2006, Staecker 1999). Vi har mätt det i SHM:s eget register, inte upptäckt det.
- Inom Mälardalen gav de härader som har många runstenar också fler hammarringar, även räknat på hur mycket som har
  grävts. Ringarna ligger i gravar som oftast är äldre än runstenarna. Det är alltså inte samma människor vid samma
  tid. Fynden visar att samma bygder först begravde sina döda med torshammarringar och sedan restes runstenar där.
  Varför går inte att säga ur detta.
- En torshammare i en grav visar en sed, inte vad den döde trodde.
- Exponeringen (kammar och spännen) mäter registrerat vikingatida material, inte fyndförhållandena i övrigt.
  Uppdragsarkeologin runt Stockholm kan påverka båda sidor på sätt som exponeringen inte fångar.

## T2 Kultplatssocknarna (tillägg 1, låst 5b64d88)
Viktor 2026-11-21: "kultplatser?" Kultplatssocknarna är asatro-studiens blindkodade lista ur SOL (78 socknar, 30 med
säkert namn). Gravfält och högar kontrollerades, eftersom kultplatssocknarna har fler gravar och ringarna är gravfynd.
Räknat med `analys_t2.py` och `analys_t2.R`; siffrorna i `t2.csv` och `t2_beskrivning.json`.

**Underlaget räcker inte.** 94 socknar har minst 3 vikingatida kammar eller spännen i SHM. Bara 7 av dem är
kultplatssocknar, och bara 2 har ett säkert namn. I *alla* kultplatssocknar finns sammanlagt **3 hammarposter**:
Österåker (U, osäkert namn) 2 ringar och Frötuna (U, osäkert namn) 1 hänge. Frötuna har ingen exponering och kommer
därför inte med i modellen. Socknar som saknas i ISOF-tabellen (Ekerö 56 poster, städerna) ger 106 okopplade
hammarposter. Ingen av dem är en kultplatssocken.

| modell | kultsocknar | hammare i dem | kvot | 95 % |
|---|---|---|---|---|
| huvud | 7 | 2 | (konvergerar inte) | – |
| utan Adelsö | 7 | 2 | 0,51 | 0,02–12,7 |
| bara säkra namn | 2 | 0 | – | – |
| sekundär: ringar | 7 | 2 | 0,76 | 0,02–27,8 |
| sekundär: utan gravkontroller | 7 | 2 | 0,48 | 0,03–7,8 |

**Utfall: T2 håller inte, men det betyder inte att det inte finns något samband.** SHM:s fynd och kultplatsnamnen
överlappar nästan inte. Hammarna ligger i ett fåtal grävda socknar runt Stockholm (Adelsö, Ekerö, Sollentuna, Lovö,
Botkyrka), och ingen av dem har ett kultplatsnamn. Frågan kan inte besvaras med det här materialet. Den kräver
fynden från de grävda kultplatserna själva (t.ex. Uppåkra, Lunda i Strängnäs, Gamla Uppsala), som ligger i
litteraturen och delvis hos andra museer.
