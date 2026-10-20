# Vitki

Ett modernt, modulärt och öppet forskningsverktyg för analys av runstenar. Appen består av en webbapp i Next.js och ett Python-API (FastAPI), och syftar till att samla spjutspetsen inom runforskning – från 3D-skannad huggspårsanalys till geografiska informationssystem (GIS) och AI-drivna expertmodeller – i en och samma plattform.

## Projektets Filosofi: Open Source & Runattribuering
Det här projektet drivs av övertygelsen att **forskning och kunskap mår bäst av att vara fri**. Källkoden och verktygen här är helt öppna (Open Source) och släpps fria för forskningens bästa. Syftet är att demokratisera tillgången till avancerade metoder för att vi tillsammans ska kunna lösa arkeologiska och historiska mysterier. 

Ett av appens huvudsakliga mål är **runristarattribuering** – att med hjälp av kvantitativ data (som spårdjup, huggvinklar i 3D-modeller och lingvistiska mönster) samt artificiell intelligens hitta tidigare okända samband mellan olika runstenar. Tänk om vi, tack vare öppen källkod och datadriven analys, kan bevisa att två stenar miltals från varandra faktiskt är huggna av samma obekanta mästare!

## Kör på tio minuter

[examples/so128/](examples/so128/) är ett helt genomfört exempel: en öppen skanning av Sö 128 (Kitzler Åhfeldt, RAÄ,
Zenodo), kommandot som kör hela kedjan och rapporten som kom ut, med figurer. Börja där om du vill se vad appen gör
innan du läser metodbeskrivningen.

## Funktioner

Allt som räknas fram beskrivs i [METHODS.md](METHODS.md) (avsnittsnummer inom parentes). Där AI används
skriver den bara text eller gör en uttalat okalibrerad bedömning; siffror, tabeller och figurer räknas fram.

**Analys**
*   **Fullständig stenanalys** (15c)**:** ladda upp en skanning och ange signum – appen tar fram bilder ur skanningen, mäter huggspåren med känslighetsanalys, låter AI gissa stilgruppen, läser luckorna med sannolikhetsmodellen, väger samman beläggen och skriver en artikel med alla figurer och en bilaga om hur analysen gjordes.
*   **3D-huggspårsanalys** (2–4)**:** V-vinkel, asymmetri, djup, bredd, bottenradie och ytråhet i STL/OBJ/PLY-skanningar – manuellt, med ett klick per snitt eller helt automatiskt (spåren på den ristade sidan hittas och bara de som känns igen som runor mäts – ornamentik, slingkanter och naturliga sprickor sorteras bort; stenens medelvärden redovisas med runan som enhet, och appen säger till om färre än 10 runor är mätta). Varje snitt redovisas med spridning och konfidensintervall, och snittens position, riktning och råprofil sparas. Strykljus med valfri ljusriktning, lättare visningsmodell för stora skanningar, export till CSV/JSON och full proveniens (filens SHA-256, parametrar, metodversion).
*   **Bilder ur skanningen** (2d)**:** strykljus från fyra håll, relief och djup under stenytan räknas direkt ur 3D-modellen och öppnas under fliken Bilder och runformer eller går in i stenrapporten.
*   **Bilder och runformer** (12)**:** en flik på 3D-sidan med foton (uppladdade eller från K-samsök), RTI-vyer, reliefer och 3D-analysens ristningskarta. Runutsnitt normaliseras och jämförs efter form med samma runa på andra stenar, och Rundatas stilgrupp visas bredvid bilden. Ingen AI: stilbedömning ur bild prövades 2026-10-20 (exakt stilgrupp rätt i 35 %) och togs bort.
*   **Läsning mot Rundata** (8)**:** en egen läsning kan prövas mot Rundata utan AI (överensstämmelse, täckning, skillnader ord för ord, ordformer, ortografi, validering mot kända inskrifter). Vitki läser inte runor med AI; den blinda AI-läsningen togs bort 2026-10-20 efter prov (METHODS.md 8).
*   **RTI-visare:** öppna PTM-filer och flytta ljuset fritt, med "diffuse gain"-förstärkning; vyn kan öppnas under Bilder och runformer.

