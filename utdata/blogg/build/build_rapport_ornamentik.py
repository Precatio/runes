"""Forskningsrapport, metodrapport (låst mall utdata/rapporter/MALL.md, version 4; Metodrapport, delvis prövad):
"Ornamentiken som mätbar källa" (sv + en). Ett register över rundjurens drag (kodbok v2, två oberoende läsare, konsensus,
kappa), källkontrollen av 1600- och 1700-talens teckningar mot planschfotona, de negativa vägarna till huvudets detaljer
(djupbilder, utsnitt), luckfyllnaden ur teckningar, valideringen (budskap och bild), skrift mot bild, Gräslund 1 och
ristargrupperna. Planerna i analysplaner/ (åtta, se PLANS) och resultaten i utdata/nya_ristare/resultat.md §§ 10–14,
utdata/nya_ristare/ornamentik/ och utdata/graslund/. Alla siffror asserteras mot filerna.

Figurerna är build_ornamentik.py:s (utdata/blogg/figurer/ornamentik/): läsningen av U 1154 i Bautil och Sö 112 i Bautil
bredvid djupbilden ur Kitzler Åhfeldts skanning (CC BY 4.0). SRI:s planscher är skyddade och visas aldrig. Koderna per sten
sägs finnas i Vitki; inget sägs om att de ges ut som öppen datamängd (Viktors beslut).
    ../../../.venv/bin/python build_rapport_ornamentik.py [--write | --update DOC]"""
import csv
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_figures, blog_labels  # noqa: E402
from utdata.nya_ristare.ornamentik.m2 import consensus  # noqa: E402

assert open(os.path.join(ROOT, "utdata", "rapporter", "MALL.md.sha256")).read().startswith("611a4d5f")  # mallens version 4
FP = "510ebfb3acc9a229"
APP_VERSION = "3.1.0"
REPORT_VERSION = 1
TODAY = "2026-11-25"
ORN = os.path.join(ROOT, "utdata", "nya_ristare", "ornamentik")
GD = os.path.join(ROOT, "utdata", "graslund")
CACHE = os.path.join(ROOT, "data", "cache", "hander", "ornamentik")
J = lambda *p: json.load(open(os.path.join(*p), encoding="utf-8"))  # noqa: E731
T = lambda *p: open(os.path.join(*p), encoding="utf-8").read()  # noqa: E731

# ---- planerna: kontrollsumman ur .sha256-filen; två planer saknar sådan och kontrolleras mot den låsta commiten ----------
PLANS = {"orn": "2026-11-24-nya-ristare-ornamentik.md", "kk": "2026-11-25-ornamentik-kallkontroll-teckningar.md",
         "3d": "2026-11-25-ornamentik-3d-halsingland-medelpad.md", "gr1": "2026-11-25-graslund-1-stilgrupper.md",
         "huvud": "2026-11-25-graslund-huvudmodul-pilot.md", "luckor": "2026-11-25-teckningar-fyller-luckor.md",
         "sr": "2026-11-25-skrev-och-ritade.md", "bb": "2026-11-25-budskap-och-bild.md"}
SHA = {}
for k, f in PLANS.items():
    p = os.path.join(ROOT, "analysplaner", f)
    if os.path.exists(p + ".sha256"):
        SHA[k] = open(p + ".sha256").read().split()[0]
        assert hashlib.sha256(open(p, "rb").read()).hexdigest() == SHA[k], f
assert set(SHA) == {"orn", "kk", "3d", "gr1", "sr", "bb"}
assert [SHA[k][:8] for k in ("orn", "kk", "3d", "gr1", "sr", "bb")] == \
    ["bec4b16b", "1298fbcc", "3f5741ee", "69d74f4e", "7ae43d01", "73c2c690"]


def _at(commit, f):
    return hashlib.sha256(subprocess.run(["git", "show", f"{commit}:analysplaner/{f}"], cwd=ROOT, capture_output=True,
                                         check=True).stdout).hexdigest()


SHA["huvud"] = _at("a87beda", PLANS["huvud"])          # låst före pilot 1
SHA["huvud2"] = _at("609c89c", PLANS["huvud"])         # pilot 2 inskriven före körningen
SHA["luckor"] = _at("161dae7", PLANS["luckor"])
assert (SHA["huvud"][:8], SHA["huvud2"][:8], SHA["luckor"][:8]) == ("bc48968b", "449ce637", "d1a61e19")
assert hashlib.sha256(open(os.path.join(ROOT, "analysplaner", PLANS["luckor"]), "rb").read()).hexdigest() == SHA["luckor"]
assert hashlib.sha256(open(os.path.join(ORN, "kodbok.md"), "rb").read()).hexdigest().startswith("97cf9214")
PL = {k: T(ROOT, "analysplaner", f) for k, f in PLANS.items()}
Q_ORN = "**Håller** om p < 0,05 och medelskillnaden > 0"
Q_KK = "när kappa mot planschen är ≥ 0,40 och minst 15 stenar kan jämföras"
Q_SR = "**P1 håller** om korrelationen är större än 0 och ensidigt p < 0,05"
Q_BB = "**B1 håller** om ρ > 0 och ensidigt p < 0,05"
Q_GR = "Det väntas hålla, eftersom stilgrupperna sattes efter samma slags drag. Det intressanta är mönstret i felen."
for k, q in (("orn", Q_ORN), ("kk", Q_KK), ("sr", Q_SR), ("bb", Q_BB), ("gr1", Q_GR)):
    assert q in PL[k], k
assert "Cohens kappa ≥ 0,40 och täckning ≥ 0,30" in PL["orn"] and "Två piloter på 12 och 20 stenar" in PL["orn"]
assert "fem stenar\n  per läsare och omgång, i omvänd ordning för den andra läsaren" in PL["orn"]
assert "minst **0,6** vardera" in subprocess.run(["git", "show", f"a87beda:analysplaner/{PLANS['huvud']}"], cwd=ROOT,
                                                  capture_output=True, text=True).stdout
assert "Bautils träsnitt (Umeå-exemplaret): 40 stenar" in PL["kk"] and "övriga teckningar som SRI återger (Bureus" in PL["kk"]
assert "ρ = 0,23 mot 0,07, p = 0,002" in PL["bb"] and "ρ = 0,08 mot 0,05, p = 0,036" in PL["bb"]
assert "Budskapet** (12 kategorier, se nedan): ρ = 0,23 mot 0,07, p = 0,002" in PL["bb"]
assert "**Totalt:** 456 stenar och 10 968 par" in PL["bb"] and "σ = 12 mm" in PL["3d"]
assert "Med färre än 8 ristare redovisas P2 bara beskrivande" in PL["sr"]

# ---- registret och läsarna (resultat.md § 10) -------------------------------------------------------------------------
RES = T(ROOT, "utdata", "nya_ristare", "resultat.md")
M2 = J(ORN, "m2_utveckling.json")
F = M2["fält"]
assert M2["stenar_med_kod"] == 981 and len(M2["godkända_fält"]) == 14 and len(F) == 17
KAP = {f: F[f]["kappa"] for f in M2["godkända_fält"]}
assert (min(KAP.values()), max(KAP.values())) == (0.72, 0.99)
assert [F[f]["kappa"] for f in ("djurhuvud", "huvud_vy", "oga", "koppel")] == [0.95, 0.93, 0.92, 0.91]
assert [F[f]["kappa"] for f in ("lappflik", "flatverk", "nackflik", "fotter", "svans")] == [0.80, 0.79, 0.78, 0.76, 0.72]
TACK = [F[f]["tackning"] for f in ("djurhuvud", "antal_djur", "huvud_vy", "oga", "nackflik", "lappflik", "svans")]
assert (min(TACK), max(TACK)) == (0.35, 0.62) and (F["nackflik"]["tackning"], F["lappflik"]["tackning"]) == (0.38, 0.35)
assert (F["mun"]["tackning"], F["huvud_svans"]["kappa"], F["kontur"]["kappa"]) == (0.08, 0.27, None)
assert set(F) - set(M2["godkända_fält"]) == {"mun", "huvud_svans", "kontur"}
for s in ("1 170 stenar", "64 stenar hade ingen användbar bild", "981 stenar har tillräckligt med eniga drag",
          "56 540 par inom 30 km", "478 av 744 fall (64 %)", "Läsarna:** två läsare per sten. Kappa var 0,67–1,0"):
    assert s in RES, s
N_PLANSCH, N_KORPUS, N_UTAN_BILD, STIL_LIKA, STIL_N = 1170, 2314, 64, 478, 744
assert "2 314" in PL["orn"] and "1 170" in PL["orn"]

KK = J(ORN, "kallkontroll.json")
K3 = J(ORN, "kallkontroll_3d.json")
HSM = K3["hs_m"]
FOTO = {s: v for s, v in HSM["stenar"].items() if v["bild"] == "foto + djupbild"}
assert KK["gotland_öland_kodade"] == 43 and HSM["kodade"] == 17 and len(FOTO) == 11
assert (min(v["fält"] for v in FOTO.values()), max(v["fält"] for v in FOTO.values())) == (5, 14)
FL = J(CACHE, "orn_koder_forlorade.json")
FB = {s["sig"] for b in J(CACHE, "forlorade_batcher.json") for s in b["stones"]}
KALLA = Counter(v["källa"] for v in FL.values())
N_LOST3 = sum(1 for v in FL.values() if len(v["koder"]) >= 3)
assert (len(FB), len(FL), N_LOST3) == (200, 185, 167) and "196 teckningar gick att läsa" in RES
assert (KALLA["Bautil"], KALLA["Peringskiöld"], KALLA["Rhezelius"], KALLA["SRI-text"]) == (135, 24, 13, 13)
assert all("lappflik" not in v["koder"] and "fotter" not in v["koder"] for v in FL.values())
UT = J(CACHE, "orn_koder_utvidgning.json")
assert not (set(FL) & set(UT)) and Counter(s.split()[0] for s in UT) == {"Öl": 22, "G": 21, "Hs": 8, "M": 7}
N_REG = M2["stenar_med_kod"] + KK["gotland_öland_kodade"] + len(FOTO) + len(FL)
assert N_REG == 1220
import pandas as pd  # noqa: E402

CORP = pd.read_csv(os.path.join(ROOT, "data", "cache", "r", "corpus", FP, "corpus.csv"), low_memory=False).set_index("signum")
N_LOST_UTAN_STIL = int(CORP.loc[list(FL), "style"].isna().sum())
assert N_LOST_UTAN_STIL == 135
OC = J(CACHE, "orn_koder.json")
assert not (set(OC) & set(FL)) and not (set(OC) & set(UT))
OC3 = [s for s, v in OC.items() if len(v) >= 3]
N_PL_LOST = sum(1 for s in OC3 if s in CORP.index and CORP.loc[s, "lost"] == 1)
assert (len(OC3), N_PL_LOST) == (1036, 41)
_PLT = J(ROOT, "data", "cache", "hander", "plansch", "teckningar.json")["_plansch_ar_teckning"]
N_PL_TECKN = sum(1 for s in OC3 if s in CORP.index and CORP.loc[s, "lost"] == 1 and _PLT.get(s))
assert N_PL_TECKN == 26

# ---- källkontrollen av teckningarna (§ 11) ----------------------------------------------------------------------------
TP = KK["teckning_mot_plansch"]["alla"]
KT = {f: TP[f]["kappa"] for f in TP}
PT = KK["per_typ"]
assert KK["teckningar"] == 129 and (PT["bautil"], PT["rhezelius"], PT["peringskiold"], PT["ovrig"]) == (37, 37, 28, 27)
assert (KT["nackflik"], KT["djurhuvud"], KT["koppel"], KT["huvud_vy"], KT["kors"], KT["flatverk"], KT["antal_djur"]) == \
    (0.88, 0.86, 0.86, 0.83, 0.81, 0.74, 0.73)
