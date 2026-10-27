"""Runor 2020 (Riksantikvarieämbetet, Samnordisk runtextdatabas utgåva 2020) bredvid appens Rundata 2018.

Appen bygger på Rundata 3.1 (2018). Runor 2020 är skördad till data/raa/runor_2020.json (scripts/fetch_runor.py,
inte i git); när filen finns visas Runors uppgifter om en inskrift bredvid Rundatas – ursprunglig plats, bevarad,
anteckningar, datering och en läsning som ändrats sedan 2018 (METHODS.md 17). Appen byter inte källa
(IMPLEMENTATIONSPLAN.md 3.2 är struken 2026-10-26); inget räknas om på Runors uppgifter.

Runor slås upp på exakt signum först och på fold_signum bara som reserv, som i api/rundata.RundataStore: annars får
Närkes Nä 1–34 Runors norska N A1–N A34 (båda blir 'na<n>').
"""
from __future__ import annotations

import ast
import json
import os
import re
import threading
import unicodedata

from src.signum import fold_signum

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "data", "raa", "runor_2020.json")
EDITION = "Runor, Riksantikvarieämbetet (Samnordisk runtextdatabas, utgåva 2020)"
SEP = re.compile(r"[\s·:'×÷+|¶⁓;,.!?\"]|§[A-Z]|\{|\}|\$|=")

_lock = threading.Lock()
# (exact, folded): the exact signum first, as in api/rundata.RundataStore. fold_signum drops diacritics, so the Närke
# 'Nä 11' and the Norwegian 'N A11' share the folded key 'na11', and Runor lists N A1–N A34 before Nä 1–34
_index: tuple[dict, dict] | None = None


def _exact_key(signum: str) -> str:
    """Signumet som det skrivs, bara utan mellanslag (samma nyckel som api/rundata._exact_key)."""
    return re.sub(r"[\s_]+", "", unicodedata.normalize("NFC", signum or ""))


def _lit(v):
    """Skördens fält är sparade som text (str() av Pythonvärden); tillbaka till värdet, annars texten."""
    if not isinstance(v, str):
        return v
    if v in ("None", ""):
        return None
    if v in ("True", "False"):
        return v == "True"
    if v[:1] in "[{(":
        try:
            return ast.literal_eval(v)
        except (ValueError, SyntaxError):
            return v
    return v


def first_reading(reading: str) -> str:
    """Rundata ger ibland två läsningar (§P och §Q); den första jämförs."""
    return re.split(r"§Q", reading or "")[0]


def runes(reading: str) -> str:
    """Läsningen utan skiljetecken, avsnittsetiketter, klamrar och mellanrum, för att jämföra två läsningar.
    Rundata 2018 skriver ʀ som R, ɴ som N och … som ..., Runor 2020 med de egentliga tecknen."""
    t = first_reading(reading).replace("...", "…").replace("R", "ʀ").replace("N", "ɴ")
    t = re.sub(r"§[A-Z]+", "", t)
    t = re.sub(r"[()\[\]{}<>^]", "", t)
    return SEP.sub("", t).lower()


def available() -> bool:
    return os.path.exists(PATH)


def _load() -> tuple[dict, dict]:
    global _index
    with _lock:
        if _index is None:
            exact: dict = {}
            idx: dict = {}
            if available():
                with open(PATH, encoding="utf-8") as f:
                    recs = json.load(f)["inscriptions"]
                # Exact keys: every record's own signum before any alternative signum, so that the alt signum 'N A14'
                # of Bo Peterson1992 cannot take the place of Runor's own record for a stone
                for rec in recs:
                    exact.setdefault(_exact_key(rec["signum"]), rec)
                for rec in recs:
                    for alt in _lit(rec.get("alt_signa")) or []:
                        if isinstance(alt, str) and alt.strip():
                            exact.setdefault(_exact_key(alt), rec)
                # Folded keys, the fallback (case, 'So 113' for 'Sö 113'): unchanged order, first record wins
                for rec in recs:
                    idx.setdefault(fold_signum(rec["signum"]), rec)
                    for alt in _lit(rec.get("alt_signa")) or []:
                        if isinstance(alt, str) and alt.strip():
                            idx.setdefault(fold_signum(alt), rec)
            _index = (exact, idx)
    return _index


def record(signum: str) -> dict | None:
    exact, idx = _load()
    return exact.get(_exact_key(signum)) or idx.get(fold_signum(signum))


def for_inscription(rec: dict) -> dict | None:
    """Runors uppgifter för en Rundata-post, i den form appen visar: None när Runor inte är skördat eller saknar stenen."""
    if not available():
        return None
    r = record(rec["signum"])
    if not r:
        return None
    readings = _lit(r.get("readings")) or []
    reading = ""
    if readings and isinstance(readings[0], dict):
        reading = readings[0].get("reading") or ""
    dating = _lit(r.get("dating")) or {}
    notes = _lit(r.get("notes")) or []
    original = _lit(r.get("original"))
    ours = rec.get("transliteration") or ""
    return {
        "edition": EDITION, "url": r.get("url") or None, "signum": r.get("signum"),
        "extant": _lit(r.get("extant")), "original_location": original,
        "placement": r.get("placement") or None,
        "dating": dating.get("dating") if isinstance(dating, dict) else None,
        "notes": [n for n in notes if isinstance(n, str)],
        "reading": reading or None,
        "reading_changed": bool(reading) and bool(ours) and runes(reading) != runes(ours),
    }
