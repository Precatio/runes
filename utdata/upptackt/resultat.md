# Upptäcktsmotorn v1: resultat (2026-10-28)

Plan: `analysplaner/2026-10-28-upptacktsmotorn.md` (SHA-256 kontrollerad före körningen). Kod: `src/discovery.py`,
`r/discovery.R`. Data: korpus 3f58e9339191761e, 1 739 svenska runstenar med minst fyra läsbara ord, 59 drag.
Siffror: `upptackt.json`; frysta kandidatlistor `kandidater_A_till_B.json` (SHA-256 bcc73aae…) och
`kandidater_B_till_A.json` (1dfaf3e1…), skrivna innan den andra halvan lästes.

## Utfall
- Halva A → B (huvud): 927 par prövade, 28 kandidater, **14 bekräftade** (Holm-p < 0,05 i halva B, ristaren som
  slumpeffekt), 6 mönster att pröva, 8 höll inte.
- Halva B → A (sekundärt): 941 par, 15 kandidater; **8 par bekräftade åt båda håll**.

## Bedömning av de 14 bekräftade
**Väntade strukturer i hur familjer reste stenar (8):** kvinnor reser efter makar (oddskvot 27 i halva B), en ensam
kvinna efter make, kvinnor mer sällan efter fäder, flera resare efter fäder (syskonskaror), färre resare efter söner,
kvinnor och ensamma kvinnor efter söner. Sanna men kända – de beskriver vem som var kvar att resa stenen. Version 2 bör
lägga resare × relation i samma familj.

**Mätartefakt (1):** o-runan sällan på stenar efter söner (oddskvot 0,08). Draget mäts bara i orden broður, bóndi,
móður, sun och kona; en sten efter en son har ordet *sun*, som skrivs med u-runa. Sambandet kommer av vilka ord som
finns, inte av en sed. Version 2 måste veta vilka drag som mäts i bestämda ord och inte para dem med relationerna.

**Värda en egen, låst plan (4):**
1. **Resestenar reses av färre personer** (msg_resa och cat_fard mot flera resare: oddskvot 0,33 i halva B). Hänger
   ihop med att de döda borta oftare var söner (människomodulen, test 5), men kan också säga något om vem som tog på sig
   minnet.
2. **Stenar efter fäder säger sällan hur eller var han dog** (oddskvot 0,36), och sällan att han dog borta (0,31) –
   fäderna dog hemma, och en död hemma var inget att berätta.
3. **Stenar efter söner säger oftare hur eller var han dog** (mönster att pröva, 2,4).
4. **Kors och apostrofliknande skiljetecken följs åt** (oddskvot 2,6 i halva B, med landskap, tid, textlängd och
   ristare konstanta). Ett hantverksdrag som inte är prövat förut; kan vara en verkstadstradition.

## Mönster att pröva (6)
þegn efter fäder (redan i människomodulen), dödsuppgift efter söner, resa och fard mot fäder, kvinnor mer sällan efter
syskon, dödsuppgift och död borta mot flera resare.

## Lärdomar till version 2
- Familjer: resare × relation; drag som mäts i bestämda ord (o_runa, ai, au, r för ʀ, preposition) mot innehåll och
  relation.
- Motorn hittade mest det vi delvis visste, men också två hantverks- och berättardrag (1, 4) som ingen fråga hade
  ställts om. Det är det den är till för.
- Nästa delar enligt förslaget: residualkartan (var modellerna har fel), kombinationer (A och B ger C) och udda stenar.
