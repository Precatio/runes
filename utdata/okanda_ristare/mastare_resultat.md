# Resultat: en och samma mästare? (2026-10-29)

Plan: `analysplaner/2026-10-29-en-och-samma-mastare.md` (9974476, SHA-256 kontrollerad före körning). Kod
`mastare_grupper.R`, `mastare_drag.py`, `mastare_modell.R`; siffror `mastare_del12.json`, `mastare_modell.json`.

## Del 1 – Tiden
Spannet mellan gruppens äldsta och yngsta stilgrupp (mittår) är 32,5 år för Konungsund (RAK 11, Fp 6), Kölaby (RAK 5,
Fp 4, Pr1 3) och Leksberg (RAK 3, Fp 2). Det är **förenligt** med en ristares livsgärning: lägre än för 86 %, 88 %
och 56 % av de kända ristarna med lika många daterade stenar (deras 90:e percentil 76–86 år). Vetlanda (1 sten med
stilgrupp) och Husaby (2) **går inte att bedöma**.

Beskrivning: grupperna omfattar en stor del av traktens samtida stenar – Konungsund 44 %, Leksberg 38 %, Kölaby 33 %
av stenarna inom 30 km från samma stilgrupper – mot 12 % i median (90:e percentil 34 %) för de kända ristarna i
Uppland och Södermanland. Där kandidaterna ligger var det alltså antingen en ristare som gjorde en stor del av bygdens
stenar, eller så är gruppen bygdens sed under perioden.

## Del 2 – Språkbruket (H5)
Positiv kontroll: kända ristares stenar delar ovanliga stavningar oftare än trakten (Fisher p 5·10⁻¹³; 9 av 19
ristare var för sig). **H5 håller:** kandidaterna delar ovanliga stavningar oftare än trakten, Fisher p 0,005.
Bärs av Kölaby (3,0 % av paren mot 0,0 %, p 0,0001: *eftR* för æftiR två gånger, *stein* för stæin två gånger) och
Konungsund (1,5 % mot 0,1 %, p 0,033: *rasti* tre gånger och *resti* två för ræisti, *tsin* för stæin två gånger).
Vetlanda, Leksberg och Husaby delar inga ovanliga stavningar.

## Del 3 – Mästarmodellen
912 kalibreringsgrupper ur 50 upprepningar av hållet-utanför-testet på kända ristare. Grundfrekvens: 62 % av grupperna
är helt en hand, 84 % till minst tre fjärdedelar. Validering (skattad på upprepning 1–25, prövad på 26–50): AUC 0,90
för båda utfallen (0,86 och 0,83 med bara handens drag), Brier 0,135 mot 0,242 och 0,084 mot 0,136 utan modell;
kalibreringen stämmer i alla tiondelar.

**Iakttagelse som ändrar läsningen av förra testet:** bland grupper som metoden bildar är gemensam bergart *inte* ett
tecken på en hand – blandade grupper delar bergart lika mycket eller mer (percentil 0,81 mot 0,64; koefficient −3,7).
Bergarten skiljer en ristares stenar från traktens, men inte en ren grupp från en blandad grupp i samma bygd. Ovanliga
stavningar skiljer (0,71 mot 0,55; koefficient +1,6); namn gör det inte.

| Grupp | En mästare (≥ 3/4 av stenarna) | Alla stenar en hand | Utanför kalibreringen |
|---|---|---|---|
| Vetlanda (Sm, 14) | 98 % (96–99) | 42 % (28–57) | – |
| Leksberg (Vg, 6) | 95 % (90–98) | 59 % (44–72) | spridningen (1,9 km, tätare än alla) |
| Husaby (Vg, 6) | 88 % (83–94) | 62 % (49–75) | – |
| Kölaby (Vg, 13) | 78 % (62–89) | 45 % (32–62) | spridningen, bergarten |
| Konungsund (Ög, 28) | 76 % (56–91) | 8 % (3–18) | bergarten |
(Grundfrekvens 84 % och 62 %; 95 %-intervall genom att dra upprepningar.)

## Läsning
- Sannolikheterna säger vad en grupp med de här dragen skulle betyda i Uppland och Södermanland, där metoden kan
  prövas. Om samma samband gäller i Östergötland, Småland och Västergötland går inte att pröva.
- **Konungsund** (28 stenar) är nästan säkert inte en enda hand (8 %), men troligen en mästare med några andra stenar
  (76 %, under grundfrekvensen). Gruppen är stor och omfattar 44 % av traktens samtida stenar – mer än nästan alla
  kända ristare. Den delar ovanliga stavningar (*rasti*, *tsin*).
- **Kölaby** har de starkaste oberoende tecknen: ovanliga stavningar (*eftR*, *stein*), bergart och namn – men ligger
  utspriddare än kalibreringsgrupperna, så siffran (78 %) är osäkrare än intervallet säger.
- **Vetlanda** får högst sannolikhet (98 %) av handens drag – stenarna är mycket lika varandra och ligger tätt – men
  har inget oberoende stöd: varken bergart, namn eller ovanliga stavningar, och nästan ingen datering.
- **Leksberg och Husaby** är små (6 stenar) och sannolikt en hand i den meningen, men utan oberoende stöd utom namnen
  (Leksberg).
- Rangordningen från förra testet (Konungsund starkast genom bergarten) håller inte: bergarten väger inte så.

## Avvikelser
- Ingen. (Spannet för kalibreringsgrupperna räknas på de stenar som har stilgrupp; saknas det används medianen, som
  planen säger.)
