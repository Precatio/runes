"""Ornamentik steg 3 (analysplaner/2026-11-24-nya-ristare-ornamentik.md): konsensuskoder, fältval, parmåttet ex_orn,
parmodellen M2 och grinden på utvecklingsdelen. UTVECKLINGSARBETE – provdelen öppnas inte här.

    .venv/bin/python utdata/nya_ristare/ornamentik/m2.py data/cache/hander/ornamentik/kodning_full.json
Skriver utdata/nya_ristare/ornamentik/m2_utveckling.json och i cachen orn_koder.json, parsannolikhet_M2.npy,
sammanslagningar_M2.npy (och M1 räknad på samma sätt, för jämförelsen).
"""
import json
import os
import sys

import numpy as np
from scipy.stats import wilcoxon
from sklearn.metrics import roc_auc_score

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import hand_groups  # noqa: E402
from utdata.nya_ristare.belagg import MAXD, load  # noqa: E402
from utdata.nya_ristare.ornamentik.overens import agreement, by_stone, norm  # noqa: E402

CACHE = os.path.join(ROOT, "data", "cache", "hander")
FIELDS = ["djurhuvud", "antal_djur", "huvud_vy", "oga", "nackflik", "lappflik", "mun", "svans", "fotter", "huvud_svans",
          "kontur", "koppel", "flatverk", "fyrfota", "orm_extra", "manniska_mask", "kors"]  # "stil" aldrig som belägg
MIN_KAPPA, MIN_COVER, MIN_FIELDS = 0.40, 0.30, 3


def consensus(codes):
    out = {}
    for sig, c in codes.items():
        if len(c) < 2 or "ingen" in (norm(c[1].get("bild")), norm(c[2].get("bild"))):
            continue
        out[sig] = {f: norm(c[1].get(f)) for f in FIELDS if norm(c[1].get(f)) and norm(c[1].get(f)) == norm(c[2].get(f))}
    return out


def excess(S, D, ok):
    """Som _excess i belagg.py, men tål saknade par (NaN): likheten minus medel för stenar på samma avstånd från a."""
    N = len(S)
    E = np.full((N, N), np.nan)
    for a in np.where(ok)[0]:
        da = D[a]
        for b in np.where((da <= MAXD) & ~np.isnan(S[a]))[0]:
            if b == a:
                continue
            d = da[b]
            lo, hi = min(d * 0.75, d - 1000), max(d * 1.25, d + 1000)
            nb = (da >= lo) & (da <= hi) & ~np.isnan(S[a])
            nb[a] = False
            if nb.sum():
                E[a, b] = S[a, b] - S[a, nb].mean()
    return np.where(np.isnan(E), E.T, np.where(np.isnan(E.T), E, 0.5 * (E + E.T)))


def merges_of(M, D):
    """Samma UPGMA som gruppering.py/hand_groups.cluster, men sparar hela sammanslagningsordningen."""
    N = len(M)
    SUM, CNT = np.nan_to_num(M.astype(float), nan=0.0), (~np.isnan(M)).astype(float)
    MX, active = D.astype(float).copy(), np.ones(N, bool)

    def rows(r):
        with np.errstate(invalid="ignore", divide="ignore"):
            s = np.where((CNT[r] > 0) & (MX[r] <= MAXD), SUM[r] / CNT[r], -np.inf)
        s[:, ~active] = -np.inf
        s[np.arange(len(r)), r] = -np.inf
        return s

    SC, out = rows(np.arange(N)), []
    while True:
        k = int(np.argmax(SC))
        i, j = divmod(k, N)
        if not np.isfinite(SC[i, j]) or SC[i, j] < 0.05:
            return np.array(out)
        out.append((i, j, float(SC[i, j])))
        SUM[i] += SUM[j]; SUM[:, i] = SUM[i]
        CNT[i] += CNT[j]; CNT[:, i] = CNT[i]
        MX[i] = np.maximum(MX[i], MX[j]); MX[:, i] = MX[i]
        active[j] = False
        SC[j, :] = -np.inf; SC[:, j] = -np.inf
        r = rows(np.array([i]))[0]
        SC[i] = r; SC[:, i] = r


def labels_at(merges, N, t):
    lab = np.arange(N)
    for i, j, s in merges:
        if s < t:
            break
        lab[lab == lab[int(j)]] = lab[int(i)]
    return lab


def group_percentile(Mx, groups, D):
    out = []
    for g in groups:
        gs, pct = set(g), []
        for a in g:
            for b in g:
                if a == b or D[a, b] > MAXD or np.isnan(Mx[a, b]):
                    continue
                d = D[a, b]
                lo, hi = min(d * 0.75, d - 1000), min(max(d * 1.25, d + 1000), MAXD)
                ok = [c for c in np.where((D[a] >= lo) & (D[a] <= hi))[0] if c not in gs and c != a and not np.isnan(Mx[a, c])]
                if len(ok) >= 5:
                    pct.append(float(np.mean(Mx[a, ok] < Mx[a, b])))
        if pct:
            out.append(float(np.mean(pct)))
    return out


