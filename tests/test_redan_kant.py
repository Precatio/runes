"""Forskningsluckor, utbyggnaden 2026-11-19: Redan känt? (src/redan_kant.py), tryckta sidor i tidskrifterna
(src/literature.journal_page_offset), frågelistan (src/fragelista.py), Rundata mot SRI (src/sri_rundata.py) och
täckningen i tidskrifterna (src/research_gaps.coverage). Testerna bygger egna små källfiler och läser inga
upphovsrättsskyddade texter."""
import json
import os
import re
import subprocess

import pytest

from src import fragelista, literature, redan_kant as rk, research_gaps, sri_rundata
from src.signum import fold_signum

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RX = literature.signum_pattern(["U", "Sö", "Ög", "M"])


# --- the carver phrases ---------------------------------------------------------------------------------------

def test_carver_base():
    assert rk.carver_base("Öpir 1") == "Öpir"
    assert rk.carver_base("Björn 2 eller -björn") == "Björn"
    assert rk.carver_base("Torbjörn skald") == "Torbjörn"
    assert rk.carver_base("Ulv i Borresta") == "Ulv"
    assert rk.carver_base("-fast") is None and rk.carver_base("þuliR") is None and rk.carver_base(None) is None


@pytest.mark.parametrize("text", [
    "Ristningen är, såsom von Friesen framhållit, med säkerhet utförd av Öpir.",
    "Brate hänför den (i Svenska runristare) till Öpir.",
    "Brate uppför U 1 bland Öpirs ristningar, en attribution som dock är osäker.",
    "Ornamentik och runformer tyda på ett verk av runristaren Öpir.",
    "»Ond och Anund läto resa stenen efter Vigbjörn. Öpir ristade.»",
    "This stone was probably carved by Öpir in the 1070s.",
])
def test_name_pattern_finds_the_carver(text):
    assert rk.name_pattern("Öpir").search(text)


@pytest.mark.parametrize("name,text", [
    ("Anund", "»Ond och Anund läto resa stenen efter Vigbjörn. Öpir ristade.»"),  # the commissioners are not carvers
    ("Gunnar", "Gunnar lät rista stenen efter sin fader."),
    ("Fot", "stenen låg vid foten av backen"),  # case matters: fot is not Fot
    ("Gunnar", "Huruvida bestämningen hänför sig enbart till Gunnar kan icke avgöras."),
])
def test_name_pattern_skips_other_roles(name, text):
    assert not rk.name_pattern(name).search(text)


def test_carver_mentions_must_concern_the_stone():
    names = rk.names_pattern(["Fot", "Öpir"])
    other = "…omtalas också i U 135. Även U 269 är säkerligen ristad av Fot. 270. Smedby…"
    # in a snippet around U 135, the phrase is closest to U 269: it is about U 269
    assert rk.carver_mentions(other, names, RX, "u135", window=True) == {}
    assert "Fot" in rk.carver_mentions(other, names, RX, "u269", window=True)
    own = "där runstenen U411 står (fig. 1: 10). Denna sten är sannolikt ristad av Fot, verksam vid mitten av 1000-talet."
    assert "Fot" in rk.carver_mentions(own, names, RX, "u411", window=True)
    # in the stone's own SRI article: another stone's signum right before the phrase makes it about that stone
    art = "Ristningen är djup. Jfr liknande förhållanden på U 967 och U 971, båda ristade av Öpir."
    assert rk.carver_mentions(art, names, RX, "u972") == {}
    art2 = "Ristningen är djup och ramlinjen grund. " + "x" * 150 + " Ristningen är utan tvivel utförd av Öpir."
    assert "Öpir" in rk.carver_mentions(art2, names, RX, "u974")


# --- printed pages in the journals ----------------------------------------------------------------------------

