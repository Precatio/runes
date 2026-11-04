"""Artikeln "De gamla landen: Fjädrundaland – folklandet längst in i havsviken" (sv + en), del 3 i serien De gamla landen.
Sedan 2026-11-04 i seriens atmosfäriska form (Viktor): leran och ängarna, hällarnas tecken, vägarna, tinget och hamnorna;
stenarna utan kors står kvar som ett inslag. Siffrorna låses mot utdata/fjadrundaland/fjadrundaland.json (plan
analysplaner/2026-11-02-fjadrundaland.md, sha 6088f2af), utdata/landprofiler/landprofiler.json och naringar.json; landskapet
mot DMS 1:8, 1:9 och länsstyrelsens riksintressebeskrivningar C48/C57/C63.
    ../../../.venv/bin/python build_fjadrundaland.py [--write | --update DOC]"""
import datetime as dt
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_figures, commons  # noqa: E402

R = json.load(open(os.path.join(ROOT, "utdata", "fjadrundaland", "fjadrundaland.json"), encoding="utf-8"))
LP = json.load(open(os.path.join(ROOT, "utdata", "landprofiler", "landprofiler.json"), encoding="utf-8"))["tests"]
NA = {o["unit"]: o for o in json.load(open(os.path.join(ROOT, "utdata", "landprofiler", "naringar.json"), encoding="utf-8"))}
recs = {r["signum"]: r for r in json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["inscriptions"]}
nz = lambda s: recs[s]["normalization"].replace('"', "").strip()  # noqa: E731
pc = lambda x: round(100 * x)  # noqa: E731

# ---- the locked numbers -----------------------------------------------------------------------------------------------
K = R["T1"]["pm_kors"]
assert (K["grund"]["k_in"], K["grund"]["n_in"], pc(K["grund"]["share_in"]), pc(K["grund"]["share_out"])) == (43, 122, 35, 61)
assert all(v["holds"] for v in K.values())
assert (K["e_utan_fjadrundalands_ristare"]["k_in"], K["e_utan_fjadrundalands_ristare"]["n_in"]) == (7, 25)
assert pc(K["e_utan_fjadrundalands_ristare"]["share_out"]) == 60
assert sorted(R["fj_carvers"]) == sorted(["Äskil", "Balle", "Erik", "Livsten", "Tidkume", "Torbjörn"])
for y in ("i_grupp", "flera_resare", "r_for_R"):
    assert all(v["holds"] for k, v in R["T1"][y].items() if k != "e_utan_fjadrundalands_ristare")
    assert not R["T1"][y]["e_utan_fjadrundalands_ristare"]["holds"]
G, F = R["T1"]["i_grupp"]["grund"], R["T1"]["flera_resare"]["grund"]
assert (pc(G["share_in"]), pc(G["share_out"]), pc(F["share_in"]), pc(F["share_out"])) == (15, 34, 44, 64)
RR = R["T1"]["r_for_R"]["grund"]
assert (pc(RR["share_in"]), pc(RR["share_out"])) == (52, 15)
for y in ("skilj_plus", "ord_ræisti"):
    assert not R["T1"][y]["a_ristare_slump"]["holds"] and not R["T1"][y]["e_utan_fjadrundalands_ristare"]["holds"]
