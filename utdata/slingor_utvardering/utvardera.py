"""Hur väl hittar slingmodellen runorna på en sten den aldrig sett? Utvärdering av groove-6 på de 24 granskade stenar som
slingmodellen (data/runmodell/slingmodell.pt) INTE tränades på (samma uppdelning som scripts/runmodell_slingor_train.py:
en fjärdedel per serie, seed 1).

Varje sten mäts två gånger med protokollet, bara runor: med Viktors ritade slingor (facit) och med modellens egna slingor
(de ritade döljs). Mått per sten och samlat:
  - precision: andelen av modellkörningens runsnitt som också är runsnitt med de ritade slingorna (samma punkt inom 3 mm);
  - täckning (recall): andelen av de ritade slingornas runsnitt som modellkörningen också hittar;
  - hur mycket stenens medelvärden (vinkel, djup, bredd …) ändras när modellens slingor används i stället för de ritade.

En körning per sten och läge i en egen process (minnet), centrerad som appen gör vid uppladdning.
    .venv/bin/python -m utdata.slingor_utvardering.utvardera lista            # visar de 24 stenarna
    .venv/bin/python -m utdata.slingor_utvardering.utvardera mat SERIE STEM ritade|modellen
    .venv/bin/python -m utdata.slingor_utvardering.utvardera alla            # mäter det som saknas, en process per körning
    .venv/bin/python -m utdata.slingor_utvardering.utvardera jamfor          # resultat.json
"""
from __future__ import annotations

import json
import os
import random
import statistics
import subprocess
import sys
import time

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "korningar")
DEPTH = os.environ.get("RUNMODELL_DEPTH_DIR", "/Volumes/2TB/cache/runmodell/djup")
SLINGOR = "/Volumes/2TB/cache/runmodell/slingor"
MATCH_MM = 3.0


def held_out() -> list[tuple[str, str]]:
    """The 24 stones the band model was not trained on: the training script's split (share 0.25 per series, seed 1)."""
    names = sorted(os.path.basename(f)[:-4] for f in os.listdir(SLINGOR) if f.endswith(".npz"))
    data = [{"name": n, "series": n.split("__")[0]} for n in names]
    rng = random.Random(1)
    test = []
    for s in sorted({d["series"] for d in data}):
        g = sorted([d for d in data if d["series"] == s], key=lambda d: d["name"])
        rng.shuffle(g)
        test += g[:round(len(g) * 0.25)]
    return [(d["series"], d["name"].split("__", 1)[1]) for d in test]


def measure(series: str, stem: str, mode: str):
    import trimesh
    from scripts.download_open_scans import local_path
    from src import protocol as protocol_spec
    from src import rune_bands
    from src.auto_grooves import analyze_grooves
    from src.stats import METRICS

    if mode == "modellen":  # hide the drawn bands, so that the analysis falls back on the model's proposal
        rune_bands.drawn_labels = lambda sha256, hf: None
    meta = json.load(open(os.path.join(DEPTH, series, stem + ".json"), encoding="utf-8"))
    path = local_path(series, meta["file"])
    if not path:
        raise SystemExit(f"skanningen saknas: {meta['file']}")
    t0 = time.time()
    mesh = trimesh.load(path, force="mesh")
    mesh.apply_translation(-(mesh.bounds[0] + mesh.bounds[1]) / 2.0)  # centred as the app does on upload
    pp = protocol_spec.PARAMETERS
    r = analyze_grooves(mesh, meta["normal"], up=meta.get("up"), spacing_mm=pp["spacing_mm"], sensitivity=pp["sensitivity"],
                        max_halfwidth_mm=pp["max_halfwidth_mm"], resolution_mm=pp["resolution_mm"],
                        harmonize_mm=pp["harmonize_mm"] or None, measure="runes", bands=True, sha256=meta["sha256"])
    acc = [s for s in r["slices"] if s["accepted"]]
    out = {"series": series, "stem": stem, "signum": meta.get("signum"), "mode": mode, "bands": r.get("bands"),
           "counts": r["counts"], "seconds": round(time.time() - t0),
           "slices": [{"point": s.get("point"), "rune_id": s.get("rune_id"), **{m: s.get(m) for m in METRICS}} for s in acc]}
    os.makedirs(OUT, exist_ok=True)
    json.dump(out, open(os.path.join(OUT, f"{series}__{stem}__{mode}.json"), "w", encoding="utf-8"), ensure_ascii=False)
    print(series, stem, mode, len(acc), "snitt", r.get("bands"), out["seconds"], "s", flush=True)


