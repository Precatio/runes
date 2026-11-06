"""Runa för runa: varje klick i granskningsbilden kopplat till en bestämd runa i Rundatas translitterering.

Tre delar, alla utan att runigenkänningens regler rörs:

1. **Tokenisering** (`tokenize`). Translittereringen delas i tecken som går att klicka på: runor, osäkra runor
   (inom parentes), förlorade runor ('-', och '?' för en runa som syns men inte går att läsa), skiljetecken, luckor
   av okänd längd ('...') och övrigt (latinska bokstäver inom klammer, symboler). Varje token har sitt index, sitt
   tecken, sin sort och sitt ordnummer (Rundatas ord: mellanslag och skiljetecken), och för runorna `pos`, platsen i
   textmodellens sammanfogade text (src/textmodel.text_groups) – samma positioner som spårläsarens `full`/`seq`
   (src/trace_reader.py) och led F (utdata/sparlasare/led_f.py). Rundatas alternativa läsningar (§…Q) utelämnas,
   som i textmodellen.

2. **Granskningsbildens pixlar till modellens mm** (`frame_from_result`, `anchors`). Den automatiska analysen ritar
   granskningsbilden ur ett höjdfält i stenytans plan (src/auto_grooves.Heightfield): kolumn ix och rad iy i rutnätet
   ligger på a = a0 + ix · res längs u och b = b0 + iy · res längs v, och bilden är vänd upp och ned och skalad med
   image_scale (`_overlay_png`). Analysen anger sedan 2026-11-06 ramen själv (`image_frame`); äldre analyser får den
   anpassad ur snittens egna lägen (minsta kvadrat, pixel mot plan). Höjden längs normalen tas ur själva modellen
   (högsta punkt inom 1 mm i planet, som höjdfältet), annars ur de närmaste snitten (botten + spårdjup).
   Punkterna är mm i 3D-modellen centrerad på sin omslutande lådas mitt, som appens övriga koordinater.

3. **Facit version 2** (`read_facit`). Version 1 (märkta snitt och runmarkeringar) läses som förut; version 2 lägger
   till `rune_links`, `skipped_tokens`, `transliteration` (strängen och dess källa) och `tokens`.
"""
from __future__ import annotations

import functools
import math
import re

import numpy as np

import src.runlm as rl

FACIT_TYPE = "vitki-rune-facit"
FACIT_VERSION = 2
RUNDATA_VERSION = "2014 med RUNDATA.xls uppdaterad 2018"
RUNDATA_LICENCE = "ODbL-1.0 / DbCL-1.0"
COORDS = "mm i 3D-modellen centrerad på sin omslutande lådas mitt (centered_by)"
LINKABLE = ("rune", "uncertain", "lost")
DIVIDERS = set(":÷'·×+")
# The runes textmodel.text_groups keeps (after runlm.runekey); other letters are runes too, but outside its text
MODEL_RUNES = re.compile(r"[a-zþðæøåöäąR]")
VIEW_DISTANCE_MM = 300.0  # the stored camera stands this far out along the normal: a rune and its neighbours in view
HEIGHT_RADIUS_MM = 1.0    # the surface height is the highest model point within this distance in the plane
MAX_MARKS = 2000


# ---- 1. tokenisation ---------------------------------------------------------------------------------------------

