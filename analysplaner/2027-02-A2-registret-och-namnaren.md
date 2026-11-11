# Analysplan A2: registret och nämnaren – vad mäter stentätheten?

Skriven 2026-11-11 som fas 1: ingenting av det som prövas nedan har räknats. Bara fältens tillgång har räknats (antal
poster som har ett fält, se ”Tillgång”). Inga stenar har lagts mot inventeringsår, bebyggelseenheter, skatt eller
registrets täthet. Planen låses med sha256 och commit när Viktor har granskat den, före körningen i februari 2027. Den
läggs på Zenodo med datum och DOI när studien startar.

Studie A2 i `PUBLICERINGSPLAN.md` (februari 2027). Den täcker frågelistans rader med studien ”feb 2027 – A2. Registret
och nämnaren” (`utdata/litteraturgenomgang/artikelkandidater/fragelista.jsonl`). Huvudfrågorna är:
- ”Tomma platser på kartan: inga stenar, eller ingen som letade?”
- ”Fornminnesregistret ser ojämnt: vad händer med våra kartor?”
- ”Hundaret, socknen och byn: stenar per gård i stället för per ruta”
- ”Gravar men inga stenar”
- ”Var är databasen tom?”
- ”Befolkning eller minne?”

Några av frågelistans rader besvaras inte här (se ”Utanför planen”).

## Varför
Vitkis platsstudier använder Kulturmiljöregistret (KMR) som underlag:
- gravfälten vid stengrupperna (82 mot 55 %);
- bygderutorna i Palms jordar (rutor med minst ett gravfält);
- vägarna.

Registret byggdes upp landskap för landskap och har reviderats ojämnt. Stentätheten jämförs i hela litteraturen, och i
Vitki, per landskap eller per ruta, utan en nämnare för hur många som bodde där eller hur noga man letade. Den här
studien skiljer tre saker åt:
- vad registret och letandet ger;
- vad bebyggelsen ger;
- vad som återstår och kan vara sed och minne.

Studien bygger på A1 (januari): P1d avgör hur stenarna räknas per socken, och P2 avgör om bortfallet måste vägas in.

## Frågorna
- **P1.** Beror registrets täthet av gravfält på när socknen inventerades? Håller Vitkis KMR-resultat när det kontrolleras
  (självkontrollerna K-A, K-B och K-C)?
- **P2.** Tomma platser: har de få stenar för att få bodde där, för att ingen letade, eller för att seden inte fanns där?
- **P3.** Nämnaren: håller Mälardalens övervikt när stenarna räknas per gård och by i stället för per ruta (P3a)? Följer
  stenarna i Uppland 1314 års skattekraft socken för socken (P3b)?
- **P4.** Var är databasen tom? Fältens fyllnadsgrad per landskap och utgåva, var Rundata och Runor är oense, och om de
  skannade stenarna är representativa.
- **P5.** Befolkning eller minne? Hur nära följer stenarna bebyggelsen, och hur mycket skiljer bygderna efter att
  bebyggelse, jord, letande och bortfall räknats bort?

**Konfirmatoriska prov:** P1, P2, P3a och P3b, med Holm över de fyra. Självkontrollerna K-A, K-B och K-C är en egen
familj med Holm över de tre. P4 är beskrivande och P5 en skattning, båda med tolkning som bestäms nu.

## Litteraturen planen bygger på
Kontrollerad mot originaltexten 2026-11-11 i `downloads/tidskrifter/sok.sqlite`. Sidorna är de tryckta.

**Inventeringen**
- **Hyenstrand 1978**, Fornvännen 73.
  - s. 70: fornminnesinventeringen gick landsdel för landsdel:
    - Gotland och Öland omkring 1940;
    - Småland och Östergötland under 1940-talet, där ”en fullständigt heltäckande inventering kunde ej uppnås”;
    - Uppland, Södermanland och Västmanland under 1950-talet;
    - Norrlands kustlandskap, Dalarna, norrländska inlandet och västra Sverige under 1960-talet;
    - Norrland–Dalarna samt Skåne och Blekinge omkring 1970;
    - Bohuslän 1973–77.

    Revidering pågår sedan 1974.
  - s. 71: statistik över förstagångsinventeringen 1938–1977 per landskap. Inventeringen blev ”primärt … en
    gravinventering”. Dateringen bygger på erfarenhetsregler som ”gravfält med högar = vikingatid” och är ”synnerligen
    inexakt”. ”Funktionella” lämningar (fångstgropar, ödesbölen, fossil åker, järnframställningsplatser) har kommit med
    allt mer.
