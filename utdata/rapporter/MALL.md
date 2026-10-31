# Forskningsrapport – mallen, version 4 (2026-10-31)

**LÅST 2026-10-31.** Version 4 ersätter version 3 (`MALL_v3.md`, låst samma dag, SHA-256 d857ec3f…). Skäl: Viktor
2026-10-31 frågade ”behöver vi förklara de statistiska termerna i våra forskningsanalyser?” och sade sedan ”gör alla
saker du föreslår”. Ändringen: varje rapport säger sitt huvudresultat **i klartext**, och de statistiska termerna
förklaras i en gemensam **ordlista** (se Skriv för en läsare som aldrig sett Vitki). De rapporter som saknade en
klartextmening fick den samma dag; inget annat i dem ändrades. Versionshistoriken nedan gäller i övrigt.

Version 3 (låst 2026-10-31) ersatte version 2 (`MALL_v2.md`, låst samma dag, SHA-256 7ae79aa3…, se
`MALL_v2.md.sha256`), som ersatte version 1 (`MALL_v1.md`). Skäl, Viktor 2026-10-31: ”alla våra rapporter får dagens
datum trots att vi jobbat med den underliggande datan för rapporterna under lång tid” och ”lägg in alla datumen”.
Ändringen gäller bara rubrikraden och hur datumen visas: varje rapport får en **tidslinje** för studien, och
rapportversionens datum är **fast** i byggaren i stället för dagens datum när byggaren körs. Version 2 lade till
nivåerna (Fullt prövat och Delvis prövat), metodrapporter och datanotiser (Viktor: ”ok då kör vi på dessa två”). De sex
rapporter som fanns 2026-10-31 fick tidslinje och formmening samma dag; inget annat i dem ändrades. Förebilden är
fortfarande rapporten om kvinnorna bland resarna (`utdata/blogg/build/build_rapport_kvinnor.py`). Formen ändras bara
genom en ny version av mallen med datum och skäl; kontrollsumman står i `MALL.md.sha256`.

En rapport per fynd, alltså ett påstående; delmått av samma påstående (stungen i och stungen u) får ingå. Etiketten är
**Rapport** (en typ per artikel) + ämnen; formen och nivån står i rubrikraden, inte som etikett. Byggare i
`utdata/blogg/build/build_rapport_*.py` med alla siffror asserterade mot filerna i `data/cache/r/corpus/<fingerprint>/`
(robustness.json, modulens json), studiens egna filer i `utdata/` och planen i `analysplaner/`. Två språk ur samma
byggare: den **engelska versionen är den kanoniska för citering** (DOI, ”citera som”, det internationella fältet och
Google Scholar läser engelska), den svenska är läsversionen för sajten och materialets egna termer. Alla former är
märkta ScholarlyArticle i den strukturerade datan. Inga tabeller (BlogBody), listor i stället.

## Golvet: vad som krävs för att ett fynd alls blir en rapport

Samma golv för båda nivåerna:
- **Replikerat inom materialet.** p < 0,05 och samma riktning i båda halvorna av korpusen (delade socken för socken),
  eller upptäckt i den ena halvan och bekräftat i den andra enligt en kandidatlista som frystes innan den andra halvan
  lästes.
- **Justerat för många test.** q_global < 0,05 för mönster i Statistik; Holm eller Benjamini–Hochberg < 0,05 inom den
  låsta planen för fristående studier. Fynd från tiden före de låsta planerna (artiklarna före 2026-10-28) räknas om
  med justeringen innan rapporten skrivs, och rapporten säger att de inte var förregistrerade.

Mönster under golvet (signifikant i bara en halva, eller inte justerat) blir inte rapporter. De kan stå i artiklar som
antydningar, eller prövas på nytt under en låst plan.

## Nivå 1 – Fullt prövat fynd (Fully tested finding)

Golvet och **hela robusthetstrappan** (METHODS.md 1v), eller en låst tilläggsplan för trappan, med alla steg som håller.
Detta är version 1:s regel. Titeln är påståendet med siffrorna i, inte ämnet.

## Nivå 2 – Delvis prövat fynd (Partially tested finding)

Golvet, men trappan är inte körd, körd i delar, eller ett steg faller.
- Varje steg som saknas eller faller räknas upp i sammanfattningens första mening och steg för steg i 5.3, med
  ”inte prövat” eller ”faller” och siffran.
- Vänder riktningen i ett steg (till exempel utan ett landskap), avgränsas påståendet i titeln till där det håller, och
  2 Förregistrering säger att avgränsningen gjordes efter att data setts.
- Titeln är påståendet med siffrorna, avgränsat; den går aldrig längre än det som håller.

## Upp och ner mellan nivåerna

