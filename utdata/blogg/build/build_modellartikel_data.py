"""Siffrorna till artikeln "Runorna som fattas" (textmodel-15 och senare, 2026-10-17): allt som texten säger om proven,
kalibreringen, kontrollerna och körningen över alla runstenar, hämtat ur provfilerna och kontrollerat. Läses av
build_modellartikel.py. Runstenar först; andra stenar och lösa föremål redovisas för sig (utdata/modellartikel/runstenar.py).
    ../../../.venv/bin/python build_modellartikel_data.py   (skriver ut siffrorna)"""
import glob
import json
import os
import re
import sys
from collections import Counter

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import runlm as rl  # noqa: E402
from src import textmodel as tm  # noqa: E402

M = os.path.join(ROOT, "utdata", "modellartikel")
F = os.path.join(ROOT, "utdata", "runlm_forfining")
LOGS = os.path.join(ROOT, "data", "cache", "logs")
J = lambda *p: json.load(open(os.path.join(*p)))  # noqa: E731
recs = rl.load_rundata()
by = {r["signum"]: r for r in recs}
rs = lambda s: rl.object_kind(by[s]) == "runsten"  # noqa: E731
pr = lambda x: int(100 * x + 0.5)  # noqa: E731 – percent, rounded as the app's panel rounds
D = {"version": tm.VERSION, "validation": tm.VALIDATION}

# --- the reading test (scripts/runlm_calibrate.py --own_d, 808 inscriptions in five parts) and the first version
RT = J(F, "kalib_tm14_egend.json")
RS = J(M, "runstenar.json")
D["reading"] = {"inscriptions": RT["n_inscriptions"], "words": RT["n_gold"], "same": RT["same"], "span": RT["span"],
                "ece_raw": RT["ece_raw"], "ece": RT["ece"], "first_same": 81, "first_span": 92,
                "gain_words": round((RT["same"] - 0.8138) * RT["n_gold"] / 50) * 50,  # step 1: 83.50 − 2.12 % (METHODS 8.1)
                "by_kind": RS["reading"]}
assert RT["n_inscriptions"] == 808 and pr(RT["same"]) == 84 and pr(RT["span"]) == 95

# --- the masking test (mask4, the generation textmodel-18's VALIDATION uses), the hard masking test (svart: only
# words outside the 50 commonest) and the traces
mask = [x for k in range(5) for x in J(F, f"mask4_f{k}.json")["rows"] if rs(x["sig"])]
hard = [x for k in range(5) for x in J(F, f"svart_f{k}.json")["rows"] if rs(x["sig"])]
G = tm._records()["G"]


def cal_bins(xs):
    """The masked gaps with today's calibration: ECE, the ≥ 95 % gaps and how many hold – under the masking test's
    strict lemma rule and under the rule the documented benchmark and the app use (rl.same_word, which also unites
    normalization variants such as hakun/hakon) – and the 0.80–0.95 band where the hard test stays overconfident."""
    xs = [x for x in xs if x["word"] and x["word"] != "<unk>"]
    q = np.array([tm.calibrate_gap(x["p_word"], x["word"], x["n"], G, x["kind"] == "helt ord") for x in xs])
    y = np.array([float(x["word_ok"]) for x in xs])
    y_sw = np.array([float(x["word_ok"] or rl.same_word(x["word"].lstrip("§"), rl.normtok(x["gold_word"]))) for x in xs])
    ece = sum(abs(q[m].mean() - y[m].mean()) * m.sum() for lo, hi in ((0, .5), (.5, .8), (.8, .95), (.95, 1.01))
              for m in [(q >= lo) & (q < hi)] if m.any()) / len(y)
    sure = q >= 0.95
    band = (q >= 0.8) & (q < 0.95)
    return {"ece": float(ece), "sure_n": int(sure.sum()),
            "sure_right": float(y[sure].mean()) if sure.any() else None,
            "sure_right_sw": float(y_sw[sure].mean()) if sure.any() else None,
            "band_n": int(band.sum()), "band_said": float(q[band].mean()) if band.any() else None,
            "band_right_sw": float(y_sw[band].mean()) if band.any() else None}


D["masking"] = {kind: {"n": sum(x["kind"] == kind for x in mask), "right": float(np.mean([x["word_ok"] for x in mask if x["kind"] == kind]))}
                for kind in ("inne i ord", "helt ord")}
D["hard"] = {kind: {"n": sum(x["kind"] == kind for x in hard), "right": float(np.mean([x["word_ok"] for x in hard if x["kind"] == kind])),
                    "cal": cal_bins([x for x in hard if x["kind"] == kind])} for kind in ("inne i ord", "helt ord")}
D["hard"]["pooled"] = cal_bins(hard)
assert pr(D["masking"]["inne i ord"]["right"]) == pr(tm.VALIDATION["inside_word"]) == 76
assert pr(D["masking"]["helt ord"]["right"]) == pr(tm.VALIDATION["whole_word"]) == 59
assert pr(D["hard"]["inne i ord"]["right"]) == 47 and D["hard"]["inne i ord"]["cal"]["ece"] < 0.06
assert D["hard"]["pooled"]["sure_n"] == 115 and 0.95 <= D["hard"]["pooled"]["sure_right_sw"] <= 0.96
assert 0.91 <= D["hard"]["pooled"]["sure_right"] <= 0.93 and 0.80 <= D["hard"]["pooled"]["band_right_sw"] <= 0.87

