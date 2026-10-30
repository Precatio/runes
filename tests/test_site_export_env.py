"""Webbplatsens git-anrop ska inte ärva GITHUB_TOKEN/GH_TOKEN (gh:s hjälpprogram tar dem före nyckelringen; .env:s
token är den skrivskyddade statistik-token – src/site_export.git_env, 2026-10-30)."""
from src import site_export


def test_git_env_strips_token_variables(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "github_pat_x")
    monkeypatch.setenv("GH_TOKEN", "gho_x")
    monkeypatch.setenv("HOME", "/tmp/hem")
    env = site_export.git_env()
    assert "GITHUB_TOKEN" not in env and "GH_TOKEN" not in env
    assert env["HOME"] == "/tmp/hem"
