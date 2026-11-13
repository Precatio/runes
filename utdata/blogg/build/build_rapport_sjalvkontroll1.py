"""Forskningsrapport (låst mall utdata/rapporter/MALL.md, version 4; Delvis prövat fynd): den första samlade
självkontrollen, "Fyra runstensfynd prövade mot hundra års invändningar – två står, ett försvagas, ett väntar på
kartorna" (sv + en; arbetsnamn "Vitki prövar sina egna resultat I"). Planerad publicering 15 december 2026
(PUBLICERINGSPLAN.md); Viktor publicerar själv, byggaren publicerar aldrig.

Fyra publicerade eller färdigskrivna resultat prövades 2026-11-10 under fem låsta planer, utlösta av invändningar i
Fornvännen och Futhark:
  1. östandelen utan Ingvarståget   analysplaner/2026-11-10-sjalvkontroll-osterled.md (4d00080) → utdata/varlden/sjalvkontroll/
  2. grupperna vid gravfälten       analysplaner/2026-11-10-sjalvkontroll-gravfalt.md (bc7da76) → utdata/familjens_plats/sjalvkontroll/
  3. stenarna vid lerans kant       analysplaner/2026-11-10-lerkanten-kontroller.md (c50b452) → utdata/palm_jordarna/kontroller*.json
  4. ristningen mot vägen           analysplaner/2026-11-10-sjalvkontroll-riktning.md (b3133a0) och
                                    analysplaner/2026-11-10-riktning-vaglinjer.md (ee90f3e) → utdata/riktning/
Varje tal läses ur resultatfilerna och låses med assert. Varje invändning citeras ur Fornvännens fria fulltext (OCR i
downloads/tidskrifter/fornvannen/text) och kontrolleras sida för sida: fragmentet måste stå på den tryckta sida som
texten anger. Vägavsnittet är OFULLSTÄNDIGT: provet L2 (Häradsekonomiska kartan, Viktors blinda avritning) är inte gjort,
och vägrapporten får sin nya version först efter L2 (Viktor 2026-11-10). Ingen slutlig dom om vägen formuleras här.

Formen: mallen version 4 har ingen egen form för en samlad självkontroll; rapporten märks "Delvis prövat fynd" (ett
resultat försvagat, ett prov inte gjort). Rapportversionens datum är skrivdagen; byt TODAY till publiceringsdagen om
Viktor vill det, innan han publicerar.
    ../../../.venv/bin/python build_rapport_sjalvkontroll1.py [--write | --update DOC]
Utan flaggor skrivs bara utdata/rapporter/rapport_sjalvkontroll1.json."""
import csv
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_labels  # noqa: E402

J = lambda *p: json.load(open(os.path.join(ROOT, *p), encoding="utf-8"))  # noqa: E731
APP_VERSION = "3.1.0"  # the Vitki version the checks were run in (tag v3.1.0 + the commits named in Data och kod)
SITE = "https://vitkirunor.se"
MALL_SHA = open(os.path.join(ROOT, "utdata", "rapporter", "MALL.md.sha256")).read().split()[0]
assert MALL_SHA.startswith("611a4d5f")  # mallens version 4
assert hashlib.sha256(open(os.path.join(ROOT, "utdata", "rapporter", "MALL.md"), "rb").read()).hexdigest() == MALL_SHA
REPORT_VERSION = 1
TODAY = "2026-12-15"  # rapportversionens datum, fast i byggaren

# ---- the five locked plans: checksum file, the file itself unchanged, the lock commit -----------------------------------
PLANS = {  # plan file: (sha256 prefix, lock commit)
    "2026-11-10-sjalvkontroll-osterled": ("656b0c99", "4d00080"),
    "2026-11-10-sjalvkontroll-gravfalt": ("8fb876c2", "bc7da76"),
    "2026-11-10-lerkanten-kontroller": ("f88ff01f", "c50b452"),
    "2026-11-10-sjalvkontroll-riktning": ("3ef2c79f", "b3133a0"),
    "2026-11-10-riktning-vaglinjer": ("ecf9039e", "ee90f3e"),
}
PTXT = {}
for f, (pre, commit) in PLANS.items():
    sha = open(os.path.join(ROOT, "analysplaner", f + ".sha256")).read().split()[0]
    raw = open(os.path.join(ROOT, "analysplaner", f + ".md"), "rb").read()
    assert sha.startswith(pre) and hashlib.sha256(raw).hexdigest() == sha, f
    PTXT[f] = re.sub(r"\s+", " ", raw.decode("utf-8"))
SHA = {f: pre for f, (pre, _) in PLANS.items()}
# the rules quoted in section 2, as the plans state them
assert "**Håller:** intervallets nedre gräns > 50 %." in PTXT["2026-11-10-sjalvkontroll-osterled"]
assert "**Försvagat (obestämt):** punktskattningen > 50 % men intervallet omfattar 50 %." in PTXT["2026-11-10-sjalvkontroll-osterled"]
assert "Kräver minst 20 platser (Σ(Ö + V)) i både tidig och sen grupp" in PTXT["2026-11-10-sjalvkontroll-osterled"]
assert ("**Står sig:** oddskvot > 1, Holm-p < 0,05, och i båda halvorna oddskvot > 1 med p < 0,05"
        in PTXT["2026-11-10-sjalvkontroll-gravfalt"])
assert "**Det publicerade resultatet står sig** om K1, K3a och K3b alla står sig." in PTXT["2026-11-10-sjalvkontroll-gravfalt"]
assert "”Kanten” = inom 200 m från lera och silt som var land år 1050" in PTXT["2026-11-10-lerkanten-kontroller"]
assert "(block om 20 km, som tidigare)" in PTXT["2026-11-10-lerkanten-kontroller"]
assert ("Ett prov **håller** när medel-cos ligger över det väntade och p < 0,05. Ingen korrigering för flera prov"
        in PTXT["2026-11-10-sjalvkontroll-riktning"])
assert "Kräver minst 30 stenar; annars \"kan inte prövas\"." in PTXT["2026-11-10-sjalvkontroll-riktning"]
assert "**K godkänd** om andelen är minst 70 procent." in PTXT["2026-11-10-riktning-vaglinjer"]
assert "andelen inom 45 grader är minst 40 procent" in PTXT["2026-11-10-riktning-vaglinjer"]
assert "Holm-korrigerat p < 0,05 (över L1 och L2" in PTXT["2026-11-10-riktning-vaglinjer"]
assert "Avritare A är Viktor" in PTXT["2026-11-10-riktning-vaglinjer"]

# ---- code state: every lock commit and every result file committed and unchanged -----------------------------------------
RESULTS = {  # result file: the commit that wrote it
    "utdata/varlden/sjalvkontroll/resultat.json": "c43111a", "utdata/varlden/sjalvkontroll/tid_resultat.json": "c43111a",
    "utdata/varlden/sjalvkontroll/ingvarsstenar.csv": "c43111a",
    "utdata/familjens_plats/sjalvkontroll/resultat.json": "4e68592", "utdata/familjens_plats/sjalvkontroll/p0.json": "4e68592",
    "utdata/familjens_plats/sjalvkontroll/klasser.csv": "4e68592",
    "utdata/palm_jordarna/kontroller.json": "66730c3", "utdata/palm_jordarna/kontroller_R.json": "66730c3",
    "utdata/riktning/sjalvkontroll.json": "d2efcd1", "utdata/riktning/vaglinjer.json": "105bb8c",
}


def git(*a):
    return subprocess.run(["git", "-C", ROOT, *a], capture_output=True, text=True)


if os.path.isdir(os.path.join(ROOT, ".git")):
    for _, c in PLANS.values():
        assert git("merge-base", "--is-ancestor", c, "HEAD").returncode == 0, c
    for f, c in RESULTS.items():
        assert git("ls-files", "--error-unmatch", f).returncode == 0, f
        assert not git("status", "--porcelain", "--", f).stdout.strip(), f"ändrad efter körningen: {f}"
        assert git("log", "-1", "--format=%h", "--", f).stdout.strip().startswith(c), f

# ---- formatting -----------------------------------------------------------------------------------------------------------
pc = lambda x: round(100 * x)  # noqa: E731


def nf(x, nd=0, en=False):
    """A number in the text: comma in Swedish, a real minus sign."""
    s = f"{abs(x):.{nd}f}"
    return ("−" if x < 0 and float(s) != 0 else "") + (s if en else s.replace(".", ","))


def th(n, en=False):
    """A whole number with thousands separated: 18 633 in Swedish, 18,633 in English."""
    return f"{n:,}".replace(",", "," if en else "\u00a0")


def pp(x, en=False):  # a difference in percentage points, with sign
    v = 100 * x
    return ("+" if v > 0 else "") + nf(v, 1, en)


def ci_pp(c, en=False):
    return f"[{pp(c[0], en)}; {pp(c[1], en)}]" if not en else f"[{pp(c[0], en)}, {pp(c[1], en)}]"


# ==== 1. The east share without the Ingvarr expedition ================================================================
OST = J("utdata", "varlden", "sjalvkontroll", "resultat.json")
assert OST["plan"] == "analysplaner/2026-11-10-sjalvkontroll-osterled.md"
P1 = OST["p1"]
assert P1["dom"] == "försvagat (obestämt)"
O_ALL, O_UI, O_B = P1["alla"], P1["utan_ingvar"], P1["beskrivande"]
N_ING = P1["antal_ingvarsstenar"]
assert N_ING == len(P1["ingvarsstenar"]) == P1["antal_ingvar_med_plats"] == 25
ING_CAND = list(csv.DictReader(open(os.path.join(ROOT, "utdata", "varlden", "sjalvkontroll", "ingvarsstenar.csv"), encoding="utf-8")))
assert len(ING_CAND) == 26 and [r["signum"] for r in ING_CAND if r["borttagen"]] == ["U 540"]
assert "U 540" not in P1["ingvarsstenar"]
O_P, O_LO, O_HI = pc(O_ALL["ostandel"]), pc(O_ALL["ci"][0]), pc(O_ALL["ci"][1])
U_P, U_LO, U_HI = pc(O_UI["ostandel"]), pc(O_UI["ci"][0]), pc(O_UI["ci"][1])
assert (O_P, O_LO, O_HI, U_P, U_LO, U_HI) == (66, 58, 74, 58, 49, 67)
assert O_UI["ci"][0] < 0.5 < O_UI["ostandel"], "försvagat: punktskattningen över hälften, intervallet omfattar hälften"
O_N, U_N = O_ALL["stenar"], O_UI["stenar"]
assert (O_N, U_N, int(O_ALL["O"]), int(O_ALL["V"]), int(O_UI["O"]), int(O_UI["V"])) == (136, 111, 102, 53, 72, 52)
OST_STONES, OST_ING = P1["oststenar"]["alla"], P1["oststenar"]["varav_ingvar"]
assert (OST_STONES, OST_ING) == (90, 25)
SURPLUS, DROP = pc(O_ALL["ostandel"] - 0.5), pc(O_ALL["ostandel"] - O_UI["ostandel"])
assert (SURPLUS, DROP) == (16, 8) and round(P1["skillnad_pe"], 1) == -7.7  # "ungefär hälften av övervikten"
NARROW, ONE = O_B["smal_definition"], O_B["ingvar_som_en_text"]
assert (pc(NARROW["ostandel"]), pc(NARROW["ci"][0]), pc(NARROW["ci"][1]), NARROW["antal"]) == (59, 50, 68, 23)
assert (pc(ONE["ostandel"]), pc(ONE["ci"][0]), pc(ONE["ci"][1])) == (59, 50, 67)
SAG = O_B["sagor_publicerade"]
FA, HK, IS = SAG["fornaldarsagor"], SAG["heimskringla"], SAG["islanningasagor"]
assert O_UI["ci"][0] > HK["ci"][1] and O_UI["ci"][0] > IS["ci"][1], "utan Ingvar: ingen överlappning med Heimskringla och islänningasagorna"
assert pc(FA["ostandel"]) == U_P == 58 and (pc(HK["ostandel"]), pc(IS["ostandel"])) == (39, 29)
P2 = OST["p2"]["huvud_med_ingvar"]
assert P2["dom"] == "för få träffar" and not P2["enough"] and P2["platser"]["sen"] == 18 and P2["platser"]["tidig"] == 89
assert OST["p2"]["huvud_utan_ingvar"]["dom"] == "för få träffar"
P2_OR, P2_CI = P2["or"], P2["ci"]
assert (nf(P2_OR, 2), nf(P2_CI[0], 2), nf(P2_CI[1], 2)) == ("0,88", "0,25", "3,11")

