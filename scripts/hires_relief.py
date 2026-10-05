"""Relief i hög upplösning direkt ur en 3D-skanning, för tryck (analysmotorns bilder begränsas till 1 600 px).
Samma metod som i appen: den mörkaste av fyra strykljusriktningar i varje punkt.

    .venv/bin/python -m scripts.hires_relief "So 131_1_4 thin_closed holes.stl" utdata/So131/relief_hires.tif
"""
import argparse

import numpy as np
import trimesh
from PIL import Image

from api.routers.threed import _estimated_normal
from src.stone_report import Surface


def relief(path: str, max_px: int = 4800, max_cells: int = 14_000_000) -> tuple[Image.Image, float]:
    mesh = trimesh.load(path, force="mesh")
    surf = Surface(mesh, _estimated_normal(mesh), None, max_cells=max_cells, max_px=max_px)
    views = [surf.shaded(az, 20) for az in (315, 45, 135, 225)]
    with np.errstate(invalid="ignore"):
        r = np.nanmin(np.stack(views), axis=0)
    r = (r - np.nanpercentile(r, 1)) / max(np.nanpercentile(r, 99) - np.nanpercentile(r, 1), 1e-6)
    img = Image.fromarray((np.flipud(np.clip(np.nan_to_num(r, nan=1.0), 0, 1)) * 255).astype(np.uint8))
    return img, surf.res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scan")
    ap.add_argument("out", help="t.ex. relief.tif")
    ap.add_argument("--max-px", type=int, default=4800)
    ap.add_argument("--dpi", type=int, default=300)
    a = ap.parse_args(argv)
    img, res = relief(a.scan, a.max_px)
    img.save(a.out, dpi=(a.dpi, a.dpi), compression="tiff_lzw" if a.out.lower().endswith((".tif", ".tiff")) else None)
    print(f"{a.out}: {img.size[0]} × {img.size[1]} px, {res:.2f} mm per pixel")


if __name__ == "__main__":
    main()
