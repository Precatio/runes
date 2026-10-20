# Analysplan: multipel imputation av runstenarnas datering (mice)

Skriven och låst 2026-10-20 innan några resultat tagits fram (METHODS.md 1x, ANALYSPLAN.md). Hash i
`analysis_plan_mi.sha256`.

## 1. Fråga
Kan de runstenar som saknar säker stilgrupp – och därför faller bort ur varje tidsfråga – tas med genom multipel
imputation av deras tidsskikt (mice), utan att resultaten snedvrids och med konfidensintervall som håller vad de lovar?
Och gör sannolikhetsmodellens språkdatering imputationen bättre?
Ja = i maskeringsprovet (punkt 4) täcker de sammanvägda 95 %-intervallen det rätta värdet i minst 90 procent av
fallen, och den imputerade skattningen ligger närmare det rätta värdet än en analys som bara använder de daterade
stenarna, när bortfallet liknar det verkliga. Nej = något av det brister; då redovisas det som negativt och appen
fortsätter att bara räkna på daterade stenar.

## 2. Underlag
* Korpusraderna som R-analyserna och Pröva en egen fråga använder (`src/r_bridge.corpus_rows`, korpusversion
  47cc8cfb5fef8a05): 2 321 svenska vikingatida runstenar. Inga stenar utesluts.
* Variabeln som imputeras: tidsskiktet E, som i `src/question.py` – stilgruppens mittår (Gräslund) i fyra ordnade
  skikt: före 1020, 1020–1050, 1050–1075, 1075 och senare. Daterade = stenar med säker stilgrupp (väntat ≈ 1 008).
* Sannolikhetsmodellens språkdatering (hjälpvariabel, bara i arm B): log-sannolikheten för texten under var och en av
  modellens fyra epoker, som två skillnader (1070–1150 mot 1000–1070, 900-talet mot 1000–1070). För stenar i
  dateringsprovet (`utdata/runlm_forfining/datering_tm14.json`) används provets värden, som är räknade med modellen
  för den del stenen inte ingick i (femfaldigt). För övriga stenar med minst 10 läsbara runor räknas värdet med en
  modell tränad på alla daterade texter (`utdata/mi/aux_dating.py`, samma inställningar som datering_tm14); deras egen
  text har ingen datering som kan läcka. Stenar med färre än 10 läsbara runor får kategorin "okänd".

## 3. Imputationsmodellen (bestämd nu)
* mice, metoden `polr` (ordnad logistisk regression) för E; m = 20 imputeringar; frö 2026. E är den enda variabel som
  imputeras, så en iteration räcker (maxit = 1). Alla prediktorer är fullständiga:
  - landskap (landskap med färre än 15 stenar slås ihop till "övrigt");
  - de 22 dragen i `src/question.py`, vart och ett som ja / nej / okänd;
  - bergartsfamilj (src/geology, med "okänd");
  - log(1 + antal ord);
  - socknens övriga stenar: tidsskiktet för medeltalet av de *andra* daterade stenarna i samma socken (stenen själv
    räknas inte; i maskeringsprovet räknas bara stenar vars datering inte är maskerad), med "ingen" när det saknas;
  - arm B dessutom: de två språkskillnaderna i kvintiler (gränserna från de daterade stenarna) och "okänd".
* Skattning med imputerade data: varje analys görs i var och en av de 20 imputerade datamängderna och vägs samman med
  Rubins regler (log-oddskvoter och deras varians; för andelar logit-andelen), med Barnard–Rubins frihetsgrader.

## 4. Maskeringsprovet (primärt)
20 upprepningar (frön 1–20). I varje maskeras 30 procent av de daterade stenarna och imputeras med arm A (utan
språkdatering) och arm B (med). Två sorters maskering:
* **MAR (primär):** sannolikheten att en daterad sten maskeras följer sannolikheten att en sten saknar säker
  stilgrupp, skattad med logistisk regression på hela korpusen med samma prediktorer som imputationsmodellen (utom
  socknens stenar och språkdateringen), skalad så att i genomsnitt 30 procent maskeras. Det efterliknar det verkliga
  bortfallet.
* **MCAR (kontroll):** 30 procent slumpvis, skiktat per landskap.
Det rätta värdet är skattningen med alla daterade stenar kända. Skattningarna (estimander), bestämda nu:
* för vart och ett av de 22 dragen: oddskvoten för draget från 1050 mot före 1050, Mantel–Haenszel över landskap
  (som Pröva en egen fråga, tidsgränsen 1050); drag där provet inte går att räkna i den fullständiga datan räknas inte.
Mått: (a) täckning – andelen sammanvägda 95 %-intervall för log-oddskvoten som innehåller det rätta värdet, över
drag × upprepningar; (b) avvikelse – medelvärdet av |skattning − rätt värde| för log-oddskvoten, jämfört med samma
mått för analysen med bara de omaskerade daterade stenarna (complete case); (c) träffsäkerhet – andelen maskerade
stenar där det vanligaste imputerade skiktet är det rätta.

**Gränser.** MI används i appen om, under MAR-maskering: täckningen är minst 0,90 över alla drag × upprepningar, och
medelavvikelsen är mindre än complete case-analysens. Arm B väljs framför arm A bara om båda gränserna håller för B och
B:s träffsäkerhet (c) är minst 2 procentenheter högre än A:s; annars arm A. Språkdragen (stungna, monoftong, o-runan,
r för ʀ, auk, at, h skrivet, nasal, bindrunor) prövas också för sig: håller B:s täckning inte 0,90 för dem används
arm A för frågor om språkdrag även om B väljs i övrigt.

## 5. Känslighet
Redovisas men ändrar inte beslutet: MCAR-maskeringens täckning och avvikelse; m = 50 i stället för 20 i en
upprepning; resultatet per tidsskikt (andelen med draget per skikt) i stället för oddskvoten.

## 6. Vad som INTE får göras
Inga ändringar av prediktorer, m, metod, maskeringsandel eller gränser efter att resultat setts. Inga drag tas bort
ur provet för att de ger dålig täckning. Imputerade dateringar visas aldrig som en stens datering – bara i
sammanvägda skattningar. Ingen egen datering av enskilda stenar.

## 7. Redovisning
Utfallet, också ett nej, skrivs i `utdata/mi/resultat.md`, METHODS.md (nytt avsnitt) och bristlistan. Om ja: R-modulen
`imputation` lägger de 20 imputerade skikten per korpusversion, och Pröva en egen fråga visar för tidsfrågor svaret
både med de daterade stenarna (som avgör domen) och med alla stenar via MI (som känslighet). Inget annat i appen
ändras utan en ny plan.
