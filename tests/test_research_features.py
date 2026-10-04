import base64
import os

import numpy as np
import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.rundata import DATA_PATH
from src.graphemes import cosine, extract
from src.stats import METRICS
from src.synthetic_runes import RUNES, render

needs_rundata = pytest.mark.skipif(not os.path.exists(DATA_PATH), reason="data/rundata.json saknas")


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_rune_forms_recognised_despite_lighting_and_scale():
    items = [(r, extract(render(r, seed=k * 7 + len(r), dark_strokes=(k % 3 != 0)))["feature_vector"])
             for r in RUNES for k in range(6)]
    hits = 0
    for i, (r, v) in enumerate(items):
        best = max((cosine(v, w), j) for j, (_, w) in enumerate(items) if j != i)[1]
        hits += items[best][0] == r
    assert hits / len(items) >= 0.7  # chance is 20 %


def test_extract_features_endpoint(client):
    img = "data:image/png;base64," + base64.b64encode(render("ᚱ")).decode()
    body = client.post("/api/2d/extract_features", json={"image_base64": img}).json()
    assert body["feature_version"] == "grapheme-2" and body["form_png"].startswith("data:image/png")


def test_recompute_reproduces_measurement(client):
    r = client.post("/api/3d/analyze", data={"use_mock": "true", "origin_x": 0, "origin_y": 0, "origin_z": 0,
                                              "dir_x": 0, "dir_y": 1, "dir_z": 0, "slice_count": 3}).json()
    profiles = [s["profile"] for s in r["slices"]]
    rc = client.post("/api/stats/recompute", json={"profiles": profiles}).json()
    for a, b in zip(r["slices"], rc["slices"]):
        assert abs(a["apex_vinkel_deg"] - b["apex_vinkel_deg"]) < 0.01  # profiles are stored rounded to 0.1 µm


@needs_rundata
def test_research_gaps(client):
    r = client.post("/api/research/gaps", json={"measured_signa": ["So 113"]}).json()
    totals = r["coverage"]["totals"]
    assert totals["total"] > 2000 and totals["carver"] < totals["total"] and totals["measured"] == 1
    h = r["hypotheses"]
    assert h["new"] and {"carver", "similarity", "carver_precision", "in_carver_area"} <= h["new"][0].keys()
    assert all(x["n_words"] >= 8 for x in h["new"])
    assert r["measurement_priorities"][0]["inscriptions"] >= 5
    assert "Axelson" in r["source_note"]


