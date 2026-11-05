"""Forskningsrapport (mallen utdata/rapporter/MALL.md, kanonisk IMRaD-/registrerad form): "Kvinnor reste runstenar oftare i Svealand än i Götaland –
31 mot 17 procent" (sv + en). Fyndet ur människomodulen (r/people.R, låst plan analysplaner/2026-10-28-manniskorna.md),
robusthetstrappan (src/robustness.py, METHODS 1v) och uppföljningen (analysplaner/2026-10-29-kvinnorna-i-svealand.md).
Alla siffror asserteras mot korpusjobbets filer (data/cache/r/corpus/<FP>/) och utdata/kvinnor_landsdel/kvinnor_landsdel.json.
Rapportversion 2 (2026-11-05): rättelser före arkiveringen i Zenodo, se ändringsloggen sist i texten.
Rapportversion 3 (2026-11-05): rättelser efter en andra, oberoende läsning av ändringarna i version 2 (korthetsrutan,
arvsläsningen i 6, rubriken för familjeseden, granskningscommit 6eae0af, det som version 2 ändrade utan att logga det).
    ../../../.venv/bin/python build_rapport_kvinnor.py [--write | --update DOC]"""
import csv
import datetime as dt
import hashlib
import json
import math
import os
import re
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_labels, r_findings, robustness  # noqa: E402
from src import r_bridge as rb  # noqa: E402

FP = "e83202e01a5e6d27"  # the corpus job the report rests on (computed 2026-10-29)
FP_FU = "3f58e9339191761e"  # the corpus version the follow-up study ran on (its plan and resultat.md name it)
FP_NOW = "3691a2c441dd03f4"  # the app's latest corpus when version 2 was written (ladder by Viking Age regions)
C = os.path.join(ROOT, "data", "cache", "r", "corpus", FP)
C_FU = os.path.join(ROOT, "data", "cache", "r", "corpus", FP_FU)
DONE = json.load(open(os.path.join(C, "done.json"), encoding="utf-8"))
assert DONE["fingerprint"] == FP and DONE["computed_at"].startswith("2026-10-29") and DONE["r_version"].startswith("R version 4.6.1")
PE = json.load(open(os.path.join(C, "people.json"), encoding="utf-8"))
ROB = json.load(open(os.path.join(C, "robustness.json"), encoding="utf-8"))
FU = json.load(open(os.path.join(ROOT, "utdata", "kvinnor_landsdel", "kvinnor_landsdel.json"), encoding="utf-8"))
PLAN_SHA = open(os.path.join(ROOT, "analysplaner", "2026-10-28-manniskorna.sha256")).read().split()[0]
FU_SHA = open(os.path.join(ROOT, "analysplaner", "2026-10-29-kvinnorna-i-svealand.sha256")).read().split()[0]
assert PLAN_SHA.startswith("ea26a388") and FU_SHA.startswith("6a03f6fd")
FU_PLAN = open(os.path.join(ROOT, "analysplaner", "2026-10-29-kvinnorna-i-svealand.md"), encoding="utf-8").read()
FU_RES = open(os.path.join(ROOT, "utdata", "kvinnor_landsdel", "resultat.md"), encoding="utf-8").read()

pc = lambda x: int(100 * x + 0.5)  # noqa: E731
d2 = lambda x: f"{x:.2f}".replace(".", ",")  # noqa: E731
d2e = lambda x: f"{x:.2f}"  # noqa: E731
sp = lambda n: f"{n:,}".replace(",", " ")  # noqa: E731
en_n = lambda n: f"{n:,}"  # noqa: E731
p3 = lambda p, en=False: (f"{p:.3f}" if en else f"{p:.3f}".replace(".", ","))  # noqa: E731
p2 = lambda p, en=False: (f"{p:.2f}" if en else f"{p:.2f}".replace(".", ","))  # noqa: E731
NUM_SV = {7: "sju", 8: "åtta"}
NUM_EN = {7: "seven", 8: "eight"}


def pfmt(p, en=False):
    if p < 0.001:
        return "p < 0.001" if en else "p < 0,001"
    s = f"{p:.3f}" if p < 0.01 else f"{p:.2f}"
    return f"p = {s}" if en else f"p = {s.replace('.', ',')}"


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


# ---- the people module's own test (r/people.R) -----------------------------------------------------------------------
assert PE["n_stones"] == 2320 and PE["plan"] == "analysplaner/2026-10-28-manniskorna.md" and PE["min_events"] == 15
T = next(t for t in PE["tests"] if t["key"] == "kvinna_landsdel")
M, HA, HB, RO = T["main"], T["halves"]["A"], T["halves"]["B"], T["robustness"]
assert T["status"] == "bekräftar" and T["replicated"] is True
assert (M["n"], M["k"]) == (1425, 391) and d2(M["or"]) == "0,46" and (d2(M["lo"]), d2(M["hi"])) == ("0,32", "0,66")
assert M["p"] < 1e-4 and 1e-4 < M["p_holm"] < 2e-4
assert (pc(M["shares_region"]["Svealand"]), pc(M["shares_region"]["Götaland"])) == (31, 17)
assert (HA["n"], HB["n"]) == (730, 695) and d2(HA["or"]) == "0,41" and d2(HB["or"]) == "0,51"
assert HA["p"] < 0.001 and 0.005 < HB["p"] < 0.01
assert (pc(HA["shares_region"]["Svealand"]), pc(HA["shares_region"]["Götaland"]), pc(HB["shares_region"]["Svealand"]), pc(HB["shares_region"]["Götaland"])) == (30, 15, 31, 19)
assert (RO["ord10"]["n"], d2(RO["ord10"]["or"])) == (951, "0,51") and RO["ord10"]["p"] < 0.005
assert (RO["kon_bestamt"]["n"], d2(RO["kon_bestamt"]["or"])) == (1390, "0,46") and RO["kon_bestamt"]["p"] < 1e-4
assert d2(RO["utan_ristare"]["or"]) == "0,46" and RO["utan_ristare"]["p"] < 1e-5
assert "or" not in RO["uppland"] and RO["son_far"] is None  # one region only: the comparison does not exist there
STATUS = {t["key"]: t["status"] for t in PE["tests"]}
assert STATUS == {"kvinna_landsdel": "bekräftar", "kvinna_tid": "indikation", "drengr_ung": "mönster att pröva",
                  "thegn_ung": "mönster att pröva", "dod_borta_ung": "bekräftar", "bro_kvinna": "ingen skillnad påvisad"}

# ---- the raw counts (follow-up study, same corpus rows) ------------------------------------------------------------------
assert FU["n_stones"] == 1425 and FU["plan"] == "analysplaner/2026-10-29-kvinnorna-i-svealand.md"
F0 = FU["tests"]["t0_huvud"]["raw"]
assert F0 == {"Svealand": {"k": 324, "n": 1013}, "Götaland": {"k": 61, "n": 370}}
RAW_SV, RAW_GO = 100 * 324 / 1013, 100 * 61 / 370
assert (round(RAW_SV), round(RAW_GO)) == (32, 16)
N_OTHER = 1425 - 1013 - 370
assert N_OTHER == 42

# ---- the robustness ladder (src/robustness.py, METHODS 1v) ------------------------------------------------------------
P = ROB["patterns"]["Människorna|people_kvinna_landsdel"]
RU = P["rungs"]
assert (P["n"], P["k"], P["direction"]) == (1383, 385, -1) and set(RU) == {"raw", "adjusted", "carver", "parish", "half_A", "half_B", "lopo"}
N_RUNGS = len(RU)
assert N_RUNGS == 7 and all(r["holds"] for r in RU.values())  # seven sensitivity analyses (version 1's abstract said eight)
assert d2(RU["raw"]["or"]) == "0,42" and d2(RU["adjusted"]["or"]) == "0,46" and d2(RU["carver"]["or"]) == "0,45" and d2(RU["parish"]["or"]) == "0,46"
assert (RU["carver"]["groups"], RU["parish"]["groups"]) == (483, 469) and not RU["carver"]["singular"] and not RU["parish"]["singular"]
assert (RU["half_A"]["n"], RU["half_B"]["n"]) == (701, 682) and d2(RU["half_A"]["or"]) == "0,43" and d2(RU["half_B"]["or"]) == "0,49"
assert RU["half_A"]["p"] < 0.001 and 0.004 < RU["half_B"]["p"] < 0.005
LO = RU["lopo"]
assert (LO["without"], LO["n"], LO["n_provinces"], LO["all_hold"], LO["flips"]) == ("U", 643, 6, True, []) and d2(LO["or"]) == "0,66" and 0.06 < LO["p"] < 0.07
EF = P["effect"]
assert (pc(EF["share_lo"]), pc(EF["share_hi"])) == (31, 17) and round(100 * EF["diff"]) == -14
DIFF_CI = [round(-100 * x) for x in EF["diff_ci"]]
assert DIFF_CI == [20, 9]
CK = P["check"]
assert CK["ok"] and CK["uniformity_p"] > 0.5 and CK["dispersion_p"] > 0.5 and CK["spatial_p"] > 0.5
CO = P["coding"]
assert (CO["n_sim"], CO["share_holds"], CO["ppv"], CO["npv"]) == (200, 1, [13, 0], [67, 0]) and d2(CO["or_median"]) == "0,47"
assert (d2(CO["or_range"][0]), d2(CO["or_range"][1])) == ("0,44", "0,55")
assert ROB["facit"]["people"]["kvinna"]["n"] == 80 and ROB["alpha"] == 0.05 and ROB["min_province"] == 30
# the common adjustment over every pattern the app shows (computed as the app computes it, today)
ANN = robustness.annotate(r_findings.corpus_patterns(rb.JOB.result(FP)), robustness.load(FP))
BY = {p["key"]: p for p in ANN}
ME = BY["people_kvinna_landsdel"]
SUMM = robustness.summary(ANN)
assert ME["confirmed"] is True and ME["q_global"] < 1e-4 and ME["ladder"]["passed"] == ME["ladder"]["tested"] == N_RUNGS
N_SHOWN, N_ALL = SUMM["n_fdr"], SUMM["all_rungs"]
assert N_SHOWN >= 40 and N_ALL == 15