def tokenize(translit: str) -> list[dict]:
    """Rundatas translitterering som en lista av token, i läsordning.

    Varje token: i (index), char (tecknet; runorna med runlm.runekey, förlorade runor '?'), orig (som i Rundata),
    kind ('rune', 'uncertain', 'lost', 'divider', 'gap', 'other'), word (ordnummer, None för skiljetecken),
    section (Rundatas sektion, 'A', 'B' … eller '-'), pos (plats i textmodellens text, None för det som inte är
    runor där). Flaggor bara när de gäller: reason ('lost' för '-', 'illegible' för '?'), bind_next (bindruna med
    nästa runa, '^'), older (inom [ ]: känd ur äldre dokumentation), uninterpreted (inom < >), line_break (radbyte
    '¶' före tecknet)."""
    tokens: list[dict] = []
    word = -1
    open_word = False

    def add(kind: str, char: str, orig: str, in_word: bool, **flags):
        nonlocal word, open_word
        if in_word and not open_word:
            word += 1
            open_word = True
        t = {"i": len(tokens), "char": char, "orig": orig, "kind": kind, "word": word if in_word else None,
             "section": section}
        t.update({k: v for k, v in flags.items() if v})
        tokens.append(t)
        return t

    for section, part in rl.sections(translit or ""):
        open_word = False
        paren = bracket = angle = brace = False
        line_break = False
        i, n = 0, len(part)
        while i < n:
            ch = part[i]
            if ch in "()":
                paren = ch == "("
            elif ch in "[]":
                bracket = ch == "["
            elif ch in "<>":
                angle = ch == "<"
            elif ch in "{}":
                brace = ch == "{"
            elif ch == "^":
                if tokens and tokens[-1]["kind"] in LINKABLE:
                    tokens[-1]["bind_next"] = True
            elif ch == "¶":
                line_break = True
            elif ch == "|":
                if part[i:i + 3] == "| |":  # the text goes on on another side: a word boundary
                    open_word = False
                    i += 3
                    continue
            elif ch.isspace():
                open_word = False
            elif ch in DIVIDERS:
                j = i
                while j < n and part[j] in DIVIDERS:
                    j += 1
                open_word = False
                add("divider", part[i:j], part[i:j], False, line_break=line_break)
                line_break = False
                open_word = False
                i = j
                continue
            elif ch == ".":
                j = i
                while j < n and part[j] == ".":
                    j += 1
                if j - i >= 2:
                    add("gap", "…", part[i:j], True, older=bracket, line_break=line_break)
                else:
                    add("other", ".", ".", True, line_break=line_break)
                line_break = False
                i = j
                continue
            else:
                flags = dict(older=bracket, uninterpreted=angle, line_break=line_break)
                if brace or not (ch.isalpha() or ch in "-?"):
                    # a lost sign in Latin text is written '?' like a lost rune, as the text model writes it
                    add("other", "?" if ch == "-" else ch, ch, True, **flags)
                elif ch in "-?":
                    add("lost", "?", ch, True, reason="lost" if ch == "-" else "illegible", **flags)
                else:
                    add("uncertain" if paren else "rune", rl.runekey(ch), ch, True, **flags)
                line_break = False
            i += 1
        open_word = False
    _positions(translit, tokens)
    return tokens


def _positions(translit: str, tokens: list[dict]) -> None:
    """pos: the token's place in textmodel.text_groups' joined text, found by walking both in order (both read the
    same sections in the same order, so every rune of the model text is met by exactly one token)."""
    from src.textmodel import text_groups
    groups, _ = text_groups(translit or "")
    full = "".join(groups)
    j = 0
    for t in tokens:
        t["pos"] = None
        c = t["char"] if t["kind"] in LINKABLE or t["kind"] == "other" else None
        if c and j < len(full) and full[j] == rl.runekey(c):
            t["pos"] = j
            j += 1


def model_text(translit: str) -> str:
    from src.textmodel import text_groups
    return "".join(text_groups(translit or "")[0])


def linkable(tokens: list[dict]) -> list[int]:
    return [t["i"] for t in tokens if t["kind"] in LINKABLE]


@functools.lru_cache(maxsize=1)
def _records_by_key() -> dict:
    from src.signum import fold_signum
    by: dict = {}
    for r in rl.load_rundata():
        by.setdefault(r["signum"], r)
        by.setdefault(fold_signum(r["signum"]), r)
    return by


def rundata_record(signum: str | None) -> tuple[dict | None, str | None]:
    """(Rundata's record, part letter) for a signum as written in the app: 'Sö 113', 'So 113', or a part stone such as
    'Sö 137A' (the record Sö 137 and part 'A')."""
    from src.signum import fold_signum
    s = (signum or "").strip()
    if not s:
        return None, None
    by = _records_by_key()
    rec = by.get(s) or by.get(fold_signum(s))
    if rec is not None:
        return rec, None
    m = re.match(r"^(.*\d)\s*([A-Da-d])$", s)
    if m:
        rec = by.get(m.group(1).strip()) or by.get(fold_signum(m.group(1)))
        if rec is not None:
            return rec, m.group(2).upper()
    return None, None


