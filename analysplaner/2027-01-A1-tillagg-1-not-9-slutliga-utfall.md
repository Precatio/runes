# A1, tillägg 1, not 9: Gotland, Västergötland och Östergötland, rättningen av "inmurad" och de slutliga utfallen

Skriven och låst 2026-11-17. Gäller tillägg 1 och noterna 1–8. Kontrollen gjordes enligt not 8 (blind Opus-läsning av
de 10 lottade kontrollstenarna, Claudes utslag där läsaren och granskaren var oense), eftersom Viktor 2026-11-16 bad
Claude att göra alla bedömningar.

## 1. Gotlands runinskrifter 3 lästes med OCR
Textlagret i PDF:erna till Gotlands runinskrifter 3 (gr3, RAÄ:s preliminära artiklar) använder ett typsnitt med egen
kodning: brödtexten kom ut teckenförskjuten ("dçíä~åÇ" för "Gotland") i 130 av 148 artiklar, medan rubriker och runor
var rätt. Den första utplockningen av gr3 byggde alltså på oläslig text. Den granskades aldrig färdigt och räknas inte.
Alla 727 sidor lästes om med OCR (ocrmypdf, svenska), artikeldelningen gav samma 148 signum som förut, och gr3 plockades
ut på nytt. OCR-kopiorna ligger utanför repot. SRI XI–XII hade inget sådant fel.

## 2. Rättningen av "inmurad"
Fältet `inmurad` gäller bara byggnader (not 4: vägg, mur, grund, golv eller tröskel i en kyrka eller annan byggnad).
Läsarna och granskarna tog ändå genomgående med stenar i kyrkogårdsmurar, ringmurar, stenmurar och gärdsgårdar. Det
var den vanligaste oenigheten mellan den blinda läsaren och granskaren i not 8-kontrollen (Nä 27, Nä 8, Vg 144,
G 192, Ög 153, Ög 185).

Alla citat med `inmurad` som nämner en sådan mur lästes igenom i de slutliga utplockningarna (55 stycken). I 51 av dem
gäller citatet bara en kyrkogårdsmur, ringmur, stenmur eller gärdsgård. De sätts till null i A1
(`INMURAD_KYRKOGARDSMUR` och `slutlig()` i `scripts/sri_fakta_kontroll.py`). Fyra står kvar: Sm 153 ligger i
vapenhuset, och Sö 129, U 1132 och Vg 184 sitter i en kyrkogårdsport, där det inte går att avgöra om porten är en
byggnad. Stenarnas läge (`lage_vid_utgavan`) påverkas inte av rättningen.

**Följd för regeln om en för snäll granskare (not 2).** Ett fält som rättas mekaniskt räknas inte mot granskaren,
eftersom felet inte längre finns i data. Det är ett beslut i den här noten. Med den strängare läsningen, där också
dessa fält räknas, hade granskaren varit för snäll i Gotlands och Östergötlands runda 2 (2 och 3 fält), och båda
enheterna hade lämnats utanför A1. Rättningen gäller alla enheter lika.

## 3. Rundorna
- **Gotland runda 1** (SRI XI–XII och gr3 efter OCR, slumpfrö 2044/2045): andelarna klarade kraven (läget 97,7 %,
  försvunnen och återfunnen 97,0 %, samma sten 99 %), men granskaren var för snäll i tre fält: G 56 är ett återfynd
  ("överstrukna och dolda", "framtagits" vid restaureringen), och G 70 ansågs "förkommen" och spårades sedan igen.
  Gotland gick därför **runda 2** med samma utplockning (reglerna 1–13 gällde redan) och ett nytt stickprov om 100
  stenar bland de 264 som inte låg i runda 1 (slumpfrö 2058, kontrollens 10 med 2059).
- **Gotland runda 2:** G 192 (bogårdsmur) rättas enligt avsnitt 2, och G 210 står fel som försvunnen ("ej återfunnen"
  är C. Säves anmärkning vid ett dubbelnummer, och stenen var känd hela tiden). Två utslag gick emot den blinda läsaren:
  putsinskrifterna G 331 och G 374 är fasta ristningar, och enligt regel 4 är `ursprunglig_plats_text` då utgivarens
  beskrivning av platsen.
- **Västergötland runda 2:** Vg 144 (kyrkogårdsmur) rättas. Vg 130 avgjordes för den blinda läsaren: stenen "åter blef
  förd till sitt förra ställe", och enligt regel 2 är läget då "ursprunglig plats".
- **Östergötland runda 2:** Ög 153 och Ög 185 (kyrkogårdsmur) rättas. Ög 200 saknar ett återfynd: stenen var sedd,
  efterspaningarna "voro länge fåfänga", och den hittades till sist på en portstolpe.
- **De mellansvenska banden runda 2:** se not 8. Nä 10 är en guldbrakteat, inte en runsten; A1 gäller runstenar.

## 4. De slutliga utfallen (A1:s fältgrupper; flyttningarna används inte, not 7)
Andel rätt med Wilsons nedre 95 %-gräns inom parentes; kraven är minst 95 % och en nedre gräns om minst 0,88.

| Enhet | Kontroll | Läget | Försvunnen och återfunnen | Samma sten | För snäll? |
|---|---|---|---|---|---|
| Södermanland, runda 2 | Viktor | 95,0 % | 98,3 % | 98,3 % | nej |
| Uppland, runda 2 | Viktor | 95,0 % (0,919) | 97,5 % (0,943) | 99,0 % (0,946) | nej (1) |
| Småland, runda 1 | Viktor | 98,0 % (0,957) | 96,0 % (0,923) | 98,0 % (0,930) | nej |
| Östergötland, runda 2 | not 8 | 97,3 % (0,948) | 99,5 % (0,972) | 100 % (0,963) | nej (1) |
| Västergötland, runda 2 | not 8 | 98,0 % (0,957) | 99,0 % (0,964) | 99,0 % (0,946) | nej |
| Öland, runda 2 (samma 40) | not 8 | 95,8 % (0,906) | 100 % (0,954) | 100 % (0,912) | nej |
| Mellansvenska banden, runda 2 (samma 81) | not 8 | 96,7 % (0,936) | 99,4 % (0,966) | 100 % (0,955) | nej |
| Gotland, runda 2 | not 8 | 98,3 % (0,962) | 99,0 % (0,964) | 99,0 % (0,946) | nej (1) |

Alla åtta enheter klarar kraven och används i A1, med rättningen i avsnitt 2. Svagheterna redovisas i rapporten:
Öland och de mellansvenska banden granskades om på samma stenar, fem enheter kontrollerades inte av en människa
(not 8), och utfallen för läget i Uppland och Södermanland ligger precis på gränsen.
