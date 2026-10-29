"""Vad har grannstenarna gemensamt? Enligt den låsta planen analysplaner/2026-10-29-grannstenarna.md.
    ../../.venv/bin/python -m utdata.avstand.grannar   (från projektmappen: .venv/bin/python utdata/avstand/grannar.py)
Skriver utdata/avstand/grannar.json."""
import json
import os
import sys
from collections import Counter

import numpy as np
import pandas as pd
from pyproj import Transformer

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
from src import entities  # noqa: E402

D = os.path.join(ROOT, "data", "cache", "r", "corpus", "3f58e9339191761e")
NPERM = 9999
STYLES = {"RAK", "Fp", "Pr1", "Pr2", "Pr3", "Pr4", "Pr5"}
rng = np.random.default_rng(2026)

c = pd.read_csv(os.path.join(D, "corpus.csv"), low_memory=False)
m = pd.read_csv(os.path.join(D, "messages.csv"))
c = c.merge(m[["signum", "msg_resa"]], on="signum", how="left")
recs = {r["signum"]: r for r in json.load(open(os.path.join(ROOT, "data", "rundata.json")))["inscriptions"]}

# Personnamn (resare och döda) per sten; de 20 vanligaste namnen bland alla svenska runstenar räknas inte (planen)
names_all = {}
for s in c.signum:
    x = entities.extract(recs[s])
    names_all[s] = {p["key"] for p in x["persons"] if p["role"] in ("resare", "minnes")}
freq = Counter(k for v in names_all.values() for k in v)
COMMON = {k for k, _ in freq.most_common(20)}

st = c[c.province.isin(["U", "Sö"]) & (c.moved == 0) & (c.lost == 0) & c.lat.notna()].reset_index(drop=True)
tr = Transformer.from_crs("EPSG:4326", "EPSG:3006", always_xy=True)
x, y = tr.transform(st.lon.to_numpy(dtype=float), st.lat.to_numpy(dtype=float))
xy = np.c_[x, y]
n = len(st)
dist = np.sqrt(((xy[:, None, :] - xy[None, :, :]) ** 2).sum(-1))
prov = st.province.to_numpy(dtype=object)
same_prov = prov[:, None] == prov[None, :]
iu = np.triu_indices(n, 1)


def masks(near, far):
    dd, sp = dist[iu], same_prov[iu]
    return (dd > near[0]) & (dd <= near[1]) & sp, (dd >= far[0]) & (dd <= far[1]) & sp


# Stenvisa egenskaper och matriser "paret har egenskapen" / "paret är känt"
carver = st.carver.fillna("").to_numpy(dtype=object)
carver_known = carver != ""
style = st["style"].fillna("").to_numpy(dtype=object)
style_known = np.isin(style, list(STYLES))
names = [names_all[s] for s in st.signum]


def share_matrix(drop_common):
    sets = [v - COMMON if drop_common else v for v in names]
    keys = sorted({k for v in sets for k in v})
    idx = {k: i for i, k in enumerate(keys)}
    M = np.zeros((n, len(keys)), dtype=np.int32)
    for i, v in enumerate(sets):
        for k in v:
            M[i, idx[k]] = 1
    known = np.array([len(v) > 0 for v in sets])
    return (M @ M.T) > 0, known


def both(col):
    v = st[col].to_numpy(dtype=float) if isinstance(col, str) else col
    known = ~pd.isna(v)
    b = np.nan_to_num(np.asarray(v, dtype=float)) > 0
    return np.outer(b, b), known


resa = ((st.cat_fard.fillna(0) > 0) | (st.msg_resa.fillna(0) > 0)).to_numpy(dtype=float)
resa_known = st.msg_resa.notna().to_numpy() | st.cat_fard.notna().to_numpy()
names_share, names_known = share_matrix(True)
names_share_all, names_known_all = share_matrix(False)
FEATURES = {
    "samma_ristare": (carver[:, None] == carver[None, :], carver_known),
    "samma_namn": (names_share, names_known),
    "samma_stilgrupp": (style[:, None] == style[None, :], style_known),
    "bro": both("cat_bro_vag"),
    "resa": (np.outer(resa > 0, resa > 0), resa_known),
    "kristen": both("cat_kristen"),
}


