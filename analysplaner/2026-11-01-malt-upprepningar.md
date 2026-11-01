# Analysplan: upprepningar i Maltstenens ristning

Skriven och låst 2026-11-01, innan något upprepningsmått har räknats på Malt eller på jämförelsematerialet. Viktor
2026-11-01: "kör på det spåret. Vårt långtgående mål med hela appen är egentligen att kunna förstå Maltstenen bättre."

## Bakgrund och vad som är känt före låsningen
Textmodellen med litteraturlexikon (tm22, negativ) läste en av Maltstenens skiljeteckengrupper, *titultitul*, som två
likadana ord. Läsningen används inte (lexikonet klarade inte sitt prov). Men själva ristningen har här samma fem runor
två gånger i rad inom en grupp, och *huaR* står tre gånger. Före låsningen är bara känt: Malts text i
`scripts/malt_decode.text` har 136 runor i 18 grupper; i Rundata finns 172 vikingatida runstenar med 91–204 läsbara runor
(150 svenska, 22 danska), 15 andra stenar och 8 lösa föremål med minst 100 runor. Delprov 2 i `utdata/sprakprov/
monster.py` (längsta upprepning på de 55 inskrifterna som inte liknar språk) är känt men mäter något annat.

## Frågorna
1. **Hur ovanligt är en direkt upprepning** (samma följd på minst fem runor två gånger i rad, *XX*) inom en
   skiljeteckengrupp i vikingatida runinskrifter, och vad är de inskrifter som har en? (beskrivande)
2. **Upprepar Malt mer än jämförbara runstenar?** (konfirmatoriskt)
3. **Liknar Malts upprepningar dem i tolkad text eller dem i inskrifter som inte liknar språk?** (beskrivande)

Ingen fråga gäller vad Malts runor betyder. Inga läsningar av Malt föreslås.

## Data
- Rundata som i `src/runlm.load_rundata`, vikingatida enligt `runlm.viking`, Malt (DR NOR1988;5) utesluten ur
  jämförelsen. Objekttyp enligt `runlm.object_kind`; runstenar är huvudmaterial, andra stenar och lösa föremål redovisas
  för sig.
- **Runföljden:** huvudläsningen som i `scripts/runlm_sprakprov.segments` (avsnitt §..Q bort, av a/b den första,
  `clean_translit`), men skiljetecknen `:÷'·×+|¶` behålls som gruppgränser; mellanslag i Rundatas translitterering
  (utgivarens ordgränser) räknas inte som gränser. Förlorade eller olästa tecken bryter följden.
- **Malt:** `malt_decode.text` med modellens bästa val i de sex omstridda punkterna; känslighet över alla 64.
  Känslighet också med Rundatas egen translitterering av DR NOR1988;5.

## Mått
- **T_k:** inskriften har en direkt upprepning *XX* med |X| ≥ k inom en obruten gruppföljd (k = 5 huvudmått; 3 och 4
  beskrivande). Upprepningar som bara är samma runa i följd (|X| = 1) räknas inte.
- **D4 (upprepningstäthet):** andelen positioner för fyrrunsföljder (inom obrutna följder, över skiljetecken) vars följd
  förekommer minst två gånger i inskriften. D3 och D5 som känslighet.

## Prov
**Fråga 2 (konfirmatoriskt):** Malts D4 mot fördelningen bland vikingatida runstenar med 91–204 runor (alla landskap och
länder, Malt utesluten). Malt **upprepar mer än jämförbara runstenar** om Malts D4 ligger över 95:e percentilen, och
gör det i alla 64 kombinationer av de omstridda punkterna. Redovisas också: percentilen bland danska och bland svenska
för sig, för D3 och D5, och med Rundatas translitterering.

**Fråga 1:** andelen runstenar (och för sig andra stenar och lösa föremål) med T_5, T_4, T_3; varje inskrift med T_5 och
T_4 listas med följden, objekt, Rundatas normalisering och översättning.

**Fråga 3:** varje upprepning i listan klassas för hand i en av fem grupper, utifrån Rundatas normalisering och
översättning, och klassningen redovisas per inskrift: (a) samma ord två gånger, (b) namn, (c) formel eller besvärjelse
(t.ex. þistil-mistil-kistil, þurs-formler), (d) Rundata har ingen tolkning, (e) annat (t.ex. ristarfel). Dessutom:
Malts D4 mot D4 hos de 55 inskrifterna som inte liknar språk och de 35 språkliknande i `utdata/sprakprov/sprakprov.json`
(beskrivande, ingen gräns).

## Vad som inte får göras
Längdbandet, måtten och gränsen ändras inte efter körningen. Inga läsningar eller tolkningar av Malts upprepade
följder läggs till; resultatet beskriver ristningen.

## Redovisning
`utdata/Malt/upprepning.py`, `utdata/Malt/upprepning.json`, `utdata/Malt/upprepning_resultat.md`.
