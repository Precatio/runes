"""Artikeln om gravhögarna (sv + en), med början i Ättekulla i Helsingborg (Viktor 2026-11-18: "Vore kul om vi började vid
Ättekulla i Helsingborg, eftersom jag började där"). Låst plan analysplaner/2026-11-18-hogarna.md (089fcfb5), resultat
utdata/hogar/resultat.json, kartor utdata/hogar/karta_*.py. Registret: /Volumes/2TB/Antigrvity/Runes/downloads/hogar/.
Litteraturen (Rydbeck 1912, Lindqvist 1917) prövas mot tidskrifternas text.
    ../../../.venv/bin/python build_hogar.py [--write | --update DOC]"""
import collections
import csv
import datetime as dt
import importlib.util
import io
import json
import os
import re
import sqlite3
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_figures, blog_labels, nordic  # noqa: E402
from utdata.norge.citat import letters  # noqa: E402

HG = os.path.join(ROOT, "utdata", "hogar")
R = json.load(open(os.path.join(HG, "resultat.json"), encoding="utf-8"))
assert R["sha"] == "089fcfb5"
P = R["prov"]
assert P["H3_runsten"]["haller"] and not P["H1_husby_tuna"]["haller"] and not P["H2_kultplats"]["haller"]
import math  # noqa: E402
OR3 = math.exp(P["H3_runsten"]["stat"])
assert round(OR3, 1) == 3.2 and all(P["H3_runsten"]["halvor"][h]["p"] < 0.01 for h in "AB")
assert P["H1_husby_tuna"]["p_holm"] < 0.001 and P["H1_husby_tuna"]["halvor"]["B"]["p"] > 0.5
assert (R["hogar"], R["stora_20"], R["med_diameter"], R["diam_median"]) == (17531, 2017, 11072, 11.0)

# ---- per province, for the chart and the text (the same layers as the test)
spec = importlib.util.spec_from_file_location("hog", os.path.join(HG, "analys.py"))
A = importlib.util.module_from_spec(spec)
spec.loader.exec_module(A)
import numpy as np  # noqa: E402
from scipy.spatial import cKDTree  # noqa: E402
HROWS = list(csv.DictReader(open("/Volumes/2TB/Antigrvity/Runes/downloads/hogar/hogar.csv", encoding="utf-8")))
PAR = A.asatro.parishes()
pc, pl = [], []
for l_, ps in PAR.items():
    for p in ps:
        pc.append(A.xy(p["latitude"], p["longitude"]))
        pl.append(l_)
ptree = cKDTree(np.array(pc))
RD = json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["inscriptions"]
RS = [A.xy(r["lat"], r["lon"]) for r in RD if nordic.is_runestone(r) and nordic.land_of(r) == "sverige" and r.get("lat")]
rtree = cKDTree(np.array(RS))
TAB = collections.defaultdict(lambda: [0, 0, 0, 0])
for r in HROWS:
    m = A.DIAM.search(re.sub(r"\s+", " ", r["beskrivning"] or ""))
    if not m:
        continue
    d = float(m.group(1).replace(",", "."))
    x, y = float(r["x"]), float(r["y"])
    land = pl[ptree.query([x, y])[1]]
    near = len(rtree.query_ball_point([x, y], 500)) > 0
    TAB[land][(0 if near else 1) if d >= 20 else (2 if near else 3)] += 1
SH = {l_: (100 * a / (a + b), 100 * c / (c + d), a + b) for l_, (a, b, c, d) in TAB.items() if a + b}
assert [round(v) for v in SH["Uppland"][:2]] == [44, 20] and [round(v) for v in SH["Södermanland"][:2]] == [44, 13]
assert [round(v) for v in SH["Medelpad"][:2]] == [24, 7] and [round(v) for v in SH["Västergötland"][:2]] == [8, 3]
assert [round(v) for v in SH["Östergötland"][:2]] == [9, 11]
assert TAB["Skåne"][0] + TAB["Skåne"][2] == 0 and TAB["Halland"][0] + TAB["Halland"][2] == 0