- **Jönsson och Löthman 1978**, Fornvännen 73, s. 108. Omkarteringen av Gotland pekar på ”en dryg fördubbling” av antalet
  registrerade lokaler jämfört med 1938–40.
- **Varenius 1978**, Fornvännen 73, s. 122. Ett tomrum i kustbandet beror på att fornlämningstypen ”inte hade
  observerats när fornminnesinventeringen gick fram i dessa landskap på 1940- och 1950-talen”.
- **Selinge 1978**, Fornvännen 73, s. 79. I Västernorrlands järnåldersbygder saknas 537 av 2 549 kända fornlämningar i
  Medelpad och 630 av 1 356 i Ångermanland, i genomsnitt omkring 30 procent.

**De tomma platserna**
- **Nordberg och Wikell 2006**, Fornvännen 101, s. 306. Att inga kammargravar är kända i vissa socknar ”betyder inte per
  se att de inte existerar”. Skillnaden mellan landskap kan bero mer på exploatering och inventering.
- **Källström 1993**, Fornvännen 88, s. 173. ”Det har allmänt antagits att runstenar inte skall ha rests inom det område
  som numera utgör landskapet Dalarna.”
- **Wikell, Källström och Dahlin 2018**, Fornvännen 113, s. 8. ”Frånvaron av runstenar i Sevede beror på en
  forskningslucka.”
- **Jansson 1948**, Fornvännen 43, s. 292. Runstensfattigdomen i Jönåkers härad, trots gammal och rik bygd, kan bero på
  att stenarna ”ha blivit ovanligt hårdhänt behandlade”.
- **Gustavson, Brink Snædal och Strid 1983**, Fornvännen 78, s. 229. En runstensfattig socken kan bero på att ”socknen är
  liten och har få stora gårdar”.

**Vad antalet kända föremål beror på**
- **Kyhlberg 1980**, Fornvännen 75, s. 170, efter Malmer 1968, s. 87. Antalet nu kända föremål av en typ beror på fem
  faktorer: produktionstiden, produktionsintensiteten, seden, bevaringsförhållandena och fyndomständigheterna. P5 är ett
  försök att skilja dem åt för runstenarna.

**Utgåvorna**
- **Källström 2022** (Futhark 12, 2021), s. 26: SRI-bandens utgivningsår. På s. 10: utgåvor för Norrland saknas.

**Rättelse av frågelistan:** raden ”Var är databasen tom?” stöder sig på Stilborg 2021 (Fornvännen). Den uppsatsen
handlar om hur representativa publicerade keramikanalyser är, inte om Rundata. Frågan står därför på Vitkis egen grund,
inte på Stilborgs.

## Underlag
**Stenarna**
- Svenska vikingatida runstenar (`research_gaps.is_runestone`, Rundata 2018, korpusens hash antecknas). Fragment och
  försvunna räknas.
- Andra föremål ingår inte. Danska och norska stenar ingår inte.
- Stenen räknas till sin fyndsocken (Rundatas `parish`) och sitt fyndhärad (`district`, annars Runors `hundred`).
- Om A1 P1d ger ”håller inte” räknas socknarna bara med orörda stenar (inte flyttade, inte försvunna) i huvudproven.
  Alla kända stenar blir då robusthet. Annars är det tvärtom.

**Studieområdet**
- Alla socknar i Sveriges landskap utom Skåne, Blekinge och Halland. Deras stenar har DR-signum och ligger utanför
  Vitkis svenska korpus.
- Socknar utan stenar ingår. Det är de tomma platserna.

**Socknarna**
- **Polygoner:** sockengränserna ur R-paketet histmaps (Riksarkivets historiska GIS, CC0), för år 1700 eller det
  tidigaste år som täcker hela studieområdet. Paketet installeras från GitHub (`junkka/histmaps`) före körningen.
