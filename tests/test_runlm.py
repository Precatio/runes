"""Sannolikhetsmodellen för runtext (src/runlm.py): stavning, samma ord i olika normaliseringar och avkodning."""
import math

from src.runlm import Model, carved_groups, decode, key, pairs, sections


def _rec(signum, translit, norm):
    return {"signum": signum, "period": "V", "transliteration": translit, "normalization": norm}


RECS = [_rec(f"T {i}", "þurir : raisþi : stain : þansi : aft : faþur : sin", "Þorir ræisti stæin þannsi æft faður sinn.")
        for i in range(6)] + [
    _rec("T 10", "kunar : raisþi : stain : aft : sun : sin", "Gunnarr ræisti stæin æft sun sinn."),
    _rec("T 11", "asa : raisþi : stain : þansi : aft : sun : sin", "Asa ræisti stæin þannsi æft sun sinn."),
]


def test_same_word_in_different_normalizations():
    assert key("stæinn") == key("sten") == key("steinn")
    assert key("sin") == key("sinn") and key("þøsi") == key("þausi") and key("faður") == key("faþur")
    assert key("æftiR") == key("eptir")
    assert key("isi") != key("es") and key("lifa") != key("lefa")


def test_sections_drop_alternative_readings_and_groups_follow_the_dividers():
    assert [lab for lab, _ in sections("§P a : b §Q c : d")] == ["-"]
    assert carved_groups("þurir raisþi : stain¶þansi") == ["þurirraisþi", "stainþansi"]
    assert pairs(RECS[0])[:3] == [("þurir", "Þorir"), ("raisþi", "ræisti"), ("stain", "stæin")]


def test_spelling_learned_from_the_carvers():
    m = Model(RECS)
    spellings = m.spell.expand("stæin")
    assert max(spellings, key=spellings.get) == "stain"
    assert abs(sum(spellings.values()) - 1) < 1e-9


def test_decoding_finds_the_words_inside_an_undivided_group():
    m = Model(RECS[:-1])  # Asa's stone is not in training
    logZ, path, post, text = decode(m, ["asaraisþistainþansi", "aft", "sunsin"])
    words = [w for _, _, w, _ in path]
    assert words[1:] == ["ræisti", "stæin", "þannsi", "æft", "sun", "sinn"]
    assert all(0 <= p <= 1 + 1e-9 for _, _, _, p in path) and math.isfinite(logZ)
    # the posteriors of the words that cover each rune sum to at most one
    for i in range(len(text)):
        assert sum(p for (a, b, _), p in post.items() if a <= i < b) <= 1 + 1e-6


def test_a_divider_is_evidence_for_a_word_boundary():
    m = Model(RECS)
    with_div = decode(m, ["stain", "þansi"])[0]
    without = decode(m, ["stainþansi"])[0]
    assert m.d > 0.5 and with_div > without
