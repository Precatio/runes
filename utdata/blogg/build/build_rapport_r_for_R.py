"""Forskningsrapport (låst mall utdata/rapporter/MALL.md, version 4): "I västra Uppland skrevs ʀ med r på fem gånger så
stor andel av runstenarna som i resten av landet" (sv + en). Klustret ur den rumsliga skanningen (r/hotspots.R),
känslighetsanalyserna (src/robustness.py, METHODS 1v) och de explorativa räkningarna om ristaren Erik och tiden, allt på
korpusens version e83202e01a5e6d27. Figurerna ritas av utdata/rapporter/figurer/karta_r_for_R.R. Varje siffra
asserteras mot filerna. Rapportversion 3 (2026-11-05): rättelser efter granskningen före arkiveringen i Zenodo.
    ../../../.venv/bin/python build_rapport_r_for_R.py [--write | --update DOC]"""
import datetime as dt
import json
import math
import os
import re
import subprocess
import sys

import pandas as pd
from pyproj import Transformer
from scipy import stats

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_figures, blog_labels, r_findings, regions, robustness  # noqa: E402
from src import r_bridge as rb  # noqa: E402
sys.path.insert(0, os.path.join(ROOT, "utdata", "rapporter", "figurer"))
from figur import andringslogg  # noqa: E402

FP = "e83202e01a5e6d27"
C = os.path.join(ROOT, "data", "cache", "r", "corpus", FP)
DONE = json.load(open(os.path.join(C, "done.json"), encoding="utf-8"))
assert DONE["fingerprint"] == FP and DONE["r_version"].startswith("R version 4.6.1")
assert DONE["computed_at"].startswith("2026-10-29")  # härledd korpus beräknad 2026-10-29
APP_VERSION = "3.0.0"  # the Vitki version the analysis was made in (tag v3.0.0 + the commits named in Data och kod), not the current one
assert open(os.path.join(ROOT, "utdata", "rapporter", "MALL.md.sha256")).read().startswith("611a4d5f")  # mallens version 4
REPORT_VERSION = 3  # version 1: 2026-10-31, version 2: 2026-11-01
FIRST = "2026-10-31"  # version 1 publicerades
V2 = "2026-11-01"
TODAY = "2026-11-05"  # rapportversionens datum, fast i byggaren (mallen version 3)
# Kodläget: den commit där analyskoden, resultatfilernas skript, figurerna och byggaren för version 2 ligger (inget i r/ eller
# i korpusjobbets kod som rör rapporten ändrades mellan körningen 2026-10-29 och den; efter den, 2026-11-02, ändrades trappan)
CODE_COMMIT = "4f80a63"
if os.path.isdir(os.path.join(ROOT, ".git")):
    assert subprocess.run(["git", "-C", ROOT, "merge-base", "--is-ancestor", CODE_COMMIT, "HEAD"]).returncode == 0
TL_SV = ("klustret upptäcktes 2026-10-12; den populära artikeln publicerades 2026-10-13; materialet frystes 2026-10-29; "
         "den populära artikeln räknades om 2026-10-31")
TL_EN = ("the cluster was found 2026-10-12; the popular article was published 2026-10-13; the material was frozen 2026-10-29; "
         "the popular article was recomputed 2026-10-31")

pc = lambda x: int(100 * x + 0.5 + 1e-9)  # noqa: E731  (half up; the result files round to 3 decimals, 0.565 is 56.5 %)
d2 = lambda x: f"{x:.2f}".replace(".", ",")  # noqa: E731
d1 = lambda x: f"{x:.1f}".replace(".", ",")  # noqa: E731
sp = lambda n: f"{n:,}".replace(",", " ")  # noqa: E731
en_n = lambda n: f"{n:,}"  # noqa: E731


def pfmt(p, en=False):
    if p < 0.001:
        return "p < 0.001" if en else "p < 0,001"
    s = f"{p:.3f}" if p < 0.01 else f"{p:.2f}"
    return f"p = {s}" if en else f"p = {s.replace('.', ',')}"


# ---- the data versions (Rundata, Runor) ---------------------------------------------------------------------------------
RDJ = json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))
RDM = RDJ["meta"]
assert RDM["source"].startswith("Samnordisk runtextdatabas 2014 (RUNDATA.xls uppdaterad 2018)") and RDM["built"] == "2026-10-04"
assert RDM["license"] == "ODbL-1.0 / DbCL-1.0" and "nordiska.uu.se/forskn/samnord.htm" in RDM["attribution"]
RUNOR = json.load(open(os.path.join(ROOT, "data", "raa", "runor_2020.json"), encoding="utf-8"))
assert (RUNOR["edition"], RUNOR["fetched"]) == ("2020", "2026-10-16") and "https://runor.raa.se" in RUNOR["source"]
del RUNOR

# ---- the scan (r/hotspots.R) -------------------------------------------------------------------------------------------
H = json.load(open(os.path.join(C, "hotspots.json"), encoding="utf-8"))
assert (H["n_stones"], H["k"], H["ubpop"], H["nsim"]) == (1097, 8, 0.1, 999)
N_TRAITS = len(H["patterns"])
assert N_TRAITS == 13
PAT = next(x for x in H["patterns"] if x["key"] == "r_for_R")
CL = PAT["clusters"][0]
assert (PAT["n"], PAT["cases"], PAT["n_hot"], PAT["n_cold"]) == (514, 87, 32, 0)
MO = PAT["moran"]
assert round(MO["i"], 3) == 0.183 and MO["p"] < 1e-20
assert (CL["center"], round(CL["radius_km"], 1), CL["n"], CL["cases"]) == ("U 1172", 30.4, 36, 24)
assert (pc(CL["rate_in"]), pc(CL["rate_out"]), d2(CL["rr"]), CL["p"], CL["q_bh"]) == (67, 13, "5,06", 0.001, 0.013)
assert CL["provinces"] == {"U": 35, "Vs": 1}  # nästan helt inom ett landskap
HA, HB = CL["halves"]["A"], CL["halves"]["B"]
assert CL["halves"]["replicated"] and (pc(HA["rate_in"]), pc(HA["rate_out"]), pc(HB["rate_in"]), pc(HB["rate_out"])) == (85, 12, 57, 15)
assert HA["p"] < 1e-7 and HB["p"] < 1e-4 and round(HA["or"]) == 41 and d1(HB["or"]) == "7,3"
SIG_TRAITS = [(p["key"], p["clusters"][0]["q_bh"]) for p in H["patterns"] if p.get("clusters")]
assert [k for k, q in SIG_TRAITS if q < 0.05] == ["r_for_R"]  # the only trait whose cluster passes the adjustment
HOT_VG = [s["signum"] for s in PAT["stones"] if s["signum"].startswith("Vg")]
HOT_UVS = [s["signum"] for s in PAT["stones"] if not s["signum"].startswith("Vg")]
assert (len(HOT_VG), len(HOT_UVS)) == (9, 23) and HOT_VG == ["Vg 2", "Vg 3", "Vg 4", "Vg 6", "Vg 12", "Vg 13", "Vg 15", "Vg 16", "Vg 106"]
INSIDE = set(CL["stones"])
RD = {r["signum"]: r for r in RDJ["inscriptions"]}
assert RD["U 1172"]["place"].startswith("Holm") and RD["U 1172"]["parish"] == "Vittinge sn"
PAR = pd.Series([RD[s]["parish"] for s in INSIDE]).value_counts()
assert (PAR["Simtuna sn"], PAR["Vårfrukyrka sn"], PAR["Tillinge sn"]) == (5, 3, 3)

# ---- the stones (corpus.csv): trait known, not moved according to Rundata (as in the scan) -------------------------------
d = pd.read_csv(os.path.join(C, "corpus.csv"), low_memory=False)
N_ALL = len(d)
assert N_ALL == 2321  # rows; the Swedish Viking-Age runestones (the people module counts 2 320 with a region)
k = d[d.pm_r_for_R.notna() & ((d.moved.isna()) | (d.moved == 0))].copy()
assert len(k) == 514 and int(k.pm_r_for_R.sum()) == 87
k["inside"] = k.signum.isin(INSIDE)
# Rundata's moved flag only; lost stones (known from older records) are in. Stones moved only according to Runor 2020 are
# in too and leave only in the sensitivity analysis moved_runor (r/robustness.R: moved == 0 & moved_runor == 0).
LOST, LOST_IN = int((k.lost == 1).sum()), int((k[k.inside].lost == 1).sum())
assert (LOST, LOST_IN) == (72, 4)
S = k["style"]
early, late = S.isin(["RAK", "Fp", "Pr1", "Pr2"]), S.isin(["Pr3", "Pr4", "Pr5"])
erik_all = k.carvers_all.fillna("").str.contains("Erik")
erik = (k.carver == "Erik") & (k.carvers_uncertain == 0)


def frac(x):
    return int(x.pm_r_for_R.sum()), len(x)


def fisher(a, b):
    return stats.fisher_exact([[a[0], a[1] - a[0]], [b[0], b[1] - b[0]]])


