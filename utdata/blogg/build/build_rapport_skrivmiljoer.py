"""Forskningsrapport, metodrapport (låst mall utdata/rapporter/MALL.md, version 4; Metodrapport, delvis prövad):
"Skrivmiljöer utan namn" (sv + en).

Rapportversion 1 (2026-10-31, commit 863e63d, aldrig publicerad) hade titeln "grupper av runstenar utan ristare blir till
85 procent en och samma hand när metoden prövas på ristare den inte sett". De 85 procenten mätte något annat: hur stor
del av en grupp som är samma ristare när metoden körs på stenar av KÄNDA ristare (hållet-utanför-provet, inte låst).
Rapportversion 2 (2026-11-19) säger vad som håller och vad som inte gör det: siffrorna omräknade på korpusen
510ebfb3acc9a229 (7 november 2026), litteraturens par (utdata/okanda_ristare/sri_par.json, 2026-10-29), mästarmodellen
(del 3 av den låsta planen 2026-10-29-en-och-samma-mastare) och de fyra låsta proven mot Runor 2020 den 8 november
(planerna 32257107, add8ff31, 9e0037d5, 15c2f757; utdata/samma_hand, textdrag_hand, nya_hander, tata_karnor). Planen
för en öppen ristarmodell (2026-11-19) är låst men inte körd; rapporten säger inget om dess utfall.
Alla siffror asserteras mot resultatfilerna.
    ../../../.venv/bin/python build_rapport_skrivmiljoer.py [--write | --update DOC]"""
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

FP = "510ebfb3acc9a229"  # materialets version för grupperingen och prövningen på kända ristare (räknad 2026-11-07)
CDIR = os.path.join(ROOT, "data", "cache", "r", "corpus", FP)
DONE = json.load(open(os.path.join(CDIR, "done.json"), encoding="utf-8"))
assert DONE["fingerprint"] == FP and DONE["computed_at"].startswith("2026-11-07") and not DONE["errors"]
APP_VERSION = "3.1.0"  # Vitki-versionen då materialet räknades om (tag v3.1.0, 2026-11-06), inte den nuvarande
assert open(os.path.join(ROOT, "utdata", "rapporter", "MALL.md.sha256")).read().startswith("611a4d5f")  # mallens version 4
REPORT_VERSION = 2
V1_DATE = "2026-10-31"  # rapportversion 1 skrevs (opublicerad)
TODAY = "2026-11-19"  # rapportversionens datum, fast i byggaren (mallen version 3)
TL_SV = ("metoden byggdes 2026-10-11; prövningen på kända ristare som hölls utanför gjordes 2026-10-20; två planer för "
         "oberoende prov låstes och kördes 2026-10-29; grupperna jämfördes med litteraturens par 2026-10-29; grupperingen "
         "och prövningen räknades om på en senare version av materialet 2026-11-07; fyra låsta prov mot runologernas "
         "grupper i Runor 2020 kördes 2026-11-08")
TL_EN = ("the method was built 2026-10-11; the test on known carvers held out was made 2026-10-20; two plans for "
         "independent tests were locked and run 2026-10-29; the groups were compared with the literature's pairs "
         "2026-10-29; the grouping and the test were recomputed on a later version of the material 2026-11-07; four "
         "locked tests against the runologists' groups in Runor 2020 were run 2026-11-08")
NB = " "
pc = lambda x: int(100 * x + 0.5 + 1e-9)  # noqa: E731
J = lambda *p: json.load(open(os.path.join(ROOT, *p), encoding="utf-8"))  # noqa: E731


def num(n, en=False):
    return f"{n:,}".replace(",", "," if en else NB)


def dec(x, nd=1, en=False):
    s = f"{x:.{nd}f}".replace("-", "−")
    return s if en else s.replace(".", ",")


def pfmt(p, en=False):
    if p < 0.001:
        m, e = f"{p:.1e}".split("e")
        m = m if en else m.replace(".", ",")
        return f"p = {m} · 10{str(int(e)).translate(str.maketrans('-0123456789', '⁻⁰¹²³⁴⁵⁶⁷⁸⁹'))}"
    s = f"{p:.3f}" if p < 0.1 else f"{p:.2f}"
    return f"p = {s}" if en else f"p = {s.replace('.', ',')}"


# ---- planerna: kontrollsummorna stämmer med filerna ----------------------------------------------------------------
PLANS = {"2026-10-29-okanda-ristare-oberoende": "a09033c8", "2026-10-29-en-och-samma-mastare": "591fd25d",
         "2026-11-08-samma-hand-runor": "32257107", "2026-11-08-textdrag-hand": "add8ff31",
         "2026-11-08-nya-handerna": "9e0037d5", "2026-11-08-tata-karnor": "15c2f757"}
SHA = {}
for k, pre in PLANS.items():
    rec = open(os.path.join(ROOT, "analysplaner", f"{k}.sha256")).read().split()[0]
    act = hashlib.sha256(open(os.path.join(ROOT, "analysplaner", f"{k}.md"), "rb").read()).hexdigest()
    assert rec == act and rec.startswith(pre), k
    SHA[k] = rec[:16]
assert os.path.exists(os.path.join(ROOT, "analysplaner", "2026-11-19-oppen-ristarmodell.md"))  # låst, inte körd

# ---- grupperingen och prövningen på kända ristare (materialet 2026-11-07) ------------------------------------------
AN = json.load(open(os.path.join(CDIR, "anonymous.json"), encoding="utf-8"))
assert (AN["n_stones"], AN["n_known"], AN["n_unattributed"], AN["n_candidates"], AN["n_robust"]) == (1292, 441, 691, 8, 5)
CA = AN["calibration"]
assert (CA["link_km"], CA["lr_min"], round(CA["lr"], 1), pc(CA["precision"]), round(CA["max_spread_km"]), AN["robust_min"]) == (30, 12, 13.6, 71, 23, 0.65)
VA = AN["validation"]
assert (VA["n_groups"], pc(VA["purity"]), pc(VA["purity_geography"]), pc(VA["share_pure"])) == (16, 71, 46, 63)
HO, HN = VA["heldout"], VA["heldout_no_time"]
assert (pc(HO["purity"]), pc(HO["purity_geography"]), pc(HO["difference"]), pc(HO["difference_ci"][0]), pc(HO["difference_ci"][1])) == (86, 71, 15, 13, 17)
assert (HO["runs_above"], HO["runs"], HO["folds"], pc(HN["purity"]), pc(HN["purity_geography"])) == (30, 30, 3, 87, 70)
assert AN["coverage"]["n_carvers"] == 35 and AN["coverage"]["carvers_by_province"] == {"Ög": 1, "Sö": 8, "U": 25, "Vs": 1}
SHARE = AN["coverage"]["share_attributed"]
assert [pc(SHARE[p]) for p in ("U", "Sö", "Ög", "Sm", "Vg", "M")] == [70, 46, 5, 2, 1, 8]
G = AN["groups"]
assert len(G) == 17
CAND = [g for g in G if g["status"] == "candidate"]
assert [(g["name"], g["n"], g["provinces"]) for g in CAND] == [
    ("Konungsundsgruppen", 31, ["Ög"]), ("Vibygruppen", 15, ["Ög"]), ("Vetlandagruppen", 14, ["Sm"]), ("Kölabygruppen", 13, ["Vg"]),
    ("Sättnagruppen", 7, ["M"]), ("Leksbergsgruppen", 6, ["Vg"]), ("Husabygruppen", 6, ["Vg"]), ("Dalumsgruppen", 5, ["Vg"])]
ROB = [g["name"] for g in CAND if g["robust"]]
assert ROB == ["Konungsundsgruppen", "Vetlandagruppen", "Kölabygruppen", "Leksbergsgruppen", "Husabygruppen"]
KNOWN = [g for g in G if g["status"] == "known"]
N_KNOWN_USO = sum(set(g["provinces"]) <= {"U", "Sö"} for g in KNOWN)
assert (len(KNOWN), N_KNOWN_USO) == (9, 8)
KOL = next(g for g in CAND if g["name"] == "Kölabygruppen")
assert {"Vg 181", "Vg 130"} <= set(KOL["stones"])  # två stenar som litteraturen knyter till olika namngivna ristare
# versionen 2026-10-29 (som de oberoende proven och litteraturens par gjordes på) hade 16 grupper och Konungsund 28 stenar
OK = J("utdata", "okanda_ristare", "okanda_ristare.json")
assert OK["fingerprint"] == "3f58e9339191761e"
OLDG = {g["parish"]: len(g["stones"]) for g in OK["candidates"]["groups"]}
assert OLDG == {"Konungsunds": 28, "Vetlanda": 14, "Kölaby": 13, "Leksbergs": 6, "Husaby": 6}
METHODS = open(os.path.join(ROOT, "METHODS.md"), encoding="utf-8").read()
assert "Grupperna blev i genomsnitt 85 % samma ristare mot 69 %" in METHODS  # rapportversion 1:s tal (2026-10-20)

# fördelningen av de kända ristarnas stenar och överföringen mellan landskapen
OV = J("utdata", "ristare", "ut", "ristare_overforing.json")
N_U, N_SO, N_OTHER = OV["Sö_till_U"]["n_test_stenar"], OV["U_till_Sö"]["n_test_stenar"], OV["USö_till_övriga"]["n_test_stenar"]
assert (N_U, N_SO, N_OTHER) == (373, 59, 9) and N_U + N_SO + N_OTHER == AN["n_known"]
SU = OV["Sö_till_U"]
assert (pc(SU["renhet"]), pc(SU["geografi"]), SU["körningar_p05"], SU["körningar"]) == (74, 61, 0, 30)
assert OV["U_till_Sö"]["grupper_per_körning"] == 1 and OV["USö_till_övriga"]["n_grupper"] == 0
assert pc(N_U / AN["n_known"]) == 85

