"""Skrev och ritade samma hand? (analysplaner/2026-11-25-skrev-och-ritade.md) – stavning mot ornamentik på samma runstenar.

    .venv/bin/python utdata/graslund/skrev_ritade.py
Skriver utdata/graslund/skrev_ritade.json.
"""
import hashlib
import json
import os
import sys
from collections import Counter, defaultdict

import numpy as np
import pandas as pd
from scipy import sparse
from scipy.stats import rankdata, spearmanr

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
from src import orthography  # noqa: E402
from utdata.nya_ristare.belagg import MAXD, load  # noqa: E402

PLAN = os.path.join(ROOT, "analysplaner", "2026-11-25-skrev-och-ritade.md")
assert hashlib.sha256(open(PLAN, "rb").read()).hexdigest().startswith(open(PLAN + ".sha256").read()[:8]), "planen ändrad"
SEED = 20261125
STYLES = {"RAK", "Fp", "Pr1", "Pr2", "Pr3", "Pr4", "Pr5"}
rng = np.random.default_rng(SEED)

st = load()
corp = st.corp
SIG, N = st.sig, len(st.sig)
FIELDS = json.load(open(os.path.join(ROOT, "utdata", "nya_ristare", "ornamentik", "m2_utveckling.json"),
                        encoding="utf-8"))["godkända_fält"]
cons = json.load(open(os.path.join(ROOT, "data", "cache", "hander", "ornamentik", "orn_koder.json"), encoding="utf-8"))

# --- stavningsprofil (som belagg.py) och språkdrag ---
recs = {r["signum"]: r for r in json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["inscriptions"]}
names_f = orthography.name_forms(list(recs.values()))
feats = [orthography.features(recs[s], names_f) for s in SIG]
has_text = np.array([f["n_words"] >= 3 for f in feats])
vocab, rows, cols, vals = {}, [], [], []
for i, f in enumerate(feats):
    if has_text[i]:
        for k, v in f["counts"].items():
            j = vocab.setdefault(k, len(vocab))
            rows.append(i), cols.append(j), vals.append(float(v))
X = sparse.csr_matrix((vals, (rows, cols)), shape=(N, len(vocab)))
df = np.asarray((X > 0).sum(0)).ravel()
X = X.multiply(np.log((1 + has_text.sum()) / (1 + df)) + 1).tocsr()
X = sparse.diags(1 / np.maximum(np.sqrt(np.asarray(X.multiply(X).sum(1)).ravel()), 1e-12)) @ X
S_orto = np.asarray((X @ X.T).todense())
tc = [c for c in corp.columns if c.startswith(("trait_", "cat_", "pm_"))]
T = corp[tc].apply(pd.to_numeric, errors="coerce").fillna(0).to_numpy(float)
Tm, Ts = T[has_text].mean(0), T[has_text].std(0)
T = (T - Tm) / np.where(Ts > 0, Ts, 1)
T = T / np.maximum(np.linalg.norm(T, axis=1, keepdims=True), 1e-12)
S_trait = T @ T.T

# --- ornamentlikhet ---
V = {f: np.array([cons.get(s, {}).get(f) for s in SIG], dtype=object) for f in FIELDS}
nf = np.zeros((N, N))
mf = np.zeros((N, N))
for f in FIELDS:
    has = np.array([v is not None for v in V[f]])
    both = has[:, None] & has[None, :]
    nf += both
    mf += both & (V[f][:, None] == V[f][None, :])
with np.errstate(invalid="ignore", divide="ignore"):
    S_orn = np.where(nf >= 3, mf / nf, np.nan)
has_orn = np.array([sum(1 for f in FIELDS if V[f][i] is not None) >= 3 for i in range(N)])

style = corp["style"].astype(str).str.replace("\xa0", " ").str.replace(" ", "").to_numpy()
district = corp["district"].astype(str).to_numpy()
parish = corp["parish"].astype(str).to_numpy()
prov = np.array([s.split()[0] for s in SIG])
ok = has_text & has_orn & np.isin(style, list(STYLES))
idx = np.where(ok)[0]
iu, ju = np.triu_indices(len(idx), 1)
I, J = idx[iu], idx[ju]
sel = (st.D[I, J] <= MAXD) & (style[I] == style[J])
I, J = I[sel], J[sel]
print(f"{ok.sum()} stenar med båda måtten och stilgrupp; {len(I)} par inom 30 km i samma stilgrupp")

# omblandning inom härad × stilgrupp (bland stenarna i ok)
strata = defaultdict(list)
for i in idx:
    key = (district[i] if district[i] not in ("nan", "None", "") else prov[i], style[i])
    strata[key].append(i)


def permuted():
    p = np.arange(N)
    for members in strata.values():
        if len(members) > 1:
            p[members] = rng.permutation(members)
    return p


