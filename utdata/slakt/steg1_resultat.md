# Resultat: släktnätverket, steg 1 (2026-11-01)

Plan: `analysplaner/2026-11-01-slaktnatverket-steg1.md` (låst före körningen, SHA-256 403fa352…). Kod `steg1.py`, siffror `steg1.json`. Material: 2320 svenska vikingatida runstenar. Kontroll: Williams 1990 (`williams1990_bilaga.json`), Jarlabankes stenar, Rundatas parstenar och anmärkningar.

## Utfall: M1 håller inte – appen behåller M0
M1 klarar fyra av planens fem villkor men inte Jarlabanke: bara 1 av 10 par blir säkra.
- W1, täckning mot Williams: M0 34 av 202 stenar (16,8 %), M1 69 av 202 (34,2 %). Minst dubbelt och minst 25 %: ja.
- W2, träffsäkerhet mot Williams: M0 19 av 21 länkar (90,5 %), M1 42 av 45 (93,3 %). Inte mer än tio enheter sämre: ja.
- J, Jarlabanke: M0 0 av 10, M1 1 av 10. Uppfyllt: nej.
- K, motsägelser bland länkarna under gränsen: M0 2 av 25 (8,0 %), M1 0 av 47 (0,0 %). Högst 5 %: ja.
- Säkra länkar: M0 23, M1 47 (av 383 kandidater). Parstenar: M0 2 och M1 6 av 14; Rundatas anmärkningar: M0 5 och M1 9 av 73.

I klartext: den nya modellen hittar dubbelt så många av de släktsamband som runologerna redan har pekat ut, utan att bli mindre träffsäker och utan en enda motsägelse – men den missar Jarlabankes egna stenar, och då säger planen nej.

## Varför Jarlabanke faller (beskrivning, ändrar inget)
- Alla tio par delar Jarlabanki och gårdsnamnet Täby (styrka 11,1). U 127 står 10–14 km från de fyra andra; i bandet över 10 km ger nollmodellen i genomsnitt 297 länkar mot 307 i data, så en äkta men avlägsen länk kan inte nå q under 0,1 (q 0,38).
- De sex paren på 3,6–6,8 km får q 0,127 med nollmodellen inom häradet men 0,017 med nollmodellen inom landskapet: sju av Jarlabankes nio stenar står i samma härad (Danderyds skeppslag), så när namnen blandas inom häradet återskapar slumpen Jarlabankepar. Häradsnollmodellen räknar en stor släkts eget avtryck i bygden som lokal namnsed – den är för sträng just där släkterna syns som tydligast.

## Per avståndsband (M1)
- Band A: 38 kandidater, i genomsnitt 4,1 i nollmodellen, 38 säkra.
- Band B: 38 kandidater, i genomsnitt 23,7 i nollmodellen, 7 säkra.
- Band C: 307 kandidater, i genomsnitt 297,4 i nollmodellen, 2 säkra.

## Beskrivning (M1, även om den inte införs)
- 38 släktgrupper med 81 stenar, 3 med minst tre stenar; 94 personer står på minst två stenar; den längsta kedjan förälder–barn över stenarna är 3 generationer.
- Grupper per landskap: U 28, Sö 4, G 2, Ög 1, Hs 1, Sm 1, Vg 1.

## Känslighet
- band_1_5: 44 säkra, W1 30,7 %, W2 92,9 %, Jarlabanke 3 av 10, motsägelser 2,2 %.
- band_3_15: 50 säkra, W1 35,1 %, W2 91,7 %, Jarlabanke 1 av 10, motsägelser 0,0 %.
- common_40: 46 säkra, W1 34,2 %, W2 93,2 %, Jarlabanke 1 av 10, motsägelser 0,0 %.
- common_80: 49 säkra, W1 36,1 %, W2 93,6 %, Jarlabanke 1 av 10, motsägelser 0,0 %.
- null_province_banded: 59 säkra, W1 39,6 %, W2 94,7 %, Jarlabanke 6 av 10, motsägelser 3,3 %.
- without_moved: 19 säkra, W1 36,7 %, W2 94,7 %, Jarlabanke 1 av 10, motsägelser 0,0 %.
- Utforskande M1b (ett enda ovanligt namn inom 2 km): 46 säkra, W1 34,2 %, W2 93,2 %. Avgör ingenting.

## Avvikelser från planen
- Utan flyttade stenar: också stenar som korpusen anger som försvunna (lost = 1) togs bort, eftersom deras plats inte är känd; planen nämnde bara moved = 0.
- I övrigt inga.

## Vad det betyder för nästa steg
Den avståndsdelade prövningen är rätt idé – den fördubblar täckningen utan att tappa träffsäkerhet – men nollmodellen inom häradet straffar just de stora släkterna. Känsligheten pekar på nollmodellen inom landskapet med avståndsband (59 säkra, W1 39,6 %). Det valet är gjort efter att ha sett data och måste därför prövas på nytt material i en ny låst plan, inte införas här.
