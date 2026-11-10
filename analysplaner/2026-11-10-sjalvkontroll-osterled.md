# Analysplan: självkontroll av ”runstenarna ser mot öster” – Ingvarståget och tiden

Skriven och låst 2026-11-10, innan något av proven nedan har räknats. En självkontroll av ett publicerat resultat
(analysplaner/2026-10-28-vikingarnas-omvarld.md, artikeln ”Vikingarnas värld – vilka platser nämner de?”), utlöst av
litteraturgenomgången (`utdata/litteraturgenomgang/SYNTES.md`).

## Påståendet som prövas
Den publicerade artikeln säger: ”De svenska runstenarna ser mot öster: 66 % av platserna ligger där” (olika platser per
sten, ΣÖ/Σ(Ö + V), 95 %-intervall 58–74 %). Talet 68 % i `utdata/varlden/README.md`, i minnet och i
litteraturgenomgången är det tidigare måttet på träffar (123/180), räknat före låsningen.

Två invändningar ur litteraturen:
1. **Sindbæk 2003** (*Fornvännen* 98, ”Varægiske vinterruter”): av de omkring 96 svenska runstenar som nämner färd
   österut hör mer än 25 till Ingvars tåg, en enda expedition (omkring 1041). Östandelen kan alltså bäras av en enda
   händelse.
2. **Westin 1941** (*Fornvännen* 36, ”En västmanländsk ryttargrav”): ”De svenska vikingatågen voro huvudsakligen
   riktade mot öster. Mot slutet av vikingatiden inträder emellertid en förskjutning” mot väster. Påståendet görs som
   allmän kunskap och har inte prövats på runstenarna med datering.

## Vad som har setts före låsningen
Den publicerade östandelen (66 %, 58–74) och det äldre träffmåttet (68 %). Kolumnerna i `platser_per_text.csv`
och `platser.csv`. I Rundata, för alla 2 321 svenska runstenar (inte bara de som nämner en plats): fördelningen av
fälten `style`, `style_uncertain` och `dating`, och att fältet `other` kallar en enda sten ”Ingvarssten”. Ingen
Ingvarsten har räknats eller listats, ingen östandel utan Ingvar och ingen tidskurva har räknats.

## Data
- **Platserna:** `utdata/varlden/platser_per_text.csv`, raderna `korpus == runstenar_sverige`, räknade med den
  ortnamnslista (`platser.csv`) som låstes 2026-10-28. Listan ändras inte. Samma urval som i den publicerade analysen:
  vikingatida svenska runstenar med engelsk översättning i Rundata (`src/nordic.is_runestone`, `land_of == sverige`).
- **Stenens övriga uppgifter:** `data/rundata.json`, kopplat på signum: översättning, normalisering, stilgrupp
  (`style`, `style_uncertain`), landskap (signumets prefix). Signa som inte går att koppla listas.
- **Måttet:** som i den låsta planen: för varje sten Ö = antal olika östliga platser och V = antal olika västliga
  (”Österled/Västerled (allmänt)” en plats var; söder och Nordatlanten ingår inte). Östandel = ΣÖ / Σ(Ö + V) över
  stenarna. Osäkerhet: klusterbootstrap över stenar, 10 000 dragningar, percentilintervall, frö 20261110.

## Ingvarsstenarna (definitionen bestäms nu)
En sten räknas som **Ingvarsten** om något av följande gäller:
- (a) `src/entities.extract(rec)["events"]` innehåller ”Ingvarståget”, det vill säga Ingvarr som tågets ledare
  (”with Ingvarr”, ”Ingvarr's retinue/troop/men/ship …”, eller namnet i samma sats som *east*, *travel*, *ship* eller
  *Serkland*); eller
- (b) översättningen eller normaliseringen nämner namnet Ingvarr i någon böjningsform (`\bIngvar`, skiftlägesokänsligt)
  **och** stenen har minst en östlig plats i tabellen. Det fångar stenar som nämner tåget utan formeln, som
  ”Haraldr, Ingvarr's brother” (Sö 179).

Definitionen är medvetet vid: den tar hellre bort en östlig sten för mycket än för lite, vilket gör det svårare för
påståendet att hålla. Listan (signum, landskap, vilket led som träffade, textutdraget) skrivs till
`ingvarsstenar.csv` och granskas mot texten **innan någon andel räknas**. En sten där Ingvarr uppenbart bara är en
vanlig man utan koppling till tåget får tas bort, med motivering i listan; därefter fryses listan. Antalet jämförs med
Sindbæks ”mer än 25” (av 96, efter Larsson 1990).

## Prov
**P1 (Sindbæk: östandelen utan Ingvarståget).** Östandelen räknas om utan Ingvarsstenarna, med 95 %-intervall
(klusterbootstrap enligt ovan). Påståendet i artikeln är att runstenarna ser mot öster, alltså att mer än hälften av
platserna ligger där.
- **Håller:** intervallets nedre gräns > 50 %.
- **Försvagat (obestämt):** punktskattningen > 50 % men intervallet omfattar 50 %.
- **Håller inte:** punktskattningen ≤ 50 %.

