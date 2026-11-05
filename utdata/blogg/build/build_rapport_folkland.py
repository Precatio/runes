"""Forskningsrapport (låst mall utdata/rapporter/MALL.md, version 4; Fullt prövat fynd): "Upplands folkland skiljer
runstenarna åt mer än 997 av 999 slumpvisa indelningar av samma härader" (sv + en). Siffrorna låses mot
utdata/gamla_granser/monster.json (plan analysplaner/2026-11-02-gamla-granser-nya-monster.md, sha 054c87d5, avvikelse 1
f0a42169), monster_trappa.json (tilläggsplan e31f2fd1), monster_kanslighet.json, monster_drag.json,
utdata/granser/gransskannern.json (plan 7d22ff40), utdata/folkland/at_ristare.json (plan c4c4f5ba) och
utdata/folkland/landrattelse.json. Granskningen 2026-11-05 (utdata/rapporter/granskning_2026-11-05_utkast.md) fann att 39
stenar föll bort ur landindelningen; den rättades efter Det medeltida Sverige 1:7 och allt kördes om 2026-11-05. Den första
körningens siffror läses ur *_v1.json bredvid och står i texten som "före rättelsen".
    ../../../.venv/bin/python build_rapport_folkland.py [--write | --update DOC]
Utan flaggor skrivs bara utdata/rapporter/rapport_folkland.json; --write/--update kräver att omkörningen är incheckad."""
import datetime as dt
import json
import os
import re
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_labels  # noqa: E402

J = lambda *p: json.load(open(os.path.join(ROOT, *p), encoding="utf-8"))  # noqa: E731
GG = ("utdata", "gamla_granser")
M, M1 = J(*GG, "monster.json"), J(*GG, "monster_v1.json")
TR, TR1 = J(*GG, "monster_trappa.json"), J(*GG, "monster_trappa_v1.json")
KS, KS1 = J(*GG, "monster_kanslighet.json"), J(*GG, "monster_kanslighet_v1.json")
DR, DR1 = J(*GG, "monster_drag.json"), J(*GG, "monster_drag_v1.json")
GS, GS1 = J("utdata", "granser", "gransskannern.json"), J("utdata", "granser", "gransskannern_v1.json")
AR = J("utdata", "folkland", "at_ristare.json")
LR = J("utdata", "folkland", "landrattelse.json")
HL = J("web", "src", "lib", "historiska_land.json")
SL = J("web", "public", "geo", "sten_land.json")
APP_VERSION = "3.0.0"  # the Vitki version the analysis was made in (tag v3.0.0 + the commits named in Data och kod), not the current one
SITE = "https://vitkirunor.se"
MALL_SHA = open(os.path.join(ROOT, "utdata", "rapporter", "MALL.md.sha256")).read().split()[0]
assert MALL_SHA.startswith("611a4d5f")  # mallens version 4
REPORT_VERSION = 1  # never published; the correction before publication is part of version 1 (no change log)
TODAY = "2026-11-05"  # rapportversionens datum, fast i byggaren
PLANS = ("2026-11-02-gamla-granser-nya-monster", "2026-11-02-gamla-granser-nya-monster-avvikelse",
         "2026-11-02-folkland-slumpindelning-trappa", "2026-11-02-gransskannern", "2026-11-01-upplands-folkland",
         "2026-11-01-folkland-at-ristare", "2026-11-01-folkland-at-trappa")
SHA = {f: open(os.path.join(ROOT, "analysplaner", f + ".sha256")).read().split()[0] for f in PLANS}
for f, pre in zip(PLANS, ("054c87d5", "f0a42169", "e31f2fd1", "7d22ff40", "48346775", "c4c4f5ba", "1ffcb5c6")):
    assert SHA[f].startswith(pre), f
PLAN_TEXT = re.sub(r"\s+", " ", open(os.path.join(ROOT, "analysplaner", PLANS[0] + ".md"), encoding="utf-8").read())
HYP = ("Om folklanden bara vore godtyckliga block av grannbygder skulle vilka block som helst skilja lika mycket, eftersom "
       "grannstenar liknar varandra.")
assert HYP in PLAN_TEXT  # quoted in full (the review: no truncated quote)
# the method's constants as the plans state them
assert "999 sammanhängande indelningar" in PLAN_TEXT and "inom 10 km" in PLAN_TEXT and "samma namn inom 25 km" in PLAN_TEXT
assert "närmaste ISOF-socken inom 15 km" in PLAN_TEXT and "(–1010, 1010–1040, 1040–1070, 1070–, odaterad)" in PLAN_TEXT
assert "inom **20 km**" in open(os.path.join(ROOT, "analysplaner", PLANS[1] + ".md"), encoding="utf-8").read()
_gs_plan = re.sub(r"\s+", " ", open(os.path.join(ROOT, "analysplaner", PLANS[3] + ".md"), encoding="utf-8").read())
assert "minst 40 stenar" in _gs_plan and "inom 10 km" in _gs_plan
assert "y.sum() < 10 or len(y) - y.sum() < 10" in open(os.path.join(ROOT, *GG, "monster.py"), encoding="utf-8").read()
assert "NPART, ADJ_KM, MIN_SUB, MIN_HARAD = int(os.environ.get(\"NPART\", 999)), 20" in open(os.path.join(ROOT, *GG, "monster.py"), encoding="utf-8").read()

# ---- code state: the first run's commit, and the rerun's commit once it is committed ---------------------------------
V1_COMMIT = "8d24b20"  # 2026-11-03: the analysis code and every result file of the first run (monster*, gransskannern)
BEFORE_COMMIT = LR["before_commit"]  # 461dca4: the land files before the correction
RERUN_FILES = ["utdata/gamla_granser/monster.py", "utdata/gamla_granser/monster.json", "utdata/gamla_granser/monster_v1.json",
               "utdata/gamla_granser/monster_trappa.json", "utdata/gamla_granser/monster_kanslighet.json",
               "utdata/gamla_granser/monster_drag.json", "utdata/granser/gransskannern.json", "utdata/folkland/landrattelse.json",
               "web/src/lib/historiska_land.json", "web/public/geo/sten_land.json", "scripts/assign_sten_land.py"]


def git(*a):
    return subprocess.run(["git", "-C", ROOT, *a], capture_output=True, text=True)


RERUN_COMMIT = None
if os.path.isdir(os.path.join(ROOT, ".git")):
    for c in (V1_COMMIT, BEFORE_COMMIT):
        assert git("merge-base", "--is-ancestor", c, "HEAD").returncode == 0, c
    tracked = all(git("ls-files", "--error-unmatch", f).returncode == 0 for f in RERUN_FILES)
    clean = not git("status", "--porcelain", "--", *RERUN_FILES).stdout.strip()
    if tracked and clean:
        RERUN_COMMIT = git("log", "-1", "--format=%h", "--", *RERUN_FILES).stdout.strip() or None
if RERUN_COMMIT is None:
    print("VARNING: omkörningen 2026-11-05 är inte incheckad; texten säger det. Checka in (git add -f för nya filer under "
          "utdata/) och bygg om innan rapporten skrivs till Firestore.")
CODE_SV = (f"den första körningen i commit {V1_COMMIT} (2–3 november 2026), omkörningen efter rättelsen i commit "
           f"{RERUN_COMMIT} (5 november 2026)" if RERUN_COMMIT else
           f"den första körningen i commit {V1_COMMIT} (2–3 november 2026); omkörningen efter rättelsen (5 november 2026) "
           f"är ännu inte incheckad")
CODE_EN = (f"the first run in commit {V1_COMMIT} (2–3 November 2026), the rerun after the correction in commit "
           f"{RERUN_COMMIT} (5 November 2026)" if RERUN_COMMIT else
           f"the first run in commit {V1_COMMIT} (2–3 November 2026); the rerun after the correction (5 November 2026) is "
           f"not yet committed")

TL_SV = ("kartlagret med de gamla landen byggdes och folklandsgränsen för *at* prövades under en låst plan 2026-11-01; "
         "häradernas folkland kontrollerades mot sexårsgärden 1314, gränsskannern kördes, och slumpindelningsprovet och "
         "tilläggsplanen för känslighetsanalyserna låstes och kördes 2026-11-02; landindelningen rättades och alla prov "
         "kördes om 2026-11-05")
TL_EN = ("the map layer of the old lands was built and the folkland border for *at* was tested under a locked plan "
         "2026-11-01; the hundreds' folklands were checked against the six-year tithe of 1314, the border scan was run, and "
         "the random-partition test and the addendum plan for the sensitivity analyses were locked and run 2026-11-02; the "
         "land assignment was corrected and every test was rerun 2026-11-05")

r0 = lambda x: f"{x:.0f}"  # noqa: E731
pc = lambda k, n: round(100 * k / n)  # noqa: E731


def pf(p, en=False):
    s = f"{p:.3f}"
    return s if en else s.replace(".", ",")


d1 = lambda x: f"{x:.1f}".replace(".", ",")  # noqa: E731
NUM = {2: ("två", "two")}  # N_GE in words where a sentence needs it


FOLK = ("attundaland", "tiundaland", "fjadrundaland", "roden")
NAME = {"attundaland": "Attundaland", "tiundaland": "Tiundaland", "fjadrundaland": "Fjädrundaland", "roden": "Roden"}

# ---- the land correction (landrattelse.json, historiska_land.json → parish_medieval) ----------------------------------
DB, DA = LR["drag"]["before"], LR["drag"]["after"]
assert DB == {"tiundaland": 319, "attundaland": 340, "fjadrundaland": 122, "roden": 60, "inget": 39}
assert DA == {"tiundaland": 320, "attundaland": 366, "fjadrundaland": 128, "roden": 59, "inget": 7}
DROP = LR["dropped_before"]
assert DROP["n"] == 39 and DROP["by_group"] == {"faringo": 24, "adelso": 6, "ekero": 5, "ovriga": 4}
FP_ = DROP["faringo_by_parish"]
assert (FP_["Sånga sn"], FP_["Lovö sn"], FP_["Hilleshögs sn"], FP_["Skå sn"], FP_["Munsö sn"], FP_["Färentuna sn"]) == (6, 6, 4, 4, 2, 2)
assert DROP["ovriga"] == ["U 419", "U 53", "U 54", "U 871"]
AFTER = DROP["after"]
N_NOW = sum(1 for v in AFTER.values() if v)
assert N_NOW == 32 and DA["inget"] == 39 - N_NOW
assert (AFTER["U 419"], AFTER["U 871"], AFTER["U 53"], AFTER["U 54"]) == ("attundaland", "tiundaland", None, None)
U77 = [c for c in LR["changed"] if c["signum"] == "U 77"][0]
assert (U77["before"], U77["after"], U77["parish"]) == ("roden", "attundaland", "Spånga sn (nu Sundbyberg)")
PM = LR["parish_medieval"]
assert all(PM[p] == "Bro härad" for p in ("Färentuna socken", "Hilleshögs socken", "Lovö socken", "Munsö socken", "Skå socken", "Sånga socken"))
assert PM["Adelsö socken"] == "Trögds härad" and PM["Ekerö socken"] == PM["Brännkyrka socken"] == "Svartlösa härad"
assert PM["Spånga socken"] == PM["Bromma socken"] == "Sollentuna härad"
# the source: DMS 1:7 (Ferm, Johansson & Rahmqvist 1992), the quotes in the OCR text, the page by the scan's page breaks
DMS = "/Volumes/2TB/Antigrvity/Runes/geografi_kallor/dms/"
D7 = re.sub(r"\s+", " ", open(DMS + "dms_1_7_dedup.txt", encoding="utf-8").read())
D7P = [re.sub(r"\s+", " ", p) for p in open(DMS + "dms_1_7.txt", encoding="utf-8").read().split("\f")]
for q, page, word in (("Bro härad, till vilket Färingö tingslag hörde, och Sollentuna härad ingick i Attundaland", 19, "tingslag"),
                      ("Adelsö socken, som hörde till Trögds härad i Fjädrundaland", 19, "Trögds"),
                      ("den andra halvan är Färingö tingslag", 44, "Brohalvahundare"),
                      ("Färingö tingslag omfattar under medeltiden och fram till 1540 Färentuna, Hilleshögs, Sånga, Skå, Lovö och Munsö socknar", 114, "Omfattning"),
                      ("Adelsö hörde dessförinnan till Trögds härad i Fjädrunda", 114, "Fjädrunda"),
                      ("Ekerö till Svartlösa härad i Södermanland", 114, "Svartlösa"),
                      ("Sollentuna härad omfattar under medeltiden och 1500-talet", 237, "Spånga socknar")):
    assert q in D7 and word in D7P[page - 1], (q, page)
