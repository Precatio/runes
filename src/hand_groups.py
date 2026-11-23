"""Stenar som kan ha samma hand (METHODS 14l, 2026-11-23): grupper av runstenar ur en inlärd parmodell för samma hand.

Metoden prövades under låsta planer (`analysplaner/2026-11-23-nya-ristare-program.md`, `…-slutprov-1.md`): mot ett facit
av runologernas egna "samme ristare" ur Sveriges runinskrifter och Runor 2020, med hälften av facit undanhållen tills
metoden var fastställd. Där hamnade 42 % av runologernas par i samma grupp mot 7 % av grannstenar på samma avstånd
(p 0,00002), och för de onämnda händerna 69 % mot 7,5 % (p 0,002). Omkring tre av fyra par i samma grupp har samma
ristare, mätt på namngivna ristare. Forskningsskripten (det som prövades) ligger i utdata/nya_ristare/.

1. **Beläggen per stenpar** inom 30 km:
   - textdragens överskott utöver grannarna (src/hand_links.py-måttet, samlat, ortografiskt och för språkdragen);
   - stilgrupp och stilavstånd;
   - korsets form enligt Lagers typologi i Runor 2020 (Jaccard);
   - ornament- och runformsord ur SRI (cosinus);
   - de kategoriska språkdragen, lika eller olika (skiljetecken, stavningen av eftir och þenna, ai, auk med flera);
   - gemensamma namn, vägda efter ovanlighet;
   - kortkvist, bergart och avståndet.

   Saknade belägg är NaN.
2. **Parmodellen:** gradient boosting tränad på par av stenar med säker ristare i Rundata (samma ristare = 1), med
   ristarna delade i fem vikter. Par av säkra stenar får sitt värde från vikten som inte sett deras ristare. Övriga par får
   medel över vikterna.
3. **Grupperna:** genomsnittlig länkning på sannolikheterna med gruppens diameter högst 30 km, avskuren vid τ = 0,8.
   Grupper med minst tre stenar redovisas med typen:
   - okänd hand: ingen sten har en säker ristare;
   - med X: alla säkra stenar har ristaren X;
   - blandad.

   Underlaget räknas som **svagt** när mindre än hälften av paren har jämförbar text och paren i snitt har färre än tre
   belägg, i praktiken fragment på samma fyndplats som hålls ihop av platsen.

build(corpus_dir) skriver <korpus>/hand_groups.json; load(corpus_dir) läser den."""
from __future__ import annotations

import glob
import json
import os
import re

import numpy as np

VERSION = "groups-1"
MAX_KM = 30.0
TAU = 0.8
MIN_SIZE = 3
SEED = 20261123
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TESTED = {"plan": "analysplaner/2026-11-23-nya-ristare-slutprov-1.md", "facit_groups": 42, "together": 0.42, "control": 0.066,
          "p": 2.1e-05, "unnamed_groups": 15, "unnamed_together": 0.69, "unnamed_control": 0.075, "unnamed_p": 0.0017,
          "precision_named": 0.77}
PR = {"Pr1": 1, "Pr2": 2, "Pr3": 3, "Pr4": 4, "Pr5": 5, "Pr 1": 1, "Pr 2": 2, "Pr 3": 3, "Pr 4": 4, "Pr 5": 5}
_cache: dict = {}


def _excess(S: np.ndarray, D: np.ndarray, ok: np.ndarray) -> np.ndarray:
    """Likheten minus medellikheten med stenar (med samma slags belägg) på samma avstånd, åt båda hållen, medel."""
    n = len(S)
    E = np.full((n, n), np.nan)
    idx = np.where(ok)[0]
    maxd = MAX_KM * 1000
    for a in idx:
        da, sa = D[a, idx], S[a, idx]
        o = np.argsort(da)
        dsort, cs = da[o], np.concatenate([[0.0], np.cumsum(sa[o])])
        for k in np.where((da <= maxd) & (idx != a))[0]:
            d = da[k]
            lo, hi = min(d * 0.75, d - 1000), max(d * 1.25, d + 1000)
            i0, i1 = np.searchsorted(dsort, lo, "left"), np.searchsorted(dsort, hi, "right")
            cnt = i1 - i0 - (1 if lo <= 0 else 0)
            tot = cs[i1] - cs[i0] - (S[a, a] if lo <= 0 else 0)
            if cnt > 0:
                E[a, idx[k]] = S[a, idx[k]] - tot / cnt
    return np.where(np.isnan(E), E.T, np.where(np.isnan(E.T), E, 0.5 * (E + E.T)))


