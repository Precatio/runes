"""Runslingorna i den automatiska spåranalysen (2026-10-26): vad som är runor och vad som är ornamentik avgörs av var
runslingorna går, inte av strecklängder. Viktor visade 2026-10-24 att den gamla streckklassningen var fel åt båda
hållen; med slingorna som facit hamnade 26 % av dess "runor" utanför textslingorna (utdata/forskningsplan/resultat.md,
studie 1b).

Slingorna kommer från, i den ordningen:
  1. ritade och granskade slingor (sidan Runmodell, data/runmodell/band/) när skanningen är en av de öppna filerna;
     slingorna förs över från djupbildens rutnät till analysens genom stenens yta i 3D, så att de gäller även när
     stenen är vriden något annorlunda än när djupbilden gjordes (högst 20° mellan normalerna);
  2. slingmodellen (data/runmodell/slingmodell.pt, ett U-nät tränat på 95 granskade stenar; mitten av provstenarnas
     överlapp med de ritade slingorna 59 %), som föreslår slingorna på analysens egen djupbild.
Utan PyTorch eller modell finns inga slingor, och analysen faller tillbaka på den gamla streckklassningen.

Varje tvärsnitt klassas: runa (inne i slingan och mer än 25° från slingans riktning), slingkant (längs slingan, inne i
den eller strax utanför), gräns (strax utanför och inte längs: runspetsar, korsningar), utanför (resten)."""
from __future__ import annotations

import glob
import json
import os
from functools import lru_cache

import numpy as np
from scipy import ndimage

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MODEL_PATH = os.path.join(ROOT, "data", "runmodell", "slingmodell.pt")
BAND_DIR = os.path.join(ROOT, "data", "runmodell", "band")
DEPTH_DIR = os.environ.get("RUNMODELL_DEPTH_DIR", "/Volumes/2TB/cache/runmodell/djup")
MODEL_MM = 2.4      # the band model's pixel (the drawing page's image halved)
ALONG_DEG = 25.0    # a groove within this angle of the band runs along it
EDGE_MM = 8.0       # the edge zone just outside a band
SMOOTH_MM = 12.0    # window for the band's direction
MAX_TILT_DEG = 20.0  # drawn bands are carried over when the analysis normal is within this of the depth image's


def _unet():
    import torch.nn as nn
    import torch.nn.functional as F
    import torch

    class UNet(nn.Module):
        def __init__(self, c=24):
            super().__init__()
            def blk(i, o):
                return nn.Sequential(nn.Conv2d(i, o, 3, padding=1), nn.BatchNorm2d(o), nn.ReLU(),
                                     nn.Conv2d(o, o, 3, padding=1), nn.BatchNorm2d(o), nn.ReLU())
            self.d1, self.d2, self.d3, self.d4 = blk(2, c), blk(c, 2 * c), blk(2 * c, 4 * c), blk(4 * c, 8 * c)
            self.u3, self.u2, self.u1 = blk(12 * c, 4 * c), blk(6 * c, 2 * c), blk(3 * c, c)
            self.out = nn.Conv2d(c, 1, 1)

        def forward(self, x):
            a = self.d1(x); b = self.d2(F.max_pool2d(a, 2)); c = self.d3(F.max_pool2d(b, 2)); d = self.d4(F.max_pool2d(c, 2))
            up = lambda t, ref: F.interpolate(t, size=ref.shape[-2:], mode="bilinear", align_corners=False)
            c = self.u3(torch.cat([up(d, c), c], 1)); b = self.u2(torch.cat([up(c, b), b], 1)); a = self.u1(torch.cat([up(b, a), a], 1))
            return self.out(a)
    return UNet


@lru_cache(maxsize=1)
def _model():
    """The band model on the CPU (small; the analysis engine may run without a GPU), or None without PyTorch/model."""
    try:
        import torch
    except ImportError:
        return None
    if not os.path.exists(MODEL_PATH):
        return None
    m = _unet()()
    m.load_state_dict(torch.load(MODEL_PATH, map_location="cpu")["state"])
    m.eval()
    return m