- **Om installationen misslyckas:** Voronoiytor kring ISOF:s sockenpunkter (`geografi_kallor/isof/parishes.json`),
  inom landskapet och klippta mot land år 1050. Rastret är `/Volumes/2TB/cache/terra/vatten1050_100m.tif`, samma som
  i `platsen.py`. Det skrivs ut.
- **Ur polygonerna:**
  - landyta;
  - andel lera och silt (`jordart_100m.tif`);
  - medelavstånd till vatten år 1050 (som i Palms jordar).

**Bebyggelsen, nämnaren**
- **Huvudnämnare:** Rosenbergs *Geografiskt-statistiskt handlexikon öfver Sverige* (1882–83), i Riksarkivets utgåva
  (`geografi_kallor/riksarkivet/Rosenberg.csv`). Uppslagsord som enligt beskrivningen är By, Byar, Gård eller
  Herregård räknas per församling och län.
- **Begränsning:** det är 1800-talets bebyggelse, och urvalet av gårdar är inte fullständigt överallt. Gotland har t.ex.
  få gårdsuppslag. Därför är ”bara By” en robusthetsrad.
- **Inte nämnare:** de geometriska kartornas namn 1630–1655 (`kartnamn_1630_1655.csv`). Kartorna täcker bara en del av
  byarna, ojämnt mellan landskapen.

**1314 års sexårsgärd** (SDHK 2593, Riksarkivet, CC BY 4.0, `geografi_kallor/sdhk/sdhk_2593.txt`)
- Uppsala ärkestifts kyrkor i Upplands folkland, ordnade per hundare (`utdata/geografi/sexarsgard_1314.json`, 157
  kyrkor i Tiundaland, Attundaland och Fjädrundaland).
- **Belopp:** tolkas ur den latinska texten (mark och öre; 1 mark = 8 öre) och skrivs i
  `utdata/registret/sexarsgard_1314_belopp.csv` innan de läggs mot stenarna.
- **Avgränsning:**
  - prebenden och ärkebiskopens bord räknas inte;
  - en kyrka ”cum annexa” räknas som en enhet med sina annexsocknar;
  - kyrkor som inte kan kopplas till en socken redovisas.
- **Kontroll:** datering och stift kontrollerades 2026-11-10. Listan är daterad 1314 i brevet och gäller Uppsala
  ärkestift. Gillingstams omdatering till 1279–82 gäller Strängnäs stift, som inte används här.

**Registret**
- KMR:s nationella uttag (`geografi_kallor/raa/lamningar_sverige.gpkg`, uttaget 2026-11-02). Bara tabellen `lamning`
  läses (typ, bedömning, aktualitetsstatus, undersökningsstatus, län, socken), med sqlite3. Ingen geometri behövs, för
  posterna har socken.
- **Gravfält:** typen Gravfält. Granskade gravfält (klassen V i självkontrollen 2026-11-10) ur
  `data/raa/gravfalt_detaljer.csv`.
- **Letandets index E (bestämt nu).** Lämningstyper som enligt Hyenstrand 1978 (s. 71) och Varenius 1978 (s. 122) kom med
  först i senare och noggrannare inventeringar:
  - fossil åker och område med fossil åkermark;
  - röjningsröse;
  - kolningsanläggning;
  - fångstgrop;
  - gränsmärke;
  - hägnad;
  - lägenhetsbebyggelse;
  - område med skogsbrukslämningar;
  - blästbrukslämning.

  E_p = log(1 + antal sådana lämningar per km² landyta i socknen).
- **Exploateringsarkeologi U:** andelen av socknens lämningar som är helt eller delvis undersökta.
- **Ej bekräftade:** andelen med aktualitetsstatus ”Uppgift om lämning, ej bekräftad i fält”. Bara beskrivande.

**Inventeringsåret, D4 (se nästa avsnitt)**

**Utgåvorna:** SRI-bandets slutår per landskap enligt Källström 2022, s. 26 (samma tabell som i A1).

**Namnmatchningen**
- Nyckeln är landskap plus normaliserat sockennamn: gemener, utan ” sn”, ”socken” och ”församling”, och med -s-genitiv
  borttagen.
