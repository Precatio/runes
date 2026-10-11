"""Jämförelse av två stenar med runan som enhet (src/stone_compare.py)."""
import numpy as np

from src.stone_compare import comparability, groove_comparison
from src.stats import METRICS


def _stone(seed, n_runes=15, per_rune=12, shift=0.0, rune_ids=True):
    """Runorna dras ur samma fördelning; snitten i en runa ligger nära runans eget värde (hög ICC)."""
    rng = np.random.default_rng(seed)
    slices = []
    for r in range(n_runes):
        centre = {m: 100 + shift + rng.normal(0, 8) for m in METRICS}
        for _ in range(per_rune):
            s = {m: centre[m] + rng.normal(0, 1) for m in METRICS}
            if rune_ids:
                s["rune_id"] = r
            slices.append(s)
    return slices


def test_runes_are_the_unit():
    a, b = _stone(1), _stone(2)
    g = groove_comparison(a, b, n_perm=999)
    assert g["unit"] == "runa" and g["n_units"] == [15, 15]
    # Same distribution of runes: no difference when whole runes are permuted
    assert g["overall"]["p_value"] > 0.05
    # Treating the 180 slices as independent finds "differences" that are only the chance draw of runes
    naive = groove_comparison([{k: v for k, v in s.items() if k != "rune_id"} for s in a],
                              [{k: v for k, v in s.items() if k != "rune_id"} for s in b], n_perm=999)
    assert naive["unit"] == "snitt" and naive["overall"]["p_value"] < g["overall"]["p_value"]


def test_real_difference_is_found():
    g = groove_comparison(_stone(1), _stone(3, shift=15), n_perm=999)
    assert g["overall"]["p_value"] < 0.01


def test_comparability_warns_without_rune_ids():
    a, b = _stone(1, rune_ids=False), _stone(2, rune_ids=False)
    g = groove_comparison(a, b, n_perm=99)
    checks = comparability({"feature_type": "rune"}, {"feature_type": "rune"}, g, None, None)
    unit = next(c for c in checks if c["key"] == "enhet")
    assert unit["ok"] is False and "för små" in unit["text"]
    few = groove_comparison(_stone(1, n_runes=8), _stone(2, n_runes=8), n_perm=99)
    runes = next(c for c in comparability({"feature_type": "rune"}, {"feature_type": "rune"}, few, None, None) if c["key"] == "runor")
    assert runes["ok"] is False