def _cosine(M: np.ndarray, ok: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(M, axis=1, keepdims=True)
    U = M / np.where(n > 0, n, 1)
    S = U @ U.T
    S[~ok, :] = np.nan
    S[:, ~ok] = np.nan
    return S


def _same(values, ok) -> np.ndarray:
    v = np.asarray(values, dtype=object)
    M = (v[:, None] == v[None, :]).astype(float)
    M[~ok, :] = np.nan
    M[:, ~ok] = np.nan
    return M


def evidence(corpus_dir: str) -> dict:
    """Stenarna och parbeläggen (N×N, NaN där belägget saknas eller avståndet är över 30 km)."""
    import pandas as pd
    from pyproj import Transformer
    from scipy import sparse

    from src import orthography
    corp = pd.read_csv(os.path.join(corpus_dir, "corpus.csv"), low_memory=False)
    corp = corp[corp.lat.notna() & ~corp.province.isin(["Bo"])]
    recs = {r["signum"]: r for r in json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["inscriptions"]}
    corp = corp[corp.signum.isin(recs)].reset_index(drop=True)
    sig = list(corp.signum)
    ix = {s: i for i, s in enumerate(sig)}
    n = len(sig)
    xy = np.array(Transformer.from_crs(4326, 3006, always_xy=True).transform(corp.lon.values, corp.lat.values)).T
    D = np.hypot(xy[:, None, 0] - xy[None, :, 0], xy[:, None, 1] - xy[None, :, 1])
    P: dict[str, np.ndarray] = {}

    # the text: orthographic stylometry and the corpus' traits (as in src/hand_links.py), excess beyond the neighbours
    names_f = orthography.name_forms(list(recs.values()))
    feats = [orthography.features(recs[s], names_f) for s in sig]
    has_text = np.array([f["n_words"] >= 3 for f in feats])
    vocab, rows, cols, vals = {}, [], [], []
    for i, f in enumerate(feats):
        if has_text[i]:
            for k, v in f["counts"].items():
                rows.append(i), cols.append(vocab.setdefault(k, len(vocab))), vals.append(float(v))
    X = sparse.csr_matrix((vals, (rows, cols)), shape=(n, len(vocab)))
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
    P["ex_text"] = _excess(0.5 * (S_orto + S_trait), D, has_text)
    P["ex_orto"] = _excess(S_orto, D, has_text)
    P["ex_trait"] = _excess(S_trait, D, has_text)

    st = corp["style"].astype(str).str.replace("\xa0", " ").str.strip()
    P["same_style"] = _same(st, corp["style"].notna().to_numpy())
    stn = np.array([PR.get(s, np.nan) for s in st], float)
    P["style_gap"] = np.abs(stn[:, None] - stn[None, :])

    cross = {}
    for f in glob.glob(os.path.join(ROOT, "data", "cache", "runor", "*.json")):
        d = json.load(open(f, encoding="utf-8"))
        s = f"{d['signum1']} {d['signum2']}".strip()
        if s in ix and d.get("crosses"):
            fs = {(cf.get("aspect"), cf.get("form")) for c in d["crosses"] for cf in (c.get("cross_forms") or [])}
            if fs:
                cross[ix[s]] = fs
    J = np.full((n, n), np.nan)
    ci = sorted(cross)
    for a in ci:
        for b in ci:
            if a < b and D[a, b] <= MAX_KM * 1000:
                J[a, b] = J[b, a] = len(cross[a] & cross[b]) / len(cross[a] | cross[b])
    P["cross_jaccard"] = J

    try:  # the SRI volumes are local downloads; without them these two are left out (NaN)
        from src import sri_text
        arts = sri_text.articles()
    except Exception:
        arts = {}
    keys = list(__import__("src.sri_text", fromlist=["VOCAB"]).VOCAB)
    cut = keys.index("kortkvist")
    Fo, Fr = np.zeros((n, cut)), np.zeros((n, len(keys) - cut))
    has_sri = np.zeros(n, bool)
    if arts:
        from src import sri_text
        for s, t in arts.items():
            if s in ix:
                f = sri_text.features(t)
                Fo[ix[s]] = [f[k] for k in keys[:cut]]
                Fr[ix[s]] = [f[k] for k in keys[cut:]]
                has_sri[ix[s]] = True
    P["sri_orn"] = _cosine(Fo, has_sri & (Fo.sum(1) > 0))
    P["sri_rune"] = _cosine(Fr, has_sri & (Fr.sum(1) > 0))
    P["same_twig"] = _same(corp["short_twig"].astype(str), corp["short_twig"].notna().to_numpy())
    P["same_material"] = _same(corp["material"].astype(str), corp["material"].notna().to_numpy())
    for col in [c for c in corp.columns if c.startswith("trait_")]:
        if not pd.api.types.is_numeric_dtype(corp[col]):  # the categorical traits: alike or not
            P["same_" + col[len("trait_"):]] = _same(corp[col].astype(str), corp[col].notna().to_numpy())

    stop = {"guð", "gud", "krist", "kristr", "maría", "mária", "michael"}
    stems = []
    for s in sig:
        t = recs[s].get("normalization_ows") or ""
        ns = {w.lower()[:5] for w in re.findall(r'"([A-ZÁÉÍÓÚÝÞÆÖØÄÅÔÇ][^\s,.;:!?()\[\]{}"/]*)', t)}
        stems.append({x.replace("[", "").replace("]", "") for x in ns if x not in stop and len(x) >= 3})
    dfn: dict = {}
    for ns in stems:
        for x in ns:
            dfn[x] = dfn.get(x, 0) + 1
    NM = np.full((n, n), np.nan)
    has_names = np.array([bool(ns) for ns in stems])
    for a in np.where(has_names)[0]:
        for b in np.where((D[a] <= MAX_KM * 1000) & has_names)[0]:
            if b > a:
                NM[a, b] = NM[b, a] = sum(np.log(n / dfn[x]) for x in stems[a] & stems[b])
    P["names_shared"] = NM

    far = D > MAX_KM * 1000
    for k in P:
        P[k] = P[k].astype(np.float32)
        P[k][far] = np.nan
        np.fill_diagonal(P[k], np.nan)
    certain = {r.signum: r.carver for r in corp.itertuples() if isinstance(r.carver, str) and not r.carvers_uncertain}
    return {"corp": corp, "sig": sig, "ix": ix, "D": D, "P": P, "certain": certain,
            "signed": set(corp.signum[corp.signed == 1]), "recs": recs}


def _excluded(ev: dict) -> tuple[dict, set]:
    """Som i den prövade metoden: facitgrupperna (utdata/nya_ristare/delning.json) – par inom en grupp tränas inte på, och
    provdelens stenar ingår inte i träningen."""
    p = os.path.join(ROOT, "utdata", "nya_ristare", "delning.json")
    if not os.path.exists(p):
        return {}, set()
    groups = json.load(open(p, encoding="utf-8"))["grupper"]
    in_group, test = {}, set()
    for k, g in enumerate(groups):
        for s in g["stenar"]:
            if s in ev["ix"]:
                in_group[ev["ix"][s]] = k
                if g["del"] == "P":
                    test.add(ev["ix"][s])
    return in_group, test


def pair_probabilities(ev: dict, log=print, seed: int = SEED) -> np.ndarray:
    """Sannolikheten för samma hand för varje stenpar inom 30 km (N×N, NaN utanför)."""
    from sklearn.ensemble import HistGradientBoostingClassifier
    sig, D, P = ev["sig"], ev["D"], ev["P"]
    n = len(sig)
    iu, ju = np.triu_indices(n, 1)
    near = D[iu, ju] <= MAX_KM * 1000
    I, J = iu[near], ju[near]
    names = sorted(P)
    X = np.column_stack([P[k][I, J] for k in names] + [D[I, J] / 1000]).astype(np.float32)
    cert = {ev["ix"][s]: c for s, c in ev["certain"].items()}
    ci = np.array([cert.get(i) for i in I], dtype=object)
    cj = np.array([cert.get(j) for j in J], dtype=object)
    lab = np.array([a is not None and b is not None for a, b in zip(ci, cj)])
    y = lab & (ci == cj)
    in_group, test = _excluded(ev)
    usable = lab & np.array([not (i in in_group and in_group.get(i) == in_group.get(j)) and i not in test and j not in test
                             for i, j in zip(I, J)])
    rng = np.random.default_rng(seed)
    fold = {c: int(rng.integers(5)) for c in sorted(set(cert.values()))}
    fi = np.array([fold.get(c, -1) for c in ci])
    fj = np.array([fold.get(c, -1) for c in cj])
    s = np.full(len(I), np.nan)
    s_avg = np.zeros(len(I))
    for f in range(5):
        clf = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, max_leaf_nodes=15, l2_regularization=1.0,
                                             class_weight="balanced", random_state=seed)
        tr = usable & (fi != f) & (fj != f)
        clf.fit(X[tr], y[tr])
        p = clf.predict_proba(X)[:, 1]
        hold = lab & ((fi == f) | (fj == f)) & np.isnan(s)
        s[hold] = p[hold]
        s_avg += p / 5
        log(f"vikt {f + 1}/5")
    s = np.where(lab, s, s_avg)
    M = np.full((n, n), np.nan, np.float32)
    M[I, J] = s
    M[J, I] = s
    return M


