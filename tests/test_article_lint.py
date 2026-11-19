"""Granskningen före godkännandet (src/article_lint.py): de gemensamma fallen (samma som webbens articleLint.ts prövas
mot i web/scripts/article_lint.test.mjs), källkontrollen mot tidskriftsdatabasen när den finns, och att godkännandet i
api/routers/blog_week.py kör granskningen och kräver en bekräftelse vid fel."""
import datetime as dt
import json
import os

import pytest

from src import article_lint as al

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASES = json.load(open(os.path.join(ROOT, "tests", "fixtures", "article_lint_cases.json"), encoding="utf-8"))["fall"]


def _when(s):
    return dt.datetime.fromisoformat(s) if s else None


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_the_shared_cases(case):
    posts = None
    if "posts" in case:
        posts = [{**p, "body_en": "x" if p.get("hasEnglish") else ""} for p in case["posts"]]
    got = al.lint(case["post"], posts, publish_at=_when(case.get("publish_at")),
                  now=_when(case.get("now")) or dt.datetime(2026, 11, 19, tzinfo=dt.timezone.utc), citations=False)
    assert sorted([f["niva"], f["kod"], f["sprak"]] for f in got) == case["expect"], got


def test_numbers_are_read_the_same_way_in_both_languages():
    assert al.numbers("1 352 borgar, 31,5 procent och år 1050", "sv") == {"1352", "31.5", "1050"}
    assert al.numbers("1,352 forts, 31.5 per cent and the year 1050", "en") == {"1352", "31.5", "1050"}


def test_citations_are_parsed_in_running_text_and_reference_lists():
    text = ("Han skrev att ”runorna måste läsas först” (*Futhark* 4, 2013, s. 24). Senare ”något helt annat här” "
            "([Fornvännen 1952, s. 209](https://pub.raa.se/dokumentation/4a911b8a-4ce4-4f00-0000-000000000000)).\n\n"
            "- Ekholm, G. 1950. Var restes runstenarna? *Fornvännen* 45, s. 137–147. Citaten s. 140.\n")
    a, b, c = al.parse_citations(text)
    assert (a["journal"], a["volume"], a["stated_year"], a["refs"], a["quotes"]) == \
        ("Futhark", "4", 2013, [(24, None)], ["runorna måste läsas först"])
    assert (b["year"], b["refs"], b["quotes"], b["linked"]) == (1952, [(209, None)], ["något helt annat här"],
                                                                "4a911b8a-4ce4-4f00-0000-000000000000")
    assert c["ref_line"] and c["author_year"] == 1950 and c["title"] == "Var restes runstenarna?"
    assert c["refs"] == [(137, 147), (140, None)]
    assert al._expand([(137, 47)]) == set(range(137, 148))


def test_volume_and_year_must_agree(monkeypatch):
    monkeypatch.setattr(al, "_db", lambda: object())
    monkeypatch.setattr(al, "docs_for", lambda *a: [])
    out = al.check_citations("- Ekholm, G. 1951. Var restes runstenarna? *Fornvännen* 45, s. 137–147.", "sv")
    errors = [f for f in out if f["niva"] == "FEL"]
    assert [f["kod"] for f in errors] == ["kalla_argang"] and "1950" in errors[0]["text"]


def test_without_the_journal_database_there_is_one_warning(monkeypatch):
    monkeypatch.setattr(al, "_db", lambda: None)
    out = al.check_citations("Se (*Fornvännen* 79, s. 258) och (*Futhark* 1, s. 3).", "sv")
    assert [(f["niva"], f["kod"]) for f in out] == [("VARNING", "kalla_ej_provad")]
    assert al.check_citations("Ingen tidskrift här.", "sv") == []


needs_sok = pytest.mark.skipif(not os.path.exists(al.SOK), reason="tidskriftsdatabasen (sok.sqlite) saknas")


@needs_sok
def test_the_printed_page_comes_from_the_page_header_not_the_pdf_page():
    # Brate 1907 (key 1907_020, whose key start is not the printed start): the quote stands on printed page 90
    q = "bevisar naturligtvis, att denna skrifttyp är hemma i Sverige"
    right = f"Brate skrev att det ”{q}” ([Fornvännen 1907, s. 90](https://pub.raa.se/dokumentation/13664e92-27ea-4555-ba76-1132fad7a2dc))."
    assert al.check_citations(right, "sv") == []
    wrong = right.replace("s. 90", "s. 30")
    (f,) = al.check_citations(wrong, "sv")
    assert (f["niva"], f["kod"]) == ("FEL", "kalla_sida") and "s. 90" in f["text"]
    # Futhark 4: Barnes's printed page 22, not 24
    futhark = ("Han varnade för ”the rush to embrace “magic” in the inter-war years” "
               "([Futhark 4 (2013), s. 24](https://uu.diva-portal.org/smash/get/diva2:682689/FULLTEXT01.pdf)).")
    (f,) = al.check_citations(futhark, "sv")
    assert f["kod"] == "kalla_sida" and "s. 22" in f["text"]


