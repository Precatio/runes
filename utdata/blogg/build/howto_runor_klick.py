"""Klicken till skärmbilderna i "Så gör du"-artikeln om att markera runorna: en markering mitt på varje runa, i läsordning,
räknad ur Viktors granskade runslingor (data/runmodell/band/), som är ritade i läsordning.

En runas stav går tvärs över slingan, så alla snitt i samma runa ligger på nästan samma ställe längs slingan. Slingans
mittlinje förs därför över till granskningsbilden genom stenens yta (som src/rune_bands.drawn), varje runsnitt
projiceras på mittlinjen, och där det är en lucka längs slingan (GAP_MM) börjar nästa runa. Markeringen sätts på
mittlinjen mitt i runan. Det är en hjälp för skärmbilderna, inte en läsning av stenen: en runa utan mätta snitt får
ingen markering, och två runor tätt intill varandra kan bli en.
    .venv/bin/python utdata/blogg/build/howto_runor_klick.py SKANNING.stl utdata/blogg/howto_runor/analys.json
"""
import glob
import json
import os
import sys

import numpy as np
import trimesh

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import rune_bands  # noqa: E402
from src.auto_grooves import Heightfield  # noqa: E402

GAP_MM = float(os.environ.get("GAP_MM", 8.0))
STEP_MM = 1.0

scan, analys = sys.argv[1], sys.argv[2]
a = json.load(open(analys, encoding="utf-8"))
sha = a["provenance"]["mesh"]["sha256"]
meta_path = next(p for p in glob.glob(os.path.join(rune_bands.DEPTH_DIR, "*", "*.json"))
                 if json.load(open(p, encoding="utf-8")).get("sha256") == sha)
meta = json.load(open(meta_path, encoding="utf-8"))
series, stem = meta_path.split(os.sep)[-2], os.path.basename(meta_path)[:-5]
band = json.load(open(os.path.join(rune_bands.BAND_DIR, series, stem + ".json"), encoding="utf-8"))

mesh = trimesh.load(scan, process=False)
mesh.apply_translation(-mesh.bounds.mean(axis=0))
p = a["parameters"]
hf = Heightfield.from_mesh(mesh, p["normal"], resolution=p["resolution_mm"], up=p.get("up"))
hf0 = Heightfield.from_mesh(mesh, meta["normal"], resolution=meta["res_mm"], up=meta.get("up"))
assert hf0.H.shape == tuple(meta["shape"]) and abs(hf0.a0 - meta["a0"]) < 1e-6
ny, nx = hf.H.shape
scale = min(1.0, 1600 / max(nx, ny))  # as src/auto_grooves._overlay_png
assert abs(a["image_width"] - int(nx * scale)) <= 1 and abs(a["image_height"] - int(ny * scale)) <= 1
mm_px = hf.res / scale


def to_image(x, y):
    """A drawing-page point (half resolution, row 0 at the top) → the review image's pixels."""
    s = band.get("scale", 2)
    ix0, iy0 = x * s, (meta["shape"][0] - 1) - y * s
    h = float(hf0.sample(np.array([iy0]), np.array([ix0]))[0])
    w = hf0.to_world(iy0, ix0, h)
    ix, iy = (w @ hf.u - hf.a0) / hf.res, (w @ hf.v - hf.b0) / hf.res
    return np.array([ix * scale, (ny - 1 - iy) * scale])


# the centre lines in reading order, one point per STEP_MM, and their running length
line, along, start = [], [], 0.0
for b in band["bands"]:
    pts = np.array([to_image(x, y) for x, y in b["points"]])
    seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
    t = np.arange(0, seg[-1], STEP_MM / mm_px)
    line.append(np.c_[np.interp(t, seg, pts[:, 0]), np.interp(t, seg, pts[:, 1])])
    along.append(start + t)
    start += seg[-1] + 50 / mm_px  # a gap between bands, so that runes never join across them
line, along = np.vstack(line), np.concatenate(along)
half = band["bands"][0]["height"] * band.get("scale", 2) * meta["res_mm"] / 2 / mm_px

rune = np.array([[s["img_x"], s["img_y"]] for s in a["slices"] if s["accepted"] and s.get("feature") == "rune"])
d = np.linalg.norm(rune[:, None, :] - line[None, :, :], axis=2)
k = d.argmin(axis=1)
inside = d[np.arange(len(rune)), k] <= half * 1.2
s = np.sort(along[k[inside]])
cuts = np.where(np.diff(s) > GAP_MM / mm_px)[0]
clicks = []
for part in np.split(s, cuts + 1):
    if len(part) >= int(os.environ.get("MIN_SNITT", 3)):
        j = int(np.argmin(np.abs(along - np.median(part))))
        clicks.append([round(float(line[j, 0]), 1), round(float(line[j, 1]), 1)])
out = os.path.join(os.path.dirname(analys), "klick.json")
json.dump(clicks, open(out, "w"))
# a preview on the review image, for checking the marks before the browser clicks them
from PIL import Image, ImageDraw  # noqa: E402
img = Image.open(os.path.join(os.path.dirname(analys), "granskningsbild.png")).convert("RGB")
dr = ImageDraw.Draw(img)
dr.line([tuple(q) for q in line], fill=(30, 64, 175), width=1)
for i, (x, y) in enumerate(clicks, 1):
    dr.ellipse([x - 9, y - 9, x + 9, y + 9], outline=(183, 65, 14), width=3)
    dr.text((x + 10, y - 6), str(i), fill=(183, 65, 14))
img.save(os.path.join(os.path.dirname(analys), "klick_forhandsvisning.png"))
print(f"{len(rune)} runsnitt, {inside.sum()} i slingorna, {len(clicks)} runor markerade → {out}")
