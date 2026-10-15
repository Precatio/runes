"""Prov och kalibrering av runavkodaren (src/runlm.py): hur ofta har modellen rätt när den säger att ett ord har
sannolikheten p? Inskrifterna delas i fem delar; modellen tränas på fyra och prövas på den femte, på de huggna
grupperna (stenens egna skiljetecken, inga ordgränser från Rundata). Facit är Rundatas normalisering. Maltstenen är
aldrig med i träningen. Provstenarna och delningen är desamma i alla varianter, så att varianterna kan jämföras.

Varianter (steg 2 och 3):
  --aligned        fler ordpar: också avsnitt där ordantalen skiljer sig (skadade och återställda ord)
  --contexts       stavning efter era, epok, trakt, landskap och ristare, och ordföljd efter epok
  --epoch known    provstenens epok tas ur Rundatas datering eller stil (okänd epok: hela vikingatiden)
  --epoch inferred epoken gissas ur texten (alla fyra epokerna vägs); dateringen prövas mot Rundatas
  --medieval       medeltida inskrifter som extra stavningsdata
  --adapt BETA     stenens egen stavning skattas ur en första läsning (styrka BETA mot sammanhanget)
Skriver --out (förval utdata/Malt/malt_avkod_kalibrering.json) med inställningarna, så att scripts/malt_decode.py
kan läsa Maltstenen med samma modell.
    .venv/bin/python -m scripts.runlm_calibrate [--aligned] [--contexts --epoch inferred] [--folds 0 1] [--out FIL]"""
import argparse
import json
import math
import os
import random
import sys
import time
from collections import Counter

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.runlm import (EPOCHS, Model, adapt_counts, carved_groups, context, decode, decode_epochs, edda_tokens,  # noqa: E402
                       epoch, is_runes, key, load_rundata, norm_words, normtok, runekey, sections, translit_words, viking)

ap = argparse.ArgumentParser()
ap.add_argument("--aligned", action="store_true")
ap.add_argument("--contexts", action="store_true")
ap.add_argument("--epoch", choices=("none", "known", "inferred"), default="none")
ap.add_argument("--medieval", action="store_true")
ap.add_argument("--adapt", type=float, default=0.0)
ap.add_argument("--alpha", type=float, default=20.0)
ap.add_argument("--kappa_e", type=float, default=5.0)
ap.add_argument("--lm_beta", type=float, default=0.0)
ap.add_argument("--lam_name", type=float, default=0.0, help="vikt för namn som modellen sätter ihop av namnled (0 = av)")
ap.add_argument("--lam_unk", type=float, default=0.01)
ap.add_argument("--lam_edda", type=float, default=0.03)
ap.add_argument("--levels", type=int, default=5, help="nivåer i stavningsträdet: 1 era, 2 +fas, 3 +epok, 4 +trakt, 5 +landskap, 6 +ristare")
ap.add_argument("--epoch_lm", type=int, default=1, help="ordföljd efter epok (1) eller bara hela vikingatiden (0)")
ap.add_argument("--folds", type=int, nargs="*", default=None)
ap.add_argument("--out", default=None)
args = ap.parse_args()

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "utdata", "Malt")
MALT = "DR NOR1988;5"
RECS = load_rundata()
V = [r for r in RECS if viking(r) and r.get("transliteration") and r.get("normalization") and r["signum"] != MALT]
MED = ([r for r in RECS if (r.get("period") or "").startswith("M") and r.get("transliteration") and r.get("normalization")]
       if args.medieval else [])
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
folds = args.folds if args.folds is not None else list(range(K))
print("prövbara inskrifter:", len(cands), "| inställningar:", vars(args), flush=True)

