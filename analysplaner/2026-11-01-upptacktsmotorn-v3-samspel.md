# Analysplan: Upptäcktsmotorn, version 3 – samspel mellan tre drag

Skriven och låst 2026-11-01, innan något samspel har räknats. Viktor 2026-11-01: "gå på spår 2, Kan vi använda nya paket
inom R för att hitta detta?" (mönster som bara syns när tre eller fler drag möts). Kod: `r/discovery_v3.R`. Resultat i
`utdata/upptackt_v3/`.

## Bakgrund och vad som är känt före låsningen
Version 1 och 2 (`analysplaner/2026-10-28-upptacktsmotorn.md`, `-2026-10-29-upptacktsmotorn-v2.md`) prövade alla *par*
av drag (b ~ a); parsökningen är uttömd (v2: 5 kandidater, 2 bekräftade, båda kända). Ingen av dem prövade **samspel**:
att sambandet mellan ett drag *a* och ett drag *y* beror på ett tredje drag *b*. Dragen är v2:s 128 per sten
(`src/discovery_v2.py`), nu byggda på korpus `e83202e01a5e6d27` (`utdata/upptackt_v3/drag.csv`, 1 739 stenar),
med v2:s familjer (`drag_familjer.json`) och förbjudna par (`drag_forbjudna.json`). Inga samspel är sedda.
Nya R-paket installerade 2026-11-01: hstats 1.2.2 (Friedmans H), pre 1.1.1 (regelensembler, RuleFit), partykit 1.3.1,
glmertree 0.2.7, arules 1.7.15; ranger fanns.

## Halvorna
Som v2: socken för socken, växelvis inom varje landskap i sockenmedeldateringens ordning. **Halva A** används bara för att
hitta kandidater; listan fryses (SHA-256) innan halva B läses. **Halva B** prövar.

## Steg 1 – hitta kandidater (bara halva A)
För varje drag *y* med minst 40 stenar med draget i halva A:
1. **ranger** (500 träd, frö 2026) förutsäger *y* ur alla drag från andra familjer än *y*:s, plus landskap, tidsskikt och
   log(1 + antal ord).
2. **hstats:** Friedmans H² för par av förklarande drag, bland de tio viktigaste (permutationsvikt). De tre paren med
   högst H² blir förslag.
3. **pre** (RuleFit, frö 2026): regler med två villkor på binära drag och koefficient skild från noll blir förslag.
Ett förslag (*y*; *a*, *b*) **blir kandidat** om *a*, *b* och *y* hör till tre olika familjer och inget av paren är
förbjudet; var och en av de fyra cellerna *a* × *b* har minst 15 stenar i halva A; och samspelstermen i
`glm(y ~ a * b + landskap + tidsskikt + log(1 + ord))` har p < 0,01 i halva A. Kandidaterna ordnas efter p; högst 30
behålls. Dubbletter (samma tre drag) räknas en gång.

## Steg 2 – pröva (bara halva B)
För varje kandidat: `gam(y ~ a * b + landskap + tidsskikt + log(1 + ord) + s(ristare, bs = "re"))`, binomial, ensidigt i
samspelstermens riktning från halva A. **Bekräftat** = Holm-justerat p < 0,05 över kandidatlistan. Sekundärt: halvorna
bytta (B hittar, A prövar), redovisas för sig.

## Steg 3 – för de bekräftade
- Effekten i klartext: andelen med *y* i de fyra cellerna *a* × *b* (justerade andelar ur glm i hela materialet).
- Utan ett landskap i taget (för landskap med minst 100 stenar): samspelets riktning ska hålla.
- Flyttade stenar (korpusens `moved`) uteslutna: riktning och p.
Bekräftade samspel som håller i båda stegen blir **mönster att pröva** i appen och kan bli rapporter under egna planer.

## Vad som inte får göras
Tröskeln 40, cellgränsen 15, p-gränsen 0,01, taket 30, fröna och halvorna ändras inte efter körningen. Kandidatlistan
ändras inte efter att den frysts.

## Redovisning
`utdata/upptackt_v3/kandidater.json` (+ `.sha256`), `utdata/upptackt_v3/resultat.json`, `utdata/upptackt_v3/resultat.md`.
