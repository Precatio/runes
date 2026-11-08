"""Likhet utöver grannarna (METHODS 14i, 2026-11-08): hur lika två runstenar är i textdragen – ortografisk stilometri
(TF-IDF över tecken-n-gram, skiljetecken och bindrunor, src/orthography.py) och korpusens språkdrag, formler och
innehållskategorier – utöver vad grannstenar på samma avstånd är, utan geografi i måttet.

Måttet prövades 2026-11-08 under låsta planer: stenar av samma säkra ristare är mer lika än grannar på samma avstånd
(30 av 37 ristare, p 1e-5), och par som runologerna i Runor 2020 kallar samma hand länkas långt oftare än grannar
(89 mot 33 %, 15 av 16 grupper, p 0,0004; `analysplaner/2026-11-08-textdrag-hand.md`, `…-nya-handerna.md`). Ristarmodellen
(r/attribution.R), som måste välja bland namngivna ristare, klarade inte det provet (`…-samma-hand-runor.md`).

För ett enskilt par är belägget måttligt, och det redovisas kalibrerat: bland stenpar inom 30 km där båda har en säker
ristare i Rundata, hur stor andel som har samma ristare vid minst den likheten (grundnivån omkring 13 %). Gränsen för en
"möjlig onämnd hand" är den lägsta likhet där minst hälften av sådana par har samma ristare – vald på de namngivna
ristarna, inte på Runor 2020.

build(corpus_dir) skriver <korpus>/hands.json; load(corpus_dir) läser den."""
from __future__ import annotations

import json
import os

import numpy as np

MAX_KM = 30.0
BAND = 0.25          # the neighbours: the distance d ± 25 %, at least ± 1 km
MIN_WORDS = 3
HAND_SHARE = 0.7     # a possible unnamed hand: seven in ten named stones whose most alike stone is this alike share its carver
MIN_PAIRS = 50       # the calibration needs at least this many named pairs at a threshold
MIN_BEST = 30        # … and at least this many named stones for the best-match calibration
VERSION = "hands-1"


def _features(corp, recs):
    from scipy import sparse

    from src import orthography
    names = orthography.name_forms(list(recs.values()))
    feats = [orthography.features(recs[s], names) for s in corp.signum]
    keep = np.array([f["n_words"] >= MIN_WORDS for f in feats])
    corp = corp[keep].reset_index(drop=True)
    feats = [f for f, k in zip(feats, keep) if k]
    n = len(corp)
    vocab, rows, cols, vals = {}, [], [], []
    for i, f in enumerate(feats):
        for k, v in f["counts"].items():
            rows.append(i), cols.append(vocab.setdefault(k, len(vocab))), vals.append(float(v))
    X = sparse.csr_matrix((vals, (rows, cols)), shape=(n, len(vocab)))
    df = np.asarray((X > 0).sum(0)).ravel()
    X = X.multiply(np.log((1 + n) / (1 + df)) + 1).tocsr()
    X = sparse.diags(1 / np.maximum(np.sqrt(np.asarray(X.multiply(X).sum(1)).ravel()), 1e-12)) @ X
    tc = [c for c in corp.columns if c.startswith(("trait_", "cat_", "pm_"))]
    import pandas as pd
    T = corp[tc].apply(pd.to_numeric, errors="coerce").fillna(0).to_numpy(float)  # as in the tests (text values → 0)
    T = (T - T.mean(0)) / np.where(T.std(0) > 0, T.std(0), 1)
    T = T / np.maximum(np.linalg.norm(T, axis=1, keepdims=True), 1e-12)
    return corp, 0.5 * (np.asarray((X @ X.T).todense()) + T @ T.T)


def excess_matrix(S: np.ndarray, D: np.ndarray) -> np.ndarray:
    """Excess similarity for every pair within MAX_KM (NaN beyond): S[a, b] minus a's mean similarity with the stones at
    the same distance from a, averaged over both directions."""
    n = len(S)
    E = np.full((n, n), np.nan)
    maxd = MAX_KM * 1000
    for a in range(n):
        o = np.argsort(D[a])
        dsort, cs = D[a][o], np.concatenate([[0.0], np.cumsum(S[a][o])])
        b = np.where((D[a] <= maxd) & (np.arange(n) != a))[0]
        d = D[a, b]
        lo, hi = np.minimum(d * (1 - BAND), d - 1000), np.maximum(d * (1 + BAND), d + 1000)
        i0, i1 = np.searchsorted(dsort, lo, "left"), np.searchsorted(dsort, hi, "right")
        self_in = lo <= 0  # a itself (distance 0) lies in the band: leave it out
        cnt = i1 - i0 - self_in
        tot = cs[i1] - cs[i0] - np.where(self_in, S[a, a], 0)
        E[a, b] = np.where(cnt > 0, S[a, b] - tot / np.maximum(cnt, 1), np.nan)
    return np.nanmean(np.stack([E, E.T]), axis=0)