def run_all():
    for series, stem in held_out():
        for mode in ("ritade", "modellen"):
            if os.path.exists(os.path.join(OUT, f"{series}__{stem}__{mode}.json")):
                continue
            subprocess.run([sys.executable, "-m", "utdata.slingor_utvardering.utvardera", "mat", series, stem, mode],
                           cwd=ROOT, env={**os.environ, "PYTHONPATH": ROOT})


def compare():
    from src.stats import METRICS
    rows = []
    for series, stem in held_out():
        f = {m: os.path.join(OUT, f"{series}__{stem}__{m}.json") for m in ("ritade", "modellen")}
        if not all(os.path.exists(p) for p in f.values()):
            continue
        a, b = (json.load(open(f[m], encoding="utf-8")) for m in ("ritade", "modellen"))
        pa = np.array([s["point"] for s in a["slices"] if s.get("point")], float).reshape(-1, 3)
        pb = np.array([s["point"] for s in b["slices"] if s.get("point")], float).reshape(-1, 3)

        def matched(x, y):
            if len(x) == 0 or len(y) == 0:
                return 0
            return int(sum(np.min(np.linalg.norm(y - p, axis=1)) <= MATCH_MM for p in x))
        mean = lambda d, m: statistics.fmean([s[m] for s in d["slices"] if s.get(m) is not None]) if d["slices"] else None  # noqa: E731
        rows.append({"series": series, "stem": stem, "signum": a.get("signum"),
                     "drawn_slices": len(pa), "model_slices": len(pb),
                     "precision": matched(pb, pa) / len(pb) if len(pb) else None,
                     "recall": matched(pa, pb) / len(pa) if len(pa) else None,
                     "model_source": (b.get("bands") or {}).get("source"),
                     "means": {m: [mean(a, m), mean(b, m)] for m in METRICS}})
    ok = [r for r in rows if r["precision"] is not None and r["recall"] is not None]
    med = lambda xs: statistics.median(xs) if xs else None  # noqa: E731
    summ = {"stones": len(rows), "scored": len(ok),
            "precision_median": med([r["precision"] for r in ok]), "recall_median": med([r["recall"] for r in ok]),
            "precision_pooled": (sum(r["precision"] * r["model_slices"] for r in ok) / max(1, sum(r["model_slices"] for r in ok))) if ok else None,
            "recall_pooled": (sum(r["recall"] * r["drawn_slices"] for r in ok) / max(1, sum(r["drawn_slices"] for r in ok))) if ok else None,
            "mean_abs_change_median": {m: med([abs(r["means"][m][1] - r["means"][m][0]) for r in ok
                                               if None not in r["means"][m]]) for m in METRICS}}
    json.dump({"summary": summ, "stones": rows}, open(os.path.join(HERE, "resultat.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(json.dumps(summ, ensure_ascii=False, indent=1))
    for r in rows:
        print(f"{r['series'][:12]:12} {r['stem'][:34]:34} ritade {r['drawn_slices']:4} modellen {r['model_slices']:4} "
              f"precision {r['precision'] if r['precision'] is None else round(r['precision'], 2)} "
              f"täckning {r['recall'] if r['recall'] is None else round(r['recall'], 2)}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "lista"
    if cmd == "lista":
        for s in held_out():
            print(*s)
    elif cmd == "mat":
        measure(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == "alla":
        run_all()
        compare()
    elif cmd == "jamfor":
        compare()
