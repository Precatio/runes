"""Metodikartikeln "Så läser vi rundjuren" (sv + en): hur Vitki kodar rundjurets ornamentik ur bilder, mäter
tillförlitligheten (två oberoende läsare, konsensus, kappa), prövar källorna mot varandra (planschfoto, 1600–1700-tals-
teckning, djupbild ur 3D-skanning) och låser planer med grind och slutprov – med resultaten som prov på metoden.

Bygger på utdata/nya_ristare/resultat.md §§ 10–13 och utdata/graslund/resultat.md (Gräslund 1). Låsta planer:
analysplaner/2026-11-24-nya-ristare-ornamentik.md, 2026-11-25-ornamentik-kallkontroll-teckningar.md,
2026-11-25-graslund-1-stilgrupper.md och 2026-11-25-ornamentik-3d-halsingland-medelpad.md. Varje tal räknas här ur
utfallsfilerna (och cachens koder) och låses med assert.

Figurer (ritas här, sv + en, i utdata/blogg/figurer/ornamentik/): läsningen av Bautils träsnitt av U 1154 (utsnitt, de två
läsarnas koder, konsensus och planschfotots konsensus som text) och Sö 112 i Bautil bredvid djupbilden ur Kitzler Åhfeldts
skanning (CC BY 4.0). Bautil: Umeå universitetsbiblioteks exemplar, "fritt från kända upphovsrättsliga restriktioner".
SRI:s planscher är skyddade och visas aldrig.
    ../../../.venv/bin/python build_ornamentik.py [--write | --update DOC]"""
import csv
import datetime as dt
import json
import os
import re
import sys
from collections import Counter, defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_figures, blog_labels  # noqa: E402
from utdata.nya_ristare.ornamentik.m2 import consensus  # noqa: E402
from utdata.nya_ristare.ornamentik.overens import by_stone  # noqa: E402

ORN = os.path.join(ROOT, "utdata", "nya_ristare", "ornamentik")
CACHE = os.path.join(ROOT, "data", "cache", "hander", "ornamentik")
J = lambda *p: json.load(open(os.path.join(*p), encoding="utf-8"))  # noqa: E731


def pc(x):
    """Procent avrundat som i resultat.md (halvor uppåt)."""
    return int(100 * x + 0.5)


def kv(x, sv=True):
    s = f"{x:.2f}".replace("-", "−")
    return s.replace(".", ",") if sv else s


# ---- kodningen ur planscherna (resultat.md § 10) -------------------------------------------------------------------
M2 = J(ORN, "m2_utveckling.json")
F = M2["fält"]
N_KODAD = M2["stenar_med_kod"]
assert N_KODAD == 981
assert [F[f]["kappa"] for f in ("djurhuvud", "huvud_vy", "oga", "koppel")] == [0.95, 0.93, 0.92, 0.91]
LAG = [F[f]["kappa"] for f in ("lappflik", "flatverk", "nackflik", "fotter", "svans")]
assert (min(LAG), max(LAG)) == (0.72, 0.80)
TACK = [F[f]["tackning"] for f in ("djurhuvud", "antal_djur", "huvud_vy", "oga", "nackflik", "lappflik", "svans")]
assert (min(TACK), max(TACK)) == (0.35, 0.62)  # "en tredjedel till drygt hälften"
N_PLANSCH, N_KORPUS, N_UTAN_BILD = 1170, 2314, 64  # resultat.md § 10 och planen (bildtexterna i SRI:s textlager)
RES = open(os.path.join(ROOT, "utdata", "nya_ristare", "resultat.md"), encoding="utf-8").read()
assert "1 170 stenar" in RES and "64 stenar hade ingen användbar bild" in RES
assert "2 314" in open(os.path.join(ROOT, "analysplaner", "2026-11-24-nya-ristare-ornamentik.md"), encoding="utf-8").read()

# ---- ristargrupperna (§ 10, slutprov 3) ---------------------------------------------------------------------------
S3 = J(ORN, "slutprov3.json")
assert M2["G1"]["håller"] and M2["G1"]["grupper"] == 10
O1 = S3["O1"]
assert (O1["grupper"], O1["grupper"] - O1["med_skillnad"], O1["bättre"], O1["sämre"]) == (25, 19, 2, 4) and not O1["håller"] and S3["O2"]["håller"]
assert "19 grupper är oförändrade, 2 blev bättre och 4 sämre" in RES and "Bara O2 höll" in RES

# ---- Gräslund 1 -----------------------------------------------------------------------------------------------------
G = J(ROOT, "utdata", "graslund", "graslund1.json")
F1, F2, F3, F4 = G["F1"], G["F2"], G["F3"], G["F4"]
assert F1["stenar"] == 620 and F1["H1_håller"] and F1["p"] == 0.001 and F2["H2_håller"] and F2["p"] == 0.001
assert (pc(F1["träffsäkerhet"]), pc(F1["vanligaste_gruppen"])) == (62, 26)
STYLES = ["RAK", "Fp", "Pr1", "Pr2", "Pr3", "Pr4", "Pr5"]
CONF = F1["förväxlingar"]
N_STIL = {s: sum(CONF[s].values()) for s in STYLES}
HIT = {s: CONF[s].get(s, 0) / N_STIL[s] for s in STYLES}
assert {s: pc(HIT[s]) for s in STYLES} == {"RAK": 92, "Fp": 63, "Pr1": 32, "Pr2": 41, "Pr3": 22, "Pr4": 84, "Pr5": 0}
assert max(CONF, key=lambda s: N_STIL[s]) == "Pr4"  # den vanligaste gruppen
assert N_STIL["Pr5"] - CONF["Pr5"].get("Pr4", 0) == 4  # "alla utom fyra blir Pr4"
assert (F2["fel_inom_Pr"], F2["avstånd"]["1"], F2["avstånd"]["2"], F2["avstånd"]["3"]) == (158, 131, 24, 3)
assert (pc(F2["andel_till_granne"]), pc(F2["omblandning_medel"])) == (83, 59)
assert F3["k"] == 3
K = {c["stenar"]: c["rundata"] for c in F3["klasser"]}
assert sorted(K) == [134, 191, 295]
assert (K[191]["RAK"], K[191]["Fp"]) == (141, 33)
assert (K[134]["Fp"], K[134]["Pr2"], K[134]["Pr1"], K[134]["Pr3"]) == (56, 28, 16, 15)
assert (K[295]["Pr4"], K[295]["Pr3"]) == (144, 71)
assert (pc(F4["inom_uppland_cv"]), pc(F4["Sö"]["träffsäkerhet"])) == (59, 41)
SO = F4["Sö"]["per_grupp"]
assert (pc(SO["RAK"]), pc(SO["Fp"]), pc(SO["Pr3"])) == (88, 35, 18)

# Utforskande (resultat.md "varför faller finindelningen?"): räknat på nytt ur koderna och stenarna i provet
OC = J(CACHE, "orn_koder.json")
ROWS = list(csv.DictReader(open(os.path.join(ROOT, "utdata", "graslund", "stil_sannolikhet.csv"), encoding="utf-8")))
assert len(ROWS) == 620


def saknas(f, g):
    rs = [r for r in ROWS if r["rundata"] == g]
    return sum(1 for r in rs if f not in OC.get(r["signum"], {})), len(rs)


NACK = [saknas("nackflik", g)[0] / saknas("nackflik", g)[1] for g in ("Pr2", "Pr3", "Pr4", "Pr5")]
LAPP = [saknas("lappflik", g)[0] / saknas("lappflik", g)[1] for g in ("Pr2", "Pr3", "Pr4", "Pr5")]
assert (pc(min(NACK)), pc(max(NACK)), pc(min(LAPP)), pc(max(LAPP))) == (75, 91, 84, 90)
assert saknas("nackflik", "Pr4") == (146, 160)
FPV = Counter(OC[r["signum"]]["huvud_vy"] for r in ROWS if r["rundata"] == "Fp" and "huvud_vy" in OC.get(r["signum"], {}))
assert (FPV["uppifran"], sum(FPV.values())) == (32, 52)

# ---- källkontrollen av teckningarna (§ 11) --------------------------------------------------------------------------
KK = J(ORN, "kallkontroll.json")
TP = KK["teckning_mot_plansch"]["alla"]
N_TECKN = KK["teckningar"]
PT = KK["per_typ"]
assert N_TECKN == 129 and (PT["bautil"], PT["rhezelius"], PT["peringskiold"], PT["ovrig"]) == (37, 37, 28, 27)
KT = {f: TP[f]["kappa"] for f in TP}
assert (KT["djurhuvud"], KT["huvud_vy"], KT["nackflik"], KT["koppel"], KT["kors"], KT["flatverk"], KT["antal_djur"]) == \
    (0.86, 0.83, 0.88, 0.86, 0.81, 0.74, 0.73)
assert (KT["svans"], KT["oga"], KT["lappflik"], KT["fotter"]) == (0.60, 0.57, 0.30, 0.0)
assert TP["lappflik"]["jämförbara"] == 16 and TP["nackflik"]["jämförbara"] == 19
BT = KK["teckning_mot_plansch"]["bautil"]["djurhuvud"]
assert (BT["jämförbara"], BT["lika"]) == (17, 1.0)
USE = KK["fält_som_får_läsas"]
assert all("lappflik" not in v and "fotter" not in v for v in USE.values())
assert all(f in USE["bautil"] for f in ("djurhuvud", "huvud_vy", "nackflik", "koppel", "svans", "oga", "kors"))
# Hur många av jämförelserna hade en flik alls (teckningens och planschens konsensus, räknat på nytt)
_runs = J(CACHE, "kodning_kallkontroll.json")
_draw = defaultdict(dict)
for r in _runs:
    if r["batch"].startswith("t"):
        for s in r["stenar"] or []:
            _draw[s["signum"].strip()][r["coder"]] = s
