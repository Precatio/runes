# Analysplan: släktnätverket, steg 1 – samma personer på flera runstenar, med avstånd och prövad osäkerhet

Skriven och låst 2026-11-01, innan några nya länkar har räknats. Viktor 2026-11-01: "ja" (på förslaget att börja med ett
länkat släktnätverk över runstenarna och först göra en litteratursökning).

## Forskningsläget
- Henrik Williams (1990, *Åsrunan*, Runrön 3, Bilaga s. 185–187) förtecknar för hand de inskrifter som runologisk litteratur
  (SRI, Fornvännen) har knutit samman genealogiskt: 144 grupper, 382 inskrifter, osäkra samband inom parentes. Han påpekar
  att många samband vilar på ett ovanligt namn eller geografisk närhet.
- Lena Peterson (2007, *Nordiskt runnamnslexikon*) markerar omkring 218 fall där belägg avser samma person, efter Williams 1990,
  Axelson 1993 och Lerche Nielsen 1997.
- Tristan Mueller-Vollmer (2021, avhandling, University of Wisconsin–Madison) byggde en relationsdatabas över 1 824 inskrifter
  (4 668 individer, 3 901 släktrelationer) för namnskick; den är inte öppen och används inte för nätverksanalys.
- Släktgrupper har använts för relativ datering (Crocker 1982; Williams 1990), och arvstesen (Sawyer 1988; 2000) har
  kritiserats (Herschend 2002).
- Det som saknas, såvitt litteratursökningen 2026-11-01 visar: en öppen länkning som går att köra om, med angiven osäkerhet,
  prövad mot experternas förteckning, som grund för ett nätverk över hela materialet.

## Vad som var känt före låsningen
- Appens länkmodell (`src/linking.py`, `data/links.json`, 2026-10-27; avsnitt 1r i METHODS): 420 kandidatlänkar, i
  genomsnitt 365 i nollmodellen (namnen blandade inom landskapet), 28 länkar med q < 0,1. Prövningen: Jarlabankes stenar
  klarade inte gränsen (största q 0,1065), 2 av 14 parstenar och 5 av 80 par som Rundatas anmärkningar knyter ihop hittades.
  De säkra länkarna ligger i median 0,3 km isär; 82 av de 420 kandidaterna ligger inom 10 km.
- Williams förteckning är avskriven för hand (`utdata/slakt/williams1990_bilaga.py` → `williams1990_bilaga.json`, SHA-256
  b796481e3da61b07…): 144 grupper, 382 inskrifter, 613 par varav 355 säkra enligt hans notation. I gruppen U 293+294 står U Fv1972;172
  bara i en hänvisningsrad och räknas som osäker medlem. Hälsinglands FA33;10 och FA33;25 är Hs 14 och Hs 15.
- Ingen av modellerna har jämförts med Williams förteckning.

## Material
- Rundata (`data/rundata.json`, SHA-256 2a99f3d29dcbfe28…), svenska vikingatida runstenar (`linking.runestones`, svenska landskap):
  2 320 stenar, 2 318 med koordinater, 2 199 med härad. Personer och gårdsnamn ur `src/entities.extract` (kod i
  8b4f51a); ristare länkar inte.
- Kontroller: Williams förteckning, begränsad till par där båda är runstenar i materialet; Rundatas parstenar och anmärkningar
  (`linking.parsten_pairs`, `linking.rundata_noted_pairs`); Jarlabankes stenar U 127, U 164, U 165, U 212, U 261.

## Modellerna
**M0, den nuvarande:** `src/linking.py` oförändrad men på de svenska runstenarna: kandidat när två stenar delar minst två
personnamn eller ett gårdsnamn och minst ett delat namn står på högst 60 stenar; styrkan är summan av log(N/n); nollmodellen
blandar namnen inom landskapet, 2 000 gånger (fröet 2026); q som i `linking.fdr`.

**M1, den nya:** samma kandidatregel och styrka, men
1. nollmodellen blandar namnen inom häradet (`level="district"`; stenar utan härad inom socknen, som i koden), och
2. q räknas för sig i tre avståndsband mellan stenarna: A upp till 2 km, B över 2 till 10 km, C över 10 km (par utan
   koordinater i ett eget band). För en länk i band X är q det väntade antalet nollänkar i band X minst lika starka, delat med
   antalet länkar i data i band X minst lika starka (`linking.fdr` på bandets länkar och bandets nollänkar).

För båda: en länk är **säker** när q < 0,1 och den inte motsäger sig själv i släktskap eller tid (`linking.contradictions`).
Släktgrupper är stenar som hänger ihop genom säkra länkar (`linking.groups`).

## Prövningen (avgör om M1 ersätter M0 i appen)
Räknas för M0 och M1 på samma material:
- **W1, Williams täckning:** av de runstenar som ingår i ett säkert par hos Williams, andelen som modellen knyter till minst en
  annan runsten i samma Williamsgrupp, direkt eller genom en släktgrupp.
- **W2, Williams träffsäkerhet:** av modellens säkra länkar i de landskap Williams tar upp (Ög, Sö, Sm, Vg, U, Vs, Hs),
  andelen där båda stenarna står i samma Williamsgrupp (säker eller osäker medlem). Ett golv, eftersom förteckningen inte är
  fullständig och nya länkar kan vara riktiga.
- **J:** alla tio par bland Jarlabankes fem stenar är säkra.
- **K:** andelen motsägelser bland kandidatlänkarna och bland de säkra länkarna före motsägelseregeln.

**M1 håller** om W1(M1) är minst dubbelt så stor som W1(M0) och minst 0,25, W2(M1) är minst W2(M0) − 0,10, J är uppfyllt
och högst 5 procent av M1:s länkar med q < 0,1 har en motsägelse. Annars behåller appen M0, och utfallet redovisas.

## Beskrivande, oavsett utfall
- Antalet säkra länkar per band, släktgrupper med minst tre stenar, personer på minst två stenar (samma namn på två länkade
  stenar utan motsägelse är samma person) och den längsta kedjan förälder–barn över stenarna, per landskap.
- W1 och W2 per band, Rundatas parstenar och anmärkningar som i dag.
- **Utforskande (M1b), märkt som sådant:** kandidat också när två stenar inom band A delar ett enda namn som står på högst 10
  stenar. Avgör ingenting.
- Känslighet: banden 1/5 km och 3/15 km; gränsen för vanliga namn 40 och 80; nollmodellen inom landskapet i stället för
  häradet; utan flyttade stenar (korpus `e83202e01a5e6d27`, moved = 0).

## Vad som inte får göras
Kandidatregeln, banden, gränserna och avskriften av Williams ändras inte efter körningen. Ett avskriftsfel som upptäcks senare
rättas bara med daterad notering, och båda resultaten redovisas.

## Redovisning
`utdata/slakt/steg1.py`, `steg1.json` och `steg1_resultat.md` med avsnittet *Avvikelser från planen*. Håller M1 byts
länkningen i appen (`scripts/link_entities.py`, METHODS 1r, nyhet i `web/content/news.json`); steg 2 (släktträden och
arvsfrågorna) får egna låsta planer.