E_IN, E_OUT = frac(k[erik & k.inside]), frac(k[erik & ~k.inside])
assert (E_IN, E_OUT) == ((11, 11), (1, 1)) and list(k[erik & ~k.inside].signum) == ["U 774"]
E_ALL = frac(k[erik_all])
assert set(k[erik]["style"]) == {"Fp"} and E_ALL == (15, 15) and sorted(k[erik_all & ~k.inside].signum) == ["U 732", "U 774"]
UNC = sorted(k[erik_all & ~erik].signum, key=lambda x: int(x.split()[1]))
assert UNC == ["U 732", "U 755", "U 1151"]
# U 774: how far outside the circle (SWEREF 99 TM, as in r/hotspots.R)
_T = Transformer.from_crs(4326, 3006, always_xy=True)
_xy = {s: _T.transform(r["lon"], r["lat"]) for s, r in d.set_index("signum")[["lat", "lon"]].iterrows() if s in ("U 1172", "U 774", "U 732")}
DIST_774 = math.dist(_xy["U 1172"], _xy["U 774"]) / 1000
OUT_774 = round(DIST_774 - CL["radius_km"])
OUT_732 = round(math.dist(_xy["U 1172"], _xy["U 732"]) / 1000 - CL["radius_km"])  # the uncertain one outside
assert d1(DIST_774) == "39,7" and (OUT_774, OUT_732) == (9, 6) and RD["U 774"]["parish"] == "Enköpings-Näs sn"
# Erik's other stones in Rundata: moved, undecidable, or the signed U 1165 (counted by hand in the text)
E_OTHER = sorted(set(d[d.carvers_all.fillna("").str.contains("Erik")].signum) - set(k[erik_all].signum) - {"U 1165"},
                 key=lambda x: (x.split()[0], int(x.split()[1])))
assert E_OTHER == ["U 738", "U 769", "U 779", "U 943", "U 978", "U 1173", "Vs 30"]
E_OTHER_R = d[d.signum.isin(E_OTHER) & d.pm_r_for_R.notna()]
assert sorted(E_OTHER_R.signum) == ["U 1173", "U 769", "U 943"] and (E_OTHER_R.pm_r_for_R == 1).all() and (E_OTHER_R.moved == 1).all()
EA_IN, EA_OUT = frac(k[early & k.inside]), frac(k[early & ~k.inside])
assert (EA_IN, EA_OUT) == ((15, 15), (34, 182)) and frac(k[early & k.inside & ~erik_all]) == (2, 2)
FP_U_OUT = frac(k[(S == "Fp") & ~k.inside & (k.province == "U")])
assert FP_U_OUT == (7, 9)
LA_IN, LA_U_OUT = frac(k[late & k.inside]), frac(k[late & ~k.inside & (k.province == "U")])
assert (LA_IN, LA_U_OUT) == ((7, 16), (12, 109))
P_LATE = fisher(LA_IN, LA_U_OUT)[1]
assert 0.002 < P_LATE < 0.004
NE_IN, ALL_OUT = frac(k[k.inside & ~erik_all]), frac(k[~k.inside])
assert (NE_IN, ALL_OUT) == ((11, 23), (63, 478))
P_NE = fisher(NE_IN, ALL_OUT)[1]
assert P_NE < 0.001
B = k[(k.carver == "Balle") & (k.carvers_uncertain == 0)]
B_IN, B_OUT = frac(B[B.inside]), frac(B[~B.inside])
P_B = fisher(B_IN, B_OUT)[1]
assert (B_IN, B_OUT) == ((3, 5), (5, 19)) and 0.25 < P_B < 0.35
BALL = k[k.carvers_all.fillna("").str.contains("Balle")]  # Balli with the uncertain attributions too
BA_IN, BA_OUT = frac(BALL[BALL.inside]), frac(BALL[~BALL.inside])
P_BA = fisher(BA_IN, BA_OUT)[1]
assert (BA_IN, BA_OUT) == ((5, 7), (6, 20)) and 0.08 < P_BA < 0.09
A = k[(k.carver == "Åsmund") & (k.carvers_uncertain == 0)]
A_IN, A_OUT = frac(A[A.inside]), frac(A[~A.inside])
assert (A_IN, A_OUT) == ((0, 3), (0, 10))
U_OUT, SO, VG = frac(k[(k.province == "U") & ~k.inside]), frac(k[k.province == "Sö"]), frac(k[k.province == "Vg"])
assert (U_OUT, SO, VG) == ((39, 244), (7, 80), (9, 41))
# Erik's signed stone is not counted: a gap breaks the word pairing (hand reading in the text)
assert pd.isna(d[d.signum == "U 1165"].pm_r_for_R.iloc[0]) and "airikr" in RD["U 1165"]["transliteration"] and "-ftir" in RD["U 1165"]["transliteration"]
# How dense the attributions are (a named carver, secure or uncertain): the cluster against the rest; Fjädrundaland
# (src/regions.py), which Stille (1999) attributed systematically, has a carver on every stone
named = k.carvers_all.notna() & (k.carvers_all.fillna("") != "")
ATTR_IN = (int(named[k.inside].sum()), int(k.inside.sum()))
ATTR_OUT = named[~k.inside].mean()
ATTR_U_OUT = named[~k.inside & (k.province == "U")].mean()
assert ATTR_IN == (33, 36) and (pc(ATTR_IN[0] / ATTR_IN[1]), pc(ATTR_OUT), pc(ATTR_U_OUT)) == (92, 42, 66)
fj = [regions.old_region(s, p) == "fjadrundaland" for s, p in zip(k.signum, k.province)]
FJ = (int(named[fj].sum()), int(sum(fj)))
assert FJ == (45, 45)

# ---- the popular article, recomputed 2026-10-31 (commit 491ceb1) ---------------------------------------------------------
ART = json.load(open(os.path.join(ROOT, "utdata", "blogg", "erik-skrev-r.json"), encoding="utf-8"))
AN = ART["numbers"]
assert (tuple(AN["E_in"]), tuple(AN["E_out"]), tuple(AN["B_in"]), tuple(AN["B_out"]), tuple(AN["BA_in"]), tuple(AN["BA_out"]),
        tuple(AN["A_in"]), tuple(AN["A_out"]), tuple(AN["early_in"]), tuple(AN["early_out"]), tuple(AN["late_in"])) == \
    (E_IN, E_OUT, B_IN, B_OUT, BA_IN, BA_OUT, A_IN, A_OUT, EA_IN, EA_OUT, LA_IN)
assert all(x in ART["body"] for x in ("Inom 30 kilometer från Holm i Vittinge har 24 av 36 stenar stavningen, alltså 67 %",
                                      "I resten av landet är det 13 %", "## Uppdatering 31 oktober 2026"))

# ---- Larsson 2002 (utdata/gamla_granser/larsson_yrrunan.md, read against the OCR and the page images) --------------------
LM = re.sub(r"\s+", " ", open(os.path.join(ROOT, "utdata", "gamla_granser", "larsson_yrrunan.md"), encoding="utf-8").read())
assert all(x in LM for x in ("Tabell 4 (s. 168)", "Uppland 218 av 1 216 (18 %)", "Västmanland 12 av 27 (45 %)", "Närke 7 av 22 (32 %)",
                             "Gästrikland 12 av 40 (30 %)", "Uppland (s. 170)",
                             "kan knappast det geografiska läget i sig vara någon förklaring, utan här måste andra faktorer – "
                             "rimligen kronologiska, delvis kanske också individuella – ha spelat in"))

# ---- the sensitivity analyses (src/robustness.py) ----------------------------------------------------------------------
ROB = json.load(open(os.path.join(C, "robustness.json"), encoding="utf-8"))
P = ROB["patterns"]["Geografi|hotspot_r_for_R_U"]
SPEC = ROB["specs"]["Geografi|hotspot_r_for_R_U"]
RU = P["rungs"]
assert (P["n"], P["k"], P["direction"]) == (514, 87, 1) and set(RU) == {"raw", "adjusted", "carver", "parish", "half_A", "half_B", "moved_rundata", "moved_runor"}
assert all(r["holds"] for r in RU.values()) and SPEC["selected"] and not SPEC["lopo"] and not SPEC["place"]
assert [round(RU[x]["or"], 1) for x in ("raw", "adjusted", "carver", "parish", "half_A", "half_B", "moved_runor")] == [13.2, 13.0, 16.7, 15.9, 10.0, 19.0, 10.5]
assert (RU["carver"]["groups"], RU["parish"]["groups"], RU["half_A"]["n"], RU["half_B"]["n"], RU["moved_runor"]["n"]) == (272, 280, 262, 252, 447)
# The rung without moved stones according to Rundata is the adjusted model itself: they are already out of the 514
assert all(RU["moved_rundata"][x] == RU["adjusted"][x] for x in ("or", "ci", "p", "n")) and RU["moved_rundata"]["n"] == 514
N_DISTINCT = len(RU) - 1
assert N_DISTINCT == 7
assert max(r["p"] for r in RU.values()) < 0.001
EF, CK = P["effect"], P["check"]
assert (pc(EF["share_hi"]), pc(EF["share_lo"]), round(100 * EF["diff"]), [round(100 * x) for x in EF["diff_ci"]]) == (63, 13, 50, [32, 67])
assert CK["ok"] and min(CK["uniformity_p"], CK["dispersion_p"], CK["spatial_p"]) > 0.05 and P.get("coding") is None
ANN = robustness.annotate(r_findings.corpus_patterns(rb.JOB.result(FP)), robustness.load(FP))
ME = next(x for x in ANN if x["key"] == "hotspot_r_for_R_U")
SUMM = robustness.summary(ANN)
N_SHOWN, N_ALLRUNG = SUMM["n_fdr"], SUMM["all_rungs"]
assert ME["confirmed"] is True and ME["ladder"]["passed"] == ME["ladder"]["tested"] == 8 and 0.015 < ME["q_global"] < 0.025
assert (N_SHOWN, N_ALLRUNG) == (48, 15)
QG = d2(ME["q_global"])
QGe = f"{ME['q_global']:.2f}"