DC = consensus(_draw)
assert len(DC) <= N_TECKN


def par(f):
    return [(DC[s][f], OC[s][f]) for s in DC if s in OC and f in DC[s] and f in OC[s]]


NP = par("nackflik")
NP_LIKA = sum(a == b for a, b in NP)
NP_FLIK = sum(1 for a, b in NP if a != "ingen" or b != "ingen")
LP_FLIK = sum(1 for a, b in par("lappflik") if a != "ingen" or b != "ingen")
assert (len(NP), NP_LIKA, NP_FLIK, LP_FLIK) == (19, 18, 5, 2)
FOT = par("fotter")
assert (len(FOT), sum(1 for a, b in FOT if a == b == "inga")) == (39, 38)
# U 1154 (bevarad, Bautil 659): teckning och plansch lika i alla jämförbara fält
U1154 = [f for f in M2["godkända_fält"] if f in DC["U 1154"] and f in OC["U 1154"]]
assert len(U1154) == 9 and all(DC["U 1154"][f] == OC["U 1154"][f] for f in U1154) and DC["U 1154"]["huvud_vy"] == "uppifran"

# ---- de förlorade stenarna (§ 12) ------------------------------------------------------------------------------------
FB = {s["sig"] for b in J(CACHE, "forlorade_batcher.json") for s in b["stones"]}
LOST_READ = consensus(by_stone(os.path.join(CACHE, "kodning_forlorade.json")))
FL = J(CACHE, "orn_koder_forlorade.json")
KALLA = Counter(v["källa"] for v in FL.values())
assert (len(FB), len(LOST_READ), len(FL), sum(1 for v in FL.values() if len(v["koder"]) >= 3)) == (200, 196, 185, 167)
assert (KALLA["Bautil"], KALLA["Peringskiöld"], KALLA["Rhezelius"], KALLA["SRI-text"]) == (135, 24, 13, 13)
assert all("lappflik" not in v["koder"] and "fotter" not in v["koder"] for v in FL.values())
import pandas as pd  # noqa: E402

CORP = pd.read_csv(os.path.join(ROOT, "data", "cache", "r", "corpus", "510ebfb3acc9a229", "corpus.csv"), low_memory=False).set_index("signum")
LANDSK = Counter(CORP.loc[s, "province"] for s in FL)
assert (LANDSK["U"], LANDSK["Sö"], LANDSK["Sm"]) == (128, 17, 16)
assert all(CORP.loc[s, "lost"] == 1 for s in FL)
N_UTAN_STIL = int(CORP.loc[list(FL), "style"].isna().sum())
assert N_UTAN_STIL == 135
N_FORLORADE_KORPUS = int((CORP["lost"] == 1).sum())
assert N_FORLORADE_KORPUS == 415
U16 = FL["U 16"]
assert U16["källa"] == "Bautil" and U16["koder"] == {
    "djurhuvud": "ja", "antal_djur": "1", "huvud_vy": "profil", "oga": "rund", "nackflik": "spiral", "svans": "spiral",
    "koppel": "ja", "flatverk": "inget", "fyrfota": "nej", "orm_extra": "nej", "kors": "ja"}
assert pd.isna(CORP.loc["U 16", "style"]) and CORP.loc["U 16", "parish"] == "Ekerö sn"
assert CORP.loc["U 1154", "lost"] == 0 and CORP.loc["U 1154", "style"] == "Fp" and CORP.loc["U 1154", "parish"] == "Simtuna sn"
assert CORP.loc["U 1154", "carver"] == "Erik" and CORP.loc["U 1154", "carvers_uncertain"] == 0
N_STILGRUPP = int(CORP["style"].isin(STYLES).sum())
assert 1000 < N_STILGRUPP < 1100  # "drygt tusen"
DAT = {s: (int(CORP.loc[CORP["style"] == s, "style_from"].iloc[0]), int(CORP.loc[CORP["style"] == s, "style_to"].iloc[0]))
       for s in ("RAK", "Pr5")}
assert DAT == {"RAK": (980, 1015), "Pr5": (1100, 1130)}

# ---- instrumentet: kodbok, piloter, regeln för fälten (planen 2026-11-24, resultat § 10) ----------------------------
PLAN_ORN = open(os.path.join(ROOT, "analysplaner", "2026-11-24-nya-ristare-ornamentik.md"), encoding="utf-8").read()
for s in ("Två piloter på 12 och 20 stenar", "rendering i 300 dpi, obligatorisk inzoomning", "kappa ≥ 0,40 och täckning ≥ 0,30",
          "fem stenar\n  per läsare och omgång, i omvänd ordning för den andra läsaren", "högst tre", "Ensidigt Wilcoxon-test"):
    assert s in PLAN_ORN, s
assert re.search(r"Andra användningen\s+av provdelen \(en återstår\)", RES)
assert (F["mun"]["tackning"], F["huvud_svans"]["kappa"], F["kontur"]["kappa"]) == (0.08, 0.27, None)
assert M2["G2"]["håller"] and M2["G2"]["auc_M2"] >= M2["G2"]["auc_M1"]
# läsarna av teckningarna (godkända fält)
LT = [KK["läsarna_teckningar"][f]["kappa"] for f in M2["godkända_fält"] if KK["läsarna_teckningar"][f]["kappa"] is not None]
assert (min(LT), max(LT)) == (0.68, 1.0)

# ---- § 13: djupbilderna och Hälsingland/Medelpad -------------------------------------------------------------------
K3 = J(ORN, "kallkontroll_3d.json")
D3 = K3["djupbild_mot_plansch"]
assert K3["källkontroll_stenar"] == 24 and K3["fält_som_får_läsas_ur_djupbild"] == ["orm_extra"]
L3 = [K3["läsarna_djupbild"][f] for f in ("djurhuvud", "antal_djur", "huvud_vy", "oga")]
assert (min(L3), max(L3)) == (0.41, 0.63)
assert (D3["djurhuvud"]["kappa"], D3["huvud_vy"]["kappa"], D3["oga"]["kappa"], D3["antal_djur"]["kappa"]) == (0.36, 0.10, -0.06, -0.14)
assert D3["svans"]["jämförbara"] == 0 and (D3["koppel"]["kappa"], D3["orm_extra"]["kappa"], D3["kors"]["kappa"], D3["flatverk"]["kappa"]) == (1.0, 1.0, 1.0, 0.58)
assert [f for f in D3 if (D3[f]["jämförbara"] or 0) >= 15 and (D3[f]["kappa"] or 0) >= 0.40] == ["orm_extra"]
HSM = K3["hs_m"]
FOTO = {s: v for s, v in HSM["stenar"].items() if v["bild"] == "foto + djupbild"}
assert HSM["kodade"] == 17 and len(FOTO) == 11 and (min(v["fält"] for v in FOTO.values()), max(v["fält"] for v in FOTO.values())) == (5, 14)
assert sorted(s for s in FOTO if s.startswith("Hs")) == sorted(["Hs 2", "Hs 6", "Hs 9", "Hs 10", "Hs 11", "Hs 12", "Hs 14", "Hs 21"])
assert "Djupbilden ger fel slags bild för det här ändamålet" in RES and "släpljus" in RES

# Sö 112: djupbildens och planschfotots konsensus (två läsare var)
_d3 = defaultdict(dict)
for r in J(CACHE, "kodning_djup_hsm.json"):
    if r["batch"].startswith("d"):
        for s in r["stenar"] or []:
            _d3[s["signum"].strip()][r["coder"]] = s
DC3 = consensus(_d3)
assert DC3["Sö 112"]["huvud_vy"] == "profil" and OC["Sö 112"]["huvud_vy"] == "uppifran" and OC["Sö 112"]["antal_djur"] == "2"
assert CORP.loc["Sö 112", "lost"] == 0 and CORP.loc["Sö 112", "parish"] == "Stenkvista sn" and CORP.loc["Sö 112", "style"] == "Fp"
DJUP = J(ROOT, "data", "cache", "hander", "plansch", "djupbild", "djupbild.json")
DJUP_FIL = [p for p in DJUP["Sö 112"] if p.endswith("So_112_1_4_thin_closed_holes.jpg")][0]
DJUP_META = J("/Volumes/2TB/cache/runmodell/djup/sodermanland/So_112_1_4_thin_closed_holes.json")
from src import scan_sources  # noqa: E402

DS = next(d for d in scan_sources.DATASETS if d["key"] == "sodermanland")
assert "Sö 112" in DS["signa"] and DS["doi"] == "10.5281/zenodo.11951255" and DS["license"] == "CC BY 4.0"
assert DJUP_META["signum"] == "Sö 112" and DJUP_META["file"] == "So 112_1_4 thin_closed holes.stl"
SCAN_FILE = DJUP_META["file"]

# U 1154: de två läsarnas koder för träsnittet, konsensus och planschfotots konsensus
U_R = _draw["U 1154"]
assert sorted(U_R) == [1, 2] or sorted(U_R) == ["1", "2"]
U_R1, U_R2 = (U_R[k] for k in sorted(U_R))
assert (U_R1["koppel"], U_R2["koppel"], U_R1["flatverk"], U_R2["flatverk"]) == ("osäkert", "nej", "inget", "osäkert")
assert "koppel" not in DC["U 1154"] and "flatverk" not in DC["U 1154"]

