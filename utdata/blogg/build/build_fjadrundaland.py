"""Artikeln "De gamla landen: Fjädrundaland – hällristningarnas land, där korset sällan höggs" (sv + en), del 3 i serien
De gamla landen, i seriens form v3 (atmosfär, berättad statistik, efterordet Så vet vi det). Siffrorna låses mot
utdata/fjadrundaland/fjadrundaland.json (plan analysplaner/2026-11-02-fjadrundaland.md, sha 6088f2af),
utdata/landprofiler/landprofiler.json och naringar.json.
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

title = "De gamla landen: Fjädrundaland – hällristningarnas land, där korset sällan höggs"
summary = ("Fjädrundaland var det västligaste av Upplands folkland, ett land av lerslätter och Mälarvikar där bronsålderns "
           "hällristningar redan var gamla när runstenarna restes. Där bär bara en sten av tre ett kors, mot sex av tio i resten "
           "av Uppland – vem som än högg den. Tredje delen i serien De gamla landen.")

body = f"""Föreställ dig att du seglar in i Mälaren för tusen år sedan. Den är ingen sjö ännu utan en vik av havet, och längst in i väster, där vattnet delar sig i fjärdar och sund, ligger Trögd: en halvö som vattnet omsluter i sydväst, söder och öster. Holmarna utanför – Oknö, Arnö, Grönsö – har haft folk sedan järnåldern. Härifrån for man också ut: i Svinnegarn har föräldrar rest stenar efter en son som ”ensam ägde ett skepp och styrde österut i Ingvars följe”.

Gå i land och följ en dalgång norrut. Leran ligger tung och blank i fårorna, och längs åarna breder sanka ängar ut sig där höet slås – längs Örsundaån ligger det som senare ska kallas Upplands näst största våtäng. Gårdarna ligger inte ute på slätten utan på kanten, där leran möter moränen och marken är torr nog att bo på. Längst i norr, på Upplands högsta urbergsplatå, tar de små skogsbygderna vid.

Det här är ett gammalt land, och det syns. På hällarna hade människor huggit sina tecken mer än tusen år innan den första runstenen restes – i Fjädrundaland är ungefär var sjunde fornlämning en hällristning, i resten av Uppland var trettionde. Gravarna är enklare än på andra håll; i landets norra del är gravfälten få och små. Men vid Torsvi i Trögd, där själva namnet minns en hednisk kultplats, ligger hundraåttio gravar från yngre järnålder i ett och samma gravfält.

Och så stenarna. Vid Ågersta står en sten som ristaren Balle har huggit, med en orm som slingrar sig över hela ytan – men inget kors. Den talar till den som går förbi:

> *{nz("U 729")}*

Vidhugse lät resa denna sten efter Särev, sin gode fader. Han bodde i Ågersta. Här ska stenen stå mellan byarna. Må den ristkunnige tyda de runor som Balle ristade.

![Runstenen U 729 vid Ågersta, huggen av Balle, utan kors]({INFO[F729]['thumb']})
U 729 vid Ågersta i Löts socken, huggen av Balle. Ormen täcker stenen; något kors finns inte. Foto: Bengt A. Lundberg, Riksantikvarieämbetet, CC BY 2.5 se, via [Wikimedia Commons]({PAGE}).

## Ett folkland vid vattnet

Fjädrundaland var det västligaste av Upplands tre folkland, med sina hundaren Trögd, Åsunda, Lagunda, Simtuna och Torstuna. Det hade sina centralorter: ett Husby i Svinnegarn, ett i Kungs-Husby, och Simtuna, vars namn på -tuna antyder en samlingsplats sedan förhistorien. När folklandet i början av 1300-talet var morgongåva åt kung Birgers drottning Märta låg dess centrum sannolikt vid Husby i Kungs-Husby. Och i Trögd var skattejorden ännu på 1500-talet delad i tre tredingar med tretton, elva och nio hamnor – de gamla enheterna för ledungen, när landet skulle rusta skepp åt kungen.

