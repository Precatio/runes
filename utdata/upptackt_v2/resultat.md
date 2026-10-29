# Upptäcktsmotorn v2: resultat (2026-10-29)

Plan: `analysplaner/2026-10-29-upptacktsmotorn-v2.md` (6cda482, SHA-256 kontrollerad före körning). Kod
`src/discovery_v2.py`, `r/discovery_v2.R` (del 1), `r/discovery_lokal.R` (del 2–3). Data: korpus 3f58e9339191761e,
1 739 svenska runstenar med minst fyra läsbara ord, 128 drag (v1:s 59 + 56 ordformer + 4 material + 5 ortnamns- och
gruppdrag). Siffror `upptackt.json` (del 1) och `lokala.json` (del 2–3). Frysta listor: `kandidater_A_till_B.json`
(7b1b0939…), `kandidater_B_till_A.json` (d41bb06c…), `lokala_kandidater.json` (fc0707cb…).

## Del 1: bredare parskanning – nästan tom
- A → B: 1 945 par, **5 kandidater**, 2 bekräftade: stenar efter fäder berättar sällan hur han dog (redan i v1) och
  nämner sällan en resa (0,44 i halva B). Mönster att pröva: dödsuppgift mot flera resare. Kryss-skiljetecken × *ræisa*
  kunde inte skattas i halva B (se avvikelser); far × i grupp höll inte.
- B → A (sekundärt): 1 953 par, 4 kandidater, 1 bekräftad: *ok* skrivet som monoftong följer med apostrofliknande
  skiljetecken (3,6 i halva A).
- **Läsning:** med landskap, tid och textlängd kontrollerade och de definitionsmässiga paren borttagna finns knappt
  några starka parvisa samband kvar att hitta i det här materialet – v1 tog det som fanns. Ord, material och
  ortnamnsmiljö tillförde inga par som höll.

## Del 2: lokala avvikelser – en bekräftad bygd, ett mönster att pröva
63 drag skannade i halva A (630 stenar), 10 kandidater; prövade i samma cirkel i halva B (600 stenar):
- **Bekräftad: formen *þennsa* (’denna’, ackusativ) kring södra Mälaren.** Cirkel 21 km runt Sö 190 (Ytterenhörna):
  halva A 11 mot 2,7 väntat (4,0×), halva B 7 mot 2,2 (3,1×, p 0,005, Holm 0,047). Formen går över landskapsgränsen
  (Sö 179, 183, 184, 187, 190, 283–305, 345, 350 och U 19, 25, 35, 37 på Mälaröarna) och används av många ristare
  (Balle, Åsgöt, Brune, Öpir, Torbjörn skald, Traen m.fl.) – en bygdens form snarare än en ristares vana.
  Ordmodulen (words.json) har den inte som landskapssignal; den syns först när man ser under landskapsnivån.
- **Mönster att pröva: *stæina* (plural, ’stenarna’) kring Täby–Vallentuna–Fresta** (7 km runt U 133): A 17 mot 3,9
  (4,4×), B 3 mot 0,7 (4,3×, p 0,03, Holm 0,27). Jarlabankes och grannfamiljernas bygd, där man reste flera stenar
  tillsammans; Fot dominerar (10 stenar). Hänger ihop med Familjens plats (grupper inom en generation).
- **Höll inte i halva B:** stungna runor och stungen e kring U 668, kryss och apostrof som skiljetecken, beröm och
  *góðan* kring U 742/U 763/U 716 (Balle, Livsten, Erik; *god* B 2,1×, p 0,058), ristarnamn kring Sö 266.

## Del 3: udda stenar (beskrivning)
De 25 mest överraskande är nästan alla långa, berättande texter: U 540, U 828, Vg 197, U 346, Sm 137, Ög 228, U 1087 …
Måttet belönar ovanliga ord, och långa texter har fler; listan pekar mest ut redan välkända stenar. Lite nytt.

## Bedömning
Det nya sättet att se – bygder under landskapsnivån – gav det enda nya: en lokal språkform (*þennsa*) som delar en
bygd över gränsen mellan Uppland och Södermanland. Parskanningen är uttömd på det här materialet.

## Avvikelser från planen
- Kodfel i steg 2 (från v1:s skript): när en modell inte kunde skattas gav raden fel kolumner och körningen stannade.
  Rättat; kandidatlistan blev byte för byte densamma (SHA-256 7b1b0939… före och efter).
- Kryss × *ræisa* kunde inte skattas i halva B (mgcv: ”inner loop 3; can't correct step size”); redovisas som ej
  prövad, räknas inte i Holm.