- Socknarna matchas mellan Rundata, KMR, Rosenberg, ISOF, histmaps och 1314-listan. Matchningsgraden skrivs i
  `utdata/registret/namnmatchning.csv` för varje källa.
- **Krav:** minst 90 % av stenarna och minst 85 % av socknarna i varje källa ska matchas.
- Det som inte matchas mappas för hand på namn och landskap, med stenantal och kovariater dolda. Det som ändå inte går
  att matcha redovisas och räknas bort.

## D4: inventeringsåret, och vad som händer om täckningen är låg
D4 hämtas nu av en annan körning. Planen läser den fil hämtningen skriver (i `data/raa/` eller
`utdata/d4_inventering/`). Filnamn, SHA-256 och hämtdatum antecknas i `utdata/registret/d4_val.json` innan något läggs
mot stenarna.

**Varianterna, i den här ordningen. Den första som klarar kraven används:**
- **D4-F, Fornsöks fältdatum per lämning.** Fältet `faltdatum` i Fornsöks lämningspost (provet 2026-11-11: en
  runristning i Fresta har `faltdatum` 1979-06-21).
  - Socknens inventeringsår = medianåret av `faltdatum` bland socknens poster av typerna Gravfält, Hög, Stensättning och
    Röse. Det är gravtyperna, som var förstagångsinventeringens kärna (Hyenstrand 1978, s. 71).
  - **Reviderad** = minst hälften av dessa poster har `faltdatum` 1974 eller senare.
  - Fältdatumet kan vara den senaste fältkontrollen och inte den första inventeringen. Måttet betyder då ”när
    registrets beskrivning i socknen senast sattes i fält”. Det är det som bestämmer vad registret innehåller nu, och
    så skrivs det i rapporten.
- **D4-T, inventeringsår ur fritexten.** Årtal ur ”Referens: skriftlig källa”, t.ex. ”Raä inv 1946” eller
  ”Inventeringsbok … 19xx”, med en regel som skrivs innan den körs. Socknens år och reviderad som i D4-F.
- **D4-H, landskapets epok enligt Hyenstrand 1978, s. 70.** Grov reserv. Den varierar bara mellan landskap.

**Kraven för D4-F och D4-T**
- Minst 70 % av gravtypernas poster har ett år.
- Minst 80 % av studieområdets socknar med minst en runsten får ett år ur minst 5 poster.

**Täckningen** räknas först, utan stenar, och skrivs i `utdata/registret/d4_tackning.json`: andel poster med år per
län och per socken, och för vilken variant.

**Om bara D4-H klarar sig**, eller om D4 inte finns i tid:
- P1 kan inte prövas inom landskap, eftersom D4-H sammanfaller med landskapets fasta effekt. Det redovisas som ”kan inte
  prövas”, med en beskrivande jämförelse mellan landskapen.
- Inventeringsåret lämnas ute ur P2, K-A, K-B, K-C och P5. Indexet E och andelen undersökta U står kvar, eftersom de
  inte beror på D4.
- Detsamma gäller om D4-F eller D4-T klarar kraven i bara en del av landet. Då används den varianten bara där, och resten
  redovisas.

## Tillgång (räknad 2026-11-11, bara antal poster med fältet)
**KMR (`lamning`)**
- 766 011 lämningar, varav 763 682 med socken. 4 790 olika par av län och socken (också städer och nya församlingar).
- Gravfält: 18 634.
- Typerna i indexet E:

  | Typ | Antal |
  |---|---|
  | Kolningsanläggning | 43 976 |
  | Lägenhetsbebyggelse | 51 373 |
  | Fossil åker | 25 462 |
  | Fångstgrop | 22 267 |
  | Område med skogsbrukslämningar | 17 640 |
  | Hägnad | 14 933 |
  | Gränsmärke | 9 492 |
  | Område med fossil åkermark | 9 322 |
  | Röjningsröse | 8 141 |
  | Blästbrukslämning | 5 705 |

- Helt undersökta: 15 123. Delundersökta: 15 335. ”Uppgift om lämning, ej bekräftad i fält”: 42 035.
- Inget fält för inventeringsår finns i uttaget. D4 hämtas ur Fornsök.

