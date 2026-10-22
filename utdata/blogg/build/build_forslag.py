"""Artikeln "Fem runstenar söker sin ristare": Stenöversiktens starkaste nya ristarförslag för runstenar utan ristare i
Rundata, blindprovet bakom dem och hur Vitki räknar fram ett förslag (analysplanen utdata/forslag/analysplan_forslag.md).
Varje siffra hämtas ur blindprovet (blindprov.json), förslagslistan (nya_forslag.json), R-körningens attribution.json,
stavningsjämförelsens egen utvärdering och Rundata, och låses med asserts. Skärmbilderna tas med forslag_bilder.py.
    ../../../.venv/bin/python build_forslag.py [--write | --update DOC | --publish DOC]
Skriver utdata/blogg/forslag.json; --write sparar ett nytt opublicerat utkast i Firestore, --publish publicerar utkastet
och webbplatsen (som Admin → Publicera)."""
import csv
import datetime as dt
import hashlib
import io
import json
import math
import os
import re
import sys
from collections import Counter

from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from api.rundata import store  # noqa: E402
from api.routers.orthography import model as orthography_model  # noqa: E402
from src import blog_figures, commons  # noqa: E402
from src.research_gaps import certain_carvers, is_runestone, model_carvers, province  # noqa: E402

FP = "5fdfd1e095bfb6fb"
RUN = os.path.join(ROOT, "data", "cache", "r", "corpus", FP)
FORSLAG = os.path.join(ROOT, "utdata", "forslag")
BILDER = os.path.join(ROOT, "utdata", "blogg", "forslag")
A = json.load(open(os.path.join(RUN, "attribution.json"), encoding="utf-8"))
B = json.load(open(os.path.join(FORSLAG, "blindprov.json"), encoding="utf-8"))
N = json.load(open(os.path.join(FORSLAG, "nya_forslag.json"), encoding="utf-8"))
pr = lambda x: round(100 * x)  # noqa: E731
sv = lambda n: f"{n:,}".replace(",", " ")  # noqa: E731
d2 = lambda x: f"{x:.2f}".replace(".", ",")  # noqa: E731
SUP = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")
ORD = "noll en två tre fyra fem sex sju åtta nio tio elva tolv".split()
ord_ = lambda n: ORD[n] if n < len(ORD) else str(n)  # noqa: E731 - small numbers in words, as in running text


def km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


# ---- låsningarna -----------------------------------------------------------------------------------
# The plan was locked before the blind test was run, and every result is from the corpus version named here
SHA = hashlib.sha256(open(os.path.join(FORSLAG, "analysplan_forslag.md"), "rb").read()).hexdigest()
assert SHA == B["plan_sha256"] == open(os.path.join(FORSLAG, "analysis_plan_forslag.sha256")).read().split()[0]
assert B["corpus"] == N["corpus"] == FP

ins = store().inscriptions
by = {r["signum"]: r for r in ins}
stones = [r for r in ins if is_runestone(r)]
C = N["counts"]
assert (C["nytt förslag"], C["möjligt förslag"], C["inget förslag"], N["n_unattributed"], len(stones)) == (86, 292, 1172, 1550, 2321)
assert round(3 * N["n_unattributed"] / len(stones)) == 2  # two of three

# The blind test (analysplan 3)
NY, MO, SI = B["nytt"], B["mojligt"], B["nytt_signed"]
assert (B["n_attributed"], B["status_counts"]) == (769, {"inget förslag": 272, "möjligt förslag": 195, "nytt förslag": 302})
assert (NY["n"], NY["right"], NY["nearest_right"], NY["vitki_only"], NY["nearest_only"]) == (302, 248, 133, 132, 17)
assert (pr(NY["precision"]), pr(NY["ci"][0]), pr(NY["ci"][1]), pr(NY["nearest_precision"])) == (82, 77, 86, 44)
P = NY["mcnemar_p"]
P_MANT, P_EXP = f"{P:.0e}".split("e")
assert (P_MANT, int(P_EXP)) == ("3", -23)
# The simile: the Swedish Lotto jackpot (7 of 35) three weeks in a row is still more likely than the McNemar p
LOTTO = 1 / math.comb(35, 7)
assert math.comb(35, 7) == 6_724_520 and LOTTO ** 4 < P < LOTTO ** 3
assert (SI["n"], SI["right"], SI["nearest_right"]) == (100, 72, 42) and SI["mcnemar_p"] < 1e-5
assert (MO["n"], MO["right"], MO["nearest_right"], pr(MO["precision"]), pr(MO["nearest_precision"])) == (195, 108, 66, 55, 34)
STR = {x["label"]: x for x in B["by_strength"]}
TOPSTR = STR["0.7–1.01"]
assert (TOPSTR["n"], TOPSTR["right"], pr(TOPSTR["precision"])) == (165, 142, 86)
PROV = B["by_province"]
SO = PROV["Sö"]
assert (PROV["U"]["n"], PROV["U"]["right"], pr(PROV["U"]["precision"]), pr(PROV["U"]["nearest_precision"])) == (270, 227, 84, 43)
assert (SO["n"], SO["right"], pr(SO["precision"]), SO["nearest_right"], pr(SO["nearest_precision"])) == (28, 17, 61, 13, 46)
assert SO["mcnemar_p"] > 0.3
assert B["outside_universe"] == {"n": 133, "nytt": 23} and B["nytt_no_model"]["n"] == 0
EX = B["external"]
assert (EX["n"], EX["in_universe"], EX["n_nytt"], EX["n_mojligt"], EX["agree_mojligt"]) == (19, 8, 0, 3, 1)
BROWS = {x["signum"]: x for x in B["rows"]}
nytt = [x for x in B["rows"] if x["status"] == "nytt förslag"]


def per(c):
    xs = [x for x in nytt if x["suggested"] == c]
    return sum(x["suggested"] in x["truth"] for x in xs), len(xs)


# Precision per suggested carver (beyond the plan): Öpir is the lowest of every carver suggested more than three times
PER = {c: per(c) for c in {x["suggested"] for x in nytt}}
assert (PER["Traen"], PER["Fot 2"], PER["Öpir 1"]) == ((11, 15), (30, 35), (68, 104))
assert min((r / n, c) for c, (r, n) in PER.items() if n > 3)[1] == "Öpir 1"
miss = [x for x in nytt if x["suggested"] == "Traen" and "Traen" not in x["truth"]]
assert sorted(x["signum"] for x in miss) == ["Sö 159", "Sö 160", "Sö 296", "Sö 46"]
assert all(x["signed"] and x["province"] == "Sö" for x in miss)
# Neighbours named in the portraits, as the blind test saw them
assert (BROWS["Sö 159"]["status"], BROWS["Sö 159"]["suggested"]) == ("nytt förslag", "Traen")
assert [c["name"] for c in by["Sö 159"]["carvers"] if c["kind"] == "S"] == ["Gunnlev 1", "Rörik", "Gudmund"]
assert (BROWS["U 1031"]["status"], BROWS["U 1031"]["suggested"], BROWS["U 1031"]["truth"]) == ("nytt förslag", "Åsmund", ["Vigmund", "Åsmund"])
assert (BROWS["U 844"]["status"], BROWS["U 844"]["suggested"], BROWS["U 844"]["truth"]) == ("nytt förslag", "Fot 2", ["Fot 2"])

# The model in R (r/attribution.R): its own test on stones it had not seen
REL = {x["threshold"]: x for x in A["calibration"]["reliability"]}
assert (REL[0.7]["n"], REL[0.7]["accuracy"]) == (20, 1)
BINS = {b["bin"]: b for b in A["calibration"]["bins"]}
b56, b67 = BINS["(0.5,0.6]"], BINS["(0.6,0.7]"]
assert (b56["n"], round(b56["n"] * b56["accuracy"]), b67["n"], round(b67["n"] * b67["accuracy"])) == (67, 61, 61, 60)
assert (A["n_train"], len(A["carvers"]), A["near_km"], A["open_set"]["threshold"]) == (497, 18, 25, 0.35)
PRED = {p["signum"]: p for p in A["predictions"]}
assert len(PRED) == A["n_predictions"] == 923
free = [p for p in A["predictions"] if p["agrees_rundata"] is None]  # no carver at all in Rundata
assert len(free) == 810 and max(free, key=lambda p: p["p"])["signum"] == "U 1026"

# The spelling (src/orthography.py): leave-one-out on the inscriptions of the carvers it knows
m = orthography_model()
EV = m.evaluate()
PC = EV["per_carver"]
right = lambda c: round(PC[c]["precision"] * PC[c]["predicted"])  # noqa: E731
assert (EV["n_inscriptions"], EV["n_carvers"], pr(EV["top1_accuracy"])) == (459, 27, 61)
assert (right("Traen"), PC["Traen"]["predicted"], right("Fot 2"), PC["Fot 2"]["predicted"]) == (14, 16, 36, 56)
assert m.rank_carvers("U 1026", 3)["n_words"] < 8  # too short for the spelling once the names are out
UNIVERSE = model_carvers(m) | set(A["carvers"])
assert len(UNIVERSE) == 28
home = {c: Counter(province(r) for r in stones if c in certain_carvers(r)) for c in UNIVERSE}
assert sum(bool(h) and h.most_common(1)[0][0] in ("U", "Sö") for h in home.values()) >= 26  # nearly all in U and Sö

