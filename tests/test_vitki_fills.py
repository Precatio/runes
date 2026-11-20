"""Vitkis ifyllningar (src/vitki_fills.py): lagringen ovanpå Rundata, statusflödet och spärren mot att
sannolikhetsmodellen tränas eller prövas på sina egna svar."""
import glob
import re
import json
import os

import pytest

from src import runlm as rl
from src import vitki_fills as vf

ADMIN = {"uid": "founder", "email": "grundare@example.org"}
GAP = {"kind": "gap", "number": 0, "group": 2, "start": 1, "end": 3, "carved": "s??in", "rundata_n": 2, "n": 2,
       "width": 2, "preserved_inside": [None, None], "key": "2:1:3"}


def _entry(**kw):
    return {"signum": "X 1", "gap": GAP, "fill": "ta", "word": "stæin", "method": "sannolikhetsmodellen",
            "model_version": "textmodel-19", "p": 0.92, "p_model": 0.97, "status": "förslag",
            "comment": "Passar spåren i skanningen.", "evidence": [{"kind": "skanning", "ref": "Sö 1, 3D-fil"}], **kw}


def test_a_filling_is_stored_with_its_provenance_and_rundata_untouched(tmp_path):
    p = str(tmp_path / "f.json")
    rec = vf.add(_entry(), ADMIN, path=p)
    data = json.load(open(p, encoding="utf-8"))
    assert data["licens"] == "CC BY 4.0" and data["fills"][0]["id"] == rec["id"]
    x = data["fills"][0]
    assert (x["signum"], x["fill"], x["word"], x["method"], x["model_version"], x["p"]) == \
        ("X 1", "ta", "stæin", "sannolikhetsmodellen", "textmodel-19", 0.92)
    assert x["gap"]["carved"] == "s??in" and x["gap"]["n"] == 2 and x["evidence"][0]["kind"] == "skanning"
    assert x["history"][0]["by"] == "grundare@example.org" and x["status"] == "förslag"
    assert "s[ta]in = stæin" in vf.provenance("X 1", path=p) and "92 %" in vf.label(x)
    # nothing is ever written to Rundata's file
    assert not any("vitki" in k for k in json.load(open(rl.RUNDATA_JSON)).keys()) if os.path.exists(rl.RUNDATA_JSON) else True


def test_a_filling_needs_a_comment_and_runes_that_fit_the_gap(tmp_path):
    p = str(tmp_path / "f.json")
    for bad in (_entry(comment=" "), _entry(fill="tai"), _entry(fill="T4"), _entry(status="okänd"), _entry(method="gissning"),
                _entry(status="avvisad"), _entry(evidence=[{"kind": "sri", "ref": ""}])):
        with pytest.raises(ValueError):
            vf.add(bad, ADMIN, path=p)
    # a preserved rune inside the gap stays
    g = dict(GAP, width=4, preserved_inside=[None, "f", "a", None])
    with pytest.raises(ValueError):
        vf.add(_entry(gap=g, fill="tfoþ"), ADMIN, path=p)
    assert vf.add(_entry(gap=g, fill="tfaþ"), ADMIN, path=p)["fill"] == "tfaþ"


def test_the_status_moves_with_who_when_and_why(tmp_path):
    p = str(tmp_path / "f.json")
    rec = vf.add(_entry(), ADMIN, path=p)
    with pytest.raises(ValueError):
        vf.set_status(rec["id"], "bekräftad", ADMIN, "", path=p)  # a comment is required
    ok = vf.set_status(rec["id"], "bekräftad", ADMIN, "SRI bekräftar k-staven.", [{"kind": "sri", "ref": "SRI 3, s. 112"}], path=p)
    assert ok["status"] == "bekräftad" and [h["status"] for h in ok["history"]] == ["förslag", "bekräftad"]
    assert {e["kind"] for e in ok["evidence"]} == {"skanning", "sri"}
    # one confirmed filling per gap: a second must wait until the first is rejected
    other = vf.add(_entry(fill="ka", word="skæin"), ADMIN, path=p)
    with pytest.raises(ValueError):
        vf.set_status(other["id"], "bekräftad", ADMIN, "Annan läsning.", path=p)
    vf.set_status(rec["id"], "avvisad", ADMIN, "Ny skanning visar annat.", path=p)
    assert vf.set_status(other["id"], "bekräftad", ADMIN, "Annan läsning.", path=p)["status"] == "bekräftad"
    # rejected fillings stay in the file but are not shown
    assert [x["fill"] for x in vf.for_stone("X 1", path=p)] == ["ka"]
    assert len(vf.load(p)["fills"]) == 2
    with pytest.raises(KeyError):
        vf.set_status("finns-inte", "avvisad", ADMIN, "x", path=p)


