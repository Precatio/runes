"""Stenar som hör ihop – täta kärnor av en hand (analysplaner/2026-11-23-stenar-som-hor-ihop.md, sha 0297bcbd, låst i
f5f0bac). Genomsnittlig länkning (UPGMA) på överskottslikheten i textdragen, diameter ≤ 30 km; τ vald på halva A av de
namngivna ristarna (F0,5); H1 på halva B; H2 mot runologernas grupper i Runor 2020. Skriver resultat.json, resultat.md
och karnor.csv.
    .venv/bin/python utdata/stenar_som_hor_ihop/prov.py"""
import csv
import glob
import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict

import numpy as np
import pandas as pd
from pyproj import Transformer
from scipy import sparse
from scipy.stats import wilcoxon

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
from src import orthography  # noqa: E402

PLAN = os.path.join(ROOT, "analysplaner", "2026-11-23-stenar-som-hor-ihop.md")
assert hashlib.sha256(open(PLAN, "rb").read()).hexdigest().startswith("0297bcbd"), "planen är ändrad efter låsningen"
C = os.path.join(ROOT, "data", "cache", "r", "corpus", "510ebfb3acc9a229")
NDRAW = 999
MAXD = 30000.0
SPLIT_SEED = 20261123
CTRL_SEED = 2026

# ======================================================================================================================
# 1. Textdragen och överskottslikheten (samma kod som utdata/nya_hander/prov.py)
# ======================================================================================================================
corp = pd.read_csv(os.path.join(C, "corpus.csv"), low_memory=False)
corp = corp[corp.lat.notna() & ~corp.province.isin(["Bo"])].reset_index(drop=True)
recs = {r["signum"]: r for r in json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["inscriptions"]}
corp = corp[corp.signum.isin(recs)].reset_index(drop=True)
names = orthography.name_forms(list(recs.values()))
feats = [orthography.features(recs[s], names) for s in corp.signum]
keep = np.array([f["n_words"] >= 3 for f in feats])
corp, feats = corp[keep].reset_index(drop=True), [f for f, k in zip(feats, keep) if k]
N = len(corp)
assert N == 1564, N
SIG = list(corp.signum)
IX = {s: i for i, s in enumerate(SIG)}
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
tc = [c for c in corp.columns if c.startswith(("trait_", "cat_", "pm_"))]
T = corp[tc].apply(pd.to_numeric, errors="coerce").fillna(0).to_numpy(float)
T = (T - T.mean(0)) / np.where(T.std(0) > 0, T.std(0), 1)
T = T / np.maximum(np.linalg.norm(T, axis=1, keepdims=True), 1e-12)
xy = np.array(Transformer.from_crs(4326, 3006, always_xy=True).transform(corp.lon.values, corp.lat.values)).T
S = 0.5 * (np.asarray((X @ X.T).todense()) + T @ T.T)
D = np.hypot(xy[:, None, 0] - xy[None, :, 0], xy[:, None, 1] - xy[None, :, 1])
EXd = np.full((N, N), np.nan)
for a in range(N):
    da, sa = D[a], S[a]
    o = np.argsort(da)
    dsort, ssort = da[o], sa[o]
    cs = np.concatenate([[0], np.cumsum(ssort)])
    for b in np.where((da <= MAXD) & (np.arange(N) != a))[0]:
        d = da[b]
        lo, hi = min(d * 0.75, d - 1000), max(d * 1.25, d + 1000)
        i0, i1 = np.searchsorted(dsort, lo, "left"), np.searchsorted(dsort, hi, "right")
        n = i1 - i0 - (1 if lo <= 0 else 0)
        tot = cs[i1] - cs[i0] - (sa[a] if lo <= 0 else 0)
        if n > 0:
            EXd[a, b] = sa[b] - tot / n
# symmetric: the mean of both directions (one direction if only one is defined), as in nya_hander
E = np.where(np.isnan(EXd), EXd.T, np.where(np.isnan(EXd.T), EXd, 0.5 * (EXd + EXd.T)))
np.fill_diagonal(E, np.nan)
del EXd

# ======================================================================================================================
# 2. Genomsnittlig länkning med diametervillkor; sammanslagningarna sparas så att varje τ är ett snitt i följden
# ======================================================================================================================
iu = np.triu_indices(N, 1)
within = (D[iu] <= MAXD) & ~np.isnan(E[iu])
GRID = np.quantile(E[iu][within], np.linspace(0.5, 0.995, 100))
SUM = np.nan_to_num(E, nan=0.0)
CNT = (~np.isnan(E)).astype(float)
MX = D.copy()
active = np.ones(N, bool)


