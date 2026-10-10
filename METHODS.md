# Metodbeskrivning

Den här filen beskriver exakt hur Vitki räknar, så att resultat kan granskas, upprepas och citeras.
Alla beräkningar finns i `src/` och testas i `tests/`. Varje analys sparar en **proveniens** (programversion,
mätmetodens version, SHA-256 för 3D-filen, alla parametrar och tidpunkt) som följer med i export och rapporter.

## 1. Huggspårsmått (mätmetod `groove-5`)

Källkod: `src/slice_analysis.py`.

1. **Tvärsnitt.** Mesh-filen centreras på mittpunkten av sin omslutande låda (samma som i webbläsaren).
   Ett plan läggs vinkelrätt mot spårets riktning och skär nätet. Bara skärningspunkter inom ±25 mm från
   mätpunkten, i sidled och höjdled, tas med (fönster) – annars kommer stenens baksida och kanter med i
   snittet genom en sluten skanning. Profilen uttrycks i x (tvärs spåret) och z (längs ytans normal).
2. **Uppåtriktning.** Vid manuell mätning används medelvärdet av ytnormalen i de klickade punkterna, vid
   ett klick och automatisk analys den lokala ytnormalen (se avsnitt 1b och 1c).
3. **Jämnt punktavstånd.** Profilen interpoleras linjärt till 0,05 mm mellan punkterna (finare än någon skanning), så
   att alla fönster nedan kan anges i millimeter. Profilens ursprungliga punktavstånd sparas (`point_spacing_mm`).
4. **Apex.** Profilen jämnas ut med ett glidande medelvärde över 1 mm. Apex är den lägsta punkten.
5. **Spårkanter (axlar).** Från apex söks utåt tills lutningen |dz/dx| understiger 0,15 och profilen nått minst
   halvvägs upp mot stenytan på den sidan (annars hittas en flat spårbotten i stället för kanten).
6. **Väggar.** Varje vägg anpassas med linjär regression, men **bara mellan 20 % och 80 % av höjden** från
   botten till spårkanten. Den rundade botten och spårkantens läpp planar annars ut väggarna och ger för
   stor vinkel (minst tre punkter, annars används hela väggen).
7. **Mått:**

| Mått | Definition |
|---|---|
| V-vinkel (°) | Öppningsvinkeln mellan väggarnas regressionslinjer, mätt från apex. |
| Asymmetri (°) | \|arctan(1/\|k₁\|) − arctan(1/\|k₂\|)\|, skillnaden mellan väggarnas vinkel mot lodlinjen. |
| Spårdjup (mm) | Höjdskillnaden mellan högsta och lägsta punkt mellan kanterna. |
| Spårbredd (mm) | Avståndet mellan väggarnas linjer i höjd med stenytan precis utanför spårkanterna (medel av sidorna). |
| Djup/bredd | Spårdjup / spårbredd. |
| Bottenradie (mm) | 1/(2a) för en andragradskurva anpassad inom ±1 mm från apex. |
| Ytråhet (mm) | Medelabsolutavvikelsen från väggarnas regressionslinjer. |
| Väggpassning (R²) | Den sämre av väggarnas förklaringsgrad; används för kvalitetsgranskning. |

**Validering.** På syntetiska stenar med kända V-spår (öppningsvinkel 50–110°, djup 2–4 mm, välvd yta,
mätbrus 0,03 mm, `src/synthetic.py`) mäts vinkeln inom ±0,6° och bredden inom ±1 % (djup 4 mm). Testerna
körs automatiskt (`tests/`).

**Punkttäthet.** Öppet publicerade skanningar är förenklade i olika grad (0,33–1,11 mm mellan punkterna i
Kitzler Åhfeldts Södermanlandsserie). Samma syntetiska spår mätt vid 0,33 och 1,11 mm ger med `groove-4` samma
vinkel inom 1,5°, bredd inom 0,15 mm och bottenradie inom 0,1 mm; med `groove-3` växte bottenradien från 1,3 till
7,0 mm och vinkeln med 10° (`tests/test_slice_analysis.py`). För jämförelser mellan stenar kan den automatiska
analysen dessutom köras med fast rutnätsupplösning (`resolution_mm`) och med utjämning till en gemensam effektiv
upplösning (`harmonize_mm`); båda sparas bland parametrarna.

**Versionshistorik.**
* `groove-1` (före 2026-10-04) gav 180° minus den verkliga öppningsvinkeln.
* `groove-2` (2026-10-04) rättade vinkeln, men anpassade väggarna över hela höjden, mätte bredden mellan
  spårkanterna och tog med hela snittet genom nätet. På smala spår blev vinkeln ca 10° för stor.
* `groove-3` (2026-10-04): väggband 20–80 %, bredd vid stenytan och fönster runt mätpunkten.
  Mätningar med äldre versioner är inte direkt jämförbara och bör göras om.
* `groove-4` (2026-10-06): fönstren räknades i punkter i stället för millimeter, så måtten berodde på
  skanningens punkttäthet. Profilen räknas nu om till jämnt punktavstånd och alla fönster anges i mm;
  spårkanten måste ligga minst halvvägs upp mot stenytan. Jämförelser mellan stenar med olika punkttäthet
  gjorda med äldre versioner bör göras om.
* `groove-5` (2026-10-10): den automatiska analysen mäter bara spår som känns igen som runor (avsnitt 1c,
  steg 5), och bara små hål (< 10 mm²) i spårmasken fylls. Förut fylldes alla hål, så att ett slingband
  som stängs av runstavar – eller insidan av en runas båge – blev en enda yta som räknades som för bred
  och inte mättes (på Sö 113 65 700 mm² mot nu 1 900 mm²). Själva tvärsnittsmätningen är oförändrad från
  `groove-4`; mätningar med ett klick eller manuellt är jämförbara, automatiska analyser bör göras om.

### 1b. Ett klick per snitt

Källkod: `src/auto_grooves.py` (`auto_slice`). Användaren klickar en gång i ett spår.

1. Punkterna inom 15 mm runt klicket ger en lokal ytnormal (minsta variansriktningen), orienterad utåt med
   den klickade ytans normal. Normalen förfinas med lutningen hos en spårfri referensyta (avsnitt 1c, steg 2).
2. Ett lokalt höjdfält beräknas. Spårets riktning tas från höjdfältets Hessian (riktningen med minst
   krökning) på den skala (1–7,5 mm) där dalformen är tydligast (skalnormaliserad krökning).
3. Riktningen förfinas genom att spårets botten följs några millimeter åt båda hållen och en linje anpassas
   genom bottenpunkterna. Mätpunkten flyttas till botten.
4. Snitten mäts sedan exakt som i avsnitt 1. Hittas ingen dalform säger programmet till i stället för att mäta.

### 1c. Automatisk spåranalys

Källkod: `src/auto_grooves.py` (`analyze_grooves`). Användaren vrider den ristade sidan mot sig; kamerans
riktning blir ytans normal och kamerans upp-riktning orienterar granskningsbilden.

1. **Höjdfält:** alla hörn och triangelcentra projiceras på planet vinkelrätt mot normalen, i ett rutnät med
   skanningens medelkantlängd som upplösning (högst 6 miljoner celler). Den högsta punkten per cell väljs, så
   att baksidan inte kommer med.
2. **Referensyta:** morfologisk stängning (dilatation följd av erosion, 20 mm) fyller fördjupningar smalare
   än ca 20 mm men bevarar plana, lutande och svagt välvda ytor; en lätt gaussisk utjämning (1 mm) dämpar brus.
3. **Spår:** celler som ligger mer än `max(0,3 mm, k · brus)` under referensytan, där brus = 1,4826 · MAD av
   avvikelserna och k = 3 (känslighet "normal"). Partier inom 10 mm från skanningens kant, branta partier
   (> 45°) och små fläckar (< 10 mm²) utesluts. Små hål i spåren (< 10 mm², brus) fylls; större hål –
   t.ex. ett slingband mellan två stavar eller insidan av en runas båge – lämnas.
4. **Mittlinjer:** spåren tunnas ut till ett skelett. Punkter nära korsningar och ändar utesluts, liksom
   partier bredare än ett huggspår (standard 16 mm) – t.ex. sänkta fält eller avflagningar.
