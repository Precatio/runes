# Analysplan: självkontroll – står stengrupperna vid gravfälten också när gravfälten granskas?

Skriven och låst 2026-11-10, innan något av proven nedan har räknats och innan registrets nya fält har lagts mot
stenarna. Gäller ett redan publicerat resultat: analysplaner/2026-10-29-familjens-plats.md (resultat
`utdata/familjens_plats/resultat.md`), publicerat i forskningsrapporten ”Runstenarna samlas i familjegrupper vid
gravfälten” (avsnitt 5.3, DOI 10.5281/zenodo.24004794) och i Familjens plats-texten i `web/content/articles.json`.

## Påståendet som prövas
”82 procent av stenarna i grupp har ett gravfält inom 500 meter, mot 55 procent av de ensamma.” Exakt definition i
koden (`utdata/familjens_plats/data.py`, `analys.R`): svenska runstenar på sin plats (`moved = 0`, `lost = 0`, korpus
3f58e9339191761e); **i grupp** = annan sten på plats 25–500 m bort, **ensam** = närmaste sten på plats mer än 1 000 m
bort. Utfall: någon post med lämningstypen *gravfält* i Kulturmiljöregistret (`data/raa/lamningar.csv`) inom 500 m.
Logistisk regression med landskap, tidsskikt och lokal runstenstäthet; oddskvot 2,4 [1,5–3,8], p 0,0002, Holm 0,003,
båda halvorna. Jämförelsen är grupp mot ensam sten, inte mot slumpvisa platser.

## Invändningarna (ur litteraturgenomgången av Fornvännen, `utdata/litteraturgenomgang/SYNTES.md`)
- **(a) Typerna:** registrets gravfält blandar gravformer, och flacka runda stensättningar och rösen är svåra att skilja
  från röjningsrösen (Häggström 2002).
- **(b) Åldern:** många gravfält är äldre (romersk järnålder, folkvandringstid, vendeltid) eller använda under flera
  perioder; ett gravfält vid en sten behöver inte vara samtida med den (Ambrosiani 1968, Holmqvist 1957, Arrhenius).
- **(c) Inventeringen:** registrets täckning beror på när och hur varje län inventerades.

## Vad registret har (kontrollerat 2026-11-10, bara tillgång, inga samband med stenarna)
- `lamningar.csv` har bara id, lämningstyp, punkt, landskap och lämningsnummer (18 633 gravfält). Ingen datering, ingen
  bedömning, inga ingående gravar, inget län.
- K-samsök (RDF-posten för varje id, stickprov 400 gravfält) har dessutom: **Antikvarisk bedömning** (Fornlämning 372,
  Ingen antikvarisk bedömning 25, Möjlig fornlämning 3), **Aktualitetsstatus** (Bekräftad i fält 389, Uppgift om
  lämning, ej bekräftad i fält 10), **Ingående lämningar** (strukturerat: typ, form, konstruktion och antal, t.ex.
  ”Stensättning – Form: Treudd, antal 3”; finns i 397 av 400), **Undersökningsstatus** (Okänd 316, Ej undersökt 51,
  Delundersökt 21, Helt undersökt 12), **län** (`countyName`), socken, terräng och fri beskrivning.
- **Ingen dateringsuppgift.** Inget fält för datering eller period finns i någon av de 400 posterna. Den fria
  beskrivningen nämner en period i ett fåtal (”vikingatid” 4 av 400, ”yngre järnålder” 1), för få att bygga på.
- **Inget inventeringsår.** Årtalet i lämningsnumret (L1957:…) är inte inventeringsåret (t.ex. L2012 för ”Raä:s inv
  1946”, L1977 för ”Raä inv 1939”); inventeringsår finns bara ibland i fri text under ”Referens: skriftlig källa”.

## Vad som kan och inte kan prövas
- **(a) kan prövas** med bedömning, aktualitetsstatus och ingående gravformer (K1). Gravarnas storlek finns bara i fri
  text och används inte.
- **(b) kan inte prövas som invändningen kräver.** Registret har ingen datering, så ”bara gravfält med vikingatida
  datering” går inte att göra, och samtidighet mellan sten och gravfält kan inte visas med dessa data. Det som går är
  ett **typologiskt ersättningsmått** (K2): gravfält med former som i Mälardalen räknas till yngre järnålder (ca
  550–1050, alltså också vendeltid). Det skiljer inte flerperiodiga gravfält från rena.
- **(c) kan prövas på länsnivå** (K3a), och finare skillnader i registrets täthet med ett täthetsmått (K3b). Inventeringsår
  per län eller socken kan inte tas fram ur strukturerade fält; länets fasta effekt tar upp allt som är lika inom länet,
  också när det inventerades.

## Data
- **Stenarna:** exakt samma tabell som i originalet (`utdata/familjens_plats/stenar.csv`, korpus 3f58e9339191761e):
  samma 657 stenar (185 i grupp, 472 ensamma), samma kontroller, samma halvor (socken för socken inom landskapet).