def score_rows(rows_):
    with np.errstate(invalid="ignore", divide="ignore"):
        s = np.where((CNT[rows_] > 0) & (MX[rows_] <= MAXD), SUM[rows_] / CNT[rows_], -np.inf)
    s[:, ~active] = -np.inf
    s[np.arange(len(rows_)), rows_] = -np.inf
    return s


SC = score_rows(np.arange(N))
merges = []                                        # (kvar, uppslukad, medelöverskott)
while True:
    k = int(np.argmax(SC))
    i, j = divmod(k, N)
    best = SC[i, j]
    if not np.isfinite(best) or best < GRID[0]:
        break
    merges.append((i, j, float(best)))
    SUM[i] += SUM[j]
    SUM[:, i] = SUM[i]
    CNT[i] += CNT[j]
    CNT[:, i] = CNT[i]
    MX[i] = np.maximum(MX[i], MX[j])
    MX[:, i] = MX[i]
    active[j] = False
    SC[j, :] = -np.inf
    SC[:, j] = -np.inf
    r = score_rows(np.array([i]))[0]
    SC[i] = r
    SC[:, i] = r
print(len(merges), "sammanslagningar till lägsta τ")


def labels_at(tau):
    lab = np.arange(N)
    for i, j, s in merges:
        if s < tau:
            break
        lab[lab == lab[j]] = lab[i]
    return lab


