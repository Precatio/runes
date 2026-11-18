# Analysplan: fornborgarnas strandkurva – vid vilken tids vatten låg borgarna?

Skriven och låst 2026-11-18, innan något av proven nedan har räknats. Fortsättning på planen "Fornborgarna – vatten, bygd
och gränser" (e0bd5ea5). Viktor 2026-11-18: "kan du jobba vidare med fornborgarna?"

## Känt före låsningen
- **F1 i förra planen höll:** borgarna låg närmare vattnet år 450 än bergen runt dem (medel-u 0,376; 64 mot 48 % inom
  500 m). Vattnet år 450 valdes då efter litteraturens datering (Götalands och Ölands borgar omkring 400–500 e.Kr.; Arne
  1924 efter Schnittger) – inte prövat mot andra tider.
- Åsa Wall (via Bornfalk Back, Fornvännen 2016) daterar Södermanlands "hägnade berg" till romersk järnålder, alltså
  något tidigare. Vikingatida bruk av borgar förekommer i litteraturen men är inte huvudtolkningen.
- SGU:s strandförskjutningsmodell finns i 19 lager: `issjohav_<BP>` för BP 1900–1200, 1000, 900–100 och 1, det vill säga
  år 50, 150, …, 750, 950, 1050, 1150, …, 1850 och i dag. Kod 1 (hav) och 4 (sjö) räknas som vatten, som tidigare.
- Inget av lagren utom BP 1500 har mätts mot borgarna.

## Data
- Samma punkter som i förra körningen (`utdata/fornborgar/punkter.csv`): varje borg med sina tio jämförelsepunkter på
  berg i dagen 0,2–5 km bort (`berg`) och tio på all mark (`mark`). Inga nya punkter dras.
- För varje punkt och varje lager: avståndet till närmaste vatten (tak 15 km, som förut). En punkt som ligger i vatten vid
  en tid har avståndet 0 och kallas **under vatten** då.

## Mått
För borg b och tid t: u(b, t) = andelen av borgens jämförelsepunkter på berg, bland dem som inte är under vatten vid t, som
ligger *närmare* vattnet än borgen (lika räknas till hälften) – samma u som förut, så u under 0,5 betyder att borgen låg
närmare vattnet än bergen runt den. u räknas bara när borgen själv inte är under vatten vid t och minst 5 jämförelsepunkter
är det inte. En borg som ligger under vatten vid t kan inte ha byggts före t (om modellen stämmer); andelen redovisas per tid.

**Strandkänsliga borgar** (huvudurvalet): borgar där minst 3 av de 10 jämförelsepunkterna på berg ändrar avstånd till
vatten med minst 100 m mellan år 50 och i dag. Urvalet bestäms bara av jämförelsepunkterna, inte av borgen själv. På
övriga borgar ändras vattnet för lite för att kurvan ska säga något; de redovisas för sig.

## Väntad mekanisk riktning
Borgarna ligger på höjder; jämförelsebergen ligger i medel lägre. Ju högre vattnet stod (ju tidigare), desto närmare
vattnet kommer de låga jämförelsebergen, och borgen ser då relativt *längre bort* ut. Utan något samband med en viss tid
väntas alltså u stiga bakåt i tiden och sjunka framåt. Ett u som är lägre år 450 än år 1050 och i dag går **mot** den
riktningen och kan inte förklaras av den.

## Två prov (bland de strandkänsliga borgarna som inte är under vatten år 450; tvåsidiga, Holm, α = 0,05)
Parvis per borg; p-värde ur teckenbyte (varje borgs skillnad byter tecken slumpvis), 10 000 varv, frö ur planens
kontrollsumma.
- **K1. Järnålder mot i dag:** d = u(b, 450) − u(b, i dag). Väntat: medel-d < 0.
- **K2. Järnålder mot vikingatid:** d = u(b, 450) − u(b, 1050). Väntat: medel-d < 0.

Ett prov **håller** när Holm-justerat p < 0,05 och medel-d har samma tecken i båda halvorna av borgarna (inom varje län,
socknarna i namnordning, varannan till A och B), med p < 0,05 i båda eller samma tecken när en halva har färre än 30 borgar.

## Beskrivande (inga prov)
- **Kurvan:** medel-u per tid för de strandkänsliga borgarna (och för alla borgar), med n per tid.
- **Kurvans botten:** den tid där medel-u är lägst, och ett 95-procentsintervall för den ur 2 000 omdragningar av
  borgarna. Det är en datering av gruppen i stort, inte av någon enskild borg. Litteraturens väntan: 250–650.
- **Under vatten:** antalet borgar vars mittpunkt ligger under vatten vid varje tid, med exempel. Det skrivs som "om
  modellen stämmer"; mittpunkten är polygonens tyngdpunkt, och modellens osäkerhet (tiotals meter i höjd lokalt) redovisas.
- Kurvan per landskap där minst 30 strandkänsliga borgar finns.
- Samma kurva med jämförelsepunkterna på all mark (`mark`) som kontroll.

## Vad som inte skrivs
Kurvans botten daterar inte en enskild borg och inte heller när borgarna byggdes – bara vid vilken tids strand de som
grupp låg bäst. Att en borg låg under vatten vid en tid sägs bara med modellens förbehåll.

## Utdata
`utdata/fornborgar/strandkurva.R` → `utdata/fornborgar/resultat_strandkurva.json` och `strandavstand.csv`.
