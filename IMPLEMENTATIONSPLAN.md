# Implementationsplan 2026-10-20 → framåt

Planen bygger på läget efter 2026-10-20 (AI-läsningen borttagen, 2D som flik, huggteknik mot bergart, etiketter,
första Så gör du-artikeln). Varje punkt har: vad, var i koden, hur den prövas, och vad som bara Viktor kan göra.
Ordningen är vald så att varje steg gör nästa mer värt. Inget här är påbörjat.

Regler som gäller alla punkter: data före tolkning (ingen egen läsning), bara runstenar i beräkningarna, justera för
period och region, varje statistiskt tal förklaras i klartext, bristlistan (`src/limitations.py`) och METHODS.md
uppdateras i samma commit som koden, publicerade artiklar patchas bara via Firestore.

---

## Fas 1 – Trovärdig för en kollega

### 1.1 Facit för runigenkänningen  (Viktor: märkning; en session för resten)
- **Viktor:** märk 8–10 stenar i facit-läget på 3D-sidan (inte Sö 113 och Sö 128, som reglerna justerats på).
  Förslag ur KÅ-serien med många runor och olika bevarande: Sö 134, 137, 143, 161, 207, 211, 319, 367, Fv1948;282,
  Fv1973;189. Spara facit-JSON i `utdata/facit/`.
- **Kod:** `scripts/evaluate_rune_detection.py` körs mot facit med låsta regler (ingen justering efter resultatet).
  Rapportera precision/recall per sten och samlat, per bergart.
- **Leverans:** siffran in i bristlistan (`rune_detection`), METHODS 2c, och en rad i granskningsrutan
  ("runigenkänningen träffar X % av runorna, Y % av det mätta är runor").
- **Klart när:** evaluate-skriptet ger ett tal på ≥ 8 stenar och testet `tests/test_auto_grooves.py` låser att
  reglerna inte ändrats sedan facit (hash av `classify_strokes`-parametrarna).

### 1.2 Test–omtest av huggspårsmåtten  (Viktor: skanning; halv session)
- **Viktor:** hitta eller gör två oberoende skanningar av samma sten (olika tillfälle, helst olika utrustning).
  Alternativ: fråga RAÄ/KÅ om någon sten skannats två gånger.
- **Kod:** `scripts/groove_robustness.py` får ett läge `--retest A.stl B.stl`: samma protokoll på båda, per-sten
  ICC för vinkel/djup/bredd, och andel snitt som återfinns inom 3 mm.
- **Leverans:** bristposten `reliability` får ett mätt tal; riktvärdena 10/20 runor räknas om om spridningen
  motiverar det (`web/src/lib/mesh.ts`, `src/limitations.py`).

### 1.3 Fyll mätkorpusen  — KLAR 2026-10-20 (37 poster, scripts/corpus_seed_ka.py)
- Mät de 36 KÅ-stenarna med protokollet (groove-5, `utdata/Rak/referenser_g5` finns) och lägg in dem i Firestore
  `corpus` som Riksantikvarieämbetets/KÅ:s data under CC BY, med scan-credit (DOI 10.5281/zenodo.11951255).
- **Kod:** ett skript `scripts/corpus_seed_ka.py` som skriver posterna via adminklienten med `contributorUid` = ditt,
  `feature_type: rune`, `means`, `slices`, provenance. Idempotent (signum + method_version som nyckel).
- **Kontroll:** "Jämför med mätkorpusen" på 3D-sidan ger ranking; `material_top1` syns; tillförlitligheten blir ≈ 0
  (som i dag) – det är rätt resultat och ska stå så.
- **Klart när:** Statistik/mätkorpus visar 36 poster och syntesen för en KÅ-sten väger in huggteknik med redovisad nivå.

### 1.4 Textmodell 19 – toleranslagret  — PÅGÅR 2026-10-20: lagret byggt (avstängt), analysplan låst, λ-val på veck 0 kör
- Underlag: `utdata/runlm_forfining/tolerans_diagnos.md` (rank-null-missar = obelagda stavningsvarianter).
- **Kod:** `src/runlm.py`: ett toleranslager som vid rankning accepterar belagda stavningsalternativ per lemma
  (ur ordförrådet, inte påhittade), med vikt som kalibreras.
- **Validering, allt låst innan resultat ses:** full 5-faldig korsvalidering, dok5 hålls utanför, mask4-generationen,
  omkalibrering (`scripts/runlm_calibrate.py`), blindtestet körs om (`scripts/blindtest.py`).