# The suggestions (analysplan 5): the ten strongest where the model does not say "kanske någon annan"
R = {r["signum"]: r for r in N["rows"]}
TOP10 = [r for r in N["rows"] if r["someone_else"] is not True][:10]
TOP5 = ["Sö 62", "Sö 158", "U 1026", "U 843", "Sö 72"]
assert [r["signum"] for r in TOP10] == TOP5 + ["U 482", "Sö 70", "Sö 137", "U 136", "Sö 335"]
assert [r["signum"] for r in N["rows"][:5]] == TOP5  # the five strongest overall
skipped = [r["signum"] for r in N["rows"] if r["someone_else"] is True and r["strength"] > R["Sö 335"]["strength"]]
assert skipped == ["U 854", "U 957"]
assert (sum(r["someone_else"] is True for r in N["rows"]), sum(r["lost"] for r in N["rows"])) == (17, 18)
CARV, PROVN = Counter(r["carver"] for r in N["rows"]), Counter(r["province"] for r in N["rows"])
assert CARV.most_common(4) == [("Öpir 1", 30), ("Fot 2", 18), ("Traen", 15), ("Balle", 14)]
assert PROVN == Counter({"U": 65, "Sö": 20, "Vs": 1})
assert Counter(r["crosscheck"]["status"] for r in N["rows"]) == Counter({"saknas": 75, "samma som": 9, "nämns": 1, "finns redan": 1})
assert R["U 1015"]["crosscheck"]["status"] == "finns redan" and R["U 1015"]["carver"] == "Öpir 1"
# Runor's "samma ristare som" pairs where both stones have a new suggestion: the same name every time
pairs = set()
for r in N["rows"]:
    if r["crosscheck"]["status"] == "samma som":
        for s in re.findall(r"(?:U|Sö|Vs) (?:Fv\d{4};\d+|\d+)", r["crosscheck"]["text"]):
            if s in R:
                assert R[s]["carver"] == r["carver"], (r["signum"], s)
                pairs.add(tuple(sorted((r["signum"], s))))
assert pairs == {("U 1026", "U 1027"), ("U 135", "U 136"), ("U 297", "U Fv1979;245")}
assert (R["U 1027"]["carver"], d2(R["U 1027"]["strength"])) == ("Öpir 1", "0,74")

# The five, one by one
r62, r158, r1026, r843, r72 = (R[s] for s in TOP5)
assert [(R[s]["carver"], d2(R[s]["strength"])) for s in TOP5] == [
    ("Traen", "0,88"), ("Traen", "0,87"), ("Öpir 1", "0,85"), ("Fot 2", "0,84"), ("Traen", "0,83")]
assert [R[s]["lost"] for s in TOP5] == [False, False, False, True, True]
assert all(R[s]["checks"]["område"] for s in TOP5) and not any(v is False for s in TOP5 for v in R[s]["checks"].values())
assert [R[s]["crosscheck"]["status"] for s in TOP5] == ["saknas", "nämns", "samma som", "saknas", "saknas"]
T = lambda s, k: R[s]["check_texts"][k]  # noqa: E731
# Sö 62
assert (pr(r62["model"]), r62["ortho_ranking"][0]["carver"], r62["ortho_ranking"][1]["carver"]) == (52, "Traen", "Tidkume")
assert r62["ortho_margin"] < 0.05 and r62["style"] == "Pr1" and "Kärnan (stilgrupper på minst en tiondel av stenarna: RAK, Fp, Pr1)" in T("Sö 62", "stil")
assert "Emot: diftongen ai i alla ord (monoftong: 6 % hos ristaren mot 20 % i Sö)" in T("Sö 62", "språkdrag")
assert by["Sö 62"]["transliteration"].startswith("kuni : rasti stan")
# Sö 158
assert (pr(r158["model"]), r158["ortho_ranking"][0]["carver"], r158["style"]) == (68, "Traen", "Fp")
assert "bindrunor (ja: 11 % hos ristaren mot 5 % i Sö)" in T("Sö 158", "språkdrag")
assert "Tidigare tolkad som signerad av Traen" in r158["crosscheck"]["text"] and "Fv 1981:196" in r158["crosscheck"]["references"][0]
assert "kitilhafþa står i seglet" in by["Sö 158"]["other"] and "þrottaR þiagn" in by["Sö 158"]["normalization"]
assert "Þegn of strength" in by["Sö 158"]["translation_en"] and "risti" not in by["Sö 158"]["normalization"]
# U 1026
assert (pr(r1026["model"]), r1026["ortho"], r1026["style"]) == (85, 0.0, "Pr4")
assert "skiljetecken (apostrof: 55 % hos ristaren mot 11 % i U)" in T("U 1026", "språkdrag")
assert "Kärnan (stilgrupper på minst en tiondel av stenarna: Pr4, Pr5)" in T("U 1026", "stil")
assert by["U 1026"]["other"] == "Skickligt utformad ornamentik." and by["U 1026"]["same_carver_as"] == ["U 1027"]
assert by["U 1026"]["translation_en"].startswith("Brandr and Sigviðr had the stone raised in memory of Mundi, (their) brother")
# U 843: the worked example
mp, op = r843["model"], r843["ortho"]
raw = 1 - (1 - mp) * (1 - op)
assert (pr(mp), d2(op), r843["n_words"], pr(1 - mp), pr(1 - op), pr((1 - mp) * (1 - op)), d2(raw)) == (72, "0,45", 8, 28, 55, 16, "0,84")
# The spelling's weight: Fot's smoothed precision as first choice, times 0.7 for a text of under 12 words
assert r843["ortho_ranking"][0]["carver"] == "Fot 2" and abs(op - (right("Fot 2") + 1) / (PC["Fot 2"]["predicted"] + 2) * 0.7) < 0.001
assert r843["checks"] == {"område": True, "stil": None, "språkdrag": None, "bergart": None} and abs(r843["strength"] - raw) < 0.001
assert "skiljetecken (kryss: 73 % hos ristaren mot 15 % i U)" in T("U 843", "språkdrag")
assert "diftongen au i 'och' (auk: 95 % hos ristaren mot 52 % i U)" in T("U 843", "språkdrag")
assert by["U 843"]["translation_en"].startswith("Harðgeirr and Þorsteinn (and) Mungeirr and Ketilmundr had the stone raised in memory of Ulfr, their father")
# Sö 72
assert (r72["model"], r72["model_top"], r72["ortho_ranking"][0]["carver"], d2(r72["ortho"])) == (0.0, None, "Traen", "0,83")
assert "Emot: æftiR eller at (æftiR: 15 % hos ristaren mot 42 % i Sö)" in T("Sö 72", "språkdrag")
assert "ift:iR" in by["Sö 72"]["transliteration"] and "God, help their souls" in by["Sö 72"]["translation_en"]
train = {r["signum"] for r in csv.DictReader(open(os.path.join(RUN, "attribution_oof.csv"), encoding="utf-8"))}
xy = lambda s: (by[s]["lat"], by[s]["lon"])  # noqa: E731
assert min(km(xy("Sö 72"), xy(s)) for s in train if by.get(s) and by[s].get("lat") is not None) > A["near_km"]

# Distances in the portraits, and the rule "närmaste ristare" for each stone
located = [r for r in stones if certain_carvers(r) and r.get("lat") is not None]


def nearest(signum, carver=None):
    """The nearest stones with a certain carver (of `carver`, if given): [(km, signum)]."""
    return sorted((km(xy(signum), xy(r["signum"])), r["signum"]) for r in located
                  if r["signum"] != signum and (carver is None or carver in certain_carvers(r)))


TRAEN = [r for r in stones if "Traen" in certain_carvers(r)]
assert (len(TRAEN), sum(r["district"] == "Rönö hd" for r in TRAEN), sum(r["parish"] == "Runtuna sn" for r in TRAEN)) == (22, 12, 4)
assert (by["Sö 158"]["parish"], by["Sö 158"]["district"]) == ("Runtuna sn", "Rönö hd")
n62, n158, n72 = nearest("Sö 62", "Traen")[0], nearest("Sö 158", "Traen")[0], nearest("Sö 72", "Traen")[0]
assert (n62[1], round(n62[0]), n158[1], round(n158[0], 1), n72[1], round(n72[0])) == ("Sö 49", 24, "Sö 153", 1.5, "Sö 112", 46)
a62, a158, a1026, a843 = nearest("Sö 62")[0], nearest("Sö 158")[0], nearest("U 1026")[0], nearest("U 843")[:2]
assert (a62[1], round(a62[0]), certain_carvers(by["Sö 54"])) == ("Sö 54", 8, ["Stenkil"])
assert (a158[1], round(a158[0])) == ("Sö 159", 1) and by["Sö 159"]["place"] == by["Sö 158"]["place"] == "Österberga"
assert (a1026[1], round(a1026[0]), sorted(certain_carvers(by["U 1031"])), by["U 1031"]["place"]) == ("U 1031", 2, ["Vigmund", "Åsmund"], "Hånsta")
o1026 = nearest("U 1026", "Öpir 1")[0]
assert round(o1026[0]) == 4 and by[o1026[1]]["place"] == "Tensta kyrka"
assert [s for _, s in a843] == ["U 841", "U 840"] and certain_carvers(by["U 841"]) == ["Fot 2"] and certain_carvers(by["U 840"]) == ["Öpir 1"]
assert by["U 841"]["place"] == by["U 840"]["place"] == "Dalby kyrka" and round(a843[0][0]) == 1
GAP_M = round((a843[1][0] - a843[0][0]) * 1000 / 5) * 5
assert GAP_M == 15
assert "Sö 158" not in BROWS and by["U 844"]["place"].startswith("Viggby")