def transliteration_for(rec: dict | None, part: str | None = None) -> dict | None:
    """The transliteration of a Rundata record with its source and tokens, or None when it has none. part: a part
    stone's letter ('A' for Sö 137A): only that section, when the record has it."""
    if not rec or not (rec.get("transliteration") or "").strip():
        return None
    text = rec["transliteration"]
    tokens = tokenize(text)
    sections = sorted({t["section"] for t in tokens})
    if part and part in sections:
        tokens = [t for t in tokens if t["section"] == part]
    return {"signum": rec["signum"], "transliteration": text, "part": part if part in sections else None,
            "sections": sections, "tokens": tokens,
            "source": {"database": "Samnordisk runtextdatabas", "version": RUNDATA_VERSION,
                       "licence": RUNDATA_LICENCE, "signum": rec["signum"],
                       "publisher": "Institutionen för nordiska språk, Uppsala universitet"}}


# ---- 2. review-image pixels to model millimetres ----------------------------------------------------------------

def basis(normal, up=None):
    from src.auto_grooves import basis as _basis
    return _basis(normal, up)


def frame_from_heightfield(hf, scale: float, width: int, height: int) -> dict:
    """The review image's frame, as analyze_grooves writes it (image_frame)."""
    from src.auto_grooves import image_frame
    return image_frame(hf, scale, width, height)


def _affine(frame: dict) -> dict:
    """{u, v, n, ka, a_off, kb, b_off}: a = a_off + ka · x, b = b_off + kb · y."""
    if "ka" in frame:
        return frame
    res, s = float(frame["grid_mm"]), float(frame["image_scale"])
    return {"u": np.asarray(frame["u"], float), "v": np.asarray(frame["v"], float), "n": np.asarray(frame["n"], float),
            "ka": res / s, "a_off": float(frame["a0_mm"]),
            "kb": -res / s, "b_off": float(frame["b0_mm"]) + (int(frame["rows"]) - 1) * res, "source": "analys"}


def frame_from_slices(slices: list[dict], normal, up=None) -> dict | None:
    """The frame fitted from the slices' own positions (pixel against plane, least squares with one pass that drops
    points more than 3 mm off), for analyses made before image_frame was written. None with fewer than 3 slices."""
    u, v, n = basis(normal, up)
    pts = [(s["img_x"], s["img_y"], s["point"]) for s in slices
           if s.get("point") is not None and s.get("img_x") is not None and s.get("img_y") is not None]
    if len(pts) < 3:
        return None
    X = np.array([[p[0], p[1]] for p in pts], float)
    P = np.array([p[2] for p in pts], float)
    a, b = P @ u, P @ v
    out = {"u": u, "v": v, "n": n, "source": "anpassad ur snitten"}
    for coord, col, key in ((a, 0, "a"), (b, 1, "b")):
        keep = np.ones(len(X), bool)
        for _ in range(2):
            A = np.column_stack([np.ones(keep.sum()), X[keep, col]])
            off, k = np.linalg.lstsq(A, coord[keep], rcond=None)[0]
            resid = np.abs(off + k * X[:, col] - coord)
            keep = resid <= max(3.0, float(np.percentile(resid, 90)) if keep.sum() < 10 else 3.0)
            if keep.sum() < 3:
                break
        out["k" + key], out[key + "_off"] = float(k), float(off)
        out[key + "_rms_mm"] = float(np.sqrt(np.mean((off + k * X[keep, col] - coord[keep]) ** 2)))
    return out


def frame_from_result(result: dict) -> dict | None:
    """The review image's frame for an analysis: its own image_frame, else fitted from its slices."""
    fr = result.get("image_frame")
    if isinstance(fr, dict) and all(k in fr for k in ("u", "v", "n", "a0_mm", "b0_mm", "grid_mm", "rows", "image_scale")):
        return _affine(fr)
    params = result.get("parameters") or ((result.get("provenance") or {}).get("parameters")) or {}
    if not params.get("normal"):
        return None
    return frame_from_slices([s for s in result.get("slices") or [] if s.get("accepted")],
                             params["normal"], params.get("up"))


