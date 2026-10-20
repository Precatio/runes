import pytest

from src import runor


def test_runes_normalises_both_editions():
    assert runor.runes("in ulfR : hafiR ...") == runor.runes("in ulfʀ hafiʀ …")
    assert runor.runes("§P a b §Q c d") == runor.runes("a b")


def test_runor_record_for_a_known_stone():
    if not runor.available():
        pytest.skip("Runor 2020 är inte skördat på maskinen")
    from api.rundata import store
    rec = store().get("Sö 113")
    r = runor.for_inscription(rec)
    assert r and r["edition"].startswith("Runor") and isinstance(r["notes"], list)
    assert r["original_location"] in (True, False, None)
