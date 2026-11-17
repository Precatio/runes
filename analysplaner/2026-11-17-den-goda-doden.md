# Analysplan: den goda döden – hur runstenarna berättar om döden

Skriven och låst 2026-11-17, innan något av proven nedan har räknats. Underlag för en populärvetenskaplig artikel i
samma anda som "Mild i ord och god på mat" (Viktor 2026-11-17: "Den goda döden: hur stenarna berättar om döden – i
strid, i sängen, drunknad, i främmande land – gör denna"). Sverige är huvudfokus (stående regel).

## Känt före låsningen
- **Ordförrådet är inventerat, inte korstabulerat.** I Rundatas engelska översättning av svenska inskrifter står ett
  dödsord (died, killed, fell, drowned, betrayed, burned, perished, met his end, lost his life, murdered, sick) i 174
  inskrifter, runstenar och annat, vikingatida och medeltida. Rundatas normalisering har *drunknaði* på omkring tio,
  *drepinn* omkring 17, *fell* sju, *í hvítavaðum* sex (alla i Uppland), *sóttdauðr*/*sjúkr* två. Inskrifterna lästes
  en och en för att formulera kodningsreglerna nedan. Inget av dem har räknats mot tid, plats, beröm eller tro.
- **Utlandsfärden är redan prövad:** rapporten "Söner och bröder dog utanför Norden oftare än fäder och makar" (10 mot
  3 procent) och artikeln "Färderna var de ungas". Den prövas inte igen; den redovisas.
- **Litteraturen:** inga räkningar av hur döden berättas på runstenarna i Fornvännen 1906–2023 eller Futhark 1–15
  (sökning i sok.sqlite på dödsorsak, dödssätt, drunknade, sotdöd, dopkläder, hvitavaðum). Nerman 1917 (Fornvännen 12,
  s. 226 ff.) ställer upp Ynglingatals och Snorres uppgifter om kungarnas död, bland dem sotdöd, och används som
  litterär bakgrund, inte som hypotes.

## Data
- Stenarna: Rundatas vikingatida runstenar enligt `nordic.is_runestone`, land `sverige` (2 321). Läsbar text:
  `nordic.features(rec)` är inte None.
- Tid: `nordic.year_of` och `nordic.bin_of` (före 1000, 1000–1050, 1050 och senare). Stenar utan år räknas bort ur de
  prov som behöver tid; antalet redovisas.
- Landskap: signumets prefix.
- Beröm: `nordic.features(rec)["praise"]` eller `["titel"]` (good, best, bravest, most generous, mildest, very good;
  þegn, drængr).
- Utomlands: `nordic.features(rec)["fard"]`.

## Kodningen av döden (låst här, görs innan något räknas mot andra drag)
En sten **berättar om döden** när texten säger hur eller var den döde som stenen är rest efter dog: verben died,
drowned, killed, slain, fell, betrayed, burned, perished, murdered, "met his/their end", "lost his life", "was dead",
"was sick", "died from sickness" i Rundatas engelska översättning. Adjektivet *dead* ("his dead son") räknas inte.
Händelser som gäller någon annan än den döde (Röks hjältar; Sö 196, där den döde dödade någon) räknas inte. En sten med
flera döda räknas en gång, efter den första döden som beskrivs.

Sättet, i den här ordningen (första som passar):
1. **Våld:** killed, slain, murdered, fell, betrayed, burned.
2. **Drunknad:** drowned.
3. **Sjukdom:** sick, sickness.
4. **I vita kläder (dopkläder):** died in christening robes (*í hvítavaðum*).
5. **Utan sätt:** died, perished, met his end, lost his life, was dead.

Varje kodad sten skrivs till `utdata/doden/kodning.csv` med signum, sätt, citatet ur översättningen och, där den
behövs, skälet. Ett osäkert ord i Rundata ("fell(?)", "died(?)") räknas, men flaggas och redovisas.

## Del A. Beskrivande
- Andelen svenska runstenar med läsbar text som berättar om döden, med Wilson-intervall, och per landskap (landskap med
  minst 30 stenar).
- Fördelningen på sätten, och för varje sätt hur ofta döden skedde utomlands (`fard`).
- Exempel ur varje sätt, ordagrant ur Rundatas normalisering och översättning.

## Del B. Två prov (tvåsidiga, Holm över de två, α = 0,05)
- **B1. Beröm vid våldsam död.** Bland stenar som berättar om döden: andelen med beröm för den döde, våld (sätt 1) mot
  övriga sätt (2–5). Mantel–Haenszel över tidsskikten (`nordic.mantel_haenszel`), stenar utan år utanför. Fisher exakt
  test utan tid redovisas bredvid.
- **B2. Döden berättas mer sällan på de sena stenarna.** Bland alla stenar med läsbar text och år: andelen som berättar
  om döden, 1050 och senare mot före 1050. Mantel–Haenszel över landskapen (landskap med stenar på båda sidor).

Ett prov **håller** när Holm-justerat p < 0,05 och det håller i båda halvorna (`question.halves`, samma
sockenhalvor som Pröva en egen fråga: samma riktning och p < 0,05 i båda, eller, när en halva har färre än 10 stenar
med utfallet, samma riktning). B2 räknas också om utan Uppland; riktningen ska hålla.

## Vad som inte prövas
Utlandsfärden (redan prövad), sjukdom och dopkläder (för få stenar för ett prov; de redovisas en och en), och vad döden
betydde. Tolkningen – den goda döden i strid eller i sängen, i Ynglingatal och hos Snorre – är artikelns läsning och
skrivs som en läsning, inte som ett resultat.

## Utdata
`utdata/doden/analys.py` → `utdata/doden/resultat.json` och `utdata/doden/kodning.csv`.