def test_journal_page_offset_fornvannen_cover_and_futhark():
    fv = [(1, "Var restes runstenarna?\nEkholm, Gunnar\nFornvännen 137-147"), (2, "VAR RESTES\ntext\n137"),
          (3, "G. EKHOLM\ntext\n138"), (4, "text\n139")]
    off = literature.journal_page_offset(fv, 137, cover=True)
    assert off == 135 and literature.journal_printed(2, off, 137) == "137"
    assert literature.journal_printed(1, off, 137) == "pdf 1"  # the cover has no printed page
    fu = [(1, "A Misidentified Separator\nAbstract"), (2, "208 • Eric T. Lander\ntext"), (3, "A Misidentified Separator in U 924 • 209\ntext")]
    assert literature.journal_page_offset(fu, 207) == 206
    # without metadata the page numbers decide, and a page without numbers stays a pdf page
    assert literature.journal_page_offset([(2, "182 Magnus Källström\nx"), (3, "Ög 231 183\ny")]) == 180
    assert literature.journal_page_offset([(1, "bara text"), (2, "mer text")]) is None
    assert literature.journal_printed(5, None) == "pdf 5"
    # a year in the header (1906) must not beat the metadata
    assert literature.journal_page_offset([(2, "1906\nx"), (3, "1906\ny")], 20, cover=True) == 18


# --- the rule on findings -------------------------------------------------------------------------------------

@pytest.fixture
def sources(tmp_path, monkeypatch):
    """Små källfiler i samma form som de byggda: SRI-artiklar, tidskrifter, registret och katalogen."""
    sri = {"stones": {
        "u100": {"signum": "U 100", "work": "sri7", "pages": ["12", "13"], "carvers": {"Öpir": {"page": "13", "text": "…utförd av Öpir…"}},
                 "same_as": [], "signa": {"u200": {"page": "12", "text": "…samma släkt som på U 200…"}}},
        "u101": {"signum": "U 101", "work": "sri7", "pages": ["14"], "carvers": {},
                 "same_as": [{"signum": "u300", "page": "14", "text": "…av samme ristare som U 300…"}], "signa": {}},
        "u102": {"signum": "U 102", "work": "sri7", "pages": ["15"], "carvers": {}, "same_as": [], "signa": {}},
    }}
    journals = {"n_articles": 2, "articles": {"1945_122": {"journal": "Fornvännen", "year": "1945", "title": "Broar",
                                                           "authors": ["Floderus, Erik"], "url": "https://x"}},
                "stones": {"u103": [{"article": "1945_122", "page": "pdf 8", "printed": "128", "text": "…U 103…",
                                     "carvers": {"Fot": "…sannolikt ristad av Fot…"}}],
                           "u104": [{"article": "1945_122", "page": "pdf 3", "list": True}]}}
    catalog = {"works": [{"id": "sri7", "author": "Wessén, Elias", "year": 1943, "title": "Upplands runinskrifter 2",
                          "kind": "utgåva"}]}
    paths = {}
    for name, obj in (("sri.json", sri), ("journals.json", journals), ("catalog.json", catalog),
                      ("index.json", {"works": {}, "stones": {}}), ("carvers.json", {})):
        p = tmp_path / name
        p.write_text(json.dumps(obj), encoding="utf-8")
        paths[name] = str(p)
    monkeypatch.setattr(rk, "SRI_MENTIONS", paths["sri.json"])
    monkeypatch.setattr(literature, "JOURNALS", paths["journals.json"])
    monkeypatch.setattr(literature, "CATALOG", paths["catalog.json"])
    monkeypatch.setattr(literature, "INDEX", paths["index.json"])
    from src import carver_literature
    monkeypatch.setattr(carver_literature, "PATH", paths["carvers.json"])
    return paths


def _finding(signum, suggested=None, verdict="nytt", assessment="Sannolikt ny och relevant kunskap – värd att pröva", **kw):
    return {"signum": signum, "suggested": suggested, "verdict": verdict, "method": kw.pop("method", "ortografi"),
            "evidence": 0.8, "novelty": 0.85, "relevance": 0.6, "score": round(0.8 * 0.85 * 0.6, 3),
            "assessment": assessment, "reasons": {"nyhet": ["Axelson (1993) attribuerade inte stenen"]}, **kw}


