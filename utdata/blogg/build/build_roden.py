"""Artikeln "De gamla landen: Roden – skeppslagens kust med färre kors" (sv + en), del 2 i serien De gamla landen.
Siffrorna låses mot utdata/roden/roden.json (plan analysplaner/2026-11-02-roden.md, sha 59ea6d58),
utdata/landprofiler/landprofiler.json (plan eb59f631) och utdata/gamla_granser/monster.json (plan 054c87d5).
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

# ---- picture and map ----------------------------------------------------------------------------------------------------
F136 = "U 136, Broby bro.jpg"
INFO = commons.commons_info([F136])
assert INFO[F136]["licence"] == "CC BY 2.5" and INFO[F136]["author"] == "Berig"
PAGE = "https://commons.wikimedia.org/wiki/File:" + F136.replace(" ", "_")
MAP = {lang: blog_figures.freeze(open(os.path.join(ROOT, "utdata", "roden", f"karta_roden_{lang}.png"), "rb").read())
       for lang in ("sv", "en")}  # utdata/roden/karta_roden.R
SOTHOLM = "/artiklar/de-gamla-landen-sotholm"

title = "De gamla landen: Roden – skeppslagens kust med färre kors"
summary = ("Upplands kust var på vikingatiden ett eget land, Roden, ordnat i skeppslag i stället för hundaren. Där bär "
           "runstenarna kors på fyra av tio stenar mot sex av tio i resten av Uppland, och det beror inte på närheten "
           "till havet. Andra delen i serien De gamla landen.")

body = f"""Föreställ dig att du ror norrut längs Upplands kust för tusen år sedan. Landet ser inte ut som i dag. Havet går långt in i det, vikarna skär djupt mellan bergen, och det som senare ska bli ådalar är ännu fjärdar där båten kan glida in mellan alarna. Överallt finns uddar och smala näs, holmar och skär. Längst i norr har landet nyss stigit ur havet; där är bygden ung, gårdarna nya, och strandängarna växer ut för varje generation.

Föreställ dig lukten av tång och tjära, ljudet av åror mot tollarna, måsarna över grunden. Gårdarna ligger där en vik möter en dalgång, och deras namn talar om vattnet: något slutar på *-vik*, något på *-näs*. På gravfälten ovanför stränderna ligger högarna tätare än i inlandet, och här och där reser sig en sten ur gräset.

Längre söderut, där kusten bryts upp mot Mälarens mynning, ligger Täby. Här bor en storman, Jarlabanke, som låter resa stenar vid en bro han har byggt och skriva att han ensam äger hela byn:

> *{nz("U 164")}*

Jarlabanke lät resa dessa stenar efter sig själv medan han levde, och gjorde denna bro för sin själ, och han ensam ägde hela Täby. Gud hjälpe hans själ.

I samma bygd reser kvinnor stenar efter dem som aldrig kom hem. Guðlaug efter sin son Holme, som dog i Lombardiet. Åstrid efter sin man Östen:

> *{nz("U 136")}*

Åstrid lät resa dessa stenar efter Östen, sin man, som for till Jerusalem och dog uppe i Grekland.

![Runstenen U 136 vid Broby bro]({INFO[F136]['thumb']})
U 136 vid Broby bro i Täby, rest av Åstrid efter Östen som for till Jerusalem. Foto: Berig, CC BY 2.5, via [Wikimedia Commons]({PAGE}).

## Ett land av skeppslag

Det här är Roden, kustlandet. De tre folklanden – Tiundaland, Attundaland och Fjädrundaland – var indelade i hundaren. Roden var indelat i skeppslag, och det syns i lagen. När Upplandslagen skrevs ner kring år 1300 gick en tvist i folklanden från hundaresting till folklandsting och sist till kungen; i Roden gick den från ett skeppslags ting till två skeppslags ting, därifrån till sex skeppslags ting och sist till kung eller hertig. Också ledungen, skatten till kungens flotta, räknades i Roden efter skeppslagen och inte efter hundarena.

