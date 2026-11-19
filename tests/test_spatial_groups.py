"""Grupper som enhet i rumsliga närhetsprov (src/spatial_groups.py, src/places.near_test, src/robustness.py): länkningen,
den klusterjusterade Mantel–Haenszel och ett syntetiskt fall där grupper blåser upp p-värdet."""
import random

import pytest

from src import places, spatial_groups as sg


def test_link_km_is_twice_the_radius_up_to_the_cap():
    assert sg.link_km(0.25) == 0.5 and sg.link_km(0.5) == 1.0 and sg.link_km(1) == 2.0
    assert sg.link_km(2) == sg.CAP_KM == 2.0 and sg.link_km(5) == 2.0
    assert sg.link_km(None) == 1.0  # hot spots: the local scale


def test_single_linkage_chains_and_shared_place_links():
    # a chain of four points 900 m apart is one group at 1 km (single linkage), a point 5 km away is its own
    xy = [(0, 0), (900, 0), (1800, 0), (2700, 0), (8000, 0)]
    assert sg.link(xy, 1000) == [0, 0, 0, 0, 1]
    assert sg.link(xy, 800) == [0, 1, 2, 3, 4]
    # two points 3 km apart with the same nearest place within the radius: linked even though the link distance is
    # shorter
    assert sg.link([(0, 0), (3000, 0), (9000, 0)], 2000, shared=["X", "X", None]) == [0, 0, 1]
    assert sg.link([], 1000) == []


def _grouped(near_groups, far_groups, size, near_yes, far_yes):
    """Synthetic stones in groups of `size`: every stone in a group has the same x (near or not) and the same y."""
    items, g = [], 0
    for n_groups, x, yes in ((near_groups, 1, near_yes), (far_groups, 0, far_yes)):
        for i in range(n_groups):
            items += [("U", x, int(i < yes), g)] * size
            g += 1
    return items


def test_groups_inflate_the_stone_level_p_value():
    # 20 groups of 8 stones near a place, 20 far; 12 of the near groups have the pattern on every stone, 8 of the far.
    # Stone by stone: 96 of 160 against 64 of 160, p well below 0.05. But the stones in a group are copies of each
    # other: there are only 40 independent observations, 12 of 20 against 8 of 20, which is no clear difference.
    items = _grouped(20, 20, 8, 12, 8)
    r = sg.cluster_cmh(items)
    assert r["n"] == 320 and r["groups"] == 40 and r["groups_near"] == 20 and r["groups_far"] == 20
    assert r["p_stone"] < 0.001
    assert r["design_effect"] == pytest.approx(8, rel=0.05)   # every group behaves as one stone
    assert r["effective_n"] == pytest.approx(40, rel=0.05)
    assert r["p_group"] > 0.05 and r["df"] == 19
    assert r["ci"][0] > 1 and r["ci_group"][0] < 1
    assert sg.verdict(r) == "bara stenar"
    # the same proportions with every stone its own group: the protection changes nothing
    lone = [(s, x, y, i) for i, (s, x, y, _) in enumerate(items)]
    r1 = sg.cluster_cmh(lone)
    # (only the F distribution with 159 degrees of freedom instead of chi-square separates them)
    assert r1["design_effect"] == 1.0 and r1["p_group"] < 0.001 and r1["df"] == 159
    assert sg.verdict(r1) == "båda"


def test_independent_stones_keep_the_ordinary_test():
    # Each stone its own group: the stone-level p is the ordinary CMH test of places.near_test
    rows = ([("U", 1, 1.0)] * 10 + [("U", 0, 1.0)] * 10 + [("U", 1, 5.0)] * 20 + [("U", 0, 5.0)] * 60
            + [("Sö", 1, 0.5)] * 6 + [("Sö", 0, 0.5)] * 4 + [("Sö", 1, 9.0)] * 10 + [("Sö", 0, 9.0)] * 30)
    plain = places.near_test(rows, 2)
    with_groups = places.near_test(rows, 2, groups=list(range(len(rows))))
    assert {k: v for k, v in with_groups.items() if k != "groups"} == plain
    g = with_groups["groups"]
    assert g["p_stone"] == pytest.approx(plain["p_mh"], abs=1e-4)
    assert g["design_effect"] == 1.0 and g["n_groups"] == len(rows) and g["verdict"] == "båda"


