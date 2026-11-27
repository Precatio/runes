# Vad försvann? Ornamentiken på förlorade och bevarade runstenar (2026-11-26)

Plan `analysplaner/2026-11-26-vad-forsvann.md`, låst före jämförelsen. Skript `data.py` och `vad_forsvann.R`, utfall
`resultat.json`.

## Urvalet
- **Förlorade:** 185 stenar som är kodade ur sina 1600- och 1700-talsteckningar.
- **Bevarade:** 125 stenar som är kodade ur sina teckningar i källkontrollen.
- **Samma källa på båda sidor:** teckningar och samma godkända fält. Uppland står för 128 respektive 96 stenar.

## Huvudprov
Modellen är glmer med socken som slumpeffekt och teckningens typ och Uppland som kontroller. Alla modeller konvergerade.

- **U2, kors:** förlorade 44 % (157 stenar) mot bevarade 62 % (114 stenar). Oddskvoten är 0,39 (0,21–0,73), Holm-p =
  0,009. **Skiljer.**
- **U1, rundjur:** 56 % (102) mot 73 % (79). Oddskvoten är 0,41 (0,18–0,95), p = 0,038, Holm-p = 0,054. Skiljer inte
  efter justeringen.
- **U3, utarbetad ornamentik** (flera djur, koppel eller tät fläta): 41 % (151) mot 57 % (109). Oddskvoten är 0,42
  (0,19–0,90), p = 0,027, Holm-p = 0,054. Skiljer inte efter justeringen.

## Beskrivande
- **Bara Uppland:**
  - kors 45 mot 65 %, oddskvot 0,35, p = 0,004;
  - rundjur 73 mot 86 %, p = 0,08;
  - utarbetad 56 mot 65 %, p = 0,15.
- **Förlorade (teckning) mot alla bevarade planschstenar (foto) i samma socknar:**
  - rundjur 56 mot 79 %;
  - kors 44 mot 65 %;
  - utarbetad 41 mot 59 %.
  - Källan skiljer sig här, men riktningen är densamma.
- **Per typ av teckning** (`per_typ` i resultat.json; rättat 2026-11-27): skillnaden i kors bärs främst av Bautil
  (förlorade 41 % av 116 mot bevarade 76 % av 34) och delvis Peringskiöld (48 mot 59 %); hos Rhezelius (55 mot 53 %) och
  övriga tecknare (56 mot 57 %) är andelarna lika. Rundjur och utarbetad ornamentik är lägre hos de förlorade i alla typer.
  Bautils utsnitt kontrolleras därför bild för bild (ett utsnitt, U 1038, visade fel träsnitt).

## Vad det betyder och inte betyder
- **De runstenar som försvann efter 1600-talet hade mer sällan kors** än de som finns kvar, i samma slags källa och med
  socknen hållen konstant. Rundjur och utarbetad ornamentik pekar åt samma håll: de förlorade stenarna var enklare. De
  skillnaderna är dock inte säkra efter justeringen för tre prov.
- **Följden för forskningen:** andelen runstenar med kors bland de bevarade stenarna överskattar troligen andelen bland
  alla som restes. Studier som räknar kors eller kristna stenar bör ta hänsyn till det.
- **Varför stenarna försvann vet vi inte.** Det kan vara tiden, om stenar utan kors är äldre och fler hann gå förlorade.
  Det kan vara var de stod, eller att stenar utan kors oftare användes som byggnadssten. Tiden kunde inte hållas konstant,
  eftersom de flesta förlorade stenarna saknar stilgrupp.
- **Urvalet är litet.** Intervallen är breda, och teckningarna själva kan vara ett urval.

## Kontroll av Bautils utsnitt (2026-11-27, utforskande)

### Granskningen
- **Underlaget:** alla 441 Bautil-utsnitt som användes i kodningen (förlorade stenar, källkontroll och luckor), granskade
  bild för bild.
- **Utfall:**
  - 380 rätt;
  - 40 där även ett grannträsnitt syns men rätt träsnitt finns helt;
  - 11 med fel nummer;
  - 10 ofullständiga.
- **Av de 11 med fel nummer** är bilden rätt i 5 fall; där är bara det registrerade numret ett skrivfel (till exempel B 591
  angivet som 691).
- **Verkliga fel:** 6 utsnitt visar fel träsnitt: U 1038, U 731, U 952, U 988, U 652 och U 237.
- **Listan** över berörda stenar finns i `felaktiga_utsnitt.json`.

### Känslighetskontrollen
Huvudprovet räknades om utan de 10 berörda stenar som ingår i analysen:
- **kors:** 43 mot 61 %, oddskvot 0,43 (0,23–0,80), p = 0,008;
- **rundjur:** oddskvot 0,41, p = 0,04;
- **utarbetad ornamentik:** oddskvot 0,43, p = 0,03.

**Slutsatsen om korset står sig.** Felen i utsnitten förklarar inte skillnaden. De felaktiga utsnitten bör göras om innan
registret används vidare.