# ---- de oberoende proven (låsta 2026-10-29) ----------------------------------------------------------------------
CO = OK["control"]["summary"]
assert (OK["control"]["n_carvers"], OK["B"], OK["radius_km"]) == (26, 9999, 30)
assert CO["rock"]["p"] < 1e-8 and CO["height"]["p"] < 1e-4 and CO["names"]["p"] < 1e-17
assert OK["holds"] == {"H1": True, "H2": False, "H3": True}
assert (round(OK["holm"]["H1"], 4), round(OK["holm"]["H3"], 3), round(OK["p"]["H2"], 2)) == (0.0023, 0.035, 0.32)
KON = OK["candidates"]["groups"][0]
assert KON["parish"] == "Konungsunds" and (pc(KON["rock"]["obs"]), pc(KON["rock"]["null_mean"]), KON["rock"]["p"]) == (92, 77, 0.0001)
MA = J("utdata", "okanda_ristare", "mastare_del12.json")
H5 = MA["part2"]
assert H5["verdict"] == "håller" and 0.004 < H5["H5"]["p"] < 0.005 and H5["control"]["p"] < 1e-12
SP = {c["group"]: c for c in H5["candidates"]}
assert (SP["Kölaby"]["p"], round(SP["Konungsund"]["p"], 3)) == (0.0001, 0.033)
P1 = MA["part1"]
assert (P1["Konungsund"]["span"], P1["Konungsund"]["verdict"], P1["Kölaby"]["verdict"], P1["Leksberg"]["verdict"]) == (32.5, "förenligt", "förenligt", "förenligt")
assert (pc(P1["Konungsund"]["coverage"]), pc(P1["_kända_ristare_U_Sö"]["coverage_median"])) == (44, 12)
MM = J("utdata", "okanda_ristare", "mastare_modell.json")
DOM, PURE = MM["estimates"]["dom"], MM["estimates"]["pure"]
assert MM["n_calibration"] == 912 and (pc(DOM["base_rate"]), pc(PURE["base_rate"])) == (84, 62)
assert round(DOM["coef"]["pct_rock"], 1) == -3.7 and round(MM["validation"]["pure_full"]["auc"], 2) == 0.90
CID = {2: "Konungsund", 5: "Vetlanda", 6: "Kölaby", 12: "Leksberg", 13: "Husaby"}
assert {g["id"]: g["parish"].rstrip("s") for g in OK["candidates"]["groups"]} == {2: "Konungsund", 5: "Vetlanda", 6: "Kölaby", 12: "Leksberg", 13: "Husaby"}
MDOM = {CID[c["candidate"]]: pc(c["p"]) for c in DOM["candidates"]}
MPURE = {CID[c["candidate"]]: pc(c["p"]) for c in PURE["candidates"]}
assert MDOM == {"Konungsund": 76, "Vetlanda": 98, "Kölaby": 78, "Leksberg": 94, "Husaby": 88} and MPURE["Konungsund"] == 8

# ---- litteraturens par (beskrivande, 2026-10-29) -----------------------------------------------------------------
SRI = J("utdata", "okanda_ristare", "sri_par.json")
TESTED = [p for p in SRI["pairs"] if p.get("tested")]
assert (len(TESTED), SRI["same_group"], SRI["expected_from_neighbours"]) == (9, 6, 4.82)
assert abs(sum(p["neighbours_same_group"] for p in TESTED) - SRI["expected_from_neighbours"]) < 0.01
assert SRI["merged_signed_carvers"] == [["Vg 181", "Vg 130"]]
LIT = {x["signum"]: x for x in J("data", "carver_literature.json")["signatures"]}
assert (LIT["Vg 181"]["carver"], LIT["Vg 130"]["carver"], LIT["Vg 181"]["page"], LIT["Vg 130"]["page"]) == ("Hávarðr(?)", "Tryggvi(?)", "s. 350", "s. 350")
_SRIP = {tuple(a["stones"]): a["page"] for a in J("data", "carver_literature.json")["attributions"] if a["source"] == "SRI V"}
assert _SRIP[("Vg 181", "Vg 158")] == "s. 296, 325 f." and _SRIP[("Vg 130",)] == "s. 250 f."
LEKS = [p for p in TESTED if {p["a"], p["b"]} <= {"Vg 11", "Vg 13", "Vg 15"}]
assert len(LEKS) == 3 and all(p["same_group"] and p["neighbours_same_group"] == 1.0 for p in LEKS)

# ---- de fyra låsta proven mot Runor 2020 (2026-11-08) ------------------------------------------------------------
SH = J("utdata", "samma_hand", "resultat.json")
assert SH["plan_sha"] == "32257107" and SH["corpus"] == "510ebfb3" and (SH["runor_notes"], SH["links"]) == (129, 230)
H1 = SH["H1"]
assert (H1["groups"], pc(H1["mean_obs"]), pc(H1["mean_ctrl"]), H1["better"], H1["worse"], round(H1["p"], 2), H1["holds"]) == (14, 50, 44, 5, 7, 0.57, False)
U1015 = next(g for g in SH["groups"] if g["stones"][0] == "U 1015")
assert len(U1015["stones"]) == 9 and set(U1015["model"].values()) == {"Öpir 1"} and pc(U1015["ctrl"]) == 85
TD = J("utdata", "textdrag_hand", "resultat.json")
assert TD["plan_sha"] == "add8ff31" and (TD["stones"], TD["traits"]) == (1564, 43)
assert (TD["K"]["better"], TD["K"]["carvers"], TD["K"]["holds"]) == (30, 37, True) and TD["K"]["p"] < 1e-4
assert (TD["T"]["better"], TD["T"]["groups"], round(TD["T"]["p"], 4), TD["T"]["holds"]) == (16, 18, 0.0002, True)
assert (TD["T"]["unnamed_only"]["groups"], round(TD["T"]["unnamed_only"]["p"], 3)) == (15, 0.001)
NH = J("utdata", "nya_hander", "resultat.json")
TH, N1 = NH["threshold"], NH["N1"]
assert NH["plan_sha"] == "9e0037d5" and (pc(TH["same_carver_linked"]), pc(TH["different_carver_linked"])) == (67, 43)
assert (pc(N1["mean_linked"]), pc(N1["mean_control"]), N1["better"], N1["groups"], round(N1["p"], 4), N1["holds"]) == (89, 33, 15, 16, 0.0004, True)
BIG = max(NH["N2_groups"], key=lambda g: g["size"])
assert (BIG["size"], round(BIG["span_km"])) == (645, 419)
TK = J("utdata", "tata_karnor", "resultat.json")
C1 = TK["C1"]
UNN = [g for g in TK["C1_groups"] if g["unnamed"]]
assert TK["plan_sha"] == "15c2f757" and TK["cstar"] == 0.58 and pc(TK["precision_at_cstar"]["precision"]) == 70
assert (C1["groups"], round(C1["p"], 3), C1["holds"]) == (16, 0.125, False)
assert (len(UNN), sum(g["together"] == 0 for g in UNN)) == (13, 12)
assert [round(g["together"] * 36) for g in UNN if g["together"] > 0] == [1] and next(g for g in UNN if g["together"] > 0)["stones"][0] == "U 1015"
PH = TK["post_hoc"]
assert (PH["runor_pairs"], pc(PH["runor_share_at_cstar"])) == (57, 7)

# ---- kodläget ----------------------------------------------------------------------------------------------------
COMMITS = {"9a600d5": "2026-10-20", "8945a74": "2026-10-29", "863e63d": "2026-10-31", "285b204": "2026-11-08",
           "5eeb691": "2026-11-08", "50aa732": "2026-11-08", "f852a80": "2026-11-08"}
if os.path.isdir(os.path.join(ROOT, ".git")):
    git = lambda *a: subprocess.run(["git", "-C", ROOT, *a], capture_output=True, text=True)  # noqa: E731
    for c, d in COMMITS.items():
        assert git("show", "-s", "--format=%ad", "--date=short", c).stdout.strip() == d, c
    assert git("log", "-1", "--format=%ad", "--date=short", "v3.1.0").stdout.strip() == "2026-11-06"
    # metoden i r/anonymous.R är oförändrad sedan 2026-10-29 (då bara namnen på grupperna ändrades)
    assert git("log", "--format=%h", "5542b59..HEAD", "--", "r/anonymous.R").stdout.strip() == ""
    # rapportversion 1 så som den byggdes
    V1 = json.loads(git("show", "863e63d:utdata/rapporter/rapport_skrivmiljoer.json").stdout)
    assert "blir till 85 procent en och samma hand" in V1["title"] and "Rapportversion 1, 2026-10-31" in V1["body"]

SLUG = "skrivmiljoer-utan-namn"
title = ("Skrivmiljöer utan namn: prövad på kända ristare samlar metoden grupper som till 86 procent är samma ristare, mot "
         "71 för grannstenar – att grupperna utan ristare är en hand är inte visat")
title_en = ("Writing milieus without names: tested on known carvers, the method gathers groups that are 86 percent the same "
            "carver, against 71 for neighbouring stones – that the groups without a carver are one hand is not shown")
summary = ("Metodrapport. Runstenar utan ristare grupperas efter hur de är skrivna. Prövad på kända ristare, främst i "
           "Uppland, är en grupp i genomsnitt till 86 procent samma ristare, mot 71 procent för lika många närliggande "
           "stenar. Att grupperna av stenar utan ristare är en hand är inte visat: litteraturens par hamnar bara något "
           "oftare i samma grupp än grannar gör, och närliggande textdrag känner igen par men inte runologernas grupper.")
summary_en = ("Methods report. Runestones without a carver are grouped by how they are written. Tested on known carvers, "
              "mainly in Uppland, a group is on average 86 percent the same carver, against 71 percent for as many nearby "
              "stones. That the groups of stones without a carver are one hand is not shown: the literature's pairs end up "
              "in the same group only slightly more often than neighbours do, and related text features recognise pairs "
              "but not the runologists' groups.")
CITE_EN = (f"Kvant, V. ({TODAY[:4]}). {title_en}. Research report (methods report), report version {REPORT_VERSION}; analysis in "
           f"Vitki {APP_VERSION}. https://vitkirunor.se/en/forskningsrapporter/{SLUG}")
POP_SV = "https://vitkirunor.se/artiklar/ristarna-som-aldrig-blev-ihagkomna"
POP_EN = "https://vitkirunor.se/en/artiklar/ristarna-som-aldrig-blev-ihagkomna"
RM_SV = "https://vitkirunor.se/forskningsrapporter/ristarforslag-blindprov"
RM_EN = "https://vitkirunor.se/en/forskningsrapporter/ristarforslag-blindprov"