En rapport på nivå 2 flyttas upp när en låst tilläggsplan för trappan håller, eller när fyndet replikeras på osedda
data under en låst plan. Det blir en ny rapportversion med ändringslogg, och adressen behålls. Faller den nya prövningen
står det i nästa version; rapporten tas inte bort. En rättelse som fäller ett steg i en rapport på nivå 1 flyttar ner
den på samma sätt.

## Formerna

**Fynd (nivå 1 eller 2).** Rubrikerna nedan (version 1, oförändrade). Längd 1 500–3 000 ord.

**Metodrapport (Methods report), nivå 1 eller 2.** Påståendet är att en metod fungerar (ristarförslag, ifyllning av
luckor), inte ett mönster i materialet. I stället för halvorna och trappan prövas metoden i ett **blindprov låst före
körningen**, på stenar där svaret döljs för hela metodkedjan (dold ristare, maskade runor), mot förutbestämda gränser och
mot en enkel jämförelseregel.
- Nivå 1: blindprovet var låst, svaret var dolt för hela kedjan och de förutbestämda gränserna håller.
- Nivå 2: något av det saknas, eller provet gäller en äldre version av metoden än den som ligger i appen.
- Rubriker som för fynd, med 2 Förregistrering = blindprovets plan; 5.1 blindprovet mot gränserna och
  jämförelseregeln; 5.2 per landskap och per ristare eller typ av lucka; 5.3 kalibreringen (stämmer sannolikheterna);
  6 Diskussion: också var metoden inte ska användas. Kodfel som rättats efter en körning står i 4.4 med vad som ändrades.
- Titeln är vad metoden klarar, med siffran. Längd 1 500–3 000 ord.

**Datanotis (Data note), ingen nivå.** Beskriver en källa eller en avvikelse mellan källor (till exempel Rundata mot
Runor 2020) och vad den gör med analyser. Den prövar ingen hypotes och får därför ingen nivå.
- Varje antal asserteras mot källan i byggaren; ett slumpvis urval kontrolleras för hand, med felandel; minst ett
  exempel visar hur ett känt resultat ändras.
- Rubriker: Huvud, Sammanfattning, 1 Källorna, 2 Jämförelsen, 3 Avvikelserna (typer, exempel, handkontroll), 4 Vad det
  gör med analyser, 5 Råd till den som använder källan, Data och kod, Referenser, korthetsrutan. Längd 800–2 000 ord.
- Titeln är avvikelsen med antal.

## Datumen

- **Rapportversionens datum** står i rubrikraden (”Rapportversion 1, 2026-10-31.”) och skrivs som en konstant i
  byggaren, aldrig som dagens datum när byggaren körs. En ny version får ett nytt datum och en ändringslogg.
- **Tidslinjen** står direkt efter versionsmeningen: ”Tidslinje: händelse ÅÅÅÅ-MM-DD; händelse ÅÅÅÅ-MM-DD.” På engelska
  ”Timeline: event YYYY-MM-DD; event YYYY-MM-DD.” Händelserna står i tidsordning som korta fraser i preteritum, med
  ISO-datum sist: när arbetet med fyndet började (mönstret upptäcktes, analysplanen låstes, modellen byggdes), planer och
  tillägg som låstes, när materialet frystes, replikeringar och omkörningar. Publiceringen hör inte dit; den visas för
  sig. Varje datum ska gå att belägga i versionshanteringen eller i planens kontrollsumma.
- **På sajten** visas tidslinjen under versionsraden på rapportsidan, listan visar när arbetet inleddes (tidslinjens
  första händelse), och den strukturerade datan får samma datum som dateCreated bredvid datePublished.

## Märkningen

- **Rubrikraden** (punkt 0 nedan): direkt efter författarmeningen står formen med punkt, sedan versionsmeningen och tidslinjen (se Datumen): ”Fullt prövat fynd.”,
  ”Delvis prövat fynd.”, ”Metodrapport, fullt prövad.”, ”Metodrapport, delvis prövad.” eller ”Datanotis.” På engelska
  ”Fully tested finding.”, ”Partially tested finding.”, ”Methods report, fully tested.”, ”Methods report, partially
  tested.”, ”Data note.” Saknas formen räknas rapporten som Fullt prövat fynd (så byggdes version 1).
- **Sammanfattningen** börjar, för allt utom nivå 1, med en mening om vad som inte är prövat eller faller.
- **På sajten** syns formen som märke på rapportsidan och i listan. Listan visar fynd på nivå 1 före nivå 2, sedan
  metodrapporter och datanotiser. Den strukturerade datan får formens engelska namn som genre. Märkningen byggs i
  `web/src/lib/report.ts`, `ReportPaper.tsx` och `ReportList.tsx` tillsammans med den första rapporten som inte är nivå 1.

