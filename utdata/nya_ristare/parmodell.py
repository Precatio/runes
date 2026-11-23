"""Medel 2: en inlärd parmodell för samma hand (analysplaner/2026-11-23-nya-ristare-program.md). UTVECKLINGSARBETE – använder
bara facits utvecklingsdel (U); provdelen (P) öppnas inte här.

Par = stenpar inom 30 km. Belägg = utdata/nya_ristare/belagg.py + avståndet. Träning: par där båda stenarna har en säker
ristare i Rundata (samma ristare = 1), men inga par inom en facitgrupp (så att facit inte läcker in). Modellerna jämförs på
utvecklingsdelens grupper: för varje facitpar (a, b) rangordnas b bland alla stenar på samma avstånd från a (± 25 %, minst
± 1 km) som inte hör till gruppen; måttet är percentilen (1 = högst av alla), medel per grupp, median över grupperna.

    .venv/bin/python utdata/nya_ristare/parmodell.py
"""
import json
import os
import sys

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
from utdata.nya_ristare.belagg import MAXD, load  # noqa: E402

st = load()
N = len(st.sig)
split = json.load(open(os.path.join(HERE, "delning.json"), encoding="utf-8"))
dev_groups = [[st.ix[s] for s in g["stenar"] if s in st.ix] for g in split["grupper"] if g["del"] == "U"]
dev_groups = [g for g in dev_groups if len(g) >= 2]
in_group = {}
for k, g in enumerate(dev_groups):
    for i in g:
        in_group[i] = k
test_stones = {st.ix[s] for g in split["grupper"] if g["del"] == "P" for s in g["stenar"] if s in st.ix}

iu, ju = np.triu_indices(N, 1)
near = st.D[iu, ju] <= MAXD
I, J = iu[near], ju[near]
FEATS = st.pair_names + ["d_km"]


def X_of(names, I, J):
    cols = [st.P[n][I, J] for n in names if n != "d_km"]
    if "d_km" in names:
        cols.append(st.D[I, J] / 1000)
    return np.column_stack(cols).astype(np.float32)


cert = {st.ix[s]: c for s, c in st.certain.items() if s in st.ix}
lab = np.array([cert.get(i) is not None and cert.get(j) is not None for i, j in zip(I, J)])
y_all = np.array([cert.get(i) == cert.get(j) for i, j in zip(I, J)])
same_group = np.array([i in in_group and in_group.get(i) == in_group.get(j) for i, j in zip(I, J)])
touch_test = np.array([i in test_stones or j in test_stones for i, j in zip(I, J)])
train = lab & ~same_group & ~touch_test
print(f"{len(I)} par inom 30 km; träningspar {train.sum()} (samma ristare {y_all[train].sum()})")

MODELS = {
    "M0 text (överskott)": None,
    "M1 alla belägg": FEATS,
    "M2 utan text": [f for f in FEATS if not f.startswith("ex_")],
    "M3 text + stil + kors": ["ex_text", "ex_orto", "ex_trait", "same_style", "style_gap", "cross_jaccard", "d_km"],
    "M5 alla belägg, bara signerade": FEATS,
}
signed_ix = {st.ix[s] for s in st.signed if s in st.ix}
both_signed = np.array([i in signed_ix and j in signed_ix for i, j in zip(I, J)])
score = {}
for name, feats in MODELS.items():
    if feats is None:
        s = st.P["ex_text"][I, J].astype(float)
    else:
        clf = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, max_leaf_nodes=15, l2_regularization=1.0,
                                             class_weight="balanced", random_state=20261123)
        # tränas med carver-delad korsvalidering så att varje par får ett värde från en modell som inte sett dess ristare
        carvers = sorted({c for c in cert.values()})
        rng = np.random.default_rng(20261123)
        fold_of = {c: int(rng.integers(5)) for c in carvers}
        s = np.zeros(len(I))
        Xall = X_of(feats, I, J)
        pf = np.array([fold_of.get(cert.get(i), -1) for i in I])
        qf = np.array([fold_of.get(cert.get(j), -1) for j in J])
        base = train & both_signed if "signerade" in name else train
        for f in range(5):
            tr = base & (pf != f) & (qf != f)
            clf.fit(Xall[tr], y_all[tr])
            hold = (pf == f) | (qf == f) | ~lab
            s[hold] = np.where(np.isnan(s[hold]) | (s[hold] == 0), clf.predict_proba(Xall[hold])[:, 1] / 5 * 5, s[hold])
        # stenar utan säker ristare (alla par med minst en sådan sten) får medel över vikterna
        s_unl = np.zeros(len(I))
        for f in range(5):
            tr = base & (pf != f) & (qf != f)
            clf.fit(Xall[tr], y_all[tr])
            s_unl += clf.predict_proba(Xall)[:, 1] / 5
        s = np.where(lab, s, s_unl)
        auc_named = roc_auc_score(y_all[train], s[train])
        print(f"{name}: AUC på namngivna par (utanför vikten) {auc_named:.3f}")
    score[name] = s

M = {n: np.full((N, N), np.nan, np.float32) for n in score}
for n, s in score.items():
    M[n][I, J] = s
    M[n][J, I] = s


unnamed_dev = [k for k, g in enumerate(dev_groups) if not any(i in cert for i in g)]


def group_percentile(Mx, only=None):
    out = []
    for k, g in enumerate(dev_groups):
        if only is not None and k not in only:
            continue
        gs = set(g)
        pct = []
        for a in g:
            for b in g:
                if a == b or st.D[a, b] > MAXD or np.isnan(Mx[a, b]):
                    continue
                d = st.D[a, b]
                lo, hi = min(d * 0.75, d - 1000), min(max(d * 1.25, d + 1000), MAXD)
                ok = np.where((st.D[a] >= lo) & (st.D[a] <= hi))[0]
                ok = [c for c in ok if c not in gs and c != a and not np.isnan(Mx[a, c])]
                if len(ok) < 5:
                    continue
                pct.append(float(np.mean(Mx[a, ok] < Mx[a, b])))
        if pct:
            out.append(np.mean(pct))
    return out


res = {}
for n in score:
    gp = group_percentile(M[n])
    res[n] = {"grupper": len(gp), "median_percentil": float(np.median(gp)), "medel": float(np.mean(gp)),
              "andel_över_0_9": float(np.mean(np.array(gp) >= 0.9))}
    gu = group_percentile(M[n], set(unnamed_dev))
    res[n]["onämnda"] = {"grupper": len(gu), "median_percentil": float(np.median(gu)) if gu else None}
    print(f"{n:30s} grupper {len(gp):3d}  median {np.median(gp):.3f}  medel {np.mean(gp):.3f}  ≥0,9: {np.mean(np.array(gp) >= 0.9):.0%}"
          f"   | onämnda {len(gu)}: median {np.median(gu) if gu else float('nan'):.3f}")
np.save(os.path.join(ROOT, "data", "cache", "hander", "parsannolikhet_M1.npy"), M["M1 alla belägg"])
json.dump(res, open(os.path.join(HERE, "parmodell_utveckling.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
