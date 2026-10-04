# Runforskning (Aagaard Research)

Ett modernt, modulärt och öppet forskningsverktyg för analys av runstenar. Appen består av en webbapp i Next.js och ett Python-API (FastAPI), och syftar till att samla spjutspetsen inom runforskning – från 3D-skannad huggspårsanalys till geografiska informationssystem (GIS) och AI-drivna expertmodeller – i en och samma plattform.

## Projektets Filosofi: Open Source & Runattribuering
Det här projektet drivs av övertygelsen att **forskning och kunskap mår bäst av att vara fri**. Källkoden och verktygen här är helt öppna (Open Source) och släpps fria för forskningens bästa. Syftet är att demokratisera tillgången till avancerade metoder för att vi tillsammans ska kunna lösa arkeologiska och historiska mysterier. 

Ett av appens huvudsakliga mål är **runristarattribuering** – att med hjälp av kvantitativ data (som spårdjup, huggvinklar i 3D-modeller och lingvistiska mönster) samt artificiell intelligens hitta tidigare okända samband mellan olika runstenar. Tänk om vi, tack vare öppen källkod och datadriven analys, kan bevisa att två stenar miltals från varandra faktiskt är huggna av samma obekanta mästare!

## Funktioner

**Analys**
*   **3D-huggspårsanalys:** V-vinkel, asymmetri, djup, bredd, bottenradie och ytråhet i STL/OBJ/PLY-skanningar – manuellt, med ett klick per snitt eller helt automatiskt (alla spår på den ristade sidan hittas, mäts och granskas). Varje snitt redovisas med standardavvikelse och konfidensintervall. Runor och ornamentik mäts separat. Strykljus med valfri ljusriktning, lättare visningsmodell för stora skanningar, export till CSV/JSON och full proveniens (filens SHA-256, parametrar, metodversion).
*   **2D-paleografi och fonetik:** AI-stöd för stilgrupp, runformer, translitterering och ljudvärden. Bilder från uppladdning, K-samsök, 3D-vyn, RTI-visaren eller 3D-analysens ristningskarta. Runutsnitt normaliseras och jämförs med samma runa på andra stenar (formlikhet), och kopplas till spårmåtten när de kommer från en ristningskarta.
*   **RTI-visare:** öppna PTM-filer och flytta ljuset fritt, med "diffuse gain"-förstärkning för svaga ristningar.

**Forskning**
*   **Inskrifter (Rundata):** hela Samnordisk runtextdatabas inbyggd – sök på signum, plats, text, ristare, stilgrupp och period.
*   **Ortografisk stilometri:** stavning, skiljetecken och bindrunor jämförs med Rundatas korpus; ristarrangordning med redovisad, korsvaliderad träffsäkerhet.
*   **Delad mätkorpus:** forskare publicerar huggspårsmätningar (CC BY 4.0) som blir referens för attribuering, ristarprofiler och Ward-klustring. Posterna kan bära skanningsmetadata, stenens skick, råa tvärsnittsprofiler (för omräkning med nya metodversioner) och runformer; andra forskare kan verifiera dem. Export som datapaket.
*   **Forskningsluckor:** täckning per landskap (ristare, stilgrupp, datering, tolkning, mätningar), ortografiska ristarhypoteser för oattribuerade stenar, attribueringar att ompröva och vilka ristare som mest behöver mätas. Appens resultat (ortografi, huggteknik, AI-stilgrupp) ställs mot Rundata – stämmer, nytt eller motsäger – med en redovisad uppskattning av belägg, nyhet och relevans. Alla tabeller kan sorteras.
*   **Akademisk rapport:** stenrapport i artikelform för en sten (runologisk presentation enligt SRI/Futhark, 3D-paradata, figurer räknade ur skanningen: strykljus, djupkarta, snittpositioner, tvärsnittsprofiler, fördelningar och jämförelse med korpusen) och korpusrapport för flera stenar. Export till Word, LaTeX och Markdown; AI-skrivna avsnitt märks.
*   **Jämför stenar:** permutationstest per mått och samlat, effektstorlek och överlagrade profiler.
*   **Syntes och rapport:** väger samman Rundata, ortografi och huggteknik till belägg utan påhittade sannolikheter; AI skriver bara löptext.
*   **Karta och stilgrupper:** geografisk spridning per period, stilgrupp och ristare; Gräslunds kronologi med fördelningen i Rundata.