# ---- the figures (utdata/rapporter/figurer/karta_r_for_R.R) --------------------------------------------------------------
FIG = os.path.join(ROOT, "utdata", "rapporter", "figurer")
FIGS = {f"{v}_{lang}": blog_figures.freeze(open(os.path.join(FIG, f"karta_r_for_R{'' if v == 'riket' else '_zoom'}_{lang}.png"), "rb").read())
        for v in ("riket", "zoom") for lang in ("sv", "en")}
MAP_SV = "Karta: Vitki, efter Rundata (ODbL); kustlinjer och sjöar: Natural Earth."
MAP_EN = "Map: Vitki, after Rundata (ODbL); coastlines and lakes: Natural Earth."

SITE = "https://vitkirunor.se"
SLUG = "r-for-yr-runan-vastra-uppland"
ART_SLUG = "erik-skrev-r-och-bygden-skrev-efter"
title = "I västra Uppland skrevs ʀ med r på fem gånger så stor andel av runstenarna som i resten av landet"
title_en = "In western Uppland ʀ was written with r on five times as large a share of the runestones as in the rest of the country"
summary = ("Runstenar där ljudet ʀ minst en gång skrivs med den vanliga r-runan samlas i västra Uppland: 67 procent av stenarna "
           "inom 30 kilometer från Holm i Vittinge mot 13 procent i resten av landet. Fyndet håller i båda halvorna av "
           "materialet och i alla känslighetsanalyser. Ristaren Erik skrev så på alla sina stenar, men klustret står kvar utan dem.")
summary_en = ("Runestones on which the sound ʀ is written at least once with the ordinary r-rune cluster in western Uppland: 67 "
              "percent of the stones within 30 kilometres of Holm in Vittinge against 13 percent in the rest of the country. The "
              "finding holds in both halves of the material and in every sensitivity analysis. The carver Erik wrote so on all "
              "his stones, but the cluster remains without them.")
CITE_EN = (f"Kvant, V. ({TODAY[:4]}). {title_en}. Research report, report version {REPORT_VERSION}; analysis in Vitki {APP_VERSION}. "
           f"{SITE}/en/forskningsrapporter/{SLUG}")

V3_SV = ("- **Version 3, 2026-11-05.** Rättelser före arkiveringen i Zenodo: flyttfiltret (bara Rundatas flyttade stenar är "
         f"borttagna; {LOST} stenar är försvunna), antalet känslighetsanalyser ({N_DISTINCT}, inte 8), påståendet att stavningen "
         "följde ristaren snarare än platsen (gäller Erik och Åsmund), titeln och klartextmeningen (andel stenar med minst ett r "
         "för ʀ) och den populära artikelns status. Tillagt: Eriks stenar utanför klustret, attributionernas täthet (Stille "
         "1999), mer av Larsson (2002), Peterson (1983), två olästa arbeten, kodläge, dataversioner, absoluta länkar och källor "
         "i bildtexterna. Inga analyser är omgjorda och inga tidigare siffror ändrade.")
V3_EN = ("- **Version 3, 2026-11-05.** Corrections before archiving in Zenodo: the filter for moved stones (only Rundata's moved "
         f"stones are left out; {LOST} stones are lost), the number of sensitivity analyses ({N_DISTINCT}, not 8), the claim that "
         "the spelling followed the carver rather than the place (holds for Erik and Åsmund), the title and the plain-words "
         "sentence (share of stones with at least one r for ʀ) and the status of the popular article. Added: Erik's stones "
         "outside the cluster, the density of attributions (Stille 1999), more of Larsson (2002), Peterson (1983), two unread "
         "works, code state, data versions, absolute links and sources in the captions. No analysis was "
         "redone and no earlier figure changed.")
LOG_SV = andringslogg("sv", 2, V2, "Bildtexterna säger nu att kartorna är gjorda av Vitki.", "") + "\n" + V3_SV
LOG_EN = andringslogg("en", 2, V2, "", "The captions now say that the maps were made by Vitki.") + "\n" + V3_EN

