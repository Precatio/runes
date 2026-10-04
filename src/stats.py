"""Statistik för huggspårsmätningar: osäkerhet, jämförelse, klustring och attribuering.

Allt är deterministiskt och reproducerbart (fast slumpfrö för permutationstester).
"""
from __future__ import annotations

import math

import numpy as np
from scipy import stats as sps
from scipy.cluster.hierarchy import dendrogram, linkage

# Mått som ingår i flervariabelanalyserna (samma ordning överallt)
METRICS = ["apex_vinkel_deg", "asymmetri_deg", "spårdjup_mm", "spårbredd_mm",
           "djup_bredd_kvot", "bottenradie_mm", "ytråhet_mm"]
METRIC_LABELS = {
    "apex_vinkel_deg": "V-vinkel (°)",
    "asymmetri_deg": "Asymmetri (°)",
    "spårdjup_mm": "Spårdjup (mm)",
    "spårbredd_mm": "Spårbredd (mm)",
    "djup_bredd_kvot": "Djup/bredd",
    "bottenradie_mm": "Bottenradie (mm)",
    "ytråhet_mm": "Ytråhet (mm)",
}


def _clean(values) -> np.ndarray:
    arr = np.asarray([v for v in values if v is not None], dtype=float)
    return arr[np.isfinite(arr)]


def summarize(values) -> dict:
    """Medelvärde, standardavvikelse, n och 95 % konfidensintervall (t-fördelning)."""
    arr = _clean(values)
    n = int(arr.size)
    if n == 0:
        return {"n": 0, "mean": None, "sd": None, "ci95": None, "min": None, "max": None}
    mean = float(arr.mean())
    sd = float(arr.std(ddof=1)) if n > 1 else 0.0
    if n > 1:
        half = float(sps.t.ppf(0.975, n - 1) * sd / math.sqrt(n))
        ci = [mean - half, mean + half]
    else:
        ci = None
    return {"n": n, "mean": mean, "sd": sd, "ci95": ci, "min": float(arr.min()), "max": float(arr.max())}


def summarize_slices(slices: list[dict]) -> dict:
    return {m: summarize([s.get(m) for s in slices]) for m in METRICS}


def permutation_test(a, b, n_perm: int = 5000, seed: int = 0) -> dict:
    """Tvåsidigt permutationstest för skillnad i medelvärde mellan två stickprov."""
    a, b = _clean(a), _clean(b)
    if a.size < 2 or b.size < 2:
        return {"p_value": None, "diff": None, "note": "Minst två snitt per sten krävs."}
    rng = np.random.default_rng(seed)
    observed = abs(a.mean() - b.mean())
    pooled = np.concatenate([a, b])
    hits = 0
    for _ in range(n_perm):
        rng.shuffle(pooled)
        if abs(pooled[:a.size].mean() - pooled[a.size:].mean()) >= observed - 1e-12:
            hits += 1
    pooled_sd = math.sqrt(((a.size - 1) * a.var(ddof=1) + (b.size - 1) * b.var(ddof=1)) / (a.size + b.size - 2))
    return {
        "p_value": (hits + 1) / (n_perm + 1),
        "diff": float(a.mean() - b.mean()),
        "effect_size_d": float((a.mean() - b.mean()) / pooled_sd) if pooled_sd > 0 else None,
    }


def multivariate_permutation_test(A: np.ndarray, B: np.ndarray, n_perm: int = 5000, seed: int = 0) -> dict:
    """Permutationstest på avståndet mellan standardiserade medelvektorer (alla mått samtidigt)."""
    A, B = np.asarray(A, float), np.asarray(B, float)
    if len(A) < 2 or len(B) < 2:
        return {"p_value": None, "note": "Minst två snitt per sten krävs."}
    X = np.vstack([A, B])
    sd = X.std(axis=0, ddof=1)
    sd[sd == 0] = 1.0
    Z = (X - X.mean(axis=0)) / sd
    na = len(A)

    def stat(z):
        return float(np.linalg.norm(z[:na].mean(axis=0) - z[na:].mean(axis=0)))

    observed = stat(Z)
    rng = np.random.default_rng(seed)
    hits = 0
    for _ in range(n_perm):
        idx = rng.permutation(len(Z))
        if stat(Z[idx]) >= observed - 1e-12:
            hits += 1
    return {"p_value": (hits + 1) / (n_perm + 1), "distance": observed}


def compare_stones(slices_a: list[dict], slices_b: list[dict], metrics=METRICS) -> dict:
    """Jämför två stenars snittmätningar mått för mått och samlat."""
    per_metric = []
    for m in metrics:
        a = [s.get(m) for s in slices_a]
        b = [s.get(m) for s in slices_b]
        per_metric.append({"metric": m, "label": METRIC_LABELS.get(m, m),
                           "a": summarize(a), "b": summarize(b), **permutation_test(a, b)})
    usable = [m for m in metrics
              if all(s.get(m) is not None for s in slices_a + slices_b)]
    A = np.array([[s[m] for m in usable] for s in slices_a]) if usable else np.empty((0, 0))
    B = np.array([[s[m] for m in usable] for s in slices_b]) if usable else np.empty((0, 0))
    overall = multivariate_permutation_test(A, B) if usable else {"p_value": None}
    # Bonferroni-justering för antalet enskilda test
    k = sum(1 for r in per_metric if r["p_value"] is not None)
    for r in per_metric:
        r["p_adjusted"] = min(1.0, r["p_value"] * k) if r["p_value"] is not None else None
    return {
        "per_metric": per_metric,
        "overall": {**overall, "metrics_used": usable},
        "interpretation": interpret_comparison(overall.get("p_value")),
    }


