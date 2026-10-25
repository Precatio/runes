"""Syntetiska runslingor för runmodellens förträning (minnet rune-recognizer): Rundatas verkliga texter ritade som
V-formade spår i en remsa av samma skala som de uträtade slingorna (src/runmodell.py: 64 rader, ungefär 1,1 mm per
pixel, djup i mm). Modellen lär sig runornas former här innan den får de riktiga stenarna.

Runorna är den yngre runradens långkvistrunor, med kortkvistformer och spegelvända varianter, ritade som streck i en
ruta där 0 är slingans nederkant och 1 överkanten. Variationen: runhöjd, bredd, lutning, avstånd, spårets djup och
bredd, ytans struktur, sprickor, vittrade fläckar och skadade runor; slingans kantlinjer ritas oftast med."""
from __future__ import annotations

import numpy as np

from src import runmodell as rm

# Strokes per rune: lists of polylines in a box x ∈ [−0.5, 0.5] (stave at 0), y ∈ [0, 1]
LONG = {
    "f": [[(0, 0), (0, 1)], [(0, 0.55), (0.35, 0.85)], [(0, 0.8), (0.3, 1.0)]],
    "u": [[(0, 0), (0, 1)], [(0, 1), (0.35, 0.7), (0.35, 0)]],
    "þ": [[(0, 0), (0, 1)], [(0, 0.72), (0.3, 0.55), (0, 0.38)]],
    "o": [[(0, 0), (0, 1)], [(0, 0.85), (-0.3, 0.6)], [(0, 0.6), (-0.3, 0.35)]],
    "r": [[(0, 0), (0, 1)], [(0, 1), (0.3, 0.8), (0, 0.58), (0.32, 0)]],
    "k": [[(0, 0), (0, 1)], [(0, 0.55), (0.32, 0.88)]],
    "h": [[(0, 0), (0, 1)], [(-0.3, 0.75), (0.3, 0.35)], [(0.3, 0.75), (-0.3, 0.35)]],
    "n": [[(0, 0), (0, 1)], [(-0.22, 0.68), (0.22, 0.42)]],
    "i": [[(0, 0), (0, 1)]],
    "a": [[(0, 0), (0, 1)], [(-0.22, 0.42), (0.22, 0.68)]],
    "s": [[(0, 1), (0, 0.62), (0.3, 0.38), (0.3, 0)]],
    "t": [[(0, 0), (0, 1)], [(0, 1), (-0.3, 0.72)], [(0, 1), (0.3, 0.72)]],
    "b": [[(0, 0), (0, 1)], [(0, 1), (0.3, 0.78), (0, 0.55), (0.3, 0.27), (0, 0.02)]],
    "m": [[(0, 0), (0, 1)], [(0, 0.62), (-0.3, 0.92)], [(0, 0.62), (0.3, 0.92)]],
    "l": [[(0, 0), (0, 1)], [(0, 1), (0.32, 0.7)]],
    "R": [[(0, 0), (0, 1)], [(0, 0.38), (-0.3, 0.08)], [(0, 0.38), (0.3, 0.08)]],
}
# Short-twig forms (stuttruna): the branches shorter and placed mid-stave; s, t, b, m, R and a differ most
SHORT = {
    "a": [[(0, 0), (0, 1)], [(0, 0.55), (0.22, 0.72)]],
    "n": [[(0, 0), (0, 1)], [(0, 0.6), (0.2, 0.45)]],
    "s": [[(0, 0.35), (0, 0.85)]],
    "t": [[(0, 0), (0, 1)], [(0, 1), (0.25, 0.8)]],
    "b": [[(0, 0), (0, 1)], [(0, 1), (0.2, 0.85), (0, 0.7)], [(0, 0.45), (0.2, 0.3), (0, 0.15)]],
    "m": [[(0, 0), (0, 1)], [(-0.2, 0.75), (0.2, 0.75)]],
    "R": [[(0, 0), (0, 1)], [(-0.2, 0.25), (0.2, 0.25)]],
    "h": [[(0, 0), (0, 1)], [(-0.2, 0.55), (0.2, 0.65)]],
    "o": [[(0, 0), (0, 1)], [(0, 0.7), (0.22, 0.85)]],
}
DIVIDERS = [[[(0, 0.5), (0, 0.5)]], [[(0, 0.35), (0, 0.35)], [(0, 0.65), (0, 0.65)]],
            [[(-0.12, 0.38), (0.12, 0.62)], [(-0.12, 0.62), (0.12, 0.38)]]]


def _segments(polys, x0, base, h, w, slant, rng, jitter):
    for poly in polys:
        pts = np.array(poly, float)
        pts = pts + rng.normal(0, jitter, pts.shape)
        X = x0 + pts[:, 0] * w + (pts[:, 1] - 0.5) * slant * h
        Y = base + pts[:, 1] * h
        for i in range(max(1, len(pts) - 1)):
            j = min(i + 1, len(pts) - 1)
            yield X[i], Y[i], X[j], Y[j]


def _groove(img, x1, y1, x2, y2, half, depth):
    """Adds a V-shaped groove along a segment (depth falls linearly to zero at `half` pixels from the centre line)."""
    H, W = img.shape
    xa, xb = int(max(0, min(x1, x2) - half - 1)), int(min(W, max(x1, x2) + half + 2))
    ya, yb = int(max(0, min(y1, y2) - half - 1)), int(min(H, max(y1, y2) + half + 2))
    if xa >= xb or ya >= yb:
        return
    yy, xx = np.mgrid[ya:yb, xa:xb]
    dx, dy = x2 - x1, y2 - y1
    L2 = dx * dx + dy * dy
    t = np.clip(((xx - x1) * dx + (yy - y1) * dy) / L2, 0, 1) if L2 > 1e-9 else np.zeros_like(xx, float)
    d = np.hypot(xx - (x1 + t * dx), yy - (y1 + t * dy))
    v = depth * np.clip(1 - d / half, 0, None)
    np.maximum(img[ya:yb, xa:xb], v, out=img[ya:yb, xa:xb])