# ---- the follow-up (analysplaner/2026-10-29-kvinnorna-i-svealand.md) --------------------------------------------------
FT = FU["tests"]
assert FT["t1_anka"]["raw"] == {"Svealand": {"k": 96, "n": 1013}, "Götaland": {"k": 23, "n": 370}} and FT["t1_anka"]["utslag"] == "ingen skillnad påvisad"
assert FT["t2_utan_resa"]["utslag"] == "håller" and d2(FT["t2_utan_resa"]["main"]["or"]) == "0,40"
assert FT["t3_antal"]["utslag"] == "antydan" and d2(FT["t3_antal"]["main"]["or"]) == "0,53" and round(100 * FU["attenuation_B"]) == 20
assert FT["t4_ensam"]["raw"] == {"Svealand": {"k": 137, "n": 1013}, "Götaland": {"k": 44, "n": 370}} and FT["t4_ensam"]["utslag"] == "ingen skillnad påvisad"
assert FT["t5_son"]["raw"] == {"Svealand": {"k": 107, "n": 195}, "Götaland": {"k": 13, "n": 70}} and FT["t5_son"]["utslag"] == "antydan" and d2(FT["t5_son"]["main"]["or"]) == "0,23"
assert FT["t6_far"]["raw"] == {"Svealand": {"k": 66, "n": 415}, "Götaland": {"k": 9, "n": 117}} and FT["t6_far"]["utslag"] == "antydan"
assert FT["t8_kristen"]["utslag"] == "ingen skillnad påvisad" and d2(FT["t8_kristen"]["main"]["or"]) == "1,27"
SON_SV, SON_GO = pc(107 / 195), pc(13 / 70)
assert (SON_SV, SON_GO) == (55, 19)
# Version 2: no role test holds by the follow-up plan's rule (håller = Holm < 0.05 and p < 0.05 the same way in both halves)
assert not any(FT[k]["utslag"] == "håller" for k in ("t5_son", "t6_far", "t7_bror"))
assert "**Rollerna (D):** skillnaden sitter där testen håller" in FU_PLAN and "**antydan** = Holm-p < 0,05 men" in FU_PLAN
T5, T6, T7 = FT["t5_son"], FT["t6_far"], FT["t7_bror"]
SON_M_SV, SON_M_GO = pc(T5["main"]["shares"]["Svealand"]), pc(T5["main"]["shares"]["Götaland"])
assert (SON_M_SV, SON_M_GO) == (51, 19)  # the model's shares beside the raw 55 against 19
assert p3(T5["main"]["p_holm"]) == "0,015" and (p3(T5["halves"]["A"]["p"]), p3(T5["halves"]["B"]["p"])) == ("0,058", "0,031")
assert T5["halves"]["A"]["p"] > 0.05 > T5["halves"]["B"]["p"]  # significant in one half only
assert d2(T6["main"]["or"]) == "0,37" and p2(T6["main"]["p_holm"]) == "0,12" and p2(T6["main"]["p"]) == "0,02"
assert T7["raw"] == {"Svealand": {"k": 42, "n": 179}, "Götaland": {"k": 10, "n": 88}} and T7["utslag"] == "ingen skillnad påvisad"
assert d2(T7["main"]["or"]) == "0,53" and p2(T7["main"]["p"]) == "0,16"
BRO_M_SV, BRO_M_GO = pc(T7["main"]["shares"]["Svealand"]), pc(T7["main"]["shares"]["Götaland"])
assert (BRO_M_SV, BRO_M_GO) == (22, 13)  # model shares; raw 42 of 179 against 10 of 88
T1, T4 = FT["t1_anka"]["main"], FT["t4_ensam"]["main"]
assert (d2(T1["or"]), d2(T1["lo"]), d2(T1["hi"])) == ("0,82", "0,47", "1,43")
assert (d2(T4["or"]), d2(T4["lo"]), d2(T4["hi"])) == ("0,77", "0,50", "1,18")
assert p2(FT["t8_kristen"]["main"]["p"]) == "0,16" and FT["t9_kristen_landsdel"]["main"]["p"] > 0.5
# the attenuation is measured on the log-odds scale: 1 - log OR (number of sponsors constant) / log OR (main test)
L0, L3 = FT["t0_huvud"]["main"]["logor"], FT["t3_antal"]["main"]["logor"]
assert abs((1 - L3 / L0) - FU["attenuation_B"]) < 1e-9 and d2(math.exp(L0)) == "0,46"
assert (d2(L0), d2(L3)) == ("-0,78", "-0,63")
LOG0, LOG3 = d2(L0).replace("-", "−"), d2(L3).replace("-", "−")
LOG0E, LOG3E = d2e(L0).replace("-", "−"), d2e(L3).replace("-", "−")
# the follow-up ran on corpus version 3f58e9339191761e: the same stones and the same coding as the report's version
assert FP_FU in FU_PLAN and FP_FU in FU_RES
for f in ("corpus.csv", "people.csv", "messages.csv"):
    assert sha(os.path.join(C, f)) == sha(os.path.join(C_FU, f)), f
# stones for a child (t5): where the sex of the dead can be read, nearly all commemorate sons only
_people = {r["signum"]: r for r in csv.DictReader(open(os.path.join(C_FU, "people.csv"), encoding="utf-8"))}
_child = [r for r in _people.values() if r["legible"] == "1" and r["region"] in ("Svealand", "Götaland")
          and int(r["n_resare"]) >= 1 and r["rel_barn"] == "1"]
CH_SONS = sum(1 for r in _child if int(r["doda_k"]) == 0 and int(r["doda_m"]) >= 1)
CH_KNOWN = sum(1 for r in _child if int(r["doda_k"]) > 0 or int(r["doda_m"]) >= 1)
assert (len(_child), CH_SONS, CH_KNOWN) == (195 + 70, 220, 235)

# ---- version 2: what was seen and published before the plan was locked ------------------------------------------------
_posts = {p["slug"]: p for p in json.load(open(os.path.join(ROOT, "web", "content", "articles.json"), encoding="utf-8"))["posts"]}
HON, DOT = _posts["hon-arvde-efter-sitt-barn-kvinnorna-pa-runstenarna"], _posts["dottrarna-som-runstenarna-glomde"]
assert HON["publishedAt"].startswith("2026-10-13") and DOT["publishedAt"].startswith("2026-10-14")
for line in ("+Uppland | 31 | 603 stenar", "Östergötland | 20 | 125 stenar", "Västergötland | 18 | 84 stenar", "Småland | 11 | 56 stenar"):
    assert line in HON["body"], line
assert "i Svealand är modern med på hälften av stenarna efter ett barn" in DOT["body"]
assert "391 läsbara svenska stenar har en kvinna bland resarna" in open(os.path.join(ROOT, "analysplaner", "2026-10-28-manniskorna.md"), encoding="utf-8").read()
HON_URL = "https://vitkirunor.se/artiklar/hon-arvde-efter-sitt-barn-kvinnorna-pa-runstenarna"
DOT_URL = "https://vitkirunor.se/artiklar/dottrarna-som-runstenarna-glomde"
HON_URL_EN = "https://vitkirunor.se/en/artiklar/hon-arvde-efter-sitt-barn-kvinnorna-pa-runstenarna"
DOT_URL_EN = "https://vitkirunor.se/en/artiklar/dottrarna-som-runstenarna-glomde"
assert HON["title_en"].startswith("She inherited from her child") and DOT["title_en"] == "The daughters the runestones forgot"

# ---- version 2: the hand coding behind the 80 comparable stones (src/robustness.people_facit) ---------------------------
_check = json.load(open(os.path.join(ROOT, "data", "people_check.json"), encoding="utf-8"))
_rows = {r["signum"]: r for r in csv.DictReader(open(os.path.join(C, "people.csv"), encoding="utf-8"))}
_comp = {name: [s for s in _check[name] if s in _rows and int(_rows[s]["n_resare"]) >= 1] for name in ("kodning", "kodning2")}
assert (len(_check["kodning"]), len(_check["kodning2"])) == (60, 40)
assert (len(_comp["kodning"]), len(_comp["kodning2"])) == (45, 35) and 45 + 35 == ROB["facit"]["people"]["kvinna"]["n"]
_miss2 = [s for s, h in _check["kodning2"].items() if int(int(_rows[s]["resare_k"]) > 0) != int((h.get("resare_k") or 0) > 0)]
assert _miss2 == ["U 1090"] and int(_rows["U 1090"]["n_resare"]) == 0  # the one error in the new sample is not comparable

# ---- version 2: the provinces behind the regions, as they occur in the selection --------------------------------------
_corpus = {r["signum"]: r["province"] for r in csv.DictReader(open(os.path.join(C, "corpus.csv"), encoding="utf-8"))}
_sel = [r for r in _rows.values() if r["legible"] == "1" and int(r["n_resare"]) >= 1
        and r["region"] in ("Svealand", "Götaland", "Gotland", "Norrland")]
assert len(_sel) == M["n"]  # the same selection as r/people.R
PROV = {reg: sorted({_corpus[r["signum"]] for r in _sel if r["region"] == reg}) for reg in ("Svealand", "Götaland")}
assert PROV == {"Svealand": sorted(["U", "Sö", "Vs", "Nä", "Gs", "Vr"]), "Götaland": sorted(["Ög", "Vg", "Sm", "Öl", "Bo"])}, PROV
assert not {"Hr", "Ds", "D"} & set(_corpus[r["signum"]] for r in _sel)  # Hr in src/messages.REGION is Härjedalen, not Halland
SV_PROV = "Uppland, Södermanland, Västmanland, Närke, Gästrikland och Värmland (Dalarna har inga stenar i urvalet)"
GO_PROV = "Östergötland, Västergötland, Småland, Öland och Bohuslän (Dalsland har inga stenar i urvalet)"
EN_SV_PROV = "Uppland, Södermanland, Västmanland, Närke, Gästrikland and Värmland (Dalarna has no stones in the selection)"
EN_GO_PROV = "Östergötland, Västergötland, Småland, Öland and Bohuslän (Dalsland has no stones in the selection)"
# Halland's runestones are DR signa in Rundata, i.e. counted as Denmark
_rd = json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))
assert _rd["meta"]["license"] == "ODbL-1.0 / DbCL-1.0"
assert {"DR 352", "DR 353", "DR 354"} <= {r["signum"] for r in _rd["inscriptions"] if "Halland" in json.dumps(r, ensure_ascii=False)}
assert "version 2014 med RUNDATA.xls från 2018" in open(os.path.join(ROOT, "METHODS.md"), encoding="utf-8").read()

# ---- version 2: the code state, the rerun commands, the glossary and the app's latest corpus ---------------------------
COMMIT = "5542b59"  # the last commit that changed the analysis code or its results before report version 1
if os.path.isdir(os.path.join(ROOT, ".git")):
    _last = subprocess.run(["git", "-C", ROOT, "log", "-1", "--format=%H", "--until=2026-10-31T12:53:00+01:00", "--",
                            "r/people.R", "r/robustness.R", "r/common.R", "src/people.py", "src/robustness.py",
                            "src/r_findings.py", "src/question.py", "src/messages.py", "src/r_bridge.py",
                            "utdata/kvinnor_landsdel", "data/people_check.json", "analysplaner/2026-10-28-manniskorna.md",
                            "analysplaner/2026-10-29-kvinnorna-i-svealand.md"], capture_output=True, text=True).stdout.strip()
    assert _last.startswith(COMMIT), _last
assert os.path.exists(os.path.join(ROOT, "scripts", "dev_api.sh"))
assert '@router.post("/corpus/run")' in open(os.path.join(ROOT, "api", "routers", "rstats.py"), encoding="utf-8").read()
assert 'prefix="/api/r"' in open(os.path.join(ROOT, "api", "main.py"), encoding="utf-8").read()
assert "Rscript utdata/kvinnor_landsdel/analys.R KORPUSMAPP UTMAPP" in open(os.path.join(ROOT, "utdata", "kvinnor_landsdel", "analys.R"), encoding="utf-8").read()
assert os.path.isdir(os.path.join(ROOT, "web", "src", "app", "forskningsrapporter", "begrepp"))
assert os.path.isdir(os.path.join(ROOT, "web", "src", "app", "en", "forskningsrapporter", "begrepp"))
TERMS = open(os.path.join(ROOT, "web", "src", "lib", "reportTerms.ts"), encoding="utf-8").read()
assert "DHARMa" not in TERMS and "logodds" not in TERMS.lower()  # not in the glossary: explained at first use below
GLOSS, GLOSS_EN = "https://vitkirunor.se/forskningsrapporter/begrepp", "https://vitkirunor.se/en/forskningsrapporter/begrepp"
_now = json.load(open(os.path.join(ROOT, "data", "cache", "r", "corpus", FP_NOW, "robustness.json"), encoding="utf-8"))
NOW = _now["patterns"]["Människorna|people_kvinna_landsdel"]["rungs"]
assert all(r["holds"] for r in NOW.values()) and len(NOW) == N_RUNGS
assert NOW["lopo"]["without"] == "attundaland" and d2(NOW["lopo"]["or"]) == "0,54" and NOW["lopo"]["all_hold"]

