import pytest
from fastapi.testclient import TestClient

from api.main import app
from api import uploads


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_root(client):
    assert client.get("/").status_code == 200


def test_3d_rejects_unsupported_extension(client):
    r = client.post("/api/3d/analyze", files={"file": ("x.txt", b"hello")})
    assert r.status_code == 400


def test_3d_rejects_oversized_mesh(client, monkeypatch):
    monkeypatch.setattr(uploads, "MAX_MESH_BYTES", 10)
    r = client.post("/api/3d/analyze", files={"file": ("big.stl", b"x" * 100)})
    assert r.status_code == 413


def test_3d_mock_analysis(client):
    r = client.post("/api/3d/analyze", data={"use_mock": "true"})
    assert r.status_code == 200
    body = r.json()
    assert {"apex_vinkel_deg", "troligt_verktyg", "apex_idx"} <= body["results"].keys()
    assert {"x", "z", "fit_left", "fit_right"} <= body["plot_data"].keys()


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