rows, gold_rows, dating = [], [], []
t0 = time.time()
for k in folds:
    test = cands[k::K]
    tset = {r["signum"] for r, _ in test}
    m = Model([r for r in V if r["signum"] not in tset], edda_tokens=ET, lam_unk=args.lam_unk, lam_edda=args.lam_edda,
              aligned=args.aligned, contexts=args.contexts, alpha=args.alpha, kappa_e=args.kappa_e, lm_beta=args.lm_beta,
              spelling_recs=MED, lam_name=args.lam_name)
    m.use_epoch_lm = bool(args.epoch_lm)
    freq = Counter(normtok(b) for r in V if r["signum"] not in tset for _, p in sections(r["normalization"]) for b in norm_words(p))
    fk = Counter()
    for w_, c_ in freq.items():
        fk[key(w_)] += c_  # how common the word is, over all its normalized forms
    for r, (groups, gw) in test:
        if args.contexts and args.epoch == "inferred":
            logZ, path, post, text, ep_post, _ = decode_epochs(m, groups, path=context(r)[:args.levels], adapt=args.adapt)
            if epoch(r) in EPOCHS:
                dating.append({"sig": r["signum"], "true": epoch(r), "post": ep_post})
        elif args.contexts:
            # a known epoch puts the stone in its branch of the tree; otherwise only the era is used
            ctx = m.ctx(context(r)[:args.levels] if (args.epoch == "known" and epoch(r) in EPOCHS) else context(r)[:1])
            logZ, path, post, text = decode(m, groups, ctx=ctx)
            if args.adapt:
                ctx = m.adapt(ctx, adapt_counts(m, post, text, ctx), args.adapt)
                logZ, path, post, text = decode(m, groups, ctx=ctx)
        else:
            logZ, path, post, text = decode(m, groups)
        G = {(i, j): w for i, j, w in gw}
        P = {(i, j): (w, p) for i, j, w, p in path}
        for i, j, w, p in path:
            g = G.get((i, j))
            ps = m.index.get(text[i:j], {}).get(w, 0.0)
            rows.append({"p": p, "lch": math.log(max(ps, 1e-12)) if w != "<unk>" else 0.0, "ok": g is not None and g == w,
                         "same": g is not None and w != "<unk>" and key(g) == key(w), "span": g is not None, "unk": w == "<unk>",
                         "freq": fk[key(w)] if w != "<unk>" else 0, "edda": w != "<unk>" and fk[key(w)] == 0, "len": j - i,
                         "sig": r["signum"], "fold": k})
        for i, j, w in gw:
            pw = P.get((i, j))
            gold_rows.append({"ok": pw is not None and pw[0] == w, "same": pw is not None and pw[0] != "<unk>" and key(pw[0]) == key(w),
                              "span": pw is not None, "seen": freq[w] > 0, "unk_pred": pw is not None and pw[0] == "<unk>",
                              "epoch": epoch(r), "sig": r["signum"]})
    print(f"del {k + 1} klar efter {time.time() - t0:.0f} s; ordpar i träningen {m.n_pairs} från {m.n_pair_inscriptions} inskrifter", flush=True)

acc = lambda xs, k="ok": sum(x[k] for x in xs) / max(1, len(xs))
seen = [g for g in gold_rows if g["seen"]]
unseen = [g for g in gold_rows if not g["seen"]]
by_epoch = {str(e): {"n": len([g for g in gold_rows if g["epoch"] == e]), "same": acc([g for g in gold_rows if g["epoch"] == e], "same")}
            for e in list(EPOCHS) + [None]}
print(f"ord i facit: {len(gold_rows)}; exakt {acc(gold_rows):.1%}; samma ord {acc(gold_rows, 'same'):.1%}; rätt gräns {acc(gold_rows, 'span'):.1%}")
print(f"  kända ord: samma ord {acc(seen, 'same'):.1%} (n={len(seen)}); okända ord: rätt gräns {acc(unseen, 'span'):.1%} (n={len(unseen)})")
print("  per epok:", {e: f"{v['same']:.1%} (n={v['n']})" for e, v in by_epoch.items()})

