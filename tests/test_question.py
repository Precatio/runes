"""Pröva en egen fråga (src/question.py): statistiken, halvorna, kända mönster och ett nollfall."""
import math
import random

import pytest
from scipy.stats import chi2, chi2_contingency

from src import question as q


def test_mantel_haenszel_one_stratum_is_the_textbook_case():
    a, b, c, d = 30, 20, 15, 35
    n = a + b + c + d
    res = q.mantel_haenszel([(a, b, c, d)])
    assert res["or"] == pytest.approx(a * d / (b * c))
    # Robins–Breslow–Greenland reduces to Woolf's interval for one table
    se = math.sqrt(1 / a + 1 / b + 1 / c + 1 / d)
    assert res["ci"][0] == pytest.approx(res["or"] * math.exp(-1.96 * se))
    assert res["ci"][1] == pytest.approx(res["or"] * math.exp(1.96 * se))
    # The corrected CMH statistic is Yates' chi-square times (n - 1) / n
    yates = chi2_contingency([[a, b], [c, d]], correction=True)[0]
    assert res["p"] == pytest.approx(float(chi2.sf(yates * (n - 1) / n, 1)))
    assert res["direction"] == 1 and res["strata"] == 1


def test_mantel_haenszel_skips_one_sided_strata_and_pools_the_rest():
    t = (12, 8, 6, 14)
    same = q.mantel_haenszel([t, t])
    assert same["or"] == pytest.approx(q.mantel_haenszel([t])["or"])
    assert q.mantel_haenszel([t, (5, 0, 0, 0), (0, 3, 0, 4)])["strata"] == 1
    assert q.mantel_haenszel([(5, 0, 0, 0)])["p"] is None


def _row(signum, province, parish, year=None):
    return {"signum": signum, "province": province, "parish": parish,
            "style_from": year, "style_to": year}


def test_halves_keep_parishes_whole_and_alternate_by_dating():
    rows = [_row("U 1", "U", "Ala", 1000), _row("U 2", "U", "Ala", 1000), _row("U 3", "U", "Bro", 1040),
            _row("U 4", "U", "Cela", 1080), _row("U 5", "U", "", None), _row("Sö 1", "Sö", "Dal", 1060)]
    h = q.halves(rows)
    assert h["U 1"] == h["U 2"] == "A"           # the earliest parish first, whole
    assert h["U 3"] == "B" and h["U 4"] == "A"   # then alternating by mean dating
    assert h["U 5"] == "B"                       # undated last; a stone without parish is its own group
    assert h["Sö 1"] == "A"                      # each province starts over


@pytest.fixture(scope="module")
def prep():
    from api.rundata import store
    from api.routers.orthography import model
    from src import r_bridge as rb
    return q.prepare(rb.corpus_rows(store().inscriptions, model().names))


@pytest.mark.parametrize("a,kind,key,direction", [
    ("at", "landskap", "Sö", 1),          # Ordförrådet: at in Södermanland
    ("monoftong", "landskap", "Vg", 1),   # the map's monophthong cluster in Västergötland
    ("stungna", "tid", 1075, 1),          # dotted runes late (METHODS 1h)
    ("bon", "tid", 1050, -1),             # the prayer falls silent ("Bönen tystnade")
])
def test_known_patterns_hold_in_both_halves(prep, a, kind, key, direction):
    r = q.ask(prep, a, kind, key)
    assert r["verdict"] == "håller", r
    assert r["adjusted"]["direction"] == direction
    assert r["halves"]["replicated"]


def test_definitions_and_too_few_are_refused(prep):
    assert q.ask(prep, "kristen", "drag", "bon")["verdict"] == "kopplade"
    assert q.ask(prep, "bro", "drag", "bro")["verdict"] == "samma"
    assert q.ask(prep, "hednisk", "landskap", "M")["verdict"] == "för få"
    with pytest.raises(ValueError):
        q.ask(prep, "bro", "tid", 1111)


def test_earlier_questions_are_adjusted_together(prep):
    first = q.ask(prep, "fard", "landskap", "Sö")
    later = q.ask(prep, "fard", "landskap", "Sö", earlier=[0.5] * 19)
    assert later["n_questions"] == 20
    assert later["q"] == pytest.approx(min(1.0, first["adjusted"]["p"] * 20))


def test_shuffled_traits_rarely_pass(prep):
    """Nollfallet: draget blandas om mellan stenarna, så att inget samband finns. Ett fynd (p < 0,05 och samma riktning
    med p < 0,05 i båda halvorna) får komma i högst 5 % av 200 omblandningar; väntat är långt färre."""
    rng = random.Random(2026)
    passed = 0
    for i in range(200):
        a = ("kors", "bro", "at", "stungna")[i % 4]
        vals = [s["v"][a] for s in prep["stones"] if s["v"][a] is not None]
        rng.shuffle(vals)
        it = iter(vals)
        shuffled = {"stones": [dict(s, v={**s["v"], a: next(it) if s["v"][a] is not None else None})
                               for s in prep["stones"]]}
        kind, key = (("landskap", "U"), ("tid", 1050), ("drag", "signatur"), ("landskap", "Sö"))[i % 4]
        if q.ask(shuffled, a, kind, key, carvers=False)["verdict"] in ("håller", "håller men inte justerat"):
            passed += 1
    assert passed <= 10


def test_r_checks_can_only_lower_the_verdict():
    base = {"verdict": "håller", "adjusted": {"direction": 1, "p": 0.001}}
    ok = {"or": 2.0, "p": 0.001, "direction": 1}
    assert q.apply_r(base, {"carver": ok, "place": ok})["verdict"] == "håller"
    assert q.apply_r(base, {"carver": {**ok, "p": 0.2}, "place": ok})["verdict"] == "beror på ristarna"
    assert q.apply_r(base, {"carver": ok, "place": {**ok, "direction": -1}})["verdict"] == "kan vara platsen"
    assert q.apply_r(base, {"carver": ok, "place": {"skipped": "landskap"}})["verdict"] == "håller"
    assert q.apply_r(base, None) == {**base, "r_checks": {"available": False}}
    # a verdict that already failed is not changed by the checks
    weak = {"verdict": "bara i hela", "adjusted": {"direction": 1, "p": 0.01}}
    assert q.apply_r(weak, {"carver": {**ok, "p": 0.5}, "place": ok})["verdict"] == "bara i hela"


@pytest.mark.needs_r  # skipped without R: see tests/conftest.py
def test_r_checks_find_the_place_behind_crosses_on_sandstone(prep, tmp_path, monkeypatch):
    """Kors är ovanligare på sandsten (Mantel–Haenszel, båda halvorna, också med ristaren som slumpeffekt), men inte när
    stenarnas läge får forma en egen yta: sandsten och färre kors hör hemma i samma trakter (r/question.R)."""
    from src import r_bridge as rb
    monkeypatch.setattr(rb, "CACHE_DIR", str(tmp_path))
    r = q.ask(prep, "kors", "bergart", "sandsten")
    assert r["verdict"] == "håller" and r["adjusted"]["direction"] == -1
    checks = rb.question("test", q.r_rows(prep, "kors", "bergart", "sandsten"), "bergart")
    out = q.apply_r(r, checks)
    assert out["r_checks"]["carver_holds"] is True and out["r_checks"]["place_holds"] is False
    assert out["verdict"] == "kan vara platsen"