**Nämnare och enheter**
- Rosenberg: 52 982 uppslag av typen By, Byar, Gård eller Herregård i 2 358 församlingar. Härad finns för 41 938.
- ISOF: 2 538 socknar (punkter) och 296 härader.
- 1314-listan: 157 kyrkor med namn i tre folkland. Beloppen är inte tolkade än.
- De geometriska kartorna 1630–55: 29 931 bebyggelsenamn, varav 28 284 med socken. Täckningen är ojämn, och de används
  inte.

**Stenarna**
- Rundata: 2 321 svenska runstenar, alla med socken och 2 200 med härad.
- Runor: härad för alla 2 402 svenska vikingatida runstenar.

**Skanningar:** 95 olika signum i 6 öppna serier (`data/scan_files.json`).

**R-paket:** sf, MASS, glmmTMB, lme4, spdep och survival finns. histmaps finns inte och installeras.

## P1. Registrets täthet och inventeringsåret (konfirmatoriskt)
**Modell**
- Socknar i studieområdet med polygon och D4-år.
- Utfall: antalet registrerade gravfält G_p.
- Negativ binomial med log(landyta) som offset. Förklaringar:
  - inventeringsåret (decennier, linjärt);
  - reviderad (0/1);
  - log(1 + bebyggelseenheter);
  - andel lera och silt;
  - avstånd till vatten 1050;
  - landskapet som fast effekt.

**Prov**
- Inventeringsårets koefficient.
- p-värdet kommer från 9 999 omblandningar av socknarnas inventeringsår och revisionsflagga (tillsammans) mellan socknar
  i samma län (slumpfrö 2026). Det är slumpen inom distriktet: länets blandning av år står kvar.
- Tvåsidigt.

**Gräns, bestämd nu:** **inventeringsåret syns i registret** om Holm-p < 0,05 och kvoten per decennium ligger utanför
0,90–1,11 (minst 10 % per decennium åt något håll). Annars **syns inte**. Under 200 socknar med år ger **kan inte
prövas**.

**Robusthet:**
- granskade gravfält (V) i stället för alla;
- Hög och Stensättning i stället för Gravfält;
- utan bebyggelseenheterna;
- bara Götaland och bara Svealand.

**Beskrivande, per län:**
- andel ”ej bekräftad i fält”;
- andel undersökta;
- Selinges 30 % för Västernorrland (1978, s. 79) bredvid länets andel ej bekräftade.

**Självkontrollerna (egen familj, Holm över tre)**

Varje självkontroll bedöms som självkontrollerna i december:
- **står sig:** villkoren nedan är uppfyllda;
- **försvagas:** okorrigerat p < 0,05 men inte allt;
- **faller:** åt fel håll eller okorrigerat p ≥ 0,05.

| Kontroll | Vad som körs | Står sig om |
|---|---|---|
| **K-A, familjens plats** | Modellen i `utdata/familjens_plats/analys.R` med samma stenar, plus inventeringsåret, revisionsflaggan och E för stenens socken | oddskvoten > 1, Holm-p < 0,05, och båda halvorna har oddskvot > 1 med p < 0,05 |
| **K-B, Palms P1** | Modellen i `utdata/palm_jordarna/analys.R` med samma rutor, plus inventeringsår och E för den socken rutans mittpunkt ligger i | lerans koefficient är > 0 med ensidigt Holm-p < 0,05 |
| **K-C, Palms P2** | Samma modell som K-B | kontrasten Mälarlandskapen mot Götalands inland är > 1 med ensidigt Holm-p < 0,05; den förklarade andelen redovisas före och efter |

## P2. De tomma platserna (konfirmatoriskt)
**Modellerna**
- Enhet: socken. Utfall: antalet runstenar S_p.
- **M1 (bygden):** negativ binomial med log(landyta) som offset. Förklaringar:
  - log(1 + bebyggelseenheter);
  - log(1 + gravfält);
  - andel lera och silt;
  - avstånd till vatten 1050.

  Inga fasta effekter för landskap: frågan gäller just skillnaderna mellan landskapen.
- **M2 (bygden och letandet):** M1 plus:
  - E_p;
  - U_p;
  - inventeringsåret och revisionsflaggan (om D4 klarar kraven);
  - SRI-band finns för landskapet (0/1);
  - år sedan bandets slutår.

