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
    rows = [("Uppland", "Uppland"), ("Södermanland", "Södermanland"), ("Medelpad", "Medelpad"), ("Västergötland", "Västergötland"),
            ("Östergötland", "Östergötland")]
    out = [":::chart " + ("Gravhögar med en runsten inom 500 meter" if sv else "Burial mounds with a runestone within 500 metres")]
    for k, en in rows:
        b, s, n = SH[k]
        f = (lambda v: f"{v:.0f}")
        out.append("# " + (k if sv else en))
        out.append(f"+{'Stor hög, minst 20 m' if sv else 'Large mound, at least 20 m'} | {f(b)} | {n} {'högar' if sv else 'mounds'}")
        out.append(f"{'Mindre hög' if sv else 'Smaller mound'} | {f(s)} |")
    out.append(("Källa: Riksantikvarieämbetet, Kulturmiljöregistret; Samnordisk runtextdatabas. Procent. Bild: Vitki.") if sv else
               ("Source: Swedish National Heritage Board, Kulturmiljöregistret; Scandinavian Runic-text Database. Per cent. Image: Vitki."))
    out.append(":::")
    return "\n".join(out)


p0 = lambda v: f"{v:.0f}"  # noqa: E731
SLUG = "kullarna-vid-skogens-rand"
title = "Kullarna vid skogens rand – från Ättekulla till Sveriges största gravhögar"
title_en = "The mounds at the edge of the forest – from Ättekulla to Sweden's largest burial mounds"
seo_title = "Gravhögar i Sverige: från bronsålder till runstenar"
seo_title_en = "Burial mounds in Sweden: who lay in them?"
summary = ("Jag växte upp i Ättekulla i Helsingborg, bland gator med fornnordiska namn. Vid skogens rand låg kullarna: "
           "bronsåldersgravar som användes i tusen år. De flesta är borta i dag. Vi följer högarna därifrån över hela landet – 76 000 i registret – och finner att vikingatidens "
           "runstenar sökte sig till de stora högarna: i Uppland och Södermanland står det en runsten vid var femte vanlig "
           "hög men vid nästan varannan stor.")
summary_en = ("I grew up at Ättekulla in Helsingborg, among streets with Old Norse names. At the edge of the forest lay the mounds: "
              "Bronze Age graves used for a thousand years. Most are gone today. We follow the mounds from there across the whole country – 76,000 in the register – and "
              "find that the Viking Age runestones sought out the large mounds: in Uppland and Södermanland a runestone stands "
              "by one ordinary mound in five but by almost every other large one.")