Bredvid redovisas (beskrivande, ändrar inte utfallet): stenarnas andel i stället för platsernas (stenar med någon
östlig plats bland stenar med östlig eller västlig plats, Wilsonintervall), med och utan Ingvar; träffmåttet (68 %)
utan Ingvar; den smala definitionen (bara led a); Ingvarståget räknat som *en* text (gruppens olika platser en gång);
samma sak för väster – utan stenarna om Knuts gäld (`events` innehåller ”Knuts gäld”) och utan båda händelserna;
skillnaden i procentenheter mot den publicerade siffran; och östandelen utan Ingvar bredvid sagornas
(fornaldarsagor, Heimskringla, islänningasagor) intervall från den publicerade analysen.

**P2 (Westin: förskjuts tyngdpunkten mot väster?).** Stenar med minst en östlig eller västlig plats och en enda säker
stilgrupp (`style` är RAK, Fp/FP, Pr1, Pr2, Pr3, Pr4 eller Pr5, eventuellt med tillägget ”[Gräslund muntligt]”, och
`style_uncertain` är falskt). KB och stenar utan eller med osäker stilgrupp ingår inte. **Tidig** = RAK, Fp, Pr1, Pr2
(enligt Gräslund före omkring 1050); **sen** = Pr3, Pr4, Pr5.
- **Modell** (R): `glm(cbind(Ö, V) ~ sen + landskap, family = quasibinomial)`, en rad per sten; landskap = Uppland,
  Södermanland, Östergötland, övriga (efter regeln att jämföra över tid bara med regionen konstant). Effekten anges som
  oddskvot för sen mot tidig med 95 %-intervall.
- **Håller (Westin):** oddskvoten < 1, ensidigt p < 0,05.
- **Motsatt riktning:** oddskvoten > 1, tvåsidigt p < 0,05 (östandelen växer i stället).
- **Ingen förskjutning av betydelse:** hela 95 %-intervallet för oddskvoten inom 0,5–2 (vid en östandel kring 66 %
  motsvarar det ungefär ±15–17 procentenheter).
- Annars **obestämt**.
- Kräver minst 20 platser (Σ(Ö + V)) i både tidig och sen grupp; annars ”för få träffar” och bara beskrivande kurva.
- Provet görs med Ingvarsstenarna (huvudprov: Westin talar om alla färder) och utan dem. Håller det bara med dem, är
  förskjutningen i så fall en följd av en enda händelse kring 1041 och redovisas så.

**Beskrivande tidskurva (inga test):** östandel per stilgrupp i ordningen RAK, Fp, Pr1, Pr2, Pr3, Pr4, Pr5 med antal
stenar, Σ(Ö + V) och intervall (för grupper med minst 10 platser), med och utan Ingvarsstenarna, i ett diagram med
Gräslunds dateringar på tidsaxeln.

**Robusthet för P2 (redovisas, ändrar inte utfallet):** utan landskap i modellen; trend på stilgruppens mittår (per
50 år) i stället för tidig/sen; med osäkra stilgrupper och kombinationer (”Pr3 - Pr4”) när alla ingående grupper
ligger på samma sida om 1050 (andra kombinationer utesluts); utan stenarna om Knuts gäld.

## Tolkning (bestämd nu)
- Håller P1: östandelen beror inte på Ingvarståget, och artikelns mening står kvar; skillnaden redovisas ändå.
- Försvagat P1: artikeln får ett tillägg att österns övervikt till en del bärs av en enda expedition, med båda
  siffrorna.
- Håller inte P1: artikelns mening rättas med en synlig rättelse (Ingvarståget, ett tåg, står för övervikten), och
  memoryn och README rättas samma dag.
- Håller P2: runstenarna visar Westins förskjutning mot väster inom 1000-talet. Motsatt riktning: runstenarna säger
  emot Westin. Ingen förskjutning av betydelse: på runstenarna syns ingen förskjutning; Westins bild vilar då på
  skattfynden (900-talet), som runstenarna inte täcker. Obestämt eller för få: runstenarna räcker inte för frågan.
- Runstenarnas datering är stilgruppens, inte årtal; stenarna minns främst dem som dog borta; att en plats nämns betyder
  inte att någon reste dit.

## Redovisning
`utdata/varlden/sjalvkontroll/`: `ingvarsstenar.py` och `ingvarsstenar.csv` (listan med granskning), `analys.py`
(P1 och tabellen till P2), `tid.R` (modellen), `resultat.json`, `resultat.md` (alla prov med antal stenar, Σ(Ö + V),
andelar, intervall, p och avvikelser från planen) och diagrammet över tidskurvan. Alla utfall redovisas, också om P1
inte håller.
