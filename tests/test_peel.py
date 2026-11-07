"""Skala av vittringen (src/peel.py, POST /api/3d/peel): ytan följer en välvd sten, djupet mäts vinkelrätt mot ytan,
ett huggspår blir spår och en grop blir grop, etikettkartan ligger exakt under bilden, och bortklickade punkter märker
rätt fläck."""
import io

import numpy as np
import pytest
from PIL import Image

from src import peel

RES = 0.5


def _grid(size_mm=240.0):
    n = int(size_mm / RES)
    y, x = np.mgrid[0:n, 0:n] * RES
    return x - size_mm / 2, y - size_mm / 2


def _dome(x, y, radius=600.0):
    return np.sqrt(radius ** 2 - x ** 2 - y ** 2) - radius


def _v(dist, half_width, depth):
    return np.clip(1 - np.abs(dist) / half_width, 0, None) * depth


def test_reference_follows_a_domed_stone():
    x, y = _grid()
    H = _dome(x, y)
    pe = peel.Peel(H, np.ones_like(H, bool), RES)
    inner = pe.use
    # A plain dome has no carving: the depth stays near zero everywhere (a flat cut would give centimetres)
    assert inner.mean() > 0.6
    assert float(np.percentile(pe.depth[inner], 99)) < 0.05
    assert float(H.max() - H[inner].min()) > 10


def test_depth_is_measured_perpendicular_to_the_surface():
    x, y = _grid()
    tilt = np.radians(30)
    d_perp = 2.0
    # A plane sloping 30° along x, with a groove along x whose depth across the surface is 2 mm
    H = x * np.tan(tilt) - _v(y, 4.0, d_perp / np.cos(tilt))
    pe = peel.Peel(H, np.ones_like(H, bool), RES)
    centre = pe.use & (np.abs(y) < RES / 2)
    assert abs(float(np.median(pe.depth[centre])) - d_perp) < 0.15  # vertical depth would be 2.31


def test_a_groove_is_a_groove_and_a_pit_is_a_pit():
    rng = np.random.default_rng(1)
    x, y = _grid()
    from scipy import ndimage
    weathering = ndimage.gaussian_filter(rng.normal(0, 0.25, x.shape), 1.5)
    groove = _v(y - 20, 3.0, 2.0) * (np.abs(x) < 40)
    pit = np.clip(1 - np.hypot(x - 50, y + 40) / 3.0, 0, None) * 2.0
    H = _dome(x, y) + weathering - groove - pit
    pe = peel.Peel(H, np.ones_like(H, bool), RES)
    layer = pe.layer(0.0)
    lab, comps = layer["labels"], {c["id"]: c for c in layer["components"]}

    def kind_at(px, py):
        r, c = int((py + 120) / RES), int((px + 120) / RES)
        win = lab[r - 2:r + 3, c - 2:c + 3]
        ids = win[win > 0]
        assert ids.size, (px, py)
        return comps[int(np.bincount(ids).argmax())]["kind"]

    assert kind_at(0, 20) == "spar"
    assert kind_at(50, -40) == "grop"
    g = comps[int(lab[int(140 / RES), int(120 / RES)])]
    assert 60 <= g["length_mm"] <= 90 and g["depth_mm"] > 1.5
    # More offset peels more: fewer cells are left
    assert (pe.layer(1.0)["labels"] > 0).sum() < (lab > 0).sum()


def test_labels_png_lies_exactly_under_the_picture():
    lab = np.zeros((5, 7), np.int32)
    lab[0, 0], lab[4, 6], lab[2, 3] = 1, 70000, 300
    im = np.array(Image.open(io.BytesIO(peel.labels_png(lab)))).astype(np.int64)
    ids = im[..., 0] + 256 * im[..., 1] + 65536 * im[..., 2]
    # row 0 of the grid is at the bottom of the picture, as in groove_export.gray_image
    assert (np.flipud(ids) == lab).all()


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient

    from api.main import app
    return TestClient(app)


def test_peel_endpoint(client):
    from src.synthetic import rune_stone
    N = [0.0, -float(np.sin(np.radians(20))), float(np.cos(np.radians(20)))]
    stl = rune_stone(opening_angle_deg=70, depth_mm=4, tilt_deg=20).export(file_type="stl")
    mid = client.post("/api/3d/upload", files={"file": ("stone.stl", stl)}).json()["mesh_id"]
    base = {"mesh_id": mid, "normal_x": N[0], "normal_y": N[1], "normal_z": N[2]}
    r = client.post("/api/3d/peel", data=base)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["counts"]["spar"] >= 1 and body["background"].startswith("data:image/png;base64,")
    import base64
    im = Image.open(io.BytesIO(base64.b64decode(body["labels"].split(",", 1)[1])))
    assert im.size == (body["width"], body["height"])
    spar = next(c for c in body["components"] if c["kind"] == "spar")
    # Clicking a groove away: its point comes back with the next layer and marks the same speck
    r2 = client.post("/api/3d/peel", data={**base, "offset_mm": 0.0, "removed_json": f"[{spar['point']}]"}).json()
    gone = [c for c in r2["components"] if c["removed"]]
    assert [c["id"] for c in gone] == [spar["id"]] and gone[0]["removed_by"] == [0]
    assert client.post("/api/3d/peel", data={**base, "removed_json": "[[1, 2]]"}).status_code == 422