def predicted(depth: np.ndarray, region: np.ndarray, res: float) -> np.ndarray | None:
    """The band model's probability per grid cell (depth in mm below the surface, positive = deeper)."""
    if os.environ.get("RUNE_BANDS_MODEL", "1") in ("0", "false"):
        return None  # the tests: no model, the stroke classification decides unless a test provides bands
    m = _model()
    if m is None:
        return None
    import torch
    import torch.nn.functional as F
    k = max(1, int(round(MODEL_MM / res)))
    H, W = (depth.shape[0] // k) * k, (depth.shape[1] // k) * k
    d = np.nan_to_num(depth[:H, :W], nan=0.0).reshape(H // k, k, W // k, k).mean(axis=(1, 3))
    r = region[:H, :W].reshape(H // k, k, W // k, k).max(axis=(1, 3)).astype(np.float32)
    x = torch.from_numpy(np.stack([np.clip(d, 0, 3) / 3.0 * r, r]).astype(np.float32))[None]
    ph, pw = (-x.shape[2]) % 8, (-x.shape[3]) % 8
    with torch.no_grad():
        p = torch.sigmoid(m(F.pad(x, (0, pw, 0, ph))))[0, 0, :x.shape[2], :x.shape[3]].numpy() * r
    full = np.zeros(depth.shape, np.float32)
    full[:H, :W] = np.repeat(np.repeat(p, k, axis=0), k, axis=1)
    return full


def _drawn_on_depth_grid(b: dict, shape, labels: bool = False) -> np.ndarray:
    """The checked bands as a mask on the depth image's own grid (row 0 at the bottom, as the analysis grids). With
    labels, each drawn band gets its own number (1, 2, …; where bands overlap, the one drawn later), so that bands drawn
    side by side stay apart even where they touch (stavlöst läge, src/staveless.py)."""
    from PIL import Image, ImageDraw
    scale = b.get("scale", 2)
    img = Image.new("L", (shape[1], shape[0]), 0)
    d = ImageDraw.Draw(img)
    for i, band in enumerate(b["bands"][:255], start=1):
        # drawing-page pixels (half resolution, row 0 at the top) → grid cells (row 0 at the bottom)
        pts = [(x * scale, (shape[0] - 1) - y * scale) for x, y in band["points"]]
        w = max(1, int(round(band["height"] * scale)))
        fill = i if labels else 255
        d.line(pts, fill=fill, width=w, joint="curve")
        for p in (pts[0], pts[-1]):
            d.ellipse([p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2], fill=fill)
    a = np.asarray(img)
    return a.astype(np.int32) if labels else a > 127


def drawn(sha256: str | None, hf) -> np.ndarray | None:
    """Viktor's checked bands for this exact file, as a mask on the analysis grid (see drawn_labels)."""
    lab = drawn_labels(sha256, hf)
    return None if lab is None else lab > 0


def drawn_labels(sha256: str | None, hf) -> np.ndarray | None:
    """Viktor's checked bands for this exact file (same SHA-256), carried over to the analysis grid: every analysis
    cell is taken to its point on the stone's surface (hf.to_world with the cell's height) and looked up in the depth
    image's grid (the same centred mesh, scripts/depth_dataset.py). None when there are no checked bands, or the
    analysis looks at the stone more than MAX_TILT_DEG away from the depth image's normal."""
    if not sha256 or not os.path.isdir(DEPTH_DIR):
        return None
    for mp in glob.glob(os.path.join(DEPTH_DIR, "*", "*.json")):
        meta = json.load(open(mp, encoding="utf-8"))
        if meta.get("sha256") != sha256:
            continue
        series, stem = mp.split(os.sep)[-2], os.path.basename(mp)[:-5]
        bp = os.path.join(BAND_DIR, series, stem + ".json")
        if not os.path.exists(bp) or "a0" not in meta:
            return None
        b = json.load(open(bp, encoding="utf-8"))
        if b.get("status") != "granskad" or not b.get("bands"):
            return None
        from src.auto_grooves import basis
        u0, v0, n0 = basis(meta["normal"], meta.get("up"))
        if float(np.degrees(np.arccos(np.clip(abs(n0 @ hf.n), -1, 1)))) > MAX_TILT_DEG:
            return None
        shape0, res0 = meta["shape"], float(meta["res_mm"])
        mask0 = _drawn_on_depth_grid(b, shape0, labels=True)
        ny, nx = hf.H.shape
        a = (hf.a0 + np.arange(nx) * hf.res)[None, :]
        bb = (hf.b0 + np.arange(ny) * hf.res)[:, None]
        h = np.where(np.isfinite(hf.H), hf.H, np.nanmedian(hf.H))
        # the surface point a·u + b·v + h·n, projected on the depth image's axes
        jx = np.rint((a * (hf.u @ u0) + bb * (hf.v @ u0) + h * (hf.n @ u0) - meta["a0"]) / res0).astype(np.int64)
        jy = np.rint((a * (hf.u @ v0) + bb * (hf.v @ v0) + h * (hf.n @ v0) - meta["b0"]) / res0).astype(np.int64)
        ok = (jx >= 0) & (jx < shape0[1]) & (jy >= 0) & (jy < shape0[0])
        out = np.zeros((ny, nx), np.int32)
        out[ok] = mask0[jy[ok], jx[ok]]
        return np.where(hf.region, out, 0)
    return None


def band_field(mask: np.ndarray, res: float) -> dict:
    """The band's direction at every cell (a structure tensor of the smoothed mask: the band runs across its
    strongest change), the distance outside the band in mm, and the mask itself."""
    s = max(1.0, SMOOTH_MM / res)
    m = ndimage.gaussian_filter(mask.astype(np.float32), s / 2)
    gy, gx = np.gradient(m)
    jyy, jxx, jxy = (ndimage.gaussian_filter(v, s) for v in (gy * gy, gx * gx, gx * gy))
    angle = 0.5 * np.arctan2(2 * jxy, jxx - jyy)  # direction of strongest change (across the band)
    ty, tx = np.cos(angle), -np.sin(angle)          # along the band: perpendicular to it (row, col)
    outside = ndimage.distance_transform_edt(~mask) * res
    return {"mask": mask, "ty": ty.astype(np.float32), "tx": tx.astype(np.float32), "outside_mm": outside}


def bands_for(depth: np.ndarray, region: np.ndarray, res: float, hf, sha256: str | None) -> dict | None:
    """The bands for an analysis (hf: its Heightfield): drawn when available, else the model's; with their field and
    where they came from."""
    pieces = drawn_labels(sha256, hf)
    mask = None if pieces is None else pieces > 0
    source = "ritade"
    if mask is None:
        p = predicted(depth, region, res)
        if p is None:
            return None
        mask = (p >= 0.5) & region
        source = "modellen"
    if not mask.any():
        return {"source": source, "empty": True}
    field = band_field(mask, res)
    field.update({"source": source, "empty": False, "coverage": float(mask[region].mean()) if region.any() else 0.0})
    if pieces is not None:
        field["pieces"] = pieces  # each drawn band on its own (src/staveless.py); the classification uses the mask
    return field


def classify(field: dict, iy: int, ix: int, t_y: float, t_x: float) -> str:
    """One cross-section: runa, slingkant, gräns or utanför (see the module text)."""
    out = float(field["outside_mm"][iy, ix])
    inside = bool(field["mask"][iy, ix])
    cos = abs(t_y * field["ty"][iy, ix] + t_x * field["tx"][iy, ix]) / max(np.hypot(t_y, t_x), 1e-9)
    along = cos >= np.cos(np.radians(ALONG_DEG))
    if inside:
        return "slingkant" if along else "runa"
    if out <= EDGE_MM:
        return "slingkant" if along else "gräns"
    return "utanför"
