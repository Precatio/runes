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


# One rule for every test that runs R (tests/test_r.py, tests/test_question.py): mark it `needs_r`. It is skipped when
# src/r_bridge.rscript() finds no Rscript, so `RSCRIPT= pytest` simulates a machine without R also where R is
# installed. A test marked `slow_r` (a corpus run of many minutes) is also skipped in CI (the CI variable that GitHub
# Actions sets) unless R_SLOW_TESTS=1, so that it cannot run into the job's time limit if a runner has R.
def pytest_configure(config):
    config.addinivalue_line("markers", "needs_r: runs R; skipped when Rscript is missing or RSCRIPT is empty")
    config.addinivalue_line("markers", "slow_r: an R run of many minutes; also skipped in CI unless R_SLOW_TESTS=1")


def pytest_runtest_setup(item):
    if item.get_closest_marker("needs_r") or item.get_closest_marker("slow_r"):
        from src import r_bridge
        if r_bridge.rscript() is None:
            pytest.skip("R är inte installerat (Rscript saknas eller RSCRIPT är tom)")
    if item.get_closest_marker("slow_r") and os.environ.get("CI") and os.environ.get("R_SLOW_TESTS") != "1":
        pytest.skip("lång R-körning; körs i CI bara med R_SLOW_TESTS=1")


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