assert (KT["svans"], KT["oga"], KT["lappflik"], KT["fotter"]) == (0.60, 0.57, 0.30, 0.0)
assert (TP["lappflik"]["jämförbara"], TP["nackflik"]["jämförbara"], TP["fotter"]["jämförbara"]) == (16, 19, 39)
LT = [KK["läsarna_teckningar"][f]["kappa"] for f in M2["godkända_fält"] if KK["läsarna_teckningar"][f]["kappa"] is not None]
assert (min(LT), max(LT)) == (0.68, 1.0)
USE = KK["fält_som_får_läsas"]
assert len(USE["bautil"]) == 11 and USE["bautil"] == USE["rhezelius"] and set(USE["ovrig"]) - set(USE["bautil"]) == {"manniska_mask"}
assert all("lappflik" not in v and "fotter" not in v for v in USE.values())
BT = KK["teckning_mot_plansch"]["bautil"]["djurhuvud"]
assert (BT["jämförbara"], BT["lika"]) == (17, 1.0)
assert "5–17 jämförbara stenar per fält" in RES and "Urvalet drog 140 teckningar" in RES
# hur många av jämförelserna hade en flik alls (konsensus för teckning och plansch, räknat på nytt som i build_ornamentik.py)
_draw = defaultdict(dict)
for r in J(CACHE, "kodning_kallkontroll.json"):
    if r["batch"].startswith("t"):
        for s in r["stenar"] or []:
            _draw[s["signum"].strip()][r["coder"]] = s
DC = consensus(_draw)


def _par(f):
    return [(DC[s][f], OC[s][f]) for s in DC if s in OC and f in DC[s] and f in OC[s]]


NP, LP, FOT = _par("nackflik"), _par("lappflik"), _par("fotter")
NP_LIKA = sum(a == b for a, b in NP)
NP_FLIK = sum(1 for a, b in NP if a != "ingen" or b != "ingen")
LP_FLIK = sum(1 for a, b in LP if a != "ingen" or b != "ingen")
FOT_INGA = sum(1 for a, b in FOT if a == b == "inga")
assert (len(NP), NP_LIKA, NP_FLIK, len(LP), LP_FLIK, len(FOT), FOT_INGA) == (19, 18, 5, 16, 2, 39, 38)
U1154 = [f for f in M2["godkända_fält"] if f in DC["U 1154"] and f in OC["U 1154"]]
assert len(U1154) == 9 and all(DC["U 1154"][f] == OC["U 1154"][f] for f in U1154) and DC["U 1154"]["huvud_vy"] == "uppifran"
assert CORP.loc["U 1154", "parish"] == "Simtuna sn" and CORP.loc["U 1154", "style"] == "Fp"

# ---- djupbilderna (§ 13), utsnitten (huvud/pilot*), luckorna (§ 14) ---------------------------------------------------
D3 = K3["djupbild_mot_plansch"]
L3 = [K3["läsarna_djupbild"][f] for f in ("djurhuvud", "antal_djur", "huvud_vy", "oga")]
assert K3["källkontroll_stenar"] == 24 and K3["fält_som_får_läsas_ur_djupbild"] == ["orm_extra"] and (min(L3), max(L3)) == (0.41, 0.63)
assert (D3["djurhuvud"]["kappa"], D3["huvud_vy"]["kappa"], D3["oga"]["kappa"], D3["antal_djur"]["kappa"]) == (0.36, 0.10, -0.06, -0.14)
assert D3["svans"]["jämförbara"] == 0 and (D3["koppel"]["kappa"], D3["orm_extra"]["kappa"], D3["kors"]["kappa"], D3["flatverk"]["kappa"]) == (1.0, 1.0, 1.0, 0.58)
assert [f for f in D3 if (D3[f]["jämförbara"] or 0) >= 15 and (D3[f]["kappa"] or 0) >= 0.40] == ["orm_extra"]
_d3 = defaultdict(dict)
for r in J(CACHE, "kodning_djup_hsm.json"):
    if r["batch"].startswith("d"):
        for s in r["stenar"] or []:
            _d3[s["signum"].strip()][r["coder"]] = s
DC3 = consensus(_d3)
assert DC3["Sö 112"]["huvud_vy"] == "profil" and OC["Sö 112"]["huvud_vy"] == "uppifran"
assert CORP.loc["Sö 112", "parish"] == "Stenkvista sn"
from src import scan_sources  # noqa: E402

DS = {d["key"]: d for d in scan_sources.DATASETS}
assert DS["sodermanland"]["doi"] == "10.5281/zenodo.11951255" and all(d["license"] == "CC BY 4.0" for d in DS.values())
assert "Henrik Zedig" in str(DS["halsingland"]) and "Henrik Zedig" in str(DS["medelpad"])
DOIS = {k: DS[k]["doi"] for k in ("sodermanland", "vastergotland", "gravmonument_og_sm", "asmund", "halsingland", "medelpad")}
P1H, P2H = J(GD, "huvud", "pilot.json"), J(GD, "huvud", "pilot2.json")
assert (P1H["stenar"], P1H["täckning"]["nackflik"], P1H["täckning"]["lappflik"], P1H["regel"]["håller"]) == (30, 0.37, 0.40, False)
assert (P2H["stenar"], P2H["täckning"]["nackflik"], P2H["täckning"]["lappflik"], P2H["regel"]["håller"]) == (30, 0.17, 0.13, False)
assert P2H["läsare1_mot_2"]["oga"]["kappa"] == 0.87 and P2H["mot_v2"]["oga"]["lika"] == 1.0
KB = J(ORN, "kombinera.json")
FILL = KB["ifyllda_värden"]
assert KB["teckningar_kodade"] == 140 and "Det blir 141 stenar" in PL["luckor"] and sum(FILL.values()) == 165
assert (FILL["oga"], FILL["nackflik"]) == (28, 25)
CV = KB["täckning_per_stilgrupp"]
NFC = {g: (CV[g]["nackflik"]["före"], CV[g]["nackflik"]["efter"]) for g in ("Pr1", "Pr2", "Pr3", "Pr4", "Pr5")}
assert NFC == {"Pr1": (0.33, 0.48), "Pr2": (0.29, 0.38), "Pr3": (0.27, 0.30), "Pr4": (0.12, 0.18), "Pr5": (0.28, 0.44)}
assert (CV["Pr4"]["oga"]["före"], CV["Pr4"]["oga"]["efter"]) == (0.48, 0.60)

# ---- budskap och bild (validering) -----------------------------------------------------------------------------------
BB = J(GD, "budskap_bild.json")
B1, BD = BB["B1"], BB["beskrivande"]
SRMD = T(GD, "skrev_ritade.md")
assert BB["stenar"] == 442 and BB["källor"] == {"utvidgning": 36, "plansch": 274, "teckning": 132} and B1["par"] == 8536
assert (round(B1["rho"], 3), round(B1["omblandning_medel"], 3), round(B1["omblandning_95"], 3), B1["p"]) == (0.227, 0.013, 0.049, 0.001) and B1["håller"]
PK = BD["per_källa"]
assert (round(PK["plansch"]["rho"], 2), PK["plansch"]["p"], round(PK["teckning"]["rho"], 2), PK["teckning"]["p"]) == (0.19, 0.002, 0.28, 0.002)
SS = BD["samma_stilgrupp"]
assert (SS["par"], round(SS["rho"], 2), round(SS["p"], 2)) == (83, 0.16, 0.09)
SM = BD["språkmarkörer"]
assert (round(SM["rho"], 3), round(SM["p"], 2)) == (0.031, 0.15)
UK = BD["utan_kategori"]
UK_OVR = [v for k, v in UK.items() if k != "pm_neutral"]
assert round(UK["pm_neutral"], 3) == 0.025 and (round(min(UK_OVR), 2), round(max(UK_OVR), 2)) == (0.23, 0.25)
for s in ("Ornamentiken utan fältet \"kors\":** budskapet ger ρ = 0,062 (p = 0,007)",
          "Utan både korset och `pm_neutral`:** ρ = 0,040 (p = 0,14)",
          "Planen räknade med 456 stenar"):
    assert s in SRMD, s

# ---- skrift och bild -----------------------------------------------------------------------------------------------------
SR = J(GD, "skrev_ritade.json")
P1, P3, P2, SB = SR["P1"], SR["P3"], SR["P2"], SR["beskrivande"]
assert SR["stenar"] == 580 and P1["par"] == 6387 and not P1["håller"] and not P3["håller"]
assert (P1["rho"], round(P1["omblandning_medel"], 3), P1["omblandning_95"], round(P1["p"], 2)) == (0.022, 0.011, 0.045, 0.29)
assert (P3["par"], round(P3["rho"], 3), P3["omblandning_medel"], round(P3["p"], 2)) == (3485, 0.030, 0.026, 0.46)
assert (P2["ristare"], P2["bara_beskrivande"], round(P2["partiell_mantel_rho"], 2), round(P2["p"], 2)) == (4, True, 0.83, 0.24)
assert sorted(P2["stenar"]) == ["Balle", "Visäte", "Åsmund", "Öpir 1"]
SU = SB["P1_utan_samma_socken"]
assert (round(SU["rho"], 3), round(SU["p"], 2)) == (0.022, 0.27)
PSG = SB["per_stilgrupp"]
assert (round(PSG["Pr1"]["rho"], 2), PSG["Pr1"]["par"], round(PSG["Pr4"]["rho"], 2), round(PSG["RAK"]["rho"], 2), round(PSG["Pr5"]["rho"], 2)) == (0.30, 109, 0.03, -0.10, -0.12)
SPD = SB["P1_språkdrag"]
assert (round(SPD["rho"], 2), round(SPD["omblandning_medel"], 2)) == (0.29, 0.10)
for s in ("6 748 par inom 30 km i samma stilgrupp", "ρ = 0,017 mot 0,036, p = 0,75",
          "Budskapet utan kors, kristna formler, själ, bön och hedniskt:** ρ = 0,19 mot 0,08, p = 0,005, 199 omblandningar"):
    assert s in SRMD, s

# ---- Gräslund 1 ----------------------------------------------------------------------------------------------------------
G = J(GD, "graslund1.json")
F1, F2, F3, F4 = G["F1"], G["F2"], G["F3"], G["F4"]
GRES = T(GD, "resultat.md")
STYLES = ["RAK", "Fp", "Pr1", "Pr2", "Pr3", "Pr4", "Pr5"]
CONF = F1["förväxlingar"]
N_STIL = {s: sum(CONF[s].values()) for s in STYLES}
HIT = {s: CONF[s].get(s, 0) / N_STIL[s] for s in STYLES}
pc = lambda x: int(100 * x + 0.5 + 1e-9)  # noqa: E731  (halvor uppåt, som i resultat.md)
assert F1["stenar"] == 620 and N_STIL == {"RAK": 146, "Fp": 96, "Pr1": 28, "Pr2": 69, "Pr3": 90, "Pr4": 160, "Pr5": 31}
assert {s: pc(HIT[s]) for s in STYLES} == {"RAK": 92, "Fp": 63, "Pr1": 32, "Pr2": 41, "Pr3": 22, "Pr4": 84, "Pr5": 0}
assert (pc(F1["träffsäkerhet"]), pc(F1["vanligaste_gruppen"]), pc(F1["omblandning_medel"]), F1["p"]) == (62, 26, 22, 0.001)
assert N_STIL["Pr5"] - CONF["Pr5"].get("Pr4", 0) == 4 and "41 indikatorer ur 14 fält" in GRES
assert (F2["fel_inom_Pr"], F2["avstånd"]["1"], F2["avstånd"]["2"], F2["avstånd"]["3"]) == (158, 131, 24, 3)
assert (pc(F2["andel_till_granne"]), pc(F2["omblandning_medel"]), F2["p"]) == (83, 59, 0.001)
K = {c["stenar"]: c["rundata"] for c in F3["klasser"]}
assert F3["k"] == 3 and sorted(K) == [134, 191, 295] and round(F3["ARI_mot_rundata"], 2) == 0.34
assert (K[191]["RAK"], K[191]["Fp"], K[134]["Fp"], K[134]["Pr2"], K[295]["Pr4"], K[295]["Pr3"]) == (141, 33, 56, 28, 144, 71)
assert (pc(F4["inom_uppland_cv"]), pc(F4["Sö"]["träffsäkerhet"]), pc(F4["Ög"]["träffsäkerhet"])) == (59, 41, 69)
ROWS = list(csv.DictReader(open(os.path.join(GD, "stil_sannolikhet.csv"), encoding="utf-8")))
assert len(ROWS) == 620


def _saknas(f, g):
    rs = [r for r in ROWS if r["rundata"] == g]
    return sum(1 for r in rs if f not in OC.get(r["signum"], {})) / len(rs)


