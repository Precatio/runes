"""Lerkantens kontroller enligt den låsta planen analysplaner/2026-11-10-lerkanten-kontroller.md (sha256 f88ff01f…):
K1 bortfall per jordart och skillnaden med de försvunna stenarna på sina uppgivna platser; K4 vattnet år 950 i stället
för 1050; K5 utan de stenar som Runor 2020 anger som flyttade; K6 Malmers dos–respons (beskrivande). K2 och K3 (åsar och
sand, våt mark) räknas i kontroller.R på punkttabellen som skrivs här (kontroller_punkter.csv).
Definitioner som i platsen.py: 2 km-bygderutor, 50 slumpvisa platser på land per sten, kanten = inom 200 m från lera och
silt (inte på den), 95 % intervall med blockbootstrap (20 km).
    .venv/bin/python utdata/palm_jordarna/kontroller.py"""
import json
import os

import numpy as np
import pandas as pd
from PIL import Image
from pyproj import Transformer

Image.MAX_IMAGE_PIXELS = None
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
E0, N1, RES, CELL = 250000.0, 7700000.0, 100.0, 2000.0
WIN = 20
NAMES = {1: "lera och silt", 2: "sand och grus", 3: "morän", 4: "torv och gyttja", 5: "berg", 7: "övrigt"}

soil = np.asarray(Image.open(os.path.join(HERE, "jordart_100m.tif")))
H, W = soil.shape
WATER = {"1050": np.asarray(Image.open("/Volumes/2TB/cache/terra/vatten1050_100m.tif")) == 1,
         "950": np.asarray(Image.open("/Volumes/2TB/cache/terra/vatten950_100m.tif")) == 1}
cells = pd.read_csv(os.path.join(HERE, "rutor_2000.csv"))
settled = set(zip(cells.x.astype(int), cells.y.astype(int)))


def cell_of(x, y):
    return (int(E0 + CELL * np.floor((x - E0) / CELL) + CELL / 2), int(N1 - CELL * np.floor((N1 - y) / CELL) - CELL / 2))


