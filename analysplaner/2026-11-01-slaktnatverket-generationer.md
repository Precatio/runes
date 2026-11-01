# Analysplan: släktnätverket, steg 2b – följer stilgrupperna generationerna?

Skriven och låst 2026-11-01, innan provet nedan har räknats. Viktor 2026-11-01: "fortsätt utan att vänta på mina
godkännanden" (efter rekommendationen att släktnätverket får en enda skarp, låst fråga på Williams grupper och våra
länkar).

## Frågan
Den som reser en sten lever när den reses. Står samma person som död på en annan sten, är den stenen alltså rest senare.
Det är en ren logisk tidsordning som inte bygger på ornamentiken. Följer Gräslunds stilgrupper (RAK, Fp, Pr1–Pr5) den
ordningen över alla släktsamband vi känner, så att stenen över den döde oftare har en senare stilgrupp än stenen han
eller hon själv reste?

Prövningen gäller två saker på en gång: stilkronologin och att länkarna verkligen gäller samma person. Faller provet kan
felet ligga i vilken som helst av dem. Håller det stöder det båda. Gräslunds kronologi bygger på ornamentikens
typologi. Enskilda släkter har diskuterats mot den, till exempel Jarlabankes stenar (Larsson 1996, *Fornvännen*), men en
genomgång av alla släkter i Williams förteckning har vi inte hittat.

## Vad som är känt före låsningen
En räkning per stenpar (inte per person, utan halvor eller steg) har gjorts för att se om materialet räcker. Den räknade
alla Williams par plus appens 70 säkra länkar, med danska stenar och osäkra par. Av 63 stenpar med stilgrupp på båda
stenarna och en person som är resare på den ena och död på den andra hade stenen över den döde senare stilgrupp i 31, lika
i 24 och tidigare i 8. Ingenting annat har räknats.

## Data
- Korpus `e83202e01a5e6d27`; `src/linking.stones` (runstenar enligt projektets regel, svenska landskap enligt
  `utdata/slakt/steg2a.py`).
- **Paren:** Williams 1990 säkra par mellan runstenar (`utdata/slakt/williams1990_bilaga.json`, `sure` = sant) och appens
  61 svenska säkra länkar (`data/links.json`, q < 0,1, inga motsägelser, modell M2).
- **Samma person:** samma namnnyckel (`names`, alltså inte ristare och inte osäkra läsningar) på båda stenarna i ett par.
  Personerna slås ihop över paren som i steg 2a (union–find över (sten, namnnyckel)). En namnnyckel med två roller på
  samma sten används inte där.
- **Roller:** `resare` på en sten och `minnes` (den döde) på en annan. `nämnd` används inte.
- **Stilgruppens rang:** RAK 0, Fp 1, Pr1 1, Pr2 2, Pr3 3, Pr4 4, Pr5 5. Ett intervall (”Pr3 - Pr4”) får mittvärdet.
  Tillägget ”[Gräslund muntligt]” tas bort. En stilgrupp med ”?”, KB och tomt räknas inte.

## Huvudprovet
En röst per person: personer med minst en resarsten och minst en minnessten, båda med stilgrupp. Rösten är tecknet av
(medelrang för minnesstenarna − medelrang för resarstenarna): *senare*, *lika* eller *tidigare*. Exakt teckentest,
ensidigt, bland personer som inte är lika. Provet **håller** om senare > tidigare och p < 0,05.

## Stegen (Fullt prövat kräver att alla håller; annars Delvis prövat med de steg som faller uppräknade)
1. **Halvorna:** släkterna (sammanhängande stenar över paren) sorteras efter sitt minsta signum och delas varannan. I
   båda halvorna senare > tidigare och p < 0,05.
2. **Bara Williams:** bara Williams säkra par, utan appens länkar.
3. **Utan Jarlabankes släkt:** släkten som innehåller U 164 räknas inte (den har diskuterats mot kronologin, Larsson
   1996).
4. **Bara fasta stilgrupper:** inga intervall.
5. **Med Williams osäkra par:** även par där en sten står inom hakparentes hos Williams.
6. **Omblandning:** stilrangerna blandas om 9 999 gånger mellan de stenar som ingår, inom landskapet; måttet är antalet
   senare − antalet tidigare. Ensidigt p < 0,05. Slumpfrö 2026.

## Beskrivande (prövas inte)
- Andelen lika: hur ofta reser någon en sten och får en egen inom samma stilgrupp.
- Avståndet i år mellan stilgruppernas mittår (`src/styles.py`) för personerna, median och kvartiler.
- Alla personer med *tidigare*, med stenar, stilgrupper och ristare, som en öppen lista för runologer: där säger antingen
  stilgruppen eller länken emot släktlogiken.

## Vad som inte får göras
Rangskalan, rollerna, paren och gränserna ändras inte efter körningen. Faller huvudprovet redovisas det som ett negativt
resultat.

## Redovisning
`utdata/slakt/generationer.py`, `utdata/slakt/generationer.json`, `utdata/slakt/generationer_resultat.md`.
