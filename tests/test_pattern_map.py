"""Mönsterkartan (src/pattern_map.py): hedniska markörer utan namn på Þór-, och kartans form."""
from src import pattern_map as pm


def _rec(**kw):
    return {"signum": "X 1", "normalization": "", "translation_en": "", "other": "", "transliteration": "", **kw}


def test_thor_is_the_god_not_names():
    assert pm.pagan(_rec(normalization='miok goðan þegn. "Þorr vigi.'))
    assert pm.pagan(_rec(normalization='sun sniallara. Siði(?) "Þorr(?).'))
    for name in ('"Þorkell ræisti', '"Þor... ... stæin', '"Þor[bio]rn(?) ok', '"Þori, faður sinn', '"Þorr[...]'):
        assert not pm.pagan(_rec(normalization=name)), name


def test_thor_motifs_and_rituals():
    assert pm.pagan(_rec(other="Pryds av en torshammare där korset brukar vara."))
    assert pm.pagan(_rec(other="Nedtill finns ett motiv ur Tors fiskafänge."))
    assert pm.pagan(_rec(transliteration="alu"))
    assert not pm.pagan(_rec(transliteration="fuþarkhniastbmlR"))
    assert not pm.pagan(_rec(other="Bilder ur berättelsen om Sigurd Fafnesbane."))


def test_build_values_follow_pattern_order():
    keys = [k for k, *_ in pm.PATTERNS]
    rec = _rec(signum="U 1", lat=59.8, lon=17.6, normalization='"Ulfr ræisti stæin', cross_form="kors", style="Pr3",
               period="V", object="runsten", carvers=[])
    out = pm.build([rec], names=set())
    assert [p["key"] for p in out["patterns"]] == keys
    assert len(out["stones"]) == 1 and out["stones"][0]["y"] is not None
    v = dict(zip(keys, out["stones"][0]["v"]))
    assert v["kristen"] == 1 and v["kors"] == 1 and v["hednisk"] == 0 and v["neutral"] == 0