# ==== 2. Stone groups at grave fields ==================================================================================
GRV = J("utdata", "familjens_plats", "sjalvkontroll", "resultat.json")
P0F = J("utdata", "familjens_plats", "sjalvkontroll", "p0.json")
assert GRV["plan"] == "analysplaner/2026-11-10-sjalvkontroll-gravfalt.md" and GRV["helhet"] == "står sig"
assert P0F["reproducerar"] and P0F["identiskt_utfall"] and P0F["stenar_csv_identisk"]
G0 = GRV["original_omkord"]
assert G0 == {**P0F["publicerat"], **{k: G0[k] for k in ("grupp_med", "grupp_utan", "ensam_med", "ensam_utan")}}
G_N, G_GR, G_EN = G0["n"], G0["grupp_med"] + G0["grupp_utan"], G0["ensam_med"] + G0["ensam_utan"]
assert (G_N, G_GR, G_EN) == (657, 185, 472)
assert (pc(G0["share_grupp"]), pc(G0["share_ensam"]), nf(G0["or"], 2), nf(G0["lo"], 2), nf(G0["hi"], 2)) == (82, 55, "2,38", "1,50", "3,78")
assert round(G0["p"], 5) == 0.00023
GT = GRV["tests"]
for k in ("K1", "K2", "K3a", "K3b"):
    t = GT[k]
    assert t["bedomning"] == "står sig" and t["main"]["or"] > 1 and t["p_holm"] < 0.05, k
    assert all(t["halves"][h]["or"] > 1 and t["halves"][h]["p"] < 0.05 for h in "AB"), k
ORS = [GT[k]["main"]["or"] for k in ("K1", "K2", "K3a", "K3b")]
assert (nf(min(ORS), 1), nf(max(ORS), 1)) == ("2,3", "2,6")
K1, K2, K3A, K3B = (GT[k]["main"] for k in ("K1", "K2", "K3a", "K3b"))
assert (pc(K1["share_grupp"]), pc(K1["share_ensam"])) == (73, 43)  # "sju av tio mot fyra av tio" in the plain-words sentence
assert (round(10 * K1["share_grupp"]), round(10 * K1["share_ensam"])) == (7, 4)
assert (pc(K2["share_grupp"]), pc(K2["share_ensam"])) == (33, 15)  # resultat.md says 16 % – the JSON (0.1547) rounds to 15
assert (pc(K3A["share_grupp"]), pc(K3A["share_ensam"])) == (82, 55)
GR_ROB = GRV["robusthet"]
assert (pc(GR_ROB["K1_250m"]["share_grupp"]), pc(GR_ROB["K1_250m"]["share_ensam"])) == (48, 27)
assert (pc(GR_ROB["K1_utan_block"]["share_grupp"]), pc(GR_ROB["K1_utan_block"]["share_ensam"])) == (70, 42)
US_ORS = [GT[k]["U_So"]["or"] for k in ("K1", "K2", "K3a", "K3b")]
assert all(GT[k]["U_So"]["p"] < 0.002 for k in ("K1", "K2", "K3a", "K3b"))
KL = {(r["grupp"], r["nyckel"]): int(r["antal"]) for r in csv.DictReader(open(os.path.join(
    ROOT, "utdata", "familjens_plats", "sjalvkontroll", "klasser.csv"), encoding="utf-8")) if r["antal"].isdigit()}
G_ALL, G_V, G_Y = KL[("totalt", "gravfält i lamningar.csv")], KL[("klass", "V granskat gravfält")], KL[("klass", "Y yngre järnålderns former")]
assert (G_ALL, G_V, G_Y, KL[("totalt", "utan detaljer")]) == (18633, 10789, 2550, 0)
assert (pc(G_V / G_ALL), pc(G_Y / G_ALL)) == (58, 14)
LAN = GRV["lan_hur"]
assert LAN["egen KMR-post"] == 653 and sum(LAN.values()) == G_N

# ==== 3. Stones at the clay edge =======================================================================================
LER, LERR = J("utdata", "palm_jordarna", "kontroller.json"), J("utdata", "palm_jordarna", "kontroller_R.json")
assert LER["plan"] == "analysplaner/2026-11-10-lerkanten-kontroller.md" and LER["sha256"].startswith(SHA["2026-11-10-lerkanten-kontroller"])
assert LER["K1"]["holds"] and LER["K4"]["holds"] and LER["K5"]["holds"] and LERR["K2_holds"] and LERR["K3_holds"]
H = LER["huvud"]
assert (H["n"], pc(H["on_clay"]), pc(H["on_clay_random"]), pc(H["edge"]), pc(H["edge_random"])) == (707, 28, 37, 52, 40)
for d in (H, LER["K1"]["med_forsvunna"], LER["K4"]["vatten_950"], LER["K5"]["utan_runor_flyttade"]):
    assert d["edge_diff_95"][0] > 0 and d["on_clay_diff_95"][1] < 0  # the rule: edge > 0, on the clay < 0, intervals clear of 0
assert (pp(H["on_clay_diff"]), pp(H["edge_diff"])) == ("−8,8", "+11,8")
assert round(2 * H["edge"]) == 1 and round(10 * H["edge_random"]) == 4  # "hälften … mot fyra av tio slumpplatser"
PJ = LER["K1"]["per_jordart"]
LOST = {k: pc(v["forsvunna"]) for k, v in PJ.items()}
MOVED = {k: pc(v["flyttade"]) for k, v in PJ.items()}
assert (LOST["lera och silt"], LOST["morän"], LOST["berg"], LOST["sand och grus"]) == (18, 18, 18, 20)
assert (MOVED["lera och silt"], MOVED["sand och grus"]) == (38, 60)
PEAT_N, PEAT_LOST = PJ["torv och gyttja"]["n"], round(PJ["torv och gyttja"]["forsvunna"] * PJ["torv och gyttja"]["n"])
assert (PEAT_N, PEAT_LOST) == (9, 4)
KF = LER["K1"]["med_forsvunna"]
N_LOST, DEFICIT = LER["K1"]["forsvunna_med_egen_plats_i_bygden"], round(LER["K1"]["underskott_pa_leran_antal_stenar"])
assert (KF["n"], N_LOST, DEFICIT) == (1024, 317, 62) and KF["n"] == H["n"] + N_LOST
assert abs(LER["K1"]["underskott_pa_leran_antal_stenar"] + H["n"] * H["on_clay_diff"]) < 0.01  # 707 × 8,8 procentenheter
K2E, K2S = LERR["K2_med_sand_och_grus"]["edge"], LERR["K2_med_sand_och_grus"]["sand200"]
K3E, K3P = LERR["K3_med_torv_och_gyttja"]["edge"], LERR["K3_med_torv_och_gyttja"]["peat200"]
assert (nf(K2E["or"], 2), nf(K2S["or"], 2), nf(K3E["or"], 2), nf(K3P["or"], 2)) == ("1,70", "1,31", "1,70", "0,34")
assert K2E["p_one_sided_pos"] < 0.001 and K3E["p_one_sided_pos"] < 0.001 and round(K2S["p_one_sided_pos"], 3) == 0.013
assert LERR["n_stenar"] == H["n"] and LERR["n_platser"] == 36057
K4W, K5R = LER["K4"]["vatten_950"], LER["K5"]["utan_runor_flyttade"]
N_RUNOR_MOVED = LER["K5"]["borttagna"]
assert (N_RUNOR_MOVED, K5R["n"]) == (154, 571)
K6 = LER["K6"]
K6_CLAY_THIRDS = {pc(v["pa_leran"]) for v in K6["ord_tredjedel"].values()}
assert K6_CLAY_THIRDS == {28}
CLAY_THIRD = K6_CLAY_THIRDS.copy().pop()
assert (pc(K6["ornament"]["True"]["pa_leran"]), pc(K6["ornament"]["False"]["pa_leran"])) == (29, 25)
assert (pc(K6["cross"]["True"]["pa_leran"]), pc(K6["cross"]["False"]["pa_leran"])) == (31, 25)
EDGES6 = [pc(v["vid_kanten"]) for g in ("ord_tredjedel", "ornament", "cross") for v in K6[g].values()]
assert (min(EDGES6), max(EDGES6)) == (51, 54)

# ==== 4. The inscription faces the road (INCOMPLETE: L2 not done) =====================================================
RPUB = J("utdata", "riktning", "riktning.json")["resultat"]["alla"]["H2"]
RS, RL = J("utdata", "riktning", "sjalvkontroll.json"), J("utdata", "riktning", "vaglinjer.json")
assert RS["plan"] == "analysplaner/2026-11-10-sjalvkontroll-riktning.md" and RL["plan"] == "analysplaner/2026-11-10-riktning-vaglinjer.md"
assert (RPUB["n"], pc(RPUB["andel_inom_45"]), RPUB["p"]) == (123, 50, 0.0001)
S = RS["prov"]
assert [S[k]["haller"] for k in ("S0", "S1", "S2", "S3")] == [True, False, True, True]
assert [S[k]["n"] for k in ("S0", "S1", "S2", "S3")] == [120, 40, 118, 75]
assert [pc(S[k]["andel_inom_45"]) for k in ("S0", "S1", "S2", "S3")] == [48, 28, 49, 45]
assert S["S1"]["n"] >= 30 and round(S["S1"]["p"], 2) == 0.16 and round(1 / S["S1"]["p"]) == 6  # "ungefär en gång på sex"
assert all(S[k]["p"] == 0.0001 for k in ("S0", "S2", "S3"))
RI = RS["info"]
assert (RI["stenar"], RI["med_vag"], RI["flyttade"], RI["flyttade_med_vag"]) == (214, 120, 91, 45)
HALV = RS["beskrivande"]["halvor"]
assert all(HALV[h][k]["p"] < 0.05 for h in "AB" for k in ("S0", "S2", "S3")) and all(HALV[h]["S1"]["p"] > 0.05 for h in "AB")
LK, L0, L1 = RL["K"], RL["L0"], RL["L1"]
assert LK["godkand"] and (LK["n"], round(LK["andel_inom_45"] * LK["n"])) == (68, 48) and round(100 * LK["andel_inom_45"], 1) == 70.6
assert LK["andel_inom_45"] - 0.70 < 1 / LK["n"], "K klarade gränsen med en sten"
assert L0["grind_haller"] and (L0["a"]["n"], pc(L0["a"]["andel_inom_45"]), L0["a"]["p"]) == (213, 50, 0.0001)
assert (L0["b"]["n"], pc(L0["b"]["andel_inom_45"])) == (122, 46)
assert L1["status"] == "håller (oavsett L2)" and (L1["a"]["n"], pc(L1["a"]["andel_inom_45"])) == (34, 32)
assert round(L1["a"]["p"], 3) == 0.023 and L1["holm_p_ovre"] < 0.05 and round(L1["holm_p_ovre"], 3) == 0.045
assert round(1 / L1["a"]["p"]) == 44  # "ungefär en gång på 44"
assert (L1["b"]["n"], pc(L1["b"]["andel_inom_45"]), round(L1["b"]["p"], 3)) == (21, 38, 0.010)
assert RL["L2"].startswith("inte räknad")
LB = RL["beskrivande"]
assert (LB["L1_300"]["a"]["n"], pc(LB["L1_300"]["a"]["andel_inom_45"]), round(LB["L1_300"]["a"]["p"], 3)) == (24, 42, 0.032)
assert (LB["L1_1000"]["a"]["n"], pc(LB["L1_1000"]["a"]["andel_inom_45"]), round(LB["L1_1000"]["a"]["p"], 2)) == (60, 25, 0.38)
assert (pc(L0["tvars_a"]["andel_tvars"]), pc(L1["tvars_a"]["andel_tvars"])) == (64, 65)

# ---- the earlier publications this report checks --------------------------------------------------------------------------
DOIS = J("web", "content", "report_dois.json")["rapporter"]
DOI_FAM, DOI_VAG = DOIS["familjegrupper-vid-gravfalten"]["doi"], DOIS["ristningen-vand-mot-vagen"]["doi"]
assert (DOI_FAM, DOI_VAG) == ("10.5281/zenodo.24004794", "10.5281/zenodo.24004764")
LINKED = {"vikingarnas-varld": "artiklar", "osterled-eller-bara-ingvars": "artiklar", "runstenarna-foljde-leran": "artiklar",
          "familjegrupper-vid-gravfalten": "forskningsrapporter", "ristningen-vand-mot-vagen": "forskningsrapporter"}
U_SV = {s: f"{SITE}/{sec}/{s}" for s, sec in LINKED.items()}
U_EN = {s: f"{SITE}/en/{sec}/{s}" for s, sec in LINKED.items()}

# ---- the literature: every quotation checked on its printed page in Fornvännen's free full text --------------------------
FVT = os.path.join(ROOT, "..", "downloads", "tidskrifter", "fornvannen")
IDX = {}
for line in open(os.path.join(FVT, "index.jsonl"), encoding="utf-8"):
    d = json.loads(line)
    IDX.setdefault(d["key"], d)
