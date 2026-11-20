"""Överblicken över en lucka (src/textmodel_overview.py, GET /api/textmodel/candidates): alla kandidater modellen
prövar, med samma modellinställning som appen, och ett valt antal förlorade runor. Prövas med en liten modell."""
import pytest

from src import runlm as rl
from src import textmodel as tm
from src import textmodel_overview as ov


def _rec(signum, translit, norm, obj="runsten"):
    return {"signum": signum, "period": "V", "transliteration": translit, "normalization": norm, "object": obj}


TRAIN = [_rec(f"T {i}", "þurir : raisþi : stain : þansi : aft : faþur : sin", "Þorir ræisti stæin þannsi æft faður sinn.")
         for i in range(6)] + [
    _rec("T 10", "kunar : raisþi : stain : aft : sun : sin", "Gunnarr ræisti stæin æft sun sinn."),
    _rec("T 11", "asa : raisþi : stain : þansi : aft : sun : sin", "Asa ræisti stæin þannsi æft sun sinn."),
    _rec("B 1", "kunar : raisþi : stain", "Gunnarr ræisti stæin.", obj="bleck"),
]
TARGET = _rec("X 1", "þurir : raisþi : s--in : þansi : aft : faþur : s-n", "Þorir ræisti s[tæ]in þannsi æft faður s[i]n.")
MERGED = _rec("X 2", "þurir : raisþi : stain : þansi : af-fa-ur : sin", "Þorir ræisti stæin þannsi æft faður sinn.")


@pytest.fixture
def small(monkeypatch, tmp_path):
    """The overview on a model learned from a handful of texts; the app's reading and calibration as they are."""
    m = rl.Model(TRAIN)
    recs = TRAIN + [TARGET, MERGED]
    data = {"recs": recs, "by": {r["signum"]: r for r in recs}, "V": recs, "sites": [], "G": None, "B": None, "T": None,
            "GL": None}
    monkeypatch.setattr(tm, "_data", data)
    monkeypatch.setattr(tm, "bundle", lambda k: {"model": m})
    monkeypatch.setattr(ov, "CACHE", str(tmp_path))
    monkeypatch.setattr(ov, "_index", {})
    fill = dict(tm.FILL, name_cands=0, near_km=10.0)
    monkeypatch.setattr(tm, "FILL", fill)

    def reading(signum):
        r = data["by"][signum]
        groups, breaks = tm.text_groups(r["transliteration"])
        every = [(gi, x.start(), x.end()) for gi, g in enumerate(groups) for x in __import__("re").finditer(r"\?+", g)]
        _, runs, _, _ = rl.merge_runs(groups, every)
        fills = {(2, 1, 3): "ta", (6, 1, 2): "i"}
        return {"available": True, "gaps": [{"number": i, "group": g, "start": a, "end": e, "best": fills.get((g, a, e))}
                                             for i, (g, a, e) in enumerate(runs)], "open_gaps": []}
    monkeypatch.setattr(tm, "analyze", reading)
    return m


def test_every_candidate_is_returned_with_its_word_and_where_it_came_from(small):
    out = ov.overview("X 1", 0)
    assert out["available"] and out["gap"]["rundata_n"] == 2 and out["gap"]["n"] == 2
    # a gap of two runes: every combination of runes is tried, not only the best five
    assert out["n_tried"] >= 17 * 17 and len(out["candidates"]) == ov.LIMIT and out["truncated"]
    best = out["candidates"][0]
    assert best["fill"] == "ta" and best["word"] == "stæin" and (best["left"], best["right"]) == ("s", "in")
    assert best["origins"] == ["vocabulary"]
    assert any(c["origins"] == ["runes"] for c in out["candidates"])  # proposed rune by rune
    # the words: stæin first; its corpus count leaves the stone itself out (8 + X 2) and counts other objects apart
    w = out["words"][0]
    assert w["word"] == "stæin" and w["corpus"]["stones"] == 9 and w["corpus"]["other_stones"] == 1
    assert "X 1" not in w["corpus"]["examples"]
    # the other gap is filled with the reading's choice while this one is tried
    assert out["context"] == [{"number": 1, "fill": "i"}]


