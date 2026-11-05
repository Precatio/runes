# *at* vid gränsen Tiundaland–Attundaland, med ristarna – resultat

Låst tilläggsplan `analysplaner/2026-11-01-folkland-at-ristare.md` (sha c4c4f5ba). Kört 2026-11-01 med
`utdata/folkland/at_rader.py` och `at_ristare.R` (lme4); tal i `at_ristare.json`.

## 1. Gränsen håller med ristarna som slumpeffekt
497 stenar i Tiundaland och Attundaland med prepositionen avgjord, 109 i gränszonen (socken med en socken i det andra
folklandet inom 10 km), 266 med namngiven ristare.
- **Gränszonen:** oddskvot 5,7 för *at* på Tiundalands sida (p 0,0016 ensidigt), med ristare och tid konstanta.
- **Båda folklanden:** oddskvot 3,5 (p < 0,0001).
Gränsen håller alltså också när vi räknar med vilken ristare som högg stenen.

## 2. Samma ristare skriver olika på var sida
Tre namngivna ristare har minst två stenar på var sida, och alla tre skriver *at* oftare i Tiundaland:
- **Öpir:** 21 av 39 stenar i Tiundaland (54 %) mot 4 av 22 i Attundaland (18 %) – nästan alla från samma tid, efter 1070.
- **Fot:** 5 av 14 (36 %) mot 3 av 22 (14 %).
- **Åsmund:** 1 av 15 (7 %) mot 0 av 12.
Teckentest 3 mot 0 (p 0,125; för få ristare för ett prov, enligt planen beskrivande).

## 3. Ristarna rörde sig över gränsen
Fem av 43 namngivna ristare har stenar i båda folklanden, och deras stenar är 162 av 266 namngivna – de flesta stenarna
med känd ristare kommer från ristare som arbetade på båda sidor.

## Tolkning enligt planen
Gränsen håller med ristarna, och samma ristare skriver olika på var sida: **gränsen är beställarnas eller bygdens, inte
verkstädernas.** Öpir, den mest produktiva ristaren, skrev *at* på mer än hälften av sina stenar i Tiundaland och på
knappt en femtedel i Attundaland under samma tid. Det tyder på att formeln var bygdens – vad familjerna ville ha skrivet
– och att bygden följde folklandsgränsen.

## Svagheter
- Bara tre ristare med stenar på båda sidor; jämförelsen inom ristare är beskrivande.
- Folklandsgränsen är ritad efter 1900-talets härader; häradernas sammansättning är delvis osäker.
- Litteratur: Peterson 1996 (*Aft/æft, at och æftir på de nordiska runstenarna – regional variation eller vad?*) behandlar
  just denna variation och är inte läst. Om hon redan har sett gränsen måste det sägas.
- Robusthetstrappan (utan ett landskap i taget, socken som slumpeffekt) är inte körd för gränsprovet.

## Omkörning 2026-11-05 med rättad landindelning (deklarerad avvikelse)
Samma skript och regler på at_rader.csv från den rättade indelningen (se resultat.md): 517 stenar (v1 497), 108 i gränszonen
(v1 109; U 899 föll ut, de 20 nya stenarna – 17 från Färingö tingslag, U 77, U 419, U 871 – ligger inte i zonen).
1. Gränszonen med ristaren som slumpeffekt: OR 5,9, p 0,0014 ensidigt (v1 5,7, p 0,0016) – **håller**. Båda folklanden:
   OR 3,1, p 0,0002 (v1 3,5, p < 0,0001).
2. Samma ristare på båda sidor: fortfarande 3 mot 0 (Öpir 21/39 mot 4/23, Fot 5/14 mot 3/22, Åsmund 1/16 mot 0/12;
   teckentest p 0,125, beskrivande).
3. 6 av 43 namngivna ristare (v1 5) har stenar på båda sidor; de står för 168 av 274 namngivna stenar (v1 162 av 266).
**Tolkning enligt planen oförändrad:** gränsen är beställarnas eller bygdens, inte verkstädernas. v1 i at_ristare_v1.json.