def pixel_to_plane(frame: dict, x: float, y: float) -> tuple[float, float]:
    f = _affine(frame)
    return f["a_off"] + f["ka"] * float(x), f["b_off"] + f["kb"] * float(y)


def plane_to_pixel(frame: dict, a: float, b: float) -> tuple[float, float]:
    f = _affine(frame)
    return (a - f["a_off"]) / f["ka"], (b - f["b_off"]) / f["kb"]


def world(frame: dict, a: float, b: float, h: float) -> np.ndarray:
    f = _affine(frame)
    return a * f["u"] + b * f["v"] + h * f["n"]


class SurfaceHeights:
    """The model's points in the plane coordinates of a frame, sorted along u, for the height at many marks."""

    def __init__(self, vertices: np.ndarray, frame: dict):
        f = _affine(frame)
        V = np.asarray(vertices, float)
        a, b, h = V @ f["u"], V @ f["v"], V @ f["n"]
        order = np.argsort(a)
        self.a, self.b, self.h = a[order], b[order], h[order]

    def at(self, a: float, b: float, radius: float = HEIGHT_RADIUS_MM) -> float | None:
        for r in (radius, 2 * radius, 5 * radius):
            lo, hi = np.searchsorted(self.a, a - r), np.searchsorted(self.a, a + r, side="right")
            if hi > lo:
                sel = np.abs(self.b[lo:hi] - b) <= r
                if sel.any():
                    return float(self.h[lo:hi][sel].max())
        return None


def _height_from_slices(frame: dict, slices: list[dict], a: float, b: float, k: int = 4) -> float | None:
    """The surface near (a, b) from the nearest accepted slices: each slice's bottom plus its groove depth."""
    f = _affine(frame)
    rows = [(np.asarray(s["point"], float), float(s.get("spårdjup_mm") or 0.0)) for s in slices
            if s.get("accepted") and s.get("point") is not None]
    if not rows:
        return None
    P = np.array([p for p, _ in rows])
    d = np.hypot(P @ f["u"] - a, P @ f["v"] - b)
    near = np.argsort(d)[:k]
    return float(np.median([P[j] @ f["n"] + rows[j][1] for j in near]))


def anchors(frame: dict, marks, mesh_vertices=None, slices=None, view_distance: float = VIEW_DISTANCE_MM) -> list[dict]:
    """The 3D anchor of every mark [x, y] (review-image pixels): {image_xy, plane_mm, point_mm, height_from,
    normal_or_view}. point_mm is None when neither the model nor any slice gives a height."""
    f = _affine(frame)
    heights = SurfaceHeights(mesh_vertices, f) if mesh_vertices is not None and len(mesh_vertices) else None
    out = []
    for m in marks:
        x, y = float(m[0]), float(m[1])
        a, b = pixel_to_plane(f, x, y)
        h, src = (heights.at(a, b), "modellen") if heights is not None else (None, None)
        if h is None and slices:
            h, src = _height_from_slices(f, slices, a, b), "snitten"
        p = world(f, a, b, h) if h is not None else None
        n = f["n"]
        out.append({
            "image_xy": [round(x, 2), round(y, 2)], "plane_mm": [round(a, 3), round(b, 3)],
            "point_mm": [round(float(c), 3) for c in p] if p is not None else None,
            "height_from": src if p is not None else None,
            "normal_or_view": {
                "normal": [round(float(c), 6) for c in n],
                "view": ({"position": [round(float(c), 2) for c in p + view_distance * n],
                          "target": [round(float(c), 3) for c in p], "up": [round(float(c), 6) for c in f["v"]]}
                         if p is not None else None),
                "source": "analysens normal: vyn när analysen kördes (Vänd ristade sidan mot mig), med bildens uppåt",
            },
        })
    return out


def check_marks(marks) -> list[list[float]]:
    if not isinstance(marks, list) or len(marks) > MAX_MARKS:
        raise ValueError(f"Markeringarna ska vara en lista med högst {MAX_MARKS} punkter.")
    out = []
    for m in marks:
        if (not isinstance(m, (list, tuple)) or len(m) != 2
                or not all(isinstance(c, (int, float)) and not isinstance(c, bool) and math.isfinite(c) for c in m)):
            raise ValueError("Varje markering ska vara [x, y] i granskningsbildens pixlar.")
        out.append([float(m[0]), float(m[1])])
    return out