JOUR = J("data", "cache", "literature", "journals.json")["articles"]
flat = lambda x: re.sub(r"\s+", "", x).replace("-", "").replace("—", "").replace("­", "")  # noqa: E731


def head(page):
    """The page number in a page's running head or foot, or None."""
    lines = [ln.strip() for ln in page.strip().splitlines() if ln.strip()]
    for ln in (lines[0], lines[-1]) if lines else ():
        n = re.match(r"^(\d{2,3})\b", ln) or re.search(r"\b(\d{2,3})$", ln)
        if n:
            return int(n.group(1))
    return None


def printed(key, idx, pages):
    """The printed page number of a pdftotext page: from the key's first page (year_first), else the running head; a
    head the OCR misread ('* 15' for 215) is taken from its neighbours when they are consecutive."""
    m = re.match(r"^\d{4}_(\d+)$", key)
    if m:
        return int(m.group(1)) + idx - 1
    h = head(pages[idx])
    prv = head(pages[idx - 1]) if idx > 1 else None
    nxt = head(pages[idx + 1]) if idx + 1 < len(pages) else None
    if prv and nxt and nxt - prv == 2 and h != prv + 1:
        return prv + 1
    assert h, f"ingen sidsiffra: {key} {idx}"
    return h


def check(key, page, *frags):
    """Every fragment must stand on the stated printed page; returns the free full text's address (CC BY 4.0)."""
    pages = open(os.path.join(FVT, "text", key + ".txt"), encoding="utf-8").read().split("\f")
    for f in frags:
        hits = [printed(key, i, pages) for i, p in enumerate(pages) if i > 0 and flat(f) in flat(p)]
        assert page in hits, (key, page, f, hits)
    assert IDX[key]["licence"] == "https://creativecommons.org/licenses/by/4.0/"
    url = IDX[key]["uri"]
    if key in JOUR:
        assert JOUR[key]["url"] == url, key
    return url


Q_SINDBAEK = "der alene tegner sig for mere end 25 sten"
# two-column OCR: a quotation that crosses a line break is checked line by line (the other column sits between)
URL_SINDBAEK = check("2003_179", 180, "kendes ikke mindre end 96 svenske runesten", "Det kaspiske Hav, der ale",
                     "ne tegner sig for mere end 25 sten")
Q_WESTIN = "Mot slutet av vikingatiden inträder emellertid en förskjutning."
URL_WESTIN = check("1941_085", 93, "De svenska vikingatågen voro huvudsakligen riktade mot öster.", Q_WESTIN)
Q_HAGG = "det är emellanåt synnerligen svårt att skilja ut vad som är gravanläggningar och vad som är röjningsrösen"
URL_HAGG = check("2002_litt_b", 217, "det är emellanåt synnerligen svårt att skilja ut", "vad som är gravanläggningar och vad som är",
                 "röjningsrösen. Detta kan exemplifieras med ett")
check("2002_litt_b", 218, "område i Vittenebygden där ett idag tydligt grav", "fält vid andragångsinventeringen 1983 regi",
      "strerades som röjningsröseområde")
check("2002_litt_b", 219, "Leif Häggström")
check("2002_litt_b", 215, "Odlingslandskap och uppdragsarkeologi", "Arkeologi och paleoekologi i sydvästra Småland")
Q_EK_AGE = "nära ett årtusende äldre än runstenen"
Q_EK_ROAD = "vänd mot den utan tvivel mycket gamla väg"
URL_EKHOLM = check("1950_137", 138, Q_EK_AGE, Q_EK_ROAD)
Q_EK_CLAY = "För övrigt ha runstenarna av detta slag ofta sin plats på lermarkerna"
Q_EK_TURN = "Att dess framsida numera är vänd mot järnvägen sammanhänger med dess nyresande under 1860-talet."
check("1950_137", 140, Q_EK_CLAY, "aldrig uppförda på lermarkerna utan på de moräner, som omge dessa", Q_EK_TURN,
      "har ett mycket långt syndaregister")
Q_SODERBERG = "åkerbruket på slätten resulterat i bortplöjning av förhistoriska gravar"
URL_SODERBERG = check("8ec5443b-49ad-4672-93a9-f57450e7a7c7", 264, "Som exempel har åkerbruket på slätten",
                      "resulterat i bortplöjning av förhistoriska gravar")
Q_LOVEN = "De långa åsarna skulle kunna betecknas som våra första riksvägar"
URL_LOVEN = check("41958e9a-bdf6-4d3c-ad0c-cb87bf3bab82", 299, "De långa åsarna skulle kunna betecknas som",
                  "våra första riksvägar, och de går att tillskriva", "var givetvis att de aldrig blev leriga")
Q_MYRDAL = "hävdade och rensade ängar eller sankmark"
URL_MYRDAL = check("1982_081", 97, Q_MYRDAL)
URL_LINDQ14 = check("1914_203", 215, "larens yta omkr. år 1040", "vid Ramsundsberget stod 4,5—5 m. ovan nutida havsytan")
Q_BERTH = "märkliga färdvägar, vägmärken, broar och liknande anläggningar upptagits bland fasta fornlämningar"
URL_BERTH = check("1944_111", 111, "Den 1 januari 1943 trädde den nya fornminneslagen i kraft", Q_BERTH)
Q_GUST = "Sedan 1932 hava 311 runstenar lagats eller rests."
URL_GUST = check("1941_243", 245, Q_GUST)
Q_SKOG = "Någon väg över mossen finns varken på denna karta eller på häradskartan från mitten av 1600-talet"
URL_SKOG = check("2002_073", 83, "Någon väg över mossen", "finns varken på denna karta eller på härads",
                 "kartan från mitten av 1600-talet")
Q_LINDQ28 = "Runstenarna ställdes så, att de lätt kunde bli lästa av förbifarande"
URL_LINDQ28 = check("1928_257", 281, Q_LINDQ28)
assert IDX["2003_179"]["authors"] == ["Sindbæk, Søren M."] and IDX["1941_085"]["authors"] == ["Westin, Gunnar"]
assert IDX["1950_137"]["authors"] == ["Ekholm, Gunnar"] and IDX["1944_111"]["authors"] == ["Berthelson, Bertil"]
assert IDX["1941_243"]["authors"] == ["Gustawsson, Karl Alfred"] and IDX["2002_073"]["authors"] == ["Skoglund, Peter", "Lagerås, Per"]
assert IDX["1982_081"]["authors"] == ["Myrdal, Janken"] and IDX["1914_203"]["authors"] == ["Lindqvist, Sune"] == IDX["1928_257"]["authors"]
assert IDX["41958e9a-bdf6-4d3c-ad0c-cb87bf3bab82"]["authors"] == ["Lovén, Christian"]
assert IDX["8ec5443b-49ad-4672-93a9-f57450e7a7c7"]["authors"] == ["Söderberg, Bengt", "Lagerås, Per", "Björk, Tony"]

# ---- title, timeline, citation --------------------------------------------------------------------------------------------
SLUG = "fyra-runstensfynd-mot-hundra-ars-invandningar"
title = "Fyra runstensfynd prövade mot hundra års invändningar – två står, ett försvagas, ett väntar på kartorna"
title_en = "Four runestone findings tested against a century of objections – two stand, one weakens, one awaits the maps"
CITE_EN = (f"Kvant, V. ({TODAY[:4]}). {title_en}. Research report, report version {REPORT_VERSION}; analysis in Vitki "
           f"{APP_VERSION}. {SITE}/en/forskningsrapporter/{SLUG}")
TL_SV = ("österns övervikt mättes under en låst plan 2026-10-28; studien av stengrupper vid gravfälten och studien av "
         "ristningens riktning låstes 2026-10-29; studien av jordarterna låstes 2026-11-08; mönstret vid lerans kant "
         "beskrevs 2026-11-09; genomläsningen av Fornvännen och Futhark inleddes 2026-11-09; de fem kontrollplanerna "
         "låstes och kördes 2026-11-10")
TL_EN = ("the eastern predominance was measured under a locked plan 2026-10-28; the study of stone groups at grave "
         "fields and the study of the inscription's direction were locked 2026-10-29; the soil study was locked "
         "2026-11-08; the pattern at the clay edge was described 2026-11-09; the reading of Fornvännen and Futhark began "
         "2026-11-09; the five check plans were locked and run 2026-11-10")
assert "*" not in TL_SV + TL_EN
summary = ("Fyra av projektets resultat om runstenarna prövades under låsta planer mot invändningar ur Fornvännen och "
           f"Futhark. Grupperna vid gravfälten och stenarna vid lerans kant står. Österns övervikt försvagas: utan de "
           f"{N_ING} Ingvarsstenarna ligger {U_P} procent av platserna i öster, inte {O_P}. Att ristningarna vetter mot "
           "vägen håller i tre av fyra kontroller och mot de gamla vägarnas linjer, men provet mot 1800-talets karta "
           "återstår.")
summary_en = ("Four of the project's results on the runestones were tested under locked plans against objections from "
              "Fornvännen and Futhark. The groups at the grave fields and the stones at the clay edge stand. The eastern "
              f"predominance weakens: without the {N_ING} Ingvarr stones, {U_P} per cent of the places lie in the east, "
              f"not {O_P}. That the inscriptions face the road holds in three of four checks and against the lines of the "
              "old roads, but the test against the 19th-century map remains.")
CHART_SV, CHART_EN = "Diagram: Vitki, efter", "Chart: Vitki, after"


def chart_grav(sv):
    rows = [":::chart Stenar med ett gravfält inom 500 m: i grupp och ensamma" if sv else
            ":::chart Stones with a grave field within 500 m: in groups and alone"]
    for lab_sv, lab_en, d in (("Alla registrerade gravfält (det publicerade)", "All registered grave fields (as published)", G0),
                              ("Bara granskade gravfält", "Only verified grave fields", K1),
                              ("Bara gravfält med yngre järnålderns former", "Only grave fields with Late Iron Age forms", K2)):
        rows.append(f"# {lab_sv if sv else lab_en}")
        rows.append(f"+{'I grupp' if sv else 'In a group'} | {pc(d['share_grupp'])} | {d['grupp_med']} {'av' if sv else 'of'} {G_GR}")
        rows.append(f"{'Ensamma' if sv else 'Alone'} | {pc(d['share_ensam'])} | {d['ensam_med']} {'av' if sv else 'of'} {G_EN}")
    rows.append(f"Källa: Rundata (ODbL), Kulturmiljöregistret via K-samsök (CC0). Råa andelar. {CHART_SV} Rundata och "
                "Kulturmiljöregistret." if sv else
                f"Source: Rundata (ODbL), the register of ancient monuments via K-samsök (CC0). Raw shares. {CHART_EN} Rundata "
                "and the register.")
    return "\n".join(rows) + "\n:::"


def chart_vag(sv):
    rows = [":::chart Ristningar som vetter inom 45 grader från vägen" if sv else
            ":::chart Inscriptions facing within 45 degrees of the road"]
    rows.append("# " + ("Riktningen till vägpostens punkt" if sv else "Bearing to the road record's point"))
    for k, lsv, len_ in (("S0", "En rad per sten", "One row per stone"), ("S2", "Jämfört inom län", "Compared within county"),
                         ("S3", "Utan flyttade och omresta stenar", "Without moved and re-erected stones"),
                         ("S1", "Bara gamla vägar", "Only old roads")):
        rows.append(f"{lsv if sv else len_} | {pc(S[k]['andel_inom_45'])} | {S[k]['n']} {'stenar' if sv else 'stones'}")
    rows.append("# " + ("Riktningen till vägens linje" if sv else "Bearing to the road's line"))
    rows.append(f"{'Dagens vägar' if sv else 'Present-day roads'} | {pc(L0['a']['andel_inom_45'])} | {L0['a']['n']} {'stenar' if sv else 'stones'}")
    rows.append(f"+{'Gamla vägar i registret' if sv else 'Old roads in the register'} | {pc(L1['a']['andel_inom_45'])} | {L1['a']['n']} {'stenar' if sv else 'stones'}")
    rows.append("# " + ("Om riktningen vore slumpvis" if sv else "If the direction were random"))
    rows.append(f"{'Väntat' if sv else 'Expected'} | 25 | {'en fjärdedel' if sv else 'one quarter'}")
    rows.append(f"Källa: Kulturmiljöregistret (CC0), OpenStreetMap (ODbL), Runor 2020, Rundata (ODbL). {CHART_SV} "
                "registret, OpenStreetMap och Rundata." if sv else
                f"Source: the register of ancient monuments (CC0), OpenStreetMap (ODbL), Runor 2020, Rundata (ODbL). {CHART_EN} "
                "the register, OpenStreetMap and Rundata.")
    return "\n".join(rows) + "\n:::"