def chart(sv):
    rows = [":::chart Andel av en grupp som är gruppens vanligaste ristare, kända ristare" if sv
            else ":::chart Share of a group that is the group's most common carver, known carvers"]
    st = (("Första valideringen", "Ristare som hölls utanför", "Utan de tidsberoende dragen") if sv else
          ("First validation", "Carvers held out", "Without the time-dependent traits"))
    me, ge = (("Grupperna", "Lika många närliggande stenar") if sv else ("The groups", "As many nearby stones"))
    f = (lambda x: f"{100 * x:.0f}")
    for lab, a, b in ((st[0], VA["purity"], VA["purity_geography"]), (st[1], HO["purity"], HO["purity_geography"]),
                      (st[2], HN["purity"], HN["purity_geography"])):
        rows += [f"# {lab}", f"+{me} | {f(a)} |", f"{ge} | {f(b)} |"]
    rows += ["Källa: Rundata; ristare med minst tre säkra stenar, 85 procent av stenarna i Uppland. Diagram: Vitki." if sv
             else "Source: Rundata; carvers with at least three secure stones, 85 percent of the stones in Uppland. Chart: Vitki.", ":::"]
    return "\n".join(rows)


def cand_list(sv):
    pv = {"Ög": "Östergötland", "Sm": "Småland", "Vg": "Västergötland", "M": "Medelpad"}
    return "; ".join(f"{g['name'] if sv else re.sub('s?gruppen$', ' group', g['name'])} ({g['n']}, {pv[g['provinces'][0]]})" for g in CAND)


def mlist(sv):
    order = ("Vetlanda", "Leksberg", "Husaby", "Kölaby", "Konungsund")
    return ", ".join(f"{k} {MDOM[k]}" for k in order) + (" procent" if sv else " percent")


ROB_EN = ", ".join(re.sub("s?gruppen$", " group", x) for x in ROB)

# ---- ändringsloggen ----------------------------------------------------------------------------------------------
LOG_SV = f"""## Ändringslogg

**Version 1, {V1_DATE}.** Skrevs men publicerades inte. Titeln var ”grupper av runstenar utan ristare blir till 85 procent en och samma hand när metoden prövas på ristare den inte sett”.

**Version {REPORT_VERSION}, {TODAY}.** Omskriven innan den publicerats, eftersom titeln och slutsatsen gick längre än proven. Ändringarna och skälen:

- **Vad de 85 procenten mätte.** Version 1 sa att grupper av stenar *utan* ristare blir en hand till 85 procent. Talet mätte något annat: hur stor del av en grupp som är gruppens vanligaste ristare när metoden körs på stenar av *kända* ristare, av vilka 85 procent står i Uppland. Titeln, sammanfattningen, avsnitt 5.1 och slutsatsen säger nu det, och att provet inte säger hur grupperna av stenar utan ristare är sammansatta.
- **Omräknat på materialet den 7 november 2026.** Med samma antal stenar ger metoden nu {pc(HO['purity'])} mot {pc(HO['purity_geography'])} procent (tidigare 85 mot 69), {len(G)} grupper (tidigare 16) och Konungsundsgruppen {CAND[0]['n']} stenar (tidigare 28). De oberoende proven och litteraturens par gäller grupperna så som de var den 29 oktober; det står i 4.8.
- **Det som version 1 utelämnade.** Jämförelsen med litteraturens par (29 oktober 2026, före version 1) står nu i 5.6: sex av nio par i samma grupp mot 4,8 väntade, och Kölabygruppen rymmer två stenar med olika ristares namn. Mästarmodellens resultat ur den låsta planen den 29 oktober står i 5.3 och 5.5, bland annat att delad bergart inte skiljer grupper som är en hand från blandade grupper. Version 1 kallade Konungsunds- och Kölabygrupperna de starkaste förslagen till okända ristare; det står inte längre.
- **De nya proven.** De fyra låsta proven mot runologernas grupper i Runor 2020 den 8 november 2026 står i 5.7 och i sammanfattningen: ristarmodellen höll inte, och textdragen känner igen par men inte grupper. Inget av dem prövade grupperingen i denna rapport, och det står också.
- **Form.** Kitzler Åhfeldt (2002) har rätt serienamn, *Theses and Papers in Scientific Archaeology*. Länkarna är fullständiga webbadresser. Referenser till Runor 2020, Sveriges runinskrifter, Wilcoxon (1945) och Sokal & Michener (1958) har lagts till."""

LOG_EN = f"""## Change log

**Version 1, {V1_DATE}.** Written but not published. The title was ”groups of runestones without a carver come out 85 percent one and the same hand when the method is tested on carvers it has not seen”.

**Version {REPORT_VERSION}, {TODAY}.** Rewritten before publication, since the title and the conclusion went further than the tests. The changes and the reasons for them:

- **What the 85 percent measured.** Version 1 said that groups of stones *without* a carver come out one hand to 85 percent. The figure measured something else: how large a part of a group is the group's most common carver when the method is run on stones by *known* carvers, 85 percent of them in Uppland. The title, the abstract, section 5.1 and the conclusion now say so, and that the test does not say how the groups of stones without a carver are made up.
- **Recomputed on the material of 7 November 2026.** With the same number of stones the method now gives {pc(HO['purity'])} against {pc(HO['purity_geography'])} percent (before 85 against 69), {len(G)} groups (before 16) and the Konungsund group {CAND[0]['n']} stones (before 28). The independent tests and the literature's pairs apply to the groups as they were on 29 October; section 4.8 says so.
- **What version 1 left out.** The comparison with the literature's pairs (29 October 2026, before version 1) now stands in 5.6: six of nine pairs in the same group against 4.8 expected, and the Kölaby group holds two stones with different carvers' names. The results of the master model from the locked plan of 29 October stand in 5.3 and 5.5, among them that shared rock type does not tell groups that are one hand from mixed groups. Version 1 called the Konungsund and Kölaby groups the strongest suggestions of unknown carvers; that no longer stands.
- **The new tests.** The four locked tests against the runologists' groups in Runor 2020 on 8 November 2026 stand in 5.7 and in the abstract: the carver model did not hold, and the text features recognise pairs but not groups. None of them tested the grouping in this report, and that is stated too.
- **Form.** Kitzler Åhfeldt (2002) has the correct series name, *Theses and Papers in Scientific Archaeology*. The links are full web addresses. References to Runor 2020, Sveriges runinskrifter, Wilcoxon (1945) and Sokal & Michener (1958) have been added."""


