# Resultat: namnen och orden som överlevde (2026-10-30)

Plan: `analysplaner/2026-10-30-namnen-och-orden-som-overlevde.md` (låst, SHA-256 kontrollerad). Kod `namn.py`, `ord.py`,
`ord_analys.py`; siffror `namn.json`, `namn_extra.json`, `ord.json`; granskning `matchningar.csv`, `ord_kodning.csv`.
SCB: tilltalsnamn med minst 10 bärare 31 december 2020 (BE0001TNamn10).

## Del A – Personnamnen
391 namn förekommer på minst tre svenska vikingatida runstenar. **82 lever** i dag (minst 10 bärare): 21 % av namnen,
37 % viktat efter hur vanliga de var på stenarna. Granskningen tog bort sex falska träffar (Dan, Elif, Hera, Kali, Uni,
Ved – samma stavning, annat namn). Känslighetsprov (inte i planen, efter granskningen): med á→a och f→v (Ástríðr →
Astrid, Tófa → Tova) och utan namnfragment lever 85 av 385 (22 %); fyra nya falska träffar togs bort där.

- **N1 Kvinnorna – faller, och går åt andra hållet.** Kvinnonamn lever *oftare* än mansnamn: 33 % (20 av 61) mot 19 %
  (62 av 330); ensidigt p 0,99 för planens riktning. Tvåsidigt p 0,017 (känslighetsprovet 36 % mot 21 %, p 0,007) –
  ett resultat åt motsatt håll mot planen, inte prövat i förväg.
- **N2 Gudarna – håller, åt andra hållet än makthypotesen väntade.** Namn med gudanamn eller *guð* som förled (Tor-, Ås-,
  Frey-, Ingi-, Gud-) lever dubbelt så ofta som andra: 39 % (22 av 56) mot 18 % (60 av 335), p 0,0006, Holm 0,001
  (känslighetsprovet 45 % mot 20 %, p 0,00005). De hedniska namnen trängdes inte undan.
- **N3 Makten – går inte att pröva.** Bara 6 namn bärs av någon som kallas *þegn*, *drengr* eller annan titel (gränsen
  var 15).
- **Kedjan genom medeltiden:** av de 60 namn som finns i breven 1350–1450 lever 44 (73 %) i dag; av de 331 som inte
  finns där lever 38 (11 %) – de flesta av dem troligen återupplivade senare (Åsa, Tora, Runa, Viking).
- **Kunganamnen** lever alla utom Steinkell: Erik (55 968 bärare), Björn (34 656), Sven (31 115), Håkan (25 508),
  Knut (4 473), Harald (2 647).
- Vanligast bland de döda: Ônundr, Œpir, Halfdan (Halvdan finns, men under 10 bärare), Ingifastr, Ôzurr, Freysteinn,
  Holmsteinn, Ófeigr, Ingjaldr, Ásgautr, Holmfastr, Holmfríðr, Vébjôrn, Guðfastr.

## Del B – Maktens ord
44 ord på minst tre runstenar, kodade efter Wiktionarys nuvarande betydelse (`ord_kodning.csv` med belägg).

- **W1 – håller.** Ord för makt, lag och kult lever med kärnbetydelsen i 9 av 17 fall (53 %), ord för släkt och vardag
  i 23 av 27 (85 %); Fishers test ensidigt p 0,024.
- **Beskrivning (ej i förväg prövad):** rangorden ensamma lever i **2 av 9** fall (22 %): *kung* och *styrman*. *drengr*
  har sjunkit till *dräng* (drängen på gården, och nedsättande om en medlöpare); *þegn*, *húskarl*, *lið*, *dróttinn*,
  *félagi* och *sveinn* (följesman) finns inte i dagens svenska – *dróttinn* bara i avledningen *drottning*. Kultorden på
  runstenarna är nästan alla kristna (*Guð*, *sál*, *and*, *heilagr*, *Kristr*) och lever alla; bara *Þórr* lever
  enbart som mytologi och namn. Lagens två ord (*þing*, *arfr*) lever. Bland släktorden har tre ändrats: *kona* är
  ålderdomligt, *bóndi* betyder lantbrukare och inte make, *fóstri* finns bara i sammansättningar.