Hur stort Roden var, och om det var ett land för sig eller en del av folklanden, är omstritt. Göran Dahlbäck och Gunnar T. Westin skriver i *Det medeltida Sverige* att ”Frågan om Rodens territoriella omfattning och kamerala och judiciella indelning är omstridd”. I sexårsgärden 1314 står Roden som en rubrik under Tiundaland. Och Jarlabanke själv, vars Täby räknades till Danderyds skeppslag, skrev på en sten vid Vallentuna kyrka att han ”ensam ägde hela detta hundare” – Vallentuna, i Attundaland. Gränsen gick alltså mitt i hans värld.

![Karta över Roden och folklanden omkring år 1000 med runstenarna med och utan kors]({MAP['sv']})
**Karta.** Upplands kust omkring år 1000, då havet gick mycket längre in i landet än i dag. Rostfärgat är Roden, ljust de tre folklanden; gränserna är ungefärliga, dragna efter häradernas socknar. Varje punkt är en runsten där det går att avgöra om den har ett kors. Karta: Vitki, efter SGU:s modell för strandförskjutningen år 1000, Institutet för språk och folkminnens ortnamnsregister och Rundata.

## Det vi har räknat

Här lämnar vi kusten för siffrorna. Roden har {R['desc']['n_roden']} runstenar där vi kan avgöra drag som kors och böner, och {R['desc']['n_tby']} av dem står i Täby. Vi jämförde dem med Upplands övriga stenar, med tiden hållen konstant, för alla drag vi har – och dessutom gravarna i fornlämningsregistret och gårdarnas namn.

Det tydligaste är korset. Fyra av tio stenar i Roden bär ett kors, {pc(K['grund']['share_in'])} procent, mot sex av tio i resten av Uppland, {pc(K['grund']['share_out'])} procent. En bön eller kristen formel står på {C['grund']['k_in']} av {C['grund']['n_in']} stenar, {pc(C['grund']['share_in'])} procent, mot {pc(C['grund']['share_out'])}. Skillnaden håller när vi delar stenarna i två grupper socken för socken och prövar var för sig – syns den i båda grupperna beror den inte på enskilda socknar – och när vi tar bort stenarna av Rodens två flitigaste ristare, Fot och Öpir.

Namnen säger samma sak som landskapet. Gårdsnamn på *-vik* är drygt tre gånger så vanliga i Roden som i resten av Uppland ({str(round(100 * V['n_vik']['share_in'], 1)).replace('.', ',')} mot {str(round(100 * V['n_vik']['share_out'], 1)).replace('.', ',')} procent av namnen), namn på *-näs* mer än dubbelt så vanliga, medan inlandets *-sta* och *-by* är hälften så vanliga eller mindre. På gravfälten är högarna fler än stensättningarna på {pc(G1['share_in'])} procent av dem där båda räknats, mot {pc(G1['share_out'])} procent i resten av Uppland, och resta stenar står på {pc(G2['share_in'])} procent av gravfälten mot {pc(G2['share_out'])}. Allt detta håller också när vi bara jämför inom samma län, så det är inte olika sätt att inventera.

## Var det havet?

Den naturliga invändningen är att det inte är Roden utan kusten: att folk vid vattnet levde annorlunda, oavsett vad deras land hette. Vi prövade det innan vi såg svaret. Med SGU:s modell för strandlinjen år 1000 mätte vi hur långt varje sten stod från vattnet. Rodens stenar står närmare – hälften inom drygt hundra meter från strandlinjen, mot omkring tvåhundrafemtio meter i resten av Uppland. Men i resten av Uppland spelar avståndet till vattnet ingen roll för om en sten har kors. Och när avståndet räknas in i samma modell står skillnaden för Roden kvar, lika stor som förut. Det är landet, inte stranden.

## Det vi inte kan säga

