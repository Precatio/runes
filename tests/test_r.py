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


@needs_r
def test_change_module_runs_on_the_corpus(rows, tmp_path, monkeypatch):
    monkeypatch.setenv("R_DISABLED", "0")
    if not r_bridge.status()["available"]:
        pytest.skip("R-paket saknas")
    r_bridge.write_csv(rows, str(tmp_path / "corpus.csv"))
    params = {"corpus": str(tmp_path / "corpus.csv"), "corpus_dir": str(tmp_path), "water_dir": None, "seed": 2026,
              "draws": 1}
    ch = r_bridge.run_module("change", params, str(tmp_path))
    feats = {f["key"]: f for f in ch["features"]}
    # Dotted runes become more common over the 11th century (with place and carver held constant)
    st = feats["stungna"]["time"]
    assert st["tested"] and st["shape"] == "rises" and st["q"] < 0.05 and st["last"] > st["first"]
    assert all(0 <= p["share"] <= 1 for p in st["curve"])
    assert {a["key"] for a in ch["assoc"]} == {"bro_bon", "bro_sjal", "bro_cross"}
    assert (tmp_path / ch["figures"]["time"]).exists()


def test_change_patterns_only_report_adjusted_results():
    ch = {"features": [
        {"key": "stungna", "label": "Stungna runor", "time": {"tested": True, "q": 0.0001, "shape": "rises", "first": 0.35,
                                                           "last": 0.85, "year_first": 998, "year_last": 1115,
                                                           "draws": {"n": 20, "share_sig": 1.0}},
         "provinces": {"p_differ": 0.03, "rows": [{"province": "U", "share1050": 0.5, "cross_year": 1043},
                                                  {"province": "Ög", "share1050": 0.7, "cross_year": 1000}]}},
        {"key": "bon", "label": "Kristen bön", "time": {"tested": True, "q": 0.2, "shape": "peak", "peak_year": 1035,
                                                      "first": 0.12, "last": 0.02, "year_first": 998, "year_last": 1115},
         "provinces": {"p_differ": 0.001, "rows": [{"province": "U", "share1050": 0.26, "cross_year": None},
                                                   {"province": "Ög", "share1050": 0.08, "cross_year": None}]}}],
        "assoc": [{"label": "Själsbön på bro- och vägstenar", "share_x": 0.23, "share_other": 0.15,
                   "all": {"or": 1.8, "lo": 1.07, "hi": 2.98, "q": 0.08}}]}
    pats = r_findings.change_patterns(ch)
    texts = " ".join(p["text"] for p in pats)
    assert pats[0]["status"] == "bekräftar" and "blir vanligare" in pats[0]["text"] and "20 av 20" in pats[0]["text"]
    # q 0.2 for the prayer curve and q 0.08 for the bridges: not reported; the province difference (p 0.001) is
    assert "vanligast omkring" not in texts and "bro- och vägstenar" not in texts
    assert any("26 % i U till 8 % i Ög" in p["text"] for p in pats)


def _anonymous(signa):
    return {"validation": {"purity": 0.71, "purity_geography": 0.55, "share_pure": 0.73},
            "groups": [{"id": 1, "status": "candidate", "name": "Fröderydsristaren", "type_stone": signa[0], "n": len(signa),
                        "stones": signa, "stability": 0.95,
                        "marks": [{"feature": "Resarformel: satte", "share_group": 0.73, "share_area": 0.13}]},
                       {"id": 2, "status": "known", "name": None, "type_stone": "U 433", "n": 6, "stones": ["U 433"],
                        "stability": 0.5, "marks": []}]}


def test_anonymous_groups_become_findings_with_a_working_name():
    s = store()
    signa = [r["signum"] for r in s.inscriptions if r["signum"].startswith("Sm ") and not r["carvers"]][:4]
    out = r_findings.anonymous_findings(_anonymous(signa), s.get, s.inscriptions)
    assert {f["signum"] for f in out} == set(signa)
    f = out[0]
    assert f["method"] == r_findings.ANONYMOUS and f["verdict"] == "nytt" and "Fröderydsristaren" in f["ours"]
    assert any("inte en person" in r for r in f["reasons"]["nyhet"])
    # Groups that resemble a known carver are not reported as unknown carvers
    pats = r_findings.corpus_patterns({"anonymous": _anonymous(signa)})
    assert any(p["topic"] == "Okända ristare" and "1 grupp av" in p["text"] and "Fröderydsristaren" in p["text"] for p in pats)


