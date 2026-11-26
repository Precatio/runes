# Analysplan: lokala ornamenttraditioner – hur mycket av ornamentiken skiljer sig mellan bygder?

Skriven och låst 2026-11-26, innan ornamentkoderna har ställts mot häraderna. Gräslundsspåret
(`utdata/graslund/resultat.md`). Gräslund 1 visade att modellen tränad på Uppland kände igen Södermanlands Pr3 och Fp
sämre. Här mäts frågan systematiskt.

## Data
- **Stenarna:** konsensuskoderna ur SRI:s planscher (`orn_koder.json`). Bevarade stenar (`lost` = 0) med en stilgrupp i
  Rundata (RAK, Fp, Pr1–Pr5) och känt härad (`district`), korpus 510ebfb3.
- **Utfallen, ett binärt drag i taget** (värdet saknas om fältet inte är kodat):
  - D1 `koppel` = ja;
  - D2 `huvud_vy` = uppifran (bland stenar med huvud);
  - D3 `oga` = mandel (bland rund eller mandel);
  - D4 `flatverk` ≠ inget;
  - D5 `orm_extra` = ja;
  - D6 `kors` = ja;
  - D7 `antal_djur` ≥ 2 (bland stenar med djur);
  - D8 `svans` = spiral (bland stenar med kodad svans).
  - Ett drag prövas bara om minst 100 stenar och minst 20 härader har ett värde.

## Modell och prov
- **Modellen** (R, `lme4::glmer`, binomial): drag ~ stilgrupp + landskap + (1 | härad) + (1 | härad:socken).
- **Andelen mellan härader (ICC):** σ²_härad / (σ²_härad + σ²_socken + π²/3).
- **Prov per drag:** likelihood-kvotprov för häradets slumpeffekt (modellen med mot utan `(1 | härad)`). p halveras
  eftersom variansen prövas mot gränsen 0. Holm-justering över de drag som prövas.
- **Ett drag har en lokal tradition** om Holm-p < 0,05.
- **Konvergerar en modell inte** tas sockentermen bort, och det redovisas.

## Beskrivande
- ICC med 95 % intervall (parametrisk bootstrap, 200 dragningar, frö 20261126) för de drag som håller.
- **Jämförelse med skrivsättet:** samma modell för sex kategoriska språkdrag (lika eller olika värden, som i beläggen),
  så att ornamentikens lokala andel kan ställas mot skriftens.
- De härader som avviker mest (slumpeffektens skattning) för de drag som håller.

## Vad som inte skrivs
- **En lokal tradition betyder inte en enda verkstad.** Härader är grova enheter, och en ristare kan verka i flera.
- **Tiden är bara grovt kontrollerad** genom stilgruppen. Stilgruppen bygger delvis på samma drag, så ICC här mäter
  variation *utöver* den.
- **Uppland dominerar.**

## Utdata
`utdata/lokala_traditioner/data.py` och `traditioner.R` → `resultat.json` och `resultat.md`.