# ---- the register: Ättekulla and the examples
AT = list(csv.DictReader(open("/Volumes/2TB/Antigrvity/Runes/downloads/hogar/attekulla_omgivning.csv", encoding="utf-8")))
gone = lambda r: r["skadestatus"] == "Förstörd" or bool(re.search(r"borttagen", r["beskrivning"] or "", re.I))  # noqa: E731
AT15 = [r for r in AT if r["lamningstyp"] == "Hög" and float(r["dist_m"]) <= 1500]
assert (len(AT15), sum(gone(r) for r in AT15)) == (54, 39)
BYNR = {r["raa_nummer"]: re.sub(r"\s+", " ", r["beskrivning"] or "") for r in AT}
assert "Ursprungligen 25 m i diam och 4 m h. Undersökt av Rolf Petré 1967-1968" in BYNR["Helsingborg 103:1"]
assert "3 skelettgravar med spår av ekkistor" in BYNR["Helsingborg 103:1"] and "bronsdolk i slida (per. III)" in BYNR["Helsingborg 103:1"]
assert "RAÄs karta över Ättekulla området 1957" in BYNR["Helsingborg 131:1"] and "Områdetär nu utfyllt" in BYNR["Helsingborg 131:1"]
assert "Sven Felling och Ster[c]h Odder vara begravd" in BYNR["Helsingborg 91:1"] and "Rannsakningarna 1667 - 68" in BYNR["Helsingborg 91:1"]
assert "Undersöktes och borttogs i samband medbebyggelseplanering 1974" in BYNR["Helsingborg 167:1"]
assert "Hög, 20 m i diam och 3.6 m h" in BYNR["Helsingborg 102:1"] and not gone(next(r for r in AT if r["raa_nummer"] == "Helsingborg 102:1"))
EX = {r["raa_nummer"]: r for r in HROWS}
assert "Hög, 65 m diam och 6-7 m h" in EX["Skalunda 3:1"]["beskrivning"] and "lär en källare ha legat" in EX["Skalunda 3:1"]["beskrivning"]
assert EX["Skalunda 3:1"]["lamningsnamn"] == "Skalunda hög" and EX["Ledberg 5:1"]["lamningsnamn"] == "Ledbergs kulle"
assert EX["Ludgo 62:1"]["lamningsnamn"] == "Tingshögen" and "30 m diam" in EX["Ludgo 62:1"]["beskrivning"]
assert "Träne byhade källare i högen" in re.sub(r"\s+", " ", EX["Träne 46:1"]["tradition"])
assert "guldvagga och därskall ligga en prins begraven" in re.sub(r"\s+", " ", EX["Borrby 18:1"]["tradition"])
N_GONE = sum(1 for r in HROWS if gone(r))
N_GROP = sum(1 for r in HROWS if re.search("grop", r["beskrivning"] or "", re.I))
N_KUNG = sum(1 for r in HROWS if (r["lamningsnamn"] or "").strip() == "Kungshögen")
assert (N_GONE, N_GROP, N_KUNG) == (1323, 5452, 18)
# runestones by the example mounds (500 m)
for nr, signa in (("Skalunda 3:1", {"Vg 44", "Vg 45"}), ("Ledberg 5:1", {"Ög 181"}), ("Ludgo 62:1", {"Sö 137", "Sö 138"})):
    r = EX[nr]
    near = {RDs for RDs, xy in ((rr["signum"], A.xy(rr["lat"], rr["lon"])) for rr in RD if rr["signum"] in signa)
            if ((xy[0] - float(r["x"])) ** 2 + (xy[1] - float(r["y"])) ** 2) ** 0.5 <= 500}
    assert near == signa, (nr, near)

# ---- the streets of Ättekulla (OpenStreetMap, within 1.2 km of the farm; downloads/hogar/gator_attekulla.csv)
GATOR = {r["name"]: int(r["d"]) for r in csv.DictReader(open("/Volumes/2TB/Antigrvity/Runes/downloads/hogar/gator_attekulla.csv", encoding="utf-8"))}
for g in ("Bifrostgatan", "Midgårdsgatan", "Utgårdsgatan", "Runristargatan", "Sven Tveskäggs gata", "Styrbjörn Starkes gata",
          "Erik Rödes gata", "Bronsgatan", "Ättekullagatan"):
    assert GATOR[g] < 1000, g

# ---- the Scanian coastal band (descriptive; distance to today's sea from SGU issjohav_1, code 1, computed by
# utdata/hogar/kust.R into downloads/hogar/hogar_kust.csv; province = nearest ISOF parish, as in analys.py)
KU = list(csv.DictReader(open("/Volumes/2TB/Antigrvity/Runes/downloads/hogar/hogar_kust.csv", encoding="utf-8")))
assert len(KU) == 17531
KBIG = collections.Counter(r["land"] for r in KU if r["big"] == "TRUE")
assert (KBIG["Skåne"], KBIG["Halland"], sum(KBIG.values())) == (1386, 219, 2017)
def _share(land):
    sz = [r for r in KU if r["land"] == land and r["d"] != "NA"]
    return 100 * sum(r["big"] == "TRUE" for r in sz) / len(sz)
assert round(_share("Skåne")) == 46 and round(_share("Uppland")) == 5
import statistics as _st  # noqa: E402
assert _st.median(float(r["d"]) for r in KU if r["land"] == "Skåne" and r["d"] != "NA") == 18
assert _st.median(float(r["d"]) for r in KU if r["land"] == "Uppland" and r["d"] != "NA") == 9
def _near(land, big):
    v = [float(r["sea"]) for r in KU if r["land"] == land and r["d"] != "NA" and (r["big"] == "TRUE") == big]
    return 100 * sum(x <= 3000 for x in v) / len(v)
assert round(_near("Skåne", True)) == 36 and round(_near("Skåne", False)) == 41
GF = collections.Counter(r["province"] for r in csv.DictReader(open(os.path.join(ROOT, "data", "raa", "lamningar.csv"), encoding="utf-8")) if r["type"] == "gravfält")
assert (GF["Uppland"], GF["Skåne"]) == (5307, 359)

