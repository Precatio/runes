"""Referensbiblioteket för runformer: runor på de öppna 3D-skanningarna, märkta med vilken runa i Rundatas text de är
och vilken ristare Rundata anger för stenen.

Arbetssidan (/runbibliotek) visar skanningens djupbild (samma som sidan Runmodell, api/routers/runmodell.py) och
textens runor i läsordning. Forskaren klickar mitt på varje runa; klick nummer k hör till textens runa nummer k (runor
som inte syns hoppas över). Klicken sparas i data/runbibliotek/<serie>/<fil>.json, i den visade bildens koordinater
(1,2 mm per pixel, raden 0 överst), tillsammans med rutans storlek.

Varje runa klipps ut ur djupbilden i full upplösning (0,6 mm) och vrids upprätt efter läsriktningen där den står
(riktningen från runan före till runan efter, när de står nära; runornas toppar ligger till vänster om läsriktningen).
Djupet normaliseras inom rutan (5:e–97:e percentilen), så att grunda och djupa ristningar ger samma kontrast. Utsnittet
får samma formbeskrivning som runutsnitten i appen (src/graphemes.py), så att de kan jämföras."""
from __future__ import annotations

import io
import json
import math
import os
import re
from functools import lru_cache

import numpy as np
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from api.routers.runmodell import DEPTH_DIR, SCALE, _band_path, _known, _stones

router = APIRouter()

LIB_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "runbibliotek")
CROP_PX = 128          # the crop image's side
DEFAULT_BOX_MM = 50.0  # the box when the stone has no drawn bands
NEAR_BOXES = 3.0       # neighbours farther apart than this many boxes are in another row: not used for the direction


# ---- the text as runes -----------------------------------------------------------------------------------------------
def runes_of(translit: str | None) -> list[dict]:
    """Rundata's transliteration as runes in reading order: {i, letter, uncertain, lost, word}. Letters are runes;
    a letter in parentheses is uncertain; '-' is a lost rune (cannot be placed); '[…]' (known only from older records,
    not on the stone), '...', section marks (§A) and dividers are left out. word counts the words, for display."""
    t = re.sub(r"§[A-ZÅÄÖ]", " ", translit or "")
    t = re.sub(r"\[[^\]]*\]", " ", t)
    t = t.replace("...", " … ")
    out, word, uncertain = [], 0, False
    prev_space = True
    for ch in t:
        if ch == "(":
            uncertain = True
            continue
        if ch == ")":
            uncertain = False
            continue
        if ch.isalpha():
            if prev_space and out:
                word += 1
            out.append({"i": len(out), "letter": ch, "uncertain": uncertain, "lost": False, "word": word})
            prev_space = False
        elif ch == "-":
            if prev_space and out:
                word += 1
            out.append({"i": len(out), "letter": "-", "uncertain": False, "lost": True, "word": word})
            prev_space = False
        else:
            prev_space = True
    return out


def _lib_path(series: str, stem: str) -> str:
    return os.path.join(LIB_DIR, series, stem + ".json")


def _load(series: str, stem: str) -> dict | None:
    p = _lib_path(series, stem)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None


def _carvers(signum: str | None) -> list[dict]:
    from api.rundata import store
    rec = store().get(signum) if signum else None
    return [{"name": c["name"], "kind": c["kind"], "uncertain": c["uncertain"]} for c in (rec or {}).get("carvers", [])
            if c["kind"] in ("S", "A")]


def _default_box(series: str, stem: str) -> float:
    """The box side in displayed pixels: the drawn bands' height, else DEFAULT_BOX_MM."""
    p = _band_path(series, stem)
    if os.path.exists(p):
        b = json.load(open(p, encoding="utf-8"))
        hs = [x["height"] for x in b.get("bands", []) if x.get("height")]
        if hs:
            return float(np.median(hs))
    meta = _known(series, stem)
    return DEFAULT_BOX_MM / (meta["res_mm"] * SCALE)


# ---- the pages' calls --------------------------------------------------------------------------------------------
@router.get("/stones")
def stones():
    """Every scan with a depth image and a text: signum, carvers, how many runes the text has and how many are placed."""
    out = []
    for (series, stem), m in _stones().items():
        if not m.get("transliteration"):
            continue
        lib = _load(series, stem) or {}
        runes = runes_of(m.get("transliteration"))
        marks = lib.get("marks", [])
        out.append({"series": series, "stem": stem, "file": m["file"], "signum": m.get("signum"),
                    "rune_types": m.get("rune_types"), "carvers": _carvers(m.get("signum")),
                    "runes": sum(1 for r in runes if not r["lost"]), "placed": sum(1 for k in marks if not k.get("skip")),
                    "skipped": sum(1 for k in marks if k.get("skip")), "status": lib.get("status")})
    return {"stones": out}


