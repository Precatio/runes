# Resultat: robusthetsstegen för ristningens riktning mot vägen (2026-10-31)

Plan: `analysplaner/2026-10-31-riktning-trappan.md` (b0ed2be, SHA-256 4da9710d…, låst före körningen). Kod
`trappa.py`, siffror `trappan.json`. Mått och omblandning som H2 i huvudplanen: medel-cos mot vägen, 9 999
omblandningar inom landskapet, ensidigt.

## Utfall – alla steg håller
- Huvudtestet (123 stenar): medel-cos 0,366 mot 0,013 väntat, 50 % inom 45°, p 0,0001.
- Halva A (71): 0,445 mot 0,037, p 0,0001. Halva B (52): 0,259 mot 0,051, p 0,016.
- Utan ett landskap i taget: utan U (62 stenar kvar, 50 %, bara riktningen krävs) 0,500 mot 0,055, p 0,0001; utan Sö
  (92, 75 %) 0,289 mot 0,015, p 0,0001; utan Ög (113, 92 %) 0,361 mot 0,015, p 0,0001.
- Socknen som enhet (76 socknar): 0,364 mot 0,016, p 0,0001.
- En sten per ristare (20 ristare; 93 stenar kvar): 0,385 mot 0,027, p 0,0001.
- Utan återresta stenar (14 av de 123 bort; ordlistan i planen träffar 29 av alla 219, mot 58 i kontrollen
  2026-10-29 med en annan ordlista): 0,426 mot 0,021, p 0,0001.
- Utan flyttade stenar enligt Runor 2020 (10 bort): 0,347 mot 0,006, p 0,0001.
- Dagens flyttregel (korpus e83202e01a5e6d27): ingen av de 123 räknas som flyttad; samma som huvudtestet.
- Bara vägar ur Kulturmiljöregistrets text (69): 0,489 mot 0,066, 62 % inom 45°, p 0,0001.
- Bara registrerade färdvägar och vägmärken inom 500 m (80): 0,163 mot 0,005, 28 % inom 45°, p 0,020.

Fyndet kvalar som **Fullt prövat fynd** i rapportmallen version 4.

## Avvikelser
Inga.