body = f"""Den här artikeln börjar inte med en runsten, utan med platsen där jag växte upp: ett område i Helsingborg som heter Ättekulla. Gatorna där har fornnordiskt inspirerade namn – Bifrostgatan, Midgårdsgatan, Utgårdsgatan, Runristargatan, Sven Tveskäggs gata, Styrbjörn Starkes gata, Erik Rödes gata. Och vid skogens rand låg kullarna.

I [Korpen som heter Minne](/artiklar/korpen-som-heter-minne/) har jag berättat om boken *Gudar och hjältar i nordisk mytologi*, som jag läste många gånger under mina unga år. Där fanns Tor hos Utgårdaloke. I Ättekulla var Utgård också en gata.

Det var där jag började, och därför börjar artikeln där. Vilka var kullarna, och vilka låg i dem? Gatunamnen pekar mot vikingatiden, mot kungar och sjöfarare som Sven Tveskägg och Erik Röde. Det ska visa sig att de pekar fel, med ett möjligt undantag: Bronsgatan. Från Ättekulla följer vi sedan kullarna ut över landet, och tillbaka in i vikingatiden.

Själva namnet berättade mer än gatorna. En *ättehög* är ett gammalt ord för en gravhög: släktens hög, där ätten låg. Riksantikvarieämbetets register har namnet Ättekulla, eller något liknande, på 97 platser i över femtio socknar. Det var bygdens eget ord för gravarna.

## Vilka låg i kullarna?

Arkeologen Otto Rydbeck skrev om just dessa högar i Fornvännen 1912. Vid vägen från Ramlösa hälsobrunn till Raus låg ”en samling grafhögar från bronsåldern, på en kort sträcka uppgående till ej mindre än fjorton stycken. Flertalet af dem äro belägna på egorna till en gård, hvilken sedan gammalt benämnes Ättekulla” (s. 82). Åtta av dem hade grävts ut av professor Sven Söderberg på 1870- och 1880-talen.

I de åtta högarna fann Söderberg elva gravar från den äldre bronsåldern – skelettgravar, i kistor av sten eller trä – och femtiotre från den yngre, där de brända benen hade grävts ned i högarna som redan stod där. Man fyllde på med ny jord för att inte störa de gamla gravarna, och högarna växte (s. 89–90). Rydbeck förklarade skillnaden så: i början var det bara ”de förnämligare” som ”hade råd att bestå sina anhöriga ett så kostsamt eftermäle som en kista af sten eller trä med dyrbar utrustning i en svåruppförd grafhög” (s. 90). Senare ”jordades sannolikt rika och fattiga om hvarandra” (s. 91).

Kullarna i Ättekulla var alltså inte vikingarnas. De var mer än tusen år äldre, och de användes i nästan tusen år. Namnet hade rätt: det var släktens högar. Av gatorna var det bara Bronsgatan som träffade rätt tid.

Den största undersöktes på nytt av Rolf Petré 1967–68. Den hade varit 25 meter bred och fyra meter hög, byggd av torv runt ett röse av sten. I mitten låg tre skelettgravar med spår av ekkistor, och i centralgraven en bronsdolk i sin slida, från bronsålderns tredje period. Sedan togs högen bort.

## Det som försvann

{IMG_AT['sv']}

Inom en och en halv kilometer från Ättekulla gård har registret 54 högar. 39 av dem är borttagna eller förstörda. 1957 ritade G. A. Hellman in högarna på Riksantikvarieämbetets karta över ”Ättekulla området”; i dag står det om en av platserna: ”Området är nu utfyllt.” En boplats från stenåldern strax intill, med tolv härdar och spjutspetsar av flinta, undersöktes och togs bort 1974 i samband med att bostadsområdet planerades.

Men minnet var långt. I Rannsakningarna 1667–68, rikets första stora inventering av fornminnen, berättade de äldsta i Raus att ett slag hade stått där, ”men mellan vem vet de icke”, och att de danska sagornas hjältar Sven Fælding och Starkodder skulle ligga begravda i högarna.

Raus är ett namn jag bär med mig. I mitt pass står det som min födelseort, och förr tror jag att det stod Raus församling. Jag har inte så mycket relation till platsen i dag, men den kommer alltid att följa med mig. Den är en del av min historia.

## 76 000 kullar

Ättekulla är inget undantag. Registret har 17 531 fristående gravhögar och ytterligare omkring 58 000 i gravfälten – omkring 76 000 i allt. Den typiska högen är elva meter bred. {R['stora_20']:,} är minst 20 meter.

{IMG_SE['sv']}

Det som slår en först är det röda bandet längs Skånes kuster, som fortsätter upp längs Halland. Ättekulla ligger mitt i det. Av landets 2 017 högar som är minst 20 meter breda ligger 1 386 i Skåne och 219 i Halland – fyra av fem. I Skåne är nästan varannan hög med känd storlek så stor; i Uppland är det var tjugonde. Den typiska skånska högen är 18 meter bred, den uppländska nio. Det är bronsålderns stora högar, som i Ättekulla.

Bandet följer kusten, men högbyggarna sökte sig inte till själva stranden. Inom Skåne ligger de stora högarna inte närmare havet än de mindre: ungefär fyra av tio ligger inom tre kilometer från dagens strand, bland de stora som bland de små. Det är bygden som ligger vid kusten, på de öppna slätterna, och där ligger högarna. Det mönstret har vi räknat men inte prövat.

Längre norrut, i Mälardalen, i Västergötland och längs Norrlandskusten, är högarna oftare från järnåldern, upp till vikingatiden. Där ligger de flesta i gravfält, och de syns inte på kartan: Uppland har 5 307 gravfält i registret, Skåne 359. Kontrasten på kartan är alltså också en skillnad i sed – bronsålderns stora, ensamma högar i söder, järnålderns gravfält i norr.

Högarna har också burit berättelser. {N_KUNG} av dem heter Kungshögen, och i Stora Fulhög i Borrby i Skåne ska det finnas ”en guldvagga” och en prins begraven.

De har också haft ett hårt liv. {N_GONE:,} av de fristående högarna står som borttagna eller förstörda i registret. I {N_GROP:,} beskrivningar, nästan var tredje, nämns en grop – ofta i mitten, där någon har grävt efter något. I Träne i Skåne hade byn sina källare i högen, och i Skalunda hög i Västergötland ”lär en källare ha legat”.

## Redan gamla för vikingarna

När vikingarna levde var kullarna i Ättekulla redan mellan ett och ett halvt och två och ett halvt tusen år gamla. De var forntid redan då.

Hur såg man på dem? Runstenarna ger några glimtar. På Karlevistenen på Öland, Öl 1, från slutet av 900-talet, står en dikt om en hövding som ligger dold ”i þæimsi haugi”, i denna hög. På två uppländska stenar gjorde de efterlevande en hög bredvid stenen. Vid Broby i Täby lät tre bröder resa stenarna efter sin far ”ok bro þessa gærðu ok haug þenna”, och gjorde denna bro och denna hög (U 135). Vid Harby i Fresta lät Illugi ”ræisa stæina ok haug gæra”, resa stenarna och göra en hög, efter sin bror (U 269). Och två män på andra stenar ägde gårdar som hade fått namn efter högar: Haugbýr (Ög 82) och kanske Kolhaugr (Sö 202, läsningen är osäker).

Ett par hundra år senare skrev islänningen Snorre Sturlasson ned hur man på hans tid mindes de gamla gravskicken. I förordet till Heimskringla delar han in forntiden i åldrar. ”Hin fyrsta öld er kölluð brunaöld”, den första åldern kallas brandåldern: då brände man de döda och reste bautastenar efter dem. Men sedan Frö hade lagts i hög i Uppsala ”gerðu margir höfðingjar eigi síður hauga en bautasteina til minningar um frændur sína” – byggde många hövdingar högar lika väl som bautastenar till minne av sina fränder. I Ynglingasagan låter han Oden själv stifta lagen: efter förnäma män skulle man göra en hög till minne, ”eptir göfga menn skyldi haug gera til minningar”, och efter alla andra som var något att räkna med skulle man ”reisa bautasteina”, resa stenar.

Snorre var en kristen lärd på 1200-talet som såg tillbaka, inte ett ögonvittne. Men i hans bild hör högen och stenen ihop, som två sätt att minnas de döda. Den bilden kan vi pröva i siffrorna.

## Runstenarna sökte sig till de stora högarna

Här finns något vi inte har sett mätt förut. Vikingatidens runstenar restes ofta i landskap där högarna redan stod. Vi ville veta om de stora högarna drog till sig fler stenar än de vanliga – och prövade det med en plan som låstes innan vi räknade.

{chart(True)}

Svaret är ja. I Uppland står det en runsten inom 500 meter från {p0(SH['Uppland'][0])} procent av de stora högarna, mot {p0(SH['Uppland'][1])} procent av de mindre. I Södermanland är det {p0(SH['Södermanland'][0])} mot {p0(SH['Södermanland'][1])} procent, i Medelpad {p0(SH['Medelpad'][0])} mot {p0(SH['Medelpad'][1])}. Räknat inom varje landskap är oddsen för en runsten ungefär tre gånger så stora vid en stor hög. Mönstret håller i båda halvorna av materialet och när gränsen för en stor hög sätts vid 15 eller 30 meter i stället för 20. Östergötland pekar svagt åt andra hållet. I Skåne och Halland går det inte att pröva, eftersom runstenarna där räknas som danska och inte ingår i det svenska materialet.

Exemplen är kända. Vid Skalunda hög i Västergötland, 65 meter bred och sex meter hög, står Vg 44 och Vg 45. Vid Ledbergs kulle i Östergötland står Ledbergsstenen, Ög 181. Vid Tingshögen i Ludgo i Södermanland, 30 meter bred, står Sö 137 och Sö 138.

Varför? Det prövade vi inte. Men den som reste en sten vid en stor hög ställde sin döde bredvid något som alla i bygden kunde se, och som redan var gammalt. En storhög var ett påstående om makt och om rätten till marken. En runsten bredvid den kan ha varit ett sätt att säga: vi hör hit, och vi har alltid gjort det. Det är också Snorres bild – högen för de förnäma, stenen för de andra – men här står de bredvid varandra.

## Det som inte höll

Sune Lindqvist skrev 1917 att storhögarna ligger vid husbyarna, kungens gårdar: ”kung Nordians hög” vid Ås-Husby, ”Björn Järnsidas hög” vid Husby på Munsön (Fornvännen 12, s. 142). Vi prövade det för hela landet. De stora högarna ligger något närmare husbyar och tunaorter än de mindre, men mönstret syns bara i den ena halvan av materialet, och det vänder när gränsen sätts vid 15 meter. Det räcker inte. Inte heller låg de stora högarna närmare de gamla kultplatserna.

## Från högen till kyrkogården

Begravde man fortsatt så? Svaret är att man aldrig riktigt slutade bygga högar, men att seden ändrades gång på gång.

I Ättekulla syns de första skiftena. De äldsta gravarna låg i kistor mitt i högarna. Under den yngre bronsåldern grävde man ned de brända benen i de högar som redan stod där. Mot slutet, skriver Rydbeck, när ”högarne blifvit öfverfyllda och seden att uppföra sådana föråldrats”, började man i stället sätta ned gravurnorna ”under flat mark, utan täckande hög” – men fortfarande nära högarna (s. 82–83). Platsen behöll sin dragningskraft också när seden ändrades.

Under järnåldern kom högarna tillbaka, nu oftast små och samlade i gravfält; omkring 58 000 av registrets högar ligger i gravfält. Några blev väldiga, som Skalunda hög. Och under vikingatiden lades de döda fortfarande i högar: Karlevistenens hövding ligger i sin.

Sedan kom kyrkan. Stenarna vid Broby och Harby bär kors, och ändå gjordes en hög vid dem. Broby-stenen hör till en stilgrupp som brukar dateras till omkring 1020–1050, Harby-stenen till omkring 1070–1100. Också när människorna var kristna kunde högen alltså höra till minnet. Men de döda började begravas obrända, på kyrkogården. Rydbeck såg sambandet redan 1912: ”Bronsåldersfolkets grafhög motsvaras längre fram af de kristnas kyrkogård” (s. 102).

Vi har försökt se skiftet i runstenarna själva. Där en familj reste flera stenar låg nästan alltid ett gravfält nära: 82 procent av stenarna i grupp mot 55 procent av de ensamma. Det var familjens plats, och den låg vid de gamla gravarna. Men när vi prövade om de senare stenarna lämnade gravfälten för kyrkorna pekade siffrorna åt det väntade hållet utan att räcka hela vägen. Bara de allra sista runstenarna, från omkring 1100–1130, står tydligt oftare vid kyrkan: 28 mot 16 på sin ursprungliga plats. Skiftet gick alltså inte på en dag.

Varför ändrades det? Det har vi inte prövat. Men Snorre ger en ledtråd till varför graven hörde ihop med tron. Oden lovade, skriver han, att var och en skulle komma till Valhall med det som brändes med honom: ”með þvílíkum auðœfum skyldi hverr koma til Valhallar, sem hann hafði á bál”. Bålet och högen var en del av en föreställning om vart de döda tog vägen. När föreställningen byttes, byttes graven.

## Tillbaka vid skogens rand

Så vilka var kullarna vid skogens rand? De var bronsålderns släktgravar. Först byggde släkterna högar åt sina förnämsta, sedan grävde de ned sina döda i samma högar, generation efter generation, i nästan tusen år. När vikingarna levde var högarna redan forntid. Vikingarna byggde nya, och de reste sina runstenar bredvid de största – kanske för att låna något av deras ålder. Sedan flyttade de döda in på kyrkogården, och högarna blev platser för sägner om slag och sagohjältar, för skattgrävare och till sist för en växande stad.

Gatunamnen i Ättekulla pekade mot vikingatiden, och de pekade fel. Men kanske inte helt. Vikingarna levde, precis som jag, bland högar som redan var gamla, och de hade sina egna berättelser om vilka som låg där. Snorre skrev ned några av dem.

I Grímnismál säger Oden att han fruktar för korpen Hugin, tanken, men ännu mer för Munin, minnet. Av kullarna runt Ättekulla gård är de flesta borta. Men namnen blev kvar: Ättekulla på området och på gatuskyltarna, Raus i mitt pass. Där klarade sig minnet bättre än kullarna.

:::box Det viktigaste i korthet
- Kullarna i Ättekulla var bronsåldersgravar, använda i nästan tusen år: först för de förnämsta, sedan för många. 39 av 54 högar runt gården är borta i dag.
- Sverige har omkring 76 000 registrerade gravhögar. Var tredje fristående hög har en grop där någon har grävt.
- Vikingatidens runstenar sökte sig till de stora högarna: i Uppland och Södermanland står det en runsten vid nästan varannan stor hög, mot var femte eller sjunde mindre.
- Högarna var forntid redan för vikingarna. Runstenar talar om högar, och ännu vid kristna stenar gjordes en hög. Sedan flyttade de döda till kyrkogården – men långsamt.
- Lindqvists gamla tanke att storhögarna hör till husbyarna går inte att bekräfta för hela landet.
:::

## Så säkra är vi

Registret anger sällan när en hög byggdes, så stora och små högar kan vara från olika tider. Högens storlek är läst ur beskrivningen, som för 11 072 av de fristående högarna anger en diameter. Runstenarnas lägen är Rundatas; flyttade stenar kan stå längre från sin hög i dag än när de restes. Planen låstes innan något räknades. En sak rättade vi innan proven räknades: registret skriver oftast ”20 m i diam”, och planen hade bara räknat med formen ”20 m diam”. Planen och koden ligger öppet på GitHub.

## Källor

- Riksantikvarieämbetet, Kulturmiljöregistret: lämningstypen Hög och högarna i gravfälten, uttag 2 november 2026. Beskrivningarna och sägnerna citeras kort.
- Samnordisk runtextdatabas (Rundata), Uppsala universitet. Open Database License.
- Gatunamnen: © OpenStreetMaps bidragsgivare, Open Database License.
- Rydbeck, Otto 1912. Undersökning af bronsåldershögar i Köpinge, nära Ramlösa hälsobrunn i Skåne. *Fornvännen* 7, s. 81–132. CC BY 4.0.
- Lindqvist, Sune 1917. Ottarshögen i Vendel. *Fornvännen* 12, s. 127–143. CC BY 4.0.
- Snorre Sturlasson, *Heimskringla*: förordet efter Frísbók (isländska Wikisource) och Ynglingasagan kap. 8 efter N. Linder och H. A. Haggsons utgåva 1869–72 (heimskringla.no). Korta citat.
- Vitkis tidigare mätningar: Familjens plats och Tog kyrkan över efter gravfältet?, analysplaner 2026-10-29 på GitHub.
- Analysplanen och koden: [GitHub](https://github.com/Precatio/runes/blob/main/analysplaner/2026-11-18-hogarna.md)."""