Fyndet håller inte överallt, och vi säger det rakt ut. När vi bara räknar stenar som står kvar på sin ursprungliga plats blir skillnaden i kors för liten för att skilja från slumpen. När vi låter varje ristare ha sin egen vana i modellen gäller samma sak för bönerna. Och när vi prövar Roden mot alla drag på en gång, i den breda jämförelse där vi letade efter allt som skiljer landen åt, räcker korsen inte riktigt till efter korrektionen för det stora antalet prov. I vår smalare plan, där korset var ett av färre drag, håller det. Fyndet är alltså starkt men inte ett av de allra säkraste.

Det finns också något som såg ut som ett fynd men inte är det. Rodens stenar berättar om färder och död långt borta oftare än resten av Upplands: sju av sextio stenar säger att någon dog i fjärran, mot tre procent. Men sex av de sju står i Täby, i Jarlabankes krets. Det är en bygds historia, inte ett lands.

## Ett land som vände sig mot havet

Varför bar Rodens stenar färre kors? Vi vet inte. Men landprofilen ger en ledtråd. Rodens stenar står sällan nära de gamla centralorterna, Husby och Tuna, där kungamakten hade sina gårdar: {pc(CO['share_in'])} procent mot {pc(CO['share_out'])} procent i resten av Uppland. Roden var ordnat efter skeppen och inte efter hundarena, och det hade sin egen väg till kungen. Vår hypotes är att den kristna bildvärlden nådde Uppland längs de vägar som gick genom centralorterna, och att kustlandet, som vände sig mot havet och styrdes på sitt eget sätt, tog till sig den långsammare. Det är en hypotes, inte ett resultat. Den kan prövas: om den stämmer bör stenarna i Roden som står nära en Husby eller Tuna bära kors lika ofta som i folklanden.

Det här är andra delen i serien De gamla landen. Den första handlade om [Sotholm på Södertörn]({SOTHOLM}), där stenarna bar kors men inte bad. I Roden bar de korset mer sällan. Två kuster, två sätt att vara kristen på en sten.

:::box Det viktigaste i korthet
- Roden var Upplands kustland, ordnat i skeppslag i stället för hundaren, med egen väg genom tingen till kungen.
- Där bär runstenarna kors mer sällan än i folklanden, fyra av tio mot sex av tio, och det förklaras inte av närheten till havet.
- Gårdsnamnen på -vik och -näs och gravfälten med högar visar ett land som levde vid och av vattnet.
- Fyndet är starkt men inte orubbligt, och Rodens gränser var omstridda redan på medeltiden.
:::

## Källor