S0_, S1_, S2_, S3_ = S["S0"], S["S1"], S["S2"], S["S3"]
G_OR_LO, G_OR_HI = nf(min(ORS), 1), nf(max(ORS), 1)
G_OR_LO_EN, G_OR_HI_EN = nf(min(ORS), 1, True), nf(max(ORS), 1, True)

# ======================================================================================================================
body = f"""*Viktor Kvant, oberoende forskare. Delvis prövat fynd. Rapportversion {REPORT_VERSION}, {TODAY}. Tidslinje: {TL_SV}. Analysen är gjord i Vitki {APP_VERSION}. Licens CC BY 4.0. Den engelska versionen är den kanoniska för citering: {CITE_EN}. Nyckelord: runstenar, vikingatid, självkontroll, Ingvarståget, gravfält, jordarter, vägar, Fornvännen. Konkurrerande intressen: inga. Finansiering: ingen.*

## Sammanfattning

**Vad som inte är prövat.** Ett av de fyra resultaten försvagades, och kontrollen av det fjärde är inte färdig: provet mot vägarna på 1800-talets häradsekonomiska karta återstår, och ingen slutlig dom om vägen ges här.

**Bakgrund och syfte.** Ett resultat är inte prövat förrän det har mött sina invändningar. Vi ställde fyra av projektets resultat om runstenarna mot invändningar ur Fornvännen och Futhark: att österns övervikt bärs av Ingvarståget (Sindbæk 2003), att registrets gravfält blandar gravar med röjningsrösen och är äldre än stenarna (Häggström 2002; Ekholm 1950), att stenarna vid lerans kant är de som plogen lämnade eller står vid åsvägar (Söderberg m.fl. 2021; Lovén 2021), och att registrets vägar är dagens och stenar vänts när de restes på nytt (Berthelson 1944; Ekholm 1950).

**Material.** Samma stenar som i de ursprungliga studierna: {O_N} stenar som nämner en plats i öster eller väster, {G_N} stenar på sin plats i grupp eller ensamma, {H['n']} stenar i bebyggda rutor och {RI['stenar']} stenar vars ristningsriktning står i Kulturmiljöregistret.

**Metod.** Fem analysplaner låstes den 10 november 2026 innan något räknades, var och en med i förväg bestämda regler för när resultatet står, försvagas eller faller.

**Resultat.** (1) Utan de {N_ING} Ingvarsstenarna ligger {U_P} % av platserna i öster (95 %-intervall {U_LO}–{U_HI}), mot publicerade {O_P} % ({O_LO}–{O_HI}): försvagat. (2) Grupperna står vid gravfälten i alla fyra prov, också med bara granskade gravfält ({pc(K1['share_grupp'])} mot {pc(K1['share_ensam'])} %); oddskvoterna {G_OR_LO}–{G_OR_HI} mot publicerade {nf(G0['or'], 1)}. (3) Lerkanten håller i alla fem kontroller: bortfallet, åsarna, våtmarken, vattennivån och flyttade stenar. (4) Ristningarna vetter mot vägen också inom län och utan flyttade och omresta stenar, men inte mot gamla vägar mätta som en punkt ({pc(S1_['andel_inom_45'])} % inom 45 grader, väntat 25, p = {nf(S1_['p'], 2)}); mot de gamla vägarnas linjer vetter {pc(L1['a']['andel_inom_45'])} % (p = {nf(L1['a']['p'], 3)}).

**Slutsats.** Två resultat står som de publicerades. Ett måste sägas försiktigare: ungefär hälften av österns övervikt är ett enda tåg. Det fjärde är ännu inte avgjort.

## 1. Inledning

Projektets fynd om runstenarna vilar på analysplaner som låstes innan något räknades. En låst plan skyddar mot att vi lurar oss själva under analysen, men inte mot invändningar vi inte tänkt på. Därför läste vi i november 2026 Fornvännen och Futhark efter invändningar mot det vi själva påstått. Det här är den första i en serie självkontroller.

Fyra resultat prövas. *Österns övervikt:* av de utländska platser som de svenska runstenarna nämner ligger {O_P} % i öster ([Vikingarnas värld – vilka platser nämner de?]({U_SV['vikingarnas-varld']})). *Gravfälten:* stenar som står i grupp har oftare ett gravfält inom 500 m än ensamma stenar, 82 mot 55 % ([Runstenarna samlas i familjegrupper vid gravfälten]({U_SV['familjegrupper-vid-gravfalten']}), doi:{DOI_FAM}). *Lerkanten:* stenarna står mer sällan på lera än slumpvisa platser i samma bygd men oftare vid dess kant ([Runstenarna stod vid lerans kant – men halva gåtan är olöst]({U_SV['runstenarna-foljde-leran']})). *Vägen:* hälften av ristningarna vetter inom 45 grader från vägen, mot en fjärdedel väntat ([Runstenarna vände texten mot vägen]({U_SV['ristningen-vand-mot-vagen']}), doi:{DOI_VAG}).

Två av iakttagelserna är äldre än vi. Gunnar Ekholm (1950) skrev om de stenar som står ensamma på åkermark: ”{Q_EK_CLAY}” (s. 140). En sten i Vaksala står ”{Q_EK_ROAD}” (s. 138). Sune Lindqvist (1928, s. 281) skrev om de danska stenarna: ”{Q_LINDQ28}”. Det nya är mätningen på hela materialet mot en slumpmodell, och att den nu ställs mot sina invändningar.

## 2. Förregistrering

Invändningarna hittades när texterna i Fornvännen och Futhark som rör vikingatiden och runorna lästes och sammanfattades med Anthropics språkmodell Claude (Claude Sonnet för läsningen, Claude Opus för sammanställningen). Varje invändning och varje citat i den här rapporten är kontrollerat av oss mot originaltexten, med sida.

Fem planer låstes den 10 november 2026, var och en innan dess prov räknades: östandelen (SHA-256 {SHA['2026-11-10-sjalvkontroll-osterled']}…), gravfälten ({SHA['2026-11-10-sjalvkontroll-gravfalt']}…), lerkanten ({SHA['2026-11-10-lerkanten-kontroller']}…), riktningen ({SHA['2026-11-10-sjalvkontroll-riktning']}…) och vägarnas linjer ({SHA['2026-11-10-riktning-vaglinjer']}…). Utfallsreglerna, ordagrant ur planerna:
- *Östandelen.* ”**Håller:** intervallets nedre gräns > 50 %.” ”**Försvagat (obestämt):** punktskattningen > 50 % men intervallet omfattar 50 %.”
- *Gravfälten.* Ett prov står sig vid ”oddskvot > 1, Holm-p < 0,05, och i båda halvorna oddskvot > 1 med p < 0,05”; ”**Det publicerade resultatet står sig** om K1, K3a och K3b alla står sig.”
- *Lerkanten.* En kontroll håller om stenarnas överskott vid kanten och underskott på leran har 95 %-intervall som inte omfattar noll, eller om kantens koefficient i modellen är positiv med ensidigt p < 0,05.
- *Riktningen.* ”Ett prov **håller** när medel-cos ligger över det väntade och p < 0,05.” Proven korrigeras inte för varandra: vart och ett är ett krav.
- *Vägarnas linjer.* Metoden ska hitta inventerarens väg för minst 70 % av stenarna, dagens vägar ska ge minst 40 % inom 45 grader, och de gamla vägarna och kartans vägar håller vid Holm-korrigerat p < 0,05.

Sett före låsningen: den publicerade östandelen men ingen lista över Ingvarsstenar; registrets gravfältsfält i ett stickprov om 400, inte mot stenarna; för vägen fem stenar som stod två gånger och hur många som har en gammal väg nära. Två saker måste sägas tydligt. Mönstret vid lerans kant var inte förregistrerat: det beskrevs efter studien av jordarterna, och bara kontrollerna av det är låsta. Och planen för vägarnas linjer skrevs *efter* att provet mot gamla vägar som punkter fallit; den är ett nytt försök, låst innan det räknades. Konfirmatoriska är de prov som står i utfallsreglerna ovan; resten är beskrivande.

## 3. Material

Runstenarna kommer ur Samnordisk runtextdatabas (Rundata), fryst för analysen den 4 oktober 2026. Varje kontroll använder sin ursprungliga studies stenar:
- *Östandelen:* {O_N} vikingatida svenska runstenar som nämner minst en plats i öster eller väster ({int(O_ALL['O'])} östliga och {int(O_ALL['V'])} västliga platser, olika platser per sten). Ingvarsstenarna definierades i planen och granskades mot texten innan någon andel räknades: av {len(ING_CAND)} kandidater togs U 540 bort, där Ingvarr är en av resarna.
- *Gravfälten:* {G_N} stenar på sin plats, {G_GR} i grupp (en annan sten 25–500 m bort) och {G_EN} ensamma (närmaste sten mer än 1 000 m bort). Alla {th(G_ALL)} gravfält i Kulturmiljöregistret (KMR) fick ur K-samsök sin antikvariska bedömning, om de bekräftats i fält och sina gravformer. Stenarnas län kommer för {LAN['egen KMR-post']} av {G_N} ur stenens egen registerpost.
- *Lerkanten:* {H['n']} stenar som står kvar i bebyggda rutor om 2 km (med gravfält och minst en fjärdedel land år 1050), SGU:s jordartskarta och 50 slumpvisa platser på land i samma ruta per sten. *Vid kanten* betyder inom 200 m från lera och silt som var land år 1050.
- *Vägen:* {RI['stenar']} stenar med ristningens riktning i KMR, en rad per sten; {RI['med_vag']} har en väg i registrets text. Vägarna ur K-samsök (punkter) och Riksantikvarieämbetets lämningspaket (linjer), dagens vägar ur OpenStreetMap.

## 4. Metod

**4.1 Proven.** *Östandelen* räknas som summan av östliga platser genom summan av östliga och västliga, med 95 %-intervall från bootstrap över stenar (10 000 dragningar). *Gravfälten:* originalets logistiska regression (i grupp eller ensam, landskap, tid, lokal stentäthet) med bara granskade gravfält som utfall (K1: fornlämning, bekräftad i fält, minst en gravform som inte kan förväxlas med röjningsrösen), bara yngre järnålderns former som treudd och kvadratisk stensättning (K2), län i stället för landskap (K3a) och dessutom gravfältstätheten 1–5 km från stenen (K3b). *Lerkanten:* andelen stenar på leran och vid kanten mot slumpplatserna, med intervall från bootstrap över block om 20 km, och en villkorad logistisk regression där varje sten jämförs bara med sina 50 slumpplatser i samma ruta. *Vägen:* medel-cos, medelvärdet av cosinus för vinkeln mellan ristningens riktning och riktningen till vägen (1 rakt mot vägen, 0 åt sidan), mot 9 999 omblandningar av riktningarna mellan stenarna inom landskapet.

**4.2 Korrigering och halvorna.** Gravfältens fyra prov är Holm-korrigerade över varandra och görs i båda halvorna av materialet (socknarna delade så att båda får stenar från samma trakter). Vägarnas linjer korrigeras med Holm över de gamla vägarna och kartan; eftersom kartan inte är prövad används den övre gränsen, två gånger p. Riktningens halvor redovisas beskrivande.

**4.3 Känslighetsanalyser.** Planernas beskrivande varianter, som inte ändrar domen, redovisas i 5.

**4.4 Avvikelser från planen.** *Östandelen:* stenarna om Knuts gäld söktes först med fel stavning och listan blev tom; felet rättades innan något resultat användes, och det rör bara en beskrivande variant. *Gravfälten:* originalets omkörning skrevs till en egen katalog; två stenar fick länet efter närmaste gravfält oavsett landskap (planen: i samma landskap); formen gravhägnad (13 gravfält) räknades inte som säker, eftersom den saknas i planens lista. *Lerkanten och vägen:* inga.

## 5. Resultat

**5.1 Österns övervikt utan Ingvarståget – försvagat.** Sindbæk (2003, s. 180) räknade 96 svenska runstenar som nämner personer som rest österut och skrev att Ingvars tåg ”{Q_SINDBAEK}”. Vi fann {N_ING} Ingvarsstenar bland de {OST_STONES} stenar som nämner en plats i öster, med {int(P1['ingvar_gruppens_platser']['O'])} östliga platser och {int(P1['ingvar_gruppens_platser']['V'])} västlig. Utan dem ligger {U_P} % av platserna i öster ({U_LO}–{U_HI} %), mot {O_P} % ({O_LO}–{O_HI}) med dem: intervallet omfattar hälften, och resultatet är enligt planen försvagat. Ungefär hälften av övervikten, {DROP} av {SURPLUS} procentenheter över hälften, bärs av ett enda tåg. Med en smalare definition, eller med tåget räknat som en enda text, blir andelen {pc(NARROW['ostandel'])} %, samma dom. Westins (1941, s. 93) förskjutning mot väster – ”{Q_WESTIN}” – kunde inte prövas: de sena stilgrupperna har bara {P2['platser']['sen']} platser, under planens spärr på 20. Artikeln fick ett tillägg med båda siffrorna den 10 november 2026; stenarna och jämförelsen med sagorna finns i [Vikingarnas österled – eller bara Ingvars?]({U_SV['osterled-eller-bara-ingvars']}).

**5.2 Grupperna vid gravfälten – står sig.** Häggström (2002, s. 217) skriver att ”{Q_HAGG}”, och ger ett exempel där ett tydligt gravfält registrerades som röjningsröseområde vid inventeringen 1983 (s. 218). Ekholm (1950, s. 138) fann att gravarna vid Ängby i Lunda var ”{Q_EK_AGE}”. Omkörningen av originalet gav exakt samma tal ({pc(G0['share_grupp'])} mot {pc(G0['share_ensam'])} %, oddskvot {nf(G0['or'], 2)}, p = {nf(G0['p'], 5)}). Av registrets {th(G_ALL)} gravfält är {th(G_V)} ({pc(G_V / G_ALL)} %) granskade och {th(G_Y)} ({pc(G_Y / G_ALL)} %) har yngre järnålderns former. Alla fyra prov står sig:
- **K1, bara granskade gravfält:** {pc(K1['share_grupp'])} mot {pc(K1['share_ensam'])} %, oddskvot {nf(K1['or'], 2)} [{nf(K1['lo'], 2)}–{nf(K1['hi'], 2)}], Holm-p {nf(GT['K1']['p_holm'] * 1e5, 1)}·10⁻⁵; halvorna {nf(GT['K1']['halves']['A']['or'], 2)} och {nf(GT['K1']['halves']['B']['or'], 2)}.
- **K2, bara yngre järnålderns former:** {pc(K2['share_grupp'])} mot {pc(K2['share_ensam'])} %, oddskvot {nf(K2['or'], 2)}, Holm-p {nf(GT['K2']['p_holm'], 4)}; halvorna {nf(GT['K2']['halves']['A']['or'], 2)} och {nf(GT['K2']['halves']['B']['or'], 2)}.
- **K3a, län i stället för landskap:** oddskvot {nf(K3A['or'], 2)}, Holm-p {nf(GT['K3a']['p_holm'], 4)}; halvorna {nf(GT['K3a']['halves']['A']['or'], 2)} och {nf(GT['K3a']['halves']['B']['or'], 2)}.
- **K3b, dessutom gravfältstätheten 1–5 km:** oddskvot {nf(K3B['or'], 2)}, Holm-p {nf(GT['K3b']['p_holm'], 4)}; halvorna {nf(GT['K3b']['halves']['A']['or'], 2)} och {nf(GT['K3b']['halves']['B']['or'], 2)}.

Beskrivande: inom 250 m {pc(GR_ROB['K1_250m']['share_grupp'])} mot {pc(GR_ROB['K1_250m']['share_ensam'])} %; utan gravformen ”grav markerad av sten” (en rest sten kan vara runstenen själv) {pc(GR_ROB['K1_utan_block']['share_grupp'])} mot {pc(GR_ROB['K1_utan_block']['share_ensam'])} %; bara Uppland och Södermanland oddskvoter {nf(min(US_ORS), 1)}–{nf(max(US_ORS), 1)}.

{chart_grav(True)}

**5.3 Stenarna vid lerans kant – håller.** Huvudresultatet: på leran står {pc(H['on_clay'])} % av stenarna mot {pc(H['on_clay_random'])} % av slumpplatserna ({pp(H['on_clay_diff'])} procentenheter {ci_pp(H['on_clay_diff_95'])}), vid kanten {pc(H['edge'])} mot {pc(H['edge_random'])} % ({pp(H['edge_diff'])} {ci_pp(H['edge_diff_95'])}).
- **K1, bortfallet.** Söderberg m.fl. (2021, s. 264) skriver om gravarna att ”{Q_SODERBERG}”. Men lika stor andel stenar har försvunnit på lera och silt ({LOST['lera och silt']} %) som på morän ({LOST['morän']} %) och berg ({LOST['berg']} %), och något fler på sand och grus ({LOST['sand och grus']} %). Underskottet på leran motsvarar omkring {DEFICIT} stenar, och bortfallet räcker inte för att förklara det. Med de {N_LOST} försvunna stenarna på sina uppgivna platser: på leran {pp(KF['on_clay_diff'])} {ci_pp(KF['on_clay_diff_95'])}, kanten {pp(KF['edge_diff'])} {ci_pp(KF['edge_diff_95'])}.
- **K2, åsarna.** Lovén (2021, s. 299): ”{Q_LOVEN}”, eftersom de ”aldrig blev leriga”. Med sand och grus inom 200 m i modellen (oddskvot {nf(K2S['or'], 2)}) är kantens oddskvot {nf(K2E['or'], 2)} (ensidigt p < 0,001).
- **K3, den våta marken.** Myrdal (1982, s. 97) knöt järnålderns lie till ”{Q_MYRDAL}”. Med torv och gyttja i modellen är kantens oddskvot {nf(K3E['or'], 2)}; stenarna undviker den våta marken (oddskvot {nf(K3P['or'], 2)}).
- **K4, vattnet.** Lindqvist (1914, s. 215) räknade med att Mälaren omkring 1040 stod 4,5–5 m över dagens hav. Med vattnet omkring år 950 i stället för 1050: på leran {pp(K4W['on_clay_diff'])} {ci_pp(K4W['on_clay_diff_95'])}, kanten {pp(K4W['edge_diff'])} {ci_pp(K4W['edge_diff_95'])}.
- **K5, flyttade stenar.** Utan de {N_RUNOR_MOVED} stenar som Runor 2020 anger som flyttade ({K5R['n']} kvar): på leran {pp(K5R['on_clay_diff'])} {ci_pp(K5R['on_clay_diff_95'])}, kanten {pp(K5R['edge_diff'])} {ci_pp(K5R['edge_diff_95'])}.

Beskrivande: dyrare stenar står inte oftare på leran ({CLAY_THIRD} % vid både korta och långa texter). Kontrollerna gjordes innan artikeln om lerkanten publicerades, och artikeln beskriver dem.

**5.4 Ristningen mot vägen – ofullständig.** Tre invändningar: vägar blev fornlämningar först med 1943 års lag, då ”{Q_BERTH}” (Berthelson 1944, s. 111), och den väg som registrets text om stenen nämner är oftast dagens; ”{Q_GUST}” (Gustawsson 1941, s. 245), och Ekholm (1950, s. 140) beskriver en sten vars framsida vändes mot järnvägen när den restes på 1860-talet; och en förhistorisk väg kan saknas på kartorna: ”{Q_SKOG}” (Skoglund & Lagerås 2002, s. 83).
- **Med en rad per sten** ({S0_['n']} stenar): {pc(S0_['andel_inom_45'])} % inom 45 grader, p = {nf(S0_['p'], 4)}. Håller.
- **Inom län** ({S2_['n']}): {pc(S2_['andel_inom_45'])} %, p = {nf(S2_['p'], 4)}. Håller.
- **Utan flyttade, lagade och återresta stenar** ({S3_['n']}; {RI['flyttade_med_vag']} borttagna): {pc(S3_['andel_inom_45'])} %, p = {nf(S3_['p'], 4)}. Håller.
- **Bara gamla vägar, mätta som registrets punkt** ({S1_['n']}): {pc(S1_['andel_inom_45'])} %, p = {nf(S1_['p'], 2)}. Håller inte; en så stor lutning uppstår av slump ungefär en gång på sex.
- **Mot vägarnas linjer.** Metoden hittar inventerarens väg för {round(LK['andel_inom_45'] * LK['n'])} av {LK['n']} stenar ({nf(100 * LK['andel_inom_45'], 1)} %, gränsen 70, alltså med en stens marginal). Mot dagens vägar vetter {pc(L0['a']['andel_inom_45'])} % ({L0['a']['n']} stenar, p = {nf(L0['a']['p'], 4)}). Mot de gamla vägarnas linjer vetter {pc(L1['a']['andel_inom_45'])} % ({L1['a']['n']} stenar, p = {nf(L1['a']['p'], 3)}, Holm högst {nf(L1['holm_p_ovre'], 3)}); utan flyttade stenar {pc(L1['b']['andel_inom_45'])} % av {L1['b']['n']}. Vid 300 m {pc(LB['L1_300']['a']['andel_inom_45'])} %, vid 1 km bara {pc(LB['L1_1000']['a']['andel_inom_45'])} %.
- **Mot 1800-talets vägar på Häradsekonomiska kartan:** inte gjort. Vägarna ska ritas av blint och avritningen prövas med en andra avritning.

{chart_vag(True)}

Avsnittet är ofullständigt, och vi drar ingen slutsats om vägen. Rapporten om vägen får sin nya version när provet mot kartan är gjort.

**5.5 Sammantaget.** I klartext: gravfälten och lerkanten håller för alla invändningar vi kunde pröva, och sambanden ändras knappt (sju av tio stenar i grupp mot fyra av tio ensamma har ett granskat gravfält nära; hälften av stenarna står vid lerans kant mot fyra av tio slumpplatser). Österns övervikt krymper från två tredjedelar till drygt hälften av platserna när ett enda tåg räknas bort, och kan då inte längre skiljas från lika många i öster som i väster. Ristningarna vetter mot dagens vägar ungefär varannan gång och mot de gamla vägarnas linjer ungefär var tredje, mot var fjärde av slump; en så stor lutning mot de gamla vägarna uppstår av slump ungefär en gång på 44.

## 6. Diskussion

För gravfälten och lerkanten är invändningarna rimliga, men de förklarar inte mönstren: röjningsrösen, länens inventeringar, bortfallet på åkermark, åsarna, ängarna och vattennivån lämnar sambanden nästan oförändrade. För östandelen hade invändningen rätt: Sindbæks ”mere end 25 sten” bär halva övervikten, och ett minne av en händelse måste skiljas från ett mönster av många resor. För vägen står frågan öppen.

Svagheterna, i ordning efter vikt: (1) *Vägens linjeprov är ett andra försök.* Det planerades efter att punktprovet fallit, klarar Holm-gränsen med liten marginal, och metodkontrollen klarades med en sten; ingen av vägarna är daterad till vikingatiden. (2) *Gravfälten är odaterade.* Registret har ingen datering, så samtidighet mellan sten och gravfält kan inte visas; yngre järnålderns former omfattar också vendeltid. (3) *Lerkantens mönster var inte förregistrerat,* och att gårdarna flyttade under yngre järnåldern kan inte prövas med våra data. (4) *Vi valde själva invändningarna och hur de mäts.* En annan läsare kunde ha formulerat dem skarpare.

Gravfältsfyndet faller om ett daterat urval visar att grupperna inte står vid samtida gravfält oftare än ensamma stenar; lerkanten om gårdarnas lägen vid tiden visar att kanten bara är där gårdarna flyttade; vägfyndet om också 1800-talets vägar på kartan inte drar ristningarna till sig.

## 7. Slutsats

Två av fyra resultat står mot hundra års invändningar, ett försvagas och sägs nu försiktigare, och ett väntar på kartorna. Att självkontrollen kan försvaga ett resultat är skälet att göra den.

## Data och kod

Analysen är gjord i Vitki {APP_VERSION}, ett öppet forskningsverktyg för runstenar ([vitkirunor.se]({SITE})). Koden och resultatfilerna finns i https://github.com/Precatio/runes under GPL-3.0. Planerna låstes i commit 4d00080, bc7da76, c50b452, b3133a0 och ee90f3e; resultaten skrevs i c43111a, 4e68592, 66730c3, d2efcd1 och 105bb8c (alla 10 november 2026).

- Planerna: `analysplaner/2026-11-10-sjalvkontroll-osterled.md`, `…-sjalvkontroll-gravfalt.md`, `…-lerkanten-kontroller.md`, `…-sjalvkontroll-riktning.md` och `…-riktning-vaglinjer.md`, med kontrollsummor bredvid.
- Östandelen: `utdata/varlden/sjalvkontroll/` (`ingvarsstenar.py` med granskningen, `analys.py`, `tid.R`, `resultat.json`). Gravfälten: `utdata/familjens_plats/sjalvkontroll/` (`hamta_gravfalt.py`, `klasser.py`, `analys.R`, `resultat.json`; omkörningen i `p0/`). Lerkanten: `utdata/palm_jordarna/kontroller.py`, `kontroller.R`, `kontroller.json`, `kontroller_R.json`. Vägen: `utdata/riktning/sjalvkontroll.py` och `vaglinjer.py` med `sjalvkontroll.json` och `vaglinjer.json`.
- Data: Rundata (version 2014 med RUNDATA.xls uppdaterad 2018), fryst 2026-10-04; KMR via K-samsök och Riksantikvarieämbetets lämningspaket, hämtat 2026-11-10 (CC0); SGU:s jordartskarta (CC BY 4.0); OpenStreetMap via Geofabrik, utdrag 2026-11-10 (ODbL); Runor 2020.
- Rapporten byggs av `utdata/blogg/build/build_rapport_sjalvkontroll1.py`, som läser alla tal ur resultatfilerna, kontrollerar varje citat på sin tryckta sida och stannar om något inte stämmer. Mallen: `utdata/rapporter/MALL.md`, version 4. Ordlista: {SITE}/forskningsrapporter/begrepp.

## Referenser

- Berthelson, B. 1944. Riksantikvarieämbetets fältarbeten: från byggnadsavdelningens verksamhet 1943. *Fornvännen* 39, s. 111–127. [Fri fulltext]({URL_BERTH}).
- Ekholm, G. 1950. Var restes runstenarna? *Fornvännen* 45, s. 137–147. [Fri fulltext]({URL_EKHOLM}).
- Gustawsson, K. A. 1941. Restaurering av runstenar. *Fornvännen* 36, s. 243–245. [Fri fulltext]({URL_GUST}).
- Holm, S. 1979. A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics* 6 (2), s. 65–70.
- Häggström, L. 2002. [Recension av] A. Ericsson (red.), *Odlingslandskap och uppdragsarkeologi* (1999) och P. Lagerås (red.), *Arkeologi och paleoekologi i sydvästra Småland* (2000). *Fornvännen* 97, s. 215–219. [Fri fulltext]({URL_HAGG}).
- Kvant, V. 2026a. Vikingarnas värld – vilka platser nämner de? Artikel. {U_SV['vikingarnas-varld']}
- Kvant, V. 2026b. Runstenarna samlas i familjegrupper vid gravfälten. Forskningsrapport. doi:{DOI_FAM}
- Kvant, V. 2026c. Runstenarna vände texten mot vägen. Forskningsrapport. doi:{DOI_VAG}
- Kvant, V. 2026d. Varför står runstenarna vid lerans kant – och sex gånger tätare i Mälardalen? Artikel. {U_SV['runstenarna-foljde-leran']}
- Kvant, V. 2026e. Vikingarnas österled – eller bara Ingvars? Artikel. {U_SV['osterled-eller-bara-ingvars']}
- Lindqvist, S. 1914. Ramsundsbron vid Sigurdsristningen och en storbondesläkt från missionstiden. *Fornvännen* 9, s. 203–230. [Fri fulltext]({URL_LINDQ14}).
- Lindqvist, S. 1928. Jellingemonumenten. *Fornvännen* 23, s. 257–285. [Fri fulltext]({URL_LINDQ28}).
- Lovén, C. 2021. Hjälmarsund: en utkonkurrerad stadsbildning? *Fornvännen* 116, s. 296–304. [Fri fulltext]({URL_LOVEN}).
- Myrdal, J. 1982. Jordbruksredskap av järn före år 1000. *Fornvännen* 77, s. 81–104. [Fri fulltext]({URL_MYRDAL}).
- Riksantikvarieämbetet. Kulturmiljöregistret, via K-samsök, och lämningspaketet för Sverige. CC0. Hämtat 2026-11-10. *Runor* (runinskriftsregister, utgåva 2020).
- Samnordisk runtextdatabas (Rundata), version 2014 med RUNDATA.xls uppdaterad 2018. Institutionen för nordiska språk, Uppsala universitet. Hämtad 2026-10-04. Open Database License (ODbL) 1.0.
- Sindbæk, S. M. 2003. Varægiske vinterruter: slædetransport i Rusland og spørgsmålet om den tidlige vikingetids orientalske import i Nordeuropa. *Fornvännen* 98, s. 179–193. [Fri fulltext]({URL_SINDBAEK}).
- Skoglund, P. & Lagerås, P. 2002. En vendeltida vagn från södra Småland: fyndet från Skirsnäs mosse i ny belysning. *Fornvännen* 97, s. 73–86. [Fri fulltext]({URL_SKOG}).
- Sveriges geologiska undersökning. *Jordarter 1:25 000–1:100 000* och *Strandförskjutningsmodell*. CC BY 4.0.
- Söderberg, B., Lagerås, P. & Björk, T. 2021. Gränslandets dynamik: samspelet mellan slätt och ås i nordöstra Skåne i ett långtidsperspektiv. *Fornvännen* 116, s. 261–280. [Fri fulltext]({URL_SODERBERG}).
- Westin, G. 1941. En västmanländsk ryttargrav. *Fornvännen* 36, s. 85–101. [Fri fulltext]({URL_WESTIN}).

:::box Det viktigaste i korthet
- Att stengrupperna står vid gravfälten och att stenarna står vid lerans kant håller för de invändningar som forskningen rest och som vi kunde pröva.
- Österns övervikt på runstenarna är till ungefär hälften ett enda tåg, Ingvars; utan det nämner stenarna öster bara något oftare än väster.
- Om ristningarna vände sig mot vikingatidens vägar är ännu inte avgjort; provet mot 1800-talets karta återstår.
- Ett resultat som kan försvagas av en självkontroll är ett resultat som har prövats på riktigt.
:::"""

