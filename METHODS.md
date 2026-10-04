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

Kandidaterna i syntesen räknas fram deterministiskt (`api/routers/synthesis.py`):

| Källa | Vikt |
|---|---|
| Rundata: signerad (S) | 4 (2 om osäker) |
| Rundata: attribuerad (A) | 2 (1 om osäker) |
| Rundata: parsten/liknar (P/L) | 1 |
| Ortografi plats 1 / 2–3 | 2 / 1 |
| Huggteknik plats 1 / 2–3 | 2 / 1 |

Styrka: **stark** = summa ≥ 4 eller stöd från alla tre källorna; **måttlig** = summa ≥ 3, eller ≥ 2 från två
källor; annars **svag**. Inga procentsatser anges. AI-modellen (Gemini) får beläggen som underlag och skriver
bara löptext; den instrueras att inte hitta på uppgifter eller sannolikheter, och syntesen fungerar utan AI.

**Verktygsklassning** (pik-/bredmejsel, tröskel 85°, +5° vid hög vittring, +2° vid måttlig vittring, +2° för
sandsten/kalksten) är en tumregel som inte är kalibrerad mot referensmaterial och redovisas som sådan.

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
