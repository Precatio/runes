"""Syntetiska runbilder för test av runformsjämförelsen."""
import cv2
import numpy as np

# Strokes in a unit box (x, y), y downwards
RUNES = {
    "ᛁ": [((0.5, 0.0), (0.5, 1.0))],
    "ᛏ": [((0.5, 0.0), (0.5, 1.0)), ((0.5, 0.0), (0.15, 0.35)), ((0.5, 0.0), (0.85, 0.35))],
    "ᚴ": [((0.4, 0.0), (0.4, 1.0)), ((0.4, 0.35), (0.85, 0.05))],
    "ᚱ": [((0.3, 0.0), (0.3, 1.0)), ((0.3, 0.0), (0.75, 0.25)), ((0.75, 0.25), (0.3, 0.5)), ((0.3, 0.5), (0.8, 1.0))],
    "ᛋ": [((0.3, 0.0), (0.3, 0.45)), ((0.3, 0.45), (0.7, 0.55)), ((0.7, 0.55), (0.7, 1.0))],
}


def render(rune: str, seed: int = 0, size: int = 160, dark_strokes: bool = True) -> bytes:
    rng = np.random.default_rng(seed)
    scale = rng.uniform(0.55, 0.8) * size
    angle = rng.uniform(-6, 6)
    width = int(rng.integers(4, 10))
    bg = rng.uniform(110, 200)
    contrast = rng.uniform(50, 90) * (-1 if dark_strokes else 1)
    img = np.full((size, size), bg, np.float32)
    ox, oy = (size - scale * 0.6) / 2 + rng.uniform(-8, 8), (size - scale) / 2 + rng.uniform(-8, 8)
    layer = np.zeros_like(img)
    for (x0, y0), (x1, y1) in RUNES[rune]:
        p0 = (int(ox + x0 * scale * 0.6), int(oy + y0 * scale))
        p1 = (int(ox + x1 * scale * 0.6), int(oy + y1 * scale))
        cv2.line(layer, p0, p1, 1.0, width, cv2.LINE_AA)
    M = cv2.getRotationMatrix2D((size / 2, size / 2), angle, 1.0)
    layer = cv2.warpAffine(layer, M, (size, size))
    img = img + contrast * layer
    # uneven lighting and texture noise
    gx = np.linspace(-1, 1, size)[None, :]
    img += rng.uniform(-30, 30) * gx + rng.normal(0, 8, img.shape)
    img = np.clip(img, 0, 255).astype(np.uint8)
    ok, buf = cv2.imencode(".png", cv2.cvtColor(img, cv2.COLOR_GRAY2BGR))
    return buf.tobytes()