**Prov.** Koefficienten för E_p i M2, alltså att fler stenar är kända där registret letade noggrannare.
- p-värdet kommer från 9 999 omblandningar av E_p mellan socknar inom samma landskap. Ensidigt (> 0).
- **Gräns:** **letandet syns i stenkartan** om Holm-p < 0,05.

**Skattning.** Hur stor del av skillnaderna mellan landskapen som letandet förklarar:
- samma modeller med landskapet som slumpeffekt (glmmTMB);
- andelen = 1 − varians(M2) / varians(M1);
- bootstrap över socknar inom landskap (2 000).

**Platserna, bestämda nu.** För var och en: observerade stenar mot M1:s och M2:s väntade antal, med 90 %
prediktionsintervall (parametrisk bootstrap, 2 000).
- Dalarna (Källström 1993, s. 173);
- Sevede härad (Wikell m.fl. 2018, s. 8);
- Jönåkers härad (Jansson 1948, s. 292);
- Västmanland;
- Värmland;
- Hälsingland och Medelpad;
- Ångermanland.

**Läsningen för varje plats**
- **Tomt men väntat:** inom M1:s intervall. Bygden förklarar.
- **Letandet förklarar:** under M1:s intervall men inom M2:s.
- **Färre än både bygd och letande väntar:** under M2:s intervall. Kandidat för var seden inte fanns, eller för bortfall
  enligt A1. Studien kan inte skilja de två åt, och det skrivs ut.

**Uppland som norm (beskrivande):** Upplands slumpeffekt i M1 och M2. Krymper den med mer än hälften (på log-skala), skrivs
det att Upplands försprång till stor del är letande.

**Robusthet:**
- utan gravfälten i M1 och M2, eftersom gravfälten själva kommer ur registret och kan bära letandet;
- bara orörda stenar;
- härad i stället för socken som enhet;
- E utan kolning och lägenhetsbebyggelse, som också följer skogsbygd;
- med A1:s bortfall per jordart som vikt, om A1 P2 gav större bortfall på någon jordart.

## P3. Nämnaren (konfirmatoriskt, två prov)

**P3a. Håller Mälardalens övervikt per gård?**
- **Grupper** som i Palms P2: Mälarlandskapen (Upplands folkland, Södermanland och Västmanland) mot Götalands inland
  (Västergötland och Smålands små land).
- **Kvoten** stenar per enhet i Mälarlandskapen delat med samma kvot i Götaland, för tre enheter:
  - per bebyggelseenhet (R_B, huvudmåttet);
  - per km² (R_yta);
  - per gravfält (R_grav).
- **Prov:** negativ binomial S_p ~ grupp, med log(bebyggelseenheter) som offset och klusterrobusta standardfel per
  härad. Ensidigt, R_B > 1.
- **Gräns:** **övervikten håller per gård** om R_B > 1 med Holm-p < 0,05. Hur mycket mindre R_B är än R_yta redovisas
  (kvoten av logaritmerna, med bootstrapintervall).
- **Robusthet:**
  - bara By som nämnare;
  - med jord och vatten i modellen;
  - Östergötland och Öland som tredje grupp (beskrivande).

**P3b. Följer stenarna 1314 års skattekraft i Uppland?**
- **Urval:** socknar och annexenheter i 1314-listan.
- **Modell:** negativ binomial S_p ~ log(sexårsgärd i öre) + folklandet som fast effekt.
- **Prov:** p-värdet kommer från 9 999 omblandningar av beloppen mellan enheter inom samma folkland. Ensidigt (> 0).
- **Gräns:** **stenarna följer skattekraften** om Holm-p < 0,05. Elasticiteten redovisas med intervall.
- **Beskrivande:** samma modell med log(bebyggelseenheter) som extra förklaring, och om elasticiteten står kvar.
- **Tolkning:** sexårsgärden beskattade kyrkans inkomst, inte gårdarna direkt. Måttet är ”socknens skattekraft 1314”,
  inte befolkning, och så skrivs det.

**P3c (beskrivande).** Per hundare i 1314-listan: stenar, summan av sexårsgärden och antalet kyrkor. Per härad i landet:
stenar per bebyggelseenhet, rangordnade, med intervall.

