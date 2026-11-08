"""Bär textdragen en hand? (analysplaner/2026-11-08-textdrag-hand.md, sha add8ff31). Likheten i ortografisk stilometri
och korpusens textdrag (utan geografi) inom samma säkra ristare (K) och inom runologernas grupper i Runor 2020 (T), mot
grannstenar på samma avstånd. Skriver resultat.json och resultat.md.
    .venv/bin/python utdata/textdrag_hand/prov.py"""
import glob
import json
import math
import os
import re
import sys
from collections import Counter

import numpy as np
import pandas as pd
from pyproj import Transformer
from scipy import sparse
from scipy.stats import wilcoxon

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
from src import orthography  # noqa: E402

C = os.path.join(ROOT, "data", "cache", "r", "corpus", "510ebfb3acc9a229")
NDRAW = 999
rng = np.random.default_rng(2026)

corp = pd.read_csv(os.path.join(C, "corpus.csv"), low_memory=False)
corp = corp[corp.lat.notna() & ~corp.province.isin(["Bo"])].reset_index(drop=True)
recs = {r["signum"]: r for r in json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["inscriptions"]}
corp = corp[corp.signum.isin(recs)].reset_index(drop=True)
names = orthography.name_forms(list(recs.values()))
feats = [orthography.features(recs[s], names) for s in corp.signum]
keep = np.array([f["n_words"] >= 3 for f in feats])
corp, feats = corp[keep].reset_index(drop=True), [f for f, k in zip(feats, keep) if k]
N = len(corp)
SIG = list(corp.signum)
IX = {s: i for i, s in enumerate(SIG)}

# orthographic stylometry: TF-IDF over character n-grams, separators and bind runes; L2-normalised
vocab = {}
rows, cols, vals = [], [], []
for i, f in enumerate(feats):
    for k, v in f["counts"].items():
        j = vocab.setdefault(k, len(vocab))
        rows.append(i), cols.append(j), vals.append(float(v))
X = sparse.csr_matrix((vals, (rows, cols)), shape=(N, len(vocab)))
df = np.asarray((X > 0).sum(0)).ravel()
X = X.multiply(np.log((1 + N) / (1 + df)) + 1).tocsr()
X = sparse.diags(1 / np.maximum(np.sqrt(np.asarray(X.multiply(X).sum(1)).ravel()), 1e-12)) @ X
# the corpus' language traits, formulas and content categories, standardised
tc = [c for c in corp.columns if c.startswith(("trait_", "cat_", "pm_"))]
T = corp[tc].apply(pd.to_numeric, errors="coerce").fillna(0).to_numpy(float)
T = (T - T.mean(0)) / np.where(T.std(0) > 0, T.std(0), 1)
T = T / np.maximum(np.linalg.norm(T, axis=1, keepdims=True), 1e-12)


def sim_row(i):
    """Similarity of stone i with every stone: the mean of the two cosines."""
    return 0.5 * (np.asarray((X @ X[i].T).todense()).ravel() + T @ T[i])


xy = np.array(Transformer.from_crs(4326, 3006, always_xy=True).transform(corp.lon.values, corp.lat.values)).T
certain = {r.signum: r.carver for r in corp.itertuples() if isinstance(r.carver, str) and not r.carvers_uncertain}


def pair_vs_control(a, b, exclude):
    """sim(A, B) − the mean over NDRAW draws of sim(A, C), C at the distance d ± 25 % (at least ± 1 km), not excluded."""
    ia, ib = IX[a], IX[b]
    d = float(np.hypot(*(xy[ia] - xy[ib])))
    dd = np.hypot(*(xy - xy[ia]).T)
    lo, hi = min(d * 0.75, d - 1000), max(d * 1.25, d + 1000)
    ok = np.where((dd >= lo) & (dd <= hi))[0]
    ok = ok[~np.isin(ok, exclude)]
    if not len(ok):
        return None
    s = sim_row(ia)
    return float(s[ib] - s[rng.choice(ok, NDRAW)].mean())


def unit_diff(stones, exclude_fn):
    diffs = []
    for i, a in enumerate(stones):
        for b in stones[i + 1:]:
            for x, y in ((a, b), (b, a)):
                v = pair_vs_control(x, y, exclude_fn(x))
                if v is not None:
                    diffs.append(v)
    return float(np.mean(diffs)) if diffs else None


# K: the same certain carver, pairs within 30 km
by_carver = {}
for s, c in certain.items():
    if s in IX:
        by_carver.setdefault(c, []).append(s)
