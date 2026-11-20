# Tillägg 1 till analysplan 2026-11-20-hundra-ar-III (låst 7e288d5c, c5a33b6)

Skrivet och låst 2026-11-20, efter M1–M3, M5 och M6 men före M4 (R har inte körts).

## Vad som upptäcktes
Kvalitetsgrinden gav 100 riktiga av 100 (seed 20261121). Men 193 av de 2 321 runstenarna har ett signum som mönstret
inte kan hitta i löptext alls (Öl Köping 12, Öl ATA4684/43A, U ATA…, Ög ATA…, Bo …): 101 på Öland, 50 i Uppland, 18 i
Östergötland, 14 i Södermanland och 10 andra. Ingen av dem räknas som nämnd, vare sig i tidskrifterna eller i
avhandlingarna (litteraturregistret använder samma mönster). Att de "aldrig nämns" är alltså ett mätfel, inget fynd.
Öland ser därför mycket mindre uppmärksammat ut i de första siffrorna än det kanske är: 103 av Ölands 154 runstenar
ligger utanför huvudserien, de flesta fragment från Köpings kyrka (median 7 runor).

## Ändringen
- En sten räknas som **mätbar** när mönstret hittar dess eget signum och ger tillbaka samma sten
  (literature.signum_pattern + fold_signum). M2, M3, M4 och M5 räknas bara på de mätbara stenarna; de 193 redovisas för
  sig, per landskap, som "kan inte räknas".
- M1 påverkas inte (omnämnandena är desamma) men landskapens andel av stenarna räknas på de mätbara.
- M4 körs som planerat, men på de mätbara stenarna. Inget annat ändras: samma modell, samma referens, samma regel för
  vad som sägs.
- De första siffrorna (alla 2 321) behålls i resultat.md som de räknades, med denna förklaring.
