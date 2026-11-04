"""Artikeln "De gamla landen: Roden – kusten som räknade i skepp" (sv + en), del 2 i serien De gamla landen. Sedan
2026-11-04 i seriens atmosfäriska form (Viktor): kusten, gården vid viken, skeppslagen och Jarlabankes Täby; korsen som är
färre står kvar som ett inslag. Siffrorna låses mot utdata/roden/roden.json (plan analysplaner/2026-11-02-roden.md, sha
59ea6d58), utdata/landprofiler/landprofiler.json (plan eb59f631) och utdata/gamla_granser/monster.json (plan 054c87d5);
landskapet mot DMS 1:1, Larsson 1993 och länsstyrelsens riksintressebeskrivningar C18/C19.
    ../../../.venv/bin/python build_roden.py [--write | --update DOC]"""
import csv
import datetime as dt
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_figures, commons  # noqa: E402

R = json.load(open(os.path.join(ROOT, "utdata", "roden", "roden.json"), encoding="utf-8"))
LP = json.load(open(os.path.join(ROOT, "utdata", "landprofiler", "landprofiler.json"), encoding="utf-8"))["tests"]
M = json.load(open(os.path.join(ROOT, "utdata", "gamla_granser", "monster.json"), encoding="utf-8"))
ST = list(csv.DictReader(open(os.path.join(ROOT, "utdata", "roden", "roden_stenar.csv"), encoding="utf-8")))
recs = {r["signum"]: r for r in json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["inscriptions"]}
nz = lambda s: recs[s]["normalization"].replace('"', "").strip()  # noqa: E731
pc = lambda x: round(100 * x)  # noqa: E731

