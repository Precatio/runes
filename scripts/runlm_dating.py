"""Kan runavkodaren (src/runlm.py) datera en inskrift ur dess text? Varje daterad vikingatida inskrift läses med
modellen för var och en av de fyra epokerna (800-talet, 900-talet, 1000–1070, 1070–1150); den epok i vilken texten är
mest sannolik är modellens datering. Femfaldigt prov: modellen tränas på fyra delar och daterar den femte. Facit är
Rundatas datering eller, för svenska stenar, ornamentikens stilgrupp (src/runlm.py, epoch). Ristarens namn används
inte, eftersom det i sig avslöjar tiden; trakt och landskap används, eftersom de är kända för varje sten.
Med förhandschanser efter hur vanliga epokerna är i träningen och med lika förhandschanser.
Skriver utdata/Malt/runlm_datering.json.
    .venv/bin/python -m scripts.runlm_dating [--min_runes 10] [--alpha 20]"""
import argparse
import json
import math
import os
import random
import re
import sys
import time
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.runlm import by_object, print_by_object, EPOCHS, PHASE, RUNES, Model, carved_groups, context, edda_tokens, epoch, load_rundata, posteriors, runekey, viking  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--min_runes", type=int, default=10)
ap.add_argument("--alpha", type=float, default=20.0)
ap.add_argument("--kappa_e", type=float, default=5.0)
ap.add_argument("--lm_beta", type=float, default=0.0)
ap.add_argument("--lam_name", type=float, default=0.0)
ap.add_argument("--lam_class", type=float, default=0.0)
ap.add_argument("--folds", type=int, nargs="*", default=None)
ap.add_argument("--out", default=None)
args = ap.parse_args()

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MALT = "DR NOR1988;5"
RECS = load_rundata()
V = [r for r in RECS if viking(r) and r.get("transliteration") and r.get("normalization") and r["signum"] != MALT]
ET = edda_tokens()


def readable(r):
    """The carved groups with damaged or unread runes taken out (each gap is a boundary at no cost)."""
    groups, signs = [], []
    for g in carved_groups(r["transliteration"]):
        parts = [p for p in re.split(r"[^%s]+" % re.escape("".join(sorted(RUNES))), runekey(g)) if p]
        for k, p in enumerate(parts):
            groups.append(p)
            if k < len(parts) - 1:
                signs.append(len(groups) - 1)
    return groups, signs


tests = [r for r in V if epoch(r) in EPOCHS and sum(len(g) for g in readable(r)[0]) >= args.min_runes]
random.Random(2026).shuffle(tests)
K = 5
folds = args.folds if args.folds is not None else list(range(K))
print("daterade inskrifter att pröva:", len(tests), Counter(epoch(r) for r in tests), flush=True)

rows = []
t0 = time.time()
for k in folds:
    test = tests[k::K]
    tset = {r["signum"] for r in test}
    m = Model([r for r in V if r["signum"] not in tset], edda_tokens=ET, aligned=True, contexts=True, alpha=args.alpha,
              kappa_e=args.kappa_e, lm_beta=args.lm_beta, lam_name=args.lam_name, lam_class=args.lam_class)
    prior = {e: (m.epoch_prior[e] or 1) for e in EPOCHS}
    for r in test:
        groups, signs = readable(r)
        path = context(r)[:5]  # era, phase, epoch, area, region – not the carver
        ll = {e: posteriors(m, groups, signs, ctx=m.ctx((path[0], PHASE[e], e) + path[3:]))[0] for e in EPOCHS}
        rows.append({"sig": r["signum"], "true": epoch(r), "runes": sum(len(g) for g in groups), "ll": ll, "prior": prior})
    print(f"del {k + 1} klar efter {time.time() - t0:.0f} s", flush=True)


def posterior(ll, prior=None):
    v = {e: ll[e] + (math.log(prior[e] / sum(prior.values())) if prior else 0.0) for e in EPOCHS}
    mx = max(v.values())
    z = sum(math.exp(x - mx) for x in v.values())
    return {e: math.exp(x - mx) / z for e, x in v.items()}


out = {}
for name, use_prior in (("prior", True), ("uniform", False)):
    P = [(x, posterior(x["ll"], x["prior"] if use_prior else None)) for x in rows]
    pick = lambda p: max(p, key=p.get)
    right = sum(pick(p) == x["true"] for x, p in P)
    near = sum(abs(EPOCHS.index(pick(p)) - EPOCHS.index(x["true"])) <= 1 for x, p in P)
    conf = {t: dict(Counter(pick(p) for x, p in P if x["true"] == t)) for t in EPOCHS}
    per = {t: (sum(pick(p) == t for x, p in P if x["true"] == t), sum(1 for x, _ in P if x["true"] == t)) for t in EPOCHS}
    base = Counter(x["true"] for x in rows).most_common(1)[0][1] / len(rows)
    by_len = {}
    for lo, hi in ((10, 30), (30, 60), (60, 10 ** 6)):
        sub = [(x, p) for x, p in P if lo <= x["runes"] < hi]
        by_len[f"{lo}-{hi if hi < 10 ** 6 else ''}"] = (sum(pick(p) == x["true"] for x, p in sub) / max(1, len(sub)), len(sub))
    rel = []
    for lo, hi in ((0, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 0.95), (0.95, 1.01)):
        sub = [(x, p) for x, p in P if lo <= max(p.values()) < hi]
        rel.append({"lo": lo, "hi": min(hi, 1), "n": len(sub), "p": sum(max(p.values()) for _, p in sub) / max(1, len(sub)),
                    "acc": sum(pick(p) == x["true"] for x, p in sub) / max(1, len(sub))})
    out[name] = {"n": len(P), "right": right / len(P), "within_one": near / len(P), "majority_baseline": base,
                 "per_epoch": per, "confusion": conf, "by_length": by_len, "reliability": rel}
    out[name]["by_object"] = by_object(P, lambda xp: xp[0]["sig"], {
        "right": lambda ys: sum(pick(p) == x["true"] for x, p in ys) / len(ys),
        "within_one": lambda ys: sum(abs(EPOCHS.index(pick(p)) - EPOCHS.index(x["true"])) <= 1 for x, p in ys) / len(ys)})
    print_by_object(f"[{name}]", out[name]["by_object"])
    print(f"[{name}] rätt epok {right / len(P):.1%} av {len(P)} (största klassen {base:.1%}); högst en epok fel {near / len(P):.1%}")
    print("   per epok (rätt, antal):", per)
    print("   efter längd:", {k_: f"{a:.0%} (n={n})" for k_, (a, n) in by_len.items()})
    print("   säkerhet → träff:", [(f"{c['p']:.2f}", f"{c['acc']:.2f}", c["n"]) for c in rel])
json.dump({"settings": vars(args), "tests": len(rows), "results": out, "rows": rows},
          open(args.out or os.path.join(ROOT, "utdata", "Malt", "runlm_datering.json"), "w"), indent=1)