@needs_rundata
def test_synthesis_style_check(client, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    r = client.post("/api/synthesis/analyze", json={"signum": "U 11", "two_d": {"predicted_style": "Pr3"}}).json()
    sc = r["evidence"]["style_check"]
    assert sc["rundata_style"] == "Pr4" and sc["agrees"] is False


@needs_rundata
def test_academic_report(client):
    rng = np.random.default_rng(3)
    entries = []
    for sig, mu in [("U 729", 70), ("U 707", 72), ("U 1022", 95), ("U 1034", 97)]:
        vals = rng.normal([mu, 3, 2, 6, .33, .2, .05], [2, 1, .2, .4, .02, .03, .01])
        entries.append({"signum": sig, "means": dict(zip(METRICS, vals)), "slices": [{}] * 4,
                        "feature_type": "rune", "method_version": "groove-3", "contributorName": "Test"})
    r = client.post("/api/reports/academic", json={"entries": entries, "use_ai": False}).json()
    assert "Tabell 2" in r["markdown"] and "Balle" in r["markdown"] and r["figures"]
    assert r["latex"].startswith(r"\documentclass")
    d = client.post("/api/reports/academic", json={"entries": entries, "use_ai": False, "format": "docx"})
    assert d.status_code == 200 and d.content[:2] == b"PK"
    # AI text from the preview is reused as-is, without a new AI call
    ai = {"abstract": "SAMMANFATTNINGSTEST", "introduction": "INLEDNINGSTEST", "discussion": "DISKUSSIONSTEST"}
    r = client.post("/api/reports/academic", json={"entries": entries, "use_ai": True, "ai_text": ai}).json()
    assert r["ai_used"] and "SAMMANFATTNINGSTEST" in r["markdown"] and "DISKUSSIONSTEST" in r["markdown"]


@needs_rundata
def test_findings_compare_with_rundata(client):
    from api.rundata import store
    from src.research_gaps import certain_carvers, has_carver, is_runestone

    recs = [r for r in store().inscriptions if is_runestone(r) and r["signum"].startswith("U ")]
    by = {}
    for r in recs:
        cs = certain_carvers(r)
        if len(cs) == 1 and cs[0] in ("Öpir 1", "Åsmund", "Balle"):
            by.setdefault(cs[0], []).append(r["signum"])
    rng = np.random.default_rng(5)
    centre = {"Öpir 1": 95, "Åsmund": 80, "Balle": 70}
    corpus = []
    for carver, signa in by.items():
        for sig in signa[:3]:
            vals = rng.normal([centre[carver], 3, 2, 6, .33, .2, .05], [1, .3, .05, .1, .01, .01, .002])
            corpus.append({"signum": sig, "feature_type": "rune", "means": dict(zip(METRICS, vals))})
    unattributed = next(r["signum"] for r in recs if not has_carver(r) and not r["flags"]["lost"])
    vals = rng.normal([95, 3, 2, 6, .33, .2, .05], [1, .3, .05, .1, .01, .01, .002])
    corpus.append({"signum": unattributed, "feature_type": "rune", "means": dict(zip(METRICS, vals))})

    r = client.post("/api/research/findings", json={
        "corpus": corpus, "styles": [{"signum": "U 11", "style": "Pr3", "confidence": 80}]}).json()
    tech = [f for f in r["findings"] if f["method"] == "huggteknik"]
    new = [f for f in tech if f["signum"] == unattributed]
    assert new and new[0]["verdict"] == "nytt" and new[0]["suggested"] == "Öpir 1"
    assert any(f["verdict"] == "stämmer" for f in tech)
    style = [f for f in r["findings"] if f["method"].startswith("stilgrupp")]
    assert style[0]["verdict"] == "motsäger"  # Rundata: Pr4
    for f in r["findings"]:
        assert 0 <= f["evidence"] <= 1 and 0 <= f["novelty"] <= 1 and 0 <= f["relevance"] <= 1
        assert f["verdict"] in ("stämmer", "nytt", "motsäger") and f["reasons"]["belägg"]
    assert r["summary"]["counts"]["nytt"] > 0


@needs_rundata
def test_synthesis_weighs_checks_and_reports_conflicts(client, monkeypatch):
    from api.rundata import store
    from src.research_gaps import certain_carvers, is_runestone

    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    rng = np.random.default_rng(2)

    def slices(mu, n=8):
        return [dict(zip(METRICS, rng.normal([mu, 3, 2, 6, .33, .2, .05], [1.5, .5, .1, .2, .01, .01, .002])))
                | {"position_mm": i} for i in range(n)]

    by = {}
    for r in store().inscriptions:
        cs = certain_carvers(r)
        if is_runestone(r) and r["signum"].startswith("U ") and len(cs) == 1 and cs[0] in ("Öpir 1", "Åsmund", "Balle"):
            by.setdefault(cs[0], []).append(r["signum"])
    centre = {"Öpir 1": 95, "Åsmund": 80, "Balle": 70}
    corpus = []
    for carver, signa in by.items():
        for sig in signa[:3]:
            x = slices(centre[carver])
            corpus.append({"signum": sig, "feature_type": "rune", "slices": x,
                           "means": {m: float(np.mean([a[m] for a in x])) for m in METRICS}})

    # U 344 is attributed to Åsmund; the measurements look like Åsmund's
    r = client.post("/api/synthesis/analyze", json={
        "signum": "U 344", "corpus": corpus,
        "analyses": [{"id": "orn", "feature_type": "ornament", "slices": slices(95)},
                     {"id": "run", "feature_type": "rune", "slices": slices(80)}]}).json()
    assert r["analysis_used"]["id"] == "run" and r["analysis_used"]["n"] == 8  # runes, not the last saved
    top = r["candidates"][0]
    assert top["name"] == "Åsmund" and top["literature"]["verdict"] == "stämmer"
    assert "Huggteknik" in top["first_in"] and top["stone_tests"]["compatible"] >= 2
    assert top["geography"]["in_area"] and top["styles"]["styles"]
    assert r["outcome"]["verdict"] == "stämmer" and "huggteknik" in r["outcome"]["support"]

    # Measurements like Öpir's on Åsmund's stone: the conflict is spelled out without AI
    r2 = client.post("/api/synthesis/analyze", json={
        "signum": "U 344", "corpus": corpus,
        "analyses": [{"id": "run", "feature_type": "rune", "slices": slices(95)}]}).json()
    assert any("huggtekniken liknar Öpir 1" in c for c in r2["conflicts"])

    # Without corpus or measurements, the missing evidence is explained
    r3 = client.post("/api/synthesis/analyze", json={"signum": "U 344", "corpus_note": "logga in"}).json()
    assert any(m.startswith("Huggteknik: logga in") for m in r3["missing"])
