"""Runstenens storlek och dess syfte och resare (se METHODS.md, 9b).

Hypotesen: stora stenar restes för större syften och av eller för mäktigare personer. Höjden (ur
Kulturmiljöregistret, src/stone_dimensions.py) jämförs med inskriftens syfte (nio kategorier, avsnitt 9), med
statusord i texten (þegn, drengr, styrman, skeppare, kung, gode), med antalet namngivna personer och med
inskriftens längd.

Bergart, landskap och lokal sed påverkar storleken, så alla test görs inom landskap: etiketterna permuteras bara
mellan stenar i samma landskap, och korrelationer räknas på rangordning inom landskapet. Höjden analyseras på
logaritmisk skala (en sten som är dubbelt så hög räknas lika långt från en hälften så hög). Fragment utesluts.
"""
from __future__ import annotations

import math
import re
from collections import defaultdict

import numpy as np

from src.inscription_types import CATEGORIES, categories
from src.research_gaps import is_runestone, province

STATUS_WORDS = ("þegn", "þiagn", "dræng", "styrimann", "skipari", "kunung", "goði", "landmann")
N_PERM = 5000
SEED = 2026


def status_words(rec: dict) -> list[str]:
    words = [w.strip('"').lower() for w in re.findall(r'"?[^\s,.:;!?()\[\]/]+', rec.get("normalization") or "")]
    return sorted({s for s in STATUS_WORDS for w in words if w.startswith(s)})


def n_names(rec: dict) -> int:
    """Antal namn i normaliseringen (Rundata markerar namn med ett inledande citattecken)."""
    return len(re.findall(r'(?:^|[\s(/])"[^\s"]', rec.get("normalization") or ""))


def n_words(rec: dict) -> int:
    return len(re.findall(r"[^\s,.:;!?()\[\]]+", rec.get("normalization") or ""))


def table(inscriptions: list[dict], dims: dict) -> list[dict]:
    """En rad per runsten med höjd (inte fragment) och förklarande variabler."""
    rows = []
    for rec in inscriptions:
        if not is_runestone(rec):
            continue
        d = dims.get(rec["signum"]) or {}
        h = d.get("height_m")
        if not h or d.get("fragment") or d.get("status") != "ok":
            continue
        cats = set(categories(rec))
        rows.append({"signum": rec["signum"], "province": province(rec), "height_m": h, "log_h": math.log(h),
                     "width_m": d.get("width_m"), "rune_height_cm": d.get("rune_height_cm"),
                     "categories": cats, "status": status_words(rec), "n_names": n_names(rec), "n_words": n_words(rec),
                     "carver": next((c["name"] for c in rec.get("carvers") or [] if c["kind"] in ("S", "A")
                                     and not c["uncertain"]), None)})
    return rows


def _strata(rows):
    by = defaultdict(list)
    for i, r in enumerate(rows):
        by[r["province"]].append(i)
    return [np.array(v) for v in by.values() if len(v) > 1]


def stratified_test(rows: list[dict], flag: np.ndarray, n_perm: int = N_PERM, seed: int = SEED) -> dict:
    """Skillnad i medel-log-höjd (med mot utan) inom landskap, med permutation av flaggan inom landskap.
    Statistiken väger landskapen efter hur många stenar med flaggan de har."""
    y = np.array([r["log_h"] for r in rows])
    strata = _strata(rows)

    def stat(f):
        num = den = 0.0
        for idx in strata:
            a, b = f[idx], ~f[idx]
            if a.any() and b.any():
                w = a.sum()
                num += w * (y[idx][a].mean() - y[idx][b].mean())
                den += w
        return num / den if den else float("nan")

    obs = stat(flag)
    if not np.isfinite(obs):
        return {"n": int(flag.sum()), "ratio": None, "p": None}
    rng = np.random.default_rng(seed)
    count = 0
    for _ in range(n_perm):
        f = flag.copy()
        for idx in strata:
            f[idx] = rng.permutation(f[idx])
        if abs(stat(f)) >= abs(obs) - 1e-12:
            count += 1
    return {"n": int(flag.sum()), "ratio": float(math.exp(obs)), "p": (count + 1) / (n_perm + 1)}


def within_rank_correlation(rows: list[dict], key: str, n_perm: int = N_PERM, seed: int = SEED) -> dict:
    """Spearman-korrelation mellan höjd och en variabel, på rangordning inom landskap; permutation inom landskap."""
    from scipy.stats import rankdata

    y = np.array([r["log_h"] for r in rows])
    x = np.array([float(r[key]) for r in rows])
    ry, rx = np.zeros(len(y)), np.zeros(len(x))
    for idx in _strata(rows):
        ry[idx] = (rankdata(y[idx]) - 0.5) / len(idx)
        rx[idx] = (rankdata(x[idx]) - 0.5) / len(idx)
    keep = np.concatenate(_strata(rows))
    obs = float(np.corrcoef(rx[keep], ry[keep])[0, 1])
    rng = np.random.default_rng(seed)
    count = 0
    for _ in range(n_perm):
        rp = rx.copy()
        for idx in _strata(rows):
            rp[idx] = rng.permutation(rp[idx])
        if abs(np.corrcoef(rp[keep], ry[keep])[0, 1]) >= abs(obs) - 1e-12:
            count += 1
    return {"rho": obs, "p": (count + 1) / (n_perm + 1), "n": int(len(keep))}


