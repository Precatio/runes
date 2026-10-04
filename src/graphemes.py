"""Runformer (grafem): förbehandling och formbeskrivning av runutsnitt.

Utsnittet görs om till en normaliserad svartvit form innan den beskrivs, så att jämförelsen
mäter runans form snarare än belysning, färg, storlek eller bildens proportioner:
  1. gråskala och lokal kontrastutjämning (CLAHE),
  2. binarisering med Otsus metod; den mindre klassen antas vara runan,
  3. små fläckar tas bort, formen beskärs till sin utbredning och läggs i en kvadrat
     med bevarade proportioner,
  4. beskrivning: HOG (riktningar av kanter), täthet i 4×4 zoner och formens proportioner.
"""
import base64

import cv2
import numpy as np
from skimage.feature import hog

FEATURE_VERSION = "grapheme-2"
SIZE = 64


def decode_image(data: bytes) -> np.ndarray:
    img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Kunde inte avkoda bilden.")
    return img


def normalize_form(img_bgr: np.ndarray) -> tuple[np.ndarray, float]:
    """Returnerar (binär form SIZE×SIZE som float 0/1, proportion bredd/höjd för formen)."""
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    scale = 256 / max(gray.shape)
    if scale < 1:
        gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    gray = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    _, binary = cv2.threshold(gray, 0, 1, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    if binary.mean() > 0.5:  # the rune is the minority class
        binary = 1 - binary
    binary = cv2.morphologyEx(binary.astype(np.uint8), cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))

    n, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
    min_area = max(4, int(0.01 * binary.size))
    keep = np.zeros_like(binary)
    for k in range(1, n):
        if stats[k, cv2.CC_STAT_AREA] >= min_area:
            keep[labels == k] = 1
    if keep.sum() == 0:
        keep = binary
    ys, xs = np.nonzero(keep)
    if len(ys) == 0:
        raise ValueError("Ingen runform hittades i utsnittet.")
    form = keep[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = form.shape
    aspect = w / h
    side = int(max(h, w) * 1.15) + 2
    canvas = np.zeros((side, side), np.uint8)
    y0, x0 = (side - h) // 2, (side - w) // 2
    canvas[y0:y0 + h, x0:x0 + w] = form
    out = cv2.resize(canvas.astype(np.float32), (SIZE, SIZE), interpolation=cv2.INTER_AREA)
    return (out > 0.35).astype(np.float32), aspect


def describe(form: np.ndarray, aspect: float) -> np.ndarray:
    h = hog(form, orientations=9, pixels_per_cell=(8, 8), cells_per_block=(2, 2),
            block_norm="L2-Hys", feature_vector=True)
    zones = form.reshape(4, SIZE // 4, 4, SIZE // 4).mean(axis=(1, 3)).ravel()
    return np.concatenate([h, zones * 0.5, [np.log(max(aspect, 1e-3)) * 0.5]])


def form_png(form: np.ndarray) -> str:
    ok, buf = cv2.imencode(".png", ((1 - form) * 255).astype(np.uint8))
    return "data:image/png;base64," + base64.b64encode(buf.tobytes()).decode("ascii")


def extract(image_bytes: bytes) -> dict:
    form, aspect = normalize_form(decode_image(image_bytes))
    return {"feature_vector": describe(form, aspect).tolist(), "form_png": form_png(form),
            "aspect": float(aspect), "feature_version": FEATURE_VERSION}


def cosine(a, b) -> float:
    a, b = np.asarray(a, float), np.asarray(b, float)
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    return float(a @ b / (na * nb)) if na and nb else 0.0
