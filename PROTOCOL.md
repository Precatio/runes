## Vitki-protokollet

**Protokoll för automatisk mätning av huggspår i 3D-skanningar av runstenar.**
Version: `vitki-groove-1-utkast` · mätmetod `groove-5` · status: **utkast** – låses (`vitki-groove-1`) när Vitki
släpps i en version med DOI. Maskinläsbar form: `src/protocol.py`. Metoderna beskrivs i detalj i METHODS.md.

### P1. Syfte

Protokollet anger hur huggspår mäts och redovisas så att mätningar av olika stenar, gjorda av olika forskare, går
att jämföra och upprepa. Det låser de val som påverkar resultatet och anger vad som minst ska redovisas. Det gäller
den automatiska analysen; mätningar med ett klick eller manuellt följer inte protokollet och redovisas som sådana.

Protokollet följer samma principer som London Charter (2009) och Sevillaprinciperna (2011) för datorbaserad
dokumentation av kulturarv: metoden ska vara öppen, varje steg dokumenterat (paradata) och osäkerheten redovisad.

### P2. Krav på skanningen

* Den ristade ytan skannad i 3D (STL, OBJ eller PLY), utan utjämning eller hålfyllning som ändrar spåren.
* Punktavstånd högst **0,5 mm** (rekommendation). Glesare skanningar ger sämre resultat: med en fjärdedel av
  trianglarna ändras stenens V-vinkel med upp till 9° (METHODS.md 1e).
* Uppgifter om skanner, upplösning, noggrannhet, datum, utförare och licens. Filens SHA-256 räknas av programmet.

### P3. Fasta parametrar

| Parameter | Värde | Varför |
|---|---|---|
| Mätmetod | `groove-5` | Resultat är bara jämförbara inom samma metodversion |
| Rutnät (`resolution_mm`) | 0,6 mm, fast | Samma rutnät oavsett skanningens täthet (METHODS.md 1, 1e) |
| Känslighet (`sensitivity`) | 3 (tröskel = max(0,3 mm, 3 × brus)) | Känslighet 2,5 ändrar stenens vinkel med 2,8° i median |
| Snittavstånd (`spacing_mm`) | 3 mm | |
| Största spårbredd (`max_halfwidth_mm`) | 8 mm (16 mm bredd) | Bredare partier är sänkta fält eller avflagningar |
| Harmonisering (`harmonize_mm`) | ingen | |
| Bara runor (`runes_only`) | ja | Ornamentik, slinglinjer och sprickor mäts inte (METHODS.md 1c, steg 5) |
| Ytnormal | stenens tunnaste riktning eller den ristade sidan vänd mot kameran | Djupet beror på normalen (0,37 mm vid 5° lutning) |

I appen väljs protokollet med rutan *Vitki-protokollet* i 3D-vyn (standard) och används för huvudanalysen i
Stenanalys. Programmet kontrollerar varje automatisk analys mot parametrarna och sparar i proveniensen om den följer
protokollet och vilka avvikelser som gjordes.

### P4. Arbetsgång

1. Läs in skanningen och ange signum, bergart och vittring.
2. Vänd den ristade sidan mot kameran (eller använd den tunnaste riktningen) och kör den automatiska analysen.
3. **Granska granskningsbilden.** Kontrollera att de mätta punkterna ligger på runor. Uteslut felaktigt mätta
   områden; redovisa hur många punkter som uteslöts för hand och varför.
4. Kontrollera antalet mätta runor mot riktvärdena: minst 10 för att beskriva stenen, minst 20 för att jämföra
   den med andra stenar (riktvärden, METHODS.md 2).
5. Spara analysen; proveniensen följer med i export, mätkorpus och rapporter.

### P5. Minsta redovisning

En mätning enligt protokollet redovisar minst:

* programversion, mätmetod och protokollversion, och om analysen avviker från protokollet;
* skanningens uppgifter och SHA-256;
* alla parametrar (sparas automatiskt);
* antal kandidatsnitt, godkända snitt, igenkända och mätta runor och skälen till bortsorterade snitt;
* stenens medelvärden med runan som enhet, med 95 % konfidensintervall och antal runor;
* mått per tvärsnitt (CSV) och råprofiler (JSON);
* granskningsbilden, och de punkter som uteslöts för hand;
* förteckningen över kända brister (version).

Stenrapporten och alla rapportmallar tar med detta.

### P6. Jämförelser mellan stenar

* Bara stenar mätta enligt samma protokollversion, eller med samma avvikelser.
* Runor och ornamentik jämförs aldrig med varandra.
* Ange bergarten. Skillnader mellan stenar av olika bergart kan bero på materialet (METHODS.md 15 och
  replikationsstudien).
* Jämförelser görs med permutationstest och effektstorlek (METHODS.md 3), inte med enstaka snitt.
* V-vinkel, djup, bredd och djup/bredd är stabila mått; asymmetri och bottenradie bör inte bära slutsatser.

### P7. Validering och status

| Del | Status |
|---|---|
| Mätningen på syntetiska spår med kända mått | gjord (vinkelfel inom ±0,6°) |
| Robusthet mot analysens val och skanningens täthet | gjord (8 stenar; METHODS.md 1e) |
| Riktvärden för antal runor | preliminära (18 stenar; METHODS.md 2) |
| Runigenkänningens träffsäkerhet mot handmärkta facit | **ej gjord** – facit-läge och utvärderingsskript finns |
| Test–omtest med oberoende skanningar av samma sten | **ej gjord** |
| Jämförelse med Groove Measure (Kitzler Åhfeldt) | **ej gjord** |

Protokollet låses först när delarna som inte är gjorda är prövade eller uttryckligen redovisade som brister.

### P8. Versioner

Protokollets version ändras när parametrarna, arbetsgången eller kraven på redovisning ändras; mätmetodens version
(`groove-N`) när beräkningen ändras. Gamla mätningar behåller sina versioner i proveniensen och kan räknas om med
råprofilerna eller skanningen.

### P9. Att hänvisa till protokollet

> Huggspåren mättes enligt Vitki-protokollet för automatisk huggspårsmätning (vitki-groove-1, mätmetod groove-5;
> Vitki version X.Y.Z, DOI …).

Så länge protokollet är ett utkast anges `vitki-groove-1-utkast` och att protokollet inte är låst.
