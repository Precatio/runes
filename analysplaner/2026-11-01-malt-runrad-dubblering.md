# Analysplan: Maltstenens runrad och dubblering

Skriven och låst 2026-11-01, innan något av måtten nedan har räknats. Viktor 2026-11-01: "annars gå vidare med punkt
6 och 7" (runraden som nyckel; dubbleringen *titultitul* mot dubbleringar i runkorpusen och litteraturen). Uppföljning
till `analysplaner/2026-11-01-malt-upprepningar.md` (resultat 38d5482). Allt här är **beskrivande**; inget prov har en
gräns och inget avgör en tolkning. Inga läsningar av Malt läggs till.

## Vad som är känt före låsningen
- Malts sida A i Rundata: *sua ai ÷ titultitul ¶ fuþorkhniastbmlR* – den fullständiga sextonrunsraden står direkt efter
  den dubblerade gruppen.
- Antal inskrifter med en följd på minst sex runor i runradens ordning (`runlm_sprakprov.futhark_run` ≥ 6): vikingatida
  6 runstenar, 3 andra stenar, 14 lösa föremål; medeltida 1 runsten, 23 andra stenar, 116 lösa föremål.
- Direkta upprepningar ≥ 3 runor inom en grupp på vikingatida inskrifter: 32 runstenar, 1 annan sten, 3 lösa föremål
  (av dem är Sm 144 och Sö 54 fel i hur huvudläsningen togs ut, se nedan).
- Eddan i `src/runlm.edda_tokens`: 90 852 ord; sagorna i `utdata/varlden/korpus/`: 107 texter.

## Rättelse av huvudläsningen (bestämd före körningen)
Två brister i rutinen från förra planen rättas här och gäller bara denna plan: (1) efter ett fristående §Q hör resten
av translittereringen till den alternativa läsningen och tas bort (Sm 144); (2) Rundatas sidor (§A, §B …) skiljs med
ett brott, så att runor på två sidor inte möts (Sö 54). Förra planens resultat räknas inte om.

## Del A – runraden
1. Alla vikingatida inskrifter med runrad (≥ 6 runor i följd i ordningen *fuþorkhniastbmlR*), per objekttyp: radens
   längd, var på föremålet den står, och vad mer som står där (hela Rundatas normalisering och översättning).
2. Det övriga innehållet klassas för hand i en av fem grupper: (i) minnesformel, (ii) namn, ägar- eller
   tillverkarformel, (iii) besvärjelse eller religiöst, (iv) Rundata har ingen tolkning, (v) inget annat än raden.
3. Står runraden intill en direkt upprepning eller en följd som Rundata inte tolkar, som på Malt?
4. De medeltida raderna sammanfattas bara med antal per objekttyp och hur många som har annan text.
De äldre (24-runiga) raderna ingår inte; de hör till en annan tid och ett annat runsystem.

## Del B – dubbleringen
1. **Runkorpusen:** alla direkta upprepningar *XX* med |X| ≥ 3 inom en skiljeteckengrupp, vikingatid och medeltid för
   sig, per objekttyp, med den rättade huvudläsningen. Varje vikingatida upprepning klassas för hand: (a) ord eller
   sammansättning, (b) namn, (c) formel, besvärjelse eller ljudupprepning, (d) ingen tolkning i Rundata, (e) ristarfel
   eller fel i utgåvan.
2. **Eddan och sagorna:** (i) samma ord två gånger i rad (*w w*), antal per 10 000 ord i Eddan och i sagorna, med alla
   Eddafall listade; (ii) ord som i sig är en dubblering *XX* med |X| ≥ 2 (t.ex. ljudhärmande ord), alla listade
   för Eddan, antal och exempel för sagorna. Syftet är en katalog över vilka slags dubbleringar språket omkring Malt
   har.
3. Malts *titultitul* jämförs bara med katalogen: vilka slag av dubblering finns, och var står de (i dikt, i
   besvärjelser, intill runrader). Ingen av dem prövas som läsning av Malt.

## Redovisning
`utdata/Malt/runrad_dubblering.py`, `utdata/Malt/runrad_dubblering.json`, `utdata/Malt/runrad_dubblering_resultat.md`
(med handklassningen per inskrift).