body = f"""*Viktor Kvant, oberoende forskare. Fullt prövat fynd. Rapportversion {REPORT_VERSION}, {TODAY} (först publicerad {FIRST}). Tidslinje: {TL_SV}. Analysen är gjord i Vitki {APP_VERSION}. Licens CC BY 4.0. Den engelska versionen är den kanoniska för citering: {CITE_EN}. Nyckelord: runstenar, vikingatid, yr-runan, ʀ, r, Uppland, ristare, rumslig statistik. Konkurrerande intressen: inga. Finansiering: ingen.*

## Sammanfattning

**Bakgrund och syfte.** Runsvenskans ʀ hade en egen runa men skrivs under 1000-talet allt oftare med den vanliga r-runan. Frågan är om stavningen samlas geografiskt mer än slumpen ger, var, och om samlingen tål en fast serie känslighetsanalyser.
**Material.** {sp(PAT['n'])} vikingatida runstenar i de svenska landskapen där det går att avgöra hur ʀ är skrivet och som inte är flyttade enligt Samnordisk runtextdatabas (Rundata); {LOST} av dem är försvunna och kända genom äldre uppteckningar.
**Metod.** Morans I, Getis-Ord Gi∗ och Kulldorffs rumsliga scanstatistik (999 simuleringar), justerat för de {N_TRAITS} drag som skannades; replikering i två på förhand bestämda halvor; {N_DISTINCT} känslighetsanalyser; justering för alla {N_SHOWN} samband som projektet redovisar.
**Resultat.** Inom {d1(CL['radius_km'])} kilometer från Holm i Vittinge socken har {CL['cases']} av {CL['n']} stenar minst ett r för ʀ ({pc(CL['rate_in'])} procent), mot {pc(CL['rate_out'])} procent i resten av landet; p = 0,001, justerat för dragen q = 0,013. Samma riktning i båda halvorna ({pc(HA['rate_in'])} mot {pc(HA['rate_out'])} och {pc(HB['rate_in'])} mot {pc(HB['rate_out'])} procent), alla känslighetsanalyser håller, och justerat för alla samband q = {QG}. Explorativt: ristaren Erik skrev r på alla sina {E_IN[1] + E_OUT[1]} säkert attribuerade stenar, men klustret står kvar utan dem ({NE_IN[0]} av {NE_IN[1]} stenar).
**Slutsats.** Västra Uppland är det område i Sverige där ʀ oftast skrevs med r. Hos Erik och Åsmund följde stavningen ristaren, men klustret står kvar med ristaren konstant; för bygden i övrigt kan materialet inte skilja ristare från plats. Vi föreslår en skrivtradition som började med Erik; uttal, som tidigare forskning menar, är inte uteslutet.

## 1. Inledning

Runsvenskans ʀ, av äldre *z* och med en egen runa, yr-runan ᛦ, stod bland annat i ändelser som *æftiʀ* ’efter’; när det föll samman med r skrevs det allt oftare med r-runan.

Patrik Larsson (2002) har kartlagt äldre ʀ i alla nordiska runinskrifter. Efter vokal skrivs det med r-runa betydligt oftare i Uppland (18 procent), Västergötland och på Gotland än i andra landskap med många belägg, och ännu oftare i Västmanland (45), Närke (32) och Gästrikland (30 procent), som har få belägg (tabell 4, s. 168; hans mått räknar skrivningar, vårt stenar). För Uppland kan enligt honom ”knappast det geografiska läget i sig vara någon förklaring”; i stället har ”rimligen kronologiska, delvis kanske också individuella” faktorer spelat in (s. 170). Den uppländska gruppen i stilen Fp är till stor del ristaren Eriks, som konsekvent skriver r-runa för ʀ (avsnitt 7.2.3); Per Stille (1999, s. 206) slöt av detsamma att r och ʀ hade fallit samman i Eriks språk. Larsson ser r-runans frammarsch som en språkförändring och inte en ortografisk reform (avsnitt 7.3): den har nästan helt tagit över efter dentala konsonanter, mindre efter andra konsonanter och minst efter vokal, och ristarna betecknar palatalisering och skriver s-runa för ʀ. Källström (2010) om enskilda ristares betydelse för bilden av språkhistorien och Källström (2014) om Erik har vi inte läst.

Det som saknas är ett mått på om stavningen samlas geografiskt mer än slumpen ger, oberoende av landskapsgränser, och om samlingen står kvar när stenarnas ålder och ristarnas vanor hålls konstanta.

## 2. Förregistrering: vad som var bestämt i förväg och vad som är explorativt

Ingen analysplan låstes innan resultaten var kända. Fyndet är upptäckt i en systematisk genomsökning av {N_TRAITS} drag, med samma metod, gränser och halvor för alla, bestämda i programkoden före körningen och utan någon hypotes om r för ʀ eller västra Uppland. Mot att fyndet beror på valet står scanstatistikens p-värde, som räknar med alla prövade cirklar, justeringen för dragen och för alla {N_SHOWN} samband, halvorna och de fasta känslighetsanalyserna. Avsnitt 5.1–5.3 är vad metoden föreskriver för varje drag; 5.4 är explorativt, räknat efter att klustret var känt, med ojusterade p-värden.

## 3. Material

- **Källa.** Rundata (utgåvan 2014, uppdaterad 2018), hämtad 2026-10-04; härledd korpus beräknad 2026-10-29. För en känslighetsanalys också Riksantikvarieämbetets Runor (utgåva 2020), hämtad 2026-10-16.
- **Stenarna.** Vikingatida runstenar (inga andra föremål) i de svenska landskapen; Skåne och Blekinge förs i Rundata till Danmark. Av stenarna har {sp(H['n_stones'])} känt ursprungligt läge och är inte flyttade enligt Rundata ({LOST} av de {sp(PAT['n'])} som ingår är försvunna och kända genom äldre uppteckningar). Stenar som bara Runor (2020) anger som flyttade ingår; de tas bort i en av känslighetsanalyserna.
- **Draget.** Ord vars normaliserade form slutar på ʀ och vars huggna form slutar på r- eller yr-runan. Stenen räknas som *r för ʀ* om minst en sådan ändelse har r-runan. Draget kan avgöras på {sp(PAT['n'])} stenar; {PAT['cases']} ({pc(PAT['cases'] / PAT['n'])} procent) har det. Måttet bygger på Rundatas normalisering och translitterering, utan egen handläsning.
- **Ristaren** enligt Rundata, med uppgift om attributionen är säker (efter Sveriges runinskrifter och Axelson 1993). Erik har tolv säkert attribuerade stenar där draget kan avgöras och tre osäkert attribuerade ({', '.join(UNC)}). Hans enda signerade sten, U 1165, räknas inte, eftersom en lucka hindrar att orden paras ihop; den har r-runa där ʀ väntas (*-ftir*, *airikr*).
- **Datering** efter stilgrupp (Gräslund 2006); i 5.4 är RAK–Pr2 tidiga och Pr3–Pr5 sena.

## 4. Metod

**4.1 Genomsökningen** i R (R {DONE['r_version'].split()[2]}), lägen i SWEREF 99 TM: *Morans I* (Moran 1950; {H['k']} närmaste grannar) för om draget alls samlas; *Getis-Ord Gi∗* (Getis & Ord 1992) för om det är vanligare bland en stens grannar än i landet (Benjamini–Hochberg över stenarna); och *Kulldorffs rumsliga scanstatistik* (Kulldorff 1997), som prövar alla cirklar med högst en tiondel av stenarna mot landets andel. Den mest avvikande cirkeln är klustret; p-värdet kommer ur {H['nsim']} slumpvisa omfördelningar och justeras med Benjamini–Hochberg över de {N_TRAITS} dragen.

**4.2 Halvorna.** Materialet delades en gång för alla analyser i två halvor, hela socknar växelvis inom varje landskap; klustret jämförs i var halva med Fishers exakta test.

**4.3 Känslighetsanalyser.** Logistisk regression, inom mot utanför klustret: rå; justerad för dateringsperiod; ristaren som slumpeffekt, så att en flitig ristares vanor inte räknas som bygdens; socknen som slumpeffekt; var halva för sig; utan stenar som Runor 2020 anger som flyttade. Utan ett landskap i taget och läget som rumslig yta görs inte: klustret ligger nästan helt inom ett landskap ({CL['provinces']['U']} av {CL['n']} stenar), och jämförelsen är själv geografisk. Valet av klustret prövas av scanstatistiken och halvorna; vid justeringen för alla {N_SHOWN} samband används det största av deras p. Antagandena prövas med simulerade residualer (DHARMa; Hartig 2022).

**4.4 Explorativt.** Andelar efter ristare och dateringsperiod, Fishers exakta test, ojusterat.

**4.5 Avvikelser och tidigare versioner.** Ingen plan fanns, så inga avvikelser finns. En populär artikel (13 oktober 2026) byggde på en äldre version av materialet, före en rättelse av vilka stenar som räknas som flyttade, och hade klustret i Grop-Norrby med radien 22 kilometer; den räknades om den 31 oktober 2026 och har nu samma siffror för klustret, Erik, Balle och Åsmund som rapporten.

## 5. Resultat

**5.1 Klustret.** Draget samlas geografiskt: Morans I = {d2(MO['i'])} (p < 0,001). Det mest extrema området har mitten i U 1172 vid Holm i Vittinge och radien {d1(CL['radius_km'])} kilometer. Där har {CL['cases']} av {CL['n']} stenar r för ʀ ({pc(CL['rate_in'])} procent), mot {pc(CL['rate_out'])} procent av stenarna i resten av landet: {d2(CL['rr'])} gånger så vanligt. p = 0,001, det lägsta möjliga; justerat för de {N_TRAITS} dragen q = 0,013, och inget annat drags kluster klarar justeringen. Flest stenar står i Simtuna ({PAR['Simtuna sn']}), Vårfrukyrka och Tillinge socknar (3 vardera). Halva A: {pc(HA['rate_in'])} mot {pc(HA['rate_out'])} procent (oddskvot {round(HA['or'])}, {pfmt(HA['p'])}); halva B: {pc(HB['rate_in'])} mot {pc(HB['rate_out'])} procent (oddskvot {d1(HB['or'])}, {pfmt(HB['p'])}).

![Figur 1. ʀ skrivet med r-runan: stenarna och klustret]({FIGS['riket_sv']})
**Figur 1.** Runstenar där draget kan avgöras; rost: r för ʀ minst en gång, grå: bara yr-runan. Ringen är klustret. {MAP_SV}

![Figur 2. Klustret i västra Uppland]({FIGS['zoom_sv']})
**Figur 2.** Klustret i närbild; svart ring: en av Eriks säkert attribuerade stenar. {MAP_SV}

**5.2 Känslighetsanalyserna** ({sp(P['n'])} stenar, {P['k']} med draget). Alla {N_DISTINCT} håller; oddskvot (95 %-intervall):

- Rå: {d1(RU['raw']['or'])} ({d1(RU['raw']['ci'][0])}–{d1(RU['raw']['ci'][1])}), {pfmt(RU['raw']['p'])}. Justerad för dateringsperiod: {d1(RU['adjusted']['or'])} ({d1(RU['adjusted']['ci'][0])}–{d1(RU['adjusted']['ci'][1])}), {pfmt(RU['adjusted']['p'])}. Utan flyttade stenar enligt Rundata: samma som den justerade modellen, eftersom de redan är borttagna.
- Ristaren som slumpeffekt ({RU['carver']['groups']} ristare och sockengrupper): {d1(RU['carver']['or'])} ({d1(RU['carver']['ci'][0])}–{d1(RU['carver']['ci'][1])}), {pfmt(RU['carver']['p'])}. Socknen som slumpeffekt ({RU['parish']['groups']} socknar): {d1(RU['parish']['or'])} ({d1(RU['parish']['ci'][0])}–{d1(RU['parish']['ci'][1])}), {pfmt(RU['parish']['p'])}.
- Halva A ({RU['half_A']['n']} stenar): {d1(RU['half_A']['or'])}; halva B ({RU['half_B']['n']}): {d1(RU['half_B']['or'])}; båda p < 0,001.
- Utan stenar som Runor 2020 anger som flyttade ({RU['moved_runor']['n']} kvar): {d1(RU['moved_runor']['or'])} ({d1(RU['moved_runor']['ci'][0])}–{d1(RU['moved_runor']['ci'][1])}), {pfmt(RU['moved_runor']['p'])}.
- I den justerade modellen {pc(EF['share_hi'])} mot {pc(EF['share_lo'])} procent, {round(100 * EF['diff'])} procentenheter (troligen {round(100 * EF['diff_ci'][0])}–{round(100 * EF['diff_ci'][1])}). Residualerna: fördelning p = {d2(CK['uniformity_p'])}, överspridning p = {d2(CK['dispersion_p'])}, rumsligt mönster p = {d2(CK['spatial_p'])}; inget avvikande.
- Justerat för alla {N_SHOWN} samband: q = {QG}, ett av {N_ALLRUNG} som håller i alla känslighetsanalyser.

**5.3 De heta stenarna.** Gi∗ pekar ut {PAT['n_hot']} heta stenar och inga kalla: {len(HOT_UVS)} i och kring klustret i Uppland och Västmanland och {len(HOT_VG)} i Västergötland ({', '.join(HOT_VG)}), en grupp för liten för att prövas som eget kluster. Larsson (2002, kapitel 7) har noterat dessa västgötska inskrifter, där *æftiʀ* skrivs med r-runa. Övriga Uppland: {U_OUT[0]} av {U_OUT[1]} ({pc(U_OUT[0] / U_OUT[1])} procent).

**5.4 Explorativt: ristarna och tiden.**

- **Erik.** Alla hans {E_IN[1] + E_OUT[1]} säkert och tre osäkert attribuerade stenar har r för ʀ, alla i stilen Fp; två står utanför klustret, U 774 (säker, {d1(DIST_774)} kilometer från mitten) och U 732 (osäker).
- **Tidiga stenar.** Inom klustret har alla {EA_IN[1]} draget ({EA_IN[1] - 2} attribuerade till Erik), utanför {EA_OUT[0]} av {EA_OUT[1]} ({pc(EA_OUT[0] / EA_OUT[1])} procent).
- **Utan Erik.** Utan alla stenar attribuerade till honom: {NE_IN[0]} av {NE_IN[1]} inom klustret ({pc(NE_IN[0] / NE_IN[1])} procent) mot {ALL_OUT[0]} av {ALL_OUT[1]} utanför ({pc(ALL_OUT[0] / ALL_OUT[1])} procent), {pfmt(P_NE)}.
- **Senare stenar** (Pr3–Pr5): {LA_IN[0]} av {LA_IN[1]} inom klustret ({pc(LA_IN[0] / LA_IN[1])} procent) mot {LA_U_OUT[0]} av {LA_U_OUT[1]} i övriga Uppland ({pc(LA_U_OUT[0] / LA_U_OUT[1])} procent), {pfmt(P_LATE)}.
- **Balle**, en generation efter Erik: {B_IN[0]} av {B_IN[1]} stenar inom klustret mot {B_OUT[0]} av {B_OUT[1]} utanför ({pfmt(P_B)}); med osäkra attributioner {BA_IN[0]} av {BA_IN[1]} mot {BA_OUT[0]} av {BA_OUT[1]} ({pfmt(P_BA)}).
- **Åsmund** skrev yr-runa på alla sina {A_IN[1] + A_OUT[1]} säkert attribuerade stenar, också de {A_IN[1]} inom klustret.
- **Attributionerna.** {ATTR_IN[0]} av klustrets {ATTR_IN[1]} stenar ({pc(ATTR_IN[0] / ATTR_IN[1])} procent) har en namngiven ristare, säker eller osäker, mot {pc(ATTR_OUT)} procent utanför och {pc(ATTR_U_OUT)} procent i övriga Uppland; i Fjädrundaland alla {FJ[1]}.

**I klartext.** Inom tre mil från Holm i Vittinge har två stenar av tre minst en gång ʀ skrivet med den vanliga r-runan, i resten av landet ungefär en av åtta, och i ingen av 999 slumpvisa omfördelningar av stavningen blev något område lika extremt.

## 6. Diskussion

**Vad fyndet säger.** Västra Uppland är det område i Sverige där ʀ oftast skrevs med r-runan, och det beror inte på tidiga stenar eller en enda flitig ristare: klustret står kvar med dateringsperiod och ristare konstanta, i var halva, utan flyttade stenar och utan Erik.

**Mot tidigare forskning.** Resultatet preciserar Larssons (2002) iakttagelse att Uppland och Västergötland skiljer ut sig, återfinner hans västgötska grupp och bekräftar Stille (1999) om Erik. Larsson förklarar Upplands andel med tid och enskilda ristare snarare än med läget; inom Uppland finns ändå ett avgränsat område som står kvar med båda konstanta. Det gränsar till Västmanland, där Larsson har 45 procent (på 27 belägg); kanske är det en västlig zon snarare än ett uppländskt drag.

**Där vi går emot tidigare forskning.** Stille och Larsson läser r-runan som uttal. Larssons skäl gäller runskriften i stort: de visar att många ristare skrev efter örat, inte att alla gjorde det, och förklarar inte varför en bygd skiljer sig så skarpt. För västra Uppland föreslår vi en skrivtradition som började med Erik och fördes vidare i bygden:

1. Erik skrev r på alla femton stenar i materialet som säkert eller osäkert attribuerats till honom, också på de två utanför klustret: U 774, {OUT_774} kilometer utanför cirkeln, med en ifrågasatt attribution (Jansson i Upplands runinskrifter 3, s. 324, 352, efter Larsson 2002, avsnitt 7.2.3), och den osäkra U 732, {OUT_732} kilometer utanför. Där Larsson, efter Peterson (1983), ser ristarnas vacklan mellan runorna som en pågående ljudförändring vacklar Erik inte; han skriver som efter en regel.
2. Åsmund skrev yr-runa på alla sina tretton stenar, också de tre inom klustret; platsen avgjorde inte hans stavning, men det är bara tre stenar.
3. Stavningen lever kvar i bygden efter Erik, och klustret står kvar med ristaren konstant.

Hos Erik och Åsmund följde stavningen ristaren, men klustret står kvar med ristaren konstant; för bygden i övrigt kan materialet inte skilja ristare från plats. Talade ristarna ett mål där ljuden fallit samman, ger det samma mönster, och Balle pekar åt det hållet (5.4). Provet är om de senare r-stenarna står i Eriks tradition – ornamentik, formler, stavning i övrigt – eller bara i hans bygd.

**Svagheter, i ordning efter vikt.**

1. **Upptäckt, inte förregistrerat.** Gränsen är vald av datan; radie och centrum är ungefärliga.
2. **Erik bär den tidiga delen.** {EA_IN[1] - 2} av {EA_IN[1]} tidiga stenar i klustret är attribuerade till honom efter stil, och flera attributioner har ifrågasatts (Larsson 2002, avsnitt 7.2.3); utan honom är marginalen mindre.
3. **Ojämna attributioner.** Attributionerna är tätare i klustret ({ATTR_IN[0]} av {ATTR_IN[1]} mot {pc(ATTR_OUT)} procent), eftersom Stille (1999) attribuerade Fjädrundalands stenar systematiskt; jämförelserna av ristare vilar på ojämnt underlag.
4. **Få ord, ingen handkontroll.** Ofta en eller två ändelser per sten, mest *æftiʀ*, och ett r räcker; en felläst yr-runa eller en annan normalisering flyttar enskilda stenar.

**Vad som skulle fälla fyndet.** En handläsning där r-formerna i klustret oftare är osäkra än utanför, eller nya fynd i bygden med yr-runa.

## 7. Slutsats

Inom {d1(CL['radius_km'])} kilometer från Holm i Vittinge har {pc(CL['rate_in'])} procent av runstenarna minst ett r för ʀ, mot {pc(CL['rate_out'])} procent i resten av landet, och samlingen tål varje känslighetsanalys. Hos Erik och Åsmund följde stavningen ristaren, men klustret står kvar med ristaren konstant; för bygden i övrigt kan materialet inte skilja ristare från plats. Vi föreslår en skrivtradition som började med Erik; uttal, som Stille och Larsson menar, är ännu inte uteslutet.

## Data och kod

Analysen är gjord i Vitki {APP_VERSION}, ett öppet forskningsverktyg för runstenar ([vitkirunor.se]({SITE})). Kodläge: commit {CODE_COMMIT} i https://github.com/Precatio/runes (Vitki {APP_VERSION} med senare ändringar). Koden och resultatfilerna finns där under GPL-3.0.

- Draget: `src/language_profile.py`, `src/pattern_map.py`; genomsökningen: `r/hotspots.R`; känslighetsanalyserna: `r/robustness.R`, `src/robustness.py` (`METHODS.md`, 1f och 1v); resultaten under materialets version `{FP}`; figurerna: `utdata/rapporter/figurer/karta_r_for_R.R`. Rapporten byggs av `utdata/blogg/build/build_rapport_r_for_R.py`, som stannar om någon siffra inte stämmer.
- I Vitki: Statistik, Geografi, och Karta, Mönster. Ordlista: {SITE}/forskningsrapporter/begrepp.
- Populär framställning: [Erik skrev r – och bygden skrev efter]({SITE}/artiklar/{ART_SLUG}), omräknad 31 oktober 2026 med samma siffror som här.

## Referenser

- Axelson, J. 1993. *Mellansvenska runristare. Förteckning över signerade och attribuerade inskrifter*. Runrön 5. Uppsala.
- Benjamini, Y. & Hochberg, Y. 1995. Controlling the false discovery rate: a practical and powerful approach to multiple testing. *Journal of the Royal Statistical Society B* 57 (1), s. 289–300.
- Getis, A. & Ord, J. K. 1992. The analysis of spatial association by use of distance statistics. *Geographical Analysis* 24 (3), s. 189–206.
- Gräslund, A.-S. 2006. Dating the Swedish Viking-Age rune stones on stylistic grounds. I: M. Stoklund m.fl. (red.), *Runes and their Secrets: Studies in Runology*. Köpenhamn, s. 117–139.
- Hartig, F. 2022. *DHARMa: Residual diagnostics for hierarchical (multi-level/mixed) regression models*. R-paket.
- Kulldorff, M. 1997. A spatial scan statistic. *Communications in Statistics – Theory and Methods* 26 (6), s. 1481–1496.
- Källström, M. 2010. Åsmund, Öpir och Önjut – om individens betydelse för bilden av vikingatidens språkhistoria. I: E. Magnusson & L. Rogström (red.), *Språkhistoria – hur och för vem?* Studier i svensk språkhistoria 10. Göteborg, s. 163–174. (Inte läst.)
- Källström, M. 2014. Från Forneby till Gamla Uppsala – några nyheter om runristaren Erik. I: *Festskrift till Per Stille*. Humanetten 32. Växjö, s. 33–41. (Inte läst.)
- Larsson, P. 2002. *Yrrunan. Användning och ljudvärde i nordiska runinskrifter*. Runrön 17. Uppsala.
- Moran, P. A. P. 1950. Notes on continuous stochastic phenomena. *Biometrika* 37 (1–2), s. 17–23.
- Peterson, L. 1983. Om s.k. palatalt r i fornsvenskan. *Arkiv för nordisk filologi* 98, s. 202–220. (Citerad efter Larsson 2002, avsnitt 7.3.)
- Riksantikvarieämbetet. *Runor* (utgåva 2020 av Samnordisk runtextdatabas). https://runor.raa.se, hämtad 2026-10-16.
- Samnordisk runtextdatabas (Rundata), utgåvan 2014, uppdaterad 2018. Institutionen för nordiska språk, Uppsala universitet. https://www.nordiska.uu.se/forskn/samnord.htm, hämtad 2026-10-04. Open Database License (ODbL) 1.0 / Database Contents License (DbCL) 1.0.
- Stille, P. 1999. *Runstenar och runristare i det vikingatida Fjädrundaland. En studie i attribuering*. Runrön 13. Uppsala.

:::box Det viktigaste i korthet
- I västra Uppland, kring Simtuna, Vårfrukyrka och Tillinge, skrevs det gamla ljudet ʀ med vanlig r-runa på långt fler runstenar än någon annanstans i Sverige.
- Erik och Åsmund stavade som de brukade var de än ristade, och bygden fortsatte efter Erik; om det var ristarnas vana eller bygdens tal kan stenarna inte avgöra.
- Vår hypotes är en skrivtradition. Tidigare forskning har läst det som uttal, och stenarna kan ännu inte avgöra vem som har rätt.
:::

{LOG_SV}
"""

