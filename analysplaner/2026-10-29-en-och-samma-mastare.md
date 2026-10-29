# Analysplan: En och samma mästare? Tiden, språkbruket och sannolikheten för de möjliga okända ristarna

Låst 2026-10-29, innan något nedan har räknats. SHA-256 i `analysplaner/2026-10-29-en-och-samma-mastare.sha256`.
Kod i `utdata/okanda_ristare/` (`mastare_grupper.R`, `mastare_drag.py`, `mastare_modell.R`), resultat i
`utdata/okanda_ristare/mastare_resultat.md`. Fortsättning på `2026-10-29-okanda-ristare-oberoende.md` (3b74562).

## Grupperna
De fem stabila kandidaterna i korpus 3f58e9339191761e: Konungsund (Ög, 28), Vetlanda (Sm, 14), Kölaby (Vg, 13),
Leksberg (Vg, 6), Husaby (Vg, 6). Känt före låsningen: bergart (Konungsund, Kölaby) och namn (Kölaby, Leksberg) delas
oftare än i trakten; kända ristare delar både bergart och namn. Stilgrupperna per grupp (t.ex. Konungsund RAK 11,
Fp 6). Inga tidsspann, stavningar eller sannolikheter är räknade.

## Del 1 – Tiden: ryms gruppen i en livsgärning? (förenlighet, inget signifikanstest)
- **Spann:** största minus minsta mittår (stilgruppens från–till) bland gruppens stenar med stilgrupp.
- **Jämförelse:** samma spann för de kända ristarna (säkra stenar, alla landskap) med minst lika många stenar med
  stilgrupp som gruppen; gruppens percentil bland dem.
- **Utfall:** *förenligt* om spannet är högst de kända ristarnas 90:e percentil; annars *längre än de flesta
  ristares*. Grupper med färre än 4 stenar med stilgrupp: *går inte att bedöma*.
- **Beskrivning:** hur stor del av traktens (30 km) stenar från samma stilgrupper som tillhör gruppen, och samma andel
  för de kända ristarna i Uppland och Södermanland. En grupp som omfattar nästan alla samtida stenar i trakten går inte
  att skilja från traktens sed under perioden.

## Del 2 – Språkbruket: delar gruppen ovanliga stavningar? (H5, α = 0,05)
- **Stavningar:** kolumnen `pairs` (normaliserat ord = stavning; personnamn ingår inte). En stavning är **ovanlig**
  när ordet finns på minst 5 stenar i landskapet och stavningen på högst 10 % av dem.
- **S_ovanlig:** andelen par i gruppen som delar minst en ovanlig stavning.
- **Nollmodell, positiv kontroll och sammanslagning:** som i den förra planen (trakten 30 km, samma fördelning på
  stilgrupp, 9 999 dragningar, Fisher över de fem grupperna; kontrollen = de kända ristarna i Uppland och Södermanland
  med minst 5 stenar). Om kontrollen inte ger p < 0,05 kallas H5 *inte informativt*.
- **Förbehåll:** stavningar delar information med runbigrammen i likheten; H5 är därför ett svagare oberoende belägg
  än bergarten. Ovanliga stavningar per grupp listas (beskrivning).

## Del 3 – Mästarmodellen: sannolikheten att gruppen är en hand (skattning, inget test)
- **Kalibreringsgrupper:** samma förfarande som `r/anonymous.R` hållet-utanför (ristarna i tre delar, gränsen
  skattad på två, grupper bildade på den tredje), 50 upprepningar, seed 2026. Varje grupp har ett facit: renhet =
  andelen av den vanligaste ristaren.
- **Utfall:** *en hand* (renhet = 1) och *en mästare med enstaka avvikare* (renhet ≥ 0,75).
- **Förklarande variabler** (samma för kalibreringsgrupper och kandidater): log(antal stenar), medel-Gower inom gruppen
  med och utan de tidsberoende dragen, spridning (median km till mitten), tidsspann (år; saknas → medianen),
  percentilen för bergart, namn och ovanliga stavningar mot trakten (andel av 199 dragningar med lägre statistik;
  saknas uppgiften → 0,5).
- **Modell:** logistisk regression (glm). Huvudmodell med alla variabler; jämförelse med en modell bara med handens
  drag (n, Gower, spridning).
- **Validering:** skattad på upprepning 1–25, prövad på 26–50: AUC, Brier och kalibrering i tiondelar.
- **Skattning för kandidaterna:** modellen skattad på alla 50 upprepningarna; 95 %-intervall genom att dra
  upprepningar med återläggning (1 000 gånger). Grundfrekvensen (andelen kalibreringsgrupper som är en hand)
  redovisas bredvid.
- **Utanför kalibreringen:** ligger en kandidat utanför kalibreringsgruppernas 1:a–99:e percentil i någon variabel
  märks skattningen så.
- **Läsning:** sannolikheten gäller vad en grupp med de här egenskaperna betyder där metoden kan prövas (Uppland och
  Södermanland). Om samma samband gäller i Östergötland, Småland och Västergötland går inte att pröva; det sägs med
  siffran.

## Förbehåll
Stilgruppernas dateringar är grova (oftast 35–40 år). Spannet mäts på mittår och underskattar därför inte en
ristare. Kalibreringsgrupperna är beroende av varandra (samma stenar i olika upprepningar); intervallen bygger därför
på upprepningar, inte på grupper.
