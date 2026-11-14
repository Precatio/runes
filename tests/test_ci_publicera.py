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


EVENING = dt.datetime(2026, 11, 13, 12, 7, tzinfo=UTC)  # 13:07 in Stockholm (winter), a Friday – a posting day


def test_bluesky_needs_secrets_and_the_switch():
    q = _queue({"date": "2026-11-13"})
    assert cb.decide(EVENING, q, "ci", False)[1] is None
    what, item = cb.decide(EVENING, q, "lokal", True)
    assert item is None and "lokala appen" in what
    assert cb.decide(EVENING, q, "ci", True)[0] == "post"


def test_bluesky_only_on_tuesdays_and_fridays_from_one_swedish_time_summer_and_winter():
    q = _queue({"date": "2026-07-03"})  # Friday 3 July 2026
    assert cb.decide(dt.datetime(2026, 7, 3, 10, 7, tzinfo=UTC), q, "ci", True)[1] is None  # 12:07 CEST
    assert cb.decide(dt.datetime(2026, 7, 3, 11, 7, tzinfo=UTC), q, "ci", True)[0] == "post"  # 13:07 CEST
    q = _queue({"date": "2026-11-13"})
    assert cb.decide(dt.datetime(2026, 11, 13, 11, 7, tzinfo=UTC), q, "ci", True)[1] is None  # 12:07 CET
    # not on the other days, whatever the hour
    q = _queue({"date": "2026-11-11"})
    for day in (9, 11, 12, 14, 15):  # Monday, Wednesday, Thursday, Saturday, Sunday
        what, item = cb.decide(dt.datetime(2026, 11, day, 12, 7, tzinfo=UTC), q, "ci", True)
        assert item is None and "tisdagar och fredagar" in what
    assert cb.decide(dt.datetime(2026, 11, 10, 12, 7, tzinfo=UTC), _queue({"date": "2026-11-10"}), "ci", True)[0] == "post"  # Tuesday


def test_bluesky_at_most_one_a_day_and_todays_article_first():
    posted = {"date": "2026-11-10", "posted": "https://bsky.app/x", "posted_at": "2026-11-13T12:05:00+00:00"}
    assert cb.decide(EVENING, _queue(posted, {"date": "2026-11-13"}), "ci", True)[1] is None
    # Tuesday evening in Sweden is not today
    late = {**posted, "posted_at": "2026-11-10T22:30:00+00:00"}
    assert cb.decide(EVENING, _queue(late, {"date": "2026-11-13"}), "ci", True)[0] == "post"
    # without a post dated today: the earliest due in list order
    q = _queue({"date": "2026-11-14", "slug": "later"}, {"date": "2026-11-09", "slug": "first"}, {"date": "2026-11-10", "slug": "second"})
    assert cb.decide(EVENING, q, "ci", True)[1]["slug"] == "first"
    # the day's article goes before an older backlog
    q = _queue({"date": "2026-11-09", "slug": "old"}, {"date": "2026-11-13", "slug": "today"})
    assert cb.decide(EVENING, q, "ci", True)[1]["slug"] == "today"
    too_long = {"date": "2026-11-01", "slug": "long", "text": "x" * 301}
    assert cb.decide(EVENING, _queue(too_long, {"date": "2026-11-12", "slug": "ok"}), "ci", True)[1]["slug"] == "ok"
    removed = {"date": "2026-11-13", "slug": "gone", "removed": True}
    assert cb.decide(EVENING, _queue(removed, {"date": "2026-11-12", "slug": "kept"}), "ci", True)[1]["slug"] == "kept"


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


def test_the_committed_switch_names_one_poster():
    assert json.load(open(os.path.join(ROOT, "data", "bluesky", "postning.json"), encoding="utf-8"))["postar"] in ("lokal", "ci")


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


# ---- Bluesky requests from /redaktion (Firestore bluesky_forfragningar → ko.json) -------------------------------------

class FakeDb:
    """Read-only Firestore with just the collections the CI merge reads; it has no way to write."""

    def __init__(self, collections):
        self.collections = collections

    def collection(self, name):
        docs = self.collections.get(name, {})

        class Snap:
            def __init__(self, i): self.id = i
            def to_dict(self): return dict(docs[self.id])

        class Col:
            def stream(self): return [Snap(i) for i in docs]
        return Col()