@router.get("/stone/{series}/{stem}")
def stone(series: str, stem: str):
    """One scan for the work page: the runes of the text, the saved marks, the box size and the drawn bands."""
    m = _known(series, stem)
    lib = _load(series, stem) or {}
    band = json.load(open(_band_path(series, stem), encoding="utf-8")) if os.path.exists(_band_path(series, stem)) else {}
    return {"series": series, "stem": stem, "signum": m.get("signum"), "file": m["file"], "rune_types": m.get("rune_types"),
            "transliteration": m.get("transliteration"), "runes": runes_of(m.get("transliteration")),
            "carvers": _carvers(m.get("signum")), "width": m["shape"][1] // SCALE, "height": m["shape"][0] // SCALE,
            "res_mm": m["res_mm"] * SCALE, "marks": lib.get("marks", []), "box": lib.get("box") or _default_box(series, stem),
            "status": lib.get("status"), "rotation": lib.get("rotation", band.get("rotation", 0)),
            "bands": band.get("bands", [])}


class Mark(BaseModel):
    i: int = Field(..., ge=0, lt=5000)          # the rune's number in the text (runes_of)
    x: float | None = None                      # centre in displayed pixels; None when skipped
    y: float | None = None
    skip: bool = False                          # not visible, too damaged, or not a rune that can be cut out


class Marks(BaseModel):
    marks: list[Mark] = Field(default_factory=list, max_length=2000)
    box: float = Field(..., gt=5, lt=500)       # the box side in displayed pixels
    status: str = Field("utkast", pattern="^(utkast|granskad)$")
    rotation: int = Field(0, ge=0, le=270, multiple_of=90)  # how the stone is shown on the page
    by: str = Field("", max_length=80)
    note: str = Field("", max_length=1000)