# ---- plan 2 (groups as units, 6870d6cd) did NOT hold: the runestone section is removed (Viktor 2026-11-18)
GR = json.load(open(os.path.join(HG, "resultat_grupper.json"), encoding="utf-8"))
assert GR["sha"] == "6870d6cd" and not GR["robust"] and not GR["steg"]["G1"]
# ---- the robustness ladder (plan 2026-11-18-hogarna-trappan, 53f11fa6): every rung must hold
TR = json.load(open(os.path.join(HG, "resultat_trappan.json"), encoding="utf-8"))
assert TR["sha"] == "53f11fa6" and TR["robust"] and all(TR["steg"].values())
assert round(TR["T1"]["or"], 1) == 3.0 and round(TR["T3"]["or"], 1) == 3.1 and TR["T5"]["Uppland"]["or"] > 3
assert TR["tathet_tredjedelar"] == [0.0, 0.0]  # tertiles collapsed: density split none/some (stated in the text)
PL = {k: (100 * v["andel_stora"], 100 * v["andel_mindre"], v["stora"]) for k, v in TR["per_landskap_pa_plats"].items()}
assert [round(v) for v in PL["Uppland"][:2]] == [27, 14] and [round(v) for v in PL["Södermanland"][:2]] == [28, 10]
assert [round(v) for v in PL["Medelpad"][:2]] == [16, 2]
from src import r_bridge  # noqa: E402
_RD = {r["signum"]: r for r in RD}
assert all(r_bridge.is_moved(_RD[s_]) for s_ in ("Vg 44", "Vg 45", "Ög 181"))
assert not any(r_bridge.is_moved(_RD[s_]) for s_ in ("Sö 137", "Sö 138", "Sö 202", "U Fv1975;169"))
assert _RD["U Fv1975;169"]["place"] == "Borresta" and _RD["Sö 202"]["place"] == "Östa"
assert "Tjärkullen" == EX["Orkesta 30:1"]["lamningsnamn"] and "35 m" in EX["Orkesta 30:1"]["beskrivning"]
assert "25 m" in EX["Ytterselö 149:2"]["beskrivning"]

# ---- the runestones that speak of mounds, and our earlier measurements
RDS = {r["signum"]: r for r in RD}
assert "i þæimsi haugi" in RDS["Öl 1"]["normalization"] and RDS["Öl 1"]["dating"] == "V s 900-t"
assert "bro þessa gærðu ok haug þenna" in RDS["U 135"]["normalization"] and RDS["U 135"]["cross_form"] and RDS["U 135"]["style"] == "Pr2"
assert "ræisa stæina ok haug gæra" in RDS["U 269"]["normalization"] and RDS["U 269"]["cross_form"] and RDS["U 269"]["style"] == "Pr4"
assert '"Haugby' in RDS["Ög 82"]["normalization"] and '"Kulhaug(?)' in RDS["Sö 202"]["normalization"]
assert (RDS["U 135"]["place"], RDS["U 269"]["place"]) == ("Broby", "Harby")
FP = open(os.path.join(ROOT, "utdata", "familjens_plats", "resultat.md"), encoding="utf-8").read()
assert "82 % av stenarna i grupp mot 55 %" in FP
KY = open(os.path.join(ROOT, "utdata", "familjens_plats", "kyrkan_resultat.md"), encoding="utf-8").read()
assert "28 vid kyrkan mot 16 på sin plats" in KY and "inget av de fyra testen håller" in KY.lower()
# Snorri (checked 2026-11-18 against is.wikisource Heimskringla/Prologus (úr Frísbók) and heimskringla.no Ynglinga saga
# ch. 8, Linder & Haggson 1869–72): the quoted words below are verbatim from those pages.

# ---- the literature
SOK = sqlite3.connect("/Volumes/2TB/Antigrvity/Runes/downloads/tidskrifter/sok.sqlite")


def jcheck(key, page, *frags):
    text = letters(SOK.execute("select text from pages where key=? and page=?", (key, page)).fetchone()[0])
    for f in frags:
        assert letters(f) in text, (key, page, f)


jcheck("1912_081", 3, "82", "en samling grafhögar från bronsåldern, på en kort sträcka uppgående till ej mindre än fjorton stycken",
       "Flertalet af dem äro belägna på egorna till en gård, hvilken sedan gammalt benämnes Ättekulla",
       "åtta af dessa senare, som genomgräfts af professor Sven Söderberg")
jcheck("1912_081", 11, "90", "elfva grafvar från äldre bronsåldern", "svara femtiotre från yngre",
       "endast de förnämligare hade råd att bestå sina anhöriga ett så kostsamt eftermäle som en kista af sten eller trä med dyrbar utrustning i en svåruppförd grafhög")
jcheck("1912_081", 12, "91", "Här jordades san", "nolikt rika och fattiga om hvarandra")
jcheck("1912_081", 10, "89", "man fort", "farande ville använda dem som begrafningsplats", "påfylla ett nytt jordlager")
jcheck("1917_127", 17, "142", "kung Nordians hög", "vid Ås-Husby", "Björn Järnsidas hög", "Husby på Munsön")
jcheck("1912_081", 3, "82", "man fortsatt med grafsättningar i närheten af högarne")
jcheck("1912_081", 4, "83", "högarne blifvit öfverfyllda och seden att uppföra sådana föråldrats",
       "bruket att nedsätta grafurnorna under flat mark, utan täckande hög")
jcheck("1912_081", 23, "102", "Bronsåldersfolkets", "grafhög motsvaras längre fram af de kristnas")

# ---- pictures
from PIL import Image  # noqa: E402


def frozen(path):
    buf = io.BytesIO()
    Image.open(path).convert("RGB").save(buf, "PNG", optimize=True)
    return blog_figures.freeze(buf.getvalue())


