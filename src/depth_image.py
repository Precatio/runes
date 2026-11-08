"""Djupbilden som ritsidan (Runmodell) och slingorna bygger på: den automatiska spåranalysen med alla spår och
arrayerna kvar, djupet under stenytan i 0,6 mm per pixel, spårmasken och metadata med rutnätets origo (a0, b0), så att
ritade slingor kan föras över till andra vyer (src/rune_bands.drawn_labels). Används av scripts/depth_dataset.py för de
öppna skanningarna och av POST /api/3d/make_drawable för en uppladdad skanning."""
from __future__ import annotations

import json
import os
import time

import numpy as np


def write(mesh, normal, up, out_base: str, meta_extra: dict) -> dict:
    """Analyse the centred mesh from (normal, up) and write <out_base>.npz and <out_base>.json; returns the metadata."""
    from src.auto_grooves import analyze_grooves
    t0 = time.time()
    g = analyze_grooves(mesh, normal, up=up, resolution_mm=0.6, runes_only=False, keep_arrays=True)
    a = g["arrays"]
    os.makedirs(os.path.dirname(out_base), exist_ok=True)
    np.savez_compressed(out_base + ".npz", depth=np.asarray(a["depth"], dtype=np.float16), mask=a["mask"].astype(bool),
                        wide_area=np.asarray(a["wide_area"]).astype(bool), region=a["region"].astype(bool),
                        inner=a["inner"].astype(bool), res=a["res"])
    meta = {**meta_extra, "res_mm": a["res"], "shape": list(np.shape(a["depth"])), "a0": float(a["a0"]),
            "b0": float(a["b0"]), "normal": [float(v) for v in normal],
            "up": None if up is None else [float(v) for v in up], "stroke_lines": g.get("stroke_lines"),
            "runes": g.get("runes"), "seconds": round(time.time() - t0)}
    tmp = out_base + ".json.tmp"
    json.dump(meta, open(tmp, "w", encoding="utf-8"), ensure_ascii=False)
    os.replace(tmp, out_base + ".json")
    return meta