def test_unchanged_modules_are_reused_from_an_earlier_run(tmp_path, monkeypatch):
    monkeypatch.setattr(r_bridge, "CACHE_DIR", str(tmp_path))
    csv_data = b"signum\nU 1\n"
    versions = r_bridge.module_hashes(csv_data)
    prev = tmp_path / "corpus" / "aaa"
    prev.mkdir(parents=True)
    (prev / "change.json").write_text('{"n_dated": 1}')
    (prev / "forandring_tid.png").write_bytes(b"png")
    # An earlier run where 'change' had the same version, and 'network' a different one
    (prev / "done.json").write_text(json.dumps({"module_hashes": {"change": versions["change"], "network": "other"},
                                                "errors": {}}))
    new = tmp_path / "corpus" / "bbb"
    new.mkdir(parents=True)
    (new / "corpus.csv").write_bytes(csv_data)
    calls = []

    def fake_run(m, params, out_dir, timeout=3600):
        calls.append(m)
        (new / f"{m}.json").write_text("{}")
        return {}
    monkeypatch.setattr(r_bridge, "run_module", fake_run)
    monkeypatch.setattr(r_bridge, "ensure_water", lambda: None)
    monkeypatch.setattr(r_bridge, "status", lambda: {"version": "R test"})
    r_bridge.run_corpus("bbb")
    done = json.loads((new / "done.json").read_text())
    assert "change" not in calls and "network" in calls and done["reused"] == ["change"]
    assert (new / "forandring_tid.png").read_bytes() == b"png" and done["module_hashes"] == versions
    # A module reruns when a module it reads changes: anonymous depends on attribution
    assert r_bridge.DEPENDS["anonymous"] and "attribution" in r_bridge.DEPENDS["anonymous"]


def test_explanations_answer_each_question_in_plain_words():
    from src import r_explain
    res = {"geography": {"carvers": [{}] * 29, "n_compact": 24, "min_inscriptions": 5,
                         "water": {"available": True, "overall": {"median_stones_km": 4.2, "median_random_km": 5.8, "p": 1e-9}}},
           "attribution": {"ablation": [{"features": "Alla", "accuracy": 0.72, "top3": 0.86},
                                        {"features": "Geografi", "accuracy": 0.44}, {"features": "Språk och innehåll", "accuracy": 0.62}],
                           "majority_baseline": 0.19, "carvers": ["a"] * 18,
                           "calibration": {"reliability": [{"threshold": 0.5, "n": 140, "accuracy": 0.95}]}},
           "anonymous": {"validation": {"purity": 0.69, "purity_geography": 0.43},
                         "groups": [{"status": "candidate", "name": "Konungsundsristaren", "n": 30, "provinces": "Ög"},
                                    {"status": "known", "n": 5}]},
           "change": {"features": [{"key": "stungna", "label": "Stungna runor", "time": {
               "tested": True, "q": 0.0, "shape": "rises", "first": 0.35, "last": 0.85,
               "curve": [{"year": 998, "share": 0.35}, {"year": 1115, "share": 0.85}]}}]}}
    secs = {s["key"]: s for s in r_explain.sections(res)}
    assert set(secs) == {"geography", "attribution", "anonymous", "change"}
    for s in secs.values():
        assert s["question"].endswith("?") and s["answer"] and s["short"] and s["interpretation"] and s["not_saying"]
        assert s["confidence"] in ("säkert", "troligt", "osäkert")
    assert secs["geography"]["headline"]["value"] == "24 av 29"
    # One province is written by R as a plain string; q exactly 0 is significant
    assert "Östergötland" in secs["anonymous"]["interpretation"][0]
    assert secs["change"]["headline"]["value"] == "1 av 1" and "stungna runor blir vanligare" in secs["change"]["answer"]
    ov = r_explain.overview(res)
    assert any(p.startswith("**Ristarna och deras hand.**") for p in ov["paragraphs"]) and ov["next_steps"]


def test_every_corpus_pattern_says_whether_it_is_significant():
    res = {"geography": {"carvers": [{"compact_q": 0.01}, {"compact_q": 0.3}], "n_compact": 1, "min_inscriptions": 5,
                         "water": {"available": True, "overall": {"median_stones_km": 4, "median_random_km": 6, "p": 1e-9}}},
           "dialect": {"mantel": {"r": 0.29, "p": 0.004}, "n_districts": 38},
           "chronology": {"validation": {"rho": 0.54, "partial_rho": 0.54, "usable": True, "mae_loo_years": 21,
                                         "mae_naive_years": 25, "p": 1e-30}, "corpus_dimensions": []}}
    pats = r_findings.corpus_patterns(res)
    assert pats and all("significance" in p for p in pats)
    assert all(p["significance"]["significant"] for p in pats)
    assert any(p["significance"]["label"] == "p < 0,001" for p in pats)