- Dahlbäck, Göran, Jansson, Bengt & Westin, Gunnar T. 1972. *Det medeltida Sverige* 1. Uppland 1. Norra Roden. Kungl. Vitterhets Historie och Antikvitets Akademien.
- Riksantikvarieämbetet, fornlämningsregistret (Kulturmiljöregistret), uttag 2026.
- Sveriges geologiska undersökning (SGU), strandförskjutningsmodell för år 1000.
- Samnordisk runtextdatabas (Rundata), Institutionen för nordiska språk, Uppsala universitet. Open Database License.
- Institutet för språk och folkminnen, ortnamnsregistret (PlaceNameService), socknar och härader. CC BY. Gårdsnamnen ur OpenStreetMap (ODbL).
- De låsta analysplanerna, data och Vitkis beräkningar finns öppet på [GitHub](https://github.com/Precatio/runes) (analysplaner/2026-11-02-roden.md och 2026-11-02-landprofiler.md).
- Bild: Wikimedia Commons, med fotografen i bildtexten."""

title_en = "The old lands: Roden – the coast of the ship districts, with fewer crosses"
summary_en = ("In the Viking Age the coast of Uppland was a land of its own, Roden, organised in ship districts rather than "
              "hundreds. There the runestones carry crosses on four stones in ten, against six in ten in the rest of "
              "Uppland, and it is not down to the closeness of the sea. The second part of the series The old lands.")

body_en = f"""Imagine rowing north along the coast of Uppland a thousand years ago. The land does not look as it does today. The sea reaches far into it, the bays cut deep between the hills, and what will later become river valleys are still inlets where the boat can glide in among the alders. Everywhere there are points and narrow necks of land, islets and skerries. Furthest north the land has only just risen from the sea; there the settlement is young, the farms new, and the shore meadows grow outwards with every generation.

Imagine the smell of seaweed and tar, the sound of oars against the thole-pins, the gulls over the shallows. The farms lie where a bay meets a valley, and their names speak of the water: some end in *-vik*, 'bay', some in *-näs*, 'point'. On the grave fields above the shores the mounds lie thicker than inland, and here and there a stone rises out of the grass.

Further south, where the coast breaks up towards the mouth of Lake Mälaren, lies Täby. A great man lives here, Jarlabanke, who has stones raised at a bridge he has built and has it written that he alone owns the whole village:

> *{nz("U 164")}*

Jarlabanke had these stones raised in memory of himself while alive, and made this bridge for his soul, and he alone owned all of Täby. May God help his soul.

In the same district women raise stones for those who never came home. Guðlaug for her son Holme, who died in Lombardy. Åstrid for her husband Östen:

> *{nz("U 136")}*

Åstrid had these stones raised in memory of Östen, her husband, who went to Jerusalem and died up in Greece.

![The runestone U 136 at Broby bro]({INFO[F136]['thumb']})
U 136 at Broby bro in Täby, raised by Åstrid for Östen who went to Jerusalem. Photo: Berig, CC BY 2.5, via [Wikimedia Commons]({PAGE}).

## A land of ship districts

This is Roden, the coastal land. The three folklands – Tiundaland, Attundaland and Fjädrundaland – were divided into hundreds. Roden was divided into ship districts, *skeppslag*, and it shows in the law. When the Law of Uppland was written down around 1300, a dispute in the folklands went from the hundred's assembly to the folkland's assembly and finally to the king; in Roden it went from the assembly of one ship district to that of two, then to that of six, and finally to king or duke. The levy for the king's fleet, too, was reckoned in Roden by ship districts and not by hundreds.

How large Roden was, and whether it was a land of its own or part of the folklands, is disputed. Göran Dahlbäck and Gunnar T. Westin write in *Det medeltida Sverige* that "the question of Roden's territorial extent and its fiscal and judicial division is disputed". In the six-year tithe of 1314 Roden appears as a heading under Tiundaland. And Jarlabanke himself, whose Täby was counted in the ship district of Danderyd, wrote on a stone at Vallentuna church that he "alone owned all of this hundred" – Vallentuna, in Attundaland. The border ran through the middle of his world.

![Map of Roden and the folklands around AD 1000 with the runestones with and without a cross]({MAP['en']})
**Map.** The coast of Uppland around AD 1000, when the sea reached much further into the land than today. Rust is Roden, light the three folklands; the borders are approximate, drawn after the parishes of the hundreds. Each point is a runestone where it can be told whether it carries a cross. Map: Vitki, after the Geological Survey of Sweden's shore-displacement model for AD 1000, the place-name register of the Institute for Language and Folklore, and Rundata.

## What we have counted

Here we leave the coast for the numbers. Roden has {R['desc']['n_roden']} runestones where we can decide features such as crosses and prayers, and {R['desc']['n_tby']} of them stand in Täby. We compared them with the other stones of Uppland, with time held constant, for every feature we have – and also the graves in the register of ancient monuments and the names of the farms.

The clearest is the cross. Four stones in ten in Roden carry a cross, {pc(K['grund']['share_in'])} percent, against six in ten in the rest of Uppland, {pc(K['grund']['share_out'])} percent. A prayer or Christian formula stands on {C['grund']['k_in']} of {C['grund']['n_in']} stones, {pc(C['grund']['share_in'])} percent, against {pc(C['grund']['share_out'])}. The difference holds when we split the stones into two groups parish by parish and test each – a difference that shows in both groups is not down to particular parishes – and when we remove the stones of Roden's two most prolific carvers, Fot and Öpir.

The names say the same as the landscape. Farm names in *-vik* are more than three times as common in Roden as in the rest of Uppland ({round(100 * V['n_vik']['share_in'], 1)} against {round(100 * V['n_vik']['share_out'], 1)} percent of the names), names in *-näs* more than twice as common, while the inland *-sta* and *-by* are half as common or less. On the grave fields, mounds outnumber stone settings on {pc(G1['share_in'])} percent of those where both have been counted, against {pc(G1['share_out'])} percent in the rest of Uppland, and standing stones occur on {pc(G2['share_in'])} percent of the grave fields against {pc(G2['share_out'])}. All of this also holds when we compare only within the same county, so it is not different ways of surveying.

## Was it the sea?

The natural objection is that it is not Roden but the coast: that people by the water lived differently, whatever their land was called. We tested that before we saw the answer. Using the Geological Survey's model of the shoreline in AD 1000, we measured how far each stone stood from the water. Roden's stones stand closer – half of them within about a hundred metres of the shoreline, against about two hundred and fifty metres in the rest of Uppland. But in the rest of Uppland the distance to the water makes no difference to whether a stone has a cross. And when the distance is put into the same model, the difference for Roden remains, as large as before. It is the land, not the shore.

## What we cannot say

The finding does not hold everywhere, and we say so plainly. When we count only stones still standing in their original place, the difference in crosses becomes too small to tell apart from chance. When we let each carver have their own habit in the model, the same goes for the prayers. And when we test Roden against all features at once, in the broad comparison where we looked for everything that sets the lands apart, the crosses do not quite survive the correction for the large number of tests. In our narrower plan, where the cross was one of fewer features, it holds. The finding is strong, then, but not among the very surest.

There is also something that looked like a finding but is not. Roden's stones tell of journeys and death far away more often than the rest of Uppland's: seven of sixty stones say someone died far off, against three percent. But six of the seven stand in Täby, in Jarlabanke's circle. That is the history of one district, not of a land.

## A land that faced the sea

Why did Roden's stones carry fewer crosses? We do not know. But the land profile gives a clue. Roden's stones seldom stand near the old central places, Husby and Tuna, where royal power had its estates: {pc(CO['share_in'])} percent against {pc(CO['share_out'])} percent in the rest of Uppland. Roden was organised by ships and not by hundreds, and it had its own road to the king. Our hypothesis is that the Christian imagery reached Uppland along the roads that ran through the central places, and that the coastal land, which faced the sea and was governed in its own way, took it up more slowly. It is a hypothesis, not a result. It can be tested: if it is right, the stones in Roden that stand near a Husby or Tuna should carry crosses as often as in the folklands.

This is the second part of the series The old lands. The first was about [Sotholm on Södertörn]({SOTHOLM}), where the stones carried crosses but did not pray. In Roden they carried the cross more rarely. Two coasts, two ways of being Christian on a stone.

:::box The essentials in brief
- Roden was Uppland's coastal land, organised in ship districts instead of hundreds, with its own road through the assemblies to the king.
- There the runestones carry crosses more rarely than in the folklands, four in ten against six in ten, and the closeness of the sea does not explain it.
- The farm names in -vik and -näs and the grave fields with mounds show a land that lived by and from the water.
- The finding is strong but not unshakeable, and Roden's borders were disputed already in the Middle Ages.
:::

## Sources

- Dahlbäck, Göran, Jansson, Bengt & Westin, Gunnar T. 1972. *Det medeltida Sverige* 1. Uppland 1. Norra Roden. Royal Swedish Academy of Letters, History and Antiquities. (Quotations translated by us.)
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
