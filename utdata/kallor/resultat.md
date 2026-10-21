# Resultat: tre nya källor kring runstenarna

Enligt `analysplan_kallor.md` (låst 2026-10-21, SHA-256 `c11d3142f984aec0263a90040f54ac2631302f4de76c24751db1d1b3b89b12b3`).
Skripten `skane_runformer.py`, `fornsvenska.py` och `blekinge_tolkningar.py`; resultatfilerna `skane_runformer.json`,
`fornsvenska.json` och `blekinge.json` (plus känslighetskörningarna `skane_runformer_utan_skiljetecken.json`,
`fornsvenska_en_form.json`, `fornsvenska_alla_former.json`). Underlaget ligger i `data/raa/kallor/` (inte i git):
RuneS-DB:s poster för Skåne och Blekinge (259 inskrifter, hämtade 2026-10-21, CC BY-SA 4.0) och Språkbankens ordböcker
(Karp v7, 2026-10-21).

## A. Skåne: runformer mot stavning – ja

43 runstenar (inte 42 som inventeringen sa: urvalsregeln i planen ger 43), 2 837 runpositioner med graftyp, 21 tecken,
63 graftyper. Varierande tecken enligt planens regel: `:` (skiljetecknet, 7 graftyper på 510 positioner), b, f, m, r,
s (10 graftyper), þ (4), ą, ʀ. Mantel (Spearman) stavningsavstånd mot runformsavstånd: **r = 0,42, p = 0,0001**
(10 000 permutationer, 902 av 903 par). Geografin förklarar inget: avstånd i km mot runform r = 0,02 (p 0,36), mot
stavning r = 0,01 (p 0,41); partiell Mantel r = 0,42, p = 0,0001. Svar: ja.

Känslighet (utöver planen): utan skiljetecknet som varierande tecken blir r = 0,15, p = 0,017 (partiell 0,15,
p 0,015) – positivt och signifikant, men större delen av sambandet ligger i skiljetecknets form, som både
stavningsmodellen (skiljetecken som drag) och RuneS-DB (graftyp) registrerar. Det är inte två oberoende mätningar av
samma hand utan samma vana sedd från två håll; de åtta runtecknen bär resten.

## B. Fornsvenskan: engångsorden är sämst belagda – ja

1 106 lemman (namn uteslutna), 11 157 förekomster på 2 321 runstenar. Ordböckerna: 39 351 unika uppslagsord. Med
planens regler: 401 lemman belagda (36 %), 8 807 förekomster (79 %). Per klass: hapax 217 av 747 (29 %), 2–4
förekomster 97 av 215 (45 %), minst 5 förekomster 87 av 144 (60 %). Hapax mot ≥ 5: z = 7,27, p = 1,8 · 10⁻¹³. Svar: ja.

Känslighet (utöver planen): (1) bara lemmat och dess vanligaste form (så att vanliga ord inte får fler chanser genom
sina böjningsformer): 29 % mot 58 %, p = 5 · 10⁻¹²; (2) ordböckernas böjda och avledda former (`<orth>`) räknade som
uppslag: 500 lemman (45 %), 10 022 förekomster (90 %); hapax 37 %, 2–4 54 %, ≥ 5 76 %, z = 8,8. Andelarna är nedre
gränser: bland de vanligaste obelagda finns böjningar reglerna inte fångar (*haggva* – hugga, *sialfan* – siälver,
*sialu* – siäl, *dræpinn* – dräpa, *markaði* – märkia) vid sidan av ord som ordböckerna kan sakna (*kumbl*, *hvitavaðum*,
*oniðingR*). Skillnaden mellan klasserna står sig i alla tre körningarna.

## C. Blekinge: förbannelsen är inte enig – nej

| Sten | Tolkningar | Publicerade | Översättningslikhet | Död | Förstörelse | Förutsägelse/skada |
|---|---|---|---|---|---|---|
| Bl 2 Gummarp | 7 | 1944–2004 | 0,72 | 0 | 0 | 0 |
| Bl 3 Stentoften | 19 | 1961–2004 | 0,21 | 9 av 19 (47 %) | 9 av 19 (47 %) | 0 |
| Bl 4 Istaby | 7 | 1960–2001 | 0,57 | 0 | 0 | 0 |
| Bl 6 Björketorp | 12 | 1966–2004 | 0,28 | 9 av 12 (75 %) | 9 av 12 (75 %) | 5 av 12 (42 %) |

Planens ja krävde minst 80 % för död och förstörelse på Bl 6 och Bl 3: 75 % och 47 %. Svar: nej. Tre av Björketorps
tolv tolkningar saknar döden – två är fragment ("... is hidden ...", "... a death trough guile visits ..." räknas,
"... The sequence of bright runes I hid here ..." inte) och en läser monumentet som en hedersvård åt en vän. På
Stentoften tolkar bara nio av nitton förbannelsedelen alls; de övriga stannar vid offer- och årsväxtraderna.

Rad för rad (täckning = andel tolkningar som translittererar raden; enighet = andel med majoritetens läsning):
Björketorp 67–92 % täckning, 78–100 % enighet; Stentoften 53–84 % täckning, enighet 100 % på de två första raderna
men 21 % på raden *hᴀriwolᴀfz(m)ᴀ(2?)usnuh(1?)e*; Gummarp och Istaby 100 % täckning, 71–100 % enighet.
Tjurkö-brakteaterna: IK 184 7 tolkningar (1914–2006), IK 185 4 (1941–1996).

## K-samsök

Statens historiska museer levererar 246 543 vikingatida föremål till K-samsök (`fromPeriodName=vikingatid`), men
ingen fyndplats följer med i indexet (socken, landskap och koordinater tomma för alla kontexttyper), och museets egen
webbplats samlingar.shm.se avvisar krypterade anslutningar härifrån (liksom Kielprojektets server). Kulturmiljöregistrets
lämningar används redan. Ingen analys.

## Avvikelser från planen

1. Urvalet i A blev 43 stenar (regeln), inte 42 (inventeringen).
2. Tolkningssidornas translitterering spänner över flera rader i HTML; den första tolkaren tog bara första raden, vilket
   gav fel täckning. Rättat innan måtten redovisades (bugg, inte måttändring); täckningen räknas en gång per tolkning.
3. Känslighetskörningarna i A och B är tillägg utöver planen och redovisas som sådana.