# ---- version 3: the second reading of version 2's changes ------------------------------------------------------------
# the family custom (B) is "not supported" by the follow-up plan's rule: less than half of the difference disappears
assert FU["attenuation_B"] < 0.5 and "Familjeseden (B)** stöds om" in FU_PLAN and "mer än hälften av skillnaden" in FU_PLAN
assert "**B. Seden att räkna upp familjen – stöds inte enligt regeln.**" in FU_RES
# widows (t1) and lone women (t4): no difference shown, and the intervals include 1 (so neither is ruled out)
assert all(FT[k]["utslag"] == "ingen skillnad påvisad" and FT[k]["main"]["lo"] < 1 < FT[k]["main"]["hi"] for k in ("t1_anka", "t4_ensam"))
# no test in either plan sets inheritance against the journeys for the mothers (the reading came from resultat.md, Läsning)
assert "arvsrätt" not in FU_PLAN and "Det pekar mot familjens sätt att minnas och mot arvsrätten" in " ".join(FU_RES.split())
# the builder as reviewed before archiving (version 2) is in commit 6eae0af
REVIEW_COMMIT = "6eae0af"
if os.path.isdir(os.path.join(ROOT, ".git")):
    _files = subprocess.run(["git", "-C", ROOT, "show", "--name-only", "--format=", REVIEW_COMMIT], capture_output=True,
                            text=True, check=True).stdout.split()
    assert "utdata/blogg/build/build_rapport_kvinnor.py" in _files, _files

TODAY = "2026-11-05"  # rapportversionens datum, fast i byggaren (mallen version 3); version 1: 2026-10-31
V1_DATE = "2026-10-31"
TL_SV = ("mönstret iakttogs och publicerades 2026-10-13; analysplanen låstes 2026-10-28; uppföljningens plan låstes 2026-10-29; "
         "materialet frystes 2026-10-29")
TL_EN = ("the pattern was observed and published 2026-10-13; the analysis plan was locked 2026-10-28; the follow-up plan was "
         "locked 2026-10-29; the material was frozen 2026-10-29")
ORc = f"{d2(M['or'])} (95 %-intervall {d2(M['lo'])}–{d2(M['hi'])})"
ORe = f"{d2e(M['or'])} (95 % interval {d2e(M['lo'])}–{d2e(M['hi'])})"

title = "Kvinnor reste runstenar oftare i Svealand än i Götaland – 31 mot 17 procent"
summary = ("Förregistrerad omprövning av ett tidigare iakttaget mönster. På 31 procent av Svealands runstenar med känd resare "
           "står en kvinna bland resarna, mot 17 procent i Götaland. Skillnaden håller med tid och ristare konstanta, i båda "
           "halvorna av materialet och i alla känslighetsanalyser. Någon skillnad i hur ofta änkor eller ensamma kvinnor "
           "reste stenen påvisades inte; tydligast är skillnaden där modern står med på stenen efter sitt barn, men det är en antydan, inte ett fynd.")
title_en = "Women raised runestones more often in Svealand than in Götaland – 31 against 17 percent"
summary_en = ("Pre-registered re-test of a previously observed pattern. A woman stands among the sponsors on 31 percent of "
              "Svealand's runestones with a known sponsor, against 17 percent in Götaland. The difference holds with time and "
              "carver constant, in both halves of the material and in every sensitivity analysis. No difference in how often "
              "widows or lone women raised the stone was shown; the difference is clearest where the mother appears on the stone for her child, but that "
              "is an indication, not a finding.")
SLUG = "kvinnor-bland-resarna-svealand-gotaland"
APP_VERSION = "3.0.0"  # the Vitki version the analysis was made in (tag v3.0.0 + the commits named in Data och kod), not the current one
REPORT_VERSION = 3  # the report's own version; version 1 was published 2026-10-31, version 2 on 2026-11-05
CITE_EN = f"Kvant, V. ({TODAY[:4]}). {title_en}. Research report, report version {REPORT_VERSION}; analysis in Vitki {APP_VERSION}. https://vitkirunor.se/en/forskningsrapporter/{SLUG}"


def chart(sv):
    rows = [":::chart En kvinna bland resarna, andel av stenarna med känd resare" if sv else
            ":::chart A woman among the sponsors, share of the stones with a known sponsor",
            "# " + ("Med tid och ristare konstanta" if sv else "With time and carver constant"),
            f"+Svealand | {pc(M['shares_region']['Svealand'])} | {'rått' if sv else 'raw'} {324} {'av' if sv else 'of'} {sp(1013) if sv else en_n(1013)}",
            f"Götaland | {pc(M['shares_region']['Götaland'])} | {'rått' if sv else 'raw'} {61} {'av' if sv else 'of'} 370",
            "# " + ("Halva A" if sv else "Half A"),
            f"+Svealand | {pc(HA['shares_region']['Svealand'])} | {HA['n']} {'stenar' if sv else 'stones'}",
            f"Götaland | {pc(HA['shares_region']['Götaland'])} |",
            "# " + ("Halva B" if sv else "Half B"),
            f"+Svealand | {pc(HB['shares_region']['Svealand'])} | {HB['n']} {'stenar' if sv else 'stones'}",
            f"Götaland | {pc(HB['shares_region']['Götaland'])} |",
            ("Källa: Rundata. Modellens andelar (marginaleffekter) med tid och ristare konstanta. Diagram: Vitki, efter Rundata." if sv else
             "Source: Rundata. Model shares (marginal effects) with time and carver constant. Chart: Vitki, after Rundata."),
            ":::"]
    return "\n".join(rows)


HALVES_SV = ("Halvorna bildas med samma regel, bestämd före studien, i alla projektets analyser (hela socknar växelvis inom "
             "varje landskap i ordning efter socknens medeldatering); eftersom regeln läggs på det urval som prövas skiljer sig "
             "halvornas storlek något mellan testen.")
HALVES_EN = ("The halves are formed with the same rule, fixed before the study, in all the project's analyses (whole parishes "
             "dealt alternately within each province in order of the parish's mean dating); since the rule is applied to the "
             "selection being tested, the size of the halves differs slightly between the tests.")
DHARMA_SV = ("Modellens antaganden prövas med simulerade residualer (DHARMa; Hartig 2022): modellen simulerar nya utfall för "
             "varje sten många gånger, och varje verkligt utfall jämförs med de simulerade. Proven söker en ojämn fördelning, mer "
             "variation än modellen räknar med (överspridning) och närliggande stenar som liknar varandra mer än modellen "
             "förklarar (kvarvarande rumsligt mönster).")
DHARMA_EN = ("The model's assumptions are checked with simulated residuals (DHARMa; Hartig 2022): the model simulates new "
             "outcomes for each stone many times, and each real outcome is compared with the simulated ones. The checks look for "
             "an uneven spread, more variation than the model allows for (overdispersion) and neighbouring stones that are more "
             "alike than the model explains (remaining spatial pattern).")
NOW_SV = (f"Rapporten gäller materialets version `{FP}`. Appens senaste version (`{FP_NOW}`) håller i känslighetsanalyserna "
          "vikingatidens indelning konstant (folkland, små land och tredingar, annars landskapet) och ger därför något andra "
          f"siffror: svagast utan ett område i taget är oddskvoten {d2(NOW['lopo']['or'])} (utan Attundaland) i stället för "
          f"{d2(LO['or'])} (utan Uppland). Alla steg håller där också.")
NOW_EN = (f"The report applies to the material's version `{FP}`. The app's latest version (`{FP_NOW}`) holds the Viking Age "
          "division constant in the sensitivity analyses (folklands, small lands and thirds, else the province) and so gives "
          f"slightly different figures: weakest without one area at a time, the odds ratio is {d2e(NOW['lopo']['or'])} (without "
          f"Attundaland) instead of {d2e(LO['or'])} (without Uppland). Every step holds there too.")

LOG_SV = f"""## Ändringslogg

- **Version 1, {V1_DATE}.** Första publicerade versionen.
- **Version 2, {TODAY}.** Rättelser efter en granskning inför arkiveringen i Zenodo. Huvudtestet, dess siffror och titeln är oförändrade.
- *Förregistreringen (avsnitt 2, sammanfattningen, tidslinjen).* Version 1 sade att ingen jämförelse mellan landsdelar hade gjorts innan planen låstes. Det var fel: två av mina artiklar, 13 och 14 oktober 2026, hade redan visat mönstret. Studien beskrivs nu som en förregistrerad omprövning av ett tidigare iakttaget mönster, och tidslinjen börjar 2026-10-13.
- *Rollerna (5.4, 6, 7, sammanfattningen, korthetsrutan).* Version 1 sade att skillnaden sitter i rollerna och att modern stod med på sonens sten tillsammans med fadern och syskonen. Inget rolltest håller enligt uppföljningsplanens regel: stenarna efter barn och efter fäder är antydningar, och för stenarna efter bröder, som version 1 inte redovisade, påvisades ingen skillnad. Att modern stod med tillsammans med fadern och syskonen prövades aldrig. För änkor och ensamma kvinnor står nu att ingen skillnad påvisades, med intervallen, i stället för att de är uteslutna.
- *Götalands landskap (3).* Version 1 räknade upp Halland och Dalsland. Urvalet har inga stenar därifrån; Hallands runstenar förs i Rundata till Danmark.
- *Antalet känslighetsanalyser.* Sammanfattningen sade åtta; de är sju.
- *Mindre ändringar.* Svagheten om Uppland säger nu ”när vilket landskap som helst tas bort”; de 80 handkodade stenarnas ursprung redovisas; simulerade residualer och logoddsskalan förklaras; halvornas regel; diagrammets källrad; Rundatas version och licens; absoluta länkar; commit för analysen och kommandon för att köra om den; länk till ordlistan; enhetlig röst.
- **Version 3, {TODAY}.** Rättelser efter en andra, oberoende läsning av ändringarna i version 2. Huvudtestet, dess siffror och titeln är oförändrade.
- *Korthetsrutan.* Version 2 skrev att änkor och ensamma kvinnor ”förklarar den inte”. Nu står, som i texten, att ingen skillnad påvisades för dem; intervallen utesluter dem inte.
- *Mot tidigare forskning (6).* Version 2 skrev att mönstret med modern passar med en arvsregel ”bättre än med färderna eller kristnandet”. Inget test i planerna jämför de förklaringarna; nu står att det inte är prövat om mönstret speglar arv, färderna eller något annat.
- *Seden att räkna upp familjen (5.4).* Rubriken anger nu planens utslag, stöds inte, som för de andra förklaringarna.
- *Data och kod.* Byggaren i den form den granskades inför arkiveringen anges med commit `{REVIEW_COMMIT}`.
- *Det som version 2 också ändrade utan att det stod i loggen.* Dalarna ströks ur uppräkningen av Svealands landskap (urvalet har inga stenar därifrån). Under Data och kod tillkom uppföljningens materialversion och appens senaste siffror (svagast {d2(NOW['lopo']['or'])} utan Attundaland), och meningen om en framtida DOI ströks. I den engelska texten blev ”raisers” ”sponsors” i ingressen och diagrammets rubrik."""
LOG_EN = f"""## Change log

- **Version 1, {V1_DATE}.** First published version.
- **Version 2, {TODAY}.** Corrections after a review before archiving in Zenodo. The main test, its figures and the title are unchanged.
- *The pre-registration (section 2, the abstract, the timeline).* Version 1 said that no comparison between regions had been made before the plan was locked. That was wrong: two of my articles, of 13 and 14 October 2026, had already shown the pattern. The study is now described as a pre-registered re-test of a previously observed pattern, and the timeline begins 2026-10-13.
- *The roles (5.4, 6, 7, the abstract, the essentials box).* Version 1 said that the difference lies in the roles and that the mother appeared on her son's stone together with the father and the siblings. No role test holds by the follow-up plan's rule: the stones for children and for fathers are indications, and for the stones for brothers, which version 1 did not report, no difference was shown. That the mother appeared together with the father and the siblings was never tested. For widows and lone women the text now says that no difference was shown, with the intervals, instead of that they are ruled out.
- *Götaland's provinces (3).* Version 1 listed Halland and Dalsland. The selection has no stones from them; Halland's runestones are counted as Denmark in Rundata.
- *The number of sensitivity analyses.* The abstract said eight; they are seven.
- *Minor changes.* The weakness about Uppland now says ”when any one province is removed”; the origin of the 80 hand-coded stones is stated; simulated residuals and the log-odds scale are explained; the rule for the halves; the chart's source line; Rundata's version and licence; absolute links; the commit of the analysis and the commands to rerun it; a link to the glossary; a consistent voice.
- **Version 3, {TODAY}.** Corrections after a second, independent reading of the changes in version 2. The main test, its figures and the title are unchanged.
- *The essentials box.* Version 2 said that widows and lone women ”do not explain it”. It now says, as the text does, that no difference was shown for them; the intervals do not rule them out.
- *Against earlier research (6).* Version 2 said that the mother pattern fits a rule of inheritance ”better than it fits the journeys or Christianisation”. No test in the plans compares those explanations; the text now says that whether the pattern reflects inheritance, the journeys or something else is not tested.
- *The custom of listing the family (5.4).* The heading now gives the plan's verdict, not supported, as for the other explanations.
- *Data and code.* The builder as reviewed before archiving is named with commit `{REVIEW_COMMIT}`.
- *What version 2 also changed without logging it.* Dalarna was removed from the list of Svealand's provinces (the selection has no stones from it). Data and code gained the follow-up's material version and the app's latest figures (weakest {d2e(NOW['lopo']['or'])} without Attundaland), and the sentence on a future DOI was removed. In the English text ”raisers” became ”sponsors” in the lede and the chart's heading."""

