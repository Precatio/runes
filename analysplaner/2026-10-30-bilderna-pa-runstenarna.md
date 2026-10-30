# Analysplan: bilderna på runstenarna (2026-10-30)

Skriven och låst 2026-10-30 innan något räknats. Viktor bad om förslag på vad litteraturen kan ge som data och
vilka frågor datan kan få; bilderna först. Bildkatalogen är Marjolein Sterns (2013, *Runestone images and visual
communication in Viking Age Scandinavia*, Appendix 1), utvunnen till `data/cache/literature/stern2013_bilder.csv` av
`utdata/litteraturdata/stern_katalog.py` (195 poster: 1.A hela stenar 111, tillägg 4, 1.B skadade/förlorade 68,
1.C för-/eftervikingatida 12). Sterns egna resultat (bild kombinerad med kors, bild mot ormslinga, bildens framträdande;
hennes tabeller 1–3) räknas inte om utan citeras.

## 0. Före körning
Viktor granskar `utdata/litteraturdata/stern_granskning.txt` (30 slumpade poster: Sterns bildcell → våra kategorier).
Är fler än 3 av 30 felklassade rättas nyckelorden i `CLASSES` och ett nytt prov dras, innan något räknas. Det är
databeredning, inte prövning, och får ske före resultat men inte efter.

## 1. Material
- **Stenar:** svenska vikingatida runstenar i Rundata (appens standardurval, `is_runestone`, datering V). Danmark och
  Norge räknas inte (Sverige-regeln); Sterns danska och norska poster lämnas utanför.
- **Bildstenar:** Sterns 1.A, 1.A tillägg och 1.B som finns i Rundata och är svenska vikingatida runstenar (vid
  utvinningen 120). 1.C utesluts (inte vikingatid). Poster med tom bildcell (9) räknas som "har bild, klass okänd":
  de ingår i "någon bild" men inte i klassproven.
- **Utan bild:** alla övriga stenar i urvalet. Antagande, redovisat som förbehåll: Sterns katalog (2013) är fullständig
  för figurbilder; ren ormslinga och ensamt kors räknas inte som bild (det gör inte Stern heller).
- **Textvariabler:** appens mönster ur R-korpusen (`pattern_labels`): *fard* (utlandsfärd eller död utomlands), *kristen*
  (kors eller kristen bön eller formel), *hednisk*, *neutral*, *bon*, *kors*; landskap; stilgrupp; ristare och skrivmiljö.
- **Djurnamn:** personer på stenen (`entities.extract`) vars namn innehåller något av leden ulf/ulfr, bjôrn/biorn, ormr/orm,
  hrafn/ravn, ôrn/arn-, bestämt nu; inga fler led efteråt.
- **Bildklasser:** skepp, ryttare, häst, fågel, mask, fyrfotadjur, människa, kors (som bild), sigurd, hammare, orm som
  bild; "djurbild" = fyrfotadjur, fågel, häst eller orm som bild; "hednisk eller förkristen figur" = mask, fyrfotadjur,
  sigurd, hammare, orm som bild; "resebild" = skepp eller ryttare.

## 2. Prövningar (Holm över B1–B3; α 0,05)
Varje prövning görs som i appens *Pröva en egen fråga* (`src/question.py`): Fishers test rått, och logistisk modell med
landskap och stilgrupp som justering; sockenhalvor som kontroll där det går. Ett klassprov kräver minst 10 bildstenar
i klassen med variabeln tillgänglig, annars redovisas det bara beskrivande.
- **B1 Resan:** stenar med resebild (skepp eller ryttare) har *fard* oftare än stenar utan bild. Ensidigt (oftare).
  Omvänt mått, beskrivande: hur stor del av *fard*-stenarna som har någon bild alls.
- **B2 Tron:** stenar med hednisk eller förkristen figur har *kristen* mer sällan än stenar utan bild (ensidigt, mer
  sällan); stenar med kors som bild har *bon* oftare än stenar utan bild (ensidigt, oftare). B2 räknas som en prövning
  med två delar; båda måste hålla.
- **B3 Djuren:** stenar där någon person bär ett djurnamn har djurbild oftare eller mer sällan än stenar utan sådant namn
  (tvåsidigt). Vår förhandstro, nedskriven nu: inget samband – djuret i namnet och djuret på stenen var två olika saker.
- **Beskrivande, utan prövning:** bildklasser per landskap och stilgrupp; Sigurdsstenarnas ristare och skrivmiljöer;
  bildstenar i stengrupper (klusterlagret 100–1 000 m) mot ensamma; antal bilder per sten.

## 3. Tolkning, bestämd i förväg
- B1 håller: bilden förstärker det texten säger om resan. Faller: bilden och formeln var två oberoende sätt att hedra.
- B2 håller: de förkristna figurerna hör till stenar med mindre kristen text – "Oden bredvid Kristus" är ett undantag,
  inte regeln. Faller: figurerna står lika gärna på kristna stenar; bildspråket bytte inte tro när texten gjorde det.
- B3 håller (samband): djurnamn och djurbild hör ihop – namnet avbildades. Faller: namnet och bilden var skilda ting.
- Små tal: bildstenarna är omkring 120 och klasserna ofta under 20; att en skillnad inte håller är inte belägg för
  likhet. Allt redovisas med exakta antal.

## 4. Vad som INTE får göras
Inga nya bildklasser eller namnled efter att resultaten setts. Inga stenar bort. Ingen övergång till DK/NO för att få
fler stenar. Inga tolkningar av enskilda bilder lagda till Sterns ord.

## 5. Redovisning
`utdata/bilder/resultat.md` med siffrorna i `resultat.json`; mönster som håller sparas under Statistik (R) enligt
regeln för nya mönster; artikel bara om något håller eller faller på ett sätt som är värt att berätta, med Sterns
katalog som uttalad källa och hennes egna resultat refererade. Tabellen ur hennes bilaga publiceras inte.
