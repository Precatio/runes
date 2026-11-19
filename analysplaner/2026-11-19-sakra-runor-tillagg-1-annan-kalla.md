# Tilläggsplan 1: säkra runor och skanningskvalitet – på skanningar från en annan källa

Skriven och låst 2026-11-19, innan något prov i huvudplanen (2026-11-19-sakra-runor-skanningskvalitet.md, sha256
fb4a444a) eller i detta tillägg har räknats; körningen av huvudplanen hade startat men inget resultat fanns. Viktor
2026-11-19: "vi bör testa på andra stenar som inte är från samma källa, dvs inte Åhfeldts."

## Varför
Huvudplanen prövar Laila Kitzler Åhfeldts Södermanlandsskanningar, en enda skanner (ATOS) och en enda skannerförare.
Ett mått som tål konstgjorda försämringar där kan ändå bete sig annorlunda på skanningar gjorda på annat sätt. Detta
tillägg upprepar huvudprovet på skanningar från en annan källa.

## Material
Henrik Zedigs skanningar (HandySCAN BLACK Elite, 0,40 mm; Länsstyrelsen Västra Götaland), utgivna i Kitzler Åhfeldt &
Zedig: Medelpad (doi 10.5281/zenodo.14141222) och Hälsingland (doi 10.5281/zenodo.15638873), CC BY 4.0. Bara filer vars
ritade slingor är granskade (`data/runmodell/band/medelpad` och `halsingland`, status "granskad"): 15 i Medelpad och 12 i
Hälsingland vid låsningen. Västergötland är också skannat av Kitzler Åhfeldt och ingår därför inte. Flera filer kan
höra till samma sten (till exempel M 14, Hs 10). Omdragningen görs därför sten för sten (signum), inte fil för fil.
Filerna mäts först med groove-7, med appens förval och de ritade slingorna, och vyn ska vara rakt mot den ristade sidan.
Den mätningen är originalet (D0) i detta tillägg.

## Prov
Samma försämringar (D0–D3), samma två sätt att räkna stenmåttet (H och S, med samma gränser 4 snitt, 15 runor och 8
runor) och samma mått (V-vinkel, djup och bredd) som i huvudplanen.
- **R1z, huvudprovet i tillägget:** som R1 i huvudplanen på Zedigs skanningar: medelskillnaden ICC(S) − ICC(H) över de
  3 × 3 kombinationerna, med ett 95-procentsintervall ur 2 000 omdragningar av stenar. Slumpfröet kommer ur detta
  tilläggs kontrollsumma. **Håller** på samma villkor som R1.
- R2 görs inte i tillägget, eftersom för få ristare har flera stenar i materialet. Finns sådana redovisas avstånden
  beskrivande.

## Beslutsregeln, ändrad
S blir appens förvalda stenmått för huggspåren bara om R1 (Kitzler Åhfeldt) **och** R1z (Zedig) håller, och R2 inte
visar att S skiljer ristarna sämre. Håller bara den ena behålls H, och S redovisas som ett alternativ med båda
resultaten.

## Beskrivande (utan prov)
- Per källa: antalet säkra runor per sten och andelen stenar som får S-mått.
- Per källa: runornas överensstämmelse (ICC) per sten, och hur mycket måtten flyttar sig vid D1–D3.
- Källorna jämförs inte på stenmåttens nivå. Stenarna är olika och från olika landskap, så en skillnad i medelvärdena
  säger inget om skannern.

## Vad som inte skrivs
Två källor med olika stenar ger inget prov av samma sten i två skannrar. Det kräver att någon sten skannas om, vilket
står kvar som förslag.

## Utdata
Samma skript som i huvudplanen, med källan som parameter. Mätningarna skrivs till
`utdata/sakra_runor/matningar_zedig/`, resultatet till `resultat.json` (nyckeln "zedig") och `resultat.md`.