def _request(slug, datum, text="New article.", tags=("runestones", "VikingAge")):
    return {"slug": slug, "datum": datum, "text": text, "tags": list(tags), "en": True, "by": "editor",
            "created": dt.datetime(2026, 11, 16, 7, 3, tzinfo=UTC)}


LIVE = {"published": True, "publishedAt": "2026-11-17T06:00:00+00:00", "body_en": "Text"}


def test_merge_requests_uses_the_same_insertion_as_the_local_approval():
    from src import bluesky_queue as bq
    from api.routers import blog_week as bw
    assert bw.queue_bluesky is bq.queue_bluesky and bw.composed_length is bq.composed_length  # one shared rule
    ko = {"items": [{"date": "2026-11-10", "slug": "gammal", "posted": "https://bsky.app/x"},
                    {"date": "2026-11-17", "slug": "v2"}, {"date": "2026-11-18", "slug": "v3"}]}
    posts = [{"slug": "ny", **LIVE}, {"slug": "gammal", **LIVE}, {"slug": "utkast", "published": False, "body_en": "T"},
             {"slug": "svensk", **{**LIVE, "body_en": ""}}, {"slug": "lang", **LIVE}]
    handled = {}
    lines = bq.merge_requests(ko, [_request("ny", "2026-11-17"), _request("gammal", "2026-11-20"),
                                   _request("utkast", "2026-11-21"), _request("svensk", "2026-11-22"),
                                   _request("lang", "2026-11-23", text="x" * 300), _request("saknas", "2026-11-24")],
                              posts, handled, "2026-11-16T08:07:00+00:00")
    assert [i["slug"] for i in ko["items"]] == ["gammal", "ny", "v2", "v3"]       # before the day's other post
    assert ko["items"][1] == {"date": "2026-11-17", "slug": "ny", "en": True, "text": "New article.",
                              "tags": ["runestones", "VikingAge"]}
    assert handled["ny"]["utfall"] == "i kön 2026-11-17 kl. 13"
    assert handled["gammal"]["utfall"] == "stod redan i kön"                      # posted counts as queued
    assert "engelsk" in handled["svensk"]["utfall"] and "300" in handled["lang"]["utfall"]
    assert "utkast" not in handled and "saknas" not in handled                    # not scheduled (yet): waits
    assert len(lines) == 4
    # handled once: the same requests again change nothing, even when the row was struck from the queue meanwhile
    ko["items"] = [i for i in ko["items"] if i["slug"] != "ny"]
    assert bq.merge_requests(ko, [_request("ny", "2026-11-17")], posts, handled, "later") == []
    assert "ny" not in [i["slug"] for i in ko["items"]]


def test_ci_merges_the_requests_into_the_queue_files(tmp_path, monkeypatch):
    ko_path, handled_path = tmp_path / "ko.json", tmp_path / "webbforfragningar.json"
    ko_path.write_text(json.dumps({"_om": "kö", "items": [{"date": "2026-11-17", "slug": "annan"}]}))
    monkeypatch.setattr(cp, "KO", str(ko_path))
    monkeypatch.setattr(cp, "HANDLED", str(handled_path))
    db = FakeDb({cp.REQUESTS: {"ny": _request("ny", "2026-11-17"), "vantar": _request("vantar", "2026-11-20")}})
    posts = [{"slug": "ny", **LIVE}, {"slug": "vantar", "published": False}]
    now = dt.datetime(2026, 11, 16, 8, 7, tzinfo=UTC)
    assert cp.merge_bluesky_requests(posts, db, now) == ["ny: i kön 2026-11-17 kl. 13"]
    ko = json.loads(ko_path.read_text())
    assert ko["_om"] == "kö" and [i["slug"] for i in ko["items"]] == ["ny", "annan"]
    handled = json.loads(handled_path.read_text())
    assert handled["_om"] and set(handled["klara"]) == {"ny"}
    # the next run: nothing new, no file is touched
    ko_mtime, h_mtime = ko_path.stat().st_mtime_ns, handled_path.stat().st_mtime_ns
    assert cp.merge_bluesky_requests(posts, db, now) == []
    assert (ko_path.stat().st_mtime_ns, handled_path.stat().st_mtime_ns) == (ko_mtime, h_mtime)
    # once the waiting article is scheduled, its request goes in; the first one is not added twice
    posts[1] = {"slug": "vantar", **LIVE}
    assert cp.merge_bluesky_requests(posts, db, now) == ["vantar: i kön 2026-11-20 kl. 13"]
    assert [i["slug"] for i in json.loads(ko_path.read_text())["items"]] == ["ny", "annan", "vantar"]
    assert cp.merge_bluesky_requests(posts, FakeDb({}), now) == []                # no requests at all