T2 = R["T2"]
assert (T2["Torbjörn pm_kors"]["in_k"], T2["Torbjörn pm_kors"]["in_n"], T2["Torbjörn pm_kors"]["out_k"], T2["Torbjörn pm_kors"]["out_n"]) == (2, 5, 9, 10)
assert R["holm"]["Torbjörn pm_kors"] > 0.05
lp = {(t["domain"], t["feature"]): t for t in LP if t["unit"] == "fjadrundaland" and t["kind"] == "land"}
assert lp[("sed", "has_carver")]["holds"] and (pc(lp[("sed", "has_carver")]["share_in"]), pc(lp[("sed", "has_carver")]["share_out"])) == (90, 60)
GH = lp[("gravskick", "gf_hogar")]
assert GH["holds"] and GH["inom_lan"]["result"] == "håller"
HR = NA["fjadrundaland"]["profile"]["hällristningar"]
assert round(1 / HR["share"]) == 7 and round(1 / HR["share_rest"]) == 33 and HR["share_in_county"] / HR["share_rest_county"] > 5
# the stones
assert "Hiær mun standa stæinn miðli byia" in nz("U 729") and "sum Balli risti" in nz("U 729") and recs["U 729"]["place"] == "Ågersta"
assert "Hann varð dauðr a Danmarku i hvitavaðum. Balli rist[i]." in nz("U 699")
assert "christening robes" in recs["U 699"]["translation_en"]
assert "Es atti æinn seR skip ok austr styrði i Ingvars lið" in nz("U 778") and recs["U 778"]["parish"] == "Svinnegarns sn"
assert "þaiR inkulfr" in recs["U 974"]["transliteration"] and recs["U 974"]["carvers"][0]["name"] == "Öpir 1" and recs["U 974"]["parish"] == "Vaksala sn"
assert "· þair · litu ·" in recs["U 749"]["transliteration"] and recs["U 749"]["carvers"][0]["name"] == "Balle"
# sources
DMS9 = " ".join(open("/Volumes/2TB/Antigrvity/Runes/geografi_kallor/dms/dms_1_9_dedup.txt", encoding="utf-8").read().split())
DMS8 = " ".join(open("/Volumes/2TB/Antigrvity/Runes/geografi_kallor/dms/dms_1_8_dedup.txt", encoding="utf-8").read().split())
for k in ("Trögd utgör till större delen en halvö, som i sydväst, söder och öster omsluts av Mälarens vatten",
          "Oknö, Arnö och Grönsö - varit bebyggda sedan järnåldern", "Centrum i morgongåvelänet var sannolikt Husby, Kungs-Husby sn",
          "indelad i tre tredingar", "13, 11 resp 9 hamnor", "Sigurd Rahmqvist Uppsala 2010"):
    assert k in DMS9, k
for k in ("bebyggelsen i brytningszonen mellan lerslätt och morän", "Områdets norra del består av flera mindre skogsbygder",
          "Gravfälten är inte bara få och små", "högsta urbergsplanet inom Uppland", "Stockholm 1994"):
    assert k in DMS8, k
LS = "/Volumes/2TB/Antigrvity/Runes/downloads/fjadrundaland_lit/"
C48 = " ".join(open(LS + "RI-kultur_C48.txt", encoding="utf-8").read().split())
C57 = " ".join(open(LS + "RI-kultur_C57.txt", encoding="utf-8").read().split())
C63 = " ".join(open(LS + "RI-kultur_C63.txt", encoding="utf-8").read().split())
assert "var ursprungligen Upplands näst största våtängsområde" in C48 and "tunanamn antyder en funktion som central samlingsplats" in C48
assert "Inom Svinnegarn finns ett Husby som antyder en central administration funktion" in C57
assert "Sockennamnet Torsvi syftar på en hednisk kultplats" in C63 and "omfattar 180 gravar från yngre järnålder" in C63

# ---- picture and map ----------------------------------------------------------------------------------------------------
F729 = "U729 Ågersta - kmb.16000300012933.jpg"
INFO = commons.commons_info([F729])
assert INFO[F729]["licence"] == "CC BY 2.5 se" and INFO[F729]["author"] == "Bengt A. Lundberg"
PAGE = "https://commons.wikimedia.org/wiki/File:" + F729.replace(" ", "_")
MAP = {lang: blog_figures.freeze(open(os.path.join(ROOT, "utdata", "fjadrundaland", f"karta_fjadrundaland_{lang}.png"), "rb").read())
       for lang in ("sv", "en")}  # utdata/fjadrundaland/karta_fjadrundaland.R
SOTHOLM, RODEN = "/artiklar/de-gamla-landen-sotholm", "/artiklar/de-gamla-landen-roden"
ERIK = "/artiklar/erik-skrev-r-och-bygden-skrev-efter"

# ---- the land as it was lived in (rewrite 2026-11-04: the series is atmospheric, the runestones one part of the place) --
for k in ("De sankare områdena närmast åarna utnyttjades för slåtter",
          "Ängsmarkerna var sedan medeltiden uppdelade i ett flertal långsmala lotter som delvis tillhörde avlägset belägna byar och gårdar i omgivande socknar",
          "I övergången mellan slätten och moränmarken finns betesmarker och där ligger fornlämningarna och bebyggelsen",
          "Runstenarna markerar de äldre vägnätet", "Hålvägsystem finns utmed Enköpingsåsen", "Yngre järnåldersgravfält ligger intill flera av byarna"):
    assert k in C48, k
