# A1, tillägg 1, not 4: förtydliganden för de övriga banden

Skriven och låst 2026-11-14, innan något av de övriga banden har plockats ut. Gäller `2027-01-A1-tillagg-1-sri-fyndhistorik.md`
och noterna 1–3. Viktor sade ja 2026-11-14.

## Utfallet för Uppland (runda 2, slutligt)
| Fältgrupp | Rätt | Wilson 95 % | Används i A1? |
|---|---|---|---|
| Läget | 95,0 % (285/300) | 0,92–0,97 | ja |
| Flyttningarna | 90,0 % (90/100) | 0,83–0,94 | nej |
| Försvunnen och återfunnen | 97,5 % (195/200) | 0,94–0,99 | ja |
| Samma sten | 99,0 % (99/100) | 0,95–1,00 | ja |

**Viktors kontroll** omfattade 10 stenar och fyra fält. Hans fyra fel prövades mot SRI-texten, och han godtog
prövningen ("kör på din bedömning"):
- U 105 (läget) och U 242 (ursprunglig plats) var rätt utplockade.
- U 31 (ursprunglig plats) och U 547 (inmurad) var fel.

Granskaren hade alltså missat ett fel, och räknas inte som för snäll. Förloppet står i `utdata/sri_fakta/upp2_kontroll.json`.

## Förtydliganden i instruktionen
Förtydligandena gäller Öland, Gotland I–II, Gotland III, Västmanland, Närke, Värmland och Gästrikland, som var och en
får sin runda 1. De rättar mönster som granskningen av Uppland visade. Inga fält eller kategorier ändras.

1. **En sten som bara ligger i en byggnad är ingen flyttning.** Står det bara att stenen "låg i kyrkdörren" eller
   "satt i muren", utan att utgivaren säger att den förts dit, blir det ingen post i `flyttningar`. Läget beskrivs i
   stället i `inmurad` eller `lage_vid_utgavan`. Regel 6 gäller när utgivaren säger att stenen murades in eller lades
   in.
2. **Årtal.**
   - Decennier ("på 1850-talet") och osäkra uppgifter ("torde", "omkring", "troligen") ger `ar = null`.
   - Ett spann med säkra årtal ("1863—64") ger det första året, som förut.
3. **Orsaker.**
   - Återresning på eller strax intill platsen (inom omkring 100 m, eller "i omedelbar närhet") är "återresning på
     samma plats eller i närheten", också när stenen flyttades några meter.
   - Ett monumenthus, ett museum, en samling eller en park som samlar runstenar är "samling eller museum".
   - Kyrkogårdens utvidgning räknas som "kyrkbygge eller restaurering".
4. **Inmurad, rättelse.** Läsarnas instruktion nämnde felaktigt *trappa*. Fältet följer planens definition: stenen
   satt eller sitter inmurad i en kyrka eller annan byggnad, det vill säga i en vägg, en mur, en grund, ett golv eller
   en tröskel i en dörröppning. En trappsten utanför byggnaden är inte inmurad.

Kraven, stickprovets storlek (100 stenar), Viktors kontroll och regeln om högst två rundor är desamma som i not 2.
