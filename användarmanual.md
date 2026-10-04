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
uvicorn api.main:app --reload
```

**Starta Web UI (Next.js):**
```bash
cd web
npm run dev
```
Applikationen kommer då att öppnas automatiskt i din webbläsare på `http://localhost:3000`.

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

---

## 4. Analyshistorik & Projekt

Klicka på **Min Forskning** (eller "Projekt") i huvudmenyn.
- Så fort du klickar på "Analysera" sparas ditt tvärsnitt ner till det aktiva projektet.
- Här kan du bygga upp ett bibliotek av analyser (t.ex. spara Snitt 1 från en runa och Snitt 2 från en annan runa).
- Du kan generera rapporter, visa sammanslagna insikter från runologen, exportera till CSV, samt köra avancerade AI-synteser (Gemini) för att bedöma sannolikheten att flera olika mätbanor delar upphovsman (samma ristare).

---
*Dokumentationen senast uppdaterad för Epigraphix AI (Next.js).*