for k in ("Vid Husby finns även en storhög kallad ”Haralds kulle”", "Ett flertal runstenar finns utmed huvudvägen",
          "i miljön vid källan finns skålgropsförekomster"):
    assert k in C57, k
DMS7 = open("/Volumes/2TB/Antigrvity/Runes/geografi_kallor/dms/dms_1_7_dedup.txt", encoding="utf-8").read()
assert "Adelsö, Arnö, Boglösa" in DMS9 and "Adelsö socken, som hörde till Trögds härad i Fjädrundaland" in DMS7
for k in ("Hovgården på Adelsö, där fem storhögar", "Skandinaviens största höggravfält", "Björkö"):
    assert k in DMS7, k
assert "ToliR bryti i roði kunungi" in nz("U 11") and recs["U 11"]["place"] == "Hovgården"
ATT = "/artiklar/de-gamla-landen-attundaland"
assert "Svinnegarns källa är länets mest välkända trefaldighetskälla" in C57 and "härbärgen för besökande pilgrimer" in C57
assert "de allra flesta utgörs av runda stensättningar men 16 högar" in C63 and "Torsviviken" in C63
for k in ("Dess rätta tingsstad låg vid byn Enhälja, Villberga sn", "tingsplatsens namn var 1299", "0bolund",
          "om åkeföret står sig eller annars med båt så fort isen går upp", "fastar och nämndemän regelmässigt"):
    assert k in DMS9, k
for k in ("Kungshögen, 35 m i diameter och 6 m hög", "endast 10-12", "närmare 250 skärvstenshögar", "skålgropsföre",
          "markerar de bronsålderns bosättningsområden", "utgjorde fastland under hela forntiden"):
    assert k in DMS8, k
assert "ok byggi i Harvistaðum. Balli risti stæin" in nz("U 744") and nz("U 744").startswith("Gyða let ræisa stæin at Þordiarf, boanda sinn, sun GuðlaugaR")
assert "Hann byggi i Agurstaðum" in nz("U 729")

title = "De gamla landen: Fjädrundaland – folklandet längst in i havsviken"
summary = ("Fjädrundaland var det västligaste av Upplands folkland: lerslätter och sanka ängar, gårdar på kanten mot moränen, "
           "vägar längs åsarna och bronsålderns tecken på hällarna. Följ med in i Mälaren, som ännu var en vik av havet, "
           "omkring år 1000. Tredje delen i serien De gamla landen.")

