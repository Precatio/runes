"""Artikeln "De gamla landen: Möre – kusten vid sundet" (sv + en), en del i serien De gamla landen i seriens atmosfäriska
form (Viktor 2026-11-04). Möre omkring år 1000: Kalmarsund, slätten och skogen, byarna vid åarna, gravarna, Hossmo och Hagby,
tinget och lagen (Östgöta lagsaga), silvret och tron. Varje uppgift är ett ordagrant citat ur källorna i
/Volumes/2TB/Antigrvity/Runes/downloads/smaland_lit (NOTES.md, insamlat 2026-11-04) och kontrolleras nedan som en delsträng
av källans text med blanktecknen sammanslagna. Kartan: utdata/gamla_landen/karta_land.R med more.json.
    ../../../.venv/bin/python build_more.py [--write | --update DOC]"""
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


DMS, HOS, HIK, KUL, RIH, FV25, ALM = ("dms_4_1_raw.txt", "KLM_Hossmo_vallgrav_del2_col.txt", "Hikuin_Andersson_Kalmarkusten_col.txt",
                                      "Kulltorp_E22_2000-1_col.txt", "RI_Kalmar-H.txt", "Fv2025_Hennius_blastugn_col.txt",
                                      "Almquist1954_Lagsagor_del1.txt")
