"""Artikeln "De gamla landen: Finnveden – landet längs Lagan" (sv + en), en del i serien De gamla landen i seriens
atmosfäriska form (Viktor 2026-11-04). Finnveden omkring år 1000: dalgångarna och ljunghedarna, höggravfälten, Bolmsö,
Lagan och Lagastigen, järnet, tinget i Hamneda och gränsen mot Danmark, tron. Varje uppgift är ett ordagrant citat ur
källorna i /Volumes/2TB/Antigrvity/Runes/downloads/smaland_lit (NOTES.md, insamlat 2026-11-04) och kontrolleras nedan som
en delsträng av källans text med blanktecknen sammanslagna. Kartan: utdata/gamla_landen/karta_land.R med finnveden.json.
    ../../../.venv/bin/python build_finnveden.py [--write | --update DOC]"""
import datetime as dt
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_figures, commons  # noqa: E402

LIT = "/Volumes/2TB/Antigrvity/Runes/downloads/smaland_lit/"
_txt = {}


def said(fil, quote):
    if fil not in _txt:
        _txt[fil] = " ".join(open(LIT + fil, encoding="utf-8").read().split())
    assert " ".join(quote.split()) in _txt[fil], (fil, quote)


H, BOL, TRO, HS, HR, FV12, FV25, RIF, VJ, VW, ALM = (
    "Hansson1999_renjagare_col.txt", "LstG_Bolmso_col.txt", "LstG_Trotteslov_col.txt", "LstG_Hamneda-skrift_col.txt",
    "LstG_Hamneda-rapport_col.txt", "Fv2012_Hansson_Hamneda_col.txt", "Fv2025_Hennius_blastugn_col.txt", "RI_Jonkoping-F.txt",
    "Varnamo_Jarnindustri_col.txt", "Varnamo_Historien_i_landskapet.txt", "Almquist1954_Lagsagor_del1.txt")
