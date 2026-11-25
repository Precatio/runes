"""Gräslund 1 (analysplaner/2026-11-25-graslund-1-stilgrupper.md): bär de kodade ornamentdragen stilgrupperna RAK, Fp,
Pr1–Pr5, och hur ser gränserna ut?

    .venv/bin/python utdata/graslund/graslund1.py
Skriver utdata/graslund/graslund1.json och stil_sannolikhet.csv (signum + sannolikheter).
"""
import hashlib
import json
import os
from collections import Counter

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import adjusted_rand_score
from sklearn.model_selection import GroupKFold

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
PLAN = os.path.join(ROOT, "analysplaner", "2026-11-25-graslund-1-stilgrupper.md")
assert hashlib.sha256(open(PLAN, "rb").read()).hexdigest().startswith(open(PLAN + ".sha256").read()[:8]), "planen ändrad"
SEED = 20261125
STYLES = ["RAK", "Fp", "Pr1", "Pr2", "Pr3", "Pr4", "Pr5"]
PR = {"Pr1": 1, "Pr2": 2, "Pr3": 3, "Pr4": 4, "Pr5": 5}

cons = json.load(open(os.path.join(ROOT, "data", "cache", "hander", "ornamentik", "orn_koder.json"), encoding="utf-8"))
fields = json.load(open(os.path.join(ROOT, "utdata", "nya_ristare", "ornamentik", "m2_utveckling.json"),
                        encoding="utf-8"))["godkända_fält"]
corp = pd.read_csv(os.path.join(ROOT, "data", "cache", "r", "corpus", "510ebfb3acc9a229", "corpus.csv"), low_memory=False)
corp["st"] = corp["style"].astype(str).str.replace("\xa0", " ").str.replace(" ", "")
meta = corp.set_index("signum")

sig = [s for s, c in cons.items() if sum(1 for f in fields if f in c) >= 3 and s in meta.index
       and meta.at[s, "st"] in STYLES]
y = np.array([meta.at[s, "st"] for s in sig])
groups = np.array([str(meta.at[s, "parish"]) if isinstance(meta.at[s, "parish"], str) else s for s in sig])
prov = np.array([s.split()[0] for s in sig])
cols = sorted({(f, v) for s in sig for f, v in cons[s].items() if f in fields})
col_ix = {c: i for i, c in enumerate(cols)}
X = np.zeros((len(sig), len(cols)))
for i, s in enumerate(sig):
    for f, v in cons[s].items():
        if (f, v) in col_ix:
            X[i, col_ix[(f, v)]] = 1
print(f"{len(sig)} stenar, {len(cols)} indikatorer; stilgrupper {dict(Counter(y))}")


def cv_proba(X, y, groups):
    P = np.zeros((len(y), len(STYLES)))
    for tr, te in GroupKFold(5).split(X, y, groups):
        m = LogisticRegression(C=1.0, max_iter=2000).fit(X[tr], y[tr])
        P[np.ix_(te, [STYLES.index(c) for c in m.classes_])] = m.predict_proba(X[te])
    return P


P = cv_proba(X, y, groups)
pred = np.array(STYLES)[P.argmax(1)]
acc = float(np.mean(pred == y))
base = Counter(y).most_common(1)[0][1] / len(y)
rng = np.random.default_rng(SEED)
null = []
for _ in range(999):
    yp = rng.permutation(y)
    null.append(float(np.mean(np.array(STYLES)[cv_proba(X, yp, groups).argmax(1)] == yp)))
p1 = (1 + sum(a >= acc for a in null)) / 1000
F1 = {"stenar": len(y), "träffsäkerhet": round(acc, 3), "vanligaste_gruppen": round(base, 3),
      "omblandning_medel": round(float(np.mean(null)), 3), "p": p1, "H1_håller": p1 < 0.05,
      "förväxlingar": {t: dict(Counter(pred[y == t])) for t in STYLES}}

# F2: felen inom Pr1–Pr5 – hamnar de hos grannen?
err = [(PR[t], PR[p]) for t, p in zip(y, pred) if t in PR and p in PR and t != p]
adj = float(np.mean([abs(a - b) == 1 for a, b in err])) if err else None
pt = np.array([b for _, b in err])
tt = np.array([a for a, _ in err])
nul2 = []
for _ in range(999):
    q = rng.permutation(pt)
    ok = q != tt
    nul2.append(float(np.mean(np.abs(tt[ok] - q[ok]) == 1)) if ok.any() else 0.0)