## Läsning
Hypotesen håller för maktens titlar men inte för namnen. Vikingatidens ord för rang och följe – *þegn*, *drengr*,
*húskarl*, *lið*, *dróttinn* – försvann eller sjönk; makten fick nya ord under medeltiden. Namnen gick åt andra
hållet: gudanamnen klarade sig bäst, och kvinnonamnen bättre än männens. Att hedniska namn levde vidare medan hedniska
ord för kult försvann (de syns knappt på runstenarna) tyder på att kristnandet bytte ut det offentliga språket men
lämnade familjens namnskick ifred – eller att namnen senare återupplivades. Kedjan genom breven visar att båda delarna
finns: tre av fyra namn som levde i medeltiden lever i dag, men många av dagens runnamn saknas i breven och är troligen
återupplivade under 1800- och 1900-talen.

## Förbehåll
- Ordkodningen är en bedömning; källan står för varje ord. Maktens ord är få (9), och kungar och jarlar nämns nästan
  aldrig på runstenarna (*konungr* på 3 stenar, *jarl* som titel på 2: Håkon jarl, Sm 76 och U 617), så de ord som prövas är de som användes där.
- Namnöversättningen med regler missar namn som ändrat form mer, och ger falska träffar som har rättats för hand
  (listan i `namn.py`). SCB räknar dagens bärare; ett namn kan ha dött och återupplivats.
- N1 och kvinnonamnen: utslaget går åt motsatt håll mot planen och är därför ett fynd att pröva, inte bekräftat.

## Avvikelser
- Ordens betydelse kodades efter svenska Wiktionary i stället för SAOL (svenska.se går inte att läsa maskinellt);
  *goði* och *vé* togs bort efter att antalen setts men före kodningen, eftersom normaliseringen inte skiljer dem från
  *góða* och *vi*.
- SCB:s första hämtning (via tabellens kodlista) missade manliga namn; datan hämtades om med filter "all".
- Känslighetsprovet med á→a och f→v lades till efter granskningen.
- Rättelse 2026-10-30: `ord.py` sökte *jarl* men Rundata stavar *iarl*; mönstret är rättat (`\biarls?\b`). Ordet står
  som titel på 2 stenar (U 498 <iarlR> är ett otolkat namn), under gränsen 3, så `ord.json` är oförändrad (kontrollerat).

## Tillägg (beskrivande, inte i planen): maktens titlar och kartan
Lagt till 2026-10-30 på Viktors begäran. Kod `politik.py` (räkning + belägg ur sv/en Wiktionary och sv Wikipedia,
`politik_underlag.json`) och `politik_analys.py` (kodning med belägg, `politik_kodning.csv`; summor `politik.json`).

- **Titlar och ämbetsord på svenska runstenar: 16.** Lever med samma innebörd 4 (*konungr*, *styrimaðr*, *skipari*,
  *þingstaðr*); sjönk 1 (*drengr*); bara historisk term 6 (jarl, stallare, bryte, huskarl, hundare, drott); borta 5
  (*þegn*, *landmaðr*, *hersir*?, *þingalið*, *liðs forungi*). *þegn* 21 stenar, 18 i Vg. Titlarna står oftast med en
  herre i genitiv (Sm 42, Sm 76, U 335, Sö 335). *dróttinn* (5) gäller på alla stenarna Gud.
- **Medeltidens maktord:** lån 9 (hertig 1285 < lty. hertoch, greve, marsk, fogde, riddare, kansler, riksdag ≈ Reichstag,
  biskop, präst); nordiska 6 (frälse, härad, lagman, socken, ledung, adel – det sista starkt påverkat av lty. adel).
  Läsning (ej räknad): kronans och kyrkans titlar lånades, bygdens institutioner behöll nordiska ord. jarl → hertig
  (riksjarl = dux regni), stallare → marsk (1200-talet), hundare → härad (unionstiden), tingsrätt + lagman 1971.
- **Områden:** 22 länder/platser på 91 stenar; samma namn 11 (44 stenar), bara historiskt 2 (4), bytt eller borta 9
  (45): Svitjod → Sverige (folk → rike), Garðar, Holmgarðr, Grikkland (Bysans), Langbarðaland, Serkland, Jórsalir,
  Saxland, Hedeby. Svitjod-stenarna (Sö 140, Sö Fv1948;289) står båda i Ludgo sn.
- Förbehåll: beskrivande; kodningen är en bedömning med belägg per ord; många titlar på en enda sten.
