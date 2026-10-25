"""Runmodellen (minnet rune-recognizer): runslingorna som uträtade remsor och Rundatas text som modellens tecken.

Mittlinjerna ritas på sidan Runmodell (api/routers/runmodell.py) i den visade bilden: halv upplösning, rad 0 överst.
Här räknas de om till djupbildens rutnät (0,6 mm, rad 0 nederst) och slingan rätas ut: för varje steg längs linjen
läses djupet tvärs över bandet, så att runorna står i en rak rad som en textrad.

Tecknen: den yngre runradens 16 runor, med stungna och sena varianter förda till sin grundruna (e → i, g → k,
d → t, y → u, æ → a, ø/ǫ → o, p → b, c → k), och skiljetecken som en egen klass. Runor inom hakparentes (lästa ur
äldre källor eller osäkra, ofta inte synliga i dag) och förlorade runor (-, ...) tas inte med."""
from __future__ import annotations

import json
import os
import re

import numpy as np

DEPTH_DIR = "/Volumes/2TB/cache/runmodell/djup"
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BAND_DIR = os.path.join(ROOT, "data", "runmodell", "band")
RUNES = "fuþorkhniastbmlR"
DIVIDER = "÷"
ALPHABET = RUNES + DIVIDER  # class 0 is CTC's blank, so a character's class is its index + 1
FOLD = {"e": "i", "g": "k", "d": "t", "y": "u", "æ": "a", "ø": "o", "ǫ": "o", "ą": "o", "p": "b", "c": "k",
        "ʀ": "R", "z": "R", "w": "u", "v": "u", "x": "k", "q": "k", "ð": "þ"}
DIVIDERS = set("·×:'+⁝¤|")


def text_target(transliteration: str | None) -> str:
    """Rundata's transliteration as the model's characters (see the module text)."""
    t = transliteration or ""
    # Rundata's §P, §Q, … are alternative readings of the same runes (another order of the text's parts): only the
    # first is kept. §A, §B, … are the stone's sides and all belong to the text.
    t = re.sub(r"§[Q-Z]\b.*?(?=§[A-O]\b|$)", " ", t, flags=re.S)
    t = re.sub(r"§[A-Z]\b", " ", t)
    t = re.sub(r"\[[^\]]*\]", " ", t)  # read from older sources or uncertain
    t = re.sub(r"\.\.\.|…", " ", t)
    out = []
    for ch in t:
        c = FOLD.get(ch, ch)
        if c in RUNES:
            out.append(c)
        elif ch in DIVIDERS:
            if out and out[-1] != DIVIDER:
                out.append(DIVIDER)
    s = "".join(out).strip(DIVIDER)
    return s


def encode(s: str) -> list[int]:
    return [ALPHABET.index(c) + 1 for c in s]


def load_bands(series: str, stem: str) -> dict | None:
    p = os.path.join(BAND_DIR, series, stem + ".json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None


def _resample(points: np.ndarray, step: float) -> np.ndarray:
    seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))]
    t = np.arange(0, seg[-1] + 1e-9, step)
    return np.c_[np.interp(t, seg, points[:, 0]), np.interp(t, seg, points[:, 1])]


def straighten(depth: np.ndarray, points_display: list, height_display: float, scale: int, smooth: int = 15,
               clip_mm: float = 3.0) -> tuple[np.ndarray, np.ndarray]:
    """One band as a straight strip of depth (mm, clipped to 0–clip_mm), one column per grid cell along the line and
    one row per grid cell across it; and the grid coordinates (row, col) of the centre line for each column, so that a
    position in the strip can be taken back to the stone."""
    from scipy.ndimage import map_coordinates, uniform_filter1d
    H = depth.shape[0]
    P = np.asarray(points_display, float) * scale
    P = np.c_[P[:, 0], (H - 1) - P[:, 1]]  # display rows run downwards, the grid's rows upwards
    C = _resample(P, 1.0)
    if len(C) < 3:
        return np.zeros((0, 0)), np.zeros((0, 2))
    tang = np.gradient(uniform_filter1d(C, size=min(smooth, len(C)), axis=0, mode="nearest"), axis=0)
    tang /= np.maximum(np.linalg.norm(tang, axis=1, keepdims=True), 1e-9)
    norm = np.c_[-tang[:, 1], tang[:, 0]]
    half = height_display * scale / 2
    across = np.arange(-half, half + 1e-9, 1.0)
    pts = C[None, :, :] + across[:, None, None] * norm[None, :, :]  # rows across, columns along
    d = np.nan_to_num(depth.astype(np.float32), nan=0.0)
    strip = map_coordinates(d, [pts[..., 1].ravel(), pts[..., 0].ravel()], order=1, mode="constant").reshape(pts.shape[:2])
    # Upright: following a band in reading direction, the runes' tops lie to the left of the direction of travel (as
    # with any writing). The last row is the left side, so the strip is turned to put it on top (Viktor, Hs 21).
    return np.clip(strip[::-1, :], 0, clip_mm), np.c_[C[:, 1], C[:, 0]]


def stone_strip(series: str, stem: str, height_px: int = 64, gap_px: int = 24) -> dict | None:
    """All of a stone's bands, straightened, scaled to height_px rows and joined in reading order with a gap; with the
    target text. None when the stone has no drawn bands."""
    from PIL import Image
    b = load_bands(series, stem)
    if not b or not b.get("bands"):
        return None
    z = np.load(os.path.join(DEPTH_DIR, series, stem + ".npz"))
    meta = json.load(open(os.path.join(DEPTH_DIR, series, stem + ".json"), encoding="utf-8"))
    parts, centres = [], []
    for band in b["bands"]:
        s, c = straighten(z["depth"], band["points"], band["height"], b.get("scale", 2))
        if s.size == 0:
            continue
        w = max(1, round(s.shape[1] * height_px / s.shape[0]))
        img = np.asarray(Image.fromarray(s.astype(np.float32)).resize((w, height_px), Image.BILINEAR))
        parts.append(img)
        centres.append(c[np.linspace(0, len(c) - 1, w).astype(int)])
        parts.append(np.zeros((height_px, gap_px), np.float32))
        centres.append(np.full((gap_px, 2), np.nan))
    if not parts:
        return None
    return {"image": np.concatenate(parts[:-1], axis=1), "centre": np.concatenate(centres[:-1], axis=0),
            "target": text_target(meta.get("transliteration")), "signum": meta.get("signum"), "status": b.get("status"),
            "quality": b.get("quality", ""), "rune_types": meta.get("rune_types") or "",
            "series": series, "stem": stem}