5. **Runor eller inte** (`classify_strokes`; standard, kan stängas av med `runes_only=false`). Naturliga
   sprickor, vittring och ornamentik har andra former än runor, och mäts de blir stenens medelvärden
   missvisande. Mittlinjerna delas därför i streck och bara streck som känns igen som runor mäts:
   * *Streck.* Mittlinjen bryts vid korsningar; en korsning räknas som hela området inom en halv spårbredd
     (median). Grenar som fortsätter i samma riktning (högst 25° ändring, högst en halv spårbredd i sidled)
     genom en korsning eller över ett avbrott på högst två spårbredder slås ihop till ett streck. En
     slingkant som runorna stöter emot blir då ett långt streck, medan runans stav och bistavar blir egna.
   * *Runstreck.* Rakt (avvikelse från rät linje ≤ max(2 mm, 4 % av längden), varje 10 mm-korda inom 20°
     från streckets riktning), 12–250 mm långt och jämnbrett (variationskoefficient för bredden ≤ 0,5).
   * *Ornamentik och slinglinjer.* Jämnt böjda streck; raka streck längre än 2,2 × 75:e percentilen av
     runstreckens längd (runorna i en inskrift är ungefär lika höga); raka bitar som fortsätter en sådan
     linje (spritt längs linjen); och streck som står vinkelrätt (± 20°) mot den tydligt dominerande
     riktningen bland runstrecken inom tre stavlängder och är minst en halv stavlängd långa – stavarna i en
     runrad är parallella och slinglinjerna går tvärs över dem, medan bistavarna sitter snett.
   * *Oregelbundna spår* (möjliga sprickor och vittring): kortare än 12 mm, ojämnt breda eller sicksackande
     (medianvridning mellan 5 mm-kordor > 25°, eller > 8° med växlande vridriktning i mer än 40 % av fallen –
     en ornamentbåge svänger åt samma håll, en spricka växlar).
   * *Runor.* Runstreck som sitter ihop är en runa. En runa godtas bara om en annan runa finns inom 2,5 × dess
     höjd (runor står i rader; ett ensamt rakt spår kan vara en spricka eller repa), och – på stenar med
     slinglinjer – om dess mitt ligger inom 0,75 × max(stavlängd, runans höjd) från en slinglinje (stavlängd =
     90:e percentilen av runstreckens längd), eftersom runorna står i banden.

   Varje snitt får strecktyp och runans nummer; snitt på andra streck redovisas som bortsorterade med skäl
   ("inte runa: …"). Igenkänningen är avsiktligt försiktig: det är bättre att en runa missas än att en
   spricka mäts. Missade runor kan mätas med ett klick (avsnitt 1b).

**Utvärdering mot facit** (`scripts/evaluate_rune_detection.py`). I 3D-vyns facit-läge mäts alla spår och inget
är förmärkt, så att programmets förslag inte styr bedömningen; forskaren märker punkterna som runa, ornamentik
(slinglinje eller ornament) eller utesluten (spricka, vittring) och sparar ett facit med positioner och märkning.
Skriptet läser in skanningen som appen gör, kör analysen på nytt med facitets parametrar, parar varje facitpunkt
med närmaste snitt (högst 2 mm) och redovisar precision (andel mätta streck som är runor), träffsäkerhet (andel
runor som hittas) och F1, med stenarna som reglerna justerades på (Sö 113, Sö 128) redovisade för sig. Eftersom
facitet bara innehåller positioner kan samma facit användas när reglerna ändras. Kedjan är prövad på en syntetisk
sten med känd geometri (precision 1,0, träffsäkerhet > 0,95); några handmärkta facit finns ännu inte.

**Jämförelse med Rundata.** Antalet igenkända runor på 19 skanningar ur Södermanlandsserien var i median 0,9 gånger
antalet runor i Rundatas translitterering (Spearman 0,58), men 0,3–1,5 på enskilda stenar: grunda, vittrade runor
faller sönder och sorteras bort (Sö 160, Sö 206), och korsarmar eller slinglinjer som brutits av vittring kan tas
för runor (Sö 143); på Sö 371, utan läsbara runor i Rundata, hittades sex. En igenkänd "runa" är en grupp
sammanhängande runstreck, så antalet är bara ett grovt mått.

**Mätning utan manuellt urval.** Tidigare 3D-studier av huggteknik (Kitzler Åhfeldt 2002 och senare) mäter
också i 3D-modeller med programvara (Groove Measure), men forskaren väljer vilka spår som mäts och var proverna
tas – oftast de bäst bevarade spåren. Den automatiska analysen tar i stället med alla igenkända runor, med samma
regler och parametrar på varje sten. Urvalet beror alltså inte på vem som mäter och kan upprepas exakt av vem
som helst med samma skanning och metodversion. Det tar bort variationen mellan bedömare men inte all systematik:
reglerna är själva val, gjorda av utvecklarna och dokumenterade här, och de kan slå olika på olika bergarter
och vittringsgrader, och att alla runor tas med ger mer vittringsbrus än ett urval av välbevarade spår. Fördelen
är att felen är desamma för alla stenar och går att granska och rätta – inte att de saknas (se avsnitt 18).
6. **Mätning:** med jämna mellanrum (standard 3 mm) längs mittlinjerna tas riktningen från mittlinjen och
   förfinas genom att botten följs (som i 1b). Tvärsnittet mäts **genom mesh-filen** med samma metod som i
   avsnitt 1 – höjdfältet används bara för att hitta spåren.
7. **Kvalitetsgranskning:** snitt sorteras bort vid orimlig vinkel (≤ 15° eller ≥ 170°), väggpassning
   R² < 0,8, djup under tröskeln, ej funnen spårkant eller botten utanför mittlinjen. Skälen redovisas.
8. **Granskning:** forskaren ser alla mätpunkter på en reliefbild – godkända runsnitt är förvalda som runor –
   kan märka om eller utesluta områden, och väljer vilket urval som blir resultatet.

**Validering.** På de syntetiska stenarna ger den automatiska analysen samma noggrannhet som avsnitt 1
(t.ex. 70,0 ± 0,9° för spår på 70°, oberoende av hur stenen lutar). På skanningen av Sö 113 (6,1 miljoner
trianglar) godkändes ca 250 av 1 000 kandidatsnitt; ett klick på samma ställen gav i median 6° skillnad i
vinkel och 10° i spårriktning, vilket speglar hur oregelbundna verkliga, vittrade spår är. Resultaten bör
därför redovisas med spridning och, för jämförelser, med samma mätsätt för alla stenar.

Runigenkänningen prövas på en syntetisk runslinga (sex runor mellan två slingkanter, en ornamentbåge och
en sicksackande spricka): alla sex runor och bara de mäts (80,8° för spår på 80°), slingkanterna och bågen
blir ornamentik och sprickan oregelbunden (`tests/test_auto_grooves.py`). På Sö 113 och Sö 128 granskades
klassningen visuellt: slinglinjerna mellan raderna och i slingorna sorteras bort, liksom raka vittringsspår
i Sö 128:s mittfält; de som mäts är nästan bara stavar och bistavar. Svagt böjda eller avbrutna stavar
missas ibland. Igenkänningen är regelbaserad och inte validerad mot en handmärkt referens.

### 1d. Bilder ur skanningen

Källkod: `api/routers/threed.py` (`render_relief`), `src/stone_report.py` (`Surface`). Bilder för läsning,
2D-analys och rapporter räknas direkt ur skanningen i stället för att fotografera skärmen:

* Ytan projiceras till ett höjdfält från den sida som vetter mot betraktaren i 3D-vyn (kamerans riktning och
  upp-riktning). Utan vy används stenens tunnaste riktning (minsta variansriktningen), vänd mot den sida där
  mest yta pekar.
* **Strykljus** från fyra riktningar (nordväst, nordost, sydost, sydväst) 20° över ytan.
* **Relief**: det mörkaste av de fyra strykljusen, så att varje spår blir mörkt oavsett riktning.
* **Djup** under en rekonstruerad stenyta (morfologisk stängning, 20 mm); kantzonen (10 mm), där
  referensytan är osäker, utelämnas.
* Bilderna har känd upplösning (mm per pixel) och påverkas inte av zoom eller skärmens belysning. Små
  skanningar skalas upp till minst 1 200 px för läsning.

### 1e. Robusthet

Källkod: `scripts/groove_robustness.py`, resultat i `utdata/groove_robustness/`. Åtta skanningar ur Kitzler Åhfeldts
Södermanlandsserie (Sö 113, 128, 134, 143, 161, 207, 319, Fv1948;282) mättes nio gånger: som standard (0,6 mm
rutnät, känslighet 3) och med rutnät 0,4 och 0,8 mm, ytnormalen lutad 5° åt två håll, känslighet 2,5 och 3,5,
och skanningen förenklad till hälften och en fjärdedel av trianglarna (som en glesare skanner).

| Ändring | Stenens V-vinkel, median (största) | Antal runor | Återkommande mätpunkter | Samma ställe: vinkel, djup |
|---|---|---|---|---|
| Rutnät 0,4 / 0,8 mm | 0,7° (2,8°) / 0,8° (3,3°) | −3 % / −15 % | 60 % / 73 % | 2,1° / 2,3°; 0,07–0,08 mm |
| Normal lutad 5° | 0,8–1,2° (4,8°) | −6 % till +10 % | 56 % | 2,3–2,6°; 0,17–0,37 mm |
| Känslighet 2,5 / 3,5 | 2,8° (4,9°) / 0,9° (3,0°) | +1 % / −6 % | 64–65 % | 1,8–2,0°; 0,07 mm |
| Hälften / en fjärdedel av trianglarna | 0,9° (4,2°) / 2,8° (9,1°) | −4 % / −12 % | 70 % / 43 % | 2,0° / 4,0°; 0,07–0,14 mm |

