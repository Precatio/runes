"""Gemensamt lager för språkmodeller: Claude (Anthropic, standard) eller Gemini (Google).

Varje anrop anger text, eventuella bilder och – för strukturerade svar – ett schema (en Pydantic-modell
eller ett JSON-schema). Claude får schemat som strukturerat svarsformat (output_config.format), så att svaret
alltid är giltig JSON enligt schemat; Gemini får det som response_schema.

Leverantör och nyckel kommer från webbläsaren (X-AI-Provider, X-Anthropic-Api-Key, X-Gemini-Api-Key): varje
användare använder sin egen nyckel. Serverns egna nycklar (miljövariablerna ANTHROPIC_API_KEY och GEMINI_API_KEY)
används bara om ALLOW_SERVER_AI_KEYS=1 är satt – för lokal utveckling och skript, aldrig på en publik server, där
alla användare annars skulle köra på serverägarens nyckel.
"""
from __future__ import annotations

import base64
import io
import json
import os
import re
from dataclasses import dataclass, field
from typing import Any, Optional

from fastapi import Header, HTTPException

from api.config import CLAUDE_FAST_MODEL, CLAUDE_PRO_MODEL, GEMINI_FLASH_MODEL, GEMINI_PRO_MODEL

PROVIDERS = ("claude", "gemini")
LABEL = {"claude": "Claude (Anthropic)", "gemini": "Gemini (Google)"}


@dataclass
class AIContext:
    provider: str
    key: str


@dataclass
class Message:
    role: str  # "user" | "assistant"
    text: str
    images: list[tuple[bytes, str]] = field(default_factory=list)  # (data, mime type)


@dataclass
class Result:
    text: str
    data: Any
    tokens: int
    model: str
    provider: str


def ai_context(
    x_ai_provider: Optional[str] = Header(None, alias="X-AI-Provider"),
    x_anthropic_api_key: Optional[str] = Header(None, alias="X-Anthropic-Api-Key"),
    x_gemini_api_key: Optional[str] = Header(None, alias="X-Gemini-Api-Key"),
) -> AIContext:
    """FastAPI-beroende: vilken modell och nyckel anropet ska använda."""
    server = os.environ.get("ALLOW_SERVER_AI_KEYS") == "1"
    keys = {"claude": x_anthropic_api_key or (os.environ.get("ANTHROPIC_API_KEY", "") if server else ""),
            "gemini": x_gemini_api_key or (os.environ.get("GEMINI_API_KEY", "") if server else "")}
    provider = (x_ai_provider or os.environ.get("AI_PROVIDER") or "").lower()
    if provider not in PROVIDERS:
        provider = "claude" if keys["claude"] else "gemini"
    return AIContext(provider, keys[provider])


def available(ctx: AIContext) -> bool:
    return bool(ctx.key)


def require(ctx: AIContext):
    if not ctx.key:
        where = "console.anthropic.com" if ctx.provider == "claude" else "aistudio.google.com"
        raise HTTPException(status_code=401, detail=(
            f"Ingen API-nyckel för {LABEL[ctx.provider]}. Skapa en på {where} och lägg in den under Inställningar."))


# ---- schemas -------------------------------------------------------------------------------

def _json_schema(schema) -> dict:
    s = schema.model_json_schema() if hasattr(schema, "model_json_schema") else dict(schema)
    defs = s.pop("$defs", {})

    def inline(node):
        if isinstance(node, dict):
            if "$ref" in node:
                return inline(defs[node["$ref"].split("/")[-1]])
            # Drop schema titles (strings), never a property that happens to be called "title"
            return {k: inline(v) for k, v in node.items() if not (k == "title" and isinstance(v, str))}
        if isinstance(node, list):
            return [inline(x) for x in node]
        return node
    return inline(s)


def _parse_json(text: str):
    t = text.strip()
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t)
    try:
        return json.loads(t)
    except ValueError:
        m = re.search(r"\{.*\}|\[.*\]", t, re.S)
        if m:
            return json.loads(m.group(0))
        raise


# ---- providers -----------------------------------------------------------------------------

CLAUDE_MAX_IMAGE_BYTES = 5 * 1024 * 1024  # the API rejects larger images
CLAUDE_MAX_IMAGE_EDGE = 2576               # larger images are scaled down by the API anyway
CLAUDE_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}


def _fit_image(data: bytes, mime: str | None) -> tuple[bytes, str]:
    """Bilden som Claude tar emot: för stora eller okända format skalas om till JPEG. Markörernas
    koordinater är normaliserade (0–1000), så omskalningen påverkar dem inte."""
    mime = (mime or "image/jpeg").lower()
    if len(data) <= CLAUDE_MAX_IMAGE_BYTES and mime in CLAUDE_IMAGE_TYPES:
        try:
            from PIL import Image
            with Image.open(io.BytesIO(data)) as im:
                if max(im.size) <= CLAUDE_MAX_IMAGE_EDGE:
                    return data, mime
        except Exception:
            return data, mime
    from PIL import Image, ImageOps
    with Image.open(io.BytesIO(data)) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
        im.thumbnail((CLAUDE_MAX_IMAGE_EDGE, CLAUDE_MAX_IMAGE_EDGE))
        out = io.BytesIO()
        im.save(out, "JPEG", quality=88)
    return out.getvalue(), "image/jpeg"


