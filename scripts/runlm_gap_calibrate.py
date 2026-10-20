"""Kalibrering av ordet i en lucka, per ordklass. Modellens sannolikhet för ordet i en lucka stämmer för formelord men
är för hög för andra ord och namn: på luckor som Rundatas utgivare har fyllt hade modellen rätt i 53 procent av
andra ord när den sa 80–95 procent, och i 88 procent av namnen när den sa minst 95.

Klassen är modellens eget ord: formelord (de 50 vanligaste orden i normaliseringarna), namn (§ hos modellen eller
skrivet som namn i Rundata) och andra ord (src/textmodel.gap_class).
P(rätt) = sigmoid(a_klass + b_klass·logit(p) + c·log(förlorade runor)), skattad på luckrapportens återställda luckor
(utdata/Malt/runlm_luckor.json, scripts/runlm_gaps.py) och prövad med femdelad korsvalidering där hela stenar hålls
utanför. Logistisk regression med scikit-learn; isoton regression per klass prövades och gav sämre
Brier-poäng och log-förlust. Koefficienterna skrivs till data/runlm_calibration.json under gap_recal.

Med --documented PREFIX (2026-10-17) skattas kalibreringen också på dokumenterade luckor (scripts/runlm_documented_test.py:
runor i [ ], kända från äldre avbildningar). Utgivare fyller helst luckor där svaret är givet, så de återställda luckorna
ger för höga procent på luckor som fallit bort av fysiska skäl – som appens. Båda slagen skattas tillsammans, med en
extra konstant för de dokumenterade; konstanten läggs till klassernas konstanter i gap_recal, så att appens procent
gäller luckor av det dokumenterade slaget. Korsvalideringen redovisas på de dokumenterade luckorna, runstenar för sig.

    .venv/bin/python -m scripts.runlm_gap_calibrate [luckrapportens rader.json] [--documented PREFIX] [--composed]
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
# RUNLM_CALIBRATION: en annan kalibreringsfil (valideringståg som inte ska röra den levande appens)
CAL = os.environ.get("RUNLM_CALIBRATION") or os.path.join(ROOT, "data", "runlm_calibration.json")
CLASSES = ["formelord", "andra ord", "namn"]


def top_words(recs, n=50) -> set[str]:
    """The n most common words (by key) in the normalizations: the formula words."""
    freq = Counter(rl.key(rl.normtok(b)) for r in recs if rl.viking(r) and r.get("normalization")
                   for _, p in rl.sections(r["normalization"]) for b in rl.norm_words(p))
    return {k for k, _ in freq.most_common(n)}


def features(p: float, cls: int, n_lost: int, K: int = 3, whole=None) -> list[float]:
    """Class constants, class slopes on logit(p), log(lost runes) and, when whole is not None, whether the gap is a
    whole word (src/textmodel.calibrate_gap)."""
    p = min(max(p, 1e-4), 1 - 1e-4)
    oh = [1.0 if cls == k else 0.0 for k in range(K)]
    return oh + [o * math.log(p / (1 - p)) for o in oh] + [math.log(max(1, n_lost))] + ([] if whole is None else [1.0 if whole else 0.0])


def fit(X, y, l2=1.0):
    """Logistic regression with an L2 penalty (scikit-learn); the class columns stand for the intercepts."""
    from sklearn.linear_model import LogisticRegression
    return LogisticRegression(fit_intercept=False, C=1.0 / l2, max_iter=1000).fit(X, y).coef_[0]


def ece(q, y, bins=((0, .5), (.5, .8), (.8, .95), (.95, 1.01))):
    return sum(abs(q[m].mean() - y[m].mean()) * m.sum() for lo, hi in bins
               for m in [(q >= lo) & (q < hi)] if m.any()) / len(y)


def documented_rows(prefix, top, names, K=3, whole=False):
    """The documented gaps (scripts/runlm_documented_test.py, prefix_f0.json …) with a word: features, right, stone, kind.
    They are all inside a word (whole=True adds the whole-word column, 0)."""
    rows = [x for k in range(5) if os.path.exists(f"{prefix}_f{k}.json") for x in json.load(open(f"{prefix}_f{k}.json"))["rows"]
            if x["gold_word"] and x["word"] and x["word"] != "<unk>"]
    X = np.array([features(x["p_model"], gap_class(x["word"], top, names, K > 3), x["lost"], K, False if whole else None) for x in rows])
    return X, np.array([float(x["word_ok"]) for x in rows]), [x["sig"] for x in rows], np.array([x["kind"] == "runsten" for x in rows])


def masked_rows(prefix, top, names, recs, K=3):
    """The masking test (scripts/runlm_restore_test.py, prefix_f0.json …): runes of a word hidden, inside the word or the
    whole word. Features (with the whole-word column), right, stone, runestone, whole."""
    rows = [x for k in range(5) if os.path.exists(f"{prefix}_f{k}.json") for x in json.load(open(f"{prefix}_f{k}.json"))["rows"]
            if x["word"] and x["word"] != "<unk>" and x["p_word"] > 0]
    wh = np.array([x["kind"] == "helt ord" for x in rows])
    X = np.array([features(x["p_word"], gap_class(x["word"], top, names, K > 3), x["n"], K, bool(w_)) for x, w_ in zip(rows, wh)])
    rs = np.array([rl.object_kind(recs[x["sig"]]) == "runsten" for x in rows])
    return X, np.array([float(x["word_ok"]) for x in rows]), [x["sig"] for x in rows], rs, wh


def _report(q, y, m):
    sure = m & (q >= 0.95)
    return {"n": int(m.sum()), "right": round(float(y[m].mean()), 3), "ece_cv": round(float(ece(q[m], y[m])), 4),
            "brier_cv": round(float(np.mean((q[m] - y[m]) ** 2)), 4),
            "sure_cv": [int(sure.sum()), round(float(y[sure].mean()), 3) if sure.any() else None]}


def pooled(X0, y0, f0, doc_prefix, mask_prefix, top, names, recs, K):
    """Restored, documented and masked gaps fitted together, each source with a constant of its own (masked and
    documented against the restored); the app uses the documented level, since its gaps are lost for physical reasons.
    The whole-word term is learned from the masked words. Cross-validated by stone on the documented and masked gaps.
    Returns (documented report, masked report, coefficients for the app)."""
    X1, y1, s1, rs1 = documented_rows(doc_prefix, top, names, K, whole=True)
    X2, y2, s2, rs2, wh2 = masked_rows(mask_prefix, top, names, recs, K)
    f1 = np.array([zlib.crc32(s_.encode()) % 5 for s_ in s1])
    f2 = np.array([zlib.crc32(s_.encode()) % 5 for s_ in s2])
    src = lambda n, a, b: np.hstack([np.full((n, 1), a), np.full((n, 1), b)])  # noqa: E731 – columns: masked, documented
    XA = np.vstack([np.hstack([X0, src(len(X0), 0, 0)]), np.hstack([X1, src(len(X1), 0, 1)]), np.hstack([X2, src(len(X2), 1, 0)])])
    yA, fA = np.concatenate([y0, y1, y2]), np.concatenate([f0, f1, f2])
    off1, off2 = len(X0), len(X0) + len(X1)
    sig = lambda z: 1 / (1 + np.exp(-z))  # noqa: E731
    p1, p2 = np.zeros(len(y1)), np.zeros(len(y2))
    for k in range(5):
        wk = fit(XA[fA != k], yA[fA != k])
        # both judged at the documented level, as the app is
        p1[f1 == k] = sig(np.hstack([X1[f1 == k], src(int((f1 == k).sum()), 0, 1)]) @ wk)
        p2[f2 == k] = sig(np.hstack([X2[f2 == k], src(int((f2 == k).sum()), 1, 0)]) @ wk)
    w = fit(XA, yA)
    app = np.concatenate([w[:K] + w[-1], w[K:-2]])  # the documented constant into the class constants
    doc = {**_report(p1, y1, rs1), "runestones_only": True, "constant": round(float(w[-1]), 4),
           "masked_constant": round(float(w[-2]), 4), "whole_word": round(float(w[-3]), 4), "source": doc_prefix}
    msk = {"inside_word": _report(p2, y2, rs2 & ~wh2), "whole_word": _report(p2, y2, rs2 & wh2), "source": mask_prefix,
           "note": "judged at the masked level, against the masked words' own answers"}
    return doc, msk, app


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    doc_prefix = mask_prefix = None
    if "--masked" in argv:  # --masked PREFIX: the masking test as a third source, with the whole-word term
        i = argv.index("--masked")
        mask_prefix = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    K = 4 if "--composed" in argv else 3  # --composed: the names composed of name elements (§) as a class of their own
    argv = [a for a in argv if a != "--composed"]
    if "--documented" in argv:
        i = argv.index("--documented")
        doc_prefix = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
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
    W = False if mask_prefix else None  # the restored gaps are never a whole word
    X = np.array([features(x["p"], gap_class(x["word"], top, names, K > 3), len(x["fill"]), K, W) for x in val])
    y = np.array([1.0 if agree(x) else 0.0 for x in val])
    fold = np.array([zlib.crc32(x["sig"].encode()) % 5 for x in val])
    pred = np.zeros(len(y))
    for k in range(5):
        w = fit(X[fold != k], y[fold != k])
        pred[fold == k] = 1 / (1 + np.exp(-(X[fold == k] @ w)))
    raw = np.array([x["p"] for x in val])
    cls = np.array([gap_class(x["word"], top, names, K > 3) for x in val])
    by_class = {}
    for k, name in enumerate(CLASSES + (["sammansatta namn"] if K > 3 else [])):
        m = cls == k
        sure_raw, sure_cal = m & (raw >= 0.95), m & (pred >= 0.95)
        by_class[name] = {"n": int(m.sum()), "right": round(float(y[m].mean()), 3),
                          "sure_raw": [int(sure_raw.sum()), round(float(y[sure_raw].mean()), 3) if sure_raw.any() else None],
                          "sure_calibrated": [int(sure_cal.sum()), round(float(y[sure_cal].mean()), 3) if sure_cal.any() else None]}
    w = fit(X, y)
    documented = masked = None
    if doc_prefix and mask_prefix:
        documented, masked, w = pooled(X, y, fold, doc_prefix, mask_prefix, top, names, recs, K)
    elif doc_prefix:
        X1, y1, sig1, rs1 = documented_rows(doc_prefix, top, names, K)
        f1 = np.array([zlib.crc32(s_.encode()) % 5 for s_ in sig1])
        pool = lambda Xa, Xb: np.vstack([np.hstack([Xa, np.zeros((len(Xa), 1))]), np.hstack([Xb, np.ones((len(Xb), 1))])])  # noqa: E731
        p1 = np.zeros(len(y1))
        for k in range(5):
            wk = fit(pool(X[fold != k], X1[f1 != k]), np.concatenate([y[fold != k], y1[f1 != k]]))
            p1[f1 == k] = 1 / (1 + np.exp(-(np.hstack([X1[f1 == k], np.ones((int((f1 == k).sum()), 1))]) @ wk)))
        old = 1 / (1 + np.exp(-(X1 @ w)))  # the restored gaps alone
        wd = fit(pool(X, X1), np.concatenate([y, y1]))
        w = np.concatenate([wd[:K] + wd[-1], wd[K:-1]])  # the documented constant into the class constants
        documented = {"n": len(y1), "runestones": int(rs1.sum()), "right": round(float(y1.mean()), 3), "constant": round(float(wd[-1]), 4),
                      "ece_restored_only": round(float(ece(old[rs1], y1[rs1])), 4), "ece_cv": round(float(ece(p1[rs1], y1[rs1])), 4),
                      "brier_restored_only": round(float(np.mean((old[rs1] - y1[rs1]) ** 2)), 4),
                      "brier_cv": round(float(np.mean((p1[rs1] - y1[rs1]) ** 2)), 4),
                      "sure_cv": [int((rs1 & (p1 >= 0.95)).sum()), round(float(y1[rs1 & (p1 >= 0.95)].mean()), 3) if (rs1 & (p1 >= 0.95)).any() else None],
                      "source": doc_prefix}
    out = {"B": [round(float(v), 4) for v in w], "top50": sorted(top), "n": len(val), "documented": documented, "masked": masked,
           "ece_raw": round(float(ece(raw, y)), 4), "ece_cv": round(float(ece(pred, y)), 4),
           "brier_raw": round(float(np.mean((raw - y) ** 2)), 4), "brier_cv": round(float(np.mean((pred - y) ** 2)), 4),
           "by_class": by_class, "source": os.path.relpath(path, ROOT),
           "note": "Ordet i en lucka, kalibrerat per ordklass (scripts/runlm_gap_calibrate.py)"
                   + ("; procenten gäller luckor av det dokumenterade slaget (documented)." if documented else ".")}
    cal = json.load(open(CAL)) if os.path.exists(CAL) else {}
    cal["gap_recal"] = out
    with open(CAL, "w", encoding="utf-8") as fh:
        json.dump(cal, fh, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "top50"}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
