# Analysplan: gudarna på kartan – ortnamnen med gudanamn

Skriven och låst 2026-11-17, innan någon ortnamnstolkning har kopplats till ett område. Underlag för artikeln med
arbetsrubriken "Fanns det någon asatro? – gudarna på kartan" (Viktor 2026-11-17: "Hur spred sig den hedniska tron över
Skandinavien och Norden? Avstånden var långa … Hur kunde asatron bli till och spridas?"; "Gå på detta spåret").
Runstenarna är inte källan här: de är sena och nästan alla kristna. Ortnamnen är äldre och finns över hela landet.

## Frågan
Var asatron *en* tro, eller flera? Om samma gudar dyrkades på samma sätt överallt borde gudanamnen i ortnamnen vara
utspridda utan mönster: Tor, Oden och Frö lika ofta i varje landsdel. Om tron var regional borde varje gud höra hemma i
vissa bygder. Planen prövar det andra mot det första. Den prövar inte hur tron spreds eller när namnen gavs.

## Känt före låsningen
- **Källorna** (inventering 2026-11-17, `/Volumes/2TB/Antigrvity/Runes/downloads/asatro/`): ISOF:s ortnamnsregister
  (CC BY) har läge och äldsta belägg men inga tolkningar i maskinläsbar form. *Svenskt ortnamnslexikon* (SOL, 2:a uppl.
  2016, fritt på isof.se, upphovsrättsligt skyddat: läses och räknas, citeras kort, återpubliceras inte) har 6 045
  uppslag med forskarnas tolkning, äldsta belägg, socken, härad och landskap. Vikstrand 2001 (*Gudarnas platser*) är
  inte öppen.
- **Antal, inte område:** en första automatisk genomgång av SOL fann omkring 16 namn med Tor, 12 med Oden, 8 med Frö, 5
  med Ull, 2 med Njärd, 2 med Fröja och 1 med Frigg (säkra och osäkra tillsammans). Ingen av dem har räknats per
  landsdel. Stamsökning i ortnamn utan tolkning duger inte: SOL tolkar Frösunda som *frö* 'bördig', Frövi som ett
  adjektiv och *vidher* 'skog', Torsby som mansnamnet Tore.
- **Litteraturen** (Namn och bygd och Fornvännen i sok.sqlite, CC BY 4.0): Hellberg (NoB 101, 2013) och Ambrosiani
  (NoB 98, 2010) om tuna-namnen, Ull och Njärd i Svealand; Nyman (NoB 111, 2023) om de sakrala namnen i norr; Særheim
  (NoB 100, 2012) om vad som räknas som teofort; Nordberg (Fornvännen 2018) om hur traditionen cirkulerade. Den
  allmänna uppfattningen i litteraturen är att Ull och Njärd hör till Mälardalen och att Tor finns överallt. Den
  uppfattningen är en förväntan, inte ett resultat från våra data.

## Data
- **Grinden:** ett namn räknas som teofort bara när SOL:s tolkning nämner guden. Alla 6 045 uppslag söks med en fast
  lista på gudanamn i tolkningstexten: Tor/Thor/Tors-, Oden/Odin/Ons-/Odens-, Frö/Frej/Frey-, Ull/Ullin, Njärd/Njord,
  Fröja/Freja/Härn/Hörn, Frigg, Tyr/Ti-, Disa/dis, Liudhgudha och "gudanamn"/"asagud".
- **Gradering** av varje träff, ur den mening där guden nämns, efter fasta ord:
  - *säker*: guden anges utan förbehåll ("innehåller gudanamnet", "förleden är gudanamnet");
  - *osäker*: guden anges med förbehåll (troligen, sannolikt, torde, kanske, möjligen, antagligen, synes, har tolkats,
    kan innehålla);
  - *avvisad*: guden nämns men förkastas eller får stå tillbaka (snarare, inte, knappast, svår, osannolik, felaktigt,
    har tidigare tolkats).
  Meningen skrivs ordagrant till kodfilen (utanför git, källregeln) med uppslag, gud och grad. **Två kodare:** Claude
  graderar alla träffar; en blind andra läsning (Claude Opus, utan den första graderingen) görs av samma meningar. Vid
  oenighet gäller den strängare graden (avvisad före osäker före säker). Oenigheten redovisas.
- **Läge:** SOL:s socken för uppslaget. Ett sockennamn matchas mot ISOF:s socknar (`parishes.json`, mittpunkt) på namn
  och landskap; övriga uppslag på den socken SOL anger. Härads- och sockennamn hålls isär: ett häradsnamn som är bildat
  av ett sockennamn räknas en gång, som socknen. Uppslag utan läge räknas bort, och antalet redovisas.
- **Landsdelar** (de gamla rikena och landen, inte dagens landskap, fasta här): Mälarlanden (Uppland, Södermanland,
  Västmanland, Närke); Västra Götaland (Västergötland, Dalsland); Östra Götaland (Östergötland, Småland, Öland);
  Gotland; det danska riket (Skåne, Blekinge, Halland); det norska riket (Bohuslän, Jämtland, Härjedalen); Norr
  (Värmland, Dalarna, Gästrikland och norrlandskapen).

## Del A. Beskrivande
- Antal säkra och osäkra namn per gud och landsdel; en karta över alla teofora namn, med gud och grad.
- Gud och efterled (vi, harg, hov, lund, åker, tuna, sjö/ö, annat), som antal.
- Äldsta belägg per gud (median och spann), bara som bakgrund: ett belägg är inte namnets ålder.

## Del B. Två prov (Tor, Oden och Frö; säkra och osäkra; tvåsidiga; Holm över de två, α = 0,05)
Proven jämför gudarna med varandra *bland de teofora namnen*, så att SOL:s ojämna täckning (fler uppslag där det finns
fler socknar) inte kan ge ett mönster. Omblandningen: gudsetiketterna blandas om mellan namnen, 10 000 gånger, med
slumpfrö ur planens kontrollsumma (de första 8 hextecknen som heltal).
- **B1. Gud och landsdel.** Teststorhet: χ² för tabellen gud × landsdel. p = andelen omblandningar med minst lika stort
  χ² (+1 i täljare och nämnare).
- **B2. Grannar.** För varje namn: andelen av dess tre närmaste teofora grannar (fågelvägen mellan socknarnas
  mittpunkter) som har samma gud; teststorheten är medelvärdet. p som i B1.

Ett prov **håller** när Holm-justerat p < 0,05 och teststorheten, räknad på bara de säkra namnen, ligger över
omblandningarnas median. **Styrkan är låg:** med omkring 35 namn kan bara stora skillnader upptäckas. Ett prov som inte
håller visar inte att tron var enhetlig, och skrivs inte så.

## Vad som inte prövas
Ull, Njärd, Fröja, Frigg och Tyr (för få namn: de redovisas ett och ett, med SOL:s tolkning), när namnen gavs, hur tron
spreds, och Danmark och Norge utanför dagens Sverige (stående regel: Sverige som standard). Artikelns läsning av
spridningen – vattenvägarna, stormännen, tingen – skrivs som en läsning ur litteraturen, inte som ett resultat.

## Utdata
`utdata/asatro/analys.py` → `utdata/asatro/resultat.json` (antal, landsdelar, prov; inga citat ur SOL) och
`/Volumes/2TB/Antigrvity/Runes/downloads/asatro/kodning.csv` (meningarna ur SOL; utanför git).
