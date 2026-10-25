"""Studie 1b, steg 1: varje mätt tvärsnitt (A-data) på de stenar där Viktor har granskat runslingorna klassas med
slingorna som facit, inte med den automatiska streckklassningen:
  runa       – inne i slingan, spåret går tvärs eller snett över slingan (stavar och bistavar)
  slingkant  – inne i slingan, spåret går längs slingan (slingans kantlinjer)
  utanför    – tydligt utanför slingan (ornamentik, ramar, kors, sprickor)
  gräns      – strax utanför slingan och inte längs den (runspetsar, korsningar): räknas inte i någon grupp
Slingans kantlinjer ligger ofta strax utanför det ritade bandet, så en kantzon på EDGE gånger halva höjden räknas till
slingan för spår som går längs den.
Snittets läge på djupbilden: projektionen på skanningens plan (u, v) minus det minsta projicerade värdet över skanningen
(a0, b0), som src/auto_grooves.Heightfield; a0 och b0 räknas här en gång per fil och sparas i djupbildens metadata.
    PYTHONPATH=. .venv/bin/python utdata/forskningsplan/s1b_klassning.py"""
import glob
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
from scripts.batch_scans import result_path  # noqa: E402
from scripts.download_open_scans import local_path  # noqa: E402
from src import runmodell as rm  # noqa: E402
from src.auto_grooves import basis  # noqa: E402

ALONG_DEG = 25.0  # a groove within this angle of the band's direction runs along it (a band line)
EDGE = 1.35  # the band's edge zone, as a multiple of half the band height
OUT = os.path.join(HERE, "s1b_klassning")


def grid_origin(series: str, meta: dict) -> tuple[float, float]:
    """a0, b0 of the depth grid (cached in the depth image's metadata)."""
    if "a0" in meta:
        return meta["a0"], meta["b0"]
    import trimesh
    mesh = trimesh.load(local_path(series, meta["file"]), process=False)
    mesh.apply_translation(-mesh.bounds.mean(axis=0))
    u, v, _ = basis(meta["normal"], meta.get("up"))
    pts = np.vstack([mesh.vertices, mesh.triangles_center])
    a, b = pts @ u, pts @ v
    meta["a0"], meta["b0"] = float(a.min()), float(b.min())
    nx = int((a.max() - meta["a0"]) / meta["res_mm"]) + 1
    ny = int((b.max() - meta["b0"]) / meta["res_mm"]) + 1
    assert [ny, nx] == meta["shape"], (meta["file"], [ny, nx], meta["shape"])  # the same grid as the depth image
    return meta["a0"], meta["b0"]


def seg_dist(P, A, B):
    """Distance from points P to segment AB, and the parameter t of the nearest point."""
    AB = B - A
    t = np.clip(((P - A) @ AB) / max(AB @ AB, 1e-9), 0, 1)
    return np.linalg.norm(P - (A + t[:, None] * AB), axis=1), t


def classify(series: str, stem: str) -> dict | None:
    band = rm.load_bands(series, stem)
    if not band or band.get("status") != "granskad" or not band.get("bands"):
        return None
    mpath = os.path.join(rm.DEPTH_DIR, series, stem + ".json")
    meta = json.load(open(mpath, encoding="utf-8"))
    files = json.load(open(os.path.join(ROOT, "data", "scan_files.json"), encoding="utf-8"))["datasets"][series]["files"]
    f = next(x for x in files if x["name"] == meta["file"])
    a_path = result_path(series, f).replace("automatisk_korning", "automatisk_korning_alla")
    if not os.path.exists(a_path):
        return None
    A = json.load(open(a_path, encoding="utf-8"))
    if "error" in A:
        return None
    had = "a0" in meta
    a0, b0 = grid_origin(series, meta)
    if not had:
        json.dump(meta, open(mpath, "w", encoding="utf-8"), ensure_ascii=False)
    u, v, _ = basis(meta["normal"], meta.get("up"))
    res, H, scale = meta["res_mm"], meta["shape"][0], band.get("scale", 2)
    sl = [s for s in A["slices"] if s.get("point") and s.get("direction")]
    P = np.array([s["point"] for s in sl]); D = np.array([s["direction"] for s in sl])
    ix = (P @ u - a0) / res; iy = (P @ v - b0) / res
    disp = np.c_[ix / scale, (H - 1 - iy) / scale]          # the drawing page's pixels (row 0 at the top)
    ddir = np.c_[D @ u, -(D @ v)]                             # the groove's direction on the page (y downwards)
    ddir /= np.maximum(np.linalg.norm(ddir, axis=1, keepdims=True), 1e-9)
    best_d = np.full(len(sl), np.inf); best_t = np.zeros((len(sl), 2)); best_h = np.zeros(len(sl))
    for b in band["bands"]:
        C = np.asarray(b["points"], float)
        for i in range(len(C) - 1):
            d, _ = seg_dist(disp, C[i], C[i + 1])
            tan = (C[i + 1] - C[i]) / max(np.linalg.norm(C[i + 1] - C[i]), 1e-9)
            better = d < best_d
            best_d[better] = d[better]; best_t[better] = tan; best_h[better] = b["height"] / 2
    inside = best_d <= best_h
    edge_zone = (best_d > best_h) & (best_d <= EDGE * best_h)
    cosang = np.abs(np.sum(ddir * best_t, axis=1))
    along = cosang >= np.cos(np.radians(ALONG_DEG))
    cls = np.where(inside & ~along, "runa", np.where((inside | edge_zone) & along, "slingkant",
                   np.where(edge_zone, "gräns", "utanför")))
    for s, c in zip(sl, cls):
        s["klass"] = str(c)
    counts = {k: int(np.sum(cls == k)) for k in ("runa", "slingkant", "gräns", "utanför")}
    out = {"series": series, "stem": stem, "signum": meta.get("signum"), "file": meta["file"], "object": meta.get("object"),
           "counts": counts, "old_feature_vs_new": {}, "slices": sl}
    for old in ("rune", "ornament", "isolated", "irregular"):
        m = np.array([s.get("feature") == old for s in sl])
        out["old_feature_vs_new"][old] = {k: int(np.sum(m & (cls == k))) for k in counts}
    os.makedirs(os.path.join(OUT, series), exist_ok=True)
    json.dump(out, open(os.path.join(OUT, series, stem + ".json"), "w", encoding="utf-8"), ensure_ascii=False)
    return out


if __name__ == "__main__":
    tot = {}
    agree = {o: {"runa": 0, "slingkant": 0, "gräns": 0, "utanför": 0} for o in ("rune", "ornament")}
    n = 0
    for p in sorted(glob.glob(os.path.join(rm.BAND_DIR, "*", "*.json"))):
        series, stem = p.split(os.sep)[-2], os.path.basename(p)[:-5]
        r = classify(series, stem)
        if not r:
            continue
        n += 1
        for k, v in r["counts"].items():
            tot[k] = tot.get(k, 0) + v
        for old in agree:
            for k, v in r["old_feature_vs_new"][old].items():
                agree[old][k] += v
        print(f"{r['signum'] or r['file']:16} {r['counts']}", flush=True)
    print(f"\n{n} filer; snitt per klass {tot}")
    for old, d in agree.items():
        s = sum(d.values()) or 1
        print(f"gamla klassen {old:9}: " + ", ".join(f"{k} {v / s:.0%}" for k, v in d.items()))
