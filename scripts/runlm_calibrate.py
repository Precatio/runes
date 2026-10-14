"""Kalibrering av runavkodaren (src/runlm.py): hur ofta har modellen rätt när den säger att ett ord har sannolikheten p?
Inskrifterna delas i fem delar; modellen tränas på fyra och prövas på den femte, på de huggna grupperna (stenens egna
skiljetecken, inga ordgränser från Rundata). Facit är Rundatas normalisering. Maltstenen är aldrig med i träningen.
Skriver malt_avkod_kalibrering.json.
    .venv/bin/python -m scripts.runlm_calibrate [grid | lam_unk lam_edda]"""
import json
import math
import os
import random
import sys
from collections import Counter

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.runlm import (Model, carved_groups, decode, edda_tokens, is_runes, key, load_rundata, norm_words, normtok,  # noqa: E402
                       pairs, runekey, sections, translit_words, viking)

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "utdata", "Malt")
MALT = "DR NOR1988;5"
RECS = load_rundata()
V = [r for r in RECS if viking(r) and r.get("transliteration") and r.get("normalization") and r["signum"] != MALT]
ET = edda_tokens()


def gold(r):
    """(carved groups, gold words [(start, end, normalized)]) when Rundata's words cover the carved text exactly."""
    T = sections(r["transliteration"]); N = dict(sections(r["normalization"]))
    if any(lab not in N for lab, _ in T):
        return None
    ws = []
    for lab, t in T:
        a, b = translit_words(t), norm_words(N[lab])
        if len(a) != len(b):
            return None
        ws.extend((runekey(x), normtok(y)) for x, y in zip(a, b))
    if not ws or not all(is_runes(x.lower()) for x, _ in ws):
        return None
    groups = [runekey(g) for g in carved_groups(r["transliteration"])]
    if "".join(groups) != "".join(x for x, _ in ws):
        return None
    out, pos = [], 0
    for x, y in ws:
        out.append((pos, pos + len(x), y)); pos += len(x)
    return groups, out


cands = [(r, gold(r)) for r in V]
cands = [(r, g) for r, g in cands if g and len(g[1]) >= 4]
random.Random(2026).shuffle(cands)
K = 5
GRID = len(sys.argv) > 1 and sys.argv[1] == "grid"
lam_unk = float(sys.argv[1]) if len(sys.argv) > 1 and not GRID else 0.01
lam_edda = float(sys.argv[2]) if len(sys.argv) > 2 else 0.03
print("prövbara inskrifter:", len(cands), "| lam_unk", lam_unk, "lam_edda", lam_edda)


def run(lam_unk, lam_edda, folds=range(K)):
    """Out-of-fold predictions: one row per word on the best path, and one per word in the key."""
    rows, gold_rows = [], []
    for k in folds:
        test = cands[k::K]
        tset = {r["signum"] for r, _ in test}
        m = Model([r for r in V if r["signum"] not in tset], edda_tokens=ET, lam_unk=lam_unk, lam_edda=lam_edda)
        freq = Counter(normtok(b) for r in V if r["signum"] not in tset for _, p in sections(r["normalization"]) for b in norm_words(p))
        fk = Counter()
        for w_, c_ in freq.items():
            fk[key(w_)] += c_  # how common the word is, over all its normalized forms
        for r, (groups, gw) in test:
            logZ, path, post, text = decode(m, groups)
            G = {(i, j): w for i, j, w in gw}
            P = {(i, j): (w, p) for i, j, w, p in path}
            for i, j, w, p in path:
                g = G.get((i, j))
                ps = m.index.get(text[i:j], {}).get(w, 0.0)
                rows.append({"p": p, "lch": math.log(max(ps, 1e-12)) if w != "<unk>" else 0.0, "ok": g is not None and g == w,
                             "same": g is not None and w != "<unk>" and key(g) == key(w), "span": g is not None, "unk": w == "<unk>", "freq": fk[key(w)] if w != "<unk>" else 0,
                             "edda": w != "<unk>" and fk[key(w)] == 0, "len": j - i, "sig": r["signum"], "fold": k})
            for i, j, w in gw:
                pw = P.get((i, j))
                gold_rows.append({"ok": pw is not None and pw[0] == w, "same": pw is not None and pw[0] != "<unk>" and key(pw[0]) == key(w),
                                  "span": pw is not None, "seen": freq[w] > 0, "unk_pred": pw is not None and pw[0] == "<unk>"})
    return rows, gold_rows


acc = lambda xs, k="ok": sum(x[k] for x in xs) / max(1, len(xs))
if GRID:
    for lu in (0.003, 0.01, 0.03):
        for le in (0.0, 0.03, 0.1):
            rows, gold_rows = run(lu, le, folds=[0, 1])
            print(f"lam_unk {lu} lam_edda {le}: exakt {acc(gold_rows):.3f} samma ord {acc(gold_rows, 'same'):.3f} gräns {acc(gold_rows, 'span'):.3f}")
    sys.exit()

