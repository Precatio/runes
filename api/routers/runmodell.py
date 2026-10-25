"""Runmodellen: djupbilderna och runslingornas mittlinjer som modellen tränas på (scripts/depth_dataset.py, minnet
rune-recognizer). Sidan Runmodell ritar mittlinjerna; här läses djupbilderna och linjerna sparas.

Bara filer som redan finns i djupmappen kan läsas eller få en linje: serie och fil kontrolleras mot den listan, så
att adressen aldrig kan peka utanför mappen."""
import io
import json
import os

import numpy as np
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

router = APIRouter()

DEPTH_DIR = os.environ.get("RUNMODELL_DEPTH_DIR", "/Volumes/2TB/cache/runmodell/djup")
BAND_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "runmodell", "band")
SCALE = 2  # the drawing page shows the depth image at half resolution (1.2 mm per pixel)


def _stones() -> dict[tuple[str, str], dict]:
    out = {}
    if not os.path.isdir(DEPTH_DIR):
        return out
    for series in sorted(os.listdir(DEPTH_DIR)):
        folder = os.path.join(DEPTH_DIR, series)
        if not os.path.isdir(folder):
            continue
        for f in sorted(os.listdir(folder)):
            if f.endswith(".json"):
                out[(series, f[:-5])] = json.load(open(os.path.join(folder, f), encoding="utf-8"))
    return out


def _known(series: str, stem: str) -> dict:
    meta = _stones().get((series, stem))
    if meta is None:
        raise HTTPException(status_code=404, detail="Ingen djupbild med det namnet.")
    return meta


def _band_path(series: str, stem: str) -> str:
    return os.path.join(BAND_DIR, series, stem + ".json")


@router.get("/stones")
def stones():
    """Alla skanningar med djupbild: signum, text, runtyp och om mittlinjer finns (och vem som ritat dem)."""
    out = []
    for (series, stem), m in _stones().items():
        band = json.load(open(_band_path(series, stem), encoding="utf-8")) if os.path.exists(_band_path(series, stem)) else None
        out.append({"series": series, "stem": stem, "file": m["file"], "signum": m.get("signum"), "object": m.get("object"),
                    "rune_types": m.get("rune_types"), "transliteration": m.get("transliteration"),
                    "width": m["shape"][1] // SCALE, "height": m["shape"][0] // SCALE, "res_mm": m["res_mm"] * SCALE,
                    "bands": len((band or {}).get("bands", [])), "status": (band or {}).get("status")})
    return {"stones": out}


