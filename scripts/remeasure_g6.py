"""Mäter om referensmätningarna av Kitzler Åhfeldts 37 öppna skanningar av Södermanlands runstenar med den aktuella
mätmetoden (groove-7: runslingorna avgör vad som är runor och delar upp runorna), med exakt samma normal som referensmätningarna med groove-5
(utdata/Rak/referenser_g5), så att bara metoden skiljer. Resultaten sparas i utdata/Rak/referenser_g<N>/ (N = metodens nummer) i samma form, och
en jämförelse sten för sten i jamforelse.json där.

En sten i taget genom analysmotorn (minnet räcker inte till fler); körningen kan avbrytas och fortsätta.
    .venv/bin/python -m scripts.remeasure_g6            # mäter det som saknas
    .venv/bin/python -m scripts.remeasure_g6 --jamfor   # bara jämförelsen
    .venv/bin/python -m scripts.remeasure_g6 --lokalt [--igen]  # i egna processer, utan analysmotorn (ingen storleksgräns)
"""
from __future__ import annotations

import json
import os
import statistics
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
from scripts import batch_scans  # noqa: E402
from scripts.batch_scans import files, known_normals, measure  # noqa: E402
from src.stats import METRICS  # noqa: E402

REF_G5 = os.path.join(ROOT, "utdata", "Rak", "referenser_g5")
from api.config import METHOD_VERSION as _MV  # noqa: E402
OUT = os.path.join(ROOT, "utdata", "Rak", "referenser_g" + _MV.split("-")[1])  # referenser_g7 for groove-7
API = os.environ.get("RUNFORSKNING_API", "http://localhost:8000")


def g5_by_file() -> dict[str, tuple[str, dict]]:
    out = {}
    for f in sorted(os.listdir(REF_G5)):
        if f.endswith(".json"):
            d = json.load(open(os.path.join(REF_G5, f), encoding="utf-8"))
            out[d["file"]] = (f, d)
    return out


def run():
    os.makedirs(os.path.join(OUT, "sodermanland"), exist_ok=True)
    batch_scans.OUT = OUT  # the review images go beside the new measurements, not over the automatic run's
    g5 = g5_by_file()
    normals = known_normals()
    todo = [(k, f, p) for k, f, p in files(["sodermanland"]) if f["name"] in g5]
    assert len(todo) == len(g5) == 37, (len(todo), len(g5))
    for i, (key, f, path) in enumerate(todo, 1):
        name, old = g5[f["name"]]
        dst = os.path.join(OUT, name)
        if os.path.exists(dst):
            continue
        assert normals.get(f["name"]) == old["parameters"]["normal"]
        d = measure(API, key, f, path, normals)
        d["review_png"] = d.get("review_png")
        json.dump(d, open(dst, "w", encoding="utf-8"), ensure_ascii=False)
        print(f"{i}/{len(todo)} {name}: {d.get('counts', {}).get('accepted')} snitt, "
              f"{(d.get('rune_summary') or {}).get('n_runes')} runor, {d.get('seconds')} s"
              + (f"  FEL {d['error']}" if "error" in d else ""), flush=True)