# ---- bilderna ----------------------------------------------------------------------------------------


def bild(fil: str, alt: str, text: str, max_w: int = 1600) -> str:
    path = os.path.join(BILDER, fil)
    assert os.path.exists(path), f"skärmbild saknas: {fil}"
    im = Image.open(path).convert("RGB")
    if im.width > max_w:
        im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
    out = io.BytesIO()
    im.save(out, "PNG", optimize=True)
    return f"![{alt}]({blog_figures.freeze(out.getvalue())})\n{text}"


FILES = commons.wikidata_files(["Sö 62", "Sö 158", "U 1026", "U 843", "Sö 72"])
INFO = commons.commons_info([FILES[s] for s in ("Sö 62", "Sö 158", "U 1026", "U 843")])
# Wikidata's picture for Sö 72 shows Sö 11 at Gryts kyrka; the lost stone has no photograph, so none is used
assert FILES["Sö 72"].startswith("Sö 11")
CREDIT = {"Sö 62": ("Berig", "CC BY 3.0"), "Sö 158": ("Berig", "CC BY-SA 3.0"), "U 1026": ("Uwe Zimmermann", "CC BY-SA 3.0"),
          "U 843": ("Johan Hadorph och Sven Bierkenius", "CC0")}


def photo(signum: str, text: str, kind: str = "Foto") -> str:
    img = {**INFO[FILES[signum]], "signum": signum}
    assert (img["author"], img["licence"]) == CREDIT[signum], (signum, img["author"], img["licence"])
    cap = commons.caption(img, "sv")
    assert cap.startswith(f"{signum}. Foto: ")
    return f"![Runstenen {signum}]({img['thumb']})\n{text} {kind}: {cap[len(signum) + 8:]}"


IMG01 = bild("01_stenar_utan_ristare.png", "Stenöversiktens diagram över stenarna utan ristare",
             "Stenöversikten i Vitki: varje punkt är en runsten utan ristare i Rundata, och ju längre åt höger, desto starkare "
             "pekar beläggen mot en ristare. Mörkblått är nytt förslag (styrka minst 0,5), ljusblått möjligt förslag (minst 0,3). "
             "Skärmbild ur Vitki.")
IMG02 = bild("02_u843_panel.png", "U 843 i Stenöversikten",
             "U 843 i Stenöversikten. Styrkan 0,84 kommer ur modellen (0,72) och stavningen (0,45); av kontrollerna går bara "
             "området att pröva (Om ✓). Skärmbild ur Vitki.")
IMG04 = bild("04_kanske_nagon_annan.png", "Modellens kanske någon annan",
             "Statistik → Vem ristade? i Vitki: när ingen av modellens ristare får minst 35 procent säger den kanske någon "
             "annan. Skärmbild ur Vitki.")
IMG05 = bild("05_topplista.png", "Topplistan i Stenöversikten",
             "Topplistan i Stenöversikten: alla statusar utom nytt förslag avstängda, tabellen sorterad efter förslagets "
             "styrka. Rundata och Stöd är tomma, eftersom stenarna saknar ristare i Rundata. Skärmbild ur Vitki.")
PH62 = photo("Sö 62", "Sö 62 vid Hässlö i Lerbo socken, Södermanland.")
PH158 = photo("Sö 158", "Skeppet på Sö 158 vid Österberga i Runtuna socken: bindrunorna bildar masten.")
PH1026 = photo("U 1026", "U 1026 vid Lena kyrka i Uppland.")
PH843 = photo("U 843", "U 843 vid Hässle i Dalby socken, tecknad före 1693. Stenen är försvunnen.", "Teckning")

CHART = f""":::chart Andel rätt i blindprovet: Vitki mot regeln ”närmaste ristare”
# Nytt förslag ({NY['n']} stenar)
+Vitki | {pr(NY['precision'])} | {NY['right']} av {NY['n']}
Närmaste ristare | {pr(NY['nearest_precision'])} | {NY['nearest_right']} av {NY['n']}
# Nytt förslag, bara signerade stenar ({SI['n']} stenar)
+Vitki | {pr(SI['precision'])} | {SI['right']} av {SI['n']}
Närmaste ristare | {pr(SI['nearest_precision'])} | {SI['nearest_right']} av {SI['n']}
# Möjligt förslag ({MO['n']} stenar)
+Vitki | {pr(MO['precision'])} | {MO['right']} av {MO['n']}
Närmaste ristare | {pr(MO['nearest_precision'])} | {MO['nearest_right']} av {MO['n']}
Källa: Vitkis blindprov på {B['n_attributed']} runstenar med säker ristare i Samnordisk runtextdatabas 3.1; facit är Rundatas ristare.
:::"""

XC = {"saknas": "ingen ristare", "samma som": None}


def runor(r):
    st = r["crosscheck"]["status"]
    if st == "samma som":
        return "samma ristare som " + re.search(r"som (.+?) \(namnlös\)", r["crosscheck"]["text"]).group(1)
    return XC[st]


SHOWN = {"Fot 2": "Fot", "Öpir 1": "Öpir", "Traen": "Traen-gruppen"}
# A list, not a table: the article page (components/BlogBody.tsx) has no tables
NEXT = "\n".join(f"- **{r['signum']} vid {r['place']}** – {SHOWN.get(r['carver'], r['carver'])}, styrka {d2(r['strength'])} "
                 f"(modellen {d2(r['model'])}, stavningen {d2(r['ortho'])}). Runor 2020: {runor(r)}." for r in TOP10[5:])
assert "samma ristare som U 135" in NEXT

title = "Fem runstenar söker sin ristare"
summary = (f"Två av tre svenska runstenar saknar ristare i Rundata. Vitki går igenom alla och säger var beläggen pekar – och i "
           f"ett blindprov på {B['n_attributed']} stenar, där svaret var dolt, hade de nya förslagen rätt fyra gånger av fem. "
           "Här är de fem starkaste, och hur Vitki kommer fram till dem.")