# --- the gaps the editors filled (scripts/runlm_gaps.py --own_d, klass3) and the documented gaps (runes in [ ])
D["restored"] = RS["gaps"]["runsten"]
D["documented"] = J(F, "dok_bins.json")
GL = J(ROOT, "data", "runlm_calibration.json")["gap_list"]  # the joint list calibration (textmodel-17)
D["calibration"] = {r["label"]: r for r in GL["report"]}
DNY = D["calibration"]["documented | runstenar | ny (KV)"]
RNY = D["calibration"]["restored | runstenar | ny (KV)"]
assert D["documented"]["gaps"] == 361 and 0.66 <= D["documented"]["right"] <= 0.73
assert DNY["sure_right"] >= 0.98 and DNY["ece"] < 0.04 and RNY["chosen_right"] >= RNY["first_choice_right"]

# --- the dating test (scripts/runlm_dating.py, textmodel-14's settings; runestones)
dr = [x["true"] for x in J(F, "datering_tm14.json")["rows"] if rs(x["sig"])]
D["dating"] = {"n": len(dr), "right": tm.VALIDATION["dating_epoch"], "near": tm.VALIDATION["dating_near"],
               "majority": max(Counter(dr).values()) / len(dr)}
assert len(dr) == 1670 and pr(D["dating"]["majority"]) == 47

# --- the run over every inscription with gaps (scripts/textmodel_batch.py) and its duration from the logs
SUM = J(ROOT, "utdata", "textmodel_batch", "sammanstallning.json")
BS = J(M, "batch_status.json")
assert SUM["version"] == BS["version"] == tm.VERSION
VNUM = re.search(r"\d+", tm.VERSION).group(0)
secs = []
for f in glob.glob(os.path.join(LOGS, f"batch{VNUM}_f*.log")):
    m = re.findall(r"klar: \d+ av \d+ på (\d+) s", open(f).read())
    if m:
        secs.append(int(m[-1]))
assert len(secs) == 5, "körningen över alla stenar är inte klar för " + tm.VERSION
D["batch"] = {**RS["batch"]["runsten"], "hours_longest_part": max(secs) / 3600, "parts": len(secs),
              "other_inscriptions": sum(RS["batch"][k]["inscriptions"] for k in ("annan sten", "lösa föremål")),
              "other_gaps": sum(RS["batch"][k]["gaps"] for k in ("annan sten", "lösa föremål"))}
D["viking_runestones"] = RS["viking"]["runsten"]
D["viking_all"] = len([r for r in recs if rl.viking(r) and r.get("transliteration") and r.get("normalization")])

# --- the pre-registered blind test (utdata/blindtest: protocol committed and pushed before the single run)
BL_ = J(ROOT, "utdata", "blindtest", "resultat.json")
POP_ = J(ROOT, "utdata", "blindtest", "population.json")
D["blind"] = {"population": len(POP_["population"]), "pop_gaps": sum(x["gaps"] for x in POP_["population"]),
              "stones": len(BL_["stones"]), "n": BL_["n"], "right": BL_["right"], "interval": BL_["interval"],
              "mean_claimed": BL_["mean_claimed"], "claimed95": BL_["claimed95"],
              "warned": sum(1 for x in BL_["rows"] if not x["word_ok"] and x["p"] < 0.45),
              "misses": [(x["sig"], x["carved"], x["word"], x["gold_word"], x["p"]) for x in BL_["rows"] if not x["word_ok"]]}
assert (BL_["n"], BL_["right"], BL_["interval"]) == (21, 16, [10, 18]) and BL_["within_interval"]
assert BL_["claimed95"] == {"n": 13, "right": 13} and BL_["right_strikt"] == 16 and D["blind"]["warned"] == 4

# --- the scan-trace reader's first real test (utdata/sparlasare/led_f_summering.json: 17 scanned stones)
LF_ = J(ROOT, "utdata", "sparlasare", "led_f_summering.json")["all"]
D["scantraces"] = {"n": LF_["n"], "stones": LF_["stones"],
                   "utan": LF_["means"]["utan"]["word_ok"], "skanner": LF_["means"]["skanner"]["word_ok"],
                   "omflyttad": LF_["means"]["omflyttad"]["word_ok"], "p": LF_["skanner_vs_utan"]["p"]}
assert D["scantraces"]["stones"] == 17 and 0.53 <= D["scantraces"]["utan"] <= 0.54 and 0.59 <= D["scantraces"]["skanner"] <= 0.61
assert D["scantraces"]["p"] < 1e-4 and D["scantraces"]["omflyttad"] <= D["scantraces"]["utan"]

# --- the checks of the code itself (tests/, METHODS.md 8.1)
n_tests = sum(len(re.findall(r"^def test_", open(os.path.join(ROOT, "tests", f)).read(), re.M)) for f in ("test_runlm.py", "test_textmodel.py"))
D["checks"] = {"unit_tests": n_tests, "nltk_diff": "10⁻¹⁶", "split_diff": "10⁻¹⁴", "split_speed": "4,7", "split_speed_en": "4.7"}
assert n_tests >= 31

if __name__ == "__main__":
    print(json.dumps({k: v for k, v in D.items() if k not in ("validation",)}, ensure_ascii=False, indent=1, default=str)[:4000])