body = f"""*Viktor Kvant, oberoende forskare. Metodrapport, delvis prövad. Rapportversion {REPORT_VERSION}, {TODAY}; version 1 skrevs {V1_DATE} men publicerades inte. Tidslinje: {TL_SV}. Analysen är gjord i Vitki {APP_VERSION}. Licens CC BY 4.0. Den engelska versionen är den kanoniska för citering: {CITE_EN}. Nyckelord: runstenar, vikingatid, runristare, skrivmiljöer, attribuering, klustring, validering, Runor 2020. Konkurrerande intressen: inga. Finansiering: ingen.*

## Sammanfattning

**Vad som inte är prövat och vad som faller.** Huvudmåttet, {pc(HO['purity'])} procent, gäller grupper som metoden bildar av stenar med *känd* ristare, varav {pc(N_U / AN['n_known'])} procent står i Uppland, och provet var inte låst. Det säger inte att grupperna av stenar utan ristare är en hand. Grupperingen är inte prövad mot runologernas bedömningar av vilka stenar som är gjorda av samma hand, och mot litteraturens par klarar den sig bara något bättre än grannstenar. Av de närliggande metoder som prövades mot runologernas bedömningar under låsta planer höll ristarmodellen inte, och textdragen kände igen par men inte grupper.
**Bakgrund och syfte.** Många runstenar saknar ristare, särskilt i Götaland. Rapporten redovisar en metod som grupperar dem efter handens drag och vad dess prov säger.
**Material.** {num(AN['n_stones'])} svenska vikingatida runstenar med minst fem läsbara ord i Samnordisk runtextdatabas (Rundata): {AN['n_known']} med säker ristare och {AN['n_unattributed']} utan.
**Metod.** Stenarna jämförs i stavning, skiljetecken, formler, runpar, stil och kors, men inte i plats och innehåll, och stenar som liknar varandra lika mycket som en ristares stenar grupperas. Metoden prövas på kända ristare som hålls utanför, och grupperna mot drag utanför likheten och mot litteraturens par.
**Resultat.** På kända ristare var en grupp i genomsnitt till {pc(HO['purity'])} procent gruppens vanligaste ristare, mot {pc(HO['purity_geography'])} procent för lika många närliggande stenar. Bland stenarna utan ristare blev det {len(G)} grupper, varav {len(CAND)} utan likhet med en känd ristare; de delar bergart och ovanliga stavningar oftare än traktens stenar. Av nio par som litteraturen knyter till samma ristare låg sex i samma grupp, mot 4,8 väntade för grannar. I de låsta proven mot Runor 2020 länkade textdragen {pc(N1['mean_linked'])} procent av runologernas par mot {pc(N1['mean_control'])} för grannar, men tolv av tretton grupper av onämnda händer samlades inte.
**Slutsats.** Metoden hittar tillbaka till kända ristare bättre än närheten gör, där den kan prövas. Grupperna av stenar utan ristare är skrivmiljöer i den meningen att stenarna skrivs lika; om en grupp är en ristare, en verkstad eller en bygds sätt att skriva avgör proven inte.

## 1. Inledning

Runologer har länge grupperat osignerade stenar efter stil, runformer och stavning för att finna ristarna bakom dem (Axelson 1993; Stille 1999). Magnus Källström (2007) har talat om skriftmiljöer: bygder där ristare och beställare delade sätt att skriva. Laila Kitzler Åhfeldt (2002) har skilt ristare åt efter huggspåren. I Uppland har de flesta stenar en ristare i Rundata, men i Götaland bara en liten del, och där är frågan vilka händer som ligger bakom de många stenarna utan namn.

Syftet här är att redovisa en metod som grupperar stenar utan ristare efter handens drag, att säga exakt vad dess prövning mäter, och hur den och närliggande metoder har klarat prov mot litteraturen och mot runologernas egna bedömningar. En grupp får ett arbetsnamn efter typstenens socken; namnet är en etikett för stenarna, inte ett påstående om en person.

## 2. Förregistrering: vad som var bestämt i förväg och vad som inte var det

**Inte låst.** Metoden byggdes den 11 oktober 2026. Gränserna valdes efter den första valideringen på kända ristare, som därför är något för optimistisk. Prövningen på ristare som hölls utanför den 20 oktober, som ger rapportens huvudmått, och jämförelsen med litteraturens par den 29 oktober var inte låsta.

**Låst den 29 oktober 2026.** Två planer, båda med en positiv kontroll på kända ristare. Den första prövar grupperna mot bergart, höjd och personnamn (SHA-256 `{SHA['2026-10-29-okanda-ristare-oberoende']}…`), den andra mot tidsspann och ovanliga stavningar, och skattar hur sannolikt det är att en grupp är en hand (SHA-256 `{SHA['2026-10-29-en-och-samma-mastare']}…`).

**Låst den 8 november 2026.** Fyra planer prövade närliggande metoder mot runologernas bedömningar i Runor 2020: ristarmodellen (`{SHA['2026-11-08-samma-hand-runor']}…`), likheten i textdragen (`{SHA['2026-11-08-textdrag-hand']}…`), en regel som länkar par (`{SHA['2026-11-08-nya-handerna']}…`) och täta kärnor av länkade stenar (`{SHA['2026-11-08-tata-karnor']}…`). Ingen av dem prövar grupperingen i denna rapport, men alla prövar samma fråga mot bedömningar som metoderna inte har sett.

**Inte gjort.** Grupperingen har inte prövats mot runologernas grupper. En plan för en öppen ristarmodell låstes den 19 november 2026 men är inte körd och gäller inte denna gruppering.

Bara proven under de låsta planerna är konfirmatoriska; huvudmåttet och jämförelsen med litteraturen är explorativa.

## 3. Material

- **Stenarna.** {num(AN['n_stones'])} svenska vikingatida runstenar i Samnordisk runtextdatabas (Rundata) med minst fem läsbara ord, i materialets version den 7 november 2026. {AN['n_known']} har en säker ristare och {AN['n_unattributed']} har ingen. Bara runstenar.
- **De kända ristarna.** {AN['coverage']['n_carvers']} ristare med minst tre säkra stenar: 25 i Uppland, 8 i Södermanland, en i Östergötland och en i Västmanland. Av deras {AN['n_known']} stenar står {N_U} i Uppland, {N_SO} i Södermanland och {N_OTHER} i andra landskap.
- **Täckningen.** I Uppland har {pc(SHARE['U'])} procent av stenarna en ristare i Rundata, i Södermanland {pc(SHARE['Sö'])}, men i Östergötland {pc(SHARE['Ög'])}, Småland {pc(SHARE['Sm'])}, Västergötland {pc(SHARE['Vg'])} och Medelpad {pc(SHARE['M'])} procent.
- **Litteraturens par.** Nio par av stenar som Sveriges runinskrifter för Östergötland och Västergötland (Brate 1911–18; Jungner & Svärdström 1940–70) knyter till samma ristare, där båda stenarna saknar ristare i Rundata och ingår i analysen.
- **Runologernas grupper.** Databasen Runor (Riksantikvarieämbetet 2020) har {SH['runor_notes']} noteringar av formen ”samma som gjort X”, ofta för händer utan namn; de ger 14 till 18 grupper beroende på provets villkor.

## 4. Metod

**4.1 Likheten.** Gowers avstånd (Gower 1971) mellan varje par av stenar i handens drag: stilgrupp, kors, kortkvistrunor, språkdrag, skiljetecken, bindrunor, formler och de vanligaste runparen, men inte plats och innehåll. Måttet ligger mellan 0 och 1 och väger samman olika slags drag; 0 betyder lika i allt.

**4.2 Gränsen.** Gränsen för att länka två stenar bestäms på par av stenar med känd ristare inom {CA['link_km']} km: par under gränsen ska vara minst {CA['lr_min']} gånger vanligare bland samma ristares par än bland olika ristares (i materialet {dec(CA['lr'])}). Av länkade par med känd ristare är då {pc(CA['precision'])} procent samma ristare.

**4.3 Grupperna.** Stenar utan ristare länkas när de ligger inom {CA['link_km']} km och under gränsen, och nätet delas med Louvain-metoden (Blondel m.fl. 2008), som söker grupper med många länkar inom och få mellan. En grupp redovisas när den har minst fyra stenar och inte är mer utspridd än 90 procent av de kända ristarna ({round(CA['max_spread_km'])} km). En grupp som ligger lika nära en känd ristares stenar i närheten som två stenar av samma ristare brukar göra räknas som lik den ristaren.

**4.4 Prövningen på kända ristare.** Samma förfarande körs på stenar med känd ristare, som om ristaren vore okänd. Måttet är *renheten*: andelen av en grupps stenar som är av gruppens vanligaste ristare, i genomsnitt viktat efter gruppens storlek. Jämförelsen är lika många stenar närmast gruppens typsten. I prövningen på ristare som hölls utanför delas de {AN['coverage']['n_carvers']} ristarna slumpvis i tre delar; gränserna tas fram på två och grupper bildas bland den tredje delens stenar, trettio gånger. En grupp bland stenarna utan ristare är robust när minst {pc(AN['robust_min'])} procent av den återkommer utan de tidsberoende dragen.

**4.5 Proven mot drag utanför likheten.** Bergart, höjd och personnamn ur Rundata, och ovanliga stavningar av vanliga ord: för varje grupp jämförs andelen par som delar dragen med 9{NB}999 slumpvisa mängder stenar ur samma trakt ({OK['radius_km']} km) och med samma stilgrupper, Holm-korrigerat över bergart, höjd och namn. Positiv kontroll: {OK['control']['n_carvers']} kända ristare. En logistisk modell, skattad på {MM['n_calibration']} grupper som metoden bildade av kända ristares stenar, ger sannolikheten att minst tre fjärdedelar av en grupp, eller hela gruppen, är en hand.

**4.6 Litteraturens par.** För varje par räknas om båda stenarna hamnar i samma grupp. Det jämförs med hur ofta stenar utan ristare på samma avstånd från parets ena sten hamnar i samma grupp som den; summan över paren är det antal par som väntas i samma grupp om grupperna bara följde avståndet.

**4.7 Proven mot runologernas grupper.** De fyra låsta proven jämför runologernas grupper med grannstenar på samma avstånd (± 25 procent, minst ± 1 km, 999 dragningar) med Wilcoxons teckenrangtest, ensidigt, över grupperna (Wilcoxon 1945). (a) *Ristarmodellen* väljer för varje sten bland de namngivna ristarna: får stenarna i en grupp samma förslag? (b) *Textdragen* är likhet i teckenföljder, skiljetecken och bindrunor, viktade efter hur ovanliga de är, och i materialets {TD['traits']} språkdrag och formler, utan plats. (c) *Parregeln* länkar två stenar när deras likhet överstiger deras medellikhet med stenar på samma avstånd med en gräns som valdes på de namngivna ristarna. (d) *Täta kärnor* samlar stenarna med medelkoppling (Sokal & Michener 1958) och kapar där {pc(TK['precision_at_cstar']['precision'])} procent av paren av namngivna ristare i samma kärna är samma ristare.

**4.8 Avvikelser.** Inga från de två planerna den 29 oktober. I två av proven den 8 november rättades ett fel innan något tolkades (noteringarna i Runor lästes först fel; grupper utan jämförbara grannar räknades först med). Grupperingen och prövningen är omräknade på materialet den 7 november 2026 med samma kod; de oberoende proven och jämförelsen med litteraturen gäller grupperna den 29 oktober, då Konungsundsgruppen hade {OLDG['Konungsunds']} stenar i stället för {CAND[0]['n']}.

## 5. Resultat

**5.1 Prövningen på kända ristare.** I den första valideringen, där gränserna valdes, var en grupp i genomsnitt till {pc(VA['purity'])} procent gruppens vanligaste ristare, mot {pc(VA['purity_geography'])} procent för lika många närliggande stenar, och {pc(VA['share_pure'])} procent av grupperna var till minst tre fjärdedelar en ristare. Med gränserna framtagna på andra ristare var en grupp till {pc(HO['purity'])} procent samma ristare, mot {pc(HO['purity_geography'])} procent för närliggande stenar: en skillnad på {pc(HO['difference'])} procentenheter (95 %-intervall {pc(HO['difference_ci'][0])}–{pc(HO['difference_ci'][1])}), till gruppernas fördel i alla {HO['runs']} upprepningar. Utan de tidsberoende dragen: {pc(HN['purity'])} mot {pc(HN['purity_geography'])} procent.

I klartext: när metoden får stenar av kända ristare, nästan alla i Uppland, och samlar dem i grupper utan att veta vem som ristat dem, är ungefär sex stenar av sju i en grupp av samma hand. Tar man i stället lika många stenar som står närmast varandra blir det ungefär sju av tio. Det säger hur väl metoden hittar tillbaka till kända ristare, inte att grupperna av stenar utan ristare är en hand.

{chart(True)}

Provets stenar är bara stenar av ristare med minst tre säkra stenar, och närheten ensam ger redan {pc(HO['purity_geography'])} procent; det metoden tillför är skillnaden, {pc(HO['difference'])} procentenheter.

**5.2 Per landskap.** {pc(N_U / AN['n_known'])} procent av provets stenar står i Uppland. Flyttad från Södermanland till Uppland gav gränsen {pc(SU['renhet'])} mot {pc(SU['geografi'])} procent, men i ingen av de {SU['körningar']} upprepningarna var skillnaden säker. Från Uppland till Södermanland bildades bara en grupp per upprepning. I Östergötland, Småland, Västergötland och Medelpad, där de möjliga okända händerna finns, har bara {N_OTHER} stenar en känd ristare, och där går metoden inte att pröva.

**5.3 Kalibreringen.** Metoden ger ingen sannolikhet per grupp; gränsen ger {pc(CA['precision'])} procent samma ristare bland länkade par med känd ristare, på samma material. Mästarmodellen ger sannolikheten att minst tre fjärdedelar av en grupp är en hand, kalibrerad på grupper i Uppland och Södermanland (förmågan att skilja grupperna åt, AUC, {dec(MM['validation']['pure_full']['auc'], 2)}): {mlist(True)}, mot grundfrekvensen {pc(DOM['base_rate'])}. Att Konungsundsgruppen helt är en hand får {MPURE['Konungsund']} procent, mot grundfrekvensen {pc(PURE['base_rate'])}. Där grupperna ligger går det inte att pröva.

**5.4 Grupperna bland stenarna utan ristare.** Det blev {len(G)} grupper. Av dem liknar {len(KNOWN)} en känd ristare i närheten, {N_KNOWN_USO} av dem i Uppland och Södermanland, och {len(CAND)} gör det inte (antal stenar inom parentes): {cand_list(True)}. Fem av dem är robusta utan de tidsberoende dragen: {', '.join(ROB)}.

**5.5 Proven mot drag utanför likheten.** I den positiva kontrollen delar kända ristares stenar bergart, höjd och personnamn oftare än traktens stenar (alla p under 0,0001). För de fem robusta grupperna:

- **Bergart – håller**, Holm-korrigerat p = 0,002, buret av Konungsundsgruppen ({pc(KON['rock']['obs'])} procent av paren delar bergart mot {pc(KON['rock']['null_mean'])} i trakten) och Kölabygruppen. Men i mästarmodellen delade blandade grupper av kända ristare bergart minst lika ofta som rena (koefficient {dec(DOM['coef']['pct_rock'])}): bergarten skiljer en grupp från traktens stenar, inte en hand från en blandad grupp.
- **Höjd – faller**, p = 0,32; bara tre grupper har mått.
- **Namn – håller**, Holm-korrigerat p = 0,035, framför allt i Kölabygruppen. Men kända ristare delar också namn, eftersom de ofta gjorde flera stenar åt samma släkt, så delade namn skiljer inte en ristare från en släkts beställningar.
- **Ovanliga stavningar – håller**, {pfmt(H5['H5']['p'])}, burna av Kölaby ({pfmt(SP['Kölaby']['p'])}) och Konungsund ({pfmt(SP['Konungsund']['p'])}).
- **Tiden.** Spannet mellan gruppens äldsta och yngsta stilgrupp är {dec(P1['Konungsund']['span'])} år för Konungsund, Kölaby och Leksberg, vilket ryms i en ristares livsgärning. Konungsundsgruppen omfattar {pc(P1['Konungsund']['coverage'])} procent av traktens samtida stenar, mot {pc(P1['_kända_ristare_U_Sö']['coverage_median'])} procent i median för de kända ristarna i Uppland och Södermanland.

**5.6 Litteraturens par.** Av de nio paren låg {SRI['same_group']} i samma grupp, mot {dec(SRI['expected_from_neighbours'])} väntade om grupperna bara följde avståndet. De tre paren i Leksberg ligger i samma grupp, men där hamnar alla grannar på samma avstånd också i gruppen. Kölabygruppen rymmer Vg 181 och Vg 130, som båda är signerade, med två olika och osäkert lästa namn: Hávarðr(?) och Tryggvi(?) (Jungner & Svärdström 1940–70 s. 250 f., 296; Källström 2007 s. 350).

**5.7 Runologernas grupper, prövade på närliggande metoder.** Inget av proven gällde denna gruppering.

- **Ristarmodellen – höll inte.** Inom runologernas {H1['groups']} grupper där minst en sten saknar säker ristare fick båda stenarna i ett par samma förslag i {pc(H1['mean_obs'])} procent av paren, mot {pc(H1['mean_ctrl'])} för grannar på samma avstånd; bättre i {H1['better']} grupper, sämre i {H1['worse']}, {pfmt(H1['p'])}. U 1015 och U 1017–1024, som runologerna håller för en hand utan namn, fick alla förslaget Öpir, och grannarna fick det i {pc(U1015['ctrl'])} procent av fallen.
- **Textdragen – höll.** Runologernas grupper var mer lika än grannarna i {TD['T']['better']} av {TD['T']['groups']} grupper ({pfmt(TD['T']['p'])}), också bland de {TD['T']['unnamed_only']['groups']} grupperna med en hand utan namn ({pfmt(TD['T']['unnamed_only']['p'])}).
- **Parregeln – höll för par.** Den länkade {pc(N1['mean_linked'])} procent av runologernas par mot {pc(N1['mean_control'])} för grannar, bättre i {N1['better']} av {N1['groups']} grupper ({pfmt(N1['p'])}). Men den länkar också {pc(TH['different_carver_linked'])} procent av paren av olika namngivna ristare, och när länkarna fick bilda grupper kedjade de ihop sig: den största fick {BIG['size']} stenar över {BIG['span_km']:.0f} km.
- **Täta kärnor – höll inte.** Av {len(UNN)} grupper med en hand utan namn hamnade {sum(g['together'] == 0 for g in UNN)} inte med något par i samma kärna, och den trettonde (U 1015–1024) med ett par av 36 (p = {dec(C1['p'], 3)}). Efter provet: bara {pc(PH['runor_share_at_cstar'])} procent av runologernas {PH['runor_pairs']} par når gränsen för en kärna.

I klartext: textdragen ser att två stenar är av samma hand oftare än grannstenar är det, men skillnaden är för liten för att samla stenarna till de grupper som runologerna ser.

## 6. Diskussion

**Vad som håller.** Där metoden kan prövas hittar den tillbaka till kända ristare bättre än närheten, och grupperna skiljer sig från traktens stenar i drag som grupperingen inte använder.

**Vad som inte är visat.** Att grupperna av stenar utan ristare är händer; version 1 läste huvudmåttet så, men det mätte provet inte. Varken litteraturens par eller bergarten talar för det, och de närliggande proven mot Runor 2020 pekar åt samma håll utan att pröva just denna gruppering.

**Mot tidigare forskning.** Metoden gör systematiskt det runologer gör när de attribuerar efter stil och stavning (Axelson 1993; Stille 1999). Grupperna motsvarar Källströms (2007) skriftmiljöer i den meningen att stenarna i dem skrivs lika; vad de är utöver det avgör proven här inte.

**Svagheter, i ordning efter vikt.**

1. **Grupperingen är inte prövad mot runologernas grupper.** De låsta proven mot Runor 2020 gällde andra metoder.
2. **Inte prövad där grupperna finns.** I Götaland och Medelpad finns nästan inga kända ristare att pröva mot, och överföringen mellan Södermanland och Uppland gav inget säkert resultat.
3. **Provets stenar är bara flitiga ristares.** Hur metoden fungerar bland stenar där många händer kan ha ristat bara en eller två stenar är inte mätt.
4. **Gränserna valdes efter den första valideringen, och huvudprovet var inte låst.**
5. **Rundatas attribueringar.** De kända ristarna, som metoden kalibreras på, är till stor del själva attribuerade efter stil och stavning.

**Var metoden inte ska användas.** Som attribuering, för enskilda stenar utanför en grupp eller för att kalla en grupp en person: en grupp är en hypotes om en skrivmiljö.

**Vad som skulle avgöra.** Ett låst prov där denna gruppering ställs mot runologernas grupper i Runor 2020 och mot litteraturens signerade stenar i Götaland, med grannstenar på samma avstånd som jämförelse. Huggspårsanalyser (Kitzler Åhfeldt 2002) av stenarna i en grupp skulle pröva handen med ett belägg som inte kommer ur texten.

## 7. Slutsats

Prövad på kända ristare, nästan helt i Uppland, hittar metoden tillbaka till ristarna bättre än närheten: {pc(HO['purity'])} mot {pc(HO['purity_geography'])} procent. Att dess {len(CAND)} grupper av stenar utan ristare, främst i Götaland, är händer är inte visat. Grupperna är förslag om var granskning och huggspårsanalyser kan pröva en hand, inte attribueringar.

## Data och kod

Grupperingen och prövningen på kända ristare är räknade i Vitki {APP_VERSION}, ett öppet forskningsverktyg för runstenar ([vitkirunor.se](https://vitkirunor.se)), på materialets version `{FP}` (räknad den 7 november 2026). Koden i `r/anonymous.R` är oförändrad sedan den 29 oktober 2026. All kod, analysplanerna och resultatfilerna finns öppet på [GitHub](https://github.com/Precatio/runes) under GPL-3.0.

- Grupperingen och prövningen: `r/anonymous.R` (resultat `anonymous.json` under materialets version `{FP}`); prövningen på ristare som hölls utanför och överföringen mellan landskapen `utdata/ristare/ristare_heldout.R` och `utdata/ristare/ristare_overforing.R` (commit `9a600d5`). Metodbeskrivning: `METHODS.md`, avsnitt 1g.
- De oberoende proven: planerna `analysplaner/2026-10-29-okanda-ristare-oberoende.md` och `analysplaner/2026-10-29-en-och-samma-mastare.md`; koden och resultaten i `utdata/okanda_ristare/` (materialets version `3f58e9339191761e`). Litteraturens par: `utdata/okanda_ristare/sri_par.py` (commit `8945a74`).
- Proven mot Runor 2020: `analysplaner/2026-11-08-samma-hand-runor.md` med `utdata/samma_hand/` (commit `285b204`), `analysplaner/2026-11-08-textdrag-hand.md` med `utdata/textdrag_hand/` (`5eeb691`), `analysplaner/2026-11-08-nya-handerna.md` med `utdata/nya_hander/` (`50aa732`) och `analysplaner/2026-11-08-tata-karnor.md` med `utdata/tata_karnor/` (`f852a80`).
- Rapporten byggs av `utdata/blogg/build/build_rapport_skrivmiljoer.py`, som läser alla tal ur resultatfilerna och stannar om något inte stämmer. Mallen: `utdata/rapporter/MALL.md`, version 4. Version 1 finns i commit `863e63d`.
- Metodrapporten om ristarmodellen: [Statistiska ristarförslag ur runtexterna]({RM_SV}). Populär framställning: [Ristarna som aldrig blev ihågkomna]({POP_SV}).

## Referenser

- Axelson, J. 1993. *Mellansvenska runristare. Förteckning över signerade och attribuerade inskrifter*. Runrön 5. Uppsala: Institutionen för nordiska språk, Uppsala universitet.
- Blondel, V. D., Guillaume, J.-L., Lambiotte, R. & Lefebvre, E. 2008. Fast unfolding of communities in large networks. *Journal of Statistical Mechanics*, P10008.
- Brate, E. 1911–18. *Östergötlands runinskrifter* (Sveriges runinskrifter 2). Stockholm: KVHAA.
- Gower, J. C. 1971. A general coefficient of similarity and some of its properties. *Biometrics* 27 (4), s. 857–871.
- Holm, S. 1979. A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics* 6 (2), s. 65–70.
- Jungner, H. & Svärdström, E. 1940–70. *Västergötlands runinskrifter* (Sveriges runinskrifter 5). Stockholm: KVHAA.
- Kitzler Åhfeldt, L. 2002. *Work and Worship: Laser Scanner Analysis of Viking Age Rune Stones*. Theses and Papers in Scientific Archaeology B:9. Stockholm: Stockholms universitet.
- Kvant, V. 2026. *Vitki {APP_VERSION}: metodbeskrivning* (METHODS.md). https://github.com/Precatio/runes
- Källström, M. 2007. *Mästare och minnesmärken. Studier kring vikingatida runristare och skriftmiljöer i Norden*. Stockholm Studies in Scandinavian Philology, New Series 43. Stockholm: Stockholms universitet.
- Riksantikvarieämbetet. 2020. *Runor*. Runinskrifter i Sverige, databas. https://app.raa.se/open/runor
- Samnordisk runtextdatabas (Rundata). Institutionen för nordiska språk, Uppsala universitet. Open Database License.
- Sokal, R. R. & Michener, C. D. 1958. A statistical method for evaluating systematic relationships. *University of Kansas Science Bulletin* 38, s. 1409–1438.
- Stille, P. 1999. *Runstenar och runristare i det vikingatida Fjädrundaland. En studie i attribuering*. Runrön 13. Uppsala: Institutionen för nordiska språk, Uppsala universitet.
- Wilcoxon, F. 1945. Individual comparisons by ranking methods. *Biometrics Bulletin* 1 (6), s. 80–83.

:::box Det viktigaste i korthet
- Metoden samlar runstenar efter hur de är skrivna, och på kända ristare hittar den tillbaka till ristaren klart bättre än närheten gör.
- Det är prövat nästan bara i Uppland och på stenar av kända ristare, inte på grupperna av stenar utan ristare i Götaland.
- Grupperna utan ristare är skrivmiljöer: stenar som skrivs lika. Om en grupp är en ristare, en verkstad eller en bygd avgör proven inte.
- Textdragen känner igen att två stenar är av samma hand, men räcker inte för att samla runologernas grupper.
:::

{LOG_SV}
"""

