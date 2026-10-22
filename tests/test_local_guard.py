"""Analysmotorn på den egna datorn: bara egna värdnamn, inga ändrande anrop från främmande sidor, och de delade
cacherna (api/cache.py) som skriver atomiskt och räknar en sak en gång också när två anrop kommer samtidigt."""
import json
import os
import threading
import time

import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_a_foreign_host_name_is_refused(client):
    # DNS rebinding: a page on evil.example whose name points at 127.0.0.1 sends its own name as Host
    assert client.get("/", headers={"Host": "evil.example.com:8000"}).status_code == 400
    for host in ("localhost:8000", "127.0.0.1:8000", "[::1]:8000"):
        assert client.get("/", headers={"Host": host}).status_code == 200


def test_writes_from_a_foreign_page_are_refused(client):
    # A form or a body-less POST needs no CORS preflight; the guard refuses it before any work is done
    r = client.post("/api/r/corpus/run", headers={"Origin": "https://evil.example"})
    assert r.status_code == 403
    r = client.post("/api/r/corpus/run", headers={"Sec-Fetch-Site": "cross-site"})
    assert r.status_code == 403
    # A GET is not a write: the CORS headers decide whether the foreign page may read it
    assert client.get("/", headers={"Origin": "https://evil.example"}).status_code == 200


def test_the_app_itself_and_the_next_server_may_write(client):
    # The local web app's own origins (the browser), and no Origin at all (the Next server, scripts, the tests): the
    # request reaches the route (503 here because R is turned off in the tests, not 403)
    for headers in ({"Origin": "http://localhost:3000", "Sec-Fetch-Site": "same-site"},
                    {"Origin": "http://127.0.0.1:3000"}, {}):
        assert client.post("/api/r/corpus/run", headers=headers).status_code == 503


def test_a_preflight_from_the_app_still_gets_cors_headers(client):
    r = client.options("/api/research/findings", headers={
        "Origin": "http://127.0.0.1:3000", "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type"})
    assert r.status_code == 200 and r.headers["access-control-allow-origin"] == "http://127.0.0.1:3000"


def test_a_figure_path_must_be_a_fingerprint(client):
    for fp in ("..", "x" * 16, "0123456789abcdef0"):
        assert client.get(f"/api/r/figure/{fp}/a.png").status_code == 404


def test_a_scan_reference_outside_its_folder_is_never_found():
    from src import trace_reader
    assert trace_reader.scan_ref("../../../../package") is None
    assert trace_reader.scan_ref("../" * 12 + "etc/hosts") is None


def test_json_is_written_atomically_by_concurrent_writers(tmp_path):
    from api.cache import write_json
    path = str(tmp_path / "sub" / "x.json")
    errors = []

    def write(i):
        try:
            for _ in range(20):
                write_json(path, {"i": i, "data": list(range(200))})
        except Exception as e:  # noqa: BLE001
            errors.append(e)
    threads = [threading.Thread(target=write, args=(i,)) for i in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors and json.load(open(path))["data"] == list(range(200))
    assert os.listdir(tmp_path / "sub") == ["x.json"]  # no temporary file left behind


def test_a_slow_builder_runs_once_for_simultaneous_callers():
    from functools import lru_cache
    from api.cache import single_flight
    calls = []

    @single_flight
    @lru_cache(maxsize=2)
    def build(key):
        calls.append(key)
        time.sleep(0.2)
        return {"key": key}
    out = []
    threads = [threading.Thread(target=lambda: out.append(build("a"))) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert calls == ["a"] and all(o is out[0] for o in out)
    build.cache_clear()
    build("a")
    assert calls == ["a", "a"]


def test_the_text_model_keeps_only_the_latest_folds(monkeypatch):
    from src import textmodel
    built = []
    monkeypatch.setattr(textmodel, "_bundles", textmodel.OrderedDict())
    monkeypatch.setattr(textmodel, "MAX_BUNDLES", 2)
    monkeypatch.setattr(textmodel, "_build", lambda keep: built.append(1) or {"n": len(built)})
    a = textmodel.bundle(0)
    textmodel.bundle(1)
    assert textmodel.bundle(0) is a  # kept, and now the latest used
    textmodel.bundle(2)  # fold 1 goes
    assert list(textmodel._bundles) == [0, 2] and len(built) == 3
    textmodel.bundle(1)
    assert len(built) == 4 and list(textmodel._bundles) == [2, 1]


def test_identical_r_requests_share_one_run(tmp_path, monkeypatch):
    from src import r_bridge
    runs = []

    def fake_run(module, params, out_dir, timeout=3600):
        runs.append(module)
        time.sleep(0.2)
        with open(os.path.join(out_dir, f"{module}.json"), "w") as fh:
            json.dump({"ok": True}, fh)
    monkeypatch.setattr(r_bridge, "run_module", fake_run)
    out_dir = str(tmp_path)
    out = []
    threads = [threading.Thread(target=lambda: out.append(r_bridge._cached_run(
        os.path.join(out_dir, "stone.json"), "stone", {}, out_dir, 10))) for _ in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert runs == ["stone"] and out == [{"ok": True}] * 3