p2 = (1 + sum(a >= adj for a in nul2)) / 1000 if err else None
F2 = {"fel_inom_Pr": len(err), "andel_till_granne": round(adj, 3) if adj is not None else None,
      "omblandning_medel": round(float(np.mean(nul2)), 3), "p": p2, "H2_håller": bool(p2 is not None and p2 < 0.05),
      "avstånd": dict(Counter(abs(a - b) for a, b in err))}


# F3: latenta klasser (blandning av kategoriska fördelningar per fält, saknat = ingen information)
def lca(k, seed):
    r = np.random.default_rng(seed)
    F = [[(f, v) for (f, v) in cols if f == fld] for fld in fields]
    F = [fl for fl in F if fl]
    idx = [[col_ix[c] for c in fl] for fl in F]
    n = len(sig)
    R = r.dirichlet(np.ones(k), n)
    for _ in range(300):
        pi = R.mean(0) + 1e-9
        th = [(R.T @ X[:, ix] + 0.5) / ((R.T @ X[:, ix]).sum(1, keepdims=True) + 0.5 * len(ix)) for ix in idx]
        L = np.log(pi)[None, :].repeat(n, 0)
        for ix, t in zip(idx, th):
            L += X[:, ix] @ np.log(t).T
        mx = L.max(1, keepdims=True)
        ll = float((mx[:, 0] + np.log(np.exp(L - mx).sum(1))).sum())
        Rn = np.exp(L - mx)
        Rn /= Rn.sum(1, keepdims=True)
        if np.abs(Rn - R).max() < 1e-6:
            R = Rn
            break
        R = Rn
    npar = (k - 1) + k * sum(len(ix) - 1 for ix in idx)
    return ll, -2 * ll + npar * np.log(n), R, th, F


best = {}
for k in range(2, 10):
    runs = [lca(k, SEED + 100 * k + s) for s in range(20)]
    best[k] = max(runs, key=lambda r: r[0])
bic = {k: round(float(v[1]), 1) for k, v in best.items()}
kb = min(bic, key=bic.get)
ll, _, R, th, F = best[kb]
cl = R.argmax(1)
desc = []
for j in range(kb):
    top = []
    for fl, t in zip(F, th):
        i = int(np.argmax(t[j]))
        if t[j][i] >= 0.6:
            top.append(f"{fl[i][0]}={fl[i][1]} ({t[j][i]:.2f})")
    desc.append({"klass": j, "stenar": int((cl == j).sum()), "rundata": dict(Counter(y[cl == j])), "drag": top})
F3 = {"bic": bic, "k": kb, "ARI_mot_rundata": round(float(adjusted_rand_score(y, cl)), 3), "klasser": desc}

# F4: tränad på Uppland, prövad på Sö och Ög
up = prov == "U"
m = LogisticRegression(C=1.0, max_iter=2000).fit(X[up], y[up])
F4 = {"inom_uppland_cv": round(float(np.mean(pred[up] == y[up])), 3)}
for pv in ("Sö", "Ög"):
    o = prov == pv
    if o.sum():
        pp = m.predict(X[o])
        F4[pv] = {"stenar": int(o.sum()), "träffsäkerhet": round(float(np.mean(pp == y[o])), 3),
                  "per_grupp": {t: round(float(np.mean(pp[y[o] == t] == t)), 2) for t in STYLES if (y[o] == t).sum() >= 5}}

# F5: sannolikhet per sten
mx = P.max(1)
F5 = {t: {"stenar": int((y == t).sum()), "typiska_≥0,7": round(float(np.mean(mx[y == t] >= 0.7)), 2),
          "gränsfall_<0,4": round(float(np.mean(mx[y == t] < 0.4)), 2)} for t in STYLES}
pd.DataFrame(P.round(3), columns=STYLES).assign(signum=sig, rundata=y, modell=pred)[["signum", "rundata", "modell"] + STYLES] \
    .to_csv(os.path.join(HERE, "stil_sannolikhet.csv"), index=False)
out = {"plan": os.path.basename(PLAN), "F1": F1, "F2": F2, "F3": F3, "F4": F4, "F5": F5}
json.dump(out, open(os.path.join(HERE, "graslund1.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False, indent=1))
