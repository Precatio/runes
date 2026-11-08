"""Runor och ornamentik (3D-sidan, POST /api/3d/band_image, METHODS.md 2d3): dagens djupbild avskuren med en gemensam
gräns för hela stenen och färgad efter textslingorna – rostrött det som ligger inne i slingorna, grått det som ligger
utanför (ornamentik, sprickor, gropar), slingornas kant svart.

Slingorna är desamma som huggspårsanalysen använder för att avgöra vad som är runor (src/rune_bands.py): Viktors
ritade och granskade slingor när skanningen är en av de öppna filerna, annars slingmodellens förslag. Bilden visar
alltså vad analysen räknar som text, så att läsaren kan se om slingorna ligger rätt.

Den gemensamma gränsen valdes efter provet av Skala av vittringen (2026-11-07, analysplaner/2026-11-07-skala-av-
provet.md): en gräns för hela stenen samlade sig bättre i textslingorna än en lokal vittringsnivå vid samma visade yta.
Utgångsläget är den 70:e percentilen av djupet över ytan innanför kantzonen, så att ungefär 30 % av ytan visas; ett
reglage flyttar gränsen från 1 mm grundare till 3 mm djupare."""
from __future__ import annotations

import io

import numpy as np
from scipy import ndimage

LEVEL_Q = 70
OFFSET_RANGE = (-1.0, 3.0)
EDGE_LINE_MM = 1.0
RUST = (0xb7, 0x41, 0x0e)      # carving inside the text bands
SLATE = (0x9a, 0xa6, 0xb8)     # carving outside them: ornament, cracks, pits
PLAIN = (0x47, 0x55, 0x69)     # carving when there are no bands
EDGE = (0x14, 0x14, 0x14)      # the edge of the bands
OUTSIDE = (0xf5, 0xf5, 0xf5)   # outside the scan


def bands_on_surface(surf, sha256: str | None) -> tuple[np.ndarray | None, str | None]:
    """The text bands on the surface's grid and where they come from: "ritade" (Viktor's checked bands for this exact
    file, carried over through the stone's surface) or "modellen" (the band model on this depth image); (None, None)
    when there are none (no model, or nothing found)."""
    from src import rune_bands
    lab = rune_bands.drawn_labels(sha256, surf.hf)
    if lab is not None:
        mask = (lab[surf.sl] > 0) & surf.region
        return (mask, "ritade") if mask.any() else (None, None)
    p = rune_bands.predicted(np.clip(-surf.residual, 0, None), surf.region, surf.res)
    if p is None:
        return None, None
    mask = (p >= 0.5) & surf.region
    return (mask, "modellen") if mask.any() else (None, None)


class BandImage:
    """The depth below the reference surface (as today's depth image) on the inner surface, its common level, and the
    bands; layer() cuts it at the level plus the slider's offset."""

    def __init__(self, depth: np.ndarray, region: np.ndarray, inner: np.ndarray, res: float,
                 bands: np.ndarray | None, source: str | None):
        self.depth = np.where(np.isfinite(depth), depth, -np.inf)
        self.region, self.res = region, float(res)
        self.use = region & inner & np.isfinite(depth)
        self.level = float(np.percentile(depth[self.use], LEVEL_Q)) if self.use.any() else 0.0
        self.bands = None if bands is None else (bands & region)
        self.source = source if bands is not None else None
        if self.bands is not None:
            k = max(1, int(round(EDGE_LINE_MM / self.res)))
            self.edge = self.bands & ~ndimage.binary_erosion(self.bands, iterations=k)
        else:
            self.edge = None

    def layer(self, offset_mm: float = 0.0) -> dict:
        lo, hi = OFFSET_RANGE
        offset = float(min(max(offset_mm, lo), hi))
        shown = self.use & (self.depth > self.level + offset)
        n_use = int(self.use.sum())
        img = np.full(self.depth.shape + (3,), 255, np.uint8)
        img[~self.region] = OUTSIDE
        out = {"offset_mm": round(offset, 2), "level_mm": round(self.level, 2), "source": self.source,
               "shown_share": float(shown.sum() / n_use) if n_use else 0.0, "band_share": None, "in_bands": None}
        if self.bands is None:
            img[shown] = PLAIN
        else:
            img[shown & ~self.bands] = SLATE
            img[shown & self.bands] = RUST
            img[self.edge] = EDGE
            out["band_share"] = float((self.bands & self.use).sum() / n_use) if n_use else 0.0
            out["in_bands"] = float((shown & self.bands).sum() / shown.sum()) if shown.any() else None
        out["rgb"] = img
        return out


def png(rgb: np.ndarray) -> bytes:
    """The picture as PNG, north up (row 0 of the grid is at the bottom, as the depth images)."""
    from PIL import Image
    buf = io.BytesIO()
    Image.fromarray(np.flipud(rgb)).save(buf, format="PNG", optimize=True)
    return buf.getvalue()
