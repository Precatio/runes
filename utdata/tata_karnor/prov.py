"""Täta kärnor – kandidater till onämnda händer (analysplaner/2026-11-08-tata-karnor.md, sha 15c2f757). Medelkoppling
(UPGMA) över överskottslikheten i textdragen (src/hand_links.py); gränsen c* vald på namngivna ristare (precision ≥ 0,70);
C1 mot runologernas grupper i Runor 2020, C2 gränsen vald på ena halvan av ristarna och prövad på den andra, C3 kärnorna
utan namngiven ristare. Skriver resultat.json och resultat.md.
    .venv/bin/python utdata/tata_karnor/prov.py"""
import glob
import json
import os
import re
import sys
from collections import Counter

import numpy as np
import pandas as pd
from pyproj import Transformer
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import squareform
from scipy.stats import wilcoxon

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
from src import hand_links  # noqa: E402

C = os.path.join(ROOT, "data", "cache", "r", "corpus", "510ebfb3acc9a229")
NDRAW = 999
MAXD = 30000.0
GRID = np.round(np.arange(0.0, 0.801, 0.01), 2)
PREC, MINPAIRS, PREC_B = 0.70, 30, 0.50

# --- the stones and the excess similarity, exactly as src/hand_links.build
corp = pd.read_csv(os.path.join(C, "corpus.csv"), low_memory=False)
corp = corp[corp.lat.notna() & ~corp.province.isin(["Bo"])]
recs = {r["signum"]: r for r in json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["inscriptions"]}
corp = corp[corp.signum.isin(recs)].reset_index(drop=True)
corp, S = hand_links._features(corp, recs)
xy = np.array(Transformer.from_crs(4326, 3006, always_xy=True).transform(corp.lon.values, corp.lat.values)).T
D = np.hypot(xy[:, None, 0] - xy[None, :, 0], xy[:, None, 1] - xy[None, :, 1])
E = hand_links.excess_matrix(S, D)
N = len(corp)
SIG = list(corp.signum)
IX = {s: i for i, s in enumerate(SIG)}
carver = [c if isinstance(c, str) and not u else None for c, u in zip(corp.carver, corp.carvers_uncertain)]
print(N, "stenar")

# --- UPGMA on (largest excess − excess); pairs beyond 30 km or without neighbours = the lowest excess (entirely unlike)
X = E.copy()
X[D > MAXD] = np.nan
lo_, hi_ = np.nanmin(X), np.nanmax(X)
X = np.where(np.isnan(X), lo_, X)
X = 0.5 * (X + X.T)
Dis = hi_ - X
np.fill_diagonal(Dis, 0.0)
Z = linkage(squareform(Dis, checks=False), method="average")


def labels_at(c):
    return fcluster(Z, t=hi_ - c + 1e-12, criterion="distance")


LAB = {c: labels_at(c) for c in GRID}


