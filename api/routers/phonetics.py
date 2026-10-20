"""Läsning mot Rundata, utan AI (METHODS.md 8): en translitterering (t.ex. en forskares egen läsning av en bild eller ett
nyfynd) jämförs med Rundatas läsning ord för ord och runa för runa, ordformerna slås upp i korpusen, läsningens ortografi
rankas mot ristarna och läsningen valideras (bekräftad, delvis, ej bekräftad, annan inskrift, ej prövbar).

Den blinda AI-läsningen (/analyze) och uppläsningen (/speak) togs bort 2026-10-20: i prov gav AI-läsningen mest streck
eller formler som inte gick att skilja från text ur minnet (Sö 113 gav Jellingstenens text). Adressen /api/phonetics
behålls för /compare, som rapporterna och syntesen fortfarande kan ta emot en läsning från.
"""
from functools import lru_cache

from api.rundata import store
from api.routers.orthography import model as orthography_model
from src.reading import Lexicon, compare, validate
from src.synthesis import smoothed_precision
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


@lru_cache(maxsize=1)
def lexicon() -> Lexicon:
    return Lexicon(store().inscriptions)


def reference_checks(signum: str, transliteration: str, normalization: str,
                     other_readings: Optional[list[str]] = None) -> dict:
    """Allt som räknas fram utan AI: Rundatas läsning, jämförelsen, ordformerna och ortografin."""
    rec = store().get(signum) if signum and signum.lower() not in ("okänd", "okänt") else None
    out: dict = {"rundata": None, "reading_comparison": None, "academic_reading": None, "comparison": None}
    if rec and rec.get("transliteration"):
        out["rundata"] = {k: rec.get(k, "") for k in ("signum", "place", "parish", "transliteration", "normalization",
                                                      "normalization_ows", "translation_en", "style", "dating")}
        out["rundata"]["carvers"] = rec["carvers"]
        out["academic_reading"] = (f"Rundata ({rec['signum']}): {rec['transliteration']} – "
                                   f"{rec.get('normalization', '').replace(chr(34), '')} – ”{rec.get('translation_en', '')}”")
        if transliteration:
            c = compare(transliteration, rec["transliteration"], normalization, rec.get("normalization", ""))
            out["reading_comparison"] = c
            out["comparison"] = c["summary"]
    elif signum and signum.lower() not in ("okänd", "okänt"):
        out["comparison"] = f"Signumet {signum} finns inte i Rundata, eller saknar translitterering – läsningen kan inte jämföras."
    out["form_check"] = lexicon().check(normalization) if normalization else None
    # May the reading be presented as the stone's text? (Rundata, known inscriptions, consistency)
    out["validation"] = validate(transliteration, rec, store().inscriptions, other_readings) if transliteration else None
    if transliteration:
        m = orthography_model()
        rk = m.rank_text(transliteration, normalization, 5, exclude_signum=rec["signum"] if rec else None)
        per = (m.evaluate() or {}).get("per_carver", {})
        out["orthography"] = {
            "n_words": rk["n_words"], "usable": rk["n_words"] >= 8,
            "ranking": [{**r, "precision": smoothed_precision(per.get(r["carver"]))} for r in rk["ranking"]],
            "note": "Vår läsning jämförd med ristarnas stavning i Rundata (stenen själv utesluten).",
        }
    return out


class CompareRequest(BaseModel):
    signum: str = ""
    transliteration: str = ""
    normalization: str = ""
    other_readings: list[str] = []  # other readings of the same image, for the consistency check


@router.post("/compare")
def compare_reading(req: CompareRequest):
    """Jämför en (t.ex. manuellt rättad) läsning med Rundata – utan AI."""
    return reference_checks(req.signum, req.transliteration, req.normalization, req.other_readings)

