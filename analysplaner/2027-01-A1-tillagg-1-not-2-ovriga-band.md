# A1, tillägg 1, not 2: rutinen för de övriga banden

Skriven och låst 2026-11-12, innan något annat band än Södermanland har plockats ut. Gäller
`2027-01-A1-tillagg-1-sri-fyndhistorik.md` och not 1. Viktor sade ja 2026-11-12.

## Utfallet för Södermanland (runda 2, slutligt)
| Fältgrupp | Rätt | 95 %-intervall | Används i A1? |
|---|---|---|---|
| Läget | 95,0 % (171/180) | 0,91–0,97 | ja |
| Flyttningarna | 95,0 % (57/60) | 0,86–0,98 | nej (nedre gränsen 0,86 är under kravet 0,88) |
| Försvunnen och återfunnen | 98,3 % (118/120) | 0,94–1,00 | ja |
| Samma sten | 98,3 % (59/60) | 0,91–1,00 | ja |

Viktor kontrollerade 8 av sina 20 stenar, alla fält (80 bedömningar). Allt var rätt och stämde med granskaren.

## Ändringar för de övriga banden
1. **Större stickprov: 100 stenar per enhet** i stället för 60. Kravet är detsamma: minst 95 % rätt och en nedre
   Wilsongräns på minst 0,88. Med 60 stenar och ett fält per grupp krävs i praktiken 58 rätt av 60. Det stora
   stickprovet gör att en verklig träffsäkerhet på 95–96 % kan klara gränsen.
2. **Enheterna.** Upplands fyra band (SRI VI–IX) bildar en enhet, med slumpfrö 2030. Övriga band är var sin enhet,
   med slumpfrön i den ordning de körs från 2032 och uppåt.
3. **Instruktionen** är densamma som i Södermanland, runda 2, inklusive de fem reglerna. Ett tillägg är tekniskt
   nödvändigt: i Uppland gäller en artikel ibland flera stenar ("309—311."). Läsaren får då veta vilket signum raden
   gäller och plockar bara uppgifter om den stenen.
4. **Viktors kontroll** omfattar 10 stenar ur stickprovet, med slumpfrö 2031 för Uppland. Den gäller bara läget
   (`lage_vid_utgavan`, `ursprunglig_plats_text`, `inmurad`) och flyttningarna.
   - Hans bedömning går före granskarens.
   - Har han fel eller saknat i minst två fält som granskaren bedömt som rätt, räknas granskaren som för snäll. Då
     granskas enheten om på ett nytt stickprov, och det räknas som enhetens runda 2.
5. **Rundorna är högst två** per enhet, som i not 1.
6. **Täckningen.** Sten för sten delas artiklarna upp av `scripts/sri_artiklar.py`. Rubrikmönstret klarar nu spärrad
   OCR, sammansatta ord ("Domkyrkan") och rubriker som gäller flera nummer. Sidhuvuden räknas inte som rubriker.
   - Nummer utan artikel redovisas per band. Uppland: 1 040 av 1 181. Södermanland efter rättningen: 367 av 383.
   - En sten utan artikel har ingen SRI-uppgift. Den räknas inte som en sten utan flyttning eller utan förlust.
   - De 13 artiklar om Södermanland som tillkom efter piloten plockas ut med samma instruktion. De ingår inte i
     Södermanlands stickprov.
