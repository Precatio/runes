"""Akademisk rapport ur mätkorpusen (Word, LaTeX, Markdown, HTML)."""

from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from api import llm
from api.routers.research import stone_context
from api.errors import logger
from api import mesh_cache
from api.rundata import store
from src import academic, groove_export, i18n, limitations, report_templates, stone_report
from src.reading import validate as validate_reading
from src.synthesis import site_geology
from api.auth import optional_user, require_admin

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
    use_ai: bool = False  # AI prose is opt-in; the computed texts are the default
    format: Literal["json", "docx"] = "json"
    lang: Literal["sv", "en"] = "sv"  # the document's language (src/i18n.py)
    # AI text from an earlier JSON call, so a download matches the preview without a new AI call
    ai_text: Optional[dict[str, str]] = None


AI_SECTIONS_SCHEMA = {
    "type": "object",
    "properties": {"abstract": {"type": "string"}, "introduction": {"type": "string"}, "discussion": {"type": "string"}},
    "required": ["abstract", "introduction", "discussion"],
}


def ai_sections(aictx: llm.AIContext, facts_text: str, known_limits: list[str] | None = None) -> dict:
    limits = "\n".join(f"- {x}" for x in known_limits or [])
    prompt = f"""
Du skriver delar av en vetenskaplig rapport på svenska om huggteknik på runstenar.
Använd ENDAST fakta nedan. Hitta inte på stenar, ristare, siffror, litteratur eller slutsatser som inte följer
av fakta. Var försiktig: få stenar ger osäkra slutsatser. Skriv i akademisk, saklig ton utan överdrifter.

FAKTA:
{facts_text}

KÄNDA BRISTER I METODEN (diskussionen ska ta upp de viktigaste; tona inte ned dem):
{limits}

Svara med JSON:
{{"abstract": "4–6 meningar", "introduction": "1–2 stycken om syfte och material", "discussion": "2–3 stycken: vad resultaten visar, hur säkra de är och vad som behövs härnäst"}}
"""
    return _as_object(llm.generate(aictx, prompt, schema=AI_SECTIONS_SCHEMA, tier="pro").data)


@router.post("/academic")
def academic_report(req: AcademicRequest, aictx: llm.AIContext = Depends(llm.ai_context),
                    _: dict = Depends(require_admin)):
    """Korpusrapporten (flera stenar) – bara för appens grundare."""
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
            ai = ai_sections(aictx, academic.facts_text(facts),
                             [x["short"] for x in limitations.select(academic.CORPUS_LIMITATION_CONTEXTS)])
            ai_used = True
        except Exception as e:
            logger.warning("AI-text för rapporten misslyckades: %r", e)

    blocks = i18n.translate_blocks(academic.build_document(facts, req.author, req.institution, ai), req.lang)
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
    lang: Literal["sv", "en"] = "sv"  # the document's language (src/i18n.py)
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
    two_d: Optional[dict] = None  # {image, crops, caption}: the picture and the rune forms for section 4.6
    synthesis: Optional[dict] = None  # result of /api/synthesis/analyze
    reading: Optional[dict] = None  # the app's own reading, compared with Rundata by /api/phonetics/compare (older projects)
    # The full stone analysis: steps, sensitivity analysis with review images, all readings, notes (appendix B)
    workflow: Optional[dict] = None
    use_ai: bool = False  # AI prose is opt-in; the computed texts are the default
    format: Literal["json", "docx"] = "json"
    ai_text: Optional[dict[str, str]] = None
    include_r: bool = True
    # Publication form (src/report_templates.py) and its options, e.g. {"venue": "fornvannen"}
    template: str = "stenrapport"
    template_options: dict = Field(default_factory=dict)


def _view(req: StoneReportRequest):
    """The carved face's normal and up: the same choice as the groove export makes (groove_export.view_normal), so
    that the exported surface images are the report's figures."""
    normal, up, _ = groove_export.view_normal(req.view, req.analyses)
    return normal, up


class AttributionRequest(BaseModel):
    signum: str
    carver: str
    author: str = ""
    institution: str = ""
    email: str = Field("", max_length=200)  # the author's contact address, from the user's own settings
    lang: Literal["sv", "en"] = "sv"  # the document's language (src/i18n.py)
    format: Literal["json", "docx"] = "json"
    check_sources: bool = True  # look the proposal up in Runor 2020 and Wikidata (network)


