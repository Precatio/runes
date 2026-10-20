import numpy as np

from src.stats import METRICS, attribute, compare_stones, material_baseline, reliability, summarize, ward_clustering

RNG = np.random.default_rng(1)
SD = [3, 1, 0.3, 0.5, 0.03, 0.05, 0.01]


def stone(mu, n=8):
    return [dict(zip(METRICS, RNG.normal(mu, SD))) for _ in range(n)]


def test_summarize_ci_contains_mean():
    s = summarize([1, 2, 3, 4])
    assert s["n"] == 4 and s["ci95"][0] < s["mean"] < s["ci95"][1]
    assert summarize([])["mean"] is None


def test_compare_detects_difference_but_not_noise():
    base = [75, 3, 2, 6, 0.33, 0.2, 0.05]
    same = compare_stones(stone(base), stone(base))["overall"]["p_value"]
    diff = compare_stones(stone(base), stone([95, 1, 1.5, 8, 0.19, 0.6, 0.04]))["overall"]["p_value"]
    assert diff < 0.01 < same


def test_attribution_reports_cross_validated_accuracy():
    ref = []
    for g, mu in [("A", [70, 3, 2, 6, .33, .2, .05]), ("B", [85, 2, 1.8, 7, .26, .4, .05]), ("C", [95, 1, 1.5, 8, .19, .6, .04])]:
        ref += [{"group": g, "label": f"{g}{k}", "values": list(RNG.normal(mu, SD))} for k in range(5)]
    r = attribute(ref, [71, 3, 2, 6, .33, .2, .05])
    assert r["ranking"][0]["group"] == "A"
    assert r["evaluation"]["top1_accuracy"] > r["evaluation"]["chance_top1"]


def test_attribution_refuses_with_too_little_data():
    r = attribute([{"group": "A", "label": "x", "values": [1] * 7}], [1] * 7)
    assert r["ranking"] == [] and "för få" in r["note"]


def test_ward_clustering_groups_similar_stones():
    X = np.array([[0, 0], [0.1, 0], [10, 10], [10.1, 10]])
    order = ward_clustering(["a1", "a2", "b1", "b2"], X)["order"]
    assert {order[0], order[1]} in ({"a1", "a2"}, {"b1", "b2"})


def test_material_baseline_is_a_leave_one_out_majority_guess():
    labels = ["A", "A", "A", "B", "B", "B", "C"]
    fam = ["granit", "granit", "granit", "sandsten", "sandsten", "sandsten", "sandsten"]
    # inom granit gissas alltid A (3 av 3 rätt); inom sandsten gissas B – rätt för de tre B, fel för C → 6 av 7
    assert abs(material_baseline(labels, fam) - 6 / 7) < 1e-9
    assert material_baseline(labels, [None] * 7) is None


def test_reliability_uses_the_stricter_of_chance_and_material():
    ev = {"top1_accuracy": 0.58, "chance_top1": 0.2, "material_top1": 0.5}
    assert abs(reliability(ev) - (0.58 - 0.5) / 0.5) < 1e-9
    assert reliability({"top1_accuracy": 0.38, "chance_top1": 1 / 3, "material_top1": 0.5}) == 0.0
    assert reliability({"top1_accuracy": 0.6, "chance_top1": 0.25, "material_top1": None}) > 0
    assert reliability(None) == 0.0


def test_attribution_reports_material_baseline_when_families_given():
    ref = []
    for g, mu, fam in [("A", [70, 3, 2, 6, .33, .2, .05], "granit"), ("B", [85, 2, 1.8, 7, .26, .4, .05], "granit"),
                       ("C", [95, 1, 1.5, 8, .19, .6, .04], "sandsten")]:
        ref += [{"group": g, "label": f"{g}{k}", "values": list(RNG.normal(mu, SD)), "family": fam} for k in range(5)]
    ev = attribute(ref, [71, 3, 2, 6, .33, .2, .05])["evaluation"]
    assert ev["material_top1"] is not None and 0 < ev["material_top1"] < 1