def stat(I, J, S_text, perm=None):
    so = S_orn[I, J] if perm is None else S_orn[perm[I], perm[J]]
    m = ~np.isnan(so)
    return float(spearmanr(S_text[I, J][m], so[m]).correlation), int(m.sum())


def pair_test(I, J, S_text, n=999):
    obs, npairs = stat(I, J, S_text)
    null = np.array([stat(I, J, S_text, permuted())[0] for _ in range(n)])
    p = (1 + np.sum(null >= obs)) / (n + 1)
    return {"par": npairs, "rho": round(obs, 4), "omblandning_medel": round(float(null.mean()), 4),
            "omblandning_95": round(float(np.quantile(null, 0.95)), 4), "p": float(p), "håller": bool(obs > 0 and p < 0.05)}


P1 = pair_test(I, J, S_orto)
pr4 = style[I] == "Pr4"
P3 = pair_test(I[pr4], J[pr4], S_orto)
besk = {"P1_språkdrag": pair_test(I, J, S_trait)}
nosame = parish[I] != parish[J]
besk["P1_utan_samma_socken"] = pair_test(I[nosame], J[nosame], S_orto)
besk["per_stilgrupp"] = {}
for s in sorted(STYLES):
    m = style[I] == s
    if m.sum() >= 30:
        r, n = stat(I[m], J[m], S_orto)
        besk["per_stilgrupp"][s] = {"par": n, "rho": round(r, 3)}
print("P1", P1, "\nP3", P3)

# --- P2: ristarna som enheter (bara signerade stenar) ---
by_c = defaultdict(list)
for i in idx:
    s = SIG[i]
    if s in st.signed and s in st.certain:
        by_c[st.certain[s]].append(i)
carv = sorted(c for c, v in by_c.items() if len(v) >= 5)
P2 = {"ristare": len(carv), "stenar": {c: len(by_c[c]) for c in carv}}
if len(carv) >= 3:
    tx = np.vstack([np.asarray(X[by_c[c]].mean(0)).ravel() for c in carv])
    tx /= np.maximum(np.linalg.norm(tx, axis=1, keepdims=True), 1e-12)
    Dt = 1 - tx @ tx.T
    dist_o = np.zeros((len(carv), len(carv)))
    for a in range(len(carv)):
        for b in range(len(carv)):
            tv = []
            for f in FIELDS:
                va = [V[f][i] for i in by_c[carv[a]] if V[f][i] is not None]
                vb = [V[f][i] for i in by_c[carv[b]] if V[f][i] is not None]
                if va and vb:
                    ca, cb = Counter(va), Counter(vb)
                    tv.append(0.5 * sum(abs(ca[k] / len(va) - cb[k] / len(vb)) for k in set(ca) | set(cb)))
            dist_o[a, b] = np.mean(tv) if tv else np.nan
    # geografiskt avstånd mellan ristare: medel av avstånden mellan deras stenar
    Dg = np.array([[np.mean(st.D[np.ix_(by_c[a], by_c[b])]) for b in carv] for a in carv])
    tri = np.triu_indices(len(carv), 1)

    def partial(dt, do, dg):
        m = ~np.isnan(do)
        rt, ro, rg = rankdata(dt[m]), rankdata(do[m]), rankdata(dg[m])
        A = np.column_stack([np.ones(m.sum()), rg])
        et = rt - A @ np.linalg.lstsq(A, rt, rcond=None)[0]
        eo = ro - A @ np.linalg.lstsq(A, ro, rcond=None)[0]
        return float(np.corrcoef(et, eo)[0, 1])

    obs = partial(Dt[tri], dist_o[tri], Dg[tri])
    null = []
    for _ in range(9999):
        p = rng.permutation(len(carv))
        null.append(partial(Dt[tri], dist_o[np.ix_(p, p)][tri], Dg[tri]))
    pval = (1 + np.sum(np.array(null) >= obs)) / 10000
    P2.update({"partiell_mantel_rho": round(obs, 3), "p": float(pval),
               "håller": bool(len(carv) >= 8 and obs > 0 and pval < 0.05), "bara_beskrivande": len(carv) < 8})
    rt = rankdata(Dt.mean(1))
    ro = rankdata(np.nanmean(np.where(np.eye(len(carv)) == 1, np.nan, dist_o), 1))
    P2["avvikare"] = sorted([{"ristare": c, "rang_stavning": int(rt[k]), "rang_ornamentik": int(ro[k])}
                             for k, c in enumerate(carv)], key=lambda x: -abs(x["rang_stavning"] - x["rang_ornamentik"]))[:5]
print("P2", {k: v for k, v in P2.items() if k != "stenar"})
out = {"plan": os.path.basename(PLAN), "stenar": int(ok.sum()), "P1": P1, "P2": P2, "P3": P3, "beskrivande": besk}
json.dump(out, open(os.path.join(HERE, "skrev_ritade.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(besk, ensure_ascii=False, indent=1))
