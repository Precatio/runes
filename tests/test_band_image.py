"""Runor och ornamentik (src/band_image.py, POST /api/3d/band_image): en gemensam gräns för hela stenen, rostrött inne
i textslingorna och grått utanför, slingornas kant svart, och endpointen."""
import base64
import io

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from api.main import app
from src import band_image


@pytest.fixture(scope="module")
def client():
    return TestClient(app)

RES = 0.5


def _stone():
    """A flat stone with a deep groove inside a band (rows 40–60) and an equally deep one outside it (rows 140–160)."""
    H, W = 200, 200
    depth = np.random.default_rng(1).normal(0, 0.05, (H, W))
    depth[48:52, 20:180] = 2.0     # the rune groove, inside the band
    depth[148:152, 20:180] = 2.0   # the ornament groove, outside
    region = np.ones((H, W), bool)
    inner = np.zeros((H, W), bool)
    inner[10:-10, 10:-10] = True
    bands = np.zeros((H, W), bool)
    bands[40:61, 10:190] = True
    return depth, region, inner, bands


def test_inside_the_band_is_rust_outside_is_grey_and_the_edge_is_drawn():
    depth, region, inner, bands = _stone()
    bi = band_image.BandImage(depth, region, inner, RES, bands, "ritade")
    L = bi.layer(0.5)
    rgb = L["rgb"]
    assert tuple(rgb[50, 100]) == band_image.RUST and tuple(rgb[150, 100]) == band_image.SLATE
    assert tuple(rgb[40, 100]) == band_image.EDGE and tuple(rgb[100, 100]) == (255, 255, 255)
    # half of what is shown lies in the band (the two grooves are equally long); the band covers its share of the surface
    assert abs(L["in_bands"] - 0.5) < 0.05 and abs(L["band_share"] - (21 * 170) / (180 * 180)) < 0.01
    assert L["source"] == "ritade" and L["level_mm"] == round(bi.level, 2)
    # more offset shows less; the offset is kept within the slider's range
    assert bi.layer(1.5)["shown_share"] < bi.layer(-0.5)["shown_share"]
    assert bi.layer(99)["offset_mm"] == band_image.OFFSET_RANGE[1]


def test_without_bands_everything_shown_is_plain():
    depth, region, inner, _ = _stone()
    L = band_image.BandImage(depth, region, inner, RES, None, "modellen").layer(0.5)
    assert tuple(L["rgb"][50, 100]) == tuple(L["rgb"][150, 100]) == band_image.PLAIN
    assert L["source"] is None and L["in_bands"] is None and L["band_share"] is None


def test_png_is_north_up():
    rgb = np.zeros((4, 3, 3), np.uint8)
    rgb[0] = 255  # grid row 0 is the bottom of the stone
    im = np.array(Image.open(io.BytesIO(band_image.png(rgb))))
    assert im.shape == (4, 3, 3) and (im[-1] == 255).all() and (im[0] == 0).all()


def test_band_image_endpoint(client):
    from src.synthetic import rune_stone
    N = [0.0, -float(np.sin(np.radians(20))), float(np.cos(np.radians(20)))]
    stl = rune_stone(opening_angle_deg=70, depth_mm=4, tilt_deg=20).export(file_type="stl")
    mid = client.post("/api/3d/upload", files={"file": ("stone.stl", stl)}).json()["mesh_id"]
    base = {"mesh_id": mid, "normal_x": N[0], "normal_y": N[1], "normal_z": N[2]}
    r = client.post("/api/3d/band_image", data=base)
    assert r.status_code == 200, r.text
    body = r.json()
    im = Image.open(io.BytesIO(base64.b64decode(body["image"].split(",", 1)[1])))
    assert im.size == (body["width"], body["height"])
    # no band model in the tests and no drawn bands for a synthetic file: the picture is plain, and says so
    assert body["source"] is None and body["in_bands"] is None and 0.2 < body["shown_share"] < 0.4
    deeper = client.post("/api/3d/band_image", data={**base, "offset_mm": 1.0}).json()
    assert deeper["shown_share"] < body["shown_share"] and deeper["level_mm"] == body["level_mm"]
    assert client.post("/api/3d/band_image", data={**base, "offset_mm": "nan"}).status_code == 422


