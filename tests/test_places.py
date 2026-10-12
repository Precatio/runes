"""Platser kring runstenarna (src/places.py): provet nära mot övriga och stenens landskap."""
import pytest

from src import places


def test_near_test_counts_and_mantel_haenszel():
    # Two provinces; in both, the pattern is twice as common near the place
    rows = ([("U", 1, 1.0)] * 10 + [("U", 0, 1.0)] * 10 + [("U", 1, 5.0)] * 20 + [("U", 0, 5.0)] * 60
            + [("Sö", 1, 0.5)] * 6 + [("Sö", 0, 0.5)] * 4 + [("Sö", 1, 9.0)] * 10 + [("Sö", 0, 9.0)] * 30)
    r = places.near_test(rows, 2)
    assert r["n_near"] == 30 and r["n_far"] == 120 and r["k_near"] == 16 and r["k_far"] == 30
    assert r["share_near"] == pytest.approx(16 / 30, abs=1e-3) and r["strata"] == 2
    assert r["or_mh"] > 2 and r["p_mh"] < 0.05
    assert places.near_test(rows[:3], 2) is None            # too few stones near and far


def test_near_test_ignores_missing_distances():
    rows = [("U", 1, None)] * 50 + [("U", 1, 1.0)] * 6 + [("U", 0, 4.0)] * 6
    r = places.near_test(rows, 2)
    assert r["n_near"] + r["n_far"] == 12


@pytest.mark.skipif(not places.available(), reason="platserna är inte hämtade (scripts/fetch_place_names.py)")
def test_landscape_lists_nearest_places():
    from api.rundata import store
    out = places.landscape(store().get("U 1161"))
    keys = {r["key"] for r in out["rows"]}
    assert out["signum"] == "U 1161" and out["moved"] is False and "cult_a" in keys
    assert all(r["km"] >= 0 for r in out["rows"])