- **Leverans:** `data/runlm_calibration.json` ny version, panelversion `textmodel-19`, CHANGELOG, METHODS 8.1,
  modellartikeln "Runorna som fattas" uppdateras bara om den är opublicerad (annars Firestore-patch).
- **Avbryt om:** maskeringsprovet inte förbättras eller blindtestet tappar täckning – då redovisas det som negativt.

---

## Fas 2 – Ta bort det som inte bär

### 2.1 Stilbedömningen (AI)  — KLAR 2026-10-20 (borttagen)
- Beslut Viktor: behålla som "gissning inom grov klass" eller ta bort. Rekommendation: ta bort.
- Om borttagning: `api/routers/twod.py` `/analyze` och `TwoDAIResult`, stenanalysens steg `twod`,
  `TwoDAnalysis.tsx` resultatkortet och `StyleFacts`, `scripts/full_stone_analysis.py`, METHODS 12, README,
  CHANGELOG, bristposten `ai`. Rundatas stilgrupp visas i stället direkt i fliken.

### 2.2 Egen läsning: fält eller bort  — KLAR 2026-10-20 (alternativ A: fält i Syntes)
- Alternativ A (rekommenderas): ett textfält "Egen läsning (translitterering)" i Syntes, skickas som `reading`
  till `/api/synthesis/analyze` och `/api/reports/stone`; valideras av `src/reading.validate` som i dag.
- Alternativ B: ta bort `reading`-spåret ur `api/routers/synthesis.py`, `reports.py`, `src/stone_report.py`,
  `src/synthesis.orthography_from_reading`, `web/src/lib/stoneReport.ts`, `linguisticResults` i `db.ts`, och
  `api/routers/phonetics.py` helt (tester i `test_api.py`, `test_research_features.py` tas bort).

### 2.3 Runformsjämförelsen  (väntar på 1.1)
- När facit finns: klipp utsnitt ur facit-stenarnas ristningskartor, jämför närmaste granne mot facitets runa.
  Ger en träff på riktiga stenar att sätta bredvid 85 % på syntetiska. Under 50 % → ta bort funktionen.

### 2.4 AI-text och AI-chatt  — KLAR 2026-10-20 (AI-text tillval, framräknad text standard; chatten kvar)
- Inventera var AI skriver löptext (syntes, rapporter, assistenten). Behåll bara där texten är märkt och
  ersättningsbar av framräknad formulering (finns redan som fallback). Rekommendation: behåll fallback som standard,
  AI-text som tillval.

### 2.5 Lintfel  — KLAR 2026-10-20 (0 fel, 0 varningar)
- De fem setState-i-effekt-felen (ShareArticle, ArticleSearch, 2D-sidan/TwoDAnalysis, m.fl.): skriv om till
  `useSyncExternalStore` eller härledd state, som LabelFilter gjordes 2026-10-20.

---

## Fas 3 – Nya resultat

### 3.1 Forskningsluckor: textmodellens luckor som flik  — KLAR 2026-10-20 (flik, datumrad, tests/test_methods_numbers.py)
- **Kod:** `api/routers/research.py` ny endpoint `/gaps/textmodel` som läser `utdata/luckartikel/bygg_kandidatlista.py`:s
  utdata (flytta byggskriptet till `src/` eller `scripts/` så att det inte ligger i gitignorerad utdata).
  Flik i `web/src/app/(app)/luckor/page.tsx`: 175 öppna luckor, de 33 kandidaterna ≥ 80 % med känt ord, filter per
  landskap, länk till inskriften och till 3D-panelen "Vad skannern ser" där skanning finns.
- Synlig rad överst på Forskningsluckor: beräkningsdatum, R-fingeravtryck, Rundata-utgåva, textmodellversion.
- Ett test som låser METHODS-siffrorna mot resultatfilerna (som artikelbyggarna gör), så att 1g-fallet
  ("30 stenar" när det var 28) inte återkommer: `tests/test_methods_numbers.py`.

### 3.2 Rundata → Runor 2020  (en session, stor effekt) — DELVIS 2026-10-20: Runor visas bredvid Rundata (src/runor.py, inskriftssidan); själva bytet återstår och kräver analysplan
- Underlag finns: `scripts/fetch_runor.py`, `scripts/runor_compare.py`, 184 flyttade stenar, 43 nya texter.
- **Kod:** `scripts/build_rundata.py` får Runor som primär källa med Rundata 3.1 som fallback per fält; fältet
  `source_version` per inskrift. Alla R-moduler körs om (nytt fingeravtryck). Bristposten `rundata` ändras.
