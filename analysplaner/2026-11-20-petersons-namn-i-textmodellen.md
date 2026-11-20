# Analysplan: Petersons namnlexikon, nyinläst, i sannolikhetsmodellen (textmodel-23-kandidat)

Skriven och låst 2026-11-20, innan något av proven nedan har körts. Viktor 2026-11-20: "Petersons namnlexikon behöver
läsas in på nytt med bättre teckenigenkänning. Först då kan namnen prövas ordentligt."

## Känt före låsningen
- **Den gamla inläsningen** (textmodel-22, plan 2026-10-30-litteraturlexikon): Petersons namn ensamma på veck 0 gav +1
  ord inne i ord och 0 hela ord (139 luckor); tillsammans med litteraturen på veck 1–4 netto −2. Lexikonet är av.
- **Den nya inläsningen** (scripts/peterson_ocr.py, scripts/peterson_lexikon.py, 2026-11-20): 1 540 uppslagsord,
  6 619 belägg, 97,7 % av beläggen kontrollerade mot Rundata (signumet finns och formen står på stenen); 1 387 uppslagsord
  (90,1 %) motsvarar ett namn i Rundata, 153 gör det inte (många danska, brittiska eller keltiska namn som Rundata
  normaliserar annorlunda). Tabellen ligger i data/cache/literature/peterson2007_namn.csv (inte i git, upphovsrätt).
- **Varför effekten kan bli liten redan av uppläggningen:** maskeringsprovet utesluter varje namn vars artikel citerar
  en provsten i vecket (annars läcker svaret). Ett namn som står på provstenen och på andra stenar finns redan i
  modellen genom träningsstenarna. Peterson kan därför bara tillföra namn som Rundatas vikingatida stenar utanför
  vecket inte har, och former som tm22 missade för att inläsningen var dålig. Provet mäter just det.
- I app_f0 är 70 av 324 luckor namn (is_name).

## Mekanismen (densamma som tm22, inget nytt)
`namn.json` byggs om ur den nya tabellen med tm22:s regler (bygg_lexikon.py, avsnittet N4 Peterson): varje form i
kolumnen `keys` som består av vanliga bokstäver (PLAIN) och har minst tre tecken blir ett namn till namnmodellen
(`extra_names`). Signa för läckspärren: unionen av kolumnen `signa` (kontrollerade) och de signa som tm22:s reguljära
uttryck hittar i `block`. Ett namn utesluts i ett veck om någon av dess signa är en provsten där. Ingen vikt väljs: namnen
läggs in med samma vikt som namnmodellens egna namn, som i tm22. Den gamla namn.json sparas som
`namn_tm22.json`. Byggskript: `utdata/runlm_forfining/tm23/bygg_namn.py`.

## Provet
Maskeringsprovet med appens inställning (samma flaggor som tm22_kor.sh, `APP=…`) med `--names_lit`, veck 0–4, mot
app_f0–f4 (samma luckor), jämfört parvis per lucka, bara runstenar. Alla fem veck räknas (ingen vikt väljs, så veck 0
behövs inte som valveck). Kontroll först: en körning utan `--names_lit` på veck 0 ska ge samma val som app_f0 (som i
tm22); annars stopp.

## Mått och gränser
**Huvudmått (namnen):** luckor där det rätta ordet är ett namn (is_name), hela namnet rätt (word_ok), båda slagen
(inne i ord, helt ord) sammanslagna: vunna och förlorade luckor mot app.
**Håller** när alla fyra gäller:
1. fler vunna än förlorade namnluckor över veck 0–4;
2. alla luckor (namn och andra ord, båda slagen): vunna minus förlorade ≥ 0;
3. svar ≥ 95 % (tm19:s kalibrering): inte fler fel än i app;
4. korta luckor (1–2 runor): inte fler nya fel än nya rätt.
Håller provet körs dokumenterade luckor (dok5, 361 luckor) med namnen (runlm_documented_test.py får då flaggan); det får
inte ge färre än 252 rätt eller fler än 2 fel bland svar ≥ 95 %. Först därefter kan namnen slås på i appen som
textmodel-23. Håller provet inte förblir namnen av, och det redovisas som negativt.

## Beskrivande (oavsett utfall)
- Den gamla mot den nya inläsningen på veck 0: namn_f0.json (tm22) mot den nya körningen, namnluckor vunna/förlorade.
- Hur många namn som kom in per veck efter läckspärren, och hur många av de 153 som inte är Rundatanamn.
- Öppna luckor på runstenar (data/textmodel_candidates.json, 112): hur många som får ett nytt namn bland förslagen ≥ 0,5
  med namnen påslagna. Inget facit; bara antal och exempel.
- U 657 (Rundata *houtian*, modellen *halfdan* 0,986 i plan db270b26): vad modellen säger med namnen.

## Vad som inte får göras
Inga namn läggs till eller tas bort för hand. Tabellen och byggreglerna ändras inte efter att något veck har setts.
Ingen vikt prövas. Rundatas normalisering av provstenarna används aldrig som källa.

## Kostnad och ordning
Två veck åt gången (3,2 GB per körning i tm22), ett tungt jobb i taget på datorn; omkring ett dygn.

## Redovisning
`utdata/runlm_forfining/tm23_resultat.md`, METHODS 8.1 (en mening, oavsett utfall), CHANGELOG, bristlistan
(textmodel_open) och news.json bara om namnen slås på.
