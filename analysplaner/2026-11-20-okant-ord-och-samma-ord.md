# Analysplan: "okänt ord" utan procent, och samma ord räknat som samma i provet med dokumenterade luckor

Skriven och låst 2026-11-20, innan något nedan har räknats om. Viktor 2026-11-20: "ja" till att först rätta buggen
och mätningen som genomgången av de ifrågasatta ifyllningarna (plan db270b26) visade.

## Känt före låsningen
- **dok5** (utdata/runlm_forfining/dok5_f0–f4.json, textmodel-19, appens inställning), runstenar: 361 luckor med ord,
  rätt ord 68,7 %; i intervallet 0,8–0,95 sade modellen 0,888 och hade rätt i 0,891 av 46; vid 0,95 och över sade den
  0,992 och hade rätt i 0,976 av 166.
- **Plan db270b26** (11 fall med p ≥ 0,8 och fel ord): Sm 8 och U 373 har ordet `<unk>` med p 1,00; fyra fall är
  samma ord i annan normalisering (sun/son, þægn/þegn, æftiR/eptir), som dok5:s jämförelse `rl.same_word` inte
  likställer; G 309 har det sammansatta namnet §øpiiR.
- Maskeringsprovet (runlm_restore_test.py) räknar redan samma ord med modellens lemma (`m.lemma(w) == m.lemma(guld)`);
  dok5 använder bara `same_word`. De två proven mäter alltså "samma ord" på olika sätt.
- I appen kalibreras inte ett ord vars första val är `<unk>` (`cal_dist16`: `if w0 == "<unk>"…: return dist`), så
  modellens råa andel kan visas.

## Del 1: okänt ord
Ett svar vars ord är `<unk>` är inget påstående om ett ord. Det får ingen sannolikhet för ordet, räknas inte i
intervallen för säkerhet (0,5, 0,8, 0,95) och redovisas för sig som "okänt ord". Runan i luckan och dess sannolikhet
redovisas som förut. Gäller dok5, maskeringsprovets säkra svar och appen (panelen, överblicken över luckor, listorna).

## Del 2: samma ord
I dok5 räknas modellens ord som rätt när `same_word` säger ja **eller** när modellens lemma är detsamma (samma regel som
maskeringsprovet), med lemmat ur den del-modell som läste stenen (`textmodel.bundle(k)`, tränad utan stenen).
Ingen annan regel, inga ord läggs till för hand.

## Vad som räknas om (inga nya ifyllningar)
dok5_f0–f4 räknas om från de sparade raderna; för del 2 behövs del-modellernas lemmatabeller. Före och efter
redovisas för runstenar och andra stenar var för sig: rätt ord, intervallen 0–0,5, 0,5–0,8, 0,8–0,95, ≥ 0,95 (sagt och
rätt), antal okända ord som tidigare stod i ett intervall, och de 11 fallen i plan db270b26 omklassade.
Det här är en rättning av mätningen, inget prov som kan hålla eller inte hålla. Båda siffrorna redovisas; de nya
ersätter de gamla i METHODS 8.1 och i appens texter, med en not om vad som ändrats och varför.

## Del 3: G 309 (beskrivs, rättas inte här)
Hur §øpiiR uppstår (vilka namnled och vilken ändelse) beskrivs. En rättning av namnmodellen ändrar ifyllningar och kräver
en egen låst plan med nytt maskeringsprov.

## Kostnad och ordning
Del 1 är kod och omräkning (lätt). Del 2 bygger fem del-modeller efter varandra och körs först när textmodel-23 (plan
321c3a6d) är klar, ett tungt jobb i taget.

## Utdata
`utdata/runlm_forfining/matt_2026_11_20/omrakna.py` → `resultat.json` och `resultat.md`.