FACTS = [
    (HIK, "Nära intill kusten gick den urgamla segelleden norrut"),
    (HIK, "En mycket stor del av all samfärdsel mellan Västeuropa och övre Östersjön torde ha passerat Kalmarsund under tidig medeltid"),
    (HIK, "Vid kusten många skyddade hamnlägen"), (RIH, "där passagen över till Öland är som närmast"),
    (DMS, "900 (omkr) Meore (Wulfstan s 25)."), (KUL, "Namnet betyder sankmark och syftar på de våtmarksområden som förr var karaktäristiska för landskapet."),
    (DMS, "Slätten har i äldre tid haft ett inte obetydligt inslag av grunda kärr- och sankmarker,"),
    (DMS, "Slättbygden, som bildar en tre till åtta kilometer bred"),
    (DMS, "remsa utmed kusten, täcks av bördig åkermark, bestående av kalkrik lera på sandstensbotten."),
    (DMS, "Skogsbygden är rik på sjöar, kärr och myrmarker."), (DMS, "I skogslandet finns totalt endast ca 25 fornlämningar"),
    (DMS, "Möres kustbygd utgör ett ovanligt gott exempel på en väl avgränsad odlingsbygd"),
    (DMS, "Möre begränsas i söder av Brömsebäck och stora skogsområden, i sydväst av Lyckebyån, i väster och nordväst av vidsträckta skogar och i norr av Nävraån."),
    (HOS, "Mören bör ha varit en enorm tillgång vid insamlandet av vinterfoder."),
    (HOS, "Bebyggelsen koncentrerades i området Kalmar, Dörby, Ljungby, Hossmo, Arby, Hagby och Voxtorps socknar."),
    (HOS, "Tillgången till vattenleder verkar ha varit en central anledning till att byarna lokaliserades till dessa platser"),
    (HOS, "Få hus har hittats från yngre järnålder i Möre."),
    (DMS, "I slättbygden dominerar vid medeltidens slut byar om 4 till 7 gårdar"),
    (DMS, "Den största byn i hela Möre är Ljungby kyrkby med grannbyn Olvingstorp som den näst största."),
    (DMS, "där ortnamnen huvudsakligen är av medeltida typ."),
    (DMS, "Gravfälten i Möre uppvisar en rik variation på konstruktioner och typer."), (DMS, "Rösen kan ingå, domarringar och resta stenar är vanliga"),
    (DMS, "Markanta gravfält av denna typ finns längs åsryggen i Harby-området i Ljungby"),
    (HOS, "Vad som återbördades av järnföremålen var 8 svärd, 7 spjutspetsar, 5 pilspetsar och en yxa."),
    (HOS, "Förutom dessa föremål fanns 8 spelbrickor av bärnsten samt 450 stycken pärlor av olika material."),
    (HOS, "Fyra av gravarna innehöll ett keramikkärl som troligtvis innehållit mat eller dryck"),
    (DMS, "Rösena är ofta 20 m eller mera i diameter."),
    (HIK, "Hossmo vid åns mynning har av allt att döma varit en föregångare till Kalmar som marknad och boplats"),
    (HIK, "som före 1178 tycks ha överlåtits till linköpingsbiskopen"), (HIK, "Där fanns under tidig medeltid en husaby, d.v.s. en kungsgård"),
    (HIK, "När Kalmar under 1200talets mitt börjar bli statens centrala förvaltningsort i Möre"),
    (DMS, "domarringar och resta stenar är vanliga, rektangulära och skeppsformiga stenkretsar förekommer"),
    (HOS, "Av sin analys kommer Brink fram till att Möres centrala delar under järnåldern varit Hossmo-Ljungby-Dörby"),
    (HIK, "Hagby, mitt i den rikaste jordbruksbygden, har troligen tidigt varit en viktig hamn och mötesplats"),
    (RIH, "farledsspärrar i åmynningen vittnar om Ljungbyån som tidig transportled"),
    (HIK, "börjar bli statens centrala förvaltningsort i Möre"),
    (HIK, "De olika bygderna har troligen vid medeltidens början haft stor egen självständighet och bl a bildat egna tingssocknar"),
    (HIK, "till mellansverige och i synnerhet till Östergötland, genom tillhörighet till Östgöta lagsaga och Linköpings stift."),
    (DMS, "Norra och Södra Möre tillhörde Östgöta lagsaga fram till 1559"),
    (ALM, "Smålands lagsaga tillkom 1559, då Svante Sture förordnades till lagman över vissa småländska härad, som tidigare lytt under östgöta lagman"),
    (DMS, "Landsting omtalas 1393 och 1521 i Dörby"),
    (HOS, "Smedby skulle visa på en hantverksplats och Tingby var platsen där ting hölls."),
    (DMS, "Denna bygd fortsätter i Värends sydöstra skogsbygd."),
    (HIK, "Kristendomens första nedslag i bygden markeras tydligast av de korsförsedda runstenarna från Arby, Ljungby, Kalmar och Ryssby"),
    (HIK, "Att kristendomen skulle ha varit djupare förankrad i bygden vid 1100-talets början, är dock knappast troligt."),
    (HIK, "Till Hagby knyts också legender om den helige Sigfrids landsstigning och mission"),
    (HOS, "Här har skatter deponerats ända fram i slutet av 1100-talet och början av 1200-talet."),
    (HIK, "Från Voxtorp finns 2 vikingatida skattfynd av arabiska mynt"),
    (HIK, "Här restes en imponerande rad av fasta kyrkborgar"),
    (DMS, "Om denna sena utvidgning av bygden vittnar närmare 400 kända lokaler,"),
    (DMS, "men det är inte uteslutet att vissa lokaler utnyttjats under sen vikingatid."),
    (FV25, "Kalibreringen visar på en kontinuerlig småskalig produktion under hela äldre järnåldern som minskade under yngre järnålder."),
    (HIK, "tillgång på myrmalm, som tidigt utvanns och under medeltiden blev en av Kalmars viktigare exportprodukter."),
]
for fil, q in FACTS:
    said(fil, q)

# ---- picture and map --------------------------------------------------------------------------------------------------
FS = "Strait of Kalmar.jpg"
INFO = commons.commons_info([FS])
assert (INFO[FS]["licence"], INFO[FS]["author"]) == ("CC BY-SA 4.0", "Pillemausaren")
LIC = f"[{INFO[FS]['licence']}]({INFO[FS]['licence_url']})" if INFO[FS].get("licence_url") else INFO[FS]["licence"]
PAGE = "https://commons.wikimedia.org/wiki/File:" + FS.replace(" ", "_")
MAP = {lang: blog_figures.freeze(open(os.path.join(ROOT, "utdata", "gamla_landen", f"karta_more_{lang}.png"), "rb").read())
       for lang in ("sv", "en")}
VAREND = "/artiklar/de-gamla-landen-varend"