# ======================================================================================================================
# 3. τ på halva A (F0,5)
# ======================================================================================================================
certain = {r.signum: r.carver for r in corp.itertuples() if isinstance(r.carver, str) and not r.carvers_uncertain}
cnt = Counter(certain.values())
carvers = sorted(c for c, n in cnt.items() if n >= 2)
rng = np.random.default_rng(SPLIT_SEED)
perm = list(rng.permutation(carvers))
HALF_A = set(perm[: len(perm) // 2])
HALF_B = set(perm[len(perm) // 2:])
A = [IX[s] for s, c in certain.items() if c in HALF_A]
B = [IX[s] for s, c in certain.items() if c in HALF_B]
CAR = {IX[s]: c for s, c in certain.items()}


def prec_recall(lab, idx):
    idx = np.array(idx)
    same_lab = lab[idx][:, None] == lab[idx][None, :]
    same_car = np.array([CAR[i] for i in idx])[:, None] == np.array([CAR[i] for i in idx])[None, :]
    near = D[np.ix_(idx, idx)] <= MAXD
    tri = np.triu(np.ones_like(same_lab, bool), 1)
    co = same_lab & tri
    tp = (co & same_car).sum()
    p = tp / co.sum() if co.sum() else np.nan
    r = tp / (same_car & near & tri).sum()
    return float(p), float(r), int(co.sum())


tune = []
for tau in GRID:
    lab = labels_at(tau)
    p, r, nco = prec_recall(lab, A)
    f = 0.0 if np.isnan(p) or p + r == 0 else 1.25 * p * r / (0.25 * p + r)
    tune.append({"tau": float(tau), "precision": p, "recall": r, "pairs": nco, "f05": f})
best_t = max(tune, key=lambda x: x["f05"])
TAU = best_t["tau"]
LAB = labels_at(TAU)
groups = defaultdict(list)
for i, g in enumerate(LAB):
    groups[g].append(i)
print("τ =", round(TAU, 4), best_t)

# ======================================================================================================================
# 4. H1 – halva B
# ======================================================================================================================
crng = np.random.default_rng(CTRL_SEED)
Bset = np.array(B)
h1 = []
for g, mem in groups.items():
    bm = [i for i in mem if i in set(B)]
    if len(bm) < 2:
        continue
    pairs = [(a, b) for k, a in enumerate(bm) for b in bm[k + 1:]]
    obs = float(np.mean([CAR[a] == CAR[b] for a, b in pairs]))
    cands = []
    mset = set(mem)
    for a, b in pairs:
        d = D[a, b]
        lo, hi = min(d * 0.75, d - 1000), max(d * 1.25, d + 1000)
        ok = Bset[(D[a, Bset] >= lo) & (D[a, Bset] <= hi)]
        ok = ok[[x not in mset for x in ok]]
        if len(ok):
            cands.append((a, ok))
    if not cands:
        continue
    ctrl = float(np.mean([np.mean([CAR[a] == CAR[crng.choice(ok)] for a, ok in cands]) for _ in range(NDRAW)]))
    h1.append({"stones": [SIG[i] for i in mem], "b_pairs": len(pairs), "precision": obs, "control": ctrl})
d1 = [x["precision"] - x["control"] for x in h1]
H1 = {"groups": len(h1), "mean_precision": float(np.mean([x["precision"] for x in h1])),
      "mean_control": float(np.mean([x["control"] for x in h1])), "median_diff": float(np.median(d1)),
      "better": int(sum(x > 0 for x in d1)), "worse": int(sum(x < 0 for x in d1)),
      "p": float(wilcoxon(d1, alternative="greater").pvalue) if any(d1) else 1.0}
H1["holds"] = H1["p"] < 0.05 and H1["median_diff"] > 0
signed = {IX[s] for s in corp.signum[corp.signed == 1]}


def pooled(idx_filter):
    co = [(a, b) for mem in groups.values() for k, a in enumerate(mem) for b in mem[k + 1:]
          if a in CAR and b in CAR and idx_filter(a) and idx_filter(b)]
    return {"pairs": len(co), "same_carver": float(np.mean([CAR[a] == CAR[b] for a, b in co])) if co else None}


H1_signed = pooled(lambda i: i in signed)
ALL_CERTAIN = pooled(lambda i: True)

# ======================================================================================================================
# 5. H2 – Runor 2020:s grupper (tolkade som i utdata/samma_hand/prov.py)
# ======================================================================================================================
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
        part = part.strip()
        rg = re.fullmatch(r"(\d+)\s*-\s*(\d+)", part)
        if rg:
            out += [f"{prefix} {k}" for k in range(int(rg.group(1)), int(rg.group(2)) + 1)]
        elif re.fullmatch(r"\d+[A-Za-z]?|Fv\d{4};\d+[A-Za-z]?", part):
            out.append(f"{prefix} {part}")
    return out


full = pd.read_csv(os.path.join(C, "corpus.csv"), low_memory=False)
full = full[full.lat.notna()]
certain_full = {r.signum: r.carver for r in full.itertuples() if isinstance(r.carver, str) and not r.carvers_uncertain}
att = json.load(open(os.path.join(C, "attribution.json"), encoding="utf-8"))
pred = {p["signum"]: p for p in att["predictions"]}
oof = pd.read_csv(os.path.join(C, "attribution_oof.csv"))
have = (set(pred) | set(oof.signum)) & set(full.signum)
links, notes, runor_note = [], {}, {}
for f in glob.glob(os.path.join(ROOT, "data", "cache", "runor", "*.json")):
    d = json.load(open(f, encoding="utf-8"))
    sig = f"{d['signum1']} {d['signum2']}".strip()
    if d.get("carver"):
        runor_note[sig] = "; ".join(f"{c.get('name')} ({c.get('attribution')})" for c in d["carver"])
    for cv in d.get("carver") or []:
        n = (cv.get("name") or "").strip()
        if SAME.match(n):
            notes.setdefault(sig, []).append(n)
            for o in referenced(n, d["signum1"]):
                links.append((sig, o))
parent = {}


def find(a):
    parent.setdefault(a, a)
    while parent[a] != a:
        parent[a] = parent[parent[a]]
        a = parent[a]
    return a


for a, b in links:
    if a in have and b in have and a != b:
        parent[find(a)] = find(b)
rgroups = defaultdict(set)
for s in parent:
    rgroups[find(s)].add(s)
rgroups = [sorted(v) for v in rgroups.values() if len(v) >= 2]
allix = np.arange(N)
h2 = []
for g in rgroups:
    if not any(s not in certain_full for s in g):
        continue
    gi = [IX[s] for s in g if s in IX]
    pairs = [(a, b) for k, a in enumerate(gi) for b in gi[k + 1:] if D[a, b] <= MAXD]
    if not pairs:
        continue
    obs = float(np.mean([LAB[a] == LAB[b] for a, b in pairs]))
    gset = set(gi)
    cands = []
    for a, b in pairs:
        for x, y in ((a, b), (b, a)):
            d = D[x, y]
            lo, hi = min(d * 0.75, d - 1000), min(max(d * 1.25, d + 1000), MAXD)
            ok = allix[(D[x] >= lo) & (D[x] <= hi)]
            ok = ok[[k not in gset and k != x for k in ok]]
            if len(ok):
                cands.append((x, ok))
    if not cands:
        continue
    ctrl = float(np.mean([np.mean([LAB[x] == LAB[crng.choice(ok)] for x, ok in cands]) for _ in range(NDRAW)]))
    h2.append({"stones": g, "pairs": len(pairs), "together": obs, "control": ctrl,
               "groups_of_stones": {SIG[i]: int(LAB[i]) for i in gi}})
d2 = [x["together"] - x["control"] for x in h2]
H2 = {"groups": len(h2), "mean_together": float(np.mean([x["together"] for x in h2])),
      "mean_control": float(np.mean([x["control"] for x in h2])), "median_diff": float(np.median(d2)),
      "better": int(sum(x > 0 for x in d2)), "worse": int(sum(x < 0 for x in d2)),
      "p": float(wilcoxon(d2, alternative="greater").pvalue) if any(d2) else 1.0}
H2["holds"] = H2["p"] < 0.05 and H2["median_diff"] > 0
DECISION = "kärnorna i appen och rapportutkast" if H1["holds"] and H2["holds"] else (
    "kärnorna redovisas, inte i appen" if H2["holds"] else "kärnorna redovisas inte som händer")

# ======================================================================================================================
# 6. Kärnorna (beskrivande)
# ======================================================================================================================
cores = []
for g, mem in groups.items():
    if len(mem) < 3:
        continue
    m = sorted(mem, key=lambda i: SIG[i])
    sub = E[np.ix_(m, m)][np.triu_indices(len(m), 1)]
    cert = {SIG[i]: CAR[i] for i in m if i in CAR}
    kinds = set(cert.values())
    typ = "okänd hand" if not kinds else (f"med {next(iter(kinds))}" if len(kinds) == 1 else "blandad")
    rows_ = corp.iloc[m]
    cores.append({"id": None, "type": typ, "size": len(m), "stones": [SIG[i] for i in m],
                  "mean_excess": float(np.nanmean(sub)), "diameter_km": float(D[np.ix_(m, m)].max() / 1000),
                  "provinces": dict(Counter(rows_.province)), "parishes": sorted(set(map(str, rows_.parish))),
                  "styles": dict(Counter(rows_["style"].fillna("–").astype(str))),
                  "certain": cert, "signed": [SIG[i] for i in m if i in signed],
                  "runor": {SIG[i]: runor_note[SIG[i]] for i in m if SIG[i] in runor_note},
                  "k0": {SIG[i]: (pred[SIG[i]]["top"], pred[SIG[i]].get("p_cal")) for i in m if SIG[i] in pred}})
cores.sort(key=lambda c: (-c["size"], -c["mean_excess"]))
for k, c in enumerate(cores, 1):
    c["id"] = f"K{k:03d}"
in_core = {s for c in cores for s in c["stones"]}
no_carver = [s for s in SIG if s not in certain]
desc = {"cores": len(cores), "types": dict(Counter(c["type"].split(" ")[0] for c in cores)),
        "sizes": dict(sorted(Counter(c["size"] for c in cores).items())),
        "stones_in_cores": len(in_core), "no_carver_stones": len(no_carver),
        "no_carver_in_cores": sum(1 for s in no_carver if s in in_core),
        "no_carver_in_cores_per_province": dict(Counter(corp.province[IX[s]] for s in no_carver if s in in_core).most_common()),
        "precision_all_certain": ALL_CERTAIN, "precision_signed_only": H1_signed,
        "U1015_1024": {s: (int(LAB[IX[s]]) if s in IX else None) for s in ["U 1015"] + [f"U {k}" for k in range(1017, 1025)]}}
res = {"plan": "analysplaner/2026-11-23-stenar-som-hor-ihop.md", "plan_sha": "0297bcbd", "corpus": "510ebfb3", "stones": N,
       "carvers_half_A": sorted(HALF_A), "carvers_half_B": sorted(HALF_B), "stones_A": len(A), "stones_B": len(B),
       "tau": TAU, "tau_choice": best_t, "tuning": tune, "H1": H1, "H1_signed_only": H1_signed, "H2": H2,
       "decision": DECISION, "descriptive": desc, "cores": cores, "H1_groups": h1, "H2_groups": h2}
json.dump(res, open(os.path.join(HERE, "resultat.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
with open(os.path.join(HERE, "karnor.csv"), "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["karna", "typ", "storlek", "signum", "landskap", "socken", "stil", "saker_ristare", "signerad",
                "k0_forslag", "k0_p_cal", "medeloverskott", "diameter_km"])
    for c in cores:
        for s in c["stones"]:
            i = IX[s]
            k0 = c["k0"].get(s, (None, None))
            w.writerow([c["id"], c["type"], c["size"], s, corp.province[i], corp.parish[i], corp["style"][i],
                        CAR.get(i, ""), int(i in signed), k0[0] or "", k0[1] if k0[1] is not None else "",
                        round(c["mean_excess"], 3), round(c["diameter_km"], 1)])
print(json.dumps({k: res[k] for k in ("tau", "tau_choice", "H1", "H1_signed_only", "H2", "decision")}, ensure_ascii=False, indent=1))
print(json.dumps(desc, ensure_ascii=False, indent=1))
for c in cores[:25]:
    print(c["id"], c["type"], c["size"], f"{c['mean_excess']:.2f}", f"{c['diameter_km']:.0f} km", ", ".join(c["stones"][:12]))
