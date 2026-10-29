# Analysplan: Vad har grannstenarna gemensamt?

Låst 2026-10-29, innan något nedan har räknats. SHA-256 i `analysplaner/2026-10-29-grannstenarna.sha256`.
Kod `utdata/avstand/grannar.py`, resultat `utdata/avstand/grannar_resultat.md`.

## Bakgrund
Avståndsanalysen (analysplaner/2026-10-28-avstand-mellan-stenar.md med tillägg) visade att runstenar som står kvar på
sin plats i Uppland och Södermanland står närmare varandra än slumpen ger på 100–1 000 m. Frågan nu är varför: står
grannstenar efter samma familj, av samma ristare, med samma budskap eller från samma tid?

## Material
Svenska runstenar på sin plats (`moved = 0`, `lost = 0`) med koordinater i Uppland och Södermanland, korpus
3f58e9339191761e. Avstånd i SWEREF 99 TM (meter, geodetiskt via pyproj).
- **Nära par:** två stenar 25–500 m isär (under 25 m räknas de som ett monument och ingår inte).
- **Jämförelsepar:** två stenar 2–10 km isär i samma landskap.

## Egenskaper per par (prövas bara på par där båda stenarnas uppgift är känd)
1. **Samma ristare:** båda har säker ristare (`carver`), och det är samma.
2. **Samma namn:** stenarna delar minst ett personnamn bland resare och döda (entitetsmodellens namnnyckel, utan
   ristare och utan de 20 vanligaste namnen i korpusen, som delas av en slump).
3. **Samma stilgrupp:** båda är stildaterade, och stilgruppen är densamma.
4. **Båda om bro eller väg** (`cat_bro_vag`).
5. **Båda om resa** (`cat_fard` eller `msg_resa`).
6. **Båda kristna** (`cat_kristen`).

## Test
Statistik för varje egenskap: kvoten mellan andelen nära par med egenskapen och andelen jämförelsepar med den.
**Permutationstest:** stenarnas egenskaper (alla på en gång, stenvis) blandas om slumpvis mellan stenarna inom samma
landskap, med platserna fasta; 9 999 omblandningar; p = andelen omblandningar med en kvot minst lika stor som den
observerade (ensidigt: grannar mer lika). Holm över de sex egenskaperna, α = 0,05. Uppland och Södermanland räknas
tillsammans med omblandning inom varje landskap.

## Tolkningsregler
- **Håller:** Holm-p < 0,05 och kvoten över 1 i både Uppland och Södermanland var för sig.
- **Antydan:** Holm-p < 0,05 men bara i det ena landskapet, eller okorrigerat p < 0,05.
- Läsningen: samma namn → familjens plats; samma ristare → ristarens eller verkstadens område på nära håll; bro eller
  resa → vägens eller minnets plats; samma stilgrupp → stenar rest under samma tid (en generation), olika stilgrupper
  på samma plats → en plats som brukades över generationer.

## Robusthet (redovisas)
Nära par 25–300 m; jämförelsepar 1–5 km; samma namn utan att ta bort vanliga namn.

## Förbehåll
Bara en tredjedel av stenarna står kvar på sin plats. Säker ristare finns för en minoritet. Ett delat namn kan vara en
annan person med samma namn; jämförelsen nära mot fjärran tar hand om slumpen men inte om att vissa namn är lokala.
