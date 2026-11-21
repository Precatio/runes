# Ormen och draken – resultat (fördjupning 5 i serien Nordiska väsen)

Enligt `analysplaner/2026-11-21-ormen-och-draken.md` (låst 15ce39f). Räknat 2026-11-21 med `analys.py`. Siffrorna finns i
`matt.json`, kontrollen i `kontroll_resultat.json` och Sigurdsstenarna i `o4_sigurd.json`.

## Klassningen
- **Alla 412 träffar** klassades för hand: 278 på *dreki* och 134 på *ormr*. Resultat: skepp 217, drake 115, orm 37, annat
  30, kenning 9 och bild 4.
- **Annat** är främst tillnamnet *Sigurðr ormr í auga* ("orm i ögat") och listorna över ord i Skáldskaparmál.
- **Oberoende blind kontroll:** 50 stratifierade träffar, omklassade av en separat instans av samma språkmodell. Den
  överensstämde i **50 av 50** (krav ≥ 85 %). Den listade åtta gränsfall, alla redovisade i klassningen. Exempel:
  - Nidhöggs ormar och ormarna i Nåstrands sal, som är mytiska men av vanligt slag;
  - helvetesormen i Hrafns saga, klassad som drake;
  - en drömorm som tyds som ett skepp, i Hrómundar saga.

## O1 Vad orden betyder
| textgrupp | ord | drake | skepp | orm | övrigt |
|---|---|---|---|---|---|
| eddadikterna | *dreki* (1) | 1 | – | – | – |
| eddadikterna | *ormr* (17) | 7 | – | 9 | bild 1 |
| prosan | *dreki* (273) | 57 | **212** | – | bild 2, kenning 1, annat 1 |
| prosan | *ormr* (102) | 48 | 1 | 25 | annat 25, kenning 2, bild 1 |
| sagornas vers | *dreki* (4) | – | 4 | – | – |
| sagornas vers | *ormr* (15) | 2 | – | 3 | kenning 6, annat 4 |

- **I sagornas prosa** betyder *dreki* ett skepp i 78 % av fallen (212 av 273).
- **Eddadikternas enda *dreki*** är Nidhögg i Völuspá, *inn dimmi dreki fljúgandi*. Annars heter draken *ormr* i
  eddadikterna, Fáfnir lika väl som Midgårdsormen.
- **Draken som djur, *dreki*,** finns i prosan i Gull-Þóris saga, Bjarnar saga Hítdælakappa, Eireks saga víðförla, Yngvars
  saga víðförla, Ketils saga hængs, Hálfdanar saga Eysteinssonar, Sörla saga sterka (en förvandling), Völsunga saga,
  Sögubrot (drömmar) och Ynglinga saga (Skytien).
- **Draken som bild:** i Völsunga saga är draken målad på Sigurds sköld (*skrifaðr á einn dreki*) och märkt på alla hans
  vapen, och sagan säger att han dödade *þann mikla dreka, er Væringar kalla Fáfni*. I Óláfs saga helga är Olavs märke
  *ormr*.

## T1 Tar lånordet över? (låst) – obestämt
- **Underlag:** eddadikterna har bara 8 draketräffar i 5 dikter (krav ≥ 10). Prosan har 105 i 20 texter.
- **Beskrivande:** i eddadikterna är 1 av 8 drakar *dreki* (12 %), och i prosan 57 av 105 (54 %).
- **Bara Fáfnirsberättelsen:** eddadikterna har 4 draketräffar, alla *ormr*. Prosan har 28 i 4 texter. Det är också
  obestämt.
- **Läsning:** riktningen är tydlig men inte prövad. Planens gräns hindrar en slutsats.

## O2 Namngivna ormar och drakar
- Fáfnir: eddadikterna 51, prosan 79 och sagornas vers 5.
- Midgårdsormen och Jörmungandr: prosan 21, eddadikterna 1.
- Nidhögg: prosan 6.
- Góinn och Móinn: 4 i eddadikterna och 4 i prosan.

## O3 Runstenarna
- **I texterna:** inga träffar på *dreki* eller *ormr*.
- **Ormslingan:** 780 av 1 038 svenska runstenar med säker stilgrupp (**75 %**) har en orm med huvud (stilgrupp Fp eller
  Pr1–Pr5).
- **Per landskap:** Uppland 92 %, Södermanland 77 %, Öland 73 %, Östergötland 33 %, Västergötland 27 % och Småland 13 %.
- **Förbehåll:** stilgruppen definieras av ormen själv, så måttet säger var ormstenarna står, inte när de kom.

## O4 Sigurdsstenarna
Rundata nämner Sigurdsbilder på fem svenska ristningar: Ramsundsberget (Sö 101), Göksten (Sö 327), Drävle (U 1163),
Årsunda (Gs 9) och Ockelbo (Gs 19, förstörd). Ingen av deras texter nämner draken.

## Varifrån draken kom
Det besvaras inte av räkningen. Ur litteraturen, inte prövat här: *dreki* är ett lån från latinets *draco* (via
fornengelska *draca* och fornsaxiska *drako*), medan *ormr* och *linnormr* är inhemska ord. Det som mätts här stämmer med
att lånordet hör till den yngre, skrivna prosan. I eddadikterna, med Völuspás Nidhögg som enda undantag, är draken en
*ormr*.
