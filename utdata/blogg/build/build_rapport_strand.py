"""Forskningsrapport (låst mall utdata/rapporter/MALL.md, version 4; Fullt prövat fynd): "Runstenarna restes vid sin tids
vatten – 64 procent inom 500 meter från vattnet år 1050, mot 46 procent av marken runt dem" (sv + en). Den låsta planen
analysplaner/2026-10-23-strand-och-gravfalt.md (H1–H3, R1–R7, S1–S4), tillägget med T1 (2026-10-31-strand-tillagg.md)
och tilläggsplanen för robusthetsstegen (2026-11-01-strand-trappan.md). Alla siffror asserteras mot
utdata/strand/resultat.json och trappan.json, och från rapportversion 2 (2026-11-05) mot utdata/strand/kontroll_v2.json
(urvalets försvunna och flyttade stenar, kartorna och tidsordningen; skrivs av utdata/strand/kontroll_v2.py).
    ../../../.venv/bin/python build_rapport_strand.py [--write | --update DOC]"""
import datetime as dt
import json
import os
import re
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_figures, blog_labels  # noqa: E402

APP_VERSION = "3.0.0"  # the Vitki version the analysis was made in (tag v3.0.0 + the commits named in Data och kod), not the current one
assert open(os.path.join(ROOT, "utdata", "rapporter", "MALL.md.sha256")).read().startswith("611a4d5f")  # mallens version 4
REPORT_VERSION = 3  # version 1: 2026-11-01, publicerad samma dag; version 2: 2026-11-05 (granskningen); version 3: 2026-11-05
# (den andra granskningen av det version 2 ändrade)
TODAY = "2026-11-05"  # rapportversionens datum, fast i byggaren (mallen version 3)
V1_PUBLISHED = "2026-11-01"  # första versionens publiceringsdatum (behålls; asserteras mot webbplatsens export nedan)
TL_SV = ("analysplanen låstes 2026-10-23; en provkörning av skriptet utan sparade resultat 2026-10-23; avstånden räknades "
         "2026-10-23; tillägget för flyttade stenar låstes 2026-10-31; statistiken kördes och lästes 2026-10-31; tilläggsplanen för "
         "känslighetsanalyserna låstes och kördes 2026-11-01")
TL_EN = ("the analysis plan was locked 2026-10-23; a test run of the script with no results kept 2026-10-23; the distances were "
         "computed 2026-10-23; the addendum for moved stones was locked 2026-10-31; the statistics were run and read 2026-10-31; "
         "the addendum plan for the sensitivity analyses was locked and run 2026-11-01")
CODE_COMMIT = "4f80a63"  # kodläget för analysen, resultatfilerna och kartorna (2026-11-01); ingen release med DOI ännu
SD = os.path.join(ROOT, "utdata", "strand")
R = json.load(open(os.path.join(SD, "resultat.json"), encoding="utf-8"))
TR = json.load(open(os.path.join(SD, "trappan.json"), encoding="utf-8"))
IL = json.load(open(os.path.join(SD, "illustration.json"), encoding="utf-8"))  # kartorna ur 06_illustration.R
assert (IL["n_stones"], IL["n_random"], IL["median_stones_m"], IL["median_random_m"], IL["n_overview"]) == (40, 100, 214, 397, 891)
SHA = {k: open(os.path.join(ROOT, "analysplaner", f"{k}.sha256")).read().split()[0][:16]
       for k in ("2026-10-23-strand-och-gravfalt", "2026-10-31-strand-tillagg", "2026-11-01-strand-trappan")}
assert SHA["2026-10-23-strand-och-gravfalt"] == R["plan_sha256"][:16] == "4ddb7d6cecb470a1"
assert SHA["2026-10-31-strand-tillagg"] == "dc63b72b3147f9c2" and SHA["2026-11-01-strand-trappan"] == TR["plan_sha256"][:16] == "2993273eff5006c6"

pc = lambda x: int(100 * x + 0.5 + 1e-9)  # noqa: E731


def num(x, d=2, en=False):
    s = f"{x:.{d}f}"
    return s if en else s.replace(".", ",")


def m(x, en=False):
    return f"{x:,}" if en else f"{x:,}".replace(",", " ")


def pfmt(p, en=False):
    if p < 0.0001:
        return "p < 0.0001" if en else "p < 0,0001"
    s = f"{p:.4f}" if p < 0.001 else (f"{p:.3f}" if p < 0.1 else f"{p:.2f}")
    return f"p = {s}" if en else f"p = {s.replace('.', ',')}"


# ---- the locked plan ------------------------------------------------------------------------------------------------
V, PO = R["verdict"], R["population"]
assert V["H1"] == "håller" and all(V["H1_criteria"].values()) and V["H3"] == "håller" and all(V["H3_criteria"].values())
assert V["H2"] == "tydligare med dåtidens vatten" and V["R6_all_delta"] is True
assert V["provinces_h1"] == V["provinces_h3"] == ["U", "Sö", "Ög", "Sm", "Vg"]
assert (PO["n"], PO["n_random"], PO["n_sites"], PO["n_dated"], PO["n_gravfalt"], PO["stones_in_water_1050"], PO["stones_in_water_1949"]) == \
    (1099, 10990, 935, 587, 18633, 108, 88)
assert PO["provinces"] == {"Ög": 89, "Öl": 20, "Sm": 69, "Sö": 234, "U": 623, "Vg": 64} and sum(PO["other_provinces_not_tested"].values()) == 45
assert PO["halves"] == {"A": 543, "B": 556}
H1, HA, HB, HS = R["H1"]["overall"], R["H1"]["halves"]["A"], R["H1"]["halves"]["B"], R["H1"]["sites"]
assert (H1["median_stones_m"], H1["median_random_m"], pc(H1["within_500_stones"]), pc(H1["within_500_random"]), num(H1["auc"])) == (305, 555, 64, 46, "0,63")
assert (pc(H1["within_1000_stones"]), pc(H1["within_1000_random"])) == (83, 76) and H1["p"] < 1e-40
assert all(x["p"] < 1e-15 for x in (HA, HB, HS)) and (HA["n_parishes"], HB["n_parishes"]) == (190, 187)
P1 = {r["province"]: r for r in R["H1"]["provinces"]}
P3 = {r["province"]: r for r in R["H3"]["provinces"]}
assert all(P1[k]["q_bh"] < 0.01 for k in ("U", "Sö", "Ög", "Sm", "Vg")) and 0.05 < P1["Öl"]["q_bh"] < 0.06
assert all(P3[k]["q_bh"] < 1e-6 for k in ("U", "Sö", "Ög", "Sm", "Vg")) and P3["Öl"]["q_bh"] > 0.3
NOW = R["today"]["overall"]
assert (NOW["median_stones_m"], NOW["median_random_m"], pc(NOW["within_500_stones"]), pc(NOW["within_500_random"]), num(NOW["auc"], 3)) == (364, 601, 60, 42, "0,620")
H2 = R["H2"]
assert (num(H2["auc_then"], 3), num(H2["auc_now"], 3), num(H2["delta_auc"], 3), [num(x, 3) for x in H2["ci95"]], H2["B"]) == \
    ("0,629", "0,620", "0,009", ["0,002", "0,017"], 2000)
H2P = {r["province"]: r for r in H2["provinces"]}
assert [k for k in H2P if H2P[k]["auc_then"] > H2P[k]["auc_now"]] == ["U", "Sö", "Ög", "Öl"]
H3, H3A, H3B, H3S = R["H3"]["overall"], R["H3"]["halves"]["A"], R["H3"]["halves"]["B"], R["H3"]["sites"]
assert (H3["median_stones_m"], H3["median_random_m"], pc(H3["within_500_stones"]), pc(H3["within_500_random"]), num(H3["auc"])) == (304, 1045, 67, 24, "0,78")
assert all(x["p"] < 1e-100 for x in (H3A, H3B, H3S))
S = R["secondary"]
assert (num(S["S1a"]["or"], 1), num(S["S1b"]["or"], 1)) == ("1,7", "3,5") and S["S1a"]["halves"]["replicated"] and S["S1b"]["halves"]["replicated"]
assert S["S1a"]["q_bh"] < 1e-30 and S["S1b"]["q_bh"] < 1e-100
assert all(S[k]["q_bh"] > 0.05 and not S[k]["halves"]["replicated"] for k in ("S2", "S3", "S4"))
assert (pc(S["S2"]["early"]), pc(S["S2"]["late"]), S["S4"]["n_bridge"], S["S4"]["median_bridge_m"], S["S4"]["median_other_m"]) == (84, 84, 82, 207, 309)
RB = R["robustness"]
R1 = RB["R1"]
assert set(R1) == {"AD750", "AD950", "AD1150", "AD1250", "AD550", "AD1550"} and all(v["p"] < 1e-30 for v in R1.values())
R1A = (min(v["auc"] for v in R1.values()), max(v["auc"] for v in R1.values()))
assert (num(R1A[0]), num(R1A[1])) == ("0,62", "0,64")
R2, R5 = RB["R2"], RB["R5"]
assert num(R2["auc"], 3) == "0,566" and R2["p"] < 1e-10 and R5["n_excluded"] == 108 and num(R5["auc"], 3) == "0,589" and R5["p"] < 1e-15
R6 = RB["R6"]
assert all(v["p"] < 1e-40 for v in R6.values()) and (num(R6["minus1"]["auc"], 3), num(R6["plus1"]["auc"], 3)) == ("0,630", "0,645")
R7 = RB["R7"]
assert (num(R7["r2km"]["water"]["auc"], 3), num(R7["r10km"]["water"]["auc"], 3), num(R7["r2km"]["grave"]["auc"], 3), num(R7["r10km"]["grave"]["auc"], 3)) == \
    ("0,628", "0,627", "0,707", "0,829")
T1 = R["T1"]
assert T1["n"] == 657 and T1["water_holds"] and T1["grave_holds"] and num(T1["water"]["auc"], 3) == "0,629" and num(T1["grave"]["auc"], 3) == "0,786"
D1, D2 = R["D1"], R["D2"]
assert (D1["n_all"], D1["n_moved"], num(D1["then"]["auc"], 3), num(D1["moved_only_then"]["auc"], 3)) == (2167, 1068, "0,650", "0,659")
assert (num(D2["water_viking"]["median_stones_km"], 1), num(D2["water_viking"]["median_random_km"], 1), D2["water_viking"]["n_stones"]) == ("3,6", "5,3", 2254)

# ---- the addendum ladder ----------------------------------------------------------------------------------------------
assert TR["plan"] == "analysplaner/2026-11-01-strand-trappan.md" and TR["H1"]["all_hold"] and TR["H3"]["all_hold"]
C = TR["counts"]
assert len(TR["H1"]["steps"]) == len(TR["H3"]["steps"]) == 9  # nio steg i tilläggsplanen
assert (C["reerected"], C["moved_runor"], C["not_staying_now"], C["carvers"], C["sure_carver_stones"], C["early"], C["late"]) == (101, 177, 295, 67, 399, 335, 252)
G1, G3, L1, L3 = TR["H1"]["rungs"], TR["H3"]["rungs"], TR["H1"]["lopo"], TR["H3"]["lopo"]
for G in (G1, G3):
    assert all(v["holds"] for v in G.values()) and not G["socken_slumpeffekt"]["warnings"]
assert all(v["holds"] for L in (L1, L3) for v in L.values()) and num(L1["U"]["share_kept"], 2) == "0,43"
assert abs(G1["huvud"]["auc"] - H1["auc"]) < 1e-9 and abs(G3["huvud"]["auc"] - H3["auc"]) < 1e-9  # same measures as the plan
MM1, MM3 = G1["socken_slumpeffekt"], G3["socken_slumpeffekt"]
assert (num(MM1["or"]), num(MM3["or"]), MM1["n_parishes"]) == ("1,82", "3,57", 373)
assert (G1["en_per_ristare"]["n_stones"], G1["utan_aterresta"]["n_stones"], G1["utan_flyttade_runor"]["n_stones"], G1["dagens_flyttregel"]["n_stones"]) == (767, 998, 922, 804)
LA1 = (min(v["auc"] for v in L1.values()), max(v["auc"] for v in L1.values()))
LA3 = (min(v["auc"] for v in L3.values()), max(v["auc"] for v in L3.values()))
GA1 = (min(v["auc"] for k, v in G1.items() if "auc" in v), max(v["auc"] for k, v in G1.items() if "auc" in v))
GA3 = (min(v["auc"] for k, v in G3.items() if "auc" in v), max(v["auc"] for k, v in G3.items() if "auc" in v))
assert (num(GA1[0]), num(GA1[1]), num(GA3[0]), num(GA3[1])) == ("0,61", "0,65", "0,72", "0,80")
assert (num(LA1[0]), num(LA1[1]), num(LA3[0]), num(LA3[1])) == ("0,62", "0,63", "0,74", "0,79")
DR1, DR3 = G1["dagens_flyttregel"], G3["dagens_flyttregel"]  # bara stenar som står kvar enligt den rättade regeln
assert (num(DR1["auc"], 3), num(DR3["auc"], 3), DR1["removed"], DR3["removed"]) == ("0,627", "0,794", 295, 295) and DR1["holds"] and DR3["holds"]
assert (pc(T1["water"]["within_500_stones"]), pc(T1["water"]["within_500_random"])) == (63, 46)
assert D1["moved_only_then"]["median_stones_m"] == 285 and D1["moved_only_then"]["n_stones"] == D1["n_moved"]