def strip(text: str, rng: np.random.Generator, height: int = 64) -> np.ndarray:
    """One synthetic strip for `text` (the model's characters, rm.ALPHABET), depth in mm, upright runes."""
    from scipy.ndimage import gaussian_filter
    # Matched to the real strips (Gs 11, Vg 53, M 1): the staves run from band line to band line, the grooves are wide
    # and deep for the strip's scale, and the runes stand close
    rune_h = rng.uniform(0.74, 0.92) * height
    base = (height - rune_h) / 2 + rng.normal(0, 1.5)
    pitch = rune_h * rng.uniform(0.32, 0.58)            # distance between runes
    width = rune_h * rng.uniform(0.4, 0.7)               # how far branches reach
    slant = rng.normal(0, 0.06)
    half = rng.uniform(3.5, 7.5)                          # half the groove width in pixels
    d0 = rng.uniform(1.8, 3.4)                            # groove depth in mm
    short = rng.random() < 0.25                           # a short-twig carver
    W = int(pitch * (len(text) + 2) + 20)
    img = np.zeros((height, W), np.float32)
    x = pitch * rng.uniform(0.6, 1.4)
    for ch in text:
        if ch == rm.DIVIDER:
            polys = DIVIDERS[rng.integers(len(DIVIDERS))]
            step = pitch * rng.uniform(0.45, 0.8)
            for x1, y1, x2, y2 in _segments(polys, x, base, rune_h, width, 0, rng, 0.02):
                _groove(img, x1, y1, x2 + 0.01, y2, half * rng.uniform(0.9, 1.4), d0 * rng.uniform(0.5, 0.9))
            x += step
            continue
        polys = (SHORT.get(ch) if short else None) or LONG[ch]
        if rng.random() < 0.15 and ch not in "fuþrkbl":  # some carvers mirrored symmetric-ish runes
            polys = [[(-px, py) for px, py in p] for p in polys]
        damaged = rng.random() < 0.06
        for x1, y1, x2, y2 in _segments(polys, x, base, rune_h, width, slant, rng, 0.03):
            dd = d0 * rng.uniform(0.75, 1.15) * (rng.uniform(0.1, 0.5) if damaged else 1)
            _groove(img, x1, y1, x2, y2, half * rng.uniform(0.85, 1.2), dd)
        x += pitch * rng.uniform(0.85, 1.2)
    img = img[:, :int(x + pitch * rng.uniform(0.3, 1.0))]
    W = img.shape[1]
    if rng.random() < 0.85:  # the band's edge lines
        for y in (base - rng.uniform(0, 2.5), base + rune_h + rng.uniform(0, 2.5)):
            wob = rng.normal(0, 1.5)
            _groove(img, 0, y, W, y + wob, half * rng.uniform(0.9, 1.3), d0 * rng.uniform(0.7, 1.1))
    for _ in range(rng.poisson(1.2)):  # cracks
        x1, y1 = rng.uniform(0, W), rng.uniform(0, height)
        ang, L = rng.uniform(0, np.pi), rng.uniform(15, 120)
        _groove(img, x1, y1, x1 + L * np.cos(ang), y1 + L * np.sin(ang), rng.uniform(0.8, 2.0), rng.uniform(0.3, 1.2))
    img = gaussian_filter(img, rng.uniform(0.4, 1.2))
    surface = gaussian_filter(rng.normal(0, 1, img.shape), rng.uniform(0.8, 3)) * rng.uniform(0.15, 0.6)
    for _ in range(rng.poisson(6)):  # pits and blobs in the stone surface
        cx, cy, r = rng.uniform(0, img.shape[1]), rng.uniform(0, height), rng.uniform(1.5, 6)
        yy, xx = np.ogrid[0:height, 0:img.shape[1]]
        surface += rng.uniform(0.5, 2.0) * np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * r * r))
    for _ in range(rng.poisson(1.5)):  # weathered patches: shallower grooves
        cx, cy, r = rng.uniform(0, W), rng.uniform(0, height), rng.uniform(8, 40)
        yy, xx = np.mgrid[0:height, 0:W]
        img *= 1 - 0.6 * np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * r * r))
    return np.clip(img + surface + rng.normal(0, 0.04, img.shape), 0, 3.0).astype(np.float32)


def corpus_texts(exclude_signa: set[str] = frozenset()) -> list[str]:
    """Rundata's texts as the model's characters (rm.text_target), without the given stones (the held-out test stones)."""
    from api.rundata import store
    out = []
    for r in store().inscriptions:
        if r.get("signum") in exclude_signa:
            continue
        t = rm.text_target(r.get("transliteration"))
        if len(t) >= 12:
            out.append(t)
    return out


def sample_text(texts: list[str], rng: np.random.Generator) -> str:
    """A random window of 12–48 characters from a random inscription."""
    t = texts[rng.integers(len(texts))]
    L = int(rng.integers(12, 49))
    if len(t) <= L:
        return t
    a = int(rng.integers(0, len(t) - L))
    return t[a:a + L].strip(rm.DIVIDER) or t[:L]
