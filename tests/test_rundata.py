import os

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.rundata import DATA_PATH, store

pytestmark = pytest.mark.skipif(not os.path.exists(DATA_PATH), reason="data/rundata.json saknas (kör scripts.build_rundata)")


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_lookup_handles_spelling_variants_and_aliases():
    s = store()
    assert s.get("Sö 113")["signum"] == "Sö 113"
    assert s.get("So113")["signum"] == "Sö 113"
    assert s.get("B 343")["signum"] == "U 654"  # alias i Rundata


def test_record_fields_are_parsed():
    rec = store().get("U 11")
    assert rec["period"] == "V" and rec["style"] == "Pr4"
    assert {c["name"] for c in rec["carvers"]} == {"Olev", "Torgöt Fotsarve"}
    assert 59 < rec["lat"] < 60 and 17 < rec["lon"] < 18  # Adelsö
    assert rec["transliteration"] and rec["translation_en"]


def test_negated_carvers_are_dropped():
    names = {c["name"] for c in store().get("U 654")["carvers"]}
    assert "Erik" not in names and not any(n.startswith("knappast") for n in names)


@pytest.mark.parametrize("text,expected", [
    ("So 113_1_4 thin_closed holes.stl", "Sö 113"),
    ("U_11_mesh.obj", "U 11"),
    ("Vg59.stl", "Vg 59"),
])
def test_find_signum_in_filenames(text, expected):
    assert store().find_in_text(text)[0]["signum"] == expected


def test_rundata_endpoints(client):
    assert client.get("/api/rundata/inscription/U%2011").json()["signum"] == "U 11"
    assert client.get("/api/rundata/inscription/XX%209999").status_code == 404
    assert client.get("/api/rundata/search?carver=Balle").json()["total"] > 50
    geo = client.get("/api/rundata/geo").json()
    assert len(geo["rows"]) > 4000
    styles = client.get("/api/rundata/styles").json()
    assert {g["code"] for g in styles["groups"]} >= {"RAK", "Fp", "Pr4"}


def test_raa_fetch_uses_rundata_without_ai(client):
    body = client.post("/api/raa/fetch", json={"signum": "U 11"}).json()
    assert body["source"] == "rundata" and "Olev" in body["attributed_carver"]


def test_orthography_ranks_signed_carver_first(client):
    r = client.get("/api/orthography/carvers/U%20729?limit=3").json()
    assert r["ranking"][0]["carver"] == "Balle"
    ev = r["evaluation"]
    # Metoden ska vara klart bättre än slumpen även för enbart signerade inskrifter
    assert ev["signed_only"]["top1_accuracy"] > 5 * ev["chance_top1"]


def test_synthesis_without_ai_returns_evidence(client, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    r = client.post("/api/synthesis/analyze", json={
        "signum": "U 729",
        "slices": [{"angle": 70, "asymmetry": 3, "depth": 2, "width": 6},
                   {"angle": 72, "asymmetry": 2, "depth": 2.1, "width": 6.2}],
    }).json()
    assert r["ai_used"] is False
    top = r["candidates"][0]
    assert top["name"] == "Balle" and top["strength"] == "stark"
    assert {e["source"] for e in top["evidence"]} >= {"Rundata", "Ortografi"}
    assert "probability" not in top