body = f"""Föreställ dig att du seglar in i Mälaren för tusen år sedan. Den är ingen sjö ännu utan en vik av havet, och längst in i väster, där vattnet delar sig i fjärdar och sund, ligger Trögd: en halvö som vattnet omsluter i sydväst, söder och öster. Holmarna utanför – Oknö, Arnö, Grönsö – har haft folk sedan järnåldern. Härifrån for man också ut. I Svinnegarn har föräldrar rest stenar efter en son som ”ensam ägde ett skepp och styrde österut i Ingvars följe”.

Längre österut, där fjärden vidgar sig, hör också Adelsö till Trögd. Där, vid Hovgården, ligger fem storhögar och en kungsgård, och en sten säger att Tole var kungens bryte, hans förvaltare. På grannön Björkö, i samma socken, låg staden Birka med Skandinaviens största gravfält med högar. Gränsen mot [Attundaland]({ATT}) gick strax öster om dem.

Det här är Fjädrundaland, det västligaste av Upplands tre folkland. Det är ett gammalt land, bördigt och tätt bebott, och det vänder sig mot vattnet.

## Leran och ängarna

Gå i land och följ en dalgång norrut. Leran ligger tung och blank i fårorna, och längs åarna breder sanka ängar ut sig. Där slås höet. Längs Örsundaån ligger det som senare ska kallas Upplands näst största våtäng, och redan på medeltiden var den delad i långa, smala lotter som hörde till byar långt bort. Föreställ dig slåttern i sensommaren: raderna av människor med liar i det våta gräset, höet som ska räcka åt djuren hela vintern.

Gårdarna ligger inte ute på slätten utan på kanten, där leran möter moränen och marken är torr nog att bo på. Där går också djuren på bete, och där ligger gravarna, intill byarna. Längst i norr, på Upplands högsta urbergsplatå, tar de små skogsbygderna vid.

Gravarna här är enklare än på andra håll i Uppland. I Simtuna och Torstuna rymmer ett gravfält i genomsnitt bara tio–tolv gravar, låga och oansenliga. Men här och där reser sig något större: Kungshögen vid Torstunaby, trettiofem meter bred och sex meter hög. Och vid Torsvi i Trögd, i en dalgång som sluttar ner mot Torsviviken, ligger hundraåttio gravar från yngre järnålder i ett och samma gravfält, nästan alla runda stensättningar men också sexton högar.

## Tecknen på hällarna

Det här är ett gammalt land, och det syns. På hällarna hade människor huggit sina tecken mer än tusen år innan den första runstenen restes. I Fjädrundaland är ungefär var sjunde fornlämning en hällristning, i resten av Uppland var trettionde. Kring Simtuna och Torstuna markerar närmare tvåhundrafemtio högar av skörbränd sten, några hällristningar och mängder av skålgropar var bronsålderns människor bodde. Vid källan i Svinnegarn, som senare blev länets mest kända trefaldighetskälla, dit pilgrimer vandrade, finns skålgropar i berget. Och själva namnet Torsvi minns en hednisk kultplats.

Den som bodde här omkring år 1000 gick alltså bland tecken som redan var uråldriga. Vad de trodde om dem vet vi inte. Men de levde med dem. Föreställ dig barnen som leker på hällarna och djuren som betar mellan tecknen.

## Vägarna mellan byarna

Vägarna går på åsarna. Längs Enköpingsåsen finns hålvägar, vägar som trafiken har nött ner i marken, och runstenarna står längs de gamla vägarna; i Enköpings-Näs står flera av dem vid huvudvägen. Vid Ågersta står en sten som ristaren Balle har huggit, med en orm som slingrar sig över hela ytan. Den talar till den som går förbi:

> *{nz("U 729")}*

Vidhugse lät resa denna sten efter Särev, sin gode fader. Han bodde i Ågersta. Här ska stenen stå mellan byarna. Må den ristkunnige tyda de runor som Balle ristade.

![Runstenen U 729 vid Ågersta, huggen av Balle, utan kors]({INFO[F729]['thumb']})
U 729 vid Ågersta i Löts socken, huggen av Balle. Ormen täcker stenen; något kors finns inte. Foto: Bengt A. Lundberg, Riksantikvarieämbetet, CC BY 2.5 se, via [Wikimedia Commons]({PAGE}).

”Han bodde i Ågersta.” Stenarna här säger ofta var de döda bodde. Balle högg en sten åt Gyda efter hennes man:

> *{nz("U 744")}*

Gyda lät resa stenen efter Tordjärv, sin make, Gudlögs son, och han bodde i Harvesta. Balle ristade stenen.

På vintern blir isen väg. Ännu 1512 skrev länsmannen i Trögd att häradsmännen ville föra fram skatten med släde om vinterföret höll, och annars med båt så snart isen gick upp. Föreställ dig veckorna däremellan, när isen varken bar eller släppte.

## Ting, hundaren och hamnor

Fjädrundaland hade fem hundaren: Trögd, Åsunda, Lagunda, Simtuna och Torstuna. Varje hundare hade sitt ting. Trögds tingsplats låg vid byn Enhälja i Villberga och hette 1299 Öbolund; på medeltiden kom vittnen och nämndemän dit från byarna i alla fastlandssocknarna. Simtunas namn på -tuna antyder en samlingsplats sedan förhistorien.

Landet hade också sina centrala gårdar. I Svinnegarn ligger ett Husby med en storhög som kallas Haralds kulle, och ett annat Husby ligger i Kungs-Husby. När folklandet i början av 1300-talet var morgongåva åt kung Birgers drottning Märta låg dess centrum sannolikt där. Och i Trögd var skattejorden ännu på 1500-talet delad i tre tredingar med tretton, elva och nio hamnor – de gamla enheterna för ledungen, när landet skulle rusta skepp åt kungen.

![Karta över Fjädrundaland omkring år 1000 med runstenarna med och utan kors]({MAP['sv']})
**Karta.** Fjädrundaland omkring år 1000, då Mälaren var en vik av havet. Rostfärgat är Fjädrundaland, ljust grannlanden; gränserna är ungefärliga. Varje punkt är en runsten där det går att avgöra om den har ett kors – i Fjädrundaland är de grå punkterna många. Karta: Vitki, efter SGU:s modell för strandförskjutningen år 1000, Institutet för språk och folkminnens ortnamnsregister och Rundata.

## Stenarna utan kors

Stenen i Ågersta har inget kors, och det är inte ovanligt här. Bara en sten av tre i Fjädrundaland bär ett kors; i resten av Uppland bär sex av tio. Det är inte en ristares vana. Landets flitigaste ristare – Balle, Erik, Livsten, Tidkume och några till – högg många stenar utan kors, men också på de stenar som andra händer högg är korset lika ovanligt: sju av tjugofem. Och det är inte tiden, för skillnaden finns kvar när vi jämför stenar från samma årtionden.

Det betyder inte att folket var hedningar. Balle högg också en sten åt Ingileif efter hennes man Brune, som ”dog i Danmark i dopkläder” – nydöpt, alltså. Inte heller den stenen bär något kors. I Fjädrundaland kunde man vara kristen utan att sätta korset på stenen. En ristare antyder att det var landet och inte handen: Torbjörn högg kors på två av fem stenar här men på nio av tio utanför. Det är för få stenar för att bevisa något, men det är vad man skulle vänta sig om ristaren rättade sig efter beställarnas land.

Stenarna här är också ensammare. De står mer sällan i grupper, en av sju mot en av tre i resten av Uppland, och de är oftare resta av en enda person än av flera syskon eller släktingar tillsammans. Och de skriver på sitt eget sätt: hälften av stenarna stavar ʀ med r-runan, mot en av sju i resten av Uppland. Det har vi berättat mer om i [Erik skrev r – och bygden skrev efter]({ERIK}).

## Ett land som bar sina gamla tecken

Det här är det andra landet i serien där korset var ovanligt; det första var [Roden]({RODEN}), kustlandet. Men Fjädrundaland är ingen kust och ingen utmark. Det är ett bördigt, tätt bebott land med egna Husbygårdar och tingsplatser, mitt i Mälardalen, där människorna slog hö på de sanka ängarna, gick sina vägar längs åsarna och bodde bland tecken som var äldre än någon kunde minnas. Kanske hade man här helt enkelt sina egna sätt att forma en minnessten, och korset blev aldrig en del av dem, på samma sätt som man i [Sotholm]({SOTHOLM}) lät bönen vara. Den som står vid stenen i Ågersta ser en orm som slingrar sig över hela ytan och en uppmaning till den ristkunnige att tyda runorna. Mer behövde stenen inte säga.

## Så vet vi det

Landskapet, gravarna, vägarna och tingsplatserna bygger på *Det medeltida Sverige*, länsstyrelsens beskrivningar av bygderna och fornlämningsregistret. Att Adelsö hörde till Trögd, tingsplatsen vid Enhälja, ängarnas lotter, hamnorna och brevet från 1512 är kända från medeltiden och 1500-talet, inte från vikingatiden. Korset har vi mätt: Fjädrundalands runstenar jämfördes med resten av Upplands, med tiden hållen konstant, och skillnaden står sig när stenarna delas i två grupper socken för socken, när varje ristare får ha sin egen vana, när bara stenar på sin ursprungliga plats räknas och när landets egna ristare tas bort. De ensammare stenarna och r för ʀ håller i allt utom det sista steget, där det blir för få stenar kvar. Planerna och beräkningarna finns öppna på GitHub, länkade nedan.

## Källor

- Ferm, Olle, Johansson, Mats & Rahmqvist, Sigurd 1994. *Det medeltida Sverige* 1. Uppland 8. Fjädrundaland: Simtuna, Torstuna. Riksantikvarieämbetet.
- Rahmqvist, Sigurd 2010. *Det medeltida Sverige* 1. Uppland 9. Fjädrundaland: Trögds härad. Upplandsmuseet.
- Ferm, Olle, Johansson, Mats & Rahmqvist, Sigurd 1992. *Det medeltida Sverige* 1. Uppland 7. Attundaland: Bro, Färingö, Adelsö, Sollentuna. Riksantikvarieämbetet.
- Länsstyrelsen i Uppsala län 2018. Riksintressen för kulturmiljövården: Fjärdhundrabygden (C48), Enköpings-Näs (C57), Torsvi (C63).
- Stille, Per 1999. *Runstenar och runristare i det vikingatida Fjädrundaland. En studie i attribuering.* Runrön 13. Uppsala.
- Riksantikvarieämbetet, fornlämningsregistret (Kulturmiljöregistret), uttag 2026. Sveriges geologiska undersökning (SGU), strandförskjutningsmodell för år 1000.
- Samnordisk runtextdatabas (Rundata), Institutionen för nordiska språk, Uppsala universitet. Open Database License.
- Institutet för språk och folkminnen, ortnamnsregistret (PlaceNameService), socknar och härader. CC BY.
- Den låsta analysplanen och Vitkis beräkningar finns öppet på [GitHub](https://github.com/Precatio/runes) (analysplaner/2026-11-02-fjadrundaland.md).
- Bild: Wikimedia Commons, med fotografen i bildtexten."""