body_en = f"""This article does not begin with a runestone, but with the place where I grew up: a part of Helsingborg called Ättekulla. Its streets have Old Norse-inspired names – Bifrostgatan, Midgårdsgatan, Utgårdsgatan, Runristargatan (Rune Carvers' Street), Sven Tveskäggs gata, Styrbjörn Starkes gata, Erik Rödes gata. And at the edge of the forest lay the mounds.

In [The raven called Memory](/en/artiklar/korpen-som-heter-minne/) I have told of Brian Branston's *Gods and Heroes from Viking Mythology*, which I read again and again in my young years. Thor's visit to Utgarda-Loki was in it. At Ättekulla, Utgård was also a street.

That is where I began, and so the article begins there. Who were the mounds, and who lay in them? The street names point to the Viking Age, to kings and seafarers such as Sweyn Forkbeard and Erik the Red. They will turn out to point the wrong way, with one possible exception: Bronsgatan, Bronze Street. From Ättekulla we then follow the mounds out across the country, and back into the Viking Age.

The name itself told more than the streets. An *ättehög* is an old word for a burial mound: the family's mound, where the kin lay. The Swedish National Heritage Board's register has the name Ättekulla, or something like it, at 97 places in more than fifty parishes. It was the district's own word for the graves.

## Who lay in the mounds?

The archaeologist Otto Rydbeck wrote about these very mounds in Fornvännen in 1912. By the road from Ramlösa spa to Raus lay ”a group of Bronze Age burial mounds, on a short stretch numbering no fewer than fourteen. Most of them lie on the land of a farm that has long been called Ättekulla” (p. 82). Eight of them had been dug by Professor Sven Söderberg in the 1870s and 1880s.

In the eight mounds Söderberg found eleven graves from the earlier Bronze Age – inhumations, in coffins of stone or wood – and fifty-three from the later, where the burnt bones had been dug down into the mounds that already stood there. New earth was heaped on so as not to disturb the old graves, and the mounds grew (pp. 89–90). Rydbeck explained the difference thus: at first only ”the more distinguished” could ”afford to give their kin so costly a memorial as a coffin of stone or wood with precious equipment in a laboriously built burial mound” (p. 90). Later ”rich and poor were probably buried side by side” (p. 91).

So the mounds at Ättekulla were not the Vikings'. They were more than a thousand years older, and they were used for almost a thousand years. The name was right: they were the family's mounds. Of the streets, only Bronsgatan hit the right age.

The largest was examined again by Rolf Petré in 1967–68. It had been 25 metres across and four metres high, built of turf around a cairn of stone. In the middle lay three inhumation graves with traces of oak coffins, and in the central grave a bronze dagger in its sheath, from the third period of the Bronze Age. Then the mound was removed.

## What disappeared

{IMG_AT['en']}

Within one and a half kilometres of Ättekulla farm the register has 54 mounds. 39 of them have been removed or destroyed. In 1957 G. A. Hellman marked the mounds on the Heritage Board's map of ”the Ättekulla area”; today the register says of one of the places: ”The area is now filled in.” A Stone Age settlement close by, with twelve hearths and flint spearheads, was excavated and removed in 1974 when the housing estate was being planned.

But the memory was long. In the Rannsakningar of 1667–68, the kingdom's first great survey of ancient monuments, the oldest people in Raus said that a battle had been fought there, ”but between whom they do not know”, and that the Danish saga heroes Sven Fælding and Starkodder were buried in the mounds.

Raus is a name I carry with me. My passport gives it as my place of birth, and I think it used to say Raus parish. I do not have much of a relationship with the place today, but it will always come with me. It is part of my story.

## 76,000 mounds

Ättekulla is no exception. The register has 17,531 free-standing burial mounds and about another 58,000 inside the grave fields – some 76,000 in all. The typical mound is eleven metres across. {R['stora_20']:,} are at least 20 metres.

{IMG_SE['en']}

What strikes one first is the red band along the coasts of Skåne, continuing up along Halland. Ättekulla lies in the middle of it. Of the country's 2,017 mounds at least 20 metres across, 1,386 lie in Skåne and 219 in Halland – four in five. In Skåne almost every other mound of known size is that large; in Uppland it is one in twenty. The typical Scanian mound is 18 metres across, the typical Uppland mound nine. These are the great mounds of the Bronze Age, as at Ättekulla.

The band follows the coast, but the mound builders did not seek out the shore itself. Within Skåne the large mounds lie no closer to the sea than the smaller ones: about four in ten lie within three kilometres of today's shore, among the large as among the small. It is the settled land that lies along the coast, on the open plains, and that is where the mounds are. We have counted this pattern but not tested it.

Further north, in the Mälar valley, in Västergötland and along the Norrland coast, the mounds are more often from the Iron Age, up to the Viking Age. There most lie in grave fields, and they do not show on the map: Uppland has 5,307 grave fields in the register, Skåne 359. So the contrast on the map is also a difference in custom – the Bronze Age's great solitary mounds in the south, the Iron Age's grave fields in the north.

The mounds have carried stories too. {N_KUNG} of them are called Kungshögen, the king's mound, and in Stora Fulhög at Borrby in Skåne there is said to be ”a golden cradle” and a prince buried.

They have also had a hard life. {N_GONE:,} of the free-standing mounds are listed as removed or destroyed. In {N_GROP:,} descriptions, almost one in three, a pit is mentioned – often in the middle, where someone has dug for something. At Träne in Skåne the village kept its cellars in the mound, and in Skalunda hög in Västergötland ”a cellar is said to have lain”.

## Already old to the Vikings

When the Vikings lived, the mounds at Ättekulla were already between one and a half and two and a half thousand years old. They were the ancient past even then.

How did people see them? The runestones give a few glimpses. On the Karlevi stone on Öland, Öl 1, from the late 900s, there is a poem about a chieftain who lies hidden ”i þæimsi haugi”, in this mound. On two stones in Uppland the survivors made a mound beside the stone. At Broby in Täby three brothers had the stones raised for their father ”ok bro þessa gærðu ok haug þenna”, and made this bridge and this mound (U 135). At Harby in Fresta Illugi had them ”ræisa stæina ok haug gæra”, raise the stones and make a mound, for his brother (U 269). And two men on other stones owned farms named after mounds: Haugbýr (Ög 82) and perhaps Kolhaugr (Sö 202, the reading is uncertain).

A couple of centuries later the Icelander Snorri Sturluson wrote down how the old burial customs were remembered in his day. In the prologue to Heimskringla he divides the ancient past into ages. ”Hin fyrsta öld er kölluð brunaöld”, the first age is called the age of burning: the dead were burned and standing stones raised after them. But after Freyr had been laid in a mound at Uppsala ”gerðu margir höfðingjar eigi síður hauga en bautasteina til minningar um frændur sína” – many chieftains built mounds no less than standing stones in memory of their kinsmen. In Ynglinga saga he has Odin himself lay down the law: for noble men a mound was to be made in their memory, ”eptir göfga menn skyldi haug gera til minningar”, and for all others of any worth one was to ”reisa bautasteina”, raise stones.

Snorri was a Christian scholar of the 1200s looking back, not an eyewitness. But in his picture the mound and the stone belong together, as two ways of remembering the dead. That picture we can test in the numbers.

## The runestones sought out the large mounds

Here is something we have not seen measured before. The Viking Age runestones were often raised in landscapes where the mounds already stood. We wanted to know whether the large mounds drew more stones than the ordinary ones – and tested it with a plan locked before we counted.

{chart(False)}

The answer is yes. In Uppland a runestone stands within 500 metres of {p0(SH['Uppland'][0])} per cent of the large mounds, against {p0(SH['Uppland'][1])} per cent of the smaller ones. In Södermanland it is {p0(SH['Södermanland'][0])} against {p0(SH['Södermanland'][1])} per cent, in Medelpad {p0(SH['Medelpad'][0])} against {p0(SH['Medelpad'][1])}. Counted within each province, the odds of a runestone are about three times as high at a large mound. The pattern holds in both halves of the material and when the limit for a large mound is set at 15 or 30 metres instead of 20. Östergötland points weakly the other way. In Skåne and Halland it cannot be tested, because the runestones there count as Danish and are not part of the Swedish material.

The examples are well known. By Skalunda hög in Västergötland, 65 metres across and six metres high, stand Vg 44 and Vg 45. By Ledbergs kulle in Östergötland stands the Ledberg stone, Ög 181. By Tingshögen in Ludgo in Södermanland, 30 metres across, stand Sö 137 and Sö 138.

Why? We did not test that. But whoever raised a stone by a large mound placed their dead beside something everyone in the district could see, and which was already old. A great mound was a statement about power and about the right to the land. A runestone beside it may have been a way of saying: we belong here, and we always have. It is Snorri's picture too – the mound for the noble, the stone for the others – but here they stand side by side.

## What did not hold

Sune Lindqvist wrote in 1917 that the great mounds lie by the husbyar, the king's farms: ”King Nordian's mound” at Ås-Husby, ”Björn Ironside's mound” at Husby on Munsön (Fornvännen 12, p. 142). We tested it for the whole country. The large mounds lie somewhat closer to husby and tuna places than the smaller ones, but the pattern shows only in one half of the material, and it reverses when the limit is set at 15 metres. That is not enough. Nor did the large mounds lie closer to the old cult places.

## From the mound to the churchyard

Did people go on burying that way? The answer is that they never quite stopped building mounds, but the custom changed again and again.

At Ättekulla the first shifts can be seen. The oldest graves lay in coffins in the middle of the mounds. In the later Bronze Age the burnt bones were dug down into the mounds that already stood there. Towards the end, Rydbeck writes, when ”the mounds had become over-filled and the custom of raising them had grown old-fashioned”, people began instead to set down the burial urns ”under flat ground, without a covering mound” – but still close to the mounds (pp. 82–83). The place kept its pull even when the custom changed.

In the Iron Age the mounds came back, now mostly small and gathered in grave fields; some 58,000 of the register's mounds lie in grave fields. A few became huge, like Skalunda hög. And in the Viking Age the dead were still laid in mounds: the Karlevi stone's chieftain lies in his.

Then came the church. The stones at Broby and Harby bear crosses, and yet a mound was made beside them. The Broby stone belongs to a style group usually dated to about 1020–1050, the Harby stone to about 1070–1100. So even when people were Christian, the mound could still belong to the memorial. But the dead began to be buried unburnt, in the churchyard. Rydbeck saw the link as early as 1912: ”The Bronze Age people's burial mound corresponds later to the Christians' churchyard” (p. 102).

We have tried to see the shift in the runestones themselves. Where a family raised several stones, a grave field almost always lay nearby: 82 per cent of the stones in groups against 55 per cent of the lone ones. That was the family's place, and it lay by the old graves. But when we tested whether the later stones left the grave fields for the churches, the numbers pointed the expected way without going the whole distance. Only the very last runestones, from about 1100–1130, clearly stand more often by the church: 28 against 16 in their original place. The shift did not happen in a day.

Why did it change? We have not tested that. But Snorri gives a clue to why the grave belonged with the belief. Odin promised, he writes, that everyone would come to Valhalla with what was burned with him: ”með þvílíkum auðœfum skyldi hverr koma til Valhallar, sem hann hafði á bál”. The pyre and the mound were part of an idea of where the dead went. When the idea changed, the grave changed.

## Back at the edge of the forest

So who were the mounds at the edge of the forest? They were the graves of Bronze Age families. First the families built mounds for their most distinguished, then they dug their dead down into the same mounds, generation after generation, for almost a thousand years. When the Vikings lived, the mounds were already the ancient past. The Vikings built new ones, and they raised their runestones beside the largest – perhaps to borrow something of their age. Then the dead moved into the churchyard, and the mounds became places for legends of battles and saga heroes, for treasure-hunters and at last for a growing town.

The street names at Ättekulla pointed to the Viking Age, and they pointed the wrong way. But perhaps not entirely. The Vikings lived, just as I did, among mounds that were already old, and they had their own stories of who lay there. Snorri wrote some of them down.

In Grímnismál Odin says that he fears for the raven Huginn, thought, but even more for Muninn, memory. Of the mounds around Ättekulla farm most are gone. But the names remained: Ättekulla on the district and on the street signs, Raus in my passport. There memory fared better than the mounds.

:::box The essentials in brief
- The mounds at Ättekulla were Bronze Age graves, used for almost a thousand years: first for the most distinguished, then for many. 39 of the 54 mounds around the farm are gone today.
- Sweden has about 76,000 registered burial mounds. One free-standing mound in three has a pit where someone has dug.
- The Viking Age runestones sought out the large mounds: in Uppland and Södermanland a runestone stands by almost every other large mound, against one in five or seven smaller ones.
- The mounds were the ancient past already to the Vikings. Runestones speak of mounds, and even beside Christian stones a mound was made. Then the dead moved to the churchyard – but slowly.
- Lindqvist's old idea that the great mounds belong to the husbyar cannot be confirmed for the whole country.
:::

## How sure we are

The register seldom says when a mound was built, so large and small mounds may be from different times. The mound's size is read from the description, which gives a diameter for 11,072 of the free-standing mounds. The runestones' positions are Rundata's; moved stones may stand further from their mound today than when they were raised. The plan was locked before anything was counted. One thing we corrected before the tests were run: the register usually writes ”20 m i diam”, and the plan had reckoned only with the form ”20 m diam”. The plan and the code are open on GitHub.

## Sources

- Swedish National Heritage Board, Kulturmiljöregistret: the type Hög and the mounds in the grave fields, extract of 2 November 2026. The descriptions and legends are quoted briefly.
- Scandinavian Runic-text Database (Rundata), Uppsala University. Open Database License.
- Street names: © OpenStreetMap contributors, Open Database License.
- Rydbeck, Otto 1912. Undersökning af bronsåldershögar i Köpinge, nära Ramlösa hälsobrunn i Skåne. *Fornvännen* 7, pp. 81–132. CC BY 4.0.
- Lindqvist, Sune 1917. Ottarshögen i Vendel. *Fornvännen* 12, pp. 127–143. CC BY 4.0.
- Snorri Sturluson, *Heimskringla*: the prologue after Frísbók (Icelandic Wikisource) and Ynglinga saga ch. 8 after N. Linder and H. A. Haggson's edition 1869–72 (heimskringla.no). Short quotations.
- Vitki's earlier measurements: Familjens plats and Did the church take over from the grave field?, analysis plans of 2026-10-29 on GitHub.
- The analysis plan and the code: [GitHub](https://github.com/Precatio/runes/blob/main/analysplaner/2026-11-18-hogarna.md)."""

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