def main(path):
    codes = by_stone(path)
    agr = agreement(codes)
    kept = [f for f in FIELDS if agr[f]["kappa"] is not None and agr[f]["kappa"] >= MIN_KAPPA
            and (agr[f]["tackning"] or 0) >= MIN_COVER]
    print("godkända fält:", kept)
    cons = consensus(codes)
    json.dump(cons, open(os.path.join(CACHE, "ornamentik", "orn_koder.json"), "w", encoding="utf-8"), ensure_ascii=False)

    st = load()
    N = len(st.sig)
    V = {f: np.array([cons.get(s, {}).get(f) for s in st.sig], dtype=object) for f in kept}
    n = np.zeros((N, N))
    m = np.zeros((N, N))
    for f in kept:
        has = np.array([v is not None for v in V[f]])
        both = has[:, None] & has[None, :]
        n += both
        m += both & (V[f][:, None] == V[f][None, :])
    with np.errstate(invalid="ignore", divide="ignore"):
        S = np.where(n >= MIN_FIELDS, m / n, np.nan)
    np.fill_diagonal(S, np.nan)
    S[st.D > MAXD] = np.nan
    ok = (~np.isnan(S)).any(1)
    print(f"{ok.sum()} stenar med ornamentkod som kan jämföras; {int((~np.isnan(S)).sum() / 2)} par inom 30 km")
    ex = excess(S, st.D, ok)
    orn_n = np.where(np.isnan(S), np.nan, n)

    ev1 = {"sig": st.sig, "ix": st.ix, "D": st.D, "P": dict(st.P), "certain": st.certain}
    ev2 = dict(ev1, P=dict(st.P, ex_orn=ex.astype(np.float32), orn_n=orn_n.astype(np.float32)))
    M1 = hand_groups.pair_probabilities(ev1, log=lambda *a: None)
    M2 = hand_groups.pair_probabilities(ev2, log=lambda *a: None)
    np.save(os.path.join(CACHE, "parsannolikhet_M1_hg.npy"), M1)
    np.save(os.path.join(CACHE, "parsannolikhet_M2.npy"), M2)

    split = json.load(open(os.path.join(ROOT, "utdata", "nya_ristare", "delning.json"), encoding="utf-8"))
    dev = [[st.ix[s] for s in g["stenar"] if s in st.ix] for g in split["grupper"] if g["del"] == "U"]
    dev = [g for g in dev if len(g) >= 2]
    cert = {st.ix[s]: c for s, c in st.certain.items() if s in st.ix}

    # G1: ornamentiken bär handen (ex_orn för utvecklingsdelens facitpar mot grannarna)
    gp = group_percentile(ex, dev, st.D)
    g1p = float(wilcoxon(np.array(gp) - 0.5, alternative="greater").pvalue) if len(gp) >= 5 else None
    G1 = {"grupper": len(gp), "median_percentil": float(np.median(gp)) if gp else None, "p": g1p,
          "håller": bool(g1p is not None and g1p < 0.05 and np.median(gp) > 0.5)}
    # G2: AUC på namngivna par (utanför vikten), samma uteslutningar som träningen
    in_group, test = hand_groups._excluded(ev1)
    iu, ju = np.triu_indices(N, 1)
    near = st.D[iu, ju] <= MAXD
    I, J = iu[near], ju[near]
    lab = np.array([i in cert and j in cert for i, j in zip(I, J)])
    use = lab & np.array([not (i in in_group and in_group.get(i) == in_group.get(j)) and i not in test and j not in test
                          for i, j in zip(I, J)])
    y = np.array([cert.get(i) == cert.get(j) for i, j in zip(I, J)])
    auc1, auc2 = roc_auc_score(y[use], M1[I, J][use]), roc_auc_score(y[use], M2[I, J][use])
    G2 = {"auc_M1": round(float(auc1), 4), "auc_M2": round(float(auc2), 4), "håller": bool(auc2 >= auc1)}
    print("G1", G1, "\nG2", G2)

    # τ₂: precision ≥ 0,77 på namngivna par, störst täckning av utvecklingsdelens facitpar
    mg1, mg2 = merges_of(M1, st.D), merges_of(M2, st.D)
    np.save(os.path.join(CACHE, "sammanslagningar_M1_hg.npy"), mg1)
    np.save(os.path.join(CACHE, "sammanslagningar_M2.npy"), mg2)
    ci = np.array(sorted(cert))
    sc = np.array([cert[i] for i in ci])
    tri = np.triu(np.ones((len(ci), len(ci)), bool), 1)
    dev_pairs = [(a, b) for g in dev for k, a in enumerate(g) for b in g[k + 1:] if st.D[a, b] <= MAXD]
    grid = []
    for t in np.round(np.arange(0.50, 0.951, 0.05), 2):
        L = labels_at(mg2, N, t)
        co = (L[ci][:, None] == L[ci][None, :]) & tri
        prec = float((co & (sc[:, None] == sc[None, :])).sum() / max(co.sum(), 1))
        cov = float(np.mean([L[a] == L[b] for a, b in dev_pairs]))
        grid.append({"tau": float(t), "precision": round(prec, 3), "tackning_utv": round(cov, 3)})
    okt = [g for g in grid if g["precision"] >= 0.77]
    tau2 = max(okt, key=lambda g: (g["tackning_utv"], g["tau"]))["tau"] if okt else 0.8
    L1 = labels_at(mg1, N, 0.8)
    same = np.array_equal(L1, labels_at(np.load(os.path.join(CACHE, "sammanslagningar_M1.npy")), N, 0.8))
    out = {"fält": {f: agr[f] for f in FIELDS}, "godkända_fält": kept, "stenar_med_kod": int(ok.sum()), "G1": G1, "G2": G2,
           "grind_håller": G1["håller"] and G2["håller"], "tau2_rutnät": grid, "tau2": tau2,
           "M1_samma_grupper_som_provat": bool(same)}
    json.dump(out, open(os.path.join(HERE, "m2_utveckling.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: out[k] for k in ("godkända_fält", "G1", "G2", "grind_håller", "tau2", "M1_samma_grupper_som_provat")},
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