def compare():
    rows = []
    for f in sorted(os.listdir(REF_G5)):
        if not f.endswith(".json") or not os.path.exists(os.path.join(OUT, f)):
            continue
        a = json.load(open(os.path.join(REF_G5, f), encoding="utf-8"))
        b = json.load(open(os.path.join(OUT, f), encoding="utf-8"))
        if "error" in b:
            rows.append({"signum": a["signum"], "error": b["error"]})
            continue
        rows.append({"signum": a["signum"],
                     "method": [(a.get("provenance") or {}).get("method_version") or "groove-5",
                                (b.get("provenance") or {}).get("method_version")],
                     "slices": [len(a["slices"]), len(b["slices"])],
                     "runes": [(a.get("rune_summary") or {}).get("n_runes"), (b.get("rune_summary") or {}).get("n_runes")],
                     "means": {m: [a["means"][m], b["means"][m]] for m in METRICS}})
    ok = [r for r in rows if "error" not in r]
    summ = {"n": len(rows), "errors": [r["signum"] for r in rows if "error" in r],
            "median_slices": [statistics.median(r["slices"][0] for r in ok), statistics.median(r["slices"][1] for r in ok)] if ok else None,
            "median_abs_change": {m: statistics.median(abs(r["means"][m][1] - r["means"][m][0]) for r in ok) for m in METRICS} if ok else None,
            "median_change": {m: statistics.median(r["means"][m][1] - r["means"][m][0] for r in ok) for m in METRICS} if ok else None}
    json.dump({"summary": summ, "stones": rows}, open(os.path.join(OUT, "jamforelse.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(json.dumps(summ, ensure_ascii=False, indent=1))


def measure_local(g5_name: str):
    """One stone in this process (no upload limit): the same steps as /api/3d/auto_analyze with the protocol, the
    normal and up direction of the groove-5 reference, the mesh centred as on upload."""
    import base64
    import time

    import numpy as np
    import trimesh

    from api.config import METHOD_VERSION
    from api.routers.threed import _digests, provenance, tool_heuristic
    from scripts.download_open_scans import local_path
    from src import protocol as protocol_spec
    from src.auto_grooves import analyze_grooves
    from src.stats import summarize_by_rune, summarize_slices

    old = json.load(open(os.path.join(REF_G5, g5_name), encoding="utf-8"))
    path = local_path("sodermanland", old["file"])
    digest, md5, size = _digests(path)
    assert digest == old["sha256"], g5_name
    t0 = time.time()
    mesh = trimesh.load(path, force="mesh")
    centre = (mesh.bounds[0] + mesh.bounds[1]) / 2.0
    mesh.apply_translation(-centre)
    pp = protocol_spec.PARAMETERS
    prm = old["parameters"]
    r = analyze_grooves(mesh, prm["normal"], up=prm.get("up"), spacing_mm=pp["spacing_mm"], sensitivity=pp["sensitivity"],
                        max_halfwidth_mm=pp["max_halfwidth_mm"], resolution_mm=pp["resolution_mm"],
                        harmonize_mm=pp["harmonize_mm"] or None, runes_only=True, measure="runes", bands=True,
                        sha256=digest)
    acc = [x for x in r["slices"] if x["accepted"]]
    info = {"mock": False, "mesh_id": digest, "filename": old["file"], "sha256": digest, "md5": md5, "bytes": size,
            "vertices": int(len(mesh.vertices)), "faces": int(len(mesh.faces)),
            "extent_mm": [float(v) for v in mesh.extents], "centered_by": [float(v) for v in centre]}
    params = {"mode": "automatic", **r["parameters"], "meta_stone": "Okänd", "meta_weathering": "Okänd"}
    prov = provenance(info, params, "rune")
    prov["protocol"] = protocol_spec.compliance(r["parameters"], METHOD_VERSION)
    out = {"signum": old["signum"], "file": old["file"], "sha256": digest, "seconds": round(time.time() - t0),
           "parameters": r["parameters"], "counts": r["counts"], "bands": r.get("bands"), "provenance": prov,
           "protocol": prov["protocol"]}
    if acc:
        out["summary"] = summarize_slices(acc)
        out["rune_summary"] = summarize_by_rune(acc)
        out["means"] = {m: out["summary"][m]["mean"] for m in METRICS}
        out["tool_heuristic"] = tool_heuristic(float(np.mean([x["apex_vinkel_deg"] for x in acc])), "Okänd", "Okänd")
    else:
        out["error"] = "inga godkända snitt"
    out["slices"] = [{**{m: x[m] for m in METRICS}, "position_mm": x["position_mm"], "fit_r2": x.get("fit_r2"),
                      "rune_id": x.get("rune_id"), "feature": x.get("feature"), "stroke_id": x.get("stroke_id"),
                      "profile": x.get("profile"), "point": x.get("point"), "direction": x.get("direction"),
                      "up": x.get("up")} for x in acc]
    png = os.path.join(OUT, "sodermanland", os.path.splitext(g5_name)[0] + "_granskning.png")
    os.makedirs(os.path.dirname(png), exist_ok=True)
    open(png, "wb").write(base64.b64decode(r["image_base64"].split(",", 1)[1]))
    out["review_png"] = os.path.relpath(png, ROOT)
    json.dump(out, open(os.path.join(OUT, g5_name), "w", encoding="utf-8"), ensure_ascii=False)
    print(f"{g5_name}: {len(acc)} snitt, {(out.get('rune_summary') or {}).get('n_runes')} runor, {out['seconds']} s", flush=True)


def run_local(again: bool = False):
    import subprocess
    os.makedirs(OUT, exist_ok=True)
    for f in sorted(os.listdir(REF_G5)):
        if not f.endswith(".json") or (os.path.exists(os.path.join(OUT, f)) and not again):
            continue
        subprocess.run([sys.executable, "-m", "scripts.remeasure_g6", "--en", f], cwd=ROOT,
                       env={**os.environ, "PYTHONPATH": ROOT})


if __name__ == "__main__":
    if "--en" in sys.argv:
        measure_local(sys.argv[sys.argv.index("--en") + 1])
        sys.exit()
    if "--lokalt" in sys.argv:
        run_local(again="--igen" in sys.argv)
    elif "--jamfor" not in sys.argv:
        run()
    compare()
