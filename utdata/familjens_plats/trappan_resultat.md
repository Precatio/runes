# Resultat: robusthetstrappan för familjens plats (2026-10-31)

Plan: `analysplaner/2026-10-31-familjens-plats-trappan.md` (låst och committad före körning, SHA-256 ec4a17c5…). Kod `trappa.R` (test A) och
`utdata/avstand/grannar_trappa.py` (test B), siffror `trappan.json` och `utdata/avstand/grannar_trappa.json`. Samma data som de
ursprungliga testen (korpus 3f58e9339191761e).

## Test A: gravfält inom 500 m, grupp mot ensam (657 stenar, 185 i grupp, 472 ensamma) – håller i alla steg
- Rått: OR 3,59 [2,37–5,43], p 1.4e-09, n 657 – håller
- Justerat (planens modell): OR 2,38 [1,50–3,78], p 0.00023, n 657 – håller
- Ristaren som slumpeffekt: OR 2,49 [1,53–4,06], p 0.00026, n 657, 324 grupper – håller
- Socknen som slumpeffekt: OR 2,45 [1,49–4,02], p 0.00042, n 657, 331 grupper – håller
- Platsen som yta: OR 2,45 [1,51–3,98], p 0.00028, n 657 – håller
- Halva A: OR 2,27 [1,22–4,23], p 0.0094, n 334 – håller
- Halva B: OR 2,53 [1,24–5,16], p 0.011, n 323 – håller
- Utan ett landskap i taget (sämst): OR 1,44 [0,67–3,12], p 0.35, n 302, utan U, 46 % kvar – håller
- Utan flyttade stenar enligt Runor 2020: OR 2,64 [1,56–4,50], p 0.00033, n 540 – håller
- Utan vart landskap: Ög 2,18 (p 0.0011, 93 % kvar); Sm 2,70 (p 4.8e-05, 92 % kvar); Sö 2,53 (p 0.00032, 82 % kvar); U 1,44 (p 0.35, 46 % kvar); Vg 2,63 (p 6.2e-05, 93 % kvar)

Förbehåll: utan Uppland är oddskvoten 1,44 och inte signifikant (46 % av stenarna kvar; regeln kräver där bara riktningen). Skillnaden bärs i hög grad av Uppland.

## Test B: samma personnamn, nära par (25–500 m) mot jämförelsepar (2–10 km) – håller i alla steg
- Huvudmåttet: kvot 7,89 (74 nära par, 4983 jämförelsepar), p 0.0001 – håller
- Halva A: kvot 9,34 (34 nära par, 1542 jämförelsepar), p 0.0024 – håller
- Halva B: kvot 5,83 (40 nära par, 1322 jämförelsepar), p 0.0045 – håller
- Bara Uppland: kvot 8,19 (63 nära par, 4342 jämförelsepar), p 0.0002 – håller (andel av paren 85 %)
- Bara Södermanland: kvot 5,83 (11 nära par, 641 jämförelsepar), p 0.094 – håller (andel av paren 15 %)
- Utan par med samma säkra ristare: kvot 7,11 (61 nära par, 4578 jämförelsepar), p 0.0003 – håller
- Utan flyttade stenar enligt Runor 2020: kvot 9,57 (44 nära par, 3212 jämförelsepar), p 0.0003 – håller

Södermanland ensamt är inte signifikant (11 nära par, 15 % av paren); regeln kräver där bara riktningen.

## Avvikelser från planen
Inga. Halvorna i test B är projektets fasta halvor (`src/question.halves`) över hela korpusen; steg 2 tar par där båda stenarna ligger i halvan.