# ---- figurerna (Vitki): läsningen av U 1154 och Sö 112 i teckning och djupbild ---------------------------------------
import io  # noqa: E402

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402
from PIL import Image  # noqa: E402

RUST, INK, MUTED = "#b7410e", "#1f1d1a", "#77706a"
TD = os.path.join(ROOT, "data", "cache", "hander", "plansch", "teckningar")
FIGDIR = os.path.join(ROOT, "utdata", "blogg", "figurer", "ornamentik")
FIELD = {"djurhuvud": ("Djurhuvud", "Animal head"), "antal_djur": ("Antal djur", "Number of animals"),
         "huvud_vy": ("Huvudets vy", "Head view"), "oga": ("Öga", "Eye"), "nackflik": ("Nackflik", "Neck lappet"),
         "lappflik": ("Läppflik", "Lip lappet"), "svans": ("Svans", "Tail"), "fotter": ("Fötter", "Feet"),
         "koppel": ("Koppel", "Koppel (loop)"), "flatverk": ("Flätverk", "Interlace"), "fyrfota": ("Fyrfota djur", "Quadruped"),
         "orm_extra": ("Extra orm", "Extra serpent"), "manniska_mask": ("Människa/mask", "Human/mask"), "kors": ("Kors", "Cross")}
VAL = {"ja": ("ja", "yes"), "nej": ("nej", "no"), "uppifran": ("ovanifrån", "from above"), "profil": ("profil", "profile"),
       "inget_huvud": ("inget huvud", "no head"), "rund": ("rund", "round"), "mandel": ("mandel", "almond"),
       "inget_synligt": ("syns inte", "not visible"), "ingen": ("ingen", "none"), "inga": ("inga", "none"), "spiral": ("spiral", "spiral"),
       "inget": ("inget", "none"), "osäkert": ("osäkert", "uncertain"), "rak": ("rak", "straight"), "attor": ("åttor", "figures of eight")}
BOX = {"huvud": (400, 440, 700, 650), "svans": (500, 730, 700, 880), "band": (240, 600, 480, 800)}  # px i Bautil 659


def _v(x, i):
    return VAL.get(x, (x, x))[i] if x is not None else "–"


def _png(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100, metadata={"Software": None})
    plt.close(fig)
    return buf.getvalue()


def fig_lasning(sv):
    i = 0 if sv else 1
    im = Image.open(os.path.join(TD, "U_1154_bautil_659.jpg")).convert("RGB")
    fig = plt.figure(figsize=(16, 8.2), facecolor="white")
    a0 = fig.add_axes([0.01, 0.13, 0.36, 0.80])
    a0.imshow(im)
    a0.set_axis_off()
    lab = {"huvud": ("1 Huvudet", "1 The head"), "svans": ("2 Svansen", "2 The tail"),
           "band": ("3 Bandändarna – koppel?", "3 The band ends – koppel?")}
    for n, (k, b) in enumerate(BOX.items()):
        a0.add_patch(Rectangle((b[0], b[1]), b[2] - b[0], b[3] - b[1], fill=False, lw=3, ec=RUST))
        a0.text(b[0] + 6, b[1] - 10, str(n + 1), color=RUST, fontsize=17, fontweight="bold", va="bottom")
    a0.set_title("Bautil nr 659 – U 1154" if sv else "Bautil no. 659 – U 1154", fontsize=14, color=INK, loc="left")
    for n, (k, b) in enumerate(BOX.items()):
        ax = fig.add_axes([0.385, 0.68 - n * 0.28, 0.16, 0.24])
        ax.imshow(im.crop(b))
        ax.set_xticks([]), ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_edgecolor(RUST), sp.set_linewidth(2.5)
        ax.set_title(lab[k][i], fontsize=12, color=RUST, loc="left")
    at = fig.add_axes([0.565, 0.13, 0.425, 0.82])
    at.set_axis_off()
    at.set_xlim(0, 1), at.set_ylim(0, 1)
    cols = [0.0, 0.29, 0.46, 0.63, 0.79]
    head = (["Drag", "Läsare 1", "Läsare 2", "Enigt", "Planschfoto*"] if sv
            else ["Feature", "Reader 1", "Reader 2", "Agreed", "Plate photo*"])
    y = 0.97
    for x, h in zip(cols, head):
        at.text(x, y, h, fontsize=12, fontweight="bold", color=INK, va="top")
    at.plot([0, 1], [y - 0.045, y - 0.045], color=INK, lw=1)
    at.set_xlim(0, 1), at.set_ylim(0, 1)
    y -= 0.07
    for f in M2["godkända_fält"]:
        r1, r2 = U_R1.get(f), U_R2.get(f)
        c = DC["U 1154"].get(f)
        never = f in ("lappflik", "fotter")
        col = RUST if (r1 != r2) else INK
        at.text(cols[0], y, FIELD[f][i] + (" †" if never else ""), fontsize=11.5, color=col, va="top")
        at.text(cols[1], y, _v(r1, i), fontsize=11.5, color=col, va="top")
        at.text(cols[2], y, _v(r2, i), fontsize=11.5, color=col, va="top")
        at.text(cols[3], y, _v(c, i), fontsize=11.5, color=MUTED if never else (RUST if c is None else INK), va="top",
                fontweight="bold" if c is not None and not never else "normal")
        at.text(cols[4], y, _v(OC["U 1154"].get(f), i), fontsize=11.5, color=INK, va="top")
        y -= 0.056
    note = (["Rött: läsarna var oeniga eller osäkra – då får draget inget värde (–).",
             "† Läppflik och fötter läses aldrig ur teckningar (källkontrollen).",
             "* Konsensus av två andra läsare på SRI:s planschfoto; bilden visas inte (upphovsrätt)."] if sv else
            ["Red: the readers disagreed or were unsure – the feature then gets no value (–).",
             "† Lip lappet and feet are never read from drawings (the source check).",
             "* Consensus of two other readers on the SRI plate photo; the image is not shown (copyright)."])
    for n, t in enumerate(note):
        at.text(0, y - 0.005 - n * 0.042, t, fontsize=9.5, color=MUTED, va="top")
    fig.text(0.01, 0.035, ("Figur: Vitki. Läsningen görs i Vitkis kodningsarbete av två oberoende läsare (Anthropics språkmodell Claude, Claude Opus), "
                           "inte i appens gränssnitt.\nTräsnitt: J. Göransson, Bautil (1750) nr 659, Umeå universitetsbiblioteks exemplar, "
                           "fritt från kända upphovsrättsliga restriktioner.") if sv else
             ("Figure: Vitki. The reading is done in Vitki's coding workflow by two independent readers (Anthropic's language model Claude, "
              "Claude Opus), not in the app's interface.\nWoodcut: J. Göransson, Bautil (1750) no. 659, Umeå University Library copy, "
              "free of known copyright restrictions."), fontsize=10, color=MUTED, va="bottom")
    return _png(fig)


def fig_djup(sv):
    i = 0 if sv else 1
    dr = Image.open(os.path.join(TD, "Sö_112_bautil_748.jpg")).convert("RGB").crop((90, 110, 1764, 1940))
    dp = Image.open(DJUP_FIL).convert("RGB").rotate(-90, expand=True)  # stenens topp (vänster i djupkartan) uppåt
    fig = plt.figure(figsize=(14, 10), facecolor="white")
    a1 = fig.add_axes([0.01, 0.19, 0.56, 0.74])
    a1.imshow(dr)
    a1.set_axis_off()
    a1.set_title("Bautil nr 748 – Sö 112, Kolunda" if sv else "Bautil no. 748 – Sö 112, Kolunda", fontsize=14, color=INK, loc="left")
    a1.add_patch(Rectangle((330, 1300), 640, 330, fill=False, lw=3, ec=RUST))
    a2 = fig.add_axes([0.58, 0.19, 0.41, 0.74])
    a2.imshow(dp)
    a2.set_axis_off()
    a2.set_title("Djupbild ur 3D-skanningen" if sv else "Depth image from the 3D scan", fontsize=14, color=INK, loc="left")
    h = dp.size[1]
    a2.add_patch(Rectangle((1147 - 290, 2100), 200, 380, fill=False, lw=3, ec=RUST))
    assert h > 2400
    t1 = ("Planschfotot, två eniga läsare: huvudet sett ovanifrån.\nBåda tog dock svansen för ett andra huvud (fel, rättat i efterhand)."
          if sv else "Plate photo, two agreeing readers: head seen from above.\nBoth, however, took the tail for a second head (an error, corrected afterwards).")
    t2 = ("Djupbilden, två eniga läsare: huvudet i profil,\nmot ovanifrån på planschfotot.\nI provet höll djupbilden bara för ”extra orm”."
          if sv else "Depth image, two agreeing readers: head in profile,\nagainst from above on the plate photo.\nIn the test the depth image held only for 'extra serpent'.")
    fig.text(0.02, 0.17, t1, fontsize=12.5, color=INK, va="top")
    fig.text(0.58, 0.17, t2, fontsize=12.5, color=RUST, va="top")
    fig.text(0.01, 0.02, ("Figur: Vitki. Vänster: J. Göransson, Bautil (1750) nr 748, Umeå universitetsbiblioteks exemplar, fritt från kända "
                          "upphovsrättsliga restriktioner.\nHöger: djupbild beräknad i Vitki ur skanningen av Sö 112 av Laila Kitzler Åhfeldt "
                          f"(Riksantikvarieämbetet), Runristandets dynamik, CC BY 4.0, doi:{DS['doi']}.") if sv else
             ("Figure: Vitki. Left: J. Göransson, Bautil (1750) no. 748, Umeå University Library copy, free of known copyright "
              "restrictions.\nRight: depth image computed in Vitki from the scan of Sö 112 by Laila Kitzler Åhfeldt "
              f"(Swedish National Heritage Board), Runristandets dynamik, CC BY 4.0, doi:{DS['doi']}."),
             fontsize=10, color=MUTED, va="bottom")
    return _png(fig)


