"""Statistik i R: export av korpusen, fynd och mönster, avstämning mot nyare källor, rapportavsnitt och – om R
finns installerat – en körning av två R-moduler på den riktiga korpusen."""
import json
import os
import shutil

import pytest

from api.rundata import store
from api.routers.orthography import model as orthography_model
from src import crosscheck, r_bridge, r_findings, r_report


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient
    from api.main import app
    return TestClient(app)


@pytest.fixture(scope="module")
def rows():
    return r_bridge.corpus_rows(store().inscriptions, orthography_model().names)


def test_corpus_rows_cover_runestones_with_features(rows):
    assert len(rows) > 2000
    so113 = next(r for r in rows if r["signum"] == "Sö 113")
    assert so113["province"] == "Sö" and so113["style"] == "RAK" and so113["carver"] == ""
    assert (so113["style_from"], so113["style_to"]) == (980, 1015)
    assert so113["cat_minne"] == 1 and so113["trait_ai_sten"] == "monoftong"
    assert "stæin=stin" in so113["pairs"]
    data = r_bridge.csv_bytes(rows)
    header = data.split(b"\n", 1)[0].decode()
    assert header.split(",") == r_bridge.CSV_COLUMNS


def test_fingerprint_ignores_stone_scripts(rows, monkeypatch):
    data = r_bridge.csv_bytes(rows[:50])
    fp = r_bridge.fingerprint(data)
    assert fp == r_bridge.fingerprint(data)
    assert fp != r_bridge.fingerprint(data + b"x")


def test_status_when_disabled(client):
    st = client.get("/api/r/status").json()
    assert st["r"]["available"] is False
    assert client.post("/api/r/corpus/run").status_code == 503


def _attribution():
    return {"carvers": ["Öpir 1", "Fot 2"],
            "calibration": {"reliability": [{"threshold": 0.3, "n": 300, "accuracy": 0.8},
                                            {"threshold": 0.5, "n": 140, "accuracy": 0.93}]},
            "predictions": [{"signum": "U 275", "top": "Fot 2", "p": 0.75, "second": "Öpir 1", "p2": 0.16,
                             "near_km": 0.5, "rundata_uncertain": ""},
                            {"signum": "U 1040", "top": "Öpir 1", "p": 0.63, "second": "Fot 2", "p2": 0.07,
                             "near_km": 1, "rundata_uncertain": "Kjule;Osniken;Kättilmund"}]}


def test_model_findings_skip_carvers_outside_the_model():
    s = store()
    out = r_findings.model_findings(_attribution(), s.get, s.inscriptions)
    signa = {f["signum"]: f for f in out}
    assert "U 275" in signa and signa["U 275"]["verdict"] == "nytt" and signa["U 275"]["suggested"] == "Fot 2"
    # Signed by carvers the model does not know: not a contradiction
    assert "U 1040" not in signa
    assert any("väljer bara bland" in r for r in signa["U 275"]["reasons"]["belägg"])


def test_corpus_patterns_flag_unexplained_dimension():
    res = {"chronology": {"validation": {"rho": 0.55, "partial_rho": 0.54, "usable": True, "mae_loo_years": 21,
                                         "mae_naive_years": 25},
                          "corpus_dimensions": [{"dim": 1, "inertia_pct": 7.5, "rho_time": 0.01, "rho_lat": 0.17,
                                                 "eta2_province": 0.04, "eta2_carver": 0.25, "positive": ["Kristen bön: ja"],
                                                 "negative": ["Kristen bön: nej"], "unexplained": True}]}}
    pats = r_findings.corpus_patterns(res)
    assert pats[0]["status"] == "bekräftar" and "Gräslunds" in pats[0]["text"]
    assert any(p["status"] == "mönster att pröva" and "varken tid" in p["text"] for p in pats)


def test_crosscheck_parsing():
    assert crosscheck._expand_signa("U 1015 och 1018-1020") == ["U 1015", "U 1018", "U 1019", "U 1020"]
    assert crosscheck._expand_signa("U Fv1953;270 och U Fv1979;245") == ["U Fv1953;270", "U Fv1979;245"]
    assert crosscheck._is_name("Öpir 1") and crosscheck._is_name("Torgöt Fotsarve")
    assert not crosscheck._is_name("En ovan och osäker ristare.")
    assert crosscheck.SAME_AS.match("Troligen samma som gjort U 1017-1024.")
    assert crosscheck._name_match("Öpir 1", "Öpir") and not crosscheck._name_match("Balle", "Tidkume")


