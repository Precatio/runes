# Upptäcktsmotorn v4 – beroendenätverket: resultat

Låst plan `analysplaner/2026-11-01-upptacktsmotorn-v4-natverk.md` (sha c43e65b7). Kört 2026-11-01 med `r/discovery_v4.R`
(bnlearn 5.2.1); `resultat.json`, nätverken `natverk_A.rds` och `natverk_B.rds`, kandidaterna `kandidater.json` (frusen).

## Avvikelse
Skattningen gick igenom första gången, men skrivningen av resultatfilen föll (en tabell som JSON). Rättat; de sparade
nätverken lästes in i stället för att skattas om (samma frö, samma data). Inget annat ändrades.

## Utfall
**Halva A (846 stenar):** 80 kanter med styrka ≥ 0,85. **74 går inom en familj** – drag som hänger ihop per definition,
som *korsformel*–*bön*, *bön*–*själabön*, *stungna runor*–*stungen e/y/g*, *signatur*–*risti*/*runaR*, skiljetecknens
former, *resa*–*död borta*, *kvinna resare*–*kvinna ensam*, *barn*–*förälder*. **3 går till bakgrunden:** ristarnamnet,
formen *þannsi* och verbet *satti* följer landskapet. **3 går mellan familjer** och blev kandidater
(*monoftong*–*r för R*, *signatur*–*stungen y*, *r för R*–*prepositionen at*). **Ingen bekräftades i halva B.** Bytta
halvor: 76 kanter, 3 kandidater, ingen bekräftad.

**De 15 kända paren:** inget är en kant i nätverket. För 14 finns ingen väg alls mellan dragen i A:s nätverk: nätverket
faller sönder i familjer, och sambanden mellan familjerna är för svaga för att klara BIC-straffet och tröskeln på 846
stenar. Ett par får en förklaring: **o-runan och barnrelationen går via ordet *sun*** (o_runa – ord_sun – rel_barn).
Det är just det v1 misstänkte, att o-runan mäts i några få ord som *sun* och *broður*; nätverket visar det utan att
vi bett om det.

## Vad det betyder
Metoden återfinner materialets definitionsstruktur nästan helt (74 av 80 kanter) men ser inga nya direkta samband mellan
familjer. Med BIC och knappt 850 stenar per halva är ett Bayesianskt nätverk för försiktigt för de måttliga samband som
parprövningarna har bekräftat; att paren saknar kant betyder därför inte att de är falska, bara att nätverket inte kan
skilja dem från brus. Negativt fynd; ingen bild, eftersom ingen kant bekräftades. Inget införs i appen.
