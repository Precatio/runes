"""Forskningsrapport, metodrapport (låst mall utdata/rapporter/MALL.md, version 4; Metodrapport, delvis prövad):
"Skanningen som ledtråd: med 3D-spåren fyllde språkmodellen i 60 procent av de dolda orden rätt i stället för 54, i ett
prov där svaret inte var dolt för hela kedjan" (sv + en). Spårläsaren (utdata/sparlasare/, led E–G), känslighetskontrollen
utan Sö 113 (utan_so113.py) och kontrollen för rapportversion 3 (kontroll_v3.py, 2026-11-05: räknar i de sparade raderna
och läser koden vid provets commits). Alla siffror asserteras mot filerna.
    ../../../.venv/bin/python build_rapport_sparlasare.py [--write | --update DOC]"""
import datetime as dt
import glob
import json
import os
import re
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_labels  # noqa: E402
sys.path.insert(0, os.path.join(ROOT, "utdata", "rapporter", "figurer"))
from figur import FIG, andringslogg, bild  # noqa: E402

APP_VERSION = "3.0.0"  # the Vitki version the analysis was made in (tag v3.0.0 + the commits named in Data och kod), not the current one
assert open(os.path.join(ROOT, "utdata", "rapporter", "MALL.md.sha256")).read().startswith("611a4d5f")  # mallens version 4
REPORT_VERSION = 4  # version 1: 2026-10-31 (publicerad), version 2: 2026-11-01 (figur 1), version 3: rättelser,
# version 4 (2026-11-05): den andra granskningen av det version 3 ändrade
V1_DATE, V2_DATE = "2026-10-31", "2026-11-01"
TODAY = "2026-11-05"  # rapportversionens datum, fast i byggaren (mallen version 3)
TL_SV = ("spårläsaren byggdes och ställdes in på Sö 113 2026-10-17; en första körning på Sö 113 och Sö 134 gjordes "
         "2026-10-17; huvudprovet kördes 2026-10-17; provet på verkliga luckor kördes 2026-10-17; provet räknades om utan "
         "Sö 113 2026-10-31; de sparade raderna räknades om för rättelsen 2026-11-05")
TL_EN = ("the trace reader was built and tuned on Sö 113 2026-10-17; a first run on Sö 113 and Sö 134 was made 2026-10-17; "
         "the main test was run 2026-10-17; the test on real lacunae was run 2026-10-17; the test was recomputed without "
         "Sö 113 2026-10-31; the saved rows were recounted for the correction 2026-11-05")
SD = os.path.join(ROOT, "utdata", "sparlasare")
F = json.load(open(os.path.join(SD, "led_f_summering.json"), encoding="utf-8"))
X = json.load(open(os.path.join(SD, "utan_so113.json"), encoding="utf-8"))
E = json.load(open(os.path.join(SD, "led_e_perm.json"), encoding="utf-8"))
G = {s["sig"]: s for s in json.load(open(os.path.join(SD, "led_g.json"), encoding="utf-8"))}
K = json.load(open(os.path.join(SD, "kontroll_v3.json"), encoding="utf-8"))  # kontroll_v3.py, 2026-11-05
LEDF_SRC = open(os.path.join(SD, "led_f.py"), encoding="utf-8").read()
SUMM_SRC = open(os.path.join(SD, "led_f_summering.py"), encoding="utf-8").read()
C3 = ("utan", "skanner", "omflyttad")
d1 = lambda x: f"{100 * x:.1f}".replace(".", ",")  # noqa: E731
e1 = lambda x: f"{100 * x:.1f}"  # noqa: E731
d3 = lambda x: f"{x:.3f}".replace(".", ",")  # noqa: E731
fac = lambda x, en=False: f"{x:g}" if en else f"{x:g}".replace(".", ",")  # noqa: E731
MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November",
          "December")
en_date = lambda d: f"{int(d[8:])} {MONTHS[int(d[5:7]) - 1]} {d[:4]}"  # noqa: E731


def pexp(p, en=False):
    m, e = f"{p:.1e}".split("e")
    m = m if en else m.replace(".", ",")
    return f"p = {m} · 10{str(int(e)).translate(str.maketrans('-0123456789', '⁻⁰¹²³⁴⁵⁶⁷⁸⁹'))}"


def pf(p, en=False):
    if p < 0.001:
        return pexp(p, en)
    s = f"{p:.3f}" if p < 0.1 else f"{p:.2f}"
    return f"p = {s}" if en else f"p = {s.replace('.', ',')}"


def p2(p, en=False):
    """Two significant digits (p = 0,0088, p = 0,051)."""
    s = f"{p:.2g}"
    return f"p = {s}" if en else f"p = {s.replace('.', ',')}"


# ---- the main test (led F) --------------------------------------------------------------------------------------------
A = F["all"]
assert (A["n"], A["stones"], len(F["stones"])) == (157, 17, 17) and "Sö 113" in F["stones"]
MN = A["means"]
assert [d1(MN[c]["word_ok"]) for c in C3] == ["53,5", "59,9", "52,9"]
assert [f"{MN[c]['p_truth']:.3f}" for c in C3] == ["0.379", "0.414", "0.365"]
SU, SO, OU = A["skanner_vs_utan"], A["skanner_vs_omflyttad"], A["omflyttad_vs_utan"]
assert 3.7e-6 < SU["p"] < 3.8e-6 and 2.0e-8 < SO["p"] < 2.1e-8 and 0.0087 < OU["p"] < 0.0089 and OU["mean_diff"] < 0
assert p2(OU["p"]) == "p = 0,0088"
assert (SU["n_changed"], SU["n_plus"]) == (113, 74)
# the p-values are paired Wilcoxon tests on the probability of the right word only (led_f_summering.py)
assert 'd = [x[a]["p_truth"] - x[b]["p_truth"] for x in both]' in SUMM_SRC and "word_ok\"] - " not in SUMM_SRC
# the recomputation (same test) reproduces the summary exactly
XA, XU = X["alla"], X["utan_So_113"]
assert abs(XA["skanner_vs_utan"]["p"] - SU["p"]) < 1e-12 and XA["n"] == A["n"]
assert (XU["n"], XU["stones"]) == (145, 16)
assert [d1(XU["means"][c]["word_ok"]) for c in C3] == ["57,2", "63,4", "55,2"]
assert 5.8e-6 < XU["skanner_vs_utan"]["p"] < 6.0e-6 and XU["skanner_vs_omflyttad"]["p"] < 2e-8
# the words, counted in the saved rows (kontroll_v3.py)
KM = K["main"]
assert (KM["positions"], KM["n"], KM["stones"]) == (197, A["n"], A["stones"])
RW = KM["right_words"]
assert RW == {"utan": 84, "skanner": 94, "omflyttad": 83}
assert all(abs(RW[c] / KM["n"] - MN[c]["word_ok"]) < 1e-12 for c in C3)
assert KM["utan_to_skanner"] == {"wrong_to_right": 10, "right_to_wrong": 0}
assert KM["utan_to_omflyttad"] == {"wrong_to_right": 4, "right_to_wrong": 5} and RW["utan"] - RW["omflyttad"] == 1
# only the probability of the right word was saved, not the probability of the model's first choice: 5.3 not tested
assert KM["row_keys"] == ["p_truth", "right", "top", "traced", "word_ok"]

# ---- the pairing saw the answer (led_f.py at the test's commit, kontroll_v3.py) ------------------------------------------
LK = K["leak"]
assert LK == {"pairs_with_full_text": True, "masked_after_pairing": True, "free_when_in_set": True, "trace_eps": 0.2}
assert 'full = "".join(groups)\n        pos_sets, quality = scan_sets(signum, full)' in LEDF_SRC  # unchanged in the file
assert re.search(r"^TRACE_EPS = 0\.2$", LEDF_SRC, re.M) and "for _ in range(20):" in LEDF_SRC and "ok = z >= 2.0" in SUMM_SRC
TRACE_EPS_F = LK["trace_eps"]
# the code's own check of the pairing: reliable on Sö 134 only, where the right words did not change
assert F["reliable"] == K["pairing"]["reliable"] == ["Sö 134"] and K["pairing"]["stones"] == 17
R1 = F["reliable_only"]
assert (R1["n"], R1["stones"]) == (14, 1) and [d1(R1["means"][c]["word_ok"]) for c in C3] == ["71,4"] * 3
assert KM["so134"] == {"n": 14, "right_words": {"utan": 10, "skanner": 10, "omflyttad": 10},
                       "utan_to_skanner": {"wrong_to_right": 0, "right_to_wrong": 0}, "words_changing": 0}
RSU, RSO = R1["skanner_vs_utan"], R1["skanner_vs_omflyttad"]
assert p2(RSU["p"]) == "p = 0,051" and p2(RSO["p"]) == "p = 0,0012" and RSU["mean_diff"] > 0
# version 4: the plain-words meaning of p = 0,051 on Sö 134 (just above 0,05; the mean probability of the right word)
d2 = lambda x, en=False: f"{x:.2f}" if en else f"{x:.2f}".replace(".", ",")  # noqa: E731
assert 0.05 < RSU["p"] < 0.06 and (d2(R1["means"]["utan"]["p_truth"]), d2(R1["means"]["skanner"]["p_truth"])) == ("0,45", "0,50")
assert abs(R1["means"]["skanner"]["p_truth"] - R1["means"]["utan"]["p_truth"] - RSU["mean_diff"]) < 1e-9

