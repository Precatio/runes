"""Artikeln om gravhögarna (sv + en), med början i Ättekulla i Helsingborg (Viktor 2026-11-18: "Vore kul om vi började vid
Ättekulla i Helsingborg, eftersom jag började där"). Låst plan analysplaner/2026-11-18-hogarna.md (089fcfb5), resultat
utdata/hogar/resultat.json, kartor utdata/hogar/karta_*.py. Registret: /Volumes/2TB/Antigrvity/Runes/downloads/hogar/.
Litteraturen (Rydbeck 1912, Lindqvist 1917, Stjerna 1906) prövas mot tidskrifternas text.
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
assert "I högen finns en skatt som vaktas av endrake" in re.sub(r"\s+", " ", EX["Träne 46:1"]["tradition"])
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
jcheck("1906_119", 26, "143", "draken bor kvar i ättekullen", "i likhet med draken i Beovulf")

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
summary = ("I Ättekulla i Helsingborg låg kullarna vid skogens rand: bronsåldersgravar som användes i tusen år. De flesta "
           "är borta i dag. Vi följer högarna därifrån över hela landet – 76 000 i registret – och finner att vikingatidens "
           "runstenar sökte sig till de stora högarna: i Uppland och Södermanland står det en runsten vid var femte vanlig "
           "hög men vid nästan varannan stor.")
summary_en = ("At Ättekulla in Helsingborg the mounds lay at the edge of the forest: Bronze Age graves used for a thousand years. "
              "Most are gone today. We follow the mounds from there across the whole country – 76,000 in the register – and "
              "find that the Viking Age runestones sought out the large mounds: in Uppland and Södermanland a runestone stands "
              "by one ordinary mound in five but by almost every other large one.")

body = f"""Den som växte upp i Ättekulla i Helsingborg, som personen bakom Vitki gjorde, minns kullarna vid skogens rand. Vad var de, och vilka låg där?

Namnet berättade det. En *ättehög* är ett gammalt ord för en gravhög: släktens hög, där ätten låg. Riksantikvarieämbetets register har namnet Ättekulla, eller något liknande, på 97 platser i över femtio socknar. Det var bygdens eget ord för gravarna.

## Vilka låg i kullarna?

Arkeologen Otto Rydbeck skrev om just dessa högar i Fornvännen 1912. Vid vägen från Ramlösa hälsobrunn till Raus låg ”en samling grafhögar från bronsåldern, på en kort sträcka uppgående till ej mindre än fjorton stycken. Flertalet af dem äro belägna på egorna till en gård, hvilken sedan gammalt benämnes Ättekulla” (s. 82). Åtta av dem hade grävts ut av professor Sven Söderberg på 1870- och 1880-talen.

I de åtta högarna fann Söderberg elva gravar från den äldre bronsåldern – skelettgravar, i kistor av sten eller trä – och femtiotre från den yngre, där de brända benen hade grävts ned i högarna som redan stod där. Man fyllde på med ny jord för att inte störa de gamla gravarna, och högarna växte (s. 89–90). Rydbeck förklarade skillnaden så: i början var det bara ”de förnämligare” som ”hade råd att bestå sina anhöriga ett så kostsamt eftermäle som en kista af sten eller trä med dyrbar utrustning i en svåruppförd grafhög” (s. 90). Senare ”jordades sannolikt rika och fattiga om hvarandra” (s. 91).

Kullarna i Ättekulla var alltså inte vikingarnas. De var tusen år äldre, och de användes i nästan tusen år. Namnet hade rätt: det var släktens högar.

Den största undersöktes på nytt av Rolf Petré 1967–68. Den hade varit 25 meter bred och fyra meter hög, byggd av torv runt ett röse av sten. I mitten låg tre skelettgravar med spår av ekkistor, och i centralgraven en bronsdolk i sin slida, från bronsålderns tredje period. Sedan togs högen bort.

## Det som försvann

{IMG_AT['sv']}

Inom en och en halv kilometer från Ättekulla gård har registret 54 högar. 39 av dem är borttagna eller förstörda. 1957 ritade G. A. Hellman in högarna på Riksantikvarieämbetets karta över ”Ättekulla området”; i dag står det om en av platserna: ”Området är nu utfyllt.” En boplats från stenåldern strax intill, med tolv härdar och spjutspetsar av flinta, undersöktes och togs bort 1974 i samband med att bostadsområdet planerades.

Men minnet var långt. I Rannsakningarna 1667–68, rikets första stora inventering av fornminnen, berättade de äldsta i Raus att ett slag hade stått där, ”men mellan vem vet de icke”, och att de danska sagornas hjältar Sven Fælding och Starkodder skulle ligga begravda i högarna.

