"""Smålands små land och deras runstenar (låst plan analysplaner/2026-11-01-smalanden.md, sha 82ddb6e5).
Tiohärad (Värend, Finnveden, Njudung) mot de östra och norra landen i 22 drag (Fisher, BH), halvor per socken, tiden
konstant; beskrivande per land. Skriver smalanden.json.
    PYTHONPATH=. .venv/bin/python utdata/smalanden/smalanden.py"""
import csv
import json
import math
import os
import sys
from collections import Counter, defaultdict

import numpy as np
from scipy.stats import fisher_exact
from scipy.stats import norm

def bh(p):
    """Benjamini–Hochberg q-values."""
    p = np.asarray(p, float)
    o = np.argsort(p)
    q = p[o] * len(p) / (np.arange(len(p)) + 1)
    q = np.minimum.accumulate(q[::-1])[::-1]
    out = np.empty_like(q)
    out[o] = np.minimum(q, 1)
    return out


def logit(X, y, it=50):
    """Logistic regression by Newton–Raphson: coefficients and Wald p-values (no statsmodels in the environment)."""
    b = np.zeros(X.shape[1])
    for _ in range(it):
        mu = 1 / (1 + np.exp(-X @ b))
        W = mu * (1 - mu)
        H = X.T @ (X * W[:, None])
        step = np.linalg.solve(H, X.T @ (y - mu))
        b += step
        if np.max(np.abs(step)) < 1e-8:
            break
    se = np.sqrt(np.diag(np.linalg.inv(H)))
    return b, 2 * norm.sf(np.abs(b / se))


HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
from src import linking as L  # noqa: E402

FEATS = ["cat_kristen", "pm_kors", "pm_bon", "pm_hednisk", "cat_magisk", "cat_fard", "msg_dod_borta", "msg_berom",
         "cat_bro_vag", "kvinna_resare", "flera_resare", "rel_barn", "rel_foralder", "rel_syskon", "rel_make",
         "rel_ej_slakt", "drengr", "thegn", "pm_signatur", "ord_kumbl", "mat_granit", "nara_gravfalt"]
TIO = {"varend", "finnveden", "njudung"}
EAST = {"vedbo", "tveta", "vista", "tjust", "sevede", "aspeland", "handbord", "more", "mo"}

rd = json.load(open(os.path.join(ROOT, "data", "rundata.json")))["inscriptions"]
ins = {r["signum"]: r for r in rd}
st = L.stones(rd)
soc = list(csv.DictReader(open(os.path.join(ROOT, "data", "geo", "socknar_land.csv"))))
byname = defaultdict(list)
for s in soc:
    byname[s["namn"]].append(s)


def km(s, x):
    return 111.2 * math.hypot(float(s["lat"]) - x["lat"], (float(s["lon"]) - x["lon"]) * math.cos(math.radians(x["lat"])))


def land_of(x):
    if x["lat"] is None:
        return None
    near = [s for s in byname.get((x["parish"] or "").replace(" sn", "") + " socken", []) if km(s, x) <= 25]
    if near:
        return min(near, key=lambda s: km(s, x))["land"] or None
    s = min(soc, key=lambda s: km(s, x))
    return (s["land"] or None) if km(s, x) <= 15 else None


feat = {r["signum"]: r for r in csv.DictReader(open(os.path.join(ROOT, "utdata", "upptackt_v3", "drag.csv")))}
rows = []
for sg, x in st.items():
    lnd = land_of(x)
    if lnd and (x["province"] == "Sm" or lnd == "kinda") and sg in feat:
        f = feat[sg]
        yr = (float(f["style_from"]) + float(f["style_to"])) / 2 if f["style_from"] else None
        rows.append({"signum": sg, "land": lnd, "province": x["province"], "parish": x["parish"] or sg, "year": yr,
                     "carvers": x["carvers"], "style": ins[sg].get("style"),
                     **{k: (None if f[k] == "" else int(float(f[k]))) for k in FEATS}})
sm_rows = [r for r in rows if r["province"] == "Sm"]
grp = lambda r: "tio" if r["land"] in TIO else "ost" if r["land"] in EAST else None  # noqa: E731
res = {"plan": "analysplaner/2026-11-01-smalanden.md", "plan_sha": "82ddb6e5", "n_by_land": dict(Counter(r["land"] for r in rows)),
       "n_tio": sum(grp(r) == "tio" for r in sm_rows), "n_ost": sum(grp(r) == "ost" for r in sm_rows)}


