# Analysplan: en öppen ristarmodell – får "ingen känd ristare" bli ett svar?

Skriven och låst 2026-11-19, innan något av proven nedan har räknats. Viktor 2026-11-19: "kan vi förbättra våra
modeller vi har?" → förslaget att börja med en öppen ristarmodell → "ja".

## Känt före låsningen
- **Den slutna modellen (K0)** (korpus 510ebfb3, attribution.json): rätt ristare först för 71 % av de signerade stenarna
  när socknen hålls utanför. Mot runologernas grupper i Runor 2020 ("samma som gjort X", plan 32257107) ger den samma
  ristare i 0,50 av paren mot 0,44 för grannstenar på samma avstånd: H1 höll inte. U 1015 och U 1017–1024 får alla Öpir.
- **Textdragen** (plan add8ff31): stenar i runologernas grupper är mer lika än grannarna i 16 av 18 grupper.
- **Parregeln** (plan 9e0037d5, utdata/nya_hander): överskottslikhet (likheten i textdragen minus medellikheten med
  stenar på samma avstånd), länkgränsen t = −0,010, vald på de namngivna ristarna med Youdens J utan Runor. Den länkar 89
  % av runologernas par mot 33 % av grannparen. Att gruppera ihop länkarna misslyckades: de kedjar ihop sig.
- Inget av proven nedan är räknat.

## Den öppna modellen (O)
För en sten s ger K0 en ristare k och en kalibrerad sannolikhet p (p_cal). O behåller k bara om **båda** villkoren gäller:
1. p ≥ 0,5. Det är appens befintliga gräns för "förslag bland kända", prövad i blindprovet.
2. Stenen liknar ristaren också i textdragen: den högsta överskottslikheten mellan s och någon av k:s stenar med säker
   ristare (utom s själv) inom 30 km är minst t = −0,010.
Annars blir svaret **okänd hand**. Båda gränserna är bestämda före Runor och ändras inte. Saknar k säkra stenar inom 30
km från s räknas villkor 2 som inte uppfyllt.

## Prov
**O1, huvudprovet (externt facit: Runor 2020).** Samma grupper, samma regler för grupperna och samma grannkontroller på
samma avstånd som i plan 32257107 (`utdata/samma_hand/prov.py`, samma dragning och samma frö). Ett par i en grupp
**stämmer** när båda stenarna får samma kända ristare, eller när båda får okänd hand och paret länkas av parregeln
(överskott ≥ t). Kontrollparen bedöms på samma sätt. Teststorhet: för varje grupp andelen par som stämmer minus
kontrollernas andel; ensidigt Wilcoxon-test över grupperna med onämnda händer. **Håller** när p < 0,05.

**O2, priset: hur många rätta svar förlorar O?** Stenar med säker ristare, med K0:s förslag utanför vikten (out of fold,
attribution_oof.csv) och överskottslikheten räknad utan stenen själv. Bland de stenar där K0 hade rätt ristare först: hur
stor andel behåller O som rätt ristare (inte okänd hand)? **Villkor:** minst tre fjärdedelar.

**Beslutsregel:** O ersätter K0:s förslag i stenöversikten, med "okänd hand" som eget svar, om O1 håller och villkoret
i O2 är uppfyllt. Annars behålls K0, och O redovisas.

## Beskrivande (utan prov)
- Hur många av stenarna utan ristare som får okänd hand, totalt och per landskap; vilka kända ristare som förlorar flest.
- U 1015 och U 1017–1024: vad O ger dem.
- O1 med bara villkor 1 och med bara villkor 2, för att se vad varje villkor gör.

## Vad som inte skrivs
"Okänd hand" betyder att ingen av de kända ristarna passar på båda sätten, inte att en ny ristare är funnen. Runor 2020:s
grupper är runologernas bedömningar, inte säkra fakta. Att O stämmer bättre med dem är ett tecken, inte ett bevis.

## Utdata
`utdata/oppen_modell/prov.py` → `utdata/oppen_modell/resultat.json` och `resultat.md`.
