"""Artikeln "De gamla landen: Attundaland – där man gjorde sina tingsplatser" (sv + en), en del i serien De gamla landen i
seriens atmosfäriska form (Viktor 2026-11-04): innerskärgården, byarna och gravfälten, Gerlögs arv på Hillersjöhällen,
tingsplatserna i Vallentuna, Bällsta och Granby, vägar och borgar, och stenarna som står i grupp. Landskapet låses mot
Det medeltida Sverige 1:5 och 1:7, inskrifterna mot Rundata och stenarna i grupp mot utdata/landprofiler/landprofiler.json
(plan eb59f631). Kartan: utdata/attundaland/karta_attundaland.R.
    ../../../.venv/bin/python build_attundaland.py [--write | --update DOC]"""
import datetime as dt
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_figures, commons  # noqa: E402

LP = json.load(open(os.path.join(ROOT, "utdata", "landprofiler", "landprofiler.json"), encoding="utf-8"))["tests"]
recs = {r["signum"]: r for r in json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["inscriptions"]}
nz = lambda s: recs[s]["normalization"].replace('"', "").strip()  # noqa: E731
pc = lambda x: round(100 * x)  # noqa: E731

# ---- the sources ------------------------------------------------------------------------------------------------------
DMS7 = open("/Volumes/2TB/Antigrvity/Runes/geografi_kallor/dms/dms_1_7_dedup.txt", encoding="utf-8").read()  # Ferm m fl 1992
DMS5 = open("/Volumes/2TB/Antigrvity/Runes/geografi_kallor/dms/dms_1_5_dedup.txt", encoding="utf-8").read()  # Rahmqvist & Skoglund 1986
for k in ("har det under hela forntiden haft karaktären av innerskärgård", "Svartsjölandet (Färingön) och Munsö",
          "ännu vid medeltidens början utgjort flera mindre öar", "finns rikligt med väldränerade jordarter",
          "ca 90 procent belägna inom", "20 fornborgar", "närmare 100 bevarade vikingatida runstenar",
          "Storhögar finns vid Husby i Bro sn (två)", "Kungshögen", "vid Runsa finns ovanligt också en monumental skeppssättning",
          "Hovgården på Adelsö, där fem storhögar", "där en vikingatida vägbank", "anknyter till en större hög",
          "invid detta är också en labyrint", "har en fornborg fomborg på Tunberget",
          "strategiskt läge vid landtungan mellan Edsviken och sjön Norrviken",
          "Adelsö socken, som hörde till Trögds härad i Fjädrundaland",
          "Bro härad, till vilket Färingö tingslag hörde, och Sollentuna härad ingick i Attundaland",
          "Häradets rätta tingsstad torde ha varit vid Granby", "Tingsplatsen bör ha legat på Granbys mark, ca 700 m",
          "Tingsstenarna", "Skandinaviens största höggravfält", "Kombinationen av omfattande kulturlager från tätortsbebyggelse",
          "stadsvall", "Upplands längsta runristning vid Hilleshög", "Ferm", "Stockholm 1992"):
    assert k in DMS7, k
assert "processionsväg" in DMS7 and "tolkad som" in DMS7
for k in ("Vid vikingatidens slut hade dessa uppgrundats eller avsnörts till insjöar", "smala, segelbara fjärdsystem",
          "det småbrutna lerslättsområdet söder och öster om sjön Erken", "där de praktiskt taget finns vid varje by",
          "vissa byar uppträder parvis under samma namn", "N och S Nånö i Estuna sn", "Tolv av dessa gravfält består av mera än 100",
          "Darsgärde i Skederids sn, är fullständigt", "talrika husgrunder och boplatsrester",
          "De flesta av fornborgarna visar dock inte några tecken", "skogsmark på något avstånd från", "V och Ö O Libby", "Stockholm 1986"):
    assert k in DMS5, k
