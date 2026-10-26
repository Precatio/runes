"""Stilgruppernas mörkertal: fördjupningen bakom den fristående artikeln. Bygger på stilgrupper.py (samma
definitioner: vikingatida, stilgrupp = Rundatas stilfält annat än "?", runsten = Rundatas runsten/fragment) och
lägger till det artikeln behöver:

  rak_of_styled      RAK:s andel av de stilsatta runstenarna per region – där RAK läses som datering blir hela
                     bestånd tidiga per definition.
  signing            signering i en 2×2 (stilgrupp × skada) på svenska runstenar: de ostilsatta signerar som den
                     tidigaste gruppen, men skadan måste hållas isär – en skadad sten kan ha förlorat både
                     ornamentiken och signaturen.
  expected_signing   väntad signeringsandel bland de ostilsatta om de hade samma stilblandning som de stilsatta,
                     mot den observerade (binomial p, exakt).
  seriation          hur många Upplandsstenar utan stilgrupp som ändå får en tidsplacering av seriationen
                     (R-korpusen), med valideringens rho och medelfel.
  dating_model       textmodellens dateringsprov (korsvaliderat; src/textmodel.VALIDATION).
Skriver morkertal.json.
    PYTHONPATH=. .venv/bin/python utdata/sprakprov/morkertal.py"""
import csv
import glob
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
import re  # noqa: E402

from scipy import stats  # noqa: E402

from src import runlm as rl  # noqa: E402
import src.textmodel as tm  # noqa: E402

SWEDEN = {"U", "Sö", "Ög", "Vg", "Sm", "Öl", "G", "Nä", "Vs", "Gs", "Hs", "M", "J", "Bo", "D", "Hä", "Ån", "Vr", "Hl",
          "Bl", "Sk", "Ds", "Lp", "Me"}


def has_style(r):
    return (r.get("style") or "").strip() not in ("", "?")


def kind(r):
    if "runsten" in (r.get("object") or "").lower():
        return "runsten"
    return "annan sten" if r.get("material_type") == "sten" else "lösa föremål"


def lost(r):
    return bool(re.search(r"[?-]|\.\.\.", rl.clean_translit(r["transliteration"]).replace("§", "")))


def signed(r):
    return any(c.get("kind") == "S" for c in (r.get("carvers") or []))


def style_code(r):
    return re.sub(r"[?]", "", (r.get("style") or "").strip())


recs = rl.load_rundata()
V = [r for r in recs if rl.viking(r) and r.get("transliteration")]
prefix = lambda r: r["signum"].split()[0]  # noqa: E731
stones = [r for r in V if kind(r) == "runsten"]
se = [r for r in stones if prefix(r) in SWEDEN]

base = json.load(open(os.path.join(HERE, "stilgrupper.json")))

# --- RAK among the styled, per region ---------------------------------------------------------------------------
rak_of_styled = {}
for p in ("U", "Sö", "Vg", "Sm", "DR", "N"):
    grp = [r for r in stones if prefix(r) == p and has_style(r)]
    rak_of_styled[p] = {"styled": len(grp), "rak": sum((r.get("style") or "").strip() == "RAK" for r in grp),
                        "n_all": sum(1 for r in stones if prefix(r) == p)}

# --- signing in a 2x2: style x damage (Swedish runestones) ------------------------------------------------------
cell = {}
for st in (True, False):
    for dm in (True, False):
        grp = [r for r in se if has_style(r) == st and lost(r) == dm]
        cell[f"{'stil' if st else 'ostil'}_{'skadad' if dm else 'hel'}"] = \
            {"n": len(grp), "signed": sum(map(signed, grp))}

# the honest comparison: whole stones only – a damaged stone can have lost both its ornament and its signature
a = cell["stil_hel"]
b = cell["ostil_hel"]
p_whole = stats.fisher_exact([[a["signed"], a["n"] - a["signed"]], [b["signed"], b["n"] - b["signed"]]])[1]

# expected signing among unstyled whole stones if they had the styled whole stones' style mix
styled_whole = [r for r in se if has_style(r) and not lost(r)]
mix = Counter(style_code(r) for r in styled_whole)
rate = {s: sum(signed(r) for r in styled_whole if style_code(r) == s) / n for s, n in mix.items()}
exp_rate = sum(mix[s] / len(styled_whole) * rate[s] for s in mix)
n_uw, k_uw = b["n"], b["signed"]
p_binom = stats.binomtest(k_uw, n_uw, exp_rate, alternative="less").pvalue

# --- the seriation lamp: unstyled Uppland runestones that still get a time estimate -----------------------------
corp = max(glob.glob(os.path.join(ROOT, "data", "cache", "r", "corpus", "*")), key=os.path.getmtime)
chron = json.load(open(os.path.join(corp, "chronology.json")))
ser_rows = list(csv.DictReader(open(os.path.join(corp, "chronology_stones.csv"))))
ser_unstyled = [x for x in ser_rows if x.get("dated_by_style") in ("FALSE", "False", "0", "false")]
u_unstyled_total = sum(1 for r in stones if prefix(r) == "U" and not has_style(r))

out = {
    "base": base,  # the published coverage numbers (stilgrupper.py), reused unchanged
    "rak_of_styled": rak_of_styled,
    "signing_cells": cell,
    "signing": {"styled_whole": a, "unstyled_whole": b, "p_fisher_whole": float(p_whole),
                "expected_rate_unstyled": float(exp_rate), "p_binom_vs_mix": float(p_binom),
                "rate_by_style_whole": {s: {"n": mix[s], "rate": round(rate[s], 4)} for s in sorted(mix, key=lambda s: -mix[s])}},
    "seriation": {"validation": chron.get("validation"), "n_scored": len(ser_rows),
                  "n_unstyled_scored": len(ser_unstyled), "u_unstyled_total": u_unstyled_total},
    "dating_model": {"epoch": tm.VALIDATION["dating_epoch"], "near": tm.VALIDATION["dating_near"]},
    "style_damage_p": float(stats.fisher_exact(
        [[base["se_runestones_whole"]["with_style"], base["se_runestones_whole"]["n"] - base["se_runestones_whole"]["with_style"]],
         [base["se_runestones_lost"]["with_style"], base["se_runestones_lost"]["n"] - base["se_runestones_lost"]["with_style"]]])[1]),
    "uncertain_styles": sum(1 for r in stones if "?" in (r.get("style") or "") and has_style(r)),
}
json.dump(out, open(os.path.join(HERE, "morkertal.json"), "w"), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in out.items() if k != "base"}, ensure_ascii=False, indent=1))
