"""Litteraturen om de möjliga okända ristarna (src/carver_literature.py): status per grupp efter stenarna."""
from src import carver_literature as cl

LIT = {"attributions": [{"stones": ["A 1", "A 2"], "carver": "X", "kind": "signerad", "source": "SRI V", "page": "s. 1",
                         "text": "t"}],
       "checked": {"stones": ["A 1", "A 2", "A 3", "B 1", "B 2", "B 3"]},
       "nearby_signed": [{"stone": "B 9", "anchor": "B 1", "text": "u"}], "sources": {"SRI V": "Jungner"}}


def test_status_follows_the_stones():
    assert cl.for_group(["A 1", "A 2", "A 3"], LIT)["status"] == "beskriven"
    assert cl.for_group(["A 1", "A 3", "A 4", "A 5"], LIT)["status"] == "delvis beskriven"
    b = cl.for_group(["B 1", "B 2", "B 3"], LIT)
    assert b["status"] == "inget i litteraturen" and b["n_read"] == 3
    assert [x["stone"] for x in b["nearby_signed"]] == ["B 9"]
    assert cl.for_group(["C 1", "C 2"], LIT)["status"] == "inte kontrollerad"


def test_attribution_lists_only_the_groups_stones():
    a = cl.for_group(["A 2", "A 9"], LIT)["attributions"][0]
    assert a["stones"] == ["A 2"] and a["reference"] == "SRI V s. 1" and a["source_full"] == "Jungner"