assert "Stockholm 1992" in D7 and "Ferm" in D7 and "skeppslag omnämns 1409" in D7 and "Senast från 1423" in D7  # Lovö, s. 30
REGS = {r["id"]: r for r in HL["epoch"]["regions"]}
assert len(REGS["attundaland"]["harad"]) == 8 and "Färingö tingslag" in REGS["attundaland"]["note"]
assert "Sexårsgärden 1314 (SDHK 2593) räknar hit de åtta hundarena" in REGS["attundaland"]["note"]
assert "Sexårsgärden 1314" in REGS["tiundaland"]["note"] and "Gästrikland och Roden" in REGS["tiundaland"]["note"]
assert "Adelsö socken hörde till Trögds härad" in REGS["fjadrundaland"]["note"] and REGS["roden"]["certainty"] == "omstridd"
assert any("CC BY 4.0" in s and "2593" in s for s in HL["epoch"]["sources"])
assert any("PlaceNameService, CC BY" in s for s in HL["epoch"]["sources"])

# ---- the literature, against the local copies ------------------------------------------------------------------------
LIT = "/Volumes/2TB/Antigrvity/Runes/geografi_kallor/litteratur/"
L02 = re.sub(r"\s+", " ", open(LIT + "Larsson_2002_Yrrunan.txt", encoding="utf-8").read())
for q in ("Beträffande de uppländska inskrifterna kan knappast det geografiska läget i sig vara någon förklaring",
          "rimligen kronologiska, delvis kanske också individuella", "Frågan är varför just Gotland, Uppland och Väster",
          "nämligen Vadsbo"):
    assert q in L02, q  # Larsson 2002, s. 169–170: Uppland's share as a whole, not variation within Uppland
L93 = re.sub(r"\s+", " ", open(LIT + "Larsson_1993.txt", encoding="utf-8").read())
for q in ("De tre folklanden är tidigast kända i en latinsk text från", "omkring 1120. Två av dem nämns också i en redogörelse",
          "vid mitten av 1000-talet", "organiserat såväl ledungen som folklandsindelningen", "hälften av 900-talet"):
    assert q in L93, q  # Larsson 1993, s. 106 f. (folklands first named) and s. 114 (Erik Segersäll)
assert "Upplandslagen år 1296" in L93
assert "Socknen överfördes från Trögds härad först 1540" in D7  # Adelsö, DMS 1:7 s. 19

# ---- the main test (step 1), after the correction and before it ------------------------------------------------------
U, S, U1, S1 = M["step1"]["uppland"], M["step1"]["smaland"], M1["step1"]["uppland"], M1["step1"]["smaland"]
assert (U["units"], U["stones"], U["features"]) == (31, 873, 25) and (U1["units"], U1["stones"], U1["features"]) == (32, 841, 25)
assert U["sizes"] == {"attundaland": 8, "roden": 7, "tiundaland": 11, "fjadrundaland": 5}
assert U1["sizes"] == {"attundaland": 9, "roden": 7, "tiundaland": 11, "fjadrundaland": 5}
assert {k: DA[k] for k in FOLK} == DR["regions"] and {k: DB[k] for k in FOLK} == DR1["regions"]
A, HA, HB = U["alla"], U["A"], U["B"]
A1, HA1, HB1 = U1["alla"], U1["A"], U1["B"]
assert (round(A["chi2_real"]), round(A["chi2_median_random"]), round(A["chi2_p95_random"]), A["p"]) == (363, 183, 256, 0.003)
assert (round(HA["chi2_real"]), round(HA["chi2_median_random"]), HA["p"]) == (245, 134, 0.001)
assert (round(HB["chi2_real"]), round(HB["chi2_median_random"]), HB["p"]) == (214, 124, 0.001)
assert (A["k_real"], A["k_median_random"], round(A["p_k"], 3)) == (15, 8.0, 0.017)
assert (round(A1["chi2_real"]), round(A1["chi2_median_random"]), round(A1["chi2_p95_random"]), A1["p"]) == (360, 183, 259, 0.001)
assert (round(HA1["chi2_real"]), round(HB1["chi2_real"]), HA1["p"], HB1["p"]) == (237, 217, 0.001, 0.001)
assert U["holds"] and U1["holds"]
N_GE = round(A["p"] * 1000) - 1  # random divisions with at least the real sum (p = (1 + N_GE) / 1000)
assert N_GE == 2 and round(HA["p"] * 1000) - 1 == round(HB["p"] * 1000) - 1 == 0
RATIO = A["chi2_real"] / A["chi2_median_random"]
assert round(RATIO, 1) == 2.0
assert (S["units"], S["stones"], S["features"], S["holds"]) == (18, 103, 14, False) and (S1["units"], S1["holds"]) == (19, False)
assert (round(S["alla"]["chi2_real"]), round(S["alla"]["chi2_median_random"]), S["alla"]["p"], S1["alla"]["p"]) == (193, 184, 0.267, 0.145)
HOLM_U = min(1, 2 * min(A["p"], S["alla"]["p"]))  # two step-1 tests in the plan, Holm
assert HOLM_U == 0.006
# the addendum ladder
ST, ST1 = TR["steps"], TR1["steps"]
assert TR["all_hold"] and TR1["all_hold"] and list(ST) == ["pa_plats", "utan_fem_ristare", "daterade", "utan_forlorade"]
LAD = {k: (v["stones"], round(v["alla"]["chi2_real"]), round(v["alla"]["chi2_median_random"]), v["alla"]["p"]) for k, v in ST.items()}
assert LAD == {"pa_plats": (513, 240, 137, 0.006), "utan_fem_ristare": (559, 232, 135, 0.002),
               "daterade": (529, 271, 145, 0.004), "utan_forlorade": (734, 311, 171, 0.004)}
LAD1 = {k: v["alla"]["p"] for k, v in ST1.items()}
assert LAD1 == {"pa_plats": 0.002, "utan_fem_ristare": 0.003, "daterade": 0.002, "utan_forlorade": 0.002}
PMIN, PMAX = min(v[3] for v in LAD.values()), max(v[3] for v in LAD.values())
# sensitivity without granite (outside the plan)
assert (KS["features"], round(KS["alla"]["chi2_real"]), round(KS["alla"]["chi2_median_random"]), KS["alla"]["p"]) == (24, 325, 153, 0.004)
assert (KS["A"]["p"], KS["B"]["p"], KS1["alla"]["p"]) == (0.002, 0.003, 0.001)
# which traits (descriptive): the 25 of the plan's 27 with ten stones with and without; pagan marker and kumbl fell out
FD = {f["feature"]: f for f in DR["features"]}
FEATS25 = ["pm_kors", "cat_kristen", "pm_bon", "pm_sjal", "cat_fard", "msg_dod_borta", "msg_berom", "cat_bro_vag",
           "kvinna_resare", "kvinna_ensam", "flera_resare", "rel_barn", "rel_foralder", "rel_syskon", "rel_make", "drengr",
           "thegn", "pm_signatur", "mat_granit", "pm_stungna", "monoftong", "r_for_R", "o_runa", "prep_at", "ord_þennsa"]
assert sorted(FD) == sorted(FEATS25) and len(FEATS25) == U["features"] and not {"pm_hednisk", "ord_kumbl"} & set(FD)
assert DR["n_stones"] == 873 and sum(1 for f in DR["features"] if f["p"] < 0.05) == 15
SH = lambda f, L: FD[f]["shares"][L]  # noqa: E731
SH1 = lambda f, L: {g["feature"]: g for g in DR1["features"]}[f]["shares"][L]  # noqa: E731
assert [pc(*SH("pm_kors", L)) for L in FOLK] == [61, 65, 35, 41]
assert [pc(*SH("prep_at", L)) for L in FOLK] == [14, 32, 39, 23] and pc(*SH1("prep_at", "attundaland")) == 12
assert [pc(*SH("r_for_R", L)) for L in FOLK] == [14, 19, 50, 12]
assert [f["feature"] for f in DR["features"][:5]] == ["pm_kors", "mat_granit", "monoftong", "prep_at", "r_for_R"]
# the plain words of 5.2: one in seven (14 %), one in eight before (12 %), four in ten, half, one in seven
fr = lambda f, L: SH(f, L)[0] / SH(f, L)[1]  # noqa: E731
assert abs(fr("prep_at", "attundaland") - 1 / 7) < 0.01 and abs(fr("r_for_R", "attundaland") - 1 / 7) < 0.01
assert abs(SH1("prep_at", "attundaland")[0] / SH1("prep_at", "attundaland")[1] - 1 / 8) < 0.01
assert round(fr("prep_at", "fjadrundaland"), 1) == 0.4 and round(fr("r_for_R", "fjadrundaland"), 1) == 0.5
assert round(fr("pm_kors", "attundaland"), 1) == round(fr("pm_kors", "tiundaland"), 1) - 0.1 == 0.6
assert abs(fr("pm_kors", "fjadrundaland") - 1 / 3) < 0.02 and round(fr("pm_kors", "roden"), 1) == 0.4
# the border scan (follow-up, its own plan): combinations of feature and border that are sharp and hold in both halves
hold = lambda g: sorted((t["feature"], tuple(sorted((t["a"], t["b"])))) for t in g["tests"] if t.get("holds"))  # noqa: E731
H2, H1 = hold(GS), hold(GS1)
assert all(a in FOLK and b in FOLK for _, (a, b) in H2 + H1)
assert (len(H2), len({f for f, _ in H2}), len(H1), len({f for f, _ in H1})) == (7, 6, 6, 5)
TA, TF, AF, AR_ = ("attundaland", "tiundaland"), ("fjadrundaland", "tiundaland"), ("attundaland", "fjadrundaland"), ("attundaland", "roden")
assert H2 == sorted([("prep_at", TA), ("mat_granit", TA), ("pm_kors", TF), ("flera_resare", TF), ("msg_berom", TF),
                     ("r_for_R", TF), ("flera_resare", AF)])
