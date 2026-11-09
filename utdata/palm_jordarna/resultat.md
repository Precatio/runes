# Palms jordar – resultat

Låst plan `analysplaner/2026-11-08-palm-jordarna.md` (sha 85a70fa3). 6190 bygderutor om 2 × 2 km (minst ett gravfält, minst 25 % land år 1050) i 36 vikingatida land, med 707 runstenar som står kvar på sin plats (av 834 sådana i det vikingatida Sverige) och 17781 gravfält. Negativ binomial regression med landen som fasta effekter, landytan som offset och klusterrobusta standardfel i block om 20 km.

## P1 (huvudprov): följer stenarna leran inom bygden?

**Håller.** I samma land och vid lika många gravfält står det fler runstenar där andelen lera och silt är större: från en ruta med 2 % lera och silt (25:e percentilen) till en med 38 % (75:e) blir det 1,45 gånger så många stenar (hela vägen från ingen lera till bara lera 2,83 gånger). Ett så tydligt samband skulle slumpen ge ungefär en gång på 4700 (ensidigt p = 0.0002).
Utan gravfälten i modellen (P0, beskrivande) är kvoten för ingen mot bara lera 3,99.

Robusthet (kvot ingen mot bara lera, ensidigt p): rutor om 1 km 2,12 (p 0,000297); rutor om 5 km 4,17 (p 8,5e-05); bara Mälarlandskapen 2,03 (p 0,0301); bara Götalands inland 5,51 (p 0,00814); utan avståndet till vattnet 2,71 (p 0,000337).

## P2: förklarar jorden skillnaden mellan Mälardalen och Götaland?

Mälarlandskapen (Upplands folkland, Södermanland, Västmanland) har utan justering 6,5 gånger så tät förekomst av runstenar i bygderutorna som Götalands inland (Västergötland och Smålands små land). Vid samma jord, gravfält och avstånd till vatten återstår 2,4 gånger (ensidigt p = 1e-06). **Håller:** jorden, bygden och vattnet förklarar ungefär 52 % av skillnaden (på log-skala), resten står kvar – som Palm skrev, jorden kan inte vara hela förklaringen.

## P3: vattenvägarna

**Håller.** Dubbelt så långt till vattnet år 1050 ger 20 % färre stenar vid samma jord, bygd och land (ensidigt p = 0.0023).

## Precisering av planen (teknisk)

Kontrasten i P2 är kvoten mellan gruppernas rutvägda medeltäthet vid samma jord, gravfält och vatten (landens effekter medelvärdesbildade på kvotskalan). Planen sa "kontrasten mellan landens fasta effekter"; på log-skala är den inte definierad, eftersom åtta land (Gotlands tredingar och flera av Smålands små land) saknar kvarstående stenar i bygderutorna och får en effekt mot minus oändligheten. Referenslandet är Södermanland.

## Svagheter

- Bara stenar som står kvar på sin plats räknas (834 av 2 317): flyttade stenar har fel läge. Om de flyttade stenarna ursprungligen stod på annan jord än de kvarstående kan det påverka resultatet; Gotland och stora delar av Småland faller nästan helt bort.
- Gravfälten är de registrerade: inventeringen är ojämn och gravfälten är från hela järnåldern, inte bara vikingatiden.
- Jordartskartan är dagens; mark som låg under vattnet år 1050 räknas inte, men kartans kvalitet varierar mellan områden (SGU).
- Lera och silt är "bästa jordarna" i mälardalsk mening; på vikingatiden odlades ofta de lättare jordarna i lerslätternas kanter. Måttet säger att stenarna står där leran finns i rutan, inte vilken jord gården brukade.
- Sambandet visar var stenarna står, inte varför; att det är den jordägande klassen som syns är Palms tolkning.

## Data

- SGU, *Jordarter 1:25 000–1:100 000* (INSPIRE-version), CC BY 4.0. SGU:s strandförskjutningsmodell (läget 900 år före nutid), CC BY 4.0.
- Riksantikvarieämbetet, Kulturmiljöregistret (gravfält). ISOF:s ortnamnsregister (socknar och landskap), CC BY.
- Samnordisk runtextdatabas (Rundata), ODbL, via Vitkis korpus (510ebfb3).
- Palm, R. 1992. *Runor och regionalitet*. Uppsala: Institutionen för nordiska språk (Runrön 7), s. 107–108, 255.

## Efter provet (beskrivande, inte i planen) – 2026-11-09

Viktors frågor efter läsningen: är det leran, vattnet eller bygden? Står stenarna på leran? Gäller det hela landet?

- **Jämförbara steg** (`bidrag.R`, samma modell, 25:e → 75:e percentilen, klusterrobusta 95 %-intervall): fler gravfält (1 → 4) 2,39 [2,03–2,82] gånger så många runstenar; mer lera och silt (2 → 38 %) 1,45 [1,18–1,78]; vid stranden mot 1 km bort 1,42 [1,11–1,80]. Lera och vatten hänger knappt ihop (r = −0,10 mot log-avståndet); lerans kvot ingen → bara lera 2,83 med vattnet i modellen, 2,71 utan; vattnets 20 respektive 19 % färre stenar per fördubbling med och utan leran.
- **Skillnaden Mälardalen–Götalands inland** (6,5 → 2,4 gånger, 52 % förklarat) fördelad med Shapley över alla ordningar: bygden (gravfälten) 33 %, leran 15 %, vattnet 5 %.
- **På leran eller vid kanten** (`platsen.py`, jordarten i 100 m-rutnätet under 707 runstenar och 17 781 gravfält, mot 50 respektive 5 slumpvisa landplatser i samma 2 km-ruta): runstenar på lera 28 % mot 37 %, inom 200 m utan att stå på den 52 % mot 40 %; gravfält 16 mot 29 % och 50 mot 36 %. Skillnaden med 20 km-block dragna på nytt (95 %): runstenar 4–13 procentenheter mer sällan på lera och 8–16 oftare vid kanten; gravfält 11–15 och 13–16. Per landsdel: gravfälten i alla tre (Mälardalen, Götalands inland, övriga); runstenarna i Mälardalen (569) och övriga landskap (69, mest Östergötland), i Götalands inland (69) åt samma håll men intervallen täcker noll.
- **Det är en gammal iakttagelse som nu är mätt:** Ekholm 1950 (Fornvännen 45, s. 140, efter von Friesen 1913): gårdarna och byarna ”äro aldrig uppförda på lermarkerna utan på de moräner, som omge dessa eller ligga som öar på slätten”; Nygren Wåhlin 2018 (kandidatuppsats, Uppsala) med GIS för Uppland.
- Kartor: `karta.R` (översikt med ram, inzoomning Täby–Vallentuna ur `zoom_jord.py` i 10 m).