K_units = {}
for c, ss in by_carver.items():
    if len(ss) < 3:
        continue
    pts = np.array([xy[IX[s]] for s in ss])
    pairs = [(a, b) for i, a in enumerate(ss) for j, b in enumerate(ss) if j > i and np.hypot(*(pts[i] - pts[j])) <= 30000]
    if not pairs:
        continue
    same = np.array([IX[s] for s in ss])
    diffs = []
    for a, b in pairs:
        for x, y in ((a, b), (b, a)):
            v = pair_vs_control(x, y, same)
            if v is not None:
                diffs.append(v)
    if diffs:
        K_units[c] = {"stones": len(ss), "pairs": len(pairs), "diff": float(np.mean(diffs))}
kd = [v["diff"] for v in K_units.values()]
K = {"carvers": len(kd), "median_diff": float(np.median(kd)), "better": int(sum(x > 0 for x in kd)),
     "p": float(wilcoxon(kd, alternative="greater").pvalue)}
K["holds"] = K["p"] < 0.05 and K["median_diff"] > 0

# T: the runologists' groups (Runor 2020 "samma som gjort X"), parsed as in utdata/samma_hand/prov.py
SAME = re.compile(r"^(Samma som|Samma ristare som|Troligen samma|Antagligen samma|Förmodligen samma|Eventuellt samma)", re.I)
PREFIX = re.compile(r"^(U|Sö|Ög|Vg|Sm|Öl|G|Vs|Nä|Gs|Hs|M|D|Vr|Ån|J|Bo|DR|N|Sk|Bl|Hl)$")


def referenced(text, own_prefix):
    m = re.search(r"gjort\s+(.*)$", text) or re.search(r".*\bsom\s+(.*)$", text)
    if not m:
        return []
    body = re.sub(r"ATA\s*[\d/]+", "", m.group(1)).replace(" och ", ",").rstrip(". ")
    out, prefix = [], own_prefix
    for part in [p.strip() for p in body.split(",") if p.strip()]:
        toks = part.split()
        if len(toks) >= 2 and PREFIX.match(toks[0]):
            prefix, part = toks[0], " ".join(toks[1:])
        rg = re.fullmatch(r"(\d+)\s*-\s*(\d+)", part.strip())
        if rg:
            out += [f"{prefix} {k}" for k in range(int(rg.group(1)), int(rg.group(2)) + 1)]
        elif re.fullmatch(r"\d+[A-Za-z]?|Fv\d{4};\d+[A-Za-z]?", part.strip()):
            out.append(f"{prefix} {part.strip()}")
    return out


parent = {}


def find(a):
    parent.setdefault(a, a)
    while parent[a] != a:
        parent[a] = parent[parent[a]]
        a = parent[a]
    return a


for f in glob.glob(os.path.join(ROOT, "data", "cache", "runor", "*.json")):
    d = json.load(open(f, encoding="utf-8"))
    sig = f"{d['signum1']} {d['signum2']}".strip()
    for cv in d.get("carver") or []:
        n = (cv.get("name") or "").strip()
        if SAME.match(n):
            for o in referenced(n, d["signum1"]):
                if sig in IX and o in IX and sig != o:
                    parent[find(sig)] = find(o)
groups = {}
for s in parent:
    groups.setdefault(find(s), []).append(s)
groups = [sorted(g) for g in groups.values() if len(g) >= 2]
T_units = []
for g in groups:
    ex = np.array([IX[s] for s in g])
    v = unit_diff(g, lambda x: ex)
    if v is not None:
        T_units.append({"stones": g, "diff": v, "unnamed": any(s not in certain for s in g)})
td = [u["diff"] for u in T_units]
Tt = {"groups": len(td), "median_diff": float(np.median(td)), "better": int(sum(x > 0 for x in td)),
      "worse": int(sum(x < 0 for x in td)), "p": float(wilcoxon(td, alternative="greater").pvalue)}
Tt["holds"] = Tt["p"] < 0.05 and Tt["median_diff"] > 0
un = [u["diff"] for u in T_units if u["unnamed"]]
Tt["unnamed_only"] = {"groups": len(un), "median_diff": float(np.median(un)) if un else None,
                      "p": float(wilcoxon(un, alternative="greater").pvalue) if len(un) >= 5 else None}
res = {"plan": "analysplaner/2026-11-08-textdrag-hand.md", "plan_sha": "add8ff31", "stones": N, "features": len(vocab),
       "traits": len(tc), "K": K, "K_per_carver": K_units, "T": Tt, "T_groups": T_units}
json.dump(res, open(os.path.join(HERE, "resultat.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({"stones": N, "K": K, "T": Tt}, ensure_ascii=False, indent=1))
for u in sorted(T_units, key=lambda u: -u["diff"]):
    print(f"{u['diff']:+.3f}  {'onämnd' if u['unnamed'] else 'namngiven'}  {', '.join(u['stones'])}")