def test_claim_in_sri_takes_the_finding_out_of_likely_new(sources):
    shared = ["Axelson (1993) attribuerade inte stenen"]
    f = _finding("U 100", "Öpir 1")
    f["reasons"]["nyhet"] = shared
    rk.annotate([f])
    k = f["known"]
    assert k["status"] == "nämns" and k["changed"] and k["claim"] == "ristaren Öpir"
    assert k["hits"][0]["source"] == "SRI" and k["hits"][0]["page"] == "s. 13" and k["hits"][0]["author"] == "Wessén"
    assert f["assessment"] == rk.ASSESS_KNOWN and f["novelty"] == rk.NOVELTY_CAP
    assert f["score"] == round(0.8 * rk.NOVELTY_CAP * 0.6, 3)
    assert any("nämns redan i litteraturen" in r for r in f["reasons"]["nyhet"])
    assert shared == ["Axelson (1993) attribuerade inte stenen"]  # the cached reasons are not touched


def test_claim_in_journal_and_same_carver_reference(sources):
    f = _finding("U 103", "Fot 2")
    rk.annotate([f])
    assert f["known"]["status"] == "nämns" and f["known"]["hits"][0]["page"] == "s. 128"
    assert f["known"]["hits"][0]["source"] == "tidskrift" and f["known"]["hits"][0]["author"] == "Floderus"
    g = _finding("U 101", "Balle")
    rk.annotate([g], inscriptions=[{"signum": "U 300", "carvers": [{"name": "Balle", "kind": "A"}]}])
    assert g["known"]["status"] == "nämns" and g["known"]["hits"][0]["via"] == "u300"


def test_discussed_but_claim_missing_keeps_the_assessment(sources):
    f = _finding("U 102", "Öpir 1")
    g = _finding("U 999", "Öpir 1")
    rk.annotate([f, g])
    assert f["known"]["status"] == "diskuteras" and f["assessment"].startswith("Sannolikt ny") and f["novelty"] == 0.85
    assert g["known"]["status"] == "inte diskuterad" and not g["known"]["changed"]
    # a confirmation is never changed, and a list page is not a discussion
    h = _finding("U 100", "Öpir 1", verdict="stämmer", assessment="Bekräftar befintlig forskning")
    rk.annotate([h])
    assert h["known"]["status"] == "nämns" and h["assessment"] == "Bekräftar befintlig forskning" and not h["known"]["changed"]
    assert rk.journal_signa() == {"u103"}


def test_family_link_found_in_sri(sources):
    from src.stone_findings import LINK
    f = _finding("U 100", method=LINK, linked="U 200")
    rk.annotate([f])
    assert f["known"]["status"] == "nämns" and f["known"]["claim"] == "sambandet med U 200"


def test_summary_counts(sources):
    items = [_finding("U 100", "Öpir 1"), _finding("U 102", "Öpir 1")]
    rk.annotate(items)
    s = rk.summary(items)
    assert s["changed"] == 1 and s["changed_likely"] == 1 and s["status"] == {"nämns": 1, "diskuteras": 1}


# --- coverage --------------------------------------------------------------------------------------------------

def test_coverage_counts_journal_stones():
    recs = [{"signum": s, "period": "V", "object": "runsten", "carvers": [], "style": None, "style_uncertain": False,
             "dating": "", "normalization": "x", "flags": {"lost": False}} for s in ("U 1", "U 2", "Sö 3")]
    cov = research_gaps.coverage(recs, set(), {"u1", "so3"})
    rows = {r["code"]: r for r in cov["per_province"]}
    assert rows["U"]["journals"] == 1 and rows["Sö"]["journals"] == 1 and cov["totals"]["journals"] == 2
    assert "journals" not in research_gaps.coverage(recs, set())["per_province"][0]


# --- the question list ----------------------------------------------------------------------------------------

def test_study_code_and_state():
    assert fragelista.study_code("jan–feb 2027 – A1. Flyttade och försvunna stenar") == "A1"
    assert fragelista.study_code("mar–apr 2029 – Språkets klockor") == "Språkets klockor"
    assert fragelista.study_code("Spår P – reservlista (låg)") is None
    assert fragelista.study_code("2029 eller spår P") is None
    assert fragelista.state("plan låst 11 nov (4eef7f6)") == "låst plan"
    assert fragelista.state("Ingvar försvagat (58 %). Gravfälten står sig") == "körd"
    assert fragelista.state("planerad") == "planerad"


