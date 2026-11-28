# Felanalys av sannolikhetsmodellen (textmodel-19, appens inställning), 2026-11-28

Beskrivande, inget prov. Underlaget är maskeringsprovets fem veck (`app_f0–f4.json`), bara runstenar. Skript
`felanalys.py`, utfall `felanalys.json`.

## Läget
- **Underlaget:** 1 396 maskerade luckor.
- **Träffsäkerhet:** 68 % rätt ord.
- **Felen:** 448.
- **Säkra svar:** 342 svar är ≥ 95 %, och 15 av dem är fel (4,4 %).

## Var felen ligger
- **Rätt ord fanns inte bland förslagen: 254 fel (57 %).** Modellen nådde aldrig fram.
  - 133 av dem är namn.
  - Övriga är ovanliga ord, till exempel *bonda* och *boanda*, och längre luckor.
- **Rätt ord fanns bland förslagen men valdes inte: 169 fel (38 %).** Modellen nådde fram men rangordnade fel. Typiska
  fall:
  - *ræisti* mot *ræistu*: verbets numerus följer hur många som reste stenen;
  - *æftiR* mot *syniR*;
  - *satti* mot *retti*;
  - *haggva* mot *ræisa*.
  - Det är fel i ordföljd och kongruens, som ett ordpar (bigram) inte ser.
- **Rätt runor men ett "fel" ord: 24 (5 %).** Ofta en annan normalisering av samma ord, till exempel *sten* mot *stæin* och
  *sigbiarn* mot *sygbiorn*. Det är troligen ett mätfel i provet, inte ett modellfel.

## Efter slag och längd
- **Andel fel efter luckans längd:**
  - 1–2 runor: 19 %;
  - 3–4 runor: 36 %;
  - 5 eller fler: 48 %.
- **Hela ord mot delar av ord:** hela ord står för 64 % av felen. Inne i ord är korta luckor lätta (17 % fel).
- **Namn mot övriga ord:**
  - namn: 61 % fel, vilket är 38 % av alla fel;
  - övriga ord: 25 % fel.
- **Efter hur vanligt ordet är i korpusen:**
  - formelord (≥ 200 förekomster): 15 % fel;
  - vanliga ord: 50 %;
  - ovanliga ord: 64 %;
  - unika ord: 43 %.

## Slutsatser för nästa version
1. **Den största vinsten ligger i att nå fler ord och namn** (57 % av felen). Den är svår, eftersom det mest gäller unika
   namn och ovanliga ord. Böjning (tm24) var inte svaret.
2. **Den bästa vinsten per insats ligger i valet bland förslagen** (38 % av felen): kongruens och formelns struktur.
   Kryptologins motsvarighet är en "crib", alltså en känd sannolik klartext. Runstenens formel *X ok Y ræistu stæin þennsi
   æftiR Z, faður sinn* är en sådan. En modell över formelns platser kan se att flera resare ger *ræistu*, och att *æftiR*
   står efter stenordet.
3. **Mätfelen** (5 %) bör rättas i provets bedömning, så att samma ord i en annan normalisering räknas som rätt. Det ska
   göras öppet och påverkar alla modeller lika.