- **Gravfälten:** samma 18 633 id som i `lamningar.csv`. För varje id hämtas RDF-posten ur K-samsök (en gång, med paus
  mellan anropen) och fälten ovan skrivs till `data/raa/gravfalt_detaljer.csv`. Id som inte längre finns i K-samsök får
  inga detaljer och räknas bara i P0. Antalet gravfält i varje klass nedan räknas och skrivs i
  `utdata/familjens_plats/sjalvkontroll/klasser.csv` **innan** de läggs mot stenarna.
- **Stenarnas län:** länet i stenens egen KMR-post (`data/raa/kmr_runstenar.json`, signum → kmr_id, länet hämtas ur
  K-samsök). Stenar utan KMR-post får länet för närmaste gravfält i samma landskap. Hur många som fick länet på vilket
  sätt redovisas.

## Klasserna (bestämda nu)
- **Granskat gravfält (V):** Antikvarisk bedömning = Fornlämning, Aktualitetsstatus = Bekräftad i fält, och minst en
  ingående grav av en **säker gravform**: hög (alla former), grav markerad av sten/block (alla typer), stenkrets/stenrad
  (alla former, t.ex. domarring, skeppssättning), stenkammargrav, eller stensättning med formen treudd, kvadratisk,
  rektangulär, triangulär eller skeppsformig. **Inte säkra** (kan förväxlas med röjningsrösen): stensättning med formen
  rund, oval, oregelbunden, övrig eller utan form, och röse (alla former). Ett gravfält med bara sådana gravar är inte V.
- **Yngre järnålderns former (Y):** V och minst en ingående stensättning med formen treudd eller kvadratisk, eller
  stenkrets/stenrad med formen kvadratisk. (Skeppssättningar räknas inte: en del är från bronsåldern.)

## Prov
Samma modell som originalet (`analys.R`, funktionen `fit`): utfall ~ i grupp + landskap + tidsskikt + lokal täthet,
landskap med under 10 stenar ihopslagna. Bara utfallet byts, om inget annat sägs.

**P0 (replikering, villkor för resten).** Originalet körs om oförändrat. Måste ge 82 mot 55 %, oddskvot 2,4 och p 0,0002
(avrundat som i resultat.md). Gör det inte det avbryts allt och skillnaden redovisas.

**K1 (invändning a).** Utfall: granskat gravfält (V) inom 500 m.

**K2 (invändning b, ersättningsmått).** Utfall: gravfält med yngre järnålderns former (Y) inom 500 m.

**K3a (invändning c).** Utfall som originalet (alla gravfält), men **län** i stället för landskap som fast effekt (län
med under 10 stenar ihopslagna, som landskapen).

**K3b (invändning c, finare).** Som K3a, plus log(1 + antal registrerade gravfält 1–5 km från stenen), alltså hur tätt
registret har gravfält i stenens omgivning utanför utfallets 500 m.

**Bedömning för varje prov (Holm över K1, K2, K3a, K3b):**
- **Står sig:** oddskvot > 1, Holm-p < 0,05, och i båda halvorna oddskvot > 1 med p < 0,05 (samma krav som originalets
  ”håller”).
- **Försvagas:** oddskvot > 1 och okorrigerat p < 0,05, men inte allt ovan.
- **Faller:** oddskvot ≤ 1 eller okorrigerat p ≥ 0,05.
- **Kan inte prövas:** färre än 20 stenar med utfallet eller färre än 20 utan det, i grupp eller bland de ensamma.

**Robusthet (beskrivande, ingen bedömning):** K1 utan ”grav markerad av sten/block” bland de säkra formerna (en rest
sten i ett gravfält kan vara runstenen själv); K1 med bara 250 m; K1 och K3a tillsammans (V som utfall, län som fast
effekt, gravfältstätheten med); bara Uppland och Södermanland för K1–K3b. Andelarna (grupp mot ensam) redovisas för
varje prov bredvid oddskvoten.

## Tolkning (bestämd nu)
- **Det publicerade resultatet står sig** om K1, K3a och K3b alla står sig. Då kan rapporten säga att sambandet håller
  med bara granskade gravfält och inom länen.
- **Det försvagas** om något av de tre försvagas men inget faller. Rapporten anger då vilken invändning som försvagar
  det, och 82/55 får inte stå utan det förbehållet.
- **Det faller** om något av de tre faller. Då rättas avsnitt 5.3 i rapporten och texten i articles.json, med det nya
  utfallet och skälet.
- **K2** avgör bara formuleringen om tid. Står det sig kan rapporten säga att grupperna också står vid gravfält med
  yngre järnålderns former. Faller det eller försvagas det får rapporten inte antyda att gravfälten är samtida med
  stenarna eller ”gårdens gravfält” från samma tid. Oavsett utfall skrivs det ut att registret saknar datering och att
  samtidighet inte kan visas med dessa data.

## Redovisning
`utdata/familjens_plats/sjalvkontroll/`: `hamta_gravfalt.py` (K-samsök → `data/raa/gravfalt_detaljer.csv`),
`klasser.csv`, `data.py`, `analys.R`, `resultat.json`, `resultat.md`. Utfallet förs in i rapporten (ny version på
Zenodo med `zenodo_rapporter.py --ny-version`) först när Viktor sagt till, oavsett om det står sig eller faller.