# ======================================================================================================================
body_en = f"""*Viktor Kvant, independent researcher. Partially tested finding. Report version {REPORT_VERSION}, {TODAY}. Timeline: {TL_EN}. The analysis was made in Vitki {APP_VERSION}. Licence CC BY 4.0. The English version is the canonical one for citation: {CITE_EN}. Keywords: runestones, Viking Age, self-check, Ingvarr expedition, grave fields, soils, roads, Fornvännen. Competing interests: none. Funding: none.*

## Abstract

**What is not tested.** One of the four results weakened, and the check of the fourth is not finished: the test against the roads on the 19th-century Häradsekonomiska kartan remains, and no final verdict on the road is given here.

**Background and aim.** A result is not tested until it has met its objections. We set four of the project's results on the runestones against objections from Fornvännen and Futhark: that the eastern predominance is carried by the Ingvarr expedition (Sindbæk 2003), that the register's grave fields mix graves with clearance cairns and are older than the stones (Häggström 2002; Ekholm 1950), that the stones at the clay edge are the ones the plough left or stand by esker roads (Söderberg et al. 2021; Lovén 2021), and that the register's roads are today's and stones were turned when re-erected (Berthelson 1944; Ekholm 1950).

**Material.** The same stones as in the original studies: {O_N} stones naming a place in the east or west, {G_N} stones in place in a group or alone, {H['n']} stones in settled cells and {RI['stenar']} stones whose inscription's direction is recorded in the register of ancient monuments.

**Method.** Five analysis plans were locked on 10 November 2026 before anything was computed, each with rules fixed in advance for when the result stands, weakens or falls.

**Results.** (1) Without the {N_ING} Ingvarr stones, {U_P}% of the places lie in the east (95% interval {U_LO}–{U_HI}), against the published {O_P}% ({O_LO}–{O_HI}): weakened. (2) The groups stand at the grave fields in all four tests, also with only verified grave fields ({pc(K1['share_grupp'])} against {pc(K1['share_ensam'])}%); odds ratios {G_OR_LO_EN}–{G_OR_HI_EN} against the published {nf(G0['or'], 1, True)}. (3) The clay edge holds in all five checks: the losses, the eskers, the wet ground, the water level and moved stones. (4) The inscriptions face the road also within counties and without moved and re-erected stones, but not old roads measured as a point ({pc(S1_['andel_inom_45'])}% within 45 degrees, 25 expected, p = {nf(S1_['p'], 2, True)}); towards the lines of the old roads, {pc(L1['a']['andel_inom_45'])}% face them (p = {nf(L1['a']['p'], 3, True)}).

**Conclusion.** Two results stand as published. One must be stated more cautiously: about half of the eastern predominance is a single expedition. The fourth is not yet decided.

## 1. Introduction

The project's findings on the runestones rest on analysis plans locked before anything was computed. A locked plan protects against fooling ourselves during the analysis, but not against objections we did not think of. In November 2026 we therefore read Fornvännen and Futhark for objections to what we ourselves have claimed. This is the first in a series of self-checks.

Four results are tested. *The eastern predominance:* of the foreign places the Swedish runestones name, {O_P}% lie in the east ([The Vikings' world – which places do they name?]({U_EN['vikingarnas-varld']})). *The grave fields:* stones standing in a group more often have a grave field within 500 m than lone stones, 82 against 55% ([Runestones gather in family groups by the grave fields]({U_EN['familjegrupper-vid-gravfalten']}), doi:{DOI_FAM}). *The clay edge:* the stones stand on clay less often than random places in the same district but more often at its edge ([Why do the runestones stand at the edge of the clay?]({U_EN['runstenarna-foljde-leran']})). *The road:* half of the inscriptions face within 45 degrees of the road, against a quarter expected ([The runestones turned their text towards the road]({U_EN['ristningen-vand-mot-vagen']}), doi:{DOI_VAG}).

Two of the observations are older than us. Gunnar Ekholm (1950) wrote of the stones standing alone on farmland: “{Q_EK_CLAY}” ('Besides, runestones of this kind often have their place on the clay lands', p. 140). A stone in Vaksala stands “{Q_EK_ROAD}” ('facing the doubtless very old road', p. 138). Sune Lindqvist (1928, p. 281) wrote of the Danish stones: “{Q_LINDQ28}” ('The runestones were placed so that they could easily be read by passers-by'). What is new is the measurement on the whole material against a chance model, and that it is now set against its objections.

## 2. Pre-registration

The objections were found when the texts in Fornvännen and Futhark concerning the Viking Age and runes were read and summarised with Anthropic's language model Claude (Claude Sonnet for the reading, Claude Opus for the synthesis). Every objection and every quotation in this report has been checked by us against the original text, with its page.

Five plans were locked on 10 November 2026, each before its tests were computed: the east share (SHA-256 {SHA['2026-11-10-sjalvkontroll-osterled']}…), the grave fields ({SHA['2026-11-10-sjalvkontroll-gravfalt']}…), the clay edge ({SHA['2026-11-10-lerkanten-kontroller']}…), the direction ({SHA['2026-11-10-sjalvkontroll-riktning']}…) and the road lines ({SHA['2026-11-10-riktning-vaglinjer']}…). The outcome rules, translated from the plans:
- *The east share.* "Holds: the interval's lower bound > 50%." "Weakened (undecided): the point estimate > 50% but the interval includes 50%."
- *The grave fields.* A test stands at "odds ratio > 1, Holm p < 0.05, and in both halves odds ratio > 1 with p < 0.05"; "the published result stands if K1, K3a and K3b all stand."
- *The clay edge.* A check holds if the stones' excess at the edge and deficit on the clay have 95% intervals that exclude zero, or if the edge coefficient in the model is positive with one-sided p < 0.05.
- *The direction.* "A test holds when the mean cos lies above the expected and p < 0.05." The tests are not corrected for each other: each is a requirement.
- *The road lines.* The method must find the surveyor's road for at least 70% of the stones, today's roads must give at least 40% within 45 degrees, and the old roads and the map's roads hold at Holm-corrected p < 0.05.

Seen before locking: the published east share but no list of Ingvarr stones; the register's grave-field fields in a sample of 400, not against the stones; for the road, five stones that appeared twice and how many have an old road nearby. Two things must be said plainly. The pattern at the clay edge was not pre-registered: it was described after the soil study, and only its checks are locked. And the plan for the road lines was written *after* the test against old roads as points had failed; it is a new attempt, locked before it was computed. Confirmatory are the tests in the outcome rules above; the rest is descriptive.

## 3. Material

The runestones come from the Scandinavian Runic-text Database (Rundata), frozen for the analysis on 4 October 2026. Each check uses its original study's stones:
- *The east share:* {O_N} Viking-Age Swedish runestones naming at least one place in the east or west ({int(O_ALL['O'])} eastern and {int(O_ALL['V'])} western places, distinct places per stone). The Ingvarr stones were defined in the plan and reviewed against the text before any share was computed: of {len(ING_CAND)} candidates, U 540 was removed, where Ingvarr is one of the raisers.
- *The grave fields:* {G_N} stones in place, {G_GR} in a group (another stone 25–500 m away) and {G_EN} alone (nearest stone more than 1,000 m away). All {th(G_ALL, True)} grave fields in the register of ancient monuments (Kulturmiljöregistret, KMR) got from K-samsök their antiquarian assessment, whether confirmed in the field and their grave forms. The stones' counties come for {LAN['egen KMR-post']} of {G_N} from the stone's own register record.
- *The clay edge:* {H['n']} stones still standing in settled 2 km cells (with a grave field and at least a quarter land in the year 1050), the Geological Survey of Sweden's (SGU) soil map and 50 random land places in the same cell per stone. *At the edge* means within 200 m of clay and silt that was land in 1050.
- *The road:* {RI['stenar']} stones with the inscription's direction in the register, one row per stone; {RI['med_vag']} have a road in the register's text. The roads from K-samsök (points) and the Heritage Board's monument package (lines), today's roads from OpenStreetMap.

## 4. Method

**4.1 The tests.** *The east share* is the sum of eastern places divided by the sum of eastern and western, with a 95% interval from a bootstrap over stones (10,000 draws). *The grave fields:* the original's logistic regression (group or alone, province, period, local stone density) with only verified grave fields as outcome (K1: ancient monument, confirmed in the field, at least one grave form that cannot be confused with clearance cairns), only Late Iron Age forms such as tripartite and square stone settings (K2), county instead of province (K3a), and in addition the grave-field density 1–5 km from the stone (K3b). *The clay edge:* the share of stones on the clay and at the edge against the random places, with intervals from a bootstrap over 20 km blocks, and a conditional logistic regression in which each stone is compared only with its own 50 random places in the same cell. *The road:* mean cos, the mean cosine of the angle between the inscription's direction and the direction to the road (1 straight at the road, 0 to the side), against 9,999 shuffles of the directions between the stones within the province.

**4.2 Correction and the halves.** The four grave-field tests are Holm-corrected over each other and run in both halves of the material (the parishes split so that both halves get stones from the same districts). The road lines are corrected with Holm over the old roads and the map; since the map is not tested, the upper bound, twice p, is used. The halves for the direction are reported descriptively.

**4.3 Sensitivity analyses.** The plans' descriptive variants, which do not change the verdict, are reported in 5.

**4.4 Deviations from the plan.** *The east share:* the stones about Cnut's payment were first searched with the wrong spelling and the list came out empty; the error was corrected before any result was used, and it concerns only a descriptive variant. *The grave fields:* the original's rerun was written to its own folder; two stones got their county from the nearest grave field regardless of province (the plan: in the same province); the form 'grave enclosure' (13 grave fields) was not counted as certain, since it is missing from the plan's list. *The clay edge and the road:* none.

## 5. Results

**5.1 The eastern predominance without the Ingvarr expedition – weakened.** Sindbæk (2003, p. 180) counted 96 Swedish runestones mentioning people who had travelled east and wrote that Ingvarr's expedition “{Q_SINDBAEK}” ('alone accounts for more than 25 stones'). We found {N_ING} Ingvarr stones among the {OST_STONES} stones naming a place in the east, with {int(P1['ingvar_gruppens_platser']['O'])} eastern places and {int(P1['ingvar_gruppens_platser']['V'])} western. Without them, {U_P}% of the places lie in the east ({U_LO}–{U_HI}%), against {O_P}% ({O_LO}–{O_HI}) with them: the interval includes one half, and by the plan the result is weakened. About half of the predominance, {DROP} of the {SURPLUS} percentage points above one half, is carried by a single expedition. By a narrower definition, or with the expedition counted as a single text, the share is {pc(NARROW['ostandel'])}%, the same verdict. Westin's (1941, p. 93) westward shift – “{Q_WESTIN}” ('Towards the end of the Viking Age, however, a shift sets in') – could not be tested: the late style groups have only {P2['platser']['sen']} places, below the plan's threshold of 20. The article got an addition with both figures on 10 November 2026; the stones and the comparison with the sagas are in [The Vikings' road east – or just Ingvarr's?]({U_EN['osterled-eller-bara-ingvars']}).

**5.2 The groups at the grave fields – stands.** Häggström (2002, p. 217) writes that “{Q_HAGG}” ('it is at times exceedingly difficult to tell what are graves and what are clearance cairns'), and gives an example where a clear grave field was registered as a clearance-cairn area in the 1983 survey (p. 218). Ekholm (1950, p. 138) found the graves at Ängby in Lunda to be “{Q_EK_AGE}” ('nearly a millennium older than the runestone'). The rerun of the original gave exactly the same figures ({pc(G0['share_grupp'])} against {pc(G0['share_ensam'])}%, odds ratio {nf(G0['or'], 2, True)}, p = {nf(G0['p'], 5, True)}). Of the register's {th(G_ALL, True)} grave fields, {th(G_V, True)} ({pc(G_V / G_ALL)}%) are verified and {th(G_Y, True)} ({pc(G_Y / G_ALL)}%) have Late Iron Age forms. All four tests stand:
- **K1, only verified grave fields:** {pc(K1['share_grupp'])} against {pc(K1['share_ensam'])}%, odds ratio {nf(K1['or'], 2, True)} [{nf(K1['lo'], 2, True)}–{nf(K1['hi'], 2, True)}], Holm p {nf(GT['K1']['p_holm'] * 1e5, 1, True)}·10⁻⁵; halves {nf(GT['K1']['halves']['A']['or'], 2, True)} and {nf(GT['K1']['halves']['B']['or'], 2, True)}.
- **K2, only Late Iron Age forms:** {pc(K2['share_grupp'])} against {pc(K2['share_ensam'])}%, odds ratio {nf(K2['or'], 2, True)}, Holm p {nf(GT['K2']['p_holm'], 4, True)}; halves {nf(GT['K2']['halves']['A']['or'], 2, True)} and {nf(GT['K2']['halves']['B']['or'], 2, True)}.
- **K3a, county instead of province:** odds ratio {nf(K3A['or'], 2, True)}, Holm p {nf(GT['K3a']['p_holm'], 4, True)}; halves {nf(GT['K3a']['halves']['A']['or'], 2, True)} and {nf(GT['K3a']['halves']['B']['or'], 2, True)}.
- **K3b, also the grave-field density 1–5 km:** odds ratio {nf(K3B['or'], 2, True)}, Holm p {nf(GT['K3b']['p_holm'], 4, True)}; halves {nf(GT['K3b']['halves']['A']['or'], 2, True)} and {nf(GT['K3b']['halves']['B']['or'], 2, True)}.

Descriptive: within 250 m {pc(GR_ROB['K1_250m']['share_grupp'])} against {pc(GR_ROB['K1_250m']['share_ensam'])}%; without the form 'grave marked by a stone' (a standing stone may be the runestone itself) {pc(GR_ROB['K1_utan_block']['share_grupp'])} against {pc(GR_ROB['K1_utan_block']['share_ensam'])}%; only Uppland and Södermanland odds ratios {nf(min(US_ORS), 1, True)}–{nf(max(US_ORS), 1, True)}.

{chart_grav(False)}

**5.3 The stones at the clay edge – holds.** The main result: {pc(H['on_clay'])}% of the stones stand on clay against {pc(H['on_clay_random'])}% of the random places ({pp(H['on_clay_diff'], True)} percentage points {ci_pp(H['on_clay_diff_95'], True)}), at the edge {pc(H['edge'])} against {pc(H['edge_random'])}% ({pp(H['edge_diff'], True)} {ci_pp(H['edge_diff_95'], True)}).
- **K1, the losses.** Söderberg et al. (2021, p. 264) write of the graves that “{Q_SODERBERG}” ('farming on the plain has resulted in the ploughing-away of prehistoric graves'), and the same may have happened to the runestones. But the same share of stones has been lost on clay and silt ({LOST['lera och silt']}%) as on till ({LOST['morän']}%) and bedrock ({LOST['berg']}%), and slightly more on sand and gravel ({LOST['sand och grus']}%). The deficit on the clay corresponds to about {DEFICIT} stones, and the losses cannot explain it. With the {N_LOST} lost stones at their recorded places: on the clay {pp(KF['on_clay_diff'], True)} {ci_pp(KF['on_clay_diff_95'], True)}, the edge {pp(KF['edge_diff'], True)} {ci_pp(KF['edge_diff_95'], True)}.
- **K2, the eskers.** Lovén (2021, p. 299): “{Q_LOVEN}” ('The long eskers could be called our first highways'), since they "aldrig blev leriga" ('never became muddy'). With sand and gravel within 200 m in the model (odds ratio {nf(K2S['or'], 2, True)}), the edge's odds ratio is {nf(K2E['or'], 2, True)} (one-sided p < 0.001).
- **K3, the wet ground.** Myrdal (1982, p. 97) tied the Iron Age scythe to “{Q_MYRDAL}” ('maintained and cleared meadows or marshland'). With peat and gyttja in the model, the edge's odds ratio is {nf(K3E['or'], 2, True)}; the stones avoid wet ground (odds ratio {nf(K3P['or'], 2, True)}).
- **K4, the water.** Lindqvist (1914, p. 215) reckoned that Lake Mälaren around 1040 stood 4.5–5 m above today's sea. With the water of about the year 950 instead of 1050: on the clay {pp(K4W['on_clay_diff'], True)} {ci_pp(K4W['on_clay_diff_95'], True)}, the edge {pp(K4W['edge_diff'], True)} {ci_pp(K4W['edge_diff_95'], True)}.
- **K5, moved stones.** Without the {N_RUNOR_MOVED} stones Runor 2020 records as moved ({K5R['n']} left): on the clay {pp(K5R['on_clay_diff'], True)} {ci_pp(K5R['on_clay_diff_95'], True)}, the edge {pp(K5R['edge_diff'], True)} {ci_pp(K5R['edge_diff_95'], True)}.

Descriptive: costlier stones do not stand on clay more often ({CLAY_THIRD}% for both short and long texts). The checks were made before the article on the clay edge was published, and the article describes them.

**5.4 The inscription facing the road – incomplete.** Three objections: roads became ancient monuments only with the law of 1943, when “{Q_BERTH}” ('notable routes, road markers, bridges and similar structures were included among fixed ancient monuments'; Berthelson 1944, p. 111), and the road the register's text about the stone mentions is mostly today's; “{Q_GUST}” ('Since 1932, 311 runestones have been repaired or raised'; Gustawsson 1941, p. 245), and Ekholm (1950, p. 140) describes a stone whose face was turned towards the railway when it was raised again in the 1860s; and a prehistoric road can be missing from the maps: “{Q_SKOG}” ('No road across the bog appears either on this map or on the hundred map from the mid-17th century'; Skoglund & Lagerås 2002, p. 83).
- **One row per stone** ({S0_['n']} stones): {pc(S0_['andel_inom_45'])}% within 45 degrees, p = {nf(S0_['p'], 4, True)}. Holds.
- **Within counties** ({S2_['n']}): {pc(S2_['andel_inom_45'])}%, p = {nf(S2_['p'], 4, True)}. Holds.
- **Without moved, repaired and re-erected stones** ({S3_['n']}; {RI['flyttade_med_vag']} removed): {pc(S3_['andel_inom_45'])}%, p = {nf(S3_['p'], 4, True)}. Holds.
- **Only old roads, measured as the register's point** ({S1_['n']}): {pc(S1_['andel_inom_45'])}%, p = {nf(S1_['p'], 2, True)}. Does not hold; a lean this large arises by chance about once in six.
- **Towards the roads' lines.** The method finds the surveyor's road for {round(LK['andel_inom_45'] * LK['n'])} of {LK['n']} stones ({nf(100 * LK['andel_inom_45'], 1, True)}%, the limit 70, a margin of one stone). Towards today's roads, {pc(L0['a']['andel_inom_45'])}% face them ({L0['a']['n']} stones, p = {nf(L0['a']['p'], 4, True)}). Towards the lines of the old roads, {pc(L1['a']['andel_inom_45'])}% ({L1['a']['n']} stones, p = {nf(L1['a']['p'], 3, True)}, Holm at most {nf(L1['holm_p_ovre'], 3, True)}); without moved stones {pc(L1['b']['andel_inom_45'])}% of {L1['b']['n']}. At 300 m {pc(LB['L1_300']['a']['andel_inom_45'])}%, at 1 km only {pc(LB['L1_1000']['a']['andel_inom_45'])}%.
- **Towards the 19th-century roads on the Häradsekonomiska kartan:** not done. The roads are to be traced blind and the tracing tested with a second tracing.

{chart_vag(False)}

The section is incomplete, and we draw no conclusion about the road. The report on the road gets its new version when the test against the map has been made.

**5.5 Taken together.** In plain words: the grave fields and the clay edge hold against every objection we could test, and the associations barely change (seven in ten stones in groups against four in ten alone have a verified grave field nearby; half of the stones stand at the clay edge against four in ten random places). The eastern predominance shrinks from two thirds to just over half of the places when a single expedition is removed, and can then no longer be told apart from as many in the east as in the west. The inscriptions face today's roads about every other time and the lines of the old roads about every third, against every fourth by chance; a lean towards the old roads this large arises by chance about once in 44.

## 6. Discussion

For the grave fields and the clay edge the objections are reasonable, but they do not explain the patterns: clearance cairns, the counties' surveys, the losses on farmland, the eskers, the meadows and the water level leave the associations almost unchanged. For the east share the objection was right: Sindbæk's “mere end 25 sten” carries half the predominance, and the memory of one event must be separated from a pattern of many journeys. For the road the question remains open.

The weaknesses, in order of weight: (1) *The road-line test is a second attempt.* It was planned after the point test had failed, meets the Holm limit with a small margin, and the method check passed by one stone; none of the roads is dated to the Viking Age. (2) *The grave fields are undated.* The register has no dating, so contemporaneity of stone and grave field cannot be shown; the Late Iron Age forms also include the Vendel period. (3) *The clay-edge pattern was not pre-registered,* and that farms moved during the Late Iron Age cannot be tested with our data. (4) *We chose the objections and how to measure them ourselves.* Another reader could have framed them more sharply.

The grave-field finding falls if a dated sample shows that the groups do not stand at contemporary grave fields more often than lone stones; the clay edge if the farms' sites of the time show that the edge is only where the farms moved; the road finding if the 19th-century roads on the map do not draw the inscriptions either.

## 7. Conclusion

Two of four results stand against a century of objections, one weakens and is now stated more cautiously, and one awaits the maps. That a self-check can weaken a result is the reason for making it.

## Data and code

The analysis was made in Vitki {APP_VERSION}, an open research tool for runestones ([vitkirunor.se]({SITE})). The code and the result files are at https://github.com/Precatio/runes under GPL-3.0. The plans were locked in commits 4d00080, bc7da76, c50b452, b3133a0 and ee90f3e; the results were written in c43111a, 4e68592, 66730c3, d2efcd1 and 105bb8c (all 10 November 2026).

- The plans: `analysplaner/2026-11-10-sjalvkontroll-osterled.md`, `…-sjalvkontroll-gravfalt.md`, `…-lerkanten-kontroller.md`, `…-sjalvkontroll-riktning.md` and `…-riktning-vaglinjer.md`, with checksums beside them.
- The east share: `utdata/varlden/sjalvkontroll/` (`ingvarsstenar.py` with the review, `analys.py`, `tid.R`, `resultat.json`). The grave fields: `utdata/familjens_plats/sjalvkontroll/` (`hamta_gravfalt.py`, `klasser.py`, `analys.R`, `resultat.json`; the rerun in `p0/`). The clay edge: `utdata/palm_jordarna/kontroller.py`, `kontroller.R`, `kontroller.json`, `kontroller_R.json`. The road: `utdata/riktning/sjalvkontroll.py` and `vaglinjer.py` with `sjalvkontroll.json` and `vaglinjer.json`.
- Data: Rundata (2014 version with RUNDATA.xls updated 2018), frozen 2026-10-04; KMR via K-samsök and the Heritage Board's monument package, retrieved 2026-11-10 (CC0); SGU's soil map (CC BY 4.0); OpenStreetMap via Geofabrik, extract 2026-11-10 (ODbL); Runor 2020.
- The report is built by `utdata/blogg/build/build_rapport_sjalvkontroll1.py`, which reads every number from the result files, checks every quotation on its printed page and stops if anything does not match. The template: `utdata/rapporter/MALL.md`, version 4. Glossary: {SITE}/en/forskningsrapporter/begrepp.

## References

- Berthelson, B. 1944. Riksantikvarieämbetets fältarbeten: från byggnadsavdelningens verksamhet 1943. *Fornvännen* 39, pp. 111–127. [Free full text]({URL_BERTH}).
- Ekholm, G. 1950. Var restes runstenarna? *Fornvännen* 45, pp. 137–147. [Free full text]({URL_EKHOLM}).
- Gustawsson, K. A. 1941. Restaurering av runstenar. *Fornvännen* 36, pp. 243–245. [Free full text]({URL_GUST}).
- Holm, S. 1979. A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics* 6 (2), pp. 65–70.
- Häggström, L. 2002. [Review of] A. Ericsson (ed.), *Odlingslandskap och uppdragsarkeologi* (1999) and P. Lagerås (ed.), *Arkeologi och paleoekologi i sydvästra Småland* (2000). *Fornvännen* 97, pp. 215–219. [Free full text]({URL_HAGG}).
- Kvant, V. 2026a. The Vikings' world – which places do they name? Article. {U_EN['vikingarnas-varld']}
- Kvant, V. 2026b. Runestones gather in family groups by the grave fields. Research report. doi:{DOI_FAM}
- Kvant, V. 2026c. The runestones turned their text towards the road. Research report. doi:{DOI_VAG}
- Kvant, V. 2026d. Why do the runestones stand at the edge of the clay – and six times as densely around Lake Mälaren? Article. {U_EN['runstenarna-foljde-leran']}
- Kvant, V. 2026e. The Vikings' road east – or just Ingvarr's? Article. {U_EN['osterled-eller-bara-ingvars']}
- Lindqvist, S. 1914. Ramsundsbron vid Sigurdsristningen och en storbondesläkt från missionstiden. *Fornvännen* 9, pp. 203–230. [Free full text]({URL_LINDQ14}).
- Lindqvist, S. 1928. Jellingemonumenten. *Fornvännen* 23, pp. 257–285. [Free full text]({URL_LINDQ28}).
- Lovén, C. 2021. Hjälmarsund: en utkonkurrerad stadsbildning? *Fornvännen* 116, pp. 296–304. [Free full text]({URL_LOVEN}).
- Myrdal, J. 1982. Jordbruksredskap av järn före år 1000. *Fornvännen* 77, pp. 81–104. [Free full text]({URL_MYRDAL}).
- Geological Survey of Sweden (SGU). *Jordarter 1:25 000–1:100 000* and *Strandförskjutningsmodell*. CC BY 4.0.
- Scandinavian Runic-text Database (Rundata), 2014 version with RUNDATA.xls updated 2018. Department of Scandinavian Languages, Uppsala University. Retrieved 2026-10-04. Open Database License (ODbL) 1.0.
- Sindbæk, S. M. 2003. Varægiske vinterruter: slædetransport i Rusland og spørgsmålet om den tidlige vikingetids orientalske import i Nordeuropa. *Fornvännen* 98, pp. 179–193. [Free full text]({URL_SINDBAEK}).
- Skoglund, P. & Lagerås, P. 2002. En vendeltida vagn från södra Småland: fyndet från Skirsnäs mosse i ny belysning. *Fornvännen* 97, pp. 73–86. [Free full text]({URL_SKOG}).
- Swedish National Heritage Board (Riksantikvarieämbetet). The register of ancient monuments (Kulturmiljöregistret), via K-samsök, and the monument package for Sweden. CC0. Retrieved 2026-11-10. *Runor* (register of runic inscriptions, 2020 edition).
- Söderberg, B., Lagerås, P. & Björk, T. 2021. Gränslandets dynamik: samspelet mellan slätt och ås i nordöstra Skåne i ett långtidsperspektiv. *Fornvännen* 116, pp. 261–280. [Free full text]({URL_SODERBERG}).
- Westin, G. 1941. En västmanländsk ryttargrav. *Fornvännen* 36, pp. 85–101. [Free full text]({URL_WESTIN}).

:::box The essentials in brief
- That the stone groups stand at the grave fields and that the stones stand at the clay edge holds against the objections research has raised and that we could test.
- About half of the eastern predominance on the runestones is a single expedition, Ingvarr's; without it the stones name the east only slightly more often than the west.
- Whether the inscriptions turned towards the roads of the Viking Age is not yet decided; the test against the 19th-century map remains.
- A result that a self-check can weaken is a result that has really been tested.
:::"""