## 76 000 kullar

Ättekulla är inget undantag. Registret har 17 531 fristående gravhögar och ytterligare omkring 58 000 i gravfälten – omkring 76 000 i allt. Den typiska högen är elva meter bred. {R['stora_20']:,} är minst 20 meter.

{IMG_SE['sv']}

Kartan visar två högbygder. I söder och väster, längs Skånes och Hallands kuster, ligger de stora runda högarna tätt – många av dem från bronsåldern, som i Ättekulla. Längre norrut, i Mälardalen, i Västergötland och längs Norrlandskusten, är högarna oftare från järnåldern, upp till vikingatiden.

Och de har haft ett hårt liv. {N_GONE:,} av de fristående högarna står som borttagna eller förstörda i registret. I {N_GROP:,} beskrivningar, nästan var tredje, nämns en grop – ofta i mitten, där någon har grävt efter något. I Träne i Skåne hade byn sina källare i högen, och i Skalunda hög i Västergötland ”lär en källare ha legat”.

## Runstenarna sökte sig till de stora högarna

Här finns något vi inte har sett mätt förut. Vikingatidens runstenar restes ofta i landskap där högarna redan stod. Vi ville veta om de stora högarna drog till sig fler stenar än de vanliga – och prövade det med en plan som låstes innan vi räknade.

{chart(True)}

Svaret är ja. I Uppland står det en runsten inom 500 meter från {p0(SH['Uppland'][0])} procent av de stora högarna, mot {p0(SH['Uppland'][1])} procent av de mindre. I Södermanland är det {p0(SH['Södermanland'][0])} mot {p0(SH['Södermanland'][1])} procent, i Medelpad {p0(SH['Medelpad'][0])} mot {p0(SH['Medelpad'][1])}. Räknat inom varje landskap är oddsen för en runsten ungefär tre gånger så stora vid en stor hög. Mönstret håller i båda halvorna av materialet och när gränsen för en stor hög sätts vid 15 eller 30 meter i stället för 20. Östergötland pekar svagt åt andra hållet. I Skåne och Halland går det inte att pröva, eftersom runstenarna där räknas som danska och inte ingår i det svenska materialet.

Exemplen är kända. Vid Skalunda hög i Västergötland, 65 meter bred och sex meter hög, står Vg 44 och Vg 45. Vid Ledbergs kulle i Östergötland står Ledbergsstenen, Ög 181. Vid Tingshögen i Ludgo i Södermanland, 30 meter bred, står Sö 137 och Sö 138.

Varför? Det prövade vi inte. Men den som reste en sten vid en stor hög ställde sin döde bredvid något som alla i bygden kunde se, och som redan var gammalt. En storhög var ett påstående om makt och om rätten till marken. En runsten bredvid den kan ha varit ett sätt att säga: vi hör hit, och vi har alltid gjort det.

## Det som inte höll

Sune Lindqvist skrev 1917 att storhögarna ligger vid husbyarna, kungens gårdar: ”kung Nordians hög” vid Ås-Husby, ”Björn Järnsidas hög” vid Husby på Munsön (Fornvännen 12, s. 142). Vi prövade det för hela landet. De stora högarna ligger något närmare husbyar och tunaorter än de mindre, men mönstret syns bara i den ena halvan av materialet, och det vänder när gränsen sätts vid 15 meter. Det räcker inte. Inte heller låg de stora högarna närmare de gamla kultplatserna.

## Kungar, drakar och skatter

Högarna har burit berättelser länge. {N_KUNG} högar i registret heter Kungshögen. I Borrby i Skåne ska det i Stora Fulhög finnas ”en guldvagga”, och där ska ligga en prins begraven. I Träne sades det att ”i högen finns en skatt som vaktas av en drake”.

Draken är gammal. Knut Stjerna skrev redan 1906 att draken i de skånska sägnerna ”bor kvar i ättekullen”, och att den liknar draken i Beowulf, den anglosaxiska dikten där en drake vaktar en skatt i en hög (Fornvännen 1, 1906, s. 143). Kanske är det därför så många högar har en grop i toppen.

:::box Det viktigaste i korthet
- Kullarna i Ättekulla var bronsåldersgravar, använda i nästan tusen år: först för de förnämsta, sedan för många. 39 av 54 högar runt gården är borta i dag.
- Sverige har omkring 76 000 registrerade gravhögar. Var tredje fristående hög har en grop där någon har grävt.
- Vikingatidens runstenar sökte sig till de stora högarna: i Uppland och Södermanland står det en runsten vid nästan varannan stor hög, mot var femte eller sjunde mindre.
- Lindqvists gamla tanke att storhögarna hör till husbyarna går inte att bekräfta för hela landet.
:::

