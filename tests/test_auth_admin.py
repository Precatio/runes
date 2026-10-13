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


def test_crosscheck_does_not_repeat_reasons():
    """The findings are cached; applying the check against newer sources again must not add the same text again."""
    from src import crosscheck
    finding = {"verdict": "nytt", "evidence": 0.5, "novelty": 0.8, "relevance": 0.8, "score": 0.32,
               "reasons": {"belägg": [], "nyhet": ["Axelson (1993) attribuerade inte stenen"], "relevans": []}}
    cc = {"status": "saknas", "runor": {"text": "Runor 2020 anger ingen ristare.", "references": []}}
    for _ in range(5):
        out = crosscheck.apply(finding, cc)
    assert out["reasons"]["nyhet"] == ["Axelson (1993) attribuerade inte stenen", "Runor 2020 anger ingen ristare."]
    assert finding["reasons"]["nyhet"] == ["Axelson (1993) attribuerade inte stenen"]


def test_github_stats_merge_days_and_token_from_env_file(tmp_path, monkeypatch):
    from src import github_stats as gs
    h = gs.merge({"days": {"2026-10-01": {"clones": 1, "clones_uniques": 1}}},
                 {"clones": [{"timestamp": "2026-10-01T00:00:00Z", "count": 3, "uniques": 2},
                             {"timestamp": "2026-10-02T00:00:00Z", "count": 5, "uniques": 4}]},
                 {"views": [{"timestamp": "2026-10-02T00:00:00Z", "count": 9, "uniques": 6}]})
    assert h["days"]["2026-10-01"] == {"clones": 3, "clones_uniques": 2}          # the newest numbers for the day
    assert h["days"]["2026-10-02"] == {"clones": 5, "clones_uniques": 4, "views": 9, "views_uniques": 6}
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setattr(gs, "ROOT", str(tmp_path))
    assert gs.token() == ""
    (tmp_path / ".env").write_text('ADMIN_UIDS=x\nGITHUB_TOKEN="github_pat_abc123"\n')
    assert gs.token() == "github_pat_abc123"


def test_github_stats_need_admin():
    from fastapi.testclient import TestClient
    from api.main import app
    assert TestClient(app).get("/api/admin/github").status_code in (401, 403)
