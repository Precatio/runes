import os
import pytest
from fastapi.testclient import TestClient

from api.main import app
from api import uploads


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_root(client):
    assert client.get("/").status_code == 200


MOCK_SLICE = {"use_mock": "true", "origin_x": "0", "origin_y": "0", "origin_z": "0",
              "dir_x": "0", "dir_y": "1", "dir_z": "0"}


def test_3d_rejects_unsupported_extension(client):
    r = client.post("/api/3d/upload", files={"file": ("x.txt", b"hello")})
    assert r.status_code == 400


def test_3d_rejects_oversized_mesh(client, monkeypatch):
    monkeypatch.setattr(uploads, "MAX_MESH_BYTES", 10)
    r = client.post("/api/3d/upload", files={"file": ("big.stl", b"x" * 100)})
    assert r.status_code == 413


def test_3d_never_falls_back_to_mock_data(client):
    # No file, no mesh_id and no explicit use_mock: the user is told what is missing
    for path, data in [
        ("/api/3d/analyze", {k: v for k, v in MOCK_SLICE.items() if k != "use_mock"}),
        ("/api/3d/auto_snap_path", {"path_points_json": "[[0,0,0],[0,1,0]]"}),
        ("/api/3d/auto_analyze", {"normal_x": "0", "normal_y": "0", "normal_z": "1"}),
        ("/api/3d/auto_slice", {"point_x": "0", "point_y": "0", "point_z": "0"}),
    ]:
        r = client.post(path, data=data)
        assert r.status_code == 400, path
        assert "Ladda upp" in r.json()["detail"]


def test_3d_analysis_requires_a_selected_slice(client):
    r = client.post("/api/3d/analyze", data={"use_mock": "true"})
    assert r.status_code == 422


def test_3d_unknown_mesh_id(client):
    r = client.post("/api/3d/analyze", data={**MOCK_SLICE, "use_mock": "false", "mesh_id": "0" * 64})
    assert r.status_code == 404


def test_3d_explicit_mock_analysis(client):
    r = client.post("/api/3d/analyze", data=MOCK_SLICE)
    assert r.status_code == 200
    body = r.json()
    assert {"apex_vinkel_deg", "troligt_verktyg", "apex_idx"} <= body["results"].keys()
    assert {"x", "z", "fit_left", "fit_right"} <= body["plot_data"].keys()
    assert body["provenance"]["mesh"]["mock"] is True


@pytest.fixture(scope="module")
def stone_id(client):
    from src.synthetic import rune_stone

    stl = rune_stone(opening_angle_deg=70, depth_mm=4, tilt_deg=20).export(file_type="stl")
    r = client.post("/api/3d/upload", files={"file": ("stone.stl", stl)})
    assert r.status_code == 200
    return r.json()["mesh_id"]


def test_upload_returns_reusable_mesh_id(client, stone_id):
    assert len(stone_id) == 64
    r = client.post("/api/3d/view_model", data={"mesh_id": stone_id, "max_faces": "20000"})
    assert r.status_code == 200 and r.headers["x-mesh-id"] == stone_id


def test_auto_analyze_measures_known_angle(client, stone_id):
    import numpy as np

    n = [0, -np.sin(np.radians(20)), np.cos(np.radians(20))]
    r = client.post("/api/3d/auto_analyze", data={"mesh_id": stone_id, "normal_x": n[0], "normal_y": n[1],
                                                   "normal_z": n[2]})
    assert r.status_code == 200
    body = r.json()
    assert body["counts"]["accepted"] >= 20
    assert abs(body["summary"]["apex_vinkel_deg"]["mean"] - 70) < 3
    assert body["image_base64"].startswith("data:image/png;base64,")
    accepted = [s for s in body["slices"] if s["accepted"]]
    assert {"img_x", "img_y", "point", "direction", "profile"} <= accepted[0].keys()


def test_auto_slice_one_click(client, stone_id):
    import numpy as np

    # Click near the vertical staff at x = -50 (stone tilted 20° about x; mesh is centred by bounds)
    from src.synthetic import rune_stone

    m = rune_stone(opening_angle_deg=70, depth_mm=4, tilt_deg=20)
    centre = (m.bounds[0] + m.bounds[1]) / 2
    target = np.array([-49.0, 0.0])
    p = m.vertices[np.argmin(np.linalg.norm(m.vertices[:, :2] - [target[0], 0], axis=1))] - centre
    r = client.post("/api/3d/auto_slice", data={"mesh_id": stone_id, "point_x": p[0], "point_y": p[1],
                                                 "point_z": p[2]})
    assert r.status_code == 200, r.text
    body = r.json()
    assert abs(body["results"]["apex_vinkel_deg"] - 70) < 5
    assert body["provenance"]["parameters"]["mode"] == "one-click"


def test_auto_slice_on_flat_surface_explains(client, stone_id):
    from src.synthetic import rune_stone
    import numpy as np

    m = rune_stone(opening_angle_deg=70, depth_mm=4, tilt_deg=20)
    centre = (m.bounds[0] + m.bounds[1]) / 2
    p = m.vertices[np.argmin(np.linalg.norm(m.vertices[:, :2] - [70, 50], axis=1))] - centre
    r = client.post("/api/3d/auto_slice", data={"mesh_id": stone_id, "point_x": p[0], "point_y": p[1],
                                                 "point_z": p[2]})
    assert r.status_code == 422 and "spår" in r.json()["detail"]


def test_summarize_selection(client):
    slices = [{m: v for m, v in zip(
        ["apex_vinkel_deg", "asymmetri_deg", "spårdjup_mm", "spårbredd_mm", "djup_bredd_kvot", "bottenradie_mm",
         "ytråhet_mm"], [70 + i, 3, 2, 6, .33, .2, .05])} for i in range(4)]
    r = client.post("/api/stats/summarize", json={"slices": slices})
    assert r.status_code == 200 and r.json()["n"] == 4


