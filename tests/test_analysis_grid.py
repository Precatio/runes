"""Samma rutnät vid jämförelse (src/analysis_grid.py, web/src/lib/analysisGrid.ts, 2026-11-19)."""
import json

from src import analysis_grid as ag
from tests.ts_runner import run_ts

P06 = {"resolution_mm": 0.6, "fixed_resolution": True, "harmonize_mm": None}
P12 = {"resolution_mm": 1.2, "fixed_resolution": True, "harmonize_mm": None}
P085 = {"resolution_mm": 0.853, "fixed_resolution": False, "harmonize_mm": 0}


def test_grid_check_for_two_stones():
    assert ag.comparability_check(P06, dict(P06))["ok"] is True
    c = ag.comparability_check(P06, P12)
    assert c["ok"] is False and c["key"] == "rutnät"
    assert "0,60 mm och 1,20 mm" in c["text"] and "omkring 2°" in c["text"] and "2026-11-19" in c["text"]
    assert ag.comparability_check(P06, {}) is None  # older measurements without a grid: no claim either way
    # harmonisation counts as part of the grid
    assert ag.comparability_check(P06, {**P06, "harmonize_mm": 1.0})["ok"] is False


def test_grid_mix_and_reference_check():
    mix = ag.grid_mix([ag.grid_of(p) for p in (P06, P06, P12, {}, P085)])
    assert mix["mixed"] and mix["unknown"] == 1
    assert [g["n"] for g in mix["groups"]] == [2, 1, 1]
    r = ag.reference_check(P06, [P06, P12, P06])
    assert r["mixed"] and "1 av 3 stenar" in r["warning"]
    assert ag.reference_check(P06, [P06, P06])["warning"] is None
    assert ag.reference_check({}, [P06]) is None


def test_compare_endpoint_warns_on_different_grids():
    from fastapi.testclient import TestClient
    from api.main import app
    sl = [{"apex_vinkel_deg": 120 + i, "spårdjup_mm": 2.0, "spårbredd_mm": 10.0, "asymmetri_deg": 1.0,
           "djup_bredd_kvot": 0.2, "bottenradie_mm": 1.0, "ytråhet_mm": 0.1, "rune_id": i % 5 + 1} for i in range(20)]
    body = {"a": {"label": "A", "feature_type": "rune", "slices": sl, "provenance": {"parameters": P06}},
            "b": {"label": "B", "feature_type": "rune", "slices": sl, "provenance": {"parameters": P12}}, "corpus": []}
    res = TestClient(app).post("/api/stats/compare", json=body)
    assert res.status_code == 200, res.text
    grid = [c for c in res.json()["comparability"] if c["key"] == "rutnät"]
    assert grid and grid[0]["ok"] is False
    assert any("analysrutnät" in w for w in res.json()["warnings"])


def test_browser_and_server_agree():
    params = [P06, P12, P085, {}, {**P06, "harmonize_mm": 1.0}]
    got = run_ts("analysisGrid", f"const ps = {json.dumps(params)};"
                 "console.log(JSON.stringify({labels: ps.map(p => M.gridLabel(M.gridOf(p))),"
                 " mix: M.gridMix(ps.map(M.gridOf)), effect: M.GRID_EFFECT_TEXT, remedy: M.GRID_REMEDY_TEXT}));")
    assert got["labels"] == [ag.grid_label(ag.grid_of(p)) for p in params]
    py = ag.grid_mix([ag.grid_of(p) for p in params])
    assert [(g["label"], g["n"]) for g in got["mix"]["groups"]] == [(g["label"], g["n"]) for g in py["groups"]]
    assert got["mix"]["unknown"] == py["unknown"]
    assert got["effect"] == ag.GRID_EFFECT_TEXT and got["remedy"] == ag.GRID_REMEDY_TEXT