def test_questions_from_small_files(tmp_path, monkeypatch):
    q = [{"titel": "Hur långt flyttades runstenarna?", "fraga": "Hur långt flyttades stenarna från sin plats?",
          "tema": "Bevarande", "relevans": 1, "studie": "jan–feb 2027 – A1. Flyttade och försvunna stenar",
          "pastaenden": ["1950_137#1", "1950_137#9"], "antal_texter": 1, "decennier_lista": [1950],
          "relevans_skal": "HEMLIG MOTIVERING", "varfor": "HEMLIGT", "data": "har"},
         {"titel": "Fråga i reserv", "fraga": "x", "tema": "T", "relevans": 3, "studie": "Spår P – reservlista",
          "pastaenden": [], "decennier_lista": []}]
    (tmp_path / "q.jsonl").write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in q), encoding="utf-8")
    (tmp_path / "c.jsonl").write_text(json.dumps({"id": "1950_137#1", "key": "1950_137", "journal": "fornvannen",
                                                  "year": "1950", "authors": "Ekholm, Gunnar", "title": "Var restes runstenarna?",
                                                  "quote": "flyttade stenar", "how": "HEMLIGT PRÖVNINGSSÄTT"}), encoding="utf-8")
    (tmp_path / "p.json").write_text(json.dumps({"pages": {"1950_137#1": "139"}}), encoding="utf-8")
    (tmp_path / "plan.md").write_text("| Period | Studie | Frågor | Data | Rapport | Status |\n|---|---|---|---|---|---|\n"
                                      "| jan–feb 2027 | **A1. Flyttade och försvunna stenar** | 4 | har | mars | plan låst 11 nov |\n",
                                      encoding="utf-8")
    plans = tmp_path / "plans"
    plans.mkdir()
    (plans / "2027-01-A1-flyttade.md").write_text("plan", encoding="utf-8")
    (plans / "2027-01-A1-flyttade.sha256").write_text("x", encoding="utf-8")
    (tmp_path / "a.json").write_text(json.dumps({"posts": []}), encoding="utf-8")
    for attr, name in (("QUESTIONS", "q.jsonl"), ("CLAIMS", "c.jsonl"), ("PAGES", "p.json"), ("PLAN", "plan.md"),
                       ("ARTICLES", "a.json")):
        monkeypatch.setattr(fragelista, attr, str(tmp_path / name))
    monkeypatch.setattr(fragelista, "PLANS_DIR", str(plans))
    d = fragelista.questions()
    assert d["internal"] and d["n"] == 2 and d["levels"] == {"avgörande": 1, "användbar": 1}
    a, b = d["questions"]
    assert a["study_code"] == "A1" and a["study_state"] == "låst plan" and a["plans"][0]["locked"]
    assert a["sources"][0] == {"id": "1950_137#1", "author": "Ekholm", "year": "1950", "title": "Var restes runstenarna?",
                               "journal": "Fornvännen", "key": "1950_137", "page": "s. 139", "quote": "flyttade stenar"}
    assert a["n_claims"] == 2 and len(a["sources"]) == 1  # a claim missing from the database is left out
    assert b["study_state"] == "reservlista" and b["plans"] == []
    # the holdback: rationales and how a question is tested never leave the server
    body = json.dumps(d, ensure_ascii=False)
    assert "HEMLIG" not in body and "relevans_skal" not in body and "varfor" not in body


def test_article_match_needs_five_shared_words():
    posts = [{"title": "A", "slug": "a", "tokens": fragelista._tokens("flyttade runstenar kyrkan inmurade gravfält landsvägen")},
             {"title": "B", "slug": "b", "tokens": fragelista._tokens("flyttade kyrkan")}]
    q = {"titel": "Flyttades stenarna till kyrkan?", "fraga": "Hur många flyttade och inmurade stenar, vid gravfält och landsvägen?"}
    assert [m["slug"] for m in fragelista.article_matches(q, posts)] == ["a"]


# --- Rundata against SRI ----------------------------------------------------------------------------------------