body = f"""Vi vill nu visa en av de verkliga styrkorna i Vitki.

Av de {sv(len(stones))} svenska vikingatida runstenarna i Samnordisk runtextdatabas (Rundata) saknar {sv(N['n_unattributed'])} en ristare – två av tre. Ingen har antecknat vem som högg dem, och för de flesta kommer vi aldrig att få veta det. Men stenarna bär spår av sina ristare: hur orden stavas, vilka tecken som skiljer dem åt, ornamentiken, platsen. Det är sådana spår runologerna följer när de attribuerar en sten för hand, en i taget. Vitki följer dem för alla stenar på en gång och säger för varje sten om beläggen pekar mot någon av de ristare Vitki känner – och hur starkt.

Det syns i **Stenöversikt**. Där får {C['nytt förslag']} stenar utan ristare ett *nytt förslag*, vilket betyder att beläggen pekar starkt mot en ristare. Ytterligare {C['möjligt förslag']} får ett *möjligt förslag*. För resten, {sv(C['inget förslag'])} stenar, räcker beläggen inte till något förslag alls.

{IMG01}

Ett förslag är bara värt något om vi vet hur ofta det stämmer. Därför börjar vi inte med förslagen utan med ett prov.

## Först ett blindprov

Rundata anger en säker ristare för {B['n_attributed']} runstenar. Vi lät Vitki gå igenom dem en i taget med svaret dolt. Ristaren togs bort ur stenens uppgifter, och allt Vitki vet om ristarna – var de verkade, vilka stilgrupper och bergarter de använde, hur de stavade – räknades om utan den stenen. Sedan fick Vitki säga sitt, precis som om stenen aldrig hade haft någon ristare. Hur provet skulle gå till och vad som skulle räknas som framgång skrev vi ner och låste innan vi såg ett enda resultat.

Som motståndare valde vi den enklaste regel vi kunde komma på: gissa på ristaren bakom den närmaste stenen med känd ristare. Regeln är inte dum. Ristarna arbetade i sina hemtrakter, och grannstenen har ofta samma ristare.

{CHART}

När Vitki gav ett nytt förslag var det Rundatas ristare i {NY['right']} av {NY['n']} fall, **{pr(NY['precision'])} procent** – troligen någonstans mellan {pr(NY['ci'][0])} och {pr(NY['ci'][1])} procent. Regeln om närmaste ristare hade rätt på samma stenar i {pr(NY['nearest_precision'])} procent av fallen. Mest talande är stenarna där de två är oense: på {NY['vitki_only']} hade Vitki rätt och regeln fel, på {NY['nearest_only']} var det tvärtom. Om Vitki och regeln vore lika bra skulle en så skev fördelning nästan aldrig uppstå av en slump (p ≈ {P_MANT} · 10{str(int(P_EXP)).translate(SUP)}). Det är mindre sannolikt än att vinna högsta vinsten på Lotto tre veckor i rad.

Det hårdaste provet är de {SI['n']} signerade stenarna bland dem. Där står ristarens namn på stenen, och facit vilar alltså inte på någon forskares bedömning av stil eller stavning. Vitki hade rätt på {SI['right']} av dem, regeln på {SI['nearest_right']}. Även de svagare möjliga förslagen slog regeln, {pr(MO['precision'])} mot {pr(MO['nearest_precision'])} procent. Och ju starkare förslaget är, desto oftare stämmer det: med en styrka på minst 0,7 hade Vitki rätt i {pr(TOPSTR['precision'])} procent av fallen, {TOPSTR['right']} av {TOPSTR['n']}.

## Så resonerar Vitki

Hur kommer Vitki fram till ett förslag? Ta U 843 från Hässle i Dalby socken utanför Uppsala. Stenen är försvunnen, och vi känner den från en teckning gjord före 1693. Enligt inskriften lät fyra personer resa den efter sin far Ulv. Rundata anger ingen ristare.

{PH843}

Vitki låter två vittnen yttra sig och prövar sedan deras besked mot fyra kontroller.

Det första vittnet är en **statistisk modell** i R, en så kallad slumpskog, som har lärt sig känna igen {len(A['carvers'])} ristare på {A['n_train']} stenar med känd ristare. Den väger samman var stenen står, ornamentik, kors, stavning, skiljetecken, formler och innehåll. För U 843 säger modellen Fot – Fot 2 i Rundata – med {pr(mp)} procent. Modellen är försiktig av sig. När den prövades på stenar den inte hade fått se, sa den minst 70 procent om {REL[0.7]['n']} stenar och hade rätt om alla {REL[0.7]['n']}.

Det andra vittnet är **stavningen**. Vitki jämför stenens text, med namnen bortplockade, med hur varje ristare brukar stava och sätta skiljetecken. U 843 liknar Fots stenar mest. När stavningen sätter Fot först har den haft rätt {right('Fot 2')} gånger av {PC['Fot 2']['predicted']}, knappt två gånger av tre. Eftersom texten bara har {r843['n_words']} ord räknas vittnet ned ytterligare, till {d2(op)}.

Sedan vägs vittnena ihop. Båda kan ha fel: modellen i {pr(1 - mp)} procent av fallen, stavningen i {pr(1 - op)}. Att båda har fel samtidigt, om de är oberoende av varandra, händer i {pr(1 - mp)} procent av {pr(1 - op)} procent av fallen, alltså ungefär {pr((1 - mp) * (1 - op))} procent. Det ger styrkan {d2(raw)}.

Sist kommer kontrollerna: stämmer **området**, **stilgruppen**, **språkdragen** och **bergarten** med ristarens övriga stenar? Varje kontroll som säger emot drar ned styrkan, ända till hälften om alla säger emot. För U 843 står en av Fots stenar, U 841 vid Dalby kyrka, en kilometer bort. Stilgrupp och bergart går inte att pröva för den försvunna stenen. Språkdragen får bara tala emot, aldrig för, eftersom stavningen redan har fått säga sitt. Ingenting säger emot, och styrkan blir kvar på {d2(r843['strength'])}.

{IMG02}

Formeln förutsätter att vittnena är oberoende, och det är de inte helt, för båda tittar delvis på stavningen. Därför är styrkan ett index att sortera stenarna efter, inte en sannolikhet. Det är också därför blindprovet behövdes: det visar vad indexet är värt.

## Fem stenar

Här är de fem starkaste nya förslagen. Vi har inte valt dem för hand: de är Stenöversiktens fem högsta, enligt regeln i den låsta planen.

{IMG05}

Tre av de fem gäller **Traen**, och det namnet behöver en förklaring. Rundata ger {len(TRAEN)} runstenar i Södermanland ristaren Traen, {sum(r['district'] == 'Rönö hd' for r in TRAEN)} av dem i Rönö härad. Men namnet bygger på en felläsning (Gustavson & Snædal Brink 1981, s. 196–97; Axelson 1993, s. 74), och Bianchi (2010, s. 153–55) och Kitzler Åhfeldt (2017, s. 65–66) ser stenarna som verk av flera ristare snarare än en. När Vitki säger Traen betyder det alltså att stenen hör hemma bland dessa stenar, i en lokal tradition – inte att en person som hette Traen högg den.

### 1. Sö 62 vid Hässlö – Traen-gruppen, styrka {d2(r62['strength'])}

{PH62}

Gunne reste stenen vid Hässlö i Lerbo socken efter sin son Ragne, som dog på vägen västerut. Modellen ger Traen {pr(r62['model'])} procent, och på den nivån har den haft rätt nio gånger av tio. Stavningen sätter också Traen först, men bara knappt före Tidkume, så det vittnet räknas något lägre. Stilgruppen Pr1 hör till kärnan av Traen-stenarna, och den närmaste av dem, Sö 49 vid Ene, står {round(n62[0])} kilometer bort. Ett språkdrag talar emot: stenen skriver *rasti stan* med a, där nästan alla Traen-stenar har ai, som i *ræisti stæin*. Formen med a finns bara på 6 procent av dem, mot 20 procent i landskapet. Den enkla regeln hade gissat på Stenkil, vars sten Sö 54 står närmast, {round(a62[0])} kilometer bort. Runor 2020 anger ingen ristare.

### 2. Sö 158 vid Österberga – Traen-gruppen, {d2(r158['strength'])}

{PH158}

På Sö 158 i Runtuna socken, mitt i Traen-stenarnas trakt, är ett skepp inristat. Bindrunorna bildar masten, och namnet på den döde fadern, **kitilhafþa**, står i seglet. Runor 2020 noterar att stenen tidigare tolkades som signerad av Traen. I den läsning som Rundata följer i dag, Gustavson och Snædal Brinks från 1981, finns ingen signatur: bindrunorna i masten blir i stället ett omdöme om fadern, *þrottaR þiagn*, ungefär ”en tägn av styrka”. Därför saknar stenen ristare i Rundata.

Vitki vet ingenting om den historien; Runors anmärkningar ingår inte i beläggen. Ändå hamnar stenen bland Traen-stenarna. Modellen säger Traen med {pr(r158['model'])} procent, en nivå där den har haft rätt {round(b67['n'] * b67['accuracy'])} gånger av {b67['n']}, och stavningen sätter Traen först. Den närmaste Traen-stenen, Sö 153 vid Skarpåker, står {str(round(n158[0], 1)).replace('.', ',')} kilometer bort, och {ord_(sum(r['parish'] == 'Runtuna sn' for r in TRAEN))} av gruppens stenar står i samma socken. Bindrunor finns på 11 procent av Traen-stenarna mot 5 procent i landskapet.

Men det finns en granne som komplicerar bilden. En kilometer bort, också vid Österberga, står Sö 159, signerad av Gunnlev, Rörik och Gudmund. Det är den stenen den enkla regeln hade gissat på, och i blindprovet tog Vitki just den för en Traen-sten. Vitki kan alltså inte skilja Traen-gruppen från de tre som signerade grannstenen. Det är en fråga för någon som kan jämföra stenarna själva – och det är precis den sortens fråga Vitki är bra på att ställa.

### 3. U 1026 vid Lena kyrka – Öpir, {d2(r1026['strength'])}

{PH1026}

Vid Lena kyrka i Norunda härad står två stenar på samma plats, U 1026 och U 1027. Brand och Sigvid lät resa U 1026 efter sin bror Munde, och Rundata noterar att ornamentiken i stilgruppen Pr4 är skickligt utformad.

Här talar bara modellen, eftersom texten blir för kort för stavningsjämförelsen när namnen plockas bort. Men modellen talar tydligt: Öpir (Öpir 1 i Rundata), {pr(r1026['model'])} procent. Det är det säkraste svar den ger för någon av de {len(free)} stenar som helt saknar ristare i Rundata. Pr4 hör till kärnan av Öpirs stenar, och skiljetecknet som Rundata återger med en apostrof (') finns på 55 procent av Öpirs stenar mot 11 procent i Uppland. De närmaste Öpir-stenarna står vid Tensta kyrka, {round(o1026[0])} kilometer bort. Den enkla regeln hade gissat på Åsmund och Vigmund, vars sten U 1031 vid Hånsta står {round(a1026[0])} kilometer bort. Den stenen klarade Vitki i blindprovet: med svaret dolt föreslog Vitki Åsmund.

Runor 2020 säger att U 1026 och U 1027 har samma ristare, utan att nämna något namn. Vitki ger båda samma namn: U 1027 får Öpir med styrkan {d2(R['U 1027']['strength'])}. Eftersom stenarna står på samma plats är det inget starkt prov, men olika namn hade varit en varningsklocka. En reservation till: Öpir är det namn Vitki oftast tar till. När Vitki har föreslagit Öpir i blindprovet har det stämt {PER['Öpir 1'][0]} gånger av {PER['Öpir 1'][1]}, sämst av alla ristare som Vitki har föreslagit mer än tre gånger. Så höga sannolikheter som {pr(r1026['model'])} procent har modellen dock ännu inte gett fel när den prövats.

### 4. U 843 vid Hässle – Fot, {d2(r843['strength'])}

U 843 har vi redan följt genom maskineriet. Det som gör förslaget starkt är att två vittnen som tittar på olika saker – modellen på helheten, stavningen på texten – pekar på samma ristare. Skiljetecknet × finns på 73 procent av Fots stenar mot 15 procent i Uppland, och *auk* för ”och” på 95 procent mot 52. Här hade den enkla regeln gissat likadant, men med knapp marginal: Fots sten vid Dalby kyrka står {GAP_M} meter närmare än en sten av Öpir vid samma kyrka. En annan av Fots stenar, U 844 vid Viggeby bro, fick rätt förslag i blindprovet. Runor 2020 anger ingen ristare, och för den försvunna stenen finns bara teckningen att granska.

### 5. Sö 72 vid Kesäter – Traen-gruppen, {d2(r72['strength'])}, och listans svagaste länk

Sö 72 i Västra Vingåkers socken är också försvunnen. Ulv och en person vars namn inte går att tolka reste stenen efter Styrman, och inskriften slutar med en bön: Gud hjälpe deras själ.

Här talar bara stavningen. Modellen svarar inte alls, eftersom stenen står mer än {A['near_km']} kilometer från varje sten den har tränats på. Stavningen sätter Traen först, och när den gör det har den haft rätt {right('Traen')} gånger av {PC['Traen']['predicted']}. Därav den höga siffran. Ändå är förslaget listans svagaste, av tre skäl. Den närmaste Traen-stenen, Sö 112 vid Kolunda, står {round(n72[0])} kilometer bort, långt från gruppens kärna. Ett språkdrag talar emot: stenen har *iftiR* (efter), där Traen-stenarna oftast skriver *at*; formen *æftiR* finns bara på 15 procent av dem mot 42 procent i landskapet. Och blindprovet kan inte säga något om förslag av det här slaget, eftersom ingen sten i provet fick ett nytt förslag på stavningen ensam. Sö 72 är ett förslag att pröva, inte att lita på.

## Nästa fem

{NEXT}

Två stenar som är starkare än Sö 335, U 854 och U 957, är inte med, eftersom modellen säger *kanske någon annan* om dem: ingen av dess ristare når {pr(A['open_set']['threshold'])} procent. Det gäller {sum(r['someone_else'] is True for r in N['rows'])} av de {C['nytt förslag']} nya förslagen.

U 136 vid Broby har enligt Runor 2020 samma ristare som grannstenen U 135, och Vitki ger båda Fot. Detsamma gäller U 297 och U Fv1979;245 vid Skånela kyrka. I alla {ord_(len(pairs))} par där Runor säger att två namnlösa stenar har samma ristare och båda får ett nytt förslag ger Vitki dem samma namn. För Sö 137 vid Aspa finns dessutom mätningar av huggtekniken: Kitzler Åhfeldt (2017, s. 41–46) placerar den i en annan teknikgrupp än Traen-stenen Sö 164 – ännu ett tecken på att Traen-gruppen rymmer flera händer.

Sammanlagt gäller {CARV['Öpir 1']} av de {C['nytt förslag']} nya förslagen Öpir, {CARV['Fot 2']} Fot, {CARV['Traen']} Traen-gruppen och {CARV['Balle']} Balle. Av dem står {PROVN['U']} i Uppland, {PROVN['Sö']} i Södermanland och {ord_(PROVN['Vs'])} i Västmanland. Inget av dem motsägs av Runor 2020 – men mest för att Runor inte heller anger någon ristare för dem. Bara för U 1015 anger Runor redan en ristare, och det är samma som Vitki föreslår: Öpir.

## Det Vitki inte kan

Vitki känner bara ristare med tillräckligt många stenar att lära sig av: {len(A['carvers'])} i modellen och {EV['n_carvers']} i stavningsjämförelsen, {len(UNIVERSE)} sammanlagt, nästan alla verksamma i Uppland och Södermanland. En sten av någon annan kan ändå få ett av deras namn. I blindprovet var {B['outside_universe']['n']} av de {B['n_attributed']} stenarna ristade av någon Vitki inte känner, och {B['outside_universe']['nytt']} av dem fick ändå ett nytt förslag. De kan inte bli rätt, och de är medräknade i de {pr(NY['precision'])} procenten. Modellen kan numera säga *kanske någon annan* när ingen av dess ristare passar, men den varnar också i onödan.

{IMG04}

Facit är inte heller oberoende. I Uppland och Södermanland bygger Rundatas attribueringar till stor del på Axelsons förteckning från 1993 och på äldre forskares bedömningar av stil och stavning – samma slags spår som Vitki följer. Därför är de signerade stenarna det viktigaste provet.

Södermanland är Vitkis svagare landskap. Där hade nya förslag rätt i {SO['right']} av {SO['n']} fall ({pr(SO['precision'])} procent), mot {pr(SO['nearest_precision'])} procent för den enkla regeln, och med så få stenar kan den skillnaden vara slump. Tre av de fem starkaste förslagen gäller Södermanland. När Vitki har föreslagit Traen har det stämt {PER['Traen'][0]} gånger av {PER['Traen'][1]}, och alla fyra missarna var stenar som andra ristare i landskapet har signerat, bland dem Sö 159 vid Österberga. Det passar med bilden av Traen-gruppen som en lokal tradition snarare än en hand.

Av de {C['nytt förslag']} förslagen gäller {sum(r['lost'] for r in N['rows'])} försvunna stenar. Deras text och ornamentik känner vi bara från äldre teckningar och läsningar, och ett fel där följer med in i beläggen.

Ett prov mot Runor 2020 blev för litet för att säga något. Runor anger ristare för {EX['n']} runstenar som saknar ristare i Rundata 3.1, men bara {ord_(EX['in_universe'])} av dem har en ristare som Vitki känner, och ingen av dem fick ett nytt förslag. Av {ord_(EX['n_mojligt'])} möjliga förslag stämde {'ett' if EX['agree_mojligt'] == 1 else ord_(EX['agree_mojligt'])}.

## Vad det ger oss

En modell som den här kan inte ge oss nya attribueringar. Det kan bara den som granskar stenarna. Men den ger runologin något som är svårt att få fram för hand: en arbetslista över alla Sveriges runstenar utan ristare, ordnad efter hur starkt beläggen pekar, med varje belägg synligt. Den visar var forskningens egna grupper håller ihop i datan, som när Sö 158, som en gång lästes som signerad av Traen, hamnar bland Traen-stenarna utan att Vitki vet om den läsningen. Den hittar platserna där frågan är öppen, som Österberga. Och den kan säga hur ofta den har rätt: fyra gånger av fem, i ett prov där svaret var dolt.

:::box Det viktigaste i korthet
- Vitki gör för alla runstenar på en gång det som runologer har gjort för hand, en sten i taget, och kan dessutom säga hur ofta det stämmer: i ett blindprov där svaret var dolt hade de nya förslagen rätt fyra gånger av fem, ungefär dubbelt så ofta som en gissning på närmaste kända ristare.
- De fem starkaste förslagen är hypoteser att pröva mot stenarna – ornamentik, runformer och huggteknik – inte nya attribueringar. Det svagaste, Sö 72, vilar på stavningen ensam.
- Traen är ingen person utan en grupp stenar med ett felläst namn. Ett Traen-förslag placerar en sten i en lokal tradition i Södermanland, där Vitki också är som osäkrast.
- Styrkan ligger i öppenheten: två vittnen och fyra kontroller, redovisade för varje sten, så att den som vet mer kan se exakt var resonemanget brister.
:::

:::box Så räknade vi
- Planen för provet skrevs och låstes 2026-10-21, innan blindprovet räknades (SHA-256 {SHA[:12]}…; metoddokumentationen avsnitt 1x och 14c).
- Underlag: vikingatida runstenar i Samnordisk runtextdatabas 3.1, korpusversion {FP}. Stenöversiktens regel är oförändrad: nytt förslag vid en styrka på minst 0,5, möjligt vid minst 0,3, och modellens kanske någon annan när förstavalet får under {pr(A['open_set']['threshold'])} procent.
- Blindprovet: {B['n_attributed']} stenar med säker ristare. Attribueringen doldes och ristarnas landskap räknades om utan stenen; modellens sannolikheter är korsvaliderade, alltså hämtade från modeller som inte såg stenen. En oberoende omräkning av 60 slumpvis valda stenar gav exakt samma resultat.
- Jämförelsen: ristaren bakom den närmaste andra stenen med säker ristare; står flera lika nära räknas alla deras ristare. McNemars exakta test på de stenar där Vitki och regeln är oense, och Wilsons 95-procentsintervall.
- Avvikelser från planen: R-modulen kortade listan över modellens förslag till 400 stenar. Felet rättades efter den första körningen, vilket gav en ny korpusversion och {C['nytt förslag']} i stället för 79 nya förslag; precisionen var 82 procent både före och efter. Regeln om närmaste ristare gjordes generös vid lika avstånd efter den första körningen, vilket höjde dess träff från 41 till {pr(NY['nearest_precision'])} procent och gör jämförelsen svårare för Vitki. Planen sa att de tio starkaste skulle visas med alla belägg; här visas fem i detalj och fem i tabell, och alla belägg finns i appen. Träffsäkerheten per ristare och per landskap är tillägg utöver planen.
:::

## Se själv

Öppna **Stenöversikt** i Vitki, stäng av alla statusar utom *nytt förslag* och välj *Visa som tabell*. Klicka på en sten för att se vad varje metod säger om den. Modellen och dess *kanske någon annan* finns under Statistik → *Vem ristade?*. Blindprovets alla rader finns i Vitkis öppna källkod.

## Källor

- Axelson, J. 1993. *Mellansvenska runristare. Förteckning över signerade och attribuerade inskrifter.* Runrön 5. Uppsala.
- Bianchi, M. 2010. *Runor som resurs. Vikingatida skriftkultur i Uppland och Södermanland.* Runrön 20. Uppsala.
- Gustavson, H. & Snædal Brink, T. 1981. Runfynd 1980. *Fornvännen* 76: 186–202.
- Kitzler Åhfeldt, L. 2017. *Runristare och mobilitet i Södermanland.* Stockholm.
- Runor. Riksantikvarieämbetet, utgåvan 2020.
- Samnordisk runtextdatabas, version 3.1 (ODbL).
- Bilder: se bildtexterna."""