def calibrate(E: np.ndarray, carver: list) -> dict:
    """Among pairs within MAX_KM where both stones have a certain carver: the share with the same carver at each
    threshold, the link threshold (Youden's J) and the hand threshold (the lowest with at least HAND_SHARE)."""
    idx = [i for i, c in enumerate(carver) if c]
    sub = E[np.ix_(idx, idx)]
    iu = np.triu_indices(len(idx), 1)
    v = sub[iu]
    same = np.array([carver[idx[i]] == carver[idx[j]] for i, j in zip(*iu)])
    ok = ~np.isnan(v)
    v, same = v[ok], same[ok]
    base = float(same.mean())
    grid = np.round(np.arange(-0.2, 0.81, 0.01), 2)
    table = []
    for t in grid:
        m = v >= t
        if m.sum() >= MIN_PAIRS:
            table.append({"min": float(t), "share": float(same[m].mean()), "pairs": int(m.sum())})
    J = [(float((v[same] >= t).mean() - (v[~same] >= t).mean()), float(t)) for t in grid]
    t_link = max(J)[1]
    # The best match: for each named stone, its most alike named stone within MAX_KM. A stone's best partner is chosen
    # among many, so it is calibrated on its own: the share whose best match has the same carver, by likeness
    best = []
    for k, i in enumerate(idx):
        row = sub[k].copy()
        row[k] = np.nan
        if np.all(np.isnan(row)):
            continue
        j = int(np.nanargmax(row))
        best.append((row[j], carver[i] == carver[idx[j]]))
    bv = np.array([b[0] for b in best])
    bs = np.array([b[1] for b in best])
    best_table = []
    for t in grid:
        m = bv >= t
        if m.sum() >= MIN_BEST:
            best_table.append({"min": float(t), "share": float(bs[m].mean()), "stones": int(m.sum())})
    t_hand = next((r["min"] for r in best_table if r["share"] >= HAND_SHARE), None)
    return {"base_share": base, "named_pairs": int(len(v)), "table": table, "t_link": t_link,
            "best_table": best_table, "best_base_share": float(bs.mean()) if len(bs) else None, "t_hand": t_hand,
            "hand_share": HAND_SHARE}


def share_at(cal: dict, excess: float | None, best: bool = False) -> float | None:
    """The calibrated share with the same carver at this excess similarity (the highest threshold it reaches): for any
    pair, or (best) for a stone's most alike stone."""
    table = (cal or {}).get("best_table" if best else "table")
    if excess is None or not table:
        return None
    hit = [r for r in table if r["min"] <= excess]
    return hit[-1]["share"] if hit else cal["best_base_share" if best else "base_share"]


def build(corpus_dir: str, log=print) -> dict:
    import pandas as pd
    from pyproj import Transformer
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    corp = pd.read_csv(os.path.join(corpus_dir, "corpus.csv"), low_memory=False)
    corp = corp[corp.lat.notna() & ~corp.province.isin(["Bo"])]
    recs = {r["signum"]: r for r in json.load(open(os.path.join(root, "data", "rundata.json"), encoding="utf-8"))["inscriptions"]}
    corp = corp[corp.signum.isin(recs)].reset_index(drop=True)
    corp, S = _features(corp, recs)
    xy = np.array(Transformer.from_crs(4326, 3006, always_xy=True).transform(corp.lon.values, corp.lat.values)).T
    D = np.hypot(xy[:, None, 0] - xy[None, :, 0], xy[:, None, 1] - xy[None, :, 1])
    E = excess_matrix(S, D)
    carver = [c if isinstance(c, str) and not u else None for c, u in zip(corp.carver, corp.carvers_uncertain)]
    cal = calibrate(E, carver)
    sig = list(corp.signum)
    stones = {}
    for a in range(len(sig)):
        row = E[a]
        nb = [b for b in np.argsort(-np.nan_to_num(row, nan=-9)) if b != a and not np.isnan(row[b]) and row[b] >= cal["t_link"]][:5]
        by = {}
        for b in np.where(~np.isnan(row))[0]:
            if b != a and carver[b]:
                by.setdefault(carver[b], []).append(row[b])
        likeness = sorted(({"carver": c, "excess": round(float(np.mean(v)), 3), "n": len(v)} for c, v in by.items()),
                          key=lambda x: -x["excess"])  # every carver with a stone within 30 km: a suggested one may rank low
        stones[sig[a]] = {"partners": [{"signum": sig[b], "excess": round(float(row[b]), 3), "km": round(float(D[a, b]) / 1000, 1),
                                        "carver": carver[b]} for b in nb],
                          "carvers": likeness}
    out = {"version": VERSION, "max_km": MAX_KM, "band": BAND, "stones_n": len(sig), "calibration": cal, "stones": stones}
    tmp = os.path.join(corpus_dir, "hands.json.tmp")
    json.dump(out, open(tmp, "w", encoding="utf-8"), ensure_ascii=False)
    os.replace(tmp, os.path.join(corpus_dir, "hands.json"))
    log(f"hands.json: {len(sig)} stenar, länkgräns {cal['t_link']}, handgräns {cal['t_hand']}, grundnivå {cal['base_share']:.3f}")
    return out


_cache: dict = {}


def load(corpus_dir: str | None) -> dict | None:
    if not corpus_dir:
        return None
    p = os.path.join(corpus_dir, "hands.json")
    if not os.path.exists(p):
        return None
    key = (p, os.path.getmtime(p))
    if key not in _cache:
        _cache.clear()
        _cache[key] = json.load(open(p, encoding="utf-8"))
    return _cache[key]