def test_near_test_reports_groups_and_the_difference():
    # the synthetic grouped stones as (province, y, km) rows with their groups
    items = _grouped(20, 20, 8, 12, 8)
    rows = [(s, y, 0.3 if x else 4.0) for s, x, y, _ in items]
    r = places.near_test(rows, 1, groups=[g for *_, g in items])
    assert r["p_mh"] < 0.001
    g = r["groups"]
    assert (g["n_groups"], g["n_groups_near"], g["n_groups_far"]) == (40, 20, 20)
    assert g["link_km"] == 2.0 and g["p_group"] > 0.05 and g["verdict"] == "bara stenar"


def test_too_few_groups_cannot_be_judged():
    items = _grouped(3, 20, 10, 3, 4)   # every near stone in three groups
    r = sg.cluster_cmh(items)
    assert r["p_stone"] < 0.05 and r["p_group"] is None and sg.verdict(r) == "för få grupper"
    assert sg.verdict({"p_stone": None}) == "saknas" and sg.verdict({"p_stone": 0.3, "p_group": None}) == "ingen"


def test_null_calibration_stone_level_false_alarms_group_level_does_not():
    """No association at all, but stones in groups share a group effect (a family's choice) and a place: the stone-level
    test raises false alarms far more often than 5 %, the group-level test stays near 5 %."""
    rng = random.Random(20261119)
    n_sim, false_stone, false_group = 300, 0, 0
    for _ in range(n_sim):
        items, g = [], 0
        for prov in ("U", "Sö"):
            for _ in range(30):
                size = rng.choice((1, 1, 2, 3, 5, 8, 12))
                x = int(rng.random() < 0.4)                 # the group's nearness to the place
                q = rng.betavariate(0.6, 0.9)               # the group's own propensity: strong within-group likeness
                items += [(prov, x, int(rng.random() < q), g) for _ in range(size)]
                g += 1
        r = sg.cluster_cmh(items)
        if r["p_stone"] is not None and r["p_stone"] < 0.05:
            false_stone += 1
        if r["p_group"] is not None and r["p_group"] < 0.05:
            false_group += 1
    assert false_stone / n_sim > 0.20
    assert false_group / n_sim < 0.10


@pytest.mark.skipif(not places.available(), reason="platserna är inte hämtade (scripts/fetch_place_names.py)")
def test_groups_latlon_links_stones_near_the_same_place():
    # two stones 1.5 km apart, on either side of a point, and one 30 km away: at a 0.5 km radius they are two groups
    # of the near pair (1 km link) unless they share the same nearest place; the far stone is alone
    lab = sg.groups_latlon([59.0, 59.0135, None, 59.3], [18.0, 18.0, None, 18.0], 0.5)
    assert lab[0] != lab[1] and len(set(lab)) == 4
    lab = sg.groups_latlon([59.0, 59.0135, 59.3], [18.0, 18.0, 18.0], 1.0)
    assert lab[0] == lab[1] != lab[2]


# --- the robustness ladder's rung "grupper som enhet" (src/robustness.py, r/robustness.R) ---

def _ladder_result(groups_rung):
    rung = lambda holds, p=0.01: {"or": 2.0, "ci": [1.2, 3.3], "p": p, "direction": 1, "n": 320, "holds": holds}  # noqa: E731
    rungs = {"raw": rung(True), "adjusted": rung(True, 0.004), "half_A": rung(True), "half_B": rung(True)}
    if groups_rung is not None:
        rungs["groups"] = groups_rung
    return {"n": 320, "k": 160, "direction": 1, "rungs": rungs}


def test_scan_keys_split_into_trait_and_kind():
    from src import robustness as rb
    assert rb._scan_parts("scan_kristen_cult_a") == ("kristen", "cult_a")
    assert rb._scan_parts("scan_r_for_R_gravfalt") == ("r_for_R", "gravfalt")
    assert rb._scan_parts("scan_indications") is None and rb._scan_parts("hotspot_arv_U") is None