def interpret_comparison(p) -> str:
    if p is None:
        return "För få snitt för ett test."
    if p < 0.01:
        return ("Tydlig skillnad i huggteknik (p < 0,01). Talar emot samma verktyg/hand, "
                "men vittring, stenart och skanningskvalitet kan också ge skillnader.")
    if p < 0.05:
        return "Viss skillnad i huggteknik (p < 0,05). Tolka försiktigt."
    return ("Ingen påvisbar skillnad (p ≥ 0,05). Det är förenligt med samma hand, "
            "men bevisar det inte – många ristare kan ha liknande teknik.")


def standardize(X: np.ndarray):
    X = np.asarray(X, float)
    mu = X.mean(axis=0)
    sd = X.std(axis=0, ddof=1) if len(X) > 1 else np.ones(X.shape[1])
    sd[sd == 0] = 1.0
    return (X - mu) / sd, mu, sd


def ward_clustering(labels: list[str], X: np.ndarray) -> dict:
    """Hierarkisk klustring (Ward, euklidiska avstånd på standardiserade variabler),
    som i Kitzler Åhfeldts analyser av huggteknik."""
    if len(labels) < 3:
        return {"note": "Minst tre stenar krävs för klustring."}
    Z, _, _ = standardize(X)
    L = linkage(Z, method="ward", metric="euclidean")
    dn = dendrogram(L, labels=labels, no_plot=True)
    return {
        "linkage": L.tolist(),
        "order": dn["ivl"],
        "icoord": dn["icoord"],
        "dcoord": dn["dcoord"],
    }


def _shrunk_cov(Z: np.ndarray, shrink: float = 0.2) -> np.ndarray:
    p = Z.shape[1]
    if len(Z) < 2:
        return np.eye(p)
    S = np.cov(Z, rowvar=False)
    return (1 - shrink) * S + shrink * np.eye(p) * np.trace(S) / p


def attribute(reference: list[dict], query: list[float], min_per_group: int = 2) -> dict:
    """Rangordnar grupper (t.ex. ristare) efter Mahalanobisavstånd från en sten.

    reference: [{"group": "Balle", "label": "U 729", "values": [..METRICS..]}, ...]
    Använder poolad, krympt kovarians på standardiserade data. Grupper med färre än
    min_per_group stenar tas inte med. Returnerar även korsvaliderad träffsäkerhet."""
    groups = {}
    for r in reference:
        groups.setdefault(r["group"], []).append(r["values"])
    groups = {g: v for g, v in groups.items() if len(v) >= min_per_group}
    if len(groups) < 2:
        return {"ranking": [], "evaluation": None,
                "note": f"Referenskorpusen har för få ristare med minst {min_per_group} uppmätta stenar."}

    all_rows = np.array([v for vals in groups.values() for v in vals], float)
    _, mu, sd = standardize(all_rows)
    zq = (np.asarray(query, float) - mu) / sd
    pooled = np.vstack([(np.array(v) - mu) / sd - ((np.array(v) - mu) / sd).mean(axis=0) for v in groups.values()])
    inv = np.linalg.pinv(_shrunk_cov(pooled))

    ranking = []
    for g, vals in groups.items():
        centre = ((np.array(vals) - mu) / sd).mean(axis=0)
        d = zq - centre
        ranking.append({"group": g, "n": len(vals), "distance": float(math.sqrt(max(0.0, d @ inv @ d)))})
    ranking.sort(key=lambda r: r["distance"])
    return {"ranking": ranking, "evaluation": evaluate_loo(groups)}


def evaluate_loo(groups: dict[str, list]) -> dict:
    """Lämna-en-ute-korsvalidering av närmaste-centroid-klassificering (Mahalanobis)."""
    items = [(g, np.array(v, float)) for g, vals in groups.items() for v in vals]
    if len(items) < 4:
        return None
    correct1 = correct3 = 0
    for i, (true_g, x) in enumerate(items):
        rest = {}
        for j, (g, v) in enumerate(items):
            if j != i:
                rest.setdefault(g, []).append(v)
        rest = {g: v for g, v in rest.items() if len(v) >= 1}
        rows = np.array([v for vals in rest.values() for v in vals])
        _, mu, sd = standardize(rows)
        pooled = np.vstack([((np.array(v) - mu) / sd) - ((np.array(v) - mu) / sd).mean(axis=0) for v in rest.values()])
        inv = np.linalg.pinv(_shrunk_cov(pooled))
        zx = (x - mu) / sd
        dists = sorted(
            (float((zx - ((np.array(v) - mu) / sd).mean(axis=0)) @ inv @ (zx - ((np.array(v) - mu) / sd).mean(axis=0))), g)
            for g, v in rest.items()
        )
        order = [g for _, g in dists]
        correct1 += order[0] == true_g
        correct3 += true_g in order[:3]
    n = len(items)
    n_groups = len(groups)
    return {
        "n_stones": n,
        "n_groups": n_groups,
        "top1_accuracy": correct1 / n,
        "top3_accuracy": correct3 / n,
        "chance_top1": 1 / n_groups,
        "method": "Lämna-en-ute, närmaste centroid (Mahalanobis, poolad krympt kovarians)",
    }