def _claude(ctx, messages, system, schema, json_mode, tier, max_tokens) -> Result:
    import anthropic

    client = anthropic.Anthropic(api_key=ctx.key, timeout=600, max_retries=2)
    model = CLAUDE_PRO_MODEL if tier == "pro" else CLAUDE_FAST_MODEL
    content = []
    for m in messages:
        images = [_fit_image(data, mime) for data, mime in m.images]
        blocks = [{"type": "image", "source": {"type": "base64", "media_type": mime,
                                               "data": base64.b64encode(data).decode()}} for data, mime in images]
        blocks.append({"type": "text", "text": m.text or " "})
        content.append({"role": m.role, "content": blocks})
    # Current models think before answering and the thinking counts against max_tokens; leave room for both
    kwargs: dict = {"model": model, "max_tokens": max(max_tokens, 16000), "messages": content}
    if system:
        kwargs["system"] = system
    if schema is not None:
        # Structured outputs: the answer is guaranteed to follow the schema. (Forcing a tool call with
        # tool_choice is rejected by Claude Opus 5.5 and later.)
        kwargs["output_config"] = {"format": {"type": "json_schema",
                                              "schema": anthropic.transform_schema(_json_schema(schema))}}
    with client.messages.stream(**kwargs) as stream:
        resp = stream.get_final_message()
    tokens = (resp.usage.input_tokens or 0) + (resp.usage.output_tokens or 0)
    text = "".join(b.text for b in resp.content if b.type == "text")
    if resp.stop_reason == "refusal":
        raise RuntimeError("Claude avböjde att svara på förfrågan.")
    if resp.stop_reason == "max_tokens" and (schema is not None or json_mode):
        raise RuntimeError("Svaret från Claude blev avklippt (för långt). Försök igen eller korta ned underlaget.")
    data = _parse_json(text) if (schema is not None or json_mode) else None
    return Result(text, data, tokens, model, "claude")


def _gemini(ctx, messages, system, schema, json_mode, tier, max_tokens, temperature) -> Result:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=ctx.key)
    model = GEMINI_PRO_MODEL if tier == "pro" else GEMINI_FLASH_MODEL
    contents = []
    for m in messages:
        parts = [types.Part.from_bytes(data=data, mime_type=mime or "image/jpeg") for data, mime in m.images]
        parts.append(types.Part.from_text(text=m.text or " "))
        contents.append(types.Content(role="user" if m.role == "user" else "model", parts=parts))
    cfg: dict = {"temperature": temperature}
    if system:
        cfg["system_instruction"] = system
    if schema is not None or json_mode:
        cfg["response_mime_type"] = "application/json"
    if schema is not None and hasattr(schema, "model_json_schema"):
        # Gemini's schema dialect lacks parts of JSON Schema; plain dict schemas use JSON mode instead
        cfg["response_schema"] = schema
    resp = client.models.generate_content(model=model, contents=contents, config=types.GenerateContentConfig(**cfg))
    text = resp.text or ""
    tokens = resp.usage_metadata.total_token_count if getattr(resp, "usage_metadata", None) else 0
    data = _parse_json(text) if (schema is not None or json_mode) else None
    return Result(text, data, tokens, model, "gemini")


def generate(ctx: AIContext, prompt: str = "", *, system: str | None = None,
             images: list[tuple[bytes, str]] | None = None, messages: list[Message] | None = None,
             schema=None, json_mode: bool = False, tier: str = "pro", temperature: float = 0.2,
             max_tokens: int = 8192) -> Result:
    """Ett anrop till vald språkmodell. `messages` ersätter `prompt`/`images` för samtal i flera steg.
    Med `schema` (Pydantic-modell eller JSON-schema) returneras `data` som tolkad JSON."""
    require(ctx)
    msgs = messages or [Message("user", prompt, images or [])]
    for attempt in range(2):
        try:
            if ctx.provider == "claude":
                if schema is not None and not hasattr(schema, "model_json_schema") and "type" not in schema:
                    raise ValueError("Schemat saknar typ.")
                return _claude(ctx, msgs, system, schema, json_mode, tier, max_tokens)
            return _gemini(ctx, msgs, system, schema, json_mode, tier, max_tokens, temperature)
        except Exception as e:
            # Long answers are sometimes cut off by the server; one retry
            if attempt == 0 and ("disconnected" in str(e).lower() or "overloaded" in str(e).lower()):
                continue
            raise
    raise RuntimeError("unreachable")