NACK = [_saknas("nackflik", g) for g in ("Pr2", "Pr3", "Pr4", "Pr5")]
LAPP = [_saknas("lappflik", g) for g in ("Pr2", "Pr3", "Pr4", "Pr5")]
assert (pc(min(NACK)), pc(max(NACK)), pc(min(LAPP)), pc(max(LAPP))) == (75, 91, 84, 90)
assert "Pr4: nackflik saknas för 146 av 160 stenar" in GRES
FPV = Counter(OC[r["signum"]]["huvud_vy"] for r in ROWS if r["rundata"] == "Fp" and "huvud_vy" in OC.get(r["signum"], {}))
assert (FPV["uppifran"], sum(FPV.values())) == (32, 52)

# ---- ristargrupperna (§ 10, grind och slutprov) ---------------------------------------------------------------------------
S3 = J(ORN, "slutprov3.json")
O1, O2 = S3["O1"], S3["O2"]
assert M2["G1"]["håller"] and M2["G1"]["grupper"] == 10 and round(M2["G1"]["median_percentil"], 2) == 0.67 and round(M2["G1"]["p"], 3) == 0.002
assert (M2["G2"]["auc_M2"], M2["G2"]["auc_M1"]) == (0.768, 0.7642) and M2["tau2"] == 0.8
assert (O1["grupper"], O1["grupper"] - O1["med_skillnad"], O1["bättre"], O1["sämre"], O1["medel_M2"], O1["medel_M1"]) == (25, 19, 2, 4, 0.359, 0.403)
assert round(O1["p"], 2) == 0.78 and not O1["håller"] and O2["håller"]
assert (O2["grupper"], O2["medel_samma"], O2["medel_kontroll"]) == (42, 0.405, 0.075) and 8.0e-5 < O2["p"] < 8.2e-5
assert "Bara O2 höll" in RES and re.search(r"Andra användningen\s+av provdelen \(en återstår\)", RES)


# ---- formatering -----------------------------------------------------------------------------------------------------------
def dec(x, n=2, en=False):
    s = f"{x:.{n}f}".replace("-", "−")
    return s if en else s.replace(".", ",")


def kv(x, en=False):
    return "1" if x == 1.0 else dec(x, 2, en)


def pexp(p, en=False):
    m, e = f"{p:.1e}".split("e")
    m = m if en else m.replace(".", ",")
    return f"{m} · 10{str(int(e)).translate(str.maketrans('-0123456789', '⁻⁰¹²³⁴⁵⁶⁷⁸⁹'))}"


def num(n, en=False):
    return f"{n:,}".replace(",", "," if en else " ")


# ---- figurerna (build_ornamentik.py:s filer, frysta här) -------------------------------------------------------------------
FIGDIR = os.path.join(ROOT, "utdata", "blogg", "figurer", "ornamentik")
BAUTIL_SV = "Umeå universitetsbiblioteks exemplar, fritt från kända upphovsrättsliga restriktioner"
BAUTIL_EN = "Umeå University Library copy, free of known copyright restrictions"
SCAN_FILE = "So 112_1_4 thin_closed holes.stl"
assert J("/Volumes/2TB/cache/runmodell/djup/sodermanland/So_112_1_4_thin_closed_holes.json")["file"] == SCAN_FILE \
    if os.path.exists("/Volumes/2TB/cache/runmodell/djup/sodermanland/So_112_1_4_thin_closed_holes.json") else True


def bild(name, lang, caption):
    assert ("Figur: Vitki." if lang == "sv" else "Figure: Vitki.") in caption[-260:], "bildtexten ska säga att Vitki gjort bilden"
    url = blog_figures.freeze(open(os.path.join(FIGDIR, f"{name}_{lang}.png"), "rb").read())
    return f"![{caption.split('.')[0]}]({url})\n{caption}"


FIG1_SV = bild("lasning_u1154", "sv", f"Figur 1. Träsnittet av U 1154 (Simtuna socken) i Bautil, med utsnitten läsarna tittar på, de två läsarnas koder och det eniga värdet, och som text de eniga värdena från planschfotot av samma sten. I de {len(U1154)} drag där båda bilderna fick ett enigt värde gav de samma svar. Träsnitt nr 659 i J. Göranssons Bautil (1750), {BAUTIL_SV}. Figur: Vitki.")
FIG1_EN = bild("lasning_u1154", "en", f"Figure 1. The woodcut of U 1154 (Simtuna parish) in Bautil, with the crops the readers look at, the two readers' codes and the agreed value, and as text the agreed values from the plate photo of the same stone. In the {len(U1154)} features where both pictures got an agreed value, they gave the same answer. Woodcut no. 659 in J. Göransson's Bautil (1750), {BAUTIL_EN}. Figure: Vitki.")
FIG2_SV = bild("djupbild_so112", "sv", f"Figur 2. Sö 112 vid Kolunda (Stenkvista socken) i Bautil och i djupbilden. På planschfotot var läsarna eniga om huvuden sedda ovanifrån, i djupbilden om ett huvud i profil. Träsnitt nr 748 i J. Göranssons Bautil (1750), {BAUTIL_SV}. Djupbild beräknad i Vitki ur skanningen av Sö 112 av Laila Kitzler Åhfeldt (2024), Riksantikvarieämbetet, projektet Runristandets dynamik (2009–2014), CC BY 4.0, doi:{DOIS['sodermanland']}. Figur: Vitki.")
FIG2_EN = bild("djupbild_so112", "en", f"Figure 2. Sö 112 at Kolunda (Stenkvista parish) in Bautil and in the depth image. On the plate photo the readers agreed on heads seen from above, in the depth image on a head in profile. Woodcut no. 748 in J. Göransson's Bautil (1750), {BAUTIL_EN}. Depth image computed in Vitki from the scan of Sö 112 by Laila Kitzler Åhfeldt (2024), Swedish National Heritage Board, project Runristandets dynamik (2009–2014), CC BY 4.0, doi:{DOIS['sodermanland']}. Figure: Vitki.")


def chart(sv):
    namn = {"RAK": ("RAK – raka bandändar", "RAK – straight band ends"), "Fp": ("Fp – huvud ovanifrån", "Fp – head from above"),
            "Pr1": ("Pr1 – profil", "Pr1 – profile")}
    rows = [":::chart Stenar där rundjurets drag pekar ut Rundatas stilgrupp, procent" if sv
            else ":::chart Stones where the rune animal's features point to Rundata's style group, percent",
            "# Per stilgrupp, i Gräslunds ordning" if sv else "# By style group, in Gräslund's order"]
    for s in STYLES:
        rows.append(f"{namn.get(s, (s, s))[0 if sv else 1]} | {pc(HIT[s])} | {N_STIL[s]} {'stenar' if sv else 'stones'}")
    rows += ["# Alla stenar" if sv else "# All stones",
             f"+{'Rundjurets drag' if sv else 'The animal’s features'} | {pc(F1['träffsäkerhet'])} | {F1['stenar']} {'stenar' if sv else 'stones'}",
             f"{'Gissa alltid Pr4' if sv else 'Always guess Pr4'} | {pc(F1['vanligaste_gruppen'])} | –",
             "Korsvaliderat, grupperat på socken; provet låstes i förväg. Diagram: Vitki, ur kodningen av planscherna i Sveriges runinskrifter och Rundata 3.1."
             if sv else "Cross-validated, grouped by parish; the test was locked in advance. Chart: Vitki, from the coding of the plates in Sveriges runinskrifter and Rundata 3.1.",
             ":::"]
    return "\n".join(rows)


# ---- texten --------------------------------------------------------------------------------------------------------------
SLUG = "ornamentiken-som-matbar-kalla"
title = "Ornamentiken som mätbar källa"  # kort rubrik (Viktor 2026-11-25: rapportrubriker ska vara korta)
title_en = "Ornament as a measurable source"
summary = ("Metodrapport. Rundjurets drag på 1 220 runstenar kodades av två oberoende läsare efter en fast kodbok, och varje "
           "sorts bild prövades mot en annan innan den fick användas. 1600- och 1700-talens teckningar stämde med fotona i "
           "huvudet, nackfliken, kopplet och flätverket på 129 bevarade stenar, men kunde inte visas återge läppflik och "
           "fötter. Hur texten är stavad följer inte hur djuret är ritat, utöver bygd och stilgrupp.")
summary_en = ("Methods report. The rune animal's features on 1,220 runestones were coded by two independent readers with a "
              "fixed codebook, and every kind of picture was tested against another before it could be used. The drawings of "
              "the 1600s and 1700s agreed with the photographs on the head, the neck lappet, the koppel and the interlace on "
              "129 surviving stones, but could not be shown to render lip lappet and feet. How the text is spelled does not "
              "follow how the animal is drawn, beyond district and style group.")
CITE_EN = (f"Kvant, V. ({TODAY[:4]}). {title_en}. Research report (methods report), report version {REPORT_VERSION}; analysis in "
           f"Vitki {APP_VERSION}. https://vitkirunor.se/en/forskningsrapporter/{SLUG}")
TL_SV = ("planen för ornamentiken och kodboken låstes 2026-11-24; planschfotona kodades och grinden och slutprovet för "
         "grupperna av stenar med samma hand kördes 2026-11-25; planerna för källkontrollen av teckningarna och för "
         "stilgrupperna låstes och kördes 2026-11-25; de försvunna stenarna kodades ur teckningar 2026-11-25; planerna för "
         "djupbilderna och för skrift och bild låstes och kördes 2026-11-25; planerna för huvudet i utsnitt och för luckorna "
         "lades in och kördes 2026-11-25; planen för budskap och bild låstes och kördes 2026-11-25")
TL_EN = ("the plan for the ornament and the codebook were locked 2026-11-24; the plate photos were coded and the gate and the "
         "final test for the groups of stones by the same hand were run 2026-11-25; the plans for the source check of the "
         "drawings and for the style groups were locked and run 2026-11-25; the lost stones were coded from drawings "
         "2026-11-25; the plans for the depth images and for writing and drawing were locked and run 2026-11-25; the plans "
         "for the head in crops and for the gaps were committed and run 2026-11-25; the plan for message and image was "
         "locked and run 2026-11-25")
S = {k: f"`{v[:8]}…`" for k, v in SHA.items()}
NHEAD = ", ".join(f"{g} {pc(a)} → {pc(b)}" for g, (a, b) in NFC.items())