Stenens medelvärden (runan som enhet) stämmer väl överens över alla nio villkor: ICC(A,1) 0,98 för V-vinkel och
djup/bredd, 0,97 för djup, 0,95 för bredd och 0,93 för bottenradie; spridningen över villkoren är 13–19 % av
spridningen mellan stenar. Asymmetrin stämmer dåligt (ICC 0,40; 40 %). Vilka ställen som mäts ändras däremot
mycket (43–73 % av punkterna återkommer), och samma ställe skiljer i median ca 2° i vinkel – stenens resultat är
stabilt för att det är ett medelvärde över många runor, inte för att varje snitt är det. Djupet beror på
ytnormalen (0,37 mm på samma ställe vid 5° lutning) och glesa skanningar (en fjärdedel av trianglarna) ger
tydligt sämre resultat. **För jämförelser mellan stenar ska därför samma rutnät och känslighet användas, och
skanningar med mycket olika punkttäthet jämföras med försiktighet.** Studien är inte ett test–omtest med
oberoende skanningar av samma sten.

## 2. Osäkerhet

Källkod: `src/stats.py`. För varje mått och sten redovisas medelvärde, standardavvikelse (n − 1),
antal snitt och 95 % konfidensintervall (t-fördelning). Spridningen mellan snitt säger hur stabilt måttet
är längs spåret – den fångar inte systematiska fel som skanningsupplösning eller vittring.

**Runan som enhet** (`summarize_by_rune`). Snitt i samma runa är inte oberoende – de delar slag, verktyg
och vittring – så ett konfidensintervall över alla snitt blir för smalt. När bara runor mäts redovisas
därför också stenens medelvärde av runornas medelvärden, med n = antal runor, konfidensintervall
(t-fördelning) och ICC(1) (andelen av spridningen som ligger mellan runor).

**Hur många runor?** (`scripts/rune_sample_size.py`). Den automatiska analysen kördes på 20 skanningar ur
Kitzler Åhfeldts Södermanlandsserie (0,6 mm rutnät, känslighet 3); 18 stenar fick minst 8 mätta runor (8–76,
median 6 snitt per runa). Spridningen delades i tre nivåer (envägs-ANOVA per sten):

| Mått | SD inom runa | SD mellan runor | ICC | SD mellan stenar |
|---|---|---|---|---|
| V-vinkel | 10,0° | 8,1° | 0,37 | 12,6° |
| Spårdjup | 0,62 mm | 0,73 mm | 0,49 | 0,99 mm |
| Spårbredd | 2,4 mm | 1,9 mm | 0,35 | 2,5 mm |
| Djup/bredd | 0,052 | 0,050 | 0,44 | 0,070 |
| Asymmetri | 6,4° | 3,4° | 0,14 | 2,4° |

Spridningen mellan runor är lika stor som inom en runa, så fler runor ger mer än fler snitt per runa.
95 % konfidensintervall för stenens V-vinkel: ± 11° med 5 runor, ± 6,5° med 10, ± 4,2° med 20 och ± 3,4° med
30 (spårdjup ± 0,96, 0,55, 0,36 och 0,29 mm). Med 20 runor per sten upptäcks en skillnad på en
SD mellan runor (ca 8° i vinkel, 0,7 mm i djup) mellan två stenar med 80 % styrka (α = 0,05). Utifrån n
slumpvis valda runor kändes en sten igen bland de 18 i 52 % av försöken med 5 runor, 63 % med 10 och 75 %
med 20 (jämfört mot medelvärdet av stenens andra hälft av runor). Asymmetrin är för osäker för att skilja
stenar åt (ICC 0,14; 30 runor ger tillförlitlighet 0,9).

Appen anger därför **minst 10 runor för att beskriva en sten och minst 20 för att jämföra stenar**; 5 räcker
inte. Gränserna gäller stenar med olika ristare *och* olika material; skillnaden mellan två ristare på samma
bergart är mindre (avsnitt 15 och replikationsstudien av Kitzler Åhfeldts grupper), så för attribuering
behövs fler – helst alla mätbara runor.

## 3. Jämförelse av två stenar

* **Per mått:** tvåsidigt permutationstest av skillnaden i medelvärde (5 000 permutationer, fast slumpfrö),
  Bonferroni-justerat för antalet mått, samt Cohens d.
* **Alla mått samtidigt:** permutationstest av avståndet mellan stenarnas standardiserade medelvektorer.
* Tolkning: p < 0,05 talar emot samma verktyg/hand; p ≥ 0,05 är *förenligt med* samma hand men bevisar den inte.
  Runor och ornamentik bör jämföras var för sig, eftersom de ofta huggs olika.

## 4. Attribuering mot mätkorpusen

* Referensen är den delade korpusen (Firestore, CC BY 4.0). En stens ristare hämtas från Rundata och används
  bara om exakt **en säker signerad (S) eller attribuerad (A)** ristare anges. Stenen själv utesluts alltid.
* Måtten standardiseras; avståndet till varje ristares centroid är Mahalanobisavståndet med poolad
  inomgruppskovarians, krympt 20 % mot en diagonal (stabilt med få stenar).
* Ristare med färre än två uppmätta stenar tas inte med. Med för lite data avstår programmet och säger det.
* **Träffsäkerheten redovisas alltid** med lämna-en-ute-korsvalidering (andel stenar där rätt ristare hamnar
  först respektive bland de tre första, jämfört med slumpnivån).

### 4b. Vad som lagras i korpusen

* Varje post har mått per snitt, sammanfattning, proveniens (filens SHA-256, parametrar, metodversion) och
  valfritt **skanningsmetadata** (utrustning, upplösning, noggrannhet, datum, skannat av, länk/DOI, licens) och
  **stenens skick** (vittring, lav, ommålning).
* **Råa tvärsnittsprofiler** (x/z i mm, fyra decimaler) kan bifogas. De lagras i delar under
  `corpus/{id}/raw` och gör att en post kan **räknas om med en senare metodversion**
  (`POST /api/stats/recompute`). Omräkning av de lagrade profilerna återger de ursprungliga vinklarna inom
  0,01°. Bara bidragsgivaren kan ersätta sina mått med omräknade.
* **Runformer** från 2D-analysen (normaliserad form och särdragsvektor, se avsnitt 11) kan bifogas under
  `corpus/{id}/runeforms`, med spårmått för runan om den markerats på en ristningskarta från 3D-analysen.
* Andra forskare kan lägga till en **verifiering** (namn, institution, kommentar); den egna posten kan inte
  verifieras av bidragsgivaren. Kvalitetsmärken visar råprofiler, skanningsuppgifter, minst fem snitt, aktuell
  metodversion och verifiering.
* Korpusen kan exporteras som ett **datapaket** (JSON med licens, citering, bidragsgivare och alla poster,
  valfritt med råprofiler) för arkivering.

## 5. Klustring

Hierarkisk klustring med Wards metod och euklidiska avstånd på standardiserade medelvärden per sten –
samma upplägg som i Kitzler Åhfeldts analyser av huggteknik (se avsnitt 15).

## 6. Ortografisk stilometri

Källkod: `src/orthography.py`. Underlag: Rundatas vikingatida inskrifter med minst fem läsbara ord (1 719 st).

* **Särdrag:** tecken-2- och 3-gram i läsbara ord (TF-IDF), skiljeteckentyper och -täthet, andel bindrunor.
  Skadade ord (med `-` eller `...`) räknas inte.
* **Egennamn tas bort** (ord som normaliseras som namn i Rundata), så att ristarens signatur ("bali risti")
  inte avslöjar svaret och beställarnamn inte styr resultatet.
* **Likhet:** cosinuslikhet. **Ristarrangordning:** närmaste centroid bland ristare med minst fem säkra
  inskrifter.
* **Vad "likhet" betyder:** cosinuslikheten (0–1) mellan inskriftens särdragsvektor (TF-IDF, normerad) och
  ristarens medelvektor. Det är ett deskriptivt mått, inte en sannolikhet. Rangordningen är en
  närmaste-centroid-klassificerare.
* **Signifikans för likheten:** p = andelen av andra ristares säkra inskrifter som är minst lika lika
  ristarens profil (empirisk nollfördelning, (k + 1)/(n + 1)). Eftersom den mest lika av alla ristare väljs
  anges även p justerat för antalet ristare (Bonferroni). Dessutom anges hur typisk likheten är för
  ristarens egna inskrifter (lämna-en-ute). Formelspråket gör många inskrifter lika: även signerade stenar
  får sällan justerat p under 0,05, så en enskild likhet är ett svagt belägg. Metodens samlade
  träffsäkerhet (nedan) är det bättre måttet.
* **Utvärdering** (lämna-en-ute, 27 ristare, 459 inskrifter, Rundata 2014): rätt ristare först i 61 %,
  bland de tre första i 71 %; för enbart signerade inskrifter (n = 135) först i 60 %. Slumpnivå 4 %.
  Attribuerade inskrifter kan ha attribuerats just på grund av ortografin, därför redovisas siffran för
  signerade separat.
* **Godtycklig text:** samma modell kan rangordna ristare för en text utanför Rundata, t.ex. appens egen
  läsning eller ett nyfynd (`rank_text`). Egennamn tas bort via normaliseringen eller via namnformer kända
  från Rundata, och en sten som finns i modellen utesluts ur sin egen ristares profil.

## 7. Språk och läsning

Källkod: `api/routers/phonetics.py`, `src/reading.py`.

