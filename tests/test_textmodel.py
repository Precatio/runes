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


def test_the_editors_word_boundaries_and_alternative_reading():
    t = "§P ra... ... ok rahnui (s)--(i)i ok at| |t¶otur s §Q ra... ... ok rahnui (s)--(i) iok at| |t¶otur s"
    # the model gets the runes without the editors' spaces; with words=True the spaces divide the groups too
    groups, _ = textmodel.text_groups(t)
    words, _ = textmodel.text_groups(t, words=True)
    assert groups == ["ra", "okrahnuis??iiokattoturs"]
    assert words == ["ra", "ok", "rahnui", "s??ii", "ok", "at", "totur", "s"]
    # the alternative reading (Q) divides the same runes differently: s--i iok
    alt, _ = textmodel.text_groups(textmodel.alternative_reading(t), words=True)
    assert "".join(alt) == "".join(groups) and alt[3:5] == ["s??i", "iok"]
    assert textmodel.alternative_reading("þorkil : risti") is None


def test_the_words_around_a_gap_are_compared_as_intervals():
    assert textmodel._offsets(["ok", "rahnui", "s??i"]) == [0, 2, 8]
    editors = [(0, 2), (2, 8), (8, 12), (12, 15)]
    # the model's word uis??i (6–12) against the editors' s??i (8–12) around the lost runes 9–11
    assert textmodel._covering(editors, 9, 11) == {(8, 12)} != {(6, 12)}


def test_a_gap_word_is_calibrated_by_its_class():
    k = lambda w: textmodel.rl.key(textmodel.rl.normtok(w))  # noqa: E731
    top, names = {k(w) for w in ("ok", "stæin", "guð")}, {k(w) for w in ("ragnvi", "viseti", "guð")}
    assert textmodel.gap_class("ok", top, names) == 0
    assert textmodel.gap_class("guð", top, names) == 0      # a formula word, though also a name
    assert textmodel.gap_class("§viseti", top, names) == 2 and textmodel.gap_class("viseti", top, names) == 2
    assert textmodel.gap_class("satti", top, names) == 1
    # the fitted coefficients: formula words keep their probability, a sure name is brought down
    G = ([0.5967, -0.7549, -0.4022, 0.6234, 0.4641, 0.5132, -0.108], top, names)
    assert textmodel.calibrate_gap(0.9747, "§viseti", 2, G) < 0.85
    assert textmodel.calibrate_gap(0.999, "ok", 1, G) > 0.98
    assert textmodel.calibrate_gap(0.5, "<unk>", 2, G) == 0.5 and textmodel.calibrate_gap(0.9, "ok", 1, None) == 0.9


def test_names_with_restored_runes_are_names():
    recs = [{"normalization": '"Alfdi[s] let ræisa stæin æftiR "Kar[l](?), sun sinn.'}]
    k = lambda w: textmodel.rl.key(textmodel.rl.normtok(w))  # noqa: E731
    names = textmodel.name_keys(recs)
    assert k("alfdis") in names and k("karl") in names and k("stæin") not in names