title_en = "The old lands: Fjädrundaland – the folkland at the far end of the bay"
summary_en = ("Fjädrundaland was the westernmost of Uppland's folklands: clay plains and wet meadows, farms on the edge of the "
              "moraine, roads along the ridges and the Bronze Age's signs on the rocks. Come into Lake Mälaren, still a bay of "
              "the sea, around AD 1000. The third part of the series The old lands.")

body_en = f"""Imagine sailing into Lake Mälaren a thousand years ago. It is not a lake yet but a bay of the sea, and furthest in to the west, where the water divides into inlets and sounds, lies Trögd: a peninsula that the water surrounds on the south-west, south and east. The islands off it – Oknö, Arnö, Grönsö – have been lived on since the Iron Age. From here people also went out. At Svinnegarn parents have raised stones for a son who "alone owned a ship and steered east in Ingvar's retinue".

Further east, where the inlet widens, Adelsö belongs to Trögd too. There, at Hovgården, lie five great mounds and a royal estate, and a stone says that Toli was the king's bryti, his steward. On the neighbouring island of Björkö, in the same parish, lay the town of Birka with Scandinavia's largest cemetery of mounds. The border with [Attundaland]({ATT}) ran just east of them.

This is Fjädrundaland, the westernmost of Uppland's three folklands. It is an old land, fertile and densely settled, and it faces the water.

## The clay and the meadows

Go ashore and follow a valley north. The clay lies heavy and shining in the furrows, and along the streams wet meadows spread out. That is where the hay is cut. Along the Örsundaån lies what will later be called the second largest wet meadow in Uppland, and already in the Middle Ages it was divided into long, narrow strips belonging to villages far away. Imagine the haymaking in late summer: the rows of people with scythes in the wet grass, the hay that must last the animals all winter.

The farms do not lie out on the plain but on its edge, where the clay meets the moraine and the ground is dry enough to live on. There the animals graze too, and there lie the graves, beside the villages. Furthest north, on Uppland's highest bedrock plateau, the small forest districts take over.

The graves here are simpler than elsewhere in Uppland. In Simtuna and Torstuna a grave field holds on average only ten to twelve graves, low and unassuming. But here and there something larger rises: the King's Mound at Torstunaby, thirty-five metres across and six metres high. And at Torsvi in Trögd, in a valley sloping down towards the bay of Torsviviken, a hundred and eighty graves from the Late Iron Age lie in a single grave field, nearly all round stone settings but also sixteen mounds.

## The signs on the rocks

This is an old land, and it shows. On the rock outcrops people had cut their signs more than a thousand years before the first runestone was raised. In Fjädrundaland about one ancient monument in seven is a rock carving, in the rest of Uppland one in thirty. Around Simtuna and Torstuna nearly two hundred and fifty mounds of fire-cracked stone, a few rock carvings and a great many cup marks show where the people of the Bronze Age lived. By the spring at Svinnegarn, which later became the county's best-known holy spring, visited by pilgrims, there are cup marks in the rock. And the very name Torsvi remembers a heathen cult place.

Whoever lived here around AD 1000 walked, then, among signs that were already ancient. What they believed about them we do not know. But they lived with them. Imagine the children playing on the rocks and the animals grazing among the signs.

## The roads between the villages

The roads run along the ridges. Along the Enköping ridge there are hollow ways, roads that traffic has worn down into the ground, and the runestones stand along the old roads; in Enköpings-Näs several of them stand by the main road. At Ågersta stands a stone that the carver Balle cut, with a serpent winding across the whole face. It speaks to whoever passes:

> *{nz("U 729")}*

Vidhugse had this stone raised in memory of Särev, his good father. He lived in Ågersta. Here shall the stone stand between the villages. May the rune-skilled interpret the runes that Balle carved.

![The runestone U 729 at Ågersta, cut by Balle, without a cross]({INFO[F729]['thumb']})
U 729 at Ågersta in Löt parish, cut by Balle. The serpent covers the stone; there is no cross. Photo: Bengt A. Lundberg, Swedish National Heritage Board, CC BY 2.5 se, via [Wikimedia Commons]({PAGE}).

"He lived in Ågersta." The stones here often say where the dead lived. Balle cut a stone for Gyda for her husband:

> *{nz("U 744")}*

Gyda had the stone raised in memory of Tordjärv, her husband, Gudlög's son, and he lived in Harvesta. Balle carved the stone.

In winter the ice becomes a road. As late as 1512 the bailiff in Trögd wrote that the men of the hundred wanted to bring in the tax by sledge if the winter road held, and otherwise by boat as soon as the ice broke up. Imagine the weeks in between, when the ice neither bore nor let go.

## Assemblies, hundreds and *hamnor*

Fjädrundaland had five hundreds: Trögd, Åsunda, Lagunda, Simtuna and Torstuna. Each hundred had its assembly. Trögd's assembly place lay by the village of Enhälja in Villberga and in 1299 was called Öbolund; in the Middle Ages witnesses and jurors came there from the villages of every mainland parish. Simtuna's name in -tuna suggests a gathering place since prehistory.

The land had its central estates too. At Svinnegarn there is a Husby with a great mound called Haralds kulle, and another Husby lies at Kungs-Husby. When the folkland was, early in the fourteenth century, the morning gift of King Birger's queen Märta, its centre was probably there. And in Trögd the taxed land was still divided in the sixteenth century into three thirds with thirteen, eleven and nine *hamnor* – the old units of the levy, when the land had to fit out ships for the king.

![Map of Fjädrundaland around AD 1000 with the runestones with and without a cross]({MAP['en']})
**Map.** Fjädrundaland around AD 1000, when Lake Mälaren was a bay of the sea. Rust is Fjädrundaland, light the neighbouring lands; the borders are approximate. Each point is a runestone where it can be told whether it carries a cross – in Fjädrundaland the grey points are many. Map: Vitki, after the Geological Survey of Sweden's shore-displacement model for AD 1000, the place-name register of the Institute for Language and Folklore, and Rundata.

## The stones without crosses

The stone at Ågersta has no cross, and that is not unusual here. Only one stone in three in Fjädrundaland carries a cross; in the rest of Uppland six in ten. It is not one carver's habit. The land's most prolific carvers – Balle, Erik, Livsten, Tidkume and a few more – cut many stones without a cross, but on the stones that other hands cut the cross is just as rare: seven of twenty-five. Nor is it time, for the difference remains when we compare stones from the same decades.

That does not mean the people were heathens. Balle also cut a stone for Ingileif for her husband Brune, who "died in christening robes in Denmark" – newly baptised, that is. That stone carries no cross either. In Fjädrundaland you could be a Christian without putting the cross on the stone. One carver hints that it was the land and not the hand: Torbjörn cut crosses on two of five stones here but on nine of ten outside. That is too few stones to prove anything, but it is what one would expect if the carver followed the land of those who ordered the stones.

The stones here are also lonelier. They stand less often in groups, one in seven against one in three in the rest of Uppland, and they are more often raised by a single person than by several siblings or kin together. And they write in their own way: half the stones spell ʀ with the r-rune, against one in seven in the rest of Uppland. We have told more about it in [Erik skrev r – och bygden skrev efter]({ERIK}).

## A land that kept its old signs

This is the second land in the series where the cross was rare; the first was [Roden]({RODEN}), the coastal land. But Fjädrundaland is no coast and no outland. It is a fertile, densely settled land with its own Husby estates and assembly places, in the middle of the Mälaren valley, where people cut hay on the wet meadows, walked their roads along the ridges and lived among signs older than anyone could remember. Perhaps people here simply had their own ways of shaping a memorial stone, and the cross never became part of them, just as in [Sotholm]({SOTHOLM}) they left out the prayer. Whoever stands by the stone at Ågersta sees a serpent winding across the whole face and a call to the rune-skilled to interpret the runes. The stone needed to say no more.

## How we know

The landscape, the graves, the roads and the assembly places rest on *Det medeltida Sverige*, the county board's descriptions of the districts and the register of ancient monuments. That Adelsö belonged to Trögd, the assembly place at Enhälja, the meadow strips, the *hamnor* and the letter of 1512 are known from the Middle Ages and the sixteenth century, not from the Viking Age. The cross we have measured: Fjädrundaland's runestones were compared with the rest of Uppland's, with time held constant, and the difference holds when the stones are split into two groups parish by parish, when each carver is allowed a habit of their own, when only stones in their original place are counted, and when the land's own carvers are removed. The lonelier stones and r for ʀ hold in everything but the last step, where too few stones remain. The plans and calculations are open on GitHub, linked below.

## Sources

- Ferm, Olle, Johansson, Mats & Rahmqvist, Sigurd 1994. *Det medeltida Sverige* 1. Uppland 8. Fjädrundaland: Simtuna, Torstuna. Swedish National Heritage Board.
- Rahmqvist, Sigurd 2010. *Det medeltida Sverige* 1. Uppland 9. Fjädrundaland: Trögds härad. Upplandsmuseet.
- Ferm, Olle, Johansson, Mats & Rahmqvist, Sigurd 1992. *Det medeltida Sverige* 1. Uppland 7. Attundaland: Bro, Färingö, Adelsö, Sollentuna. Swedish National Heritage Board.
- County Administrative Board of Uppsala 2018. Areas of national interest for cultural heritage: Fjärdhundrabygden (C48), Enköpings-Näs (C57), Torsvi (C63).
- Stille, Per 1999. *Runstenar och runristare i det vikingatida Fjädrundaland. En studie i attribuering.* Runrön 13. Uppsala.
- Swedish National Heritage Board, register of ancient monuments (Kulturmiljöregistret), extract 2026. Geological Survey of Sweden (SGU), shore-displacement model for AD 1000.
- Scandinavian Runic-text Data Base (Rundata), Department of Scandinavian Languages, Uppsala University. Open Database License.
- Institute for Language and Folklore, place-name register (PlaceNameService), parishes and hundreds. CC BY.
- The locked analysis plan and Vitki's calculations are open on [GitHub](https://github.com/Precatio/runes) (analysplaner/2026-11-02-fjadrundaland.md).
- Image: Wikimedia Commons, with the photographer in the caption."""

for b in (body, body_en):
    assert not re.search(r"^\|", b, re.M), "BlogBody har inga tabeller"
    assert ":::" not in b and "/karta" not in b and "/statistik" not in b

out = {"slug": "de-gamla-landen-fjadrundaland", "title": title, "summary": summary, "body": body,
       "title_en": title_en, "summary_en": summary_en, "body_en": body_en,
       "labels": ["Forskning", "Geografi", "Tro och magi", "Ristare"]}
from src import blog_labels  # noqa: E402
assert blog_labels.check(out["labels"]) is None, blog_labels.check(out["labels"])
path = os.path.join(ROOT, "utdata", "blogg", "fjadrundaland.json")
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
                 "topic": "Geografi|fjadrundaland", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