# ---- the first run the same day (led_f.json, kontroll_v3.py) ----------------------------------------------------------
ER = K["earlier_run"]
assert (ER["words"], ER["stones"]) == (26, ["Sö 113", "Sö 134"])
assert ER["utan"]["any_differs"] == ER["skanner"]["any_differs"] == 0
EO = ER["omflyttad"]
assert (EO["top_differs"], EO["word_ok_differs"], EO["right_in_final_not_earlier"], EO["stones_differing"]) == (3, 2, 2, ["Sö 134"])

# ---- versions: the test's and Vitki's on the day of the correction (kontroll_v3.py) -----------------------------------
VT, VN, VS = K["versions"]["test"], K["versions"]["now"], K["versions"]["g7_switch"]
assert VT == {"commit_f": "a71c134", "commit_g": "f3b8f01", "date_f": "2026-10-17", "date_g": "2026-10-17",
              "method": "groove-5", "textmodel_f": "textmodel-17", "textmodel_g": "textmodel-17", "trace_eps_g": 0.05,
              "in_v3_0_0": True}
assert {k: v for k, v in VN.items() if k != "head"} == {"date": TODAY, "method": "groove-7", "textmodel": "textmodel-19",
                                                       "trace_eps": 0.05, "trace_reader_refs": "referenser_g7",
                                                       "traces_count_after_confirmation": True}
assert VS == {"commit": "add12ef", "date": "2026-11-03", "trace_reader_to_g7": True}
RD = K["rundata"]
assert RD["blob_at_f"] == RD["blob_now"] and RD["blob_now"].startswith("ee37aec") and RD["version_note"]
assert RD["last_change"] == "2026-10-04"
# version 4: the abstract names Rundata's version as the rest of the report does, from the file's own metadata
assert json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["meta"]["source"] == "Samnordisk runtextdatabas 2014 (RUNDATA.xls uppdaterad 2018)"
# the check and the builder of version 3 are in commit 6eae0af
assert subprocess.run(["git", "log", "-1", "--format=%ad", "--date=short", "6eae0af"], cwd=ROOT, capture_output=True, text=True,
                      check=True).stdout.strip() == TODAY
