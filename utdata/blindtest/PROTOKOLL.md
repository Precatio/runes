# Förregistrerat blindtest av sannolikhetsmodellen (textmodel-17)

Registrerat 2026-10-17. Detta protokoll skrevs och committades **innan** teststenarna drogs och innan någon av dem
fylldes i. Dragningens slumpfrö bestäms av commit-hashen för den commit som registrerar protokollet, och kan därför
inte ha valts för att ge ett visst utfall. Allt nedan är bestämt i förväg; inget får ändras efter dragningen.

## Syfte

Modellens siffror hittills kommer från korsvalidering som vi själva har byggt och läst av under utvecklingen. Även om
ingen teststen någonsin ingått i sin egen modell, har aggregerade resultat styrt våra vägval (inställningar,
kalibreringsvariant, trösklar). Det här testet prövar den färdiga kedjan en enda gång, på stenar som aldrig granskats
individuellt under utvecklingen, enligt i förväg låsta regler: ingen omkörning, inga justeringar, alla luckor
redovisas.

## Population

Filen `population.json` (committad tillsammans med detta protokoll) fryser:

- **Urval:** vikingatida runstenar i Samnordisk runtextdatabas (textmodel-17:s stenurval, `rl.object_kind == "runsten"`)
  med minst en **dokumenterad lucka**: runor som utgivarna återställt i hakparentes i translittereringen, ommaskade med
  `scripts/runlm_documented_test.items_for`, 1–4 förlorade runor per lucka efter sammanslagning. Detta är exakt samma
  luckdefinition som det publicerade riktmärket (dok5).
- **Undantag:** 319 signa – varje sten som förekommit i våra artiklar, byggskript, skannade referenser eller
  fallstudier, hellre för många än för få. Listan står i `population.json`.
- **Resultat:** 197 valbara stenar med 338 dokumenterade luckor, spridda över alla fem falder.

## Dragning

1. Slumpfrö = heltalsvärdet av den fulla git-SHA:n för **registreringscommiten** (den commit som först innehåller detta
   protokoll och `population.json`), modulo 2^63.
2. Stenlistan sorteras efter signum och blandas med `random.Random(frö).shuffle`.
3. Stenar tas i ordning tills **minst 10 stenar och minst 20 dokumenterade luckor** är valda. Alla den valda stenens
   dokumenterade luckor ingår; inga luckor får strykas efter dragningen.

Skriptet `scripts/blindtest.py` kontrollerar före dragningen att protokollfilerna är oförändrade sedan
registreringscommiten och att populationen kan återskapas identiskt ur databasen.

## Pipeline (låst)

Appens egen kedja, oförändrad: textmodel-17, panelens inställningar (`tm.FILL`), ristarens egen skiljetecknadel
(`own_d=True`), modellen för stenens fald (`tm.fold_of` – teststenen ingår aldrig i sin egen modell), ordval och
procent genom den gemensamma kalibreringen (`gap_list`), via `scripts/luckprov.read_stone`, radbyggnad exakt som i
`scripts/runlm_documented_test`. Koden är den som står i registreringscommiten; körningen ska ske från en commit där
`src/runlm.py`, `src/textmodel.py`, `scripts/luckprov.py`, `scripts/runlm_documented_test.py`, `scripts/runlm_gaps.py`
och `scripts/blindtest.py` är oförändrade sedan registreringen.

**Känd begränsning, deklarerad i förväg:** kalibreringsparametrarna (`gap_list`) är anpassade på hela dok-materialet,
där de valbara stenarnas luckor ingår bland tusentals. Enskilda stenar påverkar parametrarna försumbart, och riktmärket
är beräknat med samma kedja, så jämförelsen är lika för båda. Stenvalet, som är det testet skyddar, har aldrig påverkat
något beslut.

## Mått och facit

Facit är utgivarnas återställning (`gold_word` ur Rundatas token). Per lucka redovisas modellens valda ord, dess
kalibrerade procent, fyllnaden runa för runa och alternativen.

- **Primärt mått:** andel luckor där modellens ord är utgivarnas ord enligt samma regel som riktmärket
  (`rl.same_word`, lemma eller närliggande form). Riktmärke: **0,687** (dok5, runstenar, 361 luckor).
- **Sekundärt mått:** strikt lemmalikhet (utan `same_word`-regelns prefixgenerositet). Riktmärke: **0,657**.
- **Kalibrering:** medelvärdet av modellens påstådda procent jämfört med andelen rätt (riktmärkets skillnad är
  0,71 mot 0,69), samt utfallet för varje lucka där modellen påstår minst 95 procent (riktmärke: 97,6 % håller).

## Framgångskriterier (låsta)

1. **Förenligt med riktmärket:** andelen rätt (primära måttet) ligger inom det exakta binomiala 95-procentiga
   prediktionsintervallet kring 0,687 för det dragna antalet luckor. Skriptet beräknar och skriver intervallet vid
   dragningen, innan någon lucka fylls.
2. **Kalibrering:** |medelpåstående − andel rätt| ≤ 0,15 (vid ~20 luckor är slumpvariationen ensam av den
   storleksordningen; riktmärkets avstånd är 0,02).
3. Luckor där modellen påstår ≥ 95 procent redovisas var för sig; varje miss där räknas som ett allvarligt fynd
   oavsett totalsiffran.

Faller utfallet utanför intervallet redovisas det precis så – testet körs inte om, och resultatfilen committas orörd
oavsett utfall. Testet är en stickprovskontroll med liten styrka (~20 luckor), inte en precisionsskattning; det är
avsett att avslöja grova fel i kedjan eller systematiskt överdrivna procentsiffror, inte att förfina riktmärket.

## Körning

    PYTHONPATH=. .venv/bin/python scripts/blindtest.py --draw <registrerings-SHA>   # visar urvalet och intervallet
    PYTHONPATH=. .venv/bin/python scripts/blindtest.py --run  <registrerings-SHA>   # fyller luckorna EN gång

Resultatet skrivs till `utdata/blindtest/resultat.json` och committas utan ändringar tillsammans med en läsbar
sammanfattning. Avvikelser från protokollet, om några tvingas fram (t.ex. en sten som kraschar), redovisas i
resultatfilen med orsak; stenen ersätts då av nästa i den blandade ordningen, och bytet loggas.
