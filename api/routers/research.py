"""Forskningsluckor och prioriteringar."""
from functools import lru_cache

from fastapi import APIRouter
from pydantic import BaseModel, Field

from api.rundata import store
from api.routers.orthography import model as orthography_model
from src import research_gaps as gaps

router = APIRouter()


class GapsRequest(BaseModel):
    measured_signa: list[str] = Field(default_factory=list)


@lru_cache(maxsize=1)
def _hypotheses() -> dict:
    return gaps.orthographic_hypotheses(orthography_model(), store().inscriptions)


@lru_cache(maxsize=1)
def _open_questions() -> dict:
    return gaps.open_questions(store().inscriptions)


@router.post("/gaps")
def research_gaps(req: GapsRequest):
    s = store()
    # Normalise measured signa through Rundata (e.g. "So 113" -> "Sö 113")
    measured = {rec["signum"] for rec in (s.get(x) for x in req.measured_signa) if rec}
    return {
        "coverage": gaps.coverage(s.inscriptions, measured),
        "hypotheses": _hypotheses(),
        "open_questions": _open_questions(),
        "measurement_priorities": gaps.measurement_priorities(s.inscriptions, measured),
        "source_note": gaps.SOURCE_NOTE,
        "attribution": s.meta["attribution"],
    }
