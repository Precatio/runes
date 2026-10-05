import os

# Tests must not depend on SGU's map service; geology is tested separately with a mocked lookup
os.environ.setdefault("GEOLOGY_DISABLED", "1")
# R analyses take minutes and need R installed; tests/test_r.py enables them explicitly
os.environ.setdefault("R_DISABLED", "1")

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _no_real_ai_calls(monkeypatch):
    # Tests never call a real language model, even if a key is present in .env
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("AI_PROVIDER", "claude")
