"""Figur till artikeln: vad provet (analysplaner/2026-11-07-skala-av-provet.md) räknar, på en sten. Tre paneler – A
dagens djupbild, B avskalat och C bara spår – där det visade färgas rostrött inne i Viktors granskade slingor och
grått utanför; slingornas kant är svart. Samma beräkning som provet.py.
    PYTHONPATH=. .venv/bin/python utdata/skala_av/provet_figur.py sodermanland So_113_1_4_thin_closed_holes"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
DEPTH = "/Volumes/2TB/cache/runmodell/djup"
FONT = "/System/Library/Fonts/Supplemental/Arial.ttf"
RUST, GREY, EDGE = (183, 65, 14), (160, 170, 185), (20, 20, 20)


def main(series, stem):
    import trimesh

    from scripts.download_open_scans import local_path
    from src import peel as P
    from src import scan_sources
    from src.rune_bands import drawn_labels
    from src.stone_report import Surface

    meta = json.load(open(os.path.join(DEPTH, series, stem + ".json"), encoding="utf-8"))
    mesh = trimesh.load(local_path(series, meta["file"]), force="mesh")
    mesh.apply_translation(-(mesh.bounds[0] + mesh.bounds[1]) / 2.0)
    surf = Surface(mesh, meta["normal"], meta.get("up"), max_px=2400)
    del mesh
    hf = surf.hf
    rows, cols = np.where(hf.region)
    r0, r1, c0, c1 = rows.min(), rows.max() + 1, cols.min(), cols.max() + 1
    step = max(1, int(math.ceil(max(r1 - r0, c1 - c0) / 2400)))
    band = (drawn_labels(meta["sha256"], hf) > 0)[r0:r1:step, c0:c1:step]
    pe = P.Peel(surf.H, surf.region, surf.res)
    use = pe.use
    L = pe.layer(0.0)
    B = L["labels"] > 0
    spar = np.zeros(len(L["components"]) + 1, bool)
    for c in L["components"]:
        spar[c["id"]] = c["kind"] == "spar"
    C = spar[L["labels"]]
    depth_a = -surf.residual
    share = float((B & use).sum() / use.sum())
    A = depth_a > float(np.quantile(depth_a[use], 1 - share))
    base = (band & use).sum() / use.sum()
    edge = band & ~ndimage.binary_erosion(band, iterations=2)

    panels = []
    for name, shown in (("A  Dagens djupbild", A), ("B  Avskalat, allt som är kvar", B), ("C  Avskalat, bara spår", C)):
        s = shown & use
        prec = (s & band).sum() / s.sum()
        img = np.full(surf.H.shape + (3,), 255, np.uint8)
        img[~surf.region] = (245, 245, 245)
        img[s & ~band] = GREY
        img[s & band] = RUST
        img[edge] = EDGE
        im = Image.fromarray(np.flipud(img))  # north up, as the depth images
        panels.append((name, prec, prec / base, im))
    w = 900
    ims = [im.resize((w, round(im.height * w / im.width)), Image.LANCZOS) for _, _, _, im in panels]
    f, fs = ImageFont.truetype(FONT, 26), ImageFont.truetype(FONT, 20)
    head = 70
    H = sum(i.height + head for i in ims) + 60
    out = Image.new("RGB", (w + 40, H), "white")
    d = ImageDraw.Draw(out)
    y = 10
    for (name, prec, lift, _), im in zip(panels, ims):
        d.text((20, y), name, fill=(15, 23, 42), font=f)
        d.text((20, y + 34), f"{100 * prec:.0f} % av det visade ligger i slingorna (slumpen: {100 * base:.0f} %), "
               f"lyft {lift:.2f}".replace(".", ","), fill=(71, 85, 105), font=fs)
        y += head
        out.paste(im, (20, y))
        y += im.height
    ds = next(x for x in scan_sources.DATASETS if x["key"] == series)
    credit = (f"Skanning: {ds['scanner']}, {ds['institution']}, {ds['license']}, doi:{ds['doi']}. Slingor: Viktor Kvant. "
              "Bild: Vitki.")
    d.text((20, H - 40), credit, fill=(100, 116, 139), font=ImageFont.truetype(FONT, 16))
    path = os.path.join(HERE, f"provet_figur_{stem}.png")
    out.save(path, optimize=True)
    print(path, [(n, round(float(p), 3), round(float(l), 2)) for n, p, l, _ in panels], "slump", round(float(base), 3))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
