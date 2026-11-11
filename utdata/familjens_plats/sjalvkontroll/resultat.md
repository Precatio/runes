# Resultat: självkontroll av ”grupperna står vid gravfälten” (2026-11-10)

Plan: `analysplaner/2026-11-10-sjalvkontroll-gravfalt.md` (låst i bc7da76, SHA-256 8fb876c2…, kontrollerad före körning).
Kod här: `p0.py` (replikering), `hamta_gravfalt.py` (K-samsök → `data/raa/gravfalt_detaljer.csv`,
`data/raa/runristning_lan.csv`), `klasser.py` (klasserna, `klasser.csv`, skrivna innan stenarna lades över), `data.py`
(`stenar_sk.csv`), `analys.R` (`resultat.json`).

## P0 – replikering: klar
Originalet (data.py + analys.R, oförändrade, utdata till `p0/`) ger exakt samma tal som det publicerade: 82 mot 55 %,
oddskvot 2,38 [1,50–3,78], p 0,00023. `stenar.csv` byte för byte identisk (`p0.json`).

## Registret
Alla 18 633 gravfält i `lamningar.csv` fanns kvar i K-samsök och fick detaljer; 17 777 har ingående lämningar.
Granskade gravfält (V): 10 789 (58 %). Med yngre järnålderns former (Y): 2 550 (14 %). Fördelningar per bedömning,
form och län i `klasser.csv`. Stenarnas län: 653 av 657 ur stenens egen KMR-post, 4 efter närmaste gravfält.

## Proven (657 stenar: 185 i grupp, 472 ensamma; Holm över de fyra)
- **K1 (a) bara granskade gravfält – står sig.** 73 mot 43 %; oddskvot 2,60 [1,7–3,9], p 6,5·10⁻⁶, Holm 2,6·10⁻⁵.
  Halva A 2,3 (p 0,004), halva B 3,2 (p 0,0004).
- **K2 (b) bara gravfält med yngre järnålderns former – står sig.** 33 mot 15 %; oddskvot 2,56 [1,6–4,0],
  p 5,8·10⁻⁵, Holm 0,0002. Halva A 2,3 (p 0,01), halva B 3,0 (p 0,002).
- **K3a (c) län i stället för landskap – står sig.** 82 mot 55 %; oddskvot 2,33 [1,5–3,7], p 0,0004, Holm 0,0004.
  Halva A 2,4 (p 0,006), halva B 2,3 (p 0,02).
- **K3b (c) län + registrets gravfältstäthet 1–5 km – står sig.** Oddskvot 2,51 [1,6–4,1], p 0,0002, Holm 0,0003.
  Halva A 2,6 (p 0,004), halva B 2,5 (p 0,015).

**Helhet enligt planen: det publicerade resultatet står sig** (K1, K3a och K3b står sig). Oddskvoten ändras inte nämnvärt
av någon av invändningarna (2,33–2,60 mot 2,38); de absoluta andelarna sjunker när gravfälten granskas (73/43 %).

## Robusthet (beskrivande)
- K1 utan ”grav markerad av sten/block” som säker form: 70 mot 42 %, oddskvot 2,23 [1,5–3,3].
- K1 inom 250 m: 48 mot 27 %, oddskvot 2,05 [1,4–3,1].
- K1 med län och gravfältstäthet: 2,71 [1,8–4,2]. K2 med län och gravfältstäthet: 2,58 [1,6–4,1].
- Bara Uppland och Södermanland: K1 2,7, K2 2,2, K3a 2,8, K3b 3,2 (alla p < 0,002).

## Läsning
Sambandet beror inte på att registret räknar röjningsrösen som gravfält, inte på skillnader mellan länen och inte på hur
tätt registret har gravfält runt stenen. Det håller också för gravfält med former som räknas till yngre järnålder.
**Förbehåll som ska stå kvar:** registret har ingen datering, så att gravfälten är samtida med stenarna kan inte visas;
Y är ett typologiskt ersättningsmått (ca 550–1050, också vendeltid) och skiljer inte flerperiodiga gravfält från rena.
Inventeringsår finns inte som fält; länets fasta effekt och gravfältstätheten tar upp skillnader i täckning mellan län och
bygder, inte skillnader inom en bygd.

## Avvikelser från planen
- P0 skrev till `p0/` i stället för att skriva över originalets filer (bara utdatakatalogen byttes).
- Två stenar ligger i ett landskap där ingen sten hade en KMR-post att hämta landskapets registernamn ur; de fick länet
  efter närmaste gravfält oavsett landskap (planen: i samma landskap). Påverkar 2 av 657.
- Formen ”Gravhägnad” (13 gravfält) finns i registret men inte i planens lista över säkra former och räknades därför inte
  som säker, enligt planens ordalydelse.
- Tekniskt: Pythons https-anrop behövde certifis certifikatlista; ingen följd för data.
