# Analysplan: Attribueringsmodellen version 3 – kalibrerad ”samma hand” och ristarens bygd

Låst 2026-11-04, efter version 2 och innan något av nedanstående körts. SHA-256 i
`analysplaner/2026-11-04-attribuering-v3.sha256`. Kod: `r/attribution_v3.R`. Resultat i `utdata/attribuering_v3/`.

## Bakgrund och vad som redan setts
Version 2 (`analysplaner/2026-11-04-attribuering-v2.md`, `utdata/attribuering_v2/resultat.json`) behöll bara korsformen
(A+1: rätt förstaval 71,2 %, medel per ristare 43,7 %). Två steg föll på regeln trots stora vinster: **samma hand**
(+5,7 procentenheter, intervall 0,8–11,4; per ristare +14,5, 3,8–20,4) föll på okalibrerad log-förlust (2,15 mot 1,32;
dess potens slog i rutnätets kant, a = 5); **bygd och tid** (per ristare +14,3 på halva 2) föll på förstavalet
(−2,7 på halva 2, −16 till +9). Alla siffror ovan är **sedda**: den här planen prövar samma 117 signerade stenar igen.
Därför fattas varje beslut bara på sockenhalva 2, allt som väljs (kalibrering, vikter) väljs på halva 1, och de 380
attribuerade stenarna är ett andra mått som redovisas för varje variant.

## Varianter (alla med korsformen, samma korsvalidering som version 1–2)
- **K0** A+1, kalibrerad (potens på halva 1). Jämförelsemodellen.
- **K1** Samma hand, kalibrerad: potens a i rutnät 0,5–15 vald på halva 1.
- **K2** Samma hand × bygd och tid: P ∝ P_par × bygd^w × tid^w, w i 0–2 vald på halva 1, sedan kalibrerad.
- **K3** Skogen utan koordinater × bygd och tid (version 2:s steg 3, med korsformen), w och kalibrering på halva 1.
- **K4** Blandning: (1 − v) · K0 + v · K1 (båda kalibrerade), v i 0–1 (steg 0,25) vald på halva 1.

## Beslut (på halva 2, signerade stenar)
En variant **godtas** om, mot K0: andel rätt förstaval och medel per ristare båda är högre (punktskattning > 0) och den
kalibrerade log-förlusten inte är sämre. Bland de godtagna väljs den med lägst kalibrerad log-förlust på halva 2.
**Påvisad förbättring** om bootstrap-intervallet (socknar, 2 000) för förstavalet på halva 2 inte rör 0. Godtas ingen,
blir K0 appens modell. Det andra måttet (attribuerade stenar, hela datan) redovisas men avgör inte.

## Sedan
Den valda modellen byggs in i appen (r/attribution.R) med sin kalibrering, ”någon annan”-spärren räknas om för den, och
provbänkens siffror (halva 2 och hela) blir de som appen visar, med beskedet att de 117 stenarna setts flera gånger.
