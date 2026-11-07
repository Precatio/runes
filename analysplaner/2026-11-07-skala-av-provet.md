# Analysplan: skiljer *Skala av vittringen* huggning från vittring bättre än dagens djupbild?

Skriven och låst 2026-11-07, innan provet nedan har räknats. Viktor 2026-11-07: "gå vidare med detta" (provet med kända
runor efter att funktionen provats på tio stenar, utdata/skala_av/resultat.md).

## Känt före låsningen
Funktionen (src/peel.py, METHODS 2d2) är provad med ögat på tio skanningar: mycket bra på Gs 11, Sö 113, Vg 103 och M 3,
brusig på Sö 206 och Sö 162, svagare på U 1144 och Ög 2, fungerar inte på Hs 14; på Sö 128 blev en ramslinga grå. Inga
mått mot slingorna är räknade.

## Facit
Viktors granskade runslingor (data/runmodell/band/<serie>/<fil>.json, status "granskad"): 95 skanningsfiler i sex serier
(Södermanland 36, Västergötland 18, Medelpad 15, Hälsingland 12, gravmonument Ög/Sm 11, Åsmund 3), förda till ytans
rutnät med `rune_bands.drawn_labels` (samma vy som djupbildscachen). Slingorna är textytan: de omfattar också mellanrummen
mellan runorna, och ornamentik och kors ligger utanför; måttet är därför hur väl bilden samlar det den visar i texten,
inte hur många runor som kan läsas.

## Jämförelsen
För varje fil, på ytan som dialogen använder (`stone_report.Surface`, högst 2 400 bildpunkter, inom `Peel.use`):
- **A, dagens bild:** djupet under referensytan längs projektionen (`-Surface.residual`), med en gemensam gräns för hela
  stenen vald så att **lika stor andel av ytan** visas som i B.
- **B, avskalat:** det som ligger djupare än den lokala vittringsnivån (reglaget 0 mm), alla fläckar.
- **C, avskalat, bara spår:** fläckarna som räknas som spår (roströda).
Mått: **precision** = andelen av det visade som ligger inne i slingorna; **slumpnivå** = slingornas andel av ytan;
**lyft** = precision / slumpnivå (1 = som slumpen).

## Prov
**P1 (huvudprov).** Lyftet för B jämfört med A, parvis per fil: Wilcoxons teckenrangtest, ensidigt (B högre). **Håller** om
p < 0,05 och medianen av skillnaden är positiv.
**P2.** Lyftet för C jämfört med A, parvis (C visar mindre yta; beskrivande, samma test redovisas).
**Per serie** (beskrivande): median av lyftet för A, B och C, och andelen filer där B > A.

## Tolkning (bestämd nu)
Håller P1 samlar avskalningen huggningen i texten bättre än dagens bild vid samma mängd visad yta – ett mått på att den
skiljer huggning från vittring, inte att runorna blir lästa rätt. Håller P1 inte redovisas det i artikeln om funktionen,
med de serier där den hjälper och där den inte gör det.

## Redovisning
`utdata/skala_av/provet.py` (en fil), `provet_kor.sh` (alla, en process per fil), `provet_sammanstall.py` →
`provet.json` och `provet.md`.
