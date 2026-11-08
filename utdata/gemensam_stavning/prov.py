"""Gemensam stavning: H1–H3 enligt analysplaner/2026-11-08-gemensam-stavning.md (sha a49379aa). Läser stenar.json,
skriver resultat.json och resultat.md.
    .venv/bin/python utdata/gemensam_stavning/prov.py"""
import json
import os
from collections import Counter

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, "stenar.json"), encoding="utf-8"))
ST = D["stones"]
MIN_LAND = 30
NPERM, NBOOT = 9999, 2000
EARLY, LATE = {"RAK", "Fp", "Pr1", "Pr2"}, {"Pr3", "Pr4", "Pr5"}
rng = np.random.default_rng(2026)

lands = sorted(k for k, n in Counter(s["land"] for s in ST).items() if n >= MIN_LAND)
land_ix = {k: i for i, k in enumerate(lands)}
N = len(ST)
land = np.array([land_ix.get(s["land"], -1) for s in ST])
carvers = sorted({s["carver"] for s in ST if s["carver"]})
carver = np.array([carvers.index(s["carver"]) if s["carver"] else -1 for s in ST])
style = np.array([s["style"] for s in ST])
pro = np.array([s["pro"] for s in ST])
period = np.array([0 if s["style"] in EARLY else 1 if s["style"] in LATE else -1 for s in ST])

# per word: the stones that have it and their spelling codes
WORDS = []
for w in D["common_words"]:
    idx = np.array([i for i, s in enumerate(ST) if w in s["words"]])
    sp = [ST[i]["words"][w] for i in idx]
    codes = {x: k for k, x in enumerate(sorted(set(sp)))}
    WORDS.append((idx, np.array([codes[x] for x in sp])))


def pairs(m):
    """Pairs among weighted members (multiplicities m), without self-pairs: (Σm² − Σm²ᵢ)/2 over the groups summed."""
    return m


def agreement(group, weight=None, mask=None, by=None, nby=None):
    """Identical pairs and all pairs per group label (group: label per stone, −1 = not counted; weight: multiplicity per
    stone for the bootstrap). Pairs of stones by the same attributed carver are not counted."""
    G = int(group.max()) + 1 if nby is None else nby
    same, tot = np.zeros(G), np.zeros(G)
    wgt = np.ones(N) if weight is None else weight
    for idx, code in WORDS:
        g = group[idx]
        ok = g >= 0
        if mask is not None:
            ok &= mask[idx]
        g, cd, m, cv = g[ok], code[ok], wgt[idx][ok], carver[idx][ok]
        if not len(g):
            continue
        S = int(cd.max()) + 1
        C = len(carvers) + 1

        def pc(keys, size):
            s1 = np.bincount(keys, weights=m, minlength=size)
            s2 = np.bincount(keys, weights=m * m, minlength=size)
            return (s1 * s1 - s2) / 2.0

        t = pc(g, G)
        sm = pc(g * S + cd, G * S).reshape(G, S).sum(1)
        hc = cv >= 0
        if hc.any():
            gc, cdc, mc, cvc = g[hc], cd[hc], m[hc], cv[hc]
            s1 = np.bincount(gc * C + cvc, weights=mc, minlength=G * C)
            s2 = np.bincount(gc * C + cvc, weights=mc * mc, minlength=G * C)
            t -= ((s1 * s1 - s2) / 2.0).reshape(G, C).sum(1)
            k = (gc * C + cvc) * S + cdc
            s1 = np.bincount(k, weights=mc, minlength=G * C * S)
            s2 = np.bincount(k, weights=mc * mc, minlength=G * C * S)
            sm -= ((s1 * s1 - s2) / 2.0).reshape(G, C * S).sum(1)
        same += sm
        tot += t
    return same, tot


def h1_stat(lab):
    s, t = agreement(lab, nby=len(lands))
    a = s / t
    w = t / t.sum()
    return float((w * (a - (w * a).sum()) ** 2).sum()), a, t