def test_the_list_is_the_same_as_the_apps_own_restore(small):
    """The overview does what restore_all does for the gap: the same candidates and the same probabilities."""
    out = ov.overview("X 1", 0)
    groups = ["þurir", "raisþi", "s??in", "þansi", "aft", "faþur", "sin"]
    res = rl.restore(small, groups, (2, 1, 3), signs=tm.text_groups(TARGET["transliteration"])[1],
                     div_rate=rl.stone_divider_rate(small, ["þurir", "raisþi", "s??in", "þansi", "aft", "faþur", "s?n"],
                                                    tm.text_groups(TARGET["transliteration"])[1]), **tm.FILL)
    assert [(c["fill"], round(c["p_model"], 5)) for c in out["candidates"]] == [(f, round(p, 5)) for f, p in res][:len(out["candidates"])]


def test_a_chosen_length_gives_candidates_of_that_many_runes(small):
    for n in (1, 3, 4):
        out = ov.overview("X 1", 0, n=n)
        assert out["gap"]["n"] == n and out["gap"]["rundata_n"] == 2
        assert out["candidates"] and all(len(c["fill"]) == n for c in out["candidates"])
    assert ov.overview("X 1", 0, n=5)["gap"]["tested"] is False  # longer than the model is tested on
    with pytest.raises(ValueError):
        ov.overview("X 1", 0, n=7)


def test_a_gap_with_preserved_runes_inside_keeps_its_length(small):
    out = ov.overview("X 2", 0)
    assert out["gap"]["adjustable"] is False and out["gap"]["rundata_n"] == 2
    # the preserved f and a stay where they are in every candidate
    assert all(c["fill"][1:3] == "fa" for c in out["candidates"])
    with pytest.raises(ValueError):
        ov.overview("X 2", 0, n=3)


def test_the_result_is_kept_and_read_back(small, monkeypatch):
    first = ov.overview("X 1", 0, n=3)
    monkeypatch.setattr(rl, "restore", lambda *a, **k: (_ for _ in ()).throw(AssertionError("computed again")))
    again = ov.overview("X 1", 0, n=3, limit=5)
    assert again["cached"] and len(again["candidates"]) == 5
    assert again["candidates"] == first["candidates"][:5]


def test_extra_outputs_never_change_what_restore_returns():
    m = rl.Model(TRAIN)
    g = ["þurir", "raisþi", "s???n", "þansi", "aft", "faþur", "sin"]
    plain = rl.restore(m, g, (2, 1, 4), **tm.FILL)
    orig, wr = {}, {}
    seen = rl.restore(m, g, (2, 1, 4), origins=orig, word_runes=wr, **tm.FILL)
    assert plain == seen and set(orig) == {f for f, _ in seen}
    assert wr[seen[0][0]] == ("s", "n")


def test_api_returns_the_overview(small):
    from fastapi.testclient import TestClient
    from api.main import app
    import api.routers.textmodel as router
    c = TestClient(app)
    orig = router.canonical
    router.canonical = lambda s: s
    try:
        r = c.get("/api/textmodel/candidates/X 1", params={"gap": 0, "n": 3, "limit": 10})
        assert r.status_code == 200
        body = r.json()
        assert body["gap"]["n"] == 3 and len(body["candidates"]) == 10 and body["n_tried"] >= 10
        assert all(len(x["fill"]) == 3 for x in body["candidates"])
        assert c.get("/api/textmodel/candidates/X 1", params={"gap": 0, "n": 9}).status_code == 422
        assert c.get("/api/textmodel/candidates/X 1", params={"gap": 5}).status_code == 422
        assert c.get("/api/textmodel/candidates/Q 999").status_code == 404
    finally:
        router.canonical = orig
