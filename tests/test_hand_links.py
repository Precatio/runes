"""Likhet utöver grannarna (src/hand_links.py, METHODS 14i): måttet drar bort grannarnas likhet, kalibreringen säger hur
ofta så lika stenpar har samma ristare, och Stenöversikten kallar en sten en möjlig onämnd hand bara när dess mest lika
sten saknar ristare och är tillräckligt lik."""
import numpy as np

from src import hand_links, stone_overview


def test_excess_subtracts_the_neighbours_at_the_same_distance():
    # stone 0 in the middle, twenty neighbours on a ring 15 km away; one of them (1) is alike (0.9), the others 0.5
    ang = np.linspace(0, 2 * np.pi, 20, endpoint=False)
    xy = np.vstack([[0.0, 0.0], np.c_[15000 * np.cos(ang), 15000 * np.sin(ang)]])
    D = np.hypot(xy[:, None, 0] - xy[None, :, 0], xy[:, None, 1] - xy[None, :, 1])
    S = np.full((21, 21), 0.5)
    np.fill_diagonal(S, 1.0)
    S[0, 1] = S[1, 0] = 0.9
    E = hand_links.excess_matrix(S, D)
    assert E[0, 1] > 0.3 and abs(E[0, 2]) < 0.05       # alike beyond the neighbours, and just a neighbour
    assert np.allclose(E, E.T, equal_nan=True) and np.isnan(E[0, 0])


def test_calibration_and_the_hand_threshold():
    rng = np.random.default_rng(1)
    n = 120
    carver = [f"R{i % 6}" for i in range(n)]
    E = rng.normal(0, 0.05, (n, n))
    for i in range(n):
        for j in range(n):
            if carver[i] == carver[j]:
                E[i, j] += 0.4                        # stones by the same carver are clearly more alike
    E = (E + E.T) / 2
    np.fill_diagonal(E, np.nan)
    cal = hand_links.calibrate(E, carver)
    assert 0.1 < cal["base_share"] < 0.25 and cal["t_hand"] is not None
    assert hand_links.share_at(cal, 0.45) > 0.9 > hand_links.share_at(cal, -0.1)
    assert hand_links.share_at(cal, 0.45, best=True) >= cal["hand_share"]


def test_a_possible_unnamed_hand_needs_a_carverless_best_match_above_the_threshold():
    hands = {"calibration": {"t_hand": 0.64, "table": [{"min": 0.0, "share": 0.2, "pairs": 99}], "base_share": 0.13,
                             "best_table": [{"min": 0.6, "share": 0.7, "stones": 40}], "best_base_share": 0.44, "hand_share": 0.7},
             "stones": {"A": {"partners": [{"signum": "B", "excess": 0.7, "km": 3.0, "carver": None},
                                           {"signum": "C", "excess": 0.66, "km": 9.0, "carver": "Öpir 1"}], "carvers": []},
                        "D": {"partners": [{"signum": "E", "excess": 0.7, "km": 3.0, "carver": "Balle"},
                                           {"signum": "F", "excess": 0.68, "km": 4.0, "carver": None}], "carvers": []},
                        "G": {"partners": [{"signum": "H", "excess": 0.5, "km": 3.0, "carver": None}], "carvers": []}}}
    ctx = {"hands": hands}
    assert [p["signum"] for p in stone_overview._unnamed_partners("A", ctx)] == ["B"]
    assert stone_overview._unnamed_partners("D", ctx) == []   # its best match has a carver
    assert stone_overview._unnamed_partners("G", ctx) == []   # not alike enough
    ev = stone_overview.hand_evidence("A", ctx, ["Öpir 1"])
    assert ev["unnamed"] == ["B"] and ev["carvers"]["Öpir 1"] is None and ev["best_share"] == 0.7
    assert "möjlig onämnd hand" in stone_overview.STATUS_ORDER and "nytt förslag" not in stone_overview.STATUS_ORDER