def test_the_default_view_is_the_same_every_time(client):
    from src.synthetic import rune_stone
    stl = rune_stone(opening_angle_deg=70, depth_mm=4, tilt_deg=20).export(file_type="stl")
    mid = client.post("/api/3d/upload", files={"file": ("stone.stl", stl)}).json()["mesh_id"]
    a = client.post("/api/3d/band_image", data={"mesh_id": mid}).json()
    b = client.post("/api/3d/band_image", data={"mesh_id": mid, "offset_mm": 0.5}).json()
    assert a["view"]["kind"] == "stenens" and a["view"] == b["view"] and a["view"]["up"] is not None
    r = client.post("/api/3d/render_relief", data={"mesh_id": mid}).json()
    assert r["view"]["kind"] == "stenens"
    import numpy as np
    assert np.allclose(r["view"]["normal"], a["view"]["normal"], atol=1e-4)
    assert abs(float(np.dot(a["view"]["normal"], a["view"]["up"]))) < 1e-4  # up lies in the carved face (5 decimals)
    # a view sent by the page is used as it is
    v = client.post("/api/3d/band_image", data={"mesh_id": mid, "normal_x": 0, "normal_y": 0, "normal_z": 1}).json()
    assert v["view"]["kind"] == "vy"


def test_an_upload_made_drawable_gets_its_drawn_bands(client, tmp_path, monkeypatch):
    """Upload → make_drawable (a depth image in the cache) → bands drawn and marked checked on the drawing page → the
    band picture uses them, in the same view, without a restart."""
    import json
    import os
    from src import rune_bands
    from src.synthetic import rune_stone
    monkeypatch.setattr(rune_bands, "DEPTH_DIR", str(tmp_path / "djup"))
    monkeypatch.setattr(rune_bands, "BAND_DIR", str(tmp_path / "band"))
    # a stone of its own: the mesh cache knows a file it has seen by its content, with the first name it had
    stl = rune_stone(opening_angle_deg=60, depth_mm=3, tilt_deg=10).export(file_type="stl")
    mid = client.post("/api/3d/upload", files={"file": ("min sten.stl", stl)}).json()["mesh_id"]
    before = client.post("/api/3d/band_image", data={"mesh_id": mid}).json()
    assert before["drawable"] is None and before["source"] is None
    r = client.post("/api/3d/make_drawable", data={"mesh_id": mid})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["created"] and d["series"] == "uppladdade" and d["stem"].startswith("min_sten_") and d["status"] is None
    meta = json.load(open(tmp_path / "djup" / "uppladdade" / (d["stem"] + ".json")))
    assert "a0" in meta and "b0" in meta and meta["view"] == "stenens"
    assert client.post("/api/3d/make_drawable", data={"mesh_id": mid}).json()["created"] is False
    # a band across the middle of the depth image (drawing-page pixels, half resolution), marked checked
    h, w = meta["shape"][0] // 2, meta["shape"][1] // 2
    os.makedirs(tmp_path / "band" / "uppladdade")
    (tmp_path / "band" / "uppladdade" / (d["stem"] + ".json")).write_text(json.dumps(
        {"status": "granskad", "scale": 2, "bands": [{"points": [[w * 0.1, h * 0.5], [w * 0.9, h * 0.5]], "height": h * 0.3}]}))
    after = client.post("/api/3d/band_image", data={"mesh_id": mid}).json()
    assert after["view"]["kind"] == "ritbild" and after["source"] == "ritade"
    assert after["drawable"]["status"] == "granskad" and 0.05 < after["band_share"] < 0.6
