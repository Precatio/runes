# Epigraphix AI – Användarmanual

Välkommen till Epigraphix AI, ett modernt forskningsverktyg för kvantitativ analys av huggspår i 3D-skannade runstenar (och andra historiska inskriptioner). Verktyget låter dig ladda upp 3D-modeller direkt i webbläsaren, rita mätbanor längs runskåror, inspektera stenen topografiskt, extrahera matematiska tvärsnitt, och använda artificiell intelligens för stilistisk analys.

---

## 1. Kom igång

### Systemkrav
- Node.js och npm installerat (för webb-klienten)
- Python 3.9 eller senare (för beräknings-API:et)
- En modern webbläsare med stöd för WebGL (Chrome, Firefox, Safari, Edge)

### Starta applikationen
För att starta gränssnittet på din egen dator, öppna en terminal i mappen `aagaard-research` och starta både backend och frontend (förslagsvis i två separata terminalfönster):

**Starta Python Backend (API):**
```bash
scripts/dev_api.sh
```
Skriptet startar `uvicorn api.main:app --reload --port 8000 --reload-dir api --reload-dir src`, så att servern bara
startas om när programkoden ändras – inte när du redigerar artiklar, data eller tester.

**Starta Web UI (Next.js):**
```bash
cd web
npm run local
```
Kommandot bygger appen och startar den. Öppna sedan `http://127.0.0.1:3000` i webbläsaren.

---

## 2. Navigering & 3D-vyn

När du navigerar till **3D-Miljö** i sidomenyn möts du av en arbetsyta för att visualisera och mäta på din 3D-modell. 
Applikationen stödjer standardformaten för 3D-skanningar: `.stl` och `.obj`.

- Fyll i din "Gemini API-nyckel" i inställningspanelen om du avser utföra AI-analys.
- Klicka på "Ladda upp 3D-fil" och välj din stenmodell.

### Visualisering & Verktyg
I 3D-vyn har du flera verktyg (knappar i övre vänstra hörnet):
- **Ljussättning:** Klicka på kugghjulet för att justera kontrast (omgivningsljus) och ljusstyrka (direktljus) så skuggorna framträder tydligare.
- **Topografi (Djupkarta):** Klicka på ikonen med skiktlinjer för att byta material till en "Topografisk Shader". Detta fägar modellen baserat på lokalt djup. Du kan justera känsligheten i ljus-menyn för att isolera huggspåren visuellt från stenens yta.
- **Rensa Snitt:** Raderar din utplacerade mätbana.
- **Återställ Vy:** Återställer kameravinkeln till standardläget.

---

## 3. Mätbanor & Spåranalys

Det centrala arbetsflödet för att mäta tvärsnitt är att rita en "mätbana" i 3D-miljön.

### Rita en böjd mätbana (Splines)
Du är inte begränsad till raka linjer med två punkter. 
1. Håll inne **`Alt`-tangenten** på ditt tangentbord och **vänsterklicka** i botten av det huggspår (runa) du vill analysera.
2. Fortsätt hålla `Alt` och klicka framåt längs runans botten. Ett obegränsat antal punkter kan placeras ut.
3. Systemet drar automatiskt en mjuk och organisk kurva genom alla dina valda punkter.

### Fäst mot botten (Auto-Snap)
Om du är skakig på hand eller om det är svårt att klicka exakt i botten av huggspåret kan du ta hjälp av algoritmerna:
1. När du klickat ut en bana dyker knappen **🧲 Auto-Snap** upp.
2. Genom att klicka på denna analyseras all yta kring din slarviga bana.
3. Motorn lokaliserar de absolut djupaste punkterna i spåret och tvingar (snappar) automatiskt ner hela din bana så att den ligger spikrakt längs runans botten-centrum.

### Utför Kvantitativ Analys
När din bana är perfekt placerad, klicka på knappen **Analysera spår / Extrahera data** under inställningsformuläret till vänster.

**Vad händer då?**
1. Servern beräknar automatiskt täta vinkelräta tvärsnitt utmed *hela* din kurviga mätbana.
2. För varje litet snitt längs banan räknar den ut skårans tvärsnittsegenskaper, och kombinerar sedan detta till stabila **genomsnittsvärden** för:
   - **V-vinkel:** Spetsvinkeln i botten av spåret (för att identifiera pikmejsel vs bredmejsel).
   - **Asymmetri:** Skillnaden i lutning (grader) mellan spårets vänster- och högersida.
   - **Spårdjup & Spårbredd (mm).**
3. En interaktiv 2D-graf visas till höger, som låter dig zooma in och inspektera ett av representant-snitten på mikrometernivå.

Resultatet samt en uppskattning på vilket verktyg som använts presenteras omedelbart på skärmen!

