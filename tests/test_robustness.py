"""Robusthetstrappan (src/robustness.py): facit, underlaget, den gemensamma BH-justeringen och "Nytt" först efter
bekräftelse (src/pattern_registry.py)."""
import pytest

from src import pattern_registry, robustness as rb


def _rung(holds, p=0.01):
    return {"or": 2.0, "ci": [1.2, 3.3], "p": p, "direction": 1, "n": 100, "holds": holds}


def _result(halves=(True, True), p=0.001):
    return {"n": 400, "k": 120, "direction": 1,
            "rungs": {"raw": _rung(True), "adjusted": _rung(True, p), "carver": _rung(True), "parish": _rung(False, 0.2),
                      "half_A": _rung(halves[0]), "half_B": _rung(halves[1]),
                      "lopo": {**_rung(True), "without": "U", "flips": []}},
            "effect": {"share_lo": 0.2, "share_hi": 0.35, "diff": 0.15, "diff_ci": [0.08, 0.22]}}


def test_confusion_counts_right_and_wrong_among_yes_and_no():
    c = rb._confusion([(1, 1), (1, 1), (1, 0), (0, 0), (0, 0), (0, 1)])
    assert c == {"ppv": [2, 1], "npv": [2, 1], "n": 6}


def test_feature_mirrors_change_r():
    f = rb._feature("ai_alla")
    assert f({"trait_ai_alla": "båda"}) == 1 and f({"trait_ai_alla": "diftong"}) == 0
    assert f({"trait_ai_alla": ""}) is None
    # cross only where the text is legible, as in r/change.R
    cross = rb._feature("cross")
    assert cross({"cross": 1, "trait_bon": None}) is None and cross({"cross": 1, "trait_bon": "nej"}) == 1


def test_summarize_counts_rungs_and_first_failure():
    s = rb.summarize(_result(), {"x_lo": 0})
    assert (s["passed"], s["tested"]) == (6, 7)
    assert s["first_fail"] == "parish" and s["halves"] is True and s["time"] is False
    assert [r["key"] for r in s["rungs"]][:3] == ["raw", "adjusted", "carver"]


def test_summarize_without_adjusted_rung_is_none():
    assert rb.summarize({"rungs": {"raw": _rung(True), "adjusted": {"skipped": "för få stenar"}}}, None) is None


def test_annotate_global_bh_and_confirmation():
    pats = [{"topic": "Förändring", "key": "a", "replicated": True},
            {"topic": "Förändring", "key": "b", "replicated": True},
            {"topic": "Geografi", "key": "own", "replicated": True, "significance": {"kind": "p", "value": 0.04}},
            {"topic": "Attribuering", "key": "model"}]
    rob = {"patterns": {"Förändring|a": _result(), "Förändring|b": _result(halves=(True, False))}, "specs": {}}
    out = rb.annotate(pats, rob)
    a, b, own, model = out
    assert a["ladder"]["p"] == pytest.approx(0.001) and a["confirmed"] is True
    assert b["confirmed"] is False  # one half fails
    # three p-values (0.001, 0.001, 0.04): BH q for the largest is the p itself
    assert own["q_global"] == pytest.approx(0.04) and own["confirmed"] is True and "ladder" not in own
    assert model["q_global"] is None and model["confirmed"] is None


def test_new_badge_waits_for_confirmation(tmp_path, monkeypatch):
    monkeypatch.setattr(pattern_registry, "PATH", str(tmp_path / "reg.json"))
    pattern_registry.update([], "2026-10-01")  # seed an empty registry so that later patterns count as new
    pats = [{"topic": "T", "key": "yes", "status": "s", "confirmed": True},
            {"topic": "T", "key": "no", "status": "s", "confirmed": False},
            {"topic": "T", "key": "cannot", "status": "s", "confirmed": None},
            {"topic": "T", "key": "old", "status": "s"}]
    out = {p["key"]: p.get("new") for p in pattern_registry.annotate(pats, "2026-10-29")}
    assert out == {"yes": "nytt", "no": "obekräftat", "cannot": "obekräftat", "old": "nytt"}


def test_limitation_is_never_new(tmp_path, monkeypatch):
    monkeypatch.setattr(pattern_registry, "PATH", str(tmp_path / "reg.json"))
    pattern_registry.update([], "2026-10-01")
    pats = [{"topic": "T", "key": "null", "status": "begränsning", "confirmed": False}]
    assert pattern_registry.annotate(pats, "2026-10-29")[0].get("new") is None
