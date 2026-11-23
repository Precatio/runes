"""src/hand_groups.py: grupperingen (genomsnittlig länkning med diametervillkor) och uppslagningen per sten."""
import numpy as np

from src import hand_groups


def _toy():
    # fyra stenar på en rad med 5 km mellan; 0–1 och 2–3 är mycket lika, 1–2 lite lika
    n = 4
    D = np.array([[abs(i - j) * 5000.0 for j in range(n)] for i in range(n)])
    M = np.full((n, n), np.nan)
    for a, b, p in ((0, 1, 0.95), (2, 3, 0.9), (1, 2, 0.3), (0, 2, 0.2), (1, 3, 0.2), (0, 3, 0.1)):
        M[a, b] = M[b, a] = p
    return M, D


def test_cluster_groups_the_alike_pairs():
    M, D = _toy()
    lab = hand_groups.cluster(M, D, tau=0.8)
    assert lab[0] == lab[1] and lab[2] == lab[3] and lab[0] != lab[2]


def test_cluster_uses_the_average_not_the_strongest_link():
    M, D = _toy()
    # 0–1 och 2–3 är ihopslagna först; mellan grupperna är medlet (0,3+0,2+0,2+0,1)/4 = 0,2 – under 0,25
    lab = hand_groups.cluster(M, D, tau=0.25)
    assert lab[0] != lab[2]
    lab = hand_groups.cluster(M, D, tau=0.15)
    assert len(set(lab)) == 1


def test_cluster_respects_the_diameter():
    M, D = _toy()
    D = D * 10  # 50 km mellan grannarna: inget får slås ihop
    lab = hand_groups.cluster(M, D, tau=0.5)
    assert len(set(lab)) == 4


def test_group_of():
    data = {"tested": {"precision_named": 0.77}, "stones": {"U 1": "G001", "U 2": "G001", "U 3": "G001"},
            "groups": [{"id": "G001", "type": "okänd hand", "carver": None, "evidence": "gott", "stones": ["U 1", "U 2", "U 3"],
                        "carvers": {}, "diameter_km": 4.0, "mean_p": 0.9, "stability": 1.0}]}
    g = hand_groups.group_of(data, "U 2")
    assert g["id"] == "G001" and g["others"] == ["U 1", "U 3"] and g["precision_named"] == 0.77
    assert hand_groups.group_of(data, "U 9") is None and hand_groups.group_of(None, "U 1") is None
