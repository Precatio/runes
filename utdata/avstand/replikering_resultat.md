# Resultat: replikering av avståndet i Götaland (2026-10-31)

Plan: `analysplaner/2026-10-31-avstand-replikering.md` (låst och committad före körning, SHA-256 e1fb9abc…). Kod `replikering.R`,
siffror `replikering.json`. Metoden exakt som steg 1 med tillägget (10 km, golv 5 %); korpus 3f58e9339191761e.

## Utfall: replikerat
- Huvudtest, Östergötland + Västergötland + Småland som ett mönster (167 stenar på plats, 158 platser): p 0,004, klumpat.
- Halvorna: väst p 0,023 (klumpat, 79 platser), öst p 0,011 (klumpat, 79 platser).
- Beskrivande, varje landskap för sig: Ög p 0,199 klumpat (51 platser); Vg p 0,003 klumpat (55 platser); Sm p 0,023 klumpat (52 platser).
- Närmaste grannplats (median): 4071 m; var tionde plats har en granne inom 840 m.

## Läsning
Den rättade metoden, som först användes i Uppland och Södermanland efter att planens bandbredd visat sig ge en trasig skattning, ger samma utslag oförändrad på stenar som inte ingått i någon avståndsanalys: runstenarna står närmare varandra än slumpen ger på 100–1 000 m också i Götaland.

## Avvikelser från planen
Inga. En provkörning med 19 simuleringar gjordes för att hitta kodfel (minsta möjliga p 0,05); den styrde inget val.