def test_ladder_groups_rung_decides_confirmation_for_spatial_patterns():
    from src import robustness as rb
    spec = {"groups": {"link_km": 2.0}}
    fails = {"or": 2.0, "ci": [0.7, 5.6], "p": 0.2, "direction": 1, "n": 320, "groups": 40, "groups_x1": 20,
             "groups_x0": 20, "design_effect": 5.1, "link_km": 2.0, "holds": False}
    s = rb.summarize(_ladder_result(fails), spec)
    g = next(r for r in s["rungs"] if r["key"] == "groups")
    assert g["label"].startswith("Grupper som enhet") and g["groups"] == 40 and g["design_effect"] == 5.1
    assert s["groups"] == "bara stenar" and s["first_fail"] == "groups"
    pats = [{"topic": "Geografi", "key": "cult_prayer"}, {"topic": "Geografi", "key": "scan_bon_cult_a"},
            {"topic": "Förändring", "key": "bon"}]
    rob = {"patterns": {"Geografi|cult_prayer": _ladder_result(fails),
                        "Geografi|scan_bon_cult_a": _ladder_result({**fails, "p": 0.01, "holds": True}),
                        "Förändring|bon": _ladder_result(None)},
           "specs": {"Geografi|cult_prayer": spec, "Geografi|scan_bon_cult_a": spec, "Förändring|bon": {}}}
    cult, scan, bon = rb.annotate(pats, rob)
    assert cult["confirmed"] is False                     # holds stone by stone, both halves – but not in groups
    assert scan["confirmed"] is True and scan["ladder"]["groups"] == "håller"
    assert bon["confirmed"] is True and "groups" not in bon["ladder"]   # not spatial: no rung, no change
    few = {"skipped": "för få grupper (3)", "n": 320, "groups": 23, "holds": None}
    assert rb.summarize(_ladder_result(few), spec)["groups"] == "för få grupper"


@pytest.mark.needs_r
def test_ladder_groups_rung_in_r_on_grouped_synthetic_stones(tmp_path, monkeypatch):
    """The same synthetic case through r/robustness.R: 40 groups of 8 stones, nearness and the pattern shared within
    each group. The adjusted rung (stone by stone) holds; the rung with groups as units does not."""
    import csv
    import json
    from src import r_bridge, robustness as rb
    monkeypatch.setenv("R_DISABLED", "0")
    rng = random.Random(7)
    lines, g = [], 0
    for x, high in ((1, 12), (0, 8)):
        for i in range(20):
            q = 0.9 if i < high else 0.1
            prov = "U" if g % 2 == 0 else "Sö"
            for j in range(8):
                lines.append({"pattern": "Geografi|syntet", "signum": f"S{g}-{j}", "y": int(rng.random() < q), "x": x,
                              "province": prov, "region_old": prov, "epoch": "1020–1050", "half": "A" if g % 4 < 2 else "B",
                              "hand": f"_{prov}:p{g}", "parish": f"{prov}:p{g}", "xk": g * 10.0, "yk": j * 0.1,
                              "moved": 0, "moved_runor": 0, "sgroup": g})
            g += 1
    data = tmp_path / "data.csv"
    data.write_bytes(rb._csv(lines))
    assert next(csv.reader(open(data, encoding="utf-8")))[-1] == "sgroup"
    spec = {"id": "Geografi|syntet", "adjust": ["province"], "x_lo": 0, "x_hi": 1, "lopo": False, "place": False,
            "moved": False, "selected": False, "groups": {"link_km": 2.0, "radius_km": 1.0, "kind": None, "min_groups": 5}}
    res = r_bridge.run_module("robustness", {"data": str(data), "specs": [spec], "seed": 2026}, str(tmp_path / "out"))
    r = res["patterns"]["Geografi|syntet"]
    adj, grp = r["rungs"]["adjusted"], r["rungs"]["groups"]
    assert adj["p"] < 0.05 and adj["holds"] is True
    assert grp["groups"] == 40 and grp["groups_x1"] == 20 and grp["groups_x0"] == 20 and grp["df"] == 19
    assert grp["design_effect"] > 2 and grp["p"] > 0.05 and grp["holds"] is False
    assert grp["or"] == pytest.approx(adj["or"], rel=1e-6)   # the same odds ratio, only the uncertainty differs
    s = rb.summarize(json.loads(json.dumps(r)), spec)
    assert s["groups"] == "bara stenar"