def compare(rs, f, ga, gb):
    a = [r[f] for r in rs if ga(r) and r[f] is not None]
    b = [r[f] for r in rs if gb(r) and r[f] is not None]
    if not a or not b:
        return None
    t = [[sum(a), len(a) - sum(a)], [sum(b), len(b) - sum(b)]]
    return {"k1": sum(a), "n1": len(a), "k2": sum(b), "n2": len(b), "p1": sum(a) / len(a), "p2": sum(b) / len(b),
            "p": float(fisher_exact(t)[1])}


main = {f: compare(sm_rows, f, lambda r: grp(r) == "tio", lambda r: grp(r) == "ost") for f in FEATS}
fs = [f for f in FEATS if main[f]]
q = bh([main[f]["p"] for f in fs])
for f, qq in zip(fs, q):
    main[f]["q"] = float(qq)
res["main"] = main
# halves: parishes alternately in order of mean dating
pm = defaultdict(list)
for r in sm_rows:
    pm[r["parish"]].append(r["year"])
order = sorted(pm, key=lambda p: (all(y is None for y in pm[p]), np.mean([y for y in pm[p] if y] or [0]), -len(pm[p]), p))
half = {p: i % 2 for i, p in enumerate(order)}
sig = [f for f in fs if main[f]["q"] < 0.05]
res["halves"] = {f: [compare([r for r in sm_rows if half[r["parish"]] == h], f, lambda r: grp(r) == "tio", lambda r: grp(r) == "ost") for h in (0, 1)] for f in sig}
# time constant
tc = {}
for f in sig:
    z = [r for r in sm_rows if grp(r) and r[f] is not None and r["year"]]
    if len(z) < 20:
        continue
    per = [("–1010" if r["year"] < 1010 else "1010–1040" if r["year"] < 1040 else "1040–1070" if r["year"] < 1070 else "1070–") for r in z]
    levels = sorted(set(per))
    X = np.column_stack([[1.0] * len(z), [1.0 if grp(r) == "tio" else 0.0 for r in z]] + [[1.0 if p == lv else 0.0 for p in per] for lv in levels[1:]])
    y = np.array([r[f] for r in z])
    try:
        b, pv = logit(X, y)
        tc[f] = {"n": len(z), "beta_tio": float(b[1]), "p": float(pv[1])}
    except Exception as e:  # separation in small groups
        tc[f] = {"n": len(z), "error": str(e)[:80]}
res["time_constant"] = tc
# descriptive per land
desc = {}
for lnd in ("njudung", "finnveden", "vedbo", "varend"):
    d = {f: compare(sm_rows, f, lambda r, l=lnd: r["land"] == l, lambda r, l=lnd: r["land"] != l) for f in FEATS}
    lr = [r for r in sm_rows if r["land"] == lnd]
    desc[lnd] = {"n": len(lr), "feats": d, "styles": dict(Counter(r["style"] or "–" for r in lr)),
                 "carvers": dict(Counter(c for r in lr for c in r["carvers"])),
                 "dated": sum(1 for r in lr if r["year"]), "mean_year": float(np.mean([r["year"] for r in lr if r["year"]])) if any(r["year"] for r in lr) else None}
res["per_land"] = desc
res["kinda"] = [{"signum": r["signum"], "style": r["style"]} for r in rows if r["land"] == "kinda"]
res["stones"] = [{"signum": r["signum"], "land": r["land"]} for r in rows]
json.dump(res, open(os.path.join(HERE, "smalanden.json"), "w"), ensure_ascii=False, indent=1)
print("Tiohärad", res["n_tio"], "östra", res["n_ost"])
for f in FEATS:
    m = main[f]
    if m:
        print(f"{f:16} tio {m['k1']:3}/{m['n1']:3} {m['p1']:.0%}  öst {m['k2']:3}/{m['n2']:3} {m['p2']:.0%}  p {m['p']:.4f} q {m.get('q', float('nan')):.3f}")
print("halvor", json.dumps(res["halves"], indent=0)[:1500]); print("tid", tc)
for lnd, d in desc.items():
    top = sorted(((f, v) for f, v in d["feats"].items() if v), key=lambda t: t[1]["p"])[:5]
    print(lnd, d["n"], "medelår", d["mean_year"] and round(d["mean_year"]), "stilar", d["styles"], "ristare", d["carvers"])
    for f, v in top:
        print(f"   {f:16} {v['k1']}/{v['n1']} {v['p1']:.0%} mot {v['p2']:.0%} p {v['p']:.3f}")
