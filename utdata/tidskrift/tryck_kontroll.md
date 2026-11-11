# Korpus nr 1 – tryckkontroll

Skrivs av `utdata/tidskrift/tryckkontroll.py` (anropas av `bygg_tidskrift.py --tryck`). Tryckeri: Helloprint, häftade broschyrer A4 (helloprint.com/sv-se/heftadebroschyrer).

## Svenska: `Korpus_nr1_sv_tryck.pdf`

- Sidor: **20** (delbart med 4: ja).
- Sidformat: 216.0 × 303.0 mm = A4 + 3 mm utfall på alla kanter. TrimBox [3.0, 3.0, 213.0, 300.0] mm, BleedBox [0.0, 0.0, 216.0, 303.0] mm. Inga skärmärken (Helloprint kräver inga; de ska inte ligga i utfallet).
- Typsnitt: 72 delmängder (AvenirNext-Bold, AvenirNext-DemiBold, AvenirNext-Italic, AvenirNext-Medium, AvenirNext-Regular, Charter-Black, Charter-Bold, Charter-BoldItalic, Charter-Italic, Charter-Roman, TimesNewRomanPSMT); inbäddade: alla.
- Text närmast skärkanten: 6.1 mm (s. 1, ”Omslag: U 489 vid Morby, Uppland – Gulla”). Kravet är minst 4 mm (Helloprint) / 5 mm (vår regel).
- Övertryck: inget (/OP true saknas i filen).
- Färgrymder i filen: DeviceGray, DeviceRGB, ICCBased. Filen är **RGB** (se nedan). **Viktor 2026-11-11: RGB går bra – filen laddas upp som den är, ingen CMYK-konvertering.**

### Bilder: effektiv upplösning i tryckt storlek

Under 300 dpi markeras; under 200 dpi är ett verkligt problem i tryck. **Viktor godkände upplösningen som den är (2026-11-11), även s. 5.**

- s.  1 bild 0: 2472 × 3296 px, icc, 276 dpi – under 300 dpi
- s.  1 bild 1: 396 × 275 px, gray, 300 dpi – ok
- s.  1 bild 2: 232 × 145 px, gray, 300 dpi – ok
- s.  1 bild 3: 557 × 285 px, gray, 300 dpi – ok
- s.  1 bild 4: 876 × 163 px, gray, 300 dpi – ok
- s.  1 bild 5: 1185 × 186 px, gray, 300 dpi – ok
- s.  3 bild 6: 2721 × 3817 px, icc, 320 dpi – ok
- s.  5 bild 7: 1536 × 1011 px, icc, 180 dpi – **PROBLEM < 200 dpi**
- s.  6 bild 8: 1280 × 1707 px, icc, 577 dpi – ok
- s.  9 bild 9: 2315 × 2552 px, icc, 272 dpi – under 300 dpi
- s. 11 bild 10: 1280 × 1707 px, icc, 577 dpi – ok
- s. 12 bild 11: 757 × 1000 px, icc, 235 dpi – under 300 dpi
- s. 14 bild 12: 529 × 767 px, icc, 238 dpi – under 300 dpi
- s. 15 bild 13: 1280 × 948 px, icc, 576 dpi – ok
- s. 18 bild 14: 2000 × 685 px, icc, 292 dpi – under 300 dpi

## Färg: RGB tills tryckeriets profil finns

