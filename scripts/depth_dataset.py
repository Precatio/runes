"""Djupbilder för runigenkänningen (rune-recognizer): varje öppen skanning körs genom den automatiska spåranalysen med
alla spår och arrayerna kvar, och djupet under stenytan sparas som en bild i 0,6 mm per pixel, tillsammans med
spårmasken, strecklinjerna (slingkanter m.m.), analysens runor och stenens text ur Rundata.

En fil per anrop (minnet släpps inte mellan stora skanningar), samma normal som protokollmätningen:
    .venv/bin/python -m scripts.depth_dataset SERIE FILNAMN
Utdata: /Volumes/2TB/cache/runmodell/djup/<serie>/<fil>.npz (depth float16 i mm, mask, res) och .json (metadata).
Metadata har rutnätets origo (a0, b0), som rune_bands.drawn_labels behöver för att föra över ritade slingor. Djupbilder
gjorda före 2026-11-08 saknade det; fyll i dem (laddar skanningen, kontrollerar att rutnätet blir djupbildens):
    .venv/bin/python -m scripts.depth_dataset --origin SERIE STEM
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
from scripts.batch_scans import result_path  # noqa: E402
from scripts.download_open_scans import local_path  # noqa: E402

OUT = "/Volumes/2TB/cache/runmodell/djup"


def main(series: str, name: str):
    import trimesh
    from api.rundata import store
    files = json.load(open(os.path.join(ROOT, "data", "scan_files.json"), encoding="utf-8"))["datasets"][series]["files"]
    f = next(x for x in files if x["name"] == name)
    stem = os.path.splitext(name)[0].replace(" ", "_")
    out = os.path.join(OUT, series, stem)
    if os.path.exists(out + ".npz"):
        print(f"{name}: finns redan")
        return
    p = json.load(open(result_path(series, f), encoding="utf-8"))  # the protocol measurement: normal and up
    mesh = trimesh.load(local_path(series, name), process=False)
    mesh.apply_translation(-mesh.bounds.mean(axis=0))  # centred as the app does (geo.center)
    rec = store().get(f["signum"]) if f.get("signum") else None
    from src.depth_image import write
    meta = write(mesh, p["normal"], (p.get("parameters") or {}).get("up"), out, {
        "series": series, "file": name, "sha256": f.get("sha256"), "signum": f.get("signum"), "signa": f.get("signa"),
        "transliteration": (rec or {}).get("transliteration"), "rune_types": (rec or {}).get("rune_types"),
        "object": (rec or {}).get("object"), "material": (rec or {}).get("material")})
    print(f"{name}: {meta['shape'][1]}×{meta['shape'][0]} px, {len(meta['stroke_lines'] or [])} streck "
          f"({meta['seconds']} s)", flush=True)


def fill_origin(series: str, stem: str) -> tuple[float, float] | None:
    """a0, b0 for a depth image made before they were stored: the analysis grid's origin is the smallest projection of
    the centred mesh's vertices and triangle centres on u and v (auto_grooves.Heightfield.from_mesh), and the grid it
    gives must be the depth image's. None when the metadata already has it."""
    import trimesh
    from src.auto_grooves import basis
    path = os.path.join(OUT, series, stem + ".json")
    meta = json.load(open(path, encoding="utf-8"))
    if "a0" in meta:
        return None
    mesh = trimesh.load(local_path(series, meta["file"]), process=False)
    mesh.apply_translation(-mesh.bounds.mean(axis=0))
    u, v, _ = basis(meta["normal"], meta.get("up"))
    pts = np.vstack([mesh.vertices, mesh.triangles_center])
    a, b = pts @ u, pts @ v
    a0, b0 = float(a.min()), float(b.min())
    nx = int((a.max() - a0) / meta["res_mm"]) + 1
    ny = int((b.max() - b0) / meta["res_mm"]) + 1
    assert [ny, nx] == meta["shape"], (meta["file"], [ny, nx], meta["shape"])
    meta["a0"], meta["b0"] = a0, b0
    json.dump(meta, open(path, "w", encoding="utf-8"), ensure_ascii=False)
    return a0, b0


if __name__ == "__main__":
    if sys.argv[1] == "--origin":
        print(sys.argv[3], fill_origin(sys.argv[2], sys.argv[3]))
        raise SystemExit(0)
    main(sys.argv[1], sys.argv[2])