def cluster(M: np.ndarray, D: np.ndarray, tau: float = TAU) -> np.ndarray:
    """Genomsnittlig länkning på M (NaN = ingen jämförelse) med gruppens diameter ≤ 30 km; grupp-id per sten."""
    n = len(M)
    SUM = np.nan_to_num(M.astype(float), nan=0.0)
    CNT = (~np.isnan(M)).astype(float)
    MX = D.astype(float).copy()
    active = np.ones(n, bool)
    maxd = MAX_KM * 1000

    def rows(r):
        with np.errstate(invalid="ignore", divide="ignore"):
            s = np.where((CNT[r] > 0) & (MX[r] <= maxd), SUM[r] / CNT[r], -np.inf)
        s[:, ~active] = -np.inf
        s[np.arange(len(r)), r] = -np.inf
        return s

    SC = rows(np.arange(n))
    lab = np.arange(n)
    while True:
        k = int(np.argmax(SC))
        i, j = divmod(k, n)
        if not np.isfinite(SC[i, j]) or SC[i, j] < tau:
            break
        lab[lab == lab[j]] = lab[i]
        SUM[i] += SUM[j]
        SUM[:, i] = SUM[i]
        CNT[i] += CNT[j]
        CNT[:, i] = CNT[i]
        MX[i] = np.maximum(MX[i], MX[j])
        MX[:, i] = MX[i]
        active[j] = False
        SC[j, :] = -np.inf
        SC[:, j] = -np.inf
        r = rows(np.array([i]))[0]
        SC[i] = r
        SC[:, i] = r
    return lab


