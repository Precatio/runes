# Analysplan: Attribueringsmodellen version 4 – ornamentik och runformer ur Sveriges runinskrifter

Låst 2026-11-04, innan texterna kopplats till några ristare. SHA-256 i
`analysplaner/2026-11-04-attribuering-v4-ornamentik.sha256`. Kod: `src/sri_text.py` (texterna, dragen),
`r/attribution_v4.R` (prövningen). Resultat i `utdata/attribuering_v4/`.

## Bakgrund
Viktor 2026-11-04: lyft in forskarnas egna belägg – ornamentiken utöver korset och runformerna. Strukturerade data
saknas (Rundata och Runor 2020 har bara stilgrupp och kors, Kulturmiljöregistret mått och skick). Runformer ur
skanningarna går inte: 95 skannade stenar, högst 4 per ristare i modellen (Traen 4, Åsmund 3). Däremot beskriver
*Sveriges runinskrifter* (SRI, RAÄ:s digitala utgåva, textvolymerna med OCR, nedladdade 2026-11-04 till
/Volumes/2TB/Antigrvity/Runes/downloads/sri) ornamentik och runformer sten för sten. Sett före låsningen: att
texterna finns, att OCR:en har spärrad text (”h a r”) och att SRI ibland för attribueringsresonemang i samma artikel.

## Texterna
Varje volym delas i artiklar vid rader som börjar med ett signum i korpusens form (t.ex. ”U 729.”, ”Sö 214.”), och
artikeln är texten fram till nästa sådan rad. Spärrad text slås ihop (enstaka bokstäver med mellanslag), avstavning
vid radslut tas bort, allt i gemener. Bara signum som finns i korpusen används; ett signum med flera artiklar får dem
sammanslagna.

## Dragen – en fast ordlista, bestämd nu
Ett drag = termen finns i stenens artikel (1/0; stenar utan artikel = okänt). Bara termer som finns i minst 15
artiklar för korpusens stenar används. **Inga namn, inga ord om ristare eller attribuering.**

Ornamentik: fågelperspektiv · i profil · rundjur · fyrfota · drake/drakhuvud · ormhuvud · ormslinga · två ormar ·
tre ormar · svans · flik (flikar, flikändar) · upprullad · spiral · ögla · koppel/sammanbindande band ·
tvärband/bindband · ringkors · korsband · rak runslinga · ramlinje · dubbelkontur · skuggning/streckfyllning ·
fyllnadsornament · mask · fötter/ben · nos · läppflik · nackflik · öga · ryttare · skepp · fågel · bildfält ·
Urnes · Ringerike · bandornamentik.

Runformer och skrift: kortkvist · långkvist · stavlösa · stungen/stungna · bindruna/bindrunor · spegelvänd ·
vändruna · ensidig bistav · dubbelsidig bistav · skiljetecken · kryss (skiljetecken) · punkt (skiljetecken) ·
lönnrunor · runhöjd över 10 cm (runornas höjd i artikeln > 10 cm, om angiven).

## Prövningen
Samma provbänk som version 1–3 (117 signerade stenar, korsvalidering grupperad per socken 5 × 3, seed 2026), med
appens nuvarande modell som jämförelse (K0: A + korsform, kalibrerad). Två steg:
1. **K0 + SRI-dragen.** Behålls om, på sockenhalva 2, andel rätt förstaval och medel per ristare båda är högre och den
   kalibrerade log-förlusten inte är sämre (kalibrering vald på halva 1) – samma regel som version 3. Påvisad
   förbättring om bootstrap-intervallet (socknar) för förstavalet på halva 2 inte rör 0.
2. **Delmodellen Stil** (stil, kors, kortkvist, korsform) med och utan SRI-dragen – beskrivande: hur mycket säger
   ornamentiken ensam?
Sekundärt: de attribuerade stenarna (hela datan). Risk som redovisas: SRI:s beskrivningar av attribuerade stenar
skrevs av samma forskare som attribuerade dem; facit är därför bara de signerade stenarna.

## Sedan
Behålls steget: dragen förs in i appens modell (korpusjobbet, r/attribution.R) och ristarsidan. Annars redovisas det
som negativt, och dragen kan ändå visas per sten som beskrivning.