HL = json.load(open(os.path.join(ROOT, "web", "src", "lib", "historiska_land.json"), encoding="utf-8"))
ATT = [r for r in HL["epoch"]["regions"] if r["id"] == "attundaland"][0]
assert "Sexårsgärden 1314 (SDHK 2593) räknar hit de åtta hundarena Bro, Sollentuna, Vallentuna, Seminghundra, Långhundra, Lyhundra, Ärlinghundra och Sjuhundra" in ATT["note"]
# the inscriptions
assert recs["U 29"]["place"] == "Hillersjö" and recs["U 29"]["parish"] == "Hilleshögs sn" and recs["U 29"]["object"] == "berghäll"
for k in ("GæiRmundr [f]ikk GæiRlaug møydomi i", "aðan hann drunknaði", "Ha[na] fikk Ragnfastr i Snutastaðum",
          "En moðiR kvam at sunaR arfi", "Þar kvam GæiRlaug at arfi Ingu, dottur sinnaR", "Þorbiorn Skald risti runaR"):
    assert k in nz("U 29"), k
assert recs["U 329"]["place"] == recs["U 330"]["place"] == recs["U 331"]["place"] == "Snottsta" and recs["U 329"]["parish"] == "Markims sn"
assert "Inga let ræisa stæina ok bro gærva æftiR Ragnfast, bonda sinn" in nz("U 330") and "Assurr vaR huskarl hans" in nz("U 330")
assert "Hann atti æinn by þenna æftiR Sigfast, faður sinn" in nz("U 331")
assert "ok þingstað þenna gærði, ok æinn atti allt hu[n]dari þetta" in nz("U 212") and recs["U 212"]["place"] == "Vallentuna kyrka"
assert "þæiR gærðu hiar þingstað" in nz("U 225") and "[M]unu æigi mærki mæiRi verða" in nz("U 225") and "Ulfs syniR" in nz("U 225")
assert recs["U 225"]["place"] == "Bällsta" and recs["U 225"]["parish"] == "Vallentuna sn"
G = "U RR1987;134"
assert recs[G]["place"] == "Granby" and recs[G]["parish"] == "Spånga sn" and recs[G]["object"] == "berghäll"
assert nz(G).startswith("Ingilaug let haggva hælli þessa æftiR sun sinn Sigfastr")
assert "ToliR bryti i roði kunungi" in nz("U 11") and recs["U 11"]["place"] == "Hovgården" and "Hakon bað rista" in nz("U 11")
assert "Iarlabanki" in nz("U 212") and "æinn atti allan Tæby" in nz("U 164") and "stæina þessa" in nz("U 164") and "stæina" in nz("U 330")
assert recs["U 331"]["object"] == "berghäll" and "Roðr" in recs["U 11"]["translation_en"]
# the stones in groups (the broad palette, plan eb59f631)
GR = [t for t in LP if t["unit"] == "attundaland" and t["kind"] == "land" and t["feature"] == "i_grupp"][0]
assert GR["holds"] and (GR["k_in"], GR["n_in"], pc(GR["share_in"]), pc(GR["share_out"])) == (57, 139, 41, 26)

# ---- pictures and map -------------------------------------------------------------------------------------------------
F29, F212 = "U 29, Hillersjö.jpg", "U 212 (side B), Vallentuna.JPG"
INFO = commons.commons_info([F29, F212])
assert INFO[F29]["licence"] == INFO[F212]["licence"] == "CC BY 2.5" and INFO[F29]["author"] == INFO[F212]["author"] == "Berig"
PAGE = {f: "https://commons.wikimedia.org/wiki/File:" + f.replace(" ", "_") for f in (F29, F212)}
MAP = {lang: blog_figures.freeze(open(os.path.join(ROOT, "utdata", "attundaland", f"karta_attundaland_{lang}.png"), "rb").read())
       for lang in ("sv", "en")}
RODEN, FJAD = "/artiklar/de-gamla-landen-roden", "/artiklar/de-gamla-landen-fjadrundaland"

title = "De gamla landen: Attundaland – där man gjorde sina tingsplatser"
summary = ("Attundaland var folklandet närmast Mälarens mynning: en innerskärgård av öar och djupa vikar, byar med sina "
           "gravfält och stormän som högg in i sten att de hade gjort tingsplatsen. Följ med till de åtta hundarena omkring "
           "år 1000. En del i serien De gamla landen.")