## Skriv för en läsare som aldrig sett Vitki

Rapporten ska gå att läsa av en runolog eller statistiker som inte känner appen. I löptexten (allt före Data och kod):
inga interna namn – inte modulnamn (människomodulen, budskapsmodulen), inte robusthetstrappan, q_global, korpusjobb,
fingeravtryck, facit, flikar i appen eller filvägar. Beskriv i stället vad saken är: ”en förregistrerad studie av vilka
som reste stenarna”, ”en fast serie känslighetsanalyser”, ”justerat för alla N samband projektet redovisar
(Benjamini–Hochberg), q”, ”handkodat kontrollurval”, ”Rundata, fryst för analysen den …”. Definiera varje begrepp
första gången (slumpeffekt, halvorna, marginaleffekt) och räkna upp landskapen bakom en landsdel. Filvägar, versionsnyckel
och appens flikar står bara under Data och kod. Byggaren ska kontrollera detta (sök efter jargong före Data och kod).

**Klartext och ordlista (från version 4).** Huvudresultatet sägs en gång i resultatdelen i klartext, utan statistiska
termer, i en mening eller ett stycke som börjar ”I klartext” (på engelska ”In plain words”): vad andelarna betyder som
”sju av tio”, vad effektmåttet betyder (”oddsen ungefär halveras på femtio år”). Slutsatsen i sammanfattningen skrivs
på samma sätt. Siffrorna i klartextmeningen asserteras i byggaren som alla andra. De statistiska termerna förklaras i
ordlistan (`web/src/lib/reportTerms.ts`, sidan /forskningsrapporter/begrepp och /en/forskningsrapporter/begrepp), som
varje rapportsida länkar till. En term som en rapport använder och som saknas i ordlistan förklaras vid första
användning eller läggs till i ordlistan. Siffrorna förklaras inte en och en, som i artiklarna: rapporten ska gå att läsa
för en statistiker utan att bli omständlig.

## Fasta rubriker, i denna ordning (IMRaD i registrerad form)

Ingen numrering av rapporterna i titeln; typen Rapport och versionsraden räcker.

0. **Huvud** (kursiv rad först i texten): författare och tillhörighet, formen (se Märkningen), version och datum, tidslinjen (se Datumen), licens (CC BY 4.0),
   citeringsrad till den engelska versionen, nyckelord, konkurrerande intressen, finansiering.
1. **Sammanfattning**, strukturerad: bakgrund och syfte, material, metod, resultat (effekt och osäkerhet i siffror),
   slutsats. Säg vad som inte visats.
2. **1. Inledning**: tidigare forskning med referenser, vad som saknas i den, studiens syfte.
3. **2. Förregistrering**: planens fil, datum och SHA-256; hypotesen ordagrant; förutbestämda gränser och
   tolkningsregler; vad som var sett före låsningen; vilka analyser som är konfirmatoriska, vilka som är uppföljning
   (egen låst plan) och vilka som är explorativa.
4. **3. Material**: korpusens fingerprint, urvalet steg för steg med antal (vikingatida, svenska landskap, läsbara,
   flyttfiltret), vad som mäts och hur (regel + facit mot handkodning med felandel), jämförelsen, justeringarna.
5. **4. Metod**: 4.1 modellen, 4.2 korrigering och replikering (halvorna), 4.3 robusthetstrappan, 4.4 avvikelser
   från planen (alltid med, också när det är ”inga”).
6. **5. Resultat**: 5.1 konfirmatoriskt huvudtest med halvorna och ett diagram, 5.2 planens robusthetsprov,
   5.3 trappan steg för steg som lista med modellkontroll, kodningsfel och q_global, 5.4 uppföljning (märkt).
7. **6. Diskussion**: vad fyndet säger, mot tidigare forskning, svagheter i ordning efter vikt, vad som skulle
   fälla fyndet.
8. **7. Slutsats**, kort.
9. **Data och kod**: skript, fingerprint, kommando, licens, var mönstret syns i appen, länk till populär artikel.
10. **Referenser** i Futhark-stil (efternamn, initial, år, titel, serie, sidor).
11. `:::box Det viktigaste i korthet` (sajtens korthetsregel) – tolkningen, inte sifferrepris.

## Versioner
Två versioner hålls isär: **rapportversionen** (1, 2 … efter rättelser) och **Vitkis version** (programmet, ur
web/package.json, i dag 3.0.0), plus commit för kodläget så länge ingen release med DOI finns. Skriv aldrig bara
”version 1”.
v1 med datum i rubrikraden under titeln. En rättelse ger v2 med en ändringslogg sist i rapporten (vad, varför, när);
aldrig tyst patch. DOI via Zenodo när repot släpps (RELEASING.md): rapporten hänvisar då till den versionen.