assert set(H1) - set(H2) == {("pm_kors", AR_)} and set(H2) - set(H1) == {("msg_berom", TF), ("flera_resare", AF)}
GT = {(t["feature"], tuple(sorted((t["a"], t["b"])))): t for t in GS["tests"]}
KAR = GT[("pm_kors", AR_)]
assert KAR["sharp"] and not KAR["holds"] and KAR["halves"][0]["p"] > 0.05
AT_AF, FR_AF = GT[("prep_at", AF)], GT[("flera_resare", AF)]
assert (AT_AF["high"], AT_AF["border_high"], AT_AF["border_low"]) == ("fjadrundaland", [1, 5], [4, 8]) and AT_AF["p_border"] > 0.95
assert (FR_AF["high"], FR_AF["border_high"], FR_AF["border_low"]) == ("attundaland", [9, 10], [1, 6]) and FR_AF["holds"]
AF_N = [n for t in GS["tests"] if tuple(sorted((t["a"], t["b"]))) == AF and t["q"] < 0.05 for n in (t["border_high"][1], t["border_low"][1])]
assert (min(AF_N), max(AF_N)) == (3, 14)
AF_N1 = [n for t in GS1["tests"] if tuple(sorted((t["a"], t["b"]))) == AF and t["q"] < 0.05 for n in (t["border_high"][1], t["border_low"][1])]
assert max(AF_N1) == 2
# the at border with the carver as a random effect (plan c4c4f5ba), rerun on the corrected rows
assert AR["holds_with_carvers"] and round(AR["step1"]["border"]["or"], 1) == 5.9 and AR["step1"]["border"]["p1"] < 0.002
assert round(AR["step1"]["border"]["or"]) == 6  # "ungefär sex gånger så höga"
SM2 = [c for c in LR["changed"] if c["signum"].startswith("Sm ")]  # the two stones in Jönköping (Småland's 19 → 18 hundreds)
assert sorted((c["signum"], c["before"], c["after"]) for c in SM2) == [("Sm 139", "tveta", "vedbo"), ("Sm 91", "tveta", "njudung")]
assert HA["p"] == HB["p"]


# ---- runic examples: Rundata transliterations rendered with standard younger-futhark (long-branch) forms -------------
RECS = {r["signum"]: r for r in json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["inscriptions"]}
RMAP = {"a": "ᛅ", "b": "ᛒ", "e": "ᛂ", "f": "ᚠ", "g": "ᚵ", "h": "ᚼ", "i": "ᛁ", "k": "ᚴ", "l": "ᛚ", "m": "ᛘ", "n": "ᚾ",
        "o": "ᚬ", "r": "ᚱ", "R": "ᛦ", "s": "ᛋ", "t": "ᛏ", "u": "ᚢ", "y": "ᚤ", "þ": "ᚦ", " ": "᛫"}


def ex(signum, excerpt):
    t = " ".join(RECS[signum]["transliteration"].replace("'", " ").replace("÷", " ").replace("·", " ").split())
    assert excerpt in t, (signum, excerpt)
    return "".join(RMAP[c] for c in excerpt)


EX = {"u1177": ex("U 1177", "litu risa stin at tuba"), "u181": ex("U 181", "iftiR est faþur sin"),
      "u749": ex("U 749", "þair litu rasa stan"), "u974": ex("U 974", "þaiR")}
assert RECS["U 1177"]["carvers"][0]["name"] == RECS["U 181"]["carvers"][0]["name"] == RECS["U 974"]["carvers"][0]["name"] == "Öpir 1"
assert RECS["U 749"]["carvers"][0]["name"] == "Balle"
assert (RECS["U 1177"]["parish"], RECS["U 181"]["parish"], RECS["U 749"]["parish"], RECS["U 974"]["parish"]) == (
    "Harbo sn", "Össeby-Garns sn", "Husby-Sjutolfts sn", "Vaksala sn")
assert (SL["U 1177"], SL["U 181"], SL["U 749"], SL["U 974"]) == ("tiundaland", "attundaland", "fjadrundaland", "tiundaland")

SLUG = "upplands-folkland-skiljer-runstenarna"
title = f"Upplands folkland skiljer runstenarna åt mer än {999 - N_GE} av 999 slumpvisa indelningar av samma härader"
title_en = f"Uppland's folklands separate the runestones more than {999 - N_GE} of 999 random divisions of the same hundreds"
CITE_EN = (f"Kvant, V. ({TODAY[:4]}). {title_en}. Research report, report version {REPORT_VERSION}; analysis in Vitki "
           f"{APP_VERSION}. {SITE}/en/forskningsrapporter/{SLUG}")
summary = ("Gränserna mellan Upplands gamla folkland – Tiundaland, Attundaland, Fjädrundaland och kustlandet Roden – "
           "skiljer runstenarnas språk, sed och utförande ungefär dubbelt så mycket som en typisk slumpvis indelning av samma "
           f"härader i lika stora block; bara {N_GE} av 999 slumpindelningar når lika långt. Det håller i båda halvorna av "
           "materialet och i alla förregistrerade känslighetsanalyser, också efter att landindelningen rättats för "
           f"{DROP['n']} stenar som först föll bort. Smålands små land visar inget motsvarande.")
summary_en = ("The borders between Uppland's old folklands – Tiundaland, Attundaland, Fjädrundaland and the coastal land "
              "Roden – separate the language, custom and execution of the runestones about twice as much as a typical "
              f"random division of the same hundreds into blocks of the same size; only {N_GE} of 999 random divisions reach "
              "as far. It holds in both halves of the material and in every pre-registered sensitivity analysis, also after "
              f"the land assignment was corrected for {DROP['n']} stones that had first dropped out. Småland's small lands "
              "show nothing similar.")
CHART_SV = "Diagram: Vitki, efter Rundata (ODbL)."
CHART_EN = "Chart: Vitki, after Rundata (ODbL)."


def chart(lang):
    sv = lang == "sv"
    rows = [":::chart Tre drag per folkland: kors, prepositionen at och r för ʀ" if sv else
            ":::chart Three features by folkland: cross, the preposition at and r for ʀ"]
    for f, lab in (("pm_kors", "Kors" if sv else "Cross"), ("prep_at", "at"), ("r_for_R", "r för ʀ" if sv else "r for ʀ")):
        rows.append(f"# {lab}")
        for L in FOLK:
            k, n = SH(f, L)
            rows.append(f"{NAME[L]} | {pc(k, n)} | {k} {'av' if sv else 'of'} {n}")
    # BlogBody reads the caption only from a line that starts with "Källa:"/"Source:"; the credit goes last
    rows.append("Källa: Samnordisk runtextdatabas (Rundata); folkland efter sexårsgärden 1314, Institutet för språk och "
                "folkminnens ortnamnsregister och Det medeltida Sverige 1:7, efter rättelsen. Råa andelar av stenarna där "
                f"draget går att avgöra. Procent. {CHART_SV}" if sv else
                "Source: Scandinavian Runic-text Database (Rundata); folklands after the six-year tithe of 1314, the place-name "
                "register of the Institute for Language and Folklore and Det medeltida Sverige 1:7, after the correction. Raw "
                f"shares of the stones where the feature can be decided. Percent. {CHART_EN}")
    return "\n".join(rows) + "\n:::"


P_SM, P_SM1 = S["alla"]["p"], S1["alla"]["p"]

