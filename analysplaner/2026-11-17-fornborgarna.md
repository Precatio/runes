# Analysplan: fornborgarna – vatten, bygd och gränser

Skriven och låst 2026-11-17, innan något av proven nedan har räknats. Underlag för en populärvetenskaplig artikel (Viktor
2026-11-17: "Fornborgarna förtjänar sin egen artikel … Vad var de? Var de borgar? Vad finns kvar?"; "kör alla tre").

## Känt före låsningen
- **Registret:** Kulturmiljöregistret (RAÄ, hela GeoPackage, uttag 2026-11-02) har 1 304 lämningar av typen Fornborg; 1 279
  med läge, 1 261 med yta. Medianytan omkring 1 ha. Beskrivningarna nämner stup i 703, berg i terrängen 923, ingång
  563, husgrund 46; 73 är del- eller helt undersökta; 292 har namn och 79 en sägen. Bara räknat, inte jämfört.
- **Litteraturen** (öppen, sok.sqlite): Götalands och Ölands borgar dateras väsentligen till tidig folkvandringstid,
  omkring 400–500 e.Kr. (Arne 1924, efter Schnittger; Fornvännen 1927). Tolkningar: tillflyktsborgar i utkanten och
  "strategiska borgar i mitten av bygden" (Tallgren 1932); "Fornborgar förekommer ofta nära brobyar eller vid farlederna"
  (Schneider 2011); murar som avgränsade ett område snarare än försvarade det (Bornfalk Back 2016 om Olausson). Ingen
  av dem är mätt för hela landet. Olausson 1995 och Engström 1984 är inte öppna.
- Upptäcktsmotorn v2 hade "nära fornborg" som drag för runstenarna; runstenarna prövas inte här.
- I planen "Kultplatsernas landskap" (55a61e0d) var fornborg kandidat i ena halvan men bekräftades inte.

## Data
- **Fornborgarna:** de 1 279 med läge (polygonens tyngdpunkt, annars punkten), SWEREF 99 TM.
- **Jämförelsepunkterna:** för varje borg 10 slumpvisa punkter på berg i dagen (SGU:s jordarter, klass berg, rastret
  `utdata/palm_jordarna/jordart_100m.tif`) mellan 200 m och 5 km från borgen, som inte låg i vatten år 450. Borgen jämförs
  alltså med andra berg i samma trakt. Borgar där rastret inte täcker (Skåne, Halland, Blekinge, Jämtland och norr) eller
  där färre än 10 sådana punkter finns räknas bort ur huvudproven, och antalet redovisas. Slumpfrö ur planens
  kontrollsumma.
- **Vatten år 450:** SGU:s strandförskjutningsmodell, lagret `issjohav_1500` (1500 före 1950 = år 450), kod 1 (hav) och 4
  (sjö), som i strandstudien (2026-10-23). Osäkerheten i modellen redovisas som där.
- **Gravfält:** Kulturmiljöregistrets gravfält (`data/raa/lamningar.csv`), antal mellan 200 m och 2 km från punkten.
- **De gamla landen:** gränserna mellan landen i `web/public/geo/land.geojson` (de delar av polygonernas kanter som är
  gemensamma för två land; kusten räknas inte). Bara borgar inne i ett land. Kartan gäller vikingatiden; borgarna är
  äldre, och det sägs i texten.

## Tre prov (tvåsidiga, Holm över de tre, α = 0,05)
För varje borg och varje mått: u = andelen av borgens jämförelsepunkter som har ett *lägre* värde än borgen (lika värden
räknas till hälften). Utan samband är u i medel 0,5. Teststorheten är medelvärdet av u. p-värdet ur en
omblandning: i varje varv väljs för varje borg en av de elva punkterna (borgen och dess tio) slumpvis som "borgen";
10 000 varv.
- **F1. Vatten:** avståndet till vatten år 450. Ett medel-u under 0,5 betyder att borgarna låg närmare vattnet än bergen
  runt dem.
- **F2. Bygd:** antalet gravfält inom 2 km. Ett medel-u över 0,5 betyder att borgarna låg i tätare bygd.
- **F3. Gräns:** avståndet till närmaste gräns mellan två land. Ett medel-u under 0,5 betyder att borgarna låg närmare
  gränserna.

Ett prov **håller** när Holm-justerat p < 0,05, riktningen är densamma i båda halvorna av borgarna (inom varje län,
i ordning efter socken, varannan socken till A och B; p < 0,05 i båda, eller samma riktning när en halva har färre än 30
borgar), och riktningen är densamma med jämförelsepunkter på all mark i stället för bara berg (alla borgar med läge).

## Beskrivande
- Storlek, murar och vallar, ingångar, husgrunder, skador, undersökningsgrad, namn och sägner, ur registrets text, med
  exempel.
- Andelen borgar inom 500 m från vatten år 450 och för jämförelsepunkterna, som ett lättläst mått bredvid u.
- En karta över borgarna.

## Vad som inte skrivs
Ett samband med vatten eller bygd säger inte vad borgarna användes till. Det skrivs som att det passar bättre med den
ena eller den andra tolkningen, inte som att den är bevisad. En borg är inte daterad av att ligga vid vattnet år 450.

## Utdata
`utdata/fornborgar/analys.R` → `utdata/fornborgar/resultat.json`; borgarnas data ur registret i
`/Volumes/2TB/Antigrvity/Runes/downloads/fornborgar/`.
