"""Publishing without the founder's computer: the website export and the Bluesky queue in GitHub Actions
(scripts/ci_publicera.py, scripts/ci_bluesky.py, .github/workflows/publicera.yml and bluesky.yml) and the switch that
keeps the local app from posting the queue as well (scripts/bluesky_post.local_posting)."""
from __future__ import annotations

import datetime as dt
import json
import os
import re

import pytest

from scripts import bluesky_post as bp
from scripts import ci_bluesky as cb
from scripts import ci_publicera as cp

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UTC = dt.timezone.utc


# ---- the requirements subset ---------------------------------------------------------------------------------------

def _entries(path: str) -> dict[str, str]:
    """Package → its whole entry (the pinned line and its hashes), comments left out."""
    out, cur = {}, None
    for line in open(path, encoding="utf-8").read().splitlines():
        m = re.match(r"^([A-Za-z0-9_.\-]+)==", line)
        if m:
            cur = m.group(1).lower().replace("_", "-")
            out[cur] = line
        elif cur and line.startswith("    --hash"):
            out[cur] += "\n" + line
        else:
            cur = None
    return out


def test_publish_requirements_are_copied_from_the_lock():
    sub = _entries(os.path.join(ROOT, "requirements-publicera.txt"))
    lock = _entries(os.path.join(ROOT, "requirements.lock"))
    assert {"fastapi", "firebase-admin", "pillow", "requests", "python-dotenv"} <= set(sub)
    for name, entry in sub.items():
        assert lock.get(name) == entry, f"{name} differs from requirements.lock"


# ---- the website export ----------------------------------------------------------------------------------------------

def test_no_credentials_is_a_quiet_success(monkeypatch, capsys):
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
    assert cp.main([]) == 0
    assert "inte aktiverad" in capsys.readouterr().out


def test_views_are_read_once_a_day_swedish_time():
    assert cp.views_due(dt.datetime(2026, 11, 11, 4, 7, tzinfo=UTC))      # 05:07 in winter
    assert not cp.views_due(dt.datetime(2026, 11, 11, 4, 37, tzinfo=UTC))  # the second run of that hour
    assert cp.views_due(dt.datetime(2026, 7, 1, 3, 7, tzinfo=UTC))         # 05:07 in summer
    assert not cp.views_due(dt.datetime(2026, 7, 1, 4, 7, tzinfo=UTC))


class FakeExport:
    def __init__(self, fresh):
        self.fresh, self.read = fresh, 0

    def article_views(self):
        self.read += 1
        return self.fresh

    def previous_views(self):
        return {"a": 10, "b": 5}

    from src.site_export import views_moved  # the real rule
    views_moved = staticmethod(views_moved)


def test_views_outside_the_hour_are_the_previous_ones():
    se = FakeExport({"a": 1, "b": 99})
    old = [{"slug": "a", "views": 10}, {"slug": "b", "views": 5}]
    assert cp.choose_views(se, dt.datetime(2026, 11, 11, 12, 7, tzinfo=UTC), old) == {"a": 10, "b": 5}
    assert se.read == 0  # site_views is not read at all


def test_views_in_the_hour_only_when_the_order_moved():
    old = [{"slug": "a", "views": 10}, {"slug": "b", "views": 5}]
    morning = dt.datetime(2026, 11, 11, 4, 7, tzinfo=UTC)
    assert cp.choose_views(FakeExport({"a": 11, "b": 6}), morning, old) == {"a": 10, "b": 5}
    assert cp.choose_views(FakeExport({"a": 11, "b": 30}), morning, old) == {"a": 11, "b": 30}


def test_only_the_timestamp_changed_keeps_the_old_file(tmp_path):
    path = tmp_path / "articles.json"
    before = json.dumps({"exported_at": "2026-11-11T10:00:00+00:00", "posts": [{"slug": "a"}]}).encode()
    path.write_text(json.dumps({"exported_at": "2026-11-11T10:30:00+00:00", "posts": [{"slug": "a"}]}))
    assert cp.keep_timestamp_if_unchanged(str(path), before) is False
    assert path.read_bytes() == before
    path.write_text(json.dumps({"exported_at": "2026-11-11T11:00:00+00:00", "posts": [{"slug": "a"}, {"slug": "b"}]}))
    assert cp.keep_timestamp_if_unchanged(str(path), before) is True


def test_changes_between_exports():
    old = [{"slug": "a", "title": "A"}, {"slug": "b"}]
    new = [{"slug": "a", "title": "A2"}, {"slug": "c"}]
    assert cp.changes(old, new) == {"nya": ["c"], "borttagna": ["b"], "ändrade": ["a"]}


def test_commons_decisions_of_the_previous_export_are_kept():
    from src import commons
    wide = "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Sten_1.jpg/960px-Sten_1.jpg"
    kept = "https://upload.wikimedia.org/wikipedia/commons/c/cd/Liten.png"
    old = [{"body": f"![x]({wide})\n\n![y]({kept})\n"}]
    known = cp.known_photo_sizes(old, commons)
    original = "https://upload.wikimedia.org/wikipedia/commons/a/ab/Sten_1.jpg"
    assert commons.site_photo(original, known) == wide
    assert commons.site_photo(kept, known) == kept


