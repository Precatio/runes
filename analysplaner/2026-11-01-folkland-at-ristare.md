# Tilläggsplan: prepositionen *at* vid gränsen Tiundaland–Attundaland, med ristarna

Skriven och låst 2026-11-01, innan något av proven nedan har räknats. Uppföljning till
`analysplaner/2026-11-01-upplands-folkland.md` (resultat 5d26b16): *at* (i stället för *æftiR*) 38 mot 10 % inom 10 km
från gränsen. Viktor 2026-11-01: "ja" (ristarprovet och litteraturkontrollen).

## Känt före låsningen
Resultatet ovan. Litteratur: Peterson, L. 1996, *Aft/æft, at och æftir på de nordiska runstenarna – regional variation
eller vad?* (Mål i sikte, s. 239–252) – funnen men inte läst; Palm 1992 och Holt 2017 behandlar regional variation.
Inga ristarsiffror för *at* är räknade.

## Data
Stenarna i Tiundaland och Attundaland i `utdata/folkland/folkland.py` (samma rader), med *prep_at* känd. Ristare ur
`drag.csv` (kolumnen carver, Rundatas säkra attribuering); stenar utan ristare får en egen nivå per socken (som i v2/v3).
**Gränszonen** = stenar vars socken har en socken i det andra folklandet inom 10 km (som steg 3).

## Prov
1. **Med ristaren som slumpeffekt** (lme4 `glmer`, binomial): `prep_at ~ sida + tidsskikt + (1 | ristare)`, i
   gränszonen och i båda folklanden. Gränsen **håller med ristarna** om sidans effekt har p < 0,05 i gränszonen i samma
   riktning som tidigare (Tiundaland högre).
2. **Samma ristare på båda sidor:** namngivna ristare med minst två stenar med *prep_at* känd på var sida. För var och en
   andelen *at* på var sida; teckentest över ristarna (Tiundaland högre). Beskrivande om färre än fem ristare.
3. **Hur många ristare arbetade på båda sidor:** andelen namngivna ristares stenar som hör till ristare med stenar i båda
   folklanden. Beskrivande.

## Tolkning (bestämd nu)
- Håller 1 och skriver samma ristare olika på var sida (2): gränsen är **beställarnas eller bygdens**, inte verkstädernas.
- Håller 1 men ristarna håller sig på sin sida och skriver lika överallt: gränsen syns, men den kan vara **verkstädernas
  områden**.
- Håller inte 1: skillnaden förklaras av **vilka ristare** som arbetade var.

## Redovisning
`utdata/folkland/at_ristare.R`, `at_ristare.json`, `at_ristare_resultat.md`.