# ---- rapportversion 2: urvalet, kartorna och tidsordningen (utdata/strand/kontroll_v2.py -> kontroll_v2.json) ------------
K = json.load(open(os.path.join(SD, "kontroll_v2.json"), encoding="utf-8"))
KC, KS, KM, KO = K["corpus"], K["stones"], K["maps"], K["order"]
CSV_SHA = "4fca4baf47867e5c294d4c97d7dd34496d7fcc07996f68efddec1261a2bcb5ba"
PLAN_TXT = open(os.path.join(ROOT, "analysplaner", "2026-10-23-strand-och-gravfalt.md"), encoding="utf-8").read()
assert KC["locked_fingerprint"] == "d6cffd1578418f74" and not KC["locked_folder_exists"] and not KC["config_path_exists"]
assert KC["config_path"] == "data/cache/r/corpus/d6cffd1578418f74/corpus.csv"  # sökvägen i config.R, som inte finns längre
assert KC["kept_fingerprint"] == "5fdfd1e095bfb6fb" and KC["kept_csv_sha256"] == KC["plan_csv_sha256"] == CSV_SHA and CSV_SHA in PLAN_TXT
assert KC["now_fingerprint"] == "e83202e01a5e6d27"
LOST, MOVED_NOW, NOT_NOW = KS["lost_now"], KS["moved_corrected_rule"], KS["lost_or_moved"]
assert (KS["n"], KS["lost_locked"], LOST, MOVED_NOW, KS["lost_and_moved"], NOT_NOW) == (PO["n"], 253, 253, 43, ["Sö 249"], 295)
assert KS["lost_same_in_both"] and KS["same_as_stenar_csv"] and KS["missing_in_now"] == 0
assert NOT_NOW == C["not_staying_now"] == DR1["removed"] == LOST + MOVED_NOW - len(KS["lost_and_moved"])
assert KS["stays_corrected_rule"] == DR1["n_stones"] == DR3["n_stones"] == PO["n"] - NOT_NOW == 804
assert KS["t1_stays_and_not_runor"] == T1["n"] and KS["moved_runor"] == C["moved_runor"]
MO, MD = KM["overview"], KM["detail"]
assert (MO["n"], MO["lost"], MO["moved_corrected_rule"], MO["lost_or_moved"]) == (IL["n_overview"], 205, 36, 240)
assert (MD["n"], MD["lost"], MD["moved_corrected_rule"], MD["lost_or_moved"]) == (IL["n_stones"], 5, 2, 7)
assert KM["legend_sv"] == {"overview": "Runstenar som står kvar och ingår i studien (891)", "detail": "Runsten som står kvar (40)"}
# The trial run of 2026-10-23: after the plan's checksum, before its commit; it ran the tests but printed only progress
assert KO["trial_run_done_lines"] == ["H1 klart", "H2 klart", "H3 klart", "sekundära prov klara"]
assert not KO["trial_run_done_lines_have_numbers"] and not KO["trial_run_other_files_in_cache"]
assert KO["plan_sha256_file"]["created"] < KO["trial_run_log"]["created"] < KO["trial_run_log"]["modified"] < KO["plan_commit_c0afbc8"][:19]
assert KO["trial_run_log"]["created"][:10] == KO["plan_commit_c0afbc8"][:10] == "2026-10-23"
assert KO["distances_files"] == ["2026-10-23"] and KO["distances_log"]["modified"][:10] == "2026-10-23"
assert KO["statistics_computed_at"] == R["computed_at"] and R["computed_at"][:10] == KO["statistics_log"]["modified"][:10] == "2026-10-31"
ADD_TXT = re.sub(r"\s+", " ", open(os.path.join(ROOT, "analysplaner", "2026-10-31-strand-tillagg.md"), encoding="utf-8").read())
assert "steg 1b (`01b_marginal.R`) är körda för alla sex landskap 2026-10-23" in ADD_TXT  # det låsta tillägget säger detsamma
assert "den sparade inga resultat i någon fil som finns kvar" in ADD_TXT and "07d2ec0" in ADD_TXT
# The odds ratios are per halving of (distance + 250 m)
assert "both$closer_water <- -log2(both$then + 250); both$closer_grave <- -log2(both$grave + 250)" in open(os.path.join(SD, "03_statistik.R"), encoding="utf-8").read()
assert "both$closer <- -log2(both$v + 250)" in open(os.path.join(SD, "05_trappa.R"), encoding="utf-8").read()
# The code state: the analysis, its results and the maps are unchanged since CODE_COMMIT
_files = ["01_avstand.R", "01b_marginal.R", "02_r6.R", "03_statistik.R", "04_figurer.R", "05_trappa.R", "06_illustration.R", "config.R",
          "resultat.json", "trappan.json", "stenar.csv", "illustration.json", "karta_oversikt_sv.png", "karta_oversikt_en.png",
          "karta_detalj_sv.png", "karta_detalj_en.png"]
assert subprocess.run(["git", "diff", "--quiet", CODE_COMMIT, "--"] + [f"utdata/strand/{f}" for f in _files], cwd=ROOT).returncode == 0
assert subprocess.run(["git", "merge-base", "--is-ancestor", CODE_COMMIT, "origin/main"], cwd=ROOT).returncode == 0  # pushad
# The first version's publication date, from the site's export
_site = json.load(open(os.path.join(ROOT, "web", "content", "articles.json"), encoding="utf-8"))["posts"]
assert [p_["publishedAt"][:10] for p_ in _site if p_.get("slug") == "runstenarna-vid-sin-tids-vatten"] == [V1_PUBLISHED]
# The register's licence, as the repository states it
assert any("Kulturmiljöregistret via K-samsök" in ln and "CC0" in ln for ln in open(os.path.join(ROOT, "README.md"), encoding="utf-8"))

# ---- rapportversion 3: källställena (utdata/strand/kallcitat_v3.json, ordagranna citat lästa 2026-11-05) -----------------
KQ = json.load(open(os.path.join(SD, "kallcitat_v3.json"), encoding="utf-8"))
ST14, MC14, EK50 = KQ["stille_2014"], KQ["mcleod_2014"], KQ["ekholm_1950"]
assert ST14["volym"] == 5 and ST14["sidor"] == [137, 149] and "Futhark: International Journal of Runic Studies 5 (2014, publ. 2015): 137–49." in ST14["referens"]
assert [c["sida"] for c in ST14["citat"]] == [142, 142] and (ST14["vid_vatten"], ST14["med_bestämbar_plats"]) == (20, 53)
assert f"Det är alltså {ST14['vid_vatten']} stenar av de {ST14['med_bestämbar_plats']} som med mer eller mindre säkerhet" in ST14["citat"][0]["text"]
assert "har det också funnits en väg" in ST14["citat"][1]["text"]
assert MC14["sidhuvud"] == "No. 25:1–8" and MC14["sidor"] == [1, 8]
assert EK50["sidor"] == [137, 147] and EK50["invändningen"] == [min(c["sida"] for c in EK50["citat"]), max(c["sida"] for c in EK50["citat"])] == [138, 143]
assert any(c["sida"] == 140 and "forntidens samfärdsled" in c["text"] for c in EK50["citat"])
assert any(c["sida"] == 141 and "till lands och vatten" in c["text"] for c in EK50["citat"])
MCP, EKO = f"{MC14['sidor'][0]}–{MC14['sidor'][1]}", f"{EK50['invändningen'][0]}–{EK50['invändningen'][1]}"
# Figure 1: one stone in the map is both lost and moved (Sö 249), so the two counts overlap by one
assert MO["lost"] + MO["moved_corrected_rule"] - MO["lost_or_moved"] == 1 and KS["lost_and_moved"] == ["Sö 249"]
# The trial run printed its progress and the numbers of stones, points and grave fields, but no test result. The cache is not in
# the repository (kontroll_v2.json is the record); where it is present, the log is read here too.
RUNLOG = "/Volumes/2TB/cache/strand/run.log"
if os.path.exists(RUNLOG):
    _rl = open(RUNLOG, encoding="utf-8").read()
    assert f"stenar: {PO['n']} icke flyttade" in _rl and f"slumppunkter: {PO['n_random']}" in _rl and f"gravfält: {PO['n_gravfalt']}" in _rl
    assert not re.search(r"AUC|auc|median|\bp\s*[=<]|\bq\s*[=<]", _rl)
# The check file and builder of version 2 are in commit 6eae0af
assert subprocess.run(["git", "log", "-1", "--format=%ad", "--date=short", "6eae0af"], cwd=ROOT, capture_output=True, text=True,
                      check=True).stdout.strip() == "2026-11-05"