![Karta över Fjädrundaland omkring år 1000 med runstenarna med och utan kors]({MAP['sv']})
**Karta.** Fjädrundaland omkring år 1000, då Mälaren var en vik av havet. Rostfärgat är Fjädrundaland, ljust grannlanden; gränserna är ungefärliga. Varje punkt är en runsten där det går att avgöra om den har ett kors – i Fjädrundaland är de grå punkterna många. Karta: Vitki, efter SGU:s modell för strandförskjutningen år 1000, Institutet för språk och folkminnens ortnamnsregister och Rundata.

## Korsen som uteblev

Gå bland Fjädrundalands runstenar, och korset saknas oftare än det finns. En sten av tre bär ett kors; i resten av Uppland bär sex av tio. Det är inte en ristares vana. Landets flitigaste ristare – Balle, Erik, Livsten, Tidkume och några till – högg visserligen många stenar utan kors, men också på de stenar som andra händer högg är korset lika ovanligt: sju av tjugofem. Och det är inte tiden, för skillnaden finns kvar när vi jämför stenar från samma årtionden.

Det betyder inte att folket var hedningar. Balle högg också en sten åt Ingileif efter hennes man Brune, som ”dog i Danmark i dopkläder” – nydöpt, alltså. Inte heller den stenen bär något kors. I Fjädrundaland kunde man vara kristen utan att sätta korset på stenen.

En ristare antyder att det var landet och inte handen. Torbjörn högg två kors på fem stenar i Fjädrundaland men nio på tio utanför. Det är för få stenar för att bevisa något, men det är vad man skulle vänta sig om ristaren anpassade sig till beställarnas land.

Stenarna här är också ensammare. De står mer sällan i grupper om flera, en av sju mot en av tre i resten av Uppland, och de är oftare resta av en enda person än av flera syskon eller släktingar tillsammans. Och de skriver på sitt eget sätt: hälften av stenarna stavar ʀ med r-runan, mot en av sju i resten av Uppland. Där Öpir i Tiundaland skrev ordet för ’de’ ᚦᛅᛁᛦ, med yr-runan, skrev Balle i Fjädrundaland ᚦᛅᛁᚱ. Det har vi berättat mer om i [Erik skrev r – och bygden skrev efter]({ERIK}). Plustecknen mellan orden och formen *ræisti* hör däremot till ristarnas egna händer – de följer Balle och hans krets, inte landet.

## Ett land som bar sina gamla tecken

Varför höggs korset så sällan här? Vi vet inte. Det här är det andra landet i serien där korset var ovanligt; det första var [Roden]({RODEN}), kustlandet. Men Fjädrundaland är ingen kust och ingen utmark. Det är ett bördigt, tätt bebott land med egna kungsgårdar och tingsplatser, mitt i Mälardalen. Kanske är svaret det enkla: att man i det här landet hade sina egna sätt att forma en minnessten, och att korset aldrig blev en del av dem, på samma sätt som man i [Sotholm]({SOTHOLM}) lät bönen vara. Den som står vid stenen i Ågersta ser en orm som slingrar sig över hela ytan och en uppmaning till den ristkunnige att tyda runorna. Mer behövde stenen inte säga.

## Så vet vi det

Bakom texten finns en jämförelse av Fjädrundalands runstenar med resten av Upplands, med tiden hållen konstant. Korset är det säkraste: skillnaden står sig när stenarna delas i två grupper socken för socken, när varje ristare får ha sin egen vana, när bara stenar på sin ursprungliga plats räknas och när landets egna ristare tas bort. De ensammare stenarna och r för ʀ håller i allt utom det sista steget, där det blir för få stenar kvar. Att nio av tio stenar här har en känd ristare beror på att forskningen – främst Per Stilles avhandling från 1999 – har gått igenom just Fjädrundalands stenar noga; det säger mer om forskarna än om vikingarna. Hällristningarna och gravarna kommer ur fornlämningsregistret, landskapet ur *Det medeltida Sverige* och länsstyrelsens beskrivningar. Planerna och beräkningarna finns öppna på GitHub, länkade nedan.

## Källor