## P4. Var är databasen tom? (beskrivande, med läsning som bestäms nu)
**Fältens fyllnad**
- Fält: säker stilgrupp, material, säker ristare, korsform, placeringstext och koordinat (Rundata); `original`,
  profilstil och kors (Runor).
- Redovisas:
  - per landskap med minst 50 stenar;
  - per SRI-del (Uppland, Småland, Västergötland och Gotland, där delarna kom ut olika år).
- **Standardisering:** fyllnaden för ristare, kors och material standardiseras direkt till rikets fördelning av
  stilgrupper, bland stenar med säker stilgrupp. Signaturer och kors hör till de senare stenarna, så en rå jämförelse
  vore missvisande.
- **Läsning:** ett fält är **ojämnt fyllt** om den standardiserade fyllnaden skiljer mer än 30 procentenheter mellan
  landskapen. Sådana fält skrivs in i METHODS.md som osäkra för jämförelser mellan landskap utan justering.

**Rundata mot Runor**
- Andelen stenar per landskap där de två är oense om:
  - försvunnen;
  - flyttad (Vitkis `is_moved` mot Runors `original`);
  - stilgrupp;
  - koordinater mer än 500 m isär.
- Bara beskrivande. Den danska databasen ingår inte (Sverige som standard).

**Skanningarna**
- Runstenarna bland de 95 skannade signumen jämförs med korpusen på landskap, stilgrupp och material, med Fishers exakta
  test eller omblandning.
- **Läsning:** **inte representativa för X** om p < 0,05. Det skrivs vid alla resultat som bygger på skanningar.

## P5. Befolkning eller minne? (skattning, med läsning som bestäms nu)
**Modell**
- Enhet: socken. glmmTMB, negativ binomial, landskapet som slumpeffekt. Ingen offset.
- S_p ~ log(bebyggelseenheter) + andel lera + vatten + letandets block från M2 + (1 | landskap).

**Skattas**
- Elasticiteten β mot bebyggelsen, med 95 %-intervall.
- σ, landskapets standardavvikelse på log-skala.

**Läsningen (bestämd nu)**
| Utfall | Villkor | Betydelse |
|---|---|---|
| **Följer bebyggelsen** | β:s intervall innehåller 1 men inte 0, och σ < 0,5 | landskapens takt skiljer mindre än ±65 % |
| **Ett minnesskick som skiftar mellan bygder** | σ > 1,0 | landskapen skiljer mer än e-faldigt (2,7 gånger) vid samma bebyggelse, jord och letande |
| **Både och** | annars | – |

**Bortfallet:** om A1 P2 gav större bortfall på någon jordart körs P5 också med A1:s vikter. Båda redovisas.

**Ramen:** Kyhlbergs och Malmers fem faktorer (Kyhlberg 1980, s. 170). P5 skiljer bebyggelsen (produktionsunderlaget),
letandet (fyndomständigheterna) och bortfallet (bevaringen) från resten. Resten är sed och minne, och det kan inte delas
vidare med dessa data.

## Vad som INTE får göras
- Inga nya kovariater, lämningstyper i E, grupper eller platser efter att resultaten setts.
- Platserna i P2 är bestämda ovan, och fler läggs inte till.
- D4-varianten väljs enligt kraven innan stenarna läggs mot den, och byts inte efteråt.
- Namnmatchningen görs utan att se stenantal eller kovariater.
- Ingen egen läsning av inskrifter.
- Artikeln och rapporten skrivs först efter körningen.

## Tolkning (bestämd nu)
**P1**
- **Inventeringsåret syns:** alla KMR-baserade platsresultat ska ha inventeringsåret som kontroll i fortsättningen. Det
  gäller också studie D i april, och det skrivs in i METHODS.md.
- **Syns inte:** registrets täthet beror inte mätbart på inventeringsåret, i de delar där D4 finns. Det skrivs ut med
  täckningen.

**K-A, K-B och K-C**
- **Står sig:** resultaten står kvar, och rapporterna får en rad om att kontrollen gjorts.
- **Försvagas:** förbehållet skrivs in.
- **Faller:** rättelse enligt Vitkis regel för tillbakadragna resultat. Artikeln, rapporten och IMPLEMENTATIONSPLAN.md
  ändras samma dag som Viktor sett utfallet.

