# Alverna – resultat (fördjupning 2 i serien Nordiska väsen)

Enligt `analysplaner/2026-11-21-alverna.md` (låst 5d305b6) och tillägg 1 (1b50c3d). Räknat 2026-11-21 med
`utdata/alverna/analys.py`; alla siffror i `matt.json`. Träffarna med textutdrag och handklassningen ligger i
`data/cache/alverna/` (utanför git). Texterna är desamma som i den första väsenstudien.

## Insamling och klassning
- 443 träffar på alf-/álf-formerna, alla klassade för hand: 320 personnamn, 64 väsen (varav 3 Völund-epitet),
  35 annat, 17 ortnamn, 4 kenningar och 3 världsdel.
- *Annat* är framför allt *Alföðr* (Oden, "allfadern", förleden *al-*), *álfröðull* (solen), *álfrek* (avträde) och
  *alfari*/*alfarið* (helt och hållet).
- **Tillägg 1:** mönstret missade *Ljósálfar* och *Dökkálfar*. Det lades till innan något räknades och gav 8 nya
  träffar (6 väsen, 2 ortnamn).
- **Oberoende blind kontroll:** 40 slumpade träffar klassades om av en separat instans av samma språkmodell, utan
  tillgång till den första klassningen. Resultatet blev 40 av 40 lika (krav ≥ 85 %). Stickprovet består mest av
  personnamn, som är lätta att klassa. De svåra fallen (kenningar, väsen i vers) är få i det.
- **Rättelse av den första studien:** Guðni Jónssons Eddautgåva stavar *alfar* utan accent. Den första studiens
  ordlista krävde *álf-* och missade därför de 31 alvträffarna i eddadikterna (och 3 Völund-epitet). Den studiens
  huvudtest gällde sagorna och påverkas inte, men alvsiffran där ("ett par dussin") var för låg.

## A1–A2 Var alverna finns (väsen, inklusive Völund-epitet)
- Eddadikterna: **31** träffar i 11 av 34 dikter, **6,5** per 10 000 ord.
- Gylfaginning: 8 (4,5). Skáldskaparmál: 5 (2,3).
- Fornaldarsagornas prosa: 13 i 6 av 36 sagor (0,38). Deras vers: 2.
- Islänningasagornas prosa: **2**, båda i Kormáks saga (0,02 per 10 000 ord, alltså en träff på en halv miljon ord).
  Deras vers: 1 (Grettis saga, "álfa kind og óvættum").
- Heimskringlas prosa: 1 (Sigvats alvablot). Dess vers: 1 (samma alvablot i Sigvats strof).
- Samtidssagorna: 0. Runstenarnas texter: 0.

Alverna hör alltså till myten. Utanför Eddan och Snorre finns de nästan bara i fornaldarsagorna.

## A3 Kulten
Tre ställen, alla tydliga:
- Kormáks saga: en kulle "er álfar búa í", och rådet att "gera álfum veislu" med köttet av en tjur, mot ett sår.
- Óláfs saga helga (Heimskringla): Sigvat nekas husrum i Götaland eftersom husfrun säger att de håller *álfa blót*.
- Sigvats egen strof om samma kväll (*álfa blót*).

## A4 Ljusalver och dökkalver
Bara hos Snorre:
- Gylfaginning: *Ljósálfar* (3), *Dökkálfar* (2) och *Svartálfaheimr* (1);
- Skáldskaparmál: *Svartálfar* (1) och *Svartálfaheimr* (1).

I Skáldskaparmál är det dvärgen Andvari som bor i Svartalfheim, och det är *svartálfar* som gör Sifs guldhår, alltså
dvärgarnas verk. Uppdelningen i ljus- och dökkalver förekommer inte i någon annan text i korpusen.

## A5 Namnen
- **Sagorna:** 314 namnträffar med förleden Alf-/Álf-. De vanligaste är Álfr/Álfur, Álfhildr, Álfgeirr och Alfífa (den
  engelska drottningen Ælfgifu). Namnen är alltså vanliga i sagornas värld, Norge och Island.
- **Runstenarna:** Alf-namn på **7 av 2 321** svenska runstenar (0,3 %): Alfdís (Sö 115), Alfhildr (Sö 254), Alfketill
  (Sö 257), Alfríkr (U 37), Alfgeirr (U 515), Alfgautr (U 573) och Álfrún (Hs 10). Tre står i Södermanland, tre i
  Uppland och en i Hälsingland.
- **Som jämförelse:** Tor-namn finns på 335 stenar (14,4 %) och As-namn på 168 (7,2 %). Inget test.

## A6 Ortnamnen
I Svenskt ortnamnslexikon nämner 6 artiklar *alv* i förklaringen, och **ingen av dem tolkar namnet som ett alvnamn**.
Alla gäller ordet *alv*, "jordlager närmast under matjorden": Alva och Alvaret, och Alvhem, där SOL anser att förleden
"möjligen" är just jordlagret. Läsningen finns i `a6_lasning.json`.

## T1 Alvernas sällskap (låst)
Underlag: 44 alvträffar i 13 texter i Eddan (dikterna och Snorre) och 20 i 12 texter i sagorna. Fönster ± 25 ord.

| mått | Eddan | sagorna | skillnad (95 %) | Holm-p | utfall |
|---|---|---|---|---|---|
| T1a gudaord nära alven | 68,2 % | 0,0 % | +68,2 (37,5 – 93,0) | < 0,0001 | **håller** |
| T1b vidunderord nära alven | 40,9 % | 15,0 % | +25,9 (−11,2 – 58,5) | 0,22 | håller inte |

- **Känslighet:** utan Alvíssmál blir T1a 57,6 % mot 0 (31,9 – 88,9) och håller. T1b blir 21,2 % mot 15,0 % och håller
  inte. Med fönstret ± 10 ord blir T1a 65,9 % mot 0 (37,5 – 89,6) och håller, medan T1b inte gör det.
- **Dvärgarna** (redovisas för sig): 45,5 % i Eddan och 5,0 % i sagorna.

**Utfall:** i Eddan står alverna nästan alltid tillsammans med gudarna, i formeln "æsir ok alfar" och i
uppräkningarna av världens folk. I sagorna har de förlorat det sällskapet helt: inte en enda av de 20 alvträffarna har
ett gudaord inom 25 ord. Däremot har de inte flyttat över till trollens sida. Vidunderorden är inte säkert vanligare
runt alverna i sagorna än i Eddan, och det antagande som skissades före låsningen håller alltså bara till hälften.

## Vad det betyder och inte betyder
- Alverna är ett mytens folk. I texterna om Islands och Norges historia nästan saknas de, och där de finns tar
  människor emot dem med offer och gästabud (Kormák, Sigvat). De står inte bredvid gudarna där.
- I Sverige syns alverna varken i ortnamnen (enligt SOL) eller på runstenarna, där de bara förekommer i sju personnamn.
- Ett sällskap i texten är inte tro: det visar hur berättarna ordnade sin värld när de skrev, på 1200–1300-talen.
- Den blinda kontrollen säger mest om de lätta fallen. Gränsfallen (kenning eller väsen i vers) är få och står listade
  i klassningen.
