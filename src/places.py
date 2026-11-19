"""Platser kring runstenarna: ortnamn som kan tyda på förkristen kult, medeltida kyrkor och fornlämningar
(GET /api/research/places, /api/research/landscape/{signum}, /api/research/place-test; kartan och Stenöversikt).

Samma data som korpusanalysen remains.R använder (METHODS.md 1c–1e): data/ortnamn/ (scripts/fetch_place_names.py) och
data/raa/lamningar.csv (scripts/fetch_raa_remains.py). Avstånden räknas i SWEREF 99 TM med ett kd-träd. Saknas en fil
hoppas den sortens platser över.

Provet "nära mot övriga" i appen är ett utforskande verktyg: det jämför andelen stenar med ett mönster nära en sorts
plats med övriga stenar, med landskapet konstant (Mantel–Haenszel), men utan tidsjustering och utan provet i två
halvor; det fullständiga provet för kultnamnen finns i korpusanalysen. Stenar som står i grupper och delar samma
plats räknas som en enhet när osäkerheten bedöms (src/spatial_groups.py), om inte den som prövar stänger av det.
"""
from __future__ import annotations

import csv
import math
import os
from functools import lru_cache

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CULT = os.path.join(ROOT, "data", "ortnamn", "kultnamn.csv")
CHURCHES = os.path.join(ROOT, "data", "ortnamn", "kyrkor.csv")
REMAINS = os.path.join(ROOT, "data", "raa", "lamningar.csv")

# key, label, group, help
KINDS = [
    ("cult_a", "Teofora ortnamn", "Ortnamn",
     "Ett gudanamn med en sakral efterled: Torsvi, Odensala, Ullevi, Frösö. Den gängse indikationen på en kultplats."),
    ("cult_b", "Sakrala ortnamn", "Ortnamn",
     "Sakrala ord utan gudanamn: Vi, Viby, Harg, Hov, Gudhem. Osäkrare – harg kan betyda stenig mark, hov gård."),
    ("central", "Centralortsnamn", "Ortnamn", "Husby och namn på -tuna utan gudanamn: centralorter utan kult."),
    ("church", "Medeltida kyrkor", "Kyrkor", "Wikidatas kyrkobyggnader med uppförandeår före 1350 – långt ifrån alla."),
    ("gravfalt", "Gravfält", "Fornlämningar", "Registrerade gravfält i Kulturmiljöregistret."),
    ("hog", "Högar", "Fornlämningar", "Registrerade gravhögar i Kulturmiljöregistret."),
    ("vag", "Färdvägar", "Fornlämningar", "Färdvägar och färdvägssystem i Kulturmiljöregistret, ofta yngre än stenarna."),
    ("bro", "Broar", "Fornlämningar", "Registrerade broar i Kulturmiljöregistret, oftast medeltida eller yngre."),
    ("fornborg", "Fornborgar", "Fornlämningar", "Registrerade fornborgar i Kulturmiljöregistret."),
]
KEYS = [k for k, *_ in KINDS]
REMAIN_TYPES = {"gravfalt": {"gravfält"}, "hog": {"hög"}, "vag": {"färdväg", "färdvägssystem"}, "bro": {"bro"},
                "fornborg": {"fornborg"}}


def _mtimes() -> tuple:
    return tuple(os.path.getmtime(p) if os.path.exists(p) else 0 for p in (CULT, CHURCHES, REMAINS))


