"""Underlag för slingmodellen (steg B, minnet rune-recognizer): varje granskad sten blir ett par av djupbild och mask
där runslingorna är ritade som band (Viktors mittlinjer och höjd), i den visade bildens skala (1,2 mm per pixel) och
nedskalat en gång till för träningen. Modellen ska sedan själv kunna föreslå slingorna på en ny skanning.
    .venv/bin/python -m scripts.runmodell_slingdata
Utdata: /Volumes/2TB/cache/runmodell/slingor/<serie>__<fil>.npz (depth float16 i mm, mask uint8, region uint8)."""
from __future__ import annotations

import glob
import json
import os
import sys

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
from src import runmodell as rm  # noqa: E402

OUT = "/Volumes/2TB/cache/runmodell/slingor"
DOWN = 2  # the drawing page's image (1.2 mm per pixel) halved again: 2.4 mm per pixel


def band_mask(shape: tuple[int, int], bands: list[dict]) -> np.ndarray:
    """The bands as a filled mask: every pixel within half the band height of a centre line (drawing page pixels)."""
    from PIL import Image, ImageDraw
    img = Image.new("L", (shape[1], shape[0]), 0)
    d = ImageDraw.Draw(img)
    for b in bands:
        pts = [tuple(p) for p in b["points"]]
        w = int(round(b["height"]))
        d.line(pts, fill=255, width=max(1, w), joint="curve")
        for p in (pts[0], pts[-1]):  # rounded ends, as the page draws them
            d.ellipse([p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2], fill=255)
    return (np.asarray(img) > 127).astype(np.uint8)


def main():
    os.makedirs(OUT, exist_ok=True)
    n = 0
    for p in sorted(glob.glob(os.path.join(rm.BAND_DIR, "*", "*.json"))):
        b = json.load(open(p, encoding="utf-8"))
        if b.get("status") != "granskad" or not b.get("bands"):
            continue
        series, stem = p.split(os.sep)[-2], os.path.basename(p)[:-5]
        z = np.load(os.path.join(rm.DEPTH_DIR, series, stem + ".npz"))
        scale = b.get("scale", 2)
        d = np.flipud(np.nan_to_num(z["depth"].astype(np.float32), nan=0.0))  # row 0 at the top, as the page shows it
        reg = np.flipud(z["region"])
        h, w = (d.shape[0] // scale) * scale, (d.shape[1] // scale) * scale
        d = d[:h, :w].reshape(h // scale, scale, w // scale, scale).mean(axis=(1, 3))
        reg = reg[:h, :w].reshape(h // scale, scale, w // scale, scale).max(axis=(1, 3))
        mask = band_mask(d.shape, b["bands"])
        k = DOWN
        H2, W2 = (d.shape[0] // k) * k, (d.shape[1] // k) * k
        d2 = d[:H2, :W2].reshape(H2 // k, k, W2 // k, k).mean(axis=(1, 3))
        m2 = mask[:H2, :W2].reshape(H2 // k, k, W2 // k, k).mean(axis=(1, 3)) > 0.5
        r2 = reg[:H2, :W2].reshape(H2 // k, k, W2 // k, k).max(axis=(1, 3))
        np.savez_compressed(os.path.join(OUT, f"{series}__{stem}.npz"), depth=np.clip(d2, 0, 3).astype(np.float16),
                            mask=m2.astype(np.uint8), region=r2.astype(np.uint8), quality=b.get("quality", ""),
                            rotation=b.get("rotation", 0))
        n += 1
    print(n, "stenar till slingmodellen i", OUT)


if __name__ == "__main__":
    main()
