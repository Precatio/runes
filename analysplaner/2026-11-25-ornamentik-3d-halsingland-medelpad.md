# Analysplan: källkontroll för bilder ur 3D-skanningar, och ornamentkoder för Hälsingland och Medelpad

Skriven och låst 2026-11-25, innan någon 3D-bild har kodats. Följer kodbok v2 (sha 97cf9214) och källkontrollen för
teckningar (`analysplaner/2026-11-25-ornamentik-kallkontroll-teckningar.md`). Använder inget facit om händer.

## Varför
- Hälsinglands och Medelpads stenar saknas i SRI. För de bevarade stenarna finns bra bilder, se
  `data/cache/hander/plansch/hs_m_kallor.json`, där 17 stenar har kvaliteten "god".
  - **3D-skanningarna:** Kitzler Åhfeldt & Zedig, Zenodo, CC BY 4.0.
  - **Målade foton:** Wikimedia Commons och RAÄ via K-samsök, med fria licenser.
- Bilder ur djupkartor är en egen sorts källa. Innan de används prövas de mot planschfotona för skannade stenar som också
  finns i SRI.

## Bilderna ur djupkartorna
- **Skriptet:** `utdata/nya_ristare/ornamentik/djupbild.py`.
- **Beräkningen:**
  - lokal relief, det vill säga djupet minus utjämnat djup (σ = 12 mm);
  - stenytan enligt fältet `region`;
  - klippning vid percentil 2–98;
  - spåren mörka.
- **Samma beräkning för alla skanningar,** även Hälsingland och Medelpad.

## Del 1: källkontroll
- **Urvalet:** alla skannade stenar med en djupbild och minst tre eniga planschdrag i `orn_koder.json`.
  - Serierna: Södermanland, Västergötland, Östergötland/Småland (gravmonument) och Åsmund.
- **Kodningen:** två oberoende läsare per sten (Claude Opus).
  - De ser bara djupbilden, med en not om att det är en 3D-skanning utan färg.
  - De ser inte planschen.
- **Måttet:** per fält jämförs djupbildens konsensus med planschens: antal jämförbara stenar, andel lika och kappa.
- **Regel (bestämd nu):** ett fält får läsas från djupbilder när kappa är ≥ 0,40 och minst 15 stenar kan jämföras.

## Del 2: Hälsingland och Medelpad
- **Stenarna:** de 17 med kvaliteten "god".
- **Kodningen:** två läsare per sten. De ser alla bilder som finns för stenen: djupbilder ur `djupbild.py` och de målade
  fotona ur `data/cache/hander/plansch/hs_m/`.
- **Vilka fält som används:**
  - **Har stenen minst ett målat foto:** alla fält som är godkända för planscherna, eftersom moderna målade foton är samma
    sorts källa som planschfotona.
  - **Har den bara djupbild:** bara de fält som klarar del 1.
- **Märkning:** koderna läggs i `orn_koder_utvidgning.json`, märkta med landskap och bildkälla.

## Vad som inte skrivs
- **Planschfotot är inte facit.**
- **Djupbilden kan visa mer än fotot.** Den visar grunda spår utan färg, så den kan visa mer, och ibland annat, än den
  ifyllda färgen. En låg överensstämmelse kan alltså ha båda förklaringarna.
- **Hälsingland och Medelpad blir få stenar.** De räcker för att få med landskapen i registret, inte för egna slutsatser.

## Utdata
- **Skript:** `utdata/nya_ristare/ornamentik/kallkontroll_3d.py` skriver `kallkontroll_3d.json`.
- **Koderna:** ligger i cachen.
