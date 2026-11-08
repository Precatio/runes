# Analysplan: följer runstenarna de bästa jordarna – och förklarar jorden skillnaden mellan Mälardalen och Götaland?

Skriven och låst 2026-11-08, innan något av proven nedan har räknats och innan jordartskartan har lagts över
stenarna. Viktor 2026-11-08: "1 och 3" (förslag 1: pröva Palms förklaring med jordarterna).

## Påståendet som prövas
Palm 1992 (*Runor och regionalitet*, s. 255): "Runstenarna är ett fenomen knutet till en jordägande klass och de har
sina främsta utbredningsområden i anslutning till de bästa jordarna. Detta är säkert en stor del av förklaringen till
det låga antalet monument i Norge […]. En eventuellt lägre jordbrukspotential i runstensområdena i Danmark och
Götaland än i runstensområdena i Svealand kan emellertid inte vara hela förklaringen till de stora skillnaderna i
antal och täthet, utan även andra orsaker måste sökas, och då i första hand ekonomiska." Som ekonomiska orsaker nämner
han, efter Hyenstrand 1989, råvaruhantering och sjöfart i Mälarområdet. Palm (s. 107–108) prövade tätheten mot
odlingspotential per område (efter Sporrong 1985 och Gräslund 1986–87) och fann att rangordningen i stort stod sig;
någon prövning på finare nivå än härad har vi inte hittat. Vitkis tidigare fynd: stengrupper ligger oftare vid gravfält
(Familjens plats, 82 mot 55 %), och inskrifterna vetter mot vägen (Ristningens riktning).

## Data
- **Runstenar:** Vitkis korpus (`data/cache/r/corpus/510ebfb3…/corpus.csv`), vikingatida runstenar med koordinater som
  inte är flyttade eller försvunna (`moved == 0`, `lost == 0`), som i Familjens plats. Bara det vikingatida Sverige:
  Skåne, Halland, Blekinge och Bohuslän (danska eller norska då) räknas inte, och bara län där jordartskartan är hämtad
  (01, 03–09, 14, 17–22).
- **Jordarter:** SGU, *Jordarter 1:25 000–1:100 000* (INSPIRE-version, GeoSciML 4.1, CC BY 4.0), per län. Varje
  karterad yta har SGU:s jordartsnamn. **Lera och silt** = namn som innehåller *lera* eller *silt* (glacial och
  postglacial lera och silt, lera–silt, gyttjelera, lergyttja), utom moräner (*morän* i namnet, t.ex. moränlera) och
  vittringsjord. Beskrivande grupper: sand och grus (sorterade grova sediment), morän, torv och gyttja, berg, vatten,
  övrigt. Klassningen av alla namn skrivs i `utdata/palm_jordarna/jordartsklasser.csv` innan stenarna läggs över.
- **Bygden:** registrerade gravfält i Kulturmiljöregistret (`src/places.py`, *gravfält*), som mått på var man bodde
  under järnåldern.
- **Strandlinjen:** SGU:s strandförskjutningsmodell, läget omkring år 1050 (skiktet för 900 år före nutid). Mark under
  vattnet då räknas inte.
- **Land:** varje ruta får det vikingatida land (`src/regions.py`: folkland, små land, tredingar; annars landskapet) som
  flest av dess gravfält ligger i, efter gravfältens socken.

## Enheten
Rutor om 2 × 2 km (SWEREF 99 TM) med minst ett gravfält och minst 25 % land år 1050 ("bygderutor"). Per ruta: antal
runstenar, landyta år 1050 (km²), andel lera och silt av marken, antal gravfält, avståndet från rutans mitt till
strandlinjen år 1050 (km) och landet.

## Modellen
Negativ binomial regression (R, `MASS::glm.nb`): runstenar ~ andel lera och silt + log(1 + gravfält) + log(avstånd till
vatten år 1050 + 0,5 km) + land (fasta effekter), med log(landyta) som offset. Standardfel klusterrobusta i block om
20 × 20 km (`sandwich::vcovCL`), mot rumsligt beroende.

## Prov
**P0 (beskrivande).** Samma modell utan gravfält: följer stenarna leran alls?
**P1 (huvudprov, Palms första led).** Inom samma land och vid lika många gravfält: fler runstenar där andelen lera och
silt är större. Koefficienten för lera och silt > 0, ensidigt p < 0,05. **Håller** om så.
**P2 (Palms andra led).** Skillnaden mellan Mälarlandskapen (alla land i Uppland, Södermanland och Västmanland) och
Götalands inland (Västergötland och Smålands små land): kontrasten mellan landens fasta effekter, utan och med jord,
gravfält och vatten i modellen. **Håller** om Mälarlandskapen fortfarande har högre täthet efter justeringen
(kontrasten > 0, ensidigt p < 0,05). Hur stor del av skillnaden jorden och bygden förklarar redovisas
(1 − justerad/ojusterad kontrast, på log-skala).
**P3 (vattnet, Palms ekonomiska led).** Närmare vattnet år 1050: fler runstenar, vid samma jord, bygd och land.
Koefficienten för log-avståndet < 0, ensidigt p < 0,05.

**Robusthet för P1 (beskrivande):** rutor om 1 och 5 km; bara Mälarlandskapen; bara Götaland; utan avståndet till vatten.
Jordarten är dagens karta (åkermark som odlats upp senare ändrar inte jordarten, men en del lera under 1050 års
strandlinje låg under vatten; den räknas inte), gravfälten är de registrerade (inventeringen är ojämn), och försvunna
stenar saknas (mörkertalet).

## Tolkning (bestämd nu)
Håller P1 följer runstenarna de bästa jordarna också inom bygden – mer än var folk bodde, i linje med Palms jordägande
klass. Håller P2 räcker jorden inte för att förklara Mälardalen, som Palm skrev. Håller P3 ligger stenarna dessutom nära
vattenvägarna. Håller P1 inte följer stenarna bygden men inte leran inom den, och Palms förklaring gäller i så fall
skillnader mellan bygder snarare än inom dem.

## Redovisning
`utdata/palm_jordarna/`: `jordarter.py` (SGU-kartan till ett rutnät om 100 m), `rutor.py` (rutorna), `analys.R`,
`resultat.json`, `resultat.md`.
