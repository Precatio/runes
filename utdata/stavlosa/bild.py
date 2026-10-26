"""Granskningsbild för stavlöst läge: djupbilden, slingorna (blått), runsnitten (rött = runa utan runtillhörighet,
grönt = med runa) och runornas rutor. En fil i taget (minnet).

  .venv/bin/python -m utdata.stavlosa.bild halsingland HS_15_0_40_thin03 [--stavlost]
"""
from __future__ import annotations

import argparse
import json
import os
import sys


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
DEPTH = os.environ.get("RUNMODELL_DEPTH_DIR", "/Volumes/2TB/cache/runmodell/djup")
OUT = os.path.join(ROOT, "utdata", "stavlosa", "bilder")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("series")
    ap.add_argument("stem")
    ap.add_argument("--stavlost", action="store_true")
    a = ap.parse_args(argv)
    import trimesh
    from PIL import Image, ImageDraw
    from scripts.download_open_scans import local_path
    from src import protocol
    from src.auto_grooves import analyze_grooves

    meta = json.load(open(os.path.join(DEPTH, a.series, a.stem + ".json"), encoding="utf-8"))
    mesh = trimesh.load(local_path(a.series, meta["file"]), force="mesh")
    mesh.apply_translation(-(mesh.bounds[0] + mesh.bounds[1]) / 2.0)  # centred as the app does on upload (api/routers/threed.py)
    pp = protocol.PARAMETERS
    kw = {"staveless": True} if a.stavlost else {}
    r = analyze_grooves(mesh, meta["normal"], up=meta.get("up"), spacing_mm=pp["spacing_mm"], sensitivity=pp["sensitivity"],
                        max_halfwidth_mm=pp["max_halfwidth_mm"], resolution_mm=pp["resolution_mm"],
                        harmonize_mm=pp["harmonize_mm"] or None, measure="runes", sha256=meta["sha256"],
                        **kw)
    import base64
    import io
    img = Image.open(io.BytesIO(base64.b64decode(r["image_base64"].split(",", 1)[1]))).convert("RGB")
    d = ImageDraw.Draw(img)
    for ru in r["runes"]:  # the runes' boxes: fractions of the image, y downwards
        x0, y0, x1, y1 = ru["box"]
        d.rectangle([x0 * img.width, y0 * img.height, x1 * img.width, y1 * img.height], outline=(0, 150, 0), width=2)
    acc = [s for s in r["slices"] if s["accepted"]]
    d.rectangle([0, 0, img.width, 24], fill=(255, 255, 255))
    d.text((8, 6), f"{meta.get('signum')} {'stavlöst' if a.stavlost else 'vanligt'}: runor {len(r['runes'])}, "
                   f"godkända snitt {len(acc)}, med runa {sum('rune_id' in s for s in acc)}, slingor {r['bands']}", fill=(0, 0, 0))
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, f"{a.stem}__{'stavlost' if a.stavlost else 'vanligt'}.png")
    img.save(p)
    print(p)


if __name__ == "__main__":
    main()