- Ferm, Olle, Johansson, Mats & Rahmqvist, Sigurd 1994. *Det medeltida Sverige* 1. Uppland 8. Fjädrundaland: Simtuna, Torstuna. Riksantikvarieämbetet.
- Rahmqvist, Sigurd 2010. *Det medeltida Sverige* 1. Uppland 9. Fjädrundaland: Trögds härad. Upplandsmuseet.
- Länsstyrelsen i Uppsala län 2018. Riksintressen för kulturmiljövården: Fjärdhundrabygden (C48), Enköpings-Näs (C57), Torsvi (C63).
- Stille, Per 1999. *Runstenar och runristare i det vikingatida Fjädrundaland. En studie i attribuering.* Runrön 13. Uppsala.
- Riksantikvarieämbetet, fornlämningsregistret (Kulturmiljöregistret), uttag 2026. Sveriges geologiska undersökning (SGU), strandförskjutningsmodell för år 1000.
- Samnordisk runtextdatabas (Rundata), Institutionen för nordiska språk, Uppsala universitet. Open Database License.
- Institutet för språk och folkminnen, ortnamnsregistret (PlaceNameService), socknar och härader. CC BY.
- Den låsta analysplanen och Vitkis beräkningar finns öppet på [GitHub](https://github.com/Precatio/runes) (analysplaner/2026-11-02-fjadrundaland.md).
- Bild: Wikimedia Commons, med fotografen i bildtexten."""

title_en = "The old lands: Fjädrundaland – land of the rock carvings, where the cross was seldom cut"
summary_en = ("Fjädrundaland was the westernmost of Uppland's folklands, a land of clay plains and bays of Lake Mälaren where "
              "the Bronze Age rock carvings were already old when the runestones were raised. There only one stone in three "
              "carries a cross, against six in ten in the rest of Uppland – whoever carved it. The third part of the series "
              "The old lands.")

body_en = f"""Imagine sailing into Lake Mälaren a thousand years ago. It is not a lake yet but a bay of the sea, and furthest in to the west, where the water divides into inlets and sounds, lies Trögd: a peninsula that the water surrounds on the south-west, south and east. The islands off it – Oknö, Arnö, Grönsö – have been lived on since the Iron Age. From here people also went out: at Svinnegarn parents have raised stones for a son who "alone owned a ship and steered east in Ingvar's retinue".

Go ashore and follow a valley north. The clay lies heavy and shining in the furrows, and along the streams wet meadows spread out where the hay is cut – along the Örsundaån lies what will later be called the second largest wet meadow in Uppland. The farms do not lie out on the plain but on its edge, where the clay meets the moraine and the ground is dry enough to live on. Furthest north, on Uppland's highest bedrock plateau, the small forest districts take over.

This is an old land, and it shows. On the rock outcrops people had cut their signs more than a thousand years before the first runestone was raised – in Fjädrundaland about one ancient monument in seven is a rock carving, in the rest of Uppland one in thirty. The graves are simpler than elsewhere; in the north of the land the grave fields are few and small. But at Torsvi in Trögd, where the very name remembers a heathen cult place, a hundred and eighty graves from the Late Iron Age lie in a single grave field.

And then the stones. At Ågersta stands a stone that the carver Balle cut, with a serpent winding across the whole face – but no cross. It speaks to whoever passes:

> *{nz("U 729")}*

Vidhugse had this stone raised in memory of Särev, his good father. He lived in Ågersta. Here shall the stone stand between the villages. May the rune-skilled interpret the runes that Balle carved.

![The runestone U 729 at Ågersta, cut by Balle, without a cross]({INFO[F729]['thumb']})
U 729 at Ågersta in Löt parish, cut by Balle. The serpent covers the stone; there is no cross. Photo: Bengt A. Lundberg, Swedish National Heritage Board, CC BY 2.5 se, via [Wikimedia Commons]({PAGE}).

## A folkland by the water

Fjädrundaland was the westernmost of Uppland's three folklands, with its hundreds Trögd, Åsunda, Lagunda, Simtuna and Torstuna. It had its central places: a Husby at Svinnegarn, another at Kungs-Husby, and Simtuna, whose name in -tuna suggests an assembly place since prehistory. When the folkland was, early in the fourteenth century, the morning gift of King Birger's queen Märta, its centre was probably at Husby in Kungs-Husby. And in Trögd the taxed land was still divided in the sixteenth century into three thirds with thirteen, eleven and nine *hamnor* – the old units of the levy, when the land had to fit out ships for the king.

![Map of Fjädrundaland around AD 1000 with the runestones with and without a cross]({MAP['en']})
**Map.** Fjädrundaland around AD 1000, when Lake Mälaren was a bay of the sea. Rust is Fjädrundaland, light the neighbouring lands; the borders are approximate. Each point is a runestone where it can be told whether it carries a cross – in Fjädrundaland the grey points are many. Map: Vitki, after the Geological Survey of Sweden's shore-displacement model for AD 1000, the place-name register of the Institute for Language and Folklore, and Rundata.

## The crosses that stayed away

Walk among Fjädrundaland's runestones, and the cross is missing more often than it is there. One stone in three carries a cross; in the rest of Uppland six in ten. It is not one carver's habit. The land's most prolific carvers – Balle, Erik, Livsten, Tidkume and a few more – did cut many stones without a cross, but on the stones that other hands cut the cross is just as rare: seven of twenty-five. Nor is it time, for the difference remains when we compare stones from the same decades.

That does not mean the people were heathens. Balle also cut a stone for Ingileif for her husband Brune, who "died in christening robes in Denmark" – newly baptised, that is. That stone carries no cross either. In Fjädrundaland you could be a Christian without putting the cross on the stone.

One carver hints that it was the land and not the hand. Torbjörn cut crosses on two of five stones in Fjädrundaland but on nine of ten outside it. That is too few stones to prove anything, but it is what one would expect if the carver adapted to the land of those who ordered the stones.

The stones here are also lonelier. They stand less often in groups, one in seven against one in three in the rest of Uppland, and they are more often raised by a single person than by several siblings or kin together. And they write in their own way: half the stones spell ʀ with the r-rune, against one in seven in the rest of Uppland. Where Öpir in Tiundaland wrote the word for 'they' ᚦᛅᛁᛦ, with the yr-rune, Balle in Fjädrundaland wrote ᚦᛅᛁᚱ. We have told more about it in [Erik skrev r – och bygden skrev efter]({ERIK}). The plus signs between the words and the form *ræisti*, on the other hand, belong to the carvers' own hands – they follow Balle and his circle, not the land.

## A land that kept its old signs

Why was the cross so seldom cut here? We do not know. This is the second land in the series where the cross was rare; the first was [Roden]({RODEN}), the coastal land. But Fjädrundaland is no coast and no outland. It is a fertile, densely settled land with its own royal estates and assembly places, in the middle of the Mälaren valley. Perhaps the answer is the simple one: that in this land people had their own ways of shaping a memorial stone, and that the cross never became part of them, just as in [Sotholm]({SOTHOLM}) they left out the prayer. Whoever stands by the stone at Ågersta sees a serpent winding across the whole face and a call to the rune-skilled to interpret the runes. The stone needed to say no more.

## How we know

Behind the text lies a comparison of Fjädrundaland's runestones with the rest of Uppland's, with time held constant. The cross is the surest: the difference holds when the stones are split into two groups parish by parish, when each carver is allowed a habit of their own, when only stones in their original place are counted, and when the land's own carvers are removed. The lonelier stones and r for ʀ hold in everything but the last step, where too few stones remain. That nine in ten stones here have a known carver is because research – above all Per Stille's thesis of 1999 – has gone through Fjädrundaland's stones with particular care; it says more about the researchers than about the Vikings. The rock carvings and graves come from the register of ancient monuments, the landscape from *Det medeltida Sverige* and the county board's descriptions. The plans and calculations are open on GitHub, linked below.

## Sources

- Ferm, Olle, Johansson, Mats & Rahmqvist, Sigurd 1994. *Det medeltida Sverige* 1. Uppland 8. Fjädrundaland: Simtuna, Torstuna. Swedish National Heritage Board.
- Rahmqvist, Sigurd 2010. *Det medeltida Sverige* 1. Uppland 9. Fjädrundaland: Trögds härad. Upplandsmuseet.
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
