# Metodbeskrivning

Den här filen beskriver exakt hur Runforskning räknar, så att resultat kan granskas, upprepas och citeras.
Alla beräkningar finns i `src/` och testas i `tests/`. Varje analys sparar en **proveniens** (programversion,
mätmetodens version, SHA-256 för 3D-filen, alla parametrar och tidpunkt) som följer med i export och rapporter.

## 1. Huggspårsmått (mätmetod `groove-2`)

Källkod: `src/slice_analysis.py`.

1. **Tvärsnitt.** Mesh-filen centreras på mittpunkten av sin omslutande låda (samma som i webbläsaren).
   Ett plan läggs vinkelrätt mot spårets riktning och skär nätet; skärningen projiceras till en 2D-profil
   (x = position tvärs spåret, z = höjd längs den angivna uppåtvektorn).
2. **Apex.** Profilen jämnas ut med ett glidande medelvärde (5 punkter). Apex är den lägsta punkten.
3. **Spårkanter (axlar).** Från apex söks utåt tills lutningen |dz/dx| understiger 0,15 – där börjar den plana
   stenytan. Ligger en kant närmare än 5 punkter från apex används 15 punkter som reserv.
4. **Väggar.** Vänster och höger vägg (mellan kant och apex) anpassas var för sig med linjär regression.
5. **Mått:**

| Mått | Definition |
|---|---|
| V-vinkel (°) | Öppningsvinkeln mellan väggarnas regressionslinjer, mätt från apex. |
| Asymmetri (°) | \|arctan(1/\|k₁\|) − arctan(1/\|k₂\|)\|, skillnaden mellan väggarnas vinkel mot lodlinjen. |
| Spårdjup (mm) | Höjdskillnaden mellan högsta och lägsta punkt mellan kanterna. |
| Spårbredd (mm) | Avståndet mellan kanterna. |
| Djup/bredd | Spårdjup / spårbredd. |
| Bottenradie (mm) | 1/(2a) för en andragradskurva anpassad till ±5 punkter kring apex. |
| Ytråhet (mm) | Medelabsolutavvikelsen från väggarnas regressionslinjer. |

Flera snitt läggs med 1 mm mellanrum längs spåret (eller längs en ritad bana). Varje snitt redovisas för sig.

**Versionshistorik.** `groove-1` (före 2026-10-04) beräknade vinkeln mellan väggarnas riktningsvektorer åt
samma håll och gav därför 180° minus den verkliga öppningsvinkeln (en spårfixtur på 75° rapporterades som
103,5°). Mätningar gjorda med `groove-1` ska räknas om (180° − värdet) eller göras om.

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