title = "De gamla landen: Möre – kusten vid sundet"
summary = ("Möre var kustlandet vid Kalmarsund: en smal slätt av bördig lera mellan skogen och havet, där byarna låg vid åarna "
           "och skeppen gick förbi utanför. Det hörde inte till Smålands små land utan till Östergötlands lag. Följ med dit "
           "omkring år 1000. En del i serien De gamla landen.")

body = f"""Öland ligger långt och lågt på andra sidan Kalmarsund. Genom sundet går för tusen år sedan den gamla segelleden, nära kusten, och här passerar en stor del av alla som färdas mellan Västeuropa och de norra delarna av Östersjön. Kusten har gott om skyddade lägen att lägga till vid. Där sundet är som smalast, vid Ryssby, är det bara en kort färd över till Öland.

Landet du ser till vänster heter Möre. Namnet finns redan i en reseberättelse från omkring år 900, där sjöfararen Wulfstan kallar det *Meore*. Det betyder sankmark. Kärren och de låga våtmarkerna, mörarna, präglade landet.

![Kalmarsund]({INFO[FS]['thumb']})
Kalmarsund. Foto: Pillemausaren, {LIC}, via [Wikimedia Commons]({PAGE}).

## Slätten och skogen

Möre är smalt. Längs kusten löper en slätt, tre till åtta kilometer bred, av bördig, kalkrik lera på en botten av sandsten. Där ligger åkrarna. Innanför tar skogen vid, rik på sjöar, kärr och myrar, och där har människor knappt lämnat några spår: i hela skogslandet finns bara ett tjugofemtal fornlämningar. Kustbygden är ett ovanligt tydligt avgränsat land, med Brömsebäck i söder, Nävraån i norr och stora skogar i väster. Där skogen tar slut i väster börjar [Värend]({VAREND}).

Föreställ dig sensommaren på slätten: slåttern på de sanka ängarna, där den stora våtmarken Mören vid Ljungby ger vinterfoder åt djuren. Kärren som gav landet dess namn var inte ödemark utan rikedom.

## Byarna vid åarna

Bygden samlas kring åarnas nedre lopp, i det som senare blir socknarna Kalmar, Dörby, Ljungby, Hossmo, Arby, Hagby och Voxtorp. Byarna ligger där vattenvägarna går, för åarna är vägar in i landet. På medeltiden har byarna på slätten fyra till sju gårdar, och den största är Ljungby kyrkby. Ute i skogen ligger gårdarna var för sig, och deras namn är oftast medeltida. Hur husen såg ut vet vi inte: få hus från den här tiden har hittats i Möre.

## De döda

Gravfälten i Möre är varierade. I de stora gravfälten blandas rösen, domarringar, resta stenar och skeppsformiga stenkretsar, gravar från många olika tider. Från yngre järnåldern finns gravfält med högar längs åsryggen vid Harby i Ljungby. Ett av dem plundrades på 1870-talet, och det som kom tillbaka var rikt: åtta svärd, sju spjutspetsar, fem pilspetsar och en yxa, åtta spelbrickor av bärnsten och 450 pärlor. På andra sidan ån, vid Binga, var gravarna enkla och omarkerade, och i fyra av dem stod ett lerkärl som troligen innehållit mat eller dryck åt den döde.

Längs kusten ligger också stora rösen, tjugo meter breda eller mer. De är från bronsåldern. Den som rodde längs Möres kust omkring år 1000 såg dem som minnen från en tid ingen längre kunde berätta om.

## Hossmo och Hagby

Vid Ljungbyåns mynning ligger Hossmo. Arkeologen Karin Andersson menar att platsen av allt att döma var en föregångare till Kalmar, som marknad och boplats. Under tidig medeltid fanns där en husaby, en kungsgård, som före 1178 tycks ha överlåtits till biskopen i Linköping. Spärrar i åmynningen visar att Ljungbyån tidigt var en transportled. Ortnamnsforskaren Stefan Brink har kommit fram till att Möres kärna under järnåldern låg kring Hossmo, Ljungby och Dörby.

Söderut, mitt i den rikaste jordbruksbygden, ligger Hagby, som troligen tidigt var en viktig hamn och mötesplats. Det är där legenden låter Sankt Sigfrid stiga i land för att predika. Kalmar tar över först från mitten av 1200-talet, då staden blir kungamaktens förvaltningsort i Möre.

![Karta över Möre omkring år 1000 med runstenarna och platserna i texten]({MAP['sv']})
**Karta.** Möre omkring år 1000. Rostfärgat är Norra och Södra Möre härader, ljust grannlanden; gränserna är ungefärliga. Grå punkter är runstenar, ringar platser i texten. Karta: Vitki, efter SGU:s modell för strandförskjutningen år 1000, Institutet för språk och folkminnens ortnamnsregister och Rundata.

## Tinget och lagen

Bygderna i Möre hade troligen stor självständighet när medeltiden började, med egna tingssocknar. I Dörby finns namnen Tingby och Smedby, som har tolkats som platsen där tinget hölls och en hantverksplats. Landsting omtalas i Dörby 1393 och 1521.

Men Möre hörde inte till de småländska landen. Det dömdes efter östgötsk lag och hörde till Linköpings stift. Norra och Södra Möre tillhörde Östgöta lagsaga ända till 1559, då Smålands lagsaga bildades. Kusten vid sundet hade sin väg till makten norrut, inte västerut genom skogen.

## Silvret och tron

I Voxtorp har två vikingatida skatter av arabiska mynt hittats, och i Möre fortsatte man att gräva ner silver ovanligt länge, ända in i början av 1200-talet. Kristendomen kom men slog rot långsamt. De första tecknen är runstenar med kors, från Arby, Ljungby, Kalmar och Ryssby. Att tron skulle ha varit djupare förankrad i bygden i början av 1100-talet är enligt Andersson knappast troligt. Senare byggdes en rad kyrkor längs kusten som borgar.

Och järnet? Det finns närmare fyrahundra platser i Möre där man framställt järn ur myrmalm, men de flesta är medeltida, även om några kan ha använts redan under sen vikingatid. I hela Kalmar län minskade järnframställningen under yngre järnåldern. Myrmalmen blev viktig först senare, som en av Kalmars exportvaror.

## Ett land vid sundet

Möre omkring år 1000 är ett smalt land mellan skogen och havet. Byarna ligger vid åarna, åkrarna på leran, ängarna i kärren. Utanför går skeppen, och vid Hossmo och Hagby lägger de till. Landet har sina egna ting och sin egen väg till makten, norrut mot Östergötland. Den som står vid Ljungbyåns mynning och ser ut över sundet står där Möres kärna låg, innan Kalmar fanns.

## Så vet vi det

Landskapet, byarna, tinget och lagsagan bygger på *Det medeltida Sverige* om Möre och på Karin Anderssons studie av Kalmarkustens kyrkor; Hossmo och Harby på en sammanställning från Kalmar läns museum, som i sin tur bygger på andra forskares arbeten. Att Hossmo var en föregångare till Kalmar är en tolkning, och fynden från Harby kom fram när gravfältet plundrades, så sammanhangen är oklara. Mycket av det vi vet om tinget och lagen är känt först från medeltiden. Länkarna till källorna finns nedan.

## Källor

- Ferm, Olle, Rahmqvist, Sigurd & Thor, Lars 1987. *Det medeltida Sverige* 4. Småland 1. Möre: Norra och Södra Möre, Kalmar stad. Riksantikvarieämbetet.
- Andersson, Karin 1983. Kalmarkustens kyrkor under tidig medeltid. *Hikuin* 9, s. 189–202.
- Wennerström, Ulrika (u.å.). *Hossmo under yngre järnålder och tidig medeltid*. Kalmar läns museum.
- Hallgren, A.-L. m.fl. 2000. *Kulltorp. Ett gravfält från förromersk järnålder*. Kalmar läns museum.
- Almquist, Jan Eric 1954. *Lagsagor och domsagor i Sverige* I. Stockholm.
- Hennius, Andreas m.fl. 2025. Järnframställning i blästugn – en uppdaterad kronologi. *Fornvännen* 120.
- Riksantikvarieämbetet. *Riksintressen för kulturmiljövården – Kalmar län*.
- Samnordisk runtextdatabas (Rundata), Institutionen för nordiska språk, Uppsala universitet. Open Database License. Institutet för språk och folkminnen, ortnamnsregistret, CC BY. Sveriges geologiska undersökning, strandförskjutningsmodell (kartan).
- Bild: Wikimedia Commons, med fotografen och licensen i bildtexten."""