body = f"""*Viktor Kvant, oberoende forskare. Fullt prövat fynd. Rapportversion {REPORT_VERSION}, {TODAY}. Tidslinje: {TL_SV}. Analysen är gjord i Vitki {APP_VERSION}. Licens CC BY 4.0. Den engelska versionen är den kanoniska för citering: {CITE_EN}. Nyckelord: runstenar, vikingatid, Uppland, folkland, hundare, härad, regional variation, permutationstest, logistisk regression. Konkurrerande intressen: inga. Finansiering: ingen.*

## Sammanfattning

**Bakgrund och syfte.** Uppland var under medeltiden inget enat landskap utan bestod av tre folkland – Tiundaland, Attundaland och Fjädrundaland – och kustlandet Roden, med gemensam lag först 1296. Hur gamla folklanden är vet man inte: de nämns tidigast omkring 1120, och det har föreslagits att indelningen går tillbaka till slutet av 900-talet. Runstenarna restes just under 1000-talet. Om folklandens gränser redan då skilde människorna åt, borde stenarna skilja sig mer över dessa gränser än över andra gränser genom samma bygder.

**Material.** {U['stones']} vikingatida runstenar i Uppland med känt läge, fördelade på {U['units']} härader och skeppslag med deras folkland enligt sexårsgärden 1314 och, för Mälaröarna, *Det medeltida Sverige*; {U['features']} drag i språk, formler, familj, ristning och bergart. Före publiceringen rättades landindelningen: {DROP['n']} stenar hade fallit bort för att deras socknar saknade folkland, och {N_NOW} av dem är nu med.

**Metod.** För varje drag mättes hur mycket blocktillhörigheten förklarar, med tiden konstant (logistisk regression, kvottest), och summan över dragen jämfördes med samma summa för 999 slumpvisa indelningar av samma härader i fyra sammanhängande block av samma storlek. Planen låstes före körningen.

**Resultat.** De verkliga folklanden ger summan {r0(A['chi2_real'])}; slumpindelningarna ger i median {r0(A['chi2_median_random'])}, och den högsta tjugondelen börjar vid {r0(A['chi2_p95_random'])}. Bara {N_GE} av 999 når lika högt (p = {pf(A['p'])}; Holm-korrigerat {pf(HOLM_U)}), i båda halvorna ingen (p = {pf(HA['p'])}), och provet håller i alla fyra förregistrerade känslighetsanalyser (p {pf(PMIN)}–{pf(PMAX)}). Före rättelsen: {r0(A1['chi2_real'])}, och ingen nådde upp (p = {pf(A1['p'])}). Smålands små land skiljer sig inte mer än slumpblock (p = {pf(P_SM)}).

**Slutsats.** Folklandens gränser skiljer runstenarna åt ungefär dubbelt så mycket som en typisk slumpgräns genom samma bygder. Det talar för att indelningen, eller något som föregick den, fanns redan när stenarna restes, men provet avgör inte vad som skilde – språk, sed eller verkstäder.

## 1. Inledning

Att runstenarna i Uppland varierar inom landskapet är känt. Palm (1992) visade att prepositionen *at* är vanligare i Tiundaland än i Attundaland och drog sina undersökningsområden efter folklandens gränser. Larsson (2002, s. 168–170) frågade varför Gotland, Uppland och Västergötland har en betydligt högre andel skrivningar av ʀ med r-runan än övriga områden; i Västergötland kommer de flesta beläggen från ett härad, Vadsbo, men för Uppland menade han att det geografiska läget i sig knappast är förklaringen, utan snarare kronologiska och delvis individuella faktorer. Stille (1999) undersökte runristarna i ett enda folkland, Fjädrundaland. Peterson (1996) behandlar enligt titeln just valet mellan *aft/æft*, *at* och *æftiR* och om det är regional variation; artikeln har vi inte kunnat läsa. Om folklandens ålder har Mats G. Larsson (1993, s. 114) föreslagit att både ledungen och folklandsindelningen organiserades av Erik Segersäll under senare delen av 900-talet; folklanden nämns tidigast i en latinsk text från omkring 1120, och två av dem i en redogörelse som kan gå tillbaka till mitten av 1000-talet (s. 106 f.).

Det som saknas är ett prov av gränserna själva. Att två områden skiljer sig säger ännu inget om gränsen mellan dem: grannbygder liknar varandra, och nästan vilken uppdelning av ett landskap som helst ger skillnader mellan delarna. Frågan blir därför om folklandens gränser skiljer stenarna mer än andra gränser, dragna genom samma bygder, gör. Det prövas här med ett omblandningsprov (permutationstest) där de verkliga folklanden jämförs med slumpvisa indelningar av samma härader.

## 2. Förregistrering

Planen (*Nya mönster med den vikingatida indelningen*, steg 1) låstes 2 november 2026 med SHA-256 {SHA[PLANS[0]][:16]}…, innan provet kördes. Hypotesen ordagrant: ”{HYP}” Utfallsregeln: folklanden är särskilda om deras summa ligger över 95:e percentilen av slumpindelningarna (p = (1 + antal ≥ verklig) / 1000 < 0,05), och samma rangtal redovisas i båda halvorna.

En avvikelse låstes innan något resultat hade räknats ut (SHA-256 {SHA[PLANS[1]][:16]}…): grannregeln behövde vidgas, se 4.4. Känslighetsanalyserna låstes i en egen tilläggsplan efter huvudprovet men innan de kördes (SHA-256 {SHA[PLANS[2]][:16]}…). Landindelningen rättades efter granskningen inför publiceringen och allt kördes om, efter att resultaten setts (4.4).

Sett före låsningen: att *at* skiljer skarpt vid gränsen mellan Tiundaland och Attundaland (en egen låst plan dagen före, SHA-256 {SHA[PLANS[4]][:16]}…), och att gränsskannern (egen plan, SHA-256 {SHA[PLANS[3]][:16]}…) hittat skarpa gränser, alla mellan folklanden. Huvudprovet är därför inte en blind upptäckt: det prövar om ett mönster som syntes vid enskilda gränser gäller indelningen som helhet, mot en uttalad nollhypotes. Konfirmatoriskt: steg 1 för Uppland. Sekundärt: steg 1 för Småland. Uppföljning med egen låst plan: känslighetsanalyserna. Explorativt: provet utan bergarten och vilka drag som bär skillnaden.

## 3. Material

Runstenarna kommer ur Samnordisk runtextdatabas (Rundata), version 2014 med RUNDATA.xls uppdaterad 2018, fryst för analysen den 4 oktober 2026. Urvalet: vikingatida runstenar i Uppland vars socken går att knyta till ett härad i Institutet för språk och folkminnens ortnamnsregister (samma socknamn inom 25 km, annars närmaste socken inom 15 km) och vars härad hör till ett folkland: {U['stones']} stenar i {U['units']} härader och skeppslag. Fördelningen: Attundaland {U['sizes']['attundaland']} härader och {DA['attundaland']} stenar, Tiundaland {U['sizes']['tiundaland']} och {DA['tiundaland']}, Fjädrundaland {U['sizes']['fjadrundaland']} och {DA['fjadrundaland']}, Roden {U['sizes']['roden']} och {DA['roden']}.

Häradernas folkland följer sexårsgärden 1314 (SDHK 2593), som räknar upp Attundalands åtta hundaren och Fjädrundalands fem på samma sätt som här; Tiundaland omfattar där också Gästrikland och Roden. Roden behandlas här som ett eget block. Dess omfattning och ställning är omstridd redan i det medeltida materialet (Dahlbäck m.fl. 1972).

**Rättelsen före publiceringen.** I den första körningen föll {DROP['n']} uppländska stenar bort utan att det märktes, eftersom deras socknar saknade folkland: {DROP['by_group']['faringo']} i Färingö tingslag (Sånga {FP_['Sånga sn']}, Lovö {FP_['Lovö sn']}, Hilleshög {FP_['Hilleshögs sn']}, Skå {FP_['Skå sn']}, Munsö {FP_['Munsö sn']}, Färentuna {FP_['Färentuna sn']}), {DROP['by_group']['adelso']} på Adelsö, {DROP['by_group']['ekero']} i Ekerö och fyra i Stockholm (U 53, U 54 och, på Skansen, U 419 och U 871). Enligt *Det medeltida Sverige* (Ferm m.fl. 1992, s. 19, 44, 114) var Färingö tingslag ”den andra halvan” av Bro härad i Attundaland, Adelsö hörde till Trögds härad i Fjädrundaland till 1540 och Ekerö till Svartlösa härad i Södermanland; de räknas så här, Ekerö alltså till inget folkland. U 419 och U 871 räknas till sina socknar, Norrsunda (Attundaland) och Gryta (Tiundaland). U 53 och U 54 står i Stockholms stad, utanför hundarena, och var de restes är okänt; de räknas inte med. Ortnamnsregistrets ”Ingår i Stockholms stad” (Spånga och Bromma) hade blivit ett nionde härad i Attundaland; socknarna hör till Sollentuna härad (s. 237), och en Spångasten, U 77, flyttades från Roden till Attundaland. Före rättelsen ingick {U1['stones']} stenar i {U1['units']} enheter (Attundaland {DB['attundaland']}, Tiundaland {DB['tiundaland']}, Fjädrundaland {DB['fjadrundaland']}, Roden {DB['roden']}), efter den {U['stones']} i {U['units']}. Allt är omkört, och de första siffrorna står bredvid i avsnitt 5.

De {U['features']} dragen är de av planens 27 som har minst tio stenar med och tio utan draget: korset, kristen markör, bön och bön för själen, resa och död borta, beröm, bro och väg, kvinna bland resarna, kvinna som ensam resare, flera resare, stenar efter barn, förälder, syskon och make, *drengr* och *þegn*, ristarsignatur, bergarten granit, stungna runor, monoftongstavning, r för ʀ, o-runan, prepositionen *at* och ordet *þennsa*. Planens två övriga drag, hednisk markör och ordet *kumbl*, föll bort för att för få stenar har dem. Tiden hålls konstant med fem skikt efter stilgruppens mittår (före 1010, 1010–1040, 1040–1070, efter 1070, odaterad). Dragen är kodade ur Rundatas translitterationer, normaliseringar och översättningar med projektets regler; kodningen är inte handkontrollerad för den här studien.

## 4. Metod

**4.1 Modellen.** För varje drag skattas en logistisk regression med tidsskiktet och blocktillhörigheten, och blocktermens kvottest ger ett χ²-värde: hur mycket bättre stenarnas drag förutsägs när man vet vilket block de står i. Måttet är summan av χ² över alla {U['features']} drag. Andramåttet är antalet drag med p < 0,05.

**4.2 Slumpindelningarna och halvorna.** 999 slumpindelningar byggs av samma {U['units']} härader i fyra block med lika många härader som de verkliga folklanden ({U['sizes']['attundaland']}, {U['sizes']['tiundaland']}, {U['sizes']['fjadrundaland']} och {U['sizes']['roden']}). Varje block växer från en slumpvald starthärad till slumpvald granne tills det har sin storlek; en indelning som inte går att fullborda görs om. Halvorna: socknarna i Uppland delas varannan efter medeldatering, och provet görs om i varje halva med samma 999 indelningar.

**4.3 Känslighetsanalyserna.** Samma prov på fyra urval enligt tilläggsplanen: bara stenar på sin ursprungliga plats; utan alla stenar av de fem flitigaste ristarna (Öpir, Fot, Balle, Åsmund, Gunnar, säkra och osäkra attribueringar); bara daterade stenar; utan förlorade stenar. Varje steg håller om p < 0,05.

**4.4 Avvikelser från planen.** (1) Planens grannregel (socknar inom 10 km) lämnade Värmdö skeppslag och Våla härad utan grannar, så att inga sammanhängande indelningar kunde byggas; före något resultat vidgades den till 20 km, och en härad utan grannar får sin närmaste som granne (låst avvikelse). (2) Provet utan bergarten granit gjordes efter huvudresultatet och ligger utanför planen; det redovisas som explorativt. (3) Vilka drag som bär skillnaden räknades efter resultatet och är beskrivande. (4) Landindelningen rättades 5 november 2026, efter att resultaten setts, och allt kördes om med samma kod och slumpfrö: elva socknars medeltida härad efter *Det medeltida Sverige* (avsnitt 3), Rundatas ”(nu …)” efter sockennamnet stryks, och en sten som flyttats långt från sin socken knyts till den. Metoden är oförändrad, och den första körningens resultat är sparade. Inga andra avvikelser.

## 5. Resultat

**5.1 Huvudprovet.** De verkliga folklanden ger summan {r0(A['chi2_real'])}. De 999 slumpindelningarna ger i median {r0(A['chi2_median_random'])}, och 95:e percentilen ligger vid {r0(A['chi2_p95_random'])}. {NUM[N_GE][0].capitalize()} slumpindelningar når lika högt: p = {pf(A['p'])}, och Holm-korrigerat över planens två prov {pf(HOLM_U)}. Antalet drag som skiljer är {A['k_real']} mot i median {A['k_median_random']:.0f} (p = {pf(A['p_k'])}). I halvorna: {r0(HA['chi2_real'])} mot median {r0(HA['chi2_median_random'])} och {r0(HB['chi2_real'])} mot {r0(HB['chi2_median_random'])}; ingen slumpindelning når upp i någon av dem (p = {pf(HA['p'])} i båda). Före rättelsen: {r0(A1['chi2_real'])} mot median {r0(A1['chi2_median_random'])}, ingen slumpindelning nådde upp (p = {pf(A1['p'])}), och halvorna {r0(HA1['chi2_real'])} och {r0(HB1['chi2_real'])} (p = {pf(HA1['p'])} i båda).

I klartext: folklandens gränser skiljer runstenarnas språk, sed och utförande ungefär dubbelt så mycket som en typisk slumpgräns dragen genom samma härader, och av 999 slumpvisa sätt att dela Uppland i fyra lika stora, sammanhängande delar kom bara {NUM[N_GE][0]} upp i samma nivå som de verkliga folklanden. Om folklanden bara vore godtyckliga block skulle ett så högt värde uppstå i ungefär tre fall av tusen.

Smålands små land, det sekundära provet: {S['units']} härader (före rättelsen {S1['units']}; två stenar som står i Jönköping knyts nu till sina socknar), {S['stones']} stenar och {S['features']} drag; summan {r0(S['alla']['chi2_real'])} mot median {r0(S['alla']['chi2_median_random'])} (p = {pf(P_SM)}; före rättelsen {pf(P_SM1)}). De små landen skiljer inte stenarna mer än slumpblock gör.

{chart('sv')}

**5.2 Vilka drag (beskrivande).** De fem drag som bidrar mest är korset, bergarten granit, monoftongstavningen, prepositionen *at* och r för ʀ. Korset står på sex av tio stenar i Attundaland och Tiundaland men på en av tre i Fjädrundaland och fyra av tio i Roden; *at* står på ungefär var sjunde sten i Attundaland (var åttonde före rättelsen) mot fyra av tio i Fjädrundaland; r för ʀ på hälften av stenarna i Fjädrundaland mot en av sju i Attundaland.

Så ser skillnaden ut på stenarna. Samma ristare, Öpir, skrev *at* i Tiundaland men *æftiR* i Attundaland, och samma ord, *þæiR* ’de’, stavas med r-runan i Fjädrundaland men med yr-runan i Tiundaland (runorna återges med den yngre futharkens vanliga former efter Rundatas translitteration, inte med stenarnas exakta former):
- Tiundaland, U 1177 i Harbo, ristad av Öpir: {EX['u1177']} – *litu risa stin at tuba*, ’lät resa stenen efter Tobbe’.
- Attundaland, U 181 i Össeby-Garn, ristad av Öpir: {EX['u181']} – *iftiR est faþur sin*, ’efter Äst, sin fader’.
- Fjädrundaland, U 749 i Husby-Sjutolft, attribuerad till Balle: {EX['u749']} – *þair litu rasa stan*, ’de lät resa stenen’, med ʀ i *þæiR* skrivet med r-runan ᚱ.
- Tiundaland, U 974 i Vaksala, attribuerad till Öpir: {EX['u974']} – *þaiR*, samma ord med yr-runan ᛦ.

**5.3 Känslighetsanalyserna och kalibreringen.** Alla fyra förregistrerade steg håller, som före rättelsen (då p mellan {pf(min(LAD1.values()))} och {pf(max(LAD1.values()))}):
- Bara stenar på sin ursprungliga plats ({LAD['pa_plats'][0]} stenar): {LAD['pa_plats'][1]} mot median {LAD['pa_plats'][2]}, p = {pf(LAD['pa_plats'][3])}.
- Utan de fem flitigaste ristarnas stenar ({LAD['utan_fem_ristare'][0]}): {LAD['utan_fem_ristare'][1]} mot {LAD['utan_fem_ristare'][2]}, p = {pf(LAD['utan_fem_ristare'][3])}.
- Bara daterade stenar ({LAD['daterade'][0]}): {LAD['daterade'][1]} mot {LAD['daterade'][2]}, p = {pf(LAD['daterade'][3])}.
- Utan förlorade stenar ({LAD['utan_forlorade'][0]}): {LAD['utan_forlorade'][1]} mot {LAD['utan_forlorade'][2]}, p = {pf(LAD['utan_forlorade'][3])}.
- Explorativt, utan bergarten granit ({KS['features']} drag): {r0(KS['alla']['chi2_real'])} mot {r0(KS['alla']['chi2_median_random'])}, p = {pf(KS['alla']['p'])}; i halvorna p = {pf(KS['A']['p'])} och {pf(KS['B']['p'])} (före rättelsen p = {pf(KS1['alla']['p'])}). Skillnaden bärs alltså inte av bergarten granit.

Kalibreringen: måttet jämförs med slumpindelningarna, inte med noll; redan sammanhängande slumpblock ger i median {r0(A['chi2_median_random'])}, eftersom grannbygder liknar varandra. Med 999 indelningar kan p inte bli lägre än 0,001 (Phipson & Smyth 2010). Modellen är inte kontrollerad på annat sätt. Att {N_NOW} stenar kom med genom rättelsen ändrade summan från {r0(A1['chi2_real'])} till {r0(A['chi2_real'])} och p från {pf(A1['p'])} till {pf(A['p'])}, men inte utfallet.

**5.4 Uppföljning: gränserna en och en.** Gränsskannern (egen låst plan) prövade varje par av angränsande regioner med minst 40 stenar och frågade om skillnaden finns kvar bland stenarna inom tio kilometer från gränsen. Efter rättelsen är {len(H2)} kombinationer av {len({f for f, _ in H2})} drag skarpa vid en gräns och håller i båda halvorna, alla mellan Upplands folkland: *at* och bergarten granit mellan Tiundaland och Attundaland; korset, flera resare, beröm och r för ʀ mellan Tiundaland och Fjädrundaland; och flera resare mellan Attundaland och Fjädrundaland, det sista på bara {FR_AF['border_high'][1] + FR_AF['border_low'][1]} stenar. Före rättelsen var det {len(H1)} kombinationer av {len({f for f, _ in H1})} drag; korset mellan Attundaland och Roden är fortfarande skarpt men håller inte längre i båda halvorna, och beröm håller nu. Gränsen mellan Attundaland och Fjädrundaland på Mälaröarna har nu stenar på båda sidor ({min(AF_N)}–{max(AF_N)} per drag, före rättelsen högst {max(AF_N1)}). Där är *at* inte skarpt: {AT_AF['border_high'][0]} av {AT_AF['border_high'][1]} stenar på Fjädrundalands sida mot {AT_AF['border_low'][0]} av {AT_AF['border_low'][1]} på Attundalands (p = {pf(AT_AF['p_border'])}), och för de flesta drag är stenarna för få; planen satte ingen minsta storlek på gränszonen. Gränsen för *at* mellan Tiundaland och Attundaland håller också med ristaren som slumpeffekt (egen låst plan): i tiokilometersbandet är oddsen för *at* ungefär sex gånger så höga på Tiundalands sida (oddskvot {d1(AR['step1']['border']['or'])}).

## 6. Diskussion

Resultatet säger att folklandens gränser inte är vilka gränser som helst: de skiljer stenarna åt mer än nästan alla sammanhängande slumpblock av samma storlek, i båda halvorna av materialet och i alla förregistrerade känslighetsanalyser. Eftersom stenarna i huvudsak är från 1000-talet och folklanden är kända först från omkring 1120, talar det för att indelningen – eller de bygdegemenskaper den byggde på – fanns redan när stenarna restes. Det stämmer med Larssons (1993) förslag om en organisation från slutet av 900-talet, men provet kan inte skilja en administrativ indelning från äldre bygder som indelningen sedan följde.

Mot tidigare forskning: Palm (1992) såg redan skillnaden i *at* mellan Tiundaland och Attundaland, och Larsson (2002) att Uppland hör till de områden där ʀ oftare skrivs med r-runan. Det nya här är att gränserna prövas som helhet, mot en nollhypotes som tar hänsyn till att grannbygder liknar varandra, och att de håller.

Svagheterna i ordning efter vikt: (1) Indelningen är känd från 1300-talet. Häradernas folkland bygger på sexårsgärden 1314 och häradernas gränser på senare register; hundarena kan ha sett annorlunda ut på 1000-talet. (2) Landindelningen rättades efter att resultaten setts; rättelsen följer en oberoende källa och ändrade inte utfallet, men enskilda socknar är osäkra: Lovö var eget skeppslag 1409 och räknas här till Bro härad, Ekerö räknas till Södermanland och två stenar i Stockholm står utanför. (3) Roden är omstritt och behandlas här som ett eget block. (4) Dragen hänger ihop (kors och kristna formler, flera resare och relationerna), så summan av χ² räknar sådana drag flera gånger; provet är ändå giltigt eftersom nollfördelningen bygger på samma drag, men måttet är inget antal oberoende skillnader. (5) Slumpblocken har lika många härader som folklanden, inte lika många stenar. (6) Ristarna: utan de fem flitigaste håller provet, men mindre verkstäder kan bära delar av skillnaden; provet skiljer inte land från verkstad. (7) Smålands negativa resultat kan bero på för få stenar. (8) Peterson (1996), som enligt titeln handlar om just *at*, har vi inte kunnat läsa; om den redan beskriver en gräns vet vi inte.

Fyndet faller om andra sammanhängande indelningar av Uppland som följer naturliga gränser, till exempel vattendrag eller skogsbälten, skiljer stenarna lika mycket som folklanden; eller om ett oberoende material, som gravskicket eller ortnamnen, inte visar samma gränser.

## 7. Slutsats

Upplands folkland skiljer runstenarna åt ungefär dubbelt så mycket som en typisk slumpvis indelning av samma bygder, och bara {NUM[N_GE][0]} av 999 slumpindelningar når lika långt. Det talar för att indelningen, eller de bygder den byggde på, fanns redan på 1000-talet.

## Data och kod

Analysen är gjord i Vitki {APP_VERSION}, ett öppet forskningsverktyg för runstenar ([vitkirunor.se]({SITE})). Kodläge i https://github.com/Precatio/runes: {CODE_SV}. Koden och resultatfilerna finns där under GPL-3.0.

- Data: Rundata (version 2014 med RUNDATA.xls uppdaterad 2018), fryst 2026-10-04. Dragtabellen `utdata/upptackt_v3/drag.csv` på materialets version (korpusens fingeravtryck) `e83202e01a5e6d27`, beräknad 2026-10-29; flyttade och förlorade stenar för känslighetsanalyserna ur `7b9061c9a1c12c73` (2026-11-02). ISOF:s socknar och härader hämtade 2026-11-02 (PlaceNameService, CC BY). Landindelningen `web/src/lib/historiska_land.json` (rättelserna under `parish_medieval`), `data/geo/socknar_land.csv` och `web/public/geo/sten_land.json` i rättad form 2026-11-05; före rättelsen commit {BEFORE_COMMIT}; stenarna som bytte land i `utdata/folkland/landrattelse.json`.
- Planerna: `analysplaner/2026-11-02-gamla-granser-nya-monster.md`, avvikelsen `analysplaner/2026-11-02-gamla-granser-nya-monster-avvikelse.md`, tilläggsplanen `analysplaner/2026-11-02-folkland-slumpindelning-trappa.md`, med kontrollsummor bredvid.
- Huvudprovet: `utdata/gamla_granser/monster.py` → `monster.json`; känslighetsanalyserna `monster_trappa.py` → `monster_trappa.json`; provet utan granit `monster_kanslighet.py`; dragen `monster_drag.py`; den första körningen i `*_v1.json` bredvid. Gränsskannern: `utdata/granser/gransskannern.py`; *at* med ristarna: `utdata/folkland/at_ristare.R`.
- Regionerna: `src/regions.py`, `scripts/assign_historiska_land.py` (ISOF:s ortnamnsregister som första källa, Det medeltida Sverige för de rättade socknarna), `scripts/assign_sten_land.py`, kontrollen mot sexårsgärden `utdata/geografi/sexarsgard_1314.py`.
- Rapporten byggs av `utdata/blogg/build/build_rapport_folkland.py`, som läser alla tal ur resultatfilerna och stannar om något inte stämmer. Mallen: `utdata/rapporter/MALL.md`, version 4. Ordlista: {SITE}/forskningsrapporter/begrepp.
- I Vitki syns folklanden på kartan (gränslagret Små land) och i statistiken efter de gamla gränserna. Populärt berättat i serien [De gamla landen]({SITE}/artiklar/de-gamla-landen-sotholm).

## Referenser

- Dahlbäck, G., Jansson, B. & Westin, G. T. 1972. *Det medeltida Sverige* 1. Uppland 1. Norra Roden. Stockholm: Kungl. Vitterhets Historie och Antikvitets Akademien.
- Ferm, O., Johansson, M. & Rahmqvist, S. 1992. *Det medeltida Sverige* 1. Uppland 7. Attundaland: Bro, Färingö, Adelsö, Sollentuna. Stockholm: Riksantikvarieämbetet.
- Holm, S. 1979. A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics* 6 (2), s. 65–70.
- Institutet för språk och folkminnen. Ortnamnsregistret, PlaceNameService: socknar och härader. https://placenameservice.isof.se, hämtat 2026-11-02. CC BY.
- Larsson, M. G. 1993. Kung Eriks nyordning? Spår efter samhällsorganisation i vikingatidens Uppland. *Uppland* 1993, s. 105–134.
- Larsson, P. 2002. *Yrrunan. Användning och ljudvärde i nordiska runinskrifter.* Runrön 17. Uppsala.
- Palm, R. 1992. *Runor och regionalitet. Studier av variation i de nordiska minnesinskrifterna.* Runrön 7. Uppsala.
- Peterson, L. 1996. Aft/æft, at och æftir på de nordiska runstenarna – regional variation eller vad? I: *Mål i sikte* (Uppsala), s. 239–252. (Inte läst.)
- Phipson, B. & Smyth, G. K. 2010. Permutation p-values should never be zero. *Statistical Applications in Genetics and Molecular Biology* 9 (1), artikel 39.
- Riksarkivet. Svenskt diplomatariums huvudkartotek (SDHK) nr 2593 (DS 1946), sexårsgärden 1314. CC BY 4.0.
- Samnordisk runtextdatabas (Rundata), version 2014 med RUNDATA.xls uppdaterad 2018. Institutionen för nordiska språk, Uppsala universitet. https://www.nordiska.uu.se/forskn/samnord.htm, hämtad 2026-10-04. Open Database License (ODbL) 1.0.
- Stille, P. 1999. *Runstenar och runristare i det vikingatida Fjädrundaland. En studie i attribuering.* Runrön 13. Uppsala.

:::box Det viktigaste i korthet
- Upplands folkland skiljer runstenarna mer än nästan alla andra sätt att dela samma bygder i lika stora, sammanhängande block; gränserna är inte vilka gränser som helst.
- Skillnaderna syns både i hur stenarna skrevs (*at*, r för ʀ, monoftongen) och i seden (korset, flera resare).
- Att indelningen, eller bygderna den byggde på, fanns redan när stenarna restes är en tolkning som resultatet stöder men inte bevisar; varför gränserna skilde – språk, sed eller verkstäder – avgör provet inte.
- Smålands små land visar inget motsvarande.
:::"""