def ratio(F, K, perm, near_m, far_m):
    """Andelen nära par med egenskapen genom andelen jämförelsepar, med stenarnas egenskaper permuterade."""
    Fp, Kp = F[np.ix_(perm, perm)][iu], (K[perm][:, None] & K[perm][None, :])[iu]
    a = Fp[near_m & Kp].mean() if (near_m & Kp).any() else np.nan
    b = Fp[far_m & Kp].mean() if (far_m & Kp).any() else np.nan
    return a / b if b else np.nan, int((near_m & Kp).sum()), int((far_m & Kp).sum()), a, b


def perm_within_province():
    p = np.arange(n)
    for pv in ("U", "Sö"):
        ix = np.where(prov == pv)[0]
        p[ix] = rng.permutation(ix)
    return p


def test(near=(25, 500), far=(2000, 10000), feats=FEATURES, nperm=NPERM):
    near_m, far_m = masks(near, far)
    ident = np.arange(n)
    obs = {k: ratio(F, K, ident, near_m, far_m) for k, (F, K) in feats.items()}
    sims = {k: [] for k in feats}
    for _ in range(nperm):
        p = perm_within_province()
        for k, (F, K) in feats.items():
            sims[k].append(ratio(F, K, p, near_m, far_m)[0])
    out = {}
    for k, (r, nn, nf, a, b) in obs.items():
        s = np.array(sims[k], dtype=float)
        s = s[~np.isnan(s)]
        out[k] = {"ratio": r, "near_pairs": nn, "far_pairs": nf, "share_near": a, "share_far": b,
                  "p": (1 + np.sum(s >= r)) / (1 + len(s))}
    return out


def by_province(near=(25, 500), far=(2000, 10000)):
    near_m, far_m = masks(near, far)
    res = {}
    for pv in ("U", "Sö"):
        keep = (prov[iu[0]] == pv)
        res[pv] = {k: ratio(F, K, np.arange(n), near_m & keep, far_m & keep)[0] for k, (F, K) in FEATURES.items()}
    return res


main = test()
ps = [main[k]["p"] for k in FEATURES]
order = np.argsort(ps)
holm = np.empty(len(ps))
running = 0.0
for rank, i in enumerate(order):
    running = max(running, min(1.0, (len(ps) - rank) * ps[i]))
    holm[i] = running
prov_ratios = by_province()
for i, k in enumerate(FEATURES):
    main[k]["p_holm"] = holm[i]
    both_prov = all((prov_ratios[pv][k] or 0) > 1 for pv in ("U", "Sö"))
    main[k]["U_ratio"], main[k]["So_ratio"] = prov_ratios["U"][k], prov_ratios["Sö"][k]
    main[k]["utslag"] = ("håller" if holm[i] < 0.05 and both_prov else
                         "antydan" if holm[i] < 0.05 or main[k]["p"] < 0.05 else "ingen skillnad påvisad")
rob = {"nara_300": test(near=(25, 300), nperm=1999), "fjarran_1_5km": test(far=(1000, 5000), nperm=1999),
       "namn_alla": test(feats={"samma_namn": (names_share_all, names_known_all)}, nperm=1999)}
res = {"plan": "analysplaner/2026-10-29-grannstenarna.md", "n_stones": n, "common_names_removed": sorted(COMMON),
       "main": main, "robustness": rob}
json.dump(res, open(os.path.join(ROOT, "utdata", "avstand", "grannar.json"), "w"), ensure_ascii=False, indent=1,
          default=float)
for k, v in main.items():
    print(f"{k:16s} nära {v['share_near']:.3f} ({v['near_pairs']} par)  fjärran {v['share_far']:.3f} ({v['far_pairs']} par)  "
          f"kvot {v['ratio']:.2f}  p {v['p']:.4f}  Holm {v['p_holm']:.4f}  U {v['U_ratio']:.2f} Sö {v['So_ratio']:.2f}  {v['utslag']}")
for name, r in rob.items():
    print(name, {k: (round(v["ratio"], 2), round(v["p"], 4)) for k, v in r.items()})