* **Blind läsning:** en språkmodell läser runorna från bilden utan att få signumet (steg 1). Även tolkningen
  (steg 2: normalisering till runsvenska, översättning, IPA, ljudlagar) görs utan signum, eftersom modellen
  annars återger den publicerade läsningen ur minnet i stället för det som syns på bilden. Translitterationen
  i resultatet är alltid den blinda läsningen.
* **Jämförelse med Rundata (utan AI):** translitterationerna jämförs ord för ord och runa för runa
  (difflib). *Överensstämmelse* = andelen av våra runor och ord som finns i Rundatas läsning, *täckning* =
  andelen av Rundatas text som vår läsning omfattar (en beskuren bild kan stämma helt men täcka lite). Bara
  sammanhängande träffar på minst tre runor räknas, skiljetecken och textkritiska tecken ignoreras och
  Rundatas oläsliga tecken redovisas separat.
* **Ordformer:** varje form i vår normalisering slås upp bland Rundatas normaliserade former i
  vikingatida inskrifter; obelagda former flaggas för granskning.
* **Ortografi för vår läsning:** samma modell som i avsnitt 6, med stenen själv utesluten. Används i
  syntesen när Rundata saknar en användbar text (t.ex. nyfynd), med 30 % lägre tillförlitlighet.
* **Validering – får läsningen visas som stenens text?** (`src/reading.py`, `validate`): läsningen prövas utan AI
  mot (1) stenens text i Rundata, (2) alla kända inskrifter i Rundata (trigramfilter och samma
  överensstämmelsemått) och (3) andra läsningar av samma bild. Status: *bekräftad* (≥ 80 % av runorna i stenens
  läsning), *delvis* (50–80 %), *ej bekräftad* (< 50 %), *annan inskrift* (liknar en annan känd inskrift minst
  60 % och tydligt mer än stenens egen – modellen har troligen återgett en inlärd text) eller *ej prövbar* (Rundata
  saknar text; då krävs att flera läsningar stämmer minst 80 % med varandra). Bara bekräftade, delvis bekräftade
  och samstämmiga läsningar visas som läsning, med normalisering och översättning, och bara de används som
  belägg i syntesen. I rapporter redovisas en obekräftad läsning aldrig som stenens text.
* **Erfarenhet:** i testet med Sö 113 gav tre blinda läsningar tre olika, trovärdiga men påhittade texter (6–24 %
  av runorna stämde), en av dem Jellingestenens text (DR 42, 95 % lika). Språkmodeller kan alltså inte läsa runor
  tillförlitligt; reliefbilderna är ett bättre underlag för en mänsklig läsning.
* Läsningen kan rättas för hand och jämföras igen; den märks då som rättad.
* **Bilder att läsa:** foto, 2D-analysens bild, RTI-vy eller reliefbilder ur 3D-skanningen (strykljus från
  fyra riktningar, ett kombinerat relief där varje spår blir mörkt oavsett riktning, och djup under
  stenytan), räknade från den sida som vetter mot betraktaren i 3D-vyn.
* **Uppläsning:** en modern talsyntes läser normaliseringen. Det är inte en rekonstruktion av uttalet;
  IPA-raden är modellens förslag och ljudlagarna är inte kontrollerade.

## 8. Språkdrag (fonetisk stil och språkbruk)

Källkod: `src/language_profile.py`, `GET /api/research/language/{signum}`. Dragen läses ur Rundata genom
att translitterationen paras ord för ord med normaliseringen:

| Grupp | Drag | Definition |
|---|---|---|
| Ljud | Diftongen ai i *sten* | stæinn skrivet ai/ia (bevarad) eller i/e (monoftongerad) |
| Ljud | Diftongen au i *och* | ok skrivet auk eller uk/ok/ak |
| Ljud | Nasal före konsonant | n/m utskrivet eller utelämnat (bonta mot buta, kumbl mot kubl) |
| Ljud | h-bortfall | h i hans, hialpi skrivet eller inte |
| Ljud | Stungna runor | e, g, d, y används |
| Bruk | *efter* | första vokal och slut i æftiR |
| Bruk | *denna* | þina, þino, þana, þena |
| Bruk | Kristen bön, själsbön | Guð hialpi …, and/sálu |
| Bruk | Ristarsignatur | risti, hjó, markaði … |
| Bruk | *runor* | runaR, runa, runar |

Ett drag räknas bara där inskriften har ordet. Ristarens profil är fördelningen över dennes säkra
inskrifter (stenen själv utesluten). Stenen stämmer i ett drag när värdet är ristarens vanligaste eller
förekommer i minst hälften av ristarens inskrifter med ordet. Dragen påverkas också av dialekt, tid och
beställare. De redovisas som kontroll och vägs inte in i kandidaternas poäng, eftersom stavningsdragen
delvis överlappar den ortografiska jämförelsen.

## 9. Inskrifternas syfte per ristare

Källkod: `src/inscription_types.py`, `GET /api/research/categories`. Varje vikingatida runsten med text
får en eller flera kategorier med regler på Rundatas normalisering, engelska översättning och
translitterering: minnesinskrift, självminne, bro- och vägbygge, kristen bön eller formel, utlandsfärd,
arv och ägande, ting och offentlighet, magisk eller rituell (Þórr vígi, vígi þessi kuml, siði Þórr,
förbannelser, futharkrader, alu) och gränsmärke. Gränsmärken finns i praktiken inte bland de svenska
runstenarna i Rundata; där översätts *merki* (minnesmärke) med "landmark", vilket inte är en gräns.

För ristare med minst fem säkra inskrifter testas varje kategori mot genomsnittet (tvåsidigt
binomialtest, Benjamini–Hochberg-justerat q). När en ristare saknar en kategori anges sannolikheten för 0
av en slump, (1 − basnivå)^n. För sällsynta typer (magiska inskrifter 0,5 %) är 0 därför väntat även för
ristare med många stenar. I syntesen flaggas en stens typ bara när ristarens frånvaro är osannolik
(sannolikhet för 0 under 5 %).

### 9b. Stenens storlek och syfte

Källkod: `src/stone_dimensions.py`, `scripts/build_stone_dimensions.py`, `src/stone_size.py`,
`GET /api/research/stone_size`; fliken *Storlek och syfte* i Forskningsluckor.

**Mått.** Rundata saknar mått. Runor (RAÄ, utgåva 2020) ger för varje inskrift id:t i Kulturmiljöregistret, och
lämningens beskrivning där – hämtad via K-samsök, CC0 – anger oftast mått, t.ex. "1,5 m h, 0,5-0,6 m br och
0,2-0,25 m tj. Runhöjd 6-8 cm". Höjd, bredd, tjocklek och runhöjd läses ut med reguljära uttryck (intervall ger
mittvärdet; värden utanför 0,05–6 m räknas som tolkningsfel). Beskriver lämningen flera föremål ("1) … 2) …")
används bara delen som nämner stenens signum, eller den enda delen som är en runsten; annars räknas måtten som
oklara. Fragment markeras och utesluts ur analysen. Av 2 321 vikingatida runstenar fick 1 384 mått (1 101 med höjd,
utan fragment); 395 saknar id i registret, 350 har en beskrivning utan mått och 192 kunde inte skiljas från andra
stenar i samma lämning (bygge 2026-10-10, `data/stone_dimensions.json`). Höjden är oftast höjden över mark.

**Analys.** Hypotesen är att stora stenar restes för större syften och av mäktigare personer. Höjden (logaritmisk
skala) jämförs med inskriftens syfte (avsnitt 9), med statusord i normaliseringen (þegn/þiagn, dræng-, styrimann,
skipari, kunung-, goði, landmann), med antalet namngivna personer (Rundata markerar namn med citattecken), med
textens längd och med ristare (minst tio stenar). Bergart och lokal sed påverkar storleken, så allt jämförs
**inom landskap**: skillnaden i medel-log-höjd viktas över landskapen och prövas med 5 000 permutationer av
etiketterna inom landskap (Benjamini–Hochberg över testen); korrelationer räknas på rangordning inom landskap,
med samma permutation. Antalet personer redovisas också med textens längd bortrensad (partiell rangkorrelation),
eftersom en stor sten har plats för en längre text.

**Resultat (2026-10-10, 1 101 stenar, median 1,6 m).** Minnesinskrifter är 24 % högre än övriga i samma landskap
(q 0,004) – men inskrifter där minnesformeln inte går att läsa är oftare skadade och därför lägre, så skillnaden
kan vara skenbar. Stenar med statusord är 19 % *lägre* (75 stenar, q 0,02), tvärt emot hypotesen; ordens
betydelse (t.ex. *drengr* som ung krigare) är omdiskuterad. Bro- och vägbygge, kristen bön, självminne,
utlandsfärd, arv och ting skiljer sig inte (q ≥ 0,47). Större stenar har fler namngivna personer (rho 0,26) och
längre text (rho 0,30), men med textens längd bortrensad är sambandet med antalet personer svagt (rho 0,06,
p 0,06). Åsmunds stenar är 30 % högre än andras i samma landskap (p 0,03) men inte efter korrektion för antalet
ristare (q 0,31). Runhöjden följer stenens höjd (rho 0,22), vilket talar för att måtten är rimliga.
Slutsatsen är att textens innehåll förklarar lite av stenens storlek; andra tecken på makt (läge, monument med
flera stenar, ornamentikens kvalitet) är inte mätta.

