"""Nya, onämnda händer (analysplaner/2026-11-08-nya-handerna.md, sha 9e0037d5). Överskottslikhet i textdragen (utan
geografi) mellan stenar inom 30 km; länkgränsen t vald på namngivna ristare (Youdens J); N1 mot runologernas grupper i
Runor 2020; N2 kandidatgrupper bland stenar där ingen känd ristare passar. Skriver resultat.json och resultat.md.
    .venv/bin/python utdata/nya_hander/prov.py"""
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



MAXD = 30000.0
S = 0.5 * (np.asarray((X @ X.T).todense()) + T @ T.T)          # similarity, all pairs
D = np.hypot(xy[:, None, 0] - xy[None, :, 0], xy[:, None, 1] - xy[None, :, 1])


def band_mean(a, d):
    """Mean similarity of stone a with the corpus' stones at the distance d ± 25 % (at least ± 1 km), a excluded."""
    lo, hi = min(d * 0.75, d - 1000), max(d * 1.25, d + 1000)
    m = (D[a] >= lo) & (D[a] <= hi)
    m[a] = False
    return S[a, m].mean() if m.any() else np.nan


# excess similarity for every pair within 30 km
ii, jj = np.where(np.triu(D <= MAXD, 1))
EX = {}
order = {a: np.argsort(D[a]) for a in range(N)}
for a in range(N):
    da, sa, o = D[a], S[a], order[a]
    dsort, ssort = da[o], sa[o]
    cs = np.concatenate([[0], np.cumsum(ssort)])
    sel = np.where((da <= MAXD) & (np.arange(N) != a))[0]
    for b in sel:
        d = da[b]
        lo, hi = min(d * 0.75, d - 1000), max(d * 1.25, d + 1000)
        i0, i1 = np.searchsorted(dsort, lo, "left"), np.searchsorted(dsort, hi, "right")
        n = i1 - i0 - (1 if lo <= 0 else 0)
        tot = cs[i1] - cs[i0] - (sa[a] if lo <= 0 else 0)
        EX[(a, b)] = sa[b] - tot / n if n > 0 else np.nan
exs = {}
for (a, b), v in EX.items():
    if a < b:
        w = EX.get((b, a))
        exs[(a, b)] = 0.5 * (v + w) if w is not None else v


def ex(a, b):
    return exs.get((min(a, b), max(a, b)), np.nan)


# the link threshold t on named carvers (Youden's J), Runor not used
cert_ix = {IX[s]: c for s, c in certain.items() if s in IX}
same, diff = [], []
for (a, b), v in exs.items():
    if a in cert_ix and b in cert_ix and not np.isnan(v):
        (same if cert_ix[a] == cert_ix[b] else diff).append(v)
same, diff = np.array(same), np.array(diff)
grid = np.quantile(np.concatenate([same, diff]), np.linspace(0.5, 0.995, 200))
J = [(np.mean(same >= t) - np.mean(diff >= t), t) for t in grid]
Jbest, t_link = max(J)
link = lambda a, b: D[a, b] <= MAXD and not np.isnan(ex(a, b)) and ex(a, b) >= t_link  # noqa: E731

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

# N1: the runologists' groups, linked share against distance-matched control pairs
units = []
for g in groups:
    gi = [IX[s] for s in g]
    pairs = [(a, b) for k, a in enumerate(gi) for b in gi[k + 1:] if D[a, b] <= MAXD]
    if not pairs:
        continue
    obs = np.mean([link(a, b) for a, b in pairs])
    draws = []
    cands = []
    for a, b in pairs:
        for x, y in ((a, b), (b, a)):
            d = D[x, y]
            lo, hi = min(d * 0.75, d - 1000), min(max(d * 1.25, d + 1000), MAXD)
            ok = np.where((D[x] >= lo) & (D[x] <= hi))[0]
            ok = ok[~np.isin(ok, gi)]
            if len(ok):
                cands.append((x, ok))
    if not cands:  # no stone at the same distance: the group cannot be compared (as in utdata/samma_hand)
        continue
    for _ in range(NDRAW):
        draws.append(np.mean([link(x, rng.choice(ok)) for x, ok in cands]))
    units.append({"stones": g, "pairs": len(pairs), "linked": float(obs), "control": float(np.mean(draws)),
                  "unnamed": any(s not in certain for s in g)})
