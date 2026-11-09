"""Palms jordar, efter provet (beskrivande, inte i den låsta planen 85a70fa3): står runstenarna och gravfälten PÅ leran,
eller vid dess kant? Jorden under varje runsten (som står kvar) och varje gravfält i bygderutorna, och avståndet till
närmaste lera som var land år 1050, mot slumpvisa platser på land i samma 2 km-ruta (50 per sten, 5 per gravfält).
Skriver platsen.json.
    .venv/bin/python utdata/palm_jordarna/platsen.py
Gravfälten: /Volumes/2TB/cache/terra/gravfalt_xy.csv (KMR, lämningstyp Gravfält, punkter och ytor som i rutor.R)."""
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
NAMES = {1: "lera och silt", 2: "sand och grus", 3: "morän", 4: "torv och gyttja", 5: "berg", 7: "övrigt"}
WIN = 20  # search for clay within ± 2 km
rng = np.random.default_rng(2026)

soil = np.asarray(Image.open(os.path.join(HERE, "jordart_100m.tif")))
water = np.asarray(Image.open("/Volumes/2TB/cache/terra/vatten1050_100m.tif")) == 1
land = (soil >= 1) & (soil <= 7) & (soil != 6) & ~water
clay = (soil == 1) & ~water
H, W = soil.shape

cells = pd.read_csv(os.path.join(HERE, "rutor_2000.csv"))
settled = set(zip(cells.x.astype(int), cells.y.astype(int)))
# the region groups of analys.R (P2): the Mälar lands, inland Götaland, and the rest of Viking-age Sweden
MALAR = {"attundaland", "tiundaland", "fjadrundaland", "roden", "U", "Sö", "Vs"}
GOTA = {"Vg", "Sm", "aspeland", "finnveden", "handbord", "kinda", "mo", "more", "njudung", "sevede", "tjust", "tveta",
        "varend", "vedbo", "vista"}
REGION = {(int(x), int(y)): ("Mälardalen" if r in MALAR else "Götalands inland" if r in GOTA else "övriga landskap")
          for x, y, r in zip(cells.x, cells.y, cells.region)}
rng_region = np.random.default_rng(7)  # its own generator: the region intervals leave the main draws unchanged


def cell_of(x, y):
    return (int(E0 + CELL * np.floor((x - E0) / CELL) + CELL / 2), int(N1 - CELL * np.floor((N1 - y) / CELL) - CELL / 2))