FIG = {(k, l_): frozen(os.path.join(HG, f"karta_{k}_{l_}.png")) for k in ("attekulla", "sverige") for l_ in ("sv", "en")}
IMG_AT = {"sv": f"![Karta: gravhögarna kring Ättekulla i Helsingborg]({FIG['attekulla', 'sv']})\nBild: Vitki. Högarna inom en och en halv kilometer från Ättekulla gård enligt Riksantikvarieämbetets register: röda finns kvar, vita är borttagna eller förstörda.",
          "en": f"![Map: the burial mounds around Ättekulla in Helsingborg]({FIG['attekulla', 'en']})\nImage: Vitki. The mounds within one and a half kilometres of Ättekulla farm according to the Swedish National Heritage Board's register: red are still there, white have been removed or destroyed."}
IMG_SE = {"sv": f"![Karta: Sveriges fristående gravhögar]({FIG['sverige', 'sv']})\nBild: Vitki. De fristående gravhögarna i registret, de minst 20 meter breda i rött. Högarna i gravfälten är inte med.",
          "en": f"![Map: Sweden's free-standing burial mounds]({FIG['sverige', 'en']})\nImage: Vitki. The free-standing burial mounds in the register, those at least 20 metres across in red. The mounds inside grave fields are not included."}


def chart(sv):
    rows = ["Uppland", "Södermanland", "Medelpad", "Västergötland", "Östergötland"]
    out = [":::chart " + ("Gravhögar med en runsten på sin plats inom 500 meter" if sv else "Burial mounds with a runestone in its original place within 500 metres")]
    for k in rows:
        b, s_, n = PL[k]
        out.append("# " + k)
        out.append(f"+{'Stor hög, minst 20 m' if sv else 'Large mound, at least 20 m'} | {b:.0f} | {n} {'högar' if sv else 'mounds'}")
        out.append(f"{'Mindre hög' if sv else 'Smaller mound'} | {s_:.0f} |")
    out.append(("Källa: Riksantikvarieämbetet, Kulturmiljöregistret; Samnordisk runtextdatabas (stenar som står där de restes). Procent. Bild: Vitki.") if sv else
               ("Source: Swedish National Heritage Board, Kulturmiljöregistret; Scandinavian Runic-text Database (stones standing where they were raised). Per cent. Image: Vitki."))
    out.append(":::")
    return "\n".join(out)


p0 = lambda v: f"{v:.0f}"  # noqa: E731
SLUG = "kullarna-vid-skogens-rand"
title = "Kullarna vid skogens rand – från Ättekulla till Sveriges största gravhögar"
title_en = "The mounds at the edge of the forest – from Ättekulla to Sweden's largest burial mounds"
seo_title = "Gravhögar i Sverige: vilka låg i kullarna?"
seo_title_en = "Burial mounds in Sweden: who lay in them?"
summary = ("Jag växte upp i Ättekulla i Helsingborg, bland gator med fornnordiska namn. Vid skogens rand låg kullarna: "
           "bronsåldersgravar som användes i nästan tusen år. De flesta är borta i dag. Vi följer högarna därifrån över hela landet – "
           "76 000 i registret – och in i vikingatiden, då de redan var forntid.")
summary_en = ("I grew up at Ättekulla in Helsingborg, among streets with Old Norse names. At the edge of the forest lay the mounds: "
              "Bronze Age graves used for almost a thousand years. Most are gone today. We follow the mounds from there across the whole "
              "country – 76,000 in the register – and into the Viking Age, when they were already the ancient past.")