body = f"""*Viktor Kvant, oberoende forskare. Metodrapport, delvis prövad. Rapportversion {REPORT_VERSION}, {TODAY}. Tidslinje: {TL_SV}. Analysen är gjord i Vitki {APP_VERSION}. Licens CC BY 4.0. Den engelska versionen är den kanoniska för citering: {CITE_EN}. Nyckelord: runstenar, vikingatid, ornamentik, rundjursstil, Gräslunds stilgrupper, källkritik, antikvariska teckningar, Bautil, samstämmighet mellan bedömare, Cohens kappa, förregistrering. Konkurrerande intressen: inga. Finansiering: ingen.*

## Sammanfattning

**Vad som inte är prövat.** Instrumentet prövades i låsta källkontroller med gränser bestämda i förväg, men inte i ett blindprov med svaret dolt för hela kedjan: fotot som teckningarna mättes mot är självt en återgivning, läsarna är samma språkmodell och ingen människa har kodat ett kontrollurval. Två vägar till huvudets detaljer föll (djupbilder ur 3D-skanningar och förstorade utsnitt), och ornamentiken gjorde inte grupperna av stenar med samma hand bättre i ett låst slutprov.
**Bakgrund och syfte.** Rundjurets drag är grunden för Anne-Sofie Gräslunds stilgrupper och för mycket av dateringen av runstenarna, men de har beskrivits i ord, sten för sten. Syftet var att mäta ornamentiken över hela materialet, oberoende av texten, och att pröva bilderna måttet läses från.
**Material.** Planschfotona i Sveriges runinskrifter ({num(N_PLANSCH)} av {num(N_KORPUS)} svenska vikingatida runstenar i Rundata), fria foton, teckningar från 1600- och 1700-talen och öppna 3D-skanningar.
**Metod.** Två oberoende läsare besvarade en kodbok med 17 frågor om rundjuret. Ett drag fick värde bara när båda svarade lika, och ett fält användes bara med Cohens kappa ≥ 0,40 och täckning ≥ 30 procent. Varje ny sorts bild prövades mot fotona, och koderna ställdes i låsta prov mot texten, stilgrupperna och grupper av stenar med samma hand.
**Resultat.** Läsarna var eniga med kappa {kv(min(KAP.values()))}–{kv(max(KAP.values()))} i {len(KAP)} fält; registret omfattar {num(N_REG)} stenar, varav {len(FL)} försvunna. På {KK['teckningar']} bevarade stenar stämde teckningarna med fotona i huvudet, nackfliken och kopplet (kappa {kv(KT['huvud_vy'])}–{kv(KT['nackflik'])}), men inte påvisbart i läppflik och fötter, och djupbilderna stämde inte för huvudet. Tro och kors hänger ihop i koderna på {BB['stenar']} oberoende stenar. Stavningen följer inte ornamentiken utöver bygd och stilgrupp (Spearmans ρ = {dec(P1['rho'], 3)} mot {dec(P1['omblandning_medel'], 3)} vid omblandning, p = {dec(P1['p'])}).
**Slutsats.** Rundjurets huvuddrag går att mäta tillförlitligt, också på försvunna stenar, men inte huvudets detaljer, som Gräslunds finindelning bygger på. Om den svaga kopplingen mellan skrift och bild beror på arbetsdelning eller svaga spår av handen går inte att avgöra.

## 1. Inledning

Anne-Sofie Gräslund (1991, 1992, 2006) ordnade rundjuren på de sena vikingatida runstenarna i stilgrupper: RAK, där runbandets ändar är raka utan djurhuvud, Fp, där huvudet ses ovanifrån, och Pr1–Pr5, profilhuvuden i fem steg. Grupperna bygger på enskilda drag – huvudets vy, ögat, flikar vid nacke och läppar, svansen, fötterna, kopplet som binder ihop djuren – och används för att datera stenarna (Gräslund 2006, 2015). Bilderna, korsen och ristarna har studerats av bland andra Stern (2013), Lager (2002), Källström (2007) och Kitzler Åhfeldt (2002, 2017).

Dragen har däremot inte mätts över hela materialet; Rundata har stilgruppen men inte dragen. Många stenar finns bara kvar i teckningar: Bautils träsnitt, skurna på 1600-talet och tryckta 1750, Johannes Rhezelius teckningar från 1630-talet och Johan Peringskiölds från omkring 1700. Utgivarna av Sveriges runinskrifter bedömde dem sten för sten. Såvitt vi vet har de inte prövats drag för drag mot fotografier över ett större material.

Bidraget här är mätningen: ett register där ornamentiken kodas oberoende av texten, så att hur texten är skriven och hur djuret är ritat kan ställas mot varandra. Fyra prov visar vad registret bär: ett väntat samband mellan text och bild, stavningen, Gräslunds stilgrupper och grupper av stenar med samma hand.

## 2. Förregistrering

Arbetet följde åtta planer, lagda i projektets versionshantering innan det de gällde räknades, den första 2026-11-24 och de övriga 2026-11-25 (SHA-256 är filens kontrollsumma):
- **Ornamentiken och grupperna av stenar med samma hand** ({S['orn']}): kodbok version 2 (`97cf9214…`), regeln för fälten, en grind och ett slutprov som håller, ordagrant, ”om p < 0,05 och medelskillnaden > 0”.
- **Källkontrollen av teckningarna** ({S['kk']}), låst innan någon teckning kodades. Ett fält får läsas ”{Q_KK}”.
- **Stilgrupperna** ({S['gr1']}): bär dragen stilgruppen, och är Pr-grupperna en ordnad följd? Planen säger att det första väntas hålla och att ”det intressanta är mönstret i felen”.
- **Djupbilderna och Hälsingland och Medelpad** ({S['3d']}): samma regel som för teckningarna.
- **Huvudet i förstorade utsnitt** ({S['huvud']}; pilot 2 inskriven före körningen, {S['huvud2']}): nack- och läppflik ska få värde på minst 60 procent av stenarna.
- **Skrift och bild** ({S['sr']}): ”{Q_SR.replace('**', '')}”.
- **Teckningarna fyller luckor** ({S['luckor']}): beskrivande.
- **Budskap och bild** ({S['bb']}), ett bekräftande prov på oberoende stenar: ”{Q_BB.replace('**', '')}”.

Sambandet mellan budskap och bild hade setts i ett första urval; därför prövades det på andra stenar. Planerna för utsnitten och luckorna gäller instrument och arbetsgång; de lades in i versionshanteringen före körningen men låstes inte med kontrollsumma (summorna ovan är räknade på den commit som lade in dem). Det som kallas utforskande nedan ingick inte i någon plan.

## 3. Material

- **Stenarna:** Samnordisk runtextdatabas (Rundata) 3.1, fryst för analysen: {num(N_KORPUS)} svenska vikingatida runstenar med koordinater och Rundatas stilgrupper.
- **Bilderna:** planschfotona i Sveriges runinskrifter ({num(N_PLANSCH)} stenar; upphovsrättsligt skyddade, lästa men inte visade), Gotlands och Ölands planscher, fria foton av de målade stenarna i Hälsingland och Medelpad, Bautil i Umeå universitetsbiblioteks exemplar, andra teckningar så som Sveriges runinskrifter återger dem, och Laila Kitzler Åhfeldts och Henrik Zedigs öppna 3D-skanningar (CC BY 4.0).
- **Texten:** stavningen, kategoriska språkdrag och tolv kategorier för vad texten säger, kodade per sten ur Rundata.

## 4. Metod

### 4.1 Kodboken och läsarna
- **Kodboken** har 17 frågor om rundjuret (djurhuvud, antal djur, huvudets vy, öga, nack- och läppflik, mun, svans, fötter, koppel, flätverk, kors med flera), alltid med svaret ”osäkert”. Huvud, svans och bandändar ska förstoras innan de kodas. Två piloter (12 och 20 stenar utanför provmaterialet) föregick låsningen.
- **Läsarna** var två separata körningar av Anthropics språkmodell Claude (Claude Opus). De såg bara bilden och signum, fem stenar i taget i motsatt ordning, och ombads att inte använda kunskap om stenen eller litteraturen.
- **Värdet** är det som båda anger; annars saknas det.
- **Cohens kappa** (Cohen 1960) är andelen lika svar med slumpens bidrag borträknat: 1 är full enighet, 0 inte bättre än slumpen. **Täckningen** är andelen stenar där båda gav ett värde.

### 4.2 Källkontrollerna
- **Principen:** en ny sorts bild prövas mot planschfotot på bevarade stenar som finns i båda, med nya läsare. Måttet är om två återgivningar av samma sten säger samma sak.
- **Teckningarna:** slumpvis 40 ur Bautil, 40 av Rhezelius, 30 av Peringskiöld och 30 av andra tecknare.
- **Djupbilderna:** ytan minus samma yta utjämnad över 12 mm, så att ristade linjer blir mörka, på {K3['källkontroll_stenar']} skannade stenar.
- **Huvudet i utsnitt:** två piloter på 30 stenar där nackfliken saknade värde: utskurna huvuden, två läsare och en tredje vid oenighet, i pilot 2 med ett schematiskt profilhuvud och utsnitt förstorade till minst 1 000 bildpunkter.
- **Luckor och försvunna stenar:** teckningar kodades för 141 bevarade stenar som saknade nackflik och för {len(FB)} försvunna stenar, bara i godkända fält och märkta med tecknare. Ett planschvärde ersattes aldrig.

### 4.3 Proven
- **Likheterna** mellan två stenar: i ornamentiken andelen lika värden bland minst tre gemensamma fält; i stavningen stavningsdragen vägda efter hur ovanliga de är; i budskapet tolv kategorier (som minne, bro och väg, färd, arv, och att texten saknar religiösa markörer).
- **Proven** mäter Spearmans ρ mellan två likheter över stenpar inom 30 km, mot 999 omblandningar av ornamentkoderna inom härad och stilgrupp (skrift) eller härad och bildkälla (budskap), så att bygden och, så långt stilgruppen räcker, tiden hålls konstant.
- **Stilgrupperna:** multinomial logistisk regression, korsvaliderad med socknar som enheter; felen inom Pr räknas efter avstånd i följden. En latent klassmodell söker grupper utan att se stilgrupperna, jämförd med Rundata med justerat Rand-index (0 som slumpen, 1 identiskt).
- **Grupperna av stenar med samma hand** kommer från en modell som väger samman text, stavning, stilgrupp, korsform och plats (Kvant 2026). En grind på ena halvan av runologernas uttalanden om samma hand föregick ett slutprov på den andra.

### 4.4 Avvikelser från planerna
- **Källkontrollen:** urvalet drog 140 teckningar, men några stenar kom med under flera typer; jämförelsen gäller {KK['teckningar']} stenar ({PT['bautil']} Bautil, {PT['rhezelius']} Rhezelius, {PT['peringskiold']} Peringskiöld, {PT['ovrig']} övriga).
- **Utsnitten:** pilot 2, med ändrad kodbok och ett tillägg för fält där ett värde dominerar, lades till efter pilot 1:s utfall.
- **Skrift och bild:** planens sekundära mått, ”språkdragen”, mätte i praktiken budskapet, eftersom de kategoriska dragen blev noll som tal; dess värde (ρ = {dec(SPD['rho'])} mot {dec(SPD['omblandning_medel'])}) gäller alltså budskapet. Språkdragen räknades om rätt utanför planen.
- **Budskap och bild:** planen räknade med 456 stenar men tog med fält som inte är godkända; med bara godkända fält blev det {BB['stenar']} stenar och {num(B1['par'])} par. I första urvalet gav de tolv budskapskolumnerna ρ = 0,23 mot 0,07 (p = 0,002) och de fyra språkliga markörerna 0,08 mot 0,05 (p = 0,036); resultatets 0,19 mot 0,08 gäller båda tillsammans.
- **Luckorna:** {KB['teckningar_kodade']} av 141 teckningar fick ett enigt värde.
- **I övrigt** inga avvikelser.

## 5. Resultat

### 5.1 Registret
- **Samstämmigheten** var kappa {kv(F['djurhuvud']['kappa'])} för djurhuvud, {kv(F['huvud_vy']['kappa'])} för huvudets vy, {kv(F['oga']['kappa'])} för ögat och {kv(F['koppel']['kappa'])} för kopplet, och {kv(F['svans']['kappa'])}–{kv(F['lappflik']['kappa'])} för flikar, flätverk, fötter och svans.
- **Täckningen** av huvudets drag var {pc(min(TACK))}–{pc(max(TACK))} procent, för nackfliken {pc(F['nackflik']['tackning'])} och läppfliken {pc(F['lappflik']['tackning'])}.
- **Tre fält ströks:** munnen (täckning {pc(F['mun']['tackning'])} procent), hur huvud och svans möts (kappa {kv(F['huvud_svans']['kappa'])}) och kantlinjerna (ingen variation). {len(KAP)} återstår.
- **Läsarnas stilbedömning** stämde med Rundatas i {STIL_LIKA} av {STIL_N} fall ({pc(STIL_LIKA / STIL_N)} procent) och användes aldrig som belägg.
- **Registret:** {num(M2['stenar_med_kod'])} planschstenar som kan jämföras med en sten inom 30 km på minst tre drag ({N_UTAN_BILD} saknade användbar bild), {KK['gotland_öland_kodade']} från Gotland och Öland, {len(FOTO)} från Hälsingland och Medelpad och {len(FL)} försvunna stenar ur teckningar ({N_LOST3} med minst tre drag; {KALLA['Bautil']} ur Bautil, {KALLA['Peringskiöld']} Peringskiöld, {KALLA['Rhezelius']} Rhezelius, {KALLA['SRI-text']} andra): {num(N_REG)} stenar. {N_LOST_UTAN_STIL} av de försvunna saknar stilgrupp i Rundata.

### 5.2 Källkontrollen: teckningarna
- **Läsarna** var lika eniga på teckningarna som på fotona (kappa {kv(min(LT))}–{kv(max(LT))}).
- **Mot planschfotot** stämde nackfliken med kappa {kv(KT['nackflik'])}, djurhuvudet och kopplet {kv(KT['koppel'])}, huvudets vy {kv(KT['huvud_vy'])}, korset {kv(KT['kors'])}, flätverket {kv(KT['flatverk'])} och antalet djur {kv(KT['antal_djur'])}. Svansen ({kv(KT['svans'])}) och ögat ({kv(KT['oga'])}) klarade regeln.
- **Läppfliken** ({kv(KT['lappflik'])}; {len(LP)} stenar, bara {LP_FLIK} med flik) och **fötterna** ({kv(KT['fotter'])}; {len(FOT)} stenar, {FOT_INGA} utan fötter i båda) läses aldrig ur teckningar. För fötterna betyder kappa 0 att draget nästan aldrig finns, inte att tecknarna ritade fel.
- **Talen är små:** nackfliken stämde på {NP_LIKA} av {len(NP)} stenar, men bara {NP_FLIK} hade en flik. Per typ fanns 5–17 stenar per fält, så det samlade värdet gäller.

{FIG1_SV}

I klartext: två läsare som inte ser varandra ger samma svar om rundjurets huvud, kopplet och flätverket nästan varje gång båda ser dragen, och en teckning från 1600- eller 1700-talet säger i regel samma sak om dem som ett modernt foto – men inte om läppfliken och fötterna.

### 5.3 Djupbilder, utsnitt och luckor
- **Djupbilderna höll inte.** Mot fotot stämde djurhuvudet med kappa {kv(D3['djurhuvud']['kappa'])}, huvudets vy {kv(D3['huvud_vy']['kappa'])}, ögat {kv(D3['oga']['kappa'])} och antalet djur {kv(D3['antal_djur']['kappa'])}; svansen gick inte att läsa, och läsarna var sinsemellan osäkrare (kappa {kv(min(L3))}–{kv(max(L3))}). Bara extra orm nådde 15 jämförbara stenar och får läsas. Beräkningen visar vittring och sprickor lika tydligt som grunda linjer (Figur 2); det gäller beräkningen, inte skanningarna.
- **Utsnitten höll inte.** Nack- och läppflik fick värde på {pc(P1H['täckning']['nackflik'])} och {pc(P1H['täckning']['lappflik'])} procent av stenarna i pilot 1 och {pc(P2H['täckning']['nackflik'])} och {pc(P2H['täckning']['lappflik'])} procent i pilot 2, mot kravet 60. Läsningen av flikar i utsnitt lades ned.
- **Teckningarna fyllde {sum(FILL.values())} luckor**, mest öga ({FILL['oga']}) och nackflik ({FILL['nackflik']}). Andelen stenar med djurhuvud som har nackflik, procent före → efter: {NHEAD}; ögat i Pr4 {pc(CV['Pr4']['oga']['före'])} → {pc(CV['Pr4']['oga']['efter'])}.

{FIG2_SV}

### 5.4 Validering: budskap och bild
- **Provet höll.** På {BB['stenar']} oberoende stenar ({BB['källor']['plansch']} planschstenar utan stilgrupp, {BB['källor']['teckning']} försvunna, {BB['källor']['utvidgning']} från Gotland, Öland, Hälsingland och Medelpad) och {num(B1['par'])} par var ρ = {dec(B1['rho'])} mellan budskap och ornamentik, mot {dec(B1['omblandning_medel'], 3)} vid omblandning; ingen av 999 omblandningar nådde dit (p = {dec(B1['p'], 3)}). Det gällde planschstenar (ρ = {dec(PK['plansch']['rho'])}) och teckningar ({dec(PK['teckning']['rho'])}), båda p = {dec(PK['plansch']['p'], 3)}; i samma stilgrupp fanns bara {SS['par']} par (ρ = {dec(SS['rho'])}, p = {dec(SS['p'])}).
- **Vad som bär det:** utan kategorin ”texten saknar religiösa markörer” faller ρ till {dec(UK['pm_neutral'], 3)}; varje annan kategori utelämnad ger {dec(min(UK_OVR))}–{dec(max(UK_OVR))}. Utforskande: med korset borttaget ur ornamentiken blir ρ = 0,062 (p = 0,007), utan både korset och den kategorin 0,040 (p = 0,14).
- **Tolkningen:** det väntade sambandet mellan tro och kors; läsarna kodade bara bilden, så det validerar registret men är inget nytt fynd.

### 5.5 Skrift och bild
- **Huvudprovet höll inte.** På {SR['stenar']} stenar och {num(P1['par'])} par i samma stilgrupp inom 30 km var ρ = {dec(P1['rho'], 3)} mellan stavning och ornamentik, mot {dec(P1['omblandning_medel'], 3)} vid omblandning (p = {dec(P1['p'])}); utan par från samma socken {dec(SU['rho'], 3)} (p = {dec(SU['p'])}); inom Pr4 ({num(P3['par'])} par) {dec(P3['rho'], 3)} mot {dec(P3['omblandning_medel'], 3)} (p = {dec(P3['p'])}).
- **Gränsen:** 95 procent av omblandningarna låg under {dec(P1['omblandning_95'], 3)}, så en korrelation på omkring 0,05 eller mer utöver bygd och stilgrupp hade synts.
- **Språkdragen**, rätt räknade (utforskande): ρ = 0,017 mot 0,036, p = 0,75. De språkliga markörerna (stungna runor, monoftong, o-runa, r för ʀ): ρ = {dec(SM['rho'], 3)}, p = {dec(SM['p'])}.
- **Ristarna som enheter** kunde inte prövas: bara {P2['ristare']} signerade ristare (Öpir, Balle, Åsmund, Visäte) har minst fem stenar med båda måtten; planen krävde åtta.

### 5.6 Gräslunds stilgrupper
- **Dragen bär stilgruppen.** På {F1['stenar']} stenar ({', '.join(f'{s} {N_STIL[s]}' for s in STYLES)}) satte modellen rätt grupp på {pc(F1['träffsäkerhet'])} procent, mot {pc(F1['vanligaste_gruppen'])} för att alltid gissa Pr4 och {pc(F1['omblandning_medel'])} med omblandade grupper (p = {dec(F1['p'], 3)}). Pr5 känns inte igen alls; alla utom fyra blir Pr4.
- **Pr-grupperna är en ordnad följd.** Av {F2['fel_inom_Pr']} fel inom Pr hamnade {F2['avstånd']['1']} ett steg bort, {F2['avstånd']['2']} två och {F2['avstånd']['3']} tre: {pc(F2['andel_till_granne'])} procent hos grannen, mot {pc(F2['omblandning_medel'])} vid omblandning (p = {dec(F2['p'], 3)}).
- **Dragen själva** bildar tre klasser: inget djurhuvud (191 stenar, mest RAK), ett enkelt djur utan flikar (134, mest Fp och Pr1–Pr3) och profilhuvud med koppel (295, mest Pr4 och Pr3). Justerat Rand-index mot Rundata: {dec(F3['ARI_mot_rundata'])}.
- **Mellan landskap:** tränad på Uppland träffade modellen {pc(F4['inom_uppland_cv'])} procent där men {pc(F4['Sö']['träffsäkerhet'])} i Södermanland.
- **Utforskande:** Fp skiljs mest på huvudets vy (ovanifrån på {FPV['uppifran']} av {sum(FPV.values())}). Nackfliken saknar värde för {pc(min(NACK))}–{pc(max(NACK))} procent av stenarna i Pr2–Pr5 och läppfliken för {pc(min(LAPP))}–{pc(max(LAPP))} procent.

{chart(True)}

### 5.7 Grupperna av stenar med samma hand
- **Grinden höll.** Runologernas stenpar liknade varandra i ornamentiken mer än grannstenar på samma avstånd (median över {pc(M2['G1']['median_percentil'])} procent av grannarna, {M2['G1']['grupper']} grupper, p = {dec(M2['G1']['p'], 3)}).
- **Slutprovet höll inte.** Av {O1['grupper']} grupper i den undanhållna halvan förblev {O1['grupper'] - O1['med_skillnad']} oförändrade, {O1['bättre']} blev bättre och {O1['sämre']} sämre; i genomsnitt {pc(O1['medel_M2'])} mot {pc(O1['medel_M1'])} procent av paren i samma grupp (p = {dec(O1['p'])}). Grupperna slog fortfarande grannstenarna ({pc(O2['medel_samma'])} mot {dec(100 * O2['medel_kontroll'], 1)} procent, p = {pexp(O2['p'])}). Enligt planen behölls grupperna utan ornamentik.

## 6. Diskussion

Bidraget är mätningen: med två oberoende mått på samma sten kan frågor som prövats sten för sten ställas över hela materialet. Mest nytt är källkontrollen, som gör de försvunna stenarna mätbara i rundjurets huvuddrag.

**Vad rapporten inte besvarar.**
1. **Arbetsdelningen.** Att stavningen inte följer ornamentiken kan betyda att text och bild hade olika upphov medan budskap och bild bestämdes tillsammans, kanske av beställaren. Det kan också betyda att båda måtten bär handen så svagt att deras gemensamma del inte syns. Vi hävdar ingetdera. Ett svar kräver minst åtta signerade ristare med båda måtten, ett finare ornamentmått och gärna fysiska belägg, som huggtekniken i runor och ornamentik på samma sten.
2. **Gräslunds finindelning.** Huvudlinjerna syns: band utan djur, huvud ovanifrån och en ordnad följd av profilhuvuden. Om Pr1–Pr5 är fem grupper eller ett kontinuum kan inte prövas utan flikarna. Det kräver bättre bilder (högupplösta foton med fri licens, eller släpljus från flera håll ur 3D-skanningarna under en ny låst källkontroll), ett exempelblad och en tredje läsare, och sedan ett prov mot dateringar som inte bygger på stil. Resultaten prövar och förfinar indelningen; de underkänner den inte.

**Svagheter, i ordning efter vikt:**
1. **Läsarna är samma språkmodell** och kan ha samma blinda fläckar. Källkontrollerna skyddar delvis; ett handkodat kontrollurval saknas.
2. **Planschfotot är inte sanningen.** Det är ofta ifyllt med färg, och samstämmighet kan dölja ett gemensamt fel.
3. **Flikarnas tal är små** i källkontrollen ({len(NP)} och {len(LP)} stenar, {NP_FLIK} och {LP_FLIK} med flik).
4. **Läsarna kan känna igen kända stenar.**
5. **Bortfallet följer bilden,** vars kvalitet kan variera med landskap och tid. {N_PL_LOST} planschstenar är försvunna; {N_PL_TECKN} av de {N_PL_LOST} visas på planschen genom en äldre teckning, och för övriga {N_PL_LOST - N_PL_TECKN} är förlagan inte angiven i vår förteckning.
6. **Rundatas stilgrupp är inte sanningen,** stilprovet väntades hålla, och Uppland dominerar proven.

**Var metoden inte ska användas:** för läppflik och fötter ur teckningar, för huvudets drag ur djupbilder, och för att tillskriva eller datera en enskild sten på koderna ensamma.

**Vad som skulle fälla den:** ett handkodat kontrollurval där de eniga värdena ofta avviker, eller en källkontroll på andra teckningar där huvuddragen inte klarar gränsen.

## 7. Slutsats

Rundjurets huvuddrag kan kodas tillförlitligt över hela materialet, också ur 1600- och 1700-talens teckningar av försvunna stenar. Registret visar att stavningen inte följer bilden utöver bygd och tid, och det bär Gräslunds huvudlinjer. Finindelningen och arbetsdelningen kräver bättre bilder av huvudet och fler signerade stenar.

## Data och kod

- Analysen är gjord på Rundata-korpusen med versionsnyckeln {FP}, i Vitki {APP_VERSION}. Kod och planer: https://github.com/Precatio/runes (CC BY 4.0).
- Planerna i `analysplaner/`: `{PLANS['orn']}`, `{PLANS['kk']}`, `{PLANS['3d']}`, `{PLANS['gr1']}`, `{PLANS['huvud']}`, `{PLANS['luckor']}`, `{PLANS['sr']}`, `{PLANS['bb']}`. Planerna för huvudet i utsnitt och luckorna har ingen kontrollsummefil; de lades in i commit `a87beda` (pilot 2 i `609c89c`) respektive `161dae7`.
- Kodboken: `utdata/nya_ristare/ornamentik/kodbok.md`. Skripten och utfallen i `utdata/nya_ristare/ornamentik/` (kallkontroll.py, kallkontroll_3d.py, djupbild.py, forlorade.py, kombinera.py, m2.py, slutprov3.py) och `utdata/graslund/` (graslund1.py, skrev_ritade.py, budskap_bild.py, huvud/utvardera.py). Resultaten står i `utdata/nya_ristare/resultat.md` §§ 10–14, `utdata/graslund/resultat.md` och `utdata/graslund/skrev_ritade.md`.
- Koderna per sten finns i Vitkis data. Planscherna i Sveriges runinskrifter och texterna ur dess textband ligger inte i repot.
- 3D-skanningarna (Laila Kitzler Åhfeldt, för Hälsingland och Medelpad med Henrik Zedig; Riksantikvarieämbetet; Zenodo; CC BY 4.0): Södermanland doi:{DOIS['sodermanland']}, Västergötland doi:{DOIS['vastergotland']}, gravmonument i Östergötland och Småland doi:{DOIS['gravmonument_og_sm']}, Åsmund doi:{DOIS['asmund']}, Hälsingland doi:{DOIS['halsingland']}, Medelpad doi:{DOIS['medelpad']}. Djupbilden i Figur 2 är beräknad ur filen {SCAN_FILE}, använd som den är publicerad.
- Fotona från Hälsingland och Medelpad: Wikimedia Commons och Riksantikvarieämbetet via K-samsök, med fria licenser; de visas inte här.
- Den populärvetenskapliga artikeln om metoden, ”Så läser vi rundjuren”, är ännu inte publicerad; länken läggs till när den är det.

## Referenser

- Cohen, J. 1960. A coefficient of agreement for nominal scales. *Educational and Psychological Measurement* 20 (1), s. 37–46.
- Göransson, J. 1750. *Bautil*. Stockholm. Umeå universitetsbiblioteks exemplar.
- Gräslund, A.-S. 1991. Runstenar – om ornamentik och datering. *Tor* 23, s. 113–140.
- Gräslund, A.-S. 1992. Runstenar – om ornamentik och datering II. *Tor* 24, s. 177–201.
- Gräslund, A.-S. 2006. Dating the Swedish Viking-Age rune stones on stylistic grounds. I: M. Stoklund m.fl. (red.), *Runes and their Secrets: Studies in Runology*. Köpenhamn: Museum Tusculanum Press, s. 117–139.
- Gräslund, A.-S. 2015. The Late Viking Age Runestones of Västergötland: On Ornamentation and Chronology. *Lund Archaeological Review* 20 (2014), s. 39–53.
- Kitzler Åhfeldt, L. 2002. *Work and Worship: Laser Scanner Analysis of Viking Age Rune Stones*. Theses and Papers in Scientific Archaeology B:9. Stockholm: Stockholms universitet.
- Kitzler Åhfeldt, L. 2017. *Runristare och mobilitet i Södermanland*. Stockholm: Riksantikvarieämbetet.
- Kitzler Åhfeldt, L. 2024. *3D-data Runstenar i Södermanland* [Dataset]. Riksantikvarieämbetet. https://doi.org/{DOIS['sodermanland']}
- Kvant, V. 2026. Runstenar med samma hand, också utan namn. Metodrapport, rapportversion 1, 2026-11-24 (opublicerad).
- Källström, M. 2007. *Mästare och minnesmärken. Studier kring vikingatida runristare och skriftmiljöer i Norden*. Stockholm Studies in Scandinavian Philology, New Series 43. Stockholm: Stockholms universitet.
- Lager, L. 2002. *Den synliga tron. Runstenskors som en spegling av kristnandet i Sverige*. Occasional Papers in Archaeology 31. Uppsala: Uppsala universitet.
- Riksantikvarieämbetet. *Sveriges runinskrifter*. Planscher och textband, lästa men inte återgivna.
- Samnordisk runtextdatabas (Rundata) 3.1. Institutionen för nordiska språk, Uppsala universitet.
- Stern, M. 2013. *Runestone Images and Visual Communication in Viking Age Scandinavia*. Diss. University of Nottingham.

:::box Det viktigaste i korthet
- Rundjuret går att mäta: med en fast kodbok, två oberoende läsare och en regel för vilka drag som håller blir ornamentiken ett mått över hela materialet, skilt från texten.
- De gamla teckningarna är pålitligare än man kunde vänta för djurets huvuddrag, och därför kan stenar som bara finns på papper räknas med. För läppfliken och fötterna duger de inte.
- Hur texten är stavad och hur djuret är ritat delar nästan inget utöver bygd och tid. Om det betyder att olika händer skrev och ritade kan mätningen ännu inte säga.
- Gräslunds huvudlinjer syns i koderna. Hennes finindelning väntar på bättre bilder av huvudets detaljer.
:::
"""

