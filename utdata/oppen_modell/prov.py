"""En öppen ristarmodell – får "okänd hand" bli ett svar? (analysplaner/2026-11-19-oppen-ristarmodell.md, sha 091e6cba,
låst i 7ced6eb). K0 = den slutna modellen (korpus 510ebfb3, attribution.json + attribution_oof.csv); O behåller K0:s
ristare k bara om p_cal ≥ 0,5 OCH stenen liknar k:s säkra stenar inom 30 km i textdragen (högsta överskottslikhet ≥ t,
t från utdata/nya_hander, vald på namngivna ristare utan Runor). O1 mot Runor 2020:s grupper (som utdata/samma_hand),
O2 priset bland säkra stenar. Skriver resultat.json och resultat.md.
    .venv/bin/python utdata/oppen_modell/prov.py"""
import glob
import hashlib
import json
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

PLAN = os.path.join(ROOT, "analysplaner", "2026-11-19-oppen-ristarmodell.md")
assert hashlib.sha256(open(PLAN, "rb").read()).hexdigest().startswith("091e6cba"), "planen är ändrad efter låsningen"
C = os.path.join(ROOT, "data", "cache", "r", "corpus", "510ebfb3acc9a229")
NDRAW = 999
MAXD = 30000.0
P_MIN = 0.5
A_CAL = 1.8                       # r/attribution.R: calibrate <- P^A_CAL renormalised
T_LINK = json.load(open(os.path.join(ROOT, "utdata", "nya_hander", "resultat.json"), encoding="utf-8"))["threshold"]["t"]
assert round(T_LINK, 3) == -0.010
UNK = "okänd hand"

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
xyf = np.array(Transformer.from_crs(4326, 3006, always_xy=True).transform(corp.lon.values, corp.lat.values)).T
S = 0.5 * (np.asarray((X @ X.T).todense()) + T @ T.T)
D = np.hypot(xyf[:, None, 0] - xyf[None, :, 0], xyf[:, None, 1] - xyf[None, :, 1])
EX = {}
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
        EX[(a, b)] = sa[b] - tot / n if n > 0 else np.nan
exs = {}
for (a, b), v in EX.items():
    if a < b:
        w = EX.get((b, a))
        exs[(a, b)] = 0.5 * (v + w) if w is not None else v
del EX


def ex_sig(s, t):
    """Överskottslikheten mellan två stenar (signum); nan om någon saknar textdrag eller avståndet > 30 km."""
    if s not in IX or t not in IX:
        return np.nan
    a, b = IX[s], IX[t]
    return exs.get((min(a, b), max(a, b)), np.nan)


def linked(s, t):
    v = ex_sig(s, t)
    return not np.isnan(v) and v >= T_LINK


# ======================================================================================================================
# 2. K0 och O
# ======================================================================================================================
full = pd.read_csv(os.path.join(C, "corpus.csv"), low_memory=False)
full = full[full.lat.notna()]
certain = {r.signum: r.carver for r in full.itertuples() if isinstance(r.carver, str) and not r.carvers_uncertain}
xy = dict(zip(full.signum, zip(*Transformer.from_crs(4326, 3006, always_xy=True).transform(full.lon.values, full.lat.values))))
att = json.load(open(os.path.join(C, "attribution.json"), encoding="utf-8"))
top, pcal = {}, {}
for p in att["predictions"]:
    top[p["signum"]], pcal[p["signum"]] = p["top"], p.get("p_cal")
oof = pd.read_csv(os.path.join(C, "attribution_oof.csv"))
pc = [c for c in oof.columns if c.startswith(".pred_")]
oofm = oof.groupby("signum")[pc].mean()
Q = oofm.to_numpy(float) ** A_CAL
Q = Q / np.maximum(Q.sum(1, keepdims=True), 1e-300)
oof_top = {}
for (sig, row), q in zip(oofm.iterrows(), Q):
    k = int(np.argmax(row.to_numpy()))
    oof_top[sig] = pc[k][len(".pred_"):]
    if sig not in top:                                  # säkra stenar: K0:s förslag utanför vikten
        top[sig], pcal[sig] = oof_top[sig], float(q[k])