def test_2d_rejects_non_image(client):
    r = client.post(
        "/api/2d/analyze",
        files={"file": ("a.txt", b"x", "text/plain")},
        headers={"X-Gemini-Api-Key": "dummy"},
    )
    assert r.status_code == 400


def test_extract_features_rejects_bad_base64(client):
    r = client.post("/api/2d/extract_features", json={"image_base64": "data:image/png;base64,@@@"})
    assert r.status_code == 400


def test_errors_do_not_leak_exception_text():
    from api.errors import ai_error, server_error

    secret = "internal path /srv/secret"
    assert secret not in server_error(RuntimeError(secret), "Fel.").detail
    assert ai_error(RuntimeError("429 RESOURCE_EXHAUSTED")).status_code == 429
    assert secret not in ai_error(RuntimeError(secret)).detail


@pytest.mark.skipif(not os.path.exists(os.path.join(os.path.dirname(__file__), "..", "data", "rundata.json")),
                    reason="data/rundata.json saknas")
def test_stone_report_with_surface_figures(client, stone_id):
    import numpy as np

    n = [0, -np.sin(np.radians(20)), np.cos(np.radians(20))]
    auto = client.post("/api/3d/auto_analyze", data={"mesh_id": stone_id, "normal_x": n[0], "normal_y": n[1],
                                                      "normal_z": n[2]}).json()
    acc = [s for s in auto["slices"] if s["accepted"]]
    body = {"signum": "U 344", "mesh_id": stone_id, "counts": auto["counts"], "use_ai": False,
            "analyses": [{"feature_type": "rune", "slices": acc, "provenance": auto["provenance"]}]}
    r = client.post("/api/reports/stone", json=body)
    assert r.status_code == 200
    rep = r.json()
    assert rep["surface"] is True
    names = [f["name"] for f in rep["figures"]]
    assert any("strykljus" in x for x in names) and any("tvarsnitt" in x for x in names)
    # Runological conventions: transliteration in bold, normalisation in italics, the SRI edition cited
    assert "**in ulfr hafiR" in rep["markdown"] and "*En UlfR" in rep["markdown"]
    assert "Upplands runinskrifter" in rep["markdown"]
    # Without the model in memory the report is still made, without surface figures
    r2 = client.post("/api/reports/stone", json={**body, "mesh_id": "0" * 64}).json()
    assert r2["surface"] is False and r2["surface_note"]
    d = client.post("/api/reports/stone", json={**body, "format": "docx"})
    assert d.content[:2] == b"PK"
    # The saved synthesis becomes the report's attribution section
    syn = client.post("/api/synthesis/analyze", json={
        "signum": "U 344", "analyses": [{"id": "a", "feature_type": "rune", "slices": acc}]}).json()
    r3 = client.post("/api/reports/stone", json={**body, "synthesis": syn}).json()
    assert "Attribuering" in r3["markdown"] and "Åsmund" in r3["markdown"]
    # The app's own reading becomes a reading section, compared with Rundata
    reading = client.post("/api/phonetics/compare", json={
        "signum": "U 344", "transliteration": "in ulfʀ hafiʀ o onklati þru kialt takat",
        "normalization": "En UlfR hafiR a Ænglandi þry giald takit"}).json()
    reading.update({"transliteration": "in ulfʀ hafiʀ o onklati þru kialt takat",
                    "normalization": "En UlfR hafiR a Ænglandi þry giald takit", "translation": "Och Ulf har tagit"})
    r4 = client.post("/api/reports/stone", json={**body, "reading": reading}).json()
    assert "Läsning av bilden" in r4["markdown"] and "**in ulfʀ hafiʀ" in r4["markdown"]


@pytest.mark.skipif(not os.path.exists(os.path.join(os.path.dirname(__file__), "..", "data", "rundata.json")),
                    reason="data/rundata.json saknas")
def test_report_templates(client, stone_id):
    import numpy as np

    n = [0, -np.sin(np.radians(20)), np.cos(np.radians(20))]
    auto = client.post("/api/3d/auto_analyze", data={"mesh_id": stone_id, "normal_x": n[0], "normal_y": n[1],
                                                      "normal_z": n[2]}).json()
    acc = [s for s in auto["slices"] if s["accepted"]]
    keys = [t["key"] for t in client.get("/api/reports/templates").json()["templates"]]
    assert {"stenrapport", "tidskrift", "uppsats", "avhandling", "blogg", "antikvarisk", "data"} <= set(keys)
    body = {"signum": "U 344", "mesh_id": stone_id, "counts": auto["counts"], "use_ai": False, "include_r": False,
            "analyses": [{"feature_type": "rune", "slices": acc, "provenance": auto["provenance"]}]}
    expect = {"tidskrift": "## Highlights", "uppsats": "## 1 Inledning", "avhandling": "## 7.1 Inledning",
              "blogg": "## Så mätte vi", "antikvarisk": "## Administrativa uppgifter", "data": "## 3 Datamängden"}
    options = {"tidskrift": {"venue": "jas"}, "avhandling": {"chapter": "7"}}
    for key in keys:
        r = client.post("/api/reports/stone", json={**body, "template": key, "template_options": options.get(key, {})})
        assert r.status_code == 200, key
        md = r.json()["markdown"]
        assert expect.get(key, "") in md, key
        # Figures are numbered consecutively after the selection
        nums = [int(x) for x in __import__("re").findall(r"\*Figur (\d+)\.", md)]
        assert nums == list(range(1, len(nums) + 1)), key
    assert client.post("/api/reports/stone", json={**body, "template": "okänd"}).status_code == 400