def pix(x, y):
    return int((N1 - y) // RES), int((x - E0) // RES)


class Ground:
    """The land, clay, sand and wet ground of one water level, and the nearest distance to each from a point."""
    def __init__(self, level):
        water = WATER[level]
        self.land = (soil >= 1) & (soil <= 7) & (soil != 6) & ~water
        self.mask = {"clay": (soil == 1) & ~water, "sand": (soil == 2) & ~water, "peat": (soil == 4) & ~water}

    def near(self, r, c, m):
        win = self.mask[m][r - WIN:r + WIN + 1, c - WIN:c + WIN + 1]
        rr, cc = np.nonzero(win)
        return float(np.min(np.hypot(rr - WIN, cc - WIN)) * RES) if len(rr) else np.inf

    def describe(self, x, y):
        r, c = pix(x, y)
        if not (WIN <= r < H - WIN and WIN <= c < W - WIN):
            return None
        return {"soil": int(soil[r, c]) if self.land[r, c] else None,
                "d_clay": self.near(r, c, "clay"), "d_sand": self.near(r, c, "sand"), "d_peat": self.near(r, c, "peat")}

    def random_in(self, cell, n, rng):
        cx, cy = cell
        out, tries = [], 0
        while len(out) < n and tries < n * 20:
            x, y = cx + rng.uniform(-CELL / 2, CELL / 2), cy + rng.uniform(-CELL / 2, CELL / 2)
            r, c = pix(x, y)
            if 0 <= r < H and 0 <= c < W and self.land[r, c]:
                out.append((x, y))
            tries += 1
        return out


on = lambda d: float(d["d_clay"] == 0)  # noqa: E731
edge = lambda d: float(0 < d["d_clay"] <= 200)  # noqa: E731


def compare(xs, ys, ground, seed=2026, points=None, ids=None):
    """Stone minus its own cell's random share, on clay and at the edge, with a 20 km block bootstrap."""
    rng = np.random.default_rng(seed)
    pairs = []
    for i, (x, y) in enumerate(zip(xs, ys)):
        cl = cell_of(x, y)
        if cl not in settled:
            continue
        o = ground.describe(x, y)
        rs = [d for d in (ground.describe(px, py) for px, py in ground.random_in(cl, 50, rng)) if d is not None]
        if o is None or not rs:
            continue
        pairs.append((int(x // 20000), int(y // 20000), on(o) - np.mean([on(d) for d in rs]), edge(o) - np.mean([edge(d) for d in rs]),
                      on(o), np.mean([on(d) for d in rs]), edge(o), np.mean([edge(d) for d in rs])))
        if points is not None:
            sid = ids[i] if ids is not None else i
            for k, d in enumerate([o] + rs):
                points.append((sid, int(k == 0), edge(d), float(d["d_sand"] <= 200), float(d["d_peat"] <= 200), on(d)))
    P = pd.DataFrame(pairs, columns=["bx", "by", "on", "edge", "o_on", "r_on", "o_edge", "r_edge"])
    blocks = [g for _, g in P.groupby(["bx", "by"])]
    brng = np.random.default_rng(seed + 1)
    boot = np.array([(lambda b: (b.on.mean(), b.edge.mean()))(pd.concat([blocks[i] for i in brng.integers(0, len(blocks), len(blocks))]))
                     for _ in range(2000)])
    return {"n": len(P), "blocks": len(blocks), "on_clay": float(P.o_on.mean()), "on_clay_random": float(P.r_on.mean()),
            "on_clay_diff": float(P.on.mean()), "on_clay_diff_95": [float(v) for v in np.percentile(boot[:, 0], [2.5, 97.5])],
            "edge": float(P.o_edge.mean()), "edge_random": float(P.r_edge.mean()),
            "edge_diff": float(P.edge.mean()), "edge_diff_95": [float(v) for v in np.percentile(boot[:, 1], [2.5, 97.5])]}


def holds(r):
    return r["edge_diff_95"][0] > 0, r["on_clay_diff_95"][1] < 0


corp = pd.read_csv(os.path.join(ROOT, "data", "cache", "r", "corpus", "510ebfb3acc9a229", "corpus.csv"), low_memory=False)
corp = corp[corp.lat.notna()].copy()
to = Transformer.from_crs(4326, 3006, always_xy=True)
corp["x"], corp["y"] = to.transform(corp.lon.values, corp.lat.values)
# coordinates shared by three or more stones are probably a parish or church point, not the stone's own place (K1)
shared = corp.groupby(["lat", "lon"]).signum.transform("count") >= 3
base = corp[(corp.moved == 0) & (corp.lost == 0)]
g1050, g950 = Ground("1050"), Ground("950")
out = {"plan": "analysplaner/2026-11-10-lerkanten-kontroller.md", "sha256": "f88ff01f68becfd93ad5e890200bacaaa0f41c2ef542b123359e8a145535b31e"}

# Huvudresultatet, som platsen.py, och punkttabellen för K2 och K3
points = []
out["huvud"] = compare(base.x.values, base.y.values, g1050, points=points, ids=base.signum.values)
pd.DataFrame(points, columns=["stone", "obs", "edge", "sand200", "peat200", "on_clay"]).to_csv(os.path.join(HERE, "kontroller_punkter.csv"), index=False)
print("huvud", {k: out["huvud"][k] for k in ("n", "on_clay_diff", "on_clay_diff_95", "edge_diff", "edge_diff_95")})

# K1: bortfall per jordart (alla med egna koordinater i bygden), och skillnaden med de försvunna på sina platser
rows = []
for s in corp[~shared].itertuples():
    if cell_of(s.x, s.y) not in settled:
        continue
    d = g1050.describe(s.x, s.y)
    if d is None or d["soil"] is None:
        continue
    rows.append((NAMES.get(d["soil"], "övrigt"), int(s.lost == 1), int(s.moved == 1), on(d), edge(d)))
R = pd.DataFrame(rows, columns=["jord", "lost", "moved", "on", "edge"])
per_soil = {j: {"n": int(len(g)), "forsvunna": float(g.lost.mean()), "flyttade": float(g.moved.mean())} for j, g in R.groupby("jord")}
lost = corp[(corp.lost == 1) & ~shared]
with_lost = pd.concat([base, lost])
k1 = compare(with_lost.x.values, with_lost.y.values, g1050)
deficit = (out["huvud"]["on_clay_random"] - out["huvud"]["on_clay"]) * out["huvud"]["n"]  # stones missing on clay
n_lost_settled = int(sum(cell_of(x, y) in settled for x, y in zip(lost.x, lost.y)))
out["K1"] = {"per_jordart": per_soil, "med_forsvunna": k1, "forsvunna_med_egen_plats_i_bygden": n_lost_settled,
             "underskott_pa_leran_antal_stenar": float(deficit), "holds": bool(all(holds(k1)))}
print("K1", per_soil, "\n   med försvunna", {k: k1[k] for k in ("n", "on_clay_diff", "on_clay_diff_95", "edge_diff", "edge_diff_95")},
      "\n   underskott", round(deficit, 1), "försvunna i bygden", n_lost_settled)

# K4: vattnet omkring år 950
k4 = compare(base.x.values, base.y.values, g950)
out["K4"] = {"vatten_950": k4, "holds": bool(holds(k4)[0] and holds(out["huvud"])[0])}
print("K4", {k: k4[k] for k in ("n", "on_clay_diff", "on_clay_diff_95", "edge_diff", "edge_diff_95")})

# K5: utan de stenar som Runor 2020 anger som inte på ursprunglig plats
runor = json.load(open(os.path.join(ROOT, "data", "raa", "runor_2020.json"), encoding="utf-8"))["inscriptions"]
moved_runor = {i["signum"] for i in runor if i.get("original") is False} | {a for i in runor if i.get("original") is False for a in i.get("alt_signa") or []}
b5 = base[~base.signum.isin(moved_runor)]
k5 = compare(b5.x.values, b5.y.values, g1050)
out["K5"] = {"utan_runor_flyttade": k5, "borttagna": int(len(base) - len(b5)), "holds": bool(holds(k5)[0])}
print("K5", len(base) - len(b5), "borttagna", {k: k5[k] for k in ("n", "on_clay_diff", "on_clay_diff_95", "edge_diff", "edge_diff_95")})

# K6: Malmers dos–respons, beskrivande
rows = []
for s in base.itertuples():
    if cell_of(s.x, s.y) not in settled:
        continue
    d = g1050.describe(s.x, s.y)
    if d is None:
        continue
    rows.append((s.n_words, isinstance(s.style, str) and s.style.strip() != "", bool(s.cross) if pd.notna(s.cross) else False, on(d), edge(d)))
M = pd.DataFrame(rows, columns=["words", "ornament", "cross", "on", "edge"])
M["ord_tredjedel"] = pd.qcut(M.words.rank(method="first"), 3, labels=["kort text", "mellan", "lång text"])
k6 = {}
for col in ("ord_tredjedel", "ornament", "cross"):
    k6[col] = {str(k): {"n": int(len(g)), "pa_leran": float(g.on.mean()), "vid_kanten": float(g.edge.mean())} for k, g in M.groupby(col, observed=True)}
out["K6"] = k6
print("K6", json.dumps(k6, ensure_ascii=False))
json.dump(out, open(os.path.join(HERE, "kontroller.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
