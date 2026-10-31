"""Robusthetstrappan för test B (samma personnamn, nära par mot jämförelsepar) enligt den låsta tilläggsplanen
analysplaner/2026-10-31-familjens-plats-trappan.md. Samma urval, namn och mått som grannar.py (planen 2026-10-29);
steg: huvudmåttet, halvorna, varje landskap för sig, utan par med samma säkra ristare, utan flyttade stenar enligt
Runor 2020. Skriver utdata/avstand/grannar_trappa.json.
    .venv/bin/python utdata/avstand/grannar_trappa.py"""
import json
import os
import sys
from collections import Counter

import numpy as np
import pandas as pd
from pyproj import Transformer

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
from src import entities, question, robustness  # noqa: E402

D = os.path.join(ROOT, "data", "cache", "r", "corpus", "3f58e9339191761e")
NPERM = 9999
NEAR, FAR = (25, 500), (2000, 10000)
c = pd.read_csv(os.path.join(D, "corpus.csv"), low_memory=False)
recs = {r["signum"]: r for r in json.load(open(os.path.join(ROOT, "data", "rundata.json")))["inscriptions"]}
names_all = {}
for s in c.signum:
    x = entities.extract(recs[s])
    names_all[s] = {p["key"] for p in x["persons"] if p["role"] in ("resare", "minnes")}
freq = Counter(k for v in names_all.values() for k in v)
COMMON = {k for k, _ in freq.most_common(20)}
# the fixed halves of all the project's analyses (whole parishes alternating within the province)
rows = [{k: (None if pd.isna(v) else v) for k, v in r.items()} for r in c[["signum", "province", "parish", "style_from", "style_to", "style"]].to_dict("records")]
HALF = question.halves(rows)
MOVED_RUNOR = robustness._runor_moved()
ALL = c[c.province.isin(["U", "Sö"]) & (c.moved == 0) & (c.lost == 0) & c.lat.notna()].reset_index(drop=True)
TR = Transformer.from_crs("EPSG:4326", "EPSG:3006", always_xy=True)


def run(st, drop_same_carver=False, seed=2026):
    """The ratio (near pairs sharing a name / far pairs sharing a name) and its permutation p for a set of stones."""
    rng = np.random.default_rng(seed)
    st = st.reset_index(drop=True)
    n = len(st)
    x, y = TR.transform(st.lon.to_numpy(dtype=float), st.lat.to_numpy(dtype=float))
    xy = np.c_[x, y]
    I, J = np.triu_indices(n, 1)
    dd = np.sqrt(((xy[I] - xy[J]) ** 2).sum(1))
    prov = st.province.to_numpy(dtype=object)
    sp = prov[I] == prov[J]
    near, far = (dd > NEAR[0]) & (dd <= NEAR[1]) & sp, (dd >= FAR[0]) & (dd <= FAR[1]) & sp
    if drop_same_carver:
        car = st.carver.fillna("").to_numpy(dtype=object)
        sure = (car != "") & (st.carvers_uncertain.fillna(1).to_numpy() == 0)
        same = sure[I] & sure[J] & (car[I] == car[J])
        near, far = near & ~same, far & ~same
    keep = near | far
    I, J, near_k = I[keep], J[keep], near[keep]
    sets = [names_all[s] - COMMON for s in st.signum]
    keys = sorted({k for v in sets for k in v})
    idx = {k: i for i, k in enumerate(keys)}
    M = np.zeros((n, len(keys)), dtype=np.int32)
    for i, v in enumerate(sets):
        for k in v:
            M[i, idx[k]] = 1
    share = (M @ M.T) > 0
    known = np.array([len(v) > 0 for v in sets])

    def ratio(perm):
        a, b = perm[I], perm[J]
        kn = known[a] & known[b]
        f = share[a, b]
        nn, nf = near_k & kn, ~near_k & kn
        if not nn.any() or not nf.any() or f[nf].mean() == 0:
            return np.nan, int(nn.sum()), int(nf.sum()), np.nan, np.nan
        return f[nn].mean() / f[nf].mean(), int(nn.sum()), int(nf.sum()), f[nn].mean(), f[nf].mean()
    obs = ratio(np.arange(n))
    groups = [np.where(prov == pv)[0] for pv in sorted(set(prov))]
    sims = []
    for _ in range(NPERM):
        p = np.arange(n)
        for ix in groups:
            p[ix] = rng.permutation(ix)
        sims.append(ratio(p)[0])
    s = np.array(sims, dtype=float)
    s = s[~np.isnan(s)]
    r, nn, nf, a, b = obs
    return {"ratio": r, "near_pairs": nn, "far_pairs": nf, "share_near": a, "share_far": b,
            "p": float((1 + np.sum(s >= r)) / (1 + len(s))), "n_stones": n}


out = {"plan": "analysplaner/2026-10-31-familjens-plats-trappan.md", "test": "B: samma personnamn, nära par mot jämförelsepar", "rungs": {}}
out["rungs"]["main"] = run(ALL)
h = ALL.signum.map(HALF)
out["rungs"]["half_A"] = run(ALL[h == "A"])
out["rungs"]["half_B"] = run(ALL[h == "B"])
tot = out["rungs"]["main"]["near_pairs"]
for pv in ("U", "Sö"):
    r = run(ALL[ALL.province == pv])
    r["share_of_pairs"] = r["near_pairs"] / tot
    out["rungs"][f"only_{pv}"] = r
out["rungs"]["no_same_carver"] = run(ALL, drop_same_carver=True)
out["rungs"]["moved_runor"] = run(ALL[~ALL.signum.isin(MOVED_RUNOR)])
for k, r in out["rungs"].items():
    big = r.get("share_of_pairs", 1.0) >= 2 / 3
    r["holds"] = bool(r["ratio"] > 1 and (r["p"] < 0.05 or (k.startswith("only_") and not big)))
out["n_moved_runor_dropped"] = int(ALL.signum.isin(MOVED_RUNOR).sum())
json.dump(out, open(os.path.join(ROOT, "utdata", "avstand", "grannar_trappa.json"), "w"), ensure_ascii=False, indent=1)
for k, r in out["rungs"].items():
    print(f"{k:15s} kvot {r['ratio']:.2f}  nära par {r['near_pairs']:3d}  jämförelsepar {r['far_pairs']:5d}  p {r['p']:.4f}  "
          f"{'HÅLLER' if r['holds'] else 'HÅLLER INTE'}" + (f"  (andel av paren {r['share_of_pairs']:.2f})" if 'share_of_pairs' in r else ""))
