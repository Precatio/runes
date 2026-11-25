"""Följer runstenens budskap dess bild? Bekräftande prov på ett oberoende urval (analysplaner/2026-11-25-budskap-och-bild.md).

    .venv/bin/python utdata/graslund/budskap_bild.py
Skriver utdata/graslund/budskap_bild.json.
"""
import hashlib
import json
import os
import sys
from collections import defaultdict

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
from src import orthography  # noqa: E402
from utdata.nya_ristare.belagg import MAXD, load  # noqa: E402

PLAN = os.path.join(ROOT, "analysplaner", "2026-11-25-budskap-och-bild.md")
assert hashlib.sha256(open(PLAN, "rb").read()).hexdigest().startswith(open(PLAN + ".sha256").read()[:8]), "planen ändrad"
SEED = 20261125
STYLES = {"RAK", "Fp", "Pr1", "Pr2", "Pr3", "Pr4", "Pr5"}
MSG = ["cat_minne", "cat_bro_vag", "cat_fard", "cat_arv", "cat_ting", "cat_magisk", "cat_grans",
       "pm_neutral", "pm_signatur", "pm_bro", "pm_fard", "pm_arv"]
MARK = ["pm_stungna", "pm_monoftong", "pm_o_runa", "pm_r_for_R"]
C = os.path.join(ROOT, "data", "cache", "hander", "ornamentik")
FIELDS = json.load(open(os.path.join(ROOT, "utdata", "nya_ristare", "ornamentik", "m2_utveckling.json"),
                        encoding="utf-8"))["godkända_fält"]
rng = np.random.default_rng(SEED)

st = load()
SIG, N, corp = st.sig, len(st.sig), st.corp
recs = {r["signum"]: r for r in json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["inscriptions"]}
names_f = orthography.name_forms(list(recs.values()))
has_text = np.array([orthography.features(recs[s], names_f)["n_words"] >= 3 for s in SIG])
style = corp["style"].astype(str).str.replace("\xa0", " ").str.replace(" ", "").to_numpy()
district = corp["district"].astype(str).to_numpy()
prov = np.array([s.split()[0] for s in SIG])

plate = json.load(open(os.path.join(C, "orn_koder.json"), encoding="utf-8"))
ext = json.load(open(os.path.join(C, "orn_koder_utvidgning.json"), encoding="utf-8"))
lost = {k: v["koder"] for k, v in json.load(open(os.path.join(C, "orn_koder_forlorade.json"), encoding="utf-8")).items()}
first = {s for s in plate if s in st.ix and len(plate[s]) >= 3 and has_text[st.ix[s]] and style[st.ix[s]] in STYLES}
codes = {}
for s, c in plate.items():
    if s not in first:
        codes[s] = ("plansch", {f: v for f, v in c.items() if f in FIELDS})
for s, c in ext.items():
    codes.setdefault(s, ("utvidgning", {f: v for f, v in c.items() if f in FIELDS}))
for s, c in lost.items():
    codes.setdefault(s, ("teckning", c))
idx = np.array([st.ix[s] for s, (k, c) in codes.items() if s in st.ix and len(c) >= 3 and has_text[st.ix[s]]])
src = np.array([codes[SIG[i]][0] for i in idx])
print(f"oberoende urval: {len(idx)} stenar", dict(zip(*np.unique(src, return_counts=True))))

V = {f: np.array([codes.get(s, ("", {}))[1].get(f) for s in SIG], dtype=object) for f in FIELDS}
nf, mf = np.zeros((N, N)), np.zeros((N, N))
for f in FIELDS:
    has = np.array([v is not None for v in V[f]])
    both = has[:, None] & has[None, :]
    nf += both
    mf += both & (V[f][:, None] == V[f][None, :])
with np.errstate(invalid="ignore", divide="ignore"):
    S_orn = np.where(nf >= 3, mf / nf, np.nan)


def profile_sim(cols):
    T = corp[cols].apply(pd.to_numeric, errors="coerce").fillna(0).to_numpy(float)
    Tm, Ts = T[has_text].mean(0), T[has_text].std(0)
    T = (T - Tm) / np.where(Ts > 0, Ts, 1)
    T = T / np.maximum(np.linalg.norm(T, axis=1, keepdims=True), 1e-12)
    return T @ T.T


iu, ju = np.triu_indices(len(idx), 1)
I, J = idx[iu], idx[ju]
near = st.D[I, J] <= MAXD
I, J = I[near], J[near]
srcof = {i: codes[SIG[i]][0] for i in idx}


def strata_of(keyf):
    s = defaultdict(list)
    for i in idx:
        s[keyf(i)].append(i)
    return s


def dist_key(i):
    return district[i] if district[i] not in ("nan", "None", "") else prov[i]


def test(I, J, S, strata, n=999):
    def stat(perm=None):
        so = S_orn[I, J] if perm is None else S_orn[perm[I], perm[J]]
        m = ~np.isnan(so)
        return float(spearmanr(S[I, J][m], so[m]).correlation), int(m.sum())

    def permuted():
        p = np.arange(N)
        for mem in strata.values():
            if len(mem) > 1:
                p[mem] = rng.permutation(mem)
        return p

    obs, npairs = stat()
    null = np.array([stat(permuted())[0] for _ in range(n)])
    pv = (1 + np.sum(null >= obs)) / (n + 1)
    return {"par": npairs, "rho": round(obs, 4), "omblandning_medel": round(float(null.mean()), 4),
            "omblandning_95": round(float(np.quantile(null, 0.95)), 4), "p": float(pv), "håller": bool(obs > 0 and pv < 0.05)}


S_msg = profile_sim(MSG)
ds = strata_of(lambda i: (dist_key(i), srcof[i]))
B1 = test(I, J, S_msg, ds)
print("B1", B1)
besk = {}
sty = np.isin(style[I], list(STYLES)) & (style[I] == style[J])
besk["samma_stilgrupp"] = test(I[sty], J[sty], S_msg, strata_of(lambda i: (dist_key(i), style[i], srcof[i])), n=499)
besk["per_källa"] = {}
for k in ("plansch", "teckning"):
    m = np.array([srcof[a] == k and srcof[b] == k for a, b in zip(I, J)])
    if m.sum() >= 100:
        besk["per_källa"][k] = test(I[m], J[m], S_msg, ds, n=499)
besk["språkmarkörer"] = test(I, J, profile_sim(MARK), ds, n=499)
besk["utan_kategori"] = {}
for c in MSG:
    S = profile_sim([x for x in MSG if x != c])
    so = S_orn[I, J]
    m = ~np.isnan(so)
    besk["utan_kategori"][c] = round(float(spearmanr(S[I, J][m], so[m]).correlation), 4)
out = {"plan": os.path.basename(PLAN), "stenar": int(len(idx)), "källor": {k: int((src == k).sum()) for k in set(src)},
       "B1": B1, "beskrivande": besk}
json.dump(out, open(os.path.join(HERE, "budskap_bild.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(besk, ensure_ascii=False, indent=1))