assert {"utdata/strand/kontroll_v2.py", "utdata/blogg/build/build_rapport_strand.py"} <= set(subprocess.run(
    ["git", "show", "--name-only", "--format=", "6eae0af"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split("\n"))

NAME = {"U": ("Uppland", "Uppland"), "Sö": ("Södermanland", "Södermanland"), "Ög": ("Östergötland", "Östergötland"),
        "Sm": ("Småland", "Småland"), "Vg": ("Västergötland", "Västergötland"), "Öl": ("Öland", "Öland")}
ORDER = ["U", "Sö", "Ög", "Sm", "Vg", "Öl"]


def rung(r, en=False, n=True):
    if en:
        return (f"{m(r['n_stones'], True) + ' stones, ' if n else ''}median {m(r['median_stones_m'], True)} against "
                f"{m(r['median_random_m'], True)} m, AUC {num(r['auc'], 2, True)}, {pfmt(r['p'], True)}")
    return (f"{m(r['n_stones']) + ' stenar, ' if n else ''}median {m(r['median_stones_m'])} mot {m(r['median_random_m'])} m, "
            f"AUC {num(r['auc'])}, {pfmt(r['p'])}")


def chart(sv):
    f = (lambda x: f"{100 * x:.1f}".replace(".", ",")) if sv else (lambda x: f"{100 * x:.1f}")
    st, rn = ("Runstenar", "Slumpmark i samma bygd") if sv else ("Runestones", "Random land in the same district")
    rows = [":::chart Inom 500 meter, procent" if sv else ":::chart Within 500 metres, percent"]
    for lab, r in ((("Vattnet år 1050", "The water of AD 1050"), H1), (("Dagens vatten (1949)", "Today's water (1949)"), NOW),
                   (("Registrerade gravfält", "Registered grave fields"), H3)):
        rows += [f"# {lab[0] if sv else lab[1]}", f"+{st} | {f(r['within_500_stones'])} | {m(r['n_stones'], not sv)} {'stenar' if sv else 'stones'}",
                 f"{rn} | {f(r['within_500_random'])} |"]
    # BlogBody reads the caption only from a line that starts with "Källa:" / "Source:"; the credit goes at its end
    rows += ["Källa: SGU:s strandförskjutningsmodell (CC BY 4.0), Rundata (ODbL) och Riksantikvarieämbetets kulturmiljöregister "
             "(CC0). Diagram: Vitki, efter SGU:s modell, Rundata och kulturmiljöregistret." if sv else
             "Source: SGU's shore displacement model (CC BY 4.0), Rundata (ODbL) and the Swedish register of ancient monuments "
             "(CC0). Chart: Vitki, after SGU's model, Rundata and the register.", ":::"]
    assert rows[-2].startswith("Källa:" if sv else "Source:")
    return "\n".join(rows)


def figure(name, lang, caption):
    """En karta ur 06_illustration.R som bild i inlägget (blog_figures.freeze) med bildtexten under."""
    with open(os.path.join(SD, f"{name}_{lang}.png"), "rb") as fh:
        url = blog_figures.freeze(fh.read())
    return f"![{caption.split('.')[0]}]({url})\n{caption}"


# The maps' legends say "står kvar" / "still in place", which is not true of every point (kontroll_v2.json); until the
# maps are redrawn, the captions say what the points are.
FIG1_SV = figure("karta_oversikt", "sv", f"Figur 1. Mälardalen år 1050 och i dag. Ljusblått är vatten då men land i dag. Rutan visar området i figur 2. Punkterna är de {MO['n']} stenar i studien som ligger inom kartan. Bildens förklaring kallar dem stenar som står kvar, men det gäller inte alla: {MO['lost']} av dem är försvunna och ritade på den plats där de är kända, och {MO['moved_corrected_rule']} räknas som flyttade med den rättade regeln från 27 oktober 2026, en av dem både och ({MO['lost_or_moved']} stenar sammanlagt). Karta: Vitki, efter SGU:s modell (CC BY 4.0) och Rundata.")
FIG1_EN = figure("karta_oversikt", "en", f"Figure 1. The Lake Mälaren region in AD 1050 and today. Light blue is water then but land today. The box shows the area of figure 2. The points are the {MO['n']} stones of the study that lie within the map. The legend in the image calls them stones still in place, which is not true of all: {MO['lost']} of them are lost and drawn at their recorded place, and {MO['moved_corrected_rule']} count as moved under the corrected rule of 27 October 2026, one of them both ({MO['lost_or_moved']} stones in all). Map: Vitki, after SGU's model (CC BY 4.0) and Rundata.")
FIG2_SV = figure("karta_detalj", "sv", f"Figur 2. Vad som mättes, kring Vassunda, Håtuna och Haga i Uppland: avståndet från varje sten (rött) och slumppunkt (grått) till närmaste vatten år 1050. Median här: stenarna {IL['median_stones_m']} meter, punkterna {IL['median_random_m']}. Bildens förklaring kallar de {MD['n']} stenarna stenar som står kvar; {MD['lost']} av dem är försvunna och ritade på sin kända plats, och {MD['moved_corrected_rule']} räknas som flyttade med den rättade regeln. Karta: Vitki, efter SGU:s modell och Rundata.")
FIG2_EN = figure("karta_detalj", "en", f"Figure 2. What was measured, around Vassunda, Håtuna and Haga in Uppland: the distance from each stone (red) and random point (grey) to the nearest water of AD 1050. Median here: stones {IL['median_stones_m']} metres, points {IL['median_random_m']}. The legend in the image calls all {MD['n']} stones still in place; {MD['lost']} of them are lost and drawn at their recorded place, and {MD['moved_corrected_rule']} count as moved under the corrected rule. Map: Vitki, after SGU's model and Rundata.")


SLUG = "runstenarna-vid-sin-tids-vatten"
title = "Runstenarna restes vid sin tids vatten – 64 procent inom 500 meter från vattnet år 1050, mot 46 procent av marken runt dem"
title_en = "The runestones were raised by the water of their time – 64 per cent within 500 metres of the water of AD 1050, against 46 per cent of the land around them"
summary = (f"Förregistrerad studie. Av {m(PO['n'])} vikingatida runstenar som inte räknas som flyttade står nästan två av tre "
           "inom 500 meter från vattnet som det låg år 1050, mot knappt hälften av marken runt dem; bland de "
           f"{T1['n']} som står kvar på sin plats enligt tre källor är andelen {pc(T1['water']['within_500_stones'])} procent. "
           "Det håller i båda halvorna av materialet, med en oberoende höjdmodell och i alla känslighetsanalyser. Gravfälten "
           "drar ännu starkare, och båda sambanden finns kvar när det andra hålls lika.")
summary_en = (f"Pre-registered study. Of {m(PO['n'], True)} Viking-Age runestones not counted as moved, almost two in three stand "
              "within 500 metres of the water as it lay in AD 1050, against fewer than half of the land around them; among the "
              f"{T1['n']} that stand in place according to three sources, the share is {pc(T1['water']['within_500_stones'])} per "
              "cent. This holds in both halves of the material, with an independent elevation model and in every sensitivity "
              "analysis. The grave fields draw even more strongly, and both associations remain when the other is held equal.")
CITE_EN = (f"Kvant, V. ({TODAY[:4]}). {title_en}. Research report, report version {REPORT_VERSION}; analysis in Vitki {APP_VERSION}. "
           f"https://vitkirunor.se/en/forskningsrapporter/{SLUG}")
FAM = "https://vitkirunor.se/forskningsrapporter/familjegrupper-vid-gravfalten"
VAG = "https://vitkirunor.se/forskningsrapporter/ristningen-vand-mot-vagen"
FAM_EN, VAG_EN = (u.replace("vitkirunor.se/", "vitkirunor.se/en/") for u in (FAM, VAG))
assert FAM_EN == "https://vitkirunor.se/en/forskningsrapporter/familjegrupper-vid-gravfalten"

# The change log (mallen: a new version ends with what, why and when)
LOG_SV = f"""## Ändringslogg

**Version 1, {V1_PUBLISHED}.** Publicerad {V1_PUBLISHED}. Samma morgon, före publiceringen, ändrades utkastet (commit {CODE_COMMIT}, vars meddelande bara nämner kartorna): kartorna fick källraden ”Karta: Vitki, efter …”, syftesmeningen i inledningen kortades, och meningen om gravfälten i planens prov med andra radier för slumppunkterna ströks ur 5.2 utan att skälet skrevs ned. Den publicerade versionen saknade därför gravfältens resultat i det provet, och planens jämförelse med de flyttade stenarna hade aldrig kommit med; planen säger att båda ska redovisas.

**Version 2, 2026-11-05.** Rättelser efter en granskning inför arkiveringen i Zenodo. Analysen, resultatfilerna och slutsatsen är oförändrade; kartorna är inte omritade.

- **Urvalet.** Version 1 beskrev de {m(PO['n'])} stenarna som stenar som står kvar på sin plats. Det var fel för {NOT_NOW} av dem: {LOST} är försvunna och mäts på den plats där de är kända, och {MOVED_NOW} räknas som flyttade med den regel som rättades den 27 oktober 2026, efter att planen låstes (en sten är både och). Sammanfattningen, inledningen, materialbeskrivningen, bildtexterna till figur 1 och 2, steget med den rättade regeln i 5.3 och svaghet 4 säger nu vad urvalet är, och Material beskriver den regel som användes. Slutsatsen står sig: utan de {NOT_NOW} stenarna är AUC {num(DR1['auc'], 3)} för vattnet och {num(DR3['auc'], 3)} för gravfälten, och av de {T1['n']} stenar som står kvar enligt tre källor står {pc(T1['water']['within_500_stones'])} procent inom 500 meter från vattnet år 1050.
- **Provkörningen den 23 oktober** räknade igenom proven, vilket version 1 inte sade; den skrev bara ut förloppet. Tidslinjen har fått dagen då avstånden räknades.
- **Två resultat som planen kräver** saknades: gravfälten med slumppunkter inom två och tio kilometer och jämförelsen med de flyttade stenarna. De står nu i 5.2.
- **Tidigare forskning.** Invändningen mot Klos tillskrivs nu Mats G. Larsson (2010), som McLeod (2014) hänvisar till, och inledningen nämner tidigare arbeten om stenarna och vattnet (Ekholm 1950, Larsson 1990, Stille 2014) och Larssons kritik av hur Klos mätte vattnet.
- **Vattnet och gravfälten.** Version 1 kallade sambanden oberoende, vilket säger mer än modellen visar; texten säger nu att vart och ett finns kvar när det andra hålls lika, och att oddskvoterna gäller en halvering av avståndet plus 250 meter.
- **Källor och form.** Copernicus-attributionen följer licensens lydelse, kulturmiljöregistrets licens (CC0) anges, den ociterade referensen till projektets metodbeskrivning är struken (de två andra Kvant 2026 har fått bokstäverna a och b), de engelska länkarna går till de engelska sidorna, diagrammet anger att Vitki har gjort det, och Data och kod anger kodläget med en commit och att den låsta korpusens mapp saknas.

**Version {REPORT_VERSION}, {TODAY}.** En andra granskning inför arkiveringen i Zenodo gick igenom det som version 2 ändrade. Analysen, resultatfilerna och kartorna är oförändrade.

- **Källorna.** McLeod (2014) har sidorna {MCP}, inte 1–18. Ekholms (1950) invändning mot gravfälten börjar på s. {EK50['invändningen'][0]}, så sidorna anges nu som {EKO}. Stille (2014) återges nu med det som står på s. {ST14['citat'][0]['sida']}: {ST14['vid_vatten']} av de {ST14['med_bestämbar_plats']} stenar vars plats går att bestämma stod vid vatten; version 2 skrev ”en stor del”. Artikeln och referensen är kontrollerade mot tidskriften.
- **Provkörningen den 23 oktober** skrev ut förloppet och antalet stenar, slumppunkter och gravfält, men inga provresultat; version 2 sade att den inte skrev ut några siffror. Tidslinjen har fått provkörningen.
- **Figur 1.** Bildtexten säger att en av stenarna är både försvunnen och flyttad, så att {MO['lost']} och {MO['moved_corrected_rule']} blir {MO['lost_or_moved']}.
- **Korthetsrutan** säger inte längre att en sten oftast restes där både vattnet och gravfälten fanns, vilket rapporten inte mäter; den säger det modellen visar, att de mest sannolika platserna för en runsten låg nära båda.
- **Ändringar som version 2 gjorde men inte skrev in i loggen:** sidorna för Ekholm (1950, s. 137–147) och McLeod (2014) angavs, Rundatas licens (ODbL) lades till i diagrammets källrad, och diskussionen lade till att fyndet stämmer med det Ekholm (1950) menade utifrån enskilda stenar i Uppland.
- **Data och kod** anger commit för kontrollfilen och byggskriptet för version 2 (6eae0af) och nämner filen med de citerade källställena."""
LOG_EN = f"""## Change log

**Version 1, {V1_PUBLISHED}.** Published {V1_PUBLISHED}. The same morning, before publication, the draft was changed (commit {CODE_COMMIT}, whose message mentions only the maps): the maps got the source line "Map: Vitki, after …", the sentence of aim in the introduction was shortened, and the sentence on the grave fields in the plan's test with other radii for the random points was removed from 5.2 without a reason being recorded. The published version therefore lacked the grave fields' result in that test, and the plan's comparison with the moved stones had never been included; the plan says that both are to be reported.

**Version 2, 2026-11-05.** Corrections after a review before archiving in Zenodo. The analysis, the result files and the conclusion are unchanged; the maps have not been redrawn.

- **The selection.** Version 1 described the {m(PO['n'], True)} stones as stones that still stand in place. That was wrong for {NOT_NOW} of them: {LOST} are lost and measured at their recorded place, and {MOVED_NOW} count as moved under the rule that was corrected on 27 October 2026, after the plan was locked (one stone is both). The abstract, the introduction, the description of the material, the captions of figures 1 and 2, the step with the corrected rule in 5.3 and weakness 4 now say what the selection is, and the Material section describes the rule that was used. The conclusion stands: without the {NOT_NOW} stones the AUC is {num(DR1['auc'], 3, True)} for the water and {num(DR3['auc'], 3, True)} for the grave fields, and of the {T1['n']} stones that stand in place according to three sources, {pc(T1['water']['within_500_stones'])} per cent stand within 500 metres of the water of AD 1050.
- **The test run of 23 October** ran through the tests, which version 1 did not say; it printed only its progress. The timeline now has the day the distances were computed.
- **Two results required by the plan** were missing: the grave fields with random points within two and ten kilometres, and the comparison with the moved stones. They are now in 5.2.
- **Earlier research.** The objection to Klos is now attributed to Mats G. Larsson (2010), whom McLeod (2014) cites, and the introduction names earlier work on the stones and the water (Ekholm 1950, Larsson 1990, Stille 2014) and Larsson's criticism of how Klos measured the water.
- **Water and grave fields.** Version 1 called the associations independent, which says more than the model shows; the text now says that each remains when the other is held equal, and that the odds ratios are per halving of the distance plus 250 metres.
- **Sources and form.** The Copernicus attribution follows the wording of the licence, the register's licence (CC0) is given, the uncited reference to the project's method description is removed (the two other Kvant 2026 are now a and b), the English links go to the English pages, the chart says that Vitki made it, and Data and code gives the code state as a commit and says that the locked corpus's folder is missing.

**Version {REPORT_VERSION}, {TODAY}.** A second review before archiving in Zenodo checked what version 2 changed. The analysis, the result files and the maps are unchanged.

- **Sources.** McLeod (2014) has pages {MCP}, not 1–18. Ekholm's (1950) objection to the grave fields begins on p. {EK50['invändningen'][0]}, so the pages are now given as {EKO}. Stille (2014) is now given with what p. {ST14['citat'][0]['sida']} says: {ST14['vid_vatten']} of the {ST14['med_bestämbar_plats']} stones whose place can be determined stood by water; version 2 wrote "a large share". The article and the reference have been checked against the journal.
- **The test run of 23 October** printed its progress and the numbers of stones, random points and grave fields, but no test results; version 2 said that it printed no figures. The timeline now has the test run.
- **Figure 1.** The caption says that one of the stones is both lost and moved, so that the {MO['lost']} and the {MO['moved_corrected_rule']} make {MO['lost_or_moved']}.
- **The essentials box** no longer says that a stone was most often raised where both the water and the grave fields were, which the report does not measure; it says what the model shows, that the places most likely to have a runestone lay near both.
- **Changes that version 2 made but did not log:** the pages of Ekholm (1950, pp. 137–147) and McLeod (2014) were given, the licence of Rundata (ODbL) was added to the chart's source line, and the discussion added that the finding fits what Ekholm (1950) argued from single stones in Uppland.
- **Data and code** gives the commit of the check file and builder of version 2 (6eae0af) and lists the file with the quoted source passages."""

body = f"""*Viktor Kvant, oberoende forskare. Fullt prövat fynd. Rapportversion {REPORT_VERSION}, {TODAY} (första versionen publicerad {V1_PUBLISHED}). Tidslinje: {TL_SV}. Analysen är gjord i Vitki {APP_VERSION}. Licens CC BY 4.0. Den engelska versionen är den kanoniska för citering: {CITE_EN}. Nyckelord: runstenar, vikingatid, placering, strandförskjutning, landhöjning, gravfält, rumslig statistik, förregistrering. Konkurrerande intressen: inga. Finansiering: ingen.*

## Sammanfattning

**Bakgrund och syfte.** Var runstenarna restes har diskuterats länge: vid gravfält, vid vägar och broar, vid gårdar och gränser. Vattnet är svårare att mäta, eftersom landet har höjt sig sedan vikingatiden och dagens strand inte är stenarnas. Frågan här är om stenarna restes närmare sin egen tids vatten än marken runt omkring, och om det sambandet finns kvar när närheten till gravfälten hålls lika.
**Material.** {m(PO['n'])} vikingatida runstenar som inte räknas som flyttade i den låsta korpusen ({LOST} av dem är försvunna och mäts på sin kända plats), i Uppland, Södermanland, Östergötland, Småland, Västergötland och på Öland, och {m(PO['n_random'])} slumpvisa punkter på land inom fem kilometer från stenarna. Vattnet år 1050 enligt Sveriges geologiska undersöknings (SGU) strandförskjutningsmodell, gravfälten ur Riksantikvarieämbetets kulturmiljöregister.
**Metod.** Förregistrerad studie. Avståndet till närmaste vatten jämförs mellan stenar och punkter med Wilcoxons rangsummetest och AUC, sannolikheten att en sten står närmare än en punkt. Intern replikering i två halvor, sju känslighetsprov i planen och nio känslighetsanalyser enligt en låst tilläggsplan.
**Resultat.** {pc(H1['within_500_stones'])} procent av stenarna står inom 500 meter från vattnet år 1050, mot {pc(H1['within_500_random'])} procent av punkterna; medianavståndet är {H1['median_stones_m']} mot {H1['median_random_m']} meter, AUC {num(H1['auc'])}, {pfmt(H1['p'])}. Det håller i båda halvorna, i fem av sex landskap, för andra årtal mellan 550 och 1550, med en oberoende höjdmodell och i alla känslighetsanalyser, också jämfört med marken i samma socken. Gravfälten drar starkare: {pc(H3['within_500_stones'])} mot {pc(H3['within_500_random'])} procent inom 500 meter, AUC {num(H3['auc'])}. Båda sambanden finns kvar när det andra hålls lika. Av de {T1['n']} stenar som står kvar på sin plats enligt tre källor står {pc(T1['water']['within_500_stones'])} procent inom 500 meter från vattnet (AUC {num(T1['water']['auc'], 3)}), och utan de {LOST} försvunna stenarna och de {MOVED_NOW} som den rättade regeln för flyttade stenar räknar bort är AUC {num(DR1['auc'], 3)} för vattnet och {num(DR3['auc'], 3)} för gravfälten. Dåtidens vatten stämmer något bättre med stenarna än dagens, men skillnaden är liten.
**Slutsats.** De som reste runstenarna valde platser nära vattnet, och ännu oftare nära gravfälten, inom bygder som redan låg vid vatten. Den största svagheten är att modellen för vattnet år 1050 är grov: {PO['stones_in_water_1050']} av stenarna hamnar i modellens vatten.

## 1. Inledning

Var runstenarna restes har diskuterats länge. Gunnar Ekholm (1950, s. {EKO}) invände mot bilden av stenarna som gravfältens monument: i Uppland följde de enligt honom i stor utsträckning de gamla färdvägarna till lands och vatten, och en sten på Ängby mark vid Knivsta restes för att synas från ån, ”forntidens samfärdsled”. Mats G. Larsson (1990) fann i en genomgång av stenarnas placering att gravar, vägar med broar och vadställen och troliga ägogränser var ungefär lika vanliga lägen (Larsson 2010, s. 249). Torun Zachrisson (1998) har satt stenarna i samband med gård, gräns och gravfält, och Lydia Klos (2009) har hävdat att de flesta restes vid gravfält. Mats G. Larsson (2010, s. 252) har invänt att Klos därmed överbetonar gravfälten på bekostnad av andra lägen, framför allt ägogränserna (se också McLeod 2014). Per Stille (2014, s. {ST14['citat'][0]['sida']}) fann i Tiohärad i Småland att {ST14['vid_vatten']} av de {ST14['med_bestämbar_plats']} stenar vars plats går att bestämma med mer eller mindre säkerhet stod vid vatten, vid vattendrag eller broställen, där också en väg bör ha gått. Brostenarna, som berättar om broar och vägbyggen över vatten och sank mark, visar att vattnet hörde till stenarnas sammanhang.

Att mäta närheten till vatten är svårt. Landet har höjt sig sedan vikingatiden, i Mälardalen med omkring fem meter, så en sten som stod vid en vik kan i dag stå på torr mark, och en sten vid dagens strand kan ha stått långt från vattnet. Klos (2009) mätte också avståndet till vatten, men i regel utan vikingatidens havsnivå, vilket Larsson (2010, s. 251) såg som den grundläggande bristen i den delen av hennes undersökning: Mälaren blev en insjö och inte den havsvik den var. SGU:s strandförskjutningsmodell (SGU 2022, efter Påsse & Daniels 2015) ger en öppen modell över hela landet för var vattnet låg vid olika tider.

Vi känner inte till någon studie som har mätt avståndet till vattnet på stenarnas egen tid för hela det svenska materialet, med en modell för strandförskjutningen, utan de stenar som räknas som flyttade och med en jämförelse med marken i samma bygd. Syftet är att göra det och pröva om sambandet finns kvar när närheten till gravfälten hålls lika.

## 2. Förregistrering: hypotes och plan

Hypoteserna, måtten och tolkningsreglerna skrevs ned i en analysplan den 23 oktober 2026, innan något avstånd hade räknats. Planen har kontrollsumman SHA-256 `{SHA['2026-10-23-strand-och-gravfalt']}…` och lades in i versionshanteringen samma kväll. Före låsningen var bara datakällorna hämtade, lagren listade, antalet stenar per landskap räknat och stilgruppernas mittår sammanställda för att välja årtal (median 1035). En provkörning samma kväll, efter att planen hade fått sin kontrollsumma men före incheckningen, räknade igenom proven men skrev bara ut förloppet och antalet stenar, slumppunkter och gravfält, inga provresultat; inga resultat från den finns kvar, och statistiken lästes först den 31 oktober.

Riktningen var väntad. Projektets tidigare mått, med en grov landhöjning och med flyttade stenar, hade redan visat att stenarna står närmare vatten och gravfält än marken runt dem. Studien prövar alltså om ett känt mönster håller med bättre data, inte ett nytt.

Planens hypoteser, ordagrant: **H1 (primärt): stenarna står närmare vattnet år 1050 än slumppunkterna.** **H2: närheten är tydligare mot dåtidens vatten än mot dagens.** **H3: gravfälten, på samma urval** (stenarna står närmare registrerade gravfält än slumppunkterna). H1 *håller* om fem villkor är uppfyllda: p under 0,05 och AUC över 0,5 sammantaget, samma i båda halvorna, samma när stenar inom 200 meter från varandra slås ihop till en plats, samma för fyra andra årtal inom 200 år (750, 950, 1150 och 1250), och samma med bara havet utan modellens sjöar. H3 håller om det gäller sammantaget, i båda halvorna och för platserna. H2 kallas tydligare bara om hela 95 %-intervallet för skillnaden ligger över noll.

Två tillägg låstes senare, båda innan de räknades. Den 31 oktober (SHA-256 `{SHA['2026-10-31-strand-tillagg']}…`), innan statistiken kördes: H1 och H3 prövas också på de stenar som står kvar enligt tre källor, eftersom regeln för flyttade stenar hade rättats den 27 oktober, efter att planen låstes. Den 1 november (SHA-256 `{SHA['2026-11-01-strand-trappan']}…`), när planens resultat var kända: nio fasta känslighetsanalyser för avstånd, motsvarande dem projektet gör för andra fynd. De är konfirmatoriska i den meningen att stegen och gränserna låstes innan de räknades, men de valdes efter att huvudresultatet var känt.

## 3. Material

- **Stenarna.** Svenska vikingatida runstenar i Samnordisk runtextdatabas (Rundata), i den version som låstes i planen. Av dem har vi tagit de som har koordinater och inte räknas som flyttade enligt regeln som den var när planen låstes: Rundatas placering nämner inte kyrka, vapenhus, mur eller vägg, museum, samling, park eller liknande ställen dit stenar har förts, och platsen är inte en kyrka, kyrkogård, kyrkoruin, prästgård, ett kloster, slott, en skola eller ett museum. Regeln rättades den 27 oktober 2026, efter att planen låstes, så att den också räknar stenar vars placering säger att de har flyttats eller nämner en annan plats än fyndplatsen; med den rättade regeln är {MOVED_NOW} av stenarna här flyttade. Försvunna stenar räknas inte bort av regeln: {LOST} av stenarna är försvunna och mäts på den plats där de är kända. Stenarna i urvalet står alltså inte alla kvar på sin plats; känslighetsanalyserna i 5.3 prövar resultatet utan dem. Bara landskap med minst 20 stenar i urvalet prövas: Uppland ({P1['U']['n_stones']}), Södermanland ({P1['Sö']['n_stones']}), Östergötland ({P1['Ög']['n_stones']}), Småland ({P1['Sm']['n_stones']}), Västergötland ({P1['Vg']['n_stones']}) och Öland ({P1['Öl']['n_stones']}), sammanlagt {m(PO['n'])}. De {sum(PO['other_provinces_not_tested'].values())} stenarna i övriga landskap prövas inte. Bara runstenar.
- **Vattnet.** SGU:s strandförskjutningsmodell, öppna data version 1.0 (2022, CC BY 4.0). Den bygger på strandförskjutningskurvor över hela landet, en modell för landhöjningen och en höjdmodell med 50 meters upplösning. Vattnet år 1050 är modellens hav och sjöar i tidssnittet 900 år före 1950; dagens vatten är tidssnittet för år 1949. Avstånden räknas på ett rutnät med 25 meters celler.
- **Gravfälten.** Riksantikvarieämbetets kulturmiljöregister via K-samsök (öppna data, CC0), hämtat den 12 oktober 2026: {m(PO['n_gravfalt'])} registrerade gravfält med koordinater.
- **Den oberoende höjdmodellen.** Copernicus DEM GLO-30 (omkring 30 meter), med landskapets landhöjning sedan vikingatiden som höjdgräns.
- **Dateringen** efter stenens ornamentikstil (Gräslund 2006): {PO['n_dated']} av stenarna.
- **Halvorna** är projektets fasta indelning socken för socken: {PO['halves']['A']} och {PO['halves']['B']} stenar.

{FIG1_SV}

## 4. Metod

**4.1 Måttet och jämförelsen.** För varje sten och varje punkt räknas avståndet till närmaste vatten år 1050, till dagens vatten och till närmaste gravfält; en punkt i vattnet får avståndet noll. Jämförelsen är en nollmodell: för varje landskap dras tio slumpvisa punkter per sten, likformigt inom fem kilometer från landskapets stenar, och bara punkter som är land både år 1050 och år 1949 behålls. Punkterna ligger alltså i de bygder där stenar restes, så provet gäller var i bygden stenen står, inte var bygderna ligger. Stenarna och punkterna jämförs med Wilcoxons rangsummetest (Wilcoxon 1945; Mann & Whitney 1947), ensidigt. Effekten anges som medianerna, andelen inom 500 meter och AUC, sannolikheten att en slumpvis vald sten står närmare än en slumpvis vald punkt (0,5 betyder ingen skillnad). Figur 2 visar mätningen i en bygd.

{FIG2_SV}

**4.2 Korrigering och replikering.** Varje hypotes prövas i var halva för sig. Landskapen prövas var för sig med Benjamini–Hochberg-korrigering (Benjamini & Hochberg 1995) över de sex, och de sekundära proven likaså över de fem. Skillnaden mellan dåtidens och dagens vatten (H2) får ett 95 %-intervall ur 2 000 bootstrapurval där stenarna dras plats för plats.

**4.3 Känslighetsanalyserna.** Planens sju prov och dess beskrivande jämförelse med flyttade stenar, tilläggets prov och tilläggsplanens nio steg står med sina resultat i 5.2 och 5.3. Socknen som slumpeffekt är en logistisk regression (Bates m.fl. 2015) där punkterna får den närmaste stenens socken. När stenar tas bort tas också de punkter bort som hör till dem. Ett steg håller när AUC är över 0,5 och p under 0,05; utan ett landskap i taget krävs signifikans bara där minst två tredjedelar av stenarna är kvar.

**4.4 Avvikelser från planen.** Statistiken kördes åtta dagar efter att avstånden räknades, efter tillägget för flyttade stenar; planens prov är oförändrade. De {m(PO['distances_at_tile_margin'])} avstånd som nådde kanten av beräkningsrutorna, nästan alla för bara havet långt inne i landet, räknades om på ett rutnät med 100 meters celler över hela landskapet; planen anger ingen cellstorlek. Känslighetsanalyserna i tilläggsplanen lades till efter att planens resultat var kända (se 2). I övrigt inga.

## 5. Resultat

**5.1 Vattnet år 1050 (H1), gravfälten (H3) och dagens vatten (H2).** Av de {m(PO['n'])} stenarna står {pc(H1['within_500_stones'])} procent inom 500 meter från vattnet år 1050, mot {pc(H1['within_500_random'])} procent av de {m(PO['n_random'])} punkterna; inom en kilometer {pc(H1['within_1000_stones'])} mot {pc(H1['within_1000_random'])} procent. Medianavståndet är {H1['median_stones_m']} mot {H1['median_random_m']} meter, AUC {num(H1['auc'], 3)}, {pfmt(H1['p'])}. Halva A ({HA['n_stones']} stenar i {HA['n_parishes']} socknar): AUC {num(HA['auc'], 3)}, {pfmt(HA['p'])}. Halva B ({HB['n_stones']} stenar i {HB['n_parishes']} socknar): AUC {num(HB['auc'], 3)}, {pfmt(HB['p'])}. Med {HS['n_sites']} platser i stället för stenar: AUC {num(HS['auc'], 3)}, {pfmt(HS['p'])}. H1 *håller* enligt alla fem villkoren. I klartext: jämför man en runsten med en slumpvis vald plats i samma bygd står runstenen närmare dåtidens vatten i {pc(H1['auc'])} fall av 100, och nästan två av tre stenar står inom 500 meter från vattnet, mot knappt hälften av marken.

Per landskap, med q korrigerat över de sex: AUC {num(P1['U']['auc'])} i Uppland, {num(P1['Sö']['auc'])} i Södermanland, {num(P1['Ög']['auc'])} i Östergötland, {num(P1['Sm']['auc'])} i Småland och {num(P1['Vg']['auc'])} i Västergötland, alla q < 0,01, och {num(P1['Öl']['auc'])} på Öland, q = {num(P1['Öl']['q_bh'], 3)}, där de {P1['Öl']['n_stones']} stenarna går åt samma håll men inte räcker.

Gravfälten (H3): {pc(H3['within_500_stones'])} procent av stenarna står inom 500 meter från ett registrerat gravfält, mot {pc(H3['within_500_random'])} procent av punkterna; medianen är {H3['median_stones_m']} mot {m(H3['median_random_m'])} meter, AUC {num(H3['auc'], 3)}, {pfmt(H3['p'])}. Halva A: AUC {num(H3A['auc'], 3)}, halva B: AUC {num(H3B['auc'], 3)}, platserna: AUC {num(H3S['auc'], 3)}, alla {pfmt(max(H3A['p'], H3B['p'], H3S['p']))}. H3 *håller*, i samma fem landskap som H1. I klartext: två av tre stenar står inom 500 meter från ett gravfält, mot en av fyra platser i bygden.

Dagens vatten (H2): mot vattnet år 1949 står {pc(NOW['within_500_stones'])} procent av stenarna inom 500 meter, mot {pc(NOW['within_500_random'])} procent av punkterna, AUC {num(NOW['auc'], 3)}. Skillnaden i AUC mot dåtidens vatten är {num(H2['delta_auc'], 3)}, 95 %-intervall {num(H2['ci95'][0], 3)} till {num(H2['ci95'][1], 3)}. Hela intervallet ligger över noll, så närheten är enligt planen *tydligare* mot dåtidens vatten, men skillnaden är liten. Den finns i Uppland, Södermanland, Östergötland och på Öland; i Småland och Västergötland passar dagens vatten lika bra eller något bättre.

{chart(True)}

**5.2 Planens känslighetsprov.** Alla håller för H1:

- Andra årtal: AUC mellan {num(R1A[0])} och {num(R1A[1])} för alla sex, från år 550 till år 1550, alla {pfmt(max(v['p'] for v in R1.values()))}.
- Bara havet, utan modellens sjöar: {rung(R2)}. I Östergötland, Småland och Västergötland säger provet inget, eftersom de flesta stenar och punkter där ligger mil från havet.
- Utan de {R5['n_excluded']} stenar som står i modellens vatten år 1050: {rung(R5)}.
- Den oberoende höjdmodellen: landhöjningen en meter lägre: {rung(R6['minus1'], n=False)}; lika: {rung(R6['zero'], n=False)}; en meter högre: {rung(R6['plus1'], n=False)}. Mönstret hänger alltså inte på SGU:s höjdmodell.
- Punkter inom två kilometer: AUC {num(R7['r2km']['water']['auc'], 3)}; inom tio kilometer: AUC {num(R7['r10km']['water']['auc'], 3)}. För gravfälten växer skillnaden med radien (AUC {num(R7['r2km']['grave']['auc'], 3)} och {num(R7['r10km']['grave']['auc'], 3)}), medan radien nästan inte ändrar något för vattnet.

Planens beskrivande jämförelse med de flyttade stenarna medräknade ({m(D1['n_all'])} stenar, varav {m(D1['n_moved'])} flyttade, och nya slumppunkter kring dem): AUC {num(D1['then']['auc'], 3)} mot vattnet år 1050. De flyttade stenarna för sig, mätta där de står i dag, oftast vid kyrkor: median {D1['moved_only_then']['median_stones_m']} meter, AUC {num(D1['moved_only_then']['auc'], 3)}. De står alltså ännu närmare dåtidens vatten än stenarna i urvalet, så att räkna med dem hade gjort sambandet något starkare, inte svagare.

Vatten och gravfält samtidigt, i en logistisk regression med landskapet konstant och avstånden på logaritmisk skala, räknade som avståndet plus 250 meter så att också avståndet noll går att använda: när avståndet till vattnet plus 250 meter halveras blir oddsen att platsen har en runsten {num(S['S1a']['or'], 2)} gånger så stora (95 %-intervall {num(S['S1a']['lo'], 2)}–{num(S['S1a']['hi'], 2)}), med avståndet till gravfälten lika; för gravfälten är oddskvoten {num(S['S1b']['or'], 2)} ({num(S['S1b']['lo'], 2)}–{num(S['S1b']['hi'], 2)}). Båda håller i båda halvorna och efter korrigering. I klartext: vattnet är inte bara ett tecken på att gravfälten ligger där, och tvärtom; gravfälten väger ungefär dubbelt så tungt.

De övriga sekundära proven håller inte: andelen inom en kilometer från vattnet är densamma för tidiga och sena stenar ({pc(S['S2']['early'])} procent), kristna markörer gör ingen skillnad ({pfmt(S['S3']['p'])}), och bro- och vägstenarna står något närmare ({S['S4']['median_bridge_m']} mot {S['S4']['median_other_m']} meter i median) men inte säkert ({pfmt(S['S4']['p'])}, q = {num(S['S4']['q_bh'], 2)}).

**5.3 Känslighetsanalyserna.** Bara stenar som står kvar på sin plats enligt tre källor (den låsta korpusen, den rättade regeln för flyttade och försvunna stenar och Runor 2020; {T1['n']} stenar): {pc(T1['water']['within_500_stones'])} procent inom 500 meter från vattnet år 1050, mot {pc(T1['water']['within_500_random'])} procent av punkterna, AUC {num(T1['water']['auc'], 3)}; gravfälten AUC {num(T1['grave']['auc'], 3)}, båda {pfmt(max(T1['water']['p'], T1['grave']['p']))}. I tilläggsplanens nio analyser håller alla steg för både vattnet och gravfälten. För vattnet:

- Halvorna: se 5.1.
- Utan ett landskap i taget: AUC mellan {num(LA1[0])} och {num(LA1[1])}, också utan Uppland, när bara {pc(L1['U']['share_kept'])} procent av stenarna är kvar ({pfmt(L1['U']['p'])}).
- Socknen som enhet ({G1['socken']['n_parishes']} socknar): {rung(G1['socken'])}.
- Socknen som slumpeffekt: oddskvot {num(MM1['or'])} när avståndet plus 250 meter halveras (95 %-intervall {num(MM1['lo'])}–{num(MM1['hi'])}), {pfmt(MM1['p'])}; modellen konvergerade utan varningar. I klartext: också jämfört med marken i samma socken står stenarna närmare vattnet.
- En sten per säker ristare ({C['carvers']} ristare): {rung(G1['en_per_ristare'])}.
- Utan återresta stenar ({C['reerected']} bort): {rung(G1['utan_aterresta'])}.
- Utan stenar som Runor anger som flyttade ({C['moved_runor']} bort): {rung(G1['utan_flyttade_runor'])}.
- Bara stenar som står kvar enligt den rättade regeln från 27 oktober 2026 ({NOT_NOW} bort: {LOST} försvunna och {MOVED_NOW} flyttade, en av dem både och): {rung(DR1)}; gravfälten AUC {num(DR3['auc'], 3)}.
- De tidiga stenarna, före 1050: {rung(G1['tidiga'])}. De sena: {rung(G1['sena'])}.

För gravfälten ligger AUC mellan {num(GA3[0])} och {num(GA3[1])} i alla steg, utan ett landskap i taget mellan {num(LA3[0])} och {num(LA3[1])}, och socknen som slumpeffekt ger oddskvoten {num(MM3['or'])} ({num(MM3['lo'])}–{num(MM3['hi'])}), {pfmt(MM3['p'])}.

Studien är fristående, så korrigeringen gäller inom planen och inte bland de samband projektet justerar gemensamt. Inga handkodade drag ingår; felkällan är modellen för vattnet (se 6).

## 6. Diskussion

**Vad fyndet säger.** De som reste runstenarna valde platser nära vattnet. Jämförelsen gäller marken i samma bygd, och sambandet finns kvar socken för socken, så det beror inte bara på att bygderna låg vid vatten. Det beror inte heller på några få landskap, platser eller ristare, inte på stenar som har flyttats, försvunnit eller rests upp på nytt, och inte på SGU:s höjdmodell. Det gällde både före och efter 1050. Gravfälten drar starkare, och vart och ett av sambanden finns kvar när det andra hålls lika: de mest sannolika platserna för en runsten låg nära både vatten och gravfält.

**Dåtidens och dagens vatten.** Att dåtidens vatten stämmer bara lite bättre än dagens betyder inte att landhöjningen saknar betydelse. I de flesta trakter har stranden flyttat sig mindre än de hundratals meter som skiljer stenarna från punkterna (figur 2), och sjöarna ligger kvar. Modellen för år 1050 behövs främst för att fyndet inte ska vara ett resultat av dagens kust.

**Mot tidigare forskning.** Att två av tre stenar står inom 500 meter från ett gravfält stöder Klos (2009) och stämmer med att stenar i familjegrupper oftare står vid gravfält än ensamma stenar ([Kvant 2026a]({FAM})). Att vattnet finns kvar när gravfälten hålls lika ger samtidigt Larsson (2010) och McLeod (2014) rätt i att gravfälten inte är hela svaret. Fyndet passar med att stenarnas text oftast vändes mot vägen ([Kvant 2026b]({VAG})): stenarna restes där människor färdades, till lands och till sjöss, som Ekholm (1950) menade utifrån enskilda stenar i Uppland. Det är en tolkning; studien visar var stenarna står, inte varför.

**Svagheter, i ordning efter vikt.**

1. **Modellen för vattnet är grov.** SGU:s modell är regional, med en höjdmodell på 50 meter, tidsfel på upp till 500 år och ungefärliga sjöar; åar, bäckar och våtmarker saknas. {PO['stones_in_water_1050']} stenar hamnar i modellens vatten år 1050, där ingen sten kan ha rests. Utan dem är sambandet svagare men tydligt (AUC {num(R5['auc'], 2)}), och den oberoende höjdmodellen ger samma resultat.
2. **Riktningen var väntad.** Projektets tidigare mått visade samma sak med grövre data. Studien bekräftar ett känt mönster; den upptäcker inget nytt.
3. **Känslighetsanalyserna valdes efter huvudresultatet.** Stegen och gränserna låstes innan de räknades, men efter att planens resultat var kända.
4. **Stenarnas plats.** Huvudurvalet bygger på regeln för flyttade stenar som den var före rättelsen den 27 oktober 2026, och det tar med {LOST} försvunna stenar, som mäts på den plats där de är kända. Utan dem och de {MOVED_NOW} stenar som den rättade regeln räknar som flyttade blir resultatet detsamma (AUC {num(DR1['auc'], 3)} för vattnet och {num(DR3['auc'], 3)} för gravfälten). En sten kan dessutom ha flyttats en bit utan att det har registrerats; tre källor för flyttade stenar och en ordlista för återresta stenar ger samma resultat men fångar inte allt.
5. **Gravfälten** är olika väl inventerade i olika trakter och oftast odaterade; en del kan vara yngre eller äldre än stenarna.
6. **Öland** har för få stenar för att visa något säkert.

**Vad som skulle fälla fyndet.** Att sambandet med vattnet försvann med en finare höjdmodell, till exempel Lantmäteriets med en meters upplösning, och strandförskjutningskurvor för varje bygd, eller att stenarnas ursprungliga platser på de äldsta kartorna låg systematiskt längre från vattnet.

## 7. Slutsats

Runstenarna restes vid sin tids vatten: nästan två av tre står inom 500 meter från vattnet som det låg år 1050, mot knappt hälften av marken runt dem, och sambandet tål varje känslighetsanalys. Gravfälten drog ännu starkare, och vart och ett av sambanden finns kvar när det andra hålls lika. Nästa steg är en finare höjdmodell och de äldsta kartorna.

## Data och kod

Analysen är gjord i Vitki {APP_VERSION}, ett öppet forskningsverktyg för runstenar ([vitkirunor.se](https://vitkirunor.se)), med de ändringar som gjorts efter den versionen fram till den 1 november 2026. När rapportversion 2 skrevs fanns ingen release av Vitki med DOI, så kodläget anges med en commit: analysen, resultatfilerna och kartorna är de i commit `{CODE_COMMIT}` (2026-11-01). All kod, analysplanerna och resultatfilerna finns öppet på [GitHub](https://github.com/Precatio/runes) under GPL-3.0.

- Analysplanerna: `analysplaner/2026-10-23-strand-och-gravfalt.md`, `analysplaner/2026-10-31-strand-tillagg.md` och `analysplaner/2026-11-01-strand-trappan.md`, med kontrollsummorna i `.sha256`-filerna bredvid.
- Korpusen: fingeravtryck `{KC['locked_fingerprint']}` (låst i planen). Den mappen finns inte längre i cachen, så sökvägen i `utdata/strand/config.R` pekar på en fil som saknas; samma CSV finns kvar som `data/cache/r/corpus/{KC['kept_fingerprint']}/corpus.csv`, med den SHA-256 som planen anger, `{KC['kept_csv_sha256']}`. Den som kör om analysen pekar om sökvägen dit. Den rättade regeln för flyttade och försvunna stenar kommer ur `{KC['now_fingerprint']}`. Korpusfilerna byggs lokalt ur Rundata och ingår inte i repot.
- Kontrollen för rapportversion 2: `utdata/strand/kontroll_v2.py` räknar de försvunna och flyttade stenarna i urvalet och i kartorna och läser provkörningens logg; resultatet står i `utdata/strand/kontroll_v2.json`. Filen och byggskriptet för version 2 finns i commit 6eae0af (2026-11-05).
- Källställena för rapportversion 3: `utdata/strand/kallcitat_v3.json` har de ordagranna citaten ur Stille (2014), Ekholm (1950) och McLeod (2014) som sidorna och talen i inledningen och referenserna stäms av mot.
- Analysen, ett steg per R-process: `utdata/strand/01_avstand.R`, `01b_marginal.R`, `02_r6.R`, `03_statistik.R`, `04_figurer.R` och känslighetsanalyserna `05_trappa.R`. Resultat i `utdata/strand/resultat.json` och `trappan.json`, stenarna i `stenar.csv`, hela redovisningen i `resultat.md`.
- SGU:s modell (`strandforskjutning_1_900.gpkg`, `strandforskjutning_1000_1900.gpkg`) och Copernicus DEM laddas ned till en cache och ingår inte i repot; kontrollsummorna står i planen.
- Kartorna: `utdata/strand/06_illustration.R` (rutan i figur 2 valdes som den 12-kilometersruta i Mälardalen med flest stenar gånger andelen mark som var vatten år 1050 men är land i dag). Kartornas förklaring säger ”står kvar” om alla punkter; kartorna är inte omritade, och bildtexterna säger vad punkterna är.
- Rapporten byggs av `utdata/blogg/build/build_rapport_strand.py`, som läser alla tal ur resultatfilerna och stannar om något inte stämmer.

## Referenser

- Bates, D., Mächler, M., Bolker, B. & Walker, S. 2015. Fitting linear mixed-effects models using lme4. *Journal of Statistical Software* 67 (1), s. 1–48.
- Benjamini, Y. & Hochberg, Y. 1995. Controlling the false discovery rate: a practical and powerful approach to multiple testing. *Journal of the Royal Statistical Society, Series B* 57 (1), s. 289–300.
- Copernicus DEM GLO-30. © DLR e.V. 2010–2014 och © Airbus Defence and Space GmbH 2014–2018, tillhandahållen under COPERNICUS av Europeiska unionen och ESA; alla rättigheter förbehållna. Via AWS Open Data.
- Ekholm, G. 1950. Var restes runstenarna? *Fornvännen* 45, s. 137–147.
- Gräslund, A.-S. 2006. Dating the Swedish Viking-Age rune stones on stylistic grounds. I: M. Stoklund m.fl. (red.), *Runes and their Secrets: Studies in Runology*. Köpenhamn: Museum Tusculanum Press, s. 117–139.
- Klos, L. 2009. *Runensteine in Schweden. Studien zu Aufstellungsort und Funktion*. Ergänzungsbände zum Reallexikon der Germanischen Altertumskunde 64. Berlin: de Gruyter.
- Kvant, V. 2026a. Runstenarna samlas i familjegrupper vid gravfälten. Forskningsrapport. {FAM}
- Kvant, V. 2026b. Runstenarna vände texten mot vägen. Forskningsrapport. {VAG}
- Larsson, M. G. 1990. *Runstenar och utlandsfärder. Aspekter på det senvikingatida samhället med utgångspunkt i de fasta fornlämningarna*. Acta Archaeologica Lundensia, Series in 8°, 18. Stockholm: Almqvist & Wiksell International.
- Larsson, M. G. 2010. Recension av L. Klos, *Runensteine in Schweden. Studien zu Aufstellungsort und Funktion* (2009). *Futhark. International Journal of Runic Studies* 1, s. 249–253.
- Mann, H. B. & Whitney, D. R. 1947. On a test of whether one of two random variables is stochastically larger than the other. *Annals of Mathematical Statistics* 18 (1), s. 50–60.
- McLeod, S. 2014. The rediscovery of U 170: runestones, churchyards, and burial grounds in Sweden. *Journal of the North Atlantic* 25, s. {MCP}. doi:10.3721/037.006.2503
- Påsse, T. & Daniels, J. 2015. *Past shore-level and sea-level displacements*. Sveriges geologiska undersökning, Rapporter och meddelanden 137.
- Riksantikvarieämbetet. Kulturmiljöregistret (fornlämningar), via K-samsök, öppna data (CC0), hämtat oktober 2026; *Runor* (runinskriftsregister), uttag 2020.
- Samnordisk runtextdatabas (Rundata). Institutionen för nordiska språk, Uppsala universitet. Open Database License.
- SGU 2022. *Strandförskjutningsmodell (öppna data)*. Produktbeskrivning, version 1.0. Uppsala: Sveriges geologiska undersökning. CC BY 4.0.
- Stille, P. 2014. Runstenarna i landskapet. En undersökning om placeringen av runstenarna i Tiohärad. *Futhark. International Journal of Runic Studies* 5 (2014, utg. 2015), s. 137–149.
- Wilcoxon, F. 1945. Individual comparisons by ranking methods. *Biometrics Bulletin* 1 (6), s. 80–83.
- Zachrisson, T. 1998. *Gård, gräns, gravfält. Sammanhang kring ädelmetalldepåer och runstenar från vikingatid och tidig medeltid i Uppland och Gästrikland*. Stockholm Studies in Archaeology 15. Stockholm: Stockholms universitet.

:::box Det viktigaste i korthet
- De som reste runstenarna valde platser nära sin tids vatten, inte bara för att bygden låg vid vattnet utan också inom bygden.
- Gravfälten drog ännu starkare, och vart och ett av sambanden finns kvar när det andra hålls lika: de mest sannolika platserna för en runsten låg nära både vattnet och gravfälten.
- Tillsammans med att texten vändes mot vägen pekar det mot stenar som restes för att ses av dem som färdades.
- Svagheten är modellen för vattnet år 1050, som är grov nära stränderna; nästa prov är en finare höjdmodell.
:::

{LOG_SV}
"""

body_en = f"""*Viktor Kvant, independent researcher. Fully tested finding. Report version {REPORT_VERSION}, {TODAY} (first version published {V1_PUBLISHED}). Timeline: {TL_EN}. The analysis was made in Vitki {APP_VERSION}. Licence CC BY 4.0. This English version is the canonical one for citation: {CITE_EN}. Keywords: runestones, Viking Age, placement, shore displacement, land uplift, grave fields, spatial statistics, pre-registration. Competing interests: none. Funding: none.*

## Abstract

**Background and aim.** Where the runestones were raised has long been debated: by grave fields, by roads and bridges, by farms and boundaries. Water is harder to measure, because the land has risen since the Viking Age and today's shore is not the stones' shore. The question here is whether the stones were raised closer to the water of their own time than the land around them, and whether that association remains when nearness to the grave fields is held equal.
**Material.** {m(PO['n'], True)} Viking-Age runestones not counted as moved in the locked corpus ({LOST} of them lost and measured at their recorded place), in Uppland, Södermanland, Östergötland, Småland, Västergötland and on Öland, and {m(PO['n_random'], True)} random points on land within five kilometres of the stones. The water of AD 1050 from the shore displacement model of the Geological Survey of Sweden (SGU), the grave fields from the Swedish National Heritage Board's register of ancient monuments.
**Method.** Pre-registered study. The distance to the nearest water is compared between stones and points with Wilcoxon's rank-sum test and the AUC, the probability that a stone stands closer than a point. Internal replication in two halves, seven sensitivity tests in the plan and nine sensitivity analyses under a locked addendum plan.
**Results.** {pc(H1['within_500_stones'])} per cent of the stones stand within 500 metres of the water of AD 1050, against {pc(H1['within_500_random'])} per cent of the points; the median distance is {H1['median_stones_m']} against {H1['median_random_m']} metres, AUC {num(H1['auc'], 2, True)}, {pfmt(H1['p'], True)}. It holds in both halves, in five of six provinces, for other years between 550 and 1550, with an independent elevation model and in every sensitivity analysis, including against the land in the same parish. The grave fields draw more strongly: {pc(H3['within_500_stones'])} against {pc(H3['within_500_random'])} per cent within 500 metres, AUC {num(H3['auc'], 2, True)}. Both associations remain when the other is held equal. Of the {T1['n']} stones that stand in place according to three sources, {pc(T1['water']['within_500_stones'])} per cent stand within 500 metres of the water (AUC {num(T1['water']['auc'], 3, True)}), and without the {LOST} lost stones and the {MOVED_NOW} that the corrected rule for moved stones removes, the AUC is {num(DR1['auc'], 3, True)} for the water and {num(DR3['auc'], 3, True)} for the grave fields. The water of the time fits the stones slightly better than today's, but the difference is small.
**Conclusion.** Those who raised the runestones chose places near the water, and even more often near the grave fields, within districts that already lay by water. The main weakness is that the model of the water of AD 1050 is coarse: {PO['stones_in_water_1050']} of the stones fall in the model's water.

## 1. Introduction

Where the runestones were raised has long been debated. Gunnar Ekholm (1950, pp. {EKO}) objected to the view of the stones as monuments of the grave fields: in Uppland, he argued, they largely followed the old routes by land and water, and a stone on Ängby land near Knivsta was raised to be seen from the river, "the route of travel in ancient times" (*forntidens samfärdsled*). Mats G. Larsson (1990) found in a survey of the stones' placement that graves, roads with bridges and fords, and probable property boundaries were about equally common settings (Larsson 2010, p. 249). Torun Zachrisson (1998) has linked the stones to farm, boundary and grave field, and Lydia Klos (2009) has argued that most were raised at grave fields. Mats G. Larsson (2010, p. 252) has objected that Klos thereby overstates the grave fields at the expense of other settings, above all the property boundaries (see also McLeod 2014). Per Stille (2014, p. {ST14['citat'][0]['sida']}) found in Tiohärad in Småland that {ST14['vid_vatten']} of the {ST14['med_bestämbar_plats']} stones whose place can be determined with more or less certainty stood by water, at watercourses or bridge sites, where a road presumably also ran. The bridge stones, which tell of bridges and causeways over water and wet ground, show that water belonged to the stones' setting.

Measuring the nearness to water is hard. The land has risen since the Viking Age, in the Mälaren valley by about five metres, so a stone that stood by a bay may now stand on dry land, and a stone by today's shore may have stood far from the water. Klos (2009) also measured the distance to water, but as a rule without the sea level of the Viking Age, which Larsson (2010, p. 251) saw as the basic flaw of that part of her study: Lake Mälaren became an inland lake instead of the inlet of the sea that it was. SGU's shore displacement model (SGU 2022, after Påsse & Daniels 2015) gives an open model for the whole country of where the water lay at different times.

We know of no study that has measured the distance to the water of the stones' own time for the whole Swedish material, with a model of shore displacement, without the stones counted as moved, and with a comparison with the land in the same district. The aim is to do so and test whether the association remains when nearness to the grave fields is held equal.

## 2. Pre-registration: hypothesis and plan

The hypotheses, measures and rules of interpretation were written down in an analysis plan on 23 October 2026, before any distance had been computed. The plan has the SHA-256 checksum `{SHA['2026-10-23-strand-och-gravfalt']}…` and was committed to version control the same evening. Before the lock, only the data sources had been fetched, the layers listed, the number of stones per province counted and the mid-years of the style groups compiled to choose the year (median 1035). A test run the same evening, after the plan had its checksum but before the commit, ran through the tests but printed only its progress and the numbers of stones, random points and grave fields, no test results; no results from it survive, and the statistics were first read on 31 October.

The direction was expected. The project's earlier measure, with a coarse land uplift and with moved stones, had already shown that the stones stand closer to water and grave fields than the land around them. The study therefore tests whether a known pattern holds with better data, not a new one.

The plan's hypotheses, verbatim (translated): **H1 (primary): the stones stand closer to the water of AD 1050 than the random points.** **H2: the nearness is clearer relative to the water of the time than to today's.** **H3: the grave fields, on the same selection** (the stones stand closer to registered grave fields than the random points). H1 *holds* if five conditions are met: p below 0.05 and AUC above 0.5 overall, the same in both halves, the same when stones within 200 metres of each other are merged into one place, the same for four other years within 200 years (750, 950, 1150 and 1250), and the same with only the sea, without the model's lakes. H3 holds if it holds overall, in both halves and for the places. H2 is called clearer only if the whole 95 % interval for the difference lies above zero.

Two addenda were locked later, both before they were computed. On 31 October (SHA-256 `{SHA['2026-10-31-strand-tillagg']}…`), before the statistics were run: H1 and H3 are also tested on the stones that stand in place according to three sources, because the rule for moved stones had been corrected on 27 October, after the plan was locked. On 1 November (SHA-256 `{SHA['2026-11-01-strand-trappan']}…`), when the plan's results were known: nine fixed sensitivity analyses for distances, corresponding to those the project makes for other findings. They are confirmatory in the sense that the steps and limits were locked before they were computed, but they were chosen after the main result was known.

## 3. Material

- **The stones.** Swedish Viking-Age runestones in the Scandinavian Runic-text Database (Rundata), in the version locked in the plan. Of them we took those that have coordinates and are not counted as moved under the rule as it stood when the plan was locked: Rundata's placement does not mention a church, church porch, wall, museum, collection, park or similar place to which stones have been taken, and the site is not a church, churchyard, church ruin, vicarage, monastery, castle, school or museum. The rule was corrected on 27 October 2026, after the plan was locked, so that it also counts stones whose placement says that they have been moved or names another place than the find-spot; under the corrected rule {MOVED_NOW} of the stones here are moved. Lost stones are not removed by the rule: {LOST} of the stones are lost and measured at their recorded place. So not all stones in the selection still stand in place; the sensitivity analyses in 5.3 test the result without them. Only provinces with at least 20 stones in the selection are tested: Uppland ({P1['U']['n_stones']}), Södermanland ({P1['Sö']['n_stones']}), Östergötland ({P1['Ög']['n_stones']}), Småland ({P1['Sm']['n_stones']}), Västergötland ({P1['Vg']['n_stones']}) and Öland ({P1['Öl']['n_stones']}), {m(PO['n'], True)} in all. The {sum(PO['other_provinces_not_tested'].values())} stones in the other provinces are not tested. Runestones only.
- **The water.** SGU's shore displacement model, open data version 1.0 (2022, CC BY 4.0). It is built on shore displacement curves across the country, a model of land uplift and an elevation model with a resolution of 50 metres. The water of AD 1050 is the model's sea and lakes in the slice 900 years before 1950; today's water is the slice for 1949. The distances are computed on a grid of 25-metre cells.
- **The grave fields.** The Swedish National Heritage Board's register of ancient monuments via K-samsök (open data, CC0), retrieved on 12 October 2026: {m(PO['n_gravfalt'], True)} registered grave fields with coordinates.
- **The independent elevation model.** Copernicus DEM GLO-30 (about 30 metres), with the province's land uplift since the Viking Age as the height limit.
- **The dating** by the stone's ornamental style (Gräslund 2006): {PO['n_dated']} of the stones.
- **The halves** are the project's fixed division parish by parish: {PO['halves']['A']} and {PO['halves']['B']} stones.

{FIG1_EN}

## 4. Method

**4.1 The measure and the comparison.** For every stone and every point the distance is computed to the nearest water of AD 1050, to today's water and to the nearest grave field; a point in the water gets the distance zero. The comparison is a null model: for each province ten random points per stone are drawn, uniformly within five kilometres of the province's stones, and only points that are land both in AD 1050 and in 1949 are kept. The points thus lie in the districts where stones were raised, so the test concerns where in the district the stone stands, not where the districts lie. Stones and points are compared with Wilcoxon's rank-sum test (Wilcoxon 1945; Mann & Whitney 1947), one-sided. The effect is given as the medians, the share within 500 metres and the AUC, the probability that a randomly chosen stone stands closer than a randomly chosen point (0.5 means no difference). Figure 2 shows the measurement in one district.

{FIG2_EN}

**4.2 Correction and replication.** Each hypothesis is tested in each half on its own. The provinces are tested separately with Benjamini–Hochberg correction (Benjamini & Hochberg 1995) over the six, and the secondary tests likewise over the five. The difference between the water of the time and today's (H2) gets a 95 % interval from 2,000 bootstrap samples in which the stones are drawn place by place.

**4.3 The sensitivity analyses.** The plan's seven tests and its descriptive comparison with moved stones, the addendum's test and the nine steps of the addendum plan are given with their results in 5.2 and 5.3. The parish as a random effect is a logistic regression (Bates et al. 2015) in which the points get the parish of the nearest stone. When stones are removed, the points that belong to them are removed too. A step holds when the AUC is above 0.5 and p below 0.05; without one province at a time, significance is required only where at least two thirds of the stones remain.

**4.4 Deviations from the plan.** The statistics were run eight days after the distances were computed, after the addendum for moved stones; the plan's tests are unchanged. The {m(PO['distances_at_tile_margin'], True)} distances that reached the edge of the computation tiles, nearly all for the sea alone far inland, were recomputed on a grid of 100-metre cells over the whole province; the plan gives no cell size. The sensitivity analyses of the addendum plan were added after the plan's results were known (see 2). Otherwise none.

## 5. Results

**5.1 The water of AD 1050 (H1), the grave fields (H3) and today's water (H2).** Of the {m(PO['n'], True)} stones, {pc(H1['within_500_stones'])} per cent stand within 500 metres of the water of AD 1050, against {pc(H1['within_500_random'])} per cent of the {m(PO['n_random'], True)} points; within one kilometre {pc(H1['within_1000_stones'])} against {pc(H1['within_1000_random'])} per cent. The median distance is {H1['median_stones_m']} against {H1['median_random_m']} metres, AUC {num(H1['auc'], 3, True)}, {pfmt(H1['p'], True)}. Half A ({HA['n_stones']} stones in {HA['n_parishes']} parishes): AUC {num(HA['auc'], 3, True)}, {pfmt(HA['p'], True)}. Half B ({HB['n_stones']} stones in {HB['n_parishes']} parishes): AUC {num(HB['auc'], 3, True)}, {pfmt(HB['p'], True)}. With {HS['n_sites']} places instead of stones: AUC {num(HS['auc'], 3, True)}, {pfmt(HS['p'], True)}. H1 *holds* on all five conditions. In plain words: compare a runestone with a randomly chosen place in the same district, and the runestone stands closer to the water of its time in {pc(H1['auc'])} cases out of 100; almost two in three stones stand within 500 metres of the water, against fewer than half of the land.

By province, with q corrected over the six: AUC {num(P1['U']['auc'], 2, True)} in Uppland, {num(P1['Sö']['auc'], 2, True)} in Södermanland, {num(P1['Ög']['auc'], 2, True)} in Östergötland, {num(P1['Sm']['auc'], 2, True)} in Småland and {num(P1['Vg']['auc'], 2, True)} in Västergötland, all q < 0.01, and {num(P1['Öl']['auc'], 2, True)} on Öland, q = {num(P1['Öl']['q_bh'], 3, True)}, where the {P1['Öl']['n_stones']} stones go the same way but are not enough.

The grave fields (H3): {pc(H3['within_500_stones'])} per cent of the stones stand within 500 metres of a registered grave field, against {pc(H3['within_500_random'])} per cent of the points; the median is {H3['median_stones_m']} against {m(H3['median_random_m'], True)} metres, AUC {num(H3['auc'], 3, True)}, {pfmt(H3['p'], True)}. Half A: AUC {num(H3A['auc'], 3, True)}, half B: AUC {num(H3B['auc'], 3, True)}, the places: AUC {num(H3S['auc'], 3, True)}, all {pfmt(max(H3A['p'], H3B['p'], H3S['p']), True)}. H3 *holds*, in the same five provinces as H1. In plain words: two in three stones stand within 500 metres of a grave field, against one in four places in the district.

Today's water (H2): relative to the water of 1949, {pc(NOW['within_500_stones'])} per cent of the stones stand within 500 metres, against {pc(NOW['within_500_random'])} per cent of the points, AUC {num(NOW['auc'], 3, True)}. The difference in AUC from the water of the time is {num(H2['delta_auc'], 3, True)}, 95 % interval {num(H2['ci95'][0], 3, True)} to {num(H2['ci95'][1], 3, True)}. The whole interval lies above zero, so by the plan the nearness is *clearer* relative to the water of the time, but the difference is small. It shows in Uppland, Södermanland, Östergötland and on Öland; in Småland and Västergötland today's water fits as well or slightly better.

{chart(False)}

**5.2 The plan's sensitivity tests.** All hold for H1:

- Other years: AUC between {num(R1A[0], 2, True)} and {num(R1A[1], 2, True)} for all six, from AD 550 to AD 1550, all {pfmt(max(v['p'] for v in R1.values()), True)}.
- Only the sea, without the model's lakes: {rung(R2, True)}. In Östergötland, Småland and Västergötland the test says nothing, since most stones and points there lie tens of kilometres from the sea.
- Without the {R5['n_excluded']} stones that stand in the model's water of AD 1050: {rung(R5, True)}.
- The independent elevation model: land uplift one metre lower: {rung(R6['minus1'], True, False)}; equal: {rung(R6['zero'], True, False)}; one metre higher: {rung(R6['plus1'], True, False)}. The pattern thus does not depend on SGU's elevation model.
- Points within two kilometres: AUC {num(R7['r2km']['water']['auc'], 3, True)}; within ten kilometres: AUC {num(R7['r10km']['water']['auc'], 3, True)}. For the grave fields the difference grows with the radius (AUC {num(R7['r2km']['grave']['auc'], 3, True)} and {num(R7['r10km']['grave']['auc'], 3, True)}), while the radius changes almost nothing for the water.

The plan's descriptive comparison with the moved stones included ({m(D1['n_all'], True)} stones, {m(D1['n_moved'], True)} of them moved, and new random points around them): AUC {num(D1['then']['auc'], 3, True)} against the water of AD 1050. The moved stones on their own, measured where they stand today, mostly at churches: median {D1['moved_only_then']['median_stones_m']} metres, AUC {num(D1['moved_only_then']['auc'], 3, True)}. They thus stand even closer to the water of the time than the stones in the selection, so counting them would have made the association somewhat stronger, not weaker.

Water and grave fields together, in a logistic regression with the province held constant and the distances on a logarithmic scale, taken as the distance plus 250 metres so that a distance of zero can also be used: when the distance to the water plus 250 metres halves, the odds that the place has a runestone become {num(S['S1a']['or'], 2, True)} times as large (95 % interval {num(S['S1a']['lo'], 2, True)}–{num(S['S1a']['hi'], 2, True)}), with the distance to the grave fields equal; for the grave fields the odds ratio is {num(S['S1b']['or'], 2, True)} ({num(S['S1b']['lo'], 2, True)}–{num(S['S1b']['hi'], 2, True)}). Both hold in both halves and after correction. In plain words: the water is not merely a sign that the grave fields lie there, nor the other way round; the grave fields weigh about twice as much.

The other secondary tests do not hold: the share within one kilometre of the water is the same for early and late stones ({pc(S['S2']['early'])} per cent), Christian markers make no difference ({pfmt(S['S3']['p'], True)}), and the bridge and road stones stand somewhat closer ({S['S4']['median_bridge_m']} against {S['S4']['median_other_m']} metres in median) but not reliably ({pfmt(S['S4']['p'], True)}, q = {num(S['S4']['q_bh'], 2, True)}).

**5.3 The sensitivity analyses.** Only stones that stand in place according to three sources (the locked corpus, the corrected rule for moved and lost stones and Runor 2020; {T1['n']} stones): {pc(T1['water']['within_500_stones'])} per cent within 500 metres of the water of AD 1050, against {pc(T1['water']['within_500_random'])} per cent of the points, AUC {num(T1['water']['auc'], 3, True)}; grave fields AUC {num(T1['grave']['auc'], 3, True)}, both {pfmt(max(T1['water']['p'], T1['grave']['p']), True)}. In the nine analyses of the addendum plan every step holds for both the water and the grave fields. For the water:

- The halves: see 5.1.
- Without one province at a time: AUC between {num(LA1[0], 2, True)} and {num(LA1[1], 2, True)}, also without Uppland, when only {pc(L1['U']['share_kept'])} per cent of the stones remain ({pfmt(L1['U']['p'], True)}).
- The parish as the unit ({G1['socken']['n_parishes']} parishes): {rung(G1['socken'], True)}.
- The parish as a random effect: odds ratio {num(MM1['or'], 2, True)} when the distance plus 250 metres halves (95 % interval {num(MM1['lo'], 2, True)}–{num(MM1['hi'], 2, True)}), {pfmt(MM1['p'], True)}; the model converged without warnings. In plain words: also compared with the land in the same parish, the stones stand closer to the water.
- One stone per certain carver ({C['carvers']} carvers): {rung(G1['en_per_ristare'], True)}.
- Without re-erected stones ({C['reerected']} removed): {rung(G1['utan_aterresta'], True)}.
- Without stones that Runor gives as moved ({C['moved_runor']} removed): {rung(G1['utan_flyttade_runor'], True)}.
- Only stones still standing under the corrected rule of 27 October 2026 ({NOT_NOW} removed: {LOST} lost and {MOVED_NOW} moved, one of them both): {rung(DR1, True)}; grave fields AUC {num(DR3['auc'], 3, True)}.
- The early stones, before AD 1050: {rung(G1['tidiga'], True)}. The late: {rung(G1['sena'], True)}.

For the grave fields the AUC lies between {num(GA3[0], 2, True)} and {num(GA3[1], 2, True)} in every step, without one province at a time between {num(LA3[0], 2, True)} and {num(LA3[1], 2, True)}, and the parish as a random effect gives the odds ratio {num(MM3['or'], 2, True)} ({num(MM3['lo'], 2, True)}–{num(MM3['hi'], 2, True)}), {pfmt(MM3['p'], True)}.

The study stands alone, so the correction applies within the plan and not among the associations the project adjusts jointly. No hand-coded traits are involved; the source of error is the model of the water (see 6).

## 6. Discussion

**What the finding says.** Those who raised the runestones chose places near the water. The comparison concerns the land in the same district, and the association remains parish by parish, so it is not only because the districts lay by water. Nor does it depend on a few provinces, places or carvers, on stones that have been moved, lost or re-erected, or on SGU's elevation model. It held both before and after AD 1050. The grave fields draw more strongly, and each association remains when the other is held equal: the most likely places for a runestone lay near both water and grave fields.

**The water of the time and today's.** That the water of the time fits only slightly better than today's does not mean that the land uplift is unimportant. In most districts the shore has moved less than the hundreds of metres that separate the stones from the points (figure 2), and the lakes remain. The model for AD 1050 is needed above all so that the finding is not an artefact of today's coast.

**Against earlier research.** That two in three stones stand within 500 metres of a grave field supports Klos (2009) and agrees with stones in family groups standing at grave fields more often than single stones ([Kvant 2026a]({FAM_EN})). That the water remains when the grave fields are held equal at the same time bears out Larsson's (2010) and McLeod's (2014) point that the grave fields are not the whole answer. The finding fits with the stones' text being turned mostly towards the road ([Kvant 2026b]({VAG_EN})): the stones were raised where people travelled, by land and by water, as Ekholm (1950) argued from single stones in Uppland. That is an interpretation; the study shows where the stones stand, not why.

**Weaknesses, in order of importance.**

1. **The model of the water is coarse.** SGU's model is regional, with an elevation model of 50 metres, time errors of up to 500 years and approximate lakes; rivers, streams and wetlands are missing. {PO['stones_in_water_1050']} stones fall in the model's water of AD 1050, where no stone can have been raised. Without them the association is weaker but clear (AUC {num(R5['auc'], 2, True)}), and the independent elevation model gives the same result.
2. **The direction was expected.** The project's earlier measure showed the same with coarser data. The study confirms a known pattern; it discovers nothing new.
3. **The sensitivity analyses were chosen after the main result.** The steps and limits were locked before they were computed, but after the plan's results were known.
4. **The stones' places.** The main selection rests on the rule for moved stones as it stood before the correction of 27 October 2026, and it includes {LOST} lost stones, which are measured at their recorded place. Without them and the {MOVED_NOW} stones that the corrected rule counts as moved, the result is the same (AUC {num(DR1['auc'], 3, True)} for the water and {num(DR3['auc'], 3, True)} for the grave fields). A stone may also have been moved a little without it being recorded. Three sources for moved stones and a word list for re-erected stones give the same result, but do not catch everything.
5. **The grave fields** are unevenly surveyed in different districts and mostly undated; some may be younger or older than the stones.
6. **Öland** has too few stones to show anything for certain.

**What would overturn the finding.** If the association with water disappeared with a finer elevation model, for example Lantmäteriet's at one metre's resolution, and shore displacement curves for each district, or if the stones' original places on the oldest maps lay systematically farther from the water.

## 7. Conclusion

The runestones were raised by the water of their time: almost two in three stand within 500 metres of the water as it lay in AD 1050, against fewer than half of the land around them, and the association withstands every sensitivity analysis. The grave fields drew even more strongly, and each association remains when the other is held equal. The next step is a finer elevation model and the oldest maps.

## Data and code

The analysis was made in Vitki {APP_VERSION}, an open research tool for runestones ([vitkirunor.se](https://vitkirunor.se/en)), with the changes made after that version up to 1 November 2026. When report version 2 was written there was no release of Vitki with a DOI, so the code state is given as a commit: the analysis, the result files and the maps are those of commit `{CODE_COMMIT}` (2026-11-01). All code, the analysis plans and the result files are openly available on [GitHub](https://github.com/Precatio/runes) under GPL-3.0.

- The analysis plans: `analysplaner/2026-10-23-strand-och-gravfalt.md`, `analysplaner/2026-10-31-strand-tillagg.md` and `analysplaner/2026-11-01-strand-trappan.md`, with their checksums in the `.sha256` files beside them.
- The corpus: fingerprint `{KC['locked_fingerprint']}` (locked in the plan). That folder is no longer in the cache, so the path in `utdata/strand/config.R` points to a missing file; the same CSV survives as `data/cache/r/corpus/{KC['kept_fingerprint']}/corpus.csv`, with the SHA-256 that the plan gives, `{KC['kept_csv_sha256']}`. Anyone rerunning the analysis points the path there. The corrected rule for moved and lost stones comes from `{KC['now_fingerprint']}`. The corpus files are built locally from Rundata and are not in the repository.
- The check for report version 2: `utdata/strand/kontroll_v2.py` counts the lost and moved stones in the selection and in the maps and reads the log of the test run; the result is in `utdata/strand/kontroll_v2.json`. The file and the builder of version 2 are in commit 6eae0af (2026-11-05).
- The source passages for report version 3: `utdata/strand/kallcitat_v3.json` holds the verbatim quotations from Stille (2014), Ekholm (1950) and McLeod (2014) that the pages and numbers in the introduction and the references are checked against.
- The analysis, one step per R process: `utdata/strand/01_avstand.R`, `01b_marginal.R`, `02_r6.R`, `03_statistik.R`, `04_figurer.R` and the sensitivity analyses `05_trappa.R`. Results in `utdata/strand/resultat.json` and `trappan.json`, the stones in `stenar.csv`, the full account in `resultat.md` (Swedish).
- SGU's model (`strandforskjutning_1_900.gpkg`, `strandforskjutning_1000_1900.gpkg`) and Copernicus DEM are downloaded to a cache and are not in the repository; their checksums are in the plan.
- The maps: `utdata/strand/06_illustration.R` (the window in figure 2 was chosen as the 12-kilometre window in the Mälaren region with the most stones times the share of land that was water in AD 1050 but is land today). The maps' legends say "still in place" of all points; the maps have not been redrawn, and the captions say what the points are.
- The report is built by `utdata/blogg/build/build_rapport_strand.py`, which reads every number from the result files and stops if anything disagrees.

## References

- Bates, D., Mächler, M., Bolker, B. & Walker, S. 2015. Fitting linear mixed-effects models using lme4. *Journal of Statistical Software* 67 (1), pp. 1–48.
- Benjamini, Y. & Hochberg, Y. 1995. Controlling the false discovery rate: a practical and powerful approach to multiple testing. *Journal of the Royal Statistical Society, Series B* 57 (1), pp. 289–300.
- Copernicus DEM GLO-30. © DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH 2014–2018 provided under COPERNICUS by the European Union and ESA; all rights reserved. Via AWS Open Data.
- Ekholm, G. 1950. Var restes runstenarna? *Fornvännen* 45, pp. 137–147.
- Gräslund, A.-S. 2006. Dating the Swedish Viking-Age rune stones on stylistic grounds. In: M. Stoklund et al. (eds), *Runes and their Secrets: Studies in Runology*. Copenhagen: Museum Tusculanum Press, pp. 117–139.
- Klos, L. 2009. *Runensteine in Schweden. Studien zu Aufstellungsort und Funktion*. Ergänzungsbände zum Reallexikon der Germanischen Altertumskunde 64. Berlin: de Gruyter.
- Kvant, V. 2026a. Runestones gather in family groups by the grave fields. Research report. {FAM_EN}
- Kvant, V. 2026b. The runestones turned their text towards the road. Research report. {VAG_EN}
- Larsson, M. G. 1990. *Runstenar och utlandsfärder. Aspekter på det senvikingatida samhället med utgångspunkt i de fasta fornlämningarna*. Acta Archaeologica Lundensia, Series in 8°, 18. Stockholm: Almqvist & Wiksell International.
- Larsson, M. G. 2010. Review of L. Klos, *Runensteine in Schweden. Studien zu Aufstellungsort und Funktion* (2009). *Futhark: International Journal of Runic Studies* 1, pp. 249–253.
- Mann, H. B. & Whitney, D. R. 1947. On a test of whether one of two random variables is stochastically larger than the other. *Annals of Mathematical Statistics* 18 (1), pp. 50–60.
- McLeod, S. 2014. The rediscovery of U 170: runestones, churchyards, and burial grounds in Sweden. *Journal of the North Atlantic* 25, pp. {MCP}. doi:10.3721/037.006.2503
- Påsse, T. & Daniels, J. 2015. *Past shore-level and sea-level displacements*. Geological Survey of Sweden, Rapporter och meddelanden 137.
- Scandinavian Runic-text Database (Rundata). Department of Scandinavian Languages, Uppsala University. Open Database License.
- SGU 2022. *Strandförskjutningsmodell (öppna data)* [Shore displacement model, open data]. Product description, version 1.0. Uppsala: Geological Survey of Sweden. CC BY 4.0.
- Stille, P. 2014. Runstenarna i landskapet. En undersökning om placeringen av runstenarna i Tiohärad [Runestones in the landscape: a study of the placement of the runestones in Tiohärad]. *Futhark: International Journal of Runic Studies* 5 (2014, publ. 2015), pp. 137–149.
- Swedish National Heritage Board (Riksantikvarieämbetet). The register of ancient monuments (Kulturmiljöregistret), via K-samsök, open data (CC0), retrieved October 2026; *Runor* (register of runic inscriptions), 2020 extract.
- Wilcoxon, F. 1945. Individual comparisons by ranking methods. *Biometrics Bulletin* 1 (6), pp. 80–83.
- Zachrisson, T. 1998. *Gård, gräns, gravfält. Sammanhang kring ädelmetalldepåer och runstenar från vikingatid och tidig medeltid i Uppland och Gästrikland*. Stockholm Studies in Archaeology 15. Stockholm: Stockholm University.

:::box The essentials
- Those who raised the runestones chose places near the water of their time, not only because the district lay by the water but also within the district.
- The grave fields drew even more strongly, and each association remains when the other is held equal: the places most likely to have a runestone lay near both the water and the grave fields.
- Together with the text being turned towards the road, it points to stones raised to be seen by those who travelled.
- The weakness is the model of the water of AD 1050, which is coarse near the shores; the next test is a finer elevation model.
:::

{LOG_EN}
"""

JARGON = r"modul\w*|trapp\w*|q_global|korpusjobb|fingeravtryck|fingerprint|facit|Vitkis|Vitki's|\bthe app\b|\bappen\b|`[^`]*/[^`]*`|METHODS"
for b in (body, body_en):
    assert not re.search(r"^\|", b, re.M), "BlogBody har inga tabeller"
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M)), "varje ruta ska stängas"
    assert "{" not in b and "}" not in b
    head = b.split("## Data")[0]
    assert not re.findall(JARGON, head), re.findall(JARGON, head)
