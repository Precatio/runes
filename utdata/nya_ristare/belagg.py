"""Belägg per sten och per stenpar för arbetet med nya ristare (analysplaner/2026-11-23-nya-ristare-program.md, medel 1).

Stenar: svenska runstenar i korpus 510ebfb3 med koordinater (utom Bohuslän). Textdrag bara för stenar med minst tre
läsbara ord; övriga belägg (stil, kors, SRI-ord, kortkvist, bergart) för alla som har dem – saknade värden blir NaN.
Par: alla stenpar inom 30 km.

    from utdata.nya_ristare.belagg import load   # -> Stones (stenar, parmatriser)
"""
from __future__ import annotations

import glob
import json
import os
import re
import sys
from dataclasses import dataclass

import numpy as np
import pandas as pd
from pyproj import Transformer
from scipy import sparse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
from src import orthography, sri_text  # noqa: E402

C = os.path.join(ROOT, "data", "cache", "r", "corpus", "510ebfb3acc9a229")
CACHE = os.path.join(ROOT, "data", "cache", "hander")
MAXD = 30000.0
PR = {"Pr 1": 1, "Pr 2": 2, "Pr 3": 3, "Pr 4": 4, "Pr 5": 5, "Pr1": 1, "Pr2": 2, "Pr3": 3, "Pr4": 4, "Pr5": 5}


@dataclass
class Stones:
    corp: pd.DataFrame
    sig: list
    ix: dict
    D: np.ndarray            # avstånd i meter
    pair_names: list          # namn på parmåtten
    P: dict                   # namn -> N×N matris (NaN där måttet saknas eller avståndet > 30 km)
    certain: dict             # signum -> säker ristare
    signed: set


def _excess(S: np.ndarray, D: np.ndarray, ok: np.ndarray) -> np.ndarray:
    """Likhet minus medellikheten med stenar (med samma slags belägg) på samma avstånd, åt båda hållen, medel."""
    N = len(S)
    E = np.full((N, N), np.nan)
    idx = np.where(ok)[0]
    for a in idx:
        da = D[a, idx]
        sa = S[a, idx]
        o = np.argsort(da)
        dsort, ssort = da[o], sa[o]
        cs = np.concatenate([[0], np.cumsum(ssort)])
        for k in np.where((da <= MAXD) & (idx != a))[0]:
            b = idx[k]
            d = da[k]
            lo, hi = min(d * 0.75, d - 1000), max(d * 1.25, d + 1000)
            i0, i1 = np.searchsorted(dsort, lo, "left"), np.searchsorted(dsort, hi, "right")
            n = i1 - i0 - (1 if lo <= 0 else 0)
            tot = cs[i1] - cs[i0] - (S[a, a] if lo <= 0 else 0)
            if n > 0:
                E[a, b] = S[a, b] - tot / n
    return np.where(np.isnan(E), E.T, np.where(np.isnan(E.T), E, 0.5 * (E + E.T)))