## 10. Bergart och berggrund

Källkod: `src/geology.py`, `GET /api/research/geology/{signum}`.

* Stenens material i Rundata (fältbenämningar som "röd granit", "gråsten", "kalksten") förs till
  bergartsfamiljer (granit och närstående, gnejs och migmatit, sandsten, kalksten och marmor, basiska,
  vulkaniska, kvartsit, metasediment). "Gråsten" räknas till både granit och gnejs.
* Berggrunden hämtas ur SGU:s berggrundskarta 1:50 000–1:250 000 (WMS GetFeatureInfo) på platsen och i
  ett rutnät med 2,5 km mellanrum inom 10 km (49 provpunkter). Svaren cachas.
* Utfall: samma familj **på platsen**, **i närheten** (andel provpunkter), **inte i närheten** eller okänt.
* Källkritik: runstenar är ofta flyttblock eller transporterade (t.ex. Öl 1 av smålandsporfyr på Ölands
  sand- och kalksten). En avvikelse är en ledtråd om stenens ursprung, inte ett fel. Kartan täcker bara
  Sverige.
* I syntesen och Forskningsluckor jämförs även stenens bergart med bergarterna på ristarens säkra stenar.

## 11. 2D-analys och runformer

* AI-bedömningen av en bild (stilgrupp Pr1–Pr5, RAK, Fp eller **Osäker**, runformer, translitterering) är en
  hypotes. Modellens säkerhet är dess egen skattning och **inte kalibrerad**. Om stenen har en stilgrupp i
  Rundata visas den bredvid, och syntesen redovisar om AI:n och Rundata är överens.
* **Runformer** (`src/graphemes.py`, särdragsversion `grapheme-2`): utsnittet kontrastförstärks (CLAHE),
  binäriseras (Otsu; minoritetsklassen räknas som ristning), beskärs till ristningen och läggs i en kvadrat
  med bibehållna proportioner, 64 × 64 px. Särdrag: HOG, täthet i 4 × 4 zoner och logaritmerat
  höjd/bredd-förhållande. Likhet: cosinus.
* **Validering:** på syntetiskt ritade runor (ᛁ ᛏ ᚴ ᚱ ᛋ med slumpad stavtjocklek, lutning och brus,
  `src/synthetic_runes.py`) hamnar närmaste granne på rätt runa i 85 % av fallen. Den tidigare metoden låg
  på slumpnivå. Resultatet är ett mått på **formlikhet**, inte på samma ristare; på riktiga stenar påverkas
  det av vittring, belysning och utsnittets noggrannhet.
* Jämförelser görs bara mellan utsnitt med samma särdragsversion och, om angivet, samma runtyp
  (långkvist, kortkvist, stungen m.fl.).
* Bilder kan komma från uppladdning, K-samsök, en reliefbild räknad ur 3D-skanningen, RTI-visaren eller
  **ristningskartan** från den automatiska spåranalysen (residualdjup, djupt = mörkt). Ristningskartan har
  samma pixelkoordinater som analysens granskningsbild, så ett runutsnitt där kopplas till de uppmätta
  snitten inom utsnittet.

## 12. Syntes och attribuering

Källkod: `src/synthesis.py`, `api/routers/synthesis.py`. Kandidaterna räknas fram deterministiskt:

| Källa | Vikt |
|---|---|
| Rundata: signerad (S) | 4 (2 om osäker) |
| Rundata: attribuerad (A) | 2 (1 om osäker) |
| Rundata: parsten/liknar (P/L) | 1 |
| Ortografi plats 1 / 2–3 | 2 / 1 × tillförlitlighet |
| Huggteknik plats 1 / 2–3 | 2 / 1 × tillförlitlighet |

* **Ortografins tillförlitlighet** = modellens precision för den föreslagna ristaren (korsvaliderad,
  Laplace-utjämnad: (rätt + 1)/(förslag + 2)) × 0,5 om stenen ligger utanför ristarens kända landskap ×
  textlängd (1 vid ≥ 12 läsbara ord, 0,7 vid 8–11). Texter under 8 ord vägs inte in.
* **Huggteknikens tillförlitlighet** = korsvaliderad träffsäkerhet över slumpnivån,
  (träff − slump)/(1 − slump). Är metoden inte bättre än slumpen vägs den inte in. Jämförelsen görs med
  den valda analysen (runor som standard), mot stenar med samma spårtyp och säker ristare; stenen själv
  ingår aldrig i referensen.

Styrka: **stark** = summa ≥ 4 eller ≥ 3 från tre källor; **måttlig** = ≥ 2,5 eller ≥ 1,5 från två källor;
annars **svag**. Inga procentsatser anges.

De tre främsta kandidaterna prövas dessutom mot:

* **litteraturen** – stämmer, nytt (Rundata saknar ristare) eller motsäger,
* **geografi** – avstånd till ristarens närmaste säkra sten och ristarens kända landskap,
* **stilgrupper** – stilgrupperna på ristarens säkra stenar och den datering de motsvarar enligt Gräslund;
  avviker stenens stilgrupp flaggas det,
* **sten mot sten** – permutationstest av alla mått samtidigt mot var och en av kandidatens uppmätta
  stenar (upp till fem, 1 000 permutationer).

Motsägelser mellan källorna (t.ex. Rundata mot ortografi, ortografi mot huggteknik, geografi eller
stilgrupp som inte passar) och belägg som saknas redovisas uttryckligen. Utfallet mot litteraturen räknar
bara en oberoende källa som stöd när kandidaten kommer först där. AI-modellen (Claude som standard, Gemini som alternativ) får beläggen som
underlag och skriver bara löptext; utan AI ersätts texterna av framräknade formuleringar. Syntesen kan
sparas i projektet och blir då avsnittet "Attribuering" i stenrapporten.

**Verktygsklassning** (pik-/bredmejsel, tröskel 85°, +5° vid hög vittring, +2° vid måttlig vittring, +2° för
sandsten/kalksten) är en tumregel som inte är kalibrerad mot referensmaterial och redovisas som sådan.

Ytterligare kontroller för de tre främsta kandidaterna (redovisas, men vägs inte in i poängen):

* **bergart** – stenens material jämfört med bergarterna på ristarens säkra stenar (avsnitt 10),
* **språkdrag** – fonetisk stil och språkbruk jämfört med ristarens inskrifter (avsnitt 8),
* **inskriftstyp** – stenens kategorier jämfört med ristarens; frånvaro flaggas bara när den är osannolik
  (avsnitt 9),
* **berggrund på platsen** (SGU) för stenen som helhet (avsnitt 10).

Har projektet en egen läsning från Språk & Fonetik används den som ortografiskt belägg när Rundata saknar
användbar text, med 30 % lägre tillförlitlighet, och läsningens överensstämmelse med Rundata redovisas.

## 13. Forskningsluckor

Källkod: `src/research_gaps.py`. Underlag: Rundatas svenska vikingatida runstenar (2 321).

* **Täckning** per landskap: andel med ristare, säker stilgrupp, datering, osäker tolkning, försvunna stenar
  och stenar i mätkorpusen. Ristaruppgifterna för Sö, U, Vs och Gs bygger främst på Axelson (1993); i andra
  landskap kan attribueringar finnas i litteraturen utan att stå i Rundata.
* **Ortografiska hypoteser:** stenar utan ristare i Rundata vars stavning liknar en ristares profil
  (cosinus ≥ 0,6, marginal ≥ 0,05 till nästa, minst åtta läsbara ord). Förslagen rangordnas efter den
  ristarens korsvaliderade träffsäkerhet × likhet, och nedvärderas om stenen ligger utanför ristarens
  kända landskap. Det är förslag att pröva, inte attribueringar.
* **Att ompröva:** attribuerade stenar där ortografin pekar på en annan ristare.
* **Mätprioriteringar:** ristare med många inskrifter men få uppmätta stenar (mål: fem per ristare), så att
  attribueringen mot mätkorpusen får ett underlag.
* **Klickbara siffror:** varje tal i landskapstabellen och nyckeltalen leder till inskrifterna bakom det
  (sökfilter med samma definitioner som översikten, `GET /api/rundata/search?gap=…&province=…`).
* Ortografiska hypoteser visas med likhet, p-värde (avsnitt 6), precision, bergart och språkdrag.

### 13b. Våra resultat mot befintlig forskning

Källkod: `src/findings.py`, `POST /api/research/findings`. Appens resultat ställs mot Rundata, som får
representera den publicerade forskningen:

| Metod | Stämmer | Nytt | Motsäger |
|---|---|---|---|
| Ortografi (lämna-en-ute) | rätt ristare först | stark hypotes för sten utan ristare | attribuerad (A) ristare inte bland de tre första |
| Huggteknik (mätkorpusen, runor) | närmaste ristare = Rundatas | sten utan ristare får en närmaste ristare | närmaste ristare ≠ Rundatas |
| Stilgrupp (AI, bild) | samma som Rundata | Rundata saknar säker stilgrupp | annan stilgrupp |
| Statistisk modell (R, avsnitt 17) | stöder en osäker attribuering | förstaval ≥ 0,5 för sten utan ristare | korsvaliderat förstaval ≠ Rundatas (A) |
| Seriation (R, avsnitt 17) | – | sten utan stilgrupp bland de 15 % tidigaste eller senaste i Uppland | – |