body = f"""Den här artikeln börjar inte med en runsten, utan med platsen där jag växte upp: ett område i Helsingborg som heter Ättekulla. Gatorna där har fornnordiskt inspirerade namn – Bifrostgatan, Midgårdsgatan, Utgårdsgatan, Runristargatan, Sven Tveskäggs gata, Styrbjörn Starkes gata, Erik Rödes gata. Och vid skogens rand låg kullarna.

I [Korpen som heter Minne](/artiklar/korpen-som-heter-minne/) har jag berättat om boken *Gudar och hjältar i nordisk mytologi*, som jag läste många gånger under mina unga år. Där fanns Tor hos Utgårdaloke. I Ättekulla var Utgård också en gata.

Vilka var kullarna, och vilka låg i dem? Gatunamnen pekar mot vikingatiden, mot kungar och sjöfarare som Sven Tveskägg och Erik Röde. Det ska visa sig att de pekar fel, med ett möjligt undantag: Bronsgatan. Namnet på själva platsen visste bättre. En *ättehög* är släktens hög, där ätten låg, och Riksantikvarieämbetets register har namnet Ättekulla eller något liknande på 97 platser i över femtio socknar.

## Vilka låg i kullarna?

Arkeologen Otto Rydbeck skrev om just dessa högar i Fornvännen 1912: ”en samling grafhögar från bronsåldern, på en kort sträcka uppgående till ej mindre än fjorton stycken. Flertalet af dem äro belägna på egorna till en gård, hvilken sedan gammalt benämnes Ättekulla” (s. 82). Professor Sven Söderberg hade grävt ut åtta av dem på 1870- och 1880-talen.

Söderberg fann elva gravar från den äldre bronsåldern – skelettgravar i kistor av sten eller trä – och femtiotre från den yngre, då de brända benen grävdes ned i högarna som redan stod där. Rydbeck förklarade skillnaden: i början var det bara ”de förnämligare” som ”hade råd att bestå sina anhöriga ett så kostsamt eftermäle som en kista af sten eller trä med dyrbar utrustning i en svåruppförd grafhög” (s. 90). Senare ”jordades sannolikt rika och fattiga om hvarandra” (s. 91).

Kullarna i Ättekulla var alltså inte vikingarnas. De var mer än tusen år äldre och användes i nästan tusen år. Namnet hade rätt, och av gatorna träffade bara Bronsgatan rätt tid.

Den största högen undersöktes på nytt av Rolf Petré 1967–68. Den hade varit 25 meter bred och fyra meter hög, och i centralgraven låg en bronsdolk i sin slida, från bronsålderns tredje period. Sedan togs högen bort.

## Det som försvann

{IMG_AT['sv']}

Inom en och en halv kilometer från Ättekulla gård har registret 54 högar. 39 av dem är borttagna eller förstörda. Om en av platserna står det i dag bara: ”Området är nu utfyllt.”

Men minnet var långt. I Rannsakningarna 1667–68, rikets första stora inventering av fornminnen, berättade de äldsta i Raus att ett slag hade stått där, ”men mellan vem vet de icke”, och att sagohjältarna Sven Fælding och Starkodder låg begravda i högarna.

Raus är ett namn jag bär med mig. I mitt pass står det som min födelseort, och förr tror jag att det stod Raus församling. Jag har inte så mycket relation till platsen i dag, men den kommer alltid att följa med mig. Den är en del av min historia.

## 76 000 kullar

Ättekulla är inget undantag. Registret har 17 531 fristående gravhögar och omkring 58 000 till i gravfälten. Den typiska fristående högen är elva meter bred; {R['stora_20']:,} är minst 20 meter.

{IMG_SE['sv']}

Det som slår en först är det röda bandet längs Skånes och Hallands kuster, med Ättekulla mitt i. Där ligger fyra av fem av landets stora högar. I Skåne är nästan varannan hög med känd storlek minst 20 meter bred, i Uppland var tjugonde. Det är bronsålderns stora högar, och de ligger inte närmare havet än de små: det är bygden, de öppna slätterna, som ligger vid kusten. Längre norrut är högarna oftare från järnåldern och ligger mest i gravfält, som inte syns på kartan. Uppland har 5 307 gravfält i registret, Skåne 359.

Högarna har haft ett hårt liv. {N_GONE:,} står som borttagna eller förstörda, och i {N_GROP:,} beskrivningar, nästan var tredje, nämns en grop där någon har grävt. Berättelserna har följt dem: {N_KUNG} högar heter Kungshögen, och i Stora Fulhög i Borrby ska det finnas ”en guldvagga”.

## Redan gamla för vikingarna

När vikingarna levde var kullarna i Ättekulla redan mellan 1 500 och 2 500 år gamla. Hur såg man på högarna då? Runstenarna ger glimtar. På Karlevistenen på Öland, Öl 1, från slutet av 900-talet, ligger en hövding dold ”i þæimsi haugi”, i denna hög. Vid Broby i Täby lät tre bröder resa stenar efter sin far ”ok bro þessa gærðu ok haug þenna”, och gjorde denna bro och denna hög (U 135). Vid Harby i Fresta lät Illugi ”ræisa stæina ok haug gæra”, resa stenarna och göra en hög, efter sin bror (U 269).

Ett par hundra år senare skrev islänningen Snorre Sturlasson ned hur man mindes de gamla gravskicken. Först kom brandåldern, *brunaöld*, då man brände de döda och reste bautastenar efter dem. Men sedan Frö hade lagts i hög i Uppsala ”gerðu margir höfðingjar eigi síður hauga en bautasteina til minningar um frændur sína” – byggde många hövdingar högar lika väl som bautastenar till minne av sina fränder. I Ynglingasagan låter han Oden själv stifta regeln: hög åt de förnäma, ”eptir göfga menn skyldi haug gera til minningar”, och stenar åt de andra.

Snorre var en kristen lärd som såg tillbaka, inte ett ögonvittne. Men i hans bild hör högen och stenen ihop, som två sätt att minnas de döda.

## Det som inte höll

Sune Lindqvist skrev 1917 att storhögarna ligger vid husbyarna, kungens gårdar: ”kung Nordians hög” vid Ås-Husby, ”Björn Järnsidas hög” vid Husby på Munsön (Fornvännen 12, s. 142). För hela landet håller det inte: mönstret syns bara i den ena halvan av materialet och vänder när gränsen för en stor hög sätts vid 15 meter. Inte heller låg de stora högarna närmare de gamla kultplatserna.

## Från högen till kyrkogården

Begravde man fortsatt så? Man slutade aldrig riktigt bygga högar, men seden ändrades gång på gång.

Redan i Ättekulla syns skiftena. När ”högarne blifvit öfverfyllda och seden att uppföra sådana föråldrats”, skriver Rydbeck, började man sätta ned gravurnorna ”under flat mark, utan täckande hög” – men fortfarande nära högarna (s. 82–83). Under järnåldern kom högarna tillbaka, nu oftast små och samlade i gravfält, och under vikingatiden lades de döda fortfarande i högar.

Sedan kom kyrkan. Stenarna vid Broby och Harby bär kors, och ändå gjordes en hög vid dem – Broby-stenen omkring 1020–1050, Harby-stenen omkring 1070–1100. Men de döda började begravas obrända, på kyrkogården. Rydbeck såg sambandet redan 1912: ”Bronsåldersfolkets grafhög motsvaras längre fram af de kristnas kyrkogård” (s. 102). Skiftet gick inte på en dag. När vi tidigare prövade om de senare runstenarna lämnade gravfälten för kyrkorna pekade siffrorna åt det hållet utan att räcka hela vägen; bara de allra sista stenarna, från omkring 1100–1130, står tydligt oftare vid kyrkan.

Varför ändrades det? Det har vi inte prövat. Men Snorre ger en ledtråd: var och en skulle komma till Valhall med det som brändes med honom, ”með þvílíkum auðœfum skyldi hverr koma til Valhallar, sem hann hafði á bál”. Graven hörde ihop med föreställningen om vart de döda tog vägen. När föreställningen byttes, byttes graven.

## Tillbaka vid skogens rand

Så vilka var kullarna vid skogens rand? De var bronsålderns släktgravar, först för de förnämsta och sedan för många, i nästan tusen år. För vikingarna var de redan forntid, och ibland gjorde de efterlevande en ny hög vid sin runsten. Sedan flyttade de döda in på kyrkogården, och högarna blev platser för sägner, för skattgrävare och till sist för en växande stad.

Gatunamnen i Ättekulla pekade mot vikingatiden, och de pekade fel. Men kanske inte helt. Vikingarna levde, precis som jag, bland högar som redan var gamla, och de hade sina egna berättelser om vilka som låg där.

I Grímnismál säger Oden att han fruktar för korpen Hugin, tanken, men ännu mer för Munin, minnet. Av kullarna runt Ättekulla gård är de flesta borta. Men namnen blev kvar: Ättekulla på gatuskyltarna, Raus i mitt pass. Där klarade sig minnet bättre än kullarna.

:::box Det viktigaste i korthet
- Kullarna i Ättekulla var bronsåldersgravar, använda i nästan tusen år. 39 av 54 högar runt gården är borta i dag.
- Fyra av fem av Sveriges stora gravhögar ligger i Skåne och Halland: bronsålderns högar på kustslätterna.
- Högarna var forntid redan för vikingarna, och ännu vid kristna stenar gjordes en hög. Sedan flyttade de döda långsamt till kyrkogården.
- Lindqvists tanke att storhögarna hör till husbyarna går inte att bekräfta för hela landet.
:::

## Så säkra är vi

Registret anger sällan när en hög byggdes, så stora och små högar kan vara från olika tider. Högens storlek är läst ur beskrivningen, som för 11 072 fristående högar anger en diameter; registret skriver oftast ”20 m i diam”, och den formen lade vi till innan proven räknades. Planerna och koden ligger öppet på GitHub.

*Rättad 18 november 2026: ett avsnitt om att runstenarna sökte sig till de stora högarna är struket. Räknat hög för hög såg sambandet starkt ut, men högar ligger ofta i grupper som delar samma runsten. När grupperna räknades som en enhet, enligt en plan som låstes innan vi räknade, höll mönstret inte.*

## Källor

- Riksantikvarieämbetet, Kulturmiljöregistret: lämningstypen Hög och högarna i gravfälten, uttag 2 november 2026. Beskrivningarna och sägnerna citeras kort.
- Samnordisk runtextdatabas (Rundata), Uppsala universitet. Open Database License.
- Gatunamnen: © OpenStreetMaps bidragsgivare, Open Database License.
- Rydbeck, Otto 1912. Undersökning af bronsåldershögar i Köpinge, nära Ramlösa hälsobrunn i Skåne. *Fornvännen* 7, s. 81–132. CC BY 4.0.
- Lindqvist, Sune 1917. Ottarshögen i Vendel. *Fornvännen* 12, s. 127–143. CC BY 4.0.
- Snorre Sturlasson, *Heimskringla*: förordet efter Frísbók (isländska Wikisource) och Ynglingasagan kap. 8 efter N. Linder och H. A. Haggsons utgåva 1869–72 (heimskringla.no). Korta citat.
- Vitkis tidigare mätning: Tog kyrkan över efter gravfältet?, analysplan 2026-10-29 på GitHub.
- Analysplanerna och koden: [Kullarna](https://github.com/Precatio/runes/blob/main/analysplaner/2026-11-18-hogarna.md) , [trappan](https://github.com/Precatio/runes/blob/main/analysplaner/2026-11-18-hogarna-trappan.md) och [grupperna](https://github.com/Precatio/runes/blob/main/analysplaner/2026-11-18-hogarna-grupper.md) på GitHub."""

