# En öppen ristarmodell – resultat

Låst plan `analysplaner/2026-11-19-oppen-ristarmodell.md` (sha 091e6cba, commit 7ced6eb), körd 2026-11-23.
Skript `prov.py`, siffror `resultat.json`. Korpus 510ebfb3.

**O** behåller den slutna modellens (K0) ristare bara när två villkor båda gäller:
1. p_cal ≥ 0,5;
2. stenen liknar ristarens säkra stenar inom 30 km i textdragen (högsta överskottslikheten ≥ t = −0,010).

Annars blir svaret *okänd hand*.

## O1 (huvudprov, Runor 2020:s grupper med onämnda händer): **håller inte**
13 grupper med kontroller.

| Variant | Stämmer i gruppen (medel) | Kontrollen | Median | Bättre / sämre | p |
|---|---|---|---|---|---|
| O (båda villkoren) | 0,31 | 0,11 | 0,00 | 4 / 5 | 0,21 |
| Bara villkor 1 (p_cal) | 0,33 | 0,23 | −0,05 | 5 / 7 | 0,26 |
| Bara villkor 2 (textdragen) | 0,41 | 0,24 | 0,00 | 6 / 6 | 0,17 |

Det typiska felet: i ett par får den ena stenen en känd ristare och den andra okänd hand, till exempel U 800 Balle och
U 803 okänd, eller U 685 Fot och U 686 okänd. Att stenarna bedöms en och en räcker inte. Frågan måste ställas om gruppen.
U 1015 och U 1017–1024 får alla Öpir även i O, med p_cal 0,60–0,87 och överskott 0,34–0,57.

## O2 (priset, säkra stenar utanför vikten): **håller**
- K0 hade rätt ristare först för 366 av 497 säkra stenar (74 %).
- O behåller 281 av dem (77 %). Kravet var minst tre fjärdedelar.
- Av K0:s 131 felaktiga svar behåller O 29 som en (fel) känd ristare. Övriga 102 blir okänd hand.

## Beslut
O1 håller inte, så **K0 behålls i stenöversikten**, och O redovisas här.

## Beskrivande
- 923 stenar saknar en säker ristare. K0 ger 503 av dem ett förslag med p_cal ≥ 0,5. O behåller 267, och 656 blir okänd
  hand.
- 393 av de 923 saknar textdrag (färre än tre läsbara ord) och kan därför inte uppfylla villkor 2.
- Förslagen som faller på villkor 2: Öpir 114, Balle 63, Halvdan 22, Torbjörn 2 19, Fot 9, Åsmund 5 och övriga 4.