os.makedirs(FIGDIR, exist_ok=True)
FIG = {}
for name, fn in (("lasning_u1154", fig_lasning), ("djupbild_so112", fig_djup)):
    for lang, sv in (("sv", True), ("en", False)):
        data = fn(sv)
        open(os.path.join(FIGDIR, f"{name}_{lang}.png"), "wb").write(data)
        FIG[f"{name}_{lang}"] = blog_figures.freeze(data)


def chart(sv):
    namn = {"RAK": ("RAK – raka bandändar", "RAK – straight band ends"), "Fp": ("Fp – huvud ovanifrån", "Fp – head seen from above"),
            "Pr1": ("Pr1 – profil", "Pr1 – profile"), "Pr2": ("Pr2", "Pr2"), "Pr3": ("Pr3", "Pr3"), "Pr4": ("Pr4", "Pr4"), "Pr5": ("Pr5", "Pr5")}
    rows = [":::chart Stenar där rundjurets drag pekar ut Rundatas stilgrupp, procent" if sv
            else ":::chart Stones where the rune animal's features point to Rundata's style group, percent"]
    rows.append("# Per stilgrupp, i Gräslunds ordning" if sv else "# Per style group, in Gräslund's order")
    for s in STYLES:
        rows.append(f"{namn[s][0 if sv else 1]} | {pc(HIT[s])} | {N_STIL[s]} {'stenar' if sv else 'stones'}")
    rows.append("# Alla stenar" if sv else "# All stones")
    rows.append(f"+{'Rundjurets drag' if sv else 'The animal’s features'} | {pc(F1['träffsäkerhet'])} | {F1['stenar']} {'stenar' if sv else 'stones'}")
    rows.append(f"{'Gissa alltid Pr4' if sv else 'Always guess Pr4'} | {pc(F1['vanligaste_gruppen'])} | –")
    rows.append("Korsvaliderat, grupperat på socken; provet låstes i förväg. Diagram: Vitki, ur kodningen av SRI:s planscher och Rundata 3.1."
                if sv else "Cross-validated, grouped by parish; the test was locked in advance. Chart: Vitki, from the coding of the SRI plates and Rundata 3.1.")
    return "\n".join(rows) + "\n:::"


BAUTIL_SV = "Umeå universitetsbiblioteks exemplar (Digitala samlingar), fritt från kända upphovsrättsliga restriktioner"
BAUTIL_EN = "Umeå University Library copy (Digital collections), free of known copyright restrictions"
N3 = K3["källkontroll_stenar"]
N_LOST3 = sum(1 for v in FL.values() if len(v["koder"]) >= 3)

assert round(M2["G1"]["median_percentil"], 2) == 0.67 and M2["G1"]["p"] < 1 / 500
assert "σ = 12 mm" in open(os.path.join(ORN, "djupbild.py"), encoding="utf-8").read()
assert KK["gotland_öland_kodade"] == 43
assert DS["device"].startswith("ATOS I (GOM)") and "Runristandets dynamik (2009–2014)" in DS["project"]

SLUG = "sa-laser-vi-rundjuren"
title = "Så läser vi rundjuren – en metod för att mäta ornamentiken på över tusen runstenar"
title_en = "How we read the rune animals – a method for measuring the ornament on over a thousand runestones"
summary = ("Hur gör man ett rundjur till något som går att räkna på? Två oberoende läsare, en fast kodbok, en regel för vilka "
           "drag som håller – och en prövning av varje slags bild mot en annan. De gamla teckningarna klarade provet för "
           "djurets huvuddrag. Djupbilderna ur 3D-skanningarna gjorde det inte.")
summary_en = ("How do you turn a rune animal into something you can count? Two independent readers, a fixed codebook, a rule for "
              "which features hold – and a test of every kind of picture against another. The old drawings passed the test for "
              "the animal's main features. The depth images from the 3D scans did not.")