FACTS = [
    (H, "I Finnveden koncentrerades bebyggelsen till Lagans och Nissans dalgångar och till området kring Bolmen och Vidöstern."),
    (BOL, "en punkt som i det närmaste exakt utgör Finnvedens geografiska centrum, och det är Bolmsö i Bolmen."), (BOL, "Bolmsö är Smålands största ö."),
    (BOL, "Delar av Finnveden var fram till 1900-talets början nämligen kända för sina ”svältor”, eller ljunghedar."),
    (H, "Detta talar starkt för att stora områden med ljunghedar funnits i dessa områden också under tidigare perioder."),
    (H, "Ånamnet Lagan är dock en stark kandidat och kanske det äldsta namnet här överhuvudtaget."),
    (H, "Bebyggelseomflyttningen i norra Finnveden är dock så omfattande, att man där närmast får tänka sig att en regelrätt utflyttning skedde från vissa områden."),
    (H, "där ett tidigare extensivt åkerbruk nu ersattes av ett intensivare åkerbruk och utvidgad boskapsskötsel"),
    (TRO, "Järnåldersgravfälten har, liksom i övriga Lagadalen tydliga samband med de historiska byarna"),
    (HS, "De bestod då av fem respektive sju gårdar och räknades med tidens mått som relativt stora byar."),
    (H, "På många av gravfälten från yngre järnålder uppgår andelen högar till mer än 90 procent."),
    (H, "Finnveden och speciellt Sunnerbo tillhör de områden i landet med extremt enhetligt gravskick under yngre järnålder."),
    (H, "Gravfältet ”Kånna högar” strax söder om Ljungby är länets största gravfält med ca 250 gravar."),
    (TRO, "Här karaktäriseras höggravfälten av runda och starkt välvda högar, inte sällan med tydlig kantränna."),
    (H, "Den äldre järnålderns varierade stengravfält med resta stenar, domarringar, runda stensättningar, ersattes med ett enhetligt höggravskick."),
    (TRO, "I åkermarken mellan Össlöv och vägen ligger länets största skeppssättning som uppgår till 42x13m."),
    (H, "fått två hästar, två hundar, två svin, troligen två nötdjur, samt får och get."), (H, "Kanske var den yngre kvinnan också här ett offer"),
    (H, "En av de döda hade ett mycket fragmentariskt silvermynt i munnen"), (H, "I dessa gravar framträder kristnandeprocessen tydligt."),
    (H, "I Finnveden har närmare 50 vikingatida skelettgravar undersökts."),
    (HS, "De består av sammanlagt 241 högar som ligger tydligt exponerade såväl längs vattnet som utmed Lagastigen."),
    (HS, "vardagsföremål som knivar och brynen samt pärlor av glas och silver"),
    (RIF, "manifesterar Kärda som länets högrikaste socken"),
    (H, "på Bolmsö har ett femtontal gravar med slagg påträffats."),
    (H, "Förekomsten av slagg i gravar har tolkats som att de begravda personerna varit involverade i järnhanteringen."),
    (FV25, "En inledande fas under romersk järnålder och en betydligt mer omfattande fas som inleddes i början av vikingatiden och som nådde sin höjdpunkt i början av medeltiden"),
    (VJ, "Koncentrationen runt sjön Rusken är tydlig, här finns även flera ortnamn som kan kopplas till järnframställning"),
    (VJ, "fynden kan i vissa områden lokaliseras från den yngre järnåldern och äldre medeltiden"),
    (FV12, "Lagan fungerade sedan forntiden som en viktig kommunikationsled, precis som den landsväg som följde åns lopp."),
    (HR, "Längs Lagan löper Lagastigen som sedan tidig medeltid varit en av Sveriges viktigaste farleder mellan de centrala delarna vid Mälaren och kontinenten."),
    (BOL, "Den senare formen kan syfta på den led längs med Lagan som på rullstensåsar förbundit södra Skandinavien med Uppsverige"),
    (H, "Tiohärads runstenar är koncentrerade till centrala Värend, Lagandalen norr om Hamneda samt centrala Njudung"),
    (H, "troligen säte för en hövding av betydelse för hela Finnveden."),
    (BOL, "Många forskare förefaller dessutom överens om att Bolmsö också maktpolitiskt utgjort centrum för folklandet Finnveden."),
    (BOL, "samt att ön ska ha utgjort platsen för folklandets landsting."), (BOL, "Möjligen har Bolmsö varit för Finnveden vad Visingsö var för Götaland."),
    (BOL, "Finnveden hade inte som Värend något självklart centrum."),
    (H, "Sveainslaget är särskilt starkt på Bolmsö, där Husa, Bo, Hov, Tjust och Bollstad tillsammans bildar en centralortsmiljö"),
    (H, "ytterligare guldtenar samt två guldgubbar"), (H, "av allt att döma haft samband med den hedniska kulten"),
    (H, "Ett par kilometer söder om fyndplatsen finns också ”Hov”, ett ortnamn som visar att här funnits en kultplats."),
    (BOL, "komma att utgör grunden för Finnvedens tre härader; Sunnerbo, Västbo och Östbo."),
    (FV12, "tingsplats för Sunnerbo härad från 1373 till 1693"),
    (HS, "Tingsplatsen var inget fysiskt ställe, utan det hölls på olika platser, ibland utomhus på en gravhög."),
    (RIF, "I Ölmestad är Brödrahalla, utpekad som Västbo härads tingsplats, med runsten och resta stenar."),
    (ALM, "omfattande de tre landen Finnveden, Värend och Njudung"),
    (HR, "Området utgjorde länge gränsbygd mot Danmark som tog vid söder och väster om den nuvarande småländska gränsen."),
    (H, "Av detta ska man dock inte tro att södra Småland ingick i en tidig dansk statsbildning, snarare att viktiga impulser kom söderifrån"),
    (H, "Exempel är bland annat Trotteslöv i Berga socken och Bäckaslöv utanför Växjö."),
    (FV12, "varför Hamneda tolkats som den svenska kungamaktens utpost i sydväst"),
    (H, "Odensjö < Odhinsrydh i Sunnerbo"),
    (H, "Korset är dominant i Finnveden där andelen överträffar Upplands (67 respektive 58 procent)"),
]
for fil, q in FACTS:
    said(fil, q)

