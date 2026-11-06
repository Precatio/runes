"""Artikeln "De gamla landen: Gotland – ett eget land mitt i havet" (sv + en), en del i serien De gamla landen i seriens
atmosfäriska form (Viktor 2026-11-04). Gotland omkring år 1000: Paviken och Västergarn, gårdarna som flyttade, silvret,
hamnarna, bildstenarna vid vägarna, tingen och Gutnaltinget, skatten till sveakungen, borgarna och tron. Varje uppgift är ett
ordagrant citat ur källorna i /Volumes/2TB/Antigrvity/Runes/downloads/gotland_lit (NOTES.md, insamlat 2026-11-04) och
kontrolleras nedan som en delsträng av källans text med blanktecknen sammanslagna; inskrifterna mot Rundata. Kartan:
utdata/gamla_landen/karta_land.R med gotland.json.
    ../../../.venv/bin/python build_gotland_land.py [--write | --update DOC]"""
import datetime as dt
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_figures, commons  # noqa: E402

recs = {r["signum"]: r for r in json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["inscriptions"]}
nz = lambda s: recs[s]["normalization"].replace('"', "").strip()  # noqa: E731

# ---- every fact against its source ------------------------------------------------------------------------------------
LIT = "/Volumes/2TB/Antigrvity/Runes/downloads/gotland_lit/"
_txt = {}


def said(fil, quote):
    if fil not in _txt:
        _txt[fil] = " ".join(open(LIT + fil, encoding="utf-8").read().split())
    assert " ".join(quote.split()) in _txt[fil], (fil, quote)


RI, NV, VIS, PAV, GROG, TORS = ("lst_RI_kunskapsunderlag_2018.txt", "nv_202945.txt", "lst_besok_alskog-visne-angar.txt",
                                "lst_besok_vastergarn-paviken.txt", "lst_besok_ostergarn-grogarnsberget.txt",
                                "lst_besok_kraklingbo-torsburgen.txt")
META, MYR, SAGA, LAG = ("ostergren_2020_gutnaltinget_meta.raw.txt", "myrberg_2009_island.raw.txt", "peel_1999_guta_saga.txt",
                        "peel_2009_guta_lag.raw.txt")
F13, F06, F04, F81, FRO, VRAK, ROS = ("fv2013_wake_of_hoards.raw.txt", "fv2006_frojel_silver_workshop.raw.txt",
                                      "fv2004_visby_pussel.raw.txt", "fv1981_gotlands_kulturlandskap.raw.txt", "gup_207390.raw.txt",
                                      "vrak_gotlands_lan_2025_12.raw.txt", "lup_8310496.raw.txt")