def test_sri_rundata_kinds(monkeypatch):
    from src import r_bridge, runor, sri_fyndhistorik
    sri = {
        "U 1": {"position": {"value": "flyttad", "page": "5", "quote": "flyttades 1930"}, "lost": None, "refound": []},
        "U 2": {"position": {"value": "ursprunglig plats", "page": "6", "quote": "står på sin plats"}, "lost": None, "refound": []},
        "U 3": {"position": {"value": "försvunnen"}, "lost": {"lost_at_edition": True, "page": "7", "quote": "nu förkommen"}, "refound": []},
        "U 4": {"position": {"value": "försvunnen"}, "lost": {"lost_at_edition": True, "page": "8", "quote": "förkommen"},
                "refound": [{"year": 1950}]},
        "U 5": {"position": {"value": "okänt", "page": "9", "quote": "stod vid vägen"}, "lost": None, "refound": []},
    }
    moved = {"U 2"}
    lost = {"U 5"}
    monkeypatch.setattr(sri_fyndhistorik, "available", lambda: True)
    monkeypatch.setattr(sri_fyndhistorik, "for_inscription",
                        lambda r: {**sri[r["signum"]], "volume": "SRI VI", "year": 1940, "url": None} if r["signum"] in sri else None)
    monkeypatch.setattr(r_bridge, "is_moved", lambda r: r["signum"] in moved)
    monkeypatch.setattr(runor, "available", lambda: False)
    monkeypatch.setattr(rk, "sri_for", lambda s: {"pages": ["5"]})
    recs = [{"signum": s, "period": "V", "object": "runsten", "place": "X", "placement": "",
             "flags": {"lost": s in lost}} for s in sri]
    d = sri_rundata.disagreements(recs)
    assert d["n_compared"] == 5
    assert d["counts"] == {"sri_flyttad": 1, "rundata_flyttad": 1, "sri_forsvunnen": 1, "rundata_forsvunnen": 1}
    assert {x["signum"]: x["kind"] for x in d["rows"]} == {"U 1": "sri_flyttad", "U 2": "rundata_flyttad",
                                                           "U 3": "sri_forsvunnen", "U 5": "rundata_forsvunnen"}
    assert next(x for x in d["rows"] if x["signum"] == "U 3")["sri"]["page"] == "7"


# --- the question list stays local ------------------------------------------------------------------------------

def test_question_list_is_not_on_the_public_site():
    """Kortet Öppna frågor i forskningen och dess data får bara finnas i den lokala appen (PUBLICERINGSPLAN.md)."""
    site = open(os.path.join(ROOT, ".github", "workflows", "site.yml"), encoding="utf-8").read()
    assert 'rm -rf "web/src/app/(app)"' in site and "web/src/app/api" in site  # the public build drops the app
    luckor = os.path.join(ROOT, "web", "src", "app", "(app)", "luckor")
    assert os.path.exists(os.path.join(luckor, "_delar", "fragor.tsx"))
    # nothing outside the app's pages asks for the question list
    hits = subprocess.run(["grep", "-rl", "research/questions", os.path.join(ROOT, "web", "src")],
                          capture_output=True, text=True).stdout.split()
    assert hits and all("/(app)/" in h for h in hits), hits
    # the public sitemap lists no app page, and the built data lies in the git-ignored cache
    sm = open(os.path.join(ROOT, "web", "src", "app", "sitemap.ts"), encoding="utf-8").read()
    assert "PUBLIC_PAGES" in sm and '"/luckor"' not in re.search(r"PUBLIC_PAGES = new Set\(\[(.*?)\]\)", sm, re.S).group(1)
    for p in (fragelista.PAGES, rk.SRI_MENTIONS):
        rel = os.path.relpath(p, ROOT)
        assert subprocess.run(["git", "check-ignore", "-q", rel], cwd=ROOT).returncode == 0, rel
    # no question title in the English catalogues or the website's content
    if fragelista.available():
        titles = [q["titel"] for q in fragelista.questions_raw()]
        for rel in ("web/src/i18n/en.json", "web/src/i18n/en.public.json", "web/content/articles.json",
                    "web/content/news.json", "web/public/artiklar-sok.json"):
            p = os.path.join(ROOT, rel)
            if os.path.exists(p):
                text = open(p, encoding="utf-8").read()
                leaked = [t for t in titles if len(t) > 25 and t in text]
                assert not leaked, (rel, leaked[:3])


def test_fold_signum_matches_caches():
    assert fold_signum("Sö 113") == "so113"
