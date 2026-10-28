"""Människorna (src/people.py): resarnas kön ur texten, relationerna med och utan namn, och kontrollen mot handkodningen."""
import json
import os

from src import people

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _recs():
    d = json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))
    return {r["signum"]: r for r in (d if isinstance(d, list) else d["inscriptions"])}


def test_raiser_gender_from_the_text():
    by, lex = _recs(), {}
    r = people.stone(by["Sö 179"], lex)  # Tóla ... in memory of her son Haraldr
    assert (r["resare_k"], r["resare_m"], r["rel_barn"]) == (1, 0, 1)
    r = people.stone(by["U 1154"], lex)  # Freygerðr ... in memory of Ígull, her husbandman
    assert (r["resare_k"], r["rel_make"]) == (1, 1)
    r = people.stone(by["Ög 42"], lex)  # Hrólfr ... in memory of Þorsteinn, his son
    assert (r["resare_m"], r["resare_k"], r["rel_barn"]) == (1, 0, 1)


def test_relation_without_a_name():
    r = people.stone(_recs()["U 101"], {})  # Hemingr and Jarlabanki ... in memory of their father; Ástríðr ... her sons
    assert (r["rel_foralder"], r["rel_barn"], r["resare_k"]) == (1, 1, 1)


def test_hand_coding_is_stored():
    d = json.load(open(os.path.join(ROOT, "data", "people_check.json"), encoding="utf-8"))
    assert len(d["kodning"]) == 60 and len(d["kodning2"]) == 40