Varje fynd får en **uppskattning** = belägg × nyhet × relevans (var och en 0–1, skälen redovisas):

* **Belägg**: ortografi – modellens korsvaliderade precision för den föreslagna ristaren, halverad utanför
  ristarens kända landskap, lägre för korta texter och liten marginal; huggteknik – korsvaliderad
  träffsäkerhet och avståndet till nästa ristare; AI-stilgrupp – högst 0,35 eftersom den är okalibrerad.
* **Nyhet**: bekräftelser lågt (0,05–0,3; en oberoende metod som huggteknik väger mer än ortografi,
  eftersom attribueringar kan bygga på ortografin), nya attribueringar högt (0,85 i Axelsons område,
  0,55–0,6 utanför, där attribueringar kan finnas i litteraturen utan att stå i Rundata), avvikelser mot
  attribuerade stenar 0,7 men mot signerade 0,05 – där talar avvikelsen mot metoden, inte mot ristaren.
* **Relevans**: andelen stenar med ristare i landskapet (lägre andel = större behov), ristarens antal
  säkra inskrifter, och om stenen finns kvar att undersöka.

Bedömningen ("Sannolikt ny och relevant kunskap", "Värd en omprövning", "Oberoende bekräftelse" m.fl.)
är en tumregel för att prioritera fortsatt arbete, inte en granskning av forskningsläget.

**Avstämning mot nyare källor** (`src/crosscheck.py`, `POST /api/r/crosscheck`). Appens Rundata är version 3.1
(2018). Nya och motsägande förslag (ortografi och statistisk modell) stäms av mot **Runor** (Riksantikvarieämbetet,
utgåva 2020 av samma databas, `runor.raa.se`) och **Wikidata** (skapare, P170, för objekt med Rundata-ID, P1261).
Runors hänvisningar av typen "Samma som gjort U 1015, 1017–1024" följs till de stenarna. Utfallet:
*finns redan* (förslaget står i den nyare källan – inte nytt, men en bekräftelse av metoden; nyheten sätts till
0,05), *nämns* (ristaren nämns i en anmärkning, t.ex. "Tidigare tolkad som signerad av Traen"), *annan ristare*,
*samma som* (samma namnlösa ristare som en annan sten) och *saknas*. Runors litteraturhänvisningar för stenen
visas så att de kan kontrolleras. Svaren cachas i `data/cache/crosscheck/`. Avstämningen ersätter inte en
genomgång av litteraturen: Runor 2020 har inte heller alla senare attribueringar.

**Mönster i korpusen** (avsnitt 17) visas överst i fliken: "bekräftar" när de stämmer med vad forskningen redan
utgår från, "mönster att pröva" när appen inte kan knyta dem till tid, geografi eller något den känner till ur
litteraturen (appen känner bara Rundata, Axelson 1993 och Gräslund 1998).

## 14. Rapporter

Två rapporttyper, båda manusutkast där tabeller och figurer räknas fram ur data och AI-text märks.

### 14a. Korpusrapport (flera stenar)

Källkod: `src/academic.py`, `POST /api/reports/academic`. Rapporten byggs för ett urval av korpusen (en
ristare, ett landskap, valda stenar eller hela korpusen):

* **Material, metod, tabeller och figurer räknas fram ur data**: medelvärden och spridning per mått, per
  sten och per ristare, figurer över V-vinkel och Ward-dendrogram, samt metodversioner och referenser.
* AI kan skriva **sammanfattning, inledning och diskussion**, men får bara en faktatext med de framräknade
  resultaten som underlag. Dessa avsnitt märks som AI-text. Utan AI-nyckel lämnas de för författaren att
  skriva.
* Export: Markdown, LaTeX (med figurfilerna) och Word (.docx). Rapporten är ett manusutkast som måste
  granskas innan den används.

### 14b. Stenrapport (en sten)

Källkod: `src/stone_report.py`, `POST /api/reports/stone`. Uppläggningen följer två traditioner:

* **Runologisk presentation** som i *Sveriges runinskrifter* och i stilmallen för *Futhark: International
  Journal of Runic Studies*: signum utskrivet i sin helhet och utan kursiv, translitterering i **fetstil**,
  normalisering (runsvenska och fornvästnordiska) i *kursiv*, översättning inom citattecken, ristare med S/A,
  stilgrupp (Gräslund), datering och hänvisning till stenens utgåva i SRI. Allt hämtas ur Rundata.
* **Arkeometrisk redovisning**: material och metod med 3D-dokumentationens paradata (skanner,
  upplösning, noggrannhet, vem som skannat, modellens kontrollsumma, licens), analysparametrar,
  kvalitetskontroll (godkända och underkända snitt med skäl), resultat, diskussion, källkritik, data och
  reproducerbarhet, samt en bilaga med varje tvärsnitts mått.

Figurerna räknas direkt ur 3D-modellen och snittens råprofiler (inget är retuscherat):

1. digitalt strykljus från fyra riktningar (20° över ytan),
2. djup under en rekonstruerad stenyta (morfologisk stängning, 20 mm; kantzonen utelämnad),
3. tvärsnittens positioner färgade efter V-vinkel, med bokstäver som hänvisar till profilfiguren,
4. spårdjup, spårbredd och ytråhet per tvärsnitt över ytan,
5. representativa tvärsnitt (från minsta till största vinkel) med anpassade spårväggar i lika skala,
6. alla tvärsnitt överlagrade med median och interkvartilområde,
7. måttens fördelningar, 8. samband mellan bredd, djup och vinkel,
9. runor mot ornamentik (permutationstest), 10. jämförelse med stenar med säker ristare i mätkorpusen,

och, om det finns, bilden och runformerna från 2D-analysen. Figurerna 1–4 kräver att skanningen finns i
analysmotorns minne (samma fil inläst i 3D-vyn); annars utelämnas de och rapporten säger det. Snittens
positioner och råprofiler sparas med varje analys (automatisk, ett klick per snitt och spårbana).

Stenrapporten får dessutom, när underlaget finns:

* **berggrunden på platsen** (SGU) i avsnittet om stenen,
* **Läsning av bilden** – appens blinda läsning som inskrift (fetstil/kursiv), jämförelsen med Rundata,
  skillnaderna ord för ord, kontrollen av ordformer och, märkta som AI, IPA och ljudlagar,
* **Attribuering** – den sparade syntesen: utfallet mot litteraturen, kandidattabellen, kontrollerna
  (geografi, stilgrupper, bergart, språkdrag, sten mot sten), motsägelser och saknade belägg.

### 14c. Fullständig stenanalys (arbetsgång)

Sidan **Stenanalys** och skriptet `scripts/full_stone_analysis.py` kör hela kedjan för en skanning och ett
signum, med samma beräkningar som de enskilda verktygen:

1. Uppladdning och **bilder ur skanningen** (avsnitt 1d). Den ristade sidan skattas som stenens tunnaste
   riktning; den andra sidan kan väljas.
2. **Automatisk spåranalys** med flera känsligheter (standard 3 och 5). Den första är huvudanalysen, de övriga
   en känslighetsanalys som redovisas med granskningsbilder.
3. **2D-bildanalys** av strykljuset från nordväst.
4. **Blind läsning** i en eller flera orienteringar (standard 0° och 180°), validerad mot Rundata, kända
   inskrifter och varandra (avsnitt 7).
5. **Syntes och attribuering** med berggrund (avsnitt 10 och 12); med inloggning även mot mätkorpusen.
6. **Forskningsläge och syfte** (`GET /api/research/stone/{signum}`): det Forskningsluckor vet om stenen
   (landskapets täckning, stenens luckor i Rundata, om den finns bland ortografiska hypoteser, omprövningar
   eller mätprioriteringar och hur appens resultat bedöms mot forskningen), inskriftens syfte (avsnitt 9) och,
   för de tre troligaste ristarna, hur ofta de ristade i stenens stilgrupp och inskriftstyp.
7. **Statistik i R** (avsnitt 17): startar korpusanalyserna om de saknas och ställer stenen mot dem –
   attribueringsmodellen, kandidaternas områden, gruppen i klustringen, formlerna, Upplands seriation och
   landskapet (höjdmodell, strand, sikt, vägar).
8. **Stenrapport** (14b), med avsnitten "Inskriftens syfte" och "Stenen i forskningsläget", R-avsnitten (metod 3.4,
   modellen i attribueringen, "Stenen i korpusen", "Stenen i landskapet"), en tabell över
   kandidaternas stilgrupper och inskriftstyper, bilaga A (alla tvärsnitt) och bilaga B: arbetsgångens steg och utfall,
   känslighetsanalysen, granskningsbilder, relief, 2D-motiveringen, alla läsningar med status och de fel
   eller begränsningar som uppstod.

