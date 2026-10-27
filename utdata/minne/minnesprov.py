"""Minnesprov för analysmotorn (2026-10-26): fyra stora skanningar i rad genom API:t (uppladdning + automatisk analys
enligt protokollet), med cachen på en modell, och processens minne (RSS) efter varje. --utan stänger av den
uttryckliga städningen (gc.collect blir en no-op), som före rättelsen i api/mesh_cache.py och api/main.py.

  MESH_CACHE_SIZE=1 MAX_MESH_UPLOAD_MB=2000 .venv/bin/python -m utdata.minne.minnesprov [--utan]
"""
from __future__ import annotations

import gc
import json
import os
import subprocess
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
DEPTH = "/Volumes/2TB/cache/runmodell/djup/halsingland"
FILES = ["HS_10_1b_thin03", "HS_10_3a_thin03", "HS_10_1a_thin03", "HS_10_3b_thin03"]


def rss_gb() -> float:
    out = subprocess.run(["ps", "-o", "rss=", "-p", str(os.getpid())], capture_output=True, text=True).stdout
    return int(out.strip()) / 1e6


def main():
    utan = "--utan" in sys.argv
    if utan:
        gc.collect = lambda *a, **k: 0  # the cleanup off: only Python's own, automatic collections
    from fastapi.testclient import TestClient
    from api.main import app
    from scripts.download_open_scans import local_path
    c = TestClient(app, base_url="http://localhost")
    rows = [{"steg": "start", "rss_gb": round(rss_gb(), 2)}]
    print(rows[-1], flush=True)
    for stem in FILES:
        meta = json.load(open(os.path.join(DEPTH, stem + ".json"), encoding="utf-8"))
        t0 = time.time()
        with open(local_path("halsingland", meta["file"]), "rb") as fh:
            r = c.post("/api/3d/upload", files={"file": (meta["file"], fh, "application/octet-stream")})
        r.raise_for_status()
        mid = r.json()["mesh_id"]
        n = meta["normal"]
        r = c.post("/api/3d/auto_analyze", data={"mesh_id": mid, "normal_x": n[0], "normal_y": n[1], "normal_z": n[2],
                                                 "protocol": "true"})
        r.raise_for_status()
        rows.append({"steg": stem, "rss_gb": round(rss_gb(), 2), "godkanda": r.json()["counts"]["accepted"],
                     "sekunder": round(time.time() - t0)})
        print(rows[-1], flush=True)
    out = os.path.join(os.path.dirname(__file__), f"minnesprov_{'utan' if utan else 'med'}.json")
    json.dump(rows, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