**Forskning**
*   **Syntes och attribuering** (13)**:** väger samman Rundata, ortografi och huggteknik efter metodernas korsvaliderade träffsäkerhet. Varje kandidat prövas mot litteraturen (stämmer, nytt, motsäger), geografi, ristarens stilgrupper och datering, bergart, språkdrag, inskriftstyp och – om ristarens stenar är uppmätta – sten mot sten. Motsägelser och saknade belägg redovisas; inga påhittade sannolikheter. Syntesen sparas i projektet.
*   **Inskrifter (Rundata)** (17)**:** hela Samnordisk runtextdatabas inbyggd – sök på signum, plats, text, ristare, stilgrupp, period, inskriftstyp och forskningsluckor. Varje inskrift visar ortografiskt lika ristare (med p-värde), språkdrag, inskriftstyp och berggrund.
*   **Ortografisk stilometri** (7)**:** stavning, skiljetecken och bindrunor jämförs med ristarnas inskrifter; likheten redovisas med p-värde och metoden med korsvaliderad träffsäkerhet.
*   **Språkdrag** (9)**:** elva definierade drag i fonetisk stil (diftonger, nasaler, h-bortfall, stungna runor) och språkbruk (stavning av vanliga ord, böner, signaturer) jämförs med ristarens inskrifter.
*   **Inskrifternas syfte** (10)**:** minnessten, självminne, bro och väg, kristen bön, utlandsfärd, arv, ting, magisk/rituell och gräns – per ristare med test mot genomsnittet.
*   **Bergart och berggrund** (11)**:** stenens material jämförs med SGU:s berggrundskarta på platsen och inom 10 km och med bergarterna på ristarens stenar.
*   **Delad mätkorpus** (5)**:** forskare publicerar huggspårsmätningar (CC BY 4.0) som blir referens för attribuering, ristarprofiler och Ward-klustring. Posterna kan bära skanningsmetadata, stenens skick, råa tvärsnittsprofiler (omräkning med nya metodversioner) och runformer; andra forskare kan verifiera dem. Export som datapaket.
*   **Statistik i R** (1)**:** hela korpusen analyserad i R – ristarnas områden och avstånd till vatten (sf), klustring och MCA (cluster, FactoMineR), formler och stavning (tidytext, stringdist), en korsvaliderad attribueringsmodell (tidymodels, random forest), seriation mot Gräslunds kronologi (ca), formelnätverk och släktrelationer (igraph) samt landskapet kring en sten (höjdmodell, sikt, strand vid vikingatiden och bästa vägar med terra och gdistance). Resultaten bakas in i stenanalysen och stenrapporten, blir fynd i Forskningsluckor och kan laddas ner som reproducerbarhetspaket med R-skript och data.
*   **Forskningsluckor** (14)**:** täckning per landskap med klickbara siffror, appens resultat mot befintlig forskning (stämmer, nytt, motsäger, med uppskattning av belägg, nyhet och relevans, och avstämning mot Runor 2020 och Wikidata), inskrifternas syfte per ristare, ortografiska hypoteser, attribueringar att ompröva och vilka ristare som mest behöver mätas. Alla tabeller kan sorteras.
*   **Rapporter** (15)**:** stenrapport i artikelform (runologisk presentation enligt SRI/Futhark, 3D-paradata, figurer ur skanningen, läsning och attribuering) och korpusrapport för flera stenar. Export till Word, LaTeX och Markdown.
*   **Jämför stenar** (4)**:** permutationstest per mått och samlat, effektstorlek och överlagrade profiler.
*   **Karta och stilgrupper:** geografisk spridning per period, stilgrupp och ristare; Gräslunds kronologi med fördelningen i Rundata.

**Resurser**
*   **AI-assistent** med tillgång till Rundata och den senaste analysen, **Runologiskt arkiv** och **dokumentation** i appen.

## Arkitektur

| Del | Teknik | Mapp |
|---|---|---|
| Webbapp (huvudgränssnitt) | Next.js + React, Firebase (inloggning/projekt) | `web/` |
| Backend-API | Python, FastAPI, Claude/Gemini | `api/`, `src/` |
| Statistik | R (sf, tidymodels, ranger, tidytext, FactoMineR, ca, stringdist, igraph, terra, gdistance) | `r/` |
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
3. Skapa en `.env` i projektroten (läses av backend, bara för lokal utveckling – i appen anger varje användare
   sin egen nyckel under Inställningar):
   ```bash
   ANTHROPIC_API_KEY=sk-ant-...   # Claude (standard)
   GEMINI_API_KEY=AIza...         # valfritt alternativ
   ```
4. Bygg Rundata-filen (laddar ner Samnordisk runtextdatabas, ca 2 MB):
   ```bash
   .venv/bin/python -m scripts.build_rundata
   ```