dd_ = [u["linked"] - u["control"] for u in units]
N1 = {"groups": len(units), "mean_linked": float(np.mean([u["linked"] for u in units])),
      "mean_control": float(np.mean([u["control"] for u in units])), "median_diff": float(np.median(dd_)),
      "better": int(sum(x > 0 for x in dd_)), "worse": int(sum(x < 0 for x in dd_)),
      "p": float(wilcoxon(dd_, alternative="greater").pvalue) if any(dd_) else 1.0}
N1["holds"] = N1["p"] < 0.05 and N1["median_diff"] > 0

# N2: candidate groups among stones where no known carver fits
att = json.load(open(os.path.join(C, "attribution.json"), encoding="utf-8"))
pred = {p["signum"]: p for p in att["predictions"]}
univ = [IX[s] for s in SIG if s not in certain and (s not in pred or pred[s].get("someone_else"))]
uset = set(univ)
par = {}


def f2(a):
    par.setdefault(a, a)
    while par[a] != a:
        par[a] = par[par[a]]
        a = par[a]
    return a


ulinks = [(a, b) for (a, b), v in exs.items() if a in uset and b in uset and D[a, b] <= MAXD and v >= t_link]
for a, b in ulinks:
    par[f2(a)] = f2(b)
comp = {}
for a in par:
    comp.setdefault(f2(a), []).append(a)
runor_note = {}
for f in glob.glob(os.path.join(ROOT, "data", "cache", "runor", "*.json")):
    d = json.load(open(f, encoding="utf-8"))
    sig = f"{d['signum1']} {d['signum2']}".strip()
    if sig in IX and d.get("carver"):
        runor_note[sig] = "; ".join(f"{c.get('name')} ({c.get('attribution')})" for c in d["carver"])
cand = []
lset = set(ulinks)
for members in comp.values():
    if len(members) < 3:
        continue
    m = sorted(members, key=lambda i: SIG[i])
    npairs = len(m) * (len(m) - 1) / 2
    nlink = sum(1 for k, a in enumerate(m) for b in m[k + 1:] if (min(a, b), max(a, b)) in lset)
    rows = corp.iloc[m]
    cand.append({"stones": [SIG[i] for i in m], "size": len(m), "density": nlink / npairs,
                 "mean_excess": float(np.mean([exs[(min(a, b), max(a, b))] for k, a in enumerate(m) for b in m[k + 1:]
                                               if (min(a, b), max(a, b)) in lset])),
                 "places": sorted(set(str(x) for x in rows.parish)), "styles": sorted(set(str(x) for x in rows["style"].fillna("–"))),
                 "span_km": float(D[np.ix_(m, m)].max() / 1000), "runor": {SIG[i]: runor_note[SIG[i]] for i in m if SIG[i] in runor_note},
                 "model": {SIG[i]: (pred[SIG[i]]["top"] if SIG[i] in pred else None) for i in m}})
cand.sort(key=lambda c: (-c["size"] * c["density"], -c["mean_excess"]))
res = {"plan": "analysplaner/2026-11-08-nya-handerna.md", "plan_sha": "9e0037d5", "stones": N,
       "pairs_within_30km": len(exs), "threshold": {"t": float(t_link), "J": float(Jbest),
       "same_carver_linked": float(np.mean(same >= t_link)), "different_carver_linked": float(np.mean(diff >= t_link)),
       "same_pairs": len(same), "different_pairs": len(diff)},
       "N1": N1, "N1_groups": units, "universe": len(univ), "links_in_universe": len(ulinks), "N2_groups": cand}
json.dump(res, open(os.path.join(HERE, "resultat.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: res[k] for k in ("stones", "pairs_within_30km", "threshold", "N1", "universe", "links_in_universe")},
                 ensure_ascii=False, indent=1))
print(len(cand), "kandidatgrupper med minst tre stenar")
for c in cand[:15]:
    print(f"{c['size']:2} stenar täthet {c['density']:.2f} överskott {c['mean_excess']:.2f} spann {c['span_km']:.0f} km | "
          f"{', '.join(c['stones'][:10])}{' …' if c['size'] > 10 else ''} | {', '.join(c['styles'])}")
