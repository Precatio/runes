"""Veckans publiceringar (api/routers/blog_week.py): svensk tid, veckans fönster, vad som avvisas och Bluesky-kön.

Allt körs mot en falsk Firestore; inget schemaläggs eller publiceras på riktigt."""
import datetime as dt
import json
import os

import pytest

from api.routers import blog
from api.routers import blog_week as bw

UTC = dt.timezone.utc


# ---- svensk tid och veckans fönster ----------------------------------------------------------------------------------

def test_the_plan_is_read_as_swedish_time_in_winter_and_summer():
    assert bw.publish_time("2026-11-17", "07:00") == dt.datetime(2026, 11, 17, 6, 0, tzinfo=UTC)   # vintertid, +01
    assert bw.publish_time("2027-06-01", "07:00") == dt.datetime(2027, 6, 1, 5, 0, tzinfo=UTC)     # sommartid, +02
    # the days the clock changes: after 03:00 on the last Sunday of October it is winter time, of March summer time
    assert bw.publish_time("2026-10-25", "07:00") == dt.datetime(2026, 10, 25, 6, 0, tzinfo=UTC)
    assert bw.publish_time("2027-03-28", "07:00") == dt.datetime(2027, 3, 28, 5, 0, tzinfo=UTC)
    assert bw.publish_time("2026-11-17", "07:00").tzinfo is not None


def test_the_week_is_the_coming_monday_to_sunday():
    wed, mon, sun = dt.date(2026, 11, 11), dt.date(2026, 11, 16), dt.date(2026, 11, 22)
    assert bw.week_of(None, wed) == (mon, sun)
    assert bw.week_of(None, mon) == (mon, sun)                       # on the Monday itself: this week
    assert bw.week_of(None, dt.date(2026, 11, 17)) == (dt.date(2026, 11, 23), dt.date(2026, 11, 29))
    assert bw.week_of(dt.date(2026, 11, 19), wed) == (mon, sun)      # from: the week the date lies in
    assert mon.isocalendar().week == 47
    schema = {"poster": [{"datum": "2026-11-20", "tid": "07:00", "id": "b"}, {"datum": "2026-11-17", "tid": "07:00", "id": "a"},
                         {"datum": "2026-11-24", "tid": "07:00", "id": "c"}, {"datum": "2026-11-15", "tid": "07:00", "id": "z"}]}
    assert [e["id"] for e in bw.in_week(schema, mon, sun)] == ["a", "b"]


def test_the_committed_plan_is_well_formed_and_its_posts_fit_bluesky():
    from scripts.bluesky_post import LIMIT, compose
    with open(os.path.join(bw.ROOT, "data", "publiceringsschema.json"), encoding="utf-8") as fh:
        schema = json.load(fh)
    assert schema["_om"] and schema["poster"]
    for e in schema["poster"]:
        bw.publish_time(e["datum"], e["tid"])
        assert e["spar"] in ("P", "F") and e["id"] and "godkand" in e
        if e["bluesky"]:
            n = len(compose(e["bluesky"]["text"], e["bluesky"]["tags"]))
            assert n == bw.composed_length(e["bluesky"]) and n <= LIMIT
            assert "VikingAge" in e["bluesky"]["tags"] and len(e["bluesky"]["tags"]) >= 5
            assert e["bluesky"]["tags"][1] in ("MedievalSky", "Skystorians")


# ---- vad som avvisas -------------------------------------------------------------------------------------------------

NOW = dt.datetime(2026, 11, 16, 8, 0, tzinfo=UTC)
ENTRY = {"datum": "2026-11-17", "tid": "07:00", "id": "a", "bluesky": {"text": "Hello.", "tags": ["runology"]}}
DRAFT = {"id": "a", "slug": "a", "title": "A", "body": "Text", "published": False, "labels": ["Forskning"]}


def test_published_scheduled_missing_and_past_articles_are_refused():
    assert bw.refusal(ENTRY, DRAFT, NOW) is None
    assert "finns inte" in bw.refusal(ENTRY, None, NOW)
    live = {**DRAFT, "published": True, "publishedAt": "2026-11-01T06:00:00+00:00"}
    assert bw.refusal(ENTRY, live, NOW).startswith("Redan publicerad")
    later = {**DRAFT, "published": True, "publishedAt": "2026-11-20T06:00:00+00:00"}
    assert bw.refusal(ENTRY, later, NOW).startswith("Redan schemalagd")
    assert "passerat" in bw.refusal(ENTRY, DRAFT, dt.datetime(2026, 11, 17, 6, 0, tzinfo=UTC))   # 07:00 Swedish time
    assert bw.refusal(ENTRY, DRAFT, dt.datetime(2026, 11, 17, 5, 59, tzinfo=UTC)) is None
    assert "Etiketterna" in bw.refusal(ENTRY, {**DRAFT, "labels": ["Påhittad"]}, NOW)
    assert "Bluesky-texten" in bw.refusal({**ENTRY, "bluesky": {"text": "x" * 300, "tags": ["a"]}}, DRAFT, NOW)
    assert "kan inte läsas" in bw.refusal({**ENTRY, "tid": "7"}, DRAFT, NOW)
    s = bw.status(ENTRY, later, NOW)
    assert s["state"] == "schemalagd" and not s["can_approve"] and s["bluesky_length"] == len("Hello.\n\n#runology")
    assert bw.status(ENTRY, None, NOW)["state"] == "saknas" and bw.status(ENTRY, DRAFT, NOW)["state"] == "utkast"


