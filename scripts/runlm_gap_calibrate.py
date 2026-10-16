"""Kalibrering av ordet i en lucka, per ordklass. Modellens sannolikhet för ordet i en lucka stämmer för formelord men
är för hög för andra ord och namn: på luckor som Rundatas utgivare har fyllt hade modellen rätt i 53 procent av
andra ord när den sa 80–95 procent, och i 88 procent av namnen när den sa minst 95.

Klassen är modellens eget ord: formelord (de 50 vanligaste orden i normaliseringarna), namn (§ hos modellen eller
skrivet som namn i Rundata) och andra ord (src/textmodel.gap_class).
P(rätt) = sigmoid(a_klass + b_klass·logit(p) + c·log(förlorade runor)), skattad på luckrapportens återställda luckor
(utdata/Malt/runlm_luckor.json, scripts/runlm_gaps.py) och prövad med femdelad korsvalidering där hela stenar hålls
utanför. Koefficienterna skrivs till data/runlm_calibration.json under gap_recal.

    .venv/bin/python -m scripts.runlm_gap_calibrate [luckrapportens rader.json]
"""
from __future__ import annotations

import json
import math
import os
import re
import sys
import zlib
from collections import Counter

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import runlm as rl  # noqa: E402
from src.textmodel import gap_class, name_keys  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAL = os.path.join(ROOT, "data", "runlm_calibration.json")
CLASSES = ["formelord", "andra ord", "namn"]


def top_words(recs, n=50) -> set[str]:
    """The n most common words (by key) in the normalizations: the formula words."""
    freq = Counter(rl.key(rl.normtok(b)) for r in recs if rl.viking(r) and r.get("normalization")
                   for _, p in rl.sections(r["normalization"]) for b in rl.norm_words(p))
    return {k for k, _ in freq.most_common(n)}


def features(p: float, cls: int, n_lost: int) -> list[float]:
    p = min(max(p, 1e-4), 1 - 1e-4)
    oh = [1.0 if cls == k else 0.0 for k in range(3)]
    return oh + [o * math.log(p / (1 - p)) for o in oh] + [math.log(max(1, n_lost))]


def fit(X, y, l2=1.0, iters=50):
    w = np.zeros(X.shape[1])
    for _ in range(iters):
        q = 1 / (1 + np.exp(-(X @ w)))
        g = X.T @ (q - y) + l2 * w
        H = (X.T * (q * (1 - q))) @ X + l2 * np.eye(X.shape[1])
        w -= np.linalg.solve(H, g)
    return w


def ece(q, y, bins=((0, .5), (.5, .8), (.8, .95), (.95, 1.01))):
    return sum(abs(q[m].mean() - y[m].mean()) * m.sum() for lo, hi in bins
               for m in [(q >= lo) & (q < hi)] if m.any()) / len(y)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    path = argv[0] if argv else os.path.join(ROOT, "utdata", "Malt", "runlm_luckor.json")
    recs = {r["signum"]: r for r in rl.load_rundata()}

    def interpreted(sig):
        n = re.sub(r"<[^>]*>", " ", recs[sig].get("normalization") or "") if sig in recs else ""
        return sum(1 for _, p in rl.sections(n) for w in rl.norm_words(p) if not w.startswith("...")) >= 2

    known = lambda x: bool(x["word"]) and x["word"] != "<unk>"  # noqa: E731
    agree = lambda x: bool(x["agrees"]) or rl.same_word(x["word"].lstrip("§"), x["rundata"])  # noqa: E731
    val = [x for x in json.load(open(path))["rows"]
           if interpreted(x["sig"]) and x["status"] == "återställt" and known(x)]
    top = top_words(recs.values())
    names = name_keys(recs.values())
    X = np.array([features(x["p"], gap_class(x["word"], top, names), len(x["fill"])) for x in val])
    y = np.array([1.0 if agree(x) else 0.0 for x in val])
    fold = np.array([zlib.crc32(x["sig"].encode()) % 5 for x in val])
    pred = np.zeros(len(y))
    for k in range(5):
        w = fit(X[fold != k], y[fold != k])
        pred[fold == k] = 1 / (1 + np.exp(-(X[fold == k] @ w)))
    raw = np.array([x["p"] for x in val])
    cls = np.array([gap_class(x["word"], top, names) for x in val])
    by_class = {}
    for k, name in enumerate(CLASSES):
        m = cls == k
        sure_raw, sure_cal = m & (raw >= 0.95), m & (pred >= 0.95)
        by_class[name] = {"n": int(m.sum()), "right": round(float(y[m].mean()), 3),
                          "sure_raw": [int(sure_raw.sum()), round(float(y[sure_raw].mean()), 3) if sure_raw.any() else None],
                          "sure_calibrated": [int(sure_cal.sum()), round(float(y[sure_cal].mean()), 3) if sure_cal.any() else None]}
    w = fit(X, y)
    out = {"B": [round(float(v), 4) for v in w], "top50": sorted(top), "n": len(val),
           "ece_raw": round(float(ece(raw, y)), 4), "ece_cv": round(float(ece(pred, y)), 4),
           "brier_raw": round(float(np.mean((raw - y) ** 2)), 4), "brier_cv": round(float(np.mean((pred - y) ** 2)), 4),
           "by_class": by_class, "source": os.path.relpath(path, ROOT),
           "note": "Ordet i en lucka, kalibrerat per ordklass (scripts/runlm_gap_calibrate.py)."}
    cal = json.load(open(CAL)) if os.path.exists(CAL) else {}
    cal["gap_recal"] = out
    with open(CAL, "w", encoding="utf-8") as fh:
        json.dump(cal, fh, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "top50"}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