## Så säkra är vi

Registret anger sällan när en hög byggdes, så stora och små högar kan vara från olika tider. Högens storlek är läst ur beskrivningen, som för 11 072 av de fristående högarna anger en diameter. Runstenarnas lägen är Rundatas; flyttade stenar kan stå längre från sin hög i dag än när de restes. Planen låstes innan något räknades. En sak rättade vi innan proven räknades: registret skriver oftast ”20 m i diam”, och planen hade bara räknat med formen ”20 m diam”. Planen och koden ligger öppet på GitHub.

## Källor

- Riksantikvarieämbetet, Kulturmiljöregistret: lämningstypen Hög och högarna i gravfälten, uttag 2 november 2026. Beskrivningarna och sägnerna citeras kort.
- Samnordisk runtextdatabas (Rundata), Uppsala universitet. Open Database License.
- Rydbeck, Otto 1912. Undersökning af bronsåldershögar i Köpinge, nära Ramlösa hälsobrunn i Skåne. *Fornvännen* 7, s. 81–132. CC BY 4.0.
- Lindqvist, Sune 1917. Ottarshögen i Vendel. *Fornvännen* 12, s. 127–143. CC BY 4.0.
- Stjerna, Knut 1906. Drakskatten i Beovulf. *Fornvännen* 1, s. 119–144. CC BY 4.0.
- Analysplanen och koden: [GitHub](https://github.com/Precatio/runes/blob/main/analysplaner/2026-11-18-hogarna.md)."""

body_en = f"""Whoever grew up at Ättekulla in Helsingborg, as the person behind Vitki did, remembers the mounds at the edge of the forest. What were they, and who lay there?

The name told. An *ättehög* is an old word for a burial mound: the family's mound, where the kin lay. The Swedish National Heritage Board's register has the name Ättekulla, or something like it, at 97 places in more than fifty parishes. It was the district's own word for the graves.

## Who lay in the mounds?

The archaeologist Otto Rydbeck wrote about these very mounds in Fornvännen in 1912. By the road from Ramlösa spa to Raus lay ”a group of Bronze Age burial mounds, on a short stretch numbering no fewer than fourteen. Most of them lie on the land of a farm that has long been called Ättekulla” (p. 82). Eight of them had been dug by Professor Sven Söderberg in the 1870s and 1880s.

In the eight mounds Söderberg found eleven graves from the earlier Bronze Age – inhumations, in coffins of stone or wood – and fifty-three from the later, where the burnt bones had been dug down into the mounds that already stood there. New earth was heaped on so as not to disturb the old graves, and the mounds grew (pp. 89–90). Rydbeck explained the difference thus: at first only ”the more distinguished” could ”afford to give their kin so costly a memorial as a coffin of stone or wood with precious equipment in a laboriously built burial mound” (p. 90). Later ”rich and poor were probably buried side by side” (p. 91).

So the mounds at Ättekulla were not the Vikings'. They were a thousand years older, and they were used for almost a thousand years. The name was right: they were the family's mounds.

The largest was examined again by Rolf Petré in 1967–68. It had been 25 metres across and four metres high, built of turf around a cairn of stone. In the middle lay three inhumation graves with traces of oak coffins, and in the central grave a bronze dagger in its sheath, from the third period of the Bronze Age. Then the mound was removed.

## What disappeared

{IMG_AT['en']}

Within one and a half kilometres of Ättekulla farm the register has 54 mounds. 39 of them have been removed or destroyed. In 1957 G. A. Hellman marked the mounds on the Heritage Board's map of ”the Ättekulla area”; today the register says of one of the places: ”The area is now filled in.” A Stone Age settlement close by, with twelve hearths and flint spearheads, was excavated and removed in 1974 when the housing estate was being planned.

But the memory was long. In the Rannsakningar of 1667–68, the kingdom's first great survey of ancient monuments, the oldest people in Raus said that a battle had been fought there, ”but between whom they do not know”, and that the Danish saga heroes Sven Fælding and Starkodder were buried in the mounds.

## 76,000 mounds

Ättekulla is no exception. The register has 17,531 free-standing burial mounds and about another 58,000 inside the grave fields – some 76,000 in all. The typical mound is eleven metres across. {R['stora_20']:,} are at least 20 metres.

{IMG_SE['en']}

The map shows two mound landscapes. In the south and west, along the coasts of Skåne and Halland, the large round mounds lie close together – many of them from the Bronze Age, as at Ättekulla. Further north, in the Mälar valley, in Västergötland and along the Norrland coast, the mounds are more often from the Iron Age, up to the Viking Age.

And they have had a hard life. {N_GONE:,} of the free-standing mounds are listed as removed or destroyed. In {N_GROP:,} descriptions, almost one in three, a pit is mentioned – often in the middle, where someone has dug for something. At Träne in Skåne the village kept its cellars in the mound, and in Skalunda hög in Västergötland ”a cellar is said to have lain”.

## The runestones sought out the large mounds

Here is something we have not seen measured before. The Viking Age runestones were often raised in landscapes where the mounds already stood. We wanted to know whether the large mounds drew more stones than the ordinary ones – and tested it with a plan locked before we counted.

{chart(False)}

The answer is yes. In Uppland a runestone stands within 500 metres of {p0(SH['Uppland'][0])} per cent of the large mounds, against {p0(SH['Uppland'][1])} per cent of the smaller ones. In Södermanland it is {p0(SH['Södermanland'][0])} against {p0(SH['Södermanland'][1])} per cent, in Medelpad {p0(SH['Medelpad'][0])} against {p0(SH['Medelpad'][1])}. Counted within each province, the odds of a runestone are about three times as high at a large mound. The pattern holds in both halves of the material and when the limit for a large mound is set at 15 or 30 metres instead of 20. Östergötland points weakly the other way. In Skåne and Halland it cannot be tested, because the runestones there count as Danish and are not part of the Swedish material.

The examples are well known. By Skalunda hög in Västergötland, 65 metres across and six metres high, stand Vg 44 and Vg 45. By Ledbergs kulle in Östergötland stands the Ledberg stone, Ög 181. By Tingshögen in Ludgo in Södermanland, 30 metres across, stand Sö 137 and Sö 138.

Why? We did not test that. But whoever raised a stone by a large mound placed their dead beside something everyone in the district could see, and which was already old. A great mound was a statement about power and about the right to the land. A runestone beside it may have been a way of saying: we belong here, and we always have.

## What did not hold

Sune Lindqvist wrote in 1917 that the great mounds lie by the husbyar, the king's farms: ”King Nordian's mound” at Ås-Husby, ”Björn Ironside's mound” at Husby on Munsön (Fornvännen 12, p. 142). We tested it for the whole country. The large mounds lie somewhat closer to husby and tuna places than the smaller ones, but the pattern shows only in one half of the material, and it reverses when the limit is set at 15 metres. That is not enough. Nor did the large mounds lie closer to the old cult places.

## Kings, dragons and treasure

The mounds have carried stories for a long time. {N_KUNG} mounds in the register are called Kungshögen, the king's mound. At Borrby in Skåne there is said to be ”a golden cradle” in Stora Fulhög, and a prince buried there. At Träne it was said that ”in the mound there is a treasure guarded by a dragon”.

The dragon is old. Knut Stjerna wrote as early as 1906 that the dragon of the Scanian legends ”still lives in the ättekulle”, and that it resembles the dragon in Beowulf, the Old English poem in which a dragon guards a treasure in a mound (Fornvännen 1, 1906, p. 143). Perhaps that is why so many mounds have a pit in the top.

:::box The essentials in brief
- The mounds at Ättekulla were Bronze Age graves, used for almost a thousand years: first for the most distinguished, then for many. 39 of the 54 mounds around the farm are gone today.
- Sweden has about 76,000 registered burial mounds. One free-standing mound in three has a pit where someone has dug.
- The Viking Age runestones sought out the large mounds: in Uppland and Södermanland a runestone stands by almost every other large mound, against one in five or seven smaller ones.
- Lindqvist's old idea that the great mounds belong to the husbyar cannot be confirmed for the whole country.
:::

## How sure we are

The register seldom says when a mound was built, so large and small mounds may be from different times. The mound's size is read from the description, which gives a diameter for 11,072 of the free-standing mounds. The runestones' positions are Rundata's; moved stones may stand further from their mound today than when they were raised. The plan was locked before anything was counted. One thing we corrected before the tests were run: the register usually writes ”20 m i diam”, and the plan had reckoned only with the form ”20 m diam”. The plan and the code are open on GitHub.

## Sources

- Swedish National Heritage Board, Kulturmiljöregistret: the type Hög and the mounds in the grave fields, extract of 2 November 2026. The descriptions and legends are quoted briefly.
- Scandinavian Runic-text Database (Rundata), Uppsala University. Open Database License.
- Rydbeck, Otto 1912. Undersökning af bronsåldershögar i Köpinge, nära Ramlösa hälsobrunn i Skåne. *Fornvännen* 7, pp. 81–132. CC BY 4.0.
- Lindqvist, Sune 1917. Ottarshögen i Vendel. *Fornvännen* 12, pp. 127–143. CC BY 4.0.
- Stjerna, Knut 1906. Drakskatten i Beovulf. *Fornvännen* 1, pp. 119–144. CC BY 4.0.
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
