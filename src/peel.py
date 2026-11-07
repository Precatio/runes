"""Skala av vittringen: en bild av den ristade ytan där bara det som ligger djupare än vittringen runt omkring syns, med
de djupa spåren markerade och möjliga att klicka bort (POST /api/3d/peel, dialogen *Skala av vittringen* på 3D-sidan).
METHODS.md 2h.

Tre steg skiljer bilden från "djup under stenytan" i reliefbilderna:
1. **Ytan följer stenens välvning.** Referensytan är densamma som huggspårsmätningens (stängning med ett fönster om
   20 mm): en stängning bevarar en kupig yta exakt och fyller bara fåror smalare än fönstret. (En rullande paraboloid
   prövades och underkändes 2026-11-07: den doppar ner i spåren och underskattar djupet, analysplaner/
   2026-11-07-referensyta-paraboloid.md.)
2. **Djupet mäts vinkelrätt mot ytan,** inte längs stenens huvudnormal: djupet längs projektionen gånger cos(lutningen).
   På en sluttning om 30° är skillnaden 13 %, vid 45° 29 %.
3. **Gränsen följer vittringen där den står.** I rutor om 60 mm tas den 70:e percentilen av djupet som rutans
   vittringsnivå; nivåerna jämnas ut mellan rutorna. Reglaget lägger till eller drar av millimeter från den nivån.

Det som blir kvar delas i sammanhängande fläckar. Varje fläcks djupa kärna (cellerna minst hälften så djupa som
fläckens djupaste) tunnas ut till ett skelett: skelettets längd är fläckens längd (också när en runa med bistavar har
vuxit ihop till en klump, men inte när en grop har fått små utskott av vittring), och kärnans yta delad med längden är
dess medelbredd. En
fläck med minst 12 mm skelett (huggspårsanalysens kortaste runa) och en medelbredd högst en tredjedel av skelettets längd räknas som ett **spår** (kan vara
runa, ornament eller spricka; färgas), resten som **grop** (grå). Ingenting här avgör
vad som är runa: det gör den som läser, genom att klicka bort det som inte är det. Bortklickade fläckar sparas som
punkter på 3D-modellen och följer med när reglaget flyttas.
"""
from __future__ import annotations

import math

import numpy as np
from scipy import ndimage

BLOCK_MM = 60.0         # the squares for the local weathering level
LEVEL_Q = 70            # the percentile of the depth that counts as weathering
EDGE_MM = 10.0          # the reference surface is unreliable this close to the scan's edge
MAX_SLOPE_DEG = 60.0    # steeper parts face away from the view (the stone's sides)
MIN_AREA_MM2 = 3.0      # smaller specks are noise
GROOVE_LENGTH_MM = 12.0  # a groove's skeleton (the groove analysis' shortest rune, rune_min_mm) is at least this long ...
GROOVE_ELONGATION = 3.0  # ... and at least this many times its mean width
OFFSET_RANGE = (-1.0, 3.0)


def surface_reference(H: np.ndarray, region: np.ndarray, res: float) -> np.ndarray:
    """The stone surface without the carving, the same as the groove measurement uses (auto_grooves.reference_surface,
    the closing with a 20 mm window): a closing keeps a domed surface exactly and fills only furrows narrower than the
    window. Outside the scan the nearest surface value is used, so that the edge does not pull the surface down."""
    from types import SimpleNamespace

    from src.auto_grooves import reference_surface
    filled = H.copy()
    if (~region).any():
        idx = ndimage.distance_transform_edt(~region, return_distances=False, return_indices=True)
        filled = H[tuple(idx)]
    return reference_surface(SimpleNamespace(H=filled, res=res), scale_mm=20.0)