body = f"""*Viktor Kvant, oberoende forskare. Fullt prövat fynd. Rapportversion {REPORT_VERSION}, {TODAY}. Tidslinje: {TL_SV}. Analysen är gjord i Vitki {APP_VERSION}. Licens CC BY 4.0. Den engelska versionen är den kanoniska för citering: {CITE_EN}. Nyckelord: runstenar, vikingatid, kvinnor, resare, Svealand, Götaland, logistisk regression, förregistrering. Konkurrerande intressen: inga. Finansiering: ingen.*

## Sammanfattning

**Bakgrund och syfte.** Att kvinnor reste runstenar är känt, och att deras andel skiftar mellan landskapen har iakttagits förr, också i två av mina artiklar före studien. Frågan här är om skillnaden mellan Svealand och Götaland står kvar när stenarnas ålder och ristarnas egna vanor hålls konstanta, och om den tål en fast serie känslighetsanalyser.
**Material.** {sp(M['n'])} läsbara svenska runstenar från vikingatiden med minst en namngiven eller omnämnd resare, ur Samnordisk runtextdatabas (Rundata): {sp(1013)} i Svealand och {sp(370)} i Götaland. Resarnas kön är bestämt med regler som kontrollerats mot handkodning.
**Metod.** Förregistrerad omprövning med logistisk regression, landsdel och dateringsperiod som förklarande variabler och ristaren som slumpeffekt; Holm-korrigering över studiens sex test; intern replikering i två på förhand bestämda halvor av materialet; {NUM_SV[N_RUNGS]} känslighetsanalyser; justering för alla {N_SHOWN} samband som projektet redovisar (Benjamini–Hochberg).
**Resultat.** En kvinna bland resarna på {pc(M['shares_region']['Svealand'])} procent av stenarna i Svealand mot {pc(M['shares_region']['Götaland'])} procent i Götaland; oddskvot Götaland mot Svealand {ORc}, {pfmt(M['p'])}, Holm-korrigerat {pfmt(M['p_holm'])}. Samma riktning och signifikant i båda halvorna, och alla känslighetsanalyser håller; justerat för alla samband q < 0,001. En uppföljande förregistrerad studie kunde inte knyta skillnaden till någon roll. Tydligast är den på stenar efter ett barn, där modern står med på rått {SON_SV} mot {SON_GO} procent ({SON_M_SV} mot {SON_M_GO} med tid och ristare konstanta), men det testet håller bara i den ena halvan och är en antydan. För änkor, ensamma kvinnor och kristna kännetecken påvisades ingen skillnad mellan landsdelarna.
**Slutsats.** Skillnaden är stor och tål alla kontroller, men den bärs i hög grad av Uppland, och den mäter vilka som nämns bland resarna – en sed vid minnesstenarna – inte kvinnors ställning. Vad den består i är inte fastställt.

## 1. Inledning

Kvinnorna på runstenarna har varit ett eget forskningsfält sedan 1990-talet. Judith Jesch (1991) samlade vad inskrifterna säger om kvinnor, och Birgit Sawyer (2000) räknade dem som reste stenarna landskap för landskap och visade att kvinnornas andel skiftar mellan landskapen. Sawyer läste stenarna som arvshandlingar: den som reste stenen visade sig som arvinge, och där kvinnor kunde ärva syntes de oftare. Anne-Sofie Gräslund (1995) har diskuterat samma kvinnor i förhållande till kristnandet. Räkningarna i den litteraturen är råa andelar. De tar inte hänsyn till att stenarna i Svealand i genomsnitt är yngre än i Götaland, eller till att några få ristare står för många stenar i Uppland.

Syftet är att pröva om skillnaden mellan Svealand och Götaland håller när stenarnas ålder och ristarna hålls konstanta, med en modell som bestämdes innan den kördes, och att låta den gå igenom samma känslighetsanalyser som projektets alla andra samband. Studien säger inget nytt om varför kvinnor reste stenar. Den prövar om den regionala skillnaden är ett fynd att bygga vidare på.

## 2. Förregistrering: hypotes och plan

Hypotesen, modellen och tolkningsreglerna skrevs ned i en analysplan den 28 oktober 2026, innan någon modell hade körts. Planen gällde en större studie av vilka som reste runstenarna och efter vem, med sex test; detta är det första. Planen är tidsstämplad i projektets versionshantering och har kontrollsumman SHA-256 `{PLAN_SHA[:16]}…`, så att varje senare ändring skulle synas (se Data och kod).

Testet lyder i planen: utfallet är minst en kvinna bland resarna, bland stenar med minst en identifierad resare; modellen är utfall ~ landsdel + dateringsperiod + ristaren som slumpeffekt; måttet är oddskvoten Götaland mot Svealand. De sex testen korrigeras tillsammans med Holms metod. Tolkningsreglerna bestämdes i förväg: ett test *bekräftar* när Holm-p är under 0,05 och riktningen är densamma med p under 0,05 i var och en av materialets två halvor; ett *mönster att pröva* har Holm-p under 0,05 men håller inte i båda halvorna; en *indikation* har bara okorrigerat p under 0,05.

Innan planen låstes hade jag sett och publicerat en rå jämförelse mellan landskapen: i artikeln [Hon ärvde efter sitt barn]({HON_URL}) (13 oktober 2026) var en kvinna med på 31 procent av stenarna i Uppland mot 11–20 procent i Östergötland, Västergötland och Småland, och i [Döttrarna som runstenarna glömde]({DOT_URL}) (14 oktober 2026) stod att modern i Svealand är med på hälften av stenarna efter ett barn. Om kvinnorna nämner planen bara siffran {sp(391)}. Huvudtestet och rolltesten är alltså förregistrerade omprövningar av mönster som redan var sedda, på samma material.

Analyserna i avsnitt 5.1–5.3 är de som planen föreskriver. Uppföljningen i 5.4 kommer ur en andra analysplan, skriven och låst den 29 oktober 2026 (SHA-256 `{FU_SHA[:16]}…`) efter att huvudresultatet var känt. Den är alltså förregistrerad men inte en del av det första testet, och den redovisas som uppföljning. Inga explorativa analyser ingår.

## 3. Material

- **Källa.** Samnordisk runtextdatabas (Rundata), Institutionen för nordiska språk vid Uppsala universitet: translitterering, normalisering, översättning, landskap, socken, ristare och stilgruppering för varje inskrift. Materialet frystes för analysen den 29 oktober 2026.
- **Stenarna.** Alla vikingatida runstenar i de svenska landskapen: {sp(PE['n_stones'])} stenar. Bara runstenar; andra föremål med runor ingår inte. Skåne, Blekinge och Halland, som var danska under vikingatiden, förs i Rundata till Danmark och ingår inte.
- **Urval.** Stenar vars text är så bevarad att resarna kan läsas, och där minst en resare kan identifieras: {sp(M['n'])} stenar. Av dem ligger {sp(1013)} i Svealand och {sp(370)} i Götaland. {N_OTHER} ligger på Gotland eller i Norrland; de ingår i modellen som egna nivåer men jämförs inte.
- **Landsdelarna** efter dagens landskap: Svealand är {SV_PROV}; Götaland är {GO_PROV}.
- **Utfallet** är att minst en kvinna står bland resarna. Resarnas kön läses ur Rundatas engelska översättning med regler i fyra steg: först relationen (mor, dotter, hustru; son, far, bror), sedan den ensamma resarens possessiv i formeln (*her son*, *his son*), sedan ett namnlexikon som byggts ur de två första stegen, och sist namnets ändelse. Reglerna kontrollerades mot handkodning på ett nytt urval om 40 stenar som reglerna aldrig sett: 39 av 40 rätt. I de handkodade kontrollurvalen tillsammans ({ROB['facit']['people']['kvinna']['n']} stenar som kunde jämföras) var regelns ja rätt {CO['ppv'][0]} gånger av {CO['ppv'][0]} och regelns nej rätt {CO['npv'][0]} gånger av {CO['npv'][0]}. Av de {ROB['facit']['people']['kvinna']['n']} kommer {len(_comp['kodning'])} ur det första urvalet, som reglerna justerades mot; den enda felkodningen i det nya urvalet (U 1090) ingår inte bland de jämförbara. Felen finns där texten har luckor, och de missar kvinnor oftare än de lägger till.
- **Dateringsperiod** efter stenens ornamentikstil (Gräslund 2006): före 1010, 1010–1040, 1040–1070, efter 1070, och odaterad som egen grupp.
- **Ristaren.** Den ristare Rundata anger. Stenar utan känd ristare grupperas per socken.

## 4. Metod

De statistiska termerna förklaras i rapporternas ordlista: [{GLOSS}]({GLOSS}).

**4.1 Modellen.** Logistisk regression i R-paketet mgcv (R {DONE['r_version'].split()[2]}; Wood 2017): utfallet mot landsdel och dateringsperiod, med ristaren som slumpeffekt. Slumpeffekten ger varje ristare en egen nivå, så att en flitig ristares vanor inte räknas som en landsdels sed. Andelarna per landsdel är modellens marginaleffekter, det vill säga medelvärdet över stenarna som de är.

**4.2 Korrigering och replikering.** Holm-korrigering (Holm 1979) över studiens sex test. Intern replikering: testet ska hålla i var och en av materialets två halvor. {HALVES_SV} Därtill fem robusthetsprov som planen föreskriver: bara stenar med minst tio läsbara ord, bara stenar där alla resares kön är bestämt, modellen utan ristarens slumpeffekt, bara Uppland, och söner mot fäder (det sista gäller bara studiens test om de döda).

**4.3 Känslighetsanalyser.** Projektet lägger samma fasta serie känslighetsanalyser på varje samband det redovisar, oavsett vilken studie sambandet kommer ur: rå modell; modellen justerad för dateringsperiod; ristaren som slumpeffekt; socknen som slumpeffekt, för att se om skillnaden är några socknars egenhet; var halva för sig; och modellen omräknad utan ett landskap i taget (landskap med minst {ROB['min_province']} stenar). En analys med stenens läge som rumslig yta görs inte här, eftersom jämförelsen själv är geografisk. En analys håller när p är under {str(ROB['alpha']).replace('.', ',')} och riktningen är densamma som i den justerade modellen. När ett landskap tas bort krävs signifikans bara där minst två tredjedelar av stenarna är kvar; annars räcker riktningen.

Eftersom projektet prövar många samband justeras p-värdena dessutom tillsammans för alla {N_SHOWN} samband som redovisas (Benjamini & Hochberg 1995). Det justerade värdet kallas q nedan. Ett samband räknas som bekräftat när det håller i båda halvorna och q är under 0,05. {DHARMA_SV} Felen i könsbestämningen prövas genom att modellen räknas om {CO['n_sim']} gånger, där varje stens ”sanna” utfall dras ur kontrollurvalets träffandelar.

Känslighetsanalyserna räknas på de {sp(P['n'])} stenarna i Svealand och Götaland. Huvudmodellen har {sp(M['n'])}, eftersom Gotland och Norrland är med som egna nivåer där. Känslighetsanalyserna använder projektets gemensamma dateringsperioder, så siffrorna kan skilja sig något från huvudtestets.

**4.4 Avvikelser från planen.** Inga för huvudplanen. I uppföljningens plan kördes ett av testen (en ensam kvinna reser stenen) först med en variabel som saknades i datafilen, vilket gav noll stenar. Variabeln räknades sedan fram exakt som planen definierar den och testet kördes om. Inget annat ändrades.

## 5. Resultat

**5.1 Huvudtestet.** Rått står en kvinna bland resarna på {324} av {sp(1013)} stenar i Svealand ({round(RAW_SV)} procent) mot {61} av {370} i Götaland ({round(RAW_GO)} procent). Med tid och ristare konstanta är andelarna {pc(M['shares_region']['Svealand'])} mot {pc(M['shares_region']['Götaland'])} procent. Oddskvoten Götaland mot Svealand är {ORc}, {pfmt(M['p'])}, Holm-korrigerat {pfmt(M['p_holm'])}. I klartext: drar man en sten på måfå i vardera landsdelen är det nästan dubbelt så vanligt att Svealandsstenen har en kvinna bland resarna, och ett så stort utslag av ren slump är så sällsynt att det inte är värt att räkna med. Halva A: {sp(HA['n'])} stenar, oddskvot {d2(HA['or'])} ({d2(HA['lo'])}–{d2(HA['hi'])}), {pfmt(HA['p'])}. Halva B: {sp(HB['n'])} stenar, oddskvot {d2(HB['or'])} ({d2(HB['lo'])}–{d2(HB['hi'])}), {pfmt(HB['p'])}. Samma riktning och signifikant i båda halvorna: testet *bekräftar* enligt planens regel.

{chart(True)}

**5.2 Planens robusthetsprov.**

- Bara stenar med minst tio läsbara ord: {sp(RO['ord10']['n'])} stenar, oddskvot {d2(RO['ord10']['or'])}, {pfmt(RO['ord10']['p'])}.
- Bara stenar där alla resares kön är bestämt: {sp(RO['kon_bestamt']['n'])} stenar, oddskvot {d2(RO['kon_bestamt']['or'])}, {pfmt(RO['kon_bestamt']['p'])}.
- Utan ristarens slumpeffekt: oddskvot {d2(RO['utan_ristare']['or'])}, {pfmt(RO['utan_ristare']['p'])}.
- Bara Uppland: kan inte prövas, eftersom jämförelsen gäller landsdelar och Uppland ligger helt i Svealand.

**5.3 Känslighetsanalyserna** ({sp(P['n'])} stenar, {P['k']} med en kvinna bland resarna). Alla {ME['ladder']['tested']} håller:

- Rå modell: oddskvot {d2(RU['raw']['or'])} ({d2(RU['raw']['ci'][0])}–{d2(RU['raw']['ci'][1])}), {pfmt(RU['raw']['p'])}.
- Justerad för dateringsperiod: {d2(RU['adjusted']['or'])} ({d2(RU['adjusted']['ci'][0])}–{d2(RU['adjusted']['ci'][1])}), {pfmt(RU['adjusted']['p'])}.
- Ristaren som slumpeffekt ({RU['carver']['groups']} ristare och sockengrupper): {d2(RU['carver']['or'])} ({d2(RU['carver']['ci'][0])}–{d2(RU['carver']['ci'][1])}), {pfmt(RU['carver']['p'])}.
- Socknen som slumpeffekt ({RU['parish']['groups']} socknar): {d2(RU['parish']['or'])} ({d2(RU['parish']['ci'][0])}–{d2(RU['parish']['ci'][1])}), {pfmt(RU['parish']['p'])}. Skillnaden är alltså inte några socknars egenhet.
- Halva A ({RU['half_A']['n']} stenar): {d2(RU['half_A']['or'])}, {pfmt(RU['half_A']['p'])}. Halva B ({RU['half_B']['n']} stenar): {d2(RU['half_B']['or'])}, {pfmt(RU['half_B']['p'])}.
- Utan ett landskap i taget ({LO['n_provinces']} landskap prövade): riktningen håller utan vart och ett av dem, och inget landskap vänder den. Svagast utan Uppland, då {LO['n']} stenar är kvar: oddskvot {d2(LO['or'])} ({d2(LO['ci'][0])}–{d2(LO['ci'][1])}), {pfmt(LO['p'])}. Utan Uppland försvinner mer än hälften av Svealands stenar, och där krävs bara riktningen.
- Skillnaden i procentenheter i den justerade modellen: {pc(EF['share_lo'])} mot {pc(EF['share_hi'])} procent, {-round(100 * EF['diff'])} enheter (troligen mellan {DIFF_CI[1]} och {DIFF_CI[0]}).
- Modellens antaganden: residualernas fördelning p = {str(round(CK['uniformity_p'], 2)).replace('.', ',')}, överspridning p = {str(round(CK['dispersion_p'], 2)).replace('.', ',')}, kvarvarande rumsligt mönster p = {str(round(CK['spatial_p'], 2)).replace('.', ',')}. Inget avvikande.
- Felen i könsbestämningen: sambandet håller i {pc(CO['share_holds'])} procent av de {CO['n_sim']} omräkningarna; oddskvotens median {d2(CO['or_median'])}, spann {d2(CO['or_range'][0])}–{d2(CO['or_range'][1])}.
- Justerat för alla {N_SHOWN} samband som projektet redovisar: q < 0,001. Sambandet är ett av {N_ALL} som håller i alla känslighetsanalyser.

**5.4 Uppföljning (andra förregistrerade planen).** Fem förhandsbestämda förklaringar till vad skillnaden består i, prövade med samma modell och med uppföljningsplanens tolkningsregler: ett test *håller* när Holm-p är under 0,05 och p är under 0,05 åt samma håll i båda halvorna; en *antydan* har Holm-p under 0,05 men håller inte i båda halvorna, eller har bara okorrigerat p under 0,05; annars är ingen skillnad påvisad. Kvinnans roll läses ur relationen till den döde: på en sten efter ett barn är hon modern, på en sten efter en far dotter eller hustru, på en sten efter en bror syster eller mor.

- **Änkor efter färderna – stöds inte enligt planens regel.** En kvinna reser stenen efter sin make: {96} av {sp(1013)} i Svealand mot {23} av {370} i Götaland, oddskvot {d2(T1['or'])} (95 %-intervall {d2(T1['lo'])}–{d2(T1['hi'])}): ingen skillnad påvisad, men intervallet utesluter inte en måttlig skillnad. Utan stenarna som nämner resor finns skillnaden mellan landsdelarna kvar och blir något större (oddskvot {d2(FT['t2_utan_resa']['main']['or'])}, håller i båda halvorna).
- **Seden att räkna upp familjen – stöds inte enligt planens regel; förklarar en femtedel.** Med antalet resare konstant: oddskvot {d2(FT['t3_antal']['main']['or'])}. {round(100 * FU['attenuation_B'])} procent av skillnaden försvinner, mätt på logoddsskalan, det vill säga i oddskvotens logaritm, där modellen är linjär: logaritmen går från {LOG0} till {LOG3}. Planens gräns var hälften.
- **Egen ställning – stöds inte enligt planens regel.** En ensam kvinna reser stenen: {137} av {sp(1013)} mot {44} av {370}, oddskvot {d2(T4['or'])} (95 %-intervall {d2(T4['lo'])}–{d2(T4['hi'])}): ingen skillnad påvisad, men intervallet rymmer också en måttlig skillnad.
- **Rollerna – en antydan, inte fastställt.** På stenar efter barn (där de dödas kön kan läsas nästan alltid söner, {CH_SONS} av {CH_KNOWN}) står modern med på {107} av {195} i Svealand ({SON_SV} procent) mot {13} av {70} i Götaland ({SON_GO} procent), oddskvot {d2(T5['main']['or'])}, Holm-korrigerat p = {p3(T5['main']['p_holm'])}, men i halvorna p = {p3(T5['halves']['A']['p'])} och {p3(T5['halves']['B']['p'])}: en antydan enligt uppföljningsplanens regel. Efter fäder står dotter eller hustru med på {66} av {415} mot {9} av {117}, oddskvot {d2(T6['main']['or'])}, Holm-korrigerat p = {p2(T6['main']['p_holm'])}: en antydan (okorrigerat p = {p2(T6['main']['p'])}). Efter bröder står syster eller mor med på {42} av {179} mot {10} av {88} ({BRO_M_SV} mot {BRO_M_GO} procent med tid och ristare konstanta), oddskvot {d2(T7['main']['or'])}, p = {p2(T7['main']['p'])}: ingen skillnad påvisad. Inget rolltest håller, så skillnaden kan enligt planen inte knytas till en roll.
- **Kristnandet – inget samband.** Ett kristet kännetecken på stenen (kors eller bön) och en kvinna bland resarna: oddskvot {d2(FT['t8_kristen']['main']['or'])}, p = {p2(FT['t8_kristen']['main']['p'])}, och ingen skillnad mellan landsdelarna.

## 6. Diskussion

**Vad fyndet säger.** Skillnaden mellan Svealand och Götaland beror inte på att Svealands stenar är yngre eller på att några ristare där ristade många stenar. Den står kvar när båda hålls konstanta, i var halva för sig och i varje känslighetsanalys. Det är en skillnad i sed, inte i befolkning: en kvinna *nämns* oftare bland dem som reste stenen i Svealand. Det säger inte att kvinnor där hade mer makt eller egendom.

**Mot tidigare forskning.** Sawyers (2000) iakttagelse att kvinnornas andel skiftar mellan landskapen står sig alltså också när ålder och ristare hålls konstanta. Uppföljningen avgör inte hennes tolkning. Någon skillnad mellan landsdelarna i hur ofta änkor eller ensamma kvinnor reste stenen påvisades inte, men de är inte uteslutna (se intervallen i 5.4). Tydligast är skillnaden där modern står med på stenen efter sitt barn, men det är en antydan enligt uppföljningsplanens regel. Sawyer läste stenarna som uttryck för arv; om mönstret med modern speglar arv, färderna eller något annat är inte prövat här. Rapporten står på huvudfyndet.

**Svagheter, i ordning efter vikt.**

1. **Uppland bär mycket.** Utan Uppland är oddskvoten {d2(LO['or'])} och intervallet når över 1. Riktningen håller när vilket landskap som helst tas bort, men den säkra skillnaden är i hög grad en skillnad mellan Uppland och Götaland.
2. **Könet är bestämt med regler.** Reglerna har fel på ungefär en sten av tjugo, oftast där texten har luckor, och de missar kvinnor oftare än de lägger till. Vore luckorna vanligare i Götaland skulle det förstärka skillnaden på fel grund. Med bara stenar med minst tio läsbara ord är oddskvoten {d2(RO['ord10']['or'])}, så det förklarar inte fyndet.
3. **Dateringen vilar på ornamentikstil.** Odaterade stenar är en egen grupp. En annan datering kunde flytta siffrorna något men knappast riktningen, eftersom den råa och den justerade modellen nästan sammanfaller.
4. **Landsdel är en grov indelning.** Att skillnaden är störst mellan Uppland och Götaland syns redan. Vad som händer i gränslandskapen är inte prövat här.

**Vad som skulle fälla fyndet.** En handkodning av könet på ett stort urval som visar fler fel i den ena landsdelen än i den andra, eller en omräkning med en annan datering där den justerade modellen inte längre håller.

## 7. Slutsats

En kvinna står bland resarna på {pc(M['shares_region']['Svealand'])} procent av Svealands runstenar med känd resare mot {pc(M['shares_region']['Götaland'])} procent av Götalands, med ålder och ristare konstanta, och skillnaden tål varje känslighetsanalys. Vad den består i är inte fastställt: tydligast är den där modern står med på stenen efter sitt barn, men det är en antydan, och inget rolltest håller. Fyndet gäller vilka som nämns bland resarna, en sed vid minnesstenarna, och är inget mått på kvinnors ställning. Rollerna kan bara prövas vidare på nytt material, och frågan varför seden skilde sig kräver annat material än inskrifternas egna ord.

## Data och kod

Analysen är gjord i Vitki {APP_VERSION}, ett öppet forskningsverktyg för runstenar ([vitkirunor.se](https://vitkirunor.se)). Analyskoden i det skick den hade när resultaten räknades är commit `{COMMIT}` (29 oktober 2026) i [https://github.com/Precatio/runes](https://github.com/Precatio/runes), den sista ändringen av analysen och dess resultat före rapportversion 1; den är Vitki {APP_VERSION} med senare ändringar. All kod, analysplanerna och resultatfilerna finns öppet där under GPL-3.0.

- Analysplanerna: `analysplaner/2026-10-28-manniskorna.md` och `analysplaner/2026-10-29-kvinnorna-i-svealand.md`, med kontrollsummor i filerna `.sha256` bredvid.
- Könsbestämningen: `src/people.py`; handkodningen: `data/people_check.json`.
- Huvudmodellen: `r/people.R`. Känslighetsanalyserna: `r/robustness.R` och `src/robustness.py` (metodbeskrivning i `METHODS.md`, avsnitt 1u och 1v). Resultaten sparas under materialets version `{FP}`.
- Uppföljningen: `utdata/kvinnor_landsdel/analys.R`, resultat och avvikelser i `utdata/kvinnor_landsdel/resultat.md`. Den kördes på materialets version `{FP_FU}`, som har samma stenar och samma kodning (identiska `corpus.csv`, `people.csv` och `messages.csv`).
- Att köra om analysen: checka ut commit `{COMMIT}`, starta analysmotorn med `scripts/dev_api.sh` och kör `curl -X POST http://localhost:8000/api/r/corpus/run`. Det räknar alla korpusanalyser och känslighetsanalyserna för den inlästa Rundata och sparar dem under `data/cache/r/corpus/<version>/` (varje R-modul körs som `Rscript --vanilla r/<modul>.R params.json utmapp`, se `METHODS.md`, avsnitt 1). Uppföljningen: `Rscript utdata/kvinnor_landsdel/analys.R data/cache/r/corpus/{FP_FU} utmapp`.
- Rapporten byggs av `utdata/blogg/build/build_rapport_kvinnor.py` (`.venv/bin/python utdata/blogg/build/build_rapport_kvinnor.py`), som läser varje siffra ur resultatfilerna och stannar om något inte stämmer; byggaren i den form den granskades inför arkiveringen finns i commit `{REVIEW_COMMIT}`.
- I Vitki visas sambandet under Statistik, Människorna, med känslighetsanalyserna steg för steg. {NOW_SV} En populär framställning av kvinnorna på stenarna finns i [Döttrarna som runstenarna glömde]({DOT_URL}) och [Hon ärvde efter sitt barn]({HON_URL}).

## Referenser

- Benjamini, Y. & Hochberg, Y. 1995. Controlling the false discovery rate: a practical and powerful approach to multiple testing. *Journal of the Royal Statistical Society B* 57 (1), s. 289–300.
- Gräslund, A.-S. 1995. Runstenskvinnorna ännu en gång. *Tor* 27, s. 459–474.
- Gräslund, A.-S. 2006. Dating the Swedish Viking-Age rune stones on stylistic grounds. I: M. Stoklund m.fl. (red.), *Runes and their Secrets: Studies in Runology*. Köpenhamn: Museum Tusculanum Press, s. 117–139.
- Hartig, F. 2022. *DHARMa: Residual diagnostics for hierarchical (multi-level/mixed) regression models*. R-paket.
- Holm, S. 1979. A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics* 6 (2), s. 65–70.
- Jesch, J. 1991. *Women in the Viking Age*. Woodbridge: Boydell.
- Kvant, V. 2026. *Vitki {APP_VERSION}: metodbeskrivning* (METHODS.md). https://github.com/Precatio/runes
- Samnordisk runtextdatabas (Rundata), version 2014 med RUNDATA.xls uppdaterad 2018. Institutionen för nordiska språk, Uppsala universitet. Open Database License 1.0 / Database Contents License 1.0.
- Sawyer, B. 2000. *The Viking-Age Rune-Stones: Custom and Commemoration in Early Medieval Scandinavia*. Oxford: Oxford University Press.
- Wood, S. N. 2017. *Generalized Additive Models: An Introduction with R*. 2 uppl. Boca Raton: Chapman & Hall/CRC.

:::box Det viktigaste i korthet
- I Svealand nämndes en kvinna bland dem som reste stenen nästan dubbelt så ofta som i Götaland, och skillnaden tål varje kontroll i studien.
- För änkor och ensamma kvinnor påvisades ingen skillnad; tydligast är skillnaden där modern står med på stenen efter sitt barn – men det är en antydan, inte ett fynd.
- Skillnaden gäller vem som nämns på minnesstenarna, inte kvinnors makt – och den bärs till stor del av Uppland.
:::

{LOG_SV}
"""