def test_the_queue_files_are_committed_with_the_export():
    wf = open(os.path.join(ROOT, ".github", "workflows", "publicera.yml"), encoding="utf-8").read()
    assert "data/bluesky/ko.json" in wf and "data/bluesky/webbforfragningar.json" in wf
    assert "steps.push.outputs.site == 'true'" in wf
    # the handled-file must exist in the repository, or "git add -A -- <path>" fails the job
    handled = json.load(open(cp.HANDLED, encoding="utf-8"))
    assert isinstance(handled["klara"], dict)


# ---- the plan in Firestore (scripts/publiceringsschema_sync.py) -------------------------------------------------------

class SyncDb:
    def __init__(self, plan_docs, posts):
        self.data = {"publiceringsschema": dict(plan_docs), "posts": dict(posts)}

    def collection(self, name):
        docs = self.data[name]

        class Snap:
            def __init__(self, i): self.id = i
            def to_dict(self): return dict(docs[self.id]) if self.id in docs else None

        class Doc:
            def __init__(self, i): self.id = i
            def get(self): return Snap(self.id)
            def set(self, d): docs[self.id] = dict(d)
            def delete(self): docs.pop(self.id, None)

        class Col:
            def stream(self): return [Snap(i) for i in list(docs)]
            def document(self, i): return Doc(i)
        return Col()


def test_the_plan_sync_upserts_and_never_deletes_approved_rows():
    from scripts import publiceringsschema_sync as ps
    row = lambda d, i, **kw: {"datum": d, "tid": "07:00", "id": i, "titel": i, "spar": "P", "bluesky": None,  # noqa: E731
                              "godkand": None, **kw}
    schema = {"poster": [row("2026-11-17", "a"), row("2026-11-20", "b")]}
    db = SyncDb({"2026-11-17_a": row("2026-11-17", "a", titel="gammal"),
                 "2026-11-10_godkand": row("2026-11-10", "godkand"),       # gone from the file, its article scheduled
                 "2026-11-11_lokal": row("2026-11-11", "lokal", godkand="2026-11-09T08:00:00+01:00"),
                 "2026-11-12_bort": row("2026-11-12", "bort")},
                {"godkand": {"published": True}, "bort": {"published": False}, "lokal": {"published": False}})
    out = ps.sync(db, schema, write_it=False, prune=True)
    assert out == {"write": ["2026-11-17_a", "2026-11-20_b"], "delete": ["2026-11-12_bort"],
                   "kept": ["2026-11-10_godkand", "2026-11-11_lokal"]}
    assert db.data["publiceringsschema"]["2026-11-17_a"]["titel"] == "gammal"      # a dry run writes nothing
    ps.sync(db, schema, write_it=True, prune=False)                                  # without --rensa: nothing deleted
    plan = db.data["publiceringsschema"]
    assert plan["2026-11-17_a"] == row("2026-11-17", "a") and "2026-11-12_bort" in plan
    ps.sync(db, schema, write_it=True, prune=True)
    assert set(db.data["publiceringsschema"]) == {"2026-11-17_a", "2026-11-20_b", "2026-11-10_godkand", "2026-11-11_lokal"}
    with pytest.raises(SystemExit):
        ps.rows_of({"poster": [row("2026-11-17", "a/b")]})


def test_the_committed_plan_syncs_as_documents():
    from scripts import publiceringsschema_sync as ps
    rows = ps.rows_of(json.load(open(ps.SCHEMA, encoding="utf-8")))
    assert rows and all(k == f"{r['datum']}_{r['id']}" and set(r) == set(ps.FIELDS) for k, r in rows.items())