@router.post("/attribution")
def attribution_report(req: AttributionRequest):
    """Attribueringsförslag för en sten: alla argument för en ristare, att skicka till runtextdatabasen
    (src/attribution_report.py; METHODS.md 15e)."""
    from api.config import APP_VERSION
    from api.routers.research import _fp, _overview_context
    from src import attribution_report as ar, crosscheck, stone_dimensions
    rec = store().get(req.signum)
    if not rec:
        raise HTTPException(status_code=404, detail="Stenen finns inte i Rundata.")
    ctx, _ = _overview_context(_fp())
    cc = None
    try:
        cc = (crosscheck.check(rec["signum"], req.carver, crosscheck.wikidata_creators()) if req.check_sources
              else crosscheck.cached(rec["signum"], req.carver))
    except Exception as e:
        logger.warning("Avstämningen mot Runor/Wikidata misslyckades: %r", e)
        cc = crosscheck.cached(rec["signum"], req.carver)
    att = None
    try:
        from api.routers import rstats
        from src import r_bridge as rb
        if rstats.corpus_ready():
            att = (rb.JOB.result(rstats.fingerprint()) or {}).get("attribution")
    except Exception as e:
        logger.warning("R-modellens uppgifter kunde inte läsas: %r", e)
    blocks = ar.build(rec, req.carver, ctx, cc, stone_dimensions.lookup(rec["signum"]), req.author, req.institution,
                      {"app": APP_VERSION, "fingerprint": _fp()}, att, req.email)
    blocks = i18n.translate_blocks(blocks, req.lang)
    if req.format == "docx":
        return Response(content=academic.to_docx(blocks),
                        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        headers={"Content-Disposition": 'attachment; filename="attribueringsforslag.docx"'})
    return {"html": academic.to_html(blocks), "markdown": academic.to_markdown(blocks), "latex": academic.to_latex(blocks),
            "figures": [], "ai_used": False, "ai_text": None, "title": blocks[0]["text"],
            "crosscheck": (cc or {}).get("status")}


# The full stone report is open to everyone; the other publication forms only to the app's founder
OPEN_TEMPLATES = {"stenrapport"}


@router.get("/templates")
def report_template_list(user: Optional[dict] = Depends(optional_user)):
    """Publiceringsformer för stenrapporten: blogginlägg, tidskriftsartikel, uppsats, avhandlingskapitel m.fl."""
    templates = report_templates.catalogue()
    if not (user and user.get("admin")):
        templates = [t for t in templates if t.get("key") in OPEN_TEMPLATES]
    return {"templates": templates}


@router.post("/stone")
def stone_report_endpoint(req: StoneReportRequest,
                          aictx: llm.AIContext = Depends(llm.ai_context),
                          user: Optional[dict] = Depends(optional_user)):
    if req.template not in report_templates.TEMPLATES:
        raise HTTPException(status_code=400, detail=f"Okänd rapportmall: {req.template}")
    if req.template not in OPEN_TEMPLATES and not (user and user.get("admin")):
        raise HTTPException(status_code=403, detail="Den här publiceringsformen är bara för appens grundare. "
                                                    "Stenrapporten (fullständig) är öppen för alla.")
    if not any(a.get("slices") for a in req.analyses):
        raise HTTPException(status_code=400, detail="Underlaget saknar uppmätta tvärsnitt. Gör en 3D-analys först.")
    if sum(len(a.get("slices") or []) for a in req.analyses) > 3000:
        raise HTTPException(status_code=400, detail="Högst 3000 tvärsnitt per rapport.")
    # The loaded model (when still in memory) helps decide the scan credit: only a recognised published file is
    # credited to an open dataset, never the typed signum (src/scan_sources.identify)
    entry = mesh_cache.peek(req.mesh_id) if req.mesh_id else None
    facts = stone_report.build_facts(req.model_dump(), store().get, entry.info if entry is not None else None)
    facts["geology"] = site_geology(facts["rundata"])
    from src import stone_dimensions
    if facts.get("rundata"):
        sg = facts["rundata"]["signum"]
        dims = stone_dimensions.lookup(sg)
        facts["dimensions"] = {**dims, "in_province": stone_dimensions.province_percentile(sg, lambda s: s.split(" ")[0])} if dims else None
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
    # The probability model's reading of the inscription (src/textmodel.py, METHODS.md 8.1): cached per stone, so
    # only the first report for a stone computes it. The scanner's trace proposals are shown as what the scan sees
    # and are never counted into the reading without the user confirming them in the panel.
    facts["textmodel"] = None
    facts["scan_traces"] = None
    if facts.get("rundata"):
        try:
            from src import textmodel
            res = textmodel.analyze(facts["rundata"]["signum"])
            facts["textmodel"] = res if res.get("available") else None
        except Exception as e:
            logger.warning("Sannolikhetsmodellen kunde inte läsa stenen för rapporten: %r", e)
        if facts["textmodel"]:
            try:
                from src import trace_reader
                tr = trace_reader.proposals(facts["rundata"]["signum"])
                facts["scan_traces"] = tr if tr.get("available") else None
            except Exception as e:
                logger.warning("Spårläsaren misslyckades för rapporten: %r", e)

    rd = req.reading or {}
    if rd.get("transliteration"):
        facts["reading_validation"] = rd.get("validation") or validate_reading(
            rd["transliteration"], facts["rundata"], store().inscriptions, rd.get("others") or [])

    surface, surface_note = None, None
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
            lims, warns = stone_report.report_limitations(facts, True)
            known = warns + [x["short"] for x in lims]
            if req.template == "stenrapport":
                ai = ai_sections(aictx, stone_report.facts_text(facts), known)
            else:
                spec = report_templates.ai_request(req.template, req.template_options, stone_report.facts_text(facts), known)
                if spec:
                    ai = _as_object(llm.generate(aictx, spec[0], schema=spec[1], tier="pro").data)
            ai_used = bool(ai)
        except Exception as e:
            logger.warning("AI-text för stenrapporten misslyckades: %r", e)

    blocks = stone_report.build_document(facts, req.author, req.institution, ai, surface, req.title)
    blocks = i18n.translate_blocks(report_templates.apply(req.template, blocks, facts, ai, req.template_options), req.lang)
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
