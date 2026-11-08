"""Ritade slingor som finns men inte kan föras över ska sägas, inte tyst ersättas av slingmodellen
(rune_bands.drawn_problem; hittat 2026-11-08: 29 av 95 granskade filer saknade djupbildens origo)."""
import json
from types import SimpleNamespace

import numpy as np

from src import rune_bands


def _setup(tmp_path, monkeypatch, meta_extra):
    depth, band = tmp_path / "djup" / "serie", tmp_path / "band" / "serie"
    depth.mkdir(parents=True)
    band.mkdir(parents=True)
    meta = {"sha256": "abc", "normal": [0, 0, 1], "up": [0, 1, 0], "shape": [10, 10], "res_mm": 0.6, **meta_extra}
    (depth / "sten.json").write_text(json.dumps(meta))
    (band / "sten.json").write_text(json.dumps({"status": "granskad", "bands": [{"points": [[1, 1], [5, 5]], "height": 2}]}))
    monkeypatch.setattr(rune_bands, "DEPTH_DIR", str(tmp_path / "djup"))
    monkeypatch.setattr(rune_bands, "BAND_DIR", str(tmp_path / "band"))


def test_missing_origin_is_said(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch, {})
    hf = SimpleNamespace(n=np.array([0.0, 0.0, 1.0]))
    assert "origo saknas" in rune_bands.drawn_problem("abc", hf)
    assert rune_bands.drawn_problem("annan", hf) is None and rune_bands.drawn_problem(None, hf) is None


def test_a_view_too_far_off_is_said_and_a_good_one_is_not(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch, {"a0": 0.0, "b0": 0.0})
    tilted = np.array([0.0, np.sin(np.radians(35)), np.cos(np.radians(35))])
    assert "35°" in rune_bands.drawn_problem("abc", SimpleNamespace(n=tilted))
    assert rune_bands.drawn_problem("abc", SimpleNamespace(n=np.array([0.0, 0.0, 1.0]))) is None
