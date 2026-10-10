"""Akademisk rapport ur mätkorpusen (Word, LaTeX, Markdown, HTML)."""

import numpy as np
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from api import llm
from api.routers.research import stone_context
from api.errors import logger
from api import mesh_cache
from api.rundata import store
from src import academic, report_templates, stone_report
from src.reading import validate as validate_reading
from src.synthesis import site_geology

router = APIRouter()


def _as_object(value) -> dict:
    """The model sometimes wraps its JSON object in a list; anything else counts as no answer."""
    if isinstance(value, list):
        value = next((v for v in value if isinstance(v, dict)), {})
    return value if isinstance(value, dict) else {}


class Scope(BaseModel):
    type: Literal["carver", "province", "corpus", "stones"] = "corpus"
    value: Optional[str] = None
    title: Optional[str] = None


class AcademicRequest(BaseModel):
    scope: Scope = Field(default_factory=Scope)
    entries: list[dict]
    author: str = ""
    institution: str = ""
    use_ai: bool = True
    format: Literal["json", "docx"] = "json"
    # AI text from an earlier JSON call, so a download matches the preview without a new AI call
    ai_text: Optional[dict[str, str]] = None


AI_SECTIONS_SCHEMA = {
    "type": "object",
    "properties": {"abstract": {"type": "string"}, "introduction": {"type": "string"}, "discussion": {"type": "string"}},
    "required": ["abstract", "introduction", "discussion"],
}


def ai_sections(aictx: llm.AIContext, facts_text: str) -> dict:
    prompt = f"""
Du skriver delar av en vetenskaplig rapport på svenska om huggteknik på runstenar.
Använd ENDAST fakta nedan. Hitta inte på stenar, ristare, siffror, litteratur eller slutsatser som inte följer
av fakta. Var försiktig: få stenar ger osäkra slutsatser. Skriv i akademisk, saklig ton utan överdrifter.

FAKTA:
{facts_text}

Svara med JSON:
{{"abstract": "4–6 meningar", "introduction": "1–2 stycken om syfte och material", "discussion": "2–3 stycken: vad resultaten visar, hur säkra de är och vad som behövs härnäst"}}
"""
    return _as_object(llm.generate(aictx, prompt, schema=AI_SECTIONS_SCHEMA, tier="pro").data)


@router.post("/academic")
def academic_report(req: AcademicRequest, aictx: llm.AIContext = Depends(llm.ai_context)):
    if not req.entries:
        raise HTTPException(status_code=400, detail="Urvalet innehåller inga mätningar.")
    if len(req.entries) > 500:
        raise HTTPException(status_code=400, detail="Högst 500 stenar per rapport.")
    facts = academic.build_facts(req.entries, store().get, req.scope.model_dump())

    ai, ai_used = None, False
    if req.use_ai and req.ai_text:
        ai, ai_used = req.ai_text, True
    elif req.use_ai and llm.available(aictx):
        try:
            ai = ai_sections(aictx, academic.facts_text(facts))
            ai_used = True
        except Exception as e:
            logger.warning("AI-text för rapporten misslyckades: %r", e)

    blocks = academic.build_document(facts, req.author, req.institution, ai)
    if req.format == "docx":
        return Response(content=academic.to_docx(blocks),
                        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        headers={"Content-Disposition": 'attachment; filename="rapport.docx"'})
    figures = [{"name": b["name"], "png": b["png"]} for b in blocks if b["type"] == "figure"]
    return {"html": academic.to_html(blocks), "markdown": academic.to_markdown(blocks),
            "latex": academic.to_latex(blocks), "figures": figures, "ai_used": ai_used, "ai_text": ai,
            "facts": academic.facts_text(facts)}


class StoneReportRequest(BaseModel):
    signum: str = ""
    title: Optional[str] = None
    author: str = ""
    institution: str = ""
    meta: dict = Field(default_factory=dict)
    scan: dict = Field(default_factory=dict)
    condition: dict = Field(default_factory=dict)
    # [{feature_type, slices: [{metrics…, profile, point, direction, up, fit_r2}], provenance}]
    analyses: list[dict] = Field(default_factory=list)
    counts: Optional[dict] = None
    # The model is looked up in the analysis engine's memory; without it the surface figures are left out
    mesh_id: Optional[str] = None
    view: Optional[dict] = None  # {normal, up} for the carved face
    corpus: list[dict] = Field(default_factory=list)
    two_d: Optional[dict] = None
    synthesis: Optional[dict] = None  # result of /api/synthesis/analyze
    reading: Optional[dict] = None  # result of /api/phonetics/analyze (the app's own reading)
    # The full stone analysis: steps, sensitivity analysis with review images, all readings, notes (appendix B)
    workflow: Optional[dict] = None
    use_ai: bool = True
    format: Literal["json", "docx"] = "json"
    ai_text: Optional[dict[str, str]] = None
    include_r: bool = True
    # Publication form (src/report_templates.py) and its options, e.g. {"venue": "fornvannen"}
    template: str = "stenrapport"
    template_options: dict = Field(default_factory=dict)