by_carver = {}
for s, c in certain.items():
    if s in IX:
        by_carver.setdefault(c, []).append(s)


def best_excess(s, k):
    """Högsta överskottslikheten mellan s och k:s säkra stenar inom 30 km (s själv utesluten); nan om ingen finns."""
    v = [ex_sig(s, t) for t in by_carver.get(k, []) if t != s]
    v = [x for x in v if not np.isnan(x)]
    return max(v) if v else np.nan


def answer(s, use1=True, use2=True):
    k, p = top.get(s), pcal.get(s)
    if k is None:
        return UNK
    if use1 and (p is None or p < P_MIN):
        return UNK
    if use2:
        b = best_excess(s, k)
        if np.isnan(b) or b < T_LINK:
            return UNK
    return k


# ======================================================================================================================
# 3. O1 – Runor 2020:s grupper (grupperna, kontrollerna och fröet som i utdata/samma_hand/prov.py)
# ======================================================================================================================
SAME = re.compile(r"^(Samma som|Samma ristare som|Troligen samma|Antagligen samma|Förmodligen samma|Eventuellt samma)", re.I)
PREFIX = re.compile(r"^(U|Sö|Ög|Vg|Sm|Öl|G|Vs|Nä|Gs|Hs|M|D|Vr|Ån|J|Bo|DR|N|Sk|Bl|Hl)$")
have = {s for s in top if s in xy}


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


links, notes = [], {}
for f in glob.glob(os.path.join(ROOT, "data", "cache", "runor", "*.json")):
    d = json.load(open(f, encoding="utf-8"))
    sig = f"{d['signum1']} {d['signum2']}".strip()
    for cv in d.get("carver") or []:
        n = (cv.get("name") or "").strip()
        if SAME.match(n):
            notes.setdefault(sig, []).append(n)
            for o in referenced(n, d["signum1"]):
                links.append((sig, o, bool(cv.get("certainty"))))


def groups(use_links):
    parent = {}

    def find(a):
        parent.setdefault(a, a)
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for a, b, _ in use_links:
        if a in have and b in have and a != b:
            parent[find(a)] = find(b)
    g = {}
    for s in parent:
        g.setdefault(find(s), set()).add(s)
    return [sorted(v) for v in g.values() if len(v) >= 2]


ALL = sorted(have)
P = np.array([xy[s] for s in ALL])
IDX = {s: i for i, s in enumerate(ALL)}


def run_o1(use1, use2, seed=2026):
    rng = np.random.default_rng(seed)
    ans = {s: answer(s, use1, use2) for s in ALL}

    def agree(a, b):
        if ans[a] == UNK and ans[b] == UNK:
            return linked(a, b)
        return ans[a] == ans[b]
    out = []
    for g in groups(links):
        unnamed = any(s not in certain for s in g)
        if not unnamed:
            continue
        pairs = [(a, b) for i, a in enumerate(g) for b in g[i + 1:]]
        obs = float(np.mean([agree(a, b) for a, b in pairs]))
        gset = {IDX[s] for s in g}
        cand = []
        for a, b in pairs:
            for s, t in ((a, b), (b, a)):
                d = float(np.hypot(*(np.array(xy[s]) - np.array(xy[t]))))
                dd = np.hypot(*(P - np.array(xy[s])).T)
                lo, hi = min(d * 0.75, d - 1000), max(d * 1.25, d + 1000)
                ok = np.where((dd >= lo) & (dd <= hi))[0]
                ok = np.array([k for k in ok if k not in gset])
                if len(ok):
                    cand.append((s, ok))
        draws = [np.mean([agree(s, ALL[rng.choice(ok)]) for s, ok in cand]) if cand else np.nan for _ in range(NDRAW)]
        out.append({"stones": g, "obs": obs, "ctrl": float(np.nanmean(draws)) if cand else None, "pairs": len(pairs),
                    "answers": {s: ans[s] for s in g}, "k0": {s: top[s] for s in g},
                    "rundata": {s: certain.get(s) for s in g}})
    diff = [x["obs"] - x["ctrl"] for x in out if x["ctrl"] is not None]
    w = wilcoxon(diff, alternative="greater") if len(diff) >= 5 and any(diff) else None
    summ = {"groups": len(diff), "mean_obs": float(np.mean([x["obs"] for x in out if x["ctrl"] is not None])),
            "mean_ctrl": float(np.mean([x["ctrl"] for x in out if x["ctrl"] is not None])),
            "median_diff": float(np.median(diff)), "better": int(sum(d > 0 for d in diff)),
            "worse": int(sum(d < 0 for d in diff)), "p": float(w.pvalue) if w else None}
    return out, summ