body_en = f"""*Viktor Kvant, independent researcher. Methods report, partially tested. Report version {REPORT_VERSION}, {TODAY}; version 1 was written {V1_DATE} but not published. Timeline: {TL_EN}. The analysis was made in Vitki {APP_VERSION}. Licence CC BY 4.0. This English version is the canonical one for citation: {CITE_EN}. Keywords: runestones, Viking Age, rune carvers, writing milieus, attribution, clustering, validation, Runor 2020. Competing interests: none. Funding: none.*

## Abstract

**What has not been tested and what fails.** The main measure, {pc(HO['purity'])} percent, applies to groups the method forms from stones with a *known* carver, {pc(N_U / AN['n_known'])} percent of them in Uppland, and the test was not locked. It does not say that the groups of stones without a carver are one hand. The grouping has not been tested against the runologists' judgements of which stones were made by the same hand, and against the literature's pairs it does only slightly better than neighbouring stones. Of the related methods tested against the runologists' judgements under locked plans, the carver model did not hold, and the text features recognised pairs but not groups.
**Background and aim.** Many runestones lack a carver, especially in Götaland. The report presents a method that groups them by the features of the hand and what its tests say.
**Material.** {num(AN['n_stones'], True)} Swedish Viking-Age runestones with at least five legible words in the Scandinavian Runic-text Database (Rundata): {AN['n_known']} with a secure carver and {AN['n_unattributed']} without.
**Method.** The stones are compared in spelling, word dividers, formulas, rune pairs, style and cross, but not in place and content, and stones as alike as a carver's stones are grouped. The method is tested on known carvers held out, and the groups against traits outside the similarity and against the literature's pairs.
**Results.** On known carvers a group was on average {pc(HO['purity'])} percent the group's most common carver, against {pc(HO['purity_geography'])} percent for as many nearby stones. Among the stones without a carver there were {len(G)} groups, {len(CAND)} of them without likeness to a known carver; they share rock type and unusual spellings more often than the district's stones. Of nine pairs that the literature ties to the same carver, six lay in the same group, against 4.8 expected for neighbours. In the locked tests against Runor 2020 the text features linked {pc(N1['mean_linked'])} percent of the runologists' pairs against {pc(N1['mean_control'])} for neighbours, but twelve of thirteen groups of unnamed hands were not gathered.
**Conclusion.** The method finds its way back to known carvers better than proximity does, where it can be tested. The groups of stones without a carver are writing milieus in the sense that the stones are written alike; whether a group is a carver, a workshop or a district's way of writing the tests do not decide.

## 1. Introduction

Runologists have long grouped unsigned stones by style, rune forms and spelling to find the carvers behind them (Axelson 1993; Stille 1999). Magnus Källström (2007) has spoken of writing milieus: districts where carvers and sponsors shared ways of writing. Laila Kitzler Åhfeldt (2002) has told carvers apart by their grooves. In Uppland most stones have a carver in Rundata, but in Götaland only a small part, and there the question is which hands lie behind the many stones without names.

The aim here is to present a method that groups stones without a carver by the features of the hand, to state exactly what its test measures, and how it and related methods have fared in tests against the literature and against the runologists' own judgements. A group gets a working name after the parish of its type stone; the name is a label for the stones, not a claim about a person.

## 2. Pre-registration: what was fixed in advance and what was not

**Not locked.** The method was built on 11 October 2026. The limits were chosen after the first validation on known carvers, which is therefore somewhat too optimistic. The test on carvers held out on 20 October, which gives the report's main measure, and the comparison with the literature's pairs on 29 October were not locked.

**Locked on 29 October 2026.** Two plans, both with a positive control on known carvers. The first tests the groups against rock type, height and personal names (SHA-256 `{SHA['2026-10-29-okanda-ristare-oberoende']}…`), the second against time span and unusual spellings, and estimates how likely it is that a group is one hand (SHA-256 `{SHA['2026-10-29-en-och-samma-mastare']}…`).

**Locked on 8 November 2026.** Four plans tested related methods against the runologists' judgements in Runor 2020: the carver model (`{SHA['2026-11-08-samma-hand-runor']}…`), the similarity in the text features (`{SHA['2026-11-08-textdrag-hand']}…`), a rule that links pairs (`{SHA['2026-11-08-nya-handerna']}…`) and dense cores of linked stones (`{SHA['2026-11-08-tata-karnor']}…`). None of them tests the grouping in this report, but all test the same question against judgements the methods have not seen.

**Not done.** The grouping has not been tested against the runologists' groups. A plan for an open carver model was locked on 19 November 2026 but has not been run and does not concern this grouping.

Only the tests under the locked plans are confirmatory; the main measure and the comparison with the literature are exploratory.

## 3. Material

- **The stones.** {num(AN['n_stones'], True)} Swedish Viking-Age runestones in the Scandinavian Runic-text Database (Rundata) with at least five legible words, in the version of the material of 7 November 2026. {AN['n_known']} have a secure carver and {AN['n_unattributed']} have none. Runestones only.
- **The known carvers.** {AN['coverage']['n_carvers']} carvers with at least three secure stones: 25 in Uppland, 8 in Södermanland, one in Östergötland and one in Västmanland. Of their {AN['n_known']} stones, {N_U} stand in Uppland, {N_SO} in Södermanland and {N_OTHER} in other provinces.
- **The coverage.** In Uppland {pc(SHARE['U'])} percent of the stones have a carver in Rundata, in Södermanland {pc(SHARE['Sö'])}, but in Östergötland {pc(SHARE['Ög'])}, Småland {pc(SHARE['Sm'])}, Västergötland {pc(SHARE['Vg'])} and Medelpad {pc(SHARE['M'])} percent.
- **The literature's pairs.** Nine pairs of stones that Sveriges runinskrifter for Östergötland and Västergötland (Brate 1911–18; Jungner & Svärdström 1940–70) ties to the same carver, where both stones lack a carver in Rundata and are in the analysis.
- **The runologists' groups.** The database Runor (Riksantikvarieämbetet 2020) has {SH['runor_notes']} notes of the form "same as made X", often for hands without a name; they give 14 to 18 groups depending on the test's conditions.

## 4. Method

**4.1 The similarity.** Gower distance (Gower 1971) between every pair of stones in the features of the hand: style group, cross, short-twig runes, language traits, word dividers, bind-runes, formulas and the most common rune pairs, but not place and content. The measure lies between 0 and 1 and combines different kinds of traits; 0 means alike in everything.

**4.2 The limit.** The limit for linking two stones is fixed on pairs of stones with a known carver within {CA['link_km']} km: pairs below the limit must be at least {CA['lr_min']} times more common among the same carver's pairs than among different carvers' (in the material {dec(CA['lr'], en=True)}). Of linked pairs with a known carver, {pc(CA['precision'])} percent are then the same carver.

**4.3 The groups.** Stones without a carver are linked when they lie within {CA['link_km']} km and below the limit, and the network is divided with the Louvain method (Blondel et al. 2008), which seeks groups with many links within and few between. A group is reported when it has at least four stones and is not more spread out than 90 percent of the known carvers ({round(CA['max_spread_km'])} km). A group that lies as close to a nearby known carver's stones as two stones by the same carver usually do counts as like that carver.

**4.4 The test on known carvers.** The same procedure is run on stones with a known carver, as if the carver were unknown. The measure is *purity*: the share of a group's stones that are by the group's most common carver, averaged with weights by group size. The comparison is as many stones nearest the group's type stone. In the test on carvers held out, the {AN['coverage']['n_carvers']} carvers are divided at random into three parts; the limits are derived on two and groups formed among the third part's stones, thirty times. A group among the stones without a carver is robust when at least {pc(AN['robust_min'])} percent of it recurs without the traits that depend on time.

**4.5 The tests against traits outside the similarity.** Rock type, height and personal names from Rundata, and unusual spellings of common words: for each group the share of pairs sharing the traits is compared with 9,999 random sets of stones from the same district ({OK['radius_km']} km) and with the same style groups, Holm-corrected over rock type, height and names. Positive control: {OK['control']['n_carvers']} known carvers. A logistic model, estimated on {MM['n_calibration']} groups that the method formed from known carvers' stones, gives the probability that at least three quarters of a group, or the whole group, is one hand.

**4.6 The literature's pairs.** For each pair it is counted whether both stones end up in the same group. This is compared with how often stones without a carver at the same distance from one stone of the pair end up in its group; the sum over the pairs is the number of pairs expected in the same group if the groups merely followed distance.

**4.7 The tests against the runologists' groups.** The four locked tests compare the runologists' groups with neighbouring stones at the same distance (± 25 percent, at least ± 1 km, 999 draws) with Wilcoxon's signed-rank test, one-sided, over the groups (Wilcoxon 1945). (a) *The carver model* chooses for each stone among the named carvers: do the stones in a group get the same suggestion? (b) *The text features* are similarity in character sequences, word dividers and bind-runes, weighted by how rare they are, and in the material's {TD['traits']} language traits and formulas, without place. (c) *The pair rule* links two stones when their similarity exceeds their mean similarity with stones at the same distance by a limit chosen on the named carvers. (d) *Dense cores* cluster the stones with average linkage (Sokal & Michener 1958) and cut where {pc(TK['precision_at_cstar']['precision'])} percent of the pairs of named carvers in the same core are the same carver.

**4.8 Deviations.** None from the two plans of 29 October. In two of the tests of 8 November an error was corrected before anything was interpreted (the notes in Runor were first read wrongly; groups without comparable neighbours were first counted). The grouping and the test have been recomputed on the material of 7 November 2026 with the same code; the independent tests and the comparison with the literature apply to the groups of 29 October, when the Konungsund group had {OLDG['Konungsunds']} stones instead of {CAND[0]['n']}.

## 5. Results

**5.1 The test on known carvers.** In the first validation, where the limits were chosen, a group was on average {pc(VA['purity'])} percent the group's most common carver, against {pc(VA['purity_geography'])} percent for as many nearby stones, and {pc(VA['share_pure'])} percent of the groups were at least three quarters one carver. With the limits derived on other carvers a group was {pc(HO['purity'])} percent the same carver, against {pc(HO['purity_geography'])} percent for nearby stones: a difference of {pc(HO['difference'])} percentage points (95 % interval {pc(HO['difference_ci'][0])}–{pc(HO['difference_ci'][1])}), in the groups' favour in all {HO['runs']} repetitions. Without the traits that depend on time: {pc(HN['purity'])} against {pc(HN['purity_geography'])} percent.

In plain words: when the method gets stones by known carvers, almost all in Uppland, and gathers them into groups without knowing who carved them, about six stones in seven in a group are by the same hand. Taking instead as many stones that stand closest together gives about seven in ten. That says how well the method finds its way back to known carvers, not that the groups of stones without a carver are one hand.

{chart(False)}

The test's stones are only stones by carvers with at least three secure stones, and proximity alone already gives {pc(HO['purity_geography'])} percent; what the method adds is the difference, {pc(HO['difference'])} percentage points.

**5.2 By province.** {pc(N_U / AN['n_known'])} percent of the test's stones stand in Uppland. Moved from Södermanland to Uppland the limit gave {pc(SU['renhet'])} against {pc(SU['geografi'])} percent, but in none of the {SU['körningar']} repetitions was the difference clear. From Uppland to Södermanland only one group per repetition was formed. In Östergötland, Småland, Västergötland and Medelpad, where the possible unknown hands are, only {N_OTHER} stones have a known carver, and there the method cannot be tested.

**5.3 The calibration.** The method gives no probability per group; the limit gives {pc(CA['precision'])} percent the same carver among linked pairs with a known carver, on the same material. The master model gives the probability that at least three quarters of a group is one hand, calibrated on groups in Uppland and Södermanland (ability to tell the groups apart, AUC, {dec(MM['validation']['pure_full']['auc'], 2, True)}): {mlist(False)}, against the base rate of {pc(DOM['base_rate'])}. That the Konungsund group is wholly one hand gets {MPURE['Konungsund']} percent, against the base rate of {pc(PURE['base_rate'])}. That cannot be tested where the groups lie.

**5.4 The groups among the stones without a carver.** There were {len(G)} groups. Of these, {len(KNOWN)} resemble a known carver nearby, {N_KNOWN_USO} of them in Uppland and Södermanland, and {len(CAND)} do not (number of stones in brackets): {cand_list(False)}. Five of them are robust without the time-dependent traits: {ROB_EN}.

**5.5 The tests against traits outside the similarity.** In the positive control, known carvers' stones share rock type, height and personal names more often than the district's stones (all p below 0.0001). For the five robust groups:

- **Rock type – holds**, Holm-corrected p = 0.002, carried by the Konungsund group ({pc(KON['rock']['obs'])} percent of the pairs share rock type against {pc(KON['rock']['null_mean'])} in the district) and the Kölaby group. But in the master model, mixed groups of known carvers shared rock type at least as often as pure ones (coefficient {dec(DOM['coef']['pct_rock'], en=True)}): rock type tells a group from the district's stones, not a hand from a mixed group.
- **Height – fails**, p = 0.32; only three groups have measurements.
- **Names – holds**, Holm-corrected p = 0.035, above all in the Kölaby group. But known carvers share names too, since they often made several stones for the same family, so shared names do not tell a carver from a family's commissions.
- **Unusual spellings – holds**, {pfmt(H5['H5']['p'], True)}, carried by Kölaby ({pfmt(SP['Kölaby']['p'], True)}) and Konungsund ({pfmt(SP['Konungsund']['p'], True)}).
- **Time.** The span between the group's oldest and youngest style group is {dec(P1['Konungsund']['span'], en=True)} years for Konungsund, Kölaby and Leksberg, which fits within a carver's working life. The Konungsund group covers {pc(P1['Konungsund']['coverage'])} percent of the district's contemporary stones, against a median of {pc(P1['_kända_ristare_U_Sö']['coverage_median'])} percent for the known carvers in Uppland and Södermanland.

**5.6 The literature's pairs.** Of the nine pairs, {SRI['same_group']} lay in the same group, against {dec(SRI['expected_from_neighbours'], en=True)} expected if the groups merely followed distance. The three pairs at Leksberg lie in the same group, but there all neighbours at the same distance end up in the group too. The Kölaby group holds Vg 181 and Vg 130, which are both signed, with two different and uncertainly read names: Hávarðr(?) and Tryggvi(?) (Jungner & Svärdström 1940–70 pp. 250 f., 296; Källström 2007 p. 350).

**5.7 The runologists' groups, tested on related methods.** None of the tests concerned this grouping.

- **The carver model – did not hold.** Within the runologists' {H1['groups']} groups where at least one stone lacks a secure carver, both stones in a pair got the same suggestion in {pc(H1['mean_obs'])} percent of the pairs, against {pc(H1['mean_ctrl'])} for neighbours at the same distance; better in {H1['better']} groups, worse in {H1['worse']}, {pfmt(H1['p'], True)}. U 1015 and U 1017–1024, which the runologists hold to be one hand without a name, all got the suggestion Öpir, and the neighbours got it in {pc(U1015['ctrl'])} percent of cases.
- **The text features – held.** The runologists' groups were more alike than the neighbours in {TD['T']['better']} of {TD['T']['groups']} groups ({pfmt(TD['T']['p'], True)}), also among the {TD['T']['unnamed_only']['groups']} groups with a hand without a name ({pfmt(TD['T']['unnamed_only']['p'], True)}).
- **The pair rule – held for pairs.** It linked {pc(N1['mean_linked'])} percent of the runologists' pairs against {pc(N1['mean_control'])} for neighbours, better in {N1['better']} of {N1['groups']} groups ({pfmt(N1['p'], True)}). But it also links {pc(TH['different_carver_linked'])} percent of the pairs by different named carvers, and when the links were allowed to form groups they chained together: the largest got {num(BIG['size'], True)} stones over {BIG['span_km']:.0f} km.
- **Dense cores – did not hold.** Of {len(UNN)} groups with a hand without a name, {sum(g['together'] == 0 for g in UNN)} did not have a single pair in the same core, and the thirteenth (U 1015–1024) one pair of 36 (p = {dec(C1['p'], 3, True)}). After the test: only {pc(PH['runor_share_at_cstar'])} percent of the runologists' {PH['runor_pairs']} pairs reach the limit for a core.

In plain words: the text features see that two stones are by the same hand more often than neighbouring stones are, but the difference is too small to gather the stones into the groups the runologists see.

## 6. Discussion

**What holds.** Where the method can be tested it finds its way back to known carvers better than proximity, and the groups differ from the district's stones in traits the grouping does not use.

**What is not shown.** That the groups of stones without a carver are hands; version 1 read the main measure that way, but the test did not measure that. Neither the literature's pairs nor the rock type speak for it, and the related tests against Runor 2020 point the same way without testing this particular grouping.

**Against earlier research.** The method does systematically what runologists do when they attribute by style and spelling (Axelson 1993; Stille 1999). The groups correspond to Källström's (2007) writing milieus in the sense that the stones in them are written alike; what they are beyond that the tests here do not decide.

**Weaknesses, in order of weight.**

1. **The grouping has not been tested against the runologists' groups.** The locked tests against Runor 2020 concerned other methods.
2. **Not tested where the groups are.** In Götaland and Medelpad there are almost no known carvers to test against, and the transfer between Södermanland and Uppland gave no clear result.
3. **The test's stones are only those of prolific carvers.** How the method works among stones where many hands may have carved only one or two stones has not been measured.
4. **The limits were chosen after the first validation, and the main test was not locked.**
5. **Rundata's attributions.** The known carvers on which the method is calibrated are themselves largely attributed by style and spelling.

**Where the method should not be used.** As attribution, for single stones outside a group or to call a group a person: a group is a hypothesis about a writing milieu.

**What would decide.** A locked test in which this grouping is set against the runologists' groups in Runor 2020 and against the literature's signed stones in Götaland, with neighbouring stones at the same distance as the comparison. Groove analyses (Kitzler Åhfeldt 2002) of the stones in a group would test the hand with evidence that does not come from the text.

## 7. Conclusion

Tested on known carvers, almost entirely in Uppland, the method finds its way back to the carvers better than proximity: {pc(HO['purity'])} against {pc(HO['purity_geography'])} percent. That its {len(CAND)} groups of stones without a carver, mainly in Götaland, are hands is not shown. The groups are suggestions of where examination and groove analyses can test a hand, not attributions.

## Data and code

The grouping and the test on known carvers were computed in Vitki {APP_VERSION}, an open research tool for runestones ([vitkirunor.se](https://vitkirunor.se/en)), on the material's version `{FP}` (computed on 7 November 2026). The code in `r/anonymous.R` is unchanged since 29 October 2026. All code, the analysis plans and the result files are openly available on [GitHub](https://github.com/Precatio/runes) under GPL-3.0.

- The grouping and the test: `r/anonymous.R` (results `anonymous.json` under the material's version `{FP}`); the test on carvers held out and the transfer between provinces `utdata/ristare/ristare_heldout.R` and `utdata/ristare/ristare_overforing.R` (commit `9a600d5`). Method description: `METHODS.md`, section 1g.
- The independent tests: the plans `analysplaner/2026-10-29-okanda-ristare-oberoende.md` and `analysplaner/2026-10-29-en-och-samma-mastare.md`; the code and results in `utdata/okanda_ristare/` (the material's version `3f58e9339191761e`). The literature's pairs: `utdata/okanda_ristare/sri_par.py` (commit `8945a74`).
- The tests against Runor 2020: `analysplaner/2026-11-08-samma-hand-runor.md` with `utdata/samma_hand/` (commit `285b204`), `analysplaner/2026-11-08-textdrag-hand.md` with `utdata/textdrag_hand/` (`5eeb691`), `analysplaner/2026-11-08-nya-handerna.md` with `utdata/nya_hander/` (`50aa732`) and `analysplaner/2026-11-08-tata-karnor.md` with `utdata/tata_karnor/` (`f852a80`).
- The report is built by `utdata/blogg/build/build_rapport_skrivmiljoer.py`, which reads every number from the result files and stops if anything disagrees. The template: `utdata/rapporter/MALL.md`, version 4. Version 1 is in commit `863e63d`.
- The methods report on the carver model: [Statistical carver suggestions from the runic texts]({RM_EN}). Popular account: [The carvers who were never remembered]({POP_EN}).

## References

- Axelson, J. 1993. *Mellansvenska runristare. Förteckning över signerade och attribuerade inskrifter*. Runrön 5. Uppsala: Department of Scandinavian Languages, Uppsala University.
- Blondel, V. D., Guillaume, J.-L., Lambiotte, R. & Lefebvre, E. 2008. Fast unfolding of communities in large networks. *Journal of Statistical Mechanics*, P10008.
- Brate, E. 1911–18. *Östergötlands runinskrifter* (Sveriges runinskrifter 2). Stockholm: KVHAA.
- Gower, J. C. 1971. A general coefficient of similarity and some of its properties. *Biometrics* 27 (4), pp. 857–871.
- Holm, S. 1979. A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics* 6 (2), pp. 65–70.
- Jungner, H. & Svärdström, E. 1940–70. *Västergötlands runinskrifter* (Sveriges runinskrifter 5). Stockholm: KVHAA.
- Kitzler Åhfeldt, L. 2002. *Work and Worship: Laser Scanner Analysis of Viking Age Rune Stones*. Theses and Papers in Scientific Archaeology B:9. Stockholm: Stockholm University.
- Kvant, V. 2026. *Vitki {APP_VERSION}: method description* (METHODS.md). https://github.com/Precatio/runes
- Källström, M. 2007. *Mästare och minnesmärken. Studier kring vikingatida runristare och skriftmiljöer i Norden*. Stockholm Studies in Scandinavian Philology, New Series 43. Stockholm: Stockholm University.
- Riksantikvarieämbetet. 2020. *Runor*. Runic inscriptions in Sweden, database. https://app.raa.se/open/runor
- Scandinavian Runic-text Database (Rundata). Department of Scandinavian Languages, Uppsala University. Open Database License.
- Sokal, R. R. & Michener, C. D. 1958. A statistical method for evaluating systematic relationships. *University of Kansas Science Bulletin* 38, pp. 1409–1438.
- Stille, P. 1999. *Runstenar och runristare i det vikingatida Fjädrundaland. En studie i attribuering*. Runrön 13. Uppsala: Department of Scandinavian Languages, Uppsala University.
- Wilcoxon, F. 1945. Individual comparisons by ranking methods. *Biometrics Bulletin* 1 (6), pp. 80–83.

:::box The essentials
- The method gathers runestones by how they are written, and on known carvers it finds its way back to the carver clearly better than proximity does.
- That is tested almost only in Uppland and on stones by known carvers, not on the groups of stones without a carver in Götaland.
- The groups without a carver are writing milieus: stones written alike. Whether a group is a carver, a workshop or a district the tests do not decide.
- The text features recognise that two stones are by the same hand, but do not suffice to gather the runologists' groups.
:::

{LOG_EN}
"""