dating_out = None
if dating:
    pick = lambda d: max(d["post"], key=d["post"].get)
    right = sum(pick(d) == d["true"] for d in dating)
    conf = {t: dict(Counter(pick(d) for d in dating if d["true"] == t)) for t in EPOCHS}
    ll = -sum(math.log(max(d["post"][d["true"]], 1e-12)) for d in dating) / len(dating)
    base = Counter(d["true"] for d in dating).most_common(1)[0][1] / len(dating)
    near = sum(abs(EPOCHS.index(pick(d)) - EPOCHS.index(d["true"])) <= 1 for d in dating)
    dating_out = {"n": len(dating), "right": right / len(dating), "within_one": near / len(dating), "majority_baseline": base,
                  "logloss": ll, "confusion": conf}
    print(f"datering ur texten: rätt epok {right / len(dating):.1%} av {len(dating)} (största klassen ger {base:.1%}); "
          f"högst en epok fel {near / len(dating):.1%}; förväxlingar {conf}")

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


fl = sorted({x["fold"] for x in W})
for k in fl:
    b = fit([x for x in W if x["fold"] != k]) if len(fl) > 1 else fit(W)
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
    cal.append({"lo": lo, "hi": min(hi, 1), "raw_n": len(raw), "raw_p": float(np.mean([x["p"] for x in raw])) if raw else None,
                "raw_acc": acc(raw, "same"), "n": len(cc), "p": float(np.mean([x["pc"] for x in cc])) if cc else None,
                "acc": acc(cc, "same"), "n_rare": len(rare_cc), "p_rare": float(np.mean([x["pc"] for x in rare_cc])) if rare_cc else None,
                "acc_rare": acc(rare_cc, "same")})
    c = cal[-1]
    print(f"  {lo:.1f}–{min(hi,1):.1f} | rå: n={c['raw_n']:5d} p={c['raw_p'] or 0:.2f} rätt={c['raw_acc']:.2f} | kalibrerad: n={c['n']:5d} "
          f"p={c['p'] or 0:.2f} rätt={c['acc']:.2f} | sällsynta: n={c['n_rare']:4d} p={c['p_rare'] or 0:.2f} rätt={c['acc_rare']:.2f}")
ece_raw = sum(c["raw_n"] * abs((c["raw_p"] or 0) - c["raw_acc"]) for c in cal) / len(W)
ece = sum(c["n"] * abs((c["p"] or 0) - c["acc"]) for c in cal) / len(W)
rare = [x for x in W if x["freq"] <= 2]
print(f"kalibreringsfel: rå {ece_raw:.3f}, kalibrerad {ece:.3f}; koefficienter {np.round(B, 3).tolist()}")
unk = [x for x in rows if x["unk"]]
print(f"märkta okända: {len(unk)}; av dem rätt gräns {acc(unk, 'span'):.1%}; tid {time.time() - t0:.0f} s")
config = {"aligned": args.aligned, "contexts": args.contexts, "epoch": args.epoch, "medieval": args.medieval, "adapt": args.adapt,
          "alpha": args.alpha, "kappa_e": args.kappa_e, "lm_beta": args.lm_beta, "levels": args.levels, "epoch_lm": args.epoch_lm,
          "lam_name": args.lam_name}
json.dump({"config": config, "folds": folds, "lam_unk": args.lam_unk, "lam_edda": args.lam_edda, "n_inscriptions": len(cands),
           "n_gold": len(gold_rows), "exact": acc(gold_rows), "same": acc(gold_rows, "same"), "span": acc(gold_rows, "span"),
           "same_seen": acc(seen, "same"), "n_unseen": len(unseen), "unseen_span": acc(unseen, "span"),
           "unseen_marked_unk": acc(unseen, "unk_pred"), "by_epoch": by_epoch, "dating": dating_out,
           "per_word": [(g["sig"], g["same"], g["span"]) for g in gold_rows],
           "cal": cal, "ece_raw": ece_raw, "ece": ece, "recal": B.tolist(), "n_unk": len(unk), "unk_span": acc(unk, "span"),
           "n_pred": len(W), "rare_n": len(rare), "rare_acc": acc(rare, "same"),
           "rare_mean_pc": float(np.mean([x["pc"] for x in rare])) if rare else None, "seconds": time.time() - t0},
          open(args.out or os.path.join(OUT, "malt_avkod_kalibrering.json"), "w"), indent=1)
