"""Besöksstatistiken för webbplatsen (src/site_stats.py)."""
import datetime as dt

from src import site_stats


def test_summarize_counts_views_visits_sections_and_countries():
    since = dt.date(2026, 10, 12)
    rows = [
        {"kind": "view", "path": "/", "day": "2026-10-12", "entry": True, "ref": "google.com", "tz": "Europe/Stockholm",
         "lang": "sv-SE", "device": "dator"},
        {"kind": "view", "path": "/artiklar/x", "day": "2026-10-12", "entry": False, "ref": "", "tz": "Europe/Stockholm",
         "lang": "sv-SE", "device": "dator"},
        {"kind": "view", "path": "/", "day": "2026-10-14", "entry": True, "ref": "", "tz": "Europe/Oslo", "lang": "nb",
         "device": "mobil"},
        {"kind": "view", "path": "/", "day": "2026-10-14", "entry": True, "tz": "America/Lima", "lang": "es"},
        {"kind": "section", "path": "/", "day": "2026-10-12", "section": "artiklar"},
        {"kind": "section", "path": "/", "day": "2026-10-14", "section": "artiklar"},
        {"kind": "section", "path": "/", "day": "2026-10-14", "section": "om"},
        {"kind": "view", "path": "/", "day": "2026-10-01", "entry": True},  # before the period: not in a day
    ]
    out = site_stats.summarize(rows, since, 3, site_stats.page_titles([{"slug": "x", "title": "X"}]))
    assert out["views"] == 5 and out["visits"] == 4
    assert [d["views"] for d in out["per_day"]] == [2, 0, 2]
    assert [d["visits"] for d in out["per_day"]] == [1, 0, 2]
    assert out["pages"][0] == {"path": "/", "title": "Startsidan", "n": 4}
    assert {"path": "/artiklar/x", "title": "X", "n": 1} in out["pages"]
    assert out["sections"][0] == {"key": "artiklar", "n": 2, "share": 0.5}
    assert out["referrers"] == [{"key": "google.com", "n": 1}] and out["direct"] == 3
    countries = {c["key"]: c["n"] for c in out["countries"]}
    assert countries == {"Sverige": 2, "Norge": 1, "övriga Amerika": 1, "okänt": 1}
    assert {c["key"] for c in out["languages"]} == {"svenska", "norska", "spanska", "okänt"}
    # A clicked day: everything but the bars per day counts that day alone
    one = site_stats.summarize(rows, since, 3, {}, day="2026-10-14")
    assert one["day"] == "2026-10-14" and one["views"] == 2 and one["visits"] == 2
    assert [d["views"] for d in one["per_day"]] == [2, 0, 2]
    assert one["pages"] == [{"path": "/", "title": None, "n": 2}]
    assert {c["key"]: c["n"] for c in one["countries"]} == {"Norge": 1, "övriga Amerika": 1}
    assert {s["key"] for s in one["sections"]} == {"artiklar", "om"}


def test_country_and_language_fallbacks():
    assert site_stats.country("Europe/Stockholm") == "Sverige"
    assert site_stats.country("Asia/Kolkata") == "Asien"
    assert site_stats.country("") == "okänt"
    assert site_stats.language("en-GB") == "engelska"
    assert site_stats.language("xx") == "xx"


def test_votes_on_the_articles_page_are_summarised():
    since = dt.date(2026, 10, 20)
    rows = [{"kind": "click", "path": "/artiklar", "day": "2026-10-20", "label": "rost:magi"},
            {"kind": "click", "path": "/artiklar", "day": "2026-10-20", "label": "rost:magi"},
            {"kind": "click", "path": "/artiklar", "day": "2026-10-20", "label": "rost:eddan"},
            {"kind": "click", "path": "/artiklar", "day": "2026-10-20", "label": "rost-eget:Stenarna på Öland"}]
    out = site_stats.summarize(rows, since, 1)
    assert out["clicks"]["votes"] == [{"key": "Magi, förbannelser och skydd", "n": 2}, {"key": "Eddan och fornnordisk dikt", "n": 1}]
    assert out["clicks"]["vote_texts"] == [{"key": "Stenarna på Öland", "n": 1}]