5. Statistik i R (valfritt men rekommenderat) – installera R och paketen. På macOS:
   ```bash
   brew install r gdal geos proj udunits pandoc cmake fribidi harfbuzz
   Rscript r/install.R
   ```
   Utan R fungerar appen som förut; sidan Statistik (R) och R-avsnitten i rapporten visas då inte.
   Obs: `brew install` kan uppgradera Homebrews Python. Om `.venv` slutar fungera, installera tillbaka
   den Python-version miljön skapades med (t.ex. `brew install python@3.13`).
6. Webbappen – installera beroenden och lägg Firebase-konfigurationen i `web/.env.local`
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
| `AI_PROVIDER` | api | `claude` om en Anthropic-nyckel finns, annars `gemini` | Standardmodell när webbläsaren inte anger någon |
| `CLAUDE_PRO_MODEL` / `CLAUDE_FAST_MODEL` | api | `claude-opus-5-5` / `claude-haiku-4-5-20251001` | Vilka Claude-modeller som används |
| `GEMINI_PRO_MODEL` / `GEMINI_FLASH_MODEL` | api | `gemini-pro-latest` / `gemini-flash-latest` | Vilka Gemini-modeller som används |
| `MAX_MESH_UPLOAD_MB` / `MAX_IMAGE_UPLOAD_MB` | api | `500` / `20` | Storleksgränser för uppladdningar |
| `MAX_VIEW_FACES` | api | `1500000` | Max antal ytor i den förenklade visningsmodellen för stora skanningar |
| `RUNDATA_PATH` | api | `data/rundata.json` | Sökväg till den byggda Rundata-filen |
| `MESH_CACHE_SIZE` | api | `2` | Antal uppladdade 3D-modeller som hålls i analysmotorns minne |
| `GEOLOGY_CACHE` | api | `data/cache/geology.json` | Cache för uppslag i SGU:s berggrundskarta |
| `GEOLOGY_DISABLED` | api | – | `1` stänger av berggrundsuppslag (används i testerna) |
| `RSCRIPT` | api | `Rscript` i PATH | Sökväg till Rscript |
| `R_DISABLED` | api | – | `1` stänger av statistiken i R (används i testerna) |
| `R_CACHE_DIR` | api | `data/cache/r` | Var korpus-, sten- och landskapsanalyserna i R sparas |
| `CROSSCHECK_DISABLED` / `CROSSCHECK_CACHE` | api | – / `data/cache/crosscheck` | Avstämning mot Runor 2020 och Wikidata |

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

Korpusen (verifiering, råprofiler och runformer) kräver reglerna i `web/firestore.rules`. Publicera dem med
Firebase CLI när de ändras:
```bash
cd web && npx firebase-tools deploy --only firestore:rules
```

## Citering och DOI

Citera enligt [CITATION.cff](CITATION.cff). För en citerbar DOI: koppla GitHub-repot till
[Zenodo](https://zenodo.org/account/settings/github/) och skapa en release – metadata hämtas från `.zenodo.json`.
Uppgifter ur Rundata ska citeras som Samnordisk runtextdatabas (se [data/README.md](data/README.md)).

## Tester

```bash
.venv/bin/python -m pytest          # backend, 3D-analys, rapporter, syntes och forskningsfunktioner
cd web && npx tsc --noEmit && npm run lint
```

## Om Grundaren

Projektet är grundat av **Viktor Kvant**. Till vardags arbetar Viktor som digital analytiker, men ser dataanalys som ett övergripande yrkesfält där samma analytiska metoder, AI-modeller och tekniker kan appliceras för att driva gränserna framåt även inom humaniora och arkeologi.

## Licens

Copyright © 2026 Viktor Kvant.

Detta projekt är släppt under **GNU General Public License v3.0 (GPL-3.0)** med tilläggsvillkor enligt licensens
§ 7, se `NOTICE`. Du är fri att använda, ändra och distribuera koden, förutsatt att ändringar också släpps under
samma licens och att

* upphovsangivelsen *"Bygger på Vitki, ursprungligen utvecklad av Viktor Kvant (https://github.com/Precatio/runes)"*
  bevaras i källkoden och syns i användargränssnittet (§ 7 b),
* ingen framställer kodbasen eller grunden för den som sitt eget verk, och ändrade versioner märks som ändrade
  (§ 7 c), och
* en ändrad version inte ges ut under namnet Vitki, utan som "baserad på Vitki" (§ 7 e).

Se `LICENSE` för licenstexten och `NOTICE` för tilläggsvillkoren. Använder du programmet i forskning, citera det
enligt `CITATION.cff`.