body_en = f"""This article does not begin with a runestone, but with the place where I grew up: a part of Helsingborg called Ättekulla. Its streets have Old Norse-inspired names – Bifrostgatan, Midgårdsgatan, Utgårdsgatan, Runristargatan (Rune Carvers' Street), Sven Tveskäggs gata, Styrbjörn Starkes gata, Erik Rödes gata. And at the edge of the forest lay the mounds.

In [The raven called Memory](/en/artiklar/korpen-som-heter-minne/) I have told of Brian Branston's *Gods and Heroes from Viking Mythology*, which I read again and again in my young years. Thor's visit to Utgarda-Loki was in it. At Ättekulla, Utgård was also a street.

Who were the mounds, and who lay in them? The street names point to the Viking Age, to kings and seafarers such as Sweyn Forkbeard and Erik the Red. They will turn out to point the wrong way, with one possible exception: Bronsgatan, Bronze Street. The name of the place itself knew better. An *ättehög* is the family's mound, where the kin lay, and the Swedish National Heritage Board's register has the name Ättekulla or something like it at 97 places in more than fifty parishes.

## Who lay in the mounds?

The archaeologist Otto Rydbeck wrote about these very mounds in Fornvännen in 1912: ”a group of Bronze Age burial mounds, on a short stretch numbering no fewer than fourteen. Most of them lie on the land of a farm that has long been called Ättekulla” (p. 82). Professor Sven Söderberg had dug eight of them in the 1870s and 1880s.

Söderberg found eleven graves from the earlier Bronze Age – inhumations in coffins of stone or wood – and fifty-three from the later, when the burnt bones were dug down into the mounds that already stood there. Rydbeck explained the difference: at first only ”the more distinguished” could ”afford to give their kin so costly a memorial as a coffin of stone or wood with precious equipment in a laboriously built burial mound” (p. 90). Later ”rich and poor were probably buried side by side” (p. 91).

So the mounds at Ättekulla were not the Vikings'. They were more than a thousand years older and were used for almost a thousand years. The name was right, and of the streets only Bronsgatan hit the right age.

The largest mound was examined again by Rolf Petré in 1967–68. It had been 25 metres across and four metres high, and in the central grave lay a bronze dagger in its sheath, from the third period of the Bronze Age. Then the mound was removed.

## What disappeared

{IMG_AT['en']}

Within one and a half kilometres of Ättekulla farm the register has 54 mounds. 39 of them have been removed or destroyed. Of one of the places the register now says only: ”The area is now filled in.”

But the memory was long. In the Rannsakningar of 1667–68, the kingdom's first great survey of ancient monuments, the oldest people in Raus said that a battle had been fought there, ”but between whom they do not know”, and that the saga heroes Sven Fælding and Starkodder lay buried in the mounds.

Raus is a name I carry with me. My passport gives it as my place of birth, and I think it used to say Raus parish. I do not have much of a relationship with the place today, but it will always come with me. It is part of my story.

## 76,000 mounds

Ättekulla is no exception. The register has 17,531 free-standing burial mounds and about another 58,000 inside the grave fields. The typical free-standing mound is eleven metres across; {R['stora_20']:,} are at least 20 metres.

{IMG_SE['en']}

What strikes one first is the red band along the coasts of Skåne and Halland, with Ättekulla in the middle of it. Four in five of the country's large mounds lie there. In Skåne almost every other mound of known size is at least 20 metres across, in Uppland one in twenty. These are the great mounds of the Bronze Age, and they lie no closer to the sea than the small ones: it is the settled land, the open plains, that lies along the coast. Further north the mounds are more often from the Iron Age and lie mostly in grave fields, which do not show on the map. Uppland has 5,307 grave fields in the register, Skåne 359.

The mounds have had a hard life. {N_GONE:,} are listed as removed or destroyed, and {N_GROP:,} descriptions, almost one in three, mention a pit where someone has dug. Stories have followed them: {N_KUNG} mounds are called Kungshögen, the king's mound, and in Stora Fulhög at Borrby there is said to be ”a golden cradle”.

## Already old to the Vikings

When the Vikings lived, the mounds at Ättekulla were already between 1,500 and 2,500 years old. How did people see the mounds then? The runestones give glimpses. On the Karlevi stone on Öland, Öl 1, from the late 900s, a chieftain lies hidden ”i þæimsi haugi”, in this mound. At Broby in Täby three brothers raised stones for their father ”ok bro þessa gærðu ok haug þenna”, and made this bridge and this mound (U 135). At Harby in Fresta Illugi had them ”ræisa stæina ok haug gæra”, raise the stones and make a mound, for his brother (U 269).

A couple of centuries later the Icelander Snorri Sturluson wrote down how the old burial customs were remembered. First came the age of burning, *brunaöld*, when the dead were burned and standing stones raised after them. But after Freyr had been laid in a mound at Uppsala ”gerðu margir höfðingjar eigi síður hauga en bautasteina til minningar um frændur sína” – many chieftains built mounds no less than standing stones in memory of their kinsmen. In Ynglinga saga he has Odin himself lay down the rule: a mound for the noble, ”eptir göfga menn skyldi haug gera til minningar”, and stones for the others.

Snorri was a Christian scholar looking back, not an eyewitness. But in his picture the mound and the stone belong together, as two ways of remembering the dead.

## What did not hold

Sune Lindqvist wrote in 1917 that the great mounds lie by the husbyar, the king's farms: ”King Nordian's mound” at Ås-Husby, ”Björn Ironside's mound” at Husby on Munsön (Fornvännen 12, p. 142). For the whole country it does not hold: the pattern shows only in one half of the material and reverses when the limit for a large mound is set at 15 metres. Nor did the large mounds lie closer to the old cult places.

## From the mound to the churchyard

Did people go on burying that way? They never quite stopped building mounds, but the custom changed again and again.

The shifts can be seen already at Ättekulla. When ”the mounds had become over-filled and the custom of raising them had grown old-fashioned”, Rydbeck writes, people began to set down the burial urns ”under flat ground, without a covering mound” – but still close to the mounds (pp. 82–83). In the Iron Age the mounds came back, now mostly small and gathered in grave fields, and in the Viking Age the dead were still laid in mounds.

Then came the church. The stones at Broby and Harby bear crosses, and yet a mound was made beside them – the Broby stone about 1020–1050, the Harby stone about 1070–1100. But the dead began to be buried unburnt, in the churchyard. Rydbeck saw the link as early as 1912: ”The Bronze Age people's burial mound corresponds later to the Christians' churchyard” (p. 102). The shift did not happen in a day. When we earlier tested whether the later runestones left the grave fields for the churches, the numbers pointed that way without going the whole distance; only the very last stones, from about 1100–1130, clearly stand more often by the church.

Why did it change? We have not tested that. But Snorri gives a clue: everyone would come to Valhalla with what was burned with him, ”með þvílíkum auðœfum skyldi hverr koma til Valhallar, sem hann hafði á bál”. The grave belonged with the idea of where the dead went. When the idea changed, the grave changed.

## Back at the edge of the forest

So who were the mounds at the edge of the forest? They were the graves of Bronze Age families, first for the most distinguished and then for many, for almost a thousand years. To the Vikings they were already the ancient past, and sometimes the survivors made a new mound by their runestone. Then the dead moved into the churchyard, and the mounds became places for legends, for treasure-hunters and at last for a growing town.

The street names at Ättekulla pointed to the Viking Age, and they pointed the wrong way. But perhaps not entirely. The Vikings lived, just as I did, among mounds that were already old, and they had their own stories of who lay there.

In Grímnismál Odin says that he fears for the raven Huginn, thought, but even more for Muninn, memory. Of the mounds around Ättekulla farm most are gone. But the names remained: Ättekulla on the street signs, Raus in my passport. There memory fared better than the mounds.

:::box The essentials in brief
- The mounds at Ättekulla were Bronze Age graves, used for almost a thousand years. 39 of the 54 mounds around the farm are gone today.
- Four in five of Sweden's large burial mounds lie in Skåne and Halland: the Bronze Age mounds of the coastal plains.
- The mounds were the ancient past already to the Vikings, and even beside Christian stones a mound was made. Then the dead moved slowly to the churchyard.
- Lindqvist's idea that the great mounds belong to the husbyar cannot be confirmed for the whole country.
:::

## How sure we are

The register seldom says when a mound was built, so large and small mounds may be from different times. The mound's size is read from the description, which gives a diameter for 11,072 free-standing mounds; the register usually writes ”20 m i diam”, and we added that form before the tests were run. The plans and the code are open on GitHub.

*Corrected 18 November 2026: a section saying that the runestones sought out the large mounds has been removed. Counted mound by mound the link looked strong, but mounds often lie in groups that share the same runestone. When the groups were counted as one unit, under a plan locked before we counted, the pattern did not hold.*

## Sources

- Swedish National Heritage Board, Kulturmiljöregistret: the type Hög and the mounds in the grave fields, extract of 2 November 2026. The descriptions and legends are quoted briefly.
- Scandinavian Runic-text Database (Rundata), Uppsala University. Open Database License.
- Street names: © OpenStreetMap contributors, Open Database License.
- Rydbeck, Otto 1912. Undersökning af bronsåldershögar i Köpinge, nära Ramlösa hälsobrunn i Skåne. *Fornvännen* 7, pp. 81–132. CC BY 4.0.
- Lindqvist, Sune 1917. Ottarshögen i Vendel. *Fornvännen* 12, pp. 127–143. CC BY 4.0.
- Snorri Sturluson, *Heimskringla*: the prologue after Frísbók (Icelandic Wikisource) and Ynglinga saga ch. 8 after N. Linder and H. A. Haggson's edition 1869–72 (heimskringla.no). Short quotations.
- Vitki's earlier measurement: Did the church take over from the grave field?, analysis plan of 2026-10-29 on GitHub.
- The analysis plans and the code: [the mounds](https://github.com/Precatio/runes/blob/main/analysplaner/2026-11-18-hogarna.md) , [the ladder](https://github.com/Precatio/runes/blob/main/analysplaner/2026-11-18-hogarna-trappan.md) and [the groups](https://github.com/Precatio/runes/blob/main/analysplaner/2026-11-18-hogarna-grupper.md) on GitHub."""