title_en = "The old lands: Möre – the coast by the sound"
summary_en = ("Möre was the coastal land by the Kalmar Sound: a narrow plain of fertile clay between the forest and the sea, where the "
              "villages lay by the rivers and the ships went by offshore. It did not belong to Småland's small lands but to the law "
              "of Östergötland. Come along around AD 1000. A part of the series The old lands.")

body_en = f"""Öland lies long and low on the far side of the Kalmar Sound. A thousand years ago the old sailing route runs through the sound, close to the coast, and much of all the traffic between Western Europe and the northern Baltic passes here. The coast has plenty of sheltered places to put in. Where the sound is narrowest, at Ryssby, it is only a short crossing to Öland.

The land you see to the left is called Möre. The name occurs already in a travel account from around 900, where the seafarer Wulfstan calls it *Meore*. It means marshland. The fens and the low wetlands, the *mörar*, marked the land.

![The Kalmar Sound]({INFO[FS]['thumb']})
The Kalmar Sound. Photo: Pillemausaren, {LIC}, via [Wikimedia Commons]({PAGE}).

## The plain and the forest

Möre is narrow. Along the coast runs a plain, three to eight kilometres wide, of fertile, lime-rich clay on a bed of sandstone. There lie the fields. Inland the forest takes over, rich in lakes, fens and bogs, and there people have left hardly any traces: in the whole forest land there are only some twenty-five ancient monuments. The coastal district is an unusually well-bounded land, with Brömsebäck to the south, the Nävraån to the north and great forests to the west. Where the forest ends in the west, [Värend]({VAREND}) begins.

Imagine late summer on the plain: the haymaking on the wet meadows, where the great wetland of Mören at Ljungby gives winter fodder for the animals. The fens that gave the land its name were not wasteland but wealth.

## The villages by the rivers

The settlement gathers round the lower courses of the rivers, in what will later be the parishes of Kalmar, Dörby, Ljungby, Hossmo, Arby, Hagby and Voxtorp. The villages lie where the waterways run, for the rivers are roads into the land. In the Middle Ages the villages on the plain have four to seven farms, and the largest is Ljungby church village. Out in the forest the farms lie on their own, and their names are mostly medieval. What the houses looked like we do not know: few houses from this time have been found in Möre.

## The dead

The grave fields in Möre are varied. In the large grave fields cairns, stone circles, standing stones and ship-shaped settings mix, graves from many different times. From the Late Iron Age there are grave fields with mounds along the ridge at Harby in Ljungby. One of them was plundered in the 1870s, and what came back was rich: eight swords, seven spearheads, five arrowheads and an axe, eight amber gaming pieces and 450 beads. On the other side of the river, at Binga, the graves were simple and unmarked, and in four of them stood a clay pot that probably held food or drink for the dead.

Along the coast there are also great cairns, twenty metres across or more. They are from the Bronze Age. Whoever rowed along the coast of Möre around AD 1000 saw them as memorials from a time no one could tell of any more.

## Hossmo and Hagby

At the mouth of the Ljungbyån lies Hossmo. The archaeologist Karin Andersson argues that the place was by all appearances a forerunner of Kalmar, as a market and a settlement. In the early Middle Ages there was a husaby there, a royal estate, which before 1178 seems to have been handed over to the bishop of Linköping. Barriers in the river mouth show that the Ljungbyån was early a route for transport. The place-name scholar Stefan Brink has concluded that the core of Möre in the Iron Age lay round Hossmo, Ljungby and Dörby.

To the south, in the middle of the richest farmland, lies Hagby, which was probably early an important harbour and meeting place. It is there the legend has St Sigfrid come ashore to preach. Kalmar takes over only from the middle of the thirteenth century, when the town becomes royal power's seat of administration in Möre.

![Map of Möre around AD 1000 with the runestones and the places in the text]({MAP['en']})
**Map.** Möre around AD 1000. Rust is the hundreds of North and South Möre, light the neighbouring lands; the borders are approximate. Grey points are runestones, rings places in the text. Map: Vitki, after the Geological Survey of Sweden's shore-displacement model for AD 1000, the place-name register of the Institute for Language and Folklore, and Rundata.

## The assembly and the law

The districts of Möre probably had great independence when the Middle Ages began, with assembly parishes of their own. At Dörby there are the names Tingby and Smedby, which have been read as the place where the assembly met and a craft site. A land assembly is mentioned at Dörby in 1393 and 1521.

But Möre did not belong to the lands of Småland. It was judged by the law of Östergötland and belonged to the diocese of Linköping. North and South Möre belonged to the law province of Östergötland right up to 1559, when the law province of Småland was formed. The coast by the sound had its road to power to the north, not west through the forest.

## The silver and the faith

At Voxtorp two Viking-age hoards of Arabic coins have been found, and in Möre people went on burying silver unusually long, right into the early thirteenth century. Christianity came but took root slowly. The first signs are runestones with crosses, from Arby, Ljungby, Kalmar and Ryssby. That the faith was more deeply rooted in the district by the early twelfth century is, according to Andersson, hardly likely. Later a row of churches was built along the coast as fortresses.

And the iron? There are close to four hundred places in Möre where iron was made from bog ore, but most are medieval, even if some may have been used already in the late Viking Age. In the whole of Kalmar county iron production declined during the Late Iron Age. The bog ore became important only later, as one of Kalmar's exports.

## A land by the sound

Möre around AD 1000 is a narrow land between the forest and the sea. The villages lie by the rivers, the fields on the clay, the meadows in the fens. Offshore the ships go by, and at Hossmo and Hagby they put in. The land has its own assemblies and its own road to power, north towards Östergötland. Whoever stands at the mouth of the Ljungbyån and looks out over the sound stands where the core of Möre lay, before Kalmar existed.

## How we know

The landscape, the villages, the assembly and the law province rest on *Det medeltida Sverige* on Möre and on Karin Andersson's study of the churches of the Kalmar coast; Hossmo and Harby on a compilation from Kalmar County Museum, which in turn builds on other researchers' work. That Hossmo was a forerunner of Kalmar is an interpretation, and the finds from Harby came to light when the grave field was plundered, so their contexts are unclear. Much of what we know about the assembly and the law is known only from the Middle Ages. The sources are listed below.

## Sources

- Ferm, Olle, Rahmqvist, Sigurd & Thor, Lars 1987. *Det medeltida Sverige* 4. Småland 1. Möre: Norra och Södra Möre, Kalmar stad. Swedish National Heritage Board.
- Andersson, Karin 1983. Kalmarkustens kyrkor under tidig medeltid. *Hikuin* 9, pp. 189–202.
- Wennerström, Ulrika (n.d.). *Hossmo under yngre järnålder och tidig medeltid*. Kalmar County Museum.
- Hallgren, A.-L. et al. 2000. *Kulltorp. Ett gravfält från förromersk järnålder*. Kalmar County Museum.
- Almquist, Jan Eric 1954. *Lagsagor och domsagor i Sverige* I. Stockholm.
- Hennius, Andreas et al. 2025. Järnframställning i blästugn – en uppdaterad kronologi. *Fornvännen* 120.
- Swedish National Heritage Board. *Riksintressen för kulturmiljövården – Kalmar län*.
- Scandinavian Runic-text Data Base (Rundata), Department of Scandinavian Languages, Uppsala University. Open Database License. Institute for Language and Folklore, place-name register, CC BY. Geological Survey of Sweden, shore-displacement model (the map).
- Image: Wikimedia Commons, with the photographer and the licence in the caption."""

for b in (body, body_en):
    assert not re.search(r"^\|", b, re.M), "BlogBody har inga tabeller"
    assert ":::" not in b and "/karta" not in b and "/statistik" not in b

out = {"slug": "de-gamla-landen-more", "title": title, "summary": summary, "body": body,
       "title_en": title_en, "summary_en": summary_en, "body_en": body_en,
       "labels": ["Forskning", "Geografi", "Tro och magi"]}
from src import blog_labels  # noqa: E402
assert blog_labels.check(out["labels"]) is None, blog_labels.check(out["labels"])
path = os.path.join(ROOT, "utdata", "blogg", "more.json")
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
                 "topic": "Geografi|more", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