@router.get("/depth/{series}/{stem}.png")
def depth_png(series: str, stem: str):
    """Djupbilden som gråskala (mörkt = djupt, 0–3 mm), halv upplösning, vitt utanför skanningen. Raden 0 är längst
    ned i stenens plan; bilden vänds så att den visas rättvänd (samma riktning som mittlinjernas koordinater)."""
    from PIL import Image
    _known(series, stem)
    z = np.load(os.path.join(DEPTH_DIR, series, stem + ".npz"))
    d = np.nan_to_num(z["depth"].astype(np.float32), nan=0.0)
    d[~z["region"]] = 0
    g = (255 * (1 - np.clip(d / 3.0, 0, 1))).astype(np.uint8)
    img = Image.fromarray(np.flipud(g)).resize((g.shape[1] // SCALE, g.shape[0] // SCALE), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return Response(content=buf.getvalue(), media_type="image/png", headers={"Cache-Control": "max-age=3600"})


class Band(BaseModel):
    points: list[list[float]] = Field(..., min_length=2, max_length=400)  # [x, y] in displayed pixels, reading order
    height: float = Field(..., gt=4, lt=400)  # band height in displayed pixels


class Bands(BaseModel):
    bands: list[Band] = Field(default_factory=list, max_length=20)  # in reading order
    status: str = Field("utkast", pattern="^(utkast|granskad)$")  # granskad = checked by a person
    rotation: int = Field(0, ge=0, le=270, multiple_of=90)  # how the stone is turned on the page to stand upright
    by: str = Field("", max_length=80)
    note: str = Field("", max_length=1000)


@router.get("/band/{series}/{stem}")
def get_band(series: str, stem: str):
    _known(series, stem)
    p = _band_path(series, stem)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {"bands": [], "status": None, "rotation": 0}


@router.put("/band/{series}/{stem}")
def put_band(series: str, stem: str, body: Bands):
    """Sparar runslingornas mittlinjer i läsordning (koordinater i den visade bilden, 1,2 mm per pixel)."""
    meta = _known(series, stem)
    w, h = meta["shape"][1] // SCALE, meta["shape"][0] // SCALE
    for b in body.bands:
        if any(not (0 <= x <= w and 0 <= y <= h) for x, y in b.points):
            raise HTTPException(status_code=400, detail="En punkt ligger utanför bilden.")
    p = _band_path(series, stem)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    data = {**body.model_dump(), "scale": SCALE, "res_mm": meta["res_mm"] * SCALE, "signum": meta.get("signum"),
            "file": meta["file"]}
    tmp = p + ".tmp"
    json.dump(data, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    os.replace(tmp, p)
    return {"ok": True, "bands": len(body.bands), "status": body.status}


def _mask_display(series: str, stem: str) -> np.ndarray:
    """The groove mask at the drawing page's resolution and orientation (row 0 at the top, as the picture is shown)."""
    z = np.load(os.path.join(DEPTH_DIR, series, stem + ".npz"))
    m = np.flipud(z["mask"].astype(np.float32))
    h, w = (m.shape[0] // SCALE) * SCALE, (m.shape[1] // SCALE) * SCALE
    return m[:h, :w].reshape(h // SCALE, SCALE, w // SCALE, SCALE).mean(axis=(1, 3))


def _resample(points: np.ndarray, step: float) -> np.ndarray:
    seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))]
    t = np.arange(0, seg[-1] + 1e-9, step)
    return np.c_[np.interp(t, seg, points[:, 0]), np.interp(t, seg, points[:, 1])]


def snap_band(mask: np.ndarray, points: list[list[float]], height: float, step: float = 12.0) -> list[list[float]]:
    """Moves a roughly drawn centre line across the band to where the grooves are densest: for points every `step`
    pixels, the offset along the normal (within ± half the band height) whose band-wide window holds the most groove;
    the offsets are smoothed (running median), so that the line follows the band, not single runes."""
    from scipy.ndimage import map_coordinates, median_filter
    P = _resample(np.asarray(points, float), step)
    if len(P) < 2:
        return points
    tang = np.gradient(P, axis=0)
    tang /= np.maximum(np.linalg.norm(tang, axis=1, keepdims=True), 1e-9)
    norm = np.c_[-tang[:, 1], tang[:, 0]]
    offs = np.arange(-height / 2, height / 2 + 1, 2.0)
    across = np.arange(-height / 2, height / 2 + 1, 2.0)
    along = np.arange(-step, step + 1, 3.0)
    best = np.zeros(len(P))
    for i, (p, t, n) in enumerate(zip(P, tang, norm)):
        scores = []
        for o in offs:
            c = p + o * n
            pts = c[None, None, :] + along[:, None, None] * t + across[None, :, None] * n
            vals = map_coordinates(mask, [pts[..., 1].ravel(), pts[..., 0].ravel()], order=1, mode="constant")
            scores.append(vals.mean())
        best[i] = offs[int(np.argmax(scores))]
    best = median_filter(best, size=min(len(best) // 2 * 2 + 1, 9), mode="nearest")
    # then a running mean, so that the line bends with the band but not with single runes
    k = min(7, len(best))
    best = np.convolve(np.pad(best, k // 2, mode="edge"), np.ones(k) / k, mode="valid")[:len(best)]
    out = P + best[:, None] * norm
    keep = np.r_[0, np.arange(2, len(out) - 1, 3), len(out) - 1]  # every third point, ends kept
    return [[round(float(x), 1), round(float(y), 1)] for x, y in out[np.unique(keep)]]


@router.post("/snap/{series}/{stem}")
def snap(series: str, stem: str, body: Bands):
    """Fäster de ritade mittlinjerna mot runorna (snap_band); sparar inget."""
    _known(series, stem)
    mask = _mask_display(series, stem)
    return {"bands": [{"points": snap_band(mask, b.points, b.height), "height": b.height} for b in body.bands
                      if len(b.points) >= 2]}