# ---- the locked numbers -----------------------------------------------------------------------------------------------
K, C = R["T1"]["pm_kors"], R["T1"]["cat_kristen"]
assert (K["grund"]["k_in"], K["grund"]["n_in"], pc(K["grund"]["share_in"]), pc(K["grund"]["share_out"])) == (24, 60, 40, 59)
assert (C["grund"]["k_in"], C["grund"]["n_in"], pc(C["grund"]["share_in"]), pc(C["grund"]["share_out"])) == (5, 60, 8, 21)
assert [k for k, v in K.items() if not v["holds"]] == ["b_pa_plats"] and round(K["b_pa_plats"]["p"], 2) == 0.09
assert [k for k, v in C.items() if not v["holds"]] == ["a_ristare_slump"] and round(C["a_ristare_slump"]["p"], 2) == 0.06
assert R["desc"]["ro_carvers"] == ["Fot", "Öpir"] and R["desc"]["n_tby"] == 25 and R["desc"]["n_roden"] == 60
assert R["T2"]["pm_kors"]["holds"] and R["T2"]["cat_kristen"]["holds"] and R["holm"]["T2_kors"] < 0.02
assert round(R["T2"]["pm_kors"]["dist_only"]["p"], 2) == 0.84 and round(R["T2"]["cat_kristen"]["dist_only"]["p"], 2) == 0.34
assert round(R["desc"]["km_median_roden"] * 1000) == 108 and round(R["desc"]["km_median_rest"] * 1000) == 250
B = R["T3"]["msg_dod_borta"]
assert (B["k_in"], B["n_in"], pc(B["share_in"]), pc(B["share_out"])) == (7, 60, 12, 3) and R["holm"]["T3_borta"] < 0.02
assert R["holm"]["T3_fard"] > 0.05
ro = [r for r in ST if r["region"] == "roden"]
taby = [r for r in ro if r["parish"] == "Täby sn"]
assert sum(r["msg_dod_borta"] == "1" for r in taby) == 6 and sum(r["msg_dod_borta"] == "1" for r in ro) == 7
nt = [r for r in ro if r["parish"] != "Täby sn"]
assert (sum(r["pm_kors"] == "1" for r in nt), len(nt)) == (12, 35)
# the narrow plan (054c87d5, step 2) and the broad palette (eb59f631)
S2 = {t["feature"]: t for t in M["step2"]["tests"] if t["unit"] == "roden"}
assert S2["pm_kors"]["holds"] and S2["cat_kristen"]["holds"]
lp = {(t["domain"], t["feature"]): t for t in LP if t["unit"] == "roden" and t["kind"] == "land"}
assert round(lp[("sed", "pm_kors")]["q"], 2) == 0.07 and not lp[("sed", "pm_kors")]["holds"]
V = {k: lp[("ortnamn", k)] for k in ("n_vik", "n_nas", "n_sta", "n_by")}
assert all(v["holds"] and v["inom_lan"]["result"] == "håller" for v in V.values())
assert [round(100 * V[k]["share_in"], 1) for k in V] == [4.1, 2.8, 1.5, 3.4]
assert [round(100 * V[k]["share_out"], 1) for k in V] == [1.2, 1.1, 4.9, 7.1]
G1, G2 = lp[("gravskick", "gf_fler_hogar")], lp[("gravskick", "gf_rest_sten")]
assert G1["holds"] and G2["holds"] and G1["inom_lan"]["result"] == G2["inom_lan"]["result"] == "håller"
assert (pc(G1["share_in"]), pc(G1["share_out"]), pc(G2["share_in"]), pc(G2["share_out"])) == (19, 8, 6, 14)
CO = lp[("plats", "nara_centralort")]
assert CO["holds"] and (pc(CO["share_in"]), pc(CO["share_out"])) == (20, 49)
# texts
assert "Hann do a Langbarðalandi" in nz("U 141") and nz("U 141").startswith("Guðlaug") and "es sotti IorsaliR ok ændaðis upp i Grikkium" in nz("U 136")
assert "Hann vas drepinn a Virlandi" in nz("U 533")
assert "ok æinn atti allan Tæby. Guð hialpi and hans" in nz("U 164")
assert "ok æinn atti allt hu[n]dari þetta" in nz("U 212") and recs["U 212"]["parish"] == "Vallentuna sn"
assert recs["U 164"]["carvers"][0]["name"] == "Fot 2"
# DMS 1:1 Norra Roden (Dahlbäck, Jansson & Westin 1972), deduplicated text
DMS = open("/Volumes/2TB/Antigrvity/Runes/geografi_kallor/dms/dms_1_1_dedup.txt", encoding="utf-8").read()
for k in ("Frågan om Rodens territoriella omfattning och kamerala och judiciella indelning är omstridd",
          "Områdets karaktär av skärgårdslandskap har under äldre tider varit än mer markant",
          "långa uddar, smala näs och ett stort antal öar och skär", "bosättningen där är ung",
          "från ett skeppslags ting till två skeppslags ting, därifrån till sex skeppslags ting och sist till kung eller hertig",
          "Rodens, beräknade med skeppslagen som indelningsgrund", "Rubriken Raden i Tiundalandsavsnittet",
          "Göran Dahlbäck", "Gunnar T W estin", "Stockholm i februari 1972"):
    assert k in DMS, k

for k in ("1185 utfärdar påven skyddsbrev för Uppsala domkyrka och dess egendom, bl a flera fisken i Ä",
          "skänker kung Knut Julita kloster en del i fisket i Ä"):
    assert k in DMS, k
D21 = open("/Volumes/2TB/Antigrvity/Runes/downloads/sotholm_lit/dms_dedup.txt", encoding="utf-8").read()
assert "Vindö (i Värmdö skepps" in D21 and "till Runmarö (i Värmdö skeppslag)" in D21 and "Danska itinerariet" in D21
LAR = " ".join(open("/Volumes/2TB/Antigrvity/Runes/geografi_kallor/litteratur/Larsson_1993.txt", encoding="utf-8").read().split())
assert "Skeppslaget lever också kvar i det uppländska kustområdet Roden, men är där i de flesta fall sannolikt en yngre företeelse" in LAR
BH = [t for t in json.load(open(os.path.join(ROOT, "utdata", "landprofiler", "naringar.json"))) if t["unit"] == "roden"][0]["profile"]["båtar och hamnar"]
assert round(BH["share_in_county"] / BH["share_rest_county"]) == 4