Misslyckas ett AI-steg (ingen nyckel, slut på krediter, tidsgräns) fortsätter arbetsgången, och felet
redovisas i bilaga B. Resultatet kan sparas i ett projekt; bara en validerad läsning sparas som projektets
läsning.

Från terminalen (analysmotorn måste köras):

```bash
.venv/bin/python -m scripts.full_stone_analysis "skanning.stl" --signum "Sö 113" --out utdata/So113 \
    --stone Gråsten --weathering Medel --author "Namn" --sensitivity 3,5 --orientations 0,180
```

### 14d. Språkmodeller

Källkod: `api/llm.py`. Alla AI-anrop går genom ett gemensamt lager. Standard är **Claude** (Anthropic,
`claude-opus-5-5` för analys och text, `claude-haiku-4-5` för enkla uppgifter); **Gemini** kan väljas under
Inställningar. Strukturerade svar (t.ex. stilbedömning och läsning) begärs med ett schema – för Claude som
verktygsanrop (tool use), så att svaret alltid är giltig JSON. Valet av modell ändrar inget i det som räknas fram:
mätningar, statistik, jämförelser och valideringen av läsningar görs utan AI, och AI-text märks.

### 14e. Rapportmallar (publiceringsformer)

Källkod: `src/report_templates.py`, `GET /api/reports/templates`, `POST /api/reports/stone` med `template`.
Stenrapporten byggs först i sin fullständiga form; en mall väljer sedan ut, ordnar om och kompletterar dess avsnitt.
Siffror, tabeller och figurer är desamma – bara urval, ordning, rubriker och ton skiljer. Figurer och tabeller
numreras om efter urvalet, och hänvisningarna i texten rättas. Text som författaren ska skriva själv står inom
hakparentes ("[Fyll i: …]"); mallens fria texter kan formuleras av AI utifrån samma fakta och märks då som AI-text.

| Mall | Grupp | Innehåll |
|---|---|---|
| Stenrapport (fullständig) | Vetenskapligt | allt underlag och bilagor (avsnitt 14b) |
| Artikel i forskningstidskrift | Vetenskapligt | IMRaD, engelsk abstract, nyckelord, highlights där tidskriften kräver det, datatillgänglighet, bilagor som tilläggsmaterial; riktvärden för Futhark, Fornvännen, Viking and Medieval Scandinavia, Journal of Archaeological Science: Reports och Danish Journal of Archaeology |
| Uppsats (kandidat, magister, master) | Utbildning | titelsida, syfte och frågeställningar, avgränsningar, forskningsöversikt, teori och metod, material, resultat, diskussion, slutsatser, sammanfattning |
| Avhandlingskapitel (monografi) | Vetenskapligt | kapitelnumrerade avsnitt, metoden refererad till metodkapitlet, kapitelsammanfattning, data som appendix |
| Runologisk utgåva (SRI-stil) | Vetenskapligt | placering, material och mått, ornamentik, inskrift, kommentar, ristare och datering, huggteknik |
| Konferensabstract | Vetenskapligt | 200–300 ord och nyckelord, svenska eller engelska |
| Poster | Vetenskapligt | punkter om bakgrund, metod, resultat och slutsats, tre figurer |
| Blogginlägg | Populärt | ingress, korta stycken utan facktermer, bilder, osäkerhet, läs mer |
| Pressmeddelande | Populärt | rubrik, ingress, brödtext, citat, fakta, kontakt |
| Antikvarisk dokumentationsrapport | Kulturmiljö | administrativa uppgifter (fornlämningsnummer, fastighet, beställare, diarienummer), metod, resultat, bevarandetillstånd, rekommendationer, arkivering |
| Dataartikel / datapaket | Data | översikt, metod, filer och format, licens och förvaring, återanvändning (jfr Journal of Open Archaeology Data, README för Zenodo) |

Tidskrifternas riktvärden (språk, omfång, referensstil) är ungefärliga och ändras; gränssnittet påminner om att
kontrollera aktuella författaranvisningar. För Futhark finns dessutom ett färdigt manuspaket i tidskriftens mall
(`src/journal.py`).

## 15. Jämförbarhet med tidigare forskning

Laila Kitzler Åhfeldts metod (Arkeologiska forskningslaboratoriet, Stockholms universitet; Kitzler Åhfeldt
2002) mäter spårvariabler i högupplösta 3D-modeller med funktionen *Groove Measure* (DeskArtes), analyserar
runor och ornamentik separat, beskriver varje sten med medelvärden och använder bl.a. Wards klustring på
standardiserade variabler (t.ex. Kitzler Åhfeldt & Imer 2019, *Danish Journal of Archaeology* 8,
doi:10.7146/dja.v8i0.113226). Vitki följer samma upplägg (separata spårtyper, medelvärden per sten,
standardisering, Ward), men **måtten är inte verifierade som likvärdiga** med Groove Measure-variablerna.
Innan resultat jämförs direkt bör samma referensstenar mätas med båda metoderna.

## 16. Datakällor och licenser

* **Samnordisk runtextdatabas** (Institutionen för nordiska språk, Uppsala universitet), version 2014 med
  RUNDATA.xls från 2018. Open Database License (databasen) / Database Contents License (innehållet).
  Källan ska anges: www.nordiska.uu.se/forskn/samnord.htm. `data/rundata.json` är en härledd databas och
  omfattas av samma licens. Svenska koordinater (RT90 2,5 gon V) räknas om till WGS 84 med pyproj.
* **Stilgrupper:** Gräslund, A.-S. 1998. Ornamentiken som dateringsgrund för Upplands runstenar.
  I: *Innskrifter og datering / Dating inscriptions*. Trondheim, s. 73–91. Dateringarna är ungefärliga.
* **Mätkorpusen:** bidrag publiceras under CC BY 4.0 med bidragsgivaren angiven.
* **Kartor:** © OpenStreetMap-bidragsgivare.
* **Berggrund:** Sveriges geologiska undersökning (SGU), Berggrund 1:50 000–1:250 000 (visningstjänst,
  WMS). Svaren cachas lokalt i `data/cache/geology.json` (ingår inte i repot).
* **Vatten och land:** Natural Earth 1:10 miljoner (kustlinje, sjöar, vattendrag, de europeiska tilläggen och land),
  public domain. Hämtas en gång till `data/cache/r/naturalearth/`.
* **Höjddata:** Terrain Tiles (Tilezen/Mapzen, Registry of Open Data on AWS), zoomnivå 12. Hämtas per sten till
  `data/cache/r/terrain/`.
* **Runor** (Riksantikvarieämbetet), utgåva 2020 av Samnordisk runtextdatabas, och **Wikidata** (CC0), för
  avstämningen i 13b. Svaren cachas i `data/cache/crosscheck/`.

## 17. Statistik i R

Källkod: `r/` (R-skripten), `src/r_bridge.py` (export, körning, cache), `src/r_findings.py` (fynd och mönster),
`src/r_report.py` (rapportavsnitt), `api/routers/rstats.py` (`/api/r/…`). Sidan **Statistik (R)** visar
resultaten; stenanalysen och stenrapporten använder dem för den enskilda stenen.

**Underlag.** Alla svenska vikingatida runstenar i Rundata (2 321) exporteras till en CSV med plats, härad,
ristare (en säker ristare, annars tomt), stilgrupp och Gräslunds datering, kors, kortkvistrunor, de nio
innehållskategorierna (avsnitt 9), de elva språkdragen (avsnitt 8), läsbara ord och stavningsvarianter (ordform
parad med normaliseringen; egennamn utelämnade) och normaliseringen. Korpusanalyserna körs en gång per version
av data och skript (fingeravtryck) i en egen process (`python -m src.r_bridge <fingeravtryck>`) och sparas i
`data/cache/r/corpus/<fingeravtryck>/` med `sessionInfo()`. Varje modul körs som
`Rscript --vanilla r/<modul>.R params.json utmapp` och skriver JSON och figurer.