rows, gold_rows = run(lam_unk, lam_edda)
seen = [g for g in gold_rows if g["seen"]]
unseen = [g for g in gold_rows if not g["seen"]]
print(f"ord i facit: {len(gold_rows)}; exakt {acc(gold_rows):.1%}; samma ord {acc(gold_rows, 'same'):.1%}; rätt gräns {acc(gold_rows, 'span'):.1%}")
print(f"  kända ord: samma ord {acc(seen, 'same'):.1%} (n={len(seen)}); okända ord: rätt gräns {acc(unseen, 'span'):.1%}, märkta okända {acc(unseen, 'unk_pred'):.1%} (n={len(unseen)})")

# Recalibration: logistic regression of "same word" on the raw posterior, how common the word is, whether it is known
# only from the Edda, its length and how probable its spelling is – fitted on four folds of predictions, tested on the fifth.
W = [x for x in rows if not x["unk"]]


def feats(x):
    p = min(max(x["p"], 1e-4), 1 - 1e-4)
    return [1.0, math.log(p / (1 - p)), math.log1p(x["freq"]), float(x["edda"]), math.log(x["len"]), max(x["lch"], -12.0)]


def fit(xs):
    X = np.array([feats(x) for x in xs]); y = np.array([x["same"] for x in xs], float)
    b = np.zeros(X.shape[1])
    for _ in range(50):
        mu = 1 / (1 + np.exp(-(X @ b))); Wt = mu * (1 - mu) + 1e-9
        b = b + np.linalg.solve(X.T @ (X * Wt[:, None]) + 1e-6 * np.eye(len(b)), X.T @ (y - mu))
    return b


for k in range(K):
    b = fit([x for x in W if x["fold"] != k])
    for x in W:
        if x["fold"] == k:
            x["pc"] = float(1 / (1 + math.exp(-np.dot(feats(x), b))))
B = fit(W)
bins = [0, 0.2, 0.4, 0.6, 0.8, 0.9, 1.01]
cal = []
for lo, hi in zip(bins, bins[1:]):
    raw = [x for x in W if lo <= x["p"] < hi]
    cc = [x for x in W if lo <= x["pc"] < hi]
    rare_cc = [x for x in cc if x["freq"] <= 2]
    cal.append({"lo": lo, "hi": min(hi, 1), "raw_n": len(raw), "raw_p": float(np.mean([x["p"] for x in raw])) if raw else None, "raw_acc": acc(raw, "same"),
                "n": len(cc), "p": float(np.mean([x["pc"] for x in cc])) if cc else None, "acc": acc(cc, "same"),
                "n_rare": len(rare_cc), "p_rare": float(np.mean([x["pc"] for x in rare_cc])) if rare_cc else None, "acc_rare": acc(rare_cc, "same")})
    c = cal[-1]
    print(f"  {lo:.1f}–{min(hi,1):.1f} | rå: n={c['raw_n']:5d} p={c['raw_p'] or 0:.2f} rätt={c['raw_acc']:.2f} | kalibrerad: n={c['n']:5d} p={c['p'] or 0:.2f} rätt={c['acc']:.2f} | sällsynta: n={c['n_rare']:4d} p={c['p_rare'] or 0:.2f} rätt={c['acc_rare']:.2f}")
ece_raw = sum(c["raw_n"] * abs((c["raw_p"] or 0) - c["raw_acc"]) for c in cal) / len(W)
ece = sum(c["n"] * abs((c["p"] or 0) - c["acc"]) for c in cal) / len(W)
rare = [x for x in W if x["freq"] <= 2]
print(f"kalibreringsfel: rå {ece_raw:.3f}, kalibrerad {ece:.3f}; koefficienter {np.round(B, 3).tolist()}")
unk = [x for x in rows if x["unk"]]
print(f"märkta okända: {len(unk)}; av dem rätt gräns {acc(unk, 'span'):.1%}")
json.dump({"lam_unk": lam_unk, "lam_edda": lam_edda, "n_inscriptions": len(cands), "n_gold": len(gold_rows), "exact": acc(gold_rows),
           "same": acc(gold_rows, "same"), "span": acc(gold_rows, "span"), "same_seen": acc(seen, "same"), "n_unseen": len(unseen),
           "unseen_span": acc(unseen, "span"), "unseen_marked_unk": acc(unseen, "unk_pred"), "cal": cal, "ece_raw": ece_raw, "ece": ece,
           "recal": B.tolist(), "n_unk": len(unk), "unk_span": acc(unk, "span"), "n_pred": len(W),
           "rare_n": len(rare), "rare_acc": acc(rare, "same"), "rare_mean_pc": float(np.mean([x["pc"] for x in rare]))},
          open(os.path.join(OUT, "malt_avkod_kalibrering.json"), "w"), indent=1)
