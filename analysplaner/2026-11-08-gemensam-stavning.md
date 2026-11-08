# Analysplan: var fanns en gemensam stavning? Stavningens enhetlighet i de vikingatida landen

Skriven och låst 2026-11-08, innan något av proven nedan har räknats. Viktor 2026-11-08: "1 och 3" (förslag 3: var
kunde man skriva – stavningen som mått på om skrivandet var ett hantverk eller en vanlig färdighet).

## Frågan
Stavade ristarna i ett land på samma sätt – en gemensam norm, lärd eller spridd genom verkstäder – eller stavade var
och en efter sitt eget öra? Måttet säger inget om hur många som kunde läsa; det mäter hur enhetlig skriften var.

## Känt före låsningen
Ristarnas stavning är studerad förut, främst för enskilda ristare och för Uppland (bland andra Thompson 1975 om
uppländsk runografi; Williams 1990 om åsrunan; Lagman 1990 om de stungna runorna; Bianchi 2010; Spurkland 2004 om
runkunnighet). **Inget av dessa verk är läst för den här planen**; de ska läsas innan något skrivs om nyheten i
resultatet. Palm 1992 redovisar regional variation i språkliga drag. Vitkis ortografiska stilometri
(`src/orthography.py`) parar translitterering och normalisering ord för ord; den används här.

## Data
- **Stenar:** Vitkis korpus (`data/cache/r/corpus/510ebfb3…/corpus.csv`), vikingatida runstenar i det vikingatida
  Sverige (inte Skåne, Halland, Blekinge, Bohuslän), med Rundatas translitterering och normalisering parade ord för ord
  (`orthography.features`: samma antal ord), utan egennamn och skadade ord.
- **Ord:** normaliserade ordformer (små bokstäver) som finns på minst 10 stenar i korpusen.
- **Stavning:** den translittererade formen utan textkritiska tecken och bindrunetecken (som i `orthography.features`);
  *r* och *R* hålls isär.
- **Ristare:** korpusens ristare; yrkesristare = minst 10 stenar (som i Norgestudien).
- **Land:** det vikingatida landet (`region_old`: folkland, små land, tredingar; annars landskapet). Land med minst 30
  stenar som har minst ett vanligt ord.

## Måttet
**Enhetlighet** A för en grupp stenar: för varje vanligt ord, bland alla par av stenar i gruppen som båda har ordet,
andelen par som stavar det likadant; summerat över orden (likadana par / alla par). Par där båda stenarna är
tillskrivna samma ristare räknas inte, så att en ristares egen vana inte räknas som en gemensam norm. A är sannolikheten
att två stenar från landet stavar ett vanligt ord likadant; den beror inte på hur många stenar landet har.

## Prov
**H1 (landen skiljer sig).** Spridningen av A mellan landen (variansen, vägd med antalet par). Nollhypotes: landet
spelar ingen roll – landsetiketterna blandas om mellan stenar i samma stilgrupp (RAK, Fp, Pr1–Pr5, utan stilgrupp),
9 999 gånger. **Håller** om p < 0,05. Per land redovisas A med 95 % intervall (stenarna dras om, 2 000 gånger).
**H2 (stavningen blev enhetligare med tiden).** Inom landen: A bland par av sena stenar (Pr3–Pr5) mot par av tidiga
(RAK, Fp, Pr1, Pr2). Nollhypotes: perioden blandas om mellan stenar i samma land, 9 999 gånger. **Håller** om
skillnaden sen − tidig > 0, ensidigt p < 0,05.
**H3 (beskrivande).** Inom landen: A bland par där båda stenarna är av yrkesristare, par där ingen är det, och blandade
par – hur mycket av enhetligheten verkstäderna står för.

## Tolkning (bestämd nu)
Håller H1 fanns det land med en gemensam stavning och land där var och en stavade på sitt sätt; kartan redovisas med
osäkerheten. Ett högt A kan komma av undervisning eller av verkstäder (H3 visar hur mycket), ett lågt av många
ristare utan gemensam skola eller av dialektskillnader inom landet; vi skiljer inte dem åt med det här måttet och
säger det. Håller H2 blev stavningen enhetligare under 1000-talet. Håller H1 inte skiljer sig landen inte mer än
stilgrupperna förklarar, och kartan redovisas inte som fynd.

## Redovisning
`utdata/gemensam_stavning/`: `data.py` (paren), `prov.py` (H1–H3), `resultat.json`, `resultat.md`.
