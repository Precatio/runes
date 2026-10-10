"""Stenarnas mått ur Kulturmiljöregistret och analysen av storlek mot syfte."""
import numpy as np

from src.stone_dimensions import parse
from src.stone_size import n_names, status_words, stratified_test, within_rank_partial


def test_parse_single_stone():
    d = parse("1) Runsten, ljus granit, 1,5 m h, 0,5-0,6 m br (Ö-V) och 0,2-0,25m tj. Runhöjd 6-8 cm.", "U 344")
    assert d["status"] == "ok" and d["height_m"] == 1.5 and d["width_m"] == 0.55 and d["rune_height_cm"] == 7.0
    assert d["thickness_range_m"] == [0.2, 0.25] and not d["fragment"]


def test_parse_centimetres_and_words():
    d = parse("Runsten, 180 cm hög, 90 cm bred och 25 cm tjock. Runornas höjd 7-9 cm.", "X 1")
    assert d["height_m"] == 1.8 and d["width_m"] == 0.9 and d["thickness_m"] == 0.25 and d["rune_height_cm"] == 8.0


def test_parse_several_objects():
    two = "1) Runsten, 1,5 m h, 0,6 m br. Ristningen vetter mot S. 1,5 m Ö om nr 2 är2)Runsten, 1,6 m h, 0,5 m br."
    assert parse(two, "U 344")["status"] == "oklar (flera föremål)"
    named = "1) Runsten U 343, 2,1 m h, 1 m br. 2) Runsten U 344, 1,5 m h, 0,6 m br."
    assert parse(named, "U 344")["height_m"] == 1.5
    assert parse("Fragment av runsten, 0,4 m l, 0,3 m br.", "X 1")["fragment"]
    assert parse("Runsten, se beskrivning i arkivet.", "X 1")["status"] == "inga mått"


def test_names_and_status_words():
    rec = {"normalization": 'En "UlfR hafiR a "Ænglandi þry giald takit, goðan þegn ok dræng.'}
    assert n_names(rec) == 2 and status_words(rec) == ["dræng", "þegn"]


def _rows(effect, n=300, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(n):
        prov = "A" if i % 2 else "B"
        flag = bool(rng.random() < 0.3)
        # Province B has taller stones; the flag adds `effect` on the log scale within each province
        log_h = np.log(1.4 if prov == "A" else 2.0) + (effect if flag else 0) + rng.normal(0, 0.15)
        rows.append({"province": prov, "log_h": log_h, "flag": flag, "n_words": rng.integers(5, 40), "n_names": 0})
    return rows


def test_stratified_test_finds_planted_effect_and_not_province():
    rows = _rows(np.log(1.2))
    t = stratified_test(rows, np.array([r["flag"] for r in rows]), n_perm=999)
    assert abs(t["ratio"] - 1.2) < 0.05 and t["p"] < 0.01
    rows = _rows(0.0, seed=1)
    t = stratified_test(rows, np.array([r["flag"] for r in rows]), n_perm=999)
    assert t["p"] > 0.05


def test_partial_correlation_removes_length():
    rng = np.random.default_rng(2)
    rows = []
    for i in range(400):
        words = rng.integers(5, 60)
        # Names follow the length of the text only; height follows the length of the text only
        rows.append({"province": "A" if i % 2 else "B", "n_words": words, "n_names": words // 8 + rng.integers(0, 2),
                     "log_h": 0.01 * words + rng.normal(0, 0.1)})
    assert abs(within_rank_partial(rows, "n_names", "n_words", n_perm=499)["rho"]) < 0.1