body = f"""Den som står framför en runsten ser ofta djuret innan runorna: bandet som slingrar sig runt stenen, huvudet, svansen, öglan som binder ihop två kroppar. Forskningen har beskrivit djuren i ord i över hundra år, och arkeologen Anne-Sofie Gräslunds indelning av dem i stilgrupper är en av grunderna för att datera de svenska runstenarna. Men en beskrivning i ord går inte att räkna på.

Den här artikeln handlar om hur vi i Vitki har gjort rundjuret mätbart. Hur ett djur blir en rad koder, hur vi vet om koderna går att lita på, och hur vi prövar bilderna vi läser från mot varandra. Resultaten finns med, men som prov på vad metoden klarar och inte klarar.

## Från djur till koder

Gräslunds grupper bygger på enskilda drag. RAK är stenar där runbandets ändar är raka, utan djurhuvud. Fp, efter ”fågelperspektiv”, är stenar där djurets huvud är sett ovanifrån, som en mask med två ögon. Pr1 till Pr5 är djur med huvudet i profil, i fem steg där bland annat flikarna vid nacke och läppar, huvudets form och linjernas svängar ändras. Grupperna har tider, från RAK omkring {DAT['RAK'][0]}–{DAT['RAK'][1]} till Pr5 omkring {DAT['Pr5'][0]}–{DAT['Pr5'][1]}, och drygt tusen runstenar har fått en av dem i Rundata, den samnordiska runtextdatabasen.

Vår idé är enkel: läs dragen ett och ett, på alla stenar som har en bild, och se sedan vad de säger tillsammans. Målet är att pröva och förfina Gräslunds indelning, steg för steg, inte att ersätta den.

Verktyget är en kodbok med frågor om rundjuret. Slutar bandet i ett djurhuvud? Hur många djur är det? Är huvudet sett från sidan eller ovanifrån? Är ögat runt eller mandelformat? Finns en flik i nacken eller vid läpparna? Hur slutar svansen? Finns ett koppel, en ögla som binder ihop två djur, och finns flätverk eller ett kors? Två regler gäller för varje fråga: koda bara det som syns, och svara ”osäkert” när det inte syns säkert. Läsaren ska också alltid zooma in, skära ut huvudet, svansen och bandändarna i full upplösning och titta på utsnitten innan huvudets drag kodas.

Kodboken prövades först i två piloter på 12 och 20 stenar, alla utanför de stenar som senare skulle användas i proven. Efter piloterna ändrades tre saker: bilderna läses i högre upplösning, inzoomningen blev obligatorisk, och en fråga som blandade två saker delades i två. Sedan låstes kodboken.

## Två läsare som inte ser varandra

Varje bild lästes av två läsare oberoende av varandra, två separata körningar av Anthropics språkmodell Claude (Claude Opus). Läsarna såg bara bilden och stenens signum, fem stenar i taget, och den andra läsaren fick stenarna i omvänd ordning. Båda ombads att inte använda vad de visste om stenen, ristaren eller litteraturen.

Ett drag får ett värde bara när båda läsarna ger samma svar. Är de oeniga, eller säger någon av dem ”osäkert”, saknas värdet. Det är en medveten försiktighet: ett saknat värde är ärligt, en gissning är det inte.

![Så läses ett träsnitt: U 1154 i Bautil]({FIG['lasning_u1154_sv']})
Figur: Vitki. Läsningen av träsnittet av U 1154 i Simtuna socken: de tre utsnitt som läsarna tittar på, de två läsarnas koder, det eniga värdet och – som text – vad två andra läsare kom fram till på SRI:s planschfoto av samma sten. Läsningen görs i Vitkis kodningsarbete av två oberoende läsare (Anthropics språkmodell Claude, Claude Opus); det är ännu ingen funktion i appens gränssnitt. Träsnitt nummer 659 i Johan Göranssons *Bautil* (1750), {BAUTIL_SV}.

Figuren visar hur det går till på en sten. U 1154 är en av de stenar Rundata räknar till Fp, och båda läsarna såg i träsnittet ett huvud ovanifrån med runda ögon och en svans som slutar i en spiral. Om kopplet var de inte överens: den ena svarade ”osäkert”, den andra ”nej”. Därför får kopplet inget värde. I de nio drag där både träsnittet och planschfotot fick ett enigt värde gav de samma svar.

## Hur eniga är läsarna?

Att två läsare ofta är eniga säger lite, om slumpen hade kunnat ge samma enighet. Därför mäter vi med Cohens kappa, ett mått där slumpens bidrag är borträknat. Ett kappa på 1 betyder att läsarna alltid är eniga, och 0 att de inte är eniga oftare än om de hade gissat.

*Sveriges runinskrifter*, det stora utgåvsverket, har planscher med foton av {N_PLANSCH:,} av korpusens {N_KORPUS:,} stenar. Planscherna är skyddade av upphovsrätten, så vi läser och räknar på dem men visar dem inte. På planschfotona var kappa {kv(F['djurhuvud']['kappa'])} för om bandet har ett djurhuvud, {kv(F['huvud_vy']['kappa'])} för hur huvudet är vänt, {kv(F['oga']['kappa'])} för ögat och {kv(F['koppel']['kappa'])} för kopplet, alltså nästan full enighet. Flikarna, svansen, fötterna och flätverket låg mellan {kv(min(LAG))} och {kv(max(LAG))}, vilket brukar räknas som god enighet.

Enighet räcker ändå inte. Ett drag som båda läsarna sällan kan se säger lite, även om de är eniga de få gånger de ser det. Därför bestämde vi i förväg, innan koderna jämfördes med något, att ett fält bara får användas om kappa är minst 0,40 och båda läsarna kan ge ett värde på minst 30 procent av stenarna. Tre fält föll: munnen, som bara kunde läsas på {pc(F['mun']['tackning'])} procent av stenarna, hur huvud och svans möts, där kappa bara var {kv(F['huvud_svans']['kappa'])}, och bandets kantlinjer, som inte varierade alls. Huvudets detaljer kunde läsas på en tredjedel till drygt hälften av stenarna. {N_UTAN_BILD} stenar saknade en användbar bild, och {N_KODAD} fick så många eniga drag att de kunde jämföras.

## Tre slags bilder, prövade mot varandra

Enighet är inte detsamma som rätt. Två läsare kan vara eniga om samma misstag, särskilt om de läser en dålig bild. Därför prövar vi varje ny sorts bild mot en annan innan den får användas. Vi har tre: planschfotona i *Sveriges runinskrifter*, de gamla teckningarna från 1600- och 1700-talen och djupbilder som vi räknar fram ur öppna 3D-skanningar. Regeln skrivs ned i förväg för alla tre: ett drag får läsas från en sorts bild om den stämmer med planschfotot med ett kappa på minst 0,40, mätt på minst 15 stenar. Planschfotot är inte heller facit, utan en annan återgivning av samma sten. Det vi mäter är om två bilder av samma sten säger samma sak.

**Teckningarna.** Många runstenar har försvunnit och finns bara kvar som teckningar: i *Bautil*, en samling träsnitt som skars på 1600-talet och trycktes först 1750, hos Johannes Rhezelius på 1630-talet och hos Johan Peringskiöld kring år 1700. Vi prövade teckningarna på {N_TECKN} bevarade stenar som har både en gammal teckning och ett planschfoto. Urvalet drog 140 teckningar, men några stenar kom med under flera tecknare. Två nya läsare kodade teckningarna utan att se fotona, och de var lika eniga som på fotona, med kappa mellan {kv(min(LT))} och {kv(max(LT)).replace('1,00', '1')}.

Tecknarna återgav djurets huvuddrag troget. Mot planschfotot stämde om djuret har ett huvud med kappa {kv(KT['djurhuvud'])}, hur huvudet är vänt {kv(KT['huvud_vy'])}, nackfliken {kv(KT['nackflik'])}, kopplet {kv(KT['koppel'])}, korset {kv(KT['kors'])}, flätverket {kv(KT['flatverk'])} och antalet djur {kv(KT['antal_djur'])}. Svansen ({kv(KT['svans'])}) och ögat ({kv(KT['oga'])}) stämde måttligt men klarade regeln. Läppfliken ({kv(KT['lappflik'])}) och fötterna ({kv(KT['fotter'])}) klarade den inte, och därför läses de aldrig från en teckning. Talen är små: nackfliken stämde på {NP_LIKA} av {len(NP)} stenar, men bara {NP_FLIK} av dem hade en flik alls.

**Djupbilderna.** Riksantikvarieämbetet har publicerat 3D-skanningar av runstenar under en fri licens. Ur dem räknar Vitki fram en djupbild: stenens yta minus en utjämnad version av den, så att ristade linjer blir mörka, ungefär som en sten i släpljus. Det lät som en bra väg till de stenar som saknar planschfoto. Vi prövade den på {N3} skannade stenar med planschkod.

Den höll inte. Läsarna var redan sinsemellan osäkrare än på foton, med kappa {kv(min(L3))}–{kv(max(L3))} för huvudets drag. Mot planschfotot stämde djurhuvudet med kappa {kv(D3['djurhuvud']['kappa'])}, huvudets vy med {kv(D3['huvud_vy']['kappa'])}, ögat med {kv(D3['oga']['kappa'])} och antalet djur med {kv(D3['antal_djur']['kappa'])}, alltså i stort sett inte bättre än slumpen. Svansen gick inte att läsa alls. Koppel, extra orm och kors stämde helt och flätverket måttligt ({kv(D3['flatverk']['kappa'])}), men bara extra orm hade de 15 stenar som regeln kräver. Enligt regeln får därför bara ”extra orm” läsas ur djupbilderna.

![Teckning och djupbild av Sö 112]({FIG['djupbild_so112_sv']})
Figur: Vitki. Sö 112 vid Kolunda i Stenkvista socken, i träsnittet i Bautil och i djupbilden ur 3D-skanningen. På planschfotot var läsarna eniga om att huvudena är sedda ovanifrån; i djupbilden var de lika eniga om ett huvud i profil. Vänster: träsnitt nummer 748 i Johan Göranssons *Bautil* (1750), {BAUTIL_SV}. Höger: djupbild beräknad i Vitki ur skanningen av Sö 112 (filen {SCAN_FILE}) av Laila Kitzler Åhfeldt, Riksantikvarieämbetet, inom forskningsprojektet Runristandets dynamik (2009–2014), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.sv), doi:{DS['doi']}.

Sö 112 visar varför. Djupbilden visar vittring och sprickor lika tydligt som de grunda ornamentlinjerna, och läsarna kunde inte skilja huvud, öga och svans ur bakgrunden. Det gäller just den här beräkningen, inte 3D-skanningarna i sig. En bild med släpljus från flera håll kan prövas senare, med en ny låst källkontroll. Till dess är resultatet negativt, och det står kvar.

**Hälsingland och Medelpad.** Deras stenar finns inte bland de planscher vi har läst, så där läste vi i stället fria foton av de målade stenarna. {HSM['kodade']} stenar kodades, och de {len(FOTO)} som har ett sådant foto finns nu i registret med {min(v['fält'] for v in FOTO.values())}–{max(v['fält'] for v in FOTO.values())} drag var. Stenar med bara djupbild får bara fältet extra orm och räknas i praktiken inte.

## Låsta planer, grind och slutprov

Den största risken i ett arbete som det här är att leta tills man hittar. Därför skrivs varje analys ned och låses innan koderna jämförs med det de ska prövas mot. Planen säger vad som ska mätas, hur, och vad som räknas som att det håller, och den får inte ändras efteråt.

Prövningen av ristarna visar hur det fungerar. Vi hade en modell som föreslår grupper av runstenar som kan vara gjorda av samma hand, också när ingen ristare har namn, och frågan var om rundjurets drag gör grupperna bättre. Runologernas uttalanden om ”samma ristare” är facit, och de är slumpvis delade i två delar. Den ena får vi arbeta med. Den andra, provdelen, öppnas högst tre gånger, och bara när en förbättring först har klarat en grind på den första delen.

Grinden höll. Stenar som runologerna säger har samma ristare liknar varandra mer i rundjurets drag än grannstenar på samma avstånd. Mätt över {M2['G1']['grupper']} grupper låg det typiska paret högre än två tredjedelar av grannstenarna, och ett så tydligt mönster uppstår av en slump färre än en gång på 500. Modellen tappade inte heller något på att få dragen. Då öppnades provdelen, för andra gången. Där höll det inte: av {O1['grupper']} grupper förblev {O1['grupper'] - O1['med_skillnad']} oförändrade, {O1['bättre']} blev bättre och {O1['sämre']} sämre. Enligt planen behåller Vitki därför den gamla modellen. Ornamentiken bär spår av handen, men det mesta av det den kan tillföra ser modellen redan i stilgruppen, korsformen och utgivarnas ord om ornamentiken. Provdelen har en öppning kvar, och den sparas.

## Vad metoden visade om Gräslunds stilar

Det första låsta provet av Gräslunds indelning gällde {F1['stenar']} stenar med minst tre eniga drag och en stilgrupp i Rundata. En statistisk modell fick lära sig sambandet på stenarna i fyra femtedelar av socknarna och gissa stilgruppen i den sista femtedelen, fem gånger om, så att ingen sten bedömdes av en modell som hade sett den eller dess grannar i samma socken. Den satte rätt grupp på {pc(F1['träffsäkerhet'])} procent av stenarna. Den som alltid gissar på den vanligaste gruppen, Pr4, träffar {pc(F1['vanligaste_gruppen'])} procent. När vi blandade om stilgrupperna slumpvis och gjorde om alltihop 999 gånger kom ingen av omblandningarna upp i modellens träffar.

{chart(True)}

RAK, Pr4 och Fp känns igen väl. Huvudets vy gör mycket av arbetet för Fp: av de {sum(FPV.values())} Fp-stenar där läsarna var eniga om huvudet var det sett ovanifrån på {FPV['uppifran']}. Pr1, Pr2 och Pr3 känns igen bara på mellan en av fem och två av fem stenar, och Pr5 inte alls: alla Pr5-stenar utom fyra blir Pr4.

Felen hamnar inte på måfå. Av de {F2['fel_inom_Pr']} stenar som fick fel Pr-grupp hamnade {F2['avstånd']['1']} ett steg bort, {F2['avstånd']['2']} två steg och bara {F2['avstånd']['3']} tre steg bort: {pc(F2['andel_till_granne'])} procent hos närmaste granne. Om felen hade fördelats slumpvis hade ungefär {pc(F2['omblandning_medel'])} procent ändå landat hos en granne, eftersom de flesta Pr-grupper har två grannar bland bara fyra andra, och ingen av 999 omblandningar kom upp i {pc(F2['andel_till_granne'])}. Pr-grupperna beter sig alltså som en ordnad följd, i linje med Gräslunds tanke att de följer på varandra.

När dragen själva fick visa vilka grupper de bildar, med en modell som inte fick veta stilgrupperna, blev det tre:

- **Inget djurhuvud och inget flätverk:** 191 stenar, varav {K[191]['RAK']} RAK och {K[191]['Fp']} Fp.
- **Ett djur med enkelt huvud, runt öga och svansen i spiral, utan flikar och oftast utan koppel:** 134 stenar, mest Fp ({K[134]['Fp']}), Pr2 ({K[134]['Pr2']}), Pr1 ({K[134]['Pr1']}) och Pr3 ({K[134]['Pr3']}).
- **Huvud i profil, mandelformat öga, koppel och oftast en extra orm:** 295 stenar, mest Pr4 ({K[295]['Pr4']}) och Pr3 ({K[295]['Pr3']}).

Det är Gräslunds huvudlinjer, men inte hennes sju grupper. Var finindelningen tar slut visar var metoden behöver bli bättre. Pr-grupperna skiljs åt framför allt med flikarna vid nacke och läppar, och nackfliken saknar ett enigt värde på {pc(min(NACK))}–{pc(max(NACK))} procent av stenarna i Pr2–Pr5, läppfliken på {pc(min(LAPP))}–{pc(max(LAPP))} procent. Det beror inte på att stenarna saknar flikar, utan på att flikarna inte går att läsa säkert på ett foto av hela stenen. Om Pr-grupperna är fem skilda grupper eller ett glidande kontinuum kan provet därför inte avgöra ännu.

## Det koderna redan används till

Källkontrollen gör det möjligt att läsa de försvunna stenarna. {len(FB)} förlorade stenar har en teckning från 1500- till 1700-talet. {len(LOST_READ)} teckningar gick att läsa, och {len(FL)} stenar fick minst ett godkänt drag, {N_LOST3} av dem minst tre, {KALLA['Bautil']} ur Bautil. Bara de drag som klarade källkontrollen tas med, och varje kod är märkt med vilken teckning den kommer från. {N_UTAN_STIL} av de {len(FL)} stenarna har ingen stilgrupp alls i Rundata. Till registret kom också {KK['gotland_öland_kodade']} stenar från Gotlands och Ölands planscher och de {len(FOTO)} från Hälsingland och Medelpad.

## Svagheterna

- **Rundatas stilgrupp är inte facit.** Den är experternas tillämpning av Gräslunds kriterier. När koderna och Rundata inte stämmer kan felet ligga hos koderna, hos tilldelningen eller hos indelningen.
- **De två läsarna är samma modell.** De läser oberoende av varandra, men de kan ha samma blinda fläckar. Därför prövas varje sorts bild mot en annan, och därför vill vi ha en tredje läsare.
- **Läsarna kan känna igen kända stenar** trots instruktionen.
- **Bara hälften av stenarna är avbildade** på planscherna, och huvudets detaljer syns bara på en tredjedel till drygt hälften av dem.
- **Stilprovet var väntat att hålla,** eftersom grupperna en gång sattes efter samma slags drag. Det som säger något är mönstret i felen.

## Nästa steg

Nästa steg är att se bättre. Vi ska läsa huvudena i egna utsnitt i stället för på hela stenen, ge läsarna ett exempelblad med Gräslunds egna huvudtyper och låta en tredje läsare avgöra när två är oeniga. Djupbilderna kan få en ny chans med släpljus från flera håll, under en ny låst plan. Först när flikarna går att läsa på fler stenar kan frågan om fem grupper eller en glidande följd prövas på riktigt. Därefter kommer tiden: håller ordningen mot dateringar som inte bygger på stilen?

Den som har en runsten i närheten kan prova kodboken själv. Titta på huvudet. Är det sett från sidan eller ovanifrån? Finns det en flik i nacken, och rullar den upp sig? Svara ”osäkert” när du inte ser säkert. Det är den svåraste regeln och den viktigaste.

## Om skanningen

Djupbilden av Sö 112 är beräknad i Vitki ur filen {SCAN_FILE}, använd som den är publicerad. Skanningen gjordes av runologen Laila Kitzler Åhfeldt vid Riksantikvarieämbetet inom forskningsprojektet *Runristandets dynamik* (2009–2014), med en ATOS I-skanner (GOM, strukturerat ljus); bara inskriftsytan är skannad. Den publicerades öppet på Zenodo 2024 i datamängden *3D-data Runstenar i Södermanland*, under licensen [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.sv). Om skanningarna och ristarna har Kitzler Åhfeldt själv skrivit, bland annat 2015 och 2017. Tack till Laila Kitzler Åhfeldt för att skanningarna är fritt tillgängliga.

:::box Det viktigaste i korthet
- Rundjuret går att mäta: en fast kodbok, två oberoende läsare och en regel för vilka drag som får användas gör ornamentiken till koder som går att räkna på.
- Varje sorts bild prövas mot en annan innan den används. De gamla teckningarna håller för djurets huvuddrag men inte för läppflikarna, och djupbilderna ur 3D-skanningarna håller inte för huvudet alls.
- Låsta planer och en provdel som öppnas högst tre gånger gör att också negativa utfall står kvar.
- Som prov bär koderna Gräslunds huvudlinjer. Finindelningen inom Pr väntar på en bättre läsning av flikarna.
:::

## Källor

Kitzler Åhfeldt, L. 2024. *3D-data Runstenar i Södermanland / Runestones in Södermanland* [Dataset]. Riksantikvarieämbetet. [https://doi.org/{DS['doi']}](https://doi.org/{DS['doi']}). Kitzler Åhfeldt, L. 2015. Rune Carvers and Local Mobility. *Viking and Medieval Scandinavia* 11, s. 143–182. Kitzler Åhfeldt, L. 2017. *Runristare och mobilitet i Södermanland*. Stockholm: Riksantikvarieämbetet. Gräslund, A.-S. 2006. Dating the Swedish Viking-Age rune stones on stylistic grounds. I: M. Stoklund m.fl. (red.), *Runes and their Secrets: Studies in Runology*. Köpenhamn: Museum Tusculanum Press, s. 117–139. Samnordisk runtextdatabas (Rundata) 3.1, Uppsala universitet. *Sveriges runinskrifter*, Riksantikvarieämbetet (planscher och textband, lästa men inte återgivna). Göransson, J. 1750. *Bautil*. Stockholm; {BAUTIL_SV}. De låsta analysplanerna (2026-11-24 och 2026-11-25), kodboken och resultaten finns i Vitkis öppna kodförråd."""