body_en = f"""*Viktor Kvant, independent researcher. Fully tested finding. Report version {REPORT_VERSION}, {TODAY}. Timeline: {TL_EN}. The analysis was done in Vitki {APP_VERSION}. Licence CC BY 4.0. The English version is the canonical one for citation: {CITE_EN}. Keywords: runestones, Viking Age, Uppland, folkland, hundred, regional variation, permutation test, logistic regression. Competing interests: none. Funding: none.*

## Abstract

**Background and aim.** In the Middle Ages Uppland was not one province but three folklands – Tiundaland, Attundaland and Fjädrundaland – and the coastal land Roden, with a common law only from 1296. How old the folklands are is not known: they are first mentioned around 1120, and it has been suggested that the division goes back to the late tenth century. The runestones were raised precisely in the eleventh century. If the folkland borders already separated people then, the stones should differ more across those borders than across other borders through the same districts.

**Material.** {U['stones']} Viking-age runestones in Uppland with known location, in {U['units']} hundreds and ship districts with their folkland according to the six-year tithe of 1314 and, for the islands of Lake Mälaren, *Det medeltida Sverige*; {U['features']} features of language, formulas, family, carving and stone. Before publication the land assignment was corrected: {DROP['n']} stones had dropped out because their parishes had no folkland, and {N_NOW} of them are now included.

**Method.** For each feature we measured how much block membership explains, with time held constant (logistic regression, likelihood-ratio test), and the sum over the features was compared with the same sum for 999 random divisions of the same hundreds into four contiguous blocks of the same size. The plan was locked before the run.

**Results.** The real folklands give a sum of {r0(A['chi2_real'])}; the random divisions give a median of {r0(A['chi2_median_random'])}, and the top twentieth begins at {r0(A['chi2_p95_random'])}. Only {N_GE} of 999 reach as high (p = {pf(A['p'], True)}; Holm-corrected {pf(HOLM_U, True)}), in both halves none (p = {pf(HA['p'], True)}), and the test holds in all four pre-registered sensitivity analyses (p {pf(PMIN, True)}–{pf(PMAX, True)}). Before the correction: {r0(A1['chi2_real'])}, and none reached it (p = {pf(A1['p'], True)}). Småland's small lands differ no more than random blocks (p = {pf(P_SM, True)}).

**Conclusion.** The folkland borders separate the runestones about twice as much as a typical random border through the same districts. This suggests that the division, or something that preceded it, existed already when the stones were raised, but the test does not decide what set them apart – language, custom or workshops.

## 1. Introduction

That Uppland's runestones vary within the province is known. Palm (1992) showed that the preposition *at* is more common in Tiundaland than in Attundaland and drew his study areas along the folkland borders. Larsson (2002, pp. 168–170) asked why Gotland, Uppland and Västergötland have a much higher share of ʀ written with the r-rune than other areas; in Västergötland most instances come from one hundred, Vadsbo, but for Uppland he held that the geographical position as such is hardly the explanation, rather chronological and partly individual factors. Stille (1999) studied the carvers of a single folkland, Fjädrundaland. Peterson (1996), by its title, deals with exactly the choice between *aft/æft*, *at* and *æftiR* and whether it is regional variation; we have not been able to read the article. On the age of the folklands, Mats G. Larsson (1993, p. 114) has suggested that both the levy and the folkland division were organised by Erik the Victorious in the later tenth century; the folklands are first named in a Latin text of about 1120, and two of them in an account that may go back to the mid-eleventh century (pp. 106 f.).

What is missing is a test of the borders themselves. That two areas differ says nothing yet about the border between them: neighbouring districts resemble each other, and almost any division of a province produces differences between its parts. The question is therefore whether the folkland borders separate the stones more than other borders, drawn through the same districts, do. It is tested here with a permutation test in which the real folklands are compared with random divisions of the same hundreds.

## 2. Pre-registration

The plan (*New patterns with the Viking-age division*, step 1) was locked on 2 November 2026 with SHA-256 {SHA[PLANS[0]][:16]}…, before the test was run. The hypothesis, translated in full: "If the folklands were merely arbitrary blocks of neighbouring districts, any blocks would differ as much, since neighbouring stones resemble each other." The decision rule: the folklands are special if their sum lies above the 95th percentile of the random divisions (p = (1 + number ≥ real) / 1000 < 0.05), and the same rank is reported in both halves.

One deviation was locked before any result had been computed (SHA-256 {SHA[PLANS[1]][:16]}…): the neighbour rule had to be widened, see 4.4. The sensitivity analyses were locked in a separate addendum after the main test but before they were run (SHA-256 {SHA[PLANS[2]][:16]}…). The land assignment was corrected after the review before publication and everything was rerun, after the results had been seen (4.4).

Seen before locking: that *at* changes sharply at the border between Tiundaland and Attundaland (its own locked plan the day before, SHA-256 {SHA[PLANS[4]][:16]}…), and that a border scan (its own plan, SHA-256 {SHA[PLANS[3]][:16]}…) had found sharp borders, all between the folklands. The main test is therefore not a blind discovery: it tests whether a pattern seen at single borders holds for the division as a whole, against an explicit null hypothesis. Confirmatory: step 1 for Uppland. Secondary: step 1 for Småland. Follow-up under its own locked plan: the sensitivity analyses. Exploratory: the test without the rock type and which features carry the difference.

## 3. Material

The runestones come from the Scandinavian Runic-text Database (Rundata), 2014 version with RUNDATA.xls updated 2018, frozen for the analysis on 4 October 2026. The selection: Viking-age runestones in Uppland whose parish can be linked to a hundred in the place-name register of the Institute for Language and Folklore (the same parish name within 25 km, otherwise the nearest parish within 15 km) and whose hundred belongs to a folkland: {U['stones']} stones in {U['units']} hundreds and ship districts. The distribution: Attundaland {U['sizes']['attundaland']} hundreds and {DA['attundaland']} stones, Tiundaland {U['sizes']['tiundaland']} and {DA['tiundaland']}, Fjädrundaland {U['sizes']['fjadrundaland']} and {DA['fjadrundaland']}, Roden {U['sizes']['roden']} and {DA['roden']}.

The folkland of each hundred follows the six-year tithe of 1314 (SDHK 2593), which lists Attundaland's eight hundreds and Fjädrundaland's five as here; Tiundaland there also includes Gästrikland and Roden. Roden is treated here as a block of its own. Its extent and status are disputed already in the medieval material (Dahlbäck et al. 1972).

**The correction before publication.** In the first run {DROP['n']} stones from Uppland dropped out unnoticed, because their parishes had no folkland: {DROP['by_group']['faringo']} in Färingö tingslag (Sånga {FP_['Sånga sn']}, Lovö {FP_['Lovö sn']}, Hilleshög {FP_['Hilleshögs sn']}, Skå {FP_['Skå sn']}, Munsö {FP_['Munsö sn']}, Färentuna {FP_['Färentuna sn']}), {DROP['by_group']['adelso']} on Adelsö, {DROP['by_group']['ekero']} in Ekerö and four in Stockholm (U 53, U 54 and, at Skansen, U 419 and U 871). According to *Det medeltida Sverige* (Ferm et al. 1992, pp. 19, 44, 114), Färingö tingslag was "the other half" of the hundred of Bro in Attundaland, Adelsö belonged to the hundred of Trögd in Fjädrundaland until 1540, and Ekerö to the hundred of Svartlösa in Södermanland; they are counted so here, Ekerö thus to no folkland. U 419 and U 871 are counted to their parishes, Norrsunda (Attundaland) and Gryta (Tiundaland). U 53 and U 54 stand in the town of Stockholm, outside the hundreds, and where they were raised is unknown; they are not included. The place-name register's "Ingår i Stockholms stad" (part of the town of Stockholm: Spånga and Bromma) had become a ninth hundred in Attundaland; the parishes belong to the hundred of Sollentuna (p. 237), and one stone from Spånga, U 77, moved from Roden to Attundaland. Before the correction {U1['stones']} stones in {U1['units']} units were included (Attundaland {DB['attundaland']}, Tiundaland {DB['tiundaland']}, Fjädrundaland {DB['fjadrundaland']}, Roden {DB['roden']}), after it {U['stones']} in {U['units']}. Everything has been rerun, and the first figures are given alongside in section 5.

The {U['features']} features are those of the plan's 27 that have at least ten stones with and ten without the feature: the cross, a Christian marker, prayer and prayer for the soul, journey and death abroad, praise, bridge and road, a woman among the raisers, a woman as sole raiser, several raisers, stones for a child, parent, sibling and spouse, *drengr* and *þegn*, the carver's signature, the rock type granite, dotted runes, monophthong spelling, r for ʀ, the o-rune, the preposition *at* and the word *þennsa*. The plan's two other features, a pagan marker and the word *kumbl*, fell out because too few stones have them. Time is held constant with five strata by the midpoint of the style group (before 1010, 1010–1040, 1040–1070, after 1070, undated). The features are coded from Rundata's transliterations, normalisations and translations with the project's rules; the coding has not been hand-checked for this study.

## 4. Method

**4.1 The model.** For each feature a logistic regression with the time stratum and the block membership is estimated, and the likelihood-ratio test of the block term gives a χ² value: how much better the stones' features are predicted when one knows which block they stand in. The measure is the sum of χ² over all {U['features']} features. The second measure is the number of features with p < 0.05.

**4.2 The random divisions and the halves.** 999 random divisions are built from the same {U['units']} hundreds into four blocks with as many hundreds as the real folklands ({U['sizes']['attundaland']}, {U['sizes']['tiundaland']}, {U['sizes']['fjadrundaland']} and {U['sizes']['roden']}). Each block grows from a randomly chosen starting hundred to a randomly chosen neighbour until it has its size; a division that cannot be completed is redrawn. The halves: Uppland's parishes are split alternately by mean dating, and the test is repeated in each half with the same 999 divisions.

**4.3 The sensitivity analyses.** The same test on four selections according to the addendum: only stones in their original place; without all stones by the five most prolific carvers (Öpir, Fot, Balle, Åsmund, Gunnar, certain and uncertain attributions); only dated stones; without lost stones. Each step holds if p < 0.05.

**4.4 Deviations from the plan.** (1) The plan's neighbour rule (parishes within 10 km) left the ship district of Värmdö and the hundred of Våla without neighbours, so that no contiguous divisions could be built; before any result it was widened to 20 km, and a hundred without neighbours gets its nearest as neighbour (locked deviation). (2) The test without the rock type granite was run after the main result and lies outside the plan; it is reported as exploratory. (3) Which features carry the difference was computed after the result and is descriptive. (4) The land assignment was corrected on 5 November 2026, after the results had been seen, and everything was rerun with the same code and random seed: the medieval hundred of eleven parishes after *Det medeltida Sverige* (section 3), Rundata's "(nu …)" ("now …") after the parish name is dropped, and a stone moved far from its parish is linked to it. The method is unchanged, and the first run's results are kept. No other deviations.

## 5. Results

**5.1 The main test.** The real folklands give a sum of {r0(A['chi2_real'])}. The 999 random divisions give a median of {r0(A['chi2_median_random'])}, and the 95th percentile lies at {r0(A['chi2_p95_random'])}. {NUM[N_GE][1].capitalize()} random divisions reach as high: p = {pf(A['p'], True)}, and Holm-corrected over the plan's two tests {pf(HOLM_U, True)}. The number of differing features is {A['k_real']} against a median of {A['k_median_random']:.0f} (p = {pf(A['p_k'], True)}). In the halves: {r0(HA['chi2_real'])} against a median of {r0(HA['chi2_median_random'])} and {r0(HB['chi2_real'])} against {r0(HB['chi2_median_random'])}; no random division reaches the folklands in either (p = {pf(HA['p'], True)} in both). Before the correction: {r0(A1['chi2_real'])} against a median of {r0(A1['chi2_median_random'])}, no random division reached it (p = {pf(A1['p'], True)}), and the halves {r0(HA1['chi2_real'])} and {r0(HB1['chi2_real'])} (p = {pf(HA1['p'], True)} in both).

In plain words: the folkland borders separate the language, custom and execution of the runestones about twice as much as a typical random border drawn through the same hundreds, and of 999 random ways of dividing Uppland into four equally large, contiguous parts, only {NUM[N_GE][1]} reached the level of the real folklands. If the folklands were merely arbitrary blocks, a value this high would arise in about three cases in a thousand.

Småland's small lands, the secondary test: {S['units']} hundreds (before the correction {S1['units']}; two stones standing in Jönköping are now linked to their parishes), {S['stones']} stones and {S['features']} features; the sum {r0(S['alla']['chi2_real'])} against a median of {r0(S['alla']['chi2_median_random'])} (p = {pf(P_SM, True)}; before the correction {pf(P_SM1, True)}). The small lands separate the stones no more than random blocks do.

{chart('en')}

**5.2 Which features (descriptive).** The five features that contribute most are the cross, the rock type granite, monophthong spelling, the preposition *at* and r for ʀ. The cross is on six stones in ten in Attundaland and Tiundaland but on one in three in Fjädrundaland and four in ten in Roden; *at* is on about one stone in seven in Attundaland (one in eight before the correction) against four in ten in Fjädrundaland; r for ʀ on half the stones in Fjädrundaland against one in seven in Attundaland.

This is what the difference looks like on the stones. The same carver, Öpir, wrote *at* in Tiundaland but *æftiR* in Attundaland, and the same word, *þæiR* 'they', is spelled with the r-rune in Fjädrundaland but with the yr-rune in Tiundaland (the runes are rendered with the usual younger-futhark forms after Rundata's transliteration, not with the stones' exact forms):
- Tiundaland, U 1177 at Harbo, carved by Öpir: {EX['u1177']} – *litu risa stin at tuba*, 'had the stone raised in memory of Tobbe'.
- Attundaland, U 181 at Össeby-Garn, carved by Öpir: {EX['u181']} – *iftiR est faþur sin*, 'in memory of Äst, their father'.
- Fjädrundaland, U 749 at Husby-Sjutolft, attributed to Balle: {EX['u749']} – *þair litu rasa stan*, 'they had the stone raised', with the ʀ of *þæiR* written with the r-rune ᚱ.
- Tiundaland, U 974 at Vaksala, attributed to Öpir: {EX['u974']} – *þaiR*, the same word with the yr-rune ᛦ.

**5.3 The sensitivity analyses and the calibration.** All four pre-registered steps hold, as before the correction (then p between {pf(min(LAD1.values()), True)} and {pf(max(LAD1.values()), True)}):
- Only stones in their original place ({LAD['pa_plats'][0]} stones): {LAD['pa_plats'][1]} against a median of {LAD['pa_plats'][2]}, p = {pf(LAD['pa_plats'][3], True)}.
- Without the stones of the five most prolific carvers ({LAD['utan_fem_ristare'][0]}): {LAD['utan_fem_ristare'][1]} against {LAD['utan_fem_ristare'][2]}, p = {pf(LAD['utan_fem_ristare'][3], True)}.
- Only dated stones ({LAD['daterade'][0]}): {LAD['daterade'][1]} against {LAD['daterade'][2]}, p = {pf(LAD['daterade'][3], True)}.
- Without lost stones ({LAD['utan_forlorade'][0]}): {LAD['utan_forlorade'][1]} against {LAD['utan_forlorade'][2]}, p = {pf(LAD['utan_forlorade'][3], True)}.
- Exploratory, without the rock type granite ({KS['features']} features): {r0(KS['alla']['chi2_real'])} against {r0(KS['alla']['chi2_median_random'])}, p = {pf(KS['alla']['p'], True)}; in the halves p = {pf(KS['A']['p'], True)} and {pf(KS['B']['p'], True)} (before the correction p = {pf(KS1['alla']['p'], True)}). The difference is thus not carried by the rock type granite.

The calibration: the measure is compared with the random divisions, not with zero; contiguous random blocks already give a median of {r0(A['chi2_median_random'])}, because neighbouring districts resemble each other. With 999 divisions p cannot be lower than 0.001 (Phipson & Smyth 2010). The model has not been checked in other ways. That {N_NOW} stones came in through the correction changed the sum from {r0(A1['chi2_real'])} to {r0(A['chi2_real'])} and p from {pf(A1['p'], True)} to {pf(A['p'], True)}, but not the outcome.

**5.4 Follow-up: the borders one by one.** A border scan (its own locked plan) tested every pair of neighbouring regions with at least 40 stones and asked whether the difference remains among the stones within ten kilometres of the border. After the correction {len(H2)} combinations of {len({f for f, _ in H2})} features are sharp at a border and hold in both halves, all between Uppland's folklands: *at* and the rock type granite between Tiundaland and Attundaland; the cross, several raisers, praise and r for ʀ between Tiundaland and Fjädrundaland; and several raisers between Attundaland and Fjädrundaland, the last on only {FR_AF['border_high'][1] + FR_AF['border_low'][1]} stones. Before the correction there were {len(H1)} combinations of {len({f for f, _ in H1})} features; the cross between Attundaland and Roden is still sharp but no longer holds in both halves, and praise now holds. The border between Attundaland and Fjädrundaland on the islands of Lake Mälaren now has stones on both sides ({min(AF_N)}–{max(AF_N)} per feature, before the correction at most {max(AF_N1)}). There *at* is not sharp: {AT_AF['border_high'][0]} of {AT_AF['border_high'][1]} stones on Fjädrundaland's side against {AT_AF['border_low'][0]} of {AT_AF['border_low'][1]} on Attundaland's (p = {pf(AT_AF['p_border'], True)}), and for most features the stones are too few; the plan set no minimum size for the border zone. The border for *at* between Tiundaland and Attundaland also holds with the carver as a random effect (its own locked plan): in the ten-kilometre band the odds of *at* are about six times as high on Tiundaland's side (odds ratio {AR['step1']['border']['or']:.1f}).

## 6. Discussion

The result says that the folkland borders are not just any borders: they separate the stones more than almost all contiguous random blocks of the same size, in both halves of the material and in every pre-registered sensitivity analysis. Since the stones are mainly from the eleventh century and the folklands are known only from around 1120, this suggests that the division – or the district communities it was built on – existed already when the stones were raised. This agrees with Larsson's (1993) proposal of an organisation from the late tenth century, but the test cannot tell an administrative division from older districts that the division later followed.

Against earlier research: Palm (1992) already saw the difference in *at* between Tiundaland and Attundaland, and Larsson (2002) that Uppland is among the areas where ʀ is more often written with the r-rune. What is new here is that the borders are tested as a whole, against a null hypothesis that takes into account that neighbouring districts resemble each other, and that they hold.

The weaknesses in order of importance: (1) The division is known from the fourteenth century. The hundreds' folklands rest on the six-year tithe of 1314 and the hundreds' borders on later registers; the hundreds may have looked different in the eleventh century. (2) The land assignment was corrected after the results had been seen; the correction follows an independent source and did not change the outcome, but single parishes are uncertain: Lovö was a ship district of its own in 1409 and is counted here to the hundred of Bro, Ekerö is counted to Södermanland and two stones in Stockholm stay outside. (3) Roden is disputed and is treated here as a block of its own. (4) The features are related (the cross and Christian formulas, several raisers and the relations), so the sum of χ² counts such features more than once; the test is still valid since the null distribution rests on the same features, but the measure is not a count of independent differences. (5) The random blocks have as many hundreds as the folklands, not as many stones. (6) The carvers: without the five most prolific the test holds, but smaller workshops may still carry part of the difference; the test does not separate land from workshop. (7) Småland's negative result may be due to too few stones. (8) We have not been able to read Peterson (1996), which by its title deals with exactly *at*; whether it already describes a border we do not know.

The finding falls if other contiguous divisions of Uppland that follow natural borders, such as watercourses or forest belts, separate the stones as much as the folklands; or if an independent material, such as burial customs or place names, does not show the same borders.

## 7. Conclusion

Uppland's folklands separate the runestones about twice as much as a typical random division of the same districts, and only {NUM[N_GE][1]} of 999 random divisions reach as far. This suggests that the division, or the districts it was built on, existed already in the eleventh century.

## Data and code

The analysis was done in Vitki {APP_VERSION}, an open research tool for runestones ([vitkirunor.se]({SITE}/en)). Code state in https://github.com/Precatio/runes: {CODE_EN}. The code and result files are there under GPL-3.0.

- Data: Rundata (2014 version with RUNDATA.xls updated 2018), frozen 2026-10-04. The feature table `utdata/upptackt_v3/drag.csv` on the material's version (corpus fingerprint) `e83202e01a5e6d27`, computed 2026-10-29; moved and lost stones for the sensitivity analyses from `7b9061c9a1c12c73` (2026-11-02). ISOF's parishes and hundreds retrieved 2026-11-02 (PlaceNameService, CC BY). The land assignment `web/src/lib/historiska_land.json` (the corrections under `parish_medieval`), `data/geo/socknar_land.csv` and `web/public/geo/sten_land.json` in corrected form 2026-11-05; before the correction commit {BEFORE_COMMIT}; the stones that changed land in `utdata/folkland/landrattelse.json`.
- The plans: `analysplaner/2026-11-02-gamla-granser-nya-monster.md`, the deviation `analysplaner/2026-11-02-gamla-granser-nya-monster-avvikelse.md`, the addendum `analysplaner/2026-11-02-folkland-slumpindelning-trappa.md`, with checksums beside them.
- The main test: `utdata/gamla_granser/monster.py` → `monster.json`; the sensitivity analyses `monster_trappa.py` → `monster_trappa.json`; the test without granite `monster_kanslighet.py`; the features `monster_drag.py`; the first run in `*_v1.json` beside them. The border scan: `utdata/granser/gransskannern.py`; *at* with the carvers: `utdata/folkland/at_ristare.R`.
- The regions: `src/regions.py`, `scripts/assign_historiska_land.py` (the ISOF place-name register as first source, Det medeltida Sverige for the corrected parishes), `scripts/assign_sten_land.py`, the check against the six-year tithe `utdata/geografi/sexarsgard_1314.py`.
- The report is built by `utdata/blogg/build/build_rapport_folkland.py`, which reads every number from the result files and stops if anything does not match. The template: `utdata/rapporter/MALL.md`, version 4. Glossary: {SITE}/en/forskningsrapporter/begrepp.
- In Vitki the folklands are shown on the map (the border layer Small lands) and in the statistics by the old borders. Told for a general audience in the series [The old lands]({SITE}/en/artiklar/de-gamla-landen-sotholm).

## References

- Dahlbäck, G., Jansson, B. & Westin, G. T. 1972. *Det medeltida Sverige* 1. Uppland 1. Norra Roden. Stockholm: Kungl. Vitterhets Historie och Antikvitets Akademien.
- Ferm, O., Johansson, M. & Rahmqvist, S. 1992. *Det medeltida Sverige* 1. Uppland 7. Attundaland: Bro, Färingö, Adelsö, Sollentuna. Stockholm: Riksantikvarieämbetet.
- Holm, S. 1979. A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics* 6 (2), pp. 65–70.
- Institute for Language and Folklore (Institutet för språk och folkminnen). Place-name register, PlaceNameService: parishes and hundreds. https://placenameservice.isof.se, retrieved 2026-11-02. CC BY.
- Larsson, M. G. 1993. Kung Eriks nyordning? Spår efter samhällsorganisation i vikingatidens Uppland. *Uppland* 1993, pp. 105–134.
- Larsson, P. 2002. *Yrrunan. Användning och ljudvärde i nordiska runinskrifter.* Runrön 17. Uppsala.
- Palm, R. 1992. *Runor och regionalitet. Studier av variation i de nordiska minnesinskrifterna.* Runrön 7. Uppsala.
- Peterson, L. 1996. Aft/æft, at och æftir på de nordiska runstenarna – regional variation eller vad? In: *Mål i sikte* (Uppsala), pp. 239–252. (Not read.)
- Phipson, B. & Smyth, G. K. 2010. Permutation p-values should never be zero. *Statistical Applications in Genetics and Molecular Biology* 9 (1), article 39.
- Scandinavian Runic-text Database (Rundata), 2014 version with RUNDATA.xls updated 2018. Department of Scandinavian Languages, Uppsala University. https://www.nordiska.uu.se/forskn/samnord.htm, retrieved 2026-10-04. Open Database License (ODbL) 1.0.
- Stille, P. 1999. *Runstenar och runristare i det vikingatida Fjädrundaland. En studie i attribuering.* Runrön 13. Uppsala.
- Swedish National Archives (Riksarkivet). Swedish Diplomatarium main catalogue (SDHK) no. 2593 (DS 1946), the six-year tithe of 1314. CC BY 4.0.

:::box The essentials in brief
- Uppland's folklands separate the runestones more than almost every other way of dividing the same districts into equally large, contiguous blocks; the borders are not just any borders.
- The differences show both in how the stones were written (*at*, r for ʀ, the monophthong) and in the custom (the cross, several raisers).
- That the division, or the districts it was built on, existed already when the stones were raised is an interpretation the result supports but does not prove; why the borders separated – language, custom or workshops – the test does not decide.
- Småland's small lands show nothing similar.
:::"""

