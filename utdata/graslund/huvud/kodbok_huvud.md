# Kodbok: huvudmodulen (version 3b, 2026-11-25, efter pilot 1)

Kompletterar kodbok v2 (`utdata/nya_ristare/ornamentik/kodbok.md`) för rundjurets huvud och svans. Läsaren får **utsnitt** i
full upplösning av varje huvud och varje svans- eller bandände, och hela stenens bild för sammanhang. Koda **huvudet på det
största rundjuret** (det som bär mest av runtexten). Har stenen flera rundjur med olika huvuden: koda det största och skriv
de andra i `kommentar`. Använd bara kunskap om det som syns. `osäkert` när du inte kan se draget i utsnittet.

## Före kodningen
Öppna först schemat `utdata/graslund/huvud/schema_profilhuvud.png` (absolut sökväg i uppdraget): det visar var ögat,
käkarna, nackfliken och läppfliken sitter på ett profilhuvud. Hitta alltid **ögat först**, sedan käkarna (nosen pekar bort
från kroppen); därefter är nacken bakom ögat och läpparna vid käkspetsarna. Utsnitten är förstorade – titta noga på varje
linje som går ut från huvudet: är den bandet (fortsätter in i kroppen) eller en fri flik (slutar i spets eller spiral)?

## Hur man läser ett profilhuvud
Ett rundjurshuvud i profil har ett öga, en överkäke och en underkäke (läppar), och ofta flikar:
- **Nackflik:** ett utskott eller en tunga som går bakåt från huvudets bakkant (nacken). Kan vara kort, lång eller rulla upp
  sig i en spiral. Förväxla inte med bandets fortsättning: nackfliken är fri och slutar i en spets eller spiral.
- **Läppflik:** ett utskott från käkens spets (främst överläppen, ibland underläppen) som går framåt eller böjer sig.
  Den kan sluta i en spiral. Förväxla inte med tänder eller tunga.
- **Mun:** om käkarna griper om något (bandet, en svans, ett annat djur) är det `biter`; isärgående käkar utan att gripa är
  `oppen`; käkarna ihop är `stangd`.
- **Nos:** överkäkens spets – `rundad`, `spetsig`, eller `uppvikt` (spetsen böjer uppåt).
- **Öga:** `rund` (cirkel eller punkt) eller `mandel` (spetsigt åt minst ett håll – också droppformat räknas som mandel).

Ett huvud **sett ovanifrån** (masklikt, två ögon symmetriskt, nosen rakt fram) är `uppifran`; då kodas nackflik och läppflik
som `ingen` om inga flikar syns, och `nos` efter formen.

## Fält
`huvud_vy` profil / uppifran / inget_huvud · `oga` rund / mandel / inget_synligt · `nackflik` ingen / kort / lang /
spiral · `lappflik` ingen / en / bada / spiral · `mun` biter / oppen / stangd · `nos` rundad / spetsig / uppvikt ·
`svans` rak / spiral / ogla / kluven / flatad / ingen_svans · `fotter` inga / spiral / ogla / taer · `kommentar`.
Alla fält kan vara `osäkert`.