# ---- picture and map ----------------------------------------------------------------------------------------------------
F136 = "U 136, Broby bro.jpg"
INFO = commons.commons_info([F136])
assert INFO[F136]["licence"] == "CC BY 2.5" and INFO[F136]["author"] == "Berig"
PAGE = "https://commons.wikimedia.org/wiki/File:" + F136.replace(" ", "_")
MAP = {lang: blog_figures.freeze(open(os.path.join(ROOT, "utdata", "roden", f"karta_roden_{lang}.png"), "rb").read())
       for lang in ("sv", "en")}  # utdata/roden/karta_roden.R
SOTHOLM = "/artiklar/de-gamla-landen-sotholm"

# ---- the land as it was lived in (rewrite 2026-11-04: the series is atmospheric, the runestones one part of the place) --
LS = "/Volumes/2TB/Antigrvity/Runes/downloads/roden_lit/"  # Länsstyrelsen Uppsala, riksintressen C18 (Hökhuvud), C19 (Östhammar)
C18 = " ".join(open(LS + "RI-kultur_C18.txt", encoding="utf-8").read().replace("in-sprängda", "insprängda").split())
C19 = " ".join(open(LS + "RI-kultur_C19.txt", encoding="utf-8").read().split())
for k in ("Landskapet är kuperat och omväxlande med större barrskogsklädda partier", "Området blev färdigkoloniserat under vikingatid och tidig medeltid",
          "Gravfält finns intill de flesta byarna och även det vägnät som sammanbinder dem kan genom fornlämningarna föras tillbaka till förhistorisk tid",
          "en intill ett mindre gravfält söder om Hanunda by", "Hanundastenen har förutom runristningen även en ryttarfigur och en fågelbild"):
    assert k in C18, k
for k in ("Östhammar började tidigt under medeltiden att utvecklas ur en liten handelsplats, där framför allt fiskare och bönder bytte varor",
          "Staden hette då Hamar och låg vid en havsvik"):
    assert k in C19, k
assert recs["U 599"]["place"] == "Hanunda" and recs["U 599"]["parish"] == "Hökhuvuds sn" and "Þorfastr risti runaR" in nz("U 599")
assert nz("U 599").startswith("Arnniutr ok Vigniutr ok Signiutr þæiR letu ræisa stæin") and [r for r in ST if r["signum"] == "U 599"][0]["region"] == "roden"
assert "ok þingstað þenna gærði" in nz("U 212") and recs["U 225"]["place"] == "Bällsta" and recs["U 225"]["parish"] == "Vallentuna sn"
assert "þæiR gærðu hiar þingstað" in nz("U 225") and "Ulfs syniR" in nz("U 225")

title = "De gamla landen: Roden – kusten som räknade i skepp"
summary = ("Upplands kust var på vikingatiden ett land för sig, Roden: djupa vikar och smala näs, unga gårdar på mark som "
           "nyss stigit ur havet, båtar uppdragna på stränderna. I lagen räknades det i skeppslag i stället för hundaren. Följ "
           "med längs kusten omkring år 1000. Andra delen i serien De gamla landen.")

