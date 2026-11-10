# Vikingarnas omvärld – platser utanför Norden i runstenar, Edda och sagor

Påbörjat 2026-10-28 på Viktors förslag: vilka städer och länder utanför Norden som nämns i vikingatidens texter, räknat.

## Korpusar

| Korpus | Källa | Texter | Ord | Enhet |
|---|---|---|---|---|
| Runstenar (SE, DK, NO separat) | Rundata, engelsk översättning (`data/rundata.json`) | 2 321 / 239 / 66 | – | sten |
| Eddan | `utdata/Edda/edda_karta_texter.csv` (utan Gylfaginning, Skáldskaparmál, Hugsvinnsmál, Sólarljóð; Hávamáls delar sammanslagna) | 34 | 45 000 | dikt |
| Islänningasagor | sagadb.org (Sveinbjörn Þórðarson), normaliserad nutida isländska, public domain; `korpus/islendingasogur/` | 42 | 897 000 | saga |
| Heimskringla | heimskringla.no, Linder & Haggson 1869–72, public domain; `korpus/heimskringla/` (`hk_text.py` tar texten ur den renderade sidan, action=raw är spärrat) | 16 | 243 000 (prosa) | saga |
| Fornaldarsagor | heimskringla.no, Guðni Jónsson & Bjarni Vilhjálmsson 1943–44 (36 sagor och þættir; utgåvan är inte public domain, så texten används bara för räkning och korta citat); `korpus/fornaldarsogur/` | 36 | 342 000 (prosa) | saga |
| Skaldevers | verserna i sagorna, avskilda från prosan i `rakna_platser.py` (sagadb: indragna rader; heimskringla.no: följder om minst fyra korta rader, delade i strofer om åtta rader): `heimskringla_vers` 692, `islanningasagor_vers` 681, `fornaldarsagor_vers` 752 strofer | 2 125 | 53 000 | strof |

Finnur Jónssons *Skjaldedigtning* B (1912–15) finns på Internet Archive (dennorskislandsk03finn/04finn), men OCR:en är dålig (ð→5/b, þ→]?) och den danska översättningen står insprängd; därför används verserna i sagorna i stället. Heimskringla.no har bara ett tiotal skaldedikter.

Heimskringla.no ber att bli krediterad när texterna används: nämn sajten i artikelns källförteckning.

## Ortnamnslistan (`platser.csv`)

En rad per plats med region (öster, väster, söder, Nordatlanten), ett mönster för de fornnordiska texterna och ett
för runstenarnas engelska översättning. Falska träffar som togs bort efter kontroll i `kwic.txt`:
serkir/berserkir (skjorta, krigare), fírar/tírar (män, ära), bjórsalr (Völuspá), í rúm (i säng), frakka (spjut),
vindr (vind), valir (falkar), spánn (träspån), baða (bada), brim (bränning), sax (kniv), skota (skjuta), eista,
tillnamnet jórsalafari, personnamnet Bjarmarr. Garðar ensamt räknas inte (isländskt gårds- och personnamn). Finnar = samer räknas inte.
I Eddan är austrvegr jättarnas mytiska öster.

## Första resultat (2026-10-28, `rakna_platser.py`)

Andel av träffarna öster resp. väster (öster / (öster + väster)):
- svenska runstenar: 123 / 180 = 68 % öster (138 stenar nämner en plats utanför Norden)
- Heimskringla: 300 / 694 = 43 %
- islänningasagor: 89 / 385 = 23 %; Nordatlanten (Orkney, Färöarna, Grönland) i 25 av 42 sagor
- danska och norska runstenar: bara 6 resp. 2 stenar nämner en plats utanför Norden
- Eddan: nästan ingen verklig geografi (Frankrike i Sigurdsdikterna, England en gång)

Serkland: 6 svenska runstenar, 3 kungasagor (Sigurd jorsalafarare, Harald hårdråde), ingen islänningasaga.

## Med fornaldarsagor och skaldevers (2026-10-28)

Östandel (öster / (öster + väster), träffar): svenska runstenar 68 % (58,5 % utan de 25 Ingvarsstenarna, självkontroll 2026-11-10 i `sjalvkontroll/`; den publicerade siffran är 66 %, olika platser per sten, och 58 % utan Ingvar), fornaldarsagor 58 %, Heimskringla prosa 43 %,
Heimskringla vers 38 %, Eddan 38 % (8 träffar), fornaldarsagor vers 36 %, islänningasagor 23 %, islänningasagor vers
12 % (8 träffar), danska runstenar 20 % (5 träffar). Verserna nämner sällan platser: 27 av 692 strofer i Heimskringla.

## Nästa steg

1. Låst analysplan: skrivplats eller tid? Jämför svenska/danska/norska stenar, kungasagor (norska kungar) och
   islänningasagor; räkna per text och per kapitel, bootstrap över texter.
2. Fornaldarsagor och skaldevers är med sedan 2026-10-28. Snorra Edda kan läggas till.
3. Karta per korpus.
4. Förbehåll i texten: att en plats nämns är inte att någon reste dit; sagorna är litteratur; runstenarna minns
   främst dem som dog borta.

## Uppföljning: samtidssagorna (påbörjad 2026-10-28, inte räknad)

Hypotesen ”österled blev forntid” förutsäger att samtidssagorna – skrivna på Island på 1200-talet om samtiden – ser
mot väster och söder, inte mot öster. Fritt tillgänglig ren text (heimskringla.no, Guðni Jónssons Sturlunga saga 1948;
används bara för räkning): Þorgils saga ok Hafliða, Hrafns saga Sveinbjarnarsonar (Sturlunga-versionen), Svínfellinga
saga, Sturlu þáttr, Arons saga och Smákaflar ok brot, i `korpus/samtidssagor/` (cirka 51 000 ord). Saknas: Íslendinga
saga, Þórðar saga kakala, Þorgils saga skarða, Sturlu saga, Prestssaga och Guðmundar saga dýra (inte på heimskringla.no);
biskopssagorna likaså. Vigfússons utgåva 1878 finns som OCR på Internet Archive men ð, þ och accenter är förstörda,
vilket skulle missa östliga namn (Garðaríki, Miklagarðr) men inte västliga (England, Orkney) – oanvändbar utan
handgranskning. Þórðar saga kakala (White 2020, CC BY-NC-SA 4.0) ligger bakom en bot-kontroll hos OAPEN och måste
laddas ner för hand. Guðmundar saga Arasonar på is.wikisource är Arngríms version (1300-talet) och räknas inte som
samtidssaga. Planen låstes (analysplaner/2026-10-28-vikingarnas-omvarld-samtid.md, 8e94f0b) och kördes samma dag: **för få träffar** (Σ(Ö + V) = 1, spärren var 20). Beskrivande: inga platser i öster; Skottland, Rom, Jerusalem, Orkney, Grönland. Se resultat_samtid.md.