def pix(x, y):
    return int((N1 - y) // RES), int((x - E0) // RES)


def describe(x, y):
    r, c = pix(x, y)
    if not (WIN <= r < H - WIN and WIN <= c < W - WIN):
        return None
    k = int(soil[r, c]) if land[r, c] else None
    win = clay[r - WIN:r + WIN + 1, c - WIN:c + WIN + 1]
    rr, cc = np.nonzero(win)
    d = float(np.min(np.hypot(rr - WIN, cc - WIN)) * RES) if len(rr) else None
    return k, d


def random_in(cell, n):
    """n random points on land of 1050 in the 2 km cell."""
    cx, cy = cell
    out, tries = [], 0
    while len(out) < n and tries < n * 20:
        x, y = cx + rng.uniform(-CELL / 2, CELL / 2), cy + rng.uniform(-CELL / 2, CELL / 2)
        r, c = pix(x, y)
        if 0 <= r < H and 0 <= c < W and land[r, c]:
            out.append((x, y))
        tries += 1
    return out


def summary(rows):
    rows = [r for r in rows if r is not None]
    k = [r[0] for r in rows]
    d = np.array([r[1] if r[1] is not None else np.inf for r in rows])
    on_land = [x for x in k if x is not None]
    return {"n": len(rows), "on_land": len(on_land),
            "soil": {NAMES[c]: float(np.mean([x == c for x in on_land])) for c in NAMES},
            "on_clay": float(np.mean(d == 0)), "edge_within_200m": float(np.mean((d > 0) & (d <= 200))),
            "within_500m": float(np.mean(d <= 500)), "over_1km": float(np.mean(d > 1000)),
            "median_m": float(np.median(d)) if np.isfinite(np.median(d)) else None}


corp = pd.read_csv(os.path.join(ROOT, "data", "cache", "r", "corpus", "510ebfb3acc9a229", "corpus.csv"), low_memory=False)
st = corp[(corp.moved == 0) & (corp.lost == 0) & corp.lat.notna()]
X, Y = Transformer.from_crs(4326, 3006, always_xy=True).transform(st.lon.values, st.lat.values)
gf = pd.read_csv("/Volumes/2TB/cache/terra/gravfalt_xy.csv")
groups = {}
for name, xs, ys, per in (("runstenar", X, Y, 50), ("gravfält", gf.x.values, gf.y.values, 5)):
    obs, rnd, pairs = [], [], []
    for x, y in zip(xs, ys):
        cl = cell_of(x, y)
        if cl not in settled:
            continue
        o1 = describe(x, y)
        r1 = [describe(px, py) for px, py in random_in(cl, per)]
        obs.append(o1)
        rnd += r1
        r1 = [r for r in r1 if r is not None]
        if o1 is not None and r1:  # per point: observed minus its own cell's random share, for the block bootstrap
            dd = lambda r: r[1] if r[1] is not None else np.inf  # noqa: E731
            on_r, edge_r = np.mean([dd(r) == 0 for r in r1]), np.mean([0 < dd(r) <= 200 for r in r1])
            pairs.append((int(x // 20000), int(y // 20000), float(dd(o1) == 0) - on_r, float(0 < dd(o1) <= 200) - edge_r,
                          REGION[cl], float(dd(o1) == 0), on_r, float(0 < dd(o1) <= 200), edge_r))
    groups[name] = {"observed": summary(obs), "random_same_cells": summary(rnd)}
    # 95 % intervals for the differences, resampling 20 km blocks (stones and grave fields lie in groups)
    P = pd.DataFrame(pairs, columns=["bx", "by", "on", "edge", "region", "o_on", "r_on", "o_edge", "r_edge"])
    blocks = [g for _, g in P.groupby(["bx", "by"])]
    boot = []
    for _ in range(2000):
        b = pd.concat([blocks[i] for i in rng.integers(0, len(blocks), len(blocks))])
        boot.append((b.on.mean(), b.edge.mean()))
    boot = np.array(boot)
    groups[name]["difference"] = {"on_clay": float(P.on.mean()), "on_clay_95": [float(x) for x in np.percentile(boot[:, 0], [2.5, 97.5])],
                                  "edge": float(P.edge.mean()), "edge_95": [float(x) for x in np.percentile(boot[:, 1], [2.5, 97.5])],
                                  "blocks": len(blocks)}
    print(name, "skillnad på lera", groups[name]["difference"])
    by_region = {}
    for reg, Q in P.groupby("region"):
        bl = [g for _, g in Q.groupby(["bx", "by"])]
        bt = np.array([(lambda b: (b.on.mean(), b.edge.mean()))(pd.concat([bl[i] for i in rng_region.integers(0, len(bl), len(bl))]))
                       for _ in range(2000)])
        by_region[reg] = {"n": len(Q), "blocks": len(bl), "on_clay": float(Q.o_on.mean()), "on_clay_random": float(Q.r_on.mean()),
                          "edge": float(Q.o_edge.mean()), "edge_random": float(Q.r_edge.mean()),
                          "on_clay_diff_95": [float(x) for x in np.percentile(bt[:, 0], [2.5, 97.5])],
                          "edge_diff_95": [float(x) for x in np.percentile(bt[:, 1], [2.5, 97.5])]}
        v = by_region[reg]
        print(f"   {reg}: {v['n']} | på lera {v['on_clay']:.0%} (slump {v['on_clay_random']:.0%}) "
              f"[{100*v['on_clay_diff_95'][0]:+.0f}, {100*v['on_clay_diff_95'][1]:+.0f}] | kant {v['edge']:.0%} "
              f"(slump {v['edge_random']:.0%}) [{100*v['edge_diff_95'][0]:+.0f}, {100*v['edge_diff_95'][1]:+.0f}]")
    groups[name]["by_region"] = by_region
    o, r = groups[name]["observed"], groups[name]["random_same_cells"]
    print(f"{name}: {o['n']} | på lera {o['on_clay']:.0%} (slump {r['on_clay']:.0%}) | kant ≤200 m {o['edge_within_200m']:.0%} "
          f"({r['edge_within_200m']:.0%}) | ≤500 m {o['within_500m']:.0%} ({r['within_500m']:.0%}) | median {o['median_m']} "
          f"({r['median_m']}) m")
    print("   jord under:", {k: f"{v:.0%}" for k, v in o["soil"].items()}, "\n   slump:     ", {k: f"{v:.0%}" for k, v in r["soil"].items()})
json.dump({"note": "Efter provet, beskrivande (inte i den låsta planen 85a70fa3)", "window_m": WIN * RES, **groups},
          open(os.path.join(HERE, "platsen.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
