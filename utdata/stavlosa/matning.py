"""Stavlöst läge: hur många av textens runor den automatiska analysen hittar, före och efter.

En fil per körning, i en egen process (minnet): normal, upp-riktning och SHA-256 tas från djupbildens metadata
(samma som protokollmätningen), så att de ritade slingorna gäller. Mått per fil:
  - text_runor: runorna i Rundatas translitterering (samma räkning som studie 0b, s0_stavlosa_filter.py);
  - runor_matta: runor med minst ett godkänt snitt (analysens egen runindelning, rune_id);
  - runsnitt: godkända snitt som räknas som runa;
  - slingor: varifrån slingorna kom.

  .venv/bin/python -m utdata.stavlosa.matning halsingland HS_14_0_40_runes_thin03 [--stavlost] [--utan-slingor]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
DEPTH = os.environ.get("RUNMODELL_DEPTH_DIR", "/Volumes/2TB/cache/runmodell/djup")
OUT = os.path.join(ROOT, "utdata", "stavlosa", "resultat")


def text_runes(translit: str) -> int:
    return len(re.findall(r"[a-zæøåþðîï§RAEIOUY]", re.sub(r"\[[^\]]*\]|\([^)]*\)", "", translit or ""), re.I))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("series")
    ap.add_argument("stem")
    ap.add_argument("--stavlost", action="store_true")
    ap.add_argument("--utan-slingor", action="store_true")
    a = ap.parse_args(argv)
    import trimesh
    from scripts.download_open_scans import local_path
    from src.auto_grooves import analyze_grooves
    from src import protocol as protocol_spec

    meta = json.load(open(os.path.join(DEPTH, a.series, a.stem + ".json"), encoding="utf-8"))
    path = local_path(a.series, meta["file"])
    if not path:
        raise SystemExit(f"skanningen saknas: {meta['file']}")
    t0 = time.time()
    mesh = trimesh.load(path, force="mesh")
    mesh.apply_translation(-(mesh.bounds[0] + mesh.bounds[1]) / 2.0)  # centred as the app does on upload (api/routers/threed.py)
    pp = protocol_spec.PARAMETERS
    kw = {"staveless": True} if a.stavlost else {}
    r = analyze_grooves(mesh, meta["normal"], up=meta.get("up"), spacing_mm=pp["spacing_mm"], sensitivity=pp["sensitivity"],
                        max_halfwidth_mm=pp["max_halfwidth_mm"], resolution_mm=pp["resolution_mm"],
                        harmonize_mm=pp["harmonize_mm"] or None, measure="runes", bands=not a.utan_slingor,
                        sha256=meta["sha256"], **kw)
    acc = [s for s in r["slices"] if s["accepted"]]
    out = {"series": a.series, "stem": a.stem, "signum": meta.get("signum"), "rune_types": meta.get("rune_types"),
           "staveless": a.stavlost, "bands_used": not a.utan_slingor, "text_runor": text_runes(meta.get("transliteration")),
           "runor_matta": len({s["rune_id"] for s in acc if "rune_id" in s}),
           "runsnitt": sum(1 for s in acc if s.get("feature") == "rune"), "godkanda": len(acc),
           "runor_hittade": r["counts"]["runes_identified"], "slingor": r["bands"], "counts": r["counts"],
           "parametrar": {k: r["parameters"].get(k) for k in ("staveless", "staveless_gap_mm", "band_height_mm")},
           "seconds": round(time.time() - t0)}
    os.makedirs(OUT, exist_ok=True)
    tag = ("stavlost" if a.stavlost else "vanligt") + ("_utan" if a.utan_slingor else "")
    json.dump(out, open(os.path.join(OUT, f"{a.stem}__{tag}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: out[k] for k in ("signum", "staveless", "text_runor", "runor_hittade", "runor_matta", "runsnitt",
                                          "godkanda", "seconds")}, ensure_ascii=False), out["slingor"])


if __name__ == "__main__":
    main()