# ---- picture and map --------------------------------------------------------------------------------------------------
FK = "Kungshögen Bolmsö Sweden.jpg"
INFO = commons.commons_info([FK])
assert (INFO[FK]["licence"], INFO[FK]["author"]) == ("CC BY-SA 3.0", "Sven Rosborn")
LIC = f"[{INFO[FK]['licence']}]({INFO[FK]['licence_url']})" if INFO[FK].get("licence_url") else INFO[FK]["licence"]
PAGE = "https://commons.wikimedia.org/wiki/File:" + FK.replace(" ", "_")
MAP = {lang: blog_figures.freeze(open(os.path.join(ROOT, "utdata", "gamla_landen", f"karta_finnveden_{lang}.png"), "rb").read())
       for lang in ("sv", "en")}
VAREND = "/artiklar/de-gamla-landen-varend"

title = "De gamla landen: Finnveden – landet längs Lagan"
summary = ("Finnveden var det västligaste av Smålands små land: dalgångar längs Lagan och Nissan, ljunghedar, sjön Bolmen med "
           "sin stora ö, och gravfält där nästan varje grav var en hög. Längs Lagan gick vägen mellan Mälardalen och kontinenten. "
           "Följ med dit omkring år 1000. En del i serien De gamla landen.")

body = f"""Lagan har kanske det äldsta namnet i hela trakten. Ån har varit en väg sedan forntiden, både på vattnet och på landsvägen som följer dess lopp, och den som för tusen år sedan färdas söderut längs den går på rullstensåsarna, som bär stigen. Runt omkring ligger Finnveden, det västligaste av Smålands små land.

Bygden ligger i dalgångarna, längs Lagan och Nissan och kring sjöarna Bolmen och Vidöstern. Mellan dem breder ljunghedar ut sig, öppna och karga, och ortnamnen visar att de har funnits länge. Mitt i landet, nästan exakt i dess geografiska centrum, ligger Bolmsö, Smålands största ö, i sjön Bolmen.

## Byarna och åkrarna

Finnveden har förändrats. Under yngre järnåldern flyttade bebyggelsen så kraftigt i norr att forskarna talar om en regelrätt utflyttning från vissa trakter. Samtidigt blev jordbruket intensivare, med mer åker och fler djur. Gravfälten ligger intill de gamla bytomterna, så byarna har legat på samma platser länge. Vid Hamneda, längs Lagan, fanns tidigt på medeltiden byar med fem och sju gårdar, stora för sin tid.

Föreställ dig en sådan by en sommardag: åkrarna nere i dalen, djuren uppe på ljunghedarna, röken från husen längs ån.

## Högarna

Den som färdas genom Finnveden ser högar överallt. Under yngre järnåldern ersattes de gamla gravfälten, med sina resta stenar, domarringar och runda stensättningar, av ett gravskick där nästan allt var högar: på många gravfält är mer än nio av tio gravar högar, runda och välvda, ofta med en ränna runt kanten. Finnveden, och särskilt Sunnerbo, hör till de trakter i landet där gravskicket är som mest enhetligt. Kånna högar söder om Ljungby är länets största gravfält, med omkring 250 gravar. Vid Hamneda ligger 241 högar väl synliga längs vattnet och längs vägen, och i gravarna har man hittat knivar, brynen och pärlor av glas och silver. Kärda, längre norrut, är den socken i Jönköpings län som har flest högar.

![Kungshögen på Bolmsö]({INFO[FK]['thumb']})
Kungshögen på Bolmsö. Foto: Sven Rosborn, {LIC}, via [Wikimedia Commons]({PAGE}).

Några gravar berättar mer. Vid Fallnaveka i Berga socken har två människor begravts tillsammans med två hästar, två hundar, två svin, troligen två nötdjur och får och get. Kanske var den yngre kvinnan ett offer, skriver Martin Hansson, men det är bara en möjlighet. Och vid Kånna ligger döda begravda obrända under högar, en av dem med ett litet silvermynt i munnen. Där syns kristnandet ta form. I Finnveden har närmare femtio skelettgravar från vikingatiden undersökts.

## Bolmsö

Mitt i Bolmen ligger ön där landets hövding troligen satt. På Bolmsö har man hittat guld från järnåldern, äldre än vikingatiden: en brakteat, guldtenar och två guldgubbar, små tunna bleck med bilder som av allt att döma hörde till den hedniska kulten. Ett par kilometer därifrån ligger ett ställe som heter Hov, ett namn som visar att där funnits en kultplats. Ortnamnen på ön – Husa, Bo, Hov, Tjust och Bollstad – bildar tillsammans en centralort, och ortnamnsforskaren Staffan Fridell ser i dem ett starkt inslag från Svealand, kanske en kolonisation av ön. På Bolmsö har också ett femtontal gravar med slagg från järnframställning hittats, som om de döda hade haft med järnet att göra.

Många forskare menar att Bolmsö var Finnvedens centrum och platsen för landstinget. Länsstyrelsen skriver att Bolmsö möjligen var för Finnveden vad Visingsö var för Götaland. Men det är en tolkning, och Finnveden hade inte, som Värend, något självklart centrum.

![Karta över Finnveden omkring år 1000 med runstenarna och platserna i texten]({MAP['sv']})
**Karta.** Finnveden omkring år 1000. Rostfärgat är Sunnerbo, Västbo och Östbo härader, ljust grannlanden; gränserna är ungefärliga. Grå punkter är runstenar, ringar platser i texten. Karta: Vitki, efter SGU:s modell för strandförskjutningen år 1000, Institutet för språk och folkminnens ortnamnsregister och Rundata.

## Järnet

I Finnveden hörde järnet till vardagen. Kring sjön Rusken i Östbo ligger platser där man framställt järn, och flera ortnamn där minns det; några av fynden är från yngre järnåldern och tidig medeltid. I hela Jönköpings län tog järnframställningen fart i början av vikingatiden och nådde sin höjdpunkt i början av medeltiden. Föreställ dig blästerugnarna vid myrarna, röken och slaggen, och smederna som tog järnet vidare.

## Vägen och gränsen

Lagastigen, vägen längs Lagan, var sedan tidig medeltid en av Sveriges viktigaste leder mellan Mälardalen och kontinenten. Kanske syftar själva namnet Finnveden på den leden, som på rullstensåsarna förband södra Skandinavien med Uppsverige; det är en möjlig tolkning. Runstenarna i Tiohärad står tätast i centrala Värend, i Lagans dalgång norr om Hamneda och i centrala Njudung. På Finnvedens stenar dominerar korset, oftare än i Uppland: två av tre stenar.

Finnveden var länge en gränsbygd mot Danmark, som tog vid söder och väster om landet. Ortnamn på -löv, som Trotteslöv i Berga, visar att impulser kom söderifrån. Men det betyder inte att landet var danskt, skriver Hansson. I mitten av 1100-talet byggdes kyrkan i Hamneda, som har tolkats som den svenska kungamaktens utpost i sydväst.

## Tinget

Finnveden var ett av de tre land som på medeltiden bildade lagsagan Tiohärad, tillsammans med Värend och Njudung, och det var delat i tre härader, Sunnerbo, Västbo och Östbo. Sunnerbos ting hölls i Hamneda från 1373 till 1693. Tinget var ingen byggnad. Det hölls på olika platser, ibland ute på en gravhög. Västbos tingsplats var Brödrahalla i Ölmestad, med en runsten och resta stenar. Föreställ dig männen samlade på en hög vid Lagan, med vägen nedanför och de döda under fötterna.

## Tron

Ortnamnen minns de gamla gudarna. I Sunnerbo ligger Odensjö, som tidigare hette Odhinsrydh, Odens röjning. På Bolmsö finns Hov. Och i gravarna vid Kånna syns det nya: döda som inte bränns utan läggs i jorden, med ett mynt i munnen.

## Ett land längs vägen

Finnveden omkring år 1000 är ett land av dalgångar och hedar, av högar längs ån och en ö mitt i sjön. Det ligger vid gränsen och vid vägen, och genom det går människor, varor och idéer mellan söder och norr. Den som står vid högarna i Hamneda och ser ut över Lagan ser vägen som band ihop riket med kontinenten, och högarna där landets döda vakade över den. Grannlandet i öster, [Värend]({VAREND}), vände sig mot sjöarna; Finnveden vände sig mot vägen.

## Så vet vi det

Landskapet, gravarna och Bolmsö bygger på Martin Hanssons arkeologiska historia om södra Småland (1999) och på länsstyrelsen i Kronobergs läns beskrivningar av Bolmsö, Hamneda och Trotteslöv-Össlöv-Fallnaveka; Västbo och Östbo på Riksantikvarieämbetets riksintressetexter och Värnamo kommun. Finnveden saknar en volym i *Det medeltida Sverige*, och Hanssons bok handlar mest om Sunnerbo. Att Bolmsö var landets centrum och tingsplats, att ön koloniserades från Svealand och att kvinnan vid Fallnaveka offrades är tolkningar. Tinget i Hamneda och Lagastigen är kända från medeltiden. Länkarna till källorna finns nedan.

## Källor

- Hansson, Martin 1999. Från renjägare till viking. En arkeologisk historia om södra Småland. I: Johansson (red.) *Landen kring sjöarna*. Kronobergsboken 1999/2000. Med faktarutor av Christer Knutsson och Staffan Fridell.
- Hansson, Martin 2012. Fortgående straffdom – en medeltida avrättningsplats i Hamneda i Småland. *Fornvännen* 107.
- Hennius, Andreas m.fl. 2025. Järnframställning i blästugn – en uppdaterad kronologi. *Fornvännen* 120.
- Almquist, Jan Eric 1954. *Lagsagor och domsagor i Sverige* I. Stockholm.
- Länsstyrelsen i Kronobergs län: fördjupade beskrivningar av Bolmsö kyrkby (2015), Trotteslöv-Össlöv-Fallnaveka (2014) och Hamneda (2012), samt skriften *Hamneda – kulturmiljö av riksintresse* (2015).
- Riksantikvarieämbetet. *Riksintressen för kulturmiljövården – Jönköpings län*.
- Värnamo kommun. *Järnindustri* och *Historien i landskapet*.
- Samnordisk runtextdatabas (Rundata), Institutionen för nordiska språk, Uppsala universitet. Open Database License. Institutet för språk och folkminnen, ortnamnsregistret, CC BY. Sveriges geologiska undersökning, strandförskjutningsmodell (kartan).
- Bild: Wikimedia Commons, med fotografen och licensen i bildtexten."""

