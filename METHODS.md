# Metodbeskrivning

Den här filen beskriver exakt hur Runforskning räknar, så att resultat kan granskas, upprepas och citeras.
Alla beräkningar finns i `src/` och testas i `tests/`. Varje analys sparar en **proveniens** (programversion,
mätmetodens version, SHA-256 för 3D-filen, alla parametrar och tidpunkt) som följer med i export och rapporter.

## 1. Huggspårsmått (mätmetod `groove-3`)

Källkod: `src/slice_analysis.py`.

1. **Tvärsnitt.** Mesh-filen centreras på mittpunkten av sin omslutande låda (samma som i webbläsaren).
   Ett plan läggs vinkelrätt mot spårets riktning och skär nätet. Bara skärningspunkter inom ±25 mm från
   mätpunkten, i sidled och höjdled, tas med (fönster) – annars kommer stenens baksida och kanter med i
   snittet genom en sluten skanning. Profilen uttrycks i x (tvärs spåret) och z (längs ytans normal).
2. **Uppåtriktning.** Vid manuell mätning används medelvärdet av ytnormalen i de klickade punkterna, vid
   ett klick och automatisk analys den lokala ytnormalen (se avsnitt 1b och 1c).
3. **Apex.** Profilen jämnas ut med ett glidande medelvärde (5 punkter). Apex är den lägsta punkten.
4. **Spårkanter (axlar).** Från apex söks utåt tills lutningen |dz/dx| understiger 0,15.
5. **Väggar.** Varje vägg anpassas med linjär regression, men **bara mellan 20 % och 80 % av höjden** från
   botten till spårkanten. Den rundade botten och spårkantens läpp planar annars ut väggarna och ger för
   stor vinkel (minst tre punkter, annars används hela väggen).
6. **Mått:**

| Mått | Definition |
|---|---|
| V-vinkel (°) | Öppningsvinkeln mellan väggarnas regressionslinjer, mätt från apex. |
| Asymmetri (°) | \|arctan(1/\|k₁\|) − arctan(1/\|k₂\|)\|, skillnaden mellan väggarnas vinkel mot lodlinjen. |
| Spårdjup (mm) | Höjdskillnaden mellan högsta och lägsta punkt mellan kanterna. |
| Spårbredd (mm) | Avståndet mellan väggarnas linjer i höjd med stenytan precis utanför spårkanterna (medel av sidorna). |
| Djup/bredd | Spårdjup / spårbredd. |
| Bottenradie (mm) | 1/(2a) för en andragradskurva anpassad till ±5 punkter kring apex. |
| Ytråhet (mm) | Medelabsolutavvikelsen från väggarnas regressionslinjer. |
| Väggpassning (R²) | Den sämre av väggarnas förklaringsgrad; används för kvalitetsgranskning. |

**Validering.** På syntetiska stenar med kända V-spår (öppningsvinkel 50–110°, djup 2–4 mm, välvd yta,
mätbrus 0,03 mm, `src/synthetic.py`) mäts vinkeln inom ±0,6° och bredden inom ±1 % (djup 4 mm). Testerna
körs automatiskt (`tests/`).

**Versionshistorik.**
* `groove-1` (före 2026-10-04) gav 180° minus den verkliga öppningsvinkeln.
* `groove-2` (2026-10-04) rättade vinkeln, men anpassade väggarna över hela höjden, mätte bredden mellan
  spårkanterna och tog med hela snittet genom nätet. På smala spår blev vinkeln ca 10° för stor.
* `groove-3` (2026-10-04): väggband 20–80 %, bredd vid stenytan och fönster runt mätpunkten.
  Mätningar med äldre versioner är inte direkt jämförbara och bör göras om.

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
   (> 45°) och små fläckar (< 10 mm²) utesluts.
4. **Mittlinjer:** spåren tunnas ut till ett skelett. Punkter nära korsningar och ändar utesluts, liksom
   partier bredare än ett huggspår (standard 16 mm) – t.ex. sänkta fält eller avflagningar.
5. **Mätning:** med jämna mellanrum (standard 3 mm) längs mittlinjerna tas riktningen från mittlinjen och
   förfinas genom att botten följs (som i 1b). Tvärsnittet mäts **genom mesh-filen** med samma metod som i
   avsnitt 1 – höjdfältet används bara för att hitta spåren.