body_en = f"""*Viktor Kvant, independent researcher. Methods report, partially tested. Report version {REPORT_VERSION}, {TODAY}. Timeline: {TL_EN}. The analysis was made in Vitki {APP_VERSION}. Licence CC BY 4.0. This English version is the canonical one for citation: {CITE_EN}. Keywords: runestones, Viking Age, ornament, rune-animal style, Gräslund's style groups, source criticism, antiquarian drawings, Bautil, inter-rater agreement, Cohen's kappa, preregistration. Competing interests: none. Funding: none.*

## Abstract

**What has not been tested.** The instrument was tested in locked source checks with limits set in advance, but not in a blind test with the answer hidden from the whole chain: the photograph the drawings were measured against is itself a rendering, the readers are the same language model and no person has coded a control sample. Two routes to the head's details failed (depth images from 3D scans and enlarged crops), and the ornament did not improve the groups of stones by the same hand in a locked final test.
**Background and aim.** The rune animal's features are the basis of Anne-Sofie Gräslund's style groups and of much of the dating of the runestones, but they have been described in words, stone by stone. The aim was to measure the ornament across the whole material, independently of the text, and to test the pictures the measure is read from.
**Material.** The plate photographs in Sveriges runinskrifter ({num(N_PLANSCH, True)} of {num(N_KORPUS, True)} Swedish Viking Age runestones in Rundata), free photographs, drawings of the 1600s and 1700s and open 3D scans.
**Method.** Two independent readers answered a codebook of 17 questions about the rune animal. A feature got a value only when both answered alike, and a field was used only with Cohen's kappa ≥ 0.40 and coverage ≥ 30 percent. Every new kind of picture was tested against the photographs, and the codes were set in locked tests against the text, the style groups and groups of stones by the same hand.
**Results.** The readers agreed with kappa {kv(min(KAP.values()), True)}–{kv(max(KAP.values()), True)} on {len(KAP)} fields; the register covers {num(N_REG, True)} stones, of which {len(FL)} are lost. On {KK['teckningar']} surviving stones the drawings agreed with the photographs on the head, the neck lappet and the koppel (kappa {kv(KT['huvud_vy'], True)}–{kv(KT['nackflik'], True)}), but not demonstrably on lip lappet and feet, and the depth images did not agree on the head. Faith and cross go together in the codes on {BB['stenar']} independent stones. Spelling does not follow the ornament beyond district and style group (Spearman's ρ = {dec(P1['rho'], 3, True)} against {dec(P1['omblandning_medel'], 3, True)} under shuffling, p = {dec(P1['p'], 2, True)}).
**Conclusion.** The rune animal's main features can be measured reliably, also on lost stones, but not the head's details, on which Gräslund's fine division rests. Whether the weak coupling of writing and image reflects a division of labour or weak traces of the hand cannot be decided.

## 1. Introduction

Anne-Sofie Gräslund (1991, 1992, 2006) ordered the rune animals on the late Viking Age runestones into style groups: RAK, where the ends of the rune band are straight without an animal head; Fp, where the head is seen from above; and Pr1–Pr5, profile heads in five steps. The groups rest on single features – the head's view, the eye, lappets at neck and lips, the tail, the feet, the koppel that binds the animals together – and are used to date the stones (Gräslund 2006, 2015). The images, the crosses and the carvers have been studied by Stern (2013), Lager (2002), Källström (2007) and Kitzler Åhfeldt (2002, 2017), among others.

The features, however, have not been measured across the whole material; Rundata has the style group but not the features. Many stones survive only in drawings: Bautil's woodcuts, cut in the 1600s and printed in 1750, Johannes Rhezelius's drawings from the 1630s and Johan Peringskiöld's from around 1700. The editors of Sveriges runinskrifter judged them stone by stone. As far as we know, they have not been tested feature by feature against photographs across a larger material.

The contribution here is the measurement: a register in which the ornament is coded independently of the text, so that how the text is written and how the animal is drawn can be set against each other. Four tests show what the register carries: an expected link between text and image, the spelling, Gräslund's style groups and groups of stones by the same hand.

## 2. Preregistration

The work followed eight plans, committed to the project's version control before what they concerned was computed, the first on 2026-11-24 and the others on 2026-11-25 (SHA-256 is the file's checksum):
- **The ornament and the groups of stones by the same hand** ({S['orn']}): codebook version 2 (`97cf9214…`), the rule for the fields, a gate and a final test that holds, verbatim, "if p < 0.05 and the mean difference > 0".
- **The source check of the drawings** ({S['kk']}), locked before any drawing was coded. A field may be read "when kappa against the plate is ≥ 0.40 and at least 15 stones can be compared".
- **The style groups** ({S['gr1']}): do the features carry the style group, and are the Pr groups an ordered sequence? The plan says the first is expected to hold and that "the interesting thing is the pattern in the errors".
- **The depth images and Hälsingland and Medelpad** ({S['3d']}): the same rule as for the drawings.
- **The head in enlarged crops** ({S['huvud']}; pilot 2 written in before it was run, {S['huvud2']}): neck and lip lappet must get a value on at least 60 percent of the stones.
- **Writing and drawing** ({S['sr']}): "P1 holds if the correlation is greater than 0 and one-sided p < 0.05".
- **The drawings fill gaps** ({S['luckor']}): descriptive.
- **Message and image** ({S['bb']}), a confirmatory test on independent stones: "B1 holds if ρ > 0 and one-sided p < 0.05".

The link between message and image had been seen in a first sample; that is why it was tested on other stones. The plans for the crops and the gaps concern instrument and procedure; they were committed to version control before running but not locked with a checksum (the sums above are computed on the commit that added them). What is called exploratory below was in no plan.

## 3. Material

- **The stones:** Scandinavian Runic-text Database (Rundata) 3.1, frozen for the analysis: {num(N_KORPUS, True)} Swedish Viking Age runestones with coordinates and Rundata's style groups.
- **The pictures:** the plate photographs in Sveriges runinskrifter ({num(N_PLANSCH, True)} stones; protected by copyright, read but not shown), the plates of Gotland and Öland, free photographs of the painted stones in Hälsingland and Medelpad, Bautil in the Umeå University Library copy, other drawings as Sveriges runinskrifter reproduces them, and Laila Kitzler Åhfeldt's and Henrik Zedig's open 3D scans (CC BY 4.0).
- **The text:** the spelling, categorical language traits and twelve categories for what the text says, coded per stone from Rundata.

## 4. Method

### 4.1 The codebook and the readers
- **The codebook** has 17 questions about the rune animal (animal head, number of animals, the head's view, eye, neck and lip lappet, mouth, tail, feet, koppel, interlace, cross and more), always with the answer "uncertain". Head, tail and band ends must be enlarged before they are coded. Two pilots (12 and 20 stones outside the test material) preceded the lock.
- **The readers** were two separate runs of Anthropic's language model Claude (Claude Opus). They saw only the picture and the signum, five stones at a time in opposite order, and were asked not to use knowledge of the stone or the literature.
- **The value** is what both give; otherwise it is missing.
- **Cohen's kappa** (Cohen 1960) is the share of equal answers with the contribution of chance removed: 1 is full agreement, 0 no better than chance. **The coverage** is the share of stones where both gave a value.

### 4.2 The source checks
- **The principle:** a new kind of picture is tested against the plate photograph on surviving stones present in both, with new readers. The measure is whether two renderings of the same stone say the same thing.
- **The drawings:** at random 40 from Bautil, 40 by Rhezelius, 30 by Peringskiöld and 30 by other draughtsmen.
- **The depth images:** the surface minus the same surface smoothed over 12 mm, so that carved lines turn dark, on {K3['källkontroll_stenar']} scanned stones.
- **The head in crops:** two pilots on 30 stones where the neck lappet lacked a value: cut-out heads, two readers and a third on disagreement, in pilot 2 with a schematic profile head and crops enlarged to at least 1,000 pixels.
- **Gaps and lost stones:** drawings were coded for 141 surviving stones lacking a neck lappet and for {len(FB)} lost stones, only in approved fields and labelled with the draughtsman. A plate value was never replaced.

### 4.3 The tests
- **The similarities** between two stones: in the ornament the share of equal values among at least three shared fields; in the spelling the spelling features weighted by how rare they are; in the message twelve categories (such as memorial, bridge and road, journey, inheritance, and the text lacking religious markers).
- **The tests** measure Spearman's ρ between two similarities over stone pairs within 30 km, against 999 shuffles of the ornament codes within hundred and style group (writing) or hundred and picture source (message), so that the district and, as far as the style group reaches, the time are held constant.
- **The style groups:** multinomial logistic regression, cross-validated with parishes as units; the errors within Pr are counted by distance in the sequence. A latent class model looks for groups without seeing the style groups, compared with Rundata by the adjusted Rand index (0 as chance, 1 identical).
- **The groups of stones by the same hand** come from a model that weighs together text, spelling, style group, cross form and place (Kvant 2026). A gate on one half of the runologists' statements about the same hand preceded a final test on the other.

### 4.4 Deviations from the plans
- **The source check:** the sample drew 140 drawings, but some stones came in under several types; the comparison covers {KK['teckningar']} stones ({PT['bautil']} Bautil, {PT['rhezelius']} Rhezelius, {PT['peringskiold']} Peringskiöld, {PT['ovrig']} others).
- **The crops:** pilot 2, with a changed codebook and an addition for fields where one value dominates, was added after pilot 1's outcome.
- **Writing and drawing:** the plan's secondary measure, "the language traits", in practice measured the message, since the categorical traits became zero as numbers; its value (ρ = {dec(SPD['rho'], 2, True)} against {dec(SPD['omblandning_medel'], 2, True)}) thus concerns the message. The language traits were recomputed correctly outside the plan.
- **Message and image:** the plan counted on 456 stones but included fields that are not approved; with approved fields only there were {BB['stenar']} stones and {num(B1['par'], True)} pairs. In the first sample the twelve message columns gave ρ = 0.23 against 0.07 (p = 0.002) and the four linguistic markers 0.08 against 0.05 (p = 0.036); the result's 0.19 against 0.08 concerns both together.
- **The gaps:** {KB['teckningar_kodade']} of 141 drawings got an agreed value.
- **Otherwise** no deviations.

## 5. Results

### 5.1 The register
- **The agreement** was kappa {kv(F['djurhuvud']['kappa'], True)} for animal head, {kv(F['huvud_vy']['kappa'], True)} for the head's view, {kv(F['oga']['kappa'], True)} for the eye and {kv(F['koppel']['kappa'], True)} for the koppel, and {kv(F['svans']['kappa'], True)}–{kv(F['lappflik']['kappa'], True)} for lappets, interlace, feet and tail.
- **The coverage** of the head's features was {pc(min(TACK))}–{pc(max(TACK))} percent, for the neck lappet {pc(F['nackflik']['tackning'])} and the lip lappet {pc(F['lappflik']['tackning'])}.
- **Three fields were struck:** the mouth (coverage {pc(F['mun']['tackning'])} percent), how head and tail meet (kappa {kv(F['huvud_svans']['kappa'], True)}) and the outlines (no variation). {len(KAP)} remain.
- **The readers' style judgement** agreed with Rundata's in {STIL_LIKA} of {STIL_N} cases ({pc(STIL_LIKA / STIL_N)} percent) and was never used as evidence.
- **The register:** {num(M2['stenar_med_kod'], True)} plate stones that can be compared with a stone within 30 km on at least three features ({N_UTAN_BILD} lacked a usable picture), {KK['gotland_öland_kodade']} from Gotland and Öland, {len(FOTO)} from Hälsingland and Medelpad and {len(FL)} lost stones from drawings ({N_LOST3} with at least three features; {KALLA['Bautil']} from Bautil, {KALLA['Peringskiöld']} Peringskiöld, {KALLA['Rhezelius']} Rhezelius, {KALLA['SRI-text']} others): {num(N_REG, True)} stones. {N_LOST_UTAN_STIL} of the lost stones lack a style group in Rundata.

### 5.2 The source check: the drawings
- **The readers** agreed as well on the drawings as on the photographs (kappa {kv(min(LT), True)}–{kv(max(LT), True)}).
- **Against the plate photograph** the neck lappet agreed with kappa {kv(KT['nackflik'], True)}, the animal head and the koppel {kv(KT['koppel'], True)}, the head's view {kv(KT['huvud_vy'], True)}, the cross {kv(KT['kors'], True)}, the interlace {kv(KT['flatverk'], True)} and the number of animals {kv(KT['antal_djur'], True)}. The tail ({kv(KT['svans'], True)}) and the eye ({kv(KT['oga'], True)}) passed the rule.
- **The lip lappet** ({kv(KT['lappflik'], True)}; {len(LP)} stones, only {LP_FLIK} with a lappet) and **the feet** ({kv(KT['fotter'], True)}; {len(FOT)} stones, {FOT_INGA} without feet in both) are never read from drawings. For the feet, kappa 0 means the feature hardly ever occurs, not that the draughtsmen drew wrongly.
- **The numbers are small:** the neck lappet agreed on {NP_LIKA} of {len(NP)} stones, but only {NP_FLIK} had a lappet. Per type there were 5–17 stones per field, so the pooled value applies.

{FIG1_EN}

In plain words: two readers who do not see each other give the same answer about the rune animal's head, the koppel and the interlace almost every time both see the features, and a drawing from the 1600s or 1700s as a rule says the same about them as a modern photograph – but not about the lip lappet and the feet.

### 5.3 Depth images, crops and gaps
- **The depth images did not hold.** Against the photograph the animal head agreed with kappa {kv(D3['djurhuvud']['kappa'], True)}, the head's view {kv(D3['huvud_vy']['kappa'], True)}, the eye {kv(D3['oga']['kappa'], True)} and the number of animals {kv(D3['antal_djur']['kappa'], True)}; the tail could not be read, and the readers were less sure among themselves (kappa {kv(min(L3), True)}–{kv(max(L3), True)}). Only the extra serpent reached 15 comparable stones and may be read. The computation shows weathering and cracks as clearly as shallow lines (Figure 2); this applies to the computation, not to the scans.
- **The crops did not hold.** Neck and lip lappet got a value on {pc(P1H['täckning']['nackflik'])} and {pc(P1H['täckning']['lappflik'])} percent of the stones in pilot 1 and {pc(P2H['täckning']['nackflik'])} and {pc(P2H['täckning']['lappflik'])} percent in pilot 2, against the requirement of 60. Reading lappets in crops was abandoned.
- **The drawings filled {sum(FILL.values())} gaps**, mostly eye ({FILL['oga']}) and neck lappet ({FILL['nackflik']}). The share of stones with an animal head that have a neck lappet, percent before → after: {NHEAD}; the eye in Pr4 {pc(CV['Pr4']['oga']['före'])} → {pc(CV['Pr4']['oga']['efter'])}.

{FIG2_EN}

### 5.4 Validation: message and image
- **The test held.** On {BB['stenar']} independent stones ({BB['källor']['plansch']} plate stones without a style group, {BB['källor']['teckning']} lost, {BB['källor']['utvidgning']} from Gotland, Öland, Hälsingland and Medelpad) and {num(B1['par'], True)} pairs, ρ = {dec(B1['rho'], 2, True)} between message and ornament, against {dec(B1['omblandning_medel'], 3, True)} under shuffling; none of 999 shuffles reached it (p = {dec(B1['p'], 3, True)}). It held for plate stones (ρ = {dec(PK['plansch']['rho'], 2, True)}) and drawings ({dec(PK['teckning']['rho'], 2, True)}), both p = {dec(PK['plansch']['p'], 3, True)}; within the same style group there were only {SS['par']} pairs (ρ = {dec(SS['rho'], 2, True)}, p = {dec(SS['p'], 2, True)}).
- **What carries it:** without the category "the text lacks religious markers", ρ falls to {dec(UK['pm_neutral'], 3, True)}; every other category left out gives {dec(min(UK_OVR), 2, True)}–{dec(max(UK_OVR), 2, True)}. Exploratory: with the cross removed from the ornament, ρ = 0.062 (p = 0.007), without both the cross and that category 0.040 (p = 0.14).
- **The reading:** the expected link between faith and cross; the readers coded only the picture, so it validates the register but is not a new finding.

### 5.5 Writing and drawing
- **The main test did not hold.** On {SR['stenar']} stones and {num(P1['par'], True)} pairs in the same style group within 30 km, ρ = {dec(P1['rho'], 3, True)} between spelling and ornament, against {dec(P1['omblandning_medel'], 3, True)} under shuffling (p = {dec(P1['p'], 2, True)}); without pairs from the same parish {dec(SU['rho'], 3, True)} (p = {dec(SU['p'], 2, True)}); within Pr4 ({num(P3['par'], True)} pairs) {dec(P3['rho'], 3, True)} against {dec(P3['omblandning_medel'], 3, True)} (p = {dec(P3['p'], 2, True)}).
- **The bound:** 95 percent of the shuffles lay below {dec(P1['omblandning_95'], 3, True)}, so a correlation of about 0.05 or more beyond district and style group would have shown.
- **The language traits**, correctly computed (exploratory): ρ = 0.017 against 0.036, p = 0.75. The linguistic markers (dotted runes, monophthong, o-rune, r for ʀ): ρ = {dec(SM['rho'], 3, True)}, p = {dec(SM['p'], 2, True)}.
- **The carvers as units** could not be tested: only {P2['ristare']} signing carvers (Öpir, Balle, Åsmund, Visäte) have at least five stones with both measures; the plan required eight.

### 5.6 Gräslund's style groups
- **The features carry the style group.** On {F1['stenar']} stones ({', '.join(f'{s} {N_STIL[s]}' for s in STYLES)}) the model put {pc(F1['träffsäkerhet'])} percent in the right group, against {pc(F1['vanligaste_gruppen'])} for always guessing Pr4 and {pc(F1['omblandning_medel'])} with shuffled groups (p = {dec(F1['p'], 3, True)}). Pr5 is not recognised at all; all but four become Pr4.
- **The Pr groups are an ordered sequence.** Of {F2['fel_inom_Pr']} errors within Pr, {F2['avstånd']['1']} landed one step away, {F2['avstånd']['2']} two and {F2['avstånd']['3']} three: {pc(F2['andel_till_granne'])} percent with the neighbour, against {pc(F2['omblandning_medel'])} under shuffling (p = {dec(F2['p'], 3, True)}).
- **The features themselves** form three classes: no animal head (191 stones, mostly RAK), a simple animal without lappets (134, mostly Fp and Pr1–Pr3) and a profile head with a koppel (295, mostly Pr4 and Pr3). Adjusted Rand index against Rundata: {dec(F3['ARI_mot_rundata'], 2, True)}.
- **Between provinces:** trained on Uppland the model hit {pc(F4['inom_uppland_cv'])} percent there but {pc(F4['Sö']['träffsäkerhet'])} in Södermanland.
- **Exploratory:** Fp is told apart mostly by the head's view (from above on {FPV['uppifran']} of {sum(FPV.values())}). The neck lappet lacks a value for {pc(min(NACK))}–{pc(max(NACK))} percent of the stones in Pr2–Pr5 and the lip lappet for {pc(min(LAPP))}–{pc(max(LAPP))} percent.

{chart(False)}

### 5.7 The groups of stones by the same hand
- **The gate held.** The runologists' stone pairs were more alike in the ornament than neighbouring stones at the same distance (median above {pc(M2['G1']['median_percentil'])} percent of the neighbours, {M2['G1']['grupper']} groups, p = {dec(M2['G1']['p'], 3, True)}).
- **The final test did not hold.** Of {O1['grupper']} groups in the held-back half, {O1['grupper'] - O1['med_skillnad']} stayed unchanged, {O1['bättre']} got better and {O1['sämre']} worse; on average {pc(O1['medel_M2'])} against {pc(O1['medel_M1'])} percent of the pairs in the same group (p = {dec(O1['p'], 2, True)}). The groups still beat the neighbouring stones ({pc(O2['medel_samma'])} against {dec(100 * O2['medel_kontroll'], 1, True)} percent, p = {pexp(O2['p'], True)}). As the plan said, the groups without ornament were kept.

## 6. Discussion

The contribution is the measurement: with two independent measures of the same stone, questions that were tried stone by stone can be asked across the whole material. The newest part is the source check, which makes the lost stones measurable in the rune animal's main features.

**What the report does not answer.**
1. **The division of labour.** That spelling does not follow the ornament may mean that text and image had different makers while message and image were decided together, perhaps by the commissioner. It may also mean that both measures carry the hand so weakly that their shared part does not show. We claim neither. An answer needs at least eight signing carvers with both measures, a finer ornament measure and preferably physical evidence, such as the carving technique in runes and ornament on the same stone.
2. **Gräslund's fine division.** The main lines show: bands without animals, heads from above and an ordered sequence of profile heads. Whether Pr1–Pr5 are five groups or a continuum cannot be tested without the lappets. That needs better pictures (high-resolution photographs under a free licence, or raking light from several directions computed from the 3D scans under a new locked source check), an example sheet and a third reader, and then a test against dates that do not rest on style. The results test and refine the division; they do not reject it.

**Weaknesses, in order of importance:**
1. **The readers are the same language model** and may share blind spots. The source checks guard in part; a hand-coded control sample is missing.
2. **The plate photograph is not the truth.** It is often painted in, and agreement can hide a shared error.
3. **The lappets' numbers are small** in the source check ({len(NP)} and {len(LP)} stones, {NP_FLIK} and {LP_FLIK} with a lappet).
4. **The readers may recognise well-known stones.**
5. **The missing values follow the picture,** whose quality may vary with province and time. {N_PL_LOST} plate stones are lost; {N_PL_TECKN} of the {N_PL_LOST} are shown on the plate through an older drawing, and for the other {N_PL_LOST - N_PL_TECKN} the source is not given in our index.
6. **Rundata's style group is not the truth,** the style test was expected to hold, and Uppland dominates the tests.

**Where the method should not be used:** for lip lappet and feet from drawings, for the head's features from depth images, and for attributing or dating a single stone on the codes alone.

**What would refute it:** a hand-coded control sample where the agreed values often deviate, or a source check on other drawings where the main features do not pass the limit.

## 7. Conclusion

The rune animal's main features can be coded reliably across the whole material, also from the drawings of lost stones made in the 1600s and 1700s. The register shows that spelling does not follow the image beyond district and time, and it carries Gräslund's main lines. The fine division and the division of labour need better pictures of the head and more signed stones.

## Data and code

- The analysis was made on the Rundata corpus with the version key {FP}, in Vitki {APP_VERSION}. Code and plans: https://github.com/Precatio/runes (CC BY 4.0).
- The plans in `analysplaner/`: `{PLANS['orn']}`, `{PLANS['kk']}`, `{PLANS['3d']}`, `{PLANS['gr1']}`, `{PLANS['huvud']}`, `{PLANS['luckor']}`, `{PLANS['sr']}`, `{PLANS['bb']}`. The plans for the head in crops and for the gaps have no checksum file; they were added in commit `a87beda` (pilot 2 in `609c89c`) and `161dae7` respectively.
- The codebook: `utdata/nya_ristare/ornamentik/kodbok.md`. The scripts and outcomes in `utdata/nya_ristare/ornamentik/` (kallkontroll.py, kallkontroll_3d.py, djupbild.py, forlorade.py, kombinera.py, m2.py, slutprov3.py) and `utdata/graslund/` (graslund1.py, skrev_ritade.py, budskap_bild.py, huvud/utvardera.py). The results are in `utdata/nya_ristare/resultat.md` §§ 10–14, `utdata/graslund/resultat.md` and `utdata/graslund/skrev_ritade.md`.
- The codes per stone are in Vitki's data. The plates of Sveriges runinskrifter and the texts of its text volumes are not in the repository.
- The 3D scans (Laila Kitzler Åhfeldt, for Hälsingland and Medelpad with Henrik Zedig; Swedish National Heritage Board; Zenodo; CC BY 4.0): Södermanland doi:{DOIS['sodermanland']}, Västergötland doi:{DOIS['vastergotland']}, grave monuments in Östergötland and Småland doi:{DOIS['gravmonument_og_sm']}, Åsmund doi:{DOIS['asmund']}, Hälsingland doi:{DOIS['halsingland']}, Medelpad doi:{DOIS['medelpad']}. The depth image in Figure 2 is computed from the file {SCAN_FILE}, used as published.
- The photographs from Hälsingland and Medelpad: Wikimedia Commons and the Swedish National Heritage Board via K-samsök, under free licences; they are not shown here.
- The popular article on the method, "How we read the rune animals", is not yet published; the link will be added when it is.

## References

- Cohen, J. 1960. A coefficient of agreement for nominal scales. *Educational and Psychological Measurement* 20 (1), pp. 37–46.
- Göransson, J. 1750. *Bautil*. Stockholm. Umeå University Library copy.
- Gräslund, A.-S. 1991. Runstenar – om ornamentik och datering [Runestones – on ornament and dating]. *Tor* 23, pp. 113–140.
- Gräslund, A.-S. 1992. Runstenar – om ornamentik och datering II [Runestones – on ornament and dating II]. *Tor* 24, pp. 177–201.
- Gräslund, A.-S. 2006. Dating the Swedish Viking-Age rune stones on stylistic grounds. In: M. Stoklund et al. (eds), *Runes and their Secrets: Studies in Runology*. Copenhagen: Museum Tusculanum Press, pp. 117–139.
- Gräslund, A.-S. 2015. The Late Viking Age Runestones of Västergötland: On Ornamentation and Chronology. *Lund Archaeological Review* 20 (2014), pp. 39–53.
- Kitzler Åhfeldt, L. 2002. *Work and Worship: Laser Scanner Analysis of Viking Age Rune Stones*. Theses and Papers in Scientific Archaeology B:9. Stockholm: Stockholm University.
- Kitzler Åhfeldt, L. 2017. *Runristare och mobilitet i Södermanland* [Rune carvers and mobility in Södermanland]. Stockholm: Swedish National Heritage Board.
- Kitzler Åhfeldt, L. 2024. *3D-data Runstenar i Södermanland / Runestones in Södermanland* [Dataset]. Swedish National Heritage Board. https://doi.org/{DOIS['sodermanland']}
- Kvant, V. 2026. Runestones by the same hand, also without a name. Methods report, report version 1, 2026-11-24 (unpublished).
- Källström, M. 2007. *Mästare och minnesmärken. Studier kring vikingatida runristare och skriftmiljöer i Norden* [Masters and memorials]. Stockholm Studies in Scandinavian Philology, New Series 43. Stockholm: Stockholm University.
- Lager, L. 2002. *Den synliga tron. Runstenskors som en spegling av kristnandet i Sverige* [The visible faith]. Occasional Papers in Archaeology 31. Uppsala: Uppsala University.
- Scandinavian Runic-text Database (Rundata) 3.1. Department of Scandinavian Languages, Uppsala University.
- Stern, M. 2013. *Runestone Images and Visual Communication in Viking Age Scandinavia*. PhD thesis, University of Nottingham.
- Swedish National Heritage Board (Riksantikvarieämbetet). *Sveriges runinskrifter*. Plates and text volumes, read but not reproduced.

:::box The essentials
- The rune animal can be measured: with a fixed codebook, two independent readers and a rule for which features hold, the ornament becomes a measure across the whole material, separate from the text.
- The old drawings are more reliable than one might expect for the animal's main features, so stones that survive only on paper can be counted. For the lip lappet and the feet they will not do.
- How the text is spelled and how the animal is drawn share almost nothing beyond district and time. Whether that means different hands wrote and drew, the measurement cannot yet say.
- Gräslund's main lines show in the codes. Her fine division awaits better pictures of the head's details.
:::
"""