### Exportera bilder och mätdata
I högra kolumnen på 3D-sidan finns rutan **Exportera**. Kryssa i de filer du vill ha och tryck **Ladda ned**. En
enda fil kommer som den är; väljer du flera kommer de i en ZIP-fil. Reliefen och ristningskartan kommer alltid i en
ZIP-fil med README.txt, också ensamma, eftersom de inte har någon synlig rad om skanningen. Vilka val som syns beror på vad du har gjort:
bilderna ur skanningen finns så snart en 3D-modell är inläst, medan bilderna ur mätningen och tabellerna kommer när
du har mätt. Under **Vad innehåller filerna?** står samma förklaringar som här. Första gången en bild räknas fram
kan det ta upp till en halv minut; med **Avbryt** stoppar du nedladdningen.

Är fliken för den automatiska analysen öppen exporteras den, annars mätningen som visas på sidan. Mätformen som
står i filerna är den som analysen gjordes med, inte vilken flik som är öppen. Den automatiska analysen exporteras
med dina etiketter från granskningen, precis som stenrapporten läser dem: snitt du märkt som uteslutna räknas inte i
sammanfattningen och figurerna, och sammanfattningen räknas för varje grupp (runa, ornamentik, okänt). Raderna per
runa finns bara för gruppen runa, och bara när analysen mätte enbart runor. Bilderna ur
skanningen ses från samma håll som stenrapportens figurer, så att de stämmer med rapporten.

**Bilder ur skanningen**
- **Spårdjup som värmekarta.** Färgen visar hur djupt varje punkt ligger under en referensyta som räknats fram ur
  skanningen genom att fylla igen fördjupningar smalare än 20 mm. Den ligger i nivå med ytan runt spåren och
  spårkanterna, inte på en tänkt ursprunglig stenyta. Ljust betyder i nivå och svart det djupaste; skalan i mm står
  bredvid och slutar vid stenens 99,5:e percentil, så den djupaste halva procenten blir lika svart. Kartan visar
  formen. Spårdjupen i mättabellen blir ofta 10–40 % större än kartans, ibland mindre, eftersom de mäts i täta
  tvärsnitt från spårkanten till botten, medan kartan är ett grövre rutnät där varje ruta har den högsta punkten i
  sin ruta och den smala botten i ett spår sällan träffas exakt. Den yttersta
  centimetern mot skanningens kant är tom; branta partier, sprickor, vittringsgropar och borrhål kan ändå se ut som
  djupa spår.
- **Spårdjup som rådata (rutnät i mm).** Samma djup som i värmekartan, som tal: ett värde i millimeter per ruta.
  Rutans storlek står i filhuvudet och beror på skanningens täthet och stenens storlek. Filen öppnas i QGIS, i R
  (terra) eller i Python. Rutor med −9999 ligger utanför skanningen eller i kantzonen. Koordinaterna är millimeter i
  stenytans eget plan, inte geografiska.
- **Reliefbild.** Stenytan belyst från fyra håll på en gång, där det mörkaste värdet behålls. Varje spår blir därför
  mörkt, oavsett åt vilket håll det går. Gråtonen är inte ett mått i millimeter, och kontrasten är sträckt för just
  denna sten. En pixel är en ruta i ytans rutnät.
- **Strykljus från fyra håll.** Digitalt strykljus, 20° över ytan, som när man fotograferar en sten i lågt sidoljus.
  Ett spår syns tydligast när ljuset faller tvärs över det och kan nästan försvinna när ljuset går längs med, så titta
  på alla fyra. "Nordväst" betyder snett uppifrån vänster i bilden, inte ett väderstreck vid stenen.

**Bilder ur mätningen**
- **Ristningskarta.** Spårdjupet i den automatiska analysens rutnät, i gråskala och i samma läge som
  granskningsbilden. Svart sätts vid 95:e percentilen av djupen i de rutor som ligger djupare än analysens tröskel,
  så gråtonerna kan inte jämföras mellan stenar. Kantzonen, branta partier, sprickor och ornamentik kommer med.
  Svart betyder black_mm eller djupare (värdet står i bildens metadata), och svartpunkten kan sättas av skanningens
  kant, så runorna kan se mellangrå ut.
- **Granskningsbild med mätpunkter.** Visar var programmet mätte, med en teckenförklaring under bilden. Orange är spår
  som hittats och gråblått ytor för breda att mäta; de färgade prickarna är godkända snitt färgade efter V-vinkel och
  de små grå bortsorterade snitt. Bilden visar analysens egen sortering, inte dina etiketter, och är till för att
  granska analysen, inte ett resultat i sig.
- **Snittens läge färgade efter V-vinkel.** Var varje mätt tvärsnitt ligger på stenen. Bokstäverna hör till bilden
  med tvärsnittsprofiler. Här ser man om breda eller smala vinklar samlas i en del av ristningen, till exempel där
  ytan är mer vittrad.