STABILITY_SEEDS = (SEED + 1, SEED + 2)  # the model retrained with other folds: how many of a group's pairs stay together


def build(corpus_dir: str, log=print) -> dict:
    from collections import Counter
    ev = evidence(corpus_dir)
    M = pair_probabilities(ev, log=log)
    lab = cluster(M, ev["D"])
    others = [cluster(pair_probabilities(ev, log=lambda *_: None, seed=s), ev["D"]) for s in STABILITY_SEEDS]
    corp, sig, D, P = ev["corp"], ev["sig"], ev["D"], ev["P"]
    runor = {}
    for f in glob.glob(os.path.join(ROOT, "data", "cache", "runor", "*.json")):
        d = json.load(open(f, encoding="utf-8"))
        s = f"{d['signum1']} {d['signum2']}".strip()
        if d.get("carver"):
            runor[s] = "; ".join(str(c.get("name")) for c in d["carver"])
    evid = [k for k in P if k not in ("same_twig", "same_material")]
    groups = []
    for g in np.unique(lab):
        m = sorted(np.where(lab == g)[0], key=lambda i: sig[i])
        if len(m) < MIN_SIZE:
            continue
        A = np.array(m)
        iu = np.triu_indices(len(m), 1)
        sub = M[np.ix_(A, A)][iu]
        n_ev = sum((~np.isnan(P[k][np.ix_(A, A)][iu])).astype(int) for k in evid)
        text = float(np.mean(~np.isnan(P["ex_text"][np.ix_(A, A)][iu])))
        cert = {sig[i]: ev["certain"][sig[i]] for i in m if sig[i] in ev["certain"]}
        kinds = sorted(set(cert.values()))
        typ = "okänd hand" if not kinds else ("med" if len(kinds) == 1 else "blandad")
        stab = float(np.mean([np.mean(o[A][iu[0]] == o[A][iu[1]]) for o in others])) if others else None
        groups.append({"stones": [sig[i] for i in m], "type": typ, "stability": round(stab, 2) if stab is not None else None, "carver": kinds[0] if len(kinds) == 1 else None,
                       "carvers": cert, "signed": [sig[i] for i in m if sig[i] in ev["signed"]],
                       "evidence": "svagt" if (text < 0.5 and float(np.mean(n_ev)) < 3) else "gott",
                       "text_share": round(text, 2), "mean_p": round(float(np.nanmean(sub)), 3),
                       "diameter_km": round(float(D[np.ix_(A, A)].max()) / 1000, 1),
                       "provinces": dict(Counter(corp.province[i] for i in m)),
                       "parishes": sorted(set(str(corp.parish[i]) for i in m if isinstance(corp.parish[i], str))),
                       "styles": dict(Counter(str(corp["style"][i]) for i in m if isinstance(corp["style"][i], str))),
                       "runor": {sig[i]: runor[sig[i]] for i in m if sig[i] in runor}})
    groups.sort(key=lambda x: (-len(x["stones"]), -x["mean_p"]))
    for k, x in enumerate(groups, 1):
        x["id"] = f"G{k:03d}"
    stones = {s: x["id"] for x in groups for s in x["stones"]}
    out = {"version": VERSION, "tau": TAU, "max_km": MAX_KM, "min_size": MIN_SIZE, "tested": TESTED,
           "stones_n": len(sig), "groups": groups, "stones": stones,
           "counts": {"groups": len(groups), "stones": len(stones),
                      "unknown_good": sum(1 for x in groups if x["type"] == "okänd hand" and x["evidence"] == "gott")}}
    tmp = os.path.join(corpus_dir, "hand_groups.json.tmp")
    json.dump(out, open(tmp, "w", encoding="utf-8"), ensure_ascii=False)
    os.replace(tmp, os.path.join(corpus_dir, "hand_groups.json"))
    log(f"{len(groups)} grupper, {len(stones)} stenar")
    return out


def load(corpus_dir: str | None) -> dict | None:
    if not corpus_dir:
        return None
    p = os.path.join(corpus_dir, "hand_groups.json")
    if not os.path.exists(p):
        return None
    key = (p, os.path.getmtime(p))
    if key not in _cache:
        _cache.clear()
        _cache[key] = json.load(open(p, encoding="utf-8"))
    return _cache[key]


def group_of(data: dict | None, signum: str) -> dict | None:
    """Gruppen en sten ingår i (utan stenen själv i listan över de andra), eller None."""
    if not data:
        return None
    gid = (data.get("stones") or {}).get(signum)
    if not gid:
        return None
    g = next((x for x in data["groups"] if x["id"] == gid), None)
    if not g:
        return None
    return {"id": g["id"], "type": g["type"], "carver": g["carver"], "evidence": g["evidence"],
            "others": [s for s in g["stones"] if s != signum], "carvers": g["carvers"], "diameter_km": g["diameter_km"],
            "mean_p": g["mean_p"], "stability": g.get("stability"), "precision_named": data["tested"]["precision_named"]}