KINDS = ("rune", "uncertain", "lost", "divider", "gap", "other")


def check_tokens(tokens) -> list[dict]:
    """Tokens as they come back from a browser or a file: the fields the TEI export reads, with the right types."""
    if not isinstance(tokens, list) or not tokens:
        raise ValueError("tokens ska vara en icke-tom lista.")
    for k, t in enumerate(tokens):
        if (not isinstance(t, dict) or not isinstance(t.get("i"), int) or isinstance(t.get("i"), bool)
                or t.get("kind") not in KINDS or not isinstance(t.get("char"), str) or len(t["char"]) > 8
                or not isinstance(t.get("orig", ""), str) or len(t.get("orig", "")) > 8
                or not (t.get("word") is None or isinstance(t.get("word"), int))
                or not isinstance(t.get("section", "-"), str) or len(t.get("section", "-")) > 8):
            raise ValueError(f"tokens[{k}] har fel form.")
        t.setdefault("orig", t["char"])
        t.setdefault("section", "-")
    if len({t["i"] for t in tokens}) != len(tokens):
        raise ValueError("Två token har samma index.")
    return tokens


# ---- 3. the facit file -----------------------------------------------------------------------------------------

def read_facit(d: dict) -> dict:
    """A facit file of version 1 or 2, with version 2's fields always present (empty for version 1). ValueError for
    something that is not a Vitki facit."""
    # a facit without type (made by hand, or by the evaluation's own tests) is read as version 1 when it has labels
    if not isinstance(d, dict) or d.get("type", FACIT_TYPE if isinstance(d.get("labels"), list) else None) != FACIT_TYPE:
        raise ValueError("Filen är inte ett Vitki-facit (type vitki-rune-facit).")
    version = d.get("version", 1)
    if version not in (1, 2):
        raise ValueError(f"Okänd facitversion {version!r} (1 och 2 kan läsas).")
    out = {**d, "version": version}
    out.setdefault("labels", [])
    out.setdefault("rune_marks", [])
    if version == 1:
        out.update({"rune_links": [], "skipped_tokens": [], "tokens": None, "transliteration": None})
        return out
    links = d.get("rune_links") or []
    tokens = d.get("tokens") or []
    if not isinstance(links, list) or not isinstance(tokens, list):
        raise ValueError("rune_links och tokens ska vara listor.")
    # token indices are the tokens' own i (a part stone such as Sö 137A has only its section's tokens)
    ids = {t.get("i") for t in tokens if isinstance(t, dict)}
    for k, ln in enumerate(links):
        if not isinstance(ln, dict) or not isinstance(ln.get("tokens"), list) or not 1 <= len(ln["tokens"]) <= 2:
            raise ValueError(f"rune_links[{k}]: tokens ska vara en eller två tokenindex.")
        if any(not isinstance(t, int) or isinstance(t, bool) or (ids and t not in ids) for t in ln["tokens"]):
            raise ValueError(f"rune_links[{k}]: tokenindex utanför translittereringen.")
        if ln.get("token_index") != ln["tokens"][0]:
            raise ValueError(f"rune_links[{k}]: token_index ska vara det första av tokens.")
        p = ln.get("point_mm")
        if p is not None and (not isinstance(p, list) or len(p) != 3):
            raise ValueError(f"rune_links[{k}]: point_mm ska vara [x, y, z] eller null.")
    used = [t for ln in links for t in ln["tokens"]] + list(d.get("skipped_tokens") or [])
    if len(used) != len(set(used)):
        raise ValueError("Samma runa är kopplad eller överhoppad mer än en gång.")
    out.setdefault("skipped_tokens", [])
    return out


def token_by_index(facit: dict) -> dict[int, dict]:
    return {t["i"]: t for t in facit.get("tokens") or [] if isinstance(t, dict) and "i" in t}


def link_points(facit: dict) -> np.ndarray:
    """The linked runes' 3D points (one row per link with a point), in the facit's order."""
    pts = [ln["point_mm"] for ln in facit.get("rune_links") or [] if ln.get("point_mm") is not None]
    return np.asarray(pts, float).reshape(-1, 3)