# ---- Bluesky-kön -----------------------------------------------------------------------------------------------------

def test_the_post_goes_into_the_queue_on_its_publication_day_and_only_once():
    ko = {"items": [{"date": "2026-11-10", "slug": "gammal", "posted": "https://bsky.app/x"},
                    {"date": "2026-11-16", "slug": "v1"}, {"date": "2026-11-17", "slug": "v2"},
                    {"date": "2026-11-18", "slug": "v3"}, {"date": "2026-11-05", "slug": "borttagen", "removed": True}]}
    b = {"text": " Hello. ", "tags": ["runology", "MedievalSky"]}
    assert bw.queue_bluesky(ko, "ny", "2026-11-17", b)
    assert [i["slug"] for i in ko["items"]] == ["gammal", "v1", "ny", "v2", "v3", "borttagen"]
    assert ko["items"][2] == {"date": "2026-11-17", "slug": "ny", "en": True, "text": "Hello.", "tags": ["runology", "MedievalSky"]}
    assert not bw.queue_bluesky(ko, "ny", "2026-11-17", b)            # no duplicate
    assert not bw.queue_bluesky(ko, "gammal", "2026-11-20", b)        # already posted counts as queued
    assert bw.queue_bluesky(ko, "borttagen", "2026-12-31", b)         # a removed row does not
    assert ko["items"][-1]["slug"] == "borttagen" and len(ko["items"]) == 7


# ---- godkännandet mot en falsk Firestore ------------------------------------------------------------------------------

class FakeFirestore:
    """Just what blog.store_post, blog._all and blog_week need. Writes are recorded so a test can see them."""

    def __init__(self, docs):
        self.docs, self.writes = docs, []
        fs = self

        class Snap:
            def __init__(self, i): self.id = i
            def to_dict(self): return dict(fs.docs[self.id]) if self.id in fs.docs else None

        class Doc:
            def __init__(self, i): self.id = i
            def get(self): return Snap(self.id)

            def set(self, data, merge=False):
                fs.writes.append((self.id, dict(data)))
                fs.docs.setdefault(self.id, {}).update(data)

        class Col:
            def document(self, i=None): return Doc(i or "nytt-id")
            def stream(self): return [Snap(i) for i in list(fs.docs)]

        self._col = Col()

    def collection(self, name):
        assert name == blog.COLLECTION
        return self._col


@pytest.fixture
def world(tmp_path, monkeypatch):
    from src import site_export
    monday, _ = bw.week_of(None, dt.datetime.now(bw.TZ).date())
    if monday == dt.datetime.now(bw.TZ).date():   # on a Monday the coming week is this week; use next week's to be safe
        monday += dt.timedelta(days=7)
    tue, fri = (monday + dt.timedelta(days=d) for d in (1, 4))
    old = monday - dt.timedelta(days=7)
    docs = {
        "a": {"slug": "artikel-a", "title": "A", "body": "Text A", "title_en": "A en", "body_en": "Text A en",
              "published": False, "labels": ["Forskning", "Geografi"], "month": "2026-10", "author": "Viktor"},
        "b": {"slug": "artikel-b", "title": "B", "body": "Text B", "published": False, "labels": ["Forskning"]},
        "p": {"slug": "artikel-p", "title": "P", "body": "Publicerad text", "published": True,
              "publishedAt": "2026-11-01T06:00:00+00:00", "labels": ["Forskning"]},
        "x": {"slug": "artikel-x", "title": "X", "body": "Utanför veckan", "published": False, "labels": []},
    }
    fs = FakeFirestore(docs)
    monkeypatch.setattr(blog, "firestore", lambda: fs)
    monkeypatch.setattr(blog, "_snapshot", lambda: {})
    blog._forget()
    calls = []
    monkeypatch.setattr(site_export, "publish_soon", lambda: calls.append("soon"))
    monkeypatch.setattr(site_export, "schedule", lambda posts: calls.append(("schedule", len(posts))))
    b = lambda t: {"text": t, "tags": ["runology", "MedievalSky", "VikingAge"]}  # noqa: E731
    schema = {"_om": "test", "poster": [
        {"datum": tue.isoformat(), "tid": "07:00", "id": "a", "titel": "A", "spar": "P", "bluesky": b("Post A"), "godkand": None},
        {"datum": tue.isoformat(), "tid": "12:00", "id": "p", "titel": "P", "spar": "P", "bluesky": b("Post P"), "godkand": None},
        {"datum": fri.isoformat(), "tid": "07:00", "id": "b", "titel": "B", "spar": "F", "bluesky": b("Post B"), "godkand": None},
        {"datum": old.isoformat(), "tid": "07:00", "id": "x", "titel": "X", "spar": "P", "bluesky": None, "godkand": None},
    ]}
    monkeypatch.setattr(bw, "SCHEMA", str(tmp_path / "publiceringsschema.json"))
    monkeypatch.setattr(bw, "KO", str(tmp_path / "ko.json"))
    bw._write(bw.SCHEMA, schema)
    bw._write(bw.KO, {"_om": "kö", "items": [{"date": tue.isoformat(), "slug": "annan"},
                                             {"date": (tue + dt.timedelta(days=1)).isoformat(), "slug": "annan2"}]})
    yield {"fs": fs, "monday": monday, "tue": tue, "fri": fri, "calls": calls}
    blog._forget()


