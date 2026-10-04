"""Forskningsluckor och prioriteringar."""
from functools import lru_cache

from fastapi import APIRouter
from pydantic import BaseModel, Field

from api.rundata import store
from api.routers.orthography import model as orthography_model
from src import findings, research_gaps as gaps

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


class FindingsRequest(BaseModel):
    # Corpus entries ({signum, feature_type, means}) and AI style assessments from the user's projects
    corpus: list[dict] = Field(default_factory=list)
    styles: list[dict] = Field(default_factory=list)


@lru_cache(maxsize=1)
def _orthographic_findings() -> tuple:
    return tuple(findings.orthographic_findings(orthography_model(), store().inscriptions))


@router.post("/findings")
def research_findings(req: FindingsRequest):
    """Appens resultat mot Rundata: stämmer, nytt eller motsäger – med en öppet redovisad uppskattning."""
    s = store()
    technique, technique_note = findings.technique_findings(req.corpus, s.get, s.inscriptions)
    items = list(_orthographic_findings()) + technique + findings.style_findings(req.styles, s.get, s.inscriptions)
    items.sort(key=lambda f: -f["score"])
    return {
        "findings": items,
        "summary": findings.summarize(items),
        "technique_note": technique_note,
        "method_note": findings.__doc__.split("\n\n", 1)[1].strip(),
        "source_note": gaps.SOURCE_NOTE,
    }