title_en = "The old lands: Finnveden – the land along the Lagan"
summary_en = ("Finnveden was the westernmost of Småland's small lands: valleys along the Lagan and the Nissan, heaths, Lake Bolmen "
              "with its great island, and grave fields where nearly every grave was a mound. Along the Lagan ran the road between "
              "the Mälaren valley and the continent. Come along around AD 1000. A part of the series The old lands.")

body_en = f"""The Lagan has perhaps the oldest name in the whole district. The river has been a road since prehistoric times, both on the water and on the highway that follows its course, and whoever travels south along it a thousand years ago walks on the gravel ridges that carry the path. All around lies Finnveden, the westernmost of Småland's small lands.

The settlement lies in the valleys, along the Lagan and the Nissan and round the lakes Bolmen and Vidöstern. Between them heaths spread out, open and barren, and the place-names show that they have been there a long time. In the middle of the land, almost exactly at its geographical centre, lies Bolmsö, Småland's largest island, in Lake Bolmen.

## The villages and the fields

Finnveden has changed. During the Late Iron Age the settlement in the north moved so much that researchers speak of an outright emigration from some districts. At the same time farming became more intensive, with more fields and more animals. The grave fields lie beside the old village sites, so the villages have stood in the same places for a long time. At Hamneda, along the Lagan, there were in the early Middle Ages villages of five and seven farms, large for their time.

Imagine such a village on a summer day: the fields down in the valley, the animals up on the heaths, the smoke from the houses along the river.

## The mounds

Whoever travels through Finnveden sees mounds everywhere. During the Late Iron Age the old grave fields, with their standing stones, stone circles and round stone settings, were replaced by a burial custom in which almost everything was a mound: in many grave fields more than nine graves in ten are mounds, round and domed, often with a ditch round the edge. Finnveden, and Sunnerbo in particular, is among the parts of the country where the burial custom is most uniform. Kånna högar south of Ljungby is the county's largest grave field, with about 250 graves. At Hamneda 241 mounds lie in plain view along the water and along the road, and in the graves knives, whetstones and beads of glass and silver have been found. Kärda, further north, is the parish in Jönköping county with the most mounds.

![The King's Mound on Bolmsö]({INFO[FK]['thumb']})
The King's Mound on Bolmsö. Photo: Sven Rosborn, {LIC}, via [Wikimedia Commons]({PAGE}).

Some graves tell more. At Fallnaveka in Berga parish two people were buried together with two horses, two dogs, two pigs, probably two cattle, and sheep and goat. Perhaps the younger woman was a sacrifice, writes Martin Hansson, but that is only a possibility. And at Kånna dead lie buried unburnt under mounds, one of them with a small silver coin in the mouth. There the Christianisation can be seen taking shape. In Finnveden nearly fifty Viking-age inhumation graves have been examined.

## Bolmsö

In the middle of Bolmen lies the island where the land's chieftain probably sat. On Bolmsö Iron Age gold, older than the Viking Age, has been found: a bracteate, gold rods and two gold-foil figures, small thin plaques with pictures that by all appearances belonged to the heathen cult. A couple of kilometres away lies a place called Hov, a name that shows there was a cult place there. The place-names on the island – Husa, Bo, Hov, Tjust and Bollstad – together form a central place, and the place-name scholar Staffan Fridell sees in them a strong element from Svealand, perhaps a colonisation of the island. On Bolmsö some fifteen graves with slag from iron-making have also been found, as if the dead had had to do with iron.

Many researchers think Bolmsö was Finnveden's centre and the place of the land assembly. The county board writes that Bolmsö was perhaps to Finnveden what Visingsö was to Götaland. But that is an interpretation, and Finnveden had, unlike Värend, no obvious centre.

![Map of Finnveden around AD 1000 with the runestones and the places in the text]({MAP['en']})
**Map.** Finnveden around AD 1000. Rust is the hundreds of Sunnerbo, Västbo and Östbo, light the neighbouring lands; the borders are approximate. Grey points are runestones, rings places in the text. Map: Vitki, after the Geological Survey of Sweden's shore-displacement model for AD 1000, the place-name register of the Institute for Language and Folklore, and Rundata.

## The iron

In Finnveden iron was part of everyday life. Around Lake Rusken in Östbo lie places where iron was made, and several place-names there remember it; some of the finds are from the Late Iron Age and the early Middle Ages. In the whole of Jönköping county iron-making took off at the start of the Viking Age and peaked at the start of the Middle Ages. Imagine the bloomery furnaces by the bogs, the smoke and the slag, and the smiths who carried the iron further.

## The road and the border

Lagastigen, the road along the Lagan, was from the early Middle Ages one of Sweden's most important routes between the Mälaren valley and the continent. Perhaps the very name Finnveden refers to that route, which on the gravel ridges linked southern Scandinavia with Uppsverige; that is one possible reading. The runestones of Tiohärad stand thickest in central Värend, in the Lagan valley north of Hamneda and in central Njudung. On Finnveden's stones the cross dominates, more often than in Uppland: two stones in three.

Finnveden was long a border district towards Denmark, which began south and west of the land. Place-names in -löv, such as Trotteslöv in Berga, show that impulses came from the south. But that does not mean the land was Danish, writes Hansson. In the middle of the twelfth century the church at Hamneda was built, which has been read as the Swedish crown's outpost in the south-west.

## The assembly

Finnveden was one of the three lands that in the Middle Ages formed the law province of Tiohärad, together with Värend and Njudung, and it was divided into three hundreds, Sunnerbo, Västbo and Östbo. The assembly of Sunnerbo met at Hamneda from 1373 to 1693. The assembly was no building. It was held in different places, sometimes out on a grave mound. Västbo's assembly place was Brödrahalla in Ölmestad, with a runestone and standing stones. Imagine the men gathered on a mound by the Lagan, with the road below and the dead under their feet.

## Belief

The place-names remember the old gods. In Sunnerbo lies Odensjö, which was earlier called Odhinsrydh, Odin's clearing. On Bolmsö there is Hov. And in the graves at Kånna the new shows: dead who are not burnt but laid in the ground, with a coin in the mouth.

## A land along the road

Finnveden around AD 1000 is a land of valleys and heaths, of mounds along the river and an island in the middle of the lake. It lies by the border and by the road, and through it go people, goods and ideas between south and north. Whoever stands by the mounds at Hamneda and looks out over the Lagan sees the road that tied the realm to the continent, and the mounds where the land's dead kept watch over it. The neighbouring land to the east, [Värend]({VAREND}), faced its lakes; Finnveden faced the road.

## How we know

The landscape, the graves and Bolmsö rest on Martin Hansson's archaeological history of southern Småland (1999) and on the County Administrative Board of Kronoberg's descriptions of Bolmsö, Hamneda and Trotteslöv-Össlöv-Fallnaveka; Västbo and Östbo on the National Heritage Board's texts on areas of national interest and on Värnamo municipality. Finnveden has no volume in *Det medeltida Sverige*, and Hansson's book is mostly about Sunnerbo. That Bolmsö was the land's centre and assembly place, that the island was colonised from Svealand and that the woman at Fallnaveka was sacrificed are interpretations. The assembly at Hamneda and Lagastigen are known from the Middle Ages. The sources are listed below.

## Sources

- Hansson, Martin 1999. Från renjägare till viking. En arkeologisk historia om södra Småland. In: Johansson (ed.) *Landen kring sjöarna*. Kronobergsboken 1999/2000. With boxes by Christer Knutsson and Staffan Fridell.
- Hansson, Martin 2012. Fortgående straffdom – en medeltida avrättningsplats i Hamneda i Småland. *Fornvännen* 107.
- Hennius, Andreas et al. 2025. Järnframställning i blästugn – en uppdaterad kronologi. *Fornvännen* 120.
- Almquist, Jan Eric 1954. *Lagsagor och domsagor i Sverige* I. Stockholm.
- County Administrative Board of Kronoberg: in-depth descriptions of Bolmsö kyrkby (2015), Trotteslöv-Össlöv-Fallnaveka (2014) and Hamneda (2012), and the booklet *Hamneda – kulturmiljö av riksintresse* (2015).
- Swedish National Heritage Board. *Riksintressen för kulturmiljövården – Jönköpings län*.
- Värnamo municipality. *Järnindustri* and *Historien i landskapet*.
- Scandinavian Runic-text Data Base (Rundata), Department of Scandinavian Languages, Uppsala University. Open Database License. Institute for Language and Folklore, place-name register, CC BY. Geological Survey of Sweden, shore-displacement model (the map).
- Image: Wikimedia Commons, with the photographer and the licence in the caption."""