- **Spårdjup, spårbredd och ytråhet på stenen.** Mätningarna i tabellen, ritade där de gjordes. Ytråheten är
  hundradels millimeter och ligger nära skanningens brus.
- **Tvärsnittsprofiler (bild).** Upp till tolv representativa tvärsnitt i lika skala på båda axlarna, med de
  anpassade väggarna i rött och spårkanternas nivå streckad. Här ser man om måtten rimligen beskriver spåret.

**Tabeller och data**
- **Mättabell, ett tvärsnitt per rad.** V-vinkel, spårdjup, spårbredd, ytråhet, fit_r2 och snittets läge, och i den
  automatiska analysen din etikett. Bara den automatiska analysen sorterar bort snitt med fit_r2 under 0,8. Snitt i
  samma runa är inte oberoende mätningar, så använd sammanfattningen per runa för stenens värde. Koordinaterna är
  millimeter i den centrerade 3D-modellen, inte i originalfilen.
- **Sammanfattning per sten och per runa.** Medelvärden med spridning och 95-procentigt konfidensintervall, per
  grupp. Raderna per runa ger det ärliga värdet för stenen. ICC kan bli negativ; det betyder att runorna inte skiljer
  sig mer än snitten inom en runa. Riktmärke: minst 10 mätta runor för att beskriva en sten och minst 20 för att
  jämföra stenar. Gissningen om verktyg är en tumregel och inte kalibrerad.
- **Runor och kvalitetskontroll.** Det programmet har räknat som en runa (en grupp raka streck, inte en igenkänd
  runa), med höjd, antal streck och snitt, och varför bortsorterade snitt föll bort.
- **Tvärsnittsprofiler som tal.** De uppmätta punkterna i varje tvärsnitt, så att vem som helst kan mäta om spåren.
- **Längdprofil.** Spårdjupet längs en bana du ritat, snitt för snitt.
- **Hela analysen (JSON).** Allt i maskinläsbar form med proveniens: programversion, mätmetod, skanningsfilens namn
  och fingeravtryck (SHA-256), datum, metodens kända brister och, för den automatiska analysen, dina etiketter och
  sammanfattningarna per grupp.

Tabellerna har källa och proveniens på rader som börjar med `#`. I R läses de med
`read.csv("fil.csv", comment.char = "#", fileEncoding = "UTF-8-BOM")` och i Python med
`pandas.read_csv("fil.csv", comment="#", encoding="utf-8-sig")`.

**README.txt och kalla.json.** I ZIP-filen finns README.txt, som förklarar varje fil, enheter, skalor, vilken
riktning bilderna är sedda från, dina etiketter, vem som ska krediteras och begränsningarna för just den här stenen
(till exempel för få mätta runor eller avvikelser från Vitki-protokollet), och kalla.json med samma proveniens i
maskinläsbar form.

**Kreditera den som skannat stenen.** Vitki krediterar en öppen skanning (t.ex. Kitzler Åhfeldts och Zedigs serier
på Zenodo) bara när den inlästa filen känns igen som en av datamängdens publicerade filer, på kontrollsumman eller
på filnamn och storlek tillsammans (bara filnamnet räcker inte). Då står vem som skannat, institutionen, projektet, licensen med länk och DOI i varje fil: i
bildernas metadata, som en rad under figurerna, överst i tabellerna och i README.txt. Att skriva in stenens signum
räcker inte, eftersom filen kan vara en annan skanning av samma sten. Känns filen inte igen, fyll i fältet *Skannad
av, institution, licens, DOI*; texten följer då med i filerna, märkt som din. Skicka med README.txt om du delar
filerna vidare.

Vill du ha figurerna med bildtexter, mättabeller, kvalitetskontroll och kända brister i ett och samma dokument,
välj i stället **Skapa stenrapport**. Den innehåller samma bilder och siffror och krediterar skanningen på samma
sätt.

Finns både en automatisk analys och en mätning under resultaten, står det i menyn vilken som exporteras. Knappen
*Exportera …* under en analys väljer den, och i menyn kan du byta.

---

## 4. Analyshistorik & Projekt

Klicka på **Min Forskning** (eller "Projekt") i huvudmenyn.
- Så fort du klickar på "Analysera" sparas ditt tvärsnitt ner till det aktiva projektet.
- Här kan du bygga upp ett bibliotek av analyser (t.ex. spara Snitt 1 från en runa och Snitt 2 från en annan runa).
- Mätningarna exporteras från 3D-sidan under **Exportera** (bilder, mättabeller och hela analysen, se *Exportera bilder och mätdata* ovan), och **Skapa stenrapport** samlar figurer, mättabeller, kvalitetskontroll och kända brister i ett dokument (Word, LaTeX eller Markdown).

---
*Dokumentationen senast uppdaterad för Epigraphix AI (Next.js).*
