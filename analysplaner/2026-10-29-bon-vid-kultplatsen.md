# Analysplan: Bönen vid den gamla kultplatsen – sattes den kristna bönen upp där den gamla tron haft sin plats?

Låst 2026-10-29, innan något nedan har räknats. SHA-256 i `analysplaner/2026-10-29-bon-vid-kultplatsen.sha256`.
Kod `utdata/kultplatser/data.py` och `utdata/kultplatser/analys.R`, resultat `utdata/kultplatser/resultat.md`.

## Hypotesen (mönstret cult_prayer i Statistik)
Kristen bön (`cat_kristen`) är vanligare på runstenar inom 2 km från ett teoforiskt ortnamn (gudanamn + sakral
efterled: Torsvi, Odensala, Ullevi, Frösö): 32 % mot 14 % (oddskvot 2,63; 56 stenar vid 18 namn). Förslaget: kristna
böner sattes upp demonstrativt vid de gamla kultplatserna, inte bara där eliten bodde.

## Känt före låsningen (räknat tidigare, redovisas som det är)
- Radien: 1 km oddskvot 2,79 (p 0,08, 15 stenar), 3 km 1,29 (p 0,32). Mönstret hänger på radien 2 km.
- Utan vald radie (Landskapsgenomsökningen, log2 av avståndet): bön oddskvot 1,26 per halvering, p 0,014, q 0,22,
  inte i båda halvorna.
- Robusthetstrappan (2026-10-29): håller rått, justerat, med ristare och socken som slumpeffekter och utan flyttade
  stenar, men inte i halva B och inte utan Södermanland.
- Centralortsnamn (Husby, -tuna): ingen skillnad (oddskvot 0,95); med dem konstant består skillnaden (2,63).
- Med tiden konstant (daterade stenar): oddskvot 2,71, p 0,012.
- Teofora namn ligger oftare nära en medeltida kyrka än andra ortnamn av samma slag (9 % mot 2,5 % inom 1 km,
  oddskvot 3,8). Bön är något vanligare nära kyrkor uppförda 1200 eller tidigare (1,21 per halvering, inte båda halvor).
- Ingenting av H1–H4 nedan har räknats eller tittats på.

## Material
Korpus 3f58e9339191761e: svenska vikingatida runstenar på sin plats (`moved = 0`) med koordinater, som i r/remains.R
(1 097 stenar). Bön = `cat_kristen`. Teofora namn = `data/ortnamn/kultnamn.csv` tier A (82 namn). Nära = under 2 km.
Tidigt skede = stilgruppens mittår. Halvorna = socknar växelvis inom landskapet (`half`). Kyrkor =
`data/ortnamn/kyrkor.csv` (Wikidata, uppförda före 1350; tidig = 1200 eller tidigare). Gårdar = KMR
bytomt/gårdstomt (`data/raa/lamningar_extra/bytomt_gårdstomt.csv`). Källor = KMR källa med tradition
(`data/raa/lamningar_extra/källa_med_tradition.csv`). Avstånd i SWEREF 99 TM.

## Test (Holm över H1–H4, α = 0,05; ensidiga i hypotesens riktning)
- **H1 Kristnandets tidiga skede.** Bland daterade bönestenar: har de inom 2 km från ett teofort namn ett tidigare
  mittår än övriga bönestenar? Linjär regression `år ~ nära + landskap`; ensidigt (tidigare).
- **H2 Platsen, inte gården.** Bland stenar inom 2 km från ett teofort namn: står bönestenarna närmare namnet i
  förhållande till närmaste gård än övriga stenar gör? Logistisk regression `bön ~ log2(km_namn / km_gård) +
  landskap`; ensidigt (negativ koefficient). Gården = närmaste bytomt/gårdstomt som ligger mer än 300 m från varje
  teofort namn (namnets punkt är själv dagens by eller gård; den räknas inte som "gården").
- **H3 Inte kyrkan.** Håller sambandet när närheten till kyrkorna hålls konstant? `bön ~ nära + log2(km tidig
  kyrka) + log2(km sen kyrka) + landskap`; ensidigt (oddskvot > 1). Prövar alternativet att kyrkan byggdes på
  kultplatsen och att bönen följer kyrkan.
- **H4 Andra heliga platser.** Är bön vanligare inom 2 km från en källa med tradition (offer- och
  trefaldighetskällor)? `bön ~ nära_källa + landskap`; ensidigt (oddskvot > 1). Ett oberoende mått på heliga platser,
  men känt ur senare tradition.

**Håller** (H3, H4): Holm-p < 0,05 och p < 0,05 åt samma håll i båda halvorna.
**Stöder** (H1, H2): Holm-p < 0,05. Underlaget (omkring 56 stenar nära namnen) räcker inte för halvprov; halvorna
redovisas men krävs inte, och resultatet beskrivs som stöd, inte som bekräftat.
**Antydan:** okorrigerat p < 0,05 åt hypotesens håll.
**Faller:** p ≥ 0,05, eller åt andra hållet.

## Robusthet (redovisas, ändrar inte utfallet)
- H3 och H4 med radien 1 och 3 km; med tiden (t50) konstant på daterade stenar; med ristaren som slumpeffekt (lme4);
  bara Uppland och Södermanland; utan stenar som Runor 2020 anger som flyttade; H3 utan ett teofort namn i taget.
- H1 som skillnad i sambandet före och efter 1050 (`bön ~ nära × sen + landskap`).
- H2 med Fishers test på andelen som står närmare namnet än gården.

## Beskrivning (prövas inte)
Namnen med stenar inom 2 km: gud, antal stenar, bönestenar, närmaste tidiga kyrka; KMR-offerplatser inom 2 km från
dessa namn; vilka böner (formler) stenarna nära namnen bär.

## Förbehåll
Ortnamnen är belagda långt efter vikingatiden och punkten är dagens by, inte kultplatsen. Bytomterna är kända från
1600–1700-talens kartor. Källornas tradition är oftast känd från 1600-talet och senare. Kyrkoregistret (Wikidata) är
ofullständigt och byggnadsåren osäkra. Ett utfall som faller visar inte att hypotesen är fel, bara att materialet inte
bär den. Mönstret faller enligt planen om H3 inte håller (bönen förklaras då lika väl av kyrkan).

## Artikeln
En artikel skrivs bara om H3 håller och minst en av H1, H2 och H4 stöder eller håller; annars redovisas utfallet i
resultat.md och mönstrets förbehåll, utan artikel.