assert "Det viktigaste i korthet" in body and "## 2. Förregistrering" in body and "## 6. Diskussion" in body
assert "I klartext" in body and "In plain words" in body_en  # mallen version 4
assert body.split("\n", 1)[0].startswith("*Viktor Kvant, oberoende forskare. Fullt prövat fynd. Rapportversion 3, 2026-11-05 (första versionen publicerad 2026-11-01). Tidslinje: ")
assert body_en.split("\n", 1)[0].startswith("*Viktor Kvant, independent researcher. Fully tested finding. Report version 3, 2026-11-05 (first version published 2026-11-01). Timeline: ")
# Rapportversion 2: header phrases the site parses (web/src/lib/report.ts) and the corrections of the review
assert "Den engelska versionen är den kanoniska för citering: " in body and "This English version is the canonical one for citation: " in body_en
assert re.search(r"(?:Tidslinje|Timeline):\s*(.+?)\.\s+(?:Analysen är gjord|The analysis was made)", body) and "avstånden räknades 2026-10-23" in body
assert "en provkörning av skriptet utan sparade resultat 2026-10-23" in body and "a test run of the script with no results kept 2026-10-23" in body_en
for b_, old in ((body, "restes oftast där både"), (body_en, "most often raised where both"), (body, "en stor del av stenarna med känd plats"),
               (body_en, "a large share of the stones with a known place"), (body, "inga siffror,"), (body_en, "no figures,")):
    assert old not in b_.split("## Data")[0], old
