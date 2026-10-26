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
    segs += list(zip(arc[:-1], arc[1:], strict=False))
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
    return analyze_grooves(mesh, [0, 0, 1], bands=False)  # the stroke classification on its own


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


def test_every_recognised_rune_has_a_box(band_result):
    # The boxes let the 2D page cut out the runes; each holds the rune's accepted slices
    W, H = band_result["image_width"], band_result["image_height"]
    for r in band_result["runes"]:
        x0, y0, x1, y1 = r["box"]
        assert 0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1
        for s in band_result["slices"]:
            if s["accepted"] and s.get("rune_id") == r["id"]:
                assert x0 <= s["img_x"] / W <= x1 and y0 <= s["img_y"] / H <= y1


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
    """METHODS.md section 18 must list the same limitations as src/limitations.py, in the same order."""
    import os

    from src import limitations

    text = open(os.path.join(os.path.dirname(__file__), "..", "METHODS.md"), encoding="utf-8").read()
    section = text.split("## 18. Kända brister", 1)[1]
    for x in limitations.LIMITATIONS:
        assert f"| {x['title']} |" in section, x["key"]
    assert limitations.VERSION in section
    rows = [line.split("|")[1].strip() for line in section.split("\n## ", 1)[0].splitlines() if line.startswith("| ")]
    titles = {x["title"] for x in limitations.LIMITATIONS}
    assert [r for r in rows if r in titles] == [x["title"] for x in limitations.LIMITATIONS]



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


def test_groove_map_black_point_ignores_edge_zone():
    """Skenbart djup vid skanningens kant sätter inte svartpunkten, och kantzonen ritas blekt."""
    import base64
    import io
    from types import SimpleNamespace

    from PIL import Image

    from src.auto_grooves import EDGE_ZONE_CONTRAST, _groove_map_png
    region = np.ones((40, 40), bool)
    inner = np.zeros_like(region)
    inner[10:30, 10:30] = True
    depth = np.zeros(region.shape)
    depth[15:25, 20] = 2.0  # a rune in the measured area
    depth[0:3, :] = 30.0  # false depth along the scan's edge
    img, black = _groove_map_png(SimpleNamespace(region=region), -depth, inner, 0.3, (40, 40))
    assert black == pytest.approx(2.0)
    gray = np.flipud(np.asarray(Image.open(io.BytesIO(base64.b64decode(img.split(",")[1])))))
    assert gray[20, 20] < 40  # the rune is (nearly) black
    assert gray[1, 20] >= 255 * (1 - EDGE_ZONE_CONTRAST) - 10  # the edge never darker than the faded grey


def test_runic_band_decides_what_is_a_rune(monkeypatch):
    """With a runic band (here the area between the two band lines, given to the analysis as drawn bands would be),
    the runes inside it are measured, the band lines are band edges and the arc and the crack outside it are not."""
    from src import rune_bands
    mesh = rune_stone(size=(420, 240), resolution=0.6, segments=band_segments(), depth_mm=3.0, opening_angle_deg=80)

    def fake_bands(depth, region, res, hf, sha256):
        H, W = depth.shape
        yy = (np.arange(H) - H / 2) * res  # mm from the stone's middle, rows run along y
        mask = np.zeros((H, W), bool)
        mask[np.abs(yy) <= 42] = True        # between the band lines at ±45 mm
        mask &= region
        f = rune_bands.band_field(mask, res)
        f.update({"source": "ritade", "empty": False, "coverage": float(mask[region].mean())})
        return f
    monkeypatch.setattr(rune_bands, "bands_for", fake_bands)
    r = analyze_grooves(mesh, [0, 0, 1])
    acc = [s for s in r["slices"] if s["accepted"]]
    assert acc and all(s["band"] == "runa" for s in acc)
    assert r["bands"]["source"] == "ritade" and r["parameters"]["measure"] == "runes"
    reasons = r["counts"]["rejection_reasons"]
    assert reasons.get("slingkant, inte runa", 0) > 0 and reasons.get("utanför runslingorna", 0) > 0
    assert abs(np.mean([s["apex_vinkel_deg"] for s in acc]) - 80) < 3
    orn = analyze_grooves(mesh, [0, 0, 1], measure="ornament")
    acc_o = [s for s in orn["slices"] if s["accepted"]]
    assert acc_o and all(s["band"] == "utanför" for s in acc_o)


