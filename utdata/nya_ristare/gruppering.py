"""Medel 3: grupper med parmodellens sannolikheter (UTVECKLINGSARBETE – bara facits utvecklingsdel U).

Genomsnittlig länkning (UPGMA) på M1:s sannolikhet för samma hand, gruppens diameter ≤ 30 km. För varje gräns τ:
precision på namngivna par (par av säkra stenar i samma grupp med samma ristare) och täckning av utvecklingsdelens
facitpar (andel som hamnar i samma grupp), samt grannkontrollen: andel av facitparens grannar på samma avstånd som hamnar i
samma grupp.

    .venv/bin/python utdata/nya_ristare/gruppering.py
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
from utdata.nya_ristare.belagg import MAXD, load  # noqa: E402

st = load()
N = len(st.sig)
M = np.load(os.path.join(ROOT, "data", "cache", "hander", "parsannolikhet_M1.npy")).astype(float)
split = json.load(open(os.path.join(HERE, "delning.json"), encoding="utf-8"))
dev = [[st.ix[s] for s in g["stenar"] if s in st.ix] for g in split["grupper"] if g["del"] == "U"]
dev = [g for g in dev if len(g) >= 2]
cert = {st.ix[s]: c for s, c in st.certain.items() if s in st.ix}

SUM = np.nan_to_num(M, nan=0.0)
CNT = (~np.isnan(M)).astype(float)
MX = st.D.copy()
active = np.ones(N, bool)


def rows(r):
    with np.errstate(invalid="ignore", divide="ignore"):
        s = np.where((CNT[r] > 0) & (MX[r] <= MAXD), SUM[r] / CNT[r], -np.inf)
    s[:, ~active] = -np.inf
    s[np.arange(len(r)), r] = -np.inf
    return s


SC = rows(np.arange(N))
merges = []
while True:
    k = int(np.argmax(SC))
    i, j = divmod(k, N)
    best = SC[i, j]
    if not np.isfinite(best) or best < 0.05:
        break
    merges.append((i, j, float(best)))
    SUM[i] += SUM[j]; SUM[:, i] = SUM[i]
    CNT[i] += CNT[j]; CNT[:, i] = CNT[i]
    MX[i] = np.maximum(MX[i], MX[j]); MX[:, i] = MX[i]
    active[j] = False
    SC[j, :] = -np.inf; SC[:, j] = -np.inf
    r = rows(np.array([i]))[0]
    SC[i] = r; SC[:, i] = r


def labels_at(t):
    lab = np.arange(N)
    for i, j, s in merges:
        if s < t:
            break
        lab[lab == lab[j]] = lab[i]
    return lab


rng = np.random.default_rng(2026)
ci = np.array(sorted(cert))
out = []
for t in [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2]:
    lab = labels_at(t)
    same = lab[ci][:, None] == lab[ci][None, :]
    sc = np.array([cert[i] for i in ci])
    samec = sc[:, None] == sc[None, :]
    tri = np.triu(np.ones_like(same), 1).astype(bool)
    co = same & tri
    prec = (co & samec).sum() / max(co.sum(), 1)
    rec_named = (co & samec).sum() / (samec & tri & (st.D[np.ix_(ci, ci)] <= MAXD)).sum()
    fp, fc = [], []
    for g in dev:
        for x in range(len(g)):
            for y in range(x + 1, len(g)):
                a, b = g[x], g[y]
                if st.D[a, b] > MAXD:
                    continue
                fp.append(lab[a] == lab[b])
                d = st.D[a, b]
                lo, hi = min(d * 0.75, d - 1000), min(max(d * 1.25, d + 1000), MAXD)
                ok = np.where((st.D[a] >= lo) & (st.D[a] <= hi))[0]
                ok = ok[~np.isin(ok, g)]
                if len(ok):
                    fc.append(np.mean(lab[ok] == lab[a]))
    sizes = np.bincount(lab)
    sizes = sizes[sizes > 0]
    r = {"tau": t, "precision_namngivna": round(float(prec), 3), "täckning_namngivna": round(float(rec_named), 3),
         "facit_samma_grupp": round(float(np.mean(fp)), 3), "grannar_samma_grupp": round(float(np.mean(fc)), 3),
         "grupper_minst3": int((sizes >= 3).sum()), "stenar_i_grupper_minst3": int(sizes[sizes >= 3].sum()),
         "största": int(sizes.max())}
    out.append(r)
    print(r)
json.dump(out, open(os.path.join(HERE, "gruppering_utveckling.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
np.save(os.path.join(ROOT, "data", "cache", "hander", "sammanslagningar_M1.npy"), np.array(merges))
