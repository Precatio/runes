"""Upplands folkland och deras runstenar (låst plan analysplaner/2026-11-01-upplands-folkland.md, sha 48346775).
Steg 1: kvotprov drag ~ folkland + tidsskikt mot drag ~ tidsskikt, BH över 27 drag; steg 2: halvorna; steg 3: gränsprovet
(stenar vars socken har en socken i grannlandet inom 10 km). Skriver folkland.json.
Omkörd 2026-11-05 med den rättade landindelningen (Färingö tingslag i Attundaland, Adelsö i Fjädrundaland efter Det
medeltida Sverige 1:7; web/src/lib/historiska_land.json → parish_medieval) – en deklarerad avvikelse efter låsningen;
den första körningen ligger i folkland_v1.json.
    PYTHONPATH=. .venv/bin/python utdata/folkland/folkland.py"""
import csv
import json
import math
import os
import re
import sys
from collections import defaultdict
from itertools import combinations

import numpy as np
from scipy.stats import chi2, fisher_exact

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
from src import linking as L  # noqa: E402

FEATS = ["cat_kristen", "pm_kors", "pm_bon", "pm_sjal", "pm_hednisk", "cat_fard", "msg_dod_borta", "msg_berom",
         "cat_bro_vag", "kvinna_resare", "kvinna_ensam", "flera_resare", "rel_barn", "rel_foralder", "rel_syskon",
         "rel_make", "drengr", "thegn", "pm_signatur", "ord_kumbl", "mat_granit", "pm_stungna", "monoftong", "r_for_R",
         "o_runa", "prep_at", "ord_þennsa"]
LANDS = ["tiundaland", "attundaland", "fjadrundaland", "roden"]
NAMES = {"tiundaland": "Tiundaland", "attundaland": "Attundaland", "fjadrundaland": "Fjädrundaland", "roden": "Roden"}


def bh(p):
    p = np.asarray(p, float); o = np.argsort(p)
    q = p[o] * len(p) / (np.arange(len(p)) + 1)
    q = np.minimum.accumulate(q[::-1])[::-1]
    out = np.empty_like(q); out[o] = np.minimum(q, 1)
    return out


def loglik(X, y, it=100):
    """Maximum log-likelihood of a logistic regression (Newton–Raphson with a tiny ridge against separation)."""
    b = np.zeros(X.shape[1])
    for _ in range(it):
        eta = np.clip(X @ b, -30, 30)
        mu = 1 / (1 + np.exp(-eta))
        W = mu * (1 - mu) + 1e-9
        H = X.T @ (X * W[:, None]) + 1e-6 * np.eye(X.shape[1])
        step = np.linalg.solve(H, X.T @ (y - mu) - 1e-6 * b)
        step = np.clip(step, -5, 5)
        b += step
        if np.max(np.abs(step)) < 1e-9:
            break
    eta = np.clip(X @ b, -30, 30)
    mu = np.clip(1 / (1 + np.exp(-eta)), 1e-12, 1 - 1e-12)
    return float(np.sum(y * np.log(mu) + (1 - y) * np.log(1 - mu)))


def dummies(vals, levels):
    return np.column_stack([[1.0 if v == lv else 0.0 for v in vals] for lv in levels[1:]]) if len(levels) > 1 else np.zeros((len(vals), 0))


def lr_test(rows, f):
    z = [r for r in rows if r[f] is not None]
    lands = sorted({r["land"] for r in z}); pers = sorted({r["period"] for r in z})
    if len(lands) < 2:
        return None
    y = np.array([r[f] for r in z], float)
    one = np.ones((len(z), 1))
    Xr = np.hstack([one, dummies([r["period"] for r in z], pers)])
    Xf = np.hstack([Xr, dummies([r["land"] for r in z], lands)])
    lr = 2 * (loglik(Xf, y) - loglik(Xr, y))
    df = len(lands) - 1
    shares = {l: (sum(r[f] for r in z if r["land"] == l), sum(1 for r in z if r["land"] == l)) for l in lands}
    return {"lr": lr, "df": df, "p": float(chi2.sf(max(lr, 0), df)), "shares": shares}


rd = json.load(open(os.path.join(ROOT, "data", "rundata.json")))["inscriptions"]
st = L.stones(rd)
sl = json.load(open(os.path.join(ROOT, "web", "public", "geo", "sten_land.json")))
soc = list(csv.DictReader(open(os.path.join(ROOT, "data", "geo", "socknar_land.csv"))))
byname = defaultdict(list)
for s in soc:
    byname[s["namn"]].append(s)


def km(a_lat, a_lon, b_lat, b_lon):
    return 111.2 * math.hypot(a_lat - b_lat, (a_lon - b_lon) * math.cos(math.radians(a_lat)))


def parish_point(x):
    """The stone's parish point (as scripts/assign_sten_land.py): its named parish within 25 km, else the nearest.
    Rerun 2026-11-05 (declared deviation, a data correction): as in assign_sten_land.py, Rundata's "(nu …)" is dropped
    from the parish name, and a stone moved far from its parish (Skansen) gets its named parish when the name is unique
    in Sweden and within 100 km."""
    named = byname.get(re.sub(r"\s*\(nu [^)]*\)", "", x["parish"] or "").strip().replace(" sn", "") + " socken", [])
    near = [s for s in named if km(float(s["lat"]), float(s["lon"]), x["lat"], x["lon"]) <= 25]
    if not near and len(named) == 1 and km(float(named[0]["lat"]), float(named[0]["lon"]), x["lat"], x["lon"]) <= 100:
        near = named
    pool = near or soc
    s = min(pool, key=lambda s: km(float(s["lat"]), float(s["lon"]), x["lat"], x["lon"]))
    return float(s["lat"]), float(s["lon"])