# ---- checks -----------------------------------------------------------------------------------------------------------
# the plain-words sentence rests on these numbers (mallen version 4): twice the median, 2 of 999, about three in a thousand
assert round(RATIO) == 2 and N_GE == 2 and A["p"] == 0.003
assert "I klartext" in body and "In plain words" in body_en and "tre fall av tusen" in body and "three cases in a thousand" in body_en
JARGON = r"modul\w*|trapp\w*|q_global|korpusjobb|fingeravtryck|fingerprint|facit|Vitkis|Vitki's|\bthe app\b|\bappen\b|`[^`]*/[^`]*`|METHODS"
for b, lang in ((body, "sv"), (body_en, "en")):
    assert not re.search(r"^\|", b, re.M), "BlogBody har inga tabeller"
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M)), "varje ruta ska stängas"
    assert "{" not in b and "}" not in b
    head = b.split("## Data")[0]
    assert not re.findall(JARGON, head), re.findall(JARGON, head)
    assert "e83202e01a5e6d27" not in head and "e83202e01a5e6d27" in b  # the corpus version only under Data och kod
    assert not re.search(r"\]\(/", b), "absoluta länkar"
    assert "Någon release" not in b and "No release" not in b
    caps = [ln for ln in b.split("\n") if ln.startswith(("Källa:", "Source:"))]
    assert len(caps) == 1 and caps[0].endswith(CHART_SV if lang == "sv" else CHART_EN), caps
    assert "/forskningsrapporter/begrepp" in b and "hednisk markör" not in head.split("Planens två övriga")[0]
    assert "Peterson, L. 1996. Aft/æft, at och æftir på de nordiska runstenarna – regional variation eller vad?" in b