6. **Kvalitetsgranskning:** snitt sorteras bort vid orimlig vinkel (≤ 15° eller ≥ 170°), väggpassning
   R² < 0,8, djup under tröskeln, ej funnen spårkant eller botten utanför mittlinjen. Skälen redovisas.
7. **Granskning:** forskaren ser alla mätpunkter på en reliefbild, märker områden som runor eller
   ornamentik eller utesluter dem, och väljer vilket urval som blir resultatet.

**Validering.** På de syntetiska stenarna ger den automatiska analysen samma noggrannhet som avsnitt 1
(t.ex. 70,0 ± 0,9° för spår på 70°, oberoende av hur stenen lutar). På skanningen av Sö 113 (6,1 miljoner
trianglar) godkändes ca 250 av 1 000 kandidatsnitt; ett klick på samma ställen gav i median 6° skillnad i
vinkel och 10° i spårriktning, vilket speglar hur oregelbundna verkliga, vittrade spår är. Resultaten bör
därför redovisas med spridning och, för jämförelser, med samma mätsätt för alla stenar.

## 2. Osäkerhet

Källkod: `src/stats.py`. För varje mått och sten redovisas medelvärde, standardavvikelse (n − 1),
antal snitt och 95 % konfidensintervall (t-fördelning). Spridningen mellan snitt säger hur stabilt måttet
är längs spåret – den fångar inte systematiska fel som skanningsupplösning eller vittring.

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
* **Runformer** från 2D-analysen (normaliserad form och särdragsvektor, se 7b) kan bifogas under
  `corpus/{id}/runeforms`, med spårmått för runan om den markerats på en ristningskarta från 3D-analysen.
* Andra forskare kan lägga till en **verifiering** (namn, institution, kommentar); den egna posten kan inte
  verifieras av bidragsgivaren. Kvalitetsmärken visar råprofiler, skanningsuppgifter, minst fem snitt, aktuell
  metodversion och verifiering.
* Korpusen kan exporteras som ett **datapaket** (JSON med licens, citering, bidragsgivare och alla poster,
  valfritt med råprofiler) för arkivering.

## 5. Klustring

Hierarkisk klustring med Wards metod och euklidiska avstånd på standardiserade medelvärden per sten –
samma upplägg som i Kitzler Åhfeldts analyser av huggteknik (se avsnitt 8).

## 6. Ortografisk stilometri

Källkod: `src/orthography.py`. Underlag: Rundatas vikingatida inskrifter med minst fem läsbara ord (1 719 st).

* **Särdrag:** tecken-2- och 3-gram i läsbara ord (TF-IDF), skiljeteckentyper och -täthet, andel bindrunor.
  Skadade ord (med `-` eller `...`) räknas inte.
* **Egennamn tas bort** (ord som normaliseras som namn i Rundata), så att ristarens signatur ("bali risti")
  inte avslöjar svaret och beställarnamn inte styr resultatet.
* **Likhet:** cosinuslikhet. **Ristarrangordning:** närmaste centroid bland ristare med minst fem säkra
  inskrifter.
* **Utvärdering** (lämna-en-ute, 27 ristare, 459 inskrifter, Rundata 2014): rätt ristare först i 61 %,
  bland de tre första i 71 %; för enbart signerade inskrifter (n = 135) först i 60 %. Slumpnivå 4 %.
  Attribuerade inskrifter kan ha attribuerats just på grund av ortografin, därför redovisas siffran för
  signerade separat.

## 7. Syntes och AI

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
bara en oberoende källa som stöd när kandidaten kommer först där. AI-modellen (Gemini) får beläggen som
underlag och skriver bara löptext; utan AI ersätts texterna av framräknade formuleringar. Syntesen kan
sparas i projektet och blir då avsnittet "Attribuering" i stenrapporten.

**Verktygsklassning** (pik-/bredmejsel, tröskel 85°, +5° vid hög vittring, +2° vid måttlig vittring, +2° för
sandsten/kalksten) är en tumregel som inte är kalibrerad mot referensmaterial och redovisas som sådan.

### 7a. Språk och läsning

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
* Läsningen kan rättas för hand och jämföras igen; den märks då som rättad.
* **Bilder att läsa:** foto, 2D-analysens bild, RTI-vy eller reliefbilder ur 3D-skanningen (strykljus från
  fyra riktningar, ett kombinerat relief där varje spår blir mörkt oavsett riktning, och djup under
  stenytan), räknade från den sida som vetter mot betraktaren i 3D-vyn.