@router.put("/stone/{series}/{stem}")
def put_stone(series: str, stem: str, body: Marks):
    """Saves the placed runes of one scan (data/runbibliotek/<serie>/<fil>.json)."""
    meta = _known(series, stem)
    w, h = meta["shape"][1] // SCALE, meta["shape"][0] // SCALE
    n = len(runes_of(meta.get("transliteration")))
    seen = set()
    for k in body.marks:
        if k.i >= n or k.i in seen:
            raise HTTPException(status_code=400, detail="En runa är märkt två gånger eller finns inte i texten.")
        seen.add(k.i)
        if not k.skip and (k.x is None or k.y is None or not (0 <= k.x <= w and 0 <= k.y <= h)):
            raise HTTPException(status_code=400, detail="En markering ligger utanför bilden.")
    p = _lib_path(series, stem)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    data = {**body.model_dump(), "scale": SCALE, "res_mm": meta["res_mm"] * SCALE, "signum": meta.get("signum"),
            "file": meta["file"], "sha256": meta.get("sha256"),
            "marks": sorted([k.model_dump() for k in body.marks], key=lambda k: k["i"])}
    tmp = p + ".tmp"
    json.dump(data, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    os.replace(tmp, p)
    _forms_of.cache_clear()
    return {"ok": True, "placed": sum(1 for k in body.marks if not k.skip), "status": body.status}


# ---- the crops -------------------------------------------------------------------------------------------------------
@lru_cache(maxsize=2)
def _grey(series: str, stem: str) -> tuple[np.ndarray, np.ndarray]:
    """The depth image at full resolution in display orientation (row 0 at the top), and its scan mask."""
    z = np.load(os.path.join(DEPTH_DIR, series, stem + ".npz"))
    d = np.nan_to_num(z["depth"].astype(np.float32), nan=0.0)
    return np.flipud(d), np.flipud(z["region"].astype(bool))


def _direction(marks: list[dict], k: int, box: float) -> float:
    """The reading direction at mark k (radians, display coordinates, y down): from the placed rune before to the
    placed rune after, when they stand within NEAR_BOXES boxes; 0 (left to right) when nothing is near."""
    placed = [m for m in marks if not m.get("skip") and m.get("x") is not None]
    idx = next((j for j, m in enumerate(placed) if m["i"] == k), None)
    if idx is None:
        return 0.0
    here = np.array([placed[idx]["x"], placed[idx]["y"]])
    near = lambda m: np.hypot(m["x"] - here[0], m["y"] - here[1]) <= NEAR_BOXES * box  # noqa: E731
    prev = placed[idx - 1] if idx > 0 and near(placed[idx - 1]) else None
    nxt = placed[idx + 1] if idx + 1 < len(placed) and near(placed[idx + 1]) else None
    a = np.array([prev["x"], prev["y"]]) if prev else here
    b = np.array([nxt["x"], nxt["y"]]) if nxt else here
    v = b - a
    return float(math.atan2(v[1], v[0])) if np.hypot(*v) > 1e-6 else 0.0


def crop_png(series: str, stem: str, k: int) -> bytes:
    """The rune with number k, cut out at full resolution, turned upright and normalised, as a PNG."""
    from PIL import Image
    lib = _load(series, stem)
    if not lib:
        raise HTTPException(status_code=404, detail="Inga markerade runor på skanningen.")
    mark = next((m for m in lib["marks"] if m["i"] == k and not m.get("skip")), None)
    if mark is None:
        raise HTTPException(status_code=404, detail="Runan är inte markerad.")
    depth, region = _grey(series, stem)
    s = SCALE
    cy, cx = mark["y"] * s, mark["x"] * s
    side = lib["box"] * s
    half = int(math.ceil(side * 0.75))  # room for the turn (√2 / 2 ≈ 0.71)
    y0, x0 = int(round(cy)) - half, int(round(cx)) - half
    win = np.zeros((2 * half, 2 * half), np.float32)
    ok = np.zeros_like(win, bool)
    ys, xs = slice(max(0, y0), min(depth.shape[0], y0 + 2 * half)), slice(max(0, x0), min(depth.shape[1], x0 + 2 * half))
    win[ys.start - y0:ys.stop - y0, xs.start - x0:xs.stop - x0] = depth[ys, xs]
    ok[ys.start - y0:ys.stop - y0, xs.start - x0:xs.stop - x0] = region[ys, xs]
    vals = win[ok]
    lo, hi = (np.percentile(vals, 5), np.percentile(vals, 97)) if vals.size > 20 else (0.0, 3.0)
    g = 255 * (1 - np.clip((win - lo) / max(hi - lo, 0.2), 0, 1))
    g[~ok] = 255
    img = Image.fromarray(g.astype(np.uint8))
    angle = math.degrees(_direction(lib["marks"], k, lib["box"]))
    img = img.rotate(angle, resample=Image.BICUBIC, fillcolor=255)  # turns the reading direction to point right
    c = half
    r = int(round(side / 2))
    img = img.crop((c - r, c - r, c + r, c + r)).resize((CROP_PX, CROP_PX), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


@router.get("/crop/{series}/{stem}/{k}.png")
def crop(series: str, stem: str, k: int):
    _known(series, stem)
    return Response(content=crop_png(series, stem, k), media_type="image/png", headers={"Cache-Control": "max-age=300"})


# ---- the library -----------------------------------------------------------------------------------------------------
@lru_cache(maxsize=1)
def _forms_of() -> tuple[dict, ...]:
    """Every placed rune with its form description (src/graphemes.py), its letter and the stone's carvers."""
    from src import graphemes
    out = []
    for (series, stem), meta in _stones().items():
        lib = _load(series, stem)
        if not lib:
            continue
        runes = runes_of(meta.get("transliteration"))
        carvers = _carvers(meta.get("signum"))
        for m in lib.get("marks", []):
            if m.get("skip") or m["i"] >= len(runes):
                continue
            try:
                f = graphemes.extract(crop_png(series, stem, m["i"]))
            except Exception:  # noqa: BLE001 - a box without a recognisable form is left out
                continue
            r = runes[m["i"]]
            out.append({"series": series, "stem": stem, "i": m["i"], "signum": meta.get("signum"), "letter": r["letter"],
                        "uncertain": r["uncertain"], "rune_types": meta.get("rune_types") or "", "carvers": carvers,
                        "status": lib.get("status"), "feature_vector": [round(v, 4) for v in f["feature_vector"]],
                        "feature_version": f["feature_version"],
                        "url": f"/api/runbibliotek/crop/{series}/{stem}/{m['i']}.png"})
    return tuple(out)


@router.get("/forms")
def forms(letter: str | None = None, with_vectors: bool = True):
    """The library's runes, optionally one letter (as in Rundata's transliteration), with their form vectors."""
    rows = [dict(r) for r in _forms_of() if letter is None or r["letter"] == letter]
    if not with_vectors:
        for r in rows:
            r.pop("feature_vector", None)
    return {"forms": rows, "n": len(rows)}


@router.get("/summary")
def summary():
    """How many runes the library has per carver and letter (carvers Rundata names as signed or attributed)."""
    by: dict[str, dict] = {}
    for r in _forms_of():
        names = [c["name"] for c in r["carvers"] if not c["uncertain"]] or ["(ingen säker ristare)"]
        for n in names:
            e = by.setdefault(n, {"carver": n, "signed": False, "stones": set(), "runes": 0, "letters": {}})
            e["signed"] |= any(c["name"] == n and c["kind"] == "S" for c in r["carvers"])
            e["stones"].add(r["signum"])
            e["runes"] += 1
            e["letters"][r["letter"]] = e["letters"].get(r["letter"], 0) + 1
    rows = [{**e, "stones": sorted(e["stones"])} for e in by.values()]
    return {"carvers": sorted(rows, key=lambda e: -e["runes"]), "runes": len(_forms_of())}
