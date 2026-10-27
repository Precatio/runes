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


def test_runor_record_keeps_narke_apart_from_norway():
    """Runor lists N A1–N A34 before Nä 1–34 and both fold to 'na<n>': the exact signum must win."""
    if not runor.available():
        pytest.skip("Runor 2020 är inte skördat på maskinen")
    assert runor.record("Nä 11")["signum"] == "Nä 11"
    assert runor.record("N A11")["signum"] == "N A11"
    assert runor.record("Nä 14")["signum"] == "Nä 14"  # not Bo Peterson1992 through its alt signum N A14
    from api.rundata import store
    assert runor.for_inscription(store().get("Nä 11"))["signum"] == "Nä 11"


@pytest.mark.parametrize("place,parish,placement,elsewhere", [
    ("Tälje bro, Odensbacken", "Askers sn", "Vid Hummelsta, Stora Mellösa sn.", True),
    ("Nederbacka (Rosta bro)", "Ärentuna sn", "Vid Rosta kvarn, Bälinge sn.", True),
    ("Kålsta", "Håtuna sn", "Vid Nyborg, Håtuna sn.", True),
    ("Tyttinge gård", "Grödinge sn", "På gårdsplanen.", False),
    ("Lunnebjörke", "Skärkinds sn", "Rest vid den gamla vägen.", False),
    ("Årby", "Lagga sn", "Inmurat i källaren vid Årby.", False),
    ("S:t Olovs ruin", "Sigtuna", "Sitter i en mur i V delen av ruinen.", False),
    ("Fors", "Ösmo sn", "", False),
])
def test_placement_elsewhere_needs_another_place(place, parish, placement, elsewhere):
    """'Rundata says the same as Runor' only when the placement text names another place than the find place."""
    from src.stone_findings import placement_elsewhere
    rec = {"signum": "X 1", "place": place, "parish": parish, "placement": placement}
    assert placement_elsewhere(rec, lambda s: None) is elsewhere


def test_placement_elsewhere_follows_a_stone_reference():
    from src.stone_findings import placement_elsewhere
    other = {"signum": "Sö 109", "place": "Gredby bro"}
    rec = {"signum": "Sö 107", "place": "Balsta", "parish": "Klosters sn", "placement": "Står vid Sö 109."}
    assert placement_elsewhere(rec, lambda s: other if s == "Sö 109" else None)


def test_summary_counts_a_family_link_once():
    from src.findings import summarize
    from src.stone_findings import LINK
    new = "Sannolikt ny och relevant kunskap – värd att pröva"
    fs = [{"signum": "U 1", "linked": "U 2", "method": LINK, "verdict": "nytt", "assessment": new},
          {"signum": "U 2", "linked": "U 1", "method": LINK, "verdict": "nytt", "assessment": new},
          {"signum": "U 3", "method": "egna fynd", "verdict": "nytt", "assessment": new, "stone_finding": True,
           "runestone": False},
          {"signum": "U 4", "method": "huggteknik", "verdict": "nytt", "assessment": new}]
    out = summarize(fs)
    assert out["likely_new"] == 2 and out["likely_new_links"] == 1 and out["other_objects"] == 1
    assert out["counts"]["nytt"] == 4