o1_groups, O1 = run_o1(True, True)
O1["holds"] = O1["p"] is not None and O1["p"] < 0.05
O1_only1 = run_o1(True, False)[1]
O1_only2 = run_o1(False, True)[1]

# ======================================================================================================================
# 4. O2 – priset bland säkra stenar (K0 utanför vikten)
# ======================================================================================================================
sure = [s for s in certain if s in oof_top]
right = [s for s in sure if oof_top[s] == certain[s]]
kept = [s for s in right if answer(s) == certain[s]]
O2 = {"sure_stones": len(sure), "k0_right": len(right), "k0_accuracy": len(right) / len(sure),
      "kept_right": len(kept), "kept_share": len(kept) / len(right)}
O2["holds"] = O2["kept_share"] >= 0.75
lost_by = Counter(certain[s] for s in right if s not in kept)
O2["lost_by_carver"] = dict(lost_by.most_common())
O2["kept_wrong"] = sum(1 for s in sure if oof_top[s] != certain[s] and answer(s) not in (UNK,))
O2["k0_wrong"] = len(sure) - len(right)
DECISION = O1["holds"] and O2["holds"]

# ======================================================================================================================
# 5. Beskrivande
# ======================================================================================================================
nocarv = [p["signum"] for p in att["predictions"]]
ans_nc = {s: answer(s) for s in nocarv}
prov = {p["signum"]: p["province"] for p in att["predictions"]}
k0_kept = {s for s in nocarv if pcal.get(s) is not None and pcal[s] >= P_MIN}
desc = {"stones_without_certain_carver": len(nocarv), "k0_suggestion_p_ge_05": len(k0_kept),
        "o_known": sum(1 for v in ans_nc.values() if v != UNK), "o_unknown": sum(1 for v in ans_nc.values() if v == UNK),
        "unknown_per_province": dict(Counter(prov[s] for s, v in ans_nc.items() if v == UNK).most_common()),
        "known_per_province": dict(Counter(prov[s] for s, v in ans_nc.items() if v != UNK).most_common()),
        "k0_suggestions_lost_by_condition2": dict(Counter(top[s] for s in k0_kept if ans_nc[s] == UNK).most_common()),
        "no_text_features": sum(1 for s in nocarv if s not in IX)}
u1015 = {s: {"k0": top.get(s), "p_cal": pcal.get(s), "o": answer(s),
             "best_excess": None if s not in IX or top.get(s) is None else
             (None if np.isnan(best_excess(s, top[s])) else round(float(best_excess(s, top[s])), 3))}
         for s in ["U 1015"] + [f"U {k}" for k in range(1017, 1025)]}

res = {"plan": "analysplaner/2026-11-19-oppen-ristarmodell.md", "plan_sha": "091e6cba", "corpus": "510ebfb3",
       "t_link": T_LINK, "p_min": P_MIN, "stones_with_text": N, "O1": O1, "O1_only_condition1": O1_only1,
       "O1_only_condition2": O1_only2, "O2": O2, "decision_replace_k0": DECISION, "descriptive": desc,
       "U1015_1024": u1015, "O1_groups": o1_groups}
json.dump(res, open(os.path.join(HERE, "resultat.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: res[k] for k in ("O1", "O1_only_condition1", "O1_only_condition2", "O2", "decision_replace_k0",
                                      "descriptive", "U1015_1024")}, ensure_ascii=False, indent=1))