# ---- checks -----------------------------------------------------------------------------------------------------------
assert "I klartext" in body and "In plain words" in body_en
assert "en gång på 44" in body and "once in 44" in body_en and "en gång på sex" in body and "once in six" in body_en
JARGON = r"modul\w*|trapp\w*|q_global|korpusjobb|fingeravtryck|fingerprint|facit|Vitkis|Vitki's|\bthe app\b|\bappen\b|`[^`]*/[^`]*`|METHODS|\bAI\b"
for b, lang in ((body, "sv"), (body_en, "en")):
    assert not re.search(r"^\|", b, re.M), "BlogBody har inga tabeller"
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M)) == 3, "varje ruta ska stängas"
    assert "{" not in b and "}" not in b
    front = b.split("## Data")[0]
    assert not re.findall(JARGON, front), re.findall(JARGON, front)
    assert not re.search(r"\]\(/", b), "absoluta länkar"
    caps = [ln for ln in b.split("\n") if ln.startswith(("Källa:", "Source:"))]
    assert len(caps) == 2 and all((CHART_SV if lang == "sv" else CHART_EN) in c for c in caps), caps
    assert "/forskningsrapporter/begrepp" in b
    # the literature-reading disclosure (ai-wording): named model, in the method part only, never in the box
    assert "Claude Sonnet" in b.split("## 3.")[0].split("## 2.")[1]
    assert "Claude" not in b.split(":::box")[1] and "Claude" not in b.split("## 2.")[0]
    # the road section is incomplete and gives no final verdict
    road = b.split("**5.4")[1].split("**5.5")[0]
    assert ("ofullständig" in road and "inte gjort" in road) if lang == "sv" else ("incomplete" in road and "not done" in road)
    for u in (URL_SINDBAEK, URL_WESTIN, URL_HAGG, URL_EKHOLM, URL_SODERBERG, URL_LOVEN, URL_MYRDAL, URL_LINDQ14, URL_BERTH,
              URL_GUST, URL_SKOG, URL_LINDQ28):
        assert u in b, u