assert "pagan marker" not in body_en.split("The plan's two other")[0].split("## 3. Material")[1]
assert "bärs alltså inte av bergarten granit" in body and "beror inte på berggrunden" not in body
assert "Det viktigaste i korthet" in body and "## 2. Förregistrering" in body and "## 6. Diskussion" in body
assert body.split("\n", 1)[0].startswith("*Viktor Kvant, oberoende forskare. Fullt prövat fynd. Rapportversion 1, 2026-11-05. Tidslinje:")
assert body_en.split("\n", 1)[0].startswith("*Viktor Kvant, independent researcher. Fully tested finding. Report version 1, 2026-11-05. Timeline:")
# the header line as scripts/zenodo_rapporter.py and web/src/lib/report.ts parse it
_h = body_en.splitlines()[0].strip("* ")
assert re.search(r"Report version (\d+), (\d{4}-\d{2}-\d{2})", _h) and re.search(r"(?:made|done) in Vitki (\d+(?:\.\d+)*)", _h)
assert re.search(r"Keywords: ([^.]+)\.", _h) and "CC BY 4.0" in _h
# the length (mallen: 1 500–3 000 ord på svenska före Data och kod)
WORDS_SV, WORDS_EN = len(body.split("## Data")[0].split()), len(body_en.split("## Data")[0].split())
assert 1500 <= WORDS_SV <= 3000, WORDS_SV

out = {"slug": SLUG, "title": title, "summary": summary, "body": body, "title_en": title_en, "summary_en": summary_en,
       "body_en": body_en, "labels": ["Rapport", "Geografi", "Språk och stavning", "Tro och magi"]}
labels = out["labels"]
assert blog_labels.check(labels) is None
path = os.path.join(ROOT, "utdata", "rapporter", "rapport_folkland.json")
json.dump(out, open(path, "w"), ensure_ascii=False, indent=1)
print(path, len(body.split()), "ord,", WORDS_SV, "före Data och kod;", len(body_en.split()), "words,", WORDS_EN, "before Data and code")

if "--update" in sys.argv or "--write" in sys.argv:
    assert RERUN_COMMIT, "Omkörningen 2026-11-05 måste vara incheckad innan rapporten skrivs (kodläget i Data och kod)"
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
        assert not [p_ for p_ in blog._all() if p_.get("slug") == out["slug"]], "Adressen används redan; skriv över med --update"
        ref = col.document()
        ref.set({**out, "published": False, "month": now.strftime("%Y-%m"), "author": "Viktor Kvant",
                 "topic": "Rapport|folkland", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
