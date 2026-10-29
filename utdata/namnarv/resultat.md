# Resultat: namnen som levde kvar (2026-10-29)

Plan: `analysplaner/2026-10-29-namnen-som-levde-kvar.md` (fb1fa49, SHA-256 kontrollerad före körning). Lexikon låst
före räkningen (`lexikon.csv`, 66980f0, SHA-256 671416409c413fa4). Kod `hamta.py`, `bygg_lexikon.py`,
`smp_kontroll.py`, `analys.py`, `modeller.R`; siffror `namnarv.json`. Källa: SDHK, svenskspråkiga brev i Språkbankens
Korp. 25 541 förnamnsbelägg i 3 290 brev (nästan alla 1350–1450); 1 230 fader–barn-par (unika namnkombinationer).

## Namnlexikonet och SMP-kontrollen
892 stavningar av 178 förnamn, klassade för hand ur alla ord med versal som förekommer minst fem gånger (2 699 ord).
Helgonnamn i dateringar (*Johannis*, *Petri*, *Martini* …) räknas inte. Kontroll mot Sveriges medeltida personnamn
(ISOF, häfte 1–17, A–J): 55 av 101 namn A–J kunde slås upp i den OCR-lästa texten; 52 stämde. Rättat före låsningen:
Botulf nordiskt (inte kristet), Dan nordiskt, Gerd osäkert (kan vara Gerhard).

## Utfall
- **H4 Kvinnorna – håller.** Kvinnor bär nordiska namn mycket mer sällan än män: 28 % mot 44 % av beläggen,
  oddskvot 0,51 [klusterrobust], p 4·10⁻²¹, Holm 2·10⁻²⁰; halva A 0,50, halva B 0,52 (båda p < 10⁻¹⁰). Samma med de 150
  säkraste namnen och utan Stockholm. Katarina, Kristina, Margareta, Birgitta, Cecilia, Elin mot männens Olof, Karl,
  Erik, Knut, Sven.
- **H2 Generationen – håller enligt planen, med ett viktigt förbehåll.** Barnen har nordiskt namn mer sällan än fäderna:
  46 % mot 56 % (1 230 namnkombinationer; 375 par där fadern var nordisk och barnet inte, 259 tvärtom; p 5·10⁻⁶,
  Holm 1·10⁻⁵; halva A p 0,0003, B p 0,005). **Men** skillnaden bärs till stor del av döttrarna (38 % mot 59 %), och
  döttrarna jämförs med män. Bara söner: 48 % mot 55 %, p 0,0007, men bara i halva A (B p 0,16) – för söner är det en
  antydan. Räknat per förekomst i stället för per person går riktningen svagt åt andra hållet (47 % mot 45 %), eftersom
  några män med nordiska namn (Bo Jonsson m.fl.) nämns i hundratals brev.
- **H1 Tiden – ingen skillnad påvisad.** Andelen nordiska namn är stabil 1350–1450: 45 % 1350–1399, 42 % 1400–1449
  (oddskvot 0,96 per 50 år, p 0,31). Räknas Magnus som nordiskt sjunker andelen (0,78, p 7·10⁻⁹) – det mesta av
  förändringen i breven är att Magnus blir ovanligare. Skiftet till kristna namn hade alltså i stort sett redan skett
  när de svenskspråkiga breven börjar.
- **H3 Gudanamnen – ingen skillnad påvisad.** Av de 100 vanligaste mansnamnen på runstenarna finns 39 i breven (minst
  fem belägg): 14 av 29 med gudanamn som förled (Tor-, Ås-, Frö-, Ing-, Gud-) och 25 av 71 övriga (p 0,26). Namnen
  med Tor och Ås försvann inte oftare än andra – Tore, Torsten, Esbjörn, Tord levde vidare.

## Beskrivning (prövas inte)
- Runstensnamn som lever kvar starkt: Olof (1 422 belägg), Karl (936), Sven (356), Håkan (347), Björn (268), Tore/Ture
  (268), Ulf (217), Tord (202), Anund (157), Esbjörn (124), Torsten (123). Som försvann (inga säkra belägg): Öpir,
  Halvdan, Åsmund, Ingefast, Ozur, Frösten, Ofeg, Balle, Holmfast, Åsgöt, Jorund, Sibbe, Vibjörn, Toke.
- Vanligaste namnen 1400–1449: Nils, Peder, Olof, Lars, Jöns, Magnus, Karl, Erik, Bengt, Anders, Knut, Johan.
- Andel nordiska namn efter utfärdandeort (≥ 300 belägg): Skara 58 %, Nyköping 56 %, Vadstena 52 %, Linköping 49 %,
  Strängnäs 48 %, Uppsala 46 %, Stockholm 43 %, Västerås 36 %, Åbo 26 %.

## Läsning
När breven skrevs på svenska med latinska bokstäver bar ungefär fyra av tio namn fortfarande fornnordiskan – men inte
jämnt fördelat: männen behöll de nordiska namnen, kvinnorna fick oftare helgonnamn. Inne i familjerna syns samma sak:
döttrarna fick kristna namn mycket oftare än fäderna hade haft nordiska; sönerna bara något. Gudanamnen var inget
hinder – Tor och Ås levde kvar i namnen långt efter att gudarna lämnat runstenarna.

## Avvikelser och preciseringar
- H2: enheten är en unik namnkombination (barnets och faderns namn), med år och halva från det tidigaste brevet; planen
  sa inte hur upprepade belägg av samma person skulle räknas. Förekomstvägt redovisas också (se ovan).
- H3: ”finns i breven” = namnet finns i lexikonet (minst fem belägg); namn med färre belägg räknas som saknade.
- Söner och döttrar för sig (H2) var inte förplanerat; redovisas eftersom kön visade sig skilja (H4).