body_en = f"""*Viktor Kvant, independent researcher. Fully tested finding. Report version {REPORT_VERSION}, {TODAY}. Timeline: {TL_EN}. The analysis was made in Vitki {APP_VERSION}. Licence CC BY 4.0. This English version is the canonical one for citation: {CITE_EN}. Keywords: runestones, Viking Age, women, sponsors, Svealand, Götaland, logistic regression, pre-registration. Competing interests: none. Funding: none.*

## Abstract

**Background and aim.** That women raised runestones is known, and that their share varies between provinces has been observed before, also in two of my articles before the study. The question here is whether the difference between Svealand and Götaland remains when the age of the stones and the habits of individual carvers are held constant, and whether it withstands a fixed series of sensitivity analyses.
**Material.** {en_n(M['n'])} legible Swedish Viking-Age runestones with at least one named or mentioned sponsor, from the Scandinavian Runic-text Database (Rundata): {en_n(1013)} in Svealand and {en_n(370)} in Götaland. The sponsors' sex is determined by rules checked against hand coding.
**Method.** Pre-registered re-test with logistic regression, region and dating period as explanatory variables and the carver as a random effect; Holm correction over the study's six tests; internal replication in two pre-defined halves of the material; {NUM_EN[N_RUNGS]} sensitivity analyses; adjustment for all {N_SHOWN} associations the project reports (Benjamini–Hochberg).
**Results.** A woman among the sponsors on {pc(M['shares_region']['Svealand'])} percent of the stones in Svealand against {pc(M['shares_region']['Götaland'])} percent in Götaland; odds ratio Götaland against Svealand {ORe}, {pfmt(M['p'], True)}, Holm-corrected {pfmt(M['p_holm'], True)}. Same direction and significant in both halves, and every sensitivity analysis holds; adjusted for all associations q < 0.001. A follow-up pre-registered study could not tie the difference to any role. It is clearest on stones for a child, where the mother appears on {SON_SV} against {SON_GO} percent of the stones raw ({SON_M_SV} against {SON_M_GO} with time and carver constant), but that test holds in one half only and is an indication. For widows, lone women and Christian features no difference between the regions was shown.
**Conclusion.** The difference is large and withstands every check, but it is carried to a large degree by Uppland, and it measures who is named among the sponsors – a custom of the memorial stones – not women's standing. What it consists in is not established.

## 1. Introduction

The women of the runestones have been a field of their own since the 1990s. Judith Jesch (1991) gathered what the inscriptions say about women, and Birgit Sawyer (2000) counted the sponsors province by province and showed that the share of women varies between provinces. Sawyer read the stones as documents of inheritance: whoever raised the stone presented herself or himself as the heir, and where women could inherit they appeared more often. Anne-Sofie Gräslund (1995) has discussed the same women in relation to Christianisation. The counts in that literature are raw shares. They take no account of the fact that the stones of Svealand are on average younger than those of Götaland, or that a few carvers account for many stones in Uppland.

The aim is to test whether the difference between Svealand and Götaland holds when the age of the stones and the carvers are held constant, with a model fixed before it was run, and to let it pass the same sensitivity analyses as every other association in the project. The study says nothing new about why women raised stones. It tests whether the regional difference is a finding to build on.

## 2. Pre-registration: hypothesis and plan

The hypothesis, the model and the rules of interpretation were written down in an analysis plan on 28 October 2026, before any model had been run. The plan concerned a larger study of who raised the runestones and for whom, with six tests; this is the first. The plan is time-stamped in the project's version control and has the SHA-256 checksum `{PLAN_SHA[:16]}…`, so that any later change would show (see Data and code).

The test reads in the plan: the outcome is at least one woman among the sponsors, among stones with at least one identified sponsor; the model is outcome ~ region + dating period + carver as a random effect; the measure is the odds ratio Götaland against Svealand. The six tests are corrected together by Holm's method. The rules of interpretation were fixed in advance: a test *confirms* when Holm p is below 0.05 and the direction is the same with p below 0.05 in each of the material's two halves; a *pattern to test* has Holm p below 0.05 but does not hold in both halves; an *indication* has only uncorrected p below 0.05.

Before the plan was locked I had seen and published a raw comparison between the provinces: in the article [She inherited from her child]({HON_URL_EN}) (13 October 2026) a woman was among the sponsors on 31 percent of the stones in Uppland against 11–20 percent in Östergötland, Västergötland and Småland, and [The daughters the runestones forgot]({DOT_URL_EN}) (14 October 2026) said that in Svealand the mother is on half of the stones for a child. On the women, the plan mentions only the figure {en_n(391)}. The main test and the role tests are thus pre-registered re-tests of patterns already seen, on the same material.

The analyses in sections 5.1–5.3 are those the plan prescribes. The follow-up in 5.4 comes from a second analysis plan, written and locked on 29 October 2026 (SHA-256 `{FU_SHA[:16]}…`) after the main result was known. It is thus pre-registered but not part of the first test, and it is reported as a follow-up. No exploratory analyses are included.

## 3. Material

- **Source.** The Scandinavian Runic-text Database (Rundata), Department of Scandinavian Languages, Uppsala University: transliteration, normalisation, translation, province, parish, carver and style group for each inscription. The material was frozen for the analysis on 29 October 2026.
- **The stones.** All Viking-Age runestones in the Swedish provinces: {en_n(PE['n_stones'])} stones. Runestones only; other objects with runes are not included. Skåne, Blekinge and Halland, Danish in the Viking Age, are counted as Denmark in Rundata and are not included.
- **Selection.** Stones whose text is preserved well enough for the sponsors to be read, and where at least one sponsor can be identified: {en_n(M['n'])} stones. Of these, {en_n(1013)} lie in Svealand and {en_n(370)} in Götaland. {N_OTHER} lie on Gotland or in Norrland; they enter the model as their own levels but are not compared.
- **The regions** by today's provinces: Svealand is {EN_SV_PROV}; Götaland is {EN_GO_PROV}.
- **The outcome** is that at least one woman stands among the sponsors. The sponsors' sex is read from Rundata's English translation by rules in four steps: first the relation (mother, daughter, wife; son, father, brother), then a lone sponsor's possessive in the formula (*her son*, *his son*), then a name lexicon built from the first two steps, and last the name's ending. The rules were checked against hand coding on a new sample of 40 stones the rules had never seen: 39 of 40 right. In the hand-coded samples together ({ROB['facit']['people']['kvinna']['n']} stones that could be compared) the rule's yes was right {CO['ppv'][0]} times of {CO['ppv'][0]} and its no {CO['npv'][0]} times of {CO['npv'][0]}. Of the {ROB['facit']['people']['kvinna']['n']}, {len(_comp['kodning'])} come from the first sample, which the rules were adjusted against; the one miscoding in the new sample (U 1090) is not among the comparable stones. The errors sit where the text has gaps, and they miss women more often than they add them.
- **Dating period** by the stone's ornamental style (Gräslund 2006): before 1010, 1010–1040, 1040–1070, after 1070, and undated as a group of its own.
- **The carver.** The carver Rundata gives. Stones without a known carver are grouped by parish.

## 4. Method

The statistical terms are explained in the reports' glossary: [{GLOSS_EN}]({GLOSS_EN}).

**4.1 The model.** Logistic regression with the R package mgcv (R {DONE['r_version'].split()[2]}; Wood 2017): the outcome against region and dating period, with the carver as a random effect. The random effect gives each carver a level of their own, so that a prolific carver's habits are not counted as a region's custom. The shares per region are the model's marginal effects, that is, the average over the stones as they are.

**4.2 Correction and replication.** Holm correction (Holm 1979) over the study's six tests. Internal replication: the test must hold in each of the material's two halves. {HALVES_EN} In addition, five robustness checks prescribed by the plan: only stones with at least ten legible words, only stones where every sponsor's sex is determined, the model without the carver effect, Uppland only, and sons against fathers (the last applies only to the study's tests about the dead).

**4.3 Sensitivity analyses.** The project applies the same fixed series of sensitivity analyses to every association it reports, whatever study the association comes from: the raw model; the model adjusted for dating period; the carver as a random effect; the parish as a random effect, to see whether the difference is the peculiarity of a few parishes; each half on its own; and the model refitted without one province at a time (provinces with at least {ROB['min_province']} stones). An analysis with the stone's location as a spatial surface is not made here, since the comparison itself is geographic. An analysis holds when p is below {ROB['alpha']} and the direction is the same as in the adjusted model. When a province is removed, significance is required only where at least two thirds of the stones remain; otherwise the direction suffices.

Since the project tests many associations, the p-values are also adjusted together for all {N_SHOWN} associations reported (Benjamini & Hochberg 1995). The adjusted value is called q below. An association counts as confirmed when it holds in both halves and q is below 0.05. {DHARMA_EN} The errors in the sex determination are tested by refitting the model {CO['n_sim']} times, with each stone's ”true” outcome drawn from the hit rates in the hand-coded sample.

The sensitivity analyses are computed on the {en_n(P['n'])} stones in Svealand and Götaland. The main model has {en_n(M['n'])}, since Gotland and Norrland are included there as levels of their own. The sensitivity analyses use the project's common dating periods, so their figures can differ slightly from the main test's.

**4.4 Deviations from the plan.** None for the main plan. In the follow-up plan, one of the tests (a lone woman raises the stone) was first run with a variable that was missing from the data file, which gave zero stones. The variable was then computed exactly as the plan defines it and the test rerun. Nothing else was changed.

## 5. Results

**5.1 The main test.** Raw, a woman stands among the sponsors on {324} of {en_n(1013)} stones in Svealand ({round(RAW_SV)} percent) against {61} of {370} in Götaland ({round(RAW_GO)} percent). With time and carver constant the shares are {pc(M['shares_region']['Svealand'])} against {pc(M['shares_region']['Götaland'])} percent. The odds ratio Götaland against Svealand is {ORe}, {pfmt(M['p'], True)}, Holm-corrected {pfmt(M['p_holm'], True)}. In plain words: draw a stone at random in each region, and it is nearly twice as common that the Svealand stone has a woman among the sponsors; a swing that large from chance alone is too rare to reckon with. Half A: {en_n(HA['n'])} stones, odds ratio {d2e(HA['or'])} ({d2e(HA['lo'])}–{d2e(HA['hi'])}), {pfmt(HA['p'], True)}. Half B: {en_n(HB['n'])} stones, odds ratio {d2e(HB['or'])} ({d2e(HB['lo'])}–{d2e(HB['hi'])}), {pfmt(HB['p'], True)}. Same direction and significant in both halves: the test *confirms* by the plan's rule.

{chart(False)}

**5.2 The plan's robustness checks.**

- Only stones with at least ten legible words: {en_n(RO['ord10']['n'])} stones, odds ratio {d2e(RO['ord10']['or'])}, {pfmt(RO['ord10']['p'], True)}.
- Only stones where every sponsor's sex is determined: {en_n(RO['kon_bestamt']['n'])} stones, odds ratio {d2e(RO['kon_bestamt']['or'])}, {pfmt(RO['kon_bestamt']['p'], True)}.
- Without the carver effect: odds ratio {d2e(RO['utan_ristare']['or'])}, {pfmt(RO['utan_ristare']['p'], True)}.
- Uppland only: cannot be tested, since the comparison concerns regions and Uppland lies wholly in Svealand.

**5.3 The sensitivity analyses** ({en_n(P['n'])} stones, {P['k']} with a woman among the sponsors). All {ME['ladder']['tested']} hold:

- Raw model: odds ratio {d2e(RU['raw']['or'])} ({d2e(RU['raw']['ci'][0])}–{d2e(RU['raw']['ci'][1])}), {pfmt(RU['raw']['p'], True)}.
- Adjusted for dating period: {d2e(RU['adjusted']['or'])} ({d2e(RU['adjusted']['ci'][0])}–{d2e(RU['adjusted']['ci'][1])}), {pfmt(RU['adjusted']['p'], True)}.
- Carver as a random effect ({RU['carver']['groups']} carvers and parish groups): {d2e(RU['carver']['or'])} ({d2e(RU['carver']['ci'][0])}–{d2e(RU['carver']['ci'][1])}), {pfmt(RU['carver']['p'], True)}.
- Parish as a random effect ({RU['parish']['groups']} parishes): {d2e(RU['parish']['or'])} ({d2e(RU['parish']['ci'][0])}–{d2e(RU['parish']['ci'][1])}), {pfmt(RU['parish']['p'], True)}. The difference is not the peculiarity of a few parishes.
- Half A ({RU['half_A']['n']} stones): {d2e(RU['half_A']['or'])}, {pfmt(RU['half_A']['p'], True)}. Half B ({RU['half_B']['n']} stones): {d2e(RU['half_B']['or'])}, {pfmt(RU['half_B']['p'], True)}.
- Without one province at a time ({LO['n_provinces']} provinces tested): the direction holds without each of them, and no province turns it. Weakest without Uppland, when {LO['n']} stones remain: odds ratio {d2e(LO['or'])} ({d2e(LO['ci'][0])}–{d2e(LO['ci'][1])}), {pfmt(LO['p'], True)}. Without Uppland more than half of Svealand's stones are gone, and there only the direction is required.
- The difference in percentage points in the adjusted model: {pc(EF['share_lo'])} against {pc(EF['share_hi'])} percent, {-round(100 * EF['diff'])} points (probably between {DIFF_CI[1]} and {DIFF_CI[0]}).
- The model's assumptions: residual distribution p = {round(CK['uniformity_p'], 2)}, overdispersion p = {round(CK['dispersion_p'], 2)}, remaining spatial pattern p = {round(CK['spatial_p'], 2)}. Nothing amiss.
- Errors in the sex determination: the association holds in {pc(CO['share_holds'])} percent of the {CO['n_sim']} refits; median odds ratio {d2e(CO['or_median'])}, range {d2e(CO['or_range'][0])}–{d2e(CO['or_range'][1])}.
- Adjusted for all {N_SHOWN} associations the project reports: q < 0.001. The association is one of {N_ALL} that hold in every sensitivity analysis.

**5.4 Follow-up (second pre-registered plan).** Five pre-set explanations of what the difference consists of, tested with the same model and by the follow-up plan's rules of interpretation: a test *holds* when Holm p is below 0.05 and p is below 0.05 in the same direction in both halves; an *indication* has Holm p below 0.05 but does not hold in both halves, or has only uncorrected p below 0.05; otherwise no difference is shown. The woman's role is read from the relation to the dead: on a stone for a child she is the mother, on a stone for a father a daughter or wife, on a stone for a brother a sister or mother.

- **Widows after the journeys – not supported by the plan's rule.** A woman raises the stone for her husband: {96} of {en_n(1013)} in Svealand against {23} of {370} in Götaland, odds ratio {d2e(T1['or'])} (95 % interval {d2e(T1['lo'])}–{d2e(T1['hi'])}): no difference shown, but the interval does not rule out a moderate difference. Without the stones that mention journeys the difference between the regions remains and grows slightly (odds ratio {d2e(FT['t2_utan_resa']['main']['or'])}, holds in both halves).
- **The custom of listing the family – not supported by the plan's rule; explains a fifth.** With the number of sponsors constant: odds ratio {d2e(FT['t3_antal']['main']['or'])}. {round(100 * FU['attenuation_B'])} percent of the difference disappears, measured on the log-odds scale, that is, in the logarithm of the odds ratio, where the model is linear: the logarithm goes from {LOG0E} to {LOG3E}. The plan's limit was half.
- **A position of her own – not supported by the plan's rule.** A lone woman raises the stone: {137} of {en_n(1013)} against {44} of {370}, odds ratio {d2e(T4['or'])} (95 % interval {d2e(T4['lo'])}–{d2e(T4['hi'])}): no difference shown, but the interval also allows a moderate difference.
- **The roles – an indication, not established.** On stones for children (where the sex of the dead can be read nearly always sons, {CH_SONS} of {CH_KNOWN}) the mother appears on {107} of {195} in Svealand ({SON_SV} percent) against {13} of {70} in Götaland ({SON_GO} percent), odds ratio {d2e(T5['main']['or'])}, Holm-corrected p = {p3(T5['main']['p_holm'], True)}, but in the halves p = {p3(T5['halves']['A']['p'], True)} and {p3(T5['halves']['B']['p'], True)}: an indication by the follow-up plan's rule. On stones for fathers a daughter or wife appears on {66} of {415} against {9} of {117}, odds ratio {d2e(T6['main']['or'])}, Holm-corrected p = {p2(T6['main']['p_holm'], True)}: an indication (uncorrected p = {p2(T6['main']['p'], True)}). On stones for brothers a sister or mother appears on {42} of {179} against {10} of {88} ({BRO_M_SV} against {BRO_M_GO} percent with time and carver constant), odds ratio {d2e(T7['main']['or'])}, p = {p2(T7['main']['p'], True)}: no difference shown. No role test holds, so by the plan the difference cannot be tied to a role.
- **Christianisation – no association.** A Christian feature on the stone (cross or prayer) and a woman among the sponsors: odds ratio {d2e(FT['t8_kristen']['main']['or'])}, p = {p2(FT['t8_kristen']['main']['p'], True)}, and no difference between the regions.

## 6. Discussion

**What the finding says.** The difference between Svealand and Götaland is not due to Svealand's stones being younger or to a few carvers there carving many stones. It remains when both are held constant, in each half and in every sensitivity analysis. It is a difference in custom, not in population: a woman is more often *named* among those who raised the stone in Svealand. It does not say that women there had more power or property.

**Against earlier research.** Sawyer's (2000) observation that the share of women varies between provinces thus stands also when age and carver are held constant. The follow-up does not settle her interpretation. No difference between the regions in how often widows or lone women raised the stone was shown, but they are not ruled out (see the intervals in 5.4). The difference is clearest where the mother appears on the stone for her child, but that is an indication by the follow-up plan's rule. Sawyer read the stones as statements of inheritance; whether the mother pattern reflects inheritance, the journeys or something else is not tested here. The report rests on the main finding.

**Weaknesses, in order of weight.**

1. **Uppland carries much.** Without Uppland the odds ratio is {d2e(LO['or'])} and the interval reaches above 1. The direction holds when any one province is removed, but the certain difference is to a large degree a difference between Uppland and Götaland.
2. **Sex is determined by rules.** The rules err on about one stone in twenty, mostly where the text has gaps, and they miss women more often than they add them. If gaps were more common in Götaland that would strengthen the difference on false grounds. With only stones of at least ten legible words the odds ratio is {d2e(RO['ord10']['or'])}, so that does not explain the finding.
3. **The dating rests on ornamental style.** Undated stones are a group of their own. Another dating could move the figures slightly but hardly the direction, since the raw and the adjusted models nearly coincide.
4. **Region is a coarse division.** That the difference is largest between Uppland and Götaland is already visible. What happens in the border provinces is not tested here.

**What would overturn the finding.** A hand coding of sex on a large sample showing more errors in one region than in the other, or a recomputation with another dating in which the adjusted model no longer holds.

## 7. Conclusion

A woman stands among the sponsors on {pc(M['shares_region']['Svealand'])} percent of Svealand's runestones with a known sponsor against {pc(M['shares_region']['Götaland'])} percent of Götaland's, with age and carver constant, and the difference withstands every sensitivity analysis. What it consists in is not established: it is clearest where the mother appears on the stone for her child, but that is an indication, and no role test holds. The finding concerns who is named among the sponsors, a custom of the memorial stones, and is not a measure of women's standing. The roles can only be tested further on new material, and the question why the custom differed needs other material than the inscriptions' own words.

## Data and code

The analysis was made in Vitki {APP_VERSION}, an open research tool for runestones ([vitkirunor.se](https://vitkirunor.se/en)). The analysis code as it stood when the results were computed is commit `{COMMIT}` (29 October 2026) in [https://github.com/Precatio/runes](https://github.com/Precatio/runes), the last change to the analysis and its results before report version 1; it is Vitki {APP_VERSION} with later changes. All code, the analysis plans and the result files are openly available there under GPL-3.0.

- The analysis plans: `analysplaner/2026-10-28-manniskorna.md` and `analysplaner/2026-10-29-kvinnorna-i-svealand.md`, with checksums in the `.sha256` files beside them.
- The sex determination: `src/people.py`; the hand coding: `data/people_check.json`.
- The main model: `r/people.R`. The sensitivity analyses: `r/robustness.R` and `src/robustness.py` (method description in `METHODS.md`, sections 1u and 1v). The results are saved under the material's version `{FP}`.
- The follow-up: `utdata/kvinnor_landsdel/analys.R`, results and deviations in `utdata/kvinnor_landsdel/resultat.md`. It was run on the material's version `{FP_FU}`, which has the same stones and the same coding (identical `corpus.csv`, `people.csv` and `messages.csv`).
- To rerun the analysis: check out commit `{COMMIT}`, start the analysis engine with `scripts/dev_api.sh` and run `curl -X POST http://localhost:8000/api/r/corpus/run`. That computes all the corpus analyses and the sensitivity analyses for the Rundata loaded and saves them under `data/cache/r/corpus/<version>/` (each R module is run as `Rscript --vanilla r/<module>.R params.json outdir`, see `METHODS.md`, section 1). The follow-up: `Rscript utdata/kvinnor_landsdel/analys.R data/cache/r/corpus/{FP_FU} outdir`.
- The report is built by `utdata/blogg/build/build_rapport_kvinnor.py` (`.venv/bin/python utdata/blogg/build/build_rapport_kvinnor.py`), which reads every figure from the result files and stops if anything disagrees; the builder as reviewed before archiving is in commit `{REVIEW_COMMIT}`.
- In Vitki the association is shown under Statistics, The people, with the sensitivity analyses step by step. {NOW_EN} Popular accounts of the women on the stones are [The daughters the runestones forgot]({DOT_URL_EN}) and [She inherited from her child]({HON_URL_EN}).

## References

- Benjamini, Y. & Hochberg, Y. 1995. Controlling the false discovery rate: a practical and powerful approach to multiple testing. *Journal of the Royal Statistical Society B* 57 (1), pp. 289–300.
- Gräslund, A.-S. 1995. Runstenskvinnorna ännu en gång. *Tor* 27, pp. 459–474.
- Gräslund, A.-S. 2006. Dating the Swedish Viking-Age rune stones on stylistic grounds. In: M. Stoklund et al. (eds), *Runes and their Secrets: Studies in Runology*. Copenhagen: Museum Tusculanum Press, pp. 117–139.
- Hartig, F. 2022. *DHARMa: Residual diagnostics for hierarchical (multi-level/mixed) regression models*. R package.
- Holm, S. 1979. A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics* 6 (2), pp. 65–70.
- Jesch, J. 1991. *Women in the Viking Age*. Woodbridge: Boydell.
- Kvant, V. 2026. *Vitki {APP_VERSION}: method description* (METHODS.md). https://github.com/Precatio/runes
- Scandinavian Runic-text Database (Rundata), 2014 version with RUNDATA.xls updated 2018. Department of Scandinavian Languages, Uppsala University. Open Database License 1.0 / Database Contents License 1.0.
- Sawyer, B. 2000. *The Viking-Age Rune-Stones: Custom and Commemoration in Early Medieval Scandinavia*. Oxford: Oxford University Press.
- Wood, S. N. 2017. *Generalized Additive Models: An Introduction with R*. 2nd ed. Boca Raton: Chapman & Hall/CRC.

:::box The essentials
- In Svealand a woman was named among those who raised the stone nearly twice as often as in Götaland, and the difference withstands every check in the study.
- No difference was shown for widows or lone women; the difference is clearest where the mother appears on the stone for her child – but that is an indication, not a finding.
- The difference concerns who is named on the memorial stones, not women's power – and it is carried to a large degree by Uppland.
:::

{LOG_EN}
"""

