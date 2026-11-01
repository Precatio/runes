# Analysplan: Upptäcktsmotorn, version 4 – beroendenätverket (Bayesianska nätverk)

Skriven och låst 2026-11-01, innan något nätverk har skattats. Viktor 2026-11-01: "kör det" (beroendekartan med
bnlearn efter att samspelsprovet v3 föll). Kod: `r/discovery_v4.R`. Resultat i `utdata/upptackt_v4/`.

## Frågan
Vilka av runstenarnas drag hänger **direkt** ihop, när alla andra drag, landskapet och tiden hålls konstanta – och vilka
samband finns bara genom ett tredje drag? Särskilt: vilka av de 15 parsamband som upptäcktsmotorn v1 och v2 bekräftade
är direkta, och vilka förklaras av andra drag?

## Vad som är känt före låsningen
Dragen och halvorna som i v3 (`analysplaner/2026-11-01-upptacktsmotorn-v3-samspel.md`; `utdata/upptackt_v3/drag.csv`,
1 739 stenar, 124 binära drag, familjer och förbjudna par). v3:s utfall (inga samspel) är känt. De 15 bekräftade paren ur
v1 (`utdata/upptackt/upptackt.json`) och v2 (`utdata/upptackt_v2/upptackt.json`): kvinna_ensam–rel_make,
flera_resare–rel_barn, kvinna_resare–rel_make, flera_resare–rel_foralder, kvinna_resare–rel_barn, kvinna_ensam–rel_barn,
o_runa–rel_barn, msg_dod_uppgift–rel_foralder, kvinna_resare–rel_foralder, msg_resa–flera_resare,
kvinna_ensam–rel_foralder, pm_kors–skilj_apostrof, msg_dod_borta–rel_foralder, cat_fard–flera_resare,
msg_resa–rel_foralder. bnlearn 5.2.1 installerat 2026-11-01. Inga nätverk är skattade.

## Data
Alla 124 drag som faktorer; *ej mätbart* (NA) blir en egen nivå. Landskap (landskap med färre än 20 stenar slås ihop
till *övrigt*), tidsskikt (som v3) och textlängd i tre lika stora klasser ingår som noder; inga pilar får peka *in* i
landskap, tidsskikt eller textlängd.

## Steg 1 – nätverket i halva A
`boot.strength` med 200 bootstrapdragningar av hill climbing (BIC), frö 2026. En **kant** är ett par noder med styrka ≥
0,85 (riktningen räknas inte). Kanter mellan två drag ur olika familjer och som inte är förbjudna blir **kandidater**;
kanter inom en familj (definitionsberoende) och kanter till landskap, tid och längd redovisas men prövas inte. Listan
fryses (SHA-256) innan halva B läses. Inget tak.

## Steg 2 – pröva i halva B
För varje kandidat *a*–*b*: `glm(b ~ a + G + landskap + tidsskikt + längdklass)`, där G är grannarna till *a* och *b* i
halva A:s nätverk (utom *a*, *b* och de tre bakgrundsnoderna), med NA-raderna för *a* och *b* borttagna och NA i G som
egen nivå. Ensidigt i riktningen hos samma modell i halva A. **Bekräftad direkt kant** = Holm-justerat p < 0,05.
Sekundärt: halvorna bytta.

## Steg 3 – de kända paren
För vart och ett av de 15 paren: är det en bekräftad direkt kant, en kant i A som inte bekräftades, eller ingen kant (sambandet
går genom andra drag)? För de två sista: vilka drag ligger mellan dem i A:s nätverk (kortaste väg). Beskrivande.

## Redovisning
`utdata/upptackt_v4/kandidater.json` (+ `.sha256`), `natverk_A.rds`, `resultat.json`, `resultat.md`, och en bild av de
bekräftade kanterna (`natverk.png`, med Vitki som upphov i bildtexten).

## Vad som inte får göras
Tröskeln 0,85, antalet dragningar, poängmåttet, grannmängden och Holm-gränsen ändras inte efter körningen.