body_en = f"""Anyone standing before a runestone often sees the animal before the runes: the band winding round the stone, the head, the tail, the loop that binds two bodies together. Research has described the animals in words for more than a hundred years, and the archaeologist Anne-Sofie Gräslund's division of them into style groups is one of the foundations for dating the Swedish runestones. But a description in words cannot be counted.

This article is about how we at Vitki have made the rune animal measurable. How an animal becomes a row of codes, how we know whether the codes can be trusted, and how we test the pictures we read from against each other. The results are included, but as a test of what the method can and cannot do.

## From animal to codes

Gräslund's groups rest on individual features. RAK stones have rune bands with straight ends and no animal head. Fp, for the Swedish "fågelperspektiv" (bird's-eye view), are stones where the animal's head is seen from above, like a mask with two eyes. Pr1 to Pr5 are animals with the head in profile, in five steps in which, among other things, the lappets at neck and lips, the shape of the head and the curves of the lines change. The groups have dates, from RAK around {DAT['RAK'][0]}–{DAT['RAK'][1]} to Pr5 around {DAT['Pr5'][0]}–{DAT['Pr5'][1]}, and just over a thousand runestones have been given one of them in Rundata, the Scandinavian Runic-text Database.

Our idea is simple: read the features one by one, on every stone that has a picture, and then see what they say together. The aim is to test and refine Gräslund's division, step by step, not to replace it.

The tool is a codebook of questions about the rune animal. Does the band end in an animal head? How many animals are there? Is the head seen from the side or from above? Is the eye round or almond-shaped? Is there a lappet at the neck or at the lips? How does the tail end? Is there a "koppel", a loop that binds two animals together, and is there interlace or a cross? Two rules apply to every question: code only what can be seen, and answer "uncertain" when it cannot be seen with certainty. The reader must also always zoom in, cut out the head, the tail and the band ends at full resolution and look at the crops before coding the head's features.

The codebook was first tried in two pilots on 12 and 20 stones, all outside the stones later used in the tests. After the pilots three things changed: the pictures are read at higher resolution, zooming became compulsory, and one question that mixed two things was split in two. Then the codebook was locked.

## Two readers who do not see each other

Every picture was read by two readers independently of each other, two separate runs of Anthropic's language model Claude (Claude Opus). The readers saw only the picture and the stone's signum, five stones at a time, and the second reader got the stones in reverse order. Both were told not to use what they knew about the stone, the carver or the literature.

A feature gets a value only when both readers give the same answer. If they disagree, or if either says "uncertain", the value is missing. That is deliberate caution: a missing value is honest, a guess is not.

![How a woodcut is read: U 1154 in Bautil]({FIG['lasning_u1154_en']})
Figure: Vitki. The reading of the woodcut of U 1154 in Simtuna parish: the three crops the readers look at, the two readers' codes, the agreed value and – as text – what two other readers found on the SRI plate photo of the same stone. The reading is done in Vitki's coding workflow by two independent readers (Anthropic's language model Claude, Claude Opus); it is not yet a feature in the app's interface. Woodcut number 659 in Johan Göransson's *Bautil* (1750), {BAUTIL_EN}.

The figure shows how it works on one stone. U 1154 is one of the stones Rundata counts as Fp, and in the woodcut both readers saw a head from above with round eyes and a tail ending in a spiral. On the koppel they did not agree: one answered "uncertain", the other "no". So the koppel gets no value. In the nine features where both the woodcut and the plate photo got an agreed value, they gave the same answer.

## How far do the readers agree?

That two readers often agree says little if chance could have produced the same agreement. So we measure with Cohen's kappa, a measure from which the contribution of chance is removed. A kappa of 1 means the readers always agree, and 0 that they agree no more often than if they had guessed.

*Sveriges runinskrifter*, the great edition, has plates with photographs of {N_PLANSCH:,} of the corpus's {N_KORPUS:,} stones. The plates are protected by copyright, so we read and count from them but do not show them. On the plate photos kappa was {kv(F['djurhuvud']['kappa'], False)} for whether the band has an animal head, {kv(F['huvud_vy']['kappa'], False)} for which way the head faces, {kv(F['oga']['kappa'], False)} for the eye and {kv(F['koppel']['kappa'], False)} for the koppel, that is, almost complete agreement. The lappets, the tail, the feet and the interlace lay between {kv(min(LAG), False)} and {kv(max(LAG), False)}, which is usually counted as good agreement.

Agreement is still not enough. A feature that both readers can rarely see says little, even if they agree the few times they see it. So we decided in advance, before the codes were compared with anything, that a field may be used only if kappa is at least 0.40 and both readers can give a value on at least 30 percent of the stones. Three fields fell: the mouth, readable on only {pc(F['mun']['tackning'])} percent of the stones; how head and tail meet, where kappa was only {kv(F['huvud_svans']['kappa'], False)}; and the band's outlines, which did not vary at all. The head's details could be read on a third to just over half of the stones. {N_UTAN_BILD} stones had no usable picture, and {N_KODAD} received enough agreed features to be compared.

## Three kinds of picture, tested against each other

Agreement is not the same as being right. Two readers can agree on the same mistake, especially when reading a poor picture. So we test each new kind of picture against another before it may be used. We have three: the plate photos in *Sveriges runinskrifter*, the old drawings of the seventeenth and eighteenth centuries, and depth images we compute from open 3D scans. The rule is written down in advance for all three: a feature may be read from a kind of picture if it agrees with the plate photo with a kappa of at least 0.40, measured on at least 15 stones. Nor is the plate photo the truth; it is another rendering of the same stone. What we measure is whether two pictures of the same stone say the same thing.

**The drawings.** Many runestones have vanished and survive only as drawings: in *Bautil*, a collection of woodcuts cut in the seventeenth century and not printed until 1750, by Johannes Rhezelius in the 1630s and by Johan Peringskiöld around 1700. We tested the drawings on {N_TECKN} surviving stones that have both an old drawing and a plate photo. The sample drew 140 drawings, but some stones came in under more than one draughtsman. Two new readers coded the drawings without seeing the photographs, and they agreed as well as on the photographs, with kappa between {kv(min(LT), False)} and {kv(max(LT), False).replace('1.00', '1')}.

The draughtsmen rendered the animal's main features faithfully. Against the plate photo, whether the animal has a head agreed with a kappa of {kv(KT['djurhuvud'], False)}, which way the head faces {kv(KT['huvud_vy'], False)}, the neck lappet {kv(KT['nackflik'], False)}, the koppel {kv(KT['koppel'], False)}, the cross {kv(KT['kors'], False)}, the interlace {kv(KT['flatverk'], False)} and the number of animals {kv(KT['antal_djur'], False)}. The tail ({kv(KT['svans'], False)}) and the eye ({kv(KT['oga'], False)}) agreed moderately but passed the rule. The lip lappet ({kv(KT['lappflik'], False)}) and the feet ({kv(KT['fotter'], False)}) did not, so they are never read from a drawing. The numbers are small: the neck lappet agreed on {NP_LIKA} of {len(NP)} stones, but only {NP_FLIK} of them had a lappet at all.

**The depth images.** The Swedish National Heritage Board has published 3D scans of runestones under a free licence. From them Vitki computes a depth image: the stone's surface minus a smoothed version of it, so that carved lines turn dark, rather like a stone in raking light. It looked like a good route to the stones that lack a plate photo. We tested it on {N3} scanned stones with plate codes.

It did not hold. The readers were already less sure among themselves than on photographs, with kappa {kv(min(L3), False)}–{kv(max(L3), False)} for the head's features. Against the plate photo the animal head agreed with a kappa of {kv(D3['djurhuvud']['kappa'], False)}, the view of the head {kv(D3['huvud_vy']['kappa'], False)}, the eye {kv(D3['oga']['kappa'], False)} and the number of animals {kv(D3['antal_djur']['kappa'], False)}, in other words hardly better than chance. The tail could not be read at all. Koppel, extra serpent and cross agreed completely and the interlace moderately ({kv(D3['flatverk']['kappa'], False)}), but only the extra serpent had the 15 stones the rule requires. By the rule, then, only "extra serpent" may be read from the depth images.

![Drawing and depth image of Sö 112]({FIG['djupbild_so112_en']})
Figure: Vitki. Sö 112 at Kolunda in Stenkvista parish, in the woodcut in Bautil and in the depth image from the 3D scan. On the plate photo the readers agreed that the heads are seen from above; in the depth image they agreed just as firmly on a head in profile. Left: woodcut number 748 in Johan Göransson's *Bautil* (1750), {BAUTIL_EN}. Right: depth image computed in Vitki from the scan of Sö 112 (file {SCAN_FILE}) by Laila Kitzler Åhfeldt, Swedish National Heritage Board, in the research project Runristandets dynamik (2009–2014), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), doi:{DS['doi']}.

Sö 112 shows why. The depth image shows weathering and cracks as clearly as the shallow ornament lines, and the readers could not tell head, eye and tail from the background. This applies to this particular computation, not to the 3D scans as such. An image with raking light from several directions can be tested later, with a new locked source check. Until then the result is negative, and it stands.

**Hälsingland and Medelpad.** Their stones are not among the plates we have read, so there we read free photographs of the painted stones instead. {HSM['kodade']} stones were coded, and the {len(FOTO)} that have such a photograph are now in the register with {min(v['fält'] for v in FOTO.values())}–{max(v['fält'] for v in FOTO.values())} features each. Stones with only a depth image get only the extra-serpent field and in practice do not count.

## Locked plans, gate and final test

The greatest risk in work like this is to keep looking until you find something. So every analysis is written down and locked before the codes are compared with what they are to be tested against. The plan says what is to be measured, how, and what counts as holding, and it may not be changed afterwards.

The test of the carvers shows how this works. We had a model that proposes groups of runestones that may have been made by the same hand, even when no carver has a name, and the question was whether the rune animal's features make the groups better. The runologists' statements about "the same carver" are the answer key, split at random in two. We may work with one part. The other, the test part, is opened at most three times, and only when an improvement has first passed a gate on the first part.

The gate held. Stones that the runologists say share a carver resemble each other more in the animal's features than neighbouring stones at the same distance. Measured over {M2['G1']['grupper']} groups, the typical pair ranked above two thirds of the neighbouring stones, and a pattern this clear arises by chance fewer than one time in 500. Nor did the model lose anything by getting the features. Then the test part was opened, for the second time. There it did not hold: of {O1['grupper']} groups, {O1['grupper'] - O1['med_skillnad']} stayed unchanged, {O1['bättre']} got better and {O1['sämre']} worse. As the plan says, Vitki therefore keeps the old model. The ornament carries traces of the hand, but most of what it can add the model already sees in the style group, the cross form and the editors' words about the ornament. The test part has one opening left, and it is being saved.

## What the method showed about Gräslund's styles

The first locked test of Gräslund's division covered {F1['stenar']} stones with at least three agreed features and a style group in Rundata. A statistical model learned the relationship on the stones in four fifths of the parishes and guessed the style group in the last fifth, five times over, so that no stone was judged by a model that had seen it or its neighbours in the same parish. It put {pc(F1['träffsäkerhet'])} percent of the stones in the right group. Someone who always guesses the most common group, Pr4, is right {pc(F1['vanligaste_gruppen'])} percent of the time. When we shuffled the style groups at random and repeated everything 999 times, none of the shuffles reached the model's score.

{chart(False)}

RAK, Pr4 and Fp are recognised well. The view of the head does much of the work for Fp: of the {sum(FPV.values())} Fp stones where the readers agreed on the head, it was seen from above on {FPV['uppifran']}. Pr1, Pr2 and Pr3 are recognised on only between one in five and two in five stones, and Pr5 not at all: all Pr5 stones but four become Pr4.

The errors do not fall at random. Of the {F2['fel_inom_Pr']} stones given the wrong Pr group, {F2['avstånd']['1']} landed one step away, {F2['avstånd']['2']} two steps and only {F2['avstånd']['3']} three steps away: {pc(F2['andel_till_granne'])} percent with the nearest neighbour. Had the errors fallen at random, about {pc(F2['omblandning_medel'])} percent would still have landed with a neighbour, since most Pr groups have two neighbours among only four others, and none of 999 shuffles reached {pc(F2['andel_till_granne'])}. The Pr groups thus behave as an ordered sequence, in line with Gräslund's idea that they follow one another.

When the features themselves were allowed to show what groups they form, with a model that was not told the style groups, there were three:

- **No animal head and no interlace:** 191 stones, of which {K[191]['RAK']} RAK and {K[191]['Fp']} Fp.
- **One animal with a simple head, round eye and spiral tail, without lappets and mostly without a koppel:** 134 stones, mostly Fp ({K[134]['Fp']}), Pr2 ({K[134]['Pr2']}), Pr1 ({K[134]['Pr1']}) and Pr3 ({K[134]['Pr3']}).
- **Head in profile, almond eye, koppel and usually an extra serpent:** 295 stones, mostly Pr4 ({K[295]['Pr4']}) and Pr3 ({K[295]['Pr3']}).

These are Gräslund's main lines, but not her seven groups. Where the fine division ends shows where the method needs to improve. The Pr groups are told apart above all by the lappets at neck and lips, and the neck lappet lacks an agreed value on {pc(min(NACK))}–{pc(max(NACK))} percent of the stones in Pr2–Pr5, the lip lappet on {pc(min(LAPP))}–{pc(max(LAPP))} percent. That is not because the stones lack lappets, but because the lappets cannot be read with certainty in a photograph of the whole stone. Whether the Pr groups are five separate groups or a sliding continuum, the test therefore cannot yet decide.

## What the codes are already used for

The source check makes it possible to read the vanished stones. {len(FB)} lost stones have a drawing from the sixteenth to the eighteenth century. {len(LOST_READ)} drawings could be read, and {len(FL)} stones received at least one approved feature, {N_LOST3} of them at least three, {KALLA['Bautil']} from Bautil. Only the features that passed the source check are included, and every code is marked with the drawing it comes from. {N_UTAN_STIL} of the {len(FL)} stones have no style group at all in Rundata. The register also gained {KK['gotland_öland_kodade']} stones from the plates of Gotland and Öland and the {len(FOTO)} from Hälsingland and Medelpad.

## The weaknesses

- **Rundata's style group is not the truth.** It is the experts' application of Gräslund's criteria. When the codes and Rundata disagree, the fault may lie with the codes, with the assignment or with the division.
- **The two readers are the same model.** They read independently of each other, but they may share blind spots. That is why every kind of picture is tested against another, and why we want a third reader.
- **The readers may recognise well-known stones** despite the instruction.
- **Only half the stones are depicted** on the plates, and the head's details show on only a third to just over half of them.
- **The style test was expected to hold,** since the groups were once set by the same kind of features. What tells us something is the pattern in the errors.

## Next steps

The next step is to see better. We will read the heads in their own crops rather than on the whole stone, give the readers an example sheet with Gräslund's own head types and let a third reader decide when two disagree. The depth images may get a new chance with raking light from several directions, under a new locked plan. Only when the lappets can be read on more stones can the question of five groups or a sliding sequence be tested properly. Then comes time: does the order hold against dates that do not rest on style?

Anyone with a runestone nearby can try the codebook themselves. Look at the head. Is it seen from the side or from above? Is there a lappet at the neck, and does it curl up? Answer "uncertain" when you cannot see for sure. It is the hardest rule and the most important.

## About the scan

The depth image of Sö 112 is computed in Vitki from the file {SCAN_FILE}, used as published. The scan was made by the runologist Laila Kitzler Åhfeldt at the Swedish National Heritage Board in the research project *Runristandets dynamik* (The dynamics of rune carving, 2009–2014), with an ATOS I scanner (GOM, structured light); only the inscribed surface is scanned. It was published openly on Zenodo in 2024 in the dataset *3D-data Runstenar i Södermanland / Runestones in Södermanland*, under the licence [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Kitzler Åhfeldt has written about the scans and the carvers, among other places in 2015 and 2017. Our thanks to Laila Kitzler Åhfeldt for making the scans freely available.

:::box The essentials in brief
- The rune animal can be measured: a fixed codebook, two independent readers and a rule for which features may be used turn the ornament into codes that can be counted.
- Every kind of picture is tested against another before it is used. The old drawings hold for the animal's main features but not for the lip lappets, and the depth images from the 3D scans do not hold for the head at all.
- Locked plans and a test part opened at most three times mean that negative outcomes stand too.
- As a test, the codes carry Gräslund's main lines. The fine division within Pr awaits a better reading of the lappets.
:::

## Sources

Kitzler Åhfeldt, L. 2024. *3D-data Runstenar i Södermanland / Runestones in Södermanland* [Dataset]. Swedish National Heritage Board. [https://doi.org/{DS['doi']}](https://doi.org/{DS['doi']}). Kitzler Åhfeldt, L. 2015. Rune Carvers and Local Mobility. *Viking and Medieval Scandinavia* 11, pp. 143–182. Kitzler Åhfeldt, L. 2017. *Runristare och mobilitet i Södermanland* [Rune carvers and mobility in Södermanland]. Stockholm: Swedish National Heritage Board. Gräslund, A.-S. 2006. Dating the Swedish Viking-Age rune stones on stylistic grounds. In: M. Stoklund et al. (eds), *Runes and their Secrets: Studies in Runology*. Copenhagen: Museum Tusculanum Press, pp. 117–139. Scandinavian Runic-text Database (Rundata) 3.1, Uppsala University. *Sveriges runinskrifter*, Swedish National Heritage Board (plates and text volumes, read but not reproduced). Göransson, J. 1750. *Bautil*. Stockholm; {BAUTIL_EN}. The locked analysis plans (2026-11-24 and 2026-11-25), the codebook and the results are in Vitki's open code repository."""