obs_v, A, T = h1_stat(land)
strata = {k: np.where((style == k) & (land >= 0))[0] for k in set(style)}
perm_ge = 0
for _ in range(NPERM):
    lab = land.copy()
    for ix in strata.values():
        lab[ix] = lab[rng.permutation(ix)]
    if h1_stat(lab)[0] >= obs_v:
        perm_ge += 1
p1 = (perm_ge + 1) / (NPERM + 1)

boot = np.zeros((NBOOT, len(lands)))
for b in range(NBOOT):
    wgt = np.zeros(N)
    for li in range(len(lands)):
        ix = np.where(land == li)[0]
        wgt += np.bincount(rng.choice(ix, len(ix)), minlength=N)
    s, t = agreement(land, weight=wgt, nby=len(lands))
    boot[b] = s / t
ci = np.percentile(boot, [2.5, 97.5], axis=0)

# H2: late against early, pairs within the same land and period
lp = np.where((land >= 0) & (period >= 0), land * 2 + period, -1)


def h2(labels):
    s, t = agreement(labels, nby=len(lands) * 2)
    s, t = s.reshape(-1, 2), t.reshape(-1, 2)
    return s[:, 1].sum() / t[:, 1].sum() - s[:, 0].sum() / t[:, 0].sum(), s, t


obs_d, S2, T2 = h2(lp)
ge = 0
for _ in range(NPERM):
    per = period.copy()
    for li in range(len(lands)):
        ix = np.where((land == li) & (period >= 0))[0]
        per[ix] = per[rng.permutation(ix)]
    if h2(np.where((land >= 0) & (per >= 0), land * 2 + per, -1))[0] >= obs_d:
        ge += 1
p2 = (ge + 1) / (NPERM + 1)

# H3: pairs both professional, neither, mixed (within lands) – via masks
s_pp, t_pp = agreement(land, mask=pro, nby=len(lands))
s_nn, t_nn = agreement(land, mask=~pro, nby=len(lands))
s_all, t_all = agreement(land, nby=len(lands))
s_mx, t_mx = s_all - s_pp - s_nn, t_all - t_pp - t_nn

res = {"plan": "analysplaner/2026-11-08-gemensam-stavning.md", "plan_sha": "a49379aa",
       "stones": int((land >= 0).sum()), "stones_aligned_all": D["n_aligned_stones"], "corpus": D["n_corpus"],
       "common_words": len(D["common_words"]), "lands": lands,
       "H1": {"weighted_variance": obs_v, "p": p1, "holds": p1 < 0.05,
              "per_land": {k: {"A": float(A[i]), "pairs": float(T[i]), "ci95": [float(ci[0, i]), float(ci[1, i])],
                               "stones": int((land == i).sum())} for i, k in enumerate(lands)}},
       "H2": {"A_early": float(S2[:, 0].sum() / T2[:, 0].sum()), "A_late": float(S2[:, 1].sum() / T2[:, 1].sum()),
              "diff": obs_d, "p": p2, "holds": p2 < 0.05 and obs_d > 0,
              "per_land": {k: {"early": float(S2[i, 0] / T2[i, 0]) if T2[i, 0] else None,
                               "late": float(S2[i, 1] / T2[i, 1]) if T2[i, 1] else None,
                               "pairs": [float(T2[i, 0]), float(T2[i, 1])]} for i, k in enumerate(lands)}},
       "H3": {"both_pro": float(s_pp.sum() / t_pp.sum()), "neither": float(s_nn.sum() / t_nn.sum()),
              "mixed": float(s_mx.sum() / t_mx.sum()), "pairs": [float(t_pp.sum()), float(t_nn.sum()), float(t_mx.sum())],
              "per_land_neither": {k: float(s_nn[i] / t_nn[i]) if t_nn[i] else None for i, k in enumerate(lands)}}}
json.dump(res, open(os.path.join(HERE, "resultat.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: res[k] for k in ("stones", "lands")}, ensure_ascii=False))
print("H1 p", p1, {k: round(v["A"], 3) for k, v in res["H1"]["per_land"].items()})
print("H2", round(res["H2"]["A_early"], 3), "→", round(res["H2"]["A_late"], 3), "p", p2)
print("H3", {k: round(res["H3"][k], 3) for k in ("both_pro", "neither", "mixed")})
