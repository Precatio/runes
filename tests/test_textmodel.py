"""Sannolikhetsmodellen i appen (src/textmodel.py): hur inskriften delas upp, vilken modell som läser den och vad som
svaras utan att någon modell behöver byggas."""
from src import textmodel


def test_lost_runes_become_gaps_and_lost_text_breaks_the_reading():
    groups, breaks = textmodel.text_groups("§A þorka- : -u- : ---...n-...- : ybir : risti")
    assert groups == ["þorka?", "?u?", "???", "n?", "?", "ybir", "risti"]
    # '...' (text lost to an unknown extent) breaks the reading after the group before it; the end of a section too
    assert 2 in breaks and 3 in breaks and breaks[-1] == len(groups) - 1


def test_a_stone_is_always_read_by_a_model_that_has_not_seen_it():
    parts = {textmodel.fold_of(s) for s in ("U 1072", "Sö 113", "Ög 136", "DR 42", "Vg 119", "U 344")}
    assert parts <= set(range(textmodel.K)) and len(parts) > 1
    assert textmodel.fold_of("U 1072") == textmodel.fold_of("U 1072")


def test_medieval_inscriptions_are_not_read(monkeypatch):
    monkeypatch.setattr(textmodel, "_data", {})
    monkeypatch.setattr(textmodel, "bundle", lambda k: (_ for _ in ()).throw(AssertionError("no model for this")))
    rec = {"signum": "X 1", "period": "M", "transliteration": "þorkil : risti", "normalization": "Þorkell risti"}
    monkeypatch.setattr(textmodel.rl, "load_rundata", lambda: [rec])
    monkeypatch.setattr(textmodel.rl, "edda_tokens", lambda: [])
    monkeypatch.setattr(textmodel.rg, "load_danish", lambda recs: {})
    out = textmodel.analyze("X 1")
    assert out["available"] is False and "vikingatida" in out["reason"]
