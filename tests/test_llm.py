"""The shared language-model layer: provider choice, Claude tool use for structured answers, images."""
import types as pytypes

import pytest
from pydantic import BaseModel

from api import llm


class Answer(BaseModel):
    style: str
    confidence: int


def fake_anthropic(monkeypatch, captured, content):
    class Messages:
        def create(self, **kw):
            captured.update(kw)
            return pytypes.SimpleNamespace(content=content, usage=pytypes.SimpleNamespace(input_tokens=10, output_tokens=5))

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


def test_claude_structured_answer_via_tool(monkeypatch):
    captured = {}
    tool = pytypes.SimpleNamespace(type="tool_use", input={"style": "RAK", "confidence": 80})
    fake_anthropic(monkeypatch, captured, [tool])
    ctx = llm.AIContext("claude", "sk-ant-test")
    r = llm.generate(ctx, "Bedöm stilen.", system="Du är runolog.", images=[(b"\x89PNG", "image/png")], schema=Answer)
    assert r.data == {"style": "RAK", "confidence": 80} and r.tokens == 15 and r.provider == "claude"
    assert captured["tool_choice"] == {"type": "tool", "name": "svar"}
    schema = captured["tools"][0]["input_schema"]
    assert schema["type"] == "object" and "$defs" not in schema and "title" not in schema
    blocks = captured["messages"][0]["content"]
    assert blocks[0]["type"] == "image" and blocks[0]["source"]["media_type"] == "image/png"
    assert captured["system"] == "Du är runolog." and captured["model"] == llm.CLAUDE_PRO_MODEL


def test_claude_text_and_json(monkeypatch):
    captured = {}
    fake_anthropic(monkeypatch, captured, [pytypes.SimpleNamespace(type="text", text='```json\n{"a": 1}\n```')])
    r = llm.generate(llm.AIContext("claude", "k"), "x", json_mode=True, tier="fast")
    assert r.data == {"a": 1} and captured["model"] == llm.CLAUDE_FAST_MODEL
