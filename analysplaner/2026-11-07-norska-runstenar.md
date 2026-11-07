# Analysplan: de norska runstenarna – vem reste dem, vem mindes de, och varför så få

Skriven och låst 2026-11-07, innan proven nedan har räknats. Underlag för en populärvetenskaplig artikel om Norges
vikingatida runstenar (Viktor 2026-11-07: "Jag vill ha en artikel som fokuserar på de norska runstenarna" och "Väg också in
tankar varför det är så få, mot så många i Sverige. Vilka stilar har de?").

## Känt före låsningen (räknat utan plan, med grova mönster)
- Rundata har 66 norska vikingatida runstenar (period V, föremål runsten), 2 321 svenska och 239 danska (`src/nordic.py`).
- Andelen stenar där någon *lät* resa eller göra stenen (översättningens "had … raised/made"): Norge 1 av 56 läsbara (2 %),
  Sverige 34 %, Danmark 12 %; per svenskt landskap Uppland 60 %, Västmanland 59 %, Södermanland 27 %, Östergötland 10 %,
  Småland 17 %, **Västergötland 3 av 125 (2 %)**. Skillnaden ser alltså ut att gå från väst till öst och är inte norsk
  ensam.
- En kvinna ihågkommen (bland stenar där den dödes släktskap anges): Norge 4 av 20, Sverige 6 %, Danmark 8 % (grovt mönster).
- Jord, odal eller arv: Norge 3 av 56 (N 29, N 210, N 236), Sverige omkring 1 % (grovt mönster).
- Rundata anger stilgrupp RAK (slinga utan djurhuvud) för 33 norska stenar och ingen stil för 29; Ringerikestil och
  bildstenar (Dynna, Alstad, Vang) finns inte i Rundatas kodning och tas ur litteraturen.
- Inga ristarsiffror och inga tidsjusterade jämförelser är räknade.

## Data
Rundatas vikingatida runstenar enligt `nordic.is_runestone`, uppdelade efter serie (`nordic.land_of`): Norge (N), Sverige
(alla svenska landskap), Danmark (DR). Läsbar = `nordic.features(rec)` är inte None. Tid: `nordic.year_of` (Rundatas
datering); de flesta norska stenar saknar årtal.

## Kodning (bestämd nu, ur Rundatas engelska översättning, som är gjord på samma sätt i alla serier)
- **Lät resa:** `nordic.features(rec)["had"]` (TR_HAD, "had … raised/made/carved/cut/placed/built").
- **Kvinna ihågkommen:** bland stenar där översättningen har "in memory of / for the soul of / after … his/her/their
  (ord) <släktord>": andelen där släktordet är kvinnligt (wife, mother, daughter, sister, stepmother, stepdaughter,
  foster-mother, housewife, mother-in-law, daughter-in-law). Manliga släktord: father, son, brother, husband,
  husbandman, nephew, uncle, kinsman, partner, comrade, lord, foster-son, foster-father, stepson, stepfather, son-in-law,
  father-in-law, brother-in-law, grandson, grandfather.
- **Jord och arv:** `\ballodial\b|\binherit\w*|\bheirs?\b|\bdivided\b[^.;]{0,40}\bland\b|\bproperty\b|\bestate\b|\bowned all\b`.
- **Yrkesristare (Sverige):** en ristare (Rundatas fält carvers, säkra och osäkra) med minst tio runstenar i Rundata.
  En sten räknas till yrkesristare om någon av dess ristare är det.
- Varje norsk träff listas och läses för hand innan resultatet används; fel kodning rättas inte i efterhand utan
  redovisas.

## Prov
**H1 Lät resa.** Norge har lägre andel *lät resa* än Sverige: Fishers exakta test, ensidigt.
**H2 Kvinnor.** Norge har högre andel ihågkomna kvinnor än Sverige: Fisher, ensidigt.
**H3 Jord.** Norge nämner jord och arv oftare än Sverige: Fisher, ensidigt.
H1–H3 Benjamini–Hochberg-justeras tillsammans. Ett prov **håller** om q < 0,05. Det är **robust** om riktningen
också syns mot de svenska stenar som Rundata daterar till 1050 eller tidigare (ensidigt p < 0,05), eftersom de norska
stenarna i huvudsak räknas till första hälften av 1000-talet.
Beskrivande för H1–H3: Norge mot Danmark, mot Västergötland (grannen i öster) och mot vart och ett av de svenska
landskap som har minst 30 läsbara stenar (andel med Wilsonintervall, Fisher tvåsidigt).

**H4 Verkstäderna (inom Sverige).** Stenar där någon *lät* resa stenen är oftare gjorda av en yrkesristare än stenar
utan *lät*: Mantel–Haenszel över skikt landskap × stilgrupp (Rundatas stil; stenar utan stil i ett eget skikt),
`nordic.mantel_haenszel`. **Håller** om oddskvoten > 1 och p < 0,05.
Beskrivande: antalet ristare med minst tio stenar i Sverige och i Norge, och andelen av varje lands stenar som de gjorde.

## Tolkning (bestämd nu)
- H1 och H4 håller: *lät resa* hänger ihop med beställda stenar från verkstäder, och Norge (som Västergötland) saknade den
  beställningskulturen. Det är en möjlig del av svaret på varför Norge har så få stenar, inte ett bevis; antalet stenar
  kan ha många orsaker (tro, arv, förluster), som redovisas ur litteraturen.
- H1 håller men inte H4: skillnaden är en fråga om formel och språkbruk, inte om beställning.
- H1 håller inte: ingen skillnad att tolka.
- H2 och H3 redovisas som håller, håller inte eller robust; med få norska stenar säger ett negativt utfall lite.
- Stilarna och förklaringarna till de få stenarna prövas inte här; de tas ur litteraturen med sidhänvisningar.

## Redovisning
`utdata/norge/analys.py` → `utdata/norge/resultat.json` och `resultat.md`, med listan över norska träffar per kod.