body = body.replace(f"{R['stora_20']:,}", f"{R['stora_20']:,}".replace(",", " ")).replace(f"{N_GONE:,}", f"{N_GONE:,}".replace(",", " ")).replace(f"{N_GROP:,}", f"{N_GROP:,}".replace(",", " "))
for b, lang in ((body, "sv"), (body_en, "en")):
    assert not re.search(r"^\|", b, re.M)
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M))
    assert "{" not in b and "}" not in b
    assert ("Det viktigaste i korthet" if lang == "sv" else "The essentials in brief") in b
    imgs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", b)
    assert len(imgs) == 2 and all(re.match(r"/api/blog/figures/[0-9a-f]{16}\.png$", u) for u in imgs), imgs
    assert not re.search(r"\bAI\b", b)
    assert "personen bakom Vitki" not in b and "person behind Vitki" not in b
labels = ["Forskning", "Geografi"]
assert blog_labels.check(labels) is None
assert len(seo_title) <= 52 and len(seo_title_en) <= 52
out = {"slug": SLUG, "title": title, "summary": summary, "body": body, "title_en": title_en, "summary_en": summary_en,
       "body_en": body_en, "seo_title": seo_title, "seo_title_en": seo_title_en, "labels": labels}
json.dump(out, open(os.path.join(ROOT, "utdata", "blogg", "hogar.json"), "w"), ensure_ascii=False, indent=1)
print(len(body.split()), "ord,", len(body_en.split()), "words")

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
        assert not [p for p in blog._all() if p.get("slug") == out["slug"]], "Adressen används redan"
        ref = col.document()
        ref.set({**out, "published": False, "month": now.strftime("%Y-%m"), "author": "Viktor Kvant",
                 "topic": "Forskning|gravhögar", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