body = f"""Föreställ dig att du ror in mellan öarna i östra Mälaren för tusen år sedan. Det är ingen sjö du ror på utan en vik av havet, och landet runt dig är lågt. Holmar och skär ligger tätt, sunden är smala, och det som senare ska bli en enda stor ö, Färingö, är ännu flera mindre öar. Från Saltsjön i öster skär djupa vikar in i landet, och längre norrut ligger sjöar som nyss har varit havsvikar och fjärdar som fortfarande går att segla genom. Det här är Attundaland, det folkland som ligger närmast Mälarens mynning. Det har alltid varit en innerskärgård.

## Byarna och de döda

Gå i land där en dalgång möter vattnet. Där leran från de forna fjärdarna möter den grövre moränen är jorden lätt och torr, och där ligger gårdarna, en efter en, i takt med att landet har stigit ur havet. Längre norrut, kring sjön Erken, breder en småbruten lerslätt ut sig, och där ligger bygden tätast.

Föreställ dig byn: några gårdar kring en öppen plats, röken från husen, åkrarna nedanför och betet i skogsbrynet. Och på backen ovanför, de döda. Nästan nio av tio fornlämningar i Attundaland är gravar på järnålderns gravfält, och i de norra hundarena finns ett gravfält från yngre järnålder vid så gott som varje by. Tolv av dem rymmer mer än hundra gravar. Där finns också något som är typiskt för just den här bygden: byar som ligger parvis under samma namn, Norra och Södra Nånö, Västra och Östra Libby, var och en med sin egen bytomt och sitt eget gravfält.

Här och där reser sig något större. Vid Husby i Bro ligger två storhögar, vid Hersby i Sollentuna en hög som kallas Kungshögen, och vid Runsa i Ed en skeppssättning av resta stenar. Det var tecken på makt.

## Gerlögs arv

På en häll vid Hillersjö, på ön som senare ska bli Färingö, har någon huggit in den längsta runtext som finns i Uppland. Den börjar med en uppmaning till den som går förbi:

> *{nz("U 29")}*

Tyd! Germund fick Gerlög till hustru när hon var ung. Sedan fick de en son, innan han drunknade. Sedan dog sonen. Sedan fick hon Gudrik. … Sedan fick de barn, men bara en flicka levde; hon hette Inga. Henne fick Ragnfast i Snottsta. Sedan dog han, och sedan sonen. Och modern ärvde sin son. Sedan fick hon Erik. Där dog hon. Där ärvde Gerlög Inga, sin dotter. Torbjörn skald ristade runorna.

![Hillersjöhällen, U 29]({INFO[F29]['thumb']})
U 29, hällen vid Hillersjö. Foto: Berig, CC BY 2.5, via [Wikimedia Commons]({PAGE[F29]}).

Det är en hel släkts historia, men den är berättad för att visa en sak: vem som ärvde vem. Ordningen i vilken de dog avgjorde vem som ärvde gården, och det är troligen därför den ristades in i berget, synlig för alla. Ingas egen gård syns också. Vid Snottsta i Markim lät hon resa stenar och bygga en bro efter sin man Ragnfast, och skrev att han ”ensam ägde denna by efter Sigfast, sin fader”. Ragnfast hade en huskarl, Assur. Genom Ingas och Gerlögs stenar går det att följa en gård från far till son, från son till hustru, från hustru till mor.

## Tingsplatserna

Tvister om arv och jord avgjordes på tinget. Attundaland var indelat i åtta hundaren – Bro, Sollentuna, Vallentuna, Seminghundra, Långhundra, Lyhundra, Ärlinghundra och Sjuhundra – och varje hundare hade sin tingsplats. Här kan vi se hur en sådan plats kom till. Vid Vallentuna kyrka står en sten där storbonden Jarlabanke från Täby låter skriva:

> *{nz("U 212").split("§B")[1].strip()}*

Jarlabanke lät resa denna sten efter sig själv medan han levde, och gjorde denna tingsplats, och ensam ägde han hela detta hundare.

![Runstenen U 212 vid Vallentuna kyrka]({INFO[F212]['thumb']})
U 212 vid Vallentuna kyrka, sidan där Jarlabanke skriver att han gjorde tingsplatsen. Foto: Berig, CC BY 2.5, via [Wikimedia Commons]({PAGE[F212]}).

Han var inte ensam om att göra tingsplatser. Vid Bällsta, också i Vallentuna, skriver Ulvs söner – Arnkel, Gye och en tredje, kanske Ulvkel – att de ”gjorde här tingsplats” – och tillägger, med en sons stolthet, att inga minnesmärken ska bli större än de som de gjorde efter sin far. I Sollentuna hundare låg tinget på medeltiden vid Granby i Spånga, sannolikt vid de stenar som kallas Tingsstenarna, inte långt från en häll där en mor, Ingelög, lät hugga minnesord efter sin son Sigfast.

Föreställ dig tingsdagen: männen från byarna som samlas vid stenarna, vittnen som ska intyga ett köp, en arvstvist som ska avgöras. Och runt dem stenar med namn, som påminde om vem som hade gjort platsen och vem som ägde marken.

![Karta över Attundaland omkring år 1000 med runstenarna och platserna i texten]({MAP['sv']})
**Karta.** Attundaland omkring år 1000, då Mälaren var en vik av havet. Rostfärgat är Attundaland med öarna i Färingö tingslag, ljust grannlanden; gränserna är ungefärliga. Grå punkter är runstenar, ringar platser i texten. Karta: Vitki, efter SGU:s modell för strandförskjutningen år 1000, Institutet för språk och folkminnens ortnamnsregister och Rundata.

## Vägar, vatten och borgar

Det mesta färdades på vattnet. Men landvägar fanns, och en av dem är märklig. Vid Rösaring i Låssa går en vikingatida vägbank fram till en stor hög på ett åskrön, där det också finns en labyrint av stenar. Vägen har tolkats som en processionsväg. Vad som gick där vet vi inte.

Attundaland har ett tjugotal fornborgar. Några ligger vid Mälarens vattenleder. Tunbergets borg vid Edsberg har ett strategiskt läge vid den smala landtungan mellan Edsviken och Norrviken. Men de flesta borgarna ligger i skogen, en bit från bygden, och de flesta visar inga spår av att människor bott där länge. Kanske var de platser att fly till. En borg i Skederid, Darsgärde, har grävts ut helt; där fanns husgrunder och boplatslämningar från folkvandringstiden, flera hundra år före vikingatiden.

Och västerut, där Attundaland tar slut, ligger Björkö och Adelsö. På Björkö låg staden Birka, med stadsvall, borg, hamnar och Skandinaviens största gravfält med högar. På Adelsö, vid Hovgården, låg fem storhögar och en kungsgård, och där står en sten som säger att Tole var kungens bryte, hans förvaltare, i ”Roðr” – kanske Roden. Men Adelsö räknades på medeltiden till Trögd i [Fjädrundaland]({FJAD}), inte till Attundaland. Det mest kända stället i trakten låg alltså precis utanför landets gräns.

## Stenarna som står i grupp

Attundaland är fullt av runstenar. Bara i dess sydvästra del, kring Bro, Färingö och Sollentuna, finns nästan hundra bevarade runstenar från vikingatiden. Och de står ofta tillsammans: av Attundalands runstenar står fyra av tio i en grupp med andra stenar, mot en av fyra i resten av Uppland. Jarlabanke reste flera stenar vid sin bro i Täby, och Inga reste flera vid Snottsta. En sten räckte inte. Man reste flera, vid vägen, vid bron, vid tinget, så att den som kom förbi inte kunde undgå dem.

## Ett land av ting och arv

Det är lätt att se Attundaland som runstenarnas land, och det är det. Men stenarna berättar om något mer än de döda. De berättar om gårdar som gick i arv och om ordningen för hur det skulle gå till, om tingsplatser som någon hade gjort och om män och kvinnor som ville att alla skulle veta vem som ägde vad. Det här var ett land där jorden var värd att skriva om. Den som står vid Hillersjöhällen och läser Gerlögs historia står mitt i det: en mor som överlevde sina barn och ärvde dem, berättat i berget så att ingen skulle kunna säga emot.

Jarlabanke och hans bro har vi mött förut, i [Roden]({RODEN}), kustlandet. Hans Täby låg i Roden, men tinget han gjorde låg i Attundaland.

## Så vet vi det

Landskapet, gravfälten, borgarna och tingsplatserna bygger på *Det medeltida Sverige* (häftena om Lyhundra och Sjuhundra och om Bro, Färingö, Adelsö och Sollentuna), inskrifterna på Rundata. Tingsplatsen vid Granby och hundarenas namn är kända från medeltiden; att hundarena fanns redan på vikingatiden visar Jarlabankes egen sten. Att stenarna står i grupp har vi mätt i en jämförelse av alla land, där skillnaden mot resten av Uppland stod sig. Två saker att veta: öarna i Färingö tingslag, som på medeltiden hörde till Bro hundare, saknas i den jämförelsen eftersom Vitkis landindelning inte räknar dem till något folkland, och Birka och Hovgården räknas inte hit, eftersom Adelsö hörde till Trögd. Planen och beräkningarna finns öppna på GitHub, länkade nedan.

## Källor

- Rahmqvist, Sigurd & Skoglund, Lars-Olof 1986. *Det medeltida Sverige* 1. Uppland 5. Attundaland: Lyhundra, Sjuhundra. Riksantikvarieämbetet.
- Ferm, Olle, Johansson, Mats & Rahmqvist, Sigurd 1992. *Det medeltida Sverige* 1. Uppland 7. Attundaland: Bro, Färingö, Adelsö, Sollentuna. Riksantikvarieämbetet.
- Sexårsgärden 1314, Svenskt diplomatariums huvudkartotek (SDHK 2593), Riksarkivet.
- Samnordisk runtextdatabas (Rundata), Institutionen för nordiska språk, Uppsala universitet. Open Database License.
- Institutet för språk och folkminnen, ortnamnsregistret (PlaceNameService), socknar och härader. CC BY. Sveriges geologiska undersökning (SGU), strandförskjutningsmodell för år 1000 (kartan).
- Den låsta analysplanen och Vitkis beräkningar finns öppet på [GitHub](https://github.com/Precatio/runes) (analysplaner/2026-11-02-landprofiler.md).
- Bilder: Wikimedia Commons, med fotografen i bildtexten."""

