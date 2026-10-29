# Analysplan: Namngivning i familjen – ärvde barnen namnled på runstenarna?

Låst 2026-10-29, innan något nedan har räknats. SHA-256 i `analysplaner/2026-10-29-namngivning-i-familjen.sha256`.
Kod `utdata/namngivning/analys.py`, resultat `utdata/namngivning/resultat.md`.

## Bakgrund
I germansk namnskick fick barn ofta ett namnled eller samma begynnelseljud som en förälder (variation och
allitteration: Holmsten → Holmfast). I de medeltida breven bar döttrarna oftare kristna namn än fäderna
(analysplaner/2026-10-29-namnen-som-levde-kvar.md). Frågan här: syns det nordiska namnskicket på runstenarna, och
försvagas det när kristendomen kommer? Sett före låsningen: entitetsmodellens relationsräkning (far 959, bror 275,
son 225, mor 27 …) och ett exempel (U 135, där sonen Eysteinn bär faderns namn); inga namnpar har jämförts.

## Material
Svenska vikingatida runstenar i korpus 3f58e9339191761e. Namn = entitetsmodellens namnnyckel (`src/entities.py`).
- **Förälder–barn-par:** relationerna far/mor (a är b:s far/mor: förälder a, barn b) och son/söner/dotter (a är b:s
  son: förälder b, barn a); dessutom fallet där en resare har samma namnnyckel som den döde fadern/modern/sonen på
  samma sten (namnet upprepat – modellen hoppar annars över det).
- **Syskonpar:** bror/bröder/syster-relationer och barn till samma förälder på samma sten.
- Ett par räknas en gång per socken (samma namnpar i samma socken = samma familj, t.ex. Jarlabankes stenar).

## Namnled och allitteration
- **Namnled:** en namnnyckel delas i förled + efterled där båda leden finns i minst tre andra namnnycklar i korpusen
  (delningen med störst minsta antal); annars är namnet enledat och hela namnet är dess led. **Delat led:** paret har
  något led gemensamt (oavsett plats) eller samma namn.
- **Allitteration:** samma begynnelseljud; alla vokaler (a, e, i, o, u, y, ø, æ, ǫ) allittererar med varandra, *th* = þ.

## Test (Holm över H1–H5, α = 0,05)
Nollmodell för H1, H2 och H5: barnets (andra syskonets) namn blandas om bland paren inom samma landskap, 9 999 gånger.
- **H1 Delat namnled, förälder–barn:** andelen par med delat led är större än vid omblandning (ensidigt).
- **H2 Allitteration, förälder–barn:** andelen allittererande par är större än vid omblandning (ensidigt).
- **H3 Över tid:** överskottet i delat led (observerat minus väntat per par, väntat ur omblandning inom landskap ×
  tidsskikt) är mindre för sena stenar (Pr3–Pr5) än för tidiga (RAK, Fp, Pr1–Pr2). Statistik: skillnaden i
  medelöverskott; nollfördelning genom att blanda etiketten tidig/sen bland paren inom landskapet; tvåsidigt.
- **H4 Kristna stenar:** samma som H3 med etiketten kristen markör (`cat_kristen`) ja/nej; tvåsidigt.
- **H5 Syskon:** andelen syskonpar med delat led är större än vid omblandning (ensidigt).
**Håller:** Holm-p < 0,05 och p < 0,05 åt samma håll i båda halvorna (stenarna delade socken för socken som i
change.R). **Antydan:** Holm-p < 0,05 utan halvorna, eller okorrigerat p < 0,05.

## Beskrivning (prövas inte)
Vilka led som oftast går i arv; hur ofta sonen bär faderns hela namn; kristna namn (Johan, Maria, Nikulas …) i paren;
mor–barn mot far–barn; allitteration över tid.

## Förbehåll
Entitetsmodellens relationer är inte felfria (kontrollerade mot handkodning i människomodulen). Leddelningen är
datadriven och grov (hypokoristiska former som Holmi räknas som enledade). Barnen på stenarna är oftast de vuxna
resarna, födda en generation före stenen; tiden gäller alltså namngivningen omkring 30–50 år före stilgruppen.
