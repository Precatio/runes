"""Automatisk spåranalys: runidentifiering och statistik med runan som enhet."""
import numpy as np
import pytest

from src.auto_grooves import analyze_grooves
from src.stats import summarize_by_rune
from src.synthetic import rune_stone


def band_segments(n_runes=6, crack=True):
    """En runslinga: två slingkanter, runor (stav + bistav) som når båda kanterna, en båge
    (ornamentik) ovanför och en sicksackande spricka nedanför."""
    segs = [((-190, 45), (190, 45)), ((-190, -45), (190, -45))]
    x = -160
    for i in range(n_runes):
        segs.append(((x, -45), (x, 45)))
        segs.append(((x, 20), (x + 25, 40)) if i % 2 else ((x, 0), (x + 25, -25)))
        x += 55
    t = np.linspace(0, np.pi, 40)
    arc = [(150 * np.cos(a), 60 + 40 * np.sin(a)) for a in t]
    segs += list(zip(arc[:-1], arc[1:]))
    if crack:
        rng = np.random.default_rng(3)
        p = np.array([-150.0, -75.0])
        for _ in range(25):
            q = p + [rng.uniform(4, 10), rng.uniform(-6, 6)]
            segs.append((tuple(p), tuple(q)))
            p = q
    return segs


@pytest.fixture(scope="module")
def band_result():
    mesh = rune_stone(size=(420, 240), resolution=0.6, segments=band_segments(), depth_mm=3.0, opening_angle_deg=80)
    return analyze_grooves(mesh, [0, 0, 1])


def test_only_runes_are_measured(band_result):
    acc = [s for s in band_result["slices"] if s["accepted"]]
    assert acc and all(s["feature"] == "rune" for s in acc)
    assert band_result["counts"]["runes_measured"] == 6
    assert abs(np.mean([s["apex_vinkel_deg"] for s in acc]) - 80) < 3
    # Band lines and the arc are ornament, the crack is irregular; none of them is measured
    kinds = band_result["counts"]["strokes"]
    assert kinds.get("ornament", 0) >= 3 and kinds.get("irregular", 0) >= 1
    reasons = band_result["counts"]["rejection_reasons"]
    assert any(r.startswith("inte runa: långt") for r in reasons)
    assert any(r.startswith("inte runa: kort") for r in reasons)


def test_band_closed_by_staves_is_not_filled(band_result):
    # The band between two band lines, closed off by staves, must not become one wide area
    assert band_result["counts"]["wide_area_mm2"] < 500


def test_lone_straight_line_is_not_a_rune():
    mesh = rune_stone(size=(200, 160), segments=[((-20, -50), (-20, 50))])
    r = analyze_grooves(mesh, [0, 0, 1])
    assert r["counts"]["runes_measured"] == 0
    assert not any(s["accepted"] for s in r["slices"])
    assert "inte runa: ensamt rakt spår utan andra runor intill" in r["counts"]["rejection_reasons"]
    # Without the rune filter the same groove is measured
    r_all = analyze_grooves(mesh, [0, 0, 1], runes_only=False)
    assert any(s["accepted"] for s in r_all["slices"])


def test_summary_uses_runes_as_unit():
    slices = ([{"rune_id": 1, "apex_vinkel_deg": 60.0 + e} for e in (-1, 0, 1)] * 10
              + [{"rune_id": 2, "apex_vinkel_deg": 80.0 + e} for e in (-1, 0, 1)])
    s = summarize_by_rune(slices)
    v = s["metrics"]["apex_vinkel_deg"]
    # 30 slices in rune 1 and 3 in rune 2: each rune weighs the same
    assert s["n_runes"] == 2 and v["n"] == 2 and v["n_slices"] == 33
    assert v["mean"] == pytest.approx(70.0)
    assert v["icc"] > 0.9


def test_facit_evaluation_on_synthetic_stone(tmp_path):
    """The evaluation pipeline: a facit whose labels come from the known geometry gives full precision and recall."""
    import hashlib
    import json

    from scripts.evaluate_rune_detection import evaluate, load_like_app
    from src.synthetic import _segment_distance

    mesh = rune_stone(size=(420, 240), resolution=0.6, segments=band_segments(), depth_mm=3.0, opening_angle_deg=80)
    path = tmp_path / "band.stl"
    mesh.export(path)
    # As in the app: the facit is made on the centred model loaded from the file
    app_mesh = load_like_app(str(path))
    shift = -(mesh.bounds[0] + mesh.bounds[1]) / 2.0
    full = analyze_grooves(app_mesh, [0, 0, 1], runes_only=False)
    runes = band_segments(crack=False)[2:14]  # staves and branches

    def is_rune(pt):
        x, y = pt[0] - shift[0], pt[1] - shift[1]
        return min(float(_segment_distance(np.array(x), np.array(y), a, b)) for a, b in runes) < 3

    labels = [{"point": s["point"], "label": "rune" if is_rune(s["point"]) else "ornament"}
              for s in full["slices"] if s["accepted"]]
    facit = {"signum": "Syntetisk", "mesh": {"filename": "band.stl", "sha256": hashlib.sha256(path.read_bytes()).hexdigest()},
             "parameters": full["parameters"], "labels": labels}
    res = evaluate(json.loads(json.dumps(facit)), [str(tmp_path)])
    assert res["tp"] > 50 and res["unmatched"] == 0
    assert res["precision"] == 1.0 and res["recall"] > 0.95


def test_methods_lists_every_known_limitation():
    """METHODS.md section 18 must list the same limitations as src/limitations.py."""
    import os

    from src import limitations

    text = open(os.path.join(os.path.dirname(__file__), "..", "METHODS.md"), encoding="utf-8").read()
    section = text.split("## 18. Kända brister", 1)[1]
    for x in limitations.LIMITATIONS:
        assert f"| {x['title']} |" in section, x["key"]
    assert limitations.VERSION in section



def test_protocol_matches_method_and_document():
    import os

    from api.config import METHOD_VERSION
    from src import protocol

    assert protocol.METHOD_VERSION == METHOD_VERSION
    doc = open(os.path.join(os.path.dirname(__file__), "..", "PROTOCOL.md"), encoding="utf-8").read()
    assert protocol.VERSION in doc and "0,6 mm, fast" in doc and METHOD_VERSION in doc


def test_protocol_compliance():
    from src import protocol

    mesh = rune_stone()
    ok = analyze_grooves(mesh, [0, 0, 1], **{k: v for k, v in protocol.PARAMETERS.items()})["parameters"]
    assert protocol.compliance(ok, protocol.METHOD_VERSION)["compliant"]
    other = analyze_grooves(mesh, [0, 0, 1], sensitivity=2.5)["parameters"]
    c = protocol.compliance(other, protocol.METHOD_VERSION)
    assert not c["compliant"] and any("känslighet" in d for d in c["deviations"])
    assert any("rutnätet följer skanningen" in d for d in c["deviations"])