# ---- form checks (mallen version 4; version 2 of the report) -----------------------------------------------------------
JARGON = r"modul\w*|trapp\w*|q_global|korpusjobb|fingeravtryck|fingerprint|facit|Vitkis|Vitki's|\bthe app\b|\bappen\b|METHODS"
for b, lang in ((body, "sv"), (body_en, "en")):
    assert not re.search(r"^\|", b, re.M), "BlogBody har inga tabeller"
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M)), "varje ruta ska stängas"
    assert "{" not in b and "}" not in b
    head = b.split("## Data")[0]
    assert not re.findall(JARGON, head), re.findall(JARGON, head)
    # no file paths before Data och kod (code spans one by one, so that a link between two spans is not read as a path)
    assert not [c for c in re.findall(r"`([^`\n]*)`", head) if "/" in c], re.findall(r"`([^`\n]*)`", head)
    # every link absolute; every chart's source line says who made it
    assert not re.findall(r"\]\((?!https://)", b), re.findall(r"\]\([^)]*\)", b)
    # (BlogBody reads a chart line as the caption only when it starts with "Källa:" / "Source:")
    for blk in re.findall(r"^:::chart[^\n]*\n(.*?)\n:::$", b, re.M | re.S):
        cap = blk.split("\n")[-1]
        assert cap.startswith("Källa:" if lang == "sv" else "Source:"), cap
        assert cap.endswith("Diagram: Vitki, efter Rundata." if lang == "sv" else "Chart: Vitki, after Rundata."), cap
    assert not re.search(r"^(Diagram|Chart):", b, re.M)
    assert (HALVES_SV if lang == "sv" else HALVES_EN) in b and (GLOSS if lang == "sv" else GLOSS_EN) in b
    assert "DOI finns ännu inte" not in b and "No release with a DOI" not in b and f"commit `{COMMIT}`" in b
    assert "RUNDATA.xls" in b and "3.1 (2018)" not in b and "Database Contents License 1.0" in b and "Halland" in b
    assert (f"Rapportversion {REPORT_VERSION}, {TODAY}." if lang == "sv" else f"Report version {REPORT_VERSION}, {TODAY}.") in b
    assert f"commit `{REVIEW_COMMIT}`" in b.split("## Data")[1] and (f"Version {REPORT_VERSION}, {TODAY}" in b)
    assert ("## Ändringslogg" if lang == "sv" else "## Change log") in b and f"Version 1, {V1_DATE}" in b
    assert "Hr" not in b and "Dalsland" in b
