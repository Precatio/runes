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
    m, s = orthography_model(), store()
    h = gaps.orthographic_hypotheses(m, s.inscriptions)
    for item in h["new"] + h["reconsider"]:
        item.update(findings.stone_extras(s.get(item["signum"]), item["carver"], s.inscriptions, m.names))
    return h


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
    m, s = orthography_model(), store()
    return tuple(findings.add_extras(findings.orthographic_findings(m, s.inscriptions), s.get, s.inscriptions, m.names))


@router.post("/findings")
def research_findings(req: FindingsRequest):
    """Appens resultat mot Rundata: stämmer, nytt eller motsäger – med en öppet redovisad uppskattning."""
    s = store()
    technique, technique_note = findings.technique_findings(req.corpus, s.get, s.inscriptions)
    extra = findings.add_extras(technique + findings.style_findings(req.styles, s.get, s.inscriptions),
                                s.get, s.inscriptions, orthography_model().names)
    items = list(_orthographic_findings()) + extra
    items.sort(key=lambda f: -f["score"])
    return {
        "findings": items,
        "summary": findings.summarize(items),
        "technique_note": technique_note,
        "method_note": findings.__doc__.split("\n\n", 1)[1].strip(),
        "source_note": gaps.SOURCE_NOTE,
    }


@router.get("/geology/{signum:path}")
def stone_geology(signum: str, radius_km: float = 10.0):
    """Berggrunden där stenen står (SGU) jämförd med stenens material i Rundata."""
    from fastapi import HTTPException
    from src import geology
    rec = store().get(signum)
    if not rec:
        raise HTTPException(status_code=404, detail=f"Signum '{signum}' finns inte i Rundata.")
    if rec.get("lat") is None:
        raise HTTPException(status_code=422, detail="Stenen saknar koordinater i Rundata.")
    if not 1 <= radius_km <= 25:
        raise HTTPException(status_code=400, detail="Radien ska vara 1–25 km.")
    if not geology.enabled():
        raise HTTPException(status_code=503, detail="Geologiuppslag är avstängt på servern.")
    return {"signum": rec["signum"], "place": rec["place"], **geology.bedrock(rec["lat"], rec["lon"],
                                                                                rec.get("material") or "", radius_km)}


@router.get("/language/{signum:path}")
def stone_language(signum: str, carver: str = ""):
    """Språkdrag i inskriften, och jämförda med en ristares inskrifter om en ristare anges."""
    from fastapi import HTTPException
    from src.language_profile import TRAITS, carver_profile, compare, traits
    from src.research_gaps import certain_carvers
    rec = store().get(signum)
    if not rec:
        raise HTTPException(status_code=404, detail=f"Signum '{signum}' finns inte i Rundata.")
    names = orthography_model().names
    t = traits(rec, names)
    out = {"signum": rec["signum"], "traits": [{"trait": k, "group": TRAITS[k][0], "label": TRAITS[k][1],
                                                "definition": TRAITS[k][2], "value": v} for k, v in t.items()]}
    if carver:
        out["comparison"] = compare(t, carver_profile(carver, store().inscriptions, certain_carvers, names,
                                                      exclude=rec["signum"]))
    return out
