import os

# Tests must not depend on SGU's map service; geology is tested separately with a mocked lookup
os.environ.setdefault("GEOLOGY_DISABLED", "1")
# R analyses take minutes and need R installed; tests/test_r.py enables them explicitly
os.environ.setdefault("R_DISABLED", "1")
# The background warm-up at server start is not needed in tests
os.environ.setdefault("WARM_CACHES", "0")
os.environ.setdefault("R_AUTORUN", "0")  # no R corpus run started by the server in a test
os.environ.setdefault("SITE_PUBLISH", "0")  # never push the public website from a test

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _no_real_ai_calls(monkeypatch):
    # Tests never call a real language model, even if a key is present in .env
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("AI_PROVIDER", "claude")


@pytest.fixture(autouse=True)
def _website_export_in_a_temporary_folder(tmp_path_factory, monkeypatch):
    # The website export (src/site_export.py) never writes the real web/content, web/public/artiklar-sok.json,
    # web/public/figurer or data/cache from a test, never reads the live page views and never asks Commons; article
    # backups (api/routers/blog.py) go to the temporary folder too
    from api.routers import blog
    from src import site_export
    d = tmp_path_factory.mktemp("site")
    monkeypatch.setattr(site_export, "CONTENT", str(d / "content" / "articles.json"))
    monkeypatch.setattr(site_export, "SEARCH", str(d / "public" / "artiklar-sok.json"))
    monkeypatch.setattr(site_export, "FIGURES", str(d / "public" / "figurer"))
    monkeypatch.setattr(site_export, "STATUS", str(d / "cache" / "site_publish.json"))
    monkeypatch.setattr(site_export, "PENDING", str(d / "cache" / "site_publish_pending.json"))
    monkeypatch.setattr(site_export, "article_views", lambda: {})
    monkeypatch.setattr(site_export, "_photo_sizes", lambda urls: {})
    monkeypatch.setattr(blog, "BACKUP", str(d / "backup" / "posts"))