def test_the_week_shows_each_entry_with_its_status(world):
    out = bw.week(world["monday"].isoformat(), {})
    assert out["from"] == world["monday"].isoformat() and out["week"] == world["monday"].isocalendar().week
    by = {e["id"]: e for e in out["entries"]}
    assert set(by) == {"a", "b", "p"}                                     # x lies in another week
    assert by["a"]["state"] == "utkast" and by["a"]["can_approve"] and by["a"]["title_en"] and by["a"]["slug"] == "artikel-a"
    assert by["p"]["state"] == "publicerad" and not by["p"]["can_approve"]
    assert not by["b"]["title_en"] and by["b"]["bluesky_length"] == len("Post B\n\n#runology #MedievalSky #VikingAge")


def test_approval_schedules_drafts_backs_them_up_and_queues_bluesky_once(world):
    fs, tue = world["fs"], world["tue"]
    out = bw.approve(bw.ApproveRequest.model_validate({"from": world["monday"].isoformat(), "ids": ["a", "b", "p", "x"]}),
                     {"uid": "viktor"})
    res = {r["id"]: r for r in out["results"]}
    assert res["a"]["ok"] and res["b"]["ok"]
    assert not res["p"]["ok"] and "Redan publicerad" in res["p"]["reason"]
    assert not res["x"]["ok"] and "veckans" in res["x"]["reason"]
    # scheduled through store_post: published with the plan's time in Swedish time, text untouched
    a = fs.docs["a"]
    assert a["published"] is True and a["publishedAt"] == bw.publish_time(tue.isoformat(), "07:00")
    assert a["body"] == "Text A" and a["body_en"] == "Text A en" and a["by"] == "viktor"
    assert blog.is_live(a) is False
    # the published article was never written, and each draft was backed up before the write
    assert {i for i, _ in fs.writes} == {"a", "b"}
    for i in ("a", "b"):
        (f,) = os.listdir(os.path.join(blog.BACKUP, i))
        assert json.load(open(os.path.join(blog.BACKUP, i, f), encoding="utf-8"))["published"] is False
    # Bluesky: A goes in before the queue's other post that day; B has no English edition, so no post
    ko = json.load(open(bw.KO, encoding="utf-8"))
    assert [i["slug"] for i in ko["items"]] == ["artikel-a", "annan", "annan2"]
    assert ko["items"][0]["date"] == tue.isoformat() and ko["items"][0]["en"] is True
    assert "engelsk" in res["b"]["bluesky"]
    schema = json.load(open(bw.SCHEMA, encoding="utf-8"))
    godkand = {e["id"]: e["godkand"] for e in schema["poster"]}
    assert godkand["a"] and godkand["b"] and godkand["p"] is None and godkand["x"] is None
    assert world["calls"] == ["soon", ("schedule", 4)]
    # a second approval changes nothing: both are now scheduled, and the queue gets no duplicate
    n = len(fs.writes)
    again = bw.approve(bw.ApproveRequest.model_validate({"from": world["monday"].isoformat(), "ids": ["a", "b"]}), {"uid": "viktor"})
    assert all(not r["ok"] and r["reason"].startswith("Redan schemalagd") for r in again["results"])
    assert len(fs.writes) == n and len(json.load(open(bw.KO, encoding="utf-8"))["items"]) == 3


def test_an_already_queued_slug_is_not_queued_again(world):
    ko = json.load(open(bw.KO, encoding="utf-8"))
    ko["items"].append({"date": "2026-12-31", "slug": "artikel-a", "text": "Redan här"})
    bw._write(bw.KO, ko)
    out = bw.approve(bw.ApproveRequest.model_validate({"from": world["monday"].isoformat(), "ids": ["a"]}), {"uid": "v"})
    assert out["results"][0]["ok"] and out["results"][0]["bluesky"] == "stod redan i kön"
    assert [i["slug"] for i in json.load(open(bw.KO, encoding="utf-8"))["items"]].count("artikel-a") == 1


def test_the_endpoints_are_admin_only():
    from fastapi.testclient import TestClient
    from api.main import app
    c = TestClient(app)
    assert c.get("/api/admin/blog/week").status_code in (401, 403)
    assert c.post("/api/admin/blog/week/approve", json={"from": "2026-11-16", "ids": ["a"]}).status_code in (401, 403)