Metoderna beskrivs i [METHODS.md](METHODS.md).

## Arkitektur

| Del | Teknik | Mapp |
|---|---|---|
| Webbapp (huvudgränssnitt) | Next.js + React, Firebase (inloggning/projekt) | `web/` |
| Backend-API | Python, FastAPI, Gemini/OpenAI | `api/`, `src/` |
| Äldre prototyp | Streamlit | `app.py`, `modules/` |

## Systemkrav & Installation

Kräver Python 3.11+ (utvecklas på 3.13) och Node.js 20+.

1. Klona eller ladda ner repot.
2. Backend – skapa en virtuell miljö och installera beroenden:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # (Eller .venv\Scripts\activate på Windows)
   pip install -r requirements.txt
   ```
3. Skapa en `.env` i projektroten (läses av backend):
   ```bash
   GEMINI_API_KEY=din-nyckel-här
   ```
4. Bygg Rundata-filen (laddar ner Samnordisk runtextdatabas, ca 2 MB):
   ```bash
   .venv/bin/python -m scripts.build_rundata
   ```
5. Webbappen – installera beroenden och lägg Firebase-konfigurationen i `web/.env.local`
   (`NEXT_PUBLIC_FIREBASE_*`):
   ```bash
   cd web && npm install
   ```

### Valfria miljövariabler

| Variabel | Var | Standard | Beskrivning |
|---|---|---|---|
| `NEXT_PUBLIC_API_URL` | web | `http://localhost:8000` | Backend-API:ts adress |
| `PROXY_IMAGE_ALLOWED_HOSTS` | web | – | Extra värdar (kommaseparerade) som bildproxyn får hämta från |
| `CORS_ORIGINS` | api | `http://localhost:3000` | Tillåtna ursprung (kommaseparerade) |
| `GEMINI_PRO_MODEL` / `GEMINI_FLASH_MODEL` | api | `gemini-pro-latest` / `gemini-flash-latest` | Vilka Gemini-modeller som används |
| `MAX_MESH_UPLOAD_MB` / `MAX_IMAGE_UPLOAD_MB` | api | `500` / `20` | Storleksgränser för uppladdningar |
| `MAX_VIEW_FACES` | api | `1500000` | Max antal ytor i den förenklade visningsmodellen för stora skanningar |
| `RUNDATA_PATH` | api | `data/rundata.json` | Sökväg till den byggda Rundata-filen |
| `MESH_CACHE_SIZE` | api | `2` | Antal uppladdade 3D-modeller som hålls i analysmotorns minne |

API-nycklar som anges i webbappens inställningar sparas bara lokalt i webbläsaren.

## Användning

Starta backend och webbapp i var sin terminal:
```bash
# Terminal 1 – backend (från projektroten)
.venv/bin/uvicorn api.main:app --reload --port 8000

# Terminal 2 – webbapp
cd web && npm run dev
```
Öppna sedan http://localhost:3000.

Den äldre Streamlit-prototypen kan fortfarande startas med `./run_app.sh`.

### Delad mätkorpus (Firestore)

Korpusen kräver de uppdaterade reglerna i `web/firestore.rules`. Publicera dem med Firebase CLI:
```bash
cd web && npx firebase-tools deploy --only firestore:rules
```

## Citering och DOI

Citera enligt [CITATION.cff](CITATION.cff). För en citerbar DOI: koppla GitHub-repot till
[Zenodo](https://zenodo.org/account/settings/github/) och skapa en release – metadata hämtas från `.zenodo.json`.
Uppgifter ur Rundata ska citeras som Samnordisk runtextdatabas (se [data/README.md](data/README.md)).

## Tester

```bash
.venv/bin/python -m pytest          # backend och 3D-analys
cd web && npx tsc --noEmit && npm run lint
```

## Om Grundaren

Projektet är grundat av **Viktor Kvant**. Till vardags arbetar Viktor som digital analytiker, men ser dataanalys som ett övergripande yrkesfält där samma analytiska metoder, AI-modeller och tekniker kan appliceras för att driva gränserna framåt även inom humaniora och arkeologi.

## Licens

Detta projekt är släppt under **GNU General Public License v3.0 (GPL-3.0)**. 
Du är fri att använda, ändra och distribuera koden, förutsatt att alla ändringar också släpps under samma öppna licens. Se filen `LICENSE` för den fullständiga licenstexten.