assert "Vägen håller" not in body and "the road holds" not in body_en.lower()
assert body.split("\n", 1)[0].startswith(f"*Viktor Kvant, oberoende forskare. Delvis prövat fynd. Rapportversion 1, {TODAY}. Tidslinje:")
assert body_en.split("\n", 1)[0].startswith(f"*Viktor Kvant, independent researcher. Partially tested finding. Report version 1, {TODAY}. Timeline:")
# the abstract opens with what is not tested (mallen: nivå 2)
assert body.split("## Sammanfattning\n\n")[1].startswith("**Vad som inte är prövat.**")
assert body_en.split("## Abstract\n\n")[1].startswith("**What is not tested.**")
# the header line as scripts/zenodo_rapporter.py and web/src/lib/report.ts parse it
for b in (body, body_en):
    _h = b.splitlines()[0].strip("*")
    assert re.search(r"(?:Rapportversion|Report version) (\d+), (\d{4}-\d{2}-\d{2})", _h)
    assert f"Vitki {APP_VERSION}." in _h
    assert re.search(r"(?:Nyckelord|Keywords): ([^.]+)\.", _h) and "CC BY 4.0" in _h
    tl = re.search(r"(?:Tidslinje|Timeline):\s*(.+?)\.\s+(?:Analysen är gjord|The analysis was (?:made|done))", _h).group(1)
    ev = [re.match(r"^(.*?)\s+(\d{4}-\d{2}-\d{2})$", x.strip()) for x in tl.split(";")]
    assert all(ev) and [e.group(2) for e in ev] == sorted(e.group(2) for e in ev) and len(ev) == 6
    assert re.search(r"(?:för citering|for citation):\s*(.+?)\.\s*(?:Nyckelord|Keywords):", _h)
    assert re.search(r"(?:^|\.\s)(Delvis prövat fynd|Partially tested finding)\.", _h)
