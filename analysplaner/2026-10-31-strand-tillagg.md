# Tillägg till analysplanen ”runstenarna, dåtidens strand och gravfälten”

Skrivet och låst 2026-10-31, innan statistiksteget (`utdata/strand/03_statistik.R`) har körts. Planen
`analysplaner/2026-10-23-strand-och-gravfalt.md` gäller oförändrad; tillägget lägger till ett känslighetssteg och
redovisar läget. Viktor 2026-10-31: ”Gör den prövningen.”

## Läget
- Steg 1 (avstånd, `01_avstand.R`) och steg 1b (`01b_marginal.R`) är körda för alla sex landskap 2026-10-23.
- Steg 2 (R6, oberoende höjdmodell, `02_r6.R`) är kört för U, Sö, Ög och Öl; Sm och Vg återstår.
- Steg 3 (statistiken) och steg 4 (figurerna) har inte körts. I `/Volumes/2TB/cache/strand/run.log` finns en tidig
  provkörning samma dag kl. 17.32 med en äldre version av skriptet; den sparade inga resultat i någon fil som finns kvar.
- Körningen sker när den pågående körningen av textmodellen är klar (ett tungt jobb i taget; steg 2 tar omkring 2,8 GB).

## Varför ett tillägg
Planen bygger på korpus `d6cffd1578418f74` och dess regel för flyttade stenar. Regeln rättades 2026-10-27 (commit
07d2ec0: placeringen läses ur Rundatas fält), och projektets robusthetssteg utesluter sedan 2026-10-29 också stenar som
Riksantikvarieämbetets Runor (2020) anger som inte på ursprunglig plats.

## Känslighetssteget T1
H1 (vatten år 1050) och H3 (gravfält) prövas också på de stenar som står kvar enligt **alla tre**: den låsta korpusen,
dagens korpus `e83202e01a5e6d27` (moved = 0, lost = 0) och Runor 2020 (inte `original = false`). Slumppunkterna är
desamma (de som hör till de kvarvarande stenarnas landskap); inga avstånd räknas om. Stenar som bara dagens korpus
räknar som kvar ingår inte, eftersom deras avstånd inte är räknade. Antalet stenar som faller bort redovisas per
landskap. T1 *håller* när p < 0,05 åt samma håll som huvudtestet.

## Vad som avgör
Planens regler gäller. För en forskningsrapport (mallen version 2) krävs dessutom att H1 eller H3 håller i båda
halvorna; T1 redovisas som ett steg i den uppräkning av känslighetsanalyser som rapporten ska ha.

## Redovisning
`utdata/strand/resultat.md` med avsnittet *Avvikelser från planen* (planens krav) och T1 som eget avsnitt.