# ---- kontroller (mallen och husreglerna) ------------------------------------------------------------------------------------
assert "I klartext" in body and "In plain words" in body_en
assert f"{FIG1_SV}\n\nI klartext: två läsare" in body and f"{FIG1_EN}\n\nIn plain words: two readers" in body_en  # efter Figur 1 i 5.2
JARGON = r"modul\w*|trapp\w*|q_global|korpusjobb|fingeravtryck|fingerprint|facit|Vitkis|Vitki's|\bthe app\b|\bappen\b|`[^`]*/[^`]*`|METHODS|\bAI\b"
PRONOUN = re.compile(r"\b(han|hon|hans|honom|he|she|his|him|hennes|her)\b", re.I)
for b, lang in ((body, "sv"), (body_en, "en")):
    assert not re.search(r"^\s*\|", b, re.M), "BlogBody har inga tabeller"
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M)), "varje ruta ska stängas"
    assert "{" not in b and "}" not in b
    head = b.split("## Data")[0]
    assert not re.findall(JARGON, head), (lang, re.findall(JARGON, head))
    assert FP not in head and "](/" not in b.replace("](/api/blog/figures/", "")
    assert not re.search(r"\bAI\b", b)
    # inga könade pronomen om ristare; bara Gräslunds indelning ("Hennes finindelning", "Her fine division") i korthetsrutan
    hits = [m.group(0) for m in PRONOUN.finditer(b)]
    assert hits == (["Hennes"] if lang == "sv" else ["Her"]), (lang, hits)
    assert b.count("Claude") == 2, (lang, b.count("Claude"))  # bara i 4.1
    box = b[b.index(":::box"):]
    assert "Claude" not in box and "insikt" not in box.lower() and "nyhet" not in box.lower()
    lines = b.splitlines()
    caps = [lines[i + 1] for i, ln in enumerate(lines) if ln.startswith("![")]
    assert len(caps) == 2 and all(c.startswith("Figur " if lang == "sv" else "Figure ") and "Umeå" in c for c in caps)
    assert "Kitzler Åhfeldt" in caps[1] and "CC BY 4.0" in caps[1] and DOIS["sodermanland"] in caps[1]
    assert ("Djupbild beräknad i Vitki" if lang == "sv" else "Depth image computed in Vitki") in caps[1]
    assert "Diagram: Vitki" in b or "Chart: Vitki" in b
    assert not re.search(r"öppen datamängd|open dataset|publicerade som datamängd|published as a dataset", b, re.I)
    assert "SYNTES" not in b and "frågelista" not in b.lower() and "påståenden" not in b.lower()
