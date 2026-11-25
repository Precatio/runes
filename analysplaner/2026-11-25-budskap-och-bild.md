# Analysplan: följer runstenens budskap dess bild? Bekräftande prov på ett oberoende urval

Skriven och låst 2026-11-25, innan det oberoende urvalet har analyserats. Bekräftar eller avvisar ett utforskande fynd i
`utdata/graslund/skrev_ritade.md`.

## Det utforskande fyndet (första urvalet, används inte igen)
- **Urvalet:** 580 stenar med planschkod, text och stilgrupp, i 6 387 par inom 30 km i samma stilgrupp. Omblandning inom
  härad och stilgrupp.
- **Budskapet** (12 kategorier, se nedan): ρ = 0,23 mot 0,07, p = 0,002.
- **De språkliga markörerna:** stungna runor, monoftong, o-runa och r för R. Svagare: ρ = 0,08 mot 0,05, p = 0,036.

## Det oberoende urvalet
- **Vilka stenar:** alla stenar med minst tre ornamentdrag och minst tre ord text, som **inte** ingick i första urvalet.
  Till första urvalet räknas alla planschstenar med minst tre koder, text och en stilgrupp.
- **Tre källor:**
  - planschstenar utan stilgrupp i Rundata (`orn_koder.json`): 286;
  - förlorade stenar kodade ur teckningar, bara godkända fält (`orn_koder_forlorade.json`): 132;
  - Gotland, Öland, Hälsingland och Medelpad (`orn_koder_utvidgning.json`): 38.
- **Totalt:** 456 stenar och 10 968 par inom 30 km.

## Måtten
- **Budskapet:** cosinuslikheten mellan standardiserade profiler av exakt dessa 12 kolumner i korpus 510ebfb3:
  - `cat_minne`, `cat_bro_vag`, `cat_fard`, `cat_arv`, `cat_ting`, `cat_magisk`, `cat_grans`;
  - `pm_neutral`, `pm_signatur`, `pm_bro`, `pm_fard`, `pm_arv`.
  - Standardiseringen görs över alla stenar med text.
- **Ornamentiken:** andelen lika värden bland de fält som båda stenarna har, minst tre jämförbara. Det gäller de 14
  godkända fälten; för teckningar bara de fält som är godkända för respektive typ.

## Provet
- **B1 (huvudprov):**
  - **Mått:** Spearmans ρ mellan budskapslikhet och ornamentlikhet över alla par inom 30 km.
  - **Nollhypotes:** ornamentkoderna blandas om inom härad och källa (plansch, teckning eller utvidgning), 999 gånger, frö
    20261125.
  - **B1 håller** om ρ > 0 och ensidigt p < 0,05.
- **Tiden är svagare kontrollerad här än i första urvalet,** eftersom de flesta stenarna saknar stilgrupp. Därför finns
  ett beskrivande prov för stenarna med stilgrupp: par i samma stilgrupp, med omblandning inom härad, stilgrupp och källa.

## Beskrivande
- **Varje budskapskategori utelämnad i tur och ordning:** ρ utan kategorin. Det visar vad som bär sambandet, till exempel
  signaturerna.
- **B1 per källa:** plansch respektive teckning.
- **De språkliga markörerna för sig.**

## Vad som inte skrivs
- **Om B1 håller:** budskapets typ och bildens utformning hänger ihop utöver bygden. Det kan bero på beställaren, på
  ristarens yrkesroll (signerande yrkesristare med mer utarbetad ornamentik) eller på tiden, som här bara delvis är
  kontrollerad.
- **Om B1 inte håller:** det utforskande fyndet bekräftas inte och redovisas som obekräftat.

## Utdata
`utdata/graslund/budskap_bild.py` → `budskap_bild.json` och ett avsnitt i `skrev_ritade.md`.