FACTS = [
    # Paviken and Västergarn
    (NV, "För drygt 1000 år sedan, under vikingatiden, var Paviken en lagunartad havsvik som förbands med havet genom ett smalt sund."),
    (NV, "Det skyddade läget gjorde viken till en idealisk naturhamn."), (NV, "Den har anlagts under 700-talet och kom att existera i ca 300 år"),
    (PAV, "I norra delen av Paviken, vid Idåns utlopp fanns verkstadsaktiviteter och skeppsbyggeri."),
    (NV, "en pålspärr som har spärrat av inloppet till Paviken. Anläggningarna är uppförda i början av 1000-talet."),
    (RI, "välformade och mycket välbevarade träbryggor i ån, dendrokronologiskt daterade till 1008."),
    (RI, "Omkring år 1000 anläggs av allt att döma den stadsvall som omger själva Västergarn. Någon liknande anläggning finns inte på Gotland och paralleller är närmast stadsvallen runt Birkas Svarta jord."),
    (VRAK, "Gotlands läge innebär att ön alltid haft en central roll för Östersjöns sjöfart."),
    # farms
    (VIS, "De äldsta husgrunderna på Gotland är ungefär 2000 år gamla. Det finns cirka 1800 sådana runt om på ön."),
    (VIS, "Husen kunde ha metertjocka murar och var ofta avdelade så att både människor och djur kunde bo i dem."),
    (VIS, "Taktäckningen kan ha utgjorts av torv, vass eller ag."),
    (VIS, "Man odlade korn, vete och råg. Den värdefulla marken med säd hägnades in med stenhägnader, vastar, medan korna, svinen, fåren och de andra djuren gick fritt."),
    (VIS, "Det finns även rester av fägator från husen som ledde djuren till betet i skogen."),
    (F13, "At many sites the farmstead’s buildings were not fixed to a certain position, but kept moving around its lands."),
    (RI, "den generella bild som finns om en omflyttning av bebyggelsen på Gotland under loppet av vikingatid-tidig medeltid."),
    (RI, "Hajdeby ger en tydlig bild av en ensamgård med förankring i förhistorisk tid"),
    (VIS, "Varje gård hade sitt eget gravfält och ett sådant ligger söder om bäcken."),
    (F13, "Late Iron Age settlement sites are often found close to their cemeteries."),
    (F13, "their Gotlandic counterparts are normally of more modest proportions."),
    (RI, "Mästermyr, ett av Gotlands största sjösystem under förhistorisk och historisk tid."),
    (F13, "By the Late Iron Age its population had developed a distinctive material culture"),
    # silver, harbours, trade
    (F13, "more than 700 Viking Period silver hoards have been recovered to date"), (F13, "this took proportions on a scale unseen elsewhere."),
    (F13, "The hoards themselves often seem to have been a kind of permanently deposited house offerings, to which silver was sometimes added over time"),
    (F06, "with its tremendous inflow of silver during the Viking Period."),
    (F06, "The western furnace pit was radiocarbon dated to 970–1160 cal AD"),
    (RI, "Nedre Fröjel utgörs av gårdarna och kyrkan nere vid den vikingatida hamnen"),
    (RI, "Lämningar av en hamn- och handelsplats från vikingatid-tidig medeltid. Spår av fiskebodar och båthus och fynd av flera silverdepåer från vikingatid med koppling till hamnområdet."),
    (VRAK, "Hos länsstyrelsen i Gotlands län förvaras GIS-data med 125 angivna möjliga hamnplatser."),
    (VRAK, "Flertalet hamnplatser är inte bekräftade i fält och inte heller arkeologiskt undersökta."),
    (SAGA, "Although the Gotlanders were heathen, they nevertheless sailed on trading voyages to all countries, both Christian and heathen."),
    (RI, "Vikingatidens bosättning antas snarare ha haft karaktären av en handelsplats än en permanent bosättning."),
    (RI, "Husen var små, av trä i skiftesverk eller lerklining och låg i parallella rader från hamnen och uppåt."),
    (ROS, "Staden Visby är en tidigmedeltida företeelse från början,"),
    (RI, "Strandgatan, som ungefär motsvarar den vikingatida strandlinjen"),
    # roads and picture stones
    (FRO, "Få av de totalt ca 570 hitintills funna gotländska bildstenarna har påträffats på vad som kan tolkas som den ursprungliga plats där de en gång restes under yngre järnålder"),
    (FRO, "en bildsten av den sena typen C, vilka kan dateras till sent 700- och 800-tal"), (FRO, "sannolikt har bildstenen placerats medvetet vid vägen."),
    (RI, "De två bildstenarna Bro Stajnkällingar med sina ursprungliga placeringar intill landsvägen."),
    (RI, "I Visnar ängar hålväg, kantad av gravar och avbrutna bildstenar samt sliprännor i häll intill en bäck."),
    (RI, "gravarna och gravfälten utmed de äldre vägarna som oftast följer de flacka höjderna i landskapet."),
    # governance
    (META, "Gotland i äldre tider varit indelat i lokala ting, tredingar, settingar och det övergripande ”Gutnal þing”."),
    (META, "På Gutnaltinget fattades beslut som rörde hela Gotland"), (META, "Samhället dominerades av den jordägande bondeklassen."),
    (META, "Samma struktur tycks ha varit rådande även under vikingatiden."),
    (META, "Settingstingen tycks ha haft en mer administrativ roll rörande försvar och skatteuppbörd."),
    (META, "Något som tycks vara unikt för Gotland är den starka ställning som socknarna hade."),
    (META, "Det är först i en tysk översättning av Gutalagen från 1401 som man uppger att Gutnaltinget fanns i Roma"),
    (META, "anges för första gången namnen på de lokala tingen, som då var 20 till antalet"),
    (META, "Den viktigaste historiska källan är Gutalagen med Gutasagan, vars äldsta delar anses vara nertecknade under 1220-talet"),
    (LAG, "The sixth assembly may not impose a fine of more than three marks, and the riding assembly up to six marks and the general assembly up to twelve marks."),
    (SAGA, "in a letter from the Pope to the deans of the northern and southern thirds"),
    (MYR, "the low-lying promontory surrounded by lakes and bogs in the middle of the island"),
    (META, "491 Viking Age weights, most cubo-octahedral, and 390 Viking Age silver coins, most fragments of Islamic coins, have been found."),
    (META, "Den typen av material i den omfattningen hade aldrig tidigare hittats inne i landet utan bara i vikingatida hamnlägen längs kusten."),
    (MYR, "It has been suggested that the Vendel and Viking Age material found on Guldåkern and Kräklinge tingsängen results from the fines and fees paid and exchanged during negotiations at the thing"),
    (MYR, "an older Iron Age cult site at Roma eventually came under the control of a chieftain or major landowner"),
    (MYR, "Gold and wild boar tusks were found in the Roma mire during drainage work"),
    # the Swedish king
    (SAGA, "Sixty marks of silver in respect of each year is the Gotlanders’ tax, divided so that the king of Sweden should have forty marks of silver out of the sixty, and the jarl twenty marks of silver."),
    (SAGA, "should send messengers to the Gotlanders’ general assembly and arrange for their tax to be collected there."),
    (SAGA, "to follow the Swedish king on military expeditions with seven warships, against heathen countries, but not against Christian ones."),
    (SAGA, "The treaty terms themselves probably relate more closely to those of the author’s day than to those of 200 years or more previously"),
    (SAGA, "it appears that some sort of tribute was being paid to Sweden in the second half of the eleventh century."),
    (SAGA, "If we assume that Guta saga was written between 1220 and 1330"),
    # forts
    (RI, "Torsburgen har sannolikt byggts på i omgångar under 200-900 e kr."),
    (RI, "kompletterad med en två kilometer lång stenmur i de flackare södra delarna."), (RI, "Inga bebyggelsespår finns på Torsburgen."),
    (GROG, "Fornborgen tros ha uppförts under senare delen av järnåldern och använts under vikingatid och tidig medeltid."),
    (GROG, "Möjligen har borgen på Östergarnsholm kunnat vidareförmedla vårdkasens signaler från Grogarnsberget till alla övriga borgar längs öns östkust."),
    # belief
    (SAGA, "people believed in groves and grave howes, holy places and ancient sites, and in heathen idols."),
    (SAGA, "otherwise each third held its own."),
    (LAG, "No one may pray to either groves or howes or heathen gods, nor to holy places or ancient sites."),
    (SAGA, "Ormika subsequently received Christianity according to St Olaf’s teaching and built himself an oratory at the same location as Akergarn church now stands."),
]
for fil, q in FACTS:
    said(fil, q)
