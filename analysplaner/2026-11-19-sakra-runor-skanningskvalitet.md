# Analysplan: säkra runor mot hela slingan, och hur måtten tål sämre skanningar

Skriven och låst 2026-11-19, innan något av proven nedan har räknats. Viktor 2026-11-19: "en risk med
huggspårsanalysen är att olika kvalitativa scanningar kommer att ge olika resultat"; "behöver vi mäta hela raden,
räcker inte ett antal säkra runor som verktyget kan identifiera, och mäta spåren i dessa?"; "ja lås planen".

## Känt före låsningen
- **Täthet och bergart styr måtten** (METHODS 2e, Rak-replikeringen): efter groove-4 korrelerar spårbredden r 0,26 med
  punkttätheten. Bottenradien är opålitlig (ICC 0,08) och används inte här. Kitzler Åhfeldts Rak 1/Rak 2 har inte gått att
  återskapa (groove-4 till groove-7). Teknikmåtten har inte visats slå en gissning efter bergart.
- **Överensstämmelse mellan runorna på samma sten** (ICC i groove-7:s runsammanfattning): M 15 omkring 0,27 för
  V-vinkeln; Sö 131 0,30 för vinkeln, 0,60 för djupet och 0,33 för bredden. Ur det räknades (Spearman–Brown) att 10 runor
  ger omkring 0,79 och 20 runor omkring 0,88. Bara räknat för att svara Viktor, inte prövat.
- **Indelningen i runor** (groove-7) delar ofta i fler runor än texten har, till exempel M 15 med 66 mot 42 och Sö 131
  med 157 identifierade och 99 mätta. Resultatfilerna har inget streck-id (stroke_id saknas), så stavarna kan inte skiljas
  från bistavarna i den här omgången.
- Inget av proven nedan är räknat. Ingen mätning på försämrade skanningar är gjord.

## Material
De 37 skanningarna av Södermanlands runstenar som Laila Kitzler Åhfeldt gjort (ATOS, Runristandets dynamik,
doi 10.5281/zenodo.11951255, CC BY 4.0), mätta med groove-7 i `utdata/Rak/referenser_g7/`. Alla stenar med ritade
slingor ingår. Det är en enda skanningsserie, så skillnader mellan skannrar finns inte i materialet. De efterliknas
genom försämringarna nedan.

## Försämringarna
Varje skanning mäts om fyra gånger, med samma vy (normalen och upp-riktningen ur den sparade mätningen), samma ritade
slingor och samma parametrar som originalmätningen i övrigt:
- **D0, originalet:** ingen förändring. Det är en kontroll av kedjan. Stenarnas medel ska ligga inom 0,5° (vinkel) och
  0,1 mm (djup och bredd) från de sparade värdena, annars rättas kedjan innan något prov räknas, och det redovisas.
- **D1, brus:** varje hörnpunkt flyttas längs sin normal med normalfördelat brus, σ = 0,15 mm. Slumpfröet kommer ur den
  här planens kontrollsumma.
- **D2, grövre:** analysens rutnät 1,2 mm i stället för skanningens egen upplösning (resolution_mm), som en grövre
  skanning.
- **D3, båda:** D1 och D2 tillsammans.

## Två sätt att räkna ett stenmått
- **H, hela slingan:** medelvärdet över alla godkända snitt i runslingorna, som i dag.
- **S, säkra runor:** runor med minst 4 godkända snitt. Per sten tas de 15 sådana runor som har flest snitt (vid lika:
  ordningen längs slingan). Stenmåttet är medelvärdet av runornas medianer. En sten med färre än 8 säkra runor får inget
  S-mått och redovisas.
Urvalet bestäms av antalet snitt, inte av måttens värden. Det görs om för varje försämring, så som verktyget skulle göra.

**Mått:** V-vinkeln (apex_vinkel_deg), spårdjupet och spårbredden.

## Prov
**R1, huvudprovet: tål S sämre skanningar bättre än H?** För varje mått, sätt (H, S) och försämring (D1–D3): ICC(2,1),
absolut överensstämmelse mellan originalets och den försämrade skanningens stenmått, över de stenar som har både H- och
S-mått i alla fyra körningarna. Teststorheten är medelvärdet av skillnaden ICC(S) − ICC(H) över de 3 × 3 kombinationerna.
95-procentsintervall ur 2 000 omdragningar av stenar, med slumpfrö ur kontrollsumman. **Håller** när intervallet ligger
över 0 och skillnaden har samma tecken för minst två av de tre måtten.

**R2, delprov: skiljer S ristarna åt minst lika bra som H?** Stenar med en säker ristare i Rundata, där ristaren har
minst två stenar i materialet. Mått: standardiserat avstånd (de tre måtten z-skalade över stenarna i originalet) mellan
par med samma ristare minus par med olika ristare. Bara par på samma bergart (Rundatas material, familjer som i
`src/geology`), så att bergarten hålls konstant. p ur omblandning av ristarna inom bergarten, 10 000 varv, för S och H var
för sig, på originalet. **Håller för S** när S:s avstånd mellan samma ristare är mindre än mellan olika ristare med
p < 0,05. Är H:s skillnad större än S:s redovisas det som att S skiljer sämre.

**Beslutsregel:** S blir appens förvalda stenmått för huggspåren om R1 håller och R2 inte visar att S skiljer ristarna
sämre än H. Annars behålls H, och S redovisas som ett alternativ.

## Beskrivande (utan prov)
- Hur många säkra runor varje sten har, och hur många stenar som får S-mått.
- Spearman–Brown-kurvan: tillförlitligheten för medelvärdet av k runor (k = 1–30) ur runornas ICC per sten.
- Hur mycket varje mått flyttar sig i medel mellan originalet och D1–D3, i grader och millimeter.
- Exempel: den sten där H och S skiljer sig mest.

## Vad som inte skrivs
Försämringarna efterliknar sämre skanningar men är inte riktiga skanningar med en annan skanner; det sägs. Ett S som
tål försämringen bättre betyder inte att det mäter ristarens hand. R2 är litet, eftersom få ristare har två eller fler
stenar i materialet, och det redovisas med antal par.

## Utdata
`utdata/sakra_runor/kor.py` (mätningarna, en sten åt gången) → `utdata/sakra_runor/matningar/<signum>_<D>.json`;
`utdata/sakra_runor/analys.py` → `utdata/sakra_runor/resultat.json` och `resultat.md`. Skanningarna stannar på
/Volumes/2TB utanför versionshanteringen.
