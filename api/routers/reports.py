"""Akademisk rapport ur mätkorpusen (Word, LaTeX, Markdown, HTML)."""
import json
import os
from typing import Literal, Optional

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import Response
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from api.config import GEMINI_PRO_MODEL
from api.errors import logger
from api.rundata import store
from src import academic

router = APIRouter()


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


def ai_sections(api_key: str, facts_text: str) -> dict:
    client = genai.Client(api_key=api_key)
    prompt = f"""
Du skriver delar av en vetenskaplig rapport på svenska om huggteknik på runstenar.
Använd ENDAST fakta nedan. Hitta inte på stenar, ristare, siffror, litteratur eller slutsatser som inte följer
av fakta. Var försiktig: få stenar ger osäkra slutsatser. Skriv i akademisk, saklig ton utan överdrifter.

FAKTA:
{facts_text}

Svara med JSON:
{{"abstract": "4–6 meningar", "introduction": "1–2 stycken om syfte och material", "discussion": "2–3 stycken: vad resultaten visar, hur säkra de är och vad som behövs härnäst"}}
"""
    resp = client.models.generate_content(
        model=GEMINI_PRO_MODEL, contents=prompt,
        config=types.GenerateContentConfig(temperature=0.2, response_mime_type="application/json"))
    return json.loads(resp.text)


@router.post("/academic")
def academic_report(req: AcademicRequest, x_gemini_api_key: Optional[str] = Header(None, alias="X-Gemini-Api-Key")):
    if not req.entries:
        raise HTTPException(status_code=400, detail="Urvalet innehåller inga mätningar.")
    if len(req.entries) > 500:
        raise HTTPException(status_code=400, detail="Högst 500 stenar per rapport.")
    facts = academic.build_facts(req.entries, store().get, req.scope.model_dump())

    ai, ai_used = None, False
    api_key = x_gemini_api_key or os.environ.get("GEMINI_API_KEY")
    if req.use_ai and req.ai_text:
        ai, ai_used = req.ai_text, True
    elif req.use_ai and api_key:
        try:
            ai = ai_sections(api_key, academic.facts_text(facts))
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
