# Analysplan: vad försvann? Ornamentiken på förlorade och bevarade runstenar, ur samma slags källa

Skriven och låst 2026-11-26, innan ornamentkoderna för förlorade och bevarade stenar har jämförts. Bygger på
ornamentregistret (`utdata/nya_ristare/resultat.md` § 11–12) och källkontrollen av 1600–1700-talets teckningar.

## Frågan
- **Frågan:** var det särskilda slags runstenar som försvann efter att de tecknades på 1600- och 1700-talen? Till exempel
  stenar utan rundjur, utan kors eller med enkel ornamentik.
- **Varför den är viktig:** varje studie av runstenarnas utseende förutsätter att de bevarade stenarna är representativa.
- **Om stenar försvann oberoende av hur de såg ut** är förutsättningen rimlig för de drag som prövas här.

## Urvalet: samma slags källa på båda sidor
- **Förlorade:** de 185 förlorade stenar som har koder ur en teckning (`orn_koder_forlorade.json`), bara fält som är
  godkända för teckningens typ.
- **Bevarade:** de 125 bevarade stenar som kodades ur sina teckningar i källkontrollen. Konsensus av två läsare, ur
  `kodning_kallkontroll.json` (`batch` t*). De valdes slumpvis inom fyra typer av teckning.
- **Planschfotona används inte i huvudprovet,** så att skillnaden inte kan bero på bildkällan.

## Utfallen (bestämda nu)
- **U1, rundjur:** `djurhuvud` = ja.
- **U2, kors:** `kors` = ja.
- **U3, utarbetad ornamentik:** minst ett av följande.
  - `antal_djur` = 2 eller 3+;
  - `koppel` = ja;
  - `flatverk` = attor eller tat.
  - Värdet saknas om inget av de tre fälten är kodat.

## Modell och prov
- **Modellen** (R, `lme4::glmer`, binomial, ett utfall i taget): utfall ~ förlorad + teckningens typ (Bautil, Rhezelius,
  Peringskiöld, övrig) + Uppland (ja/nej) + (1 | socken).
  - Socken som slumpeffekt tar hänsyn till att närliggande stenar hänger ihop.
- **Prov:** tvåsidigt Wald-p för `förlorad`, Holm-justerat över U1–U3.
- **Ett utfall skiljer sig** om Holm-p < 0,05. Oddskvoten med 95 % intervall redovisas för alla tre.
- **Kontroll av modellen:** konvergerar inte glmer används vanlig logistisk regression med klusterrobust fel per socken
  (`sandwich`). Det redovisas.

## Beskrivande
- Samma tre utfall bara i Uppland.
- Förlorade (teckning) mot alla bevarade planschstenar (foto) i samma socknar. Här skiljer sig källan, men källkontrollen
  visar att djurhuvud (κ 0,86) och kors (κ 0,81) stämmer väl mellan teckning och foto.
- Andelarna per grupp och typ av teckning.

## Vad som inte skrivs
- **Ingen skillnad betyder inte representativitet.** Urvalet är litet (54–157 stenar per utfall), så måttliga skillnader
  kan missas. Intervallen redovisas.
- **Tiden kan inte hållas konstant.** De flesta förlorade stenarna saknar stilgrupp.
- **Varför en sten försvann vet vi inte.** Provet visar bara om de som försvann såg annorlunda ut.
- **Teckningarna kan ha valts ut.** De tecknade stenarna kan vara de som tecknarna fann värda att teckna.

## Utdata
- `utdata/vad_forsvann/data.py` skriver `data.csv`.
- `vad_forsvann.R` skriver `resultat.json`.
- Sammanfattningen skrivs i `resultat.md`.