for b in (body, body_en):
    assert not re.search(r"^\|", b, re.M), "BlogBody har inga tabeller"
    assert ":::" not in b and "/karta" not in b and "/statistik" not in b

out = {"slug": "de-gamla-landen-finnveden", "title": title, "summary": summary, "body": body,
       "title_en": title_en, "summary_en": summary_en, "body_en": body_en,
       "labels": ["Forskning", "Geografi", "Tro och magi"]}
from src import blog_labels  # noqa: E402
assert blog_labels.check(out["labels"]) is None, blog_labels.check(out["labels"])
path = os.path.join(ROOT, "utdata", "blogg", "finnveden.json")
json.dump(out, open(path, "w"), ensure_ascii=False, indent=1)
print(path, len(body.split()), "ord,", len(body_en.split()), "words")

if "--update" in sys.argv or "--write" in sys.argv:
    from api.routers import blog
    col = blog.firestore().collection(blog.COLLECTION)
    now = dt.datetime.now(dt.timezone.utc)
    if "--update" in sys.argv:
        doc = sys.argv[sys.argv.index("--update") + 1]
        ref = col.document(doc)
        old = ref.get().to_dict()
        assert old and not old.get("published"), "Bara opublicerade utkast skrivs över härifrån"
        ref.set({**out, "updatedAt": now}, merge=True)
        print("uppdaterat utkast:", doc)
    else:
        assert not [p for p in blog._all() if p.get("slug") == out["slug"]], "Adressen används redan; skriv över med --update"
        ref = col.document()
        ref.set({**out, "published": False, "month": now.strftime("%Y-%m"), "author": "Viktor Kvant",
                 "topic": "Geografi|finnveden", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
