# Gräslund 1: bär de kodade dragen stilgrupperna? (2026-11-25)

Plan `analysplaner/2026-11-25-graslund-1-stilgrupper.md` (sha 69d74f4e), låst före analysen. Skript `graslund1.py`, utfall
`graslund1.json` och sannolikheter per sten i `stil_sannolikhet.csv`.

## Data
- **Stenarna:** 620 med minst tre eniga ornamentdrag ur SRI:s planscher och en stilgrupp i Rundata.
  - Fördelning: RAK 146, Fp 96, Pr1 28, Pr2 69, Pr3 90, Pr4 160 och Pr5 31.
- **Dragen:** 41 indikatorer ur 14 fält.

## F1, bär dragen stilgruppen? **Håller.**
- **Träffsäkerheten** utanför vikten (femfaldig korsvalidering grupperad på socken) är 62 %. Att alltid gissa den
  vanligaste gruppen ger 26 %, och omblandade stilgrupper ger 22 %. p = 0,001.
- **Per grupp:**
  - RAK 92 %, Pr4 84 %, Fp 63 %;
  - Pr2 41 %, Pr1 32 %, Pr3 22 %;
  - Pr5 0 %: alla Pr5-stenar utom fyra blir Pr4.

## F2, är stilgrupperna en ordnad följd? **Håller.**
- Av 158 felklassade stenar inom Pr1–Pr5 hamnar 83 % hos en grannklass (Pr n ± 1). Slumpen ger 59 %, p = 0,001.
- Fördelningen av felen: 131 fel ett steg bort, 24 två steg och 3 tre steg.
- I de här dragen ser Pr-grupperna ut som en glidande följd, inte som skarpt skilda grupper.

## F3, vilka grupper finns i dragen själva? (beskrivande)
Den latenta klassmodellen väljer **tre klasser** (BIC). Justerat Rand-index mot Rundata är 0,34.
1. **Inget djurhuvud, inget flätverk:** 191 stenar, varav RAK 141 och Fp 33.
2. **Ett djur med enkelt huvud, rund öga, inga flikar, svans i spiral, oftast inget koppel:** 134 stenar, varav Fp 56,
   Pr2 28, Pr1 16 och Pr3 15.
3. **Huvud i profil, mandelformat öga, svans i spiral, koppel och extra orm:** 295 stenar, varav Pr4 144, Pr3 71, Pr2 35
   och Pr5 29.

Dragen räcker alltså till tre breda faser, men inte till Gräslunds sju grupper.

## F4, samma stil i olika landskap? (beskrivande)
- **Tränad på Uppland:**
  - inom Uppland: 59 % (korsvaliderat);
  - Östergötland: 69 % (mest RAK);
  - Södermanland: 41 % (RAK 88 %, Pr2 44 %, Fp 35 %, Pr3 18 %).
- Det som kallas Pr3 och Fp i Södermanland känns sämre igen med Upplands drag. Det är värt en egen fråga.

## F5, sannolikhet per sten (beskrivande)
- **Typiska stenar** (högsta sannolikheten ≥ 0,7):
  - RAK 85 %, Fp 50 %;
  - Pr4 35 %, Pr5 29 %, Pr3 26 %, Pr1 21 %;
  - Pr2 10 %.
- **Gränsfall** (< 0,4): Pr1 36 %, Pr2 29 % och Pr3 23 %.

## Utforskande, inte i planen: varför faller finindelningen?
- **Huvudets vy:** skiljer Fp (huvud ovanifrån, 32 av 52 kodade) från Pr1–Pr5 (nästan alla i profil).
- **Nack- och läppflikarna saknar konsensus för 75–95 % av Pr2–Pr5-stenarna.** Det är just de drag som Gräslund
  använder för att skilja Pr-grupperna åt.
  - Pr4: nackflik saknas för 146 av 160 stenar.
  - Pr3: nackflik saknas för 73 av 90 stenar.
- Finindelningen faller alltså främst på att flikarna inte kunde läsas från planschfotona, och inte nödvändigtvis på
  indelningen själv.

## Vad det betyder och inte betyder
- **Gräslunds huvudlinjer syns tydligt i data:**
  - band utan djur (RAK);
  - huvud ovanifrån (Fp);
  - en följd av profilhuvuden (Pr).
- **Pr-grupperna bildar en ordnad följd.**
- **Om fem skilda Pr-grupper eller ett kontinuum: inget besked ännu.** Proven kan inte avgöra det förrän nack- och
  läppflikar, huvudets form och linjernas proportioner är kodade på fler stenar.
- **Nästa steg i Gräslundsspåret:** en läsning av huvudena i utsnitt, ett exempelblad med Gräslunds egna huvudtyper och
  en tredje läsare som avgör vid oenighet. Därefter prövas ordningen i tid mot datering som inte bygger på stilen.
- **Rundatas stilgrupp är inte facit.** Den är experternas tillämpning av Gräslunds kriterier.
