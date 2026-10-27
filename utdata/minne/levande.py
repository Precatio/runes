"""Minnesprov 2: hur många 3D-modeller som fortfarande lever i analysmotorn efter varje uppladdning (cachen rymmer en),
och hur mycket deras punkter och trianglar väger. Mäter mekanismen direkt, oberoende av hur mycket av processen som
ligger i växlingsfilen. --utan stänger av den uttryckliga städningen (som före rättelsen).

  MESH_CACHE_SIZE=1 .venv/bin/python -m utdata.minne.levande [--utan]
"""
import gc
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
FILES = [("medelpad", "M_1_Nolby_thin03"), ("medelpad", "M_11_Högom_thin03"), ("medelpad", "M_4_Attmarby_thin02"),
         ("medelpad", "M_15_Sköns_kyrka_thin02"), ("medelpad", "M_8_Sköle_thin03"), ("medelpad", "M_3_Berga_thin02")]


def alive():
    import trimesh
    ms = [o for o in gc.get_objects() if isinstance(o, trimesh.Trimesh)]
    return len(ms), round(sum(m.vertices.nbytes + m.faces.nbytes for m in ms) / 1e9, 2)


def main():
    utan = "--utan" in sys.argv
    collect = gc.collect
    if utan:
        gc.collect = lambda *a, **k: 0
    from fastapi.testclient import TestClient
    from api.main import app
    from scripts.download_open_scans import local_path
    c = TestClient(app, base_url="http://localhost")
    rows = []
    for series, stem in FILES:
        meta = json.load(open(f"/Volumes/2TB/cache/runmodell/djup/{series}/{stem}.json", encoding="utf-8"))
        with open(local_path(series, meta["file"]), "rb") as fh:
            c.post("/api/3d/upload", files={"file": (meta["file"], fh, "application/octet-stream")}).raise_for_status()
        n, gb = alive()
        rows.append({"efter": stem, "levande_modeller": n, "gb_punkter_trianglar": gb})
        print(rows[-1], flush=True)
    gc.collect = collect
    json.dump(rows, open(os.path.join(os.path.dirname(__file__), f"levande_{'utan' if utan else 'med'}.json"), "w"),
              ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
