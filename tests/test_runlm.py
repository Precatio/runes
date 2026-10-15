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


def test_dating_strings_and_epochs():
    from src.runlm import epoch, years
    assert years("V 1065-1075") == (1065, 1075) and years("V s 1000-t") == (1066, 1099)
    assert years("V inte före 915/920") == (915, 965) and years("V Helnæs-Gørlev") == (750, 900)
    assert epoch({"period": "V", "dating": "V 800-t"}) == "800"
    assert epoch({"period": "V", "dating": "V", "style": "Pr4"}) == "1100"
    assert epoch({"period": "V", "dating": "V 800-900-t"}) is None  # too wide to place
    assert epoch({"period": "M", "dating": "M"}) == "M"


def test_alignment_survives_damaged_and_restored_words():
    from src.runlm import align
    got = align(["þurir", "...", "stain", "þansi", "----", "faþur"], ["Þorir", "ræisti", "stæin", "þannsi", "æft", "faður"])
    assert ("þurir", "Þorir") in got and ("stain", "stæin") in got and ("faþur", "faður") in got
    assert all(a[0] != "." and a[0] != "-" for a, _ in got)


def test_epochs_are_weighed_by_how_probable_the_text_is():
    from src.runlm import EPOCHS, decode_epochs
    early = [dict(r, dating="V 800-t", signum=f"E {i}") for i, r in enumerate(RECS[:4])]
    late = [_rec(f"L {i}", "þurir : rist : stin : þansi : eftiR : faþur : sin", "Þorir ræisti stæin þannsi æftiR faður sinn.")
            for i in range(4)]
    for r in late:
        r["dating"] = "V 1100-t"
    m = Model(early + late, contexts=True, aligned=True)
    _, path, post, text, ep_post, ll = decode_epochs(m, ["þurir", "rist", "stin", "þansi", "eftiR", "faþur", "sin"])
    assert abs(sum(ep_post.values()) - 1) < 1e-9 and set(ll) == set(EPOCHS)
    assert ep_post["1100"] > ep_post["800"]


def test_a_name_never_seen_is_composed_of_known_name_elements():
    from collections import Counter
    from src.runlm import NameModel, Spelling
    seen = Counter({"þorbiorn": 3, "þorstæinn": 3, "þorulfR": 3, "asbiorn": 3, "asstæinn": 2, "asulfR": 2,
                    "sigbiorn": 2, "sigulfR": 2, "gunnbiorn": 2, "gunnstæinn": 2, "gunnmundr": 1, "asmundr": 1})
    nm = NameModel(seen, Spelling([]))
    assert {"þor", "as"} <= set(nm.first) and {"biorn", "stæinn"} <= set(nm.second)
    got = nm.candidates("kunulfR")  # Gunnulfr is not among the names seen
    assert "gunnulfR" in got


def test_an_overconfident_dating_is_softened():
    import random
    from src.runlm import EPOCHS, epoch_posterior, fit_temperature
    rng = random.Random(1)
    rows = []
    for _ in range(300):  # the model always says 'sure', but is right only 60 % of the time
        true = rng.choice(EPOCHS)
        said = true if rng.random() < 0.6 else rng.choice([e for e in EPOCHS if e != true])
        rows.append({"true": true, "ll": {e: (0.0 if e == said else -12.0) for e in EPOCHS}, "prior": {e: 1 for e in EPOCHS}})
    T = fit_temperature(rows, use_prior=False)
    p = epoch_posterior(rows[0]["ll"], None, T)
    assert T > 3 and 0.45 < max(p.values()) < 0.75