def test_crosscheck_statuses_from_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(crosscheck, "CACHE", str(tmp_path))
    records = {
        "U 1022": {"signum": "U 1022", "carvers": [{"name": "Samma som gjort U 1015, 1017-1021", "attribution": "attributed"},
                                                   {"name": "Öpir 1", "attribution": "signed"}], "references": ["Källström 2007a"]},
        "U 1017": {"signum": "U 1017", "carvers": [{"name": "Samma som gjort U 1022.", "attribution": "attributed"}],
                   "references": []},
        "Sö 158": {"signum": "Sö 158", "carvers": [{"name": "Tidigare tolkad som signerad av Traen.", "attribution": None}],
                   "references": []},
        "U 275": {"signum": "U 275", "carvers": [], "references": []},
    }
    for sg, rec in records.items():
        with open(crosscheck._path("runor", f"{crosscheck._safe(sg)}.json"), "w", encoding="utf-8") as fh:
            json.dump(rec, fh, ensure_ascii=False)
    monkeypatch.setattr(crosscheck, "runor", lambda sg, refresh=False: records.get(sg))
    assert crosscheck.check("U 1017", "Öpir 1", {}, fetch=False)["status"] == "finns redan"
    assert crosscheck.check("Sö 158", "Traen", {}, fetch=False)["status"] == "nämns"
    assert crosscheck.check("U 275", "Fot 2", {}, fetch=False)["status"] == "saknas"
    assert crosscheck.check("U 275", "Fot 2", {"U275": ["Fot"]}, fetch=False)["status"] in ("finns redan", "saknas")
    f = {"signum": "U 1017", "verdict": "nytt", "evidence": 0.8, "novelty": 0.85, "relevance": 0.7, "score": 0.48,
         "assessment": "Sannolikt ny", "reasons": {"belägg": [], "nyhet": [], "relevans": []}}
    applied = crosscheck.apply(f, crosscheck.check("U 1017", "Öpir 1", {}, fetch=False))
    assert applied["novelty"] == 0.05 and applied["assessment"].startswith("Finns redan")


def test_report_blocks_from_r_results():
    r = {"model": {"top": [{"carver": "Traen", "p": 0.21}], "source": "stenen ingick inte i träningen", "in_range": True,
                   "near_limit_km": 25, "reliability": [{"threshold": 0.3, "n": 300, "accuracy": 0.84}],
                   "candidates": [{"carver": "Traen", "in_model": True, "p": 0.21, "rank": 1},
                                  {"carver": "Ärnfast", "in_model": False, "p": None, "rank": None}]},
         "cluster": {"included": True, "cluster": 1, "k": 5, "silhouette": 0.43, "structure": "svag men verklig",
                     "profile": {"n": 178, "features": [{"level": "Kors=inget kors", "share_in_cluster": 1, "share_overall": 0.4}]},
                     "neighbours": [{"signum": "U 4", "distance": 0, "carver": None, "cluster": 1}]},
         "chronology": {"included": False, "note": "Seriationen gäller Upplands runstenar."},
         "formulas": [{"label": "Resarformel", "value": "satte", "overall_share": 0.03,
                       "candidates": [{"carver": "Traen", "n": 22, "k": 0, "share": 0}]}]}
    figs, tabs = [], []
    fig = lambda png, cap, slug: figs.append(cap) or {"type": "figure"}
    tab = lambda h, rows, cap: tabs.append(cap) or {"type": "table", "headers": h, "rows": rows}
    blocks = r_report.attribution_blocks(r, "Sö 113", fig, tab) + r_report.corpus_blocks(r, "Sö 113", fig, tab)
    text = json.dumps(blocks, ensure_ascii=False)
    assert "Traen högst sannolikhet (0,21)" in text and "nej (för få säkra stenar)" in text
    assert "grupp 1 av 5" in text and "Upplands runstenar" in text
    assert any("formler" in t for t in tabs)
    assert r_report.landscape_blocks(None, "Sö 113", fig, tab) == []


needs_r = pytest.mark.skipif(not shutil.which("Rscript") and not os.path.exists("/opt/homebrew/bin/Rscript"),
                             reason="R är inte installerat")


@needs_r
def test_r_modules_run_on_the_corpus(rows, tmp_path, monkeypatch):
    monkeypatch.setenv("R_DISABLED", "0")
    if not r_bridge.status()["available"]:
        pytest.skip("R-paket saknas")
    r_bridge.write_csv(rows, str(tmp_path / "corpus.csv"))
    params = {"corpus": str(tmp_path / "corpus.csv"), "corpus_dir": str(tmp_path), "water_dir": None, "seed": 2026}
    text = r_bridge.run_module("text", params, str(tmp_path))
    assert text["formulas"]["tests"] and text["lemmas"][0]["cramers_v"] > 0.3
    assert (tmp_path / "text_features.csv").exists() and (tmp_path / "text_formler.png").exists()
    clusters = r_bridge.run_module("clusters", params, str(tmp_path))
    assert 2 <= clusters["k"] <= 10 and clusters["n_stones"] > 500
    assert all(0 <= c["stability"] <= 1 for c in clusters["clusters"])