# ---- formen ------------------------------------------------------------------------------------------------------
JARGON = r"modul\w*|trapp\w*|q_global|korpusjobb|fingeravtryck|fingerprint|facit|Vitkis|Vitki's|\bthe app\b|\bappen\b|`[^`]*/[^`]*`|METHODS"
for b in (body, body_en):
    assert not re.search(r"^\|", b, re.M), "BlogBody har inga tabeller"
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M)), "varje ruta ska stängas"
    assert "{" not in b and "}" not in b
    head = b.split("## Data")[0]
    assert not re.findall(JARGON, head), re.findall(JARGON, head)
    assert FP not in head and "3f58e93" not in head  # versionsnyckeln bara under Data och kod
    assert not re.search(r"\bAI\b", b)
    assert not re.search(r"\b(han|hans|honom|he|his|him)\b", b, re.I), re.findall(r"\b(han|hans|honom|he|his|him)\b", b, re.I)
    assert "](/" not in b, "relativa länkar når inte en läsare av pdf:en"
    assert "Theses and Papers in Scientific Archaeology B:9" in b
    assert b.rstrip().split("\n## ")[-1].startswith(("Ändringslogg", "Change log"))
    assert b.count("**Version ") == 2 and f"**Version 2, {TODAY}.**" in b and f"**Version 1, {V1_DATE}.**" in b
    # ingenstans före ändringsloggen påstås att grupperna utan ristare är en hand till 85 procent
    assert "en och samma hand" not in b.split("## Ändringslogg")[0] and "one and the same hand" not in b.split("## Change log")[0]
