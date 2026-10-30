# Analysplan: Namnen och orden som överlevde – från runstenen till i dag

Låst 2026-10-30, innan något utfall nedan har räknats. SHA-256 i `analysplaner/2026-10-30-namnen-och-orden-som-overlevde.sha256`.
Kod i `utdata/overlevde/`, resultat i `utdata/overlevde/resultat.md`.

## Frågan
Viktors hypotes: av det som levde under vikingatiden har vardagens namn och ord överlevt, men det som hörde till makten –
titlar, ämbeten, lag och kult – ersattes, ofta av kristna eller utländska ord. Två delar: personnamnen (lever
runstenarnas namn kvar i Sverige i dag?) och maktens ord (lever runstenarnas ord för makt, lag och kult kvar med sin
betydelse?).

Känt före låsningen: SCB:s tilltalsnamn med minst 10 bärare 1999 och 2020 (29 626 namn) är hämtade men inte jämförda;
`utdata/namnarv/` (låst plan 2026-10-29) visade att kvinnor bar nordiska namn mer sällan än män i breven 1350–1450 (28 %
mot 44 %). Kunganamnen Erik, Olof, Knut, Sven och Harald är kända för att leva kvar. Inga andelar är räknade.

## Del A – Personnamnen

**Material.** Personnamn på svenska vikingatida runstenar (`src/entities.extract`, osäkra läsningar utan), med antal
stenar där namnet förekommer. Namn på minst 3 stenar ingår (stabilare än enstaka belägg); kön ur `src/people.gender`.
Ett namn räknas som **teoforiskt** när det börjar på Þór-, Ás-/Ôs- (Áss), Frey-, Ingi-/Yngv- eller Guð- (förled som
gudanamn eller *guð*); som **kungligt** när det bärs av en känd vikingatida eller tidigmedeltida svensk, dansk eller
norsk kung (Eiríkr, Óláfr, Knútr, Sveinn, Haraldr, Hákon, Ingi, Magnús, Bjôrn, Emundr, Anundr, Stenkil = Steinkell).

**Modern form.** För varje namn: (1) normalformen i namnlexikonet från breven (`utdata/namnarv/lexikon.csv`), annars
(2) en regelöversättning: Þ/þ→T, ð→d, ô→å, ó→o, á→å, æ→ä, ø→ö, ey→ö, ei→e, au→ö, í→i, ú→u, ý→y, é→e, slutljudande
-r efter konsonant tas bort, -rr→r, -nn→n, -ll→ll; dessutom varianterna med ä→e, å→o och o→å. Varje kandidat jämförs
med SCB 2020; namnet **lever** om någon kandidat har minst 10 bärare. Alla matchningar skrivs ut för granskning;
uppenbart falska träffar (en modern form som är ett annat namn) rättas i en lista med skäl, och antalet rättelser
redovisas.

**Test (Holm över N1–N3, α = 0,05; Fishers exakta test, viktat per namn)**
- **N1 Kvinnorna:** kvinnonamn lever mer sällan än mansnamn.
- **N2 Gudarna:** teoforiska namn lever inte mer sällan än andra (prövas tvåsidigt; hypotesen om makt förutsäger att
  hedniska namn skulle trängas undan – ett utslag åt det hållet talar för den, ett åt andra hållet emot).
- **N3 Makten:** namn som bärs av personer med en titel eller rang på runstenarna (*þegn*, *drengr*, *styrimaðr*,
  *skipari*, *landmaðr*, *húskarl*, *bóndi*, *konungr*, *jarl*) lever mer sällan än andra namn. Bara om minst 15 sådana
  namn finns; annars beskrivning.
**Beskrivning:** andelen som lever totalt, viktat per namn och per bärare; kedjan runsten → breven 1350–1450 → 2020 för
de namn som finns i lexikonet; de vanligaste levande och döda namnen; kunganamnen.

## Del B – Maktens ord

**Material.** Ord i Rundatas normalisering på svenska vikingatida runstenar som förekommer på minst 3 stenar och inte är
namn, pronomen, prepositioner eller konjunktioner. Varje ord förs till en domän med en fast lista (skriven före
kodningen av överlevnad):
- **makt och rang:** konungr, jarl, þegn, drengr, hersir, goði, landmaðr, húskarl, styrimaðr, skipari, bóndi, lið, dróttinn,
  ríki, góðr (som rangord ej), stallari, félagi, sveinn (som följesman);
- **lag och ting:** þing, lag (lagh), lagmaðr, arfr, erfa, eign, bú, skipta, vitni;
- **kult och tro:** Guð, Kristr, sál, and (ônd), heilagr, kirkja, kross, vígja, vé, goð, Þórr, blót, mæla (kult), dróttinn
  (Herren);
- **släkt:** faðir, móðir, bróðir, systir, sonr, dóttir, kona, bóndi (make), fóstri, mágr, frændi, barn, erfingi;
- **vardag och natur:** steinn, brú, vegr, land, skip, kuml, hús, bý, garðr, hestr, haugr, sjór, eyja, dauðr, deyja, fara, ráða,
  rísta, hôggva, góðr, harða.
Ord som hamnar i två listor kodas efter sin vanligaste användning på runstenarna (bóndi: make → släkt; *bóndi* som
titel → makt redovisas separat).

**Överlevnad**, kodad ur Hellquist, *Svensk etymologisk ordbok* (1922, runeberg.org) och SAOL (svenska.se), med källan
angiven per ord:
- **lever:** en ättling finns i dagens svenska med samma kärnbetydelse (steinn → sten, konungr → kung);
- **lever med sänkt eller ändrad betydelse:** ättlingen finns men betyder något lägre eller annat (drengr → dräng,
  bóndi → bonde);
- **borta:** ingen ättling i allmänt bruk (finns bara i ortnamn, fackspråk eller som återupplivning).

**Test (α = 0,05)**
- **W1:** ord för makt, lag och kult lever med kärnbetydelsen mer sällan än ord för släkt och vardag (Fishers exakta
  test, ensidigt).
**Beskrivning:** vilka maktord som försvann, vilka som sjönk i status, och vilka ord som tog deras plats (hertig, greve,
biskop, präst, riddare, frälse, kyrka …) med Hellquists uppgift om ursprung och första belägg.

## Förbehåll
Runstenarna är ett urval: de nämner de döda och deras släkt, och maktens folk syns mer än andra. Namnöversättningen med
regler kan missa namn som ändrat form mer (Ásbjôrn → Esbjörn finns i lexikonet, men inte alla sådana). SCB räknar
tilltalsnamn i dag, inte namn som funnits däremellan; ett namn kan ha dött och återupplivats (Tor, Ragnar). Ordkodningen
är en bedömning; källan står för varje ord så att den kan prövas.
