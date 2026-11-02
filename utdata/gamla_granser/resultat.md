# Statistiken efter de gamla gränserna – resultat (IMPLEMENTATIONSPLAN 5.2)

Låst plan `analysplaner/2026-11-02-gamla-granser-statistik.md` (sha 13084e18). Jämförelse med `utdata/gamla_granser/
jamforelse.py`: korpus 605ba7cc (dagens landskap) mot 622e0506 (de gamla regionerna; ISOF som förstakälla för sockens
härad, Gotlands tredingar). Siffror i `jamforelse.json`.

## Avvikelser
- Första omräkningen (a398c0c2) gav ingen skillnad: kolumnen `region_old` saknades i korpusens fasta kolumnlista, så
  modulerna fick dagens landskap. Rättat (a31f43e).
- Andra omräkningen (5690b172): mönstren *Regional skillnad* jämför nu par av gamla regioner, men trappans underlag
  filtrerade fortfarande på landskapskoden, så paren fick för få stenar. Rättat (58a3787).
- Mellan körningarna ersattes Wikidata av ISOF:s register som förstakälla för sockens härad (5e78157); fyra socknar fick
  rätt land. Det ingår i den slutliga jämförelsen.

## Robusthetstrappan: 14 av 31 mönster håller i alla steg (15 av 33 före)
**De regionala skillnaderna gäller nu par av gamla regioner** och blir oftast skarpare:
- Prepositionen *at*: Södermanland mot **Attundaland** (oddskvot 10,2, förut Sö mot hela Uppland 4,8).
- r för ʀ: **Fjädrundaland** mot Södermanland (38,4, förut Uppland mot Sö 4,4). Håller nu i alla steg (förut föll en halva).
- Själabön: **Attundaland** mot Västergötland (25,0, förut Uppland mot Vg 20,6).
- Kors: **Tiundaland** mot Västergötland (2,9). Förut höll Uppland mot Vg i alla steg; nu faller ena halvan och stegen
  utan flyttade stenar.
- Bro och väg: **Roden** mot Östergötland (5,7), nytt par; faller i ena halvan.
- Monoftong (ai): Västergötland mot Södermanland, oförändrat.
- Bön och stungna runor (Ög mot U) finns inte längre som regionala mönster: när Uppland delas finns inget par där de
  sticker ut lika mycket.
**Förändringarna över tid** står sig. Bönens nedgång håller nu i alla steg (förut vände riktningen utan Uppland; nu
lämnas Attundaland ut i stället och riktningen håller). Monoftongens ökning faller i steget utan en region i taget
(utan Attundaland).

## Ordförrådet
375 ord–landskap-prov blev 525 ord–region-prov; 14 signaler höll i båda halvorna förut, 9 nu. Nya: *ok*, *and* och
*hans* hör till **Attundaland**. Kvar: *at* och *æftiR* i Södermanland, *ræisti*, *goðan* och *æftiR* i Västergötland,
*æftiR* i Östergötland.

## Genomsökningen av platserna
Oförändrad: 0 av 117 klarar justeringen, med båda indelningarna.

## Läsning
Med de gamla gränserna blir de regionala skillnaderna i språket både skarpare och mer precisa: det är Fjädrundaland som
skriver r för ʀ och Attundaland som skiljer sig i *at*, inte "Uppland". Två uppländska mönster (korset, bönen mot
Västergötland) var mindre robusta än de såg ut när hela Uppland räknades som ett. Förändringarna över tid påverkas
knappt.
