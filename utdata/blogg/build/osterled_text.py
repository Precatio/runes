"""Brödtexten till build_osterled.py (sv + en), berättande form 2026-10-28. Importeras av byggaren, som låser alla siffror
och citat; här står bara texten med platshållare som fylls av byggarens variabler."""

BODY_SV = """*ÞæiR foru drængila fiarri at gulli ok austarla ærni gafu, dou sunnarla a Særklandi.*

De for som män fjärran efter guld och gav örnen föda i öster. De dog i söder, i Serkland – de muslimska länderna kring Kaspiska havet.

En mor, Tola, lät hugga de raderna i en sten vid Gripsholm i Södermanland (Sö 179). Stenen restes efter hennes son Harald, bror till Ingvar. Några mil därifrån, vid Lundby, reste två bröder en sten efter en tredje, Skarði: *For austr heðan með Ingvari, a Særklandi liggR sunR ØyvindaR* – han for härifrån österut med Ingvar; i Serkland ligger Øyvinds son (Sö 131). Ingvarståget mot öster omkring 1040 minns på {ING} svenska runstenar. Det är det största minnet av en enda färd som runstenarna har.

Ett par hundra år senare satt någon på Island och skrev om samma man. I *Yngvars saga víðförla*, Ingvar den vittfarnes saga, är han inte längre en son eller en bror som inte kom hem. Han är en sagohjälte som slåss mot drakar och jättar i öster.

Vi ville veta om det är en tillfällighet, eller om det säger något om hur vikingatidens värld mindes. Så vi räknade.

![Runstenen Sö 179]({PHOTO})
Sö 179 vid Gripsholm: ”De dog i söder, i Serkland.” {CREDIT_SV}

:::box Kort sagt
- Vi räknade varje plats utanför Norden som nämns på {SE_N} svenska runstenar och i {N_SAGOR} sagor, och om platsen ligger i öster eller väster.
- De svenska runstenarna ser mot öster: {SE_P} % av platserna ligger där. Men nästan hälften av den övervikten är ett enda tåg, Ingvars – utan det är det {SE_UI_P} %.
- Islänningarna skrev två slags sagor under samma tid. Sagorna om de egna förfäderna ser mot väster, bara {IS_P} % öster. Sagorna om forntiden ser mot öster, {FA_P} % – lika ofta som runstenarna utan Ingvarståget.
- Vår hypotes: på Island hade österleden blivit forntid. Den egna historien låg i väster.
:::

## Två sätt att minnas en värld

Runstenarna och sagorna är de två stora rösterna från den nordiska vikingatiden. De talar på olika sätt. En runsten är ristad av människor som kände den döde, ofta inom några år efter att han dog. En saga är skriven långt senare, på Island, av människor som berättade om förfäder de aldrig hade träffat. Den ena är en minnessten, den andra en berättelse.

Vi gick igenom fyra slags texter: runstenarna i Samnordisk runtextdatabas, ristade under 1000-talet; islänningasagorna, {IS_N} sagor om Islands första generationer, skrivna på 1200- och 1300-talen; kungasagorna i Snorre Sturlassons *Heimskringla*, skrivna omkring 1230; och fornaldarsagorna, {FA_N} sagor om tiden före Islands bebyggelse, nedskrivna på Island under samma tid som islänningasagorna. Sagornas vers räknade vi för sig.

I texterna letade vi efter platser utanför Norden. Varje träff lästes i sitt sammanhang, för fornnordiskan är full av fällor: *serkr* är en skjorta, *rúm* en säng, *frakka* ett spjut och *vindr* en vind. Varje plats räknas en gång per sten eller saga, så att en lång saga som nämner England femtio gånger inte väger tyngre än en kort som nämner det en gång.

{PLATSER_SV}

{MAP_SV}

## Stenarna: en väg som gick österut

Den vanligaste platsen på runstenarna är ingen plats alls. Det är en riktning: *austr*, i öster. Den som läste stenen behövde inte mer. Alla visste vart vägen gick.

När stenarna nämner ett land står två namn nästan jämsides: England på {ENG} stenar, där män tog *gæld*, betalning från de engelska kungarna, och Grekland på {GRE} – det bysantinska riket och dess huvudstad Miklagård. Sedan kommer Garðaríki, rikena längs de ryska floderna, och längst bort Serkland, där Ingvars män dog. Men tyngdpunkten ligger i öster. {SE_P} % av platserna ligger där, och {MAL[0]} av de {MAL[1]} stenar som nämner en plats i öster står i Mälardalen.

Men en stor del av den övervikten är ett enda tåg. Räknar vi bort Ingvarsstenarna – de {ING} som nämner färden, Tolas sten och en sten efter en Ingvar som dog i öster, {UI_N} i allt – ligger {SE_UI_P} % av platserna i öster, troligen mellan {SE_UI_LO} och {SE_UI_HI} %. Stenarna ser då fortfarande något oftare mot öster än mot väster, men inte så tydligt att vi kan utesluta att det var lika ofta. Skillnaden mot islänningarnas sagor om förfäderna, {IS_P} %, står kvar. Det prövade vi i efterhand, efter en plan som vi låste innan vi räknade (2026-11-10).

Det säger något om vilka som rest och vilka som blev kvar. Stenarna restes av mödrar som Tola, av bröder som Spjute och Halvdan, av hustrur och söner. De restes efter dem som inte kom hem. Runstenarna är inte reseberättelser utan minnen av en väg som var verklig, och som många inte kom tillbaka från.

Det är också något svenskt med det. De danska och norska runstenarna nämner nästan aldrig en plats utanför Norden. Före år 1000 gör {EARLY0} av {EARLY_SE} svenska stenar det, men ingen av {EARLY_OT} danska och norska.

## Islänningasagorna: havet i väster

På Island berättade man en annan historia. Islänningasagorna handlar om de första generationerna på ön, om gårdar och fejder, om ära och om resor. Men resorna går västerut.

*{BJORN}*, står det i Bjarnar saga: Sommaren därpå for Björn västerut till England och fick stor heder där. Han stannade två vintrar hos Knut den mäktige. Andra far till Irland, till Orkney, till Skottland, och längst bort till Grönland. Nordatlanten – Orkney, Färöarna, Grönland – nämns i {ATL0} av {ATL1} islänningasagor. Det är inte så märkligt. Många av islänningarnas förfäder kom till ön via de brittiska öarna, och deras handel och släktband gick åt det hållet.

Öster finns också, men nästan bara som en enda stad: Miklagård, där islänningar tog tjänst i kejsarens väringagarde. Den nämns i {MIKLA_IS} islänningasagor. När Bolle Bollason i *Laxdæla saga* kommer hem därifrån är det en scen som sagan låter ta tid. *{BOLLI}* – Bolle var så prålig när han kom hem från den resan att han inte ville bära andra kläder än scharlakan och siden, och alla hans vapen var guldbeslagna. Miklagård är i islänningasagorna en plats man kommer hem från, med rikedom och berättelser. Serkland nämns i ingen enda.

## Fornaldarsagorna: österut igen

Det överraskande är fornaldarsagorna. De skrevs av samma folk, på samma ö, under samma tid som islänningasagorna. Men de berättar om forntiden, om kungar och hjältar före landnamet – och de ser mot öster.

*{BOSA}*, står det i Bósa saga: De höll österut och kom till Bjarmaland och lade till vid en öde skog. I skogen står ett tempel. *{JOMALI}* – Där dyrkas den gud som heter Jómali. Där finns mycket guld och dyrbarheter. Bjarmaland vid Vita havet finns i {BJ_FA} fornaldarsagor men bara i {BJ_IS} islänningasagor. Garðaríki och Miklagård är kungarikena dit hjältarna far för att vinna en brud eller ett rike.

{CHART_SV}

Skillnaden mellan de två slagen av sagor är {D1} procentenheter: {FA_P} % öster i fornaldarsagorna mot {IS_P} % i islänningasagorna. Den är troligen mellan {D1_LO} och {D1_HI} procentenheter. En så tydlig skillnad skulle uppstå av en slump i färre än ett fall av tusen. Vi bestämde hur provet skulle göras innan vi körde det, och skillnaden står kvar hur vi än räknar – utan de längsta sagorna, utan Yngvars saga och utan de allmänna riktningarna: mellan {ROB_LO} och {ROB_HI} procentenheter. Och fornaldarsagornas omvärld liknar runstenarnas mer än den liknar islänningasagornas.

## Vår hypotes: österleden blev forntid

Att fornaldarsagorna ofta utspelar sig i Östeuropa är känt i forskningen (Jackson 2019). Det vi tillför är mätningen: hur stor skillnaden är mot de sagor som skrevs samtidigt, och att fornaldarsagornas omvärld liknar runstenarnas.

Vår hypotes är att österleden på Island hade blivit forntid. På 1000-talet var den en verklig väg. Mödrar och bröder i Mälardalen visste vart deras söner och bröder hade farit, och var de låg. Men islänningarnas egen historia började i väster, och när de på 1200-talet skrev om sina förfäder skrev de om Orkney, Irland och England. Öster blev platsen för det som hade hänt förr, för hjältar och kungar i en tid före deras egen. Där fanns Jómalis tempel och guldet i Bjarmaland. Ingvar, vars färd Tola och de andra mödrarna mindes på sina stenar, blev huvudperson i en fornaldarsaga.

Hypotesen kan formuleras skarpare:

> I det isländska minnet låg forntiden i öster och den egna historien i väster. Österleden blev saga när den inte längre var någons väg.

## Det vi inte kan avgöra än

Vi prövade också två andra förklaringar, och båda gav för få träffar för ett säkert svar.

**Tiden.** Om sagornas västliga blick bara beror på att de skrevs två hundra år efter vikingatiden, borde skaldeverserna – diktade av samtida skalder och citerade i sagorna – se mer mot öster än prosan runt omkring. I Heimskringla gör de det inte: {HKV_P} % öster i verserna mot {T2_PROSA} % i prosan i samma sagor. Men verserna nämner sällan platser, bara {T2_HITS} gånger, och osäkerheten är för stor för att säga om tiden spelar roll.

**Platsen.** Med tiden konstant nämner de svenska runstenarna omvärlden ungefär {MH_OR} gånger så ofta som de danska och norska, och det skulle hända av en slump i färre än ett fall av tusen. Men om de danska och norska stenarna ser åt ett annat håll kan vi inte säga: bara åtta av dem nämner en plats alls.

## Vad fynden säger oss

Runstenarna och sagorna beskriver samma värld, men de minns den på olika sätt. På 1000-talet var omvärlden för många familjer i Mälardalen en väg österut, mot Miklagård, Garðaríki och Serkland. Den kom att stå på stenarna för att någon inte hade kommit hem. Stenarna är minnen av verkliga människor och verkliga färder, och de visar att österleden var en del av livet – och av sorgen – i det som i dag är Sverige, på ett sätt den inte var i Danmark och Norge.

Två hundra år senare, på Island, hade samma värld delats upp. Islänningarnas egen historia, den om förfäderna som tog land, låg i väster: Orkney, Irland, England, Grönland. Österut låg en annan tid. Dit förlades det som hade hänt före den egna historien, i berättelser om hjältar, kungar, drakar och guld. Att samma författare på samma ö vände blicken åt två håll beroende på vilken tid de skrev om är det fynd som står säkrast i vår analys. Det betyder att väderstrecket i en saga inte bara säger var något hände, utan också när berättaren tänkte sig att det hände.

Det säger något om hur minnet arbetar. Det som en gång var en väg som grannarna for blev, när ingen längre for den, en plats för sagor. Ingvar är det tydligaste exemplet: på stenarna en son och en bror som inte kom hem, i sagan en hjälte. Vad vi ännu inte vet är om tiden ensam förklarar skillnaden, eller om det också spelade roll att sagorna skrevs på Island och inte i Sverige. Verserna och de danska och norska stenarna är för få för att avgöra det. Men själva mönstret står fast: källorna ser åt olika håll, och de gör det på ett sätt som går att mäta.

## Så kan hypotesen prövas vidare

1. **Samtidssagorna.** Sagorna om 1200-talets Island, som *Sturlunga saga*, skrevs samtidigt men om samtiden. Om hypotesen stämmer ser de mot väster och söder – mot Norge, England och pilgrimsvägen till Rom – och inte mot öster.
2. **Fornaldarsagornas ålder.** Om de äldsta fornaldarsagorna ser mer mot öster än de yngsta, har österleden bleknat också inom genren.
3. **Hela skaldediktningen.** En ren utgåva av all bevarad skaldediktning skulle ge tiofalt fler versträffar, och då kan tiden prövas på allvar.

## Läs med kompassen

Nästa gång du läser en saga, lägg märke till åt vilket håll skeppet styr. Går det västerut, mot Orkney eller Irland, är du troligen bland förfäderna. Går det österut, mot Garðaríki eller Bjarmaland, är du i forntiden. Och står du framför en runsten i Mälardalen som säger *austr*, står du vid ett minne av någon som verkligen for.

## Förbehåll

- Att en plats nämns betyder inte att någon reste dit. Sagorna är litteratur, inte reseberättelser.
- Runstenarna minns främst dem som dog borta. De som kom hem fick sällan en sten.
- Versen har skilts från prosan maskinellt, och enstaka korta prosarader kan ha kommit med.
- Fornaldarsagornas text är Guðni Jónssons och Bjarni Vilhjálmssons utgåva från 1943–44. Vi har använt den för att räkna och citerar bara korta stycken.
- Platserna är grupperade i öster, väster och söder efter vad som ligger närmast till hands. Baltikum, Bjarmaland och Finland räknas till öster, Frankrike till väster.

:::box Det viktigaste i korthet
- Runstenarna och sagorna ser åt olika håll. De svenska stenarna från 1000-talet ser mot öster, islänningarnas sagor om de egna förfäderna mot väster.
- Det beror inte bara på var och när sagorna skrevs. Samma folk, på samma ö och under samma tid, skrev också fornaldarsagor – och de ser mot öster, lika ofta som runstenarna när Ingvarståget räknas bort.
- Vår hypotes: på Island hade österleden blivit forntid, en värld för hjältar och kungar före den egna historien. Ingvar, som mödrar och bröder mindes på svenska stenar, blev en sagofigur.
- Om tiden och platsen spelar in kan vi inte avgöra med de få träffar som verserna och de danska och norska stenarna ger.
:::

## Källor

- Samnordisk runtextdatabas (Rundata), Institutionen för nordiska språk, Uppsala universitet. Open Database License.
- Islänningasagorna: Icelandic Saga Database, sagadb.org (Sveinbjörn Þórðarson). Public domain.
- Snorri Sturluson, *Heimskringla*, utg. N. Linder och H. A. Haggson, 1869–72, via heimskringla.no.
- *Fornaldarsögur Norðurlanda*, utg. Guðni Jónsson och Bjarni Vilhjálmsson, Reykjavík 1943–44, via heimskringla.no.
- Jackson, T. N. 2019. *Eastern Europe in Icelandic Sagas*. Boston: Academic Studies Press.
- Foto: Wikimedia Commons, med fotograf och licens i bildtexten. Kartan: Vitki, på OpenStreetMaps underlag (© OpenStreetMap-bidragsgivare). Räkningen: Vitki (analysplanen och koden ligger öppet på [GitHub](https://github.com/Precatio/runes))."""

