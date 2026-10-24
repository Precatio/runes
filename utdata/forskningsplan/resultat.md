# Resultat: de öppna 3D-skanningarna, fyra studier

Enligt den låsta planen `analysplaner/2026-10-24-skanningarna.md` (SHA-256 `55bb1048…`, commit 41b66b7). Underlag:
142 skanningsfiler i sex öppna serier, alla mätta två gånger (P-data: protokollet, bara runor; A-data: alla spår med
streckklass). Råutdata: `s0_stavlosa_filter.txt`, `s0a.txt`, `s_analys.txt/.json`, `s3_varians.txt/.json`,
`s3_fall.txt`, `s4_*.txt/.json` i den här mappen; mätningarna i `utdata/automatisk_korning/` och
`utdata/automatisk_korning_alla/`.

## Steg 0 – grunden
- **0a Upplösning.** Hs 14 (0,40 mm runor mot 1 mm hela stenen): V-vinkeln stabil (|Δ| 0,33° mot 16,6° mellan
  stenar), djup, bredd och bottenradie *upplösningskänsliga*; den grova filen har bara 11 snitt. M 14 (två filer, 2
  snitt i varje): alla fyra mått märks känsliga enligt regeln, men jämförelsen bygger på 2 snitt per fil och säger
  nästan ingenting. Följd enligt planen: upplösningen tas med i studie 3 för alla fyra måtten.
- **0b Stavlösa runor.** Runfiltret känner igen median 20 % av textens runor på de tio stenarna med stavlösa runor
  mot 81 % på övriga (Hs 10: 1 av 225). Stavlösa inskrifter underskattas alltså av den automatiska analysen med
  runfilter; de mäts i A-data och utesluts ur studie 3. *Förbättring att göra i appen:* ett läge för stavlösa runor.
- **0c** – se studie 4.

## Studie 1 – samma händer eller nytt hantverk?
- **Giltighetskontroll** (före testet; sex objekt, `scratchpad`-figur återskapas med koden i loggen): streckklassen
  *ornament* är i praktiken *långa eller böjda spår*: slingkanter, ramlinjer och ornamentik. Runorna klassas som
  runor inne i slingorna på båda objekttyperna. Stoppregeln (ornamentiken mestadels klassad som annat) utlöstes inte.
  Jämförelsen gäller därför **runor mot de långa linjerna** (ramar, slingkanter, ornamentik).
- **Underlag:** 33 gravmonument (Västergötland 24, Ög/Sm 8, Sö 371) och 71 runstenar (Sö 34, M 13, Hs 12, Vg 9,
  Åsmund 3) med minst 10 snitt i båda klasserna; 4 gravmonument och 2 runstenar föll bort på det kravet.
- **Inom objekten skiljer sig runor och linjer knappt:** median-Δ (runor − linjer) för V-vinkeln −1,6° på
  gravmonumenten och −0,4° på runstenarna; djup −0,13 och −0,05 mm, bredd −0,68 och −0,41 mm.
- **Huvudtest (V-vinkel):** skillnad i median-Δ −1,20°, 90 % KI [−3,21; +0,55], p = 0,29. **Utfall: samma mönster**
  (intervallet inom ±5°).
- **Sidotest:** djup −0,08 mm (q 0,30), bredd −0,27 mm (q 0,30), bottenradie +0,03 mm (q 0,83). Inget signifikant.
- **Robusthet:** samma mönster i alla åtta varianterna (bara runstenar i sandsten/kalksten, 16 st; varje serie
  utelämnad; bara ATOS). Enda sidosignalen: utan Västergötland (9 gravmonument kvar) djup −0,27 mm, q = 0,049.
- **Efterhandskontroll 1 (inte i planen; tillagd när figuren visade felklassade runstavar i slingan på Vg 50):**
  bara linjesnitt minst 10 mm från varje runsnitt: skillnad −1,07°, 90 % KI [−3,21; +0,57], p = 0,32, samma mönster;
  med 20 mm −1,30° [−2,81; +0,44], p = 0,19 (`s1_efterhand.txt`).
- **Efterhandskontroll 2, mätningens känslighet:** runor mot oregelbundna spår (sprickor, vittring) på samma sten,
  103 objekt: djup +0,24 mm (Wilcoxon p = 2,9e−14), V-vinkel −2,45° (p = 8,0e−6), bredd +0,27 mm (p = 1,9e−5)
  (`s1_kanslighet.txt`). Mätningen ser alltså skillnader på någon grad och tiondels millimeter inom en sten.
- **Begränsningar:** ingen positiv kontroll (inget objekt där vi vet att linjerna höggs av andra händer); metoden
  ser spårets profil (verktygets form och vinkel), inte planering eller layout. 15 av gravmonumenten saknar
  Rundatapost (Varnhemsfilerna utan signum) och därmed bergart. Gravmonumenten kommer till stor del från en serie och
  en skanner (ATOS), men ATOS-varianten ger samma resultat.