body = body.replace(f"{N_PLANSCH:,}", "1 170").replace(f"{N_KORPUS:,}", "2 314")

# ---- kontroller ---------------------------------------------------------------------------------------------------------
HOLDBACK = re.compile(r"\bAI\b|signifikan|p-värde|p-value|bootstrap|\bHolm\b", re.I)
PRONOUN = re.compile(r"\b(han|hon|hans|hennes|honom|he|she|his|him|her)\b", re.I)
labels = ["Metod", "Datering och stil", "Huggspår och 3D", "Ristare"]
assert blog_labels.check(labels) is None, blog_labels.check(labels)
for b, lang in ((body, "sv"), (body_en, "en")):
    assert not HOLDBACK.search(b), (lang, HOLDBACK.search(b).group(0))
    assert not re.search(r"^\s*\|", b, re.M)
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M))
    assert "{" not in b and "}" not in b
    assert b.index("Det viktigaste i korthet" if lang == "sv" else "The essentials in brief") < b.index("## Källor" if lang == "sv" else "## Sources")
    lines = b.splitlines()
    caps = [lines[i + 1] for i, ln in enumerate(lines) if ln.startswith("![")]
    assert len(caps) == 2 and all(c.startswith("Figur: Vitki." if lang == "sv" else "Figure: Vitki.") and "Bautil" in c and "Umeå" in c for c in caps)
    assert "Kitzler Åhfeldt" in caps[1] and "CC BY 4.0" in caps[1] and DS["doi"] in caps[1]
    assert ("djupbild beräknad i Vitki" if lang == "sv" else "depth image computed in Vitki") in caps[1]
    assert "Claude Opus" in caps[0] and b.count("Claude") == 4  # metoddelen + bildtexten till läsningsfiguren
    box = b[b.index(":::box"):b.index(":::", b.index(":::box") + 3)]
    assert "Claude" not in box and "insikt" not in box.lower() and "nyhet" not in box.lower()
    # inga könade pronomen (Gräslunds "hennes"/"her" om indelningen är tillåtet)
    assert all(m.group(0).lower() in ("hennes", "her") for m in PRONOUN.finditer(b)), (lang, [m.group(0) for m in PRONOUN.finditer(b)])