body_en = f"""*Viktor Kvant, independent researcher. Fully tested finding. Report version {REPORT_VERSION}, {TODAY} (first published {FIRST}). Timeline: {TL_EN}. The analysis was made in Vitki {APP_VERSION}. Licence CC BY 4.0. This English version is the canonical one for citation: {CITE_EN}. Keywords: runestones, Viking Age, yr-rune, ʀ, r, Uppland, carvers, spatial statistics. Competing interests: none. Funding: none.*

## Abstract

**Background and aim.** The ʀ of Runic Swedish had a rune of its own but is written ever more often with the ordinary r-rune during the eleventh century. The question is whether the spelling clusters geographically more than chance would give, where, and whether the cluster withstands a fixed series of sensitivity analyses.
**Material.** {en_n(PAT['n'])} Viking-Age runestones in the Swedish provinces where it can be decided how ʀ is written and which are not moved according to the Scandinavian Runic-text Database (Rundata); {LOST} of them are lost and known from older records.
**Method.** Moran's I, Getis-Ord Gi∗ and Kulldorff's spatial scan statistic (999 simulations), adjusted for the {N_TRAITS} traits scanned; replication in two pre-defined halves; {N_DISTINCT} sensitivity analyses; adjustment for all {N_SHOWN} associations the project reports.
**Results.** Within {CL['radius_km']:.1f} kilometres of Holm in Vittinge parish, {CL['cases']} of {CL['n']} stones have at least one r for ʀ ({pc(CL['rate_in'])} percent), against {pc(CL['rate_out'])} percent in the rest of the country; p = 0.001, adjusted for the traits q = 0.013. Same direction in both halves ({pc(HA['rate_in'])} against {pc(HA['rate_out'])} and {pc(HB['rate_in'])} against {pc(HB['rate_out'])} percent), every sensitivity analysis holds, and adjusted for all associations q = {QGe}. Exploratory: the carver Erik wrote r on all his {E_IN[1] + E_OUT[1]} securely attributed stones, but the cluster remains without them ({NE_IN[0]} of {NE_IN[1]} stones).
**Conclusion.** Western Uppland is the area of Sweden where ʀ was most often written with r. With Erik and Åsmund the spelling followed the carver, but the cluster remains with the carver held constant; for the rest of the district the material cannot separate carver from place. We propose a writing tradition that began with Erik; pronunciation, as earlier research holds, is not ruled out.

## 1. Introduction

The ʀ of Runic Swedish, from older *z* and with a rune of its own, the yr-rune ᛦ, stood among other places in endings such as *æftiʀ* ’after’; as it merged with r it was written ever more often with the r-rune.

Patrik Larsson (2002) mapped older ʀ in all Scandinavian runic inscriptions. After a vowel it is written with the r-rune markedly more often in Uppland (18 percent), Västergötland and on Gotland than in other provinces with many instances, and more often still in Västmanland (45), Närke (32) and Gästrikland (30 percent), which have few (table 4, p. 168; his measure counts spellings, ours stones). For Uppland, in his words, ”knappast det geografiska läget i sig vara någon förklaring” (the geographical position in itself can hardly be an explanation); rather, ”rimligen kronologiska, delvis kanske också individuella” (presumably chronological, partly perhaps also individual) factors have played a part (p. 170). The Uppland group in the Fp style is largely the carver Erik's, who consistently writes the r-rune for ʀ (section 7.2.3); Per Stille (1999, p. 206) inferred from the same that r and ʀ had merged in Erik's speech. Larsson sees the advance of the r-rune as a language change, not an orthographic reform (section 7.3): it has almost wholly taken over after dental consonants, less after other consonants and least after vowels, and the carvers mark palatalisation and write the s-rune for ʀ. Källström (2010) on individual carvers and the picture of language history and Källström (2014) on Erik we have not read.

What is lacking is a measure of whether the spelling clusters geographically more than chance would give, independently of provincial boundaries, and whether the cluster remains when the age of the stones and the habits of the carvers are held constant.

## 2. Pre-registration: what was fixed in advance and what is exploratory

No analysis plan was locked before the results were known. The finding was discovered in a systematic search of {N_TRAITS} traits, with the same method, limits and halves for all, fixed in the program code before the run and without any hypothesis about r for ʀ or western Uppland. Against the finding being an artefact of the choice stand the scan statistic's p-value, which takes every tested circle into account, the adjustment for the traits and for all {N_SHOWN} associations, the halves and the fixed sensitivity analyses. Sections 5.1–5.3 are what the method prescribes for every trait; 5.4 is exploratory, computed after the cluster was known, with unadjusted p-values.

## 3. Material

- **Source.** Rundata (2014 edition, updated 2018), retrieved 2026-10-04; derived corpus computed 2026-10-29. For one sensitivity analysis also the Swedish National Heritage Board's Runor (2020 edition), retrieved 2026-10-16.
- **The stones.** Viking-Age runestones (no other objects) in the Swedish provinces; Skåne and Blekinge are counted as Denmark in Rundata. Of the stones, {en_n(H['n_stones'])} have a known original location and are not moved according to Rundata ({LOST} of the {en_n(PAT['n'])} included are lost and known from older records). Stones that only Runor (2020) records as moved are included; they are left out in one of the sensitivity analyses.
- **The trait.** Words whose normalised form ends in ʀ and whose carved form ends in the r- or the yr-rune. The stone counts as *r for ʀ* if at least one such ending has the r-rune. The trait can be decided on {en_n(PAT['n'])} stones; {PAT['cases']} ({pc(PAT['cases'] / PAT['n'])} percent) have it. The measure rests on Rundata's normalisation and transliteration, without a reading of our own.
- **The carver** according to Rundata, with a note of whether the attribution is secure (after Sveriges runinskrifter and Axelson 1993). Erik has twelve securely attributed stones where the trait can be decided and three uncertainly attributed ones ({', '.join(UNC)}). His only signed stone, U 1165, is not counted, since a gap keeps the words from being paired; it has the r-rune where ʀ is expected (*-ftir*, *airikr*).
- **Dating** by style group (Gräslund 2006); in 5.4, RAK–Pr2 are early and Pr3–Pr5 late.

## 4. Method

**4.1 The search** in R (R {DONE['r_version'].split()[2]}), locations in SWEREF 99 TM: *Moran's I* (Moran 1950; {H['k']} nearest neighbours) for whether the trait clusters at all; *Getis-Ord Gi∗* (Getis & Ord 1992) for whether it is more common among a stone's neighbours than in the country (Benjamini–Hochberg across the stones); and *Kulldorff's spatial scan statistic* (Kulldorff 1997), which tests every circle holding at most a tenth of the stones against the national share. The most deviant circle is the cluster; its p-value comes from {H['nsim']} random redistributions and is adjusted with Benjamini–Hochberg across the {N_TRAITS} traits.

**4.2 The halves.** The material was divided once for all analyses into two halves, whole parishes dealt alternately within each province; the cluster is compared in each half with Fisher's exact test.

**4.3 Sensitivity analyses.** Logistic regression, within against outside the cluster: raw; adjusted for dating period; the carver as a random effect, so that a prolific carver's habits are not counted as the district's; the parish as a random effect; each half on its own; without stones that Runor 2020 records as moved. Without one province at a time and location as a spatial surface are not made: the cluster lies almost wholly within one province ({CL['provinces']['U']} of {CL['n']} stones), and the comparison is itself geographic. The choice of the cluster is tested by the scan statistic and the halves; the adjustment for all {N_SHOWN} associations uses the largest of their p-values. The assumptions are checked with simulated residuals (DHARMa; Hartig 2022).

**4.4 Exploratory.** Shares by carver and dating period, Fisher's exact test, unadjusted.

**4.5 Deviations and earlier versions.** No plan existed, so no deviations can be reported. A popular article (13 October 2026) rested on an older version of the material, before a correction of which stones count as moved, and had the cluster at Grop-Norrby with a radius of 22 kilometres; it was recomputed on 31 October 2026 and now has the same figures for the cluster, Erik, Balli and Åsmund as the report.

## 5. Results

**5.1 The cluster.** The trait clusters geographically: Moran's I = {MO['i']:.2f} (p < 0.001). The most extreme area has its centre at U 1172 at Holm in Vittinge parish and a radius of {CL['radius_km']:.1f} kilometres. There {CL['cases']} of {CL['n']} stones have r for ʀ ({pc(CL['rate_in'])} percent), against {pc(CL['rate_out'])} percent of the stones in the rest of the country: {CL['rr']:.2f} times as common. p = 0.001, the lowest possible; adjusted for the {N_TRAITS} traits q = 0.013, and no other trait's cluster passes the adjustment. Most stones stand in Simtuna ({PAR['Simtuna sn']}), Vårfrukyrka and Tillinge parishes (3 each). Half A: {pc(HA['rate_in'])} against {pc(HA['rate_out'])} percent (odds ratio {round(HA['or'])}, {pfmt(HA['p'], True)}); half B: {pc(HB['rate_in'])} against {pc(HB['rate_out'])} percent (odds ratio {HB['or']:.1f}, {pfmt(HB['p'], True)}).

![Figure 1. ʀ written with the r-rune: the stones and the cluster]({FIGS['riket_en']})
**Figure 1.** Runestones where the trait can be decided; rust: r for ʀ at least once, grey: the yr-rune only. The ring is the cluster. {MAP_EN}

![Figure 2. The cluster in western Uppland]({FIGS['zoom_en']})
**Figure 2.** The cluster close up; black ring: one of Erik's securely attributed stones. {MAP_EN}

**5.2 The sensitivity analyses** ({en_n(P['n'])} stones, {P['k']} with the trait). All {N_DISTINCT} hold; odds ratio (95 % interval):

- Raw: {RU['raw']['or']:.1f} ({RU['raw']['ci'][0]:.1f}–{RU['raw']['ci'][1]:.1f}), {pfmt(RU['raw']['p'], True)}. Adjusted for dating period: {RU['adjusted']['or']:.1f} ({RU['adjusted']['ci'][0]:.1f}–{RU['adjusted']['ci'][1]:.1f}), {pfmt(RU['adjusted']['p'], True)}. Without stones moved according to Rundata: the same as the adjusted model, since they are already left out.
- Carver as a random effect ({RU['carver']['groups']} carvers and parish groups): {RU['carver']['or']:.1f} ({RU['carver']['ci'][0]:.1f}–{RU['carver']['ci'][1]:.1f}), {pfmt(RU['carver']['p'], True)}. Parish as a random effect ({RU['parish']['groups']} parishes): {RU['parish']['or']:.1f} ({RU['parish']['ci'][0]:.1f}–{RU['parish']['ci'][1]:.1f}), {pfmt(RU['parish']['p'], True)}.
- Half A ({RU['half_A']['n']} stones): {RU['half_A']['or']:.1f}; half B ({RU['half_B']['n']}): {RU['half_B']['or']:.1f}; both p < 0.001.
- Without stones that Runor 2020 records as moved ({RU['moved_runor']['n']} remain): {RU['moved_runor']['or']:.1f} ({RU['moved_runor']['ci'][0]:.1f}–{RU['moved_runor']['ci'][1]:.1f}), {pfmt(RU['moved_runor']['p'], True)}.
- In the adjusted model {pc(EF['share_hi'])} against {pc(EF['share_lo'])} percent, {round(100 * EF['diff'])} percentage points (probably {round(100 * EF['diff_ci'][0])}–{round(100 * EF['diff_ci'][1])}). The residuals: distribution p = {CK['uniformity_p']:.2f}, overdispersion p = {CK['dispersion_p']:.2f}, spatial pattern p = {CK['spatial_p']:.2f}; nothing amiss.
- Adjusted for all {N_SHOWN} associations: q = {QGe}, one of {N_ALLRUNG} that hold in every sensitivity analysis.

**5.3 The hot stones.** Gi∗ singles out {PAT['n_hot']} hot stones and no cold ones: {len(HOT_UVS)} in and around the cluster in Uppland and Västmanland and {len(HOT_VG)} in Västergötland ({', '.join(HOT_VG)}), a group too small to be tested as a cluster of its own. Larsson (2002, chapter 7) noted these inscriptions in Västergötland, where *æftiʀ* is written with the r-rune. The rest of Uppland: {U_OUT[0]} of {U_OUT[1]} ({pc(U_OUT[0] / U_OUT[1])} percent).

**5.4 Exploratory: the carvers and time.**

- **Erik.** All his {E_IN[1] + E_OUT[1]} securely and three uncertainly attributed stones have r for ʀ, all in the Fp style; two stand outside the cluster, U 774 (secure, {DIST_774:.1f} kilometres from the centre) and U 732 (uncertain).
- **Early stones.** Within the cluster all {EA_IN[1]} have the trait ({EA_IN[1] - 2} attributed to Erik), outside {EA_OUT[0]} of {EA_OUT[1]} ({pc(EA_OUT[0] / EA_OUT[1])} percent).
- **Without Erik.** Without every stone attributed to him: {NE_IN[0]} of {NE_IN[1]} within the cluster ({pc(NE_IN[0] / NE_IN[1])} percent) against {ALL_OUT[0]} of {ALL_OUT[1]} outside ({pc(ALL_OUT[0] / ALL_OUT[1])} percent), {pfmt(P_NE, True)}.
- **Later stones** (Pr3–Pr5): {LA_IN[0]} of {LA_IN[1]} within the cluster ({pc(LA_IN[0] / LA_IN[1])} percent) against {LA_U_OUT[0]} of {LA_U_OUT[1]} in the rest of Uppland ({pc(LA_U_OUT[0] / LA_U_OUT[1])} percent), {pfmt(P_LATE, True)}.
- **Balli**, a generation after Erik: {B_IN[0]} of {B_IN[1]} stones within the cluster against {B_OUT[0]} of {B_OUT[1]} outside ({pfmt(P_B, True)}); with uncertain attributions {BA_IN[0]} of {BA_IN[1]} against {BA_OUT[0]} of {BA_OUT[1]} ({pfmt(P_BA, True)}).
- **Åsmund** wrote the yr-rune on all his {A_IN[1] + A_OUT[1]} securely attributed stones, including the {A_IN[1]} within the cluster.
- **The attributions.** {ATTR_IN[0]} of the cluster's {ATTR_IN[1]} stones ({pc(ATTR_IN[0] / ATTR_IN[1])} percent) have a named carver, secure or uncertain, against {pc(ATTR_OUT)} percent outside and {pc(ATTR_U_OUT)} percent in the rest of Uppland; in Fjädrundaland all {FJ[1]}.

**In plain words.** Within thirty kilometres of Holm in Vittinge two stones in three have ʀ written with the ordinary r-rune at least once, in the rest of the country about one in eight, and in none of 999 random redistributions of the spelling did any area become as extreme.

## 6. Discussion

**What the finding says.** Western Uppland is the area of Sweden where ʀ was most often written with the r-rune, and that is not because of early stones or a single prolific carver: the cluster remains with dating period and carver constant, in each half, without moved stones and without Erik.

**Against earlier research.** The result sharpens Larsson's (2002) observation that Uppland and Västergötland stand out, recovers his group in Västergötland and confirms Stille (1999) on Erik. Larsson explains Uppland's share by time and individual carvers rather than by location; within Uppland there is nonetheless a bounded area that remains with both held constant. It borders on Västmanland, where Larsson has 45 percent (on 27 instances); perhaps this is a western zone rather than an Uppland trait.

**Where we depart from earlier research.** Stille and Larsson read the r-rune as pronunciation. Larsson's reasons concern runic writing at large: they show that many carvers wrote by ear, not that all did, and do not explain why one district differs so sharply. For western Uppland we propose a writing tradition that began with Erik and was passed on in the district:

1. Erik wrote r on all fifteen stones in the material securely or uncertainly attributed to him, including the two outside the cluster: U 774, {OUT_774} kilometres outside the circle, with a questioned attribution (Jansson in Upplands runinskrifter 3, pp. 324, 352, after Larsson 2002, section 7.2.3), and the uncertain U 732, {OUT_732} kilometres outside. Where Larsson, after Peterson (1983), sees the carvers' wavering between the runes as a sound change in progress, Erik does not waver; he writes as if by a rule.
2. Åsmund wrote the yr-rune on all his thirteen stones, including the three within the cluster; the place did not decide his spelling, but these are only three stones.
3. The spelling lives on in the district after Erik, and the cluster remains with the carver held constant.

With Erik and Åsmund the spelling followed the carver, but the cluster remains with the carver held constant; for the rest of the district the material cannot separate carver from place. If the carvers spoke a variety in which the sounds had merged, that gives the same pattern, and Balli points that way (5.4). The test is whether the later r-stones stand in Erik's tradition – ornament, formulas, spelling otherwise – or merely in his district.

**Weaknesses, in order of weight.**

1. **Discovered, not pre-registered.** The boundary is chosen by the data; radius and centre are approximate.
2. **Erik carries the early part.** {EA_IN[1] - 2} of {EA_IN[1]} early stones in the cluster are attributed to him by style, and several attributions have been questioned (Larsson 2002, section 7.2.3); without him the margin is smaller.
3. **Uneven attributions.** The attributions are denser in the cluster ({ATTR_IN[0]} of {ATTR_IN[1]} against {pc(ATTR_OUT)} percent), since Stille (1999) attributed the stones of Fjädrundaland systematically; the comparisons of carvers rest on uneven ground.
4. **Few words, no hand check.** Often one or two endings per stone, mostly *æftiʀ*, and a single r is enough; a misread yr-rune or a different normalisation moves individual stones.

**What would overturn the finding.** A hand reading in which the r-forms in the cluster are more often uncertain than outside it, or new finds in the district with the yr-rune.

## 7. Conclusion

Within {CL['radius_km']:.1f} kilometres of Holm in Vittinge, {pc(CL['rate_in'])} percent of the runestones have at least one r for ʀ, against {pc(CL['rate_out'])} percent in the rest of the country, and the cluster withstands every sensitivity analysis. With Erik and Åsmund the spelling followed the carver, but the cluster remains with the carver held constant; for the rest of the district the material cannot separate carver from place. We propose a writing tradition that began with Erik; pronunciation, as Stille and Larsson hold, is not yet ruled out.

## Data and code

The analysis was made in Vitki {APP_VERSION}, an open research tool for runestones ([vitkirunor.se]({SITE}/en)). Code state: commit {CODE_COMMIT} in https://github.com/Precatio/runes (Vitki {APP_VERSION} plus later changes). The code and result files are there under GPL-3.0.

- The trait: `src/language_profile.py`, `src/pattern_map.py`; the search: `r/hotspots.R`; the sensitivity analyses: `r/robustness.R`, `src/robustness.py` (`METHODS.md`, 1f and 1v); the results under the material's version `{FP}`; the figures: `utdata/rapporter/figurer/karta_r_for_R.R`. The report is built by `utdata/blogg/build/build_rapport_r_for_R.py`, which stops if any figure disagrees.
- In Vitki: Statistics, Geography, and Map, Patterns. Glossary: {SITE}/en/forskningsrapporter/begrepp.
- Popular account: [Erik wrote r – and the district followed]({SITE}/en/artiklar/{ART_SLUG}), recomputed on 31 October 2026 with the same figures as here.

## References

- Axelson, J. 1993. *Mellansvenska runristare. Förteckning över signerade och attribuerade inskrifter*. Runrön 5. Uppsala.
- Benjamini, Y. & Hochberg, Y. 1995. Controlling the false discovery rate: a practical and powerful approach to multiple testing. *Journal of the Royal Statistical Society B* 57 (1), pp. 289–300.
- Getis, A. & Ord, J. K. 1992. The analysis of spatial association by use of distance statistics. *Geographical Analysis* 24 (3), pp. 189–206.
- Gräslund, A.-S. 2006. Dating the Swedish Viking-Age rune stones on stylistic grounds. In: M. Stoklund et al. (eds), *Runes and their Secrets: Studies in Runology*. Copenhagen, pp. 117–139.
- Hartig, F. 2022. *DHARMa: Residual diagnostics for hierarchical (multi-level/mixed) regression models*. R package.
- Kulldorff, M. 1997. A spatial scan statistic. *Communications in Statistics – Theory and Methods* 26 (6), pp. 1481–1496.
- Källström, M. 2010. Åsmund, Öpir och Önjut – om individens betydelse för bilden av vikingatidens språkhistoria. In: E. Magnusson & L. Rogström (eds), *Språkhistoria – hur och för vem?* Studier i svensk språkhistoria 10. Gothenburg, pp. 163–174. (Not read.)
- Källström, M. 2014. Från Forneby till Gamla Uppsala – några nyheter om runristaren Erik. In: *Festskrift till Per Stille*. Humanetten 32. Växjö, pp. 33–41. (Not read.)
- Larsson, P. 2002. *Yrrunan. Användning och ljudvärde i nordiska runinskrifter*. Runrön 17. Uppsala.
- Moran, P. A. P. 1950. Notes on continuous stochastic phenomena. *Biometrika* 37 (1–2), pp. 17–23.
- Peterson, L. 1983. Om s.k. palatalt r i fornsvenskan. *Arkiv för nordisk filologi* 98, pp. 202–220. (Cited after Larsson 2002, section 7.3.)
- Swedish National Heritage Board (Riksantikvarieämbetet). *Runor* (2020 edition of the Scandinavian Runic-text Database). https://runor.raa.se, retrieved 2026-10-16.
- Scandinavian Runic-text Database (Rundata), 2014 edition, updated 2018. Department of Scandinavian Languages, Uppsala University. https://www.nordiska.uu.se/forskn/samnord.htm, retrieved 2026-10-04. Open Database License (ODbL) 1.0 / Database Contents License (DbCL) 1.0.
- Stille, P. 1999. *Runstenar och runristare i det vikingatida Fjädrundaland. En studie i attribuering*. Runrön 13. Uppsala.

:::box The essentials
- In western Uppland, around Simtuna, Vårfrukyrka and Tillinge, the old sound ʀ was written with the ordinary r-rune on far more runestones than anywhere else in Sweden.
- Erik and Åsmund spelled as they were used to wherever they carved, and the district carried on after Erik; whether that was the carvers' habit or the district's speech the stones cannot decide.
- Our hypothesis is a writing tradition. Earlier research has read it as pronunciation, and the stones cannot yet decide who is right.
:::

{LOG_EN}
"""

