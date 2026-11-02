"""Landprofiler – proven (låst plan analysplaner/2026-11-02-landprofiler.md, sha eb59f631). Läser stenar.csv, gravar.csv,
namn.csv och drag.json (data.py) och skriver landprofiler.json.
    PYTHONPATH=. .venv/bin/python utdata/landprofiler/analys.py"""
import csv
import json
import math
import os
from collections import Counter, defaultdict

import numpy as np
from scipy.stats import chi2

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
D = json.load(open(os.path.join(HERE, "drag.json")))
SPLIT = {"U", "Sm", "G"}
MIN = {"stenar": 15, "gravar": 30, "namn": 50}


def bh(p):
    p = np.asarray(p, float); o = np.argsort(p)
    q = p[o] * len(p) / (np.arange(len(p)) + 1)
    q = np.minimum.accumulate(q[::-1])[::-1]
    out = np.empty_like(q); out[o] = np.minimum(q, 1)
    return out


def loglik(X, y, it=100):
    b = np.zeros(X.shape[1])
    for _ in range(it):
        mu = 1 / (1 + np.exp(-np.clip(X @ b, -30, 30)))
        H = X.T @ (X * (mu * (1 - mu) + 1e-9)[:, None]) + 1e-6 * np.eye(X.shape[1])
        step = np.clip(np.linalg.solve(H, X.T @ (y - mu) - 1e-6 * b), -5, 5)
        b += step
        if np.max(np.abs(step)) < 1e-9:
            break
    mu = np.clip(1 / (1 + np.exp(-np.clip(X @ b, -30, 30))), 1e-12, 1 - 1e-12)
    return float(np.sum(y * np.log(mu) + (1 - y) * np.log(1 - mu)))


def g_test(k1, n1, k0, n0):
    """Likelihood-ratio test for a 2×2 table (= logistic regression y ~ group without covariates)."""
    def ll(k, n):
        return (k * math.log(k / n) if k else 0) + ((n - k) * math.log((n - k) / n) if n - k else 0)
    stat = 2 * (ll(k1, n1) + ll(k0, n0) - ll(k1 + k0, n1 + n0))
    return float(chi2.sf(max(stat, 0), 1))


def test(zin, zout, f, period):
    zin = [r for r in zin if r[f] not in ("", None)]; zout = [r for r in zout if r[f] not in ("", None)]
    if not zin or not zout:
        return None
    yi = [int(float(r[f])) for r in zin]; yo = [int(float(r[f])) for r in zout]
    k1, n1, k0, n0 = sum(yi), len(yi), sum(yo), len(yo)
    if k1 + k0 < 10 or (n1 + n0) - (k1 + k0) < 10:
        return None
    si, so = k1 / n1, k0 / n0
    if period:
        z = zin + zout; y = np.array(yi + yo, float)
        pers = sorted({r["period"] for r in z})
        Xr = np.hstack([np.ones((len(z), 1)), np.column_stack([[1.0 if r["period"] == p else 0.0 for r in z] for p in pers[1:]])
                        if len(pers) > 1 else np.zeros((len(z), 0))])
        Xf = np.hstack([Xr, np.array([[1.0]] * n1 + [[0.0]] * n0)])
        p = float(chi2.sf(max(2 * (loglik(Xf, y) - loglik(Xr, y)), 0), 1))
    else:
        p = g_test(k1, n1, k0, n0)
    orr = ((k1 + .5) / (n1 - k1 + .5)) / ((k0 + .5) / (n0 - k0 + .5))
    return {"k_in": k1, "n_in": n1, "k_out": k0, "n_out": n0, "share_in": si, "share_out": so, "or": orr, "p": p}


def units(rows, minsize):
    """(name, kind, rows_in, rows_out): old lands vs the rest of the province; härader vs the rest of their old land
    (subdivided provinces) or province."""
    out = []
    byprov = defaultdict(list)
    for r in rows:
        byprov[r["province"]].append(r)
    for pv, rs in byprov.items():
        if pv in SPLIT:
            for reg in sorted({r["region"] for r in rs} - {pv}):
                zi = [r for r in rs if r["region"] == reg]
                if len(zi) >= minsize:
                    out.append((reg, "land", pv, zi, [r for r in rs if r["region"] != reg]))
        for h in sorted({r["harad"] for r in rs}):
            zi = [r for r in rs if r["harad"] == h]
            if len(zi) < minsize:
                continue
            reg = Counter(r["region"] for r in zi).most_common(1)[0][0]
            ctx = [r for r in rs if r["region"] == reg] if (pv in SPLIT and reg != pv) else rs
            zo = [r for r in ctx if r["harad"] != h]
            if len(zo) >= minsize:
                out.append((h, "harad", reg if (pv in SPLIT and reg != pv) else pv, zi, zo))
    return out


