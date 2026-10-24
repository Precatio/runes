"""Djupbilder för runigenkänningen (rune-recognizer): varje öppen skanning körs genom den automatiska spåranalysen med
alla spår och arrayerna kvar, och djupet under stenytan sparas som en bild i 0,6 mm per pixel, tillsammans med
spårmasken, strecklinjerna (slingkanter m.m.), analysens runor och stenens text ur Rundata.

En fil per anrop (minnet släpps inte mellan stora skanningar), samma normal som protokollmätningen:
    .venv/bin/python -m scripts.depth_dataset SERIE FILNAMN
Utdata: /Volumes/2TB/cache/runmodell/djup/<serie>/<fil>.npz (depth float16 i mm, mask, res) och .json (metadata).
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
    from src.auto_grooves import analyze_grooves
    files = json.load(open(os.path.join(ROOT, "data", "scan_files.json"), encoding="utf-8"))["datasets"][series]["files"]
    f = next(x for x in files if x["name"] == name)
    stem = os.path.splitext(name)[0].replace(" ", "_")
    out = os.path.join(OUT, series, stem)
    if os.path.exists(out + ".npz"):
        print(f"{name}: finns redan")
        return
    p = json.load(open(result_path(series, f), encoding="utf-8"))  # the protocol measurement: normal and up
    t0 = time.time()
    mesh = trimesh.load(local_path(series, name), process=False)
    mesh.apply_translation(-mesh.bounds.mean(axis=0))  # centred as the app does (geo.center)
    g = analyze_grooves(mesh, p["normal"], up=(p.get("parameters") or {}).get("up"), resolution_mm=0.6,
                        runes_only=False, keep_arrays=True)
    a = g["arrays"]
    os.makedirs(os.path.dirname(out), exist_ok=True)
    np.savez_compressed(out + ".npz", depth=np.asarray(a["depth"], dtype=np.float16), mask=a["mask"].astype(bool),
                        wide_area=np.asarray(a["wide_area"]).astype(bool), region=a["region"].astype(bool),
                        inner=a["inner"].astype(bool), res=a["res"])
    rec = store().get(f["signum"]) if f.get("signum") else None
    meta = {"series": series, "file": name, "sha256": f.get("sha256"), "signum": f.get("signum"),
            "signa": f.get("signa"), "res_mm": a["res"], "shape": list(np.shape(a["depth"])), "normal": p["normal"],
            "up": (p.get("parameters") or {}).get("up"), "stroke_lines": g.get("stroke_lines"), "runes": g.get("runes"),
            "transliteration": (rec or {}).get("transliteration"), "rune_types": (rec or {}).get("rune_types"),
            "object": (rec or {}).get("object"), "material": (rec or {}).get("material"),
            "seconds": round(time.time() - t0)}
    json.dump(meta, open(out + ".json", "w", encoding="utf-8"), ensure_ascii=False)
    print(f"{name}: {meta['shape'][1]}×{meta['shape'][0]} px, {len(meta['stroke_lines'] or [])} streck "
          f"({meta['seconds']} s)", flush=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