* **Uppläsning:** en modern talsyntes läser normaliseringen. Det är inte en rekonstruktion av uttalet;
  IPA-raden är modellens förslag och ljudlagarna är inte kontrollerade.

### 7b. 2D-analys och runformer

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
* Bilder kan komma från uppladdning, K-samsök, en ögonblicksbild av 3D-vyn, RTI-visaren eller
  **ristningskartan** från den automatiska spåranalysen (residualdjup, djupt = mörkt). Ristningskartan har
  samma pixelkoordinater som analysens granskningsbild, så ett runutsnitt där kopplas till de uppmätta
  snitten inom utsnittet.

### 7c. Forskningsluckor

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

### 7d. Akademisk rapport

Källkod: `src/academic.py`, `POST /api/reports/academic`. Rapporten byggs för ett urval av korpusen (en
ristare, ett landskap, valda stenar eller hela korpusen):

* **Material, metod, tabeller och figurer räknas fram ur data**: medelvärden och spridning per mått, per
  sten och per ristare, figurer över V-vinkel och Ward-dendrogram, samt metodversioner och referenser.
* AI kan skriva **sammanfattning, inledning och diskussion**, men får bara en faktatext med de framräknade
  resultaten som underlag. Dessa avsnitt märks som AI-text. Utan AI-nyckel lämnas de för författaren att
  skriva.
* Export: Markdown, LaTeX (med figurfilerna) och Word (.docx). Rapporten är ett manusutkast som måste
  granskas innan den används.

### 7e. Stenrapport (en sten)

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

### 7f. Våra resultat mot befintlig forskning

Källkod: `src/findings.py`, `POST /api/research/findings`. Appens resultat ställs mot Rundata, som får
representera den publicerade forskningen:

| Metod | Stämmer | Nytt | Motsäger |
|---|---|---|---|
| Ortografi (lämna-en-ute) | rätt ristare först | stark hypotes för sten utan ristare | attribuerad (A) ristare inte bland de tre första |
| Huggteknik (mätkorpusen, runor) | närmaste ristare = Rundatas | sten utan ristare får en närmaste ristare | närmaste ristare ≠ Rundatas |
| Stilgrupp (AI, bild) | samma som Rundata | Rundata saknar säker stilgrupp | annan stilgrupp |

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

## 8. Jämförbarhet med tidigare forskning

Laila Kitzler Åhfeldts metod (Arkeologiska forskningslaboratoriet, Stockholms universitet; Kitzler Åhfeldt
2002) mäter spårvariabler i högupplösta 3D-modeller med funktionen *Groove Measure* (DeskArtes), analyserar
runor och ornamentik separat, beskriver varje sten med medelvärden och använder bl.a. Wards klustring på
standardiserade variabler (t.ex. Kitzler Åhfeldt & Imer 2019, *Danish Journal of Archaeology* 8,
doi:10.7146/dja.v8i0.113226). Runforskning följer samma upplägg (separata spårtyper, medelvärden per sten,
standardisering, Ward), men **måtten är inte verifierade som likvärdiga** med Groove Measure-variablerna.
Innan resultat jämförs direkt bör samma referensstenar mätas med båda metoderna.

## 9. Datakällor och licenser

* **Samnordisk runtextdatabas** (Institutionen för nordiska språk, Uppsala universitet), version 2014 med
  RUNDATA.xls från 2018. Open Database License (databasen) / Database Contents License (innehållet).
  Källan ska anges: www.nordiska.uu.se/forskn/samnord.htm. `data/rundata.json` är en härledd databas och
  omfattas av samma licens. Svenska koordinater (RT90 2,5 gon V) räknas om till WGS 84 med pyproj.
* **Stilgrupper:** Gräslund, A.-S. 1998. Ornamentiken som dateringsgrund för Upplands runstenar.
  I: *Innskrifter og datering / Dating inscriptions*. Trondheim, s. 73–91. Dateringarna är ungefärliga.
* **Mätkorpusen:** bidrag publiceras under CC BY 4.0 med bidragsgivaren angiven.
* **Kartor:** © OpenStreetMap-bidragsgivare.