# the length (mallen: 1 500–3 000 ord på svenska före Data och kod)
WORDS_SV, WORDS_EN = len(body.split("## Data")[0].split()), len(body_en.split("## Data")[0].split())
assert 1500 <= WORDS_SV <= 3000, WORDS_SV

out = {"slug": SLUG, "title": title, "summary": summary, "body": body, "title_en": title_en, "summary_en": summary_en,
       "body_en": body_en, "labels": ["Rapport", "Geografi"]}
assert blog_labels.check(out["labels"]) is None
path = os.path.join(ROOT, "utdata", "rapporter", "rapport_sjalvkontroll1.json")
json.dump(out, open(path, "w"), ensure_ascii=False, indent=1)
print(path, len(body.split()), "ord,", WORDS_SV, "före Data och kod;", len(body_en.split()), "words,", WORDS_EN, "before Data and code")

if "--update" in sys.argv or "--write" in sys.argv:
    from api.routers import blog
    col = blog.firestore().collection(blog.COLLECTION)
    now = dt.datetime.now(dt.timezone.utc)
    # the linked articles must be published before this report is (the Ingvar article is planned for 8 December)
    live = {p_.get("slug"): bool(p_.get("published")) for p_ in blog._all()}
    for s_ in LINKED:
        if not live.get(s_):
            print(f"OBS: länkad text {s_!r} är inte publicerad ännu; publicera den före rapporten.")
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
                 "topic": "Rapport|sjalvkontroll", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