## Studie 2 – stavlösa runor på sten
- **2a (pilot):** Hälsinglands stavlösa stenar (Hs 10, 12, 14, 15) mot övriga nio: spårdjup 2,53 mot 1,74 mm,
  exakt p = 0,26; bland bara kristallina stenar (2 mot 5) 2,16 mot 2,55 mm, p = 0,81. Ingen skillnad som går att
  skilja från slumpen med så få stenar.
- **2b (inom sten):** väntar på handmärkning av runorna på M 3, M 4, M 7, M 8 och Sö 164.

## Studie 3 – hur mycket av ristaren syns i spåret?
- **Underlag:** bara 9 stenar av 4 ristare uppfyller villkoren (en säker ristare, minst två stenar, inga stavlösa
  runor): Tore 1 (Sö 143, 149), Traen (Sö 112, 129, 45), Äsbjörn (Sö 206, 208), Åsmund (Gs 11, U 1144); 5 393 snitt.
- **Variansandelar** (95 % bootstrap): V-vinkel sten 10,8 % [0,1; 19,8], ristare 0,0 % [0; 13,6], bergart 0,0 %
  [0; 15,4], inom sten 89,2 %. Djup: ristare 8,8 % [0; 35,5]; bredd 19,3 % [0; 45,2]; bottenradie 12,7 % [0; 32,0].
- **Tolkning:** de öppna skanningarna räcker inte för att skilja ristarens andel från bergartens; intervallen är för
  breda. Det tydliga resultatet är att **72–89 % av variationen ligger mellan snitten på samma sten** – ett enskilt
  stenmedelvärde är brusigt och kräver många snitt.
- **Fallstudie Åsmund (beskrivande, i planen inget test):** U 1144 (granit) ligger närmare Åsmunds sandstensstenar
  Gs 11 (0,61) och Gs 13 (0,85) än medianen för kristallina stenar (1,90); rang 5 och 7 av 71. *Efterhandskontroll,
  inte planerad:* att båda hamnar bland de 7 närmaste av slump har sannolikheten 21/2485 ≈ 0,8 %. Gs 13 och U 1144
  har medristare, och alla tre kommer ur samma skanningsserie.
- **Fallstudie Fartägn (förslag):** närmast M 1 i Medelpad: M 15 (0,82), M 2 (1,11), M 7 (1,20). Inte kalibrerat
  utanför Mälardalen.

## Studie 4 – vad skannern ser i de skadade partierna
- **Spårcacher:** 30 stenar (Medelpad 14, Hälsingland 13, Gs 11, Gs 13, U 1144), inga fel.
- **0c Blindprovet** (led F:s upplägg, `s4_blindprov.txt`, `s4_blindprov_sammanfattning.json`): bara 9 av 30 stenar
  kunde prövas (Rundatas orddelning måste täcka texten): Gs 11, Hs 12, Hs 21, M 1, M 2, M 3, M 5, M 8, M 15; 108 ord
  med spår. Rätt ord: utan spår 61 %, med skannerns spår 65 %, med omflyttade spår 60 %. Sannolikheten för rätt svar:
  0,324 → 0,365 (Wilcoxon p = 0,004 mot utan spår, p < 0,0001 mot omflyttade). Rätt ord: 4 vinner, 0 förlorar
  (McNemar p = 0,13). **Regeln uppfylld:** spåren används också utanför Södermanland.
- **Läsningarna** (`s4_lasningar.txt/.json`): modellen läser 28 av 30 stenar (Hs 3 och Hs 4 har för få läsbara runor);
  13 förslag når minst 80 % kalibrerad sannolikhet. **Alla luckor med förslag är redan återställda av utgivarna i
  Rundata** (luckinventeringen tm19, status återställt), inga är öppna. Modellens ord stämmer med utgivarnas
  återställning i 15 av 16 luckor; den 16:e (Hs 14) skiljer bara i böjningen (He-Gylfi mot He-Gylf[a]).
- **Tolkning:** studien ger inga nya läsningar på dessa stenar, men en oberoende bekräftelse av utgivarnas
  återställningar och ett första belägg för att spårläsaren hjälper även på skanningar från en annan skanner
  (HandySCAN) och andra landskap. En jämförelse runa för runa mellan spåren och de återställda runorna gick bara att
  göra på 2 positioner och redovisas inte.

## Avvikelser från planen
- **Studie 4, blindprovet:** planen sade "3 läsbara runor per sten, slumpfrö 1". Körs i stället som led F
  2026-10-17 (hela ord på 2–6 runor, med omflyttade spår som kontroll), för att resultatet ska kunna jämföras med
  Södermanlandsprovet.
- **Steg 0a:** M 14 bygger på 2 snitt per fil; regeln tillämpades ändå som den står.
- **Studie 1:** två efterhandskontroller tillagda (se ovan); de ändrar inte utfallet och redovisas som efterhand.