- **Kontroll:** jämför artiklarnas låsta siffror före/efter (byggskripten faller om något ändras – gå igenom
  varje assert och avgör om artikeln ska patchas). Räkna hur många "nya" fynd som redan finns i Runor.

### 3.3 Materialstratifiering överallt  — KLAR 2026-10-20 (R-modellen: Bergart-delmodell 19 % = majoritet; träff per familj i Statistik)
- `r/attribution.R`: korsvalidering grupperad så att material inte läcker; redovisa träff per bergartsfamilj.
- `src/stats.compare_stones` / jämförelsesidan: materialfamiljens referensskala som standard (finns i jämförelsevyn,
  gör den till huvudtal).
- METHODS 1i/4/13 och bristposten `validity`.

### 3.4 Preregistrerade analysplaner  — KLAR 2026-10-20 (ANALYSPLAN.md, METHODS 1x)
- Mall `utdata/<spår>/analysplan.md` + `analysis_plan.sha256` (som Rak-studien). Krav i METHODS 1x: varje artikel
  som gör ett nytt anspråk hänvisar till sin plan och dess hash. Börja med toleranslagret (1.4) och Runor-bytet (3.2).

### 3.5 Okända ristare: litteraturkontroll  (Viktor)
- De fem robusta grupperna (Konungsund, Vetlanda, Leksberg, Husaby, Kölaby) mot Sveriges runinskrifter och
  Östergötlands/Västergötlands runinskrifter. Resultatet in i artikelutkastet `zHgKo0HEjEJPmpooUXpq` innan publicering.

---

## Fas 4 – Användbar för andra

### 4.1 Så gör du-serien  — PÅGÅR: huggspår (nUU578Mmm1BIuq3dZBUv) och inskrifter/luckor (3Uc5chZvfRUCViMpqTwt) forskningsluckor (Y25XTQKplbCbg69mf2ze) och statistik i R som utkast 2026-10-20; kvar: Stenrapport, Syntes (kräver inloggat projekt)
- Ordning: Inskrifter (sök, filter, stenöversikt) → Forskningsluckor → Statistik i R (läsa en modul) →
  Stenrapport (från mätning till Word) → Syntes.
- Varje: `utdata/blogg/build/howto_<namn>_bilder.py` (Playwright, dev-servrar igång) +
  `build_howto_<namn>.py` med etiketterna `Så gör du` + ämne. Engelsk version när svenskan är godkänd.

### 4.2 Exempelpaket  — KLAR 2026-10-20 (examples/so128/)
- `examples/so128/`: skanningen (länk till Zenodo, inte filen), signum, kommandot till
  `scripts/full_stone_analysis.py`, den färdiga rapporten som Markdown. README-avsnitt "Kör på tio minuter".

### 4.3 Citera Vitki och DOI  (när Viktor säger att utvecklingen är klar)
- `RELEASING.md` följs: låst protokollversion (`src/protocol.py` → `vitki-groove-1`), CITATION.cff, Zenodo-DOI.
  Lägg DOI i bristposten `software` och på startsidan.

### 4.4 Löpande
- Bing Webmaster (Viktor), IndexNow-ping vid publicering (finns, kontrollera att den körs).
- Statistikrutorna: kontrollera i Admin efter en vecka att sökningar, delningar och utgående länkar kommer in.

---

## Väntande beslut som planen behöver från Viktor
1. ~~Stilbedömningen~~ – beslutat 2026-10-20: bort.
2. ~~Egen läsning~~ – beslutat: fält i Syntes (A).
3. ~~AI-text~~ – beslutat: tillval.
4. Vilka utkast som publiceras först: Hávamál, Möjliga ristare utan namn (efter 3.5), Så gör du: huggspår,
   Runorna som fattas → därefter Malt.

## Vad som INTE ska göras
- Inga nya AI-funktioner. Ingen funktion utan ett test den kan misslyckas på.
- Inga artiklar som visar modellen fel (Vada förblir opublicerad). Sö 131-errata väntar på besked.
- Inga ändringar i publicerade artiklar annat än via Firestore-patch.