class Peel:
    """The expensive part, computed once per surface: reference, perpendicular depth and the local weathering level.
    `layer(offset_mm)` is then cheap enough to follow a slider."""

    def __init__(self, H: np.ndarray, region: np.ndarray, res: float):
        self.res = float(res)
        self.ref = surface_reference(H, region, res)
        gy, gx = np.gradient(self.ref, res)
        self.slope = np.degrees(np.arctan(np.hypot(gx, gy)))
        edge = ndimage.distance_transform_edt(np.pad(region, 1))[1:-1, 1:-1] * res > EDGE_MM
        self.use = region & edge & (self.slope < MAX_SLOPE_DEG)
        self.depth = np.where(region, np.clip(self.ref - H, 0, None) * np.cos(np.radians(self.slope)), 0.0)
        self.level = self._local_level()
        self.H = H

    def _local_level(self) -> np.ndarray:
        h, w = self.depth.shape
        blk = max(4, int(round(BLOCK_MM / self.res)))
        gh, gw = math.ceil(h / blk), math.ceil(w / blk)
        grid = np.full((gh, gw), np.nan)
        for i in range(gh):
            for j in range(gw):
                sl = (slice(i * blk, (i + 1) * blk), slice(j * blk, (j + 1) * blk))
                v = self.depth[sl][self.use[sl]]
                if v.size >= 50:
                    grid[i, j] = np.percentile(v, LEVEL_Q)
        if np.isnan(grid).all():
            return np.zeros_like(self.depth)
        grid = np.where(np.isnan(grid), np.nanmedian(grid), grid)
        grid = ndimage.gaussian_filter(grid, 1.0)
        level = ndimage.zoom(grid, (h / gh, w / gw), order=1)
        out = np.zeros_like(self.depth)
        out[:level.shape[0], :level.shape[1]] = level[:h, :w]
        return out

    def level_range(self) -> tuple[float, float, float]:
        v = self.level[self.use]
        return (float(v.min()), float(np.median(v)), float(v.max())) if v.size else (0.0, 0.0, 0.0)

    def layer(self, offset_mm: float = 0.0) -> dict:
        """What lies deeper than the local weathering level + offset: the remaining depth, the labelled specks and
        their measures (in mm, on the surface's grid)."""
        from skimage.measure import regionprops
        from skimage.morphology import skeletonize
        lo, hi = OFFSET_RANGE
        offset = float(min(max(offset_mm, lo), hi))
        left = np.where(self.use, self.depth - self.level - offset, 0.0)
        mask = left > 0
        lab, n = ndimage.label(mask, structure=np.ones((3, 3), bool))
        comps = []
        if n:
            # the deep core of each speck: at least half as deep (below the level) as its deepest cell
            deepest = np.asarray(ndimage.maximum(left, lab, index=np.arange(n + 1)))
            core = mask & (left >= 0.5 * deepest[lab])
            skel_len = np.bincount(lab[skeletonize(core)], minlength=n + 1) * self.res
            core_area = np.bincount(lab[core], minlength=n + 1) * self.res ** 2
            min_px = MIN_AREA_MM2 / self.res ** 2
            keep = np.zeros(n + 1, bool)
            for rp in regionprops(lab, intensity_image=self.depth):
                if rp.area < min_px:
                    continue
                keep[rp.label] = True
                length = max(float(skel_len[rp.label]), self.res)
                width = float(core_area[rp.label]) / length
                kind = "spar" if length >= GROOVE_LENGTH_MM and length / width >= GROOVE_ELONGATION else "grop"
                r, c = (int(round(x)) for x in rp.centroid)
                if not lab[r, c] == rp.label:  # a curved speck: take its deepest cell instead of the centroid
                    cells = rp.coords
                    r, c = (int(x) for x in cells[np.argmax(self.depth[cells[:, 0], cells[:, 1]])])
                comps.append({"label": int(rp.label), "kind": kind, "area_mm2": float(rp.area * self.res ** 2),
                              "length_mm": float(length), "width_mm": float(width),
                              "depth_mm": float(rp.intensity_max), "cell": [r, c]})
            lab = np.where(keep[lab], lab, 0)
        # Renumber 1 … len(comps) in the order of the list
        remap = np.zeros(n + 1, np.int32)
        for i, comp in enumerate(comps, 1):
            remap[comp["label"]] = i
            comp["id"] = i
            del comp["label"]
        lab = remap[lab]
        shown = np.clip(left, 0, None)
        top = float(np.percentile(shown[mask], 99.5)) if mask.any() else 1.0
        return {"offset_mm": offset, "labels": lab, "components": comps, "left_mm": shown, "top_mm": top}


def labels_png(lab: np.ndarray) -> bytes:
    """The label map as an RGB PNG (id = r + 256 g + 65536 b; 0 = nothing), with row 0 at the bottom like
    groove_export.gray_image, so that it lies exactly under the picture."""
    import io

    from PIL import Image
    lab = np.flipud(lab.astype(np.int64))
    rgb = np.stack([lab & 255, (lab >> 8) & 255, (lab >> 16) & 255], axis=-1).astype(np.uint8)
    buf = io.BytesIO()
    Image.fromarray(rgb, "RGB").save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def background(layer: dict, region: np.ndarray) -> np.ndarray:
    """The peeled surface as a grey scale 0–1 for groove_export.gray_image: 1 = at or above the level, darker the
    deeper below it; outside the scan NaN (white)."""
    img = 1 - np.clip(layer["left_mm"] / max(layer["top_mm"], 1e-6), 0, 1)
    return np.where(region, img, np.nan)