title_en = "The old lands: Attundaland – where they made their assembly places"
summary_en = ("Attundaland was the folkland nearest the mouth of Lake Mälaren: an inner archipelago of islands and deep bays, "
              "villages with their grave fields, and great men who cut into stone that they had made the assembly place. Come "
              "to the eight hundreds around AD 1000. A part of the series The old lands.")

body_en = f"""Imagine rowing in among the islands of eastern Lake Mälaren a thousand years ago. It is no lake you are rowing on but a bay of the sea, and the land around you is low. Islets and skerries lie close together, the sounds are narrow, and what will later become one large island, Färingö, is still several smaller ones. From the Baltic in the east deep bays cut into the land, and further north lie lakes that were bays of the sea not long ago and inlets that can still be sailed through. This is Attundaland, the folkland nearest the mouth of Lake Mälaren. It has always been an inner archipelago.

## The villages and the dead

Go ashore where a valley meets the water. Where the clay of the old inlets meets the coarser moraine the soil is light and dry, and there lie the farms, one after another, as the land has risen from the sea. Further north, around Lake Erken, a broken clay plain spreads out, and there the settlement is densest.

Imagine the village: a few farms round an open space, the smoke from the houses, the fields below and the grazing at the edge of the forest. And on the slope above, the dead. Nearly nine in ten ancient monuments in Attundaland are graves on the grave fields of the Iron Age, and in the northern hundreds there is a Late Iron Age grave field by practically every village. Twelve of them hold more than a hundred graves. There is also something typical of just this district: villages that lie in pairs under the same name, North and South Nånö, West and East Libby, each with its own village site and its own grave field.

Here and there something larger rises. At Husby in Bro lie two great mounds, at Hersby in Sollentuna a mound called the King's Mound, and at Runsa in Ed a ship setting of standing stones. They were signs of power.

## Gerlög's inheritance

On a rock face at Hillersjö, on the island that will later become Färingö, someone has cut the longest runic text in Uppland. It begins with a call to whoever passes:

> *{nz("U 29")}*

Interpret! Geirmundr got Geirlaug to wife when she was a maiden. Then they had a son, before he drowned. Then the son died. Then she got Guðríkr. … Then they had children, but only one girl lived; she was called Inga. Ragnfastr of Snottsta got her. Then he died, and then the son. And the mother inherited from her son. Then she got Eiríkr. Then she died. Then Geirlaug inherited from Inga, her daughter. Þorbjôrn Skald carved the runes.

![The Hillersjö rock, U 29]({INFO[F29]['thumb']})
U 29, the rock at Hillersjö. Photo: Berig, CC BY 2.5, via [Wikimedia Commons]({PAGE[F29]}).

It is the history of a whole family, but it is told to show one thing: who inherited from whom. The order in which they died decided who inherited the farm, and that is probably why it was cut into the rock, for everyone to see. Inga's own farm can be seen too. At Snottsta in Markim she had stones raised and a bridge built for her husband Ragnfast, and wrote that he "alone owned this village after Sigfast, his father". Ragnfast had a housecarl, Assur. Through Inga's and Geirlaug's stones a farm can be followed from father to son, from son to wife, from wife to mother.

## The assembly places

Disputes over inheritance and land were settled at the assembly. Attundaland was divided into eight hundreds – Bro, Sollentuna, Vallentuna, Seminghundra, Långhundra, Lyhundra, Ärlinghundra and Sjuhundra – and each hundred had its assembly place. Here we can see how such a place came about. At Vallentuna church stands a stone on which the great farmer Jarlabanke of Täby has it written:

> *{nz("U 212").split("§B")[1].strip()}*

Jarlabanke had this stone raised in memory of himself while alive, and made this assembly place, and alone owned all of this hundred.

![The runestone U 212 at Vallentuna church]({INFO[F212]['thumb']})
U 212 at Vallentuna church, the side on which Jarlabanke writes that he made the assembly place. Photo: Berig, CC BY 2.5, via [Wikimedia Commons]({PAGE[F212]}).

He was not alone in making assembly places. At Bällsta, also in Vallentuna, Ulf's sons – Arnkell, Gye and a third, perhaps Ulfkell – write that they "made here an assembly place" – and add, with a son's pride, that no memorials shall be greater than those they made for their father. In the hundred of Sollentuna the assembly met in the Middle Ages at Granby in Spånga, probably by the stones called Tingsstenarna, the Assembly Stones, not far from a rock on which a mother, Ingelög, had words cut in memory of her son Sigfast.

Imagine the assembly day: the men from the villages gathering by the stones, witnesses who are to confirm a purchase, an inheritance dispute to be settled. And around them stones with names, reminding everyone who had made the place and who owned the land.

![Map of Attundaland around AD 1000 with the runestones and the places in the text]({MAP['en']})
**Map.** Attundaland around AD 1000, when Lake Mälaren was a bay of the sea. Rust is Attundaland with the islands of Färingö, light the neighbouring lands; the borders are approximate. Grey points are runestones, rings places in the text. Map: Vitki, after the Geological Survey of Sweden's shore-displacement model for AD 1000, the place-name register of the Institute for Language and Folklore, and Rundata.

## Roads, water and forts

Most travel went by water. But there were roads on land, and one of them is remarkable. At Rösaring in Låssa a Viking-age road embankment runs up to a large mound on a ridge crest, where there is also a labyrinth of stones. The road has been interpreted as a processional way. What went along it we do not know.

Attundaland has some twenty hillforts. Some lie by the waterways of Lake Mälaren. The fort on Tunberget at Edsberg has a strategic position on the narrow neck of land between Edsviken and Norrviken. But most of the forts lie in the forest, some way from the settlement, and most show no sign that people lived there for long. Perhaps they were places to flee to. One fort in Skederid, Darsgärde, has been fully excavated; there were house foundations and settlement remains from the Migration Period, several hundred years before the Viking Age.

And to the west, where Attundaland ends, lie Björkö and Adelsö. On Björkö lay the town of Birka, with a town rampart, a fort, harbours and Scandinavia's largest cemetery of mounds. On Adelsö, at Hovgården, lay five great mounds and a royal estate, and there stands a stone that says Toli was the king's bryti, his steward, in "Roðr" – perhaps Roden. But Adelsö was counted in the Middle Ages to Trögd in [Fjädrundaland]({FJAD}), not to Attundaland. The best-known place in the district lay just outside the land's border.

## The stones that stand in groups

Attundaland is full of runestones. In its south-western part alone, around Bro, Färingö and Sollentuna, there are nearly a hundred preserved runestones from the Viking Age. And they often stand together: of Attundaland's runestones four in ten stand in a group with other stones, against one in four in the rest of Uppland. Jarlabanke raised several stones at his bridge in Täby, and Inga raised several at Snottsta. One stone was not enough. People raised several, by the road, by the bridge, by the assembly, so that whoever passed could not miss them.

## A land of assemblies and inheritance

It is easy to see Attundaland as the land of runestones, and it is. But the stones tell of more than the dead. They tell of farms that passed by inheritance and of the order for how that should happen, of assembly places that someone had made and of men and women who wanted everyone to know who owned what. This was a land where the land was worth writing about. Whoever stands by the Hillersjö rock and reads Geirlaug's story stands in the middle of it: a mother who outlived her children and inherited from them, told in the rock so that no one could gainsay it.

Jarlabanke and his bridge we have met before, in [Roden]({RODEN}), the coastal land. His Täby lay in Roden, but the assembly place he made lay in Attundaland.

## How we know

The landscape, the grave fields, the forts and the assembly places rest on *Det medeltida Sverige* (the volumes on Lyhundra and Sjuhundra and on Bro, Färingö, Adelsö and Sollentuna), the inscriptions on Rundata. The assembly place at Granby and the names of the hundreds are known from the Middle Ages; that the hundreds existed already in the Viking Age is shown by Jarlabanke's own stone. That the stones stand in groups we have measured in a comparison of all the lands, where the difference from the rest of Uppland held. Two things to know: the islands of Färingö, which in the Middle Ages belonged to the hundred of Bro, are missing from that comparison because Vitki's division into lands does not count them to any folkland, and Birka and Hovgården are not counted here, since Adelsö belonged to Trögd. The plan and the calculations are open on GitHub, linked below.

## Sources

- Rahmqvist, Sigurd & Skoglund, Lars-Olof 1986. *Det medeltida Sverige* 1. Uppland 5. Attundaland: Lyhundra, Sjuhundra. Swedish National Heritage Board.
- Ferm, Olle, Johansson, Mats & Rahmqvist, Sigurd 1992. *Det medeltida Sverige* 1. Uppland 7. Attundaland: Bro, Färingö, Adelsö, Sollentuna. Swedish National Heritage Board.
- The six-year tithe of 1314, Svenskt diplomatariums huvudkartotek (SDHK 2593), National Archives of Sweden.
- Scandinavian Runic-text Data Base (Rundata), Department of Scandinavian Languages, Uppsala University. Open Database License.
- Institute for Language and Folklore, place-name register (PlaceNameService), parishes and hundreds. CC BY. Geological Survey of Sweden (SGU), shore-displacement model for AD 1000 (the map).
- The locked analysis plan and Vitki's calculations are open on [GitHub](https://github.com/Precatio/runes) (analysplaner/2026-11-02-landprofiler.md).
- Images: Wikimedia Commons, with the photographer in the caption."""

for b in (body, body_en):
    assert not re.search(r"^\|", b, re.M), "BlogBody har inga tabeller"
    assert ":::" not in b and "/karta" not in b and "/statistik" not in b

out = {"slug": "de-gamla-landen-attundaland", "title": title, "summary": summary, "body": body,
       "title_en": title_en, "summary_en": summary_en, "body_en": body_en,
       "labels": ["Forskning", "Geografi", "Kvinnor och barn"]}
from src import blog_labels  # noqa: E402
assert blog_labels.check(out["labels"]) is None, blog_labels.check(out["labels"])
path = os.path.join(ROOT, "utdata", "blogg", "attundaland.json")
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
                 "topic": "Geografi|attundaland", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
