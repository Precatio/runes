"""Siffrorna i textmodel.VALIDATION för textmodel-19 (toleranslagret λ = 0,02 ovanpå namnkvoten), räknade på runstenar
(2026-10-20) med den omskattade kalibreringen tm19/runlm_calibration_tm19.json (= data/runlm_calibration.json sedan
bytet). Underlag, alla regenererade av tm19-tåget (tm19_pipeline.py) i utdata/runlm_forfining/tm19/: maskeringsprovet
mask4_f* (= tol02_f*), gapprovet klass3_alla, de dokumenterade luckorna dok5_f*, dateringsprovet datering_tm14
(opåverkat). textmodel-18:s underlag ligger kvar på toppnivån. Spårproven (with_traces, with_misread_traces) är äldre
och gäller alla slags inskrifter, precis som i tidigare versioner.
    cd aagaard-research && RUNLM_CALIBRATION=utdata/runlm_forfining/tm19/runlm_calibration_tm19.json \\
        PYTHONPATH=. .venv/bin/python utdata/runlm_forfining/validering_tm19.py"""
import json

import numpy as np

from src import runlm as rl
from src import textmodel as tm

F = "utdata/runlm_forfining/tm19/"
CAL = F + "runlm_calibration_tm19.json"
d = tm._records()
by, G = d["by"], d["G"]
rs = lambda s: rl.object_kind(by[s]) == "runsten"  # noqa: E731
mask = [x for k in range(5) for x in json.load(open(f"{F}mask4_f{k}.json"))["rows"] if rs(x["sig"])]
inside = [x for x in mask if x["kind"] == "inne i ord"]
whole = [x for x in mask if x["kind"] == "helt ord"]
cal = [(tm.calibrate_gap(x["p_word"], x["word"], x["n"], G, x["kind"] == "helt ord"), x["word_ok"]) for x in mask
       if x["word"] and x["word"] != "<unk>"]
sure = [ok for q, ok in cal if q >= 0.95]
gaps = [x for x in json.load(open(F + "klass3_alla.json"))["rows"] if rs(x["sig"]) and x["status"] == "återställt"
        and x["word"] and x["word"] != "<unk>"]
agree = lambda x: bool(x.get("agrees")) or rl.same_word(x["word"].lstrip("§"), x["rundata"])  # noqa: E731
gsure = [agree(x) for x in gaps if tm.calibrate_gap(x["p"], x["word"], len(x["fill"]), G) >= 0.95]
dok = [x for k in range(5) for x in json.load(open(f"{F}dok5_f{k}.json"))["rows"] if x["kind"] == "runsten" and x["gold_word"]]
gr = json.load(open(CAL))["gap_recal"]
dat = json.load(open("utdata/runlm_forfining/datering_tm14.json"))
out = {"inside_word": np.mean([x["word_ok"] for x in inside]), "whole_word": np.mean([x["word_ok"] for x in whole]),
       "sure_right": np.mean(sure), "rundata_sure": np.mean(gsure),
       "documented_right": np.mean([x["word_ok"] for x in dok]), "documented_sure": gr["documented"]["sure_cv"][1]}
print({k: round(float(v), 3) for k, v in out.items()})
print("antal:", {"inne i ord": len(inside), "helt ord": len(whole), "≥95 % i maskeringen": len(sure), "≥95 % i gapprovet": len(gsure),
                 "dokumenterade": len(dok), "dokumenterade ≥95 %": gr["documented"]["sure_cv"][0]})
print("datering (runstenar):", {k: v.get("by_object", {}).get("runsten") for k, v in dat.items() if isinstance(v, dict) and "by_object" in v})
