# Analysplan: håller ”stenarna står vid lerans kant” för de invändningar som litteraturen reser?

Skriven och låst 2026-11-10, innan någon av kontrollerna nedan har räknats. Viktor 2026-11-10: ”YES” på att starta
novembers kontroller för lerartikeln (`PUBLICERINGSPLAN.md`). Bygger på det beskrivande resultatet efter den låsta planen
2026-11-08-palm-jordarna (`utdata/palm_jordarna/platsen.py`, `platsen.json`): runstenarna står mer sällan *på* lera och
silt än slumpvisa platser på land i samma 2 km-ruta (28 mot 37 %) men oftare *inom 200 m från* den (52 mot 40 %).

## Invändningarna (ur litteraturgenomgången, kontrollerade mot originaltexten innan de används)
1. **Bortfall på lera:** stenar på plöjd lerslätt har oftare försvunnit eller flyttats (Söderberg m.fl.; Ambrosiani 1972;
   Arrhenius i recension; Alvastra: stenar sprängdes bort för åkerns skull). Då kan ”inte på leran” vara ett bortfall.
2. **Bortfall på sand och grus:** grustäkter och vägbyggen tog stenar på åsar och sand (Åby 1985; Hovgårdsberg 1935).
3. **Åsvägarna:** åsarna var de första vägarna (Lovén). Kanten kan vara åsen eller vägen, inte leran.
4. **Hävd och våtmark:** kanten kan vara ängen och den våta marken, inte åkern (Myrdal 1982).
5. **Vattennivån:** Mälarens och sjöarnas nivå var en annan; sjösänkningar på 1800-talet (Lindqvist 1926, 1928; Edberg).
6. **Flyttade gårdar:** gårdarna flyttades under yngre järnåldern (Göransson via Welinder 1971). Kan inte prövas med våra
   data (kräver 1600-talets kartor och fosfat); redovisas som begränsning.
7. **Malmers dos–respons:** ju kostsammare monument, desto mer på den bästa jorden (Malmer 1988). Beskrivande.

## Data
Som i platsen.py: vikingatida runstenar i korpusen (`corpus.csv`), SGU:s jordartskarta i 100 m-rutnät
(`jordart_100m.tif`: 1 lera och silt, 2 sand och grus, 3 morän, 4 torv och gyttja, 5 berg, 7 övrigt), vatten år 1050
(`vatten1050_100m.tif`, SGU-skiktet 900 år före nutid), bygderutorna om 2 km (`rutor_2000.csv`) och slumpvisa platser på
land i samma ruta (50 per sten, frö 2026). ”Kanten” = inom 200 m från lera och silt som var land år 1050; ”på leran” =
jordarten under stenen.

## Kontrollerna
**K1. Bortfall per jordart (invändning 1 och 2).** Alla vikingatida runstenar med koordinater i bygderutorna, också
försvunna (`lost == 1`) och flyttade. Försvunna stenars koordinater är den uppgivna platsen; koordinater som delas av tre
eller fler stenar räknas inte (troligen sockenpunkt eller kyrka). Andelen försvunna per jordart under den uppgivna
platsen: lera och silt, sand och grus, morän, berg. Sedan räknas skillnaden ”på leran” och ”vid kanten” om **med** de
försvunna stenarna på sina uppgivna platser. **Håller** om skillnaden mot slumpen (sten minus slump) för kanten
fortfarande är > 0 och för ”på leran” fortfarande < 0, med 95 % blockbootstrap-intervall (block om 20 km, som tidigare)
som inte omfattar 0. Dessutom beräknas hur många försvunna stenar *på leran* som skulle behövas för att utjämna
underskottet på leran, mot hur många försvunna stenar som finns.

**K2. Åsar och sand (invändning 3).** Punktmodell: varje sten (1) mot dess 50 slumpvisa platser (0) i samma ruta,
villkorad logistisk regression med rutan som stratum (`survival::clogit`). Förklaringar: vid kanten (inom 200 m från lera
och silt), inom 200 m från sand och grus. **Håller** om kantens koefficient fortfarande är > 0 (ensidigt p < 0,05) med
sand och grus i modellen.

**K3. Våt mark (invändning 4).** Samma modell som K2 med också ”inom 200 m från torv och gyttja”. **Håller** om kantens
koefficient fortfarande är > 0 (ensidigt p < 0,05).

**K4. Vattennivån (invändning 5).** Skillnaden ”vid kanten” och ”på leran” räknas om med vattnet enligt SGU-skiktet 1000
år före nutid (omkring år 950) i stället för 900 år. **Håller** om kantens skillnad är > 0 med 95 %-intervall som inte
omfattar 0 med båda skikten. (Ett test med strandlinjen ±1–3 m kräver en höjdmodell, D2 i publiceringsplanen, och görs
när den finns.)

**K5. Flyttade enligt Runor 2020.** Huvudresultatet räknat utan de stenar som Runor 2020 anger som inte på ursprunglig
plats (`original == False`) men som korpusen räknar som orörda. **Håller** som K4.

**K6. Malmers dos–respons (beskrivande, invändning 7).** Bland stenarna som står kvar: andelen på leran och vid kanten
efter textens längd (antal ord, tredjedelar), om stenen har ornamentik (stilgrupp angiven) och om den har kors.

## Tolkning (bestämd nu)
- Håller K1–K5 står resultatet: stenarna står vid lerans kant, inte bara för att stenarna på leran försvann, inte för att
  kanten är en ås eller våtmark, och inte på grund av vattennivån. Artikeln publiceras med kontrollerna beskrivna.
- Håller K1 inte, kan bortfallet förklara mönstret, och artikeln skrivs om: mönstret kan vara vilka stenar som överlevde.
- Håller K2 eller K3 inte, skrivs artikeln om så att kanten beskrivs som åsen respektive den våta marken.
- Håller K4 eller K5 inte, beskrivs resultatet som känsligt för vattennivån respektive flyttningarna.
- Invändning 6 kan inte prövas och nämns som begränsning.

## Redovisning
`utdata/palm_jordarna/kontroller.py` och `kontroller.R`, `kontroller.json`, `kontroller.md`.