ORD_EN = "zero one two three four five six seven eight nine ten eleven twelve".split()
ord_en = lambda n: ORD_EN[n] if n < len(ORD_EN) else str(n)  # noqa: E731
e2 = lambda x: f"{x:.2f}"  # noqa: E731


def photo_en(signum: str, text: str, kind: str = "Photo") -> str:
    img = {**INFO[FILES[signum]], "signum": signum}
    cap = commons.caption(img, "en")
    assert cap.startswith(f"{signum}. Photo: ")
    return f"![The runestone {signum}]({img['thumb']})\n{text} {kind}: {cap[len(signum) + 9:]}"


IMG01_EN = bild("01_stenar_utan_ristare.png", "The stone overview's chart of the stones without a carver",
                "The stone overview in Vitki: every dot is a runestone without a carver in Rundata, and the further right, the more "
                "strongly the evidence points to a carver. Dark blue is a new suggestion (strength at least 0.5), light blue a possible "
                "suggestion (at least 0.3). Screenshot from Vitki.")
IMG02_EN = bild("02_u843_panel.png", "U 843 in the stone overview",
                "U 843 in the stone overview. The strength 0.84 comes from the model (0.72) and the spelling (0.45); of the checks only "
                "the area can be tested (Om ✓). Screenshot from Vitki.")