assert body.split("\n", 1)[0].startswith(f"*Viktor Kvant, oberoende forskare. Metodrapport, delvis prövad. Rapportversion 1, {TODAY}. Tidslinje: ")
assert body_en.split("\n", 1)[0].startswith(f"*Viktor Kvant, independent researcher. Methods report, partially tested. Report version 1, {TODAY}. Timeline: ")
assert "## Sammanfattning\n\n**Vad som inte är prövat.**" in body and "## Abstract\n\n**What has not been tested.**" in body_en
SEC = lambda b: [re.match(r"[\d.]*", h).group(0) for h in re.findall(r"^##+ (.+)$", b, re.M)]  # noqa: E731
assert SEC(body) == SEC(body_en), (SEC(body), SEC(body_en))
assert len(re.findall(r"^\s*- ", body, re.M)) == len(re.findall(r"^\s*- ", body_en, re.M))
assert len(re.findall(r"^\s*\d+\. ", body, re.M)) == len(re.findall(r"^\s*\d+\. ", body_en, re.M))
assert "Det viktigaste i korthet" in body and body.index(":::box") > body.index("## Referenser")
for b_, rh in ((body, "## Referenser"), (body_en, "## References")):
    head_, refs_ = b_.split(rh)[0], b_.split(rh)[1].split(":::box")[0]
    for m in re.finditer(r"^- ([^,.]+?)(?:,| \(| [A-Z]\.)[^\n]*?(\d{4})\.", refs_, re.M):
        name, yr = m.group(1).split(",")[0].split()[0], m.group(2)
        if name in ("Samnordisk", "Scandinavian", "Riksantikvarieämbetet.", "Swedish", "Riksantikvarieämbetet"):
            continue
        assert re.search(re.escape(name) + r"[^\n]{0,80}?" + yr, head_), (rh, name, yr)