BODY_EN = """*ÞæiR foru drængila fiarri at gulli ok austarla ærni gafu, dou sunnarla a Særklandi.*

They travelled valiantly far for gold and in the east gave food to the eagle. They died in the south, in Serkland – the Muslim lands around the Caspian Sea.

A mother, Tóla, had those lines carved on a stone at Gripsholm in Södermanland (Sö 179). The stone was raised for her son Haraldr, brother of Ingvarr. Not far away, at Lundby, two brothers raised a stone for a third, Skarði: *For austr heðan með Ingvari, a Særklandi liggR sunR ØyvindaR* – from here he travelled east with Ingvarr; in Serkland lies Eyvindr's son (Sö 131). Ingvarr's expedition to the east around 1040 is remembered on {ING} Swedish runestones. It is the largest memory of a single journey that the runestones hold.

A couple of hundred years later someone in Iceland sat down to write about the same man. In *Yngvars saga víðförla*, the saga of Ingvarr the Far-Travelled, he is no longer a son or a brother who did not come home. He is a saga hero who fights dragons and giants in the east.

We wanted to know whether that is a coincidence, or whether it says something about how the world of the Viking Age was remembered. So we counted.

![The runestone Sö 179]({PHOTO})
Sö 179 at Gripsholm: "They died in the south, in Serkland." {CREDIT_EN}

:::box In short
- We counted every place outside Scandinavia named on {SE_N_EN} Swedish runestones and in {N_SAGOR} sagas, and whether it lies in the east or the west.
- The Swedish runestones look east: {SE_P} % of the places lie there. But almost half of that surplus is a single expedition, Ingvarr's – without it the figure is {SE_UI_P} %.
- The Icelanders wrote two kinds of saga at the same time. The sagas about their own ancestors look west, only {IS_P} % east. The sagas about the ancient past look east, {FA_P} % – as often as the runestones without Ingvarr's expedition.
- Our hypothesis: in Iceland the eastern route had become the ancient past. Their own history lay in the west.
:::

## Two ways of remembering a world

The runestones and the sagas are the two great voices from the Norse Viking Age. They speak in different ways. A runestone was carved by people who knew the dead man, often within a few years of his death. A saga was written much later, in Iceland, by people telling of ancestors they had never met. One is a memorial, the other a story.

We went through four kinds of text: the runestones in the Scandinavian Runic-text Data Base, carved in the eleventh century; the sagas of Icelanders, {IS_N} sagas about Iceland's first generations, written in the thirteenth and fourteenth centuries; the kings' sagas in Snorri Sturluson's *Heimskringla*, written around 1230; and the legendary sagas, {FA_N} sagas about the time before Iceland was settled, written down in Iceland in the same period as the sagas of Icelanders. The verse in the sagas we counted separately.

In the texts we looked for places outside Scandinavia. Every hit was read in context, for Old Norse is full of traps: *serkr* is a shirt, *rúm* a bed, *frakka* a spear and *vindr* a wind. Each place counts once per stone or saga, so that a long saga naming England fifty times weighs no more than a short one naming it once.

{PLATSER_EN}

{MAP_EN}

## The stones: a road that ran east

The most common place on the runestones is no place at all. It is a direction: *austr*, in the east. Whoever read the stone needed no more. Everyone knew where the road went.

When the stones name a country, two names stand almost side by side: England on {ENG} stones, where men took *gæld*, payment from the English kings, and Greece on {GRE} – the Byzantine Empire and its capital Miklagarðr. Then comes Garðaríki, the realms along the Russian rivers, and furthest away Serkland, where Ingvarr's men died. But the weight lies in the east. {SE_P} % of the places lie there, and {MAL[0]} of the {MAL[1]} stones that name a place in the east stand in the Mälaren region.

But much of that surplus is a single expedition. If we set aside the Ingvarr stones – the {ING} that name the journey, Tóla's stone and a stone for an Ingvarr who died in the east, {UI_N} in all – {SE_UI_P} % of the places lie in the east, probably between {SE_UI_LO} and {SE_UI_HI} %. The stones then still look east somewhat more often than west, but not clearly enough to rule out that it was equally often. The difference from the Icelanders' sagas about their ancestors, {IS_P} %, remains. We tested this afterwards, following a plan we locked before counting (10 November 2026).

That says something about who travelled and who stayed. The stones were raised by mothers like Tóla, by brothers like Spjóti and Halfdan, by wives and sons. They were raised for those who did not come home. The runestones are not travel accounts but memories of a road that was real, and that many did not come back from.

There is also something Swedish about it. The Danish and Norwegian runestones almost never name a place outside Scandinavia. Before the year 1000, {EARLY0} of {EARLY_SE} Swedish stones do, but none of {EARLY_OT} Danish and Norwegian ones.

## The sagas of Icelanders: the sea to the west

In Iceland another story was told. The sagas of Icelanders are about the first generations on the island, about farms and feuds, about honour and about journeys. But the journeys go west.

*{BJORN}*, says Bjarnar saga: The following summer Björn travelled west to England and won great honour there. He stayed two winters with Knútr the Mighty. Others go to Ireland, to Orkney, to Scotland, and furthest of all to Greenland. The North Atlantic – Orkney, the Faroes, Greenland – is named in {ATL0} of {ATL1} sagas of Icelanders. That is not so strange. Many of the Icelanders' forebears came to the island by way of the British Isles, and their trade and kinship ran that way.

The east is there too, but almost only as a single city: Miklagarðr, where Icelanders took service in the emperor's Varangian guard. It is named in {MIKLA_IS} sagas of Icelanders. When Bolli Bollason in *Laxdæla saga* comes home from there, the saga lets the scene take its time. *{BOLLI}* – Bolli was so splendid when he came home from that journey that he would wear no clothes but scarlet and silk, and all his weapons were set with gold. In the sagas of Icelanders Miklagarðr is a place one comes home from, with riches and stories. Serkland is named in not a single one.

## The legendary sagas: east again

The surprise is the legendary sagas. They were written by the same people, on the same island, at the same time as the sagas of Icelanders. But they tell of the ancient past, of kings and heroes before the settlement – and they look east.

*{BOSA}*, says Bósa saga: They held east and came to Bjarmaland and put in by a deserted forest. In the forest stands a temple. *{JOMALI}* – There the god called Jómali is worshipped. There is much gold and treasure. Bjarmaland by the White Sea appears in {BJ_FA} legendary sagas but in only {BJ_IS} sagas of Icelanders. Garðaríki and Miklagarðr are the kingdoms where heroes go to win a bride or a realm.

{CHART_EN}

The difference between the two kinds of saga is {D1} percentage points: {FA_P} % east in the legendary sagas against {IS_P} % in the sagas of Icelanders. It probably lies between {D1_LO} and {D1_HI} points. A difference this clear would arise by chance in fewer than one case in a thousand. We decided how the test would be done before we ran it, and the difference remains however we count – without the longest sagas, without Yngvars saga and without the general directions: between {ROB_LO} and {ROB_HI} percentage points. And the world of the legendary sagas resembles that of the runestones more than that of the sagas of Icelanders.

## Our hypothesis: the eastern route became the ancient past

That the legendary sagas often take place in Eastern Europe is known in research (Jackson 2019). What we add is the measurement: how large the difference is from the sagas written at the same time, and that the world of the legendary sagas resembles that of the runestones.

Our hypothesis is that in Iceland the eastern route had become the ancient past. In the eleventh century it was a real road. Mothers and brothers in the Mälaren region knew where their sons and brothers had gone, and where they lay. But the Icelanders' own history began in the west, and when they wrote about their ancestors in the thirteenth century they wrote about Orkney, Ireland and England. The east became the place of what had happened long ago, of heroes and kings in a time before their own. There stood Jómali's temple and the gold of Bjarmaland. Ingvarr, whose journey Tóla and the other mothers remembered on their stones, became the hero of a legendary saga.

The hypothesis can be put more sharply:

> In Icelandic memory the ancient past lay in the east and their own history in the west. The eastern route became legend once it was no longer anyone's road.

## What we cannot settle yet

We also tested two other explanations, and both gave too few hits for a firm answer.

**Time.** If the western gaze of the sagas is only because they were written two hundred years after the Viking Age, the skaldic verse – composed by contemporary poets and quoted in the sagas – should look more to the east than the prose around it. In Heimskringla it does not: {HKV_P} % east in the verse against {T2_PROSA} % in the prose of the same sagas. But the verse rarely names places, only {T2_HITS} times, and the uncertainty is too large to say whether time matters.

**Place.** With time held constant the Swedish runestones name the wider world about {MH_OR} times as often as the Danish and Norwegian ones, which would happen by chance in fewer than one case in a thousand. But whether the Danish and Norwegian stones look another way we cannot say: only eight of them name a place at all.

## What our findings tell us

The runestones and the sagas describe the same world, but they remember it in different ways. In the eleventh century the wider world was, for many families in the Mälaren region, a road to the east, towards Miklagarðr, Garðaríki and Serkland. It came to be written on the stones because someone had not come home. The stones are memories of real people and real journeys, and they show that the eastern route was part of life – and of grief – in what is now Sweden, in a way it was not in Denmark and Norway.

Two hundred years later, in Iceland, the same world had been divided. The Icelanders' own history, that of the ancestors who settled the land, lay in the west: Orkney, Ireland, England, Greenland. To the east lay another time. There they placed what had happened before their own history, in stories of heroes, kings, dragons and gold. That the same writers on the same island turned their gaze two ways depending on which time they were writing about is the finding that stands firmest in our analysis. It means that the point of the compass in a saga tells not only where something happened, but also when the storyteller imagined it happening.

That says something about how memory works. What was once a road one's neighbours travelled became, when no one travelled it any longer, a place for legend. Ingvarr is the clearest example: on the stones a son and a brother who did not come home, in the saga a hero. What we do not yet know is whether time alone explains the difference, or whether it also mattered that the sagas were written in Iceland and not in Sweden. The verse and the Danish and Norwegian stones are too few to settle it. But the pattern itself stands: the sources look different ways, and they do so in a way that can be measured.

## How the hypothesis can be tested further

1. **The contemporary sagas.** The sagas about thirteenth-century Iceland, such as *Sturlunga saga*, were written at the same time but about their own time. If the hypothesis holds they look west and south – to Norway, England and the pilgrim road to Rome – and not east.
2. **The age of the legendary sagas.** If the oldest legendary sagas look further east than the youngest, the eastern route faded within the genre too.
3. **The whole of skaldic poetry.** A clean edition of all surviving skaldic verse would give ten times as many verse hits, and then time could be tested properly.

## Read with a compass

Next time you read a saga, notice which way the ship is steering. If it goes west, towards Orkney or Ireland, you are probably among the ancestors. If it goes east, towards Garðaríki or Bjarmaland, you are in the ancient past. And if you stand before a runestone in the Mälaren region that says *austr*, you stand before the memory of someone who really went.

## Caveats

- That a place is named does not mean that anyone travelled there. The sagas are literature, not travel accounts.
- The runestones mainly remember those who died abroad. Those who came home seldom got a stone.
- The verse has been separated from the prose by machine, and a few short prose lines may have come along.
- The text of the legendary sagas is Guðni Jónsson's and Bjarni Vilhjálmsson's edition of 1943–44. We have used it for counting and quote only short passages.
- The places are grouped into east, west and south by what lies closest to hand. The Baltic lands, Bjarmaland and Finland count as east, France as west.

:::box The essentials in brief
- The runestones and the sagas look different ways. The Swedish stones of the eleventh century look east, the Icelanders' sagas about their own ancestors west.
- That is not only because of where and when the sagas were written. The same people, on the same island and at the same time, also wrote legendary sagas – and they look east, as often as the runestones once Ingvarr's expedition is set aside.
- Our hypothesis: in Iceland the eastern route had become the ancient past, a world for heroes and kings before their own history. Ingvarr, whom mothers and brothers remembered on Swedish stones, became a figure of legend.
- Whether time and place play a part we cannot settle with the few hits that the verse and the Danish and Norwegian stones give.
:::

## Sources

- Scandinavian Runic-text Data Base (Rundata), Department of Scandinavian Languages, Uppsala University. Open Database License.
- The sagas of Icelanders: Icelandic Saga Database, sagadb.org (Sveinbjörn Þórðarson). Public domain.
- Snorri Sturluson, *Heimskringla*, ed. N. Linder and H. A. Haggson, 1869–72, via heimskringla.no.
- *Fornaldarsögur Norðurlanda*, ed. Guðni Jónsson and Bjarni Vilhjálmsson, Reykjavík 1943–44, via heimskringla.no.
- Jackson, T. N. 2019. *Eastern Europe in Icelandic Sagas*. Boston: Academic Studies Press.
- Photo: Wikimedia Commons, with photographer and licence in the caption. The map: Vitki, on OpenStreetMap's base map (© OpenStreetMap contributors). The count: Vitki (the analysis plan and the code are open on [GitHub](https://github.com/Precatio/runes))."""