def _cosine(M: np.ndarray, ok: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(M, axis=1, keepdims=True)
    U = M / np.where(n > 0, n, 1)
    S = U @ U.T
    S[~ok, :] = np.nan
    S[:, ~ok] = np.nan
    return S


def load(cache: bool = True) -> Stones:
    path = os.path.join(CACHE, "belagg.npz")
    corp = pd.read_csv(os.path.join(C, "corpus.csv"), low_memory=False)
    corp = corp[corp.lat.notna() & ~corp.province.isin(["Bo"])].reset_index(drop=True)
    recs = {r["signum"]: r for r in json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["inscriptions"]}
    corp = corp[corp.signum.isin(recs)].reset_index(drop=True)
    SIG = list(corp.signum)
    IX = {s: i for i, s in enumerate(SIG)}
    N = len(SIG)
    certain = {r.signum: r.carver for r in corp.itertuples() if isinstance(r.carver, str) and not r.carvers_uncertain}
    signed = set(corp.signum[corp.signed == 1])
    xy = np.array(Transformer.from_crs(4326, 3006, always_xy=True).transform(corp.lon.values, corp.lat.values)).T
    D = np.hypot(xy[:, None, 0] - xy[None, :, 0], xy[:, None, 1] - xy[None, :, 1])
    if cache and os.path.exists(path):
        z = np.load(path, allow_pickle=True)
        if list(z["sig"]) == SIG:
            names = list(z["names"])
            return Stones(corp, SIG, IX, D, names, {n: z[n] for n in names}, certain, signed)

    # --- textdragen (samma som utdata/nya_hander) ---
    names_f = orthography.name_forms(list(recs.values()))
    feats = [orthography.features(recs[s], names_f) for s in SIG]
    has_text = np.array([f["n_words"] >= 3 for f in feats])
    vocab, rows, cols, vals = {}, [], [], []
    for i, f in enumerate(feats):
        if not has_text[i]:
            continue
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
    S_text = 0.5 * (S_orto + S_trait)
    P = {"ex_text": _excess(S_text, D, has_text), "ex_orto": _excess(S_orto, D, has_text),
         "ex_trait": _excess(S_trait, D, has_text)}

    # --- stil (profil) ---
    st = corp["style"].astype(str).str.replace("\xa0", " ").str.strip()
    stn = np.array([PR.get(s, np.nan) for s in st], float)
    has_style = corp["style"].notna().to_numpy()
    same_style = (st.to_numpy()[:, None] == st.to_numpy()[None, :]).astype(float)
    same_style[~has_style, :] = np.nan
    same_style[:, ~has_style] = np.nan
    P["same_style"] = same_style
    P["style_gap"] = np.abs(stn[:, None] - stn[None, :])

    # --- korset (Runor 2020, Lagers typologi: aspekt + form) ---
    cross = {}
    for f in glob.glob(os.path.join(ROOT, "data", "cache", "runor", "*.json")):
        d = json.load(open(f, encoding="utf-8"))
        s = f"{d['signum1']} {d['signum2']}".strip()
        if s in IX and d.get("crosses"):
            fs = {(cf.get("aspect"), cf.get("form")) for c in d["crosses"] for cf in (c.get("cross_forms") or [])}
            if fs:
                cross[IX[s]] = fs
    J = np.full((N, N), np.nan)
    ci = sorted(cross)
    for a in ci:
        for b in ci:
            if a < b and D[a, b] <= MAXD:
                u = cross[a] | cross[b]
                J[a, b] = J[b, a] = len(cross[a] & cross[b]) / len(u)
    P["cross_jaccard"] = J

    # --- SRI: ornament- och runformsord ---
    arts = sri_text.articles()
    keys = list(sri_text.VOCAB)
    orn_keys = keys[:keys.index("kortkvist")]
    rune_keys = keys[keys.index("kortkvist"):]
    Fo, Fr = np.zeros((N, len(orn_keys))), np.zeros((N, len(rune_keys)))
    has_sri = np.zeros(N, bool)
    for s, t in arts.items():
        if s in IX:
            f = sri_text.features(t)
            Fo[IX[s]] = [f[k] for k in orn_keys]
            Fr[IX[s]] = [f[k] for k in rune_keys]
            has_sri[IX[s]] = True
    P["sri_orn"] = _cosine(Fo, has_sri & (Fo.sum(1) > 0))
    P["sri_rune"] = _cosine(Fr, has_sri & (Fr.sum(1) > 0))

    # --- kortkvist, bergart ---
    for col, name in (("short_twig", "same_twig"), ("material", "same_material")):
        v = corp[col].astype(str).to_numpy()
        ok = corp[col].notna().to_numpy()
        M = (v[:, None] == v[None, :]).astype(float)
        M[~ok, :] = np.nan
        M[:, ~ok] = np.nan
        P[name] = M

    # --- de kategoriska språkdragen (skiljetecken, stavningen av eftir/þenna, ai/a, auk/ok …): lika, olika eller saknas ---
    for col in [c for c in corp.columns if c.startswith("trait_")]:
        v = corp[col]
        if pd.api.types.is_numeric_dtype(v):
            continue
        ok = v.notna().to_numpy()
        vv = v.astype(str).to_numpy()
        M = (vv[:, None] == vv[None, :]).astype(float)
        M[~ok, :] = np.nan
        M[:, ~ok] = np.nan
        P["same_" + col[len("trait_"):]] = M

    # --- gemensamma namn (personer och platser markerade med " i Rundatas normalisering), vägda efter ovanlighet ---
    STOP = {"guð", "gud", "krist", "kristr", "maría", "mária", "michael"}
    stems = []
    for s in SIG:
        t = recs[s].get("normalization_ows") or ""
        ns = {w.lower()[:5] for w in re.findall(r'"([A-ZÁÉÍÓÚÝÞÆÖØÄÅÔÇ][^\s,.;:!?()\[\]{}"/]*)', t)}
        stems.append({n.replace("[", "").replace("]", "") for n in ns if n not in STOP and len(n) >= 3})
    dfn = {}
    for ns in stems:
        for n in ns:
            dfn[n] = dfn.get(n, 0) + 1
    NM = np.full((N, N), np.nan)
    has_names = np.array([bool(ns) for ns in stems])
    for a in np.where(has_names)[0]:
        for b in np.where((D[a] <= MAXD) & has_names)[0]:
            if b > a:
                sh = stems[a] & stems[b]
                NM[a, b] = NM[b, a] = sum(np.log(N / dfn[n]) for n in sh)
    P["names_shared"] = NM

    far = D > MAXD
    for k in P:
        P[k] = P[k].astype(np.float32)
        P[k][far] = np.nan
        np.fill_diagonal(P[k], np.nan)
    names = list(P)
    os.makedirs(CACHE, exist_ok=True)
    np.savez_compressed(path, sig=np.array(SIG, dtype=object), names=np.array(names, dtype=object), **P)
    return Stones(corp, SIG, IX, D, names, P, certain, signed)


if __name__ == "__main__":
    st = load(cache=False)
    iu = np.triu_indices(len(st.sig), 1)
    near = st.D[iu] <= MAXD
    print(len(st.sig), "stenar,", int(near.sum()), "par inom 30 km")
    for n in st.pair_names:
        v = st.P[n][iu][near]
        print(f"{n:14s} finns för {np.mean(~np.isnan(v)):.0%} av paren")