# mallens längd gäller löptexten: utan huvudraden och diagrammet, fram till Data och kod
prose = re.sub(r":::chart.*?\n:::", "", body.split("## Data")[0].split("\n", 1)[1], flags=re.S)
words = len(prose.split())
prose_en = re.sub(r":::chart.*?\n:::", "", body_en.split("## Data")[0].split("\n", 1)[1], flags=re.S)
words_en = len(prose_en.split())
assert 1500 <= words <= 3000, words

out = {"slug": SLUG, "title": title, "summary": summary, "body": body, "title_en": title_en, "summary_en": summary_en,
       "body_en": body_en, "labels": ["Rapport", "Datering och stil", "Ristare", "Huggspår och 3D", "Språk och stavning"]}
assert blog_labels.check(out["labels"]) is None
path = os.path.join(ROOT, "utdata", "rapporter", "rapport_ornamentik.json")
json.dump(out, open(path, "w"), ensure_ascii=False, indent=1)
print(path, len(body.split()), "ord,", words, "före Data och kod;", len(body_en.split()), "words,", words_en, "before Data and code")

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
        assert not [p_ for p_ in blog._all() if p_.get("slug") == out["slug"]], "Adressen används redan; skriv över med --update"
        ref = col.document()
        ref.set({**out, "published": False, "month": now.strftime("%Y-%m"), "author": "Viktor Kvant",
                 "topic": "Rapport|ornamentik", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