def _read(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


@lru_cache(maxsize=2)
def _load(_stamp: tuple) -> dict[str, list[dict]]:
    """Alla platser per sort: lat, lon, namn och en kort uppgift (gud, år, RAÄ-nummer)."""
    out: dict[str, list[dict]] = {k: [] for k in KEYS}
    tier = {"A": "cult_a", "B": "cult_b", "C": "central"}
    for r in _read(CULT):
        k = tier.get(r["tier"])
        if k:
            out[k].append({"lat": float(r["lat"]), "lon": float(r["lon"]), "name": r["name"], "info": r.get("god") or ""})
    for r in _read(CHURCHES):
        out["church"].append({"lat": float(r["lat"]), "lon": float(r["lon"]), "name": r["id"], "info": r["year"],
                              "url": f"https://www.wikidata.org/wiki/{r['id']}"})
    for r in _read(REMAINS):
        for k, types in REMAIN_TYPES.items():
            if r["type"] in types:
                out[k].append({"lat": float(r["lat"]), "lon": float(r["lon"]), "name": r["type"], "info": r.get("label") or "",
                               "url": f"https://kulturarvsdata.se/raa/lamning/html/{r['id']}" if r.get("id") else None})
    return out


def places() -> dict[str, list[dict]]:
    return _load(_mtimes())


def available() -> list[str]:
    return [k for k, v in places().items() if v]


@lru_cache(maxsize=1)
def _transformer():
    from pyproj import Transformer
    return Transformer.from_crs("EPSG:4326", "EPSG:3006", always_xy=True)


def _xy(lats, lons):
    import numpy as np
    x, y = _transformer().transform(np.asarray(lons, dtype=float), np.asarray(lats, dtype=float))
    return np.column_stack([x, y])


@lru_cache(maxsize=24)
def _tree(kind: str, _stamp: tuple):
    from scipy.spatial import cKDTree
    pts = places()[kind]
    if not pts:
        return None
    return cKDTree(_xy([p["lat"] for p in pts], [p["lon"] for p in pts]))


def nearest(kind: str, lats, lons) -> tuple[list[float | None], list[int | None]]:
    """Avståndet (km) till närmaste plats av sorten för varje punkt, och platsens index."""
    tree = _tree(kind, _mtimes())
    if tree is None:
        return [None] * len(lats), [None] * len(lats)
    d, i = tree.query(_xy(lats, lons))
    return [round(float(x) / 1000, 2) for x in d], [int(x) for x in i]


def stone_distances(stones: list[dict]) -> tuple[list[str], list[list[float | None]]]:
    """Avstånden från varje sten till varje sorts plats, i ordningen av den första listan."""
    kinds = available()
    lats, lons = [s["lat"] for s in stones], [s["lon"] for s in stones]
    cols = [nearest(k, lats, lons)[0] for k in kinds]
    return kinds, [[None if c[j] is None else round(c[j], 1) for c in cols] for j in range(len(stones))]


def landscape(rec: dict) -> dict:
    """Närmaste plats av varje sort för en sten, med namn och avstånd."""
    from src.r_bridge import is_moved
    rows = []
    for key, label, group, help_ in KINDS:
        if not places()[key] or rec.get("lat") is None:
            continue
        d, i = nearest(key, [rec["lat"]], [rec["lon"]])
        p = places()[key][i[0]]
        rows.append({"key": key, "label": label, "group": group, "help": help_, "km": d[0], "name": p["name"],
                     "info": p["info"], "lat": p["lat"], "lon": p["lon"], "url": p.get("url")})
    placement = (rec.get("placement") or "").strip()
    return {"signum": rec["signum"], "moved": is_moved(rec), "placement": placement or rec.get("place") or None, "rows": rows}


def _fisher_p(a: int, b: int, c: int, d: int) -> float:
    from scipy.stats import fisher_exact
    return float(fisher_exact([[a, b], [c, d]])[1])


def near_test(rows: list[tuple[str, int, float]], km: float, groups: list[int] | None = None) -> dict | None:
    """Nära mot övriga: rows är (landskap, har mönstret 0/1, avstånd i km). Andelar, oddskvot och Mantel–Haenszel per
    landskap (oddskvot och CMH-test med kontinuitetskorrektion). Med groups (en grupp per rad, src/spatial_groups.py)
    också provet med grupperna som enheter: designeffekten, p på gruppnivå, antalet grupper och om svaret skiljer sig."""
    from scipy.stats import chi2
    near = [(p, y) for p, y, d in rows if d is not None and d < km]
    far = [(p, y) for p, y, d in rows if d is not None and d >= km]
    if len(near) < 5 or len(far) < 5:
        return None
    a, b = sum(y for _, y in near), sum(1 - y for _, y in near)
    c, d = sum(y for _, y in far), sum(1 - y for _, y in far)
    crude = (a + 0.5) * (d + 0.5) / ((b + 0.5) * (c + 0.5))
    # Mantel–Haenszel over provinces with stones both near and far
    num = den = sa = ea = va = 0.0
    strata = 0
    for prov in {p for p, _, _ in rows}:
        n1 = [(y) for p, y in near if p == prov]
        n0 = [(y) for p, y in far if p == prov]
        if not n1 or not n0:
            continue
        a_, b_ = sum(n1), len(n1) - sum(n1)
        c_, d_ = sum(n0), len(n0) - sum(n0)
        n = a_ + b_ + c_ + d_
        if n < 2:
            continue
        strata += 1
        num += a_ * d_ / n
        den += b_ * c_ / n
        m1, m0, r1 = a_ + b_, c_ + d_, a_ + c_
        sa += a_
        ea += m1 * r1 / n
        va += m1 * m0 * r1 * (n - r1) / (n * n * (n - 1)) if n > 1 else 0
    mh = num / den if den > 0 else None
    cmh = ((abs(sa - ea) - 0.5) ** 2 / va) if va > 0 else None
    return {"km": km, "n_near": len(near), "n_far": len(far), "k_near": a, "k_far": c,
            "share_near": round(a / len(near), 3), "share_far": round(c / len(far), 3),
            "or_crude": round(crude, 2), "p_crude": round(_fisher_p(a, b, c, d), 4),
            "or_mh": None if mh is None or not math.isfinite(mh) else round(mh, 2),
            "p_mh": None if cmh is None else round(float(chi2.sf(cmh, 1)), 4), "strata": strata,
            **({"groups": _group_level(rows, km, groups)} if groups is not None else {})}


def _group_level(rows, km: float, groups: list[int]) -> dict:
    """Samma jämförelse med stenarna i grupper som enheter (src/spatial_groups.cluster_cmh), och antalet grupper bland
    stenarna nära och övriga."""
    from src import spatial_groups as sg
    items = [(p, int(d < km), y, g) for (p, y, d), g in zip(rows, groups, strict=True) if d is not None]
    res = sg.cluster_cmh(items)
    near_g = {g for _, x, _, g in items if x == 1}
    far_g = {g for _, x, _, g in items if x == 0}

    def r(v, n=4):
        return None if v is None else round(v, n)
    return {"n_groups": len(near_g | far_g), "n_groups_near": len(near_g), "n_groups_far": len(far_g),
            "link_km": sg.link_km(km), "design_effect": r(res["design_effect"], 2), "effective_n": r(res["effective_n"], 0),
            "p_stone": r(res["p_stone"]), "p_group": r(res["p_group"]), "df": res["df"],
            "ci_group": None if res["ci_group"] is None else [round(v, 2) for v in res["ci_group"]],
            "verdict": sg.verdict(res)}
