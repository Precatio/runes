# Analysplan: utvandrarna och hemmet (2026-10-30)

Viktors fråga: vad säger de vikingatida runinskrifterna utanför Norden om det gamla hemmet? Märks saknad, personer
från förr eller gamla gudar i det nya landet – eller lämnade man det bakom sig? Del två till "Vad berättar
runskrifterna på de brittiska öarna?".

## Vad som redan är sett (planen är inte blind för detta)
En första beskrivande genomgång (`utdata/utvandrarna/forsta_blick.py`, commit 8d4b989) har redan visat, med
reguljära uttryck på Rundatas engelska översättningar: inga nordiska platser i de 29 västliga minnesinskrifterna;
släkt bakåt 9/29 mot Norge 6/43 (p 0,14); gudanamn i 17/56 nordiska namn i väster mot Norge 21/113 (p 0,12).
Därför avgörs H1–H3 bara på den handkodning som görs efter denna plan, mot den jämförelse som låses här (Norge), och
H4–H5 är frågor som inte har tittats på.

## Material
- **Väster:** vikingatida (datering börjar med V) inskrifter i Rundata med signum IM, E, IR, Sc, Or, Sh, som är
  minnesinskrifter (formeln i `forsta_blick.py`: in memory of, raised … stone/cross, erected … cross, made this …
  vault/tomb, laid this stone).
- **Huvudjämförelse: Norge** (signum N, samma urval). Skäl, givet före resultaten i denna plan: de västliga
  inskrifterna är till största delen ristade med kortkvistrunor av norsk typ (Barnes & Page 2006), så Norge är det
  gamla hem som de flesta kom ifrån.
- **Sekundära jämförelser:** Danmark (DR) och Sverige (svenska landskap), med reguljära uttryck och utan handkodning.
- **Österled och Nordatlanten** (Berezan, Pireus, Hagia Sofia, Narsaq, Färöarna): citeras och beskrivs, prövas inte.
- Bilderna på korsen finns inte i Rundata och räknas inte; de redovisas ur litteraturen med källa.

## Kodning (handkodning, `utdata/utvandrarna/kodning.csv`, en rad per inskrift i väster och Norge)
- **plats_andra_sidan:** inskriften nämner ett land, folk eller en ort på andra sidan havet – för väster en nordisk
  plats eller ett nordiskt folk, för Norge en plats utanför Norden.
- **slakt_bakat:** en person identifieras med sin far eller mor (X:s son/dotter, son till X) utöver relationen mellan
  resare och död (sin son, sin far räknas inte).
- **slakt_bakat_nordisk:** som ovan, men föräldern har ett nordiskt namn (känslighetsprov mot gaeliskt *mac*-skick).
- **pris:** den döde eller resaren får ett omdöme (god, bäst, duglig, tapper, mild, frikostig, snäll med flera) eller
  ett ordspråk om vad som är gott.
- **namn:** varje personnamn en gång per inskrift, med ursprung (nordiskt, gaeliskt, anglosaxiskt, osäkert) efter
  `utdata/brittiska/kodning.csv` för väster; gudanamn = nordiskt namn som börjar på Þór-/Þor-/Þúr-, Ás-/Ást-, Frey-,
  Ingi-/Yngv-, Guð-.
- **generation (bara Man):** par där både förälder och barn är namngivna och båda namnens ursprung är kända.

## Prövningar (Fisher, α 0,05, Holm över H1–H4)
- **H1 Hemmet:** väster nämner andra sidan havet mer sällan än Norge (ensidigt, väster < Norge).
- **H2 Släkt bakåt:** väster identifierar personer med föräldern oftare än Norge (ensidigt, väster > Norge).
  Känslighet: samma med *slakt_bakat_nordisk*.
- **H3 Gudanamn:** en större andel av de nordiska namnen i väster bär en gud än i Norge (ensidigt, väster > Norge).
- **H4 Pris (ny):** andelen inskrifter som prisar den döde skiljer sig mellan väster och Norge (tvåsidigt).
- **H5 Generationerna (ny, beskrivande):** antal par nordisk förälder → gaeliskt barn och gaelisk förälder → nordiskt
  barn. Teckentest bara om minst 8 par.
- Sekundärt, beskrivande: samma andelar för Danmark och Sverige med reguljära uttryck, utan Holm.

## Tolkning, bestämd i förväg
- H1 håller: utvandrarna talar inte om hemmet, mer än de som stannade hemma talar om resorna – "man såg framåt".
- H1 faller: tystnaden om hemmet är inte större än vanligt; en minnesinskrift nämner sällan platser alls.
- H2 håller, också i känslighetsprovet: släkten bakåt var viktigare i det nya landet. Håller bara utan
  känslighetsprovet: gaeliskt namnskick, inte nordiskt minne.
- H3 håller: de gamla gudarna fanns kvar i namnen. Faller: lika många som hemma – inte färre.
- Små tal: väster har omkring 30 minnesinskrifter; en skillnad som inte håller är inte belägg för likhet.
