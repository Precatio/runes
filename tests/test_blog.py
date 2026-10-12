"""Månadens fynd (api/routers/blog.py): utkastet ur mönstren, och de nya mönstren om strand och lämningar."""
from api.routers import blog
from src import r_findings as rf


def _pattern(key, status, replicated=None, topic="Förändring"):
    return {"key": key, "topic": topic, "status": status, "replicated": replicated,
            "text": f"Draget {key} blir vanligare över tid (q 0,01). Mer text.", "hypothesis": "En hypotes.",
            "test": "Ett sätt att pröva den."}


def test_draft_takes_what_is_new_or_changed():
    pats = [_pattern("a", "bekräftar", True), _pattern("b", "mönster att pröva", True), _pattern("c", "indikation"),
            _pattern("d", "bekräftar", True)]
    before = {"Förändring|a": "bekräftar", "Förändring|c": "mönster att pröva"}  # a unchanged, c changed, b and d new
    out = blog.build_draft("2026-11", pats, before, None)
    body = out["draft"]["body"]
    assert "Draget a" not in body
    assert body.index("Draget b") < body.index("Draget d") < body.index("Draget c")  # new patterns to test first
    assert out["draft"]["slug"].startswith("2026-11-") and out["draft"]["month"] == "2026-11"
    assert "3 mönster" in out["draft"]["summary"]
    assert any("tidigare mönster att pröva" in s for s in out["sources"])
    # The English version is written with English sentences, not translated piece by piece
    assert out["draft"]["body_en"].startswith("Here are the patterns that are new")
    assert "**What we see.**" in out["draft"]["body_en"] and "**Vad vi ser.**" in body


def test_draft_mentions_the_map_shift_with_a_link():
    shift = {"key": "o_runa", "label": "o-runan för o", "early": 0.08, "late": 0.51, "n_early": 218, "n_late": 136}
    out = blog.build_draft("2026-11", [_pattern("b", "mönster att pröva")], {}, shift)
    assert "(/karta?pattern=o_runa&split=1)" in out["draft"]["body"] and "8 %" in out["draft"]["body"]
    assert "[pattern map](/karta?pattern=o_runa&split=1)" in out["draft"]["body_en"]


def test_slug_rules():
    assert blog.SLUG.match("2026-10-monoftong-i-nagot-ai-ord")
    assert not blog.SLUG.match("Med Versaler") and not blog.SLUG.match("-borjar-med-streck")
    assert blog._slug("Ög 136: Rökstenen och Þórr") == "og-136-rokstenen-och-orr"


def test_viking_shore_pattern():
    today = {"median_stones_km": 4.16, "median_random_km": 5.6}
    v = {"n_stones": 2254, "median_stones_km": 3.6, "median_random_km": 5.25, "p": 1e-28,
         "provinces": [{"province": "U", "n": 1177, "p": 1e-30, "median_stones_km": 3.36, "median_random_km": 6.37},
                       {"province": "Sm", "n": 121, "p": 0.15, "median_stones_km": 5.5, "median_random_km": 5.7}]}
    (pt,) = rf._viking_shore(v, today, [{"province": "U", "median_stones_km": 4.26, "median_random_km": 6.69}])
    assert pt["status"] == "mönster att pröva" and "tydligare" in pt["text"] and "1 av 2 landskap (U)" in pt["text"]
    assert "I U (1177 stenar): 64 % med dagens vatten, 53 % omkring år 1000." in pt["text"]
    assert rf._viking_shore({}, today) == []


def test_remains_patterns():
    r = {"available": True, "near_km": 0.5, "note": "Lämningarna …",
         "distances": [{"key": "gravfalt", "near_stones": 0.59, "near_random": 0.21, "median_stones_km": 0.38,
                        "median_random_km": 1.09, "q_bh": 1e-200},
                       {"key": "hog", "near_stones": 0.32, "near_random": 0.08, "median_stones_km": 0.8,
                        "median_random_km": 1.9, "q_bh": 1e-100},
                       {"key": "vag", "near_stones": 0.16, "near_random": 0.07, "median_stones_km": 1.4,
                        "median_random_km": 2.0, "q_bh": 1e-50}],
         "tests": {"time_gravfalt": {"or": 0.88, "q_bh": 0.37, "periods": {"early": 0.56, "late": 0.62}},
                   "christian_gravfalt": {"or": 1.2, "q_bh": 0.37},
                   "bridge_vag": {"or": 2.1, "lo": 1.4, "hi": 3.1, "q_bh": 0.0014, "halves": {"replicated": True}}},
         "gravfalt_provinces": [{"province": "U", "p": 1e-90, "near_stones": 0.69, "near_random": 0.26}]}
    pats = {p["key"]: p for p in rf._remains(r)}
    g, b = pats["remains_graves"], pats["remains_bridges"]
    assert g["status"] == "bekräftar" and "59 %" in g["text"] and "lika stor för stenar med kristna markörer" in g["text"]
    assert b["status"] == "mönster att pröva" and b["replicated"] is True and "oddskvot 2,10" in b["text"]
    assert rf._remains({"available": False}) == []
