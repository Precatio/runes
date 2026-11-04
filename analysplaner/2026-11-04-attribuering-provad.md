# Analysplan: Attribueringsmodellen prövad mot de signerade stenarna

Låst 2026-11-04, innan något körs. SHA-256 i `analysplaner/2026-11-04-attribuering-provad.sha256`. Kod:
`r/attribution_audit.R`. Resultat i `utdata/attribuering_provad/`.

## Bakgrund
Vitkis attribueringsmodell (r/attribution.R, random forest) ger 72,8 % rätt förstaval vid slumpvis korsvalidering och
68,8 % när hela socknar hålls utanför (korpus 7b9061c9). Men facit är Rundatas ristare, och 380 av de 497
träningsstenarna är *attribuerade*, inte signerade – tillskrivna efter just stil, stavning och plats, som modellen
själv använder. Modellen kan alltså mest ha lärt sig att återskapa attribueringarna. Viktor 2026-11-04: attribuering
blir appens nästa stora fokus; först ska utgångsläget mätas ärligt. Sett före låsningen: antalet signerade och
attribuerade stenar per ristare (bland modellens 18: 117 signerade; Traen 0, Halvdan 0, Erik 1, Gunnar 2) och
attribution.json:s egna siffror ovan (ECE 0,32; gränsen för ”någon annan” 0,35). Inga nya körningar.

## Material
Som r/attribution.R: svenska vikingatida runstenar i korpus 7b9061c9a1c12c73 med säker ristare (carver), ristare med
minst 8 stenar (18 ristare), samma variabler (”Alla”: koordinater, landskap, stil, kors, kortkvist, språkdrag,
formler, runbigram, innehåll), random forest 500 träd, min_n 2, seed 2026. **Facit = signerade stenar.**
Korsvalideringen är grupperad per socken (5 delar, 3 upprepningar; stenar utan socken egen grupp), så att en sten
aldrig prövas med en grannsten från samma socken i träningen.

## Fråga 1: hur ofta har modellen rätt om en signerad sten?
Modell A (som i dag) tränas på signerade och attribuerade stenar. Mått på de signerade stenarna i provdelarna:
andel rätt förstaval, rätt bland tre, log-förlust, med 95 % bootstrap-intervall över socknar (2 000 dragningar).
**Huvudsiffran** som appen ska visa är andel rätt förstaval på signerade stenar, grupperat per socken.

## Fråga 2: lär sig modellen ristarna eller attribueringarna?
Samma körning, de attribuerade stenarna i provdelarna. Jämförelse signerade mot attribuerade inom ristare:
glmer(rätt ~ signerad + (1 | ristare), binomial). Är attribuerade stenar klart lättare (koefficient < 0 för
signerad, p < 0,05) säger det att modellen delvis återskapar forskarnas egna bedömningar.

## Fråga 3: tillför attribueringarna något?
Ristarna med minst 5 signerade stenar (S). Modell B tränas bara på signerade stenar av S; modell A som ovan. Båda
prövas på samma signerade stenar av S i samma provdelar, A:s sannolikheter begränsade till S och omnormerade.
Skillnad i andel rätt förstaval, parvis per sten, bootstrap över socknar. **Attribueringarna hjälper** om A − B > 0 med
intervall som inte rör 0; **skadar** om < 0 på samma sätt; annars ingen påvisad skillnad.

## Fråga 4: slår modellen geografin?
Två jämförelser på samma signerade stenar: (a) delmodellen med bara geografi (koordinater + landskap), (b) närmaste
träningsstens ristare (1-NN i rummet). Modellen **slår geografin** om andel rätt för A minus den bästa av (a) och (b)
är > 0 med bootstrap-intervall som inte rör 0.

## Fråga 5: kalibrering och ”någon annan”
- ECE för förstavalet på de signerade stenarna (10 lika breda fack).
- Omkalibrering: p_k^a omnormerat, a valt genom att minimera log-förlust på provdelarna för socknar i halva 1 (socknar
  ordnade efter namn, varannan), utvärderat (ECE, log-förlust) på socknar i halva 2.
- ”Någon annan”: tröskeln från r/attribution.R räknas om med de **grupperade** sannolikheterna för kända stenar (i dag
  används de slumpvis korsvaliderade, som är för säkra). Rapporteras: andel flaggade bland kända signerade stenar och
  bland utelämnade ristares stenar.

## Vad som rapporteras och vad som händer sedan
Alla fem svaren, i klartext. Inget i appen ändras i det här steget. Huvudsiffran och svaren på fråga 2–4 avgör nästa
steg: om attribueringarna inte hjälper (fråga 3) eller modellen inte slår geografin (fråga 4), byggs nästa modell
kring de signerade stenarna och nya belägg (ornamentik, runformer) i stället för fler attribuerade etiketter.
Begränsning: 117 signerade stenar, de flesta av Öpir och Balle; fyra av modellens ristare har nästan inga signerade
stenar och kan inte prövas mot facit alls.