- Helloprint vill ha CMYK med FOGRA39 (ISO Coated v2), total färgmängd högst 300 % (bilder 260 %), liten svart text som 100 % K. Profilen finns inte på den här datorn (sökt i Ghostscript, /Library/ColorSync, ~/Library/ColorSync och Adobe-mapparna), så `Korpus_nr1_sv_tryck.pdf` är **RGB** med utfall och boxar. Inget har installerats.
- Förberett i filen: all svart och grå text och alla grå linjer ligger i **DeviceGray** (svart text = ren svart), så att de går till bara K-plåten vid konverteringen. Rosten (#b7410e) och bilderna är RGB.
- Konverteringen är byggd och provad: `bygg_tidskrift.py --bara-tryck --icc <profil.icc>` skriver `Korpus_nr1_sv_tryck_cmyk.pdf` som PDF/X-3 med profilen som OutputIntent (Ghostscript, ingen nedsampling). Provkörd med Ghostscripts egen default_cmyk.icc (inte för tryck): 20 sidor, TrimBox/BleedBox kvar, och separationerna visar 0 % C, M och Y under all svart text (bara K).
- Att göra före tryck: hämta ECI:s profil **ISOcoated_v2_300_eci.icc** (ISO Coated v2 300 %, FOGRA39, gratis från eci.org) – den håller 300 %-gränsen – och kör kommandot ovan. Helloprints 260 % för bilder: be tryckeriet bekräfta om deras preflight gör det, eller använd deras egen profil om de har en.

## Papper (förslag för 20 sidor, häftad)

- Omslag 250 g/m² bestruket (silk eller gloss), gärna laminerat (matt), och inlaga 135 g/m² (eller 170 g/m² för en tyngre känsla). Med separat omslag är 20 sidor = 4 omslagssidor + 16 inlagesidor; fråga Helloprint hur de räknar.
- Alternativ: självomslag – alla 20 sidor på samma papper (t.ex. 170 g/m²). Billigare och enklare, men omslaget blir mjukare och tål mindre.

## Baslinjer i brödtexten (skärmversionerna, samma sats som tryck)

Varje brödtextsida i tre spalter: alla rader på samma raster (13,5 pt) och spalterna slutar på samma baslinje. En kortare sista spalt godtas bara på artikelns sista sida.

- sv s.  6: spalternas sista baslinje [277.5, 277.5, 277.5] mm från sidans överkant; raster ett – ok
- sv s.  7: spalternas sista baslinje [277.5, 277.5, 277.5] mm från sidans överkant; raster ett – ok
- sv s.  8: spalternas sista baslinje [255.6, 258.5, 163.2] mm från sidans överkant; raster FLERA: [3.7, 9.0] (artikelns sista sida: kortare sista spalt och källor på trekvartsrader godtas) – ok
- sv s. 10: spalternas sista baslinje [277.5, 277.5, 277.5] mm från sidans överkant; raster ett – ok
- sv s. 11: spalternas sista baslinje [239.4, 250.0, 182.3] mm från sidans överkant; raster FLERA: [3.7, 3.8, 6.7] (artikelns sista sida: kortare sista spalt och källor på trekvartsrader godtas) – ok
- sv s. 13: spalternas sista baslinje [277.5, 277.5, 277.5] mm från sidans överkant; raster ett – ok
- sv s. 14: spalternas sista baslinje [277.5, 277.5, 277.5] mm från sidans överkant; raster ett – ok
- sv s. 15: spalternas sista baslinje [268.0, 277.5, 277.5] mm från sidans överkant; raster ett – AVVIKER
- sv s. 16: spalternas sista baslinje [82.3, 48.9, None] mm från sidans överkant; raster ett (artikelns sista sida: kortare sista spalt och källor på trekvartsrader godtas) – ok
- en s.  6: spalternas sista baslinje [277.5, 277.5, 277.5] mm från sidans överkant; raster ett – ok
- en s.  7: spalternas sista baslinje [277.5, 277.5, 277.5] mm från sidans överkant; raster ett – ok
- en s.  8: spalternas sista baslinje [268.0, 263.3, 157.4] mm från sidans överkant; raster FLERA: [0.7, 3.7] (artikelns sista sida: kortare sista spalt och källor på trekvartsrader godtas) – ok
- en s. 10: spalternas sista baslinje [277.5, 277.5, 277.5] mm från sidans överkant; raster ett – ok
- en s. 11: spalternas sista baslinje [258.5, 258.5, 177.5] mm från sidans överkant; raster ett (artikelns sista sida: kortare sista spalt och källor på trekvartsrader godtas) – ok
- en s. 13: spalternas sista baslinje [277.5, 277.5, 277.5] mm från sidans överkant; raster ett – ok
- en s. 14: spalternas sista baslinje [277.5, 277.5, 277.5] mm från sidans överkant; raster ett – ok
- en s. 15: spalternas sista baslinje [277.5, 272.8, 277.5] mm från sidans överkant; raster ett – AVVIKER
- en s. 16: spalternas sista baslinje [149.0, 72.8, 25.1] mm från sidans överkant; raster ett (artikelns sista sida: kortare sista spalt och källor på trekvartsrader godtas) – ok