assert recs["U 614"]["place"] == "Torsätra" and recs["U 614"]["parish"] == "Västra Ryds sn"
assert "Hann vas siukR uti, þa þæiR giald toku a Gutlandi" in nz("U 614")

# ---- pictures and map -------------------------------------------------------------------------------------------------
FP, FB = "Västergarn - Paviken 01.jpg", "Bildstenar Bro.jpg"
INFO = commons.commons_info([FP, FB])
assert (INFO[FP]["licence"], INFO[FP]["author"]) == ("CC BY 2.5 se", "Jan Norrman")
assert (INFO[FB]["licence"], INFO[FB]["author"]) == ("CC BY-SA 3.0", "Arkland")
LIC = {f: f"[{INFO[f]['licence']}]({INFO[f]['licence_url']})" if INFO[f].get("licence_url") else INFO[f]["licence"] for f in (FP, FB)}
PAGE = {f: "https://commons.wikimedia.org/wiki/File:" + f.replace(" ", "_") for f in (FP, FB)}
MAP = {lang: blog_figures.freeze(open(os.path.join(ROOT, "utdata", "gamla_landen", f"karta_gotland_{lang}.png"), "rb").read())
       for lang in ("sv", "en")}
ATT = "/artiklar/de-gamla-landen-attundaland"

title = "De gamla landen: Gotland – ett eget land mitt i havet"
summary = ("Gotland var på vikingatiden ett land för sig: gårdar som flyttade runt på sina ägor, hamnar längs hela kusten, mer "
           "silver i jorden än någon annanstans och ett eget ting för hela ön. Följ med till Paviken och Roma omkring år 1000. "
           "En del i serien De gamla landen.")