assert "Det viktigaste i korthet" in body and "## 2. Förregistrering" in body and "## 6. Diskussion" in body
# version 1's claims that the corrections removed must not come back (outside the change log, which quotes them)
for b in (body, summary, body_en, summary_en):
    b = b.split("## Ändringslogg")[0].split("## Change log")[0]
    for gone in ("här sitter skillnaden", "this is where the difference lies", "tillsammans med fadern och syskonen",
                 "together with the father and the siblings", "Ingen jämförelse mellan landsdelar", "No comparison between regions",
                 "robusthetstrappans", "robustness ladder", "åtta känslighetsanalyser", "eight sensitivity analyses",
                 "Riktningen håller i alla landskap", "direction holds in every province", "finner att skillnaden sitter",
                 "finds that the difference lies", "varje kontroll vi har", "every check we have",
                 # version 3: the box and the inheritance reading of version 2
                 "förklarar den inte", "do not explain it", "bättre än med färderna", "better than it fits the journeys",
                 "familjen – förklarar en femtedel", "family – explains a fifth"):
        assert gone not in b, gone
assert summary.startswith("Förregistrerad omprövning av ett tidigare iakttaget mönster.")
assert summary_en.startswith("Pre-registered re-test of a previously observed pattern.")

out = {"slug": SLUG, "title": title, "summary": summary, "body": body,
       "title_en": title_en, "summary_en": summary_en, "body_en": body_en,
       "labels": ["Rapport", "Kvinnor och barn", "Geografi"]}
assert blog_labels.check(out["labels"]) is None
path = os.path.join(ROOT, "utdata", "rapporter", "rapport1_kvinnor.json")
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
                 "topic": "Rapport|kvinnor", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