land_pts = {l: [(float(s["lat"]), float(s["lon"])) for s in soc if s["land"] == l] for l in LANDS}
feat = {r["signum"]: r for r in csv.DictReader(open(os.path.join(ROOT, "utdata", "upptackt_v3", "drag.csv")))}
rows = []
for sg, x in st.items():
    lnd = sl.get(sg)
    if lnd in LANDS and sg in feat and x["lat"] is not None:
        f = feat[sg]
        yr = (float(f["style_from"]) + float(f["style_to"])) / 2 if f["style_from"] else None
        per = "odaterad" if yr is None else "–1010" if yr < 1010 else "1010–1040" if yr < 1040 else "1040–1070" if yr < 1070 else "1070–"
        pp = parish_point(x)
        rows.append({"signum": sg, "land": lnd, "parish": x["parish"] or sg, "year": yr, "period": per, "pp": pp,
                     **{k: (None if f.get(k, "") == "" else int(float(f[k]))) for k in FEATS}})
res = {"plan": "analysplaner/2026-11-01-upplands-folkland.md", "plan_sha": "48346775",
       "rerun": "2026-11-05: rättad landindelning (parish_medieval i historiska_land.json); v1 i folkland_v1.json",
       "n": {l: sum(r["land"] == l for r in rows) for l in LANDS}}

# step 1
s1 = {f: lr_test(rows, f) for f in FEATS}
fs = [f for f in FEATS if s1[f]]
for f, q in zip(fs, bh([s1[f]["p"] for f in fs])):
    s1[f]["q"] = float(q)
res["step1"] = s1
sig = [f for f in fs if s1[f]["q"] < 0.05]

# step 2: halves by parish, alternately in order of mean dating
pm = defaultdict(list)
for r in rows:
    pm[r["parish"]].append(r["year"])
order = sorted(pm, key=lambda p: (all(y is None for y in pm[p]), np.mean([y for y in pm[p] if y] or [0]), -len(pm[p]), p))
half = {p: i % 2 for i, p in enumerate(order)}
top = lambda t: max(t["shares"], key=lambda l: t["shares"][l][0] / max(1, t["shares"][l][1]))  # noqa: E731
s2 = {}
for f in sig:
    hs = [lr_test([r for r in rows if half[r["parish"]] == h], f) for h in (0, 1)]
    s2[f] = {"halves": hs, "holds": all(h and h["p"] < 0.05 for h in hs) and top(hs[0]) == top(hs[1]) == top(s1[f])}
res["step2"] = s2

# step 3: border test between neighbouring folklands
def neighbours(a, b):
    return any(km(p[0], p[1], q[0], q[1]) <= 10 for p in land_pts[a][::2] for q in land_pts[b][::2])


nb = {(a, b): neighbours(a, b) for a, b in combinations(LANDS, 2)}
res["neighbours"] = {f"{a}-{b}": v for (a, b), v in nb.items()}
s3 = {}
for f in [f for f in sig if s2[f]["holds"]]:
    sh = {l: s1[f]["shares"][l][0] / max(1, s1[f]["shares"][l][1]) for l in s1[f]["shares"]}
    pairs = sorted(((a, b) for (a, b), v in nb.items() if v), key=lambda ab: -abs(sh[ab[0]] - sh[ab[1]]))
    if not pairs:
        continue
    a, b = pairs[0]
    if sh[a] < sh[b]:
        a, b = b, a

    def border(r, other):
        return any(km(r["pp"][0], r["pp"][1], q[0], q[1]) <= 10 for q in land_pts[other])
    ra = [r for r in rows if r["land"] == a and r[f] is not None]
    rb = [r for r in rows if r["land"] == b and r[f] is not None]
    ba = [r for r in ra if border(r, b)]; bb = [r for r in rb if border(r, a)]
    ia = [r for r in ra if not border(r, b)]; ib = [r for r in rb if not border(r, a)]
    k = lambda xs: (sum(r[f] for r in xs), len(xs))  # noqa: E731
    (k1, n1), (k2, n2) = k(ba), k(bb)
    p = float(fisher_exact([[k1, n1 - k1], [k2, n2 - k2]], alternative="greater")[1]) if n1 and n2 else None
    s3[f] = {"high": a, "low": b, "border_high": [k1, n1], "border_low": [k2, n2], "inner_high": list(k(ia)), "inner_low": list(k(ib)),
             "p": p, "at_border": p is not None and p < 0.05}
res["step3"] = s3
json.dump(res, open(os.path.join(HERE, "folkland.json"), "w"), ensure_ascii=False, indent=1)
print(res["n"])
for f in FEATS:
    t = s1[f]
    if t:
        sh = "  ".join(f"{NAMES[l][:5]} {t['shares'][l][0]}/{t['shares'][l][1]}={t['shares'][l][0]/max(1,t['shares'][l][1]):.0%}" for l in LANDS if l in t["shares"])
        print(f"{f:14} LR {t['lr']:6.1f} p {t['p']:.2e} q {t['q']:.3f} | {sh}")
print("halvor:", {f: (v["holds"], [round(h["p"], 4) if h else None for h in v["halves"]]) for f, v in s2.items()})
print("grannar:", res["neighbours"])
for f, v in s3.items():
    print("gräns", f, v)