| Modul | Paket | Vad den gör |
|---|---|---|
| `geography.R` | sf, leaflet | ristarnas tyngdpunkter, spridning och konvexa höljen (SWEREF 99 TM); permutationstest (499 urval ur samma landskap) av om ristaren arbetade inom ett mindre område än slumpen ger (Benjamini–Hochberg); avstånd till vatten mot slumpvisa punkter på land per landskap (Wilcoxon); interaktiv karta |
| `clusters.R` | cluster, FactoMineR, factoextra | Gowers avstånd på stil, språkdrag, kors, kortkvistrunor och innehåll (kategorierna asymmetriskt binära), PAM med k = 2–10 efter silhuettbredd, stabilitet som Jaccard-likhet i 20 delurval om 80 % (Hennig 2007), MCA; ristare och landskap jämförs efteråt (justerat Rand-index) |
| `text.R` | tidytext, stringr | formler ur normaliseringen (resarformel, monument, ordföljd, ristarsignatur, bön) per ristare; stavning per ord mot ristare (χ² med simulerat p, Cramérs V); ordformer som utmärker en ristare (Fishers exakta test, BH); tf-idf; de 100 vanligaste runbigrammen som variabler till modellen |
| `attribution.R` | tidymodels, ranger | random forest (500 träd) på stenar med säker ristare, ristare med minst åtta stenar (i dag 18 ristare, 497 stenar); 5-faldig stratifierad korsvalidering upprepad 3 gånger, och grupperad per socken och härad; delmodeller med bara geografi, bara stil, bara språk och innehåll; kalibrering (andel rätt per sannolikhetsnivå, ECE); permutationsvikter; förslag för stenar utan ristare inom 25 km från en träningssten |
| `chronology.R` | ca | seriation (korrespondensanalys av språkdrag, formler, kors, kortkvistrunor och innehåll – utan stilgrupp) för Uppland, prövad mot Gräslunds stilkronologi (Spearman mot stilgruppens mittår, och partiell med latituden konstant); tidsskattning med 80 % prediktionsintervall och korsvaliderat medelfel; för hela korpusen redovisas vad de tre första dimensionerna följer (tid, geografi, ristare eller oförklarat) |
| `dialect.R` | stringdist | förväntat normerat Levenshtein-avstånd mellan häradernas stavning av vanliga ord; Mantel-test mot geografiskt avstånd (999 permutationer); grupper av härader (PAM); kartor över stavningen av "efter" och "sten" |
| `network.R` | igraph, tidygraph, ggraph | ord som står i samma inskrifter (positiv PMI), grupper med Louvain; släktorden i inskrifterna (fader, moder, son, broder, félagi …) före och efter ca 1050 och i kristna mot övriga inskrifter (Fisher, BH) |
| `stone.R` | sf, cluster, tidymodels | en sten mot korpusen: modellens sannolikheter (korsvaliderade om stenen har ristare i Rundata), avstånd till kandidaternas tyngdpunkter och höljen, grupp och närmaste grannar (Gower), formler jämförda med kandidaternas inskrifter, läge i Upplands seriation |
| `landscape.R` | terra, gdistance | höjdmodell (ca 20 m), höjd, lutning, topografiskt positionsindex; strand vid vikingatiden som dagens höjd minus en grov landhöjning per landskap (t.ex. 5 m i Södermanland, 5,5 m i Uppland); sikt (viewshed, stenens topp 2 m, betraktare 1,6 m) mot slumpvisa platser; bästa vägar (Toblers vandringsfunktion, vatten tio gånger långsammare) mellan andra runstensplatser inom 12 km och stenens avstånd till dem mot slumpvisa punkter |

**Grupperad korsvalidering** (från 2026-10-10). Vid slumpvis korsvalidering kan stenar från samma plats – ofta resta
av samma ristare samtidigt – hamna både i tränings- och testdata. Modellen utvärderas därför också med hela socknar
(164 grupper) respektive härader (69 grupper) utelämnade (`group_vfold_cv`, 5 delar, 3 upprepningar). En ristare vars
alla stenar ligger i det utelämnade området saknas då i träningen och räknas som fel. Resultat (beräkning
2026-10-10): rätt ristare först i 72 % slumpvis, 68 % med ny socken och 57 % med nytt härad (bland tre främsta
87, 85 och 78 %); geografi ensamt 44, 40 och 30 %, språk och innehåll ensamt 60, 56 och 47 %, mot 19 % om man
alltid gissar på den vanligaste ristaren. En del av träffsäkerheten kommer alltså från platsen, men modellen
fungerar också för platser den inte sett. Sannolikheterna för enskilda stenar kommer fortfarande från den
slumpvisa korsvalideringen, som motsvarar en ny sten på en känd plats.

**Resultat i korpusen (beräkning 2026-10-05).** Attribueringsmodellen hittar rätt ristare i 72 % av fallen
(87 % bland de tre främsta) mot 19 % om man alltid gissar på den vanligaste; språk och innehåll ensamt ger 60 %,
geografi ensamt 44 %. Sannolikheterna är försiktiga: vid minst 0,5 är förstavalet rätt i 93 % av fallen. 24 av 29
ristare arbetade inom ett tydligt mindre område än slumpen ger. I Uppland följer seriationen Gräslunds kronologi
(rho 0,55; 0,54 med latituden konstant), men tidsskattningen är bara något bättre än medelåret (medelfel 21 mot
25 år). Stavningsavståndet mellan härader växer med det geografiska (Mantel r 0,29). I hela korpusen följer den
första CA-dimensionen (kristen bön mot ingen bön) varken tid eller geografi – ett mönster att pröva.

**Reproducerbarhet.** `GET /api/r/package` (knappen på sidan Statistik) ger en zip med R-skripten, korpusens CSV,
resultaten, `sessionInfo()` och `KOR_OM.R`, som kör om allt i R utan appen. Paketen installeras med
`Rscript r/install.R` (sf kräver GDAL, GEOS, PROJ och udunits; ragg kräver fribidi och harfbuzz; nloptr kräver
cmake).

**Begränsningar.**
* Attribueringsmodellen väljer bara bland sina ristare; ett förslag för en sten utan ristare vägs därför med hur
  stor andel av landskapets attribuerade stenar modellens ristare står för. Signerade stenar av ristare utanför
  modellen räknas inte som motsägelser.
* Träningsdata är Rundatas attribueringar, i Mälardalen främst Axelsons (1993), som själv vägde in stil, stavning
  och geografi. Korsvalideringen mäter därför överensstämmelse med dessa bedömningar snarare än med en oberoende
  sanning.
* Natural Earths vattenlager saknar mindre vattendrag och våtmarker – därför står brostenarna "längre från vatten"
  i analysen, vilket visar lagrets gräns och inte broarnas läge.
* Landhöjningen är en grov skattning per landskap, höjdmodellen visar dagens markyta och vägarna är simulerade
  bästa vägar, inte belagda vikingatida vägar.
* Klustringen ger svag struktur (silhuett omkring 0,33); grupperna följer kors, stungna runor och bön, inte ristare.

## 18. Kända brister

Källkod: `src/limitations.py`, `GET /api/limitations`. Metodens kända brister förs i en enda förteckning
(version 2026-10-10) som följer med varje analys:

* **I appen** visas de brister som gäller sidan under varje analyssida (3D-analys, stenanalys, jämförelse,
  mätkorpus, syntes, statistik, forskningsluckor, inskrifter, karta, stilgrupper, 2D-analys, läsning, rapporter).
* **I rapporterna** har stenrapporten och korpusrapporten ett avsnitt "Kända brister och begränsningar", och varje
  publiceringsform (avsnitt 14e) tar med dem – fullständigt i vetenskapliga och antikvariska former, i populär form
  i blogginlägg, pressmeddelande och poster. Varningar för just analysen (t.ex. färre runor än riktvärdet) står först.
  AI som formulerar text får förteckningen och instrueras att inte tona ned den.
* **I proveniensen** som sparas med varje mätning och syntes står förteckningens version och vilka brister som
  gällde (`known_limitations`), så att det går att se i efterhand vad som var känt när mätningen gjordes.

När en brist åtgärdas ändras förteckningen och versionen höjs. Bristerna i dag:

| Brist | Gäller | Vad som behövs |
|---|---|---|
| Måtten är inte validerade som spår av ristarens hand | attribution, comparison, grooves | Stenar med känd ristare på samma bergart, jämförelse med Groove Measure-data och gärna experimentella ristningar med kända ristare och verktyg. |
| Bottenradie och asymmetri är osäkra mått | comparison, grooves | Bättre bottenmodell och test på skanningar av samma sten med olika punkttäthet. |
| Ingen sten är mätt i oberoende skanningar | comparison, grooves | Test–omtest med oberoende skanningar av samma stenar, och manuell mot automatisk mätning; samma rutnät och känslighet för alla stenar som jämförs. |
| Inte jämförbart med tidigare 3D-studier utan kalibrering | comparison, grooves | Samma referensstenar mätta med båda metoderna. |
| Runigenkänningen är inte utvärderad | auto | Handmärkta facit för 8–10 stenar som inte använts för att justera reglerna (facit-läget i 3D-vyn, scripts/evaluate_rune_detection.py), med låsta regler. |
| Gränserna 10 och 20 runor är riktvärden | auto, comparison | Ny beräkning när test–omtest och stenar med känd ristare på samma bergart finns. |
| Attribueringen riskerar att bli cirkulär | attribution, statistics | Prövning på signerade stenar som inte använts i träningen och med variabler som inte låg bakom attribueringarna. |
| Träffsäkerheten beror på om platsen är känd | attribution, r, statistics | Grupperad korsvalidering även för mätkorpusens attribuering, när korpusen är stor nog. |
| Många utforskande test på samma data | attribution, research, statistics | Förregistrerade analysplaner för de hypoteser som ska publiceras. |
| Stenarnas mått är ofullständiga och ojämna | research, rundata | Mått ur Sveriges runinskrifter eller nya mätningar för stenarna som saknas; hela höjden för resta stenar. |
| AI-resultat är okalibrerade och kan vara påhittade | ai | Kalibrering mot runologers läsningar av samma bilder. |
| Rundata är en äldre utgåva | attribution, research, rundata | Uppdatering till senaste utgåvan av Runor. |
| Programvaran är under utveckling | attribution, comparison, grooves, software | Låst version med DOI (Zenodo) och extern granskning av koden. |

R-analysernas egna begränsningar (avsnitt 17) ingår när de används.