body = f"""Föreställ dig att du ror norrut längs Upplands kust för tusen år sedan. Landet ser inte ut som det kommer att göra. Havet går långt in i det, vikarna skär djupt mellan bergen, och det som senare ska bli ådalar är ännu fjärdar där båten kan glida in mellan alarna. Överallt finns uddar och smala näs, holmar och skär. Längst i norr har landet nyss stigit ur havet; där är bygden ung, gårdarna nya, och strandängarna växer ut för varje generation. Där Dalälven störtar ut i havet vid Älvkarleby fångar man lax – när breven börjar tala, på 1180-talet, skyddar påven domkyrkans fisken där och kungen ger bort en del av fisket till ett kloster.

Föreställ dig lukten av tång och tjära, ljudet av åror mot tollarna, måsarna över grunden. I söder, i Värmdös skärgård, går sjövägen mellan holmarna; ännu i medeltidens danska seglingsbeskrivning slutar lederna vid Runmarö och Vindö. Det här är Roden, kustlandet. Här är vattnet vägen.

## Gården vid viken

Gårdarna ligger där en vik möter en dalgång, och deras namn talar om vattnet. Gårdar som heter något på *-vik* är drygt tre gånger så vanliga här som i resten av Uppland, och *-näs* mer än dubbelt så vanliga, medan inlandets *-sta* och *-by* är hälften så vanliga eller mindre. Längs stränderna har inventerarna hittat fyra gånger så många båtlänningar och hamnlämningar, räknat mot allt annat, som i resten av Uppland. De kommer från alla tider, men de visar var båtarna drogs upp. Föreställ dig en båt uppdragen nedanför varje gård, lika självklar som kon i fähuset.

De döda begravs på backarna ovanför stränderna. På gravfälten här är högarna fler än de låga stensättningarna oftare än i folklanden inåt land, och de resta stenarna är färre. Det är inte bara olika sätt att inventera: skillnaderna finns kvar också när vi bara jämför med grannar inom samma län.

Längst i norr, i Hökhuvud, är landet kuperat, med stora partier barrskog mellan gårdarna. Bygden där blev färdigodlad först under vikingatiden och den tidiga medeltiden, och gravfälten ligger intill de flesta byarna. Vägarna mellan byarna är så gamla att fornlämningarna följer dem. Vid en av dem, intill ett litet gravfält söder om Hanunda, står en sten som tre bröder lät resa efter sin far. Utöver runorna bär den en ryttare och en fågel:

> *{nz("U 599")}*

Arnnjut och Vignjut och Signjut lät resa denna sten efter …, sin fader. Torfast ristade runorna.

Längre fram i medeltiden växer en liten handelsplats fram vid en havsvik i norr, Hamar, där fiskare och bönder byter varor med varandra. Det är lätt att föreställa sig samma byte längs hela kusten långt tidigare: det man inte fick av jorden fick man av havet.

## Ett land av skeppslag

De tre folklanden inåt land – Tiundaland, Attundaland och Fjädrundaland – var indelade i hundaren. Roden var indelat i skeppslag, och det syns i lagen. När Upplandslagen skrevs ner kring år 1300 gick en tvist i folklanden från hundaresting till folklandsting och sist till kungen; i Roden gick den från ett skeppslags ting till två skeppslags ting, därifrån till sex skeppslags ting och sist till kung eller hertig. Också ledungen, skatten till kungens flotta, räknades i Roden efter skeppslagen och inte efter hundarena. Kusten räknade i skepp.

Hur gammal den ordningen är vet vi inte. Historikern Mats G. Larsson menar att skeppslagen i Roden ”i de flesta fall sannolikt [är] en yngre företeelse” – lagens Roden är medeltidens, och det land där stenarna restes kan ha varit ordnat på ett annat sätt. Inte heller hur stort Roden var, eller om det var ett land för sig eller en del av folklanden, är säkert. Göran Dahlbäck och Gunnar T. Westin skriver i *Det medeltida Sverige* att ”Frågan om Rodens territoriella omfattning och kamerala och judiciella indelning är omstridd”. I sexårsgärden 1314 står Roden som en rubrik under Tiundaland.

![Karta över Roden och folklanden omkring år 1000 med runstenarna med och utan kors]({MAP['sv']})
**Karta.** Upplands kust omkring år 1000, då havet gick mycket längre in i landet än senare. Rostfärgat är Roden, ljust de tre folklanden; gränserna är ungefärliga, dragna efter häradernas socknar. Varje punkt är en runsten där det går att avgöra om den har ett kors. Karta: Vitki, efter SGU:s modell för strandförskjutningen år 1000, Institutet för språk och folkminnens ortnamnsregister och Rundata.

## Jarlabankes Täby

Längre söderut, där kusten bryts upp mot Mälarens mynning, ligger Täby. Här bor en storman, Jarlabanke, som låter resa stenar vid en bro han har byggt och skriva att han ensam äger hela byn:

> *{nz("U 164")}*

Jarlabanke lät resa dessa stenar efter sig själv medan han levde, och gjorde denna bro för sin själ, och han ensam ägde hela Täby. Gud hjälpe hans själ.

Täby räknades till Danderyds skeppslag. Men på en sten vid Vallentuna kyrka, i Attundaland, skriver Jarlabanke att han ”gjorde denna tingsplats” och ”ensam ägde hela detta hundare”. Gränsen mellan kustlandet och folklandet gick alltså mitt i hans värld. En tingsplats var något man gjorde, och också vid Bällsta i Vallentuna skrev Ulvs söner på en sten att de ”gjorde här tingsplats”.

I Jarlabankes bygd reser kvinnor stenar efter dem som aldrig kom hem. Guðlaug efter sin son Holme, som dog i Lombardiet. Åstrid efter sin man Östen:

> *{nz("U 136")}*

Åstrid lät resa dessa stenar efter Östen, sin man, som for till Jerusalem och dog uppe i Grekland.

![Runstenen U 136 vid Broby bro]({INFO[F136]['thumb']})
U 136 vid Broby bro i Täby, rest av Åstrid efter Östen som for till Jerusalem. Foto: Berig, CC BY 2.5, via [Wikimedia Commons]({PAGE}).

Stenar som berättar om död långt borta – i Lombardiet, i Grekland, i öster – är fler i Roden än i resten av Uppland. Men nästan alla står i Täby. Det är en bygds historia: en släkt och dess grannar som for ut i världen och reste stenar när de inte kom hem.

## Färre kors

Gå bland Rodens stenar, och en sak märks efter ett tag. Korset, som i folklanden inåt land sitter på sex stenar av tio, sitter här bara på fyra. Böner för de döda är ännu ovanligare: i resten av Uppland ber ungefär var femte sten, här knappt en av tolv. Det beror inte på några enskilda ristare – också när Fot och Öpir, Rodens flitigaste, räknas bort är korsen färre.

Det naturliga är att tänka att det är havet, att folk vid stranden levde annorlunda än folk i inlandet, vad deras land än hette. Rodens stenar står också närmare vattnet: hälften av dem inom ett hundratal meter från strandlinjen år 1000. Men i resten av Uppland spelar det ingen roll om en sten står vid vattnet eller långt därifrån – korset är lika vanligt. Och när vi tar hänsyn till närheten till vattnet står skillnaden för Roden kvar, lika stor som förut. Det är landet, inte stranden.

## Ett land som vände sig mot havet

Varför bar Rodens stenar färre kors? Vi vet inte. Men en ledtråd finns. Rodens stenar står sällan nära de gamla centralorterna, Husby och Tuna, där kungamakten hade sina gårdar – bara en av fem, mot hälften i folklanden. Kanske nådde korset Uppland längs de vägar som gick genom kungens gårdar, och kustlandet, som vände sig mot havet och styrdes på sitt eget sätt, tog det till sig långsammare. Det är en tanke, inte ett resultat.

Den som ror förbi Rodens stränder ser ändå något annat än skillnader i stenar: båtarna dragna upp på land, högarna på backen ovanför, röken från gårdarna längst in i vikarna. Ett land där vattnet var vägen och där man räknade i skepp.

Det här är andra delen i serien De gamla landen. Den första tog oss till [Sotholm på ön Tören]({SOTHOLM}), där bygderna låg i skogens gläntor och stenarna bar kors men inte bad.

## Så vet vi det

Landskapet och livet längs kusten bygger på *Det medeltida Sverige*, länsstyrelsens beskrivningar av bygderna och fornlämningsregistret; namnen och gravarna har vi räknat ur registret och kartorna, och båtlänningarna kan vara från alla tider. Skeppslagen och handelsplatsen är kända från medeltiden, inte från vikingatiden. Korsen har vi mätt: Rodens runstenar jämfördes med resten av Upplands, med tiden hållen konstant, och prövningen att närheten till havet inte förklarar skillnaden låstes innan vi räknade. Skillnaden står sig när stenarna delas i två grupper socken för socken och när de största ristarnas stenar tas bort, men inte när bara stenar på sin ursprungliga plats räknas, och en stor del av Rodens stenar står i Täby, vars plats i Roden är omstridd. Planerna och beräkningarna finns öppna på GitHub, länkade nedan.

## Källor

- Dahlbäck, Göran, Jansson, Bengt & Westin, Gunnar T. 1972. *Det medeltida Sverige* 1. Uppland 1. Norra Roden. Kungl. Vitterhets Historie och Antikvitets Akademien.
- Janzon, Kaj & Rahmqvist, Sigurd 2002. *Det medeltida Sverige* 2. Södermanland 1. Tören: Svartlösa, Sotholm. Riksantikvarieämbetet (den danska seglingsbeskrivningen).
- Larsson, Mats G. 1993. Kung Eriks nyordning. *Uppland* 1993, s. 105–134.
- Länsstyrelsen i Uppsala län 2018. Riksintressen för kulturmiljövården: Bygden norr om Hökhuvuds kyrka (C18), Östhammars stad (C19).
- Riksantikvarieämbetet, fornlämningsregistret (Kulturmiljöregistret), uttag 2026.
- Sveriges geologiska undersökning (SGU), strandförskjutningsmodell för år 1000.
- Samnordisk runtextdatabas (Rundata), Institutionen för nordiska språk, Uppsala universitet. Open Database License.
- Institutet för språk och folkminnen, ortnamnsregistret (PlaceNameService), socknar och härader. CC BY. Gårdsnamnen ur OpenStreetMap (ODbL).
- De låsta analysplanerna, data och Vitkis beräkningar finns öppet på [GitHub](https://github.com/Precatio/runes) (analysplaner/2026-11-02-roden.md och 2026-11-02-landprofiler.md).
- Bild: Wikimedia Commons, med fotografen i bildtexten."""

