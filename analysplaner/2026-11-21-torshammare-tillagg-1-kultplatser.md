# Tillägg 1 till analysplanen "Torshammare i svensk jord" – kultplatserna

Skrivet och låst 2026-11-21, innan något nedan har räknats. Huvudplanen är analysplaner/2026-11-20-torshammare.md (låst
14a659e, sha256 096f3d07…). Viktor 2026-11-21, efter resultatet: "kultplatser?"

## Känt före låsningen
- Huvudplanens resultat (8cb291a): 494 SHM-poster, 398 ringar (85 % i gravar, 98,5 % i Mälardalen), 96 hängen. T1:
  kvot 1,71 (1,11–2,63) per fördubbling av runstenarna per härad, bärs av ringarna och Mälardalen. Gotland och Skåne
  saknas nästan i SHM:s data.
- **Kultplatssocknarna** finns redan, kodade blint ur SOL i asatro-studien (analysplaner/2026-11-17-gudarna-pa-kartan
  tillägg 1, f7b339ef; tabellen `utdata/asatro/landskap_drag.csv`): 1 844 ISOF-socknar, 78 kultplatssocknar, varav
  30 med ett säkert namn. Där bekräftades att kultplatssocknarna oftare har gravfält och fler högar (plan 55a61e0d).
  Eftersom ringarna är gravfynd måste gravfälten och högarna kontrolleras här. Annars mäter testet bara gravarna.
- Tidigare prov med kultnamn (upptäcktsmotorn v2, "bön vid kultplatsen" 2026-10-29, runstenarna i kultplatssocknarna
  90e7af35) gällde runstenar, inte fynd. Inget av dem har prövat torshammare.
- Ingen riktning förutsägs.

## T2 – hittas torshammare oftare i kultplatssocknarna? (låst)
- **Enhet:** ISOF-socken i `landskap_drag.csv`, utanför Gotland, i landskap med minst tre kultplatssocknar, med en
  exponering ≥ 3 (SHM-poster med benämningen Kam eller Spänne och Tidsperiod som innehåller "Vikingatid", samma som i
  T1).
- **Koppling:** SHM:s socken till ISOF-socknen på namn + landskap ("Norrsunda socken" = "Norrsunda sn"; även
  genitivformen). Okopplade redovisas. Häradet hämtas som i T1.
- **Modell** (R, lme4): `glmer(hammare ~ kult + log1p(gravfält) + log1p(högar) + offset(log(exponering)) +
  (1 | landskap) + (1 | härad) + (1 | socken), family = poisson)`. Socknens slumpterm tar överspridningen, och häradets
  slumpterm tar hänsyn till att socknar i samma bygd inte är oberoende.
- **Rapporteras:** kvoten för kultplatssocken med 95 % intervall.
- **Ett samband sägs finnas** bara om hela intervallet ligger på samma sida om 1, och om det håller både utan Adelsö
  socken (Birka) och när bara socknar med ett *säkert* kultnamn räknas som kultplatssocknar.
- **Sekundärt, utan egen slutsats:** ringar och hängen var för sig, och modellen utan gravkontrollerna (för att visa
  hur mycket gravarna betyder).
- **Beskrivande:** antal hammarposter i kultplatssocknarna, per socken.

## Vad som skrivs
Ett samband skrivs som att torshammare oftare hittas i socknar med ett kultplatsnamn. Det skrivs inte som att de hittats
vid kultplatsen, eftersom socknen är stor och namnets plats inte är fyndplatsen. Faller testet står det i resultatet.
