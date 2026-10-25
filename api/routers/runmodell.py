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
    by: str = Field("", max_length=80)
    note: str = Field("", max_length=1000)


@router.get("/band/{series}/{stem}")
def get_band(series: str, stem: str):
    _known(series, stem)
    p = _band_path(series, stem)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {"bands": [], "status": None}


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