assert "Det viktigaste i korthet" in body and "## 2. Förregistrering" in body and "## 6. Diskussion" in body
assert "I klartext" in body and "In plain words" in body_en  # mallen version 4
assert "## Sammanfattning\n\n**Vad som inte är prövat och vad som faller.**" in body
assert "## Abstract\n\n**What has not been tested and what fails.**" in body_en
assert body.startswith(f"*Viktor Kvant, oberoende forskare. Metodrapport, delvis prövad. Rapportversion 2, {TODAY}; version 1 skrevs {V1_DATE} men publicerades inte. Tidslinje: ")
assert body_en.startswith(f"*Viktor Kvant, independent researcher. Methods report, partially tested. Report version 2, {TODAY}; version 1 was written {V1_DATE} but not published. Timeline: ")
assert "inte visat" in title and "not shown" in title_en and "86" in title and "71" in title
SEC = lambda b: [re.match(r"[\d.]*", h).group(0) for h in re.findall(r"^## (.+)$", b, re.M)]  # noqa: E731
assert SEC(body) == SEC(body_en), (SEC(body), SEC(body_en))
assert len(re.findall(r"^- ", body, re.M)) == len(re.findall(r"^- ", body_en, re.M))
assert len(re.findall(r"^\*\*\d\.\d", body, re.M)) == len(re.findall(r"^\*\*\d\.\d", body_en, re.M))
assert 1500 <= len(body.split("## Data")[0].split()) <= 3000  # mallen: metodrapport 1 500–3 000 ord
for a, b_ in (("I klartext", "In plain words"),):
    assert body.count(a) == body_en.count(b_)

out = {"slug": SLUG, "title": title, "summary": summary, "body": body, "title_en": title_en, "summary_en": summary_en,
       "body_en": body_en, "labels": ["Rapport", "Ristare"],
       "seo_title": "Skrivmiljöer utan namn: vad som håller", "seo_title_en": "Writing milieus without names: what holds"}
assert len(out["seo_title"]) <= 52 and len(out["seo_title_en"]) <= 52
assert blog_labels.check(out["labels"]) is None
path = os.path.join(ROOT, "utdata", "rapporter", "rapport_skrivmiljoer.json")
json.dump(out, open(path, "w"), ensure_ascii=False, indent=1)
print(path, len(body.split()), "ord,", len(body.split("## Data")[0].split()), "före Data och kod;", len(body_en.split()), "words,",
      len(body_en.split("## Data")[0].split()), "before Data and code")

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
                 "topic": "Rapport|skrivmiljoer", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
