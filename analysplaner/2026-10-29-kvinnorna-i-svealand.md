# Analysplan: Varför stod kvinnorna i Svealand oftare på stenen?

Låst 2026-10-29, innan något nedan har räknats. SHA-256 i `analysplaner/2026-10-29-kvinnorna-i-svealand.sha256`.
Kod `utdata/kvinnor_landsdel/analys.R`, resultat `utdata/kvinnor_landsdel/resultat.md`.

## Utgångsläge (sett före låsningen)
Människomodulen (analysplaner/2026-10-28-manniskorna.md, test 1): en kvinna står bland resarna på 31 % av stenarna i
Svealand mot 17 % i Götaland (oddskvot 0,46 Götaland mot Svealand, landsdel, tid och ristare konstanta, båda
halvorna). Också sett: av 69 stenar efter män som dog utanför Norden är 4 resta efter en make; Svealands stenar nämner
resor oftare (budskapsmodulen); arvsstenar finns bara i Svealand (19 mot 0). Inga av testen nedan har körts.

## Material
Som människomodulen: läsbara svenska runstenar med minst en identifierad resare (`n_resare ≥ 1`), korpus
3f58e9339191761e (`corpus.csv`, `people.csv`, `messages.csv`). Huvudkontrast Götaland mot Svealand; Gotland och
Norrland ingår i modellen som egna nivåer. Modell som i r/people.R: logistisk regression (mgcv), landsdel + tidsskikt
+ ristaren som slumpeffekt. Halvorna socken för socken som i change.R.

## Hypoteser och test (Holm-korrigerade tillsammans, tvåsidiga, α = 0,05)
**A. Änkorna efter färderna.** Om kvinnorna i Svealand oftare var änkor efter män som dog borta, sitter skillnaden i
stenarna efter makar och i resestenarna.
1. y = kvinna reser efter make (kvinna bland resarna och relationen make), bland alla stenar. Oddskvot Götaland mot
   Svealand.
2. Huvudtestet (kvinna bland resarna) bland stenar som **inte** nämner resa eller död utanför Norden (`msg_resa = 0`
   och `msg_dod_borta = 0`). Oddskvot Götaland mot Svealand.

**B. Seden att räkna upp familjen.** Om stenarna i Svealand oftare nämner flera i familjen (arvingarna), och kvinnorna
kommer med som en av många, försvinner en del av skillnaden när antalet resare hålls konstant.
3. Huvudtestet med log(antal resare) som kontroll. Oddskvot Götaland mot Svealand.

**C. Kvinnans egen ställning.** Om kvinnor i Svealand hade en självständigare ställning, reser de också oftare stenar
ensamma.
4. y = en ensam kvinna reser stenen (`kvinna_ensam`: kvinnor bland resarna, inga män, alla resares kön bestämt).
   Oddskvot Götaland mot Svealand.

**D. Rollerna.** Var sitter skillnaden? Inom samma slags sten, y = kvinna bland resarna:
5. bland stenar efter **söner** (relation barn): modern;
6. bland stenar efter **fäder** (relation förälder, ingen make): dottern eller hustrun;
7. bland stenar efter **bröder** (relation syskon): systern eller modern.
Oddskvot Götaland mot Svealand i varje.

**E. Kristendomen.** Om kvinnor var drivande i kristnandet står de oftare på stenar med kristna markörer.
8. y = kristen markör (`cat_kristen`) ~ kvinna bland resarna + landsdel + tidsskikt + ristare. Oddskvot för kvinna.
9. Samma med interaktionen kvinna × landsdel (Götaland mot Svealand). Kvoten mellan oddskvoterna.

Ett test körs bara om utfallet finns på minst 15 stenar; annars ”för få”.

## Tolkningsregler
- Varje test: **håller** = Holm-p < 0,05 och p < 0,05 åt samma håll i båda halvorna; **antydan** = Holm-p < 0,05 men
  inte båda halvorna, eller okorrigerat p < 0,05; annars ingen skillnad påvisad.
- **Änkehypotesen (A) stöds** om test 1 håller med fler änkestenar i Svealand **och** skillnaden i test 2 är mindre
  än i huvudtestet (oddskvoten närmare 1). Den **stöds inte** om test 2 håller med samma storlek som huvudtestet.
- **Familjeseden (B)** stöds om oddskvoten i test 3 ligger närmare 1 än i huvudtestet (0,46) så att den inte längre
  håller, och mer än hälften av skillnaden på logoddsskalan försvinner.
- **Egen ställning (C)** stöds om test 4 håller med färre ensamma kvinnor i Götaland.
- **Rollerna (D):** skillnaden sitter där testen håller; håller den i alla tre är den inte knuten till en roll.
- **Kristendomen (E):** test 8 visar sambandet; test 9 om det skiljer sig mellan landsdelarna.

## Robusthet (redovisas)
Bara stenar med minst tio läsbara ord; bara Uppland och Södermanland mot Östergötland, Västergötland och Småland
(de största landskapen); utan ristarens slumpeffekt.

## Förbehåll
Kvinnans roll läses ur relationen till den döde; en kvinna på en sten efter en far kan vara dotter eller hustru, och på
en sten efter en bror syster eller mor. Kön och relation har fel på omkring en sten av tjugo (people_check.json).