def test_confirmed_words_are_counted_only_on_request(tmp_path):
    p = str(tmp_path / "f.json")
    rec = vf.add(_entry(), ADMIN, path=p)
    assert vf.apply_words("X 1", path=p) == []  # a proposal is not used
    vf.set_status(rec["id"], "bekräftad", ADMIN, "ok", path=p)
    assert vf.apply_words("X 1", path=p) == [("stæin", False)]


def test_the_model_is_never_trained_on_vitkis_fillings():
    rec = {"signum": "T 1", "period": "V", "transliteration": "þurir : raisþi : stain",
           "normalization": "Þorir ræisti stæin."}
    rl.Model([rec, rec])  # Rundata's records: fine
    with pytest.raises(ValueError):
        rl.Model([rec, vf.mark(rec)])
    with pytest.raises(ValueError):
        rl.Model([rec], spelling_recs=[vf.mark(rec)])


def test_no_model_training_or_validation_code_reads_the_fillings():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    files = [os.path.join(root, "src", f) for f in ("runlm.py", "textmodel.py", "rungloss.py", "trace_reader.py")]
    files += glob.glob(os.path.join(root, "scripts", "runlm_*.py")) + glob.glob(os.path.join(root, "scripts", "textmodel_*.py"))
    files += [os.path.join(root, "scripts", "blindtest.py")]
    for f in files:
        if os.path.exists(f):
            src = open(f, encoding="utf-8").read()
            # neither the module nor its file is read (a comment naming them is fine)
            assert not re.search(r"^\s*(from\s+\S+\s+)?import\s+.*vitki_fills", src, re.M), f
            assert "vitki_ifyllningar.json" not in src.replace("data/vitki_ifyllningar.json)", ""), f
    # Rundata as the model loads it carries no fillings
    if os.path.exists(rl.RUNDATA_JSON):
        assert not any(r.get(vf.FILLED_MARK) for r in rl.load_rundata())


def test_api_saving_needs_an_admin(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient
    from api.auth import require_admin
    from api.main import app
    import api.routers.textmodel as router
    from src import textmodel_overview as ov
    monkeypatch.setattr(vf, "FILE", str(tmp_path / "f.json"))
    monkeypatch.setattr(router, "canonical", lambda s: s)
    monkeypatch.setattr(ov, "locate", lambda s, g, n=None, kind="gap": GAP)
    monkeypatch.setattr(ov, "candidate", lambda s, g, f, n=None, kind="gap": {"fill": f, "word": "stæin", "name": False,
                                                                             "p_word": 0.92, "p_model": 0.97})
    c = TestClient(app)
    body = {"signum": "X 1", "gap": 0, "fill": "ta", "status": "förslag", "comment": "Passar.",
            "evidence": [{"kind": "sri", "ref": "SRI 3"}]}
    assert c.post("/api/textmodel/fills", json=body).status_code == 403
    app.dependency_overrides[require_admin] = lambda: ADMIN
    try:
        r = c.post("/api/textmodel/fills", json=body)
        assert r.status_code == 200, r.text
        x = r.json()
        # the probability and version come from the server's overview, not from the call
        assert x["p"] == 0.92 and x["model_version"] and x["label"].startswith("ifyllt av Vitki")
        assert c.post("/api/textmodel/fills", json={**body, "comment": ""}).status_code == 422
        r = c.post(f"/api/textmodel/fills/{x['id']}/status", json={"status": "bekräftad", "comment": "SRI stämmer."})
        assert r.status_code == 200 and r.json()["status"] == "bekräftad"
        listed = c.get("/api/textmodel/fills", params={"signum": "X 1"}).json()
        assert [f["fill"] for f in listed["fills"]] == ["ta"] and listed["license"] == "CC BY 4.0"
    finally:
        app.dependency_overrides.pop(require_admin, None)


def test_word_counts_use_the_fillings_only_when_switched_on(monkeypatch, tmp_path):
    from api.routers import rundata as rd
    p = str(tmp_path / "f.json")
    monkeypatch.setattr(vf, "FILE", p)
    rec = vf.add(_entry(signum="Sö 206", word="kumbl"), ADMIN, path=p)  # a word Rundata's text of Sö 206 lacks
    vf.set_status(rec["id"], "bekräftad", ADMIN, "ok", path=p)
    rd._words.cache_clear()
    plain = rd.words(area="Sö", top=1000)
    withf = rd.words(area="Sö", top=1000, fills=True)
    assert plain["vitki_fills"] is None and withf["vitki_fills"]["used"] == 1
    n = lambda out: next((w["stones"] for w in out["words"] if w["w"] == "kumbl"), 0)  # noqa: E731
    assert n(withf) == n(plain) + 1