body = f"""Hammarslag hörs från verkstäder och från skepp som byggs, längst in i en lagun på Gotlands västkust där Idån rinner ut. Lagunen heter Paviken, och den är en naturlig hamn: ett smalt sund leder in från havet, och innanför ligger vattnet skyddat. Här har man haft en hamn sedan 700-talet. Ön ligger mitt i Östersjön, och alla som seglar mellan öst och väst har den i sikte.

Men om du kommer omkring år 1000 håller hamnen på att flytta. I början av 1000-talet stängs inloppet till Paviken med en spärr av pålar, och söderut, vid Västergarn, byggs nytt. I ån där ligger bryggor av trä, och virket till dem höggs år 1008. Omkring år 1000 får Västergarn en vall runt hela platsen, den enda i sitt slag på Gotland. Den närmaste motsvarigheten är vallen kring Birka.

![Västergarn och Paviken]({INFO[FP]['thumb']})
Västergarn och Paviken. Foto: Jan Norrman, Riksantikvarieämbetet, {LIC[FP]}, via [Wikimedia Commons]({PAGE[FP]}).

## Gården som flyttade

Gå i land och in på ön. Inne på ön ligger stora sjöar och myrar – Mästermyr är ett av öns största sjösystem. Gutarna hade sin egen kultur, som skilde sig från fastlandets, och den syns i hur de bodde.

Runt om på ön ligger omkring 1 800 husgrunder av sten, de äldsta två tusen år gamla. De är rester av långhus från äldre järnålder, med metertjocka murar och tak av torv, vass eller ag, där människor och djur bodde under samma tak. Man odlade korn, vete och råg, och åkrarna hägnades in med stenmurar medan korna, svinen och fåren gick fritt. Fägator ledde djuren från husen ut till betet i skogen.

Omkring år 1000 bor man inte längre i de husen. På många håll ligger gårdens hus inte stilla utan flyttar runt på ägorna, och under vikingatiden och den tidiga medeltiden flyttar bebyggelsen till de lägen där gårdarna sedan ska ligga. Gårdarna ligger ofta var för sig, som ensamgårdar, inte samlade i byar. Och varje gård har sina döda nära sig, på ett eget gravfält. Gravarna är enkla, mer anspråkslösa än på fastlandet.

## Silvret

Under golven ligger silvret. Mer än sjuhundra silverskatter från vikingatiden har hittats på Gotland, i en omfattning som saknar motstycke någon annanstans. Många kom fram när myrarna dikades ut och nya åkrar bröts på 1800-talet. Skatterna verkar ofta ha legat kvar i gårdens hus, ibland påfyllda med tiden, kanske som offer till huset. Det är en tolkning, men den ger en bild: silver som inte bara var rikedom utan också något man lade ner hos sig.

Silvret kom över havet. Vid Fröjel, där gårdarna och kyrkan ligger nere vid den vikingatida hamnen, har man hittat en verkstad där silver renades i en ugn, daterad till mellan 970 och 1160. Vid Bandlunde i Burs, på östkusten, finns spår av en hamn och handelsplats med fiskebodar, båthus och flera silverskatter. Länsstyrelsen har registrerat 125 möjliga hamnplatser runt ön, de flesta aldrig undersökta. Gutasagan, nedskriven på 1200-talet, minns att gutarna, fast de var hedningar, seglade i handel till alla länder, både kristna och hedniska.

Och Visby? Där Strandgatan går låg strandlinjen på vikingatiden, och små hus av trä låg i rader upp från hamnen. Men platsen var snarare en handelsplats än en stad. Arkeologen Mats Roslund menar att staden Visby är medeltida från början.

## Vägarna och bildstenarna

Mellan gårdarna går vägarna, ofta längs de flacka höjderna, och vid dem ligger gravarna. Och vid vägarna står bildstenarna, de gotländska stenarna med sina bilder. Omkring 570 är kända, men få står kvar där de restes. Vid Fröjel har man grävt ut platsen för en bildsten från sent 700- eller 800-tal och funnit att den sannolikt ställdes medvetet vid vägen. I Bro står två bildstenar, Stajnkällingarna, kvar på sin ursprungliga plats vid landsvägen. I Visnar ängar går en hålväg, kantad av gravar och avbrutna bildstenar.

![Bildstenarna vid Bro]({INFO[FB]['thumb']})
Bro Stajnkällingar, två bildstenar på sin ursprungliga plats vid landsvägen. Foto: Arkland, {LIC[FB]}, via [Wikimedia Commons]({PAGE[FB]}).

Föreställ dig att färdas längs en sådan väg: förbi gårdarnas gravfält, förbi stenar med bilder, de dödas minnen vid vägkanten, så att den som gick förbi skulle minnas.

## Tinget mitt på ön

Gotland styrde sig självt. Ön var indelad i lokala ting, i settingar och i tre tredingar, och över dem stod Gutnaltinget, där man fattade beslut som rörde hela Gotland. Gutalagen visar hur nivåerna hängde ihop: settingstinget fick döma till högst tre marks böter, tredingstinget till sex och Gutnaltinget till tolv. Socknarna hade en ovanligt stark ställning, och det var de jordägande bönderna som dominerade samhället. Någon adel fanns inte. Arkeologen Majvor Östergren menar att samma ordning tycks ha gällt redan på vikingatiden.

Men allt detta kommer ur Gutalagen och Gutasagan, vars äldsta delar skrevs ner på 1220-talet. Tredingarna nämns första gången 1213, de lokala tingen namnges först 1412, och att Gutnaltinget låg i Roma står först i en tysk översättning av lagen från 1401.

Roma ligger mitt på ön, på en låg udde omgiven av sjöar och myrar. På en åker där har man hittat 491 vikter och 390 silvermynt från vikingatiden, de flesta bitar av islamiska mynt – sådant man annars bara hittar i hamnarna vid kusten. Har det betalats böter och avgifter här, när tinget samlades? Det har föreslagits. Arkeologen Nanouschka Myrberg tolkar platsen på ett annat sätt: att en hövding eller storbonde tog kontroll över en äldre kultplats. Om Gotland var ett land av jämlika bönder eller av stormän är alltså omstritt.

![Karta över Gotland omkring år 1000 med runstenarna och platserna i texten]({MAP['sv']})
**Karta.** Gotland omkring år 1000. Ön var delad i tre tredingar, men gränserna mellan dem är osäkra och ritas inte ut. Grå punkter är runstenar, ringar platser i texten. Karta: Vitki, efter SGU:s modell för strandförskjutningen år 1000, Institutet för språk och folkminnens ortnamnsregister och Rundata.

## Ön och sveakungen

Gotland var ett eget land, men det hade en överenskommelse med sveakungen. Enligt Gutasagan betalade gutarna sextio mark silver om året, fyrtio till kungen och tjugo till jarlen, och kungens sändebud skulle hämta skatten vid Gutnaltinget. Gutarna skulle följa kungen i ledung med sju skepp, men bara mot hedniska länder, inte mot kristna. När överenskommelsen gjordes vet ingen, och villkoren speglar troligen 1200-talet mer än vikingatiden.

Men en runsten i Uppland visar att något liknande fanns redan på 1000-talet. Vid Torsätra i Västra Ryd, i [Attundaland]({ATT}), reste två bröder en sten efter sin bror:

> *{nz("U 614")}*

Skule och Folke lät resa denna sten efter Husbjörn, sin broder. Han låg sjuk utomlands, när de tog upp gäld på Gotland.

## Borgarna

Gotland har sina borgar. Torsburgen, byggd i omgångar mellan 200 och 900, omges av en två kilometer lång stenmur där berget inte skyddar, men inga spår av bebyggelse finns innanför. Kanske var det en plats att fly till. Grogarnsberget på östkusten användes under vikingatiden och den tidiga medeltiden, och kanske kunde en vårdkase där tändas och signalen föras vidare från borg till borg längs hela östkusten.

## Tron

Gutasagan berättar hur det var före kristendomen: folk trodde på lundar och högar, på heliga platser och gamla platser, och på hedniska gudar. Det största offret hölls av hela landet, men annars höll varje treding sitt eget. Gutalagen förbjuder senare att be till lundar, högar, hedniska gudar och heliga platser – ett förbud som visar vad man hade gjort. I myren vid Roma har man vid utdikning hittat guld och betar av vildsvin.

Sagan berättar också hur det nya kom. En man, Ormika, tog emot kristendomen efter Olav den heliges lära och byggde ett bönehus där Akergarns kyrka sedan kom att stå. Det är en berättelse, nedskriven två hundra år senare, men den pekar mot samma tid som den här artikeln: början av 1000-talet.

## Ett land mitt i havet

Gotland omkring år 1000 är ett land som lever av havet och styr sig självt. Gårdarna ligger ofta var för sig, med sina döda nära och sitt silver under golvet. Hamnarna flyttar, Paviken stängs och Västergarn får sin vall. Mitt på ön, där sjöarna och myrarna möts, samlas tinget. Den som står vid Paviken och ser ut över lagunen ser en hamn som har tjänat i tre hundra år och nu ska lämnas, på en ö som hade sin egen lag och sin egen väg.

## Så vet vi det

Landskapet, gårdarna, hamnarna och borgarna bygger på länsstyrelsens kunskapsunderlag för Gotlands riksintressen, Naturvårdsverkets beskrivning av Paviken och artiklar i *Fornvännen* om silverskatterna och verkstaden i Fröjel. Tingen, lagen och skatten till sveakungen bygger på Gutalagen och Gutasagan, som skrevs ner på 1200-talet; de visar medeltidens Gotland, och om ordningen var densamma på vikingatiden är omstritt. Var Gutnaltinget låg, om ön var ett land av jämlika bönder eller av stormän, och när Gotland kom under sveakungen är frågor där forskarna inte är eniga. De 1 800 husgrunderna av sten är äldre än vikingatiden, och att silverskatterna var offer till huset är en tolkning. Länkarna till källorna finns nedan.

## Källor

- Länsstyrelsen i Gotlands län 2026. *Riksintresse för kulturmiljövården i Gotlands län – Kunskapsunderlag*. Visby. Samt länsstyrelsens beskrivningar av Alskog Visne ängar, Västergarn Paviken, Kräklingbo Torsburgen och Östergarn Grogarnsberget.
- Martinsson, M. (red.) 1999. *Registerblad. Paviken*. Naturvårdsverket.
- Gustafsson, Ny Björn 2013. In the wake of the hoards. *Fornvännen* 108, s. 1–11. CC BY 4.0.
- Söderberg, Anders & Gustafsson, Ny Björn 2006. A Viking Period silver workshop in Fröjel, Gotland. *Fornvännen* 101, s. 29–31. CC BY 4.0.
- Andreeff, Alexander & Bakunic Fridén, Imelda 2014. *Arkeologisk undersökning vid bildstensplatsen Fröjel, Stenstugu 1:8*. GOTARC Serie D 96.
- Östergren, Majvor 2020. Gutnaltinget i Roma och andra tingsplatser på Gotland. *META* 2020.
- Myrberg, Nanouschka 2009. An Island in the Middle of an Island: On Cult, Laws and Authority in Viking Age Gotland. I: *From Ephesos to Dalecarlia*. Statens historiska museum.
- Peel, Christine (utg. och övers.) 1999. *Guta saga: The History of the Gotlanders*. Viking Society for Northern Research.
- Peel, Christine (övers. och utg.) 2009. *Guta lag: The Law of the Gotlanders*. Viking Society for Northern Research.
- Roslund, Mats 2001. Gutar, främlingar och den förblindande vikingatiden. I: *Från stad till land*. Lund Studies in Medieval Archaeology 29.
- Statens maritima och transporthistoriska museer 2025. *Marinarkeologisk kunskapsöversikt … Gotlands län*. Rapport 2025:12.
- Samnordisk runtextdatabas (Rundata), Institutionen för nordiska språk, Uppsala universitet. Open Database License. Institutet för språk och folkminnen, ortnamnsregistret, CC BY. Sveriges geologiska undersökning, strandförskjutningsmodell (kartan).
- Bilder: Wikimedia Commons, med fotografen och licensen i bildtexten."""

