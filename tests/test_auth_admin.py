"""Inloggning, roller, rapporter som bara är för grundaren, admin och att serverns AI-nycklar inte delas ut."""
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from api import auth, llm
from api.main import app

client = TestClient(app)
FOUNDER = {"uid": "founder-uid", "email": "founder@example.org", "email_verified": True}
RESEARCHER = {"uid": "other-uid", "email": "researcher@example.org", "email_verified": True}


@pytest.fixture(autouse=True)
def tokens(monkeypatch):
    """Two accounts; 'Bearer founder' and 'Bearer other' stand in for real Firebase ID tokens."""
    monkeypatch.setenv("ADMIN_EMAILS", "founder@example.org")
    monkeypatch.delenv("ADMIN_UIDS", raising=False)

    def verify(token):
        claims = {"founder": FOUNDER, "other": RESEARCHER}.get(token)
        if claims is None:
            raise HTTPException(status_code=401, detail="Ogiltig inloggning.")
        return {**claims, "admin": auth.is_admin(claims)}
    monkeypatch.setattr(auth, "verify", verify)


def bearer(name):
    return {"Authorization": f"Bearer {name}"}


def test_me_and_roles():
    assert client.get("/api/me").json() == {"signed_in": False, "admin": False}
    assert client.get("/api/me", headers=bearer("other")).json()["admin"] is False
    me = client.get("/api/me", headers=bearer("founder")).json()
    assert me["signed_in"] and me["admin"] and me["uid"] == "founder-uid"
    assert client.get("/api/me", headers=bearer("forged")).status_code == 401


def test_unverified_email_is_not_admin(monkeypatch):
    assert not auth.is_admin({**FOUNDER, "email_verified": False})
    monkeypatch.setenv("ADMIN_UIDS", "other-uid")
    assert auth.is_admin(RESEARCHER)


def test_report_forms_only_full_stone_report_for_others():
    others = [t["key"] for t in client.get("/api/reports/templates", headers=bearer("other")).json()["templates"]]
    anonymous = [t["key"] for t in client.get("/api/reports/templates").json()["templates"]]
    founder = [t["key"] for t in client.get("/api/reports/templates", headers=bearer("founder")).json()["templates"]]
    assert others == anonymous == ["stenrapport"]
    assert "tidskrift" in founder and len(founder) > 1

    journal = {"template": "tidskrift", "analyses": []}
    assert client.post("/api/reports/stone", json=journal, headers=bearer("other")).status_code == 403
    # The founder gets past the check (and then stops on the missing measurements)
    assert client.post("/api/reports/stone", json=journal, headers=bearer("founder")).status_code == 400
    # The full stone report is open to everyone (here it stops on the missing measurements, not on the role)
    assert client.post("/api/reports/stone", json={"template": "stenrapport", "analyses": []}).status_code == 400


def test_corpus_report_and_admin_only_for_founder():
    assert client.post("/api/reports/academic", json={"entries": []}, headers=bearer("other")).status_code == 403
    assert client.post("/api/reports/academic", json={"entries": []}).status_code == 403
    assert client.post("/api/reports/academic", json={"entries": []}, headers=bearer("founder")).status_code == 400
    for method, path in [("get", "/api/admin/users"), ("get", "/api/admin/messages"), ("post", "/api/admin/users/x/ban"),
                         ("post", "/api/admin/messages"), ("delete", "/api/admin/messages/x")]:
        assert getattr(client, method)(path, headers=bearer("other")).status_code in (403, 422), path
        assert getattr(client, method)(path).status_code in (403, 422), path


def test_founder_cannot_ban_self():
    r = client.post("/api/admin/users/founder-uid/ban", json={"reason": ""}, headers=bearer("founder"))
    assert r.status_code == 400


def test_server_ai_keys_are_not_shared(monkeypatch):
    """On a public server the owner's keys in the environment must never be used for visitors."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-owner")
    monkeypatch.setenv("GEMINI_API_KEY", "AIza-owner")
    monkeypatch.delenv("ALLOW_SERVER_AI_KEYS", raising=False)
    assert llm.ai_context("claude", None, None).key == ""
    assert llm.ai_context("gemini", None, None).key == ""
    assert llm.ai_context("claude", "sk-ant-visitor", None).key == "sk-ant-visitor"
    monkeypatch.setenv("ALLOW_SERVER_AI_KEYS", "1")  # local development and scripts only
    assert llm.ai_context("claude", None, None).key == "sk-ant-owner"
