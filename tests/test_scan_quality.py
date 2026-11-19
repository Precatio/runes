"""Kvalitetsbetyget per skanning (src/scan_quality.py och web/src/lib/scanQuality.ts, 2026-11-19)."""
import json

import numpy as np
import pytest

from src import scan_quality as sq
from tests.ts_runner import run_ts

CASES = [
    {"mesh_point_spacing_mm": 0.4, "hole_fraction": 0.0, "noise_mm": 0.3},
    {"mesh_point_spacing_mm": 0.5, "hole_fraction": 0.02, "noise_mm": 0.3},
    {"mesh_point_spacing_mm": 0.6, "hole_fraction": 0.01, "noise_mm": 0.6},
    {"mesh_point_spacing_mm": 0.6, "hole_fraction": 0.15},
    {"mesh_point_spacing_mm": 1.0, "hole_fraction": 0.10},
    {"mesh_point_spacing_mm": 1.13},
    {"mesh_point_spacing_mm": 0.43, "noise_mm": 0.39},
    {"hole_fraction": 0.0},
    {},
    {"mesh_point_spacing_mm": float("nan"), "hole_fraction": 0.0},
]


def test_limits_are_the_protocol_and_documented_ones():
    from src import protocol
    assert sq.SPACING_GOOD_MM == protocol.MAX_MESH_SPACING_MM  # the protocol's recommendation, set before
    assert sq.SPACING_OK_MM == 2 * protocol.MAX_MESH_SPACING_MM
    assert (sq.HOLES_GOOD, sq.HOLES_OK) == (0.02, 0.10)


@pytest.mark.parametrize("params, klass", [
    (CASES[0], "god"), (CASES[1], "god"), (CASES[2], "godtagbar"), (CASES[3], "svag"), (CASES[4], "godtagbar"),
    (CASES[5], "svag"), (CASES[6], "god"), (CASES[7], "okänd"), (CASES[8], "okänd"), (CASES[9], "okänd"),
])
def test_grade_is_the_worst_part(params, klass):
    g = sq.grade(params)
    assert g["klass"] == klass
    assert g["label"] == sq.LABEL[klass]
    assert [p["key"] for p in g["parts"]] == ["punktavstånd", "hål", "brus"]
    assert g["parts"][2]["klass"] is None  # noise is shown, not graded


def test_grade_says_what_it_is_built_on():
    g = sq.grade(CASES[6])
    assert "här bara punktavståndet" in g["text"] and "0,43 mm" in g["text"] and "0,39 mm" in g["text"]
    g = sq.grade(CASES[3])
    assert g["text"].startswith("Svag") and "15,0 %" in g["text"]


def test_hole_fraction_counts_gaps_not_sparse_points():
    valid = np.zeros((100, 100), bool)
    valid[10:90, 10:90] = True
    assert sq.hole_fraction(valid) == 0.0
    sparse = valid.copy()
    sparse[10:90:2, 10:90:2] = False  # every other cell empty: points sparser than the grid, not a hole
    assert sq.hole_fraction(sparse) == 0.0
    holed = valid.copy()
    holed[40:60, 40:60] = False  # a 20 × 20 hole in an 80 × 80 stone
    f = sq.hole_fraction(holed)
    assert 0.04 < f < 0.07
    assert sq.holes_class(f) == "godtagbar"
    assert np.isnan(sq.hole_fraction(np.zeros((5, 5), bool)))


def test_browser_and_server_agree():
    cases = [{k: (None if isinstance(v, float) and v != v else v) for k, v in c.items()} for c in CASES]
    got = run_ts("scanQuality", f"console.log(JSON.stringify({json.dumps(cases)}.map(c => M.scanQuality(c))));")
    for c, js in zip(cases, got):
        py = sq.grade(c)
        assert js["klass"] == py["klass"], c
        assert js["label"] == py["label"]
        assert js["text"] == py["text"], (js["text"], py["text"])