# the plain-words sentence rests on these numbers (mallen version 4): 24 of 36 is two in three, 13 % about one in eight
assert (CL["cases"], CL["n"]) == (24, 36) and abs(CL["rate_out"] - 1 / 8) < 0.01
assert "24 av 36 stenar" in body and "mot 13 procent av stenarna i resten" in body
assert "999 simuleringar" in body and "30,4 kilometer" in body
assert "I klartext" in body and "In plain words" in body_en
assert "två stenar av tre minst en gång ʀ skrivet med den vanliga r-runan" in body
assert "two stones in three have ʀ written with the ordinary r-rune at least once" in body_en
# version 3: the claims that were corrected must not come back
for b in (re.split(r"## (?:Ändringslogg|Change log)", x)[0] for x in (body, body_en)):  # the change log names them
    assert "står kvar på sin ursprungliga plats" not in b and "eller Riksantikvarieämbetets register Runor" not in b
    assert "snarare än platsen" not in b and "rather than the place" not in b
    assert "med äldre siffror" not in b and "with older figures" not in b
    assert not re.search(r"(?<!!)\[[^\]]*\]\((?!https://)", b), "alla länkar absoluta (bilderna går via sajtens figurlager)"
    assert "Någon release med DOI" not in b and "No release with a DOI" not in b
    assert "Rapportversion 3, 2026-11-05 (först publicerad 2026-10-31)." in b or "Report version 3, 2026-11-05 (first published 2026-10-31)." in b
