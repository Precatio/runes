"""Gränsskannern (låst plan analysplaner/2026-11-02-gransskannern.md, sha 7d22ff40): varje par av angränsande gamla
regioner × 27 drag – skiljer regionerna (kvotprov med tiden konstant, BH), och är skillnaden skarp vid gränsen (stenar
inom 10 km från den andra regionen, Fisher) eller en gradient; halvorna för de skarpa. Skriver gransskannern.json.
    PYTHONPATH=. .venv/bin/python utdata/granser/gransskannern.py"""
import csv
import json
import math
import os
import sys
from collections import defaultdict
from itertools import combinations

import numpy as np
from scipy.stats import chi2, fisher_exact

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "utdata", "folkland"))
from src import linking as L  # noqa: E402
from src import regions  # noqa: E402
from src.research_gaps import place_name  # noqa: E402
from folkland import FEATS, bh, dummies, loglik  # noqa: E402  (same 27 traits and the same logistic machinery)

NB_KM, MIN_STONES, MIN_EVENTS = 10, 40, 10


def km(a, b):
    return 111.2 * math.hypot(a[0] - b[0], (a[1] - b[1]) * math.cos(math.radians(a[0])))


rd = json.load(open(os.path.join(ROOT, "data", "rundata.json")))["inscriptions"]
st = L.stones(rd)
feat = {r["signum"]: r for r in csv.DictReader(open(os.path.join(ROOT, "utdata", "upptackt_v3", "drag.csv")))}
rows = []
for sg, x in st.items():
    if sg not in feat or x["lat"] is None or x["province"] not in ("U", "Sö", "Ög", "Vg", "Sm", "Öl", "G", "Nä", "Vs", "Gs", "Hs", "M", "Bo", "Vr", "D", "J"):
        continue
    f = feat[sg]
    yr = (float(f["style_from"]) + float(f["style_to"])) / 2 if f["style_from"] else None
    per = "odaterad" if yr is None else "–1010" if yr < 1010 else "1010–1040" if yr < 1040 else "1040–1070" if yr < 1070 else "1070–"
    rows.append({"signum": sg, "region": regions.old_region(sg, x["province"]), "province": x["province"],
                 "parish": x["parish"] or sg, "year": yr, "period": per, "pt": (x["lat"], x["lon"]),
                 **{k: (None if f.get(k, "") == "" else int(float(f[k]))) for k in FEATS}})
by_reg = defaultdict(list)
for r in rows:
    by_reg[r["region"]].append(r)
big = [g for g, v in by_reg.items() if len(v) >= MIN_STONES]


def near(r, other):
    return min(km(r["pt"], o["pt"]) for o in by_reg[other]) <= NB_KM


pairs = [(a, b) for a, b in combinations(sorted(big), 2) if any(near(r, b) for r in by_reg[a])]
# halves: parishes alternately within the province, in order of mean dating
pm = defaultdict(list)
for r in rows:
    pm[(r["province"], r["parish"])].append(r["year"])
half = {}
for prov in {p for p, _ in pm}:
    keys = sorted((k for k in pm if k[0] == prov), key=lambda k: (all(y is None for y in pm[k]), np.mean([y for y in pm[k] if y] or [0]), -len(pm[k]), k[1]))
    for i, k in enumerate(keys):
        half[k] = i % 2


def lr(z, f):
    pers = sorted({r["period"] for r in z}); regs = sorted({r["region"] for r in z})
    y = np.array([r[f] for r in z], float)
    Xr = np.hstack([np.ones((len(z), 1)), dummies([r["period"] for r in z], pers)])
    Xf = np.hstack([Xr, dummies([r["region"] for r in z], regs)])
    stat = 2 * (loglik(Xf, y) - loglik(Xr, y))
    return float(chi2.sf(max(stat, 0), len(regs) - 1))


tests = []
for a, b in pairs:
    for f in FEATS:
        z = [r for r in by_reg[a] + by_reg[b] if r[f] is not None]
        k = sum(r[f] for r in z)
        if k < MIN_EVENTS or len(z) - k < MIN_EVENTS:
            continue
        sa = np.mean([r[f] for r in z if r["region"] == a]); sb = np.mean([r[f] for r in z if r["region"] == b])
        tests.append({"a": a, "b": b, "feature": f, "n": len(z), "share_a": float(sa), "share_b": float(sb), "p": lr(z, f)})
for t, q in zip(tests, bh([t["p"] for t in tests])):
    t["q"] = float(q)
for t in tests:
    if t["q"] >= 0.05:
        continue
    hi, lo = (t["a"], t["b"]) if t["share_a"] > t["share_b"] else (t["b"], t["a"])
    zh = [r for r in by_reg[hi] if r[t["feature"]] is not None and near(r, lo)]
    zl = [r for r in by_reg[lo] if r[t["feature"]] is not None and near(r, hi)]
    k1, n1 = sum(r[t["feature"]] for r in zh), len(zh)
    k2, n2 = sum(r[t["feature"]] for r in zl), len(zl)
    pb = float(fisher_exact([[k1, n1 - k1], [k2, n2 - k2]], alternative="greater")[1]) if n1 and n2 else None
    t.update({"high": hi, "low": lo, "border_high": [k1, n1], "border_low": [k2, n2], "p_border": pb,
              "sharp": pb is not None and pb < 0.05})
    if t["sharp"]:
        hs = []
        for h in (0, 1):
            zz = [r for r in by_reg[hi] + by_reg[lo] if r[t["feature"]] is not None and half[(r["province"], r["parish"])] == h]
            same = (np.mean([r[t["feature"]] for r in zz if r["region"] == hi] or [0]) > np.mean([r[t["feature"]] for r in zz if r["region"] == lo] or [0]))
            hs.append({"p": lr(zz, t["feature"]), "same_direction": bool(same)})
        t["halves"] = hs
        t["holds"] = all(h["p"] < 0.05 and h["same_direction"] for h in hs)
res = {"plan": "analysplaner/2026-11-02-gransskannern.md", "plan_sha": "7d22ff40", "regions": {g: len(by_reg[g]) for g in big},
       "pairs": [[a, b] for a, b in pairs], "n_tests": len(tests), "tests": tests}
json.dump(res, open(os.path.join(HERE, "gransskannern.json"), "w"), ensure_ascii=False, indent=1)
sig = [t for t in tests if t["q"] < 0.05]
print("regioner", res["regions"]); print("grannpar", len(pairs), [f"{place_name(a)}–{place_name(b)}" for a, b in pairs])
print("prov", len(tests), "skiljer", len(sig), "skarpa", sum(t.get("sharp", False) for t in sig), "håller", sum(t.get("holds", False) for t in sig))
for t in sorted(sig, key=lambda t: (not t.get("holds", False), not t.get("sharp", False), t["q"])):
    print(f"{place_name(t['high']):14} > {place_name(t['low']):14} {t['feature']:14} {t['share_a']:.0%}/{t['share_b']:.0%} q {t['q']:.4f} "
          f"gräns {t['border_high'][0]}/{t['border_high'][1]} mot {t['border_low'][0]}/{t['border_low'][1]} p {t['p_border'] if t['p_border'] is None else round(t['p_border'], 4)} "
          f"{'SKARP' if t['sharp'] else 'gradient'}{' HÅLLER' if t.get('holds') else ''}")