def _view(req: StoneReportRequest):
    v = req.view or {}
    if v.get("normal"):
        return v["normal"], v.get("up")
    for a in req.analyses:
        params = (a.get("provenance") or {}).get("parameters") or {}
        if params.get("normal"):
            return params["normal"], params.get("up")
    ups = [s["up"] for a in req.analyses for s in a.get("slices") or [] if s.get("up")]
    if ups:
        return list(np.mean(np.asarray(ups, float), axis=0)), None
    return None, None


@router.get("/templates")
def report_template_list():
    """Publiceringsformer för stenrapporten: blogginlägg, tidskriftsartikel, uppsats, avhandlingskapitel m.fl."""
    return {"templates": report_templates.catalogue()}


@router.post("/stone")
def stone_report_endpoint(req: StoneReportRequest,
                          aictx: llm.AIContext = Depends(llm.ai_context)):
    if req.template not in report_templates.TEMPLATES:
        raise HTTPException(status_code=400, detail=f"Okänd rapportmall: {req.template}")
    if not any(a.get("slices") for a in req.analyses):
        raise HTTPException(status_code=400, detail="Underlaget saknar uppmätta tvärsnitt. Gör en 3D-analys först.")
    if sum(len(a.get("slices") or []) for a in req.analyses) > 3000:
        raise HTTPException(status_code=400, detail="Högst 3000 tvärsnitt per rapport.")
    facts = stone_report.build_facts(req.model_dump(), store().get)
    facts["geology"] = site_geology(facts["rundata"])
    # What Forskningsluckor knows about the stone, and the style and inscription types of the top candidates
    names = [c["name"] for c in ((req.synthesis or {}).get("candidates") or [])[:3]]
    facts["research"] = stone_context(facts["signum"], names) if facts.get("rundata") else None
    # The stone against the R corpus analyses (only if R and the corpus results exist; never started here)
    facts["r"] = None
    if facts.get("rundata") and req.include_r:
        try:
            from api.routers.rstats import stone_analysis
            facts["r"] = stone_analysis(facts["rundata"]["signum"], names)
        except Exception as e:
            logger.warning("R-analysen för stenrapporten misslyckades: %r", e)
    rd = req.reading or {}
    if rd.get("transliteration"):
        facts["reading_validation"] = rd.get("validation") or validate_reading(
            rd["transliteration"], facts["rundata"], store().inscriptions, rd.get("others") or [])

    surface, surface_note = None, None
    entry = mesh_cache.peek(req.mesh_id) if req.mesh_id else None
    normal, up = _view(req)
    if entry is not None and not entry.info.get("mock") and normal is not None:
        try:
            surface = stone_report.Surface(entry.mesh, normal, up)
        except Exception as e:
            logger.warning("Ytbilder för stenrapporten misslyckades: %r", e)
            surface_note = "Ytbilderna kunde inte räknas fram."
    elif req.mesh_id:
        surface_note = "3D-modellen finns inte i analysmotorns minne. Ladda in skanningen i 3D-vyn igen."

    ai, ai_used = None, False
    if req.use_ai and req.ai_text:
        ai, ai_used = req.ai_text, True
    elif req.use_ai and llm.available(aictx):
        try:
            if req.template == "stenrapport":
                ai = ai_sections(aictx, stone_report.facts_text(facts))
            else:
                spec = report_templates.ai_request(req.template, req.template_options, stone_report.facts_text(facts))
                if spec:
                    ai = _as_object(llm.generate(aictx, spec[0], schema=spec[1], tier="pro").data)
            ai_used = bool(ai)
        except Exception as e:
            logger.warning("AI-text för stenrapporten misslyckades: %r", e)

    blocks = stone_report.build_document(facts, req.author, req.institution, ai, surface, req.title)
    blocks = report_templates.apply(req.template, blocks, facts, ai, req.template_options)
    if req.format == "docx":
        return Response(content=academic.to_docx(blocks),
                        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        headers={"Content-Disposition": f'attachment; filename="{req.template}.docx"'})
    figures = [{"name": b["name"], "png": b["png"]} for b in blocks if b["type"] == "figure"]
    return {"html": academic.to_html(blocks), "markdown": academic.to_markdown(blocks),
            "latex": academic.to_latex(blocks), "figures": figures, "ai_used": ai_used, "ai_text": ai,
            "surface": surface is not None, "surface_note": surface_note,
            "facts": stone_report.facts_text(facts),
            "template": req.template, "guide": report_templates.guide(req.template, req.template_options)}
