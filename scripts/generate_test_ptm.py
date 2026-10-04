"""Skapar en syntetisk PTM-fil (PTM_FORMAT_LRGB) av ett höjdfält med en V-skåra.

Används för att testa RTI-visaren. Kör från projektroten:
    .venv/bin/python -m scripts.generate_test_ptm test_groove.ptm
"""
import sys

import numpy as np


def heightmap(w=160, h=120):
    y, x = np.mgrid[0:h, 0:w].astype(float)
    z = np.zeros((h, w))
    # Diagonal V-groove (like a rune staff) and a horizontal branch
    for (x0, y0, x1, y1) in [(30, 100, 130, 20), (60, 60, 140, 60)]:
        d = np.abs((y1 - y0) * x - (x1 - x0) * y + x1 * y0 - y1 * x0) / np.hypot(y1 - y0, x1 - x0)
        t = ((x - x0) * (x1 - x0) + (y - y0) * (y1 - y0)) / ((x1 - x0) ** 2 + (y1 - y0) ** 2)
        mask = (t >= 0) & (t <= 1)
        z = np.minimum(z, np.where(mask, -np.clip(6 - d, 0, None), 0))
    return z


def fit_ptm(z):
    gy, gx = np.gradient(z)
    n = np.dstack([-gx, gy, np.ones_like(z)])  # image y grows downwards; lv points up
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    lights = []
    for el in np.radians([15, 30, 45, 60, 75]):
        for az in np.radians(np.arange(0, 360, 30)):
            lights.append((np.cos(el) * np.cos(az), np.cos(el) * np.sin(az), np.sin(el)))
    L = np.array(lights)
    A = np.column_stack([L[:, 0] ** 2, L[:, 1] ** 2, L[:, 0] * L[:, 1], L[:, 0], L[:, 1], np.ones(len(L))])
    I = np.clip(n.reshape(-1, 3) @ L.T, 0, None)  # (pixels, lights)
    coeffs, *_ = np.linalg.lstsq(A, I.T, rcond=None)
    return coeffs.T.reshape(z.shape[0], z.shape[1], 6)


def write_ptm(path, coeffs, rgb=(200, 180, 160)):
    h, w, _ = coeffs.shape
    lo, hi = coeffs.reshape(-1, 6).min(0), coeffs.reshape(-1, 6).max(0)
    scale = np.where(hi > lo, (hi - lo) / 255.0, 1.0)
    bias = np.round(-lo / scale).astype(int)
    raw = np.clip(np.round(coeffs / scale + bias), 0, 255).astype(np.uint8)
    header = "PTM_1.2\nPTM_FORMAT_LRGB\n{}\n{}\n{}\n{}\n".format(
        w, h, " ".join(f"{s:.8f}" for s in scale), " ".join(str(b) for b in bias))
    colors = np.tile(np.array(rgb, np.uint8), (h, w, 1))
    with open(path, "wb") as f:
        f.write(header.encode("ascii"))
        f.write(raw[::-1].tobytes())      # rows bottom-to-top
        f.write(colors[::-1].tobytes())
    return scale, bias, raw


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "test_groove.ptm"
    c = fit_ptm(heightmap())
    write_ptm(out, c)
    print(f"Skrev {out}")
