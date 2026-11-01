# Analysplan: Maltstenens runmästeriprofil – automatiska drag, blind klassning och tolkningarna

Skriven och låst 2026-11-01, innan något av måtten nedan har räknats. Viktor 2026-11-01: "gå vidare på spåret" om att
sida A (*titultitul* + hel runrad) liknar runmästeri och besvärjelse, med svagheterna litet underlag och handklassning
utan blindning. Uppföljning till `analysplaner/2026-11-01-malt-runrad-dubblering.md` (446e064).

## Vad som är känt före låsningen
- Resultatet i `utdata/Malt/runrad_dubblering_resultat.md`: av åtta vikingatida inskrifter med runrad och minst 20 runor
  annan text är två vanlig text (vår handklassning).
- Malt har enligt utgåvorna ett eget tecken, en tredubblad t-runa (`utdata/Malt/tolkningar.json`, avsnitt *ttt*); i
  Rundatas translitterering står det som *?*. Gørlev (DR 239) och Ledberg (Ög 181) skriver *þistill, mistill, kistill*
  med tredubblade runor (*þmkiiissstttiiilll*).
- De sju tolkningarnas kodning av avsnitten *suaai*, *ttt*, *runor* och *helhet* (`tolkningar.json`).

## Del 1 – runmästeridrag räknade med regler (ersätter handklassningen)
På alla vikingatida inskrifter (`runlm.viking`), med den rättade huvudläsningen från förra planen:
- **D1 runrad:** minst sex runor i följd i ordningen *fuþorkhniastbmlR*.
- **D2 mångdubblade runor:** minst två följder i rad av samma runa tre gånger eller fler (*iiisss*), över skiljetecken.
- **D3 dubblering:** en direkt upprepning *XX* med |X| ≥ 4 inom en skiljeteckengrupp.
- **D4 runorna själva:** Rundatas normalisering innehåller ett påstående om runorna eller om att tyda dem, enligt
  mönstret `runaR\W+(ret|rett|rettaR)|raða skal|\braði\b|\bræð\b|raðu\b|tæitirun|ævinrun|ginnurun|raginakund|reginkunn`
  (gemener, utan skiljetecken).
Malt får D2 ur utgåvorna (tecknet *ttt*), inte ur Rundatas translitterering; det redovisas.
**Profil:** antalet drag D1–D4 per inskrift. Alla inskrifter med minst två drag listas.

## Del 2 – följs dragen åt? (konfirmatoriskt)
Bland vikingatida inskrifter med minst tio runor (Malt utesluten): har inskrifter med runrad (D1) oftare något av D2–D4
än inskrifter utan? Fishers exakta test, ensidigt. **Håller** om p < 0,05 och andelen är högre med runrad i båda
halvorna (inskrifterna sorterade efter signum och delade varannan). Runstenar och övriga objekt redovisas också för sig.

## Del 3 – blind klassning
En oberoende agent (ny, utan tillgång till projektet, planen eller tidigare samtal) får texterna (Rundatas normalisering
och engelska översättning, runraden ersatt med *[runrad]*, utan signum och utan Malt) för de åtta inskrifterna med
runrad och minst 20 runor annan text, blandade med 16 slumpvis valda vikingatida inskrifter med 20–200 runor (frö
2026), och klassar var och en i: (i) minnesformel, (ii) namn, ägar- eller tillverkarformel, (iii) besvärjelse eller
religiöst, (iv) ingen tolkning, (v) annat. Mått: hur ofta agenten och vår handklassning ger samma klass på de åtta
(och Cohens kappa på alla 24 mot vår klassning av de 16, som görs före agentens svar läses). Vår slutsats om de åtta
**står sig** om agenten klassar högst tre av dem som (i) eller (ii).

## Del 4 – tolkningarna mot profilen (beskrivande)
För var och en av de sju tolkningarna: hur behandlar den sida A (*suaai : titultitul*), tecknet *ttt* och avsnittet om
runorna – som runmästeri, besvärjelse eller ritual; som vanlig minnestext eller dikt; eller oläst? Ur kodningen i
`tolkningar.json`, utan ny läsning av källorna. Ingen tolkning får "poäng" för att den stämmer; tabellen visar bara
vilka som tar ställning till de drag ristningen har.

## Vad som inte får göras
Mönstret i D4, reglerna för D1–D3, urvalet i del 3 och gränserna ändras inte efter körningen. Ingen läsning av Malt.

## Redovisning
`utdata/Malt/runmasteri.py`, `runmasteri.json`, `runmasteri_blind.json`, `runmasteri_resultat.md`.