def within_rank_partial(rows: list[dict], key: str, control: str, n_perm: int = N_PERM, seed: int = SEED) -> dict:
    """Som within_rank_correlation, men med kontrollvariabeln bortrensad (linjärt, på rangerna inom landskap) ur
    både höjden och variabeln – t.ex. antal namn med hänsyn till hur lång texten är."""
    from scipy.stats import rankdata

    y = np.array([r["log_h"] for r in rows])
    x = np.array([float(r[key]) for r in rows])
    z = np.array([float(r[control]) for r in rows])
    strata = _strata(rows)
    ry, rx, rz = np.zeros(len(y)), np.zeros(len(x)), np.zeros(len(z))
    for idx in strata:
        for src, dst in ((y, ry), (x, rx), (z, rz)):
            dst[idx] = (rankdata(src[idx]) - 0.5) / len(idx)
    keep = np.concatenate(strata)

    def resid(a):
        A = np.column_stack([np.ones(len(keep)), rz[keep]])
        coef, *_ = np.linalg.lstsq(A, a[keep], rcond=None)
        out = np.zeros(len(a))
        out[keep] = a[keep] - A @ coef
        return out

    ey, ex = resid(ry), resid(rx)
    obs = float(np.corrcoef(ex[keep], ey[keep])[0, 1])
    rng = np.random.default_rng(seed)
    count = 0
    for _ in range(n_perm):
        ep = ex.copy()
        for idx in strata:
            ep[idx] = rng.permutation(ep[idx])
        if abs(np.corrcoef(ep[keep], ey[keep])[0, 1]) >= abs(obs) - 1e-12:
            count += 1
    return {"rho": obs, "p": (count + 1) / (n_perm + 1), "n": int(len(keep))}


def bh(pvalues: list[float | None]) -> list[float | None]:
    idx = [i for i, p in enumerate(pvalues) if p is not None]
    m = len(idx)
    q: list[float | None] = [None] * len(pvalues)
    running = 1.0
    for rank, i in sorted(enumerate(sorted(idx, key=lambda i: pvalues[i]), start=1), key=lambda t: -t[0]):
        running = min(running, pvalues[i] * m / rank)
        q[i] = running
    return q


def analyse(inscriptions: list[dict], dims: dict, n_perm: int = N_PERM) -> dict:
    rows = table(inscriptions, dims)
    if len(rows) < 30:
        return {"n": len(rows), "error": "För få runstenar med kända mått."}
    h = np.array([r["height_m"] for r in rows])
    out = {"n": len(rows), "median_height_m": float(np.median(h)),
           "quartiles_m": [float(np.percentile(h, 25)), float(np.percentile(h, 75))],
           "by_province": sorted(({"province": p, "n": int(len(idx)), "median_height_m": float(np.median(h[idx]))}
                                  for p, idx in ((rows[ix[0]]["province"], ix) for ix in _strata(rows))),
                                 key=lambda x: -x["n"])}
    tests = []
    for key, spec in CATEGORIES.items():
        label = spec[0]
        flag = np.array([key in r["categories"] for r in rows])
        if 5 <= flag.sum() <= len(rows) - 5:
            t = stratified_test(rows, flag, n_perm)
            tests.append({"variable": f"Syfte: {label}", "kind": "category", "key": key, **t,
                          "median_with_m": float(np.median(h[flag])), "median_without_m": float(np.median(h[~flag]))})
    flag = np.array([bool(r["status"]) for r in rows])
    if flag.sum() >= 5:
        tests.append({"variable": "Statusord (þegn, drengr, styrman, skeppare, kung, gode)", "kind": "status", "key": "status",
                      **stratified_test(rows, flag, n_perm),
                      "median_with_m": float(np.median(h[flag])), "median_without_m": float(np.median(h[~flag]))})
    for t, q in zip(tests, bh([t["p"] for t in tests])):
        t["q"] = q
    out["tests"] = tests
    out["correlations"] = [{"variable": "Antal namngivna personer", "key": "n_names", **within_rank_correlation(rows, "n_names", n_perm)},
                           {"variable": "Inskriftens längd (ord)", "key": "n_words", **within_rank_correlation(rows, "n_words", n_perm)}]
    out["correlations"].append({"variable": "Antal namngivna personer, med hänsyn till inskriftens längd", "key": "n_names|n_words",
                                "partial": True, **within_rank_partial(rows, "n_names", "n_words", n_perm)})
    # Carvers with at least ten measured stones: did some raise larger stones than others in the same province?
    by_carver = defaultdict(int)
    for r in rows:
        if r["carver"]:
            by_carver[r["carver"]] += 1
    carvers = []
    for name in sorted(c for c, n in by_carver.items() if n >= 10):
        flag = np.array([r["carver"] == name for r in rows])
        carvers.append({"carver": name, **stratified_test(rows, flag, n_perm),
                        "median_m": float(np.median(h[flag]))})
    for c, q in zip(carvers, bh([c["p"] for c in carvers])):
        c["q"] = q
    out["carvers"] = sorted(carvers, key=lambda c: -(c["ratio"] or 0))
    rh = [r for r in rows if r.get("rune_height_cm")]
    if len(rh) >= 30:
        out["correlations"].append({"variable": "Runornas höjd (kontroll av måtten)", "key": "rune_height_cm",
                                    **within_rank_correlation(rh, "rune_height_cm", n_perm)})
    out["largest"] = [{"signum": r["signum"], "height_m": r["height_m"], "province": r["province"],
                       "categories": sorted(r["categories"]), "status": r["status"]}
                      for r in sorted(rows, key=lambda r: -r["height_m"])[:15]]
    return out
