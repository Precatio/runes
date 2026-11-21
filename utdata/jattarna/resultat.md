# Jättarna – resultat (fördjupning 3 i serien Nordiska väsen)

Enligt `analysplaner/2026-11-21-jattarna.md` (låst d57af06) med den frysta ordlistan `ordlista.csv` (sha256 ce1e6dd8…).
Räknat 2026-11-21 med `utdata/jattarna/analys.py`; siffrorna i `matt.json`, efterkontrollen i `efterkontroll.json`.

## Kvalitetsgrinden (klarad) – och ett fel den inte fångade
- **Grinden:** 102 slumpade träffar, högst 10 per term, bedömda för hand. 96 var riktiga, viktat 97,8 % (krav ≥ 90 %).
  Varje term med minst 20 träffar låg på ≥ 80 %. Felen var:
  - kenningar där ordet betyder något annat ("trollkvinna" för yxa);
  - *upp risinn* (uppstigen);
  - *þursligir* om män;
  - *risinn* på en runsten (rest).
- **Upptäckt efter räkningen:** utanför Eddan är termerna för namngivna jättar och jättinnor ofta något annat:
  - *Greip* är verbet "grep";
  - Surtr och Baugi är personnamn i islänningasagorna;
  - Skrýmir är ett svärd;
  - Gillingr i Gautreks saga är en bonde.

  Alla 71 sådana träffar i sagorna lästes för hand, och omkring 29 är verkliga jättar (till exempel tröllkonan Gríðr i
  Illuga saga). Grindens stickprov för de två termerna råkade bara innehålla Eddaträffar. Resultatet redovisas med
  och utan dessa namn.

## J1 Var jättarna finns (träffar per 10 000 ord)
| korpus | täthet |
|---|---|
| Gylfaginning | 91,0 |
| Skáldskaparmál | 72,9 |
| Eddadikterna | 54,3 |
| Fornaldarsagorna, vers | 14,3 |
| Islänningasagorna, vers | 12,0 |
| Fornaldarsagorna, prosa | 8,4 |
| Heimskringla, vers | 8,3 |
| Islänningasagorna, prosa | 1,7 |
| Samtidssagorna | 0,6 |
| Heimskringla, prosa | 0,5 |

- **Eddadikterna:** mest namngivna jättar (109), *jötunn* 91, namngivna jättinnor 29 och *þurs* 19.
- **Fornaldarsagorna:** *tröll* 101, *jötunn* 67, *risi* 30, namngivna jättinnor 20 (Gríðr) och *tröllkona* 18.
- **Islänningasagorna:** *tröll* 75, *þurs* 17 och *jötunn* 14.

## J2 Ordet *risi* (beskrivande, inte prövat)
Andelen *risi* bland *jötunn*, *þurs* och *risi*:

| text | *risi* | av | andel |
|---|---|---|---|
| eddadikterna | 0 | 110 | 0 % |
| Gylfaginning | 7 | 52 | 13 % |
| Skáldskaparmál | 0 | 41 | 0 % |
| islänningasagorna | 8 | 39 | 21 % |
| fornaldarsagorna | 30 | 103 | 29 % |

Ordet *risi* saknas helt i eddadikterna. Det var känt i grova drag före låsningen och prövades därför inte.

## J3 De vanligaste namngivna
- **Jättar:** Vafþrúðnir, Útgarða-Loki, Hymir, Skrýmir, Hrungnir, Þjazi, Surtr, Baugi, Ymir och Þrymr.
- **Jättinnor:** Gríðr, Hrímgerðr, Greip (i Eddan), Hyndla, Fenja och Menja, Gjálp, Bestla och Hyrrokkin.

## J4 Runstenarna
Två träffar, båda falska: *Greip* på Ög 64 är en mans namn, och *risinn* på U 703 betyder "rest". **Inga jättar i
runstenarnas texter.**

## J5 Ortnamnen (Svenskt ortnamnslexikon)
48 kandidater lästa. Åtta namn tolkas av SOL som jätte- eller trollnamn, säkert eller möjligt:
- **Edenryd** (Skåne): troligen *iætæn* "jätte"; en tradition från 1620-talet säger att jättar bodde i ett stenröse
  där.
- **Gigerugnen** vid Ekornavallen (Västergötland): en gånggrift, sannolikt "jättekvinnans ugn" (motsvarande fvn.
  *gýgr*).
- **Trollhättan** (Västergötland): fallet liknat vid ett vattentrolls hätta.
- **Trullhalsar** (Gotland): ett gravfält, "trollhalsar".
- **Bobergs härad** (Östergötland): möjligen *bo* "boning", om jättar eller troll i berget.
- **Tossebergsklätten** (Värmland): möjligen *tusse* "jätte".
- **Locknevi** (Småland): en av tolkningarna är "trollkäring".
- **Trollaborg** (Småland): sägner om troll, eller släkten Trolle.

Därtill finns två samiska namn med *stállo*, den människoätande jätten (Staloluokta och Stalon). Bland namnen som
**inte** är jättenamn finns **Jättendal** (*iæt* "betesmark") och **Jättene** (*gátt* "öppning"). Tre av de åtta
svenska namnen sitter på förhistoriska gravar och stenar: Gigerugnen, Trullhalsar och Edenryds stenröse.

## Testerna (Holm över T2 och T3)
- **T2 kvinnorna: håller inte.**
  - Andelen jätteträffar som betecknar en kvinna är 11,7 % i Eddan och 22,9 % i sagorna. Skillnaden är −11,1
    procentenheter (95 % intervall −23,9 till 3,6), med p 0,12.
  - **Känslighet** (utan egen slutsats): utan *tröll* blir det 11,9 % mot 36,2 % (−40,0 till −7,1). Bara
    fornaldarsagorna ger 25,2 %, och bara islänningasagorna ger 16,1 %. Ingen av dem håller.
  - **Efterkontroll** (olåst, utan namngivna jättar i sagorna): 11,7 % mot 20,0 % (−18,9 till 5,2). Utan namn och
    *tröll* blir det 11,9 % mot 34,9 % (−37,3 till −7,8).
  - **Läsning:** när sagorna använder de bestämda jätteorden, och inte det allmänna *tröll*, är ungefär en tredjedel
    kvinnor: tröllkonor, flögð och skessor. I Eddan är andelen en åttondel. Det är en **hypotes** för en ny låst
    plan, inte ett resultat här.
- **T3 väderstrecket: obestämt.** Bara 18 jätteträffar i Eddan och 21 i sagorna har ett nord- eller östord inom ± 25
  ord (krav ≥ 20 i vardera). Med ± 10 ord blir det ännu färre. Jättarnas väderstreck går inte att mäta så här.

## Vad det betyder och inte betyder
- Jättarna hör till myten, liksom alverna. I sagorna lever de vidare, mest som *tröll*, och i fornaldarsagorna med egna
  namn (Gríðr).
- Ordet *risi* finns inte i eddadikterna men är vanligt i fornaldarsagorna.
- I Sverige sitter jättarna, när de finns i ortnamnen, på de gamla gravarna och stenarna: gånggriften, gravfältet och
  stenröset.
- Inget av de låsta testerna gav ett säkert resultat. Kvinnornas plats bland jättarna är en fråga för en egen plan.