for b in (body, body_en):
    for cap in re.findall(r"^\*\*(?:Figur|Figure) \d\.\*\*.*$", b, re.M):
        assert cap.endswith(MAP_SV) or cap.endswith(MAP_EN), cap
assert body.count("**Version ") == body_en.count("**Version ") == 2
JARGON = r"modul\w*|trapp\w*|q_global|korpusjobb|fingeravtryck|fingerprint|facit|Vitkis|Vitki's|\bthe app\b|\bappen\b|`[^`]*/[^`]*`|METHODS"
for b in (body, body_en):
    assert not re.search(r"^\|", b, re.M), "BlogBody har inga tabeller"
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M)), "varje ruta ska stängas"
    assert "{" not in b and "}" not in b
    head = b.split("## Data")[0]
    assert not re.findall(JARGON, head), re.findall(JARGON, head)  # the locked template: no internal names before Data och kod
assert "Det viktigaste i korthet" in body and "## 2. Förregistrering" in body and "## 6. Diskussion" in body
assert len(body.split()) <= 3000, len(body.split())  # mallen: 1 500–3 000 ord

out = {"slug": SLUG, "title": title, "summary": summary, "body": body, "title_en": title_en, "summary_en": summary_en,
       "body_en": body_en, "labels": ["Rapport", "Språk och stavning", "Geografi", "Ristare"]}
assert blog_labels.check(out["labels"]) is None
path = os.path.join(ROOT, "utdata", "rapporter", "rapport_r_for_R.json")
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
                 "topic": "Rapport|r_for_R", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