IMG04_EN = bild("04_kanske_nagon_annan.png", "The model's perhaps someone else",
                "Statistics → Who carved? in Vitki: when none of the model's carvers reaches 35 per cent it says perhaps someone else. "
                "Screenshot from Vitki.")
IMG05_EN = bild("05_topplista.png", "The top list in the stone overview",
                "The top list in the stone overview: every status except new suggestion switched off, the table sorted by the "
                "suggestion's strength. Rundata and Support are empty, since the stones have no carver in Rundata. Screenshot from Vitki.")
PH62_EN = photo_en("Sö 62", "Sö 62 at Hässlö in Lerbo parish, Södermanland.")
PH158_EN = photo_en("Sö 158", "The ship on Sö 158 at Österberga in Runtuna parish: the bind-runes form the mast.")
PH1026_EN = photo_en("U 1026", "U 1026 at Lena church in Uppland.")
PH843_EN = photo_en("U 843", "U 843 at Hässle in Dalby parish, drawn before 1693. The stone is lost.", "Drawing")

CHART_EN = f""":::chart Share correct in the blind test: Vitki against the rule “nearest carver”
# New suggestion ({NY['n']} stones)
+Vitki | {pr(NY['precision'])} | {NY['right']} of {NY['n']}
Nearest carver | {pr(NY['nearest_precision'])} | {NY['nearest_right']} of {NY['n']}
# New suggestion, signed stones only ({SI['n']} stones)
+Vitki | {pr(SI['precision'])} | {SI['right']} of {SI['n']}
Nearest carver | {pr(SI['nearest_precision'])} | {SI['nearest_right']} of {SI['n']}
# Possible suggestion ({MO['n']} stones)
+Vitki | {pr(MO['precision'])} | {MO['right']} of {MO['n']}
Nearest carver | {pr(MO['nearest_precision'])} | {MO['nearest_right']} of {MO['n']}
Source: Vitki's blind test on {B['n_attributed']} runestones with a certain carver in the Scandinavian Runic-text Database 3.1; the key is Rundata's carver.
:::"""

RUNOR_EN = {"saknas": "no carver", "samma som": None}


def runor_en(r):
    st = r["crosscheck"]["status"]
    if st == "samma som":
        return "same carver as " + re.search(r"som (.+?) \(namnlös\)", r["crosscheck"]["text"]).group(1)
    return RUNOR_EN[st]


NEXT_EN = "\n".join(f"- **{r['signum']} at {r['place']}** – {SHOWN.get(r['carver'], r['carver'])}, strength {e2(r['strength'])} "
                    f"(the model {e2(r['model'])}, the spelling {e2(r['ortho'])}). Runor 2020: {runor_en(r)}." for r in TOP10[5:])

title_en = "Five Runestones Looking for Their Carver"
summary_en = (f"Two of three Swedish runestones have no carver in Rundata. Vitki goes through them all and says where the evidence "
              f"points – and in a blind test on {B['n_attributed']} stones, with the answer hidden, the new suggestions were right four "
              "times out of five. Here are the five strongest, and how Vitki arrives at them.")

