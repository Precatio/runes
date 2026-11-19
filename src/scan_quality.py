"""Ett enkelt kvalitetsbetyg per skanning (God, Godtagbar, Svag) ur det huggspårsanalysen redan mäter (2026-11-19).

Delarna:
- *Punktavstånd* (parameters.mesh_point_spacing_mm, medianlängden på meshens kanter).
- *Hål* (parameters.hole_fraction, från 2026-11-19): andelen av stenytans kontur i analysens rutnät som saknar
  skanningspunkter, efter att glapp på några få rutor har slutits (`hole_fraction`). Det är luckor i skanningen,
  inte glesa punkter: punkter glesare än rutnätet sluts av samma stängning som höjdfältet använder.
- *Brus* (parameters.noise_mm): visas men betygsätts inte. Det är ytans spridning kring referensytan i 20 mm skala
  (1,4826 × MAD) och mäter mest stenens egen ojämnhet (korn, vittring): extra skannerbrus på 0,15 mm (provet
  2026-11-19, D1) höjde det bara med i median 0,05 mm (0,07 på Zedigs skanningar), medan det skiljer 0,07–0,83 mm
  mellan skanningarna. Det styr ändå analysens djuptröskel (3 × bruset), så det visas bredvid betyget.

Betyget är den sämsta av delarna punktavstånd och hål. Gränserna sattes innan någon andel hål räknades och är inte
anpassade efter provet 2026-11-19:
- Punktavstånd: God högst 0,5 mm – Vitki-protokollets rekommendation sedan tidigare (src/protocol.MAX_MESH_SPACING_MM).
  Godtagbar högst 1,0 mm – det dubbla. I robusthetsprovet (METHODS 2e) flyttade en skanning glesad till hälften av
  trianglarna (ungefär 1,4 gånger punktavståndet) stenens V-vinkel i median 0,9°, en fjärdedel (ungefär dubbla
  punktavståndet) 2,8° (som mest 9,1°).
- Hål: God högst 2 %, Godtagbar högst 10 % – runda konventionsgränser, inte kalibrerade. Varje hål tar dessutom
  analysens kantzon runt sig ur mätningen, så hål kostar mer yta än sin egen.
Samma regel som web/src/lib/scanQuality.ts (tests/test_scan_quality.py kör båda)."""
from __future__ import annotations

import math

import numpy as np
from scipy import ndimage

SPACING_GOOD_MM = 0.5
SPACING_OK_MM = 1.0
HOLES_GOOD = 0.02
HOLES_OK = 0.10
LABEL = {"god": "God", "godtagbar": "Godtagbar", "svag": "Svag", "okänd": "Okänd"}
_RANK = {"god": 0, "godtagbar": 1, "svag": 2}


def hole_fraction(valid: np.ndarray, closing_iterations: int = 2) -> float:
    """Andelen av konturen (de ifyllda rutorna) som saknar punkter efter en stängning med lika många steg som
    Heightfield.region använder: glapp på någon enstaka ruta (glesa punkter) räknas inte, större luckor gör det."""
    closed = ndimage.binary_closing(valid, iterations=closing_iterations)
    region = ndimage.binary_fill_holes(closed)
    n = int(region.sum())
    return float((region & ~closed).sum() / n) if n else float("nan")


def _num(v) -> float | None:
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) else None


def _dec(v: float, d: int) -> str:
    return f"{v:.{d}f}".replace(".", ",")


def spacing_class(mm: float | None) -> str:
    if mm is None:
        return "okänd"
    return "god" if mm <= SPACING_GOOD_MM else "godtagbar" if mm <= SPACING_OK_MM else "svag"


def holes_class(share: float | None) -> str:
    if share is None:
        return "okänd"
    return "god" if share <= HOLES_GOOD else "godtagbar" if share <= HOLES_OK else "svag"


def grade(params: dict | None) -> dict:
    """Betyget ur en mätnings parametrar: {klass, label, parts, text}."""
    p = params or {}
    spacing, holes, noise = (_num(p.get(k)) for k in ("mesh_point_spacing_mm", "hole_fraction", "noise_mm"))
    ks, kh = spacing_class(spacing), holes_class(holes)
    parts = [
        {"key": "punktavstånd", "value": spacing, "klass": ks,
         "text": "punktavståndet är inte känt" if spacing is None else
         f"punktavstånd {_dec(spacing, 2)} mm (god högst {_dec(SPACING_GOOD_MM, 1)}, godtagbar högst "
         f"{_dec(SPACING_OK_MM, 1)} mm)"},
        {"key": "hål", "value": holes, "klass": kh,
         "text": "andelen hål är inte uppmätt (äldre analys)" if holes is None else
         f"hål {_dec(100 * holes, 1)} % av stenytan (god högst {HOLES_GOOD * 100:g} %, godtagbar högst "
         f"{HOLES_OK * 100:g} %)"},
        {"key": "brus", "value": noise, "klass": None,
         "text": "ytans brus är inte känt" if noise is None else
         f"ytans brus {_dec(noise, 2)} mm (betygsätts inte: det speglar mest stenens egen ojämnhet; spårtröskeln "
         f"blir 3 × bruset)"},
    ]
    if ks == "okänd":
        klass = "okänd"
        text = "Skanningens kvalitet kan inte bedömas: punktavståndet saknas."
    else:
        klass = max((k for k in (ks, kh) if k != "okänd"), key=_RANK.__getitem__)
        text = (f"{LABEL[klass]}: den sämsta av delarna punktavstånd och hål"
                + (" (här bara punktavståndet, hålen är inte uppmätta)" if kh == "okänd" else "") + ". "
                + "; ".join(x["text"] for x in parts) + ".")
    return {"klass": klass, "label": LABEL[klass], "parts": parts, "text": text}
