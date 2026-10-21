# Analysplan: Vitkis säkraste ristarförslag för runstenar utan ristare

Skriven och låst 2026-10-21 innan något av punkterna 3–5 har räknats (METHODS.md 1x, ANALYSPLAN.md). Hash i
`analysis_plan_forslag.sha256`. Kända sedan tidigare: Stenöversiktens antal per status (79 nytt förslag, 254 möjligt
förslag) och listan över stenar som har en ristare i Runor 2020 men inte i Rundata 3.1 (namnen, inte Vitkis förslag
för dem).

## 1. Fråga
Hur ofta har Vitkis förslag rätt när en runsten saknar ristare, och vilka stenar utan ristare i Rundata 3.1 får de
säkraste förslagen? Ja = i blindprovet (punkt 3) har förslagen med status *nytt förslag* rätt klart oftare än en enkel
regel som föreslår ristaren bakom den närmaste stenen med säker ristare, på samma stenar (McNemar, p < 0,05). Nej =
inte det; då skrivs ingen artikel som presenterar förslagen som Vitkis styrka, och utfallet redovisas.

## 2. Underlag
* Runstenar (`research_gaps.is_runestone`), Samnordisk runtextdatabas 3.1 (2018), korpusversion 5ebd6df1627127fd.
* Stenöversiktens regel oförändrad (`src/stone_overview.py`, commit f96d11b): förslagets styrka ur R-modellens
  sannolikhet och ortografins förstaval, nedräknad med kontrollerna område, stil, språkdrag och bergart; *nytt förslag*
  vid styrka ≥ 0,5, *möjligt förslag* vid ≥ 0,3.
* R-modellens *kanske någon annan*: förstavalets sannolikhet under 0,35 (`attribution.json`, `open_set`).

## 3. Blindprovet (primärt)
* Stenar: alla runstenar med en säker ristare i Rundata (signerad eller attribuerad, utan frågetecken), vars ristare
  finns bland de ristare Vitki kan föreslå (modellens 18 eller ortografins), plus de vars ristare inte finns där – de
  senare kan inte få rätt men visar hur ofta Vitki föreslår fel ristare.
* För varje sten döljs attribueringen: stenen görs ristarlös i en kopia av korpusen, och ristarnas landskap, stilgrupper,
  bergarter och språkprofiler räknas utan den. Ortografin utesluter redan stenen själv. R-modellens sannolikheter är de
  korsvaliderade (från modeller som inte såg stenen); för stenar utanför modellens träning används modellens förstaval
  ur `open_set.small_carvers` när stenen ligger inom 25 km, annars ingen modell – som för en ristarlös sten.
* Mått: (a) **precision** för *nytt förslag* = andelen där den föreslagna ristaren är Rundatas, med Wilsons 95
  %-intervall; samma för *möjligt förslag*; (b) andelen stenar som får ett *nytt förslag*; (c) **jämförelse** med
  regeln *närmaste ristare* (ristaren bakom den närmaste andra stenen med säker ristare) på exakt samma stenar, parvis
  med McNemars exakta test; (d) samma för bara signerade stenar; (e) precisionen när R-modellen säger *kanske någon
  annan* och när den inte gör det.

## 4. Externt prov (sekundärt)
Runstenar utan ristare i Rundata 3.1 som har en namngiven ristare i Runor 2020 (`data/raa/runor_2020.json`; inte
"Samma som gjort …", "Imitation av …" eller anmärkningar). Vitkis förslag räknas som i appen, på Rundata 3.1, och
jämförs med Runors ristare. Redovisas med antal (få stenar väntas), ingen gräns.

## 5. Urvalet i artikeln
Stenar utan ristare i Rundata 3.1 med status *nytt förslag*, ordnade efter styrka. De tio starkaste där R-modellen inte
säger *kanske någon annan* visas med alla belägg; övriga räknas och visas i en tabell. Varje visat förslag stäms av mot
Runor 2020 och Wikidata (`src/crosscheck.py`): *finns redan* redovisas som en bekräftelse, *annan ristare* som en
motsägelse, *saknas* som nytt. Inga stenar väljs bort för hand.

## 6. Vad som INTE får göras
Inga ändringar av vikter, gränser (0,5, 0,3, 0,35) eller regler efter att resultaten setts. Ingen egen läsning av
inskrifterna och inga egna attribueringar; förslagen är hypoteser att pröva mot stenarna. Bara runstenar.

## 7. Redovisning
`utdata/forslag/resultat.md` och `utdata/forslag/blindprov.json`, METHODS.md 14c (blindprovets precision) och, om
punkt 1 ger ja, ett opublicerat artikelutkast med skärmbilder ur appen. Ett nej redovisas lika tydligt.