body_en = f"""We now want to show one of Vitki's real strengths.

Of the {len(stones):,} Swedish Viking-age runestones in the Scandinavian Runic-text Database (Rundata), {N['n_unattributed']:,} have no carver – two out of three. No one recorded who cut them, and for most of them we will never know. But the stones carry traces of their carvers: how the words are spelled, which signs separate them, the ornament, the place. These are the traces runologists follow when they attribute a stone by hand, one at a time. Vitki follows them for all the stones at once and says, for each stone, whether the evidence points to one of the carvers Vitki knows – and how strongly.

It shows in the **stone overview**. There {C['nytt förslag']} stones without a carver get a *new suggestion*, which means that the evidence points strongly to a carver. Another {C['möjligt förslag']} get a *possible suggestion*. For the rest, {C['inget förslag']:,} stones, the evidence is not enough for any suggestion at all.

{IMG01_EN}

A suggestion is only worth something if we know how often it is right. So we do not begin with the suggestions but with a test.

## First a blind test

Rundata gives a certain carver for {B['n_attributed']} runestones. We let Vitki go through them one at a time with the answer hidden. The carver was removed from the stone's record, and everything Vitki knows about the carvers – where they worked, which style groups and rock types they used, how they spelled – was recounted without that stone. Then Vitki had its say, exactly as if the stone had never had a carver. How the test would be run and what would count as success we wrote down and locked before we saw a single result.

As the opponent we chose the simplest rule we could think of: guess the carver behind the nearest stone with a known carver. The rule is not stupid. Carvers worked in their home districts, and the neighbouring stone often has the same carver.

{CHART_EN}

When Vitki gave a new suggestion it was Rundata's carver in {NY['right']} of {NY['n']} cases, **{pr(NY['precision'])} per cent** – probably somewhere between {pr(NY['ci'][0])} and {pr(NY['ci'][1])} per cent. The nearest-carver rule was right on the same stones in {pr(NY['nearest_precision'])} per cent of cases. Most telling are the stones where the two disagree: on {NY['vitki_only']} Vitki was right and the rule wrong, on {NY['nearest_only']} it was the other way round. If Vitki and the rule were equally good, a split that lopsided would almost never arise by chance (p ≈ {P_MANT} · 10{str(int(P_EXP)).translate(SUP)}). That is less likely than winning the top prize in the lottery three weeks in a row.

The hardest test is the {SI['n']} signed stones among them. There the carver's name stands on the stone, so the key does not rest on any scholar's judgement of style or spelling. Vitki was right on {SI['right']} of them, the rule on {SI['nearest_right']}. Even the weaker possible suggestions beat the rule, {pr(MO['precision'])} against {pr(MO['nearest_precision'])} per cent. And the stronger the suggestion, the more often it holds: with a strength of at least 0.7 Vitki was right in {pr(TOPSTR['precision'])} per cent of cases, {TOPSTR['right']} of {TOPSTR['n']}.

## How Vitki reasons

How does Vitki arrive at a suggestion? Take U 843 from Hässle in Dalby parish outside Uppsala. The stone is lost, and we know it from a drawing made before 1693. According to the inscription four people had it raised in memory of their father Ulfr. Rundata gives no carver.

{PH843_EN}

Vitki lets two witnesses speak and then tests their evidence against four checks.

The first witness is a **statistical model** in R, a so-called random forest, which has learned to recognise {len(A['carvers'])} carvers on {A['n_train']} stones with a known carver. It weighs together where the stone stands, ornament, crosses, spelling, word dividers, formulas and content. For U 843 the model says Fótr – Fot 2 in Rundata – with {pr(mp)} per cent. The model is cautious by nature. When it was tested on stones it had not been allowed to see, it said at least 70 per cent about {REL[0.7]['n']} stones and was right about all {REL[0.7]['n']}.

The second witness is the **spelling**. Vitki compares the stone's text, with the names removed, with how each carver usually spells and places word dividers. U 843 most resembles Fótr's stones. When the spelling puts Fótr first it has been right {right('Fot 2')} times out of {PC['Fot 2']['predicted']}, just under two times in three. Since the text has only {r843['n_words']} words the witness is discounted further, to {e2(op)}.

Then the witnesses are weighed together. Both can be wrong: the model in {pr(1 - mp)} per cent of cases, the spelling in {pr(1 - op)}. Both being wrong at the same time, if they are independent of each other, happens in {pr(1 - mp)} per cent of {pr(1 - op)} per cent of cases, that is about {pr((1 - mp) * (1 - op))} per cent. That gives the strength {e2(raw)}.

Last come the checks: do the **area**, the **style group**, the **language traits** and the **rock type** agree with the carver's other stones? Every check that speaks against lowers the strength, down to half if all speak against. For U 843 one of Fótr's stones, U 841 at Dalby church, stands a kilometre away. Style group and rock type cannot be tested for the lost stone. The language traits may only speak against, never for, since the spelling has already had its say. Nothing speaks against, and the strength stays at {e2(r843['strength'])}.

{IMG02_EN}

The formula assumes that the witnesses are independent, and they are not entirely, because both look partly at the spelling. That is why the strength is an index for sorting the stones, not a probability. It is also why the blind test was needed: it shows what the index is worth.

## Five stones

Here are the five strongest new suggestions. We have not chosen them by hand: they are the stone overview's five highest, by the rule in the locked plan.

{IMG05_EN}

Three of the five concern **Traen**, and that name needs an explanation. Rundata gives {len(TRAEN)} runestones in Södermanland the carver Traen, {sum(r['district'] == 'Rönö hd' for r in TRAEN)} of them in Rönö hundred. But the name rests on a misreading (Gustavson & Snædal Brink 1981, pp. 196–97; Axelson 1993, p. 74), and Bianchi (2010, pp. 153–55) and Kitzler Åhfeldt (2017, pp. 65–66) see the stones as the work of several carvers rather than one. So when Vitki says Traen it means that the stone belongs among these stones, in a local tradition – not that a person called Traen cut it.

### 1. Sö 62 at Hässlö – the Traen group, strength {e2(r62['strength'])}

{PH62_EN}

Gunni raised the stone at Hässlö in Lerbo parish in memory of his son Ragni, who died on the way west. The model gives Traen {pr(r62['model'])} per cent, and at that level it has been right nine times out of ten. The spelling also puts Traen first, but only just ahead of Tidkume, so that witness counts for somewhat less. The style group Pr1 belongs to the core of the Traen stones, and the nearest of them, Sö 49 at Ene, stands {round(n62[0])} kilometres away. One language trait speaks against: the stone writes *rasti stan* with a, where nearly all Traen stones have ai, as in *ræisti stæin*. The form with a occurs on only 6 per cent of them, against 20 per cent in the province. The simple rule would have guessed Steinkell, whose stone Sö 54 stands nearest, {round(a62[0])} kilometres away. Runor 2020 gives no carver.

### 2. Sö 158 at Österberga – the Traen group, {e2(r158['strength'])}

{PH158_EN}

On Sö 158 in Runtuna parish, in the middle of the Traen stones' district, a ship is carved. The bind-runes form the mast, and the name of the dead father, **kitilhafþa**, stands in the sail. Runor 2020 notes that the stone was earlier read as signed by Traen. In the reading Rundata follows today, Gustavson and Snædal Brink's from 1981, there is no signature: the bind-runes in the mast become instead a judgement on the father, *þrottaR þiagn*, roughly “a thegn of strength”. That is why the stone has no carver in Rundata.

Vitki knows nothing of that history; Runor's notes are not part of the evidence. Still the stone ends up among the Traen stones. The model says Traen with {pr(r158['model'])} per cent, a level at which it has been right {round(b67['n'] * b67['accuracy'])} times out of {b67['n']}, and the spelling puts Traen first. The nearest Traen stone, Sö 153 at Skarpåker, stands {round(n158[0], 1)} kilometres away, and {ord_en(sum(r['parish'] == 'Runtuna sn' for r in TRAEN))} of the group's stones stand in the same parish. Bind-runes occur on 11 per cent of the Traen stones against 5 per cent in the province.

But there is a neighbour that complicates the picture. A kilometre away, also at Österberga, stands Sö 159, signed by Gunnleifr, Hrœríkr and Guðmundr. That is the stone the simple rule would have guessed, and in the blind test Vitki took that very stone for a Traen stone. So Vitki cannot separate the Traen group from the three who signed the neighbouring stone. That is a question for someone who can compare the stones themselves – and it is exactly the kind of question Vitki is good at asking.

### 3. U 1026 at Lena church – Œpir, {e2(r1026['strength'])}

{PH1026_EN}

At Lena church in Norunda hundred two stones stand on the same spot, U 1026 and U 1027. Brandr and Sigviðr had U 1026 raised in memory of their brother Mundi, and Rundata notes that the ornament in style group Pr4 is skilfully designed.

Here only the model speaks, since the text becomes too short for the spelling comparison once the names are removed. But the model speaks clearly: Œpir (Öpir 1 in Rundata), {pr(r1026['model'])} per cent. That is the surest answer it gives for any of the {len(free)} stones that have no carver at all in Rundata. Pr4 belongs to the core of Œpir's stones, and the word divider that Rundata renders with an apostrophe (') occurs on 55 per cent of Œpir's stones against 11 per cent in Uppland. The nearest Œpir stones stand at Tensta church, {round(o1026[0])} kilometres away. The simple rule would have guessed Ásmundr and Vígmundr, whose stone U 1031 at Hånsta stands {round(a1026[0])} kilometres away. That stone Vitki got right in the blind test: with the answer hidden, Vitki suggested Ásmundr.

Runor 2020 says that U 1026 and U 1027 have the same carver, without naming one. Vitki gives both the same name: U 1027 gets Œpir with the strength {e2(R['U 1027']['strength'])}. Since the stones stand on the same spot that is no strong test, but different names would have been a warning. One more reservation: Œpir is the name Vitki reaches for most often. When Vitki has suggested Œpir in the blind test it has held {PER['Öpir 1'][0]} times out of {PER['Öpir 1'][1]}, the worst of all carvers Vitki has suggested more than three times. Probabilities as high as {pr(r1026['model'])} per cent, however, the model has not yet got wrong when tested.

### 4. U 843 at Hässle – Fótr, {e2(r843['strength'])}

U 843 we have already followed through the machinery. What makes the suggestion strong is that two witnesses looking at different things – the model at the whole, the spelling at the text – point to the same carver. The divider × occurs on 73 per cent of Fótr's stones against 15 per cent in Uppland, and *auk* for “and” on 95 per cent against 52. Here the simple rule would have guessed the same, but by a narrow margin: Fótr's stone at Dalby church stands {GAP_M} metres closer than a stone by Œpir at the same church. Another of Fótr's stones, U 844 at Viggeby bridge, got the right suggestion in the blind test. Runor 2020 gives no carver, and for the lost stone there is only the drawing to examine.

### 5. Sö 72 at Kesäter – the Traen group, {e2(r72['strength'])}, and the list's weakest link

Sö 72 in Västra Vingåker parish is also lost. Ulfr and a person whose name cannot be interpreted raised the stone in memory of Styrmaðr, and the inscription ends with a prayer: may God help their souls.

Here only the spelling speaks. The model does not answer at all, since the stone stands more than {A['near_km']} kilometres from every stone it was trained on. The spelling puts Traen first, and when it does it has been right {right('Traen')} times out of {PC['Traen']['predicted']}. Hence the high figure. Still the suggestion is the list's weakest, for three reasons. The nearest Traen stone, Sö 112 at Kolunda, stands {round(n72[0])} kilometres away, far from the group's core. One language trait speaks against: the stone has *iftiR* (after), where the Traen stones mostly write *at*; the form *æftiR* occurs on only 15 per cent of them against 42 per cent in the province. And the blind test can say nothing about suggestions of this kind, since no stone in the test got a new suggestion on the spelling alone. Sö 72 is a suggestion to test, not to trust.

## The next five

{NEXT_EN}

Two stones stronger than Sö 335, U 854 and U 957, are not included, because the model says *perhaps someone else* about them: none of its carvers reaches {pr(A['open_set']['threshold'])} per cent. That applies to {sum(r['someone_else'] is True for r in N['rows'])} of the {C['nytt förslag']} new suggestions.

U 136 at Broby has, according to Runor 2020, the same carver as the neighbouring stone U 135, and Vitki gives both Fótr. The same holds for U 297 and U Fv1979;245 at Skånela church. In all {ord_en(len(pairs))} pairs where Runor says that two nameless stones have the same carver and both get a new suggestion, Vitki gives them the same name. For Sö 137 at Aspa there are also measurements of the carving technique: Kitzler Åhfeldt (2017, pp. 41–46) places it in a different technique group from the Traen stone Sö 164 – another sign that the Traen group holds several hands.

In all, {CARV['Öpir 1']} of the {C['nytt förslag']} new suggestions concern Œpir, {CARV['Fot 2']} Fótr, {CARV['Traen']} the Traen group and {CARV['Balle']} Balli. Of them {PROVN['U']} stand in Uppland, {PROVN['Sö']} in Södermanland and {ord_en(PROVN['Vs'])} in Västmanland. None of them is contradicted by Runor 2020 – but mostly because Runor gives no carver for them either. Only for U 1015 does Runor already give a carver, and it is the same one Vitki suggests: Œpir.

## What Vitki cannot do

Vitki only knows carvers with enough stones to learn from: {len(A['carvers'])} in the model and {EV['n_carvers']} in the spelling comparison, {len(UNIVERSE)} in all, nearly all active in Uppland and Södermanland. A stone by someone else can still get one of their names. In the blind test {B['outside_universe']['n']} of the {B['n_attributed']} stones were carved by someone Vitki does not know, and {B['outside_universe']['nytt']} of them still got a new suggestion. They cannot be right, and they are counted in the {pr(NY['precision'])} per cent. The model can now say *perhaps someone else* when none of its carvers fits, but it also warns unnecessarily.

{IMG04_EN}

Nor is the key independent. In Uppland and Södermanland Rundata's attributions rest largely on Axelson's list from 1993 and on earlier scholars' judgements of style and spelling – the same kind of traces Vitki follows. That is why the signed stones are the most important test.

Södermanland is Vitki's weaker province. There new suggestions were right in {SO['right']} of {SO['n']} cases ({pr(SO['precision'])} per cent), against {pr(SO['nearest_precision'])} per cent for the simple rule, and with so few stones that difference may be chance. Three of the five strongest suggestions concern Södermanland. When Vitki has suggested Traen it has held {PER['Traen'][0]} times out of {PER['Traen'][1]}, and all four misses were stones that other carvers in the province signed, among them Sö 159 at Österberga. That fits the picture of the Traen group as a local tradition rather than a hand.

Of the {C['nytt förslag']} suggestions, {sum(r['lost'] for r in N['rows'])} concern lost stones. Their text and ornament we know only from older drawings and readings, and an error there follows into the evidence.

A test against Runor 2020 was too small to say anything. Runor gives carvers for {EX['n']} runestones that have no carver in Rundata 3.1, but only {ord_en(EX['in_universe'])} of them have a carver Vitki knows, and none of them got a new suggestion. Of {ord_en(EX['n_mojligt'])} possible suggestions, {ord_en(EX['agree_mojligt'])} held.

## What it gives us

A model like this cannot give us new attributions. Only someone who examines the stones can. But it gives runology something that is hard to produce by hand: a work list of all Sweden's runestones without a carver, ordered by how strongly the evidence points, with every piece of evidence visible. It shows where scholarship's own groups hold together in the data, as when Sö 158, once read as signed by Traen, lands among the Traen stones without Vitki knowing of that reading. It finds the places where the question is open, such as Österberga. And it can say how often it is right: four times out of five, in a test where the answer was hidden.

:::box The essentials in brief
- Vitki does for all runestones at once what runologists have done by hand, one stone at a time, and can also say how often it holds: in a blind test with the answer hidden, the new suggestions were right four times out of five, about twice as often as a guess at the nearest known carver.
- The five strongest suggestions are hypotheses to test against the stones – ornament, rune forms and carving technique – not new attributions. The weakest, Sö 72, rests on the spelling alone.
- Traen is not a person but a group of stones with a misread name. A Traen suggestion places a stone in a local tradition in Södermanland, where Vitki is also at its least certain.
- The strength lies in the openness: two witnesses and four checks, reported for every stone, so that anyone who knows more can see exactly where the reasoning falls short.
:::

:::box How we counted
- The plan for the test was written and locked on 21 October 2026, before the blind test was computed (SHA-256 {SHA[:12]}…; the methods documentation, sections 1x and 14c).
- Data: Viking-age runestones in the Scandinavian Runic-text Database 3.1, corpus version {FP}. The stone overview's rule is unchanged: new suggestion at a strength of at least 0.5, possible at at least 0.3, and the model's perhaps someone else when the first choice gets under {pr(A['open_set']['threshold'])} per cent.
- The blind test: {B['n_attributed']} stones with a certain carver. The attribution was hidden and the carvers' provinces recounted without the stone; the model's probabilities are cross-validated, that is taken from models that did not see the stone. An independent recomputation of 60 randomly chosen stones gave exactly the same result.
- The comparison: the carver behind the nearest other stone with a certain carver; if several stand equally near, all their carvers count. McNemar's exact test on the stones where Vitki and the rule disagree, and Wilson's 95 per cent intervals.
- Deviations from the plan: the R module cut the list of the model's suggestions to 400 stones. The fault was corrected after the first run, which gave a new corpus version and {C['nytt förslag']} instead of 79 new suggestions; the precision was 82 per cent both before and after. The nearest-carver rule was made generous at equal distances after the first run, which raised its hit rate from 41 to {pr(NY['nearest_precision'])} per cent and makes the comparison harder for Vitki. The plan said the ten strongest would be shown with all their evidence; here five are shown in detail and five in a list, and all the evidence is in the app. The hit rates per carver and per province are additions beyond the plan.
:::

## See for yourself

Open the **stone overview** in Vitki, switch off every status except *new suggestion* and choose *Show as table*. Click a stone to see what each method says about it. The model and its *perhaps someone else* are under Statistics → *Who carved?*. All the rows of the blind test are in Vitki's open source code.

## Sources

- Axelson, J. 1993. *Mellansvenska runristare. Förteckning över signerade och attribuerade inskrifter.* Runrön 5. Uppsala.
- Bianchi, M. 2010. *Runor som resurs. Vikingatida skriftkultur i Uppland och Södermanland.* Runrön 20. Uppsala.
- Gustavson, H. & Snædal Brink, T. 1981. Runfynd 1980. *Fornvännen* 76: 186–202.
- Kitzler Åhfeldt, L. 2017. *Runristare och mobilitet i Södermanland.* Stockholm.
- Runor. Swedish National Heritage Board, 2020 edition.
- Scandinavian Runic-text Database, version 3.1 (ODbL).
- Images: see the captions."""
assert body_en.count("## ") == body.count("## ") and not re.search(r"^\|", body_en, re.M)