def test_drawn_bands_follow_the_stone_when_it_is_turned(tmp_path, monkeypatch):
    """Checked bands drawn on the depth image (src/rune_bands.drawn) are carried over through the stone's surface, so
    that they land on the same place on the stone when the analysis looks at it from a slightly different direction."""
    import json
    import trimesh
    from src import rune_bands
    from src.auto_grooves import Heightfield, basis
    mesh = trimesh.creation.box(extents=[300, 200, 20])
    mesh = trimesh.Trimesh(*trimesh.remesh.subdivide_to_size(mesh.vertices, mesh.faces, 4.0))
    normal, up, res = [0, 0, 1], [0, 1, 0], 1.0
    hf0 = Heightfield.from_mesh(mesh, normal, resolution=res, up=up)
    (tmp_path / "djup" / "s").mkdir(parents=True)
    (tmp_path / "band" / "s").mkdir(parents=True)
    json.dump({"sha256": "abc", "normal": normal, "up": up, "res_mm": res, "shape": list(hf0.H.shape),
               "a0": hf0.a0, "b0": hf0.b0}, open(tmp_path / "djup" / "s" / "x.json", "w"))
    # a horizontal band through the middle of the stone, 40 mm high (drawing page: half resolution, row 0 at the top)
    H, W = hf0.H.shape
    json.dump({"status": "granskad", "scale": 2, "bands": [{"points": [[20, H / 4], [W / 2 - 20, H / 4]], "height": 20}]},
              open(tmp_path / "band" / "s" / "x.json", "w"))
    monkeypatch.setattr(rune_bands, "DEPTH_DIR", str(tmp_path / "djup"))
    monkeypatch.setattr(rune_bands, "BAND_DIR", str(tmp_path / "band"))
    for deg in (0, 10):
        t = np.radians(deg)
        hf = Heightfield.from_mesh(mesh, [np.sin(t), 0, np.cos(t)], resolution=res, up=up)
        m = rune_bands.drawn("abc", hf)
        assert m is not None and m.any()
        # the band's cells are on the stone's middle line (y ≈ 0) and nowhere else
        iy, ix = np.nonzero(m)
        y = hf.b0 + iy * res
        assert abs(np.median(y)) < 3 and np.abs(y).max() < 25
    assert rune_bands.drawn("abc", Heightfield.from_mesh(mesh, [np.sin(0.6), 0, np.cos(0.6)], resolution=res, up=up)) is None
    assert rune_bands.drawn("other", hf0) is None


def test_staveless_runes_are_split_along_the_band(monkeypatch):
    """Staveless runes (src/staveless.py): seven runes of two short strokes each, no staves, in a band 90 mm high. The
    ordinary rune division (touching strokes of at least 12 mm) finds almost none of them; staveless mode splits them
    along the band into about seven runes, each with its own number on the slices. Off, the analysis is unchanged."""
    from src import rune_bands
    segs = [((-200, 45), (200, 45)), ((-200, -45), (200, -45))]
    x = -165
    for i in range(7):
        segs.append(((x, -5), (x, 7)))                                         # a short upright stroke, 12 mm
        segs.append(((x + 4, 12), (x + 11, 20)) if i % 2 else ((x + 4, -12), (x + 11, -20)))  # a short twig, ~11 mm
        x += 50
    mesh = rune_stone(size=(440, 240), resolution=0.6, segments=segs, depth_mm=2.0, opening_angle_deg=80)

    def fake_bands(depth, region, res, hf, sha256):
        H, W = depth.shape  # the band: the stone's own y within ±42 mm, whichever way the grid's rows run
        wy = (hf.a0 + np.arange(W) * res)[None, :] * hf.u[1] + (hf.b0 + np.arange(H) * res)[:, None] * hf.v[1]
        mask = (np.abs(wy) <= 42) & region
        f = rune_bands.band_field(mask, res)
        f.update({"source": "ritade", "empty": False, "coverage": float(mask[region].mean())})
        return f
    monkeypatch.setattr(rune_bands, "bands_for", fake_bands)
    plain = analyze_grooves(mesh, [0, 0, 1])
    sl = analyze_grooves(mesh, [0, 0, 1], staveless=True)
    ids = lambda r: {s["rune_id"] for s in r["slices"] if s["accepted"] and "rune_id" in s}  # noqa: E731
    assert len(ids(plain)) <= 2
    assert 6 <= len(ids(sl)) <= 8 and 6 <= sl["counts"]["runes_identified"] <= 8
    assert sl["parameters"]["staveless"] is True and plain["parameters"]["staveless"] is False
    assert sl["parameters"]["staveless_gap_mm"] > 0
    # the measurements themselves are the same: only which rune a slice belongs to changes
    key = lambda r: sorted((round(s["apex_vinkel_deg"], 6), s["position_mm"]) for s in r["slices"] if s["accepted"])  # noqa: E731
    assert key(plain) == key(sl)