assert "*Journal of the North Atlantic* 25, s. 1–8. doi:" in body and "*Journal of the North Atlantic* 25, pp. 1–8. doi:" in body_en
assert "Ekholm (1950, s. 138–143)" in body and "Ekholm (1950, pp. 138–143)" in body_en
for old in ("Av de runstenar som står kvar på sin plats", "runstenar som står kvar på sin plats, i", "bara stenar som står kvar och",
            "sambanden är oberoende", "Med dagens regel för flyttade stenar", "när den görs", "Kvant 2026c", "METHODS.md)",
            "skrev bara ut förloppet och inga siffror", "s. 137 ff", "Copernicusprogrammet", "\nDiagram:"):
    assert old not in body and old not in summary, old
for old in ("Of the runestones that still stand in place", "runestones that still stand in place, in", "only stones that still stand in place",
            "associations are independent", "With today's rule for moved stones", "when one is made", "Kvant 2026c", "METHODS.md)",
            "Cite as:", "bears out McLeod (2014) that", "the stone stood best", "pp. 137 ff", "Copernicus programme", "\nChart:"):
    assert old not in body_en and old not in summary_en, old
assert "](https://vitkirunor.se/forskningsrapporter/" not in body_en and not re.search(r"\]\((?!https://|/api/blog/figures/)", body + body_en)
assert body.rstrip().endswith(LOG_SV) and body_en.rstrip().endswith(LOG_EN)

out = {"slug": SLUG, "title": title, "summary": summary, "body": body, "title_en": title_en, "summary_en": summary_en,
       "body_en": body_en, "labels": ["Rapport", "Geografi"]}
assert blog_labels.check(out["labels"]) is None
path = os.path.join(ROOT, "utdata", "rapporter", "rapport_strand.json")
json.dump(out, open(path, "w"), ensure_ascii=False, indent=1)
print(path, len(body.split()), "ord,", len(body.split("## Data")[0].split()), "före Data och kod;", len(body_en.split()), "words")

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
                 "topic": "Rapport|strand", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
