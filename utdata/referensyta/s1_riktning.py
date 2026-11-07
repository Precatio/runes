"""S1 i analysplaner/2026-11-07-referensyta-paraboloid.md (sha 5f64ffe4): riktningsberoende på konstgjorda spår. Ett plant
höjdfält (0,5 mm per cell, brus 0,03 mm) med ett rakt V-spår (bredd 8 mm, djup 2 mm) i riktningarna 0°, 22,5°, 45° och
67,5°; djupet under referensen mitt i spåret och spårmaskens bredd vid tröskeln 0,3 mm, med båda referensytorna.
Skriver s1.json.
    PYTHONPATH=. .venv/bin/python utdata/referensyta/s1_riktning.py"""
import json
import os
import sys
from types import SimpleNamespace

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))
from src.auto_grooves import reference_surface  # noqa: E402

RES, SIZE, DEPTH, HALF, NOISE, THRESH = 0.5, 300.0, 2.0, 4.0, 0.03, 0.3
n = int(SIZE / RES)
y, x = (np.mgrid[0:n, 0:n] * RES) - SIZE / 2
rng = np.random.default_rng(2026)
out = {"plan_sha": "5f64ffe4", "angles": [0, 22.5, 45, 67.5], "true_depth_mm": DEPTH, "true_width_at_threshold_mm":
       2 * HALF * (1 - THRESH / DEPTH)}
for kind in ("square", "paraboloid"):
    rows = []
    for ang in out["angles"]:
        t = np.radians(ang)
        across = -x * np.sin(t) + y * np.cos(t)       # distance across the groove
        along = x * np.cos(t) + y * np.sin(t)
        H = -np.clip(1 - np.abs(across) / HALF, 0, None) * DEPTH + rng.normal(0, NOISE, x.shape)
        ref = reference_surface(SimpleNamespace(H=H, res=RES), scale_mm=20.0, kind=kind)
        resid = H - ref
        core = (np.abs(along) < 50) & (np.abs(across) < RES)        # the groove's centre line, middle 100 mm
        band = (np.abs(along) < 50) & (np.abs(across) < 3 * HALF)
        depth = float(np.median(-resid[core]))
        width = float((resid[band] < -THRESH).sum() * RES * RES / 100.0)   # mask area / 100 mm of groove
        rows.append({"angle": ang, "depth_mm": round(depth, 3), "width_mm": round(width, 2)})
    d = [r["depth_mm"] for r in rows]; w = [r["width_mm"] for r in rows]
    out[kind] = {"rows": rows, "depth_spread_mm": round(max(d) - min(d), 3), "width_spread_mm": round(max(w) - min(w), 2),
                 "max_depth_error_mm": round(max(abs(v - DEPTH) for v in d), 3)}
S, P = out["square"], out["paraboloid"]
out["holds"] = bool(P["depth_spread_mm"] < S["depth_spread_mm"] and P["width_spread_mm"] <= S["width_spread_mm"]
                    and P["max_depth_error_mm"] <= S["max_depth_error_mm"])
json.dump(out, open(os.path.join(HERE, "s1.json"), "w"), indent=1)
for k in ("square", "paraboloid"):
    print(k, out[k])
print("S1 håller:", out["holds"])
