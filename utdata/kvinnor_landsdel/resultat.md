# Resultat: varför stod kvinnorna i Svealand oftare på stenen? (2026-10-29)

Plan: `analysplaner/2026-10-29-kvinnorna-i-svealand.md` (d70b426, SHA-256 kontrollerad). Kod `analys.R`, siffror
`kvinnor_landsdel.json`. Korpus 3f58e9339191761e, 1 425 läsbara svenska stenar med minst en identifierad resare.
Andelarna är modellens (landsdel, tid och ristare konstanta); råa tal inom parentes.

Utgångsläge: en kvinna bland resarna på 31 % av stenarna i Svealand mot 17 % i Götaland (324/1 013 mot 61/370).

## Hypoteserna
- **A. Änkorna efter färderna – stöds inte.** Kvinna reser efter make: 9 mot 7 % (96/1 013 mot 23/370), oddskvot 0,82,
  Holm 0,96. Utan resestenar finns skillnaden kvar och blir något större: 32 mot 15 %, oddskvot 0,40, Holm < 0,001,
  båda halvorna (håller).
- **B. Seden att räkna upp familjen – stöds inte enligt regeln.** Med antalet resare konstant: 30 mot 19 %, oddskvot
  0,53, Holm 0,008 men bara i ena halvan (antydan). En femtedel (20 %) av skillnaden på logoddsskalan försvinner, under
  planens gräns på hälften.
- **C. Egen ställning – stöds inte.** En ensam kvinna reser stenen: 14 mot 11 % (137/1 013 mot 44/370), oddskvot 0,77,
  Holm 0,78.
- **D. Rollerna – här sitter skillnaden.**
  - Stenar efter **söner**: modern med på **51 % i Svealand mot 19 % i Götaland** (107/195 mot 13/70), oddskvot 0,23,
    Holm 0,015; halvorna p 0,058 och 0,031 (antydan). Håller i alla robusthetsprov (minst tio ord 0,28, stora landskap
    0,19, utan ristare 0,21).
  - Stenar efter **fäder**: dotter eller hustru med på 16 mot 7 % (66/415 mot 9/117), oddskvot 0,37, okorrigerat p
    0,02, Holm 0,12 (antydan).
  - Stenar efter **bröder**: 22 mot 13 %, oddskvot 0,53, p 0,16 (ingen skillnad påvisad).
- **E. Kristendomen – inget samband.** Kvinna bland resarna och kristen markör: oddskvot 1,27, p 0,16; ingen skillnad
  mellan landsdelarna (interaktion p 0,88).

## Läsning
Kvinnorna i Svealand var inte fler som änkor och inte fler som ensamma resare. Skillnaden är att modern stod med på
sonens sten – tillsammans med fadern och syskonen – och i mindre mån hustrun eller dottern på faderns. Det pekar mot
familjens sätt att minnas och mot arvsrätten (en mor kunde ärva efter sitt barn), inte mot färderna eller
kristnandet. Rollerna är antydningar enligt planens regel (starka i hela materialet och i robusthetsproven, men inte
signifikanta i båda halvorna var för sig).

## Avvikelser från planen
- Test C4 kördes först med en kolumn som inte fanns i `people.csv` (n = 0). Kolumnen räknades sedan fram exakt som
  planen definierar den (kvinnor bland resarna, inga män, alla resares kön bestämt) och testet kördes om; inget
  annat ändrades.