title_en = "The old lands: Gotland – a land of its own in the middle of the sea"
summary_en = ("In the Viking Age Gotland was a land of its own: farms that moved about their land, harbours all along the coast, "
              "more silver in the ground than anywhere else and its own assembly for the whole island. Come to Paviken and Roma "
              "around AD 1000. A part of the series The old lands.")

body_en = f"""Hammering is heard from workshops and from ships being built at the far end of a lagoon on the west coast of Gotland, where the Idån flows out. The lagoon is Paviken, a natural harbour: a narrow sound leads in from the sea, and inside it the water lies sheltered. There has been a harbour here since the eighth century. The island lies in the middle of the Baltic, and everyone sailing between east and west has it in sight.

But if you come around AD 1000, the harbour is moving. Early in the eleventh century the entrance to Paviken is closed with a barrier of stakes, and to the south, at Västergarn, something new is being built. In the river there lie wooden jetties, and the timber for them was felled in 1008. Around AD 1000 Västergarn gets a rampart round the whole place, the only one of its kind on Gotland. The nearest parallel is the rampart round Birka.

![Västergarn and Paviken]({INFO[FP]['thumb']})
Västergarn and Paviken. Photo: Jan Norrman, Swedish National Heritage Board, {LIC[FP]}, via [Wikimedia Commons]({PAGE[FP]}).

## The farm that moved

Go ashore and into the island. Inland lie large lakes and bogs – Mästermyr is one of the island's largest lake systems. The Gotlanders had a culture of their own, distinct from the mainland's, and it shows in how they lived.

All over the island lie some 1,800 stone house foundations, the oldest two thousand years old. They are the remains of longhouses from the Early Iron Age, with walls a metre thick and roofs of turf, reed or sedge, where people and animals lived under one roof. People grew barley, wheat and rye, and the fields were fenced with stone walls while the cows, pigs and sheep went free. Droveways led the animals from the houses out to the grazing in the forest.

Around AD 1000 people no longer live in those houses. In many places the farm's buildings do not stay put but move around its lands, and during the Viking Age and the early Middle Ages the settlement moves to the sites where the farms will later lie. The farms often lie on their own, as single farms, not gathered in villages. And each farm keeps its dead close, in a grave field of its own. The graves are simple, more modest than on the mainland.

## The silver

Under the floors lies the silver. More than seven hundred Viking-age silver hoards have been found on Gotland, on a scale unseen anywhere else. Many came to light when the bogs were drained and new fields broken in the nineteenth century. The hoards often seem to have stayed in the farm's buildings, sometimes added to over time, perhaps as offerings to the house. That is an interpretation, but it gives a picture: silver that was not only wealth but also something one laid down at home.

The silver came over the sea. At Fröjel, where the farms and the church lie down by the Viking-age harbour, a workshop has been found where silver was refined in a furnace, dated to between 970 and 1160. At Bandlunde in Burs, on the east coast, there are traces of a harbour and trading place with fishing huts, boathouses and several silver hoards. The county board has registered 125 possible harbour sites round the island, most never examined. Guta saga, written down in the thirteenth century, remembers that the Gotlanders, though heathen, sailed on trading voyages to all countries, Christian and heathen alike.

And Visby? Where Strandgatan runs, the shoreline lay in the Viking Age, and small wooden houses lay in rows up from the harbour. But the place was a trading place rather than a town. The archaeologist Mats Roslund argues that the town of Visby was medieval from the start.

## The roads and the picture stones

Between the farms run the roads, often along the low heights, and beside them lie the graves. And by the roads stand the picture stones, the Gotlandic stones with their pictures. Some 570 are known, but few still stand where they were raised. At Fröjel the site of a picture stone from the late eighth or ninth century has been excavated, and it turned out to have been placed by the road, probably on purpose. At Bro two picture stones, the Stajnkällingar, still stand in their original place by the highway. In Visnar ängar a hollow way runs, lined with graves and broken picture stones.

![The picture stones at Bro]({INFO[FB]['thumb']})
Bro Stajnkällingar, two picture stones in their original place by the highway. Photo: Arkland, {LIC[FB]}, via [Wikimedia Commons]({PAGE[FB]}).

Imagine travelling along such a road: past the farms' grave fields, past stones with pictures, the memories of the dead by the wayside, so that whoever passed would remember.

## The assembly in the middle of the island

Gotland governed itself. The island was divided into local assemblies, into sixths and into three thirds, and above them stood the Gutnalthing, where decisions were made that concerned the whole of Gotland. Guta lag shows how the levels fitted together: the sixth's assembly could fine up to three marks, the third's up to six and the Gutnalthing up to twelve. The parishes had an unusually strong position, and it was the land-owning farmers who dominated society. There was no nobility. The archaeologist Majvor Östergren thinks the same order seems to have held already in the Viking Age.

But all this comes from Guta lag and Guta saga, whose oldest parts were written down in the 1220s. The thirds are first mentioned in 1213, the local assemblies are first named in 1412, and that the Gutnalthing met at Roma is first stated in a German translation of the law from 1401.

Roma lies in the middle of the island, on a low promontory surrounded by lakes and bogs. In a field there 491 weights and 390 silver coins from the Viking Age have been found, most of them pieces of Islamic coins – things otherwise found only in the harbours on the coast. Were fines and fees paid here when the assembly met? It has been suggested. The archaeologist Nanouschka Myrberg reads the place differently: that a chieftain or great landowner took control of an older cult site. Whether Gotland was a land of equal farmers or of great men is therefore disputed.

![Map of Gotland around AD 1000 with the runestones and the places in the text]({MAP['en']})
**Map.** Gotland around AD 1000. The island was divided into three thirds, but the borders between them are uncertain and are not drawn. Grey points are runestones, rings places in the text. Map: Vitki, after the Geological Survey of Sweden's shore-displacement model for AD 1000, the place-name register of the Institute for Language and Folklore, and Rundata.

## The island and the Swedish king

Gotland was a land of its own, but it had an agreement with the king of the Swedes. According to Guta saga the Gotlanders paid sixty marks of silver a year, forty to the king and twenty to the jarl, and the king's messengers were to collect the tax at the Gutnalthing. The Gotlanders were to follow the king on levy with seven ships, but only against heathen lands, not against Christian ones. When the agreement was made no one knows, and the terms probably reflect the thirteenth century more than the Viking Age.

But a runestone in Uppland shows that something similar existed already in the eleventh century. At Torsätra in Västra Ryd, in [Attundaland]({ATT}), two brothers raised a stone for their brother:

> *{nz("U 614")}*

Skúli and Folki had this stone raised in memory of Húsbjôrn, their brother. He lay sick abroad when they took payment on Gotland.

## The forts

Gotland has its forts. Torsburgen, built in stages between 200 and 900, is enclosed by a stone wall two kilometres long where the cliff gives no protection, but there are no traces of settlement inside. Perhaps it was a place to flee to. Grogarnsberget on the east coast was used in the Viking Age and the early Middle Ages, and perhaps a beacon there could be lit and the signal passed on from fort to fort along the whole east coast.

## Belief

Guta saga tells how it was before Christianity: people believed in groves and grave mounds, in holy places and ancient sites, and in heathen gods. The greatest sacrifice was held by the whole land, but otherwise each third held its own. Guta lag later forbids praying to groves, mounds, heathen gods and holy places – a ban that shows what people had done. In the mire at Roma gold and wild boar tusks have been found during drainage.

The saga also tells how the new came. A man, Ormika, received Christianity after St Olaf's teaching and built an oratory where Akergarn church later came to stand. It is a story, written down two hundred years later, but it points to the same time as this article: the beginning of the eleventh century.

## A land in the middle of the sea

Gotland around AD 1000 is a land that lives by the sea and governs itself. The farms often lie each on their own, with their dead close by and their silver under the floor. The harbours move, Paviken is closed and Västergarn gets its rampart. In the middle of the island, where the lakes and the bogs meet, the assembly gathers. Whoever stands by Paviken and looks out over the lagoon sees a harbour that has served for three hundred years and is now to be left, on an island that had its own law and its own way.

## How we know

The landscape, the farms, the harbours and the forts rest on the county board's survey of Gotland's areas of national interest, the Swedish Environmental Protection Agency's description of Paviken and articles in *Fornvännen* on the silver hoards and the workshop at Fröjel. The assemblies, the law and the tax to the Swedish king rest on Guta lag and Guta saga, which were written down in the thirteenth century; they show medieval Gotland, and whether the order was the same in the Viking Age is disputed. Where the Gutnalthing met, whether the island was a land of equal farmers or of great men, and when Gotland came under the Swedish king are questions on which researchers do not agree. The 1,800 stone house foundations are older than the Viking Age, and that the silver hoards were offerings to the house is an interpretation. The sources are listed below.

## Sources

- County Administrative Board of Gotland 2026. *Riksintresse för kulturmiljövården i Gotlands län – Kunskapsunderlag*. Visby. And the board's descriptions of Alskog Visne ängar, Västergarn Paviken, Kräklingbo Torsburgen and Östergarn Grogarnsberget.
- Martinsson, M. (ed.) 1999. *Registerblad. Paviken*. Swedish Environmental Protection Agency.
- Gustafsson, Ny Björn 2013. In the wake of the hoards. *Fornvännen* 108, pp. 1–11. CC BY 4.0.
- Söderberg, Anders & Gustafsson, Ny Björn 2006. A Viking Period silver workshop in Fröjel, Gotland. *Fornvännen* 101, pp. 29–31. CC BY 4.0.
- Andreeff, Alexander & Bakunic Fridén, Imelda 2014. *Arkeologisk undersökning vid bildstensplatsen Fröjel, Stenstugu 1:8*. GOTARC Serie D 96.
- Östergren, Majvor 2020. Gutnaltinget i Roma och andra tingsplatser på Gotland. *META* 2020.
- Myrberg, Nanouschka 2009. An Island in the Middle of an Island: On Cult, Laws and Authority in Viking Age Gotland. In: *From Ephesos to Dalecarlia*. Swedish History Museum.
- Peel, Christine (ed. and transl.) 1999. *Guta saga: The History of the Gotlanders*. Viking Society for Northern Research.
- Peel, Christine (transl. and ed.) 2009. *Guta lag: The Law of the Gotlanders*. Viking Society for Northern Research.
- Roslund, Mats 2001. Gutar, främlingar och den förblindande vikingatiden. In: *Från stad till land*. Lund Studies in Medieval Archaeology 29.
- Swedish National Maritime and Transport History Museums 2025. *Marinarkeologisk kunskapsöversikt … Gotlands län*. Report 2025:12.
- Scandinavian Runic-text Data Base (Rundata), Department of Scandinavian Languages, Uppsala University. Open Database License. Institute for Language and Folklore, place-name register, CC BY. Geological Survey of Sweden, shore-displacement model (the map).
- Images: Wikimedia Commons, with the photographer and the licence in the caption."""

for b in (body, body_en):
    assert not re.search(r"^\|", b, re.M), "BlogBody har inga tabeller"
    assert ":::" not in b and "/karta" not in b and "/statistik" not in b

out = {"slug": "de-gamla-landen-gotland", "title": title, "summary": summary, "body": body,
       "title_en": title_en, "summary_en": summary_en, "body_en": body_en,
       "labels": ["Forskning", "Geografi", "Tro och magi"]}
from src import blog_labels  # noqa: E402
assert blog_labels.check(out["labels"]) is None, blog_labels.check(out["labels"])
path = os.path.join(ROOT, "utdata", "blogg", "gotland_land.json")
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
                 "topic": "Geografi|gotland", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