def run(domain, table, feats, period, top_key):
    rows = list(csv.DictReader(open(os.path.join(HERE, table + ".csv"))))
    for r in rows:
        r["half"] = int(r["half"])
    tests = []
    for name, kind, ctx, zi, zo in units(rows, MIN[table]):
        for f in feats:
            t = test(zi, zo, f, period)
            if t and t["k_in"] >= 5:   # the plan: at least 5 with the trait in the unit
                tests.append({"domain": domain, "unit": name, "kind": kind, "context": ctx, "province": zi[0]["province"],
                              "feature": f, **t, "_zi": zi, "_zo": zo})
    for t, q in zip(tests, bh([t["p"] for t in tests]) if tests else []):
        t["q"] = float(q)
    for t in tests:
        if t["q"] >= 0.05:
            t["holds"] = False
            continue
        up = t["share_in"] > t["share_out"]
        hs = []
        for h in (0, 1):
            c = test([r for r in t["_zi"] if r["half"] == h], [r for r in t["_zo"] if r["half"] == h], t["feature"], period)
            hs.append(None if c is None else {"p": c["p"], "same": (c["share_in"] > c["share_out"]) == up})
        t["halves"] = hs
        if top_key == "carver":
            top = Counter(r["carver"] for r in t["_zi"] if r["carver"]).most_common(1)
            drop = top[0][0] if top and top[0][1] > 5 else None
        else:
            hits = Counter(r["parish"] for r in t["_zi"] if r[t["feature"]] not in ("", None) and int(float(r[t["feature"]])) == (1 if up else 0))
            drop = hits.most_common(1)[0][0] if hits else None
        if drop is not None:
            c = test([r for r in t["_zi"] if r[top_key] != drop], t["_zo"], t["feature"], period)
            t["without_top"] = {"dropped": drop, **({"p": c["p"], "same": (c["share_in"] > c["share_out"]) == up} if c else {"p": None})}
            ok = c is not None and c["p"] < 0.05 and (c["share_in"] > c["share_out"]) == up
        else:
            t["without_top"] = None; ok = True
        t["holds"] = all(h is not None and h["p"] < 0.05 and h["same"] for h in hs) and ok
    for t in tests:
        t.pop("_zi"); t.pop("_zo")
    return tests


known = set()
m = json.load(open(os.path.join(ROOT, "utdata", "gamla_granser", "monster.json")))
for t in m["step3"]["tests"] + m["step2"]["tests"]:
    if t["q"] < 0.05:
        known.add((t.get("harad") or t["unit"], t["feature"]))
gs = json.load(open(os.path.join(ROOT, "utdata", "granser", "gransskannern.json")))
for t in gs["tests"]:
    if t["q"] < 0.05:
        known |= {(t["a"], t["feature"]), (t["b"], t["feature"])}

ALL = []
for domain, table, feats, period, top in (("språk", "stenar", D["LANG"] + D["ORD"], True, "carver"),
                                          ("sed", "stenar", D["SED"], True, "carver"),
                                          ("plats", "stenar", D["PLATS"], True, "carver"),
                                          ("natur", "stenar", D["NATUR"], True, "carver"),
                                          ("gravskick", "gravar", D["GRAV"], False, "parish"),
                                          ("ortnamn", "namn", D["NAMN"], False, "parish")):
    ts = run(domain, table, feats, period, top)
    for t in ts:
        t["known"] = (t["unit"], t["feature"]) in known
    ALL += ts
    h = [t for t in ts if t["holds"]]
    print(f"{domain:10} prov {len(ts):5}  q<0,05 {sum(t['q'] < 0.05 for t in ts):4}  håller {len(h):4}", flush=True)
json.dump({"plan": "analysplaner/2026-11-02-landprofiler.md", "plan_sha": "eb59f631", "tests": ALL},
          open(os.path.join(HERE, "landprofiler.json"), "w"), ensure_ascii=False, indent=0, default=float)
