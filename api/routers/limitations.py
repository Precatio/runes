"""Kända brister i metoderna (src/limitations.py) – samma lista som i rapporterna och proveniensen."""
from typing import Optional

from fastapi import APIRouter

from src import limitations

router = APIRouter()


@router.get("")
def known_limitations(contexts: Optional[str] = None):
    """Bristerna som gäller sammanhangen (kommaseparerade, t.ex. grooves,auto); utan sammanhang alla."""
    ctx = [c.strip() for c in contexts.split(",") if c.strip()] if contexts else \
        ["grooves", "auto", "comparison", "attribution", "statistics", "research", "ai", "rundata", "software"]
    return {"version": limitations.VERSION, "items": limitations.as_json(limitations.select(ctx)),
            "min_runes_describe": limitations.MIN_RUNES_DESCRIBE, "min_runes_compare": limitations.MIN_RUNES_COMPARE}
