# Analysplan: vilka runstenar forskningen har skrivit om (Hundra år av runfrågor III)

Skriven och låst 2026-11-20, innan något nedan har räknats per landskap, period eller sten. Viktor 2026-11-20: "ja" till
en tredje del i serien som går igenom allt vi har hemma, årtionde för årtionde, och vad forskningen saknar – mätt mot
stenarna själva. Beskrivande studie; bara M4 är ett test, och det är låst här.

## Känt före låsningen
- Del II visar redan vilka **frågor** (28, vår sortering) som berörs per årtionde. Del III räknar i stället vilka
  **stenar** som nämns. Ingenting ur litteraturgenomgångens interna filer (frågelista, påståenden, relevans, SYNTES)
  används eller publiceras.
- Underlaget: 2 321 svenska vikingatida runstenar (`src/research_gaps.is_runestone`, Rundata 3.1). Omnämnanden enligt
  `utdata/hundra_ar_iii/omnamnanden.py`: 1 884 text–sten-par i tidskrifterna och 4 434 verk–sten-par i de indexerade
  avhandlingarna (räknat 2026-11-20 som kontroll av skriptet, inget uppdelat).
- Ett första stickprov (60 omnämnanden) gav 58 riktiga; de två felen var ett inventarienummer (St. H. M. 8,756) och en
  yxtabell (Sm 1, Ha 1). Regeln mot "[,.]siffra" lades till efter stickprovet.
- Signum fanns inte innan landskapets band av Sveriges runinskrifter kom ut (Öl 1900, Ög 1911, Sö 1924, Sm 1935,
  Vg 1940, U 1940–58, G 1962–, Vs 1964, Nä 1975, Gs 1981; Hs, M, J, Bo, D, Vr senare eller via Rundata). Före dess
  nämndes stenarna med ortnamn, och det fångas inte. Därför jämförs årtionden före 1950 inte med senare.

## Definitioner (bestämda nu)
- **Omnämnande** = en text (artikel eller avhandling) som nämner stenens signum minst en gång enligt regeln i
  omnamnanden.py: litteraturregistrets signummönster, stenen finns som svensk runsten i Rundata, "run" inom 300 tecken,
  inte följt av [,.]siffra, inte spärrad OCR-text. Registerdelar och hela Futhark-volymer räknas inte.
- **Tidskrifterna** = Fornvännen 1906–2022, Futhark 2010–2025, Namn och bygd 2010–2025, Current Swedish Archaeology
  2020– (det som finns i sökindexet). **Avhandlingarna** = verken med kind "avhandling" i litteraturregistrets index
  (inte SRI-utgåvorna, som per definition tar upp varje sten i sitt landskap).
- **Landskap** = signumprefixet. Landskap med färre än 20 runstenar slås ihop till "övriga" i M4.
- **Stilgrupp** = Rundatas stil, grovt: Pr1–Pr2, Pr3, Pr4, Pr5, RAK, Fp, KB, och "ingen säker" (?, tom, osäker).
  Mellanformer (Pr3 - Pr4) går till den första.
- **Förlorad** = Rundatas flagga lost. **Ristare** = minst en signerad eller attribuerad ristare i Rundata.
  **Textlängd** = antal runor i translittereringen (bokstäver utan skiljetecken).
- **Årtionde** = textens tryckår // 10.

## Kvalitetsgrind (före allt annat)
Ett nytt stickprov om 100 omnämnanden (seed 20261121) bedöms för hand: är det verkligen runstenen? Kräver ≥ 90 riktiga.
Annars skärps regeln (krav på "runsten|runinskrift|rune" i stället för "run") och stickprovet görs om en gång; klarar
den inte heller det stoppas studien. Utfallet redovisas.

## Måtten
- **M1 per årtionde** (1950-talet och framåt; 1906–1949 som en grupp): antal texter som nämner minst en runsten, antal
  olika stenar, och varje landskaps andel av omnämnandena mot dess andel av runstenarna (kvoten andel/andel).
- **M2 koncentration**: andel runstenar som aldrig nämns i tidskrifterna; hur stor andel av alla omnämnanden som går till
  de 5 % mest nämnda stenarna; de tio mest nämnda.
- **M3 aldrig nämnda** (tidskrifterna, och tidskrifterna + avhandlingarna) per landskap, stilgrupp, förlorad/kvar,
  ristare/ingen ristare och textlängdens kvartiler.
- **M4 justerat (test)**: logistisk regression i R (lme4::glmer), nämnd i tidskrifterna minst en gång ~ landskap +
  stilgrupp + förlorad + ristare + log(textlängd + 1) + (1 | socken). Socknen som slumpeffekt, eftersom stenar i samma
  socken ofta nämns i samma text (grupper som enhet). Rapporteras: oddskvoter med 95 % intervall. Uppland är referens.
  Ett landskap sägs vara **mindre uppmärksammat än Uppland** bara om hela intervallet ligger under 1.
- **M5 de gamla gränserna**: härader (Rundatas district) med minst 10 runstenar där minst 80 % aldrig nämns i
  tidskrifterna; listas med antal. Socknar räknas inte som oberoende i någon slutsats.
- **M6 avhandlingarna**: per årtionde verken i litteraturregistrets katalog (år, ämne), och för de indexerade hur många
  runstenar per landskap de nämner.

## Vad som redovisas
Allt ovan, oavsett utfall, i artikeln och i utdata/hundra_ar_iii/resultat.md. Inga slutsatser om varför ett landskap är
mindre uppmärksammat än vad tabellerna bär; omnämnanden mäter uppmärksamhet i de texter vi har, inte forskningens
kvalitet eller vad som står i böcker vi inte har läst. Om M4 inte bär en skillnad som M3 visar, står det i artikeln.