def precision(lab, allowed=None):
    """Pairs of stones with a certain carver (among the allowed carvers) in the same group: share with the same carver."""
    by = {}
    for i, c in enumerate(carver):
        if c and (allowed is None or c in allowed):
            by.setdefault(lab[i], Counter())[c] += 1
    same = sum(n * (n - 1) // 2 for cnt in by.values() for n in cnt.values())
    tot = sum(sum(cnt.values()) * (sum(cnt.values()) - 1) // 2 for cnt in by.values())
    return (same / tot if tot else None), tot


def choose(allowed=None):
    table = []
    for c in GRID:
        p, n = precision(LAB[c], allowed)
        table.append({"c": float(c), "precision": p, "pairs": n})
    cstar = next((r["c"] for r in table if r["pairs"] >= MINPAIRS and r["precision"] is not None and r["precision"] >= PREC), None)
    return cstar, table


cstar, table = choose()
print("c* =", cstar)
assert cstar is not None, "inget c når precisionen 0,70 med minst 30 par – planen avbryts"
lab = LAB[round(cstar, 2)]

# --- C2: half of the carvers chooses c, the other half measures it
rng2 = np.random.default_rng(2026)
cnt = Counter(c for c in carver if c)
multi = sorted(c for c, n in cnt.items() if n >= 2)
perm = rng2.permutation(len(multi))
A = {multi[i] for i in perm[: len(multi) // 2]}
B = set(multi) - A
cA, tableA = choose(A)
pB, nB = precision(LAB[round(cA, 2)], B) if cA is not None else (None, 0)
C2 = {"carvers_A": len(A), "carvers_B": len(B), "c_A": cA, "precision_B": pB, "pairs_B": nB,
      "precision_A": next((r["precision"] for r in tableA if r["c"] == cA), None)}
C2["holds"] = pB is not None and pB >= PREC_B
print("C2", C2)

# --- C1: the runologists' groups in Runor 2020 (as utdata/nya_hander/prov.py)
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


runor_note = {}
for f in sorted(glob.glob(os.path.join(ROOT, "data", "cache", "runor", "*.json"))):
    d = json.load(open(f, encoding="utf-8"))
    sig = f"{d['signum1']} {d['signum2']}".strip()
    if sig in IX and d.get("carver"):
        runor_note[sig] = "; ".join(f"{c.get('name')} ({c.get('attribution')})" for c in d["carver"])
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

rng1 = np.random.default_rng(2026)
units = []
for g in sorted(groups):
    gi = [IX[s] for s in g]
    pairs = [(a, b) for k, a in enumerate(gi) for b in gi[k + 1:] if D[a, b] <= MAXD]
    if not pairs:
        continue
    cands = []
    for a, b in pairs:
        for x, y in ((a, b), (b, a)):
            d = D[x, y]
            lo, hi = min(d * 0.75, d - 1000), min(max(d * 1.25, d + 1000), MAXD)
            ok = np.where((D[x] >= lo) & (D[x] <= hi))[0]
            ok = ok[~np.isin(ok, gi)]
            if len(ok):
                cands.append((x, ok))
    if not cands:
        continue
    obs = float(np.mean([lab[a] == lab[b] for a, b in pairs]))
    draws = [np.mean([lab[x] == lab[rng1.choice(ok)] for x, ok in cands]) for _ in range(NDRAW)]
    units.append({"stones": g, "pairs": len(pairs), "together": obs, "control": float(np.mean(draws)),
                  "unnamed": any(carver[IX[s]] is None for s in g)})
dd = [u["together"] - u["control"] for u in units]
nz = [x for x in dd if x != 0]
C1 = {"groups": len(units), "mean_together": float(np.mean([u["together"] for u in units])),
      "mean_control": float(np.mean([u["control"] for u in units])), "median_diff": float(np.median(dd)),
      "better": int(sum(x > 0 for x in dd)), "worse": int(sum(x < 0 for x in dd)), "zero": int(sum(x == 0 for x in dd)),
      "p": float(wilcoxon(nz, alternative="greater").pvalue) if nz else 1.0}
C1["holds"] = C1["p"] < 0.05 and C1["better"] > C1["worse"]
print("C1", C1)

# --- C3: the dense cores at c*
att = json.load(open(os.path.join(C, "attribution.json"), encoding="utf-8"))
pred = {p["signum"]: p for p in att["predictions"]}
members = {}
for i, l in enumerate(lab):
    members.setdefault(l, []).append(i)
cores = [sorted(m, key=lambda i: SIG[i]) for m in members.values() if len(m) >= 3]
kinds = Counter()
cand = []
for m in cores:
    named = {carver[i] for i in m if carver[i]}
    if len(named) >= 2:
        kinds["flera namngivna ristare"] += 1
        continue
    if named and all(carver[i] for i in m):
        kinds["en namngiven ristare"] += 1
        continue
    if named:
        kinds["namngiven ristare och stenar utan"] += 1
        continue
    kinds["utan namngiven ristare"] += 1
    pe = [E[a, b] for k, a in enumerate(m) for b in m[k + 1:]]
    within = [D[a, b] <= MAXD and not np.isnan(E[a, b]) for k, a in enumerate(m) for b in m[k + 1:]]
    rows = corp.iloc[m]
    unc = {}
    for i in m:
        u = [c["name"] for c in recs[SIG[i]]["carvers"] if c["kind"] in ("S", "A") and c["uncertain"]]
        if u:
            unc[SIG[i]] = u
    model = {SIG[i]: (pred[SIG[i]].get("top"), pred[SIG[i]].get("p_cal", pred[SIG[i]].get("p"))) if SIG[i] in pred else None
             for i in m}
    cand.append({"stones": [SIG[i] for i in m], "size": len(m),
                 "mean_excess": float(np.nanmean([x if w else np.nan for x, w in zip(pe, within)])) if any(within) else None,
                 "pairs_within_30km": float(np.mean(within)), "span_km": float(D[np.ix_(m, m)].max() / 1000),
                 "parishes": sorted(set(str(x) for x in rows.parish)), "styles": dict(Counter(str(x) for x in rows["style"].fillna("–"))),
                 "runor": {SIG[i]: runor_note[SIG[i]] for i in m if SIG[i] in runor_note}, "uncertain_carvers": unc,
                 "model": model, "model_opir": sum(1 for v in model.values() if v and v[0] == "Öpir")})
cand.sort(key=lambda c: (-c["size"], -(c["mean_excess"] or 0)))
sizes = Counter(len(m) for m in cores)

res = {"plan": "analysplaner/2026-11-08-tata-karnor.md", "plan_sha": "15c2f757", "corpus": "510ebfb3", "stones": N,
       "cstar": cstar, "precision_at_cstar": next(r for r in table if r["c"] == cstar), "table": table,
       "C1": C1, "C1_groups": units, "C2": C2, "cores": len(cores), "core_sizes": dict(sorted(sizes.items())),
       "core_kinds": dict(kinds), "stones_in_cores": int(sum(len(m) for m in cores)), "C3": cand}
json.dump(res, open(os.path.join(HERE, "resultat.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: res[k] for k in ("cstar", "precision_at_cstar", "cores", "core_sizes", "core_kinds", "stones_in_cores")},
                 ensure_ascii=False))
for c in cand[:25]:
    print(f"{c['size']:2} st {c['span_km']:5.1f} km överskott {c['mean_excess'] if c['mean_excess'] is None else round(c['mean_excess'], 2)} | "
          f"{', '.join(c['stones'])} | {c['styles']} | Öpir {c['model_opir']}")

# --- After the test (descriptive, not in the plan): how alike the runologists' pairs are against c*
post = []
for u in units:
    gi = [IX[s] for s in u["stones"]]
    for k, a in enumerate(gi):
        for b in gi[k + 1:]:
            if D[a, b] <= MAXD and not np.isnan(E[a, b]):
                post.append({"pair": [SIG[a], SIG[b]], "excess": round(float(E[a, b]), 3), "unnamed": u["unnamed"]})
named_same = [E[a, b] for a in range(N) for b in range(a + 1, N)
              if carver[a] and carver[a] == carver[b] and D[a, b] <= MAXD and not np.isnan(E[a, b])]
res["post_hoc"] = {"note": "räknat efter provet, beskrivande",
                   "runor_pairs": len(post), "runor_median_excess": float(np.median([p["excess"] for p in post])),
                   "runor_share_at_cstar": float(np.mean([p["excess"] >= cstar for p in post])),
                   "runor_unnamed_median": float(np.median([p["excess"] for p in post if p["unnamed"]])),
                   "named_same_pairs": len(named_same), "named_same_median": float(np.median(named_same)),
                   "named_same_share_at_cstar": float(np.mean(np.array(named_same) >= cstar))}
json.dump(res, open(os.path.join(HERE, "resultat.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("efter provet:", res["post_hoc"])
