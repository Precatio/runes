"""Färdiga JSON-svar (api/cache.py): ETag och 304, förkomprimering, okomprimerad storlek och ett bygge per nyckel."""
import gzip
import threading
import time

from fastapi.testclient import TestClient

from api import cache
from api.main import app


class _Req:
    def __init__(self, **headers):
        self.headers = {k.replace("_", "-"): v for k, v in headers.items()}


def test_etag_gzip_and_uncompressed_size():
    cache.clear()
    data = {"rows": [{"signum": f"U {i}", "text": "runa " * 20} for i in range(200)]}
    plain = cache.cached_json(_Req(), "t|1", lambda: data)
    etag = plain.headers["etag"]
    assert plain.headers["cache-control"] == "no-cache" and plain.media_type == "application/json"
    zipped = cache.cached_json(_Req(accept_encoding="gzip, br"), "t|1", lambda: data)
    assert zipped.headers["content-encoding"] == "gzip"
    assert gzip.decompress(zipped.body) == plain.body and zipped.headers["x-content-length"] == str(len(plain.body))
    assert len(zipped.body) < len(plain.body) / 4
    assert cache.cached_json(_Req(if_none_match=etag), "t|1", lambda: data).status_code == 304


def test_one_build_per_key_also_when_asked_at_once():
    cache.clear()
    calls = []

    def build():
        calls.append(1)
        time.sleep(0.2)
        return {"ok": True}
    threads = [threading.Thread(target=cache.json_bytes, args=("t|2", build)) for _ in range(4)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert len(calls) == 1


def test_large_answers_are_compressed_and_revalidated():
    client = TestClient(app)
    r = client.get("/api/rundata/geo", headers={"Accept-Encoding": "gzip"})
    assert r.status_code == 200 and r.headers["content-encoding"] == "gzip" and "x-content-length" in r.headers
    assert client.get("/api/rundata/geo", headers={"If-None-Match": r.headers["etag"]}).status_code == 304
    small = client.get("/api/rundata/meta", headers={"Accept-Encoding": "gzip"})
    assert "content-encoding" not in small.headers  # under the 1 kB limit