assert "1 170" in body and "1,170" in body_en
OUT = {"slug": SLUG, "title": title, "summary": summary, "body": body, "title_en": title_en, "summary_en": summary_en,
       "body_en": body_en, "labels": labels}
path = os.path.join(ROOT, "utdata", "blogg", "ornamentik.json")
json.dump(OUT, open(path, "w"), ensure_ascii=False, indent=1)
print(path, len(body.split()), "ord sv,", len(body_en.split()), "words en")

if "--update" in sys.argv or "--write" in sys.argv:
    from api.routers import blog
    col = blog.firestore().collection(blog.COLLECTION)
    now = dt.datetime.now(dt.timezone.utc)
    if "--update" in sys.argv:
        doc = sys.argv[sys.argv.index("--update") + 1]
        ref = col.document(doc)
        old = ref.get().to_dict()
        # Utkastet byter adress (metodikartikel): bara det opublicerade utkastet med den gamla eller nya adressen skrivs över
        assert old and not old.get("published") and old.get("slug") in (SLUG, "rundjuren-som-bara-finns-kvar-pa-papper"), \
            "Bara det opublicerade utkastet skrivs över härifrån"
        assert not [p for p in blog._all() if p.get("slug") == SLUG and p.get("id") != doc], "Adressen används redan"
        ref.set({**OUT, "topic": "Datering och stil|ornamentik metod", "updatedAt": now}, merge=True)
        print("uppdaterat utkast:", doc, SLUG)
    else:
        assert not [p for p in blog._all() if p.get("slug") == SLUG], "Adressen används redan; skriv över med --update"
        ref = col.document()
        ref.set({**OUT, "published": False, "month": now.strftime("%Y-%m"), "author": "Viktor Kvant",
                 "topic": "Datering och stil|ornamentik metod", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id, SLUG)
    blog._forget()
