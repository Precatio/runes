# Attribueringsmodellen prövad mot de signerade stenarna (2026-11-04)

Låst plan `analysplaner/2026-11-04-attribuering-provad.md` (daba3bc). Kod `r/attribution_audit.R`. Korpus 7b9061c9.
497 träningsstenar, 18 ristare, 117 signerade (16 ristare har minst en). Korsvalidering grupperad per socken, 5 × 3.

## Svaren
1. **Rätt ristare först på en signerad sten: 71,2 %** (95 % 63,9–78,6), bland tre främsta 85,5 % (79,4–91,5),
   log-förlust 1,37. Mycket ojämnt: Öpir 96 % (38 st.), Balle 93 % (20), Åsmund 73 % (16), Visäte 61 %, Fot,
   Livsten 56 % (6 vardera); Likbjörn, Tidkume, Torbjörn skald, Tore, Vidbjörn 0 % (1–4 st.). Medel över ristarna
   (varje ristare lika tung): 43 %.
2. **Attribueringarna återskapas inte mer än ristarna:** attribuerade stenar 67,7 % (63,0–72,6) mot signerade 71,2 %;
   inom ristare ingen skillnad (glmer, koefficient för signerad −0,09, se 0,45, p 0,85).
3. **Attribueringarna som träningsdata:** på 92 signerade stenar av de sex ristarna med minst fem signerade
   (Åsmund, Balle, Fot, Livsten, Öpir, Visäte): A (signerade + attribuerade) 83,7 %, B (bara signerade) 78,6 %,
   skillnad +5,1 (−0,7 till +11,2) → **ingen påvisad skillnad**; tecknet talar för att de hjälper något.
4. **Slår geografin:** bara geografi 38,2 % (29,2–46,8), närmaste stens ristare 32,5 %; modellen +33,0
   procentenheter (23,1–42,8) över den bästa.
5. **Kalibrering:** ECE 0,31 på signerade stenar – modellen är för försiktig. Potens a = 1,7 (vald på sockenhalva 1)
   ger på halva 2 (50 signerade): ECE 0,337 → 0,144, log-förlust 1,17 → 0,92.
   **”Någon annan”** med grupperade sannolikheter: tröskel 0,33; 35 % av kända signerade stenar flaggas, 75 % av
   utelämnade ristares stenar; bland de signerade som inte flaggas är 89,5 % rätt (65 % av stenarna). Den nuvarande
   tröskeln 0,35 flaggade 42 % av de kända.

## Vad det betyder
- Modellen känner de stora ristarna väl (Öpir, Balle, Åsmund) och de små nästan inte alls.
- Den är inte bara ett eko av forskarnas attribueringar, och den gör mycket mer än geografin.
- Sannolikheterna i appen är för låga och bör omkalibreras (a ≈ 1,7) innan de visas som procent.
- Nästa modell bör ge de små ristarna mer underlag: ornamentik, runformer, och ristarprofiler som den för Balle.