for word in (" han ", " hans ", " hon ", " henne ", " hennes "):  # no pronouns for carvers or the people on the stones
    assert word not in body, word
assert not re.search(r"\b(jag|mig|min)\b", body, re.I) and "beslutsunderlag" not in body.lower()  # we-voice, as the other articles
assert not re.search(r"^\|", body, re.M)  # no tables (the article page cannot show them)

out = {"slug": "fem-runstenar-soker-sin-ristare", "title": title, "summary": summary, "body": body,
       "title_en": title_en, "summary_en": summary_en, "body_en": body_en, "labels": ["Forskning", "Ristare"]}
json.dump(out, open(os.path.join(ROOT, "utdata", "blogg", "forslag.json"), "w"), ensure_ascii=False, indent=1)
print(os.path.join(ROOT, "utdata", "blogg", "forslag.json"), len(body.split()), "ord")

if {"--update", "--write", "--publish"} & set(sys.argv):
    from api.routers import blog
    col = blog.firestore().collection(blog.COLLECTION)
    now = dt.datetime.now(dt.timezone.utc)
    if "--write" in sys.argv:
        assert not [p for p in blog._all() if p.get("slug") == out["slug"]], "Adressen används redan; skriv över med --update"
        ref = col.document()
        ref.set({**out, "published": False, "month": now.strftime("%Y-%m"), "author": "Viktor Kvant",
                 "topic": "Stenöversikt|nya förslag", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    else:
        flag = "--update" if "--update" in sys.argv else "--publish"
        doc = sys.argv[sys.argv.index(flag) + 1]
        ref = col.document(doc)
        old = ref.get().to_dict()
        assert old and old.get("slug") == out["slug"], "Fel dokument"
        if flag == "--update":
            assert not old.get("published"), "Bara opublicerade utkast skrivs över härifrån"
            ref.set({**out, "updatedAt": now}, merge=True)
            print("uppdaterat utkast:", doc)
        else:
            # As Admin → Publicera (api/routers/blog.save_post): the date of publication, the month, the snapshot of the
            # patterns and IndexNow the first time; then the website (export, commit, push), as the button does
            from src import site_export
            at = blog.publication_time(None, blog._ts(old.get("publishedAt")), now)
            data = {**out, "published": True, "publishedAt": at, "month": at.strftime("%Y-%m"), "updatedAt": now}
            if not old.get("snapshot"):
                data["snapshot"] = blog._snapshot()
            ref.set(data, merge=True)
            blog._forget()
            if at <= now and not old.get("announced") and blog.indexnow(out["slug"]):
                ref.set({"announced": True}, merge=True)
            print("publicerad:", doc, at.isoformat())
            print("webbplatsen:", site_export.publish_now())
    blog._forget()