# ---- Bluesky ---------------------------------------------------------------------------------------------------------

def _queue(*items):
    return {"items": [{"slug": "s", "text": "t", "tags": [], **i} for i in items]}


EVENING = dt.datetime(2026, 11, 11, 17, 7, tzinfo=UTC)  # 18:07 in Stockholm (winter)


def test_bluesky_needs_secrets_and_the_switch():
    q = _queue({"date": "2026-11-11"})
    assert cb.decide(EVENING, q, "ci", False)[1] is None
    what, item = cb.decide(EVENING, q, "lokal", True)
    assert item is None and "lokala appen" in what
    assert cb.decide(EVENING, q, "ci", True)[0] == "post"


def test_bluesky_not_before_six_swedish_time_summer_and_winter():
    q = _queue({"date": "2026-07-01"})
    assert cb.decide(dt.datetime(2026, 7, 1, 15, 7, tzinfo=UTC), q, "ci", True)[1] is None  # 17:07 CEST
    assert cb.decide(dt.datetime(2026, 7, 1, 16, 7, tzinfo=UTC), q, "ci", True)[0] == "post"  # 18:07 CEST
    q = _queue({"date": "2026-11-11"})
    assert cb.decide(dt.datetime(2026, 11, 11, 16, 7, tzinfo=UTC), q, "ci", True)[1] is None  # 17:07 CET


def test_bluesky_at_most_one_a_day_and_the_earliest_due():
    posted = {"date": "2026-11-10", "posted": "https://bsky.app/x", "posted_at": "2026-11-11T17:05:00+00:00"}
    assert cb.decide(EVENING, _queue(posted, {"date": "2026-11-11"}), "ci", True)[1] is None
    # yesterday evening in Sweden is not today
    late = {**posted, "posted_at": "2026-11-10T22:30:00+00:00"}
    assert cb.decide(EVENING, _queue(late, {"date": "2026-11-11"}), "ci", True)[0] == "post"
    q = _queue({"date": "2026-11-12", "slug": "later"}, {"date": "2026-11-09", "slug": "first"}, {"date": "2026-11-10", "slug": "second"})
    assert cb.decide(EVENING, q, "ci", True)[1]["slug"] == "first"
    too_long = {"date": "2026-11-01", "slug": "long", "text": "x" * 301}
    assert cb.decide(EVENING, _queue(too_long, {"date": "2026-11-11", "slug": "ok"}), "ci", True)[1]["slug"] == "ok"


def test_the_switch_file_and_the_local_thread(tmp_path, monkeypatch):
    switch = tmp_path / "postning.json"
    monkeypatch.setattr(bp, "SWITCH", str(switch))
    monkeypatch.delenv("BLUESKY_LOCAL", raising=False)
    assert bp.posting_place() == "lokal" and bp.local_posting()  # no file: as before
    switch.write_text(json.dumps({"postar": "ci"}))
    assert bp.posting_place() == "ci" and not bp.local_posting()
    switch.write_text(json.dumps({"postar": "lokal"}))
    monkeypatch.setenv("BLUESKY_LOCAL", "0")
    assert not bp.local_posting()
    switch.write_text("not json")
    monkeypatch.delenv("BLUESKY_LOCAL")
    assert bp.posting_place() == "lokal"


def test_the_committed_switch_keeps_local_posting():
    assert json.load(open(os.path.join(ROOT, "data", "bluesky", "postning.json"), encoding="utf-8"))["postar"] == "lokal"


def test_articles_from_the_website_export(tmp_path, monkeypatch):
    site = tmp_path / "articles.json"
    site.write_text(json.dumps({"posts": [{"slug": "a", "title": "A", "title_en": "A en", "summary_en": "S",
                                           "body_en": "B", "labels": ["Rapport"]}]}))
    monkeypatch.setattr(bp, "SITE_ARTICLES", str(site))
    monkeypatch.setenv("BLUESKY_ARTICLES", "site")
    url, title, desc = bp.card("a", True)
    assert url == "https://vitkirunor.se/en/forskningsrapporter/a/?via=bluesky" and title == "A en" and desc == "S"
    with pytest.raises(SystemExit):
        bp.article("not-live")


def test_ci_bluesky_does_nothing_without_secrets(monkeypatch, capsys):
    monkeypatch.delenv("BLUESKY_HANDLE", raising=False)
    monkeypatch.delenv("BLUESKY_APP_PASSWORD", raising=False)
    monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
    monkeypatch.setenv("BLUESKY_ARTICLES", "site")  # main sets it for the process; restored after the test
    tz = os.environ.get("TZ")
    try:
        assert cb.main([]) == 0
    finally:  # main sets Swedish time for the process
        if tz is None:
            os.environ.pop("TZ", None)
        else:
            os.environ["TZ"] = tz
        import time
        time.tzset()
    assert "inte aktiverad" in capsys.readouterr().out