@needs_sok
def test_a_reference_entry_must_lie_inside_its_article():
    ok = "- Ekholm, G. 1950. Var restes runstenarna? *Fornvännen* 45, s. 137–147.\n"
    assert al.check_citations(ok, "sv") == []
    (f,) = al.check_citations(ok.replace("137–147", "237–247"), "sv")
    assert (f["niva"], f["kod"]) == ("FEL", "kalla_omfang")


# ---- the approval ----------------------------------------------------------------------------------------------------

def test_approval_refuses_an_article_with_errors_until_they_are_confirmed(tmp_path, monkeypatch):
    from api.routers import blog
    from api.routers import blog_week as bw
    from src import site_export
    from tests.test_blog_week import FakeFirestore
    monday, _ = bw.week_of(None, dt.datetime.now(bw.TZ).date())
    if monday == dt.datetime.now(bw.TZ).date():
        monday += dt.timedelta(days=7)
    tue = monday + dt.timedelta(days=1)
    docs = {"a": {"slug": "a", "title": "A", "body": "Bilden {COVER} står kvar.", "published": False, "labels": ["Forskning"]}}
    fs = FakeFirestore(docs)
    monkeypatch.setattr(blog, "firestore", lambda: fs)
    monkeypatch.setattr(blog, "_snapshot", lambda: {})
    monkeypatch.setattr(blog, "BACKUP", str(tmp_path / "backup"))
    monkeypatch.setattr(site_export, "publish_soon", lambda: None)
    monkeypatch.setattr(site_export, "schedule", lambda posts: None)
    monkeypatch.setattr(bw, "SCHEMA", str(tmp_path / "s.json"))
    monkeypatch.setattr(bw, "KO", str(tmp_path / "ko.json"))
    bw._write(bw.SCHEMA, {"poster": [{"datum": tue.isoformat(), "tid": "07:00", "id": "a", "titel": "A", "spar": "P",
                                      "bluesky": None, "godkand": None}]})
    bw._write(bw.KO, {"items": []})
    blog._forget()
    week = bw.week(monday.isoformat(), {})
    (e,) = week["entries"]
    assert e["granskning"]["fel"] == 1 and e["granskning"]["fynd"][0]["kod"] == "platshallare"
    assert e["can_approve"]   # errors do not block, they ask for a confirmation
    assert "queue" in week and week["queue"]["until"] == tue.isoformat()
    req = lambda **kw: bw.ApproveRequest.model_validate({"from": monday.isoformat(), "ids": ["a"], **kw})  # noqa: E731
    (r,) = bw.approve(req(), {"uid": "v"})["results"]
    assert not r["ok"] and "bekräfta" in r["reason"] and r["granskning"]["fel"] == 1
    assert fs.docs["a"]["published"] is False
    (r,) = bw.approve(req(confirm_errors=["a"]), {"uid": "v"})["results"]
    assert r["ok"] and r["granskning"]["fel"] == 1 and fs.docs["a"]["published"] is True
    blog._forget()


def test_the_queue_end_and_its_alarm():
    from api.routers import blog_week as bw
    today = dt.date(2026, 11, 19)
    posts = {"a": {"published": True, "publishedAt": "2027-02-07T06:00:00+00:00", "labels": ["Forskning"]},
             "r": {"published": True, "publishedAt": "2027-03-01T06:00:00+00:00", "labels": ["Rapport"]},
             "d": {"published": False, "labels": ["Forskning"]}}
    schema = {"poster": [{"datum": "2027-02-10", "id": "d", "spar": "P"}, {"datum": "2027-02-12", "id": "saknas", "spar": "P"},
                         {"datum": "2027-03-05", "id": "r", "spar": "F"}]}
    q = bw.queue_end(schema, posts, today)
    assert q["until"] == "2027-02-10" and q["days_left"] == 83 and not q["alarm"]
    q = bw.queue_end(schema, posts, dt.date(2027, 1, 25))
    assert q["days_left"] == 16 and q["alarm"]
    assert bw.queue_end({"poster": []}, {}, today) == {"until": None, "days_left": 0, "alarm": True}