assert {"utdata/sparlasare/kontroll_v3.py", "utdata/blogg/build/build_rapport_sparlasare.py"} <= set(subprocess.run(
    ["git", "show", "--name-only", "--format=", "6eae0af"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split("\n"))
# the glossary the report links to (mallen version 4)
assert all(os.path.exists(os.path.join(ROOT, "web", "src", "app", *p, "forskningsrapporter", "begrepp", "page.tsx")) for p in ((), ("en",)))

# ---- the earlier step on undamaged runes (led E) ----------------------------------------------------------------------
assert (E["n_shuffles"], E["p_value"], E["p_value_top1"]) == (200, 0.01, 0.015)
assert (f"{E['pooled_mean_p']:.3f}", f"{E['pooled_null'][0]:.3f}", d1(E["pooled_top1"]), d1(E["pooled_top1_null"][0])) == ("0.077", "0.066", "19,3", "13,8")

# ---- real gaps end to end (led G) -------------------------------------------------------------------------------------
assert len(G) == 5 and set(G) == {"Sö 162", "Sö 206", "Sö 211", "Sö 360", "Sö 45"}
assert (G["Sö 162"]["utan"][0]["word"], G["Sö 162"]["skanner"][0]["word"], G["Sö 162"]["utan"][0]["rundata"]) == ("stæin", "staf", "st[æin]")
assert G["Sö 162"]["skanner"][0]["agrees"] is True  # the code's rule counts staf as stæin
assert (G["Sö 206"]["utan"][1]["word"], G["Sö 206"]["skanner"][1]["word"], G["Sö 206"]["utan"][1]["rundata"]) == ("karl", "kumbl", "G[uðl]aug")
assert G["Sö 206"]["utan"][1]["agrees"] is False and G["Sö 206"]["skanner"][1]["agrees"] is False
assert G["Sö 211"]["skanner"][0]["word"] == "stæin" and G["Sö 45"]["skanner"][0]["word"] == "gæiRfastr"
S360U, S360S = G["Sö 360"]["utan"][1], G["Sö 360"]["skanner"][1]
assert (S360U["word"], S360S["word"], S360U["rundata"]) == ("farinn", "farinn", "<far-nki>")
assert (f"{S360U['p']:.2f}", f"{S360S['p']:.2f}") == ("0.82", "0.27")
P360_SV = [f"{x['p']:.2f}".replace(".", ",") for x in (S360U, S360S)]
P360_EN = [f"{x['p']:.2f}" for x in (S360U, S360S)]
N_GAP_WORDS = sum(len(s["utan"]) for s in G.values())
KG = K["real_gaps"]
assert N_GAP_WORDS == KG["words"] == 7
assert (KG["utan"]["code_agrees"], KG["utan"]["agrees"], KG["skanner"]["code_agrees"], KG["skanner"]["agrees"]) == (3, 3, 3, 2)
GU, GS = KG["utan"]["agrees"], KG["skanner"]["agrees"]

SLUG = "skanningen-som-ledtrad"
TOP_S, TOP_U = round(100 * MN["skanner"]["word_ok"]), round(100 * MN["utan"]["word_ok"])
assert (TOP_S, TOP_U) == (60, 54)
title = (f"Skanningen som ledtråd: med 3D-spåren fyllde språkmodellen i {TOP_S} procent av de dolda orden rätt i stället "
         f"för {TOP_U}, i ett prov där svaret inte var dolt för hela kedjan")
title_en = (f"The scan as a clue: with the 3D traces the language model filled in {TOP_S} percent of the hidden words "
            f"correctly instead of {TOP_U}, in a test where the answer was not hidden from the whole chain")
summary = (f"Metodrapport. En spårläsare läser i en 3D-skanning vilka runor en skadad runa kan vara, och en språkmodell "
           f"väljer bland dem. När hela ord doldes på {A['stones']} skannade runstenar blev {d1(MN['skanner']['word_ok'])} "
           f"procent rätt med spåren mot {d1(MN['utan']['word_ok'])} procent utan dem, och med spåren omflyttade försvann "
           "vinsten. Men svaret var inte dolt för hela kedjan: skanningens runor parades mot texten med det dolda ordet "
           "synligt, och på den enda sten där parningen var säkrare än slumpen ändrades inte andelen rätt ord. Provet gäller "
           "äldre versioner av mätmetoden och språkmodellen än dem Vitki använde när rapporten rättades i november 2026.")
summary_en = (f"Methods report. A trace reader reads from a 3D scan which runes a damaged rune can be, and a language model "
              f"chooses among them. When whole words were hidden on {A['stones']} scanned runestones, "
              f"{e1(MN['skanner']['word_ok'])} percent came out right with the traces against {e1(MN['utan']['word_ok'])} "
              "percent without them, and with the traces shuffled the gain vanished. But the answer was not hidden from the "
              "whole chain: the scan's runes were paired with the text with the hidden word visible, and on the only stone "
              "where the pairing beat chance the share of right words did not change. The test concerns older versions of "
              "the measurement method and the language model than those Vitki used when the report was corrected in "
              "November 2026.")
CITE_EN = (f"Kvant, V. ({TODAY[:4]}). {title_en}. Research report (methods report), report version {REPORT_VERSION}; analysis in "
           f"Vitki {APP_VERSION}. https://vitkirunor.se/en/forskningsrapporter/{SLUG}")

# the abstract's first sentences (mallen: nivå 2 säger först vad som inte är prövat, och att provet gäller en äldre version)
FIRST_SV = (f"Svaret var inte dolt för hela kedjan: skanningens runor parades mot textens platser med hela den kända texten, "
            f"också det dolda ordet, och parningen var säkrare än slumpen bara på {F['reliable'][0]}, där andelen rätt ord "
            f"inte ändrades. Provet gäller mätmetoden {VT['method']} och språkmodellen {VT['textmodel_f']}; Vitki använder "
            f"i dag ({TODAY}) {VN['method']} och {VN['textmodel']}, som inte är prövade på samma sätt.")
FIRST_EN = (f"The answer was not hidden from the whole chain: the scan's runes were paired with text positions using the "
            f"full known text, the hidden word included, and the pairing beat chance only on {F['reliable'][0]}, where the "
            f"share of right words did not change. The test concerns the {VT['method']} measurement method and the "
            f"{VT['textmodel_f']} language model; Vitki now ({en_date(TODAY)}) uses {VN['method']} and {VN['textmodel']}, "
            "which have not been tested in the same way.")


def chart(sv):
    f = d1 if sv else e1
    lab = (("Utan spår", "Med skanningens spår", "Spåren omflyttade") if sv else ("Without traces", "With the scan's traces", "Traces shuffled"))
    rows = [":::chart Dolda ord som fylldes i rätt, procent" if sv else ":::chart Hidden words filled in correctly, percent"]
    for g_sv, g_en, mm, n in (("Alla 17 stenar", "All 17 stones", MN, A["n"]), ("Utan Sö 113", "Without Sö 113", XU["means"], XU["n"])):
        rows.append(f"# {g_sv if sv else g_en}")
        for c, lb in zip(C3, lab):
            rows.append(f"{'+' if c == 'skanner' else ''}{lb} | {f(mm[c]['word_ok'])} | {n} {'ord' if sv else 'words'}")
    # the caption line must start with Källa:/Source: (components/BlogBody.tsx), the credit follows it
    rows += ["Källa: Rundata (ODbL); skanningar av Laila Kitzler Åhfeldt, Riksantikvarieämbetet (CC BY 4.0). Diagram: Vitki, efter Rundata och Kitzler Åhfeldts skanningar." if sv else
             "Source: Rundata (ODbL); scans by Laila Kitzler Åhfeldt, Swedish National Heritage Board (CC BY 4.0). Chart: Vitki, after Rundata and Kitzler Åhfeldt's scans.", ":::"]
    return "\n".join(rows)


SP, SC = FIG["spar"], FIG["spar_counts"]
assert SC == {"n": 157, "wrong_to_right": 10, "right_to_wrong": 0} and SC["wrong_to_right"] == KM["utan_to_skanner"]["wrong_to_right"]
assert (SP["gain"]["sig"], SP["loss"]["sig"], SP["loss"]["truth_allowed"]) == ("Sö 112", "Sö 319", [False, True, False])
FIG_SV = bild("spar", "sv", f"Figur 1. Vad spåren säger om ett dolt ord. Rutorna visar för varje runa vilka av runradens 16 runor som ingår i skanningens uppsättning (mörka) och vilka som ligger utanför den (ljusa); rätt runa har en ring. Bilden kallar de ljusa runorna uteslutna, men i modellen blir de bara mindre sannolika: i provet vägde varje sådan runa ned ett förslag med faktorn {fac(TRACE_EPS_F)}. Till vänster ordet där spåren hjälpte mest (Sö 112), till höger ordet där de sänkte sannolikheten för rätt svar mest (Sö 319), där rätt runa ligger utanför uppsättningen på två av tre platser. I inget av de 157 orden gjorde spåren ett rätt ord fel; i 10 gjorde de ett fel ord rätt. Illustration: Vitki, ur Laila Kitzler Åhfeldts 3D-skanningar (Riksantikvarieämbetet, projektet Runristandets dynamik; Zenodo, CC BY 4.0) och Rundata.")
FIG_EN = bild("spar", "en", f"Figure 1. What the traces say about a hidden word. For each rune the boxes show which of the 16 runes of the futhark are in the scan's set (dark) and which are outside it (light); the right rune is circled. The image calls the light runes ruled out, but in the model they only become less probable: in the test each such rune weighed a suggestion down by a factor of {fac(TRACE_EPS_F, True)}. Left, the word where the traces helped most (Sö 112); right, the word where they lowered the probability of the right answer most (Sö 319), where the right rune is outside the set in two of three places. In none of the 157 words did the traces make a right word wrong; in 10 they made a wrong word right. Illustration: Vitki, from Laila Kitzler Åhfeldt's 3D scans (Swedish National Heritage Board, project Runristandets dynamik; Zenodo, CC BY 4.0) and Rundata.")

V2_SV = "Figur 1 tillagd: vad spåren säger om ett dolt ord, i två exempel valda efter en regel som anges i bildtexten."
V2_EN = "Figure 1 added: what the traces say about a hidden word, in two examples chosen by a rule given in the caption."
V3_SV = ("- **Version 3, 2026-11-05.** Rättelser efter en granskning inför arkiveringen i Zenodo; inga resultatfiler från provet är "
         "ändrade och inget är omkört. Sammanfattningen börjar nu med att svaret inte var dolt för hela kedjan (parningen av "
         "skanningens runor mot texten såg det dolda ordet, och den var säkrare än slumpen bara på Sö 134, där andelen rätt "
         f"ord inte ändrades) och att provet gäller {VT['method']} och {VT['textmodel_f']}, inte de versioner Vitki använder; "
         "titeln, metoden, avvikelserna, resultaten, diskussionen, slutsatsen och korthetsrutan säger samma sak. Data och kod "
         "anger provets commits och versioner: meningen om ändringar fram till den 31 oktober var fel, eftersom omräkningen "
         "bara räknade om sparade rader, och meningen om en kommande release är ersatt med kodläget. p-värdena gällde "
         "sannolikheten för rätt ord men stod vid andelen rätt ord; med omflyttade spår blev ett ord färre rätt än utan spår "
         f"({RW['omflyttad']} mot {RW['utan']} av {KM['n']}), så sämre än inga spår gäller bara sannolikheten. Provet kördes "
         "inte en gång: den första körningen redovisas nu. Verkliga luckor: på Sö 206 är både karl och kumbl fel, och staf på "
         f"Sö 162 stämmer inte med stæin; {GU} av {N_GAP_WORDS} förslag stämde med Rundata utan spår och {GS} av "
         f"{N_GAP_WORDS} med spåren. Avsnitt 5.3 Kalibreringen (inte prövad) är tillagt och de följande avsnitten "
         "omnumrerade; det skarpa provet heter nu huvudprovet; figurtexten säger att runor utanför skanningens uppsättning "
         "blir mindre sannolika, inte uteslutna; en referens som inte citerades är borttagen; diagrammet anger Vitki som "
         "upphov; ordlistan länkas. De nya talen räknades i de sparade raderna med ett nytt kontrollskript.")
V3_EN = ("- **Version 3, 2026-11-05.** Corrections after a review before archiving in Zenodo; no result file of the test has "
         "changed and nothing has been rerun. The abstract now begins by saying that the answer was not hidden from the "
         "whole chain (the pairing of the scan's runes with the text saw the hidden word, and it beat chance only on Sö 134, "
         f"where the share of right words did not change) and that the test concerns {VT['method']} and "
         f"{VT['textmodel_f']}, not the versions Vitki uses; the title, the method, the deviations, the results, the "
         "discussion, the conclusion and the essentials box say the same. Data and code give the test's commits and "
         "versions: the sentence about changes up to 31 October was wrong, since the recomputation only re-aggregated "
         "saved rows, and the sentence about a future release has been replaced by the code state. The p-values concerned "
         "the probability of the right word but stood next to the share of right words; with shuffled traces one word fewer "
         f"came out right than without traces ({RW['omflyttad']} against {RW['utan']} of {KM['n']}), so worse than no "
         "traces holds only for the probability. The test was not run once: the first run is now reported. Real lacunae: "
         "on Sö 206 both karl and kumbl are wrong, and staf on Sö 162 does not agree with stæin; "
         f"{GU} of {N_GAP_WORDS} suggestions agreed with Rundata without traces and {GS} of {N_GAP_WORDS} with them. "
         "Section 5.3 Calibration (not tested) has been added and the following sections renumbered; the sharp test is now "
         "called the main test; the figure caption says that runes outside the scan's set become less probable, not ruled "
         "out; a reference that was not cited has been removed; the chart credits Vitki; the glossary is linked. The new "
         "numbers were counted in the saved rows with a new check script.")
V4_SV = (f"- **Version {REPORT_VERSION}, {TODAY}.** En andra granskning inför arkiveringen i Zenodo gick igenom det som version 3 "
         "ändrade; inga resultatfiler är ändrade och inget är omkört. I 5.1 står nu att en del av vinsten, eller hela, kan komma "
         "från parningen; version 3 skrev bara en del, fast provet inte kan visa att någon del kommer från skanningen. I 5.2 har "
         f"{p2(RSU['p'])} på {F['reliable'][0]} fått en förklaring i klartext, med medelsannolikheterna "
         f"{d2(R1['means']['utan']['p_truth'])} och {d2(R1['means']['skanner']['p_truth'])}. Sammanfattningen anger Rundatas "
         "version på samma sätt som resten av rapporten (version 2014 med RUNDATA.xls uppdaterad 2018); version 3 angav där en "
         "annan versionsbeteckning. Ändringsloggen har fått raden för version 1, och Data och kod anger commit för kontrollen och "
         "byggskriptet för version 3 (6eae0af). Ändringar som version 3 gjorde men inte skrev in i loggen: Rundatas version "
         "angavs i materialet, i Data och kod och bland referenserna; 5.4 säger inte längre att spåren säger mer tillsammans med "
         "språket; diskussionen säger inte längre att skanningarna visar sig vara en källa för läsningen, bara att de kan bli "
         "det; och diskussionen och Data och kod säger att spåren i Vitki räknas först när användaren har bekräftat dem, så som "
         "Vitki var byggt när version 3 skrevs.")
V4_EN = (f"- **Version {REPORT_VERSION}, {TODAY}.** A second review before archiving in Zenodo checked what version 3 changed; "
         "no result file has changed and nothing has been rerun. 5.1 now says that some or all of the gain may come from the "
         "pairing; version 3 said part of it, although the test cannot show that any part comes from the scan. In 5.2, "
         f"{p2(RSU['p'], True)} on {F['reliable'][0]} is explained in plain words, with the mean probabilities "
         f"{d2(R1['means']['utan']['p_truth'], True)} and {d2(R1['means']['skanner']['p_truth'], True)}. The abstract gives "
         "Rundata's version in the same way as the rest of the report (2014 version with RUNDATA.xls updated 2018); version 3 "
         "gave a different version designation there. The change log has the line for version 1, and Data and code gives the "
         "commit of the check and the builder of version 3 (6eae0af). Changes that version 3 made but did not log: Rundata's "
         "version was given in the material, in Data and code and in the references; 5.4 no longer says that the traces say "
         "more together with the language; the discussion no longer says that the scans turn out to be a source for reading, "
         "only that they may become one; and the discussion and Data and code say that the traces count in Vitki only once the "
         "user has confirmed them, as Vitki was built when version 3 was written.")
V1_SV, V1_EN = f"- **Version 1, {V1_DATE}.** Första publicerade versionen.\n", f"- **Version 1, {V1_DATE}.** First published version.\n"
LOG_SV = andringslogg("sv", 2, V2_DATE, V2_SV, V2_EN).replace("## Ändringslogg\n\n", "## Ändringslogg\n\n" + V1_SV, 1) + "\n" + V3_SV + "\n" + V4_SV
LOG_EN = andringslogg("en", 2, V2_DATE, V2_SV, V2_EN).replace("## Change log\n\n", "## Change log\n\n" + V1_EN, 1) + "\n" + V3_EN + "\n" + V4_EN
assert LOG_SV.count("- **Version ") == LOG_EN.count("- **Version ") == 4

body = f"""*Viktor Kvant, oberoende forskare. Metodrapport, delvis prövad. Rapportversion {REPORT_VERSION}, {TODAY} (version 1 publicerad {V1_DATE}, version 2 {V2_DATE}). Tidslinje: {TL_SV}. Analysen är gjord i Vitki {APP_VERSION}; provet kördes {VT['date_f']} med kod som ingår i den versionen (se Data och kod). Licens CC BY 4.0. Den engelska versionen är den kanoniska för citering: {CITE_EN}. Nyckelord: runstenar, vikingatid, 3D-skanning, skadade runor, språkmodell, luckor, rekonstruktion, Södermanland. Konkurrerande intressen: inga. Finansiering: ingen.*

## Sammanfattning

**Vad som inte är prövat.** {FIRST_SV} Provet var inte heller låst i en plan, och spårläsarens inställningar togs fram på en av stenarna i provet. Provet döljer hela ord på hela runor; vid verkliga skador har spåren bara prövats på fem stenar, och där stämde färre förslag med utgivarnas läsning med spåren än utan dem.
**Bakgrund och syfte.** När runor är skadade läser runologen vad som finns kvar på stenen, och en språkmodell kan föreslå vad som stod där. Frågan här är om det som en 3D-skanning visar av de skadade runorna gör språkmodellens förslag bättre.
**Material.** 17 runstenar i Södermanland som Laila Kitzler Åhfeldt har skannat i 3D och publicerat öppet, med texten i Samnordisk runtextdatabas (Rundata, version 2014 med RUNDATA.xls uppdaterad 2018); {A['n']} ord som gick att pröva.
**Metod.** En spårläsare läser i skanningens djupbild vilka av de sexton runorna varje upptäckt runa kan vara, med en sannolikhet för var och en. Skanningens runor paras mot textens platser. Varje helt ord på två till sex runor döljs, och en språkmodell som är tränad utan stenen fyller i det: utan spår, med spåren och med samma spår slumpvis omflyttade mellan stenens platser. Jämförelsen är parad, ord för ord.
**Resultat.** Med spåren blev {d1(MN['skanner']['word_ok'])} procent av orden rätt, mot {d1(MN['utan']['word_ok'])} procent utan dem ({KM['utan_to_skanner']['wrong_to_right']} ord blev rätt med spåren och inget blev fel; sannolikheten för rätt ord steg, {pexp(SU['p'])}). Med omflyttade spår försvann vinsten och sannolikheten sjönk ({p2(OU['p'])}). Utan stenen där inställningarna togs fram: {d1(XU['means']['skanner']['word_ok'])} mot {d1(XU['means']['utan']['word_ok'])} procent. På Sö 134, den enda sten där parningen var säkrare än slumpen, blev {d1(R1['means']['utan']['word_ok'])} procent av de {R1['n']} orden rätt i alla tre villkoren. På fem stenar med verkliga luckor stämde {GU} av {N_GAP_WORDS} förslag med utgivarnas läsning i Rundata utan spår och {GS} av {N_GAP_WORDS} med spåren.
**Slutsats.** Spåren höjde sannolikheten för rätt ord i provet, men eftersom parningen såg svaret går det inte att skilja det skanningen läser från det parningen redan visste, och på den enda säkert parade stenen ändrades inte andelen rätt ord. Metoden behöver prövas på nytt med svaret dolt för hela kedjan och med de versioner Vitki använder. Vid svåra skador ska spåren visas för den som läser och vägas in först när den har bekräftat dem.

## 1. Inledning

Många runinskrifter har skadade eller förlorade runor. Runologen läser det som finns kvar på stenen, och utgåvorna anger säkra, osäkra och förlorade runor. På senare år har språkmodeller använts för att föreslå vad som stått i skadade inskrifter; den mest kända är Ithaca för grekiska inskrifter (Assael m.fl. 2022). Laila Kitzler Åhfeldt har skannat ett stort antal runstenar i 3D för att studera huggtekniken (Kitzler Åhfeldt 2002; 2015) och publicerat skanningarna öppet (Kitzler Åhfeldt 2024).

Det som saknas är ett sätt att låta det som skanningen visar av en skadad runa styra vad en språkmodell föreslår, och ett prov på om det hjälper. Syftet här är att redovisa en spårläsare som gör det och att pröva den på dolda ord på skannade stenar.

## 2. Förregistrering: vad som var bestämt i förväg och vad som inte var det

Provet var inte låst i en plan. Spårläsaren byggdes i steg den 17 oktober 2026. Dess två inställningar, hur skarpt sannolikheterna fördelas och vad en extra del av en runa kostar, prövades fram på Sö 113 ensam och validerades sedan på Sö 134 och Sö 207, som inte hade använts. Huvudprovet bestämdes därefter i koden, med tre villkor och samma mått för alla stenar. En första körning samma dag på Sö 113 och Sö 134 ({ER['words']} ord) gav samma resultat utan spår och med spåren, men med omflyttade spår blev förslaget ett annat för {EO['top_differs']} av de {ER['words']} orden, alla på Sö 134, eftersom omflyttningen slumpades annorlunda när de två stenarna kördes tillsammans; {EO['right_in_final_not_earlier']} av dem blev rätt i den slutliga körningen men var fel i den första. Den slutliga körningen gjordes sten för sten på alla 17 stenar, och det är den som redovisas. Sö 113 ingår bland de 17 stenarna; den 31 oktober räknades provet om utan Sö 113, med samma test på de sparade raderna. Provet på verkliga luckor kördes samma dag som huvudprovet.

## 3. Material

- **Skanningarna.** Laila Kitzler Åhfeldt, Riksantikvarieämbetet, skannade runstenarna i Södermanland med en ATOS-skanner i projektet Runristandets dynamik och publicerade dem på Zenodo under CC BY 4.0 (Kitzler Åhfeldt 2024). Av dem användes de {A['stones']} stenar där Rundata har en ordtext som kan paras mot de upptäckta runorna. Bara runstenar.
- **Texterna.** Translitterering och normalisering ur Samnordisk runtextdatabas (Rundata), version 2014 med RUNDATA.xls uppdaterad 2018.
- **Orden.** Varje helt ord på två till sex runor: {KM['positions']} ordplatser, varav {A['n']} där alla tre villkoren gav ett resultat.
- **Verkliga luckor.** Fem stenar ur samma serie med luckor som Rundata markerar: {', '.join(sorted(G))}.

## 4. Metod

**4.1 Spårläsaren.** I skanningens djupbild hittas runornas stavar. Delar av huggspåret utanför stavarna, kvistar och bågar, får en vikt efter hur djupa, långsträckta och långa de är, eftersom vittring och märken i ytan ger grunda och korta spår. Varje upptäckt runa jämförs med formen för var och en av de sexton runorna, med en kostnad för delar som saknas eller är för många, och kostnaderna görs om till en sannolikhet per runa. Huggspåren mättes med den version av mätmetoden som gällde den 17 oktober 2026 ({VT['method']}); Vitki har sedan gått över till en senare version ({VN['method']}), som inte är prövad på det här sättet.

**4.2 Språkmodellen.** Projektets modell för runtext, i den version som gällde den 17 oktober 2026 ({VT['textmodel_f']}), föreslår ord och väger dem efter hur vanliga de är i runtexterna och i sitt sammanhang. Den är tränad utan stenen som prövas. Spåren läggs in mjukt: en runa som skanningen inte stöder blir mindre sannolik, inte omöjlig. I huvudprovet vägdes varje sådan runa ned med faktorn {fac(TRACE_EPS_F)}, i provet på verkliga luckor med {fac(VT['trace_eps_g'])}, som Vitki också använder.

**4.3 Provet.** Varje helt ord på två till sex runor döljs och fylls i under tre villkor: utan spår, med spårläsarens sannolikheter för ordets runor, och med samma uppsättningar slumpvis omflyttade mellan stenens platser. Det sista villkoret skulle pröva om spåren hjälper för att de läser stenen, eller bara för att de minskar antalet möjliga runor. Måtten är andelen ord som blev rätt och sannolikheten för det rätta ordet; sannolikheten jämförs ord för ord med Wilcoxons test för parade värden, andelen rätt ord redovisas utan test. För att veta vilken upptäckt runa som hör till vilken plats i texten parades skanningens runor mot textens runor, en gång per sten och med hela den kända texten, innan något ord doldes (se 4.4). Parningen prövades mot samma parning med texten omkastad 20 gånger och räknades som säker när andelen parade runor vars textruna fanns bland dem skanningen stöder låg minst två standardavvikelser över den omkastade textens.

**4.4 Avvikelser och fel.** Ingen plan fanns, så inga avvikelser från en plan kan redovisas. Tre saker redovisades inte i rapportens första två versioner: att parningen såg det dolda ordet, att kodens egen kontroll fann parningen säker bara på en sten, och att provet kördes mer än en gång. Parningen av skanningens runor mot texten använde hela den kända texten, också det ord som sedan doldes, och den kostar ingenting där textens runa finns bland dem skanningen stöder; den kan därför dra skanningens uppsättningar till de platser där de stämmer med svaret. Det kan gynna villkoret med spår, och kontrollen med omflyttade spår skiljer inte den fördelen från spårens egen läsning, eftersom båda försvinner när uppsättningarna flyttas. Kodens egen kontroll fann parningen säker bara på Sö 134 (1 av {K['pairing']['stones']} stenar). Felet är inte rättat och provet är inte omkört. Den första körningen redovisas i 2. Omräkningen utan Sö 113 gjordes efter provet.

## 5. Resultat

**5.1 Huvudprovet.** {A['n']} ord på {A['stones']} stenar. Rätt ord: {d1(MN['utan']['word_ok'])} procent utan spår ({RW['utan']} ord), {d1(MN['skanner']['word_ok'])} procent med spåren ({RW['skanner']}) och {d1(MN['omflyttad']['word_ok'])} procent med spåren omflyttade ({RW['omflyttad']}). Med spåren blev {KM['utan_to_skanner']['wrong_to_right']} ord rätt som var fel utan dem, och inget ord som var rätt blev fel; med omflyttade spår blev {KM['utan_to_omflyttad']['wrong_to_right']} ord rätt och {KM['utan_to_omflyttad']['right_to_wrong']} fel. Sannolikheten för det rätta ordet: {d3(MN['utan']['p_truth'])} utan, {d3(MN['skanner']['p_truth'])} med och {d3(MN['omflyttad']['p_truth'])} med omflyttade spår. Spåren gav högre sannolikhet än inga spår, {pexp(SU['p'])}, och högre än omflyttade spår, {pexp(SO['p'])}. Omflyttade spår gav lägre sannolikhet än inga spår, {p2(OU['p'])}; i andelen rätt ord var skillnaden ett ord av {A['n']}. Alla p-värden gäller sannolikheten för det rätta ordet, inte andelen rätt ord. I klartext: med skanningens spår blev ungefär sex dolda ord av tio rätt i stället för drygt fem; {KM['utan_to_skanner']['wrong_to_right']} ord blev rätt och inget blev fel. När spåren kastades om försvann vinsten. Men parningen mellan skanning och text såg svaret (4.4), så en del av vinsten, eller hela, kan komma från parningen och inte från skanningen.

{chart(True)}

{FIG_SV}

**5.2 Utan Sö 113, och den enda säkert parade stenen.** Utan stenen där inställningarna togs fram: {XU['n']} ord på {XU['stones']} stenar, {d1(XU['means']['utan']['word_ok'])} procent rätt utan spår, {d1(XU['means']['skanner']['word_ok'])} med och {d1(XU['means']['omflyttad']['word_ok'])} med omflyttade; sannolikheten för rätt ord med spåren mot inga spår {pexp(XU['skanner_vs_utan']['p'])}, mot omflyttade {pexp(XU['skanner_vs_omflyttad']['p'])}. Bara på Sö 134 var parningen säkrare än slumpen. Där blev {d1(R1['means']['utan']['word_ok'])} procent av de {R1['n']} orden rätt i alla tre villkoren, och inget ord ändrades; sannolikheten för rätt ord steg med spåren (i medel från {d2(R1['means']['utan']['p_truth'])} till {d2(R1['means']['skanner']['p_truth'])}), {p2(RSU['p'])} mot inga spår, strax över den vanliga gränsen 0,05 och med {R1['n']} ord ett svagt tecken, och {p2(RSO['p'])} mot omflyttade.

**5.3 Kalibreringen.** Inte prövad. Provet sparade sannolikheten för det rätta ordet men inte för modellens förstaval, så det går inte att se om modellens sannolikheter stämmer med hur ofta förslagen blev rätt. De {N_GAP_WORDS} orden i verkliga luckor är för få för en sådan prövning.

**5.4 Det tidigare steget, på oskadade runor.** Innan språkmodellen kopplades in prövades spårläsaren ensam på de upptäckta runorna på Sö 113, Sö 134 och Sö 207: sannolikheten för den rätta runan var i medel {d3(E['pooled_mean_p'])} mot {d3(E['pooled_null'][0])} när texten blandades om ({E['n_shuffles']} omblandningar, {pf(E['p_value'])}), och den rätta runan kom först i {d1(E['pooled_top1'])} procent mot {d1(E['pooled_top1_null'][0])} ({pf(E['p_value_top1'])}). Spåren ensamma säger lite.

**5.5 Verkliga luckor.** På de fem stenarna med luckor som Rundata markerar ({N_GAP_WORDS} ord med förlorade runor) kördes kedjan från skanning till förslag, och förslagen jämfördes med utgivarnas läsning i Rundata. Utan spår stämde {GU} av {N_GAP_WORDS} ord, med spåren {GS} av {N_GAP_WORDS}. Där stavarna är hela behöll spåren de rätta orden, *stæin* på Sö 211 och *gæiRfastr* på Sö 45. På Sö 162 drog spåren förslaget från *stæin* (sten), som stämmer, till *staf* (stav), som inte gör det; kodens regel för samma ord räknade *staf* som *stæin*. På Sö 206 läser Rundata namnet *G[uðl]aug*, och både förslaget utan spår, *karl*, och förslaget med spår, *kumbl*, är fel. På Sö 360 sänkte spåren sannolikheten för förslaget *farinn* från {P360_SV[0]} till {P360_SV[1]}; utgivarna lämnar den runföljden otolkad. Spårläsaren är prövad på oskadade runor, och vittring vid en skada ger just de falska kvistar som den då läser.

## 6. Diskussion

**Vad metoden klarar.** I provet höjde skanningens spår sannolikheten för rätt ord, och samma uppsättningar på fel plats tog bort vinsten. Men parningen mellan skanning och text såg svaret, och på den enda sten där parningen var säker ändrades inte andelen rätt ord. Provet visar alltså att kedjan från skanning till förslag går att bygga, inte hur mycket spåren hjälper när svaret är okänt. Det är ett första steg mot att 3D-skanning och språkmodell läser en inskrift tillsammans, där skanningen visar vad som går att se och modellen vad som går att säga.

**Mot tidigare forskning.** Ithaca använder bara texten (Assael m.fl. 2022). Här läggs det som går att se på stenen till, i form av sannolikheter som modellen väger in. Skanningarna gjordes för att studera huggteknik (Kitzler Åhfeldt 2015) och kan också bli en källa för läsningen.

**Svagheter, i ordning efter vikt.**

1. **Svaret var inte dolt för parningen.** Skanningens runor parades mot texten med det dolda ordet synligt, och kontrollen med omflyttade spår skiljer inte parningens fördel från spårens egen läsning. Parningen var säkrare än slumpen bara på Sö 134, och där ändrades inte andelen rätt ord.
2. **Äldre versioner.** Provet gäller mätmetoden {VT['method']} och språkmodellen {VT['textmodel_f']}, i huvudprovet med faktorn {fac(TRACE_EPS_F)} för spåren. Vitki använder i dag ({TODAY}) {VN['method']} och {VN['textmodel']} med faktorn {fac(VN['trace_eps'])}; de är inte prövade på samma sätt.
3. **Dolda ord är inte skadade ord.** Provet döljer ord vars runor är hela på stenen. Vid verkliga skador har spåren bara prövats på fem stenar, och där stämde {GS} av {N_GAP_WORDS} förslag med spåren mot {GU} av {N_GAP_WORDS} utan.
4. **Ingen låst plan.** Provets villkor bestämdes före körningen, men utan en plan med kontrollsumma, och en första körning gav delvis andra förslag med omflyttade spår. Inställningarna togs fram på Sö 113, som ingår i provet; utan den är resultatet detsamma.
5. **En skanningsserie.** Alla stenar kommer ur samma serie i Södermanland, med samma skanner. Andra skannrar och andra stenar kan ge andra spår.
6. **Måttet för rätt ord.** Ett ord räknas som rätt när det är samma ord eller böjning; regeln räknar ibland närliggande former som samma, vilket gäller alla tre villkoren lika. I provet på verkliga luckor räknade en likhetsregel *staf* som *stæin*.

**Var metoden inte ska användas.** Ensam, vid svåra skador. Där ska spåren visas för den som läser stenen och vägas in först när läsaren har bekräftat dem; så var Vitki byggt när denna rapportversion skrevs ({TODAY}).

**Vad som skulle fälla metoden.** Att ett nytt prov med svaret dolt också för parningen inte gav någon förbättring, att spåren inte hjälpte på stenar ur andra skanningsserier, eller att de oftare ledde fel än rätt vid verkliga skador i ett större material.

## 7. Slutsats

Med 3D-skanningens spår fyllde språkmodellen i {d1(MN['skanner']['word_ok'])} procent av de dolda orden rätt mot {d1(MN['utan']['word_ok'])} procent utan, men parningen mellan skanning och text såg svaret, så provet visar inte hur mycket spåren hjälper när svaret är okänt. Provet gäller äldre versioner av mätmetoden och språkmodellen och behöver göras om med svaret dolt för hela kedjan. Vid svåra skador måste en människa bekräfta vad skanningen ser innan det vägs in.

## Data och kod

Provet kördes {VT['date_f']} (commit {VT['commit_f']} och {VT['commit_g']}) med mätmetoden {VT['method']} och språkmodellen {VT['textmodel_f']}; omräkningen 2026-10-31 räknade bara om de sparade raderna. När denna rapportversion skrevs ({TODAY}) använde Vitki mätmetoden {VN['method']} (spårläsaren läser {VN['method']}-mätningarna sedan commit {VS['commit']}, {VS['date']}) och språkmodellen {VN['textmodel']} med faktorn {fac(VN['trace_eps'])} för spåren; ingen av dem är prövad på det här sättet. Kodläget anges med commit i [Precatio/runes](https://github.com/Precatio/runes), eftersom det inte fanns någon release av Vitki med DOI när denna rapportversion skrevs. Kontrollen för rapportversion 3 (`kontroll_v3.py`) och byggskriptet för den versionen finns i commit 6eae0af ({TODAY}). Koden och resultatfilerna nedan finns öppet på GitHub under GPL-3.0.

- Spårläsaren och proven: `utdata/sparlasare/` (stegen `led_a.py`–`led_g.py`; huvudprovet `led_f.py` med raderna per sten `led_f_Sö_*.json`, skanningens mätta drag `*_feats_e.json` och sammanställningen `led_f_summering.py` → `led_f_summering.json`; den första körningen `led_f.json`; det tidigare steget `led_e.py` → `led_e_perm.json`; omräkningen utan Sö 113 `utan_so113.py` → `utan_so113.json`; verkliga luckor `led_g.py` → `led_g.json`; kontrollen för rapportversion 3 `kontroll_v3.py` → `kontroll_v3.json`).
- Huggspåren: `src/auto_grooves.py` ({VT['method']} vid commit {VT['commit_f']}). Språkmodellen: `src/runlm.py` och `src/textmodel.py` ({VT['textmodel_f']} vid commit {VT['commit_f']} och {VT['commit_g']}). Spårläsaren i Vitki: `src/trace_reader.py`.
- Texterna: Rundata (version 2014, RUNDATA.xls 2018), `data/rundata.json`, oförändrad sedan {RD['last_change']} (git-blob {RD['blob_now'][:7]}), samma fil som provet läste.
- Skanningarna: Kitzler Åhfeldt 2024, [doi:10.5281/zenodo.11951255](https://doi.org/10.5281/zenodo.11951255).
- Rapporten byggs av `utdata/blogg/build/build_rapport_sparlasare.py`, som läser alla tal ur resultatfilerna och stannar om något inte stämmer.
- I Vitki visas spåren i stenanalysen under ”Vad skannern ser i luckan”, och de räknas först när användaren har bekräftat dem.
- De statistiska begreppen förklaras i ordlistan: [vitkirunor.se/forskningsrapporter/begrepp](https://vitkirunor.se/forskningsrapporter/begrepp).

## Referenser

- Assael, Y., Sommerschield, T., Shillingford, B. m.fl. 2022. Restoring and attributing ancient texts using deep neural networks. *Nature* 603, s. 280–283.
- Kitzler Åhfeldt, L. 2002. *Work and Worship: Laser Scanner Analysis of Viking Age Rune Stones*. Theses and Papers in Archaeology B:9. Stockholm: Stockholms universitet.
- Kitzler Åhfeldt, L. 2015. Rune Carvers and Local Mobility. *Viking and Medieval Scandinavia* 11, s. 143–182.
- Kitzler Åhfeldt, L. 2024. *3D-data Runstenar i Södermanland / Runestones in Södermanland* [datamängd]. Riksantikvarieämbetet. Zenodo. [doi:10.5281/zenodo.11951255](https://doi.org/10.5281/zenodo.11951255). CC BY 4.0.
- Samnordisk runtextdatabas (Rundata), version 2014 med RUNDATA.xls uppdaterad 2018. Institutionen för nordiska språk, Uppsala universitet. Open Database License.

:::box Det viktigaste i korthet
- Det en 3D-skanning visar av en runa höjde sannolikheten för rätt ord i provet, men parningen mellan skanning och text såg svaret, så provet visar inte hur mycket skanningen hjälper när svaret är okänt.
- Tanken att skanningen och språket läser en runsten tillsammans, där det ena visar vad som syns och det andra vad som går att säga, återstår att pröva med svaret dolt för hela kedjan och med de versioner Vitki använder.
- Vid svåra skador kan spåren leda fel, så en människa måste se och bekräfta dem först.
:::

{LOG_SV}
"""

body_en = f"""*Viktor Kvant, independent researcher. Methods report, partially tested. Report version {REPORT_VERSION}, {TODAY} (version 1 published {V1_DATE}, version 2 {V2_DATE}). Timeline: {TL_EN}. The analysis was made in Vitki {APP_VERSION}; the test was run on {VT['date_f']} with code that this version contains (see Data and code). Licence CC BY 4.0. This English version is the canonical one for citation: {CITE_EN}. Keywords: runestones, Viking Age, 3D scanning, damaged runes, language model, lacunae, restoration, Södermanland. Competing interests: none. Funding: none.*

## Abstract

**What has not been tested.** {FIRST_EN} Nor was the test locked in a plan, and the trace reader's settings were derived on one of the stones in the test. The test hides whole words of whole runes; at real damage the traces have been tested on only five stones, and there fewer suggestions agreed with the editors' reading with the traces than without them.
**Background and aim.** When runes are damaged the runologist reads what remains on the stone, and a language model can suggest what stood there. The question here is whether what a 3D scan shows of the damaged runes makes the language model's suggestions better.
**Material.** 17 runestones in Södermanland that Laila Kitzler Åhfeldt has scanned in 3D and published openly, with their text in the Scandinavian Runic-text Database (Rundata, 2014 version with RUNDATA.xls updated 2018); {A['n']} words that could be tested.
**Method.** A trace reader reads in the scan's depth image which of the sixteen runes each detected rune can be, with a probability for each. The scan's runes are paired with the positions of the text. Every whole word of two to six runes is hidden, and a language model trained without the stone fills it in: without traces, with the traces and with the same traces shuffled at random among the stone's positions. The comparison is paired, word by word.
**Results.** With the traces {e1(MN['skanner']['word_ok'])} percent of the words came out right, against {e1(MN['utan']['word_ok'])} percent without them ({KM['utan_to_skanner']['wrong_to_right']} words became right with the traces and none became wrong; the probability of the right word rose, {pexp(SU['p'], True)}). With shuffled traces the gain vanished and the probability fell ({p2(OU['p'], True)}). Without the stone on which the settings were derived: {e1(XU['means']['skanner']['word_ok'])} against {e1(XU['means']['utan']['word_ok'])} percent. On Sö 134, the only stone where the pairing beat chance, {e1(R1['means']['utan']['word_ok'])} percent of the {R1['n']} words came out right in all three conditions. On five stones with real lacunae {GU} of {N_GAP_WORDS} suggestions agreed with the editors' reading in Rundata without traces and {GS} of {N_GAP_WORDS} with them.
**Conclusion.** The traces raised the probability of the right word in the test, but since the pairing saw the answer, what the scan reads cannot be told apart from what the pairing already knew, and on the only reliably paired stone the share of right words did not change. The method needs to be tested again with the answer hidden from the whole chain and with the versions Vitki uses. At severe damage the traces should be shown to the reader and weighed in only once the reader has confirmed them.

## 1. Introduction

Many runic inscriptions have damaged or lost runes. The runologist reads what remains on the stone, and the editions mark certain, uncertain and lost runes. In recent years language models have been used to suggest what stood in damaged inscriptions; the best known is Ithaca for Greek inscriptions (Assael et al. 2022). Laila Kitzler Åhfeldt has scanned a large number of runestones in 3D to study carving technique (Kitzler Åhfeldt 2002; 2015) and published the scans openly (Kitzler Åhfeldt 2024).

What is missing is a way of letting what the scan shows of a damaged rune steer what a language model suggests, and a test of whether it helps. The aim here is to report a trace reader that does so and to test it on hidden words on scanned stones.

## 2. Pre-registration: what was fixed in advance and what was not

The test was not locked in a plan. The trace reader was built in steps on 17 October 2026. Its two settings, how sharply the probabilities are distributed and what an extra part of a rune costs, were tried out on Sö 113 alone and then validated on Sö 134 and Sö 207, which had not been used. The main test was then fixed in the code, with three conditions and the same measures for all stones. A first run the same day on Sö 113 and Sö 134 ({ER['words']} words) gave the same results without traces and with the traces, but with shuffled traces the suggestion differed for {EO['top_differs']} of the {ER['words']} words, all on Sö 134, because the shuffle was drawn differently when the two stones were run together; {EO['right_in_final_not_earlier']} of them came out right in the final run but wrong in the first. The final run was made stone by stone on all 17 stones, and it is the one reported. Sö 113 is among the 17 stones; on 31 October the test was recomputed without Sö 113, with the same test on the saved rows. The test on real lacunae was run the same day as the main test.

## 3. Material

- **The scans.** Laila Kitzler Åhfeldt, Swedish National Heritage Board, scanned the runestones of Södermanland with an ATOS scanner in the project Runristandets dynamik and published them on Zenodo under CC BY 4.0 (Kitzler Åhfeldt 2024). Of these, the {A['stones']} stones were used for which Rundata has a word text that can be paired with the detected runes. Runestones only.
- **The texts.** Transliteration and normalisation from the Scandinavian Runic-text Database (Rundata), 2014 version with RUNDATA.xls updated 2018.
- **The words.** Every whole word of two to six runes: {KM['positions']} word positions, {A['n']} of them where all three conditions gave a result.
- **Real lacunae.** Five stones from the same series with lacunae marked in Rundata: {', '.join(sorted(G))}.

## 4. Method

**4.1 The trace reader.** In the scan's depth image the runes' staves are found. Parts of the groove outside the staves, branches and bows, get a weight by how deep, elongated and long they are, since weathering and marks in the surface give shallow and short traces. Each detected rune is compared with the shape of each of the sixteen runes, with a cost for parts missing or too many, and the costs are turned into a probability per rune. The grooves were measured with the version of the measurement method in use on 17 October 2026 ({VT['method']}); Vitki has since moved to a later version ({VN['method']}), which has not been tested in this way.

**4.2 The language model.** The project's model of runic text, in the version in use on 17 October 2026 ({VT['textmodel_f']}), suggests words and weighs them by how common they are in the runic texts and in their context. It is trained without the stone being tested. The traces are put in softly: a rune the scan does not support becomes less probable, not impossible. In the main test each such rune weighed a suggestion down by a factor of {fac(TRACE_EPS_F, True)}, in the test on real lacunae by {fac(VT['trace_eps_g'], True)}, the factor Vitki also uses.

**4.3 The test.** Every whole word of two to six runes is hidden and filled in under three conditions: without traces, with the trace reader's probabilities for the word's runes, and with the same sets shuffled at random among the stone's positions. The last condition was meant to test whether the traces help because they read the stone, or merely because they reduce the number of possible runes. The measures are the share of words that came out right and the probability of the right word; the probability is compared word by word with Wilcoxon's test for paired values, the share of right words is reported without a test. To know which detected rune belongs to which position in the text, the scan's runes were paired with the text's runes, once per stone and using the full known text, before any word was hidden (see 4.4). The pairing was tested against the same pairing with the text shuffled 20 times, and counted as reliable when the share of paired runes whose text rune was among those the scan supports lay at least two standard deviations above that of the shuffled text.

**4.4 Deviations and errors.** No plan existed, so no deviations from a plan can be reported. Three things were not reported in the first two versions of the report: that the pairing saw the hidden word, that the code's own check found the pairing reliable on only one stone, and that the test was run more than once. The pairing of the scan's runes with the text used the full known text, including the word that was then hidden, and it costs nothing where the text's rune is among those the scan supports; it can therefore pull the scan's sets to the positions where they agree with the answer. This can favour the condition with traces, and the control with shuffled traces does not separate that advantage from the traces' own reading, since both vanish when the sets are moved. The code's own check found the pairing reliable only on Sö 134 (1 of {K['pairing']['stones']} stones). The error has not been corrected and the test has not been rerun. The first run is reported in 2. The recomputation without Sö 113 was made after the test.

## 5. Results

**5.1 The main test.** {A['n']} words on {A['stones']} stones. Right word: {e1(MN['utan']['word_ok'])} percent without traces ({RW['utan']} words), {e1(MN['skanner']['word_ok'])} percent with the traces ({RW['skanner']}) and {e1(MN['omflyttad']['word_ok'])} percent with the traces shuffled ({RW['omflyttad']}). With the traces {KM['utan_to_skanner']['wrong_to_right']} words came out right that were wrong without them, and no word that was right became wrong; with shuffled traces {KM['utan_to_omflyttad']['wrong_to_right']} words became right and {KM['utan_to_omflyttad']['right_to_wrong']} wrong. The probability of the right word: {MN['utan']['p_truth']:.3f} without, {MN['skanner']['p_truth']:.3f} with and {MN['omflyttad']['p_truth']:.3f} with shuffled traces. The traces gave a higher probability than no traces, {pexp(SU['p'], True)}, and higher than shuffled traces, {pexp(SO['p'], True)}. Shuffled traces gave a lower probability than no traces, {p2(OU['p'], True)}; in the share of right words the difference was one word of {A['n']}. All p-values concern the probability of the right word, not the share of right words. In plain words: with the scan's traces about six hidden words in ten came out right instead of just over five; {KM['utan_to_skanner']['wrong_to_right']} words became right and none became wrong. When the traces were shuffled the gain vanished. But the pairing between scan and text saw the answer (4.4), so some or all of the gain may come from the pairing rather than from the scan.

{chart(False)}

{FIG_EN}

**5.2 Without Sö 113, and the only reliably paired stone.** Without the stone on which the settings were derived: {XU['n']} words on {XU['stones']} stones, {e1(XU['means']['utan']['word_ok'])} percent right without traces, {e1(XU['means']['skanner']['word_ok'])} with and {e1(XU['means']['omflyttad']['word_ok'])} with shuffled; the probability of the right word with the traces against no traces {pexp(XU['skanner_vs_utan']['p'], True)}, against shuffled {pexp(XU['skanner_vs_omflyttad']['p'], True)}. Only on Sö 134 did the pairing beat chance. There {e1(R1['means']['utan']['word_ok'])} percent of the {R1['n']} words came out right in all three conditions, and no word changed; the probability of the right word rose with the traces (on average from {d2(R1['means']['utan']['p_truth'], True)} to {d2(R1['means']['skanner']['p_truth'], True)}), {p2(RSU['p'], True)} against no traces, just above the usual 0.05 limit and with {R1['n']} words a weak sign, and {p2(RSO['p'], True)} against shuffled.

**5.3 Calibration.** Not tested. The test saved the probability of the right word but not that of the model's first choice, so it cannot show whether the model's probabilities match how often the suggestions came out right. The {N_GAP_WORDS} words in real lacunae are too few for such a test.

**5.4 The earlier step, on undamaged runes.** Before the language model was connected, the trace reader was tested on its own on the detected runes of Sö 113, Sö 134 and Sö 207: the probability of the right rune was on average {E['pooled_mean_p']:.3f} against {E['pooled_null'][0]:.3f} when the text was shuffled ({E['n_shuffles']} shuffles, {pf(E['p_value'], True)}), and the right rune came first in {e1(E['pooled_top1'])} percent against {e1(E['pooled_top1_null'][0])} ({pf(E['p_value_top1'], True)}). The traces alone say little.

**5.5 Real lacunae.** On the five stones with lacunae marked in Rundata ({N_GAP_WORDS} words with lost runes) the chain from scan to suggestion was run, and the suggestions were compared with the editors' reading in Rundata. Without traces {GU} of {N_GAP_WORDS} words agreed, with the traces {GS} of {N_GAP_WORDS}. Where the staves are whole the traces kept the right words, *stæin* on Sö 211 and *gæiRfastr* on Sö 45. On Sö 162 the traces pulled the suggestion from *stæin* (stone), which agrees, to *staf* (staff), which does not; the code's rule for the same word counted *staf* as *stæin*. On Sö 206 Rundata reads the name *G[uðl]aug*, and both the suggestion without traces, *karl*, and the one with traces, *kumbl*, are wrong. On Sö 360 the traces lowered the probability of the suggestion *farinn* from {P360_EN[0]} to {P360_EN[1]}; the editors leave that rune sequence uninterpreted. The trace reader is tested on undamaged runes, and weathering at a lesion produces exactly the false branches it then reads.

## 6. Discussion

**What the method can do.** In the test the scan's traces raised the probability of the right word, and the same sets in the wrong place removed the gain. But the pairing between scan and text saw the answer, and on the only stone where the pairing was reliable the share of right words did not change. The test thus shows that the chain from scan to suggestion can be built, not how much the traces help when the answer is unknown. It is a first step towards 3D scanning and a language model reading an inscription together, the scan showing what can be seen and the model what can be said.

**Against earlier research.** Ithaca uses only the text (Assael et al. 2022). Here what can be seen on the stone is added, as probabilities the model weighs in. The scans were made to study carving technique (Kitzler Åhfeldt 2015) and may also become a source for reading.

**Weaknesses, in order of weight.**

1. **The answer was not hidden from the pairing.** The scan's runes were paired with the text with the hidden word visible, and the control with shuffled traces does not separate the pairing's advantage from the traces' own reading. The pairing beat chance only on Sö 134, and there the share of right words did not change.
2. **Older versions.** The test concerns the {VT['method']} measurement method and the {VT['textmodel_f']} language model, in the main test with a factor of {fac(TRACE_EPS_F, True)} for the traces. Vitki now ({en_date(TODAY)}) uses {VN['method']} and {VN['textmodel']} with a factor of {fac(VN['trace_eps'], True)}; they have not been tested in the same way.
3. **Hidden words are not damaged words.** The test hides words whose runes are whole on the stone. At real damage the traces have been tested on only five stones, and there {GS} of {N_GAP_WORDS} suggestions agreed with the traces against {GU} of {N_GAP_WORDS} without.
4. **No locked plan.** The test's conditions were fixed before the run, but without a plan with a checksum, and a first run gave partly different suggestions with shuffled traces. The settings were derived on Sö 113, which is in the test; without it the result is the same.
5. **One scanning series.** All stones come from the same series in Södermanland, with the same scanner. Other scanners and other stones may give other traces.
6. **The measure of a right word.** A word counts as right when it is the same word or inflection; the rule sometimes counts neighbouring forms as the same, which applies equally to all three conditions. In the test on real lacunae a similarity rule counted *staf* as *stæin*.

**Where the method should not be used.** On its own, at severe damage. There the traces should be shown to the reader of the stone and weighed in only once the reader has confirmed them; that is how Vitki was built when this report version was written ({en_date(TODAY)}).

**What would overturn the method.** If a new test with the answer hidden from the pairing as well gave no improvement, if the traces did not help on stones from other scanning series, or if they misled more often than they helped at real damage in a larger material.

## 7. Conclusion

With the 3D scan's traces the language model filled in {e1(MN['skanner']['word_ok'])} percent of the hidden words correctly against {e1(MN['utan']['word_ok'])} percent without, but the pairing between scan and text saw the answer, so the test does not show how much the traces help when the answer is unknown. The test concerns older versions of the measurement method and the language model and needs to be redone with the answer hidden from the whole chain. At severe damage a human must confirm what the scan sees before it is weighed in.

## Data and code

The test was run on {en_date(VT['date_f'])} (commits {VT['commit_f']} and {VT['commit_g']}) with the {VT['method']} measurement method and the {VT['textmodel_f']} language model; the 31 October recomputation only re-aggregated the saved rows. When this report version was written ({en_date(TODAY)}), Vitki used the {VN['method']} measurement method (the trace reader has read the {VN['method']} measurements since commit {VS['commit']}, {en_date(VS['date'])}) and the {VN['textmodel']} language model with a factor of {fac(VN['trace_eps'], True)} for the traces; neither has been tested in this way. The code state is given by commit in [Precatio/runes](https://github.com/Precatio/runes), since no release of Vitki with a DOI existed when this report version was written. The check for report version 3 (`kontroll_v3.py`) and the builder of that version are in commit 6eae0af ({en_date(TODAY)}). The code and the result files below are openly available on GitHub under GPL-3.0.

- The trace reader and the tests: `utdata/sparlasare/` (the steps `led_a.py`–`led_g.py`; the main test `led_f.py` with the rows per stone `led_f_Sö_*.json`, the scan's measured features `*_feats_e.json` and the summary `led_f_summering.py` → `led_f_summering.json`; the first run `led_f.json`; the earlier step `led_e.py` → `led_e_perm.json`; the recomputation without Sö 113 `utan_so113.py` → `utan_so113.json`; real lacunae `led_g.py` → `led_g.json`; the check for report version 3 `kontroll_v3.py` → `kontroll_v3.json`).
- The grooves: `src/auto_grooves.py` ({VT['method']} at commit {VT['commit_f']}). The language model: `src/runlm.py` and `src/textmodel.py` ({VT['textmodel_f']} at commits {VT['commit_f']} and {VT['commit_g']}). The trace reader in Vitki: `src/trace_reader.py`.
- The texts: Rundata (version 2014, RUNDATA.xls 2018), `data/rundata.json`, unchanged since {en_date(RD['last_change'])} (git blob {RD['blob_now'][:7]}), the same file the test read.
- The scans: Kitzler Åhfeldt 2024, [doi:10.5281/zenodo.11951255](https://doi.org/10.5281/zenodo.11951255).
- The report is built by `utdata/blogg/build/build_rapport_sparlasare.py`, which reads every number from the result files and stops if anything disagrees.
- In Vitki the traces are shown in the stone analysis under "Vad skannern ser i luckan" (what the scanner sees in the gap), and they count only once the user has confirmed them.
- The statistical terms are explained in the glossary: [vitkirunor.se/en/forskningsrapporter/begrepp](https://vitkirunor.se/en/forskningsrapporter/begrepp).

## References

- Assael, Y., Sommerschield, T., Shillingford, B. et al. 2022. Restoring and attributing ancient texts using deep neural networks. *Nature* 603, pp. 280–283.
- Kitzler Åhfeldt, L. 2002. *Work and Worship: Laser Scanner Analysis of Viking Age Rune Stones*. Theses and Papers in Archaeology B:9. Stockholm: Stockholm University.
- Kitzler Åhfeldt, L. 2015. Rune Carvers and Local Mobility. *Viking and Medieval Scandinavia* 11, pp. 143–182.
- Kitzler Åhfeldt, L. 2024. *3D-data Runstenar i Södermanland / Runestones in Södermanland* [dataset]. Swedish National Heritage Board. Zenodo. [doi:10.5281/zenodo.11951255](https://doi.org/10.5281/zenodo.11951255). CC BY 4.0.
- Scandinavian Runic-text Database (Rundata), 2014 version with RUNDATA.xls updated 2018. Department of Scandinavian Languages, Uppsala University. Open Database License.

:::box The essentials
- What a 3D scan shows of a rune raised the probability of the right word in the test, but the pairing between scan and text saw the answer, so the test does not show how much the scan helps when the answer is unknown.
- The idea that the scan and the language read a runestone together, one showing what can be seen and the other what can be said, remains to be tested with the answer hidden from the whole chain and with the versions Vitki uses.
- At severe damage the traces can mislead, so a human must see and confirm them first.
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
    # every link is absolute (the figure is the site's own image path, which BlogBody only accepts relative)
    assert all(u.startswith("https://") or u.startswith("/api/blog/figures/") for u in re.findall(r"\]\(([^)]+)\)", b))
    pre_log = b.split("## Ändringslogg")[0].split("## Change log")[0]
    assert "Kvant, V. 2026" not in b and "sharp test" not in pre_log and "skarpa provet" not in pre_log
    # the chart's caption is recognised only when its line starts with Källa:/Source: (BlogBody.tsx); the credit ends it
    for blk in re.findall(r"^:::chart[^\n]*\n(.*?)^:::$", b, re.M | re.S):
        cap = [ln for ln in blk.splitlines() if "Vitki" in ln]
        assert len(cap) == 1 and re.match(r"^(Källa|Source):", cap[0]) and re.search(r"(Diagram|Chart): Vitki, (efter|after) [^\n]+\.$", cap[0])
        assert not re.search(r"^(Diagram|Chart):", blk, re.M)
assert "Det viktigaste i korthet" in body and "## 2. Förregistrering" in body and "## 6. Diskussion" in body
assert "I klartext" in body and "In plain words" in body_en  # mallen version 4
assert f"## Sammanfattning\n\n**Vad som inte är prövat.** {FIRST_SV}" in body  # mallen: nivå 2, äldre version först
assert f"## Abstract\n\n**What has not been tested.** {FIRST_EN}" in body_en
assert "**5.3 Kalibreringen.** Inte prövad." in body and "**5.3 Calibration.** Not tested." in body_en
assert body.split("\n", 1)[0].startswith(f"*Viktor Kvant, oberoende forskare. Metodrapport, delvis prövad. Rapportversion 4, {TODAY} (version 1 publicerad 2026-10-31, version 2 2026-11-01). Tidslinje: ")
assert body_en.split("\n", 1)[0].startswith(f"*Viktor Kvant, independent researcher. Methods report, partially tested. Report version 4, {TODAY} (")
assert "## Ändringslogg" in body and body.rstrip().endswith(V4_SV) and body_en.rstrip().endswith(V4_EN)
for b_, old in ((body, "version 3.1"), (body_en, "version 3.1"), (body, "så en del av vinsten kan"), (body_en, "so part of the gain")):
    assert old not in b_, old
# the header line as the site and the Zenodo script read it (web/src/lib/report.ts, scripts/zenodo_rapporter.py)
H_EN = body_en.split("\n", 1)[0]
assert re.search(r"Report version (\d+), (\d{4}-\d{2}-\d{2})", H_EN).groups() == ("4", TODAY)
assert re.search(r"made in Vitki ([\d.]+)", H_EN).group(1) == APP_VERSION
assert re.search(r"independent researcher\. ([^.]+)\.", H_EN).group(1) == "Methods report, partially tested"
for line, lab in ((body.split("\n", 1)[0], "Analysen är gjord"), (H_EN, "The analysis was made")):
    tl = re.search(r"(?:Tidslinje|Timeline):\s*(.+?)\.\s+(?:Analysen är gjord|The analysis was made|Licens|Licence)", line)
    assert tl and lab in line and all(re.match(r"^.*?\s+\d{4}-\d{2}-\d{2}$", ev.strip()) for ev in tl.group(1).split(";"))
    assert len(tl.group(1).split(";")) == 6

out = {"slug": SLUG, "title": title, "summary": summary, "body": body, "title_en": title_en, "summary_en": summary_en,
       "body_en": body_en, "labels": ["Rapport", "Huggspår och 3D", "Sannolikhetsmodellen"]}
assert blog_labels.check(out["labels"]) is None
path = os.path.join(ROOT, "utdata", "rapporter", "rapport_sparlasare.json")
json.dump(out, open(path, "w"), ensure_ascii=False, indent=1)
print(path, len(body.split()), "ord,", len(body.split("## Data")[0].split()), "före Data och kod;", len(body_en.split()), "words")

# Data och kod says the result files are open on GitHub: they live under the ignored utdata/ and need `git add -f`
NEED = sorted(os.path.relpath(p, ROOT) for p in glob.glob(os.path.join(SD, "*.json")) + glob.glob(os.path.join(SD, "*.py")))
try:
    tracked = set(subprocess.run(["git", "-c", "core.quotepath=off", "-C", ROOT, "ls-files", "utdata/sparlasare"],
                                 capture_output=True, text=True, check=True).stdout.splitlines())
    missing = [p for p in NEED if p not in tracked]
    if missing:
        print(f"OBS: {len(missing)} filer i utdata/sparlasare är inte i git; Data och kod stämmer först efter `git add -f`:")
        print("  " + " ".join(missing))
except (OSError, subprocess.CalledProcessError):
    pass

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
                 "topic": "Rapport|sparlasare", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
