# Analysplan: de döda som går igen – fördjupning 8 i serien "Fornnordiska väsen"

Skriven och låst 2026-11-23, innan något nedan har räknats per textgrupp eller betydelse. Viktor 2026-11-23: "ja" till att
ta del 8 vid sidan om ristargrupperna. Ordningen i serien är bestämd sedan 2026-11-21, och de döda som går igen är nästa
del efter vargarna.

## Känt före låsningen
- **Antal:** för att välja metod räknades bara totalerna, i alla texter utom runstenarna. Inget är uppdelat.
  - Ord för den gående döde: *draugr* 17, *haugbúi* 3, *aptrganga/afturganga* (substantiv) 23, *ganga aftr* (verbfras)
    15, *reimt/reimleik-* 14, *uppvakningr* 0.
  - Ord för högen (*haugr* med böjningar): 311.
- **Bakgrund ur litteraturen** (allmänt, inte mätt): islänningasagornas kända gengångare är Glámr (Grettis saga),
  Þórólfr bægifótr och Fróðá-undren (Eyrbyggja saga) och Hrappr (Laxdæla saga). Fornaldarsagorna har högbor som
  gravplundraren möter i högen, som Þráinn i Hrómundar saga. *Ganga aftr* kan också betyda "gå tillbaka", och *draugr*
  kan stå i skaldiska omskrivningar för en man.

Texter och klassning med utdrag stannar utanför git.

## Träffarna och handklassningen
- **Mönster A, den gående döde** (skiftlägesokänsliga):
  - `\bdraug(?:r|ur|s|i|a|ar|ana|arnir|um|inn|inum)?\b`
  - `\bhaugbú\w*`
  - `\b(?:aptr|aftr|aftur|apt)gang\w*|\bafturgöng\w*|\baptrgöng\w*`
  - `\b(?:gekk|gengu|ganga|gengi|gangi|gengr|gengur|gengið|genginn)\s+(?:aftur|aftr|aptr|apt)\b`
  - `\breim(?:t|leik\w*|ast\w*)\b`
  - `\buppvakning\w*`
- **Mönster B, högen:** `\bhaug(?:r|ur|s|i|inn|inum|ins|a|ar|um|ana|arnir)?\b`. En träff som redan är fångad av mönster A
  på samma ställe räknas bara en gång.
- **Alla träffar klassas för hand** med Anthropics språkmodell Claude (Claude Opus), i en av klasserna:
  - *gengångare* – en död som återvänder bland de levande: går, spökar, anfaller, visar sig på gården eller vid huset;
  - *högbo* – den döde är verksam i högen: talar, slåss, sitter, vaktar skatten eller möter den som bryter sig in;
  - *grav* – högen som grav eller gravläggning, utan att den döde gör något;
  - *plats* – högen som plats eller landmärke, eller någon som sitter på en hög;
  - *annan betydelse* – ordet betyder något annat: "gå tillbaka", en omskrivning, ett namn;
  - *annat*.
- **Oberoende blind kontroll:** 40 träffar klassas av en separat instans av samma modell, utan att den ser den första
  klassningen.
  - Stickprovet stratifieras efter mönster (A eller B) × textgrupp, med frö 20261123.
  - Kravet är ≥ 85 % lika. Oenigheterna redovisas.

## Grupper
- **Islänningasagorna** = islänningasagornas prosa.
- **Fornaldarsagorna** = fornaldarsagornas prosa.
- **Övriga** redovisas men ingår inte i T1:
  - eddadikterna;
  - Snorres Edda;
  - Heimskringla;
  - samtidssagorna;
  - all vers.

## Test T1 – hemma eller i högen (låst)
- **De verksamma döda** är träffarna i klasserna *gengångare* och *högbo*.
- **Måttet:** andelen *högbo* bland de verksamma döda, i fornaldarsagorna jämfört med islänningasagorna.
- **Utfallet:** skillnad i procentenheter med 95 % intervall.
  - Bootstrap över texterna, 10 000 dragningar, frö 20261123.
  - Tvåsidigt p.
- **Testet håller** om p < 0,05 och intervallet inte täcker 0.
- **Minsta underlag:** ≥ 10 verksamma döda i vardera gruppen, fördelade på ≥ 3 texter. Annars är testet obestämt.
- **Känslighet** (utan egen slutsats): bara mönster A (utan högarna), och med varje sagas verksamma döda räknade som högst
  en gengångare och en högbo (så att en enda lång episod inte väger tyngst).

## Mått (beskrivande)
- **V1:** klasserna per textgrupp och per mönster, och täthet per 10 000 ord.
- **V2:** de sagor som har flest verksamma döda. De namngivna döda som återkommer, ur handläsningen.
- **V3:** runstenarna. Ordet för hög i Rundatas normalisering (`\bhaug\w*|\bhôg\w*`, liten bokstav) och sammanhanget
  stenarna nämner det i. Bara beskrivande.

## Vad som redovisas
- Allt ovan redovisas i `utdata/de_doda/resultat.md`, oavsett utfall.
- Ett ord i en text är inte en tro. Sagorna skrevs på 1200- och 1300-talen.
- Citaten är korta och anges med källa.