title_en = "The old lands: Roden – the coast that counted in ships"
summary_en = ("In the Viking Age the coast of Uppland was a land of its own, Roden: deep bays and narrow necks of land, young "
              "farms on ground just risen from the sea, boats hauled up on the shores. In the law it was reckoned in ship "
              "districts rather than hundreds. Come along the coast around AD 1000. The second part of the series The old lands.")

body_en = f"""Imagine rowing north along the coast of Uppland a thousand years ago. The land does not look as it later will. The sea reaches far into it, the bays cut deep between the hills, and what will later become river valleys are still inlets where the boat can glide in among the alders. Everywhere there are points and narrow necks of land, islets and skerries. Furthest north the land has only just risen from the sea; there the settlement is young, the farms new, and the shore meadows grow outwards with every generation. Where the Dalälven river falls into the sea at Älvkarleby, people catch salmon – when the charters begin to speak, in the 1180s, the pope protects the cathedral's fisheries there and the king gives part of the fishery to a convent.

Imagine the smell of seaweed and tar, the sound of oars against the thole-pins, the gulls over the shallows. In the south, in the archipelago of Värmdö, the sea road runs between the islets; still in the medieval Danish sailing description the routes end at Runmarö and Vindö. This is Roden, the coastal land. Here the water is the road.

## The farm by the bay

The farms lie where a bay meets a valley, and their names speak of the water. Farms with names in *-vik*, 'bay', are more than three times as common here as in the rest of Uppland, and *-näs*, 'point', more than twice as common, while the inland *-sta* and *-by* are half as common or less. Along the shores the surveyors have found four times as many boat landings and harbour remains, counted against everything else, as in the rest of Uppland. They come from all periods, but they show where the boats were hauled up. Imagine a boat hauled up below every farm, as much a matter of course as the cow in the byre.

The dead are buried on the slopes above the shores. On the grave fields here, mounds outnumber the low stone settings more often than in the folklands inland, and the standing stones are fewer. It is not just different ways of surveying: the differences remain when we compare only with neighbours in the same county.

Furthest north, in Hökhuvud, the land is hilly, with large stretches of pine forest between the farms. The settlement there was fully cleared only during the Viking Age and the early Middle Ages, and the grave fields lie beside most of the villages. The roads between the villages are so old that the ancient monuments follow them. By one of them, beside a small grave field south of Hanunda, stands a stone that three brothers had raised for their father. Besides the runes it carries a rider and a bird:

> *{nz("U 599")}*

Arnnjut and Vignjut and Signjut had this stone raised in memory of …, their father. Torfast carved the runes.

Later in the Middle Ages a small trading place grows up by a bay in the north, Hamar, where fishermen and farmers trade goods with one another. It is easy to imagine the same exchange along the whole coast long before: what the soil did not give, the sea did.

## A land of ship districts

The three folklands inland – Tiundaland, Attundaland and Fjädrundaland – were divided into hundreds. Roden was divided into ship districts, *skeppslag*, and it shows in the law. When the Law of Uppland was written down around 1300, a dispute in the folklands went from the hundred's assembly to the folkland's assembly and finally to the king; in Roden it went from the assembly of one ship district to that of two, then to that of six, and finally to king or duke. The levy for the king's fleet, too, was reckoned in Roden by ship districts and not by hundreds. The coast counted in ships.

How old that order is we do not know. The historian Mats G. Larsson argues that the ship districts in Roden are "in most cases probably a younger phenomenon" – the Roden of the law is the Middle Ages', and the land where the stones were raised may have been organised differently. Nor is it certain how large Roden was, or whether it was a land of its own or part of the folklands. Göran Dahlbäck and Gunnar T. Westin write in *Det medeltida Sverige* that "the question of Roden's territorial extent and its fiscal and judicial division is disputed". In the six-year tithe of 1314 Roden appears as a heading under Tiundaland.

![Map of Roden and the folklands around AD 1000 with the runestones with and without a cross]({MAP['en']})
**Map.** The coast of Uppland around AD 1000, when the sea reached much further into the land than later. Rust is Roden, light the three folklands; the borders are approximate, drawn after the parishes of the hundreds. Each point is a runestone where it can be told whether it carries a cross. Map: Vitki, after the Geological Survey of Sweden's shore-displacement model for AD 1000, the place-name register of the Institute for Language and Folklore, and Rundata.

## Jarlabanke's Täby

Further south, where the coast breaks up towards the mouth of Lake Mälaren, lies Täby. A great man lives here, Jarlabanke, who has stones raised at a bridge he has built and has it written that he alone owns the whole village:

> *{nz("U 164")}*

Jarlabanke had these stones raised in memory of himself while alive, and made this bridge for his soul, and he alone owned all of Täby. May God help his soul.

Täby was counted in the ship district of Danderyd. But on a stone at Vallentuna church, in Attundaland, Jarlabanke writes that he "made this assembly place" and "alone owned all of this hundred". The border between the coastal land and the folkland ran through the middle of his world. An assembly place was something one made, and at Bällsta in Vallentuna, too, Ulf's sons wrote on a stone that they "made here an assembly place".

In Jarlabanke's district women raise stones for those who never came home. Guðlaug for her son Holme, who died in Lombardy. Åstrid for her husband Östen:

> *{nz("U 136")}*

Åstrid had these stones raised in memory of Östen, her husband, who went to Jerusalem and died up in Greece.

![The runestone U 136 at Broby bro]({INFO[F136]['thumb']})
U 136 at Broby bro in Täby, raised by Åstrid for Östen who went to Jerusalem. Photo: Berig, CC BY 2.5, via [Wikimedia Commons]({PAGE}).

Stones that tell of death far away – in Lombardy, in Greece, in the east – are more common in Roden than in the rest of Uppland. But nearly all of them stand in Täby. That is the history of one district: a family and its neighbours who went out into the world and raised stones when they did not come home.

## Fewer crosses

Walk among Roden's stones, and after a while one thing stands out. The cross, which in the folklands inland sits on six stones in ten, here sits on only four. Prayers for the dead are rarer still: in the rest of Uppland about one stone in five prays, here hardly one in twelve. It is not down to particular carvers – even when Fot and Öpir, Roden's most prolific, are left out, the crosses are fewer.

The natural thought is that it is the sea, that people by the shore lived differently from people inland, whatever their land was called. Roden's stones do stand closer to the water: half of them within a hundred metres or so of the shoreline of AD 1000. But in the rest of Uppland it makes no difference whether a stone stands by the water or far from it – the cross is just as common. And when we take the closeness of the water into account, the difference for Roden remains, as large as before. It is the land, not the shore.

## A land that faced the sea

Why did Roden's stones carry fewer crosses? We do not know. But there is a clue. Roden's stones seldom stand near the old central places, Husby and Tuna, where royal power had its estates – only one in five, against half in the folklands. Perhaps the cross reached Uppland along the roads that ran through the king's estates, and the coastal land, which faced the sea and was governed in its own way, took it up more slowly. It is a thought, not a result.

Whoever rows past Roden's shores sees something other than differences between stones, though: the boats hauled up on land, the mounds on the slope above, the smoke from the farms at the far end of the bays. A land where the water was the road and where people counted in ships.

This is the second part of the series The old lands. The first took us to [Sotholm on the island of Tören]({SOTHOLM}), where the settlements lay in forest clearings and the stones carried crosses but did not pray.

## How we know

The landscape and the life along the coast rest on *Det medeltida Sverige*, the county board's descriptions of the districts and the register of ancient monuments; the names and the graves we have counted from the register and the maps, and the boat landings may be from any period. The ship districts and the trading place are known from the Middle Ages, not from the Viking Age. The crosses we have measured: Roden's runestones were compared with the rest of Uppland's, with time held constant, and the test that the closeness of the sea does not explain the difference was fixed before we counted. The difference holds when the stones are split into two groups parish by parish and when the stones of the main carvers are removed, but not when only stones in their original place are counted, and a large share of Roden's stones stand in Täby, whose place in Roden is itself disputed. The plans and calculations are open on GitHub, linked below.

## Sources

- Dahlbäck, Göran, Jansson, Bengt & Westin, Gunnar T. 1972. *Det medeltida Sverige* 1. Uppland 1. Norra Roden. Royal Swedish Academy of Letters, History and Antiquities. (Quotations translated by us.)
- Janzon, Kaj & Rahmqvist, Sigurd 2002. *Det medeltida Sverige* 2. Södermanland 1. Tören: Svartlösa, Sotholm. Swedish National Heritage Board (the Danish sailing description).
- Larsson, Mats G. 1993. Kung Eriks nyordning. *Uppland* 1993, pp. 105–134. (Quotation translated by us.)
- County Administrative Board of Uppsala 2018. Areas of national interest for cultural heritage: Bygden norr om Hökhuvuds kyrka (C18), Östhammars stad (C19).
- Swedish National Heritage Board, register of ancient monuments (Kulturmiljöregistret), extract 2026.
- Geological Survey of Sweden (SGU), shore-displacement model for AD 1000.
- Scandinavian Runic-text Data Base (Rundata), Department of Scandinavian Languages, Uppsala University. Open Database License.
- Institute for Language and Folklore, place-name register (PlaceNameService), parishes and hundreds. CC BY. Farm names from OpenStreetMap (ODbL).
- The locked analysis plans, the data and Vitki's calculations are open on [GitHub](https://github.com/Precatio/runes) (analysplaner/2026-11-02-roden.md and 2026-11-02-landprofiler.md).
- Image: Wikimedia Commons, with the photographer in the caption."""

for b in (body, body_en):
    assert not re.search(r"^\|", b, re.M), "BlogBody har inga tabeller"
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M)), "varje ruta och diagram ska stängas"
    assert "/karta" not in b and "/statistik" not in b

out = {"slug": "de-gamla-landen-roden", "title": title, "summary": summary, "body": body,
       "title_en": title_en, "summary_en": summary_en, "body_en": body_en,
       "labels": ["Forskning", "Geografi", "Tro och magi", "Formler och syfte"]}
from src import blog_labels  # noqa: E402
assert blog_labels.check(out["labels"]) is None, blog_labels.check(out["labels"])
path = os.path.join(ROOT, "utdata", "blogg", "roden.json")
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
                 "topic": "Geografi|roden", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