**P2**
- **Letandet syns:** artikeln ”Fanns det inga stenar – eller letade ingen?” (9 feb) skrivs med P2:s platser, var och en
  med sin läsning.
- **Syns inte:** artikeln får vinkeln att de tomma platserna inte är tomma för att ingen letade. Den tar upp de platser
  som har färre stenar än både bygd och letande väntar.
- **I båda fallen** skrivs det ut att seden och bortfallet inte kan skiljas åt med dessa data.

**P3a**
- **Övervikten håller per gård:** Mälardalens övervikt är inte bara fler gårdar. Palm-artikeln kan säga det.
- **Håller inte:** övervikten är i första hand fler gårdar per yta. Det skrivs in i Palm-resultatets svagheter och i
  rapporten.

**P3b:** avgör om ”rikare socknar reste fler stenar” får skrivas om Uppland 1314, med förbehållet om vad skatten mäter.
Studie F i juni (Malmers regel) bygger vidare på det.

**P4:** de fält som är ojämnt fyllda listas i METHODS.md. Framtida jämförelser mellan landskap av dem kräver justering.

**P5:** läsningen styr hur Vitki skriver om stentäthet:
- **följer bebyggelsen:** ”stentätheten följer bebyggelsen”;
- **minnesskick:** ”stentätheten mäter seden mer än folket”;
- **både och:** det skrivs med β och σ.

**Rapporten** ”Stenarna vi känner – registret, nämnaren och kartan” (23 feb) redovisar allt, också nollresultat och det
som inte kunde prövas.

## Utanför planen (frågelistans rader som inte besvaras här)
- **”Uppland som norm” för stavning, formler och stilgrupp mot avståndet från Uppland:** till 2028 (språkets klockor).
  Här ingår bara Upplands försprång i stentäthet (P2).
- **”Vem skrev av stenarna och när” (utgivarens blick):** bara fyllnaden per SRI-del (P4). Läsningarnas beroende av
  utgivaren hör till studie C (mars, utgivareffekt per SRI-band).
- **”Tre databaser, en sten”:** bara Rundata mot Runor (P4). Den danska databasen ingår inte.
- **”Varför har Västmanland fyrtio gånger färre runstenar”:** Västmanland finns bland platserna i P2. Berggrund, kalk och
  järn hör till studie S (oktober, D1).

Kopplingen mellan studie och fråga i `bygg_fragelista.py` (STUDIER) ändras inte av den här planen. Om Viktor vill flytta
raderna görs det där och i PUBLICERINGSPLAN.md samtidigt.

## Redovisning
Allt i `utdata/registret/`:
- **Indata, skrivna innan något läggs mot stenarna:**
  - `d4_val.json` och `d4_tackning.json`;
  - `namnmatchning.csv`;
  - `sexarsgard_1314_belopp.csv`;
- **`socknar.py`:** en rad per socken med stenar, bebyggelseenheter, gravfält, E, U, D4, landyta, lera och vatten. Skriver
  `socknar.csv` med korpusens hash.
- **R-skripten:**
  - `p1_register.R` med självkontrollerna i `kontroller/`;
  - `p2_tomma.R`;
  - `p3_namnare.R`;
  - `p5_minne.R`;
- **`p4_fyllnad.py`**;
- **`resultat.json` och `resultat.md`**, med planens sha256;
- **figurerna:**
  - karta över observerat mot väntat per socken och härad;
  - landskapens takt per yta, per gård och per gravfält.

**Rapport och artikel**
- Rapport på Zenodo enligt MALL.md, med Scholar-taggar, PDF på webbplatsen och data som eget dataset med DOI. Rosenberg
  och SDHK krediteras med sina licenser.
- Utfallen förs in i rapporter och artiklar först när Viktor har sett dem.

**Minne och körning (16 GB-Macen)**
- KMR-tabellen läses utan geometri, med sqlite3 och bara de kolumner som behövs.
- Sockenpolygonerna och de två rastrerna läses en gång.
- Modellerna har några tusen rader.
- Ett jobb i taget. histmaps installeras före körningen, inte under den.
