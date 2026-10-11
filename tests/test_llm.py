"""The shared language-model layer: provider choice, Claude structured outputs, images."""
import types as pytypes

import pytest
from pydantic import BaseModel

from api import llm


class Answer(BaseModel):
    style: str
    confidence: int


def fake_anthropic(monkeypatch, captured, content, stop_reason="end_turn"):
    class Stream:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def get_final_message(self):
            return pytypes.SimpleNamespace(content=content, stop_reason=stop_reason,
                                           usage=pytypes.SimpleNamespace(input_tokens=10, output_tokens=5))

    class Messages:
        def stream(self, **kw):
            captured.update(kw)
            return Stream()

    class Client:
        def __init__(self, **kw):
            captured["client"] = kw
            self.messages = Messages()

    import anthropic
    monkeypatch.setattr(anthropic, "Anthropic", Client)


def test_provider_choice():
    assert llm.ai_context("claude", "sk-ant", None).provider == "claude"
    assert llm.ai_context("gemini", None, "AIza").key == "AIza"
    with pytest.raises(Exception):
        llm.require(llm.AIContext("claude", ""))


def test_claude_structured_answer(monkeypatch):
    captured = {}
    text = pytypes.SimpleNamespace(type="text", text='{"style": "RAK", "confidence": 80}')
    fake_anthropic(monkeypatch, captured, [text])
    ctx = llm.AIContext("claude", "sk-ant-test")
    r = llm.generate(ctx, "Bedöm stilen.", system="Du är runolog.", images=[(b"\x89PNG", "image/png")], schema=Answer)
    assert r.data == {"style": "RAK", "confidence": 80} and r.tokens == 15 and r.provider == "claude"
    # Forced tool choice is rejected by Claude Opus 5.5; the schema goes in output_config instead
    assert "tool_choice" not in captured and "tools" not in captured
    fmt = captured["output_config"]["format"]
    schema = fmt["schema"]
    assert fmt["type"] == "json_schema" and schema["type"] == "object" and "$defs" not in schema
    assert schema["additionalProperties"] is False and set(schema["required"]) == {"style", "confidence"}
    blocks = captured["messages"][0]["content"]
    assert blocks[0]["type"] == "image" and blocks[0]["source"]["media_type"] == "image/png"
    assert captured["system"] == "Du är runolog." and captured["model"] == llm.CLAUDE_PRO_MODEL


def test_claude_text_and_json(monkeypatch):
    captured = {}
    fake_anthropic(monkeypatch, captured, [pytypes.SimpleNamespace(type="text", text='```json\n{"a": 1}\n```')])
    r = llm.generate(llm.AIContext("claude", "k"), "x", json_mode=True, tier="fast")
    assert r.data == {"a": 1} and captured["model"] == llm.CLAUDE_FAST_MODEL


def test_claude_truncated_or_refused_answer_is_an_error(monkeypatch):
    for reason in ("max_tokens", "refusal"):
        fake_anthropic(monkeypatch, {}, [pytypes.SimpleNamespace(type="text", text='{"style": "RA')], stop_reason=reason)
        with pytest.raises(RuntimeError):
            llm.generate(llm.AIContext("claude", "k"), "x", schema=Answer)


def test_large_or_unusual_images_are_fitted_for_claude():
    import io
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (4000, 1000), "gray").save(buf, "TIFF")
    data, mime = llm._fit_image(buf.getvalue(), "image/tiff")
    assert mime == "image/jpeg" and max(Image.open(io.BytesIO(data)).size) == llm.CLAUDE_MAX_IMAGE_EDGE
    small = io.BytesIO()
    Image.new("RGB", (800, 600), "gray").save(small, "PNG")
    assert llm._fit_image(small.getvalue(), "image/png") == (small.getvalue(), "image/png")
