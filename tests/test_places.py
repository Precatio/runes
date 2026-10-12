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


def test_scan_patterns():
    from src import r_findings as rf
    cell = lambda f, k, o, q, rep, **kw: {"feature": f, "kind": k, "radius_km": 2, "n_near": 166, "share_near": 0.66,
                                          "share_far": 0.52, "n": 1563, "or": o, "lo": o * 0.9, "hi": o * 1.1, "p": q / 10,
                                          "q_bh": q, "halves": {"replicated": rep}, **kw}
    sc = {"available": True, "n_tests": 117,
          "cells": [cell("kristen", "central", 1.24, 0.001, True, time={"n": 765, "or": 1.23, "p": 0.009}),
                    cell("neutral", "central", 0.81, 0.001, True),          # the mirror of kristen: left out
                    cell("bon", "cult_a", 1.26, 0.047, False),
                    cell("arv", "vag", 1.1, 0.4, False)]}
    pats = {p["key"]: p for p in rf._scan(sc)}
    assert set(pats) == {"scan_kristen_central", "scan_indications"}
    k = pats["scan_kristen_central"]
    assert k["status"] == "mönster att pröva" and "vanligare ju närmare centralortsnamn" in k["text"]
    assert "med tiden konstant (oddskvot 1,23)" in k["text"] and "eliten" in k["hypothesis"]
    assert "kristen bön och teofora ortnamn" in pats["scan_indications"]["text"]
    assert rf._scan({"available": False}) == []


def test_hotspot_patterns():
    from src import r_findings as rf
    cl = lambda center, q, rep: {"center": center, "lat": 59.6, "lon": 17.2, "radius_km": 22, "n": 53, "cases": 32,
                                 "rate_in": 0.604, "rate_out": 0.124, "rr": 4.86, "p": 0.001, "q_bh": q,
                                 "provinces": {"U": 51, "Vs": 2}, "stones": ["U 768"], "halves": {"replicated": rep}}
    h = {"patterns": [
        {"key": "r_for_R", "moran": {"i": 0.17, "p": 1e-20, "q_bh": 1e-19}, "clusters": [cl("U 768", 0.014, True)]},
        {"key": "arv", "moran": {"i": 0.0, "p": 0.4, "q_bh": 0.45}, "clusters": [cl("U 96", 0.09, True)]},
        {"key": "o_runa", "moran": {"i": 0.16, "p": 1e-14, "q_bh": 1e-13}, "clusters": [cl("U 921", 0.09, False)]}]}
    pats = {p["key"]: p for p in rf._hotspots(h)}
    assert set(pats) == {"hotspot_r_for_R_U 768", "hotspot_arv_U 96"}          # not replicated: left out
    assert pats["hotspot_r_for_R_U 768"]["status"] == "mönster att pröva"
    assert pats["hotspot_arv_U 96"]["status"] == "indikation"
    assert "Klustrets mitt: U 768." in pats["hotspot_r_for_R_U 768"]["text"] and "U 51" in pats["hotspot_r_for_R_U 768"]["text"]
