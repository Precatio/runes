"""Hur träffsäker är runigenkänningen? Utvärdering mot handmärkta facit (METHODS.md, 1c steg 5).

Facit skapas i 3D-vyn i facit-läge: alla spår mäts, inget är förmärkt, och forskaren märker punkterna som runa,
ornamentik (slinglinje eller ornament) eller utesluten (spricka, vittring). Facitfilen innehåller bara positioner
och märkning, så samma facit kan användas när reglerna ändras: skriptet kör den automatiska analysen på nytt med
facitets parametrar, paras ihop varje facitpunkt med närmaste snitt (högst 2 mm) och jämför.

    .venv/bin/python -m scripts.evaluate_rune_detection facit/*.json --out utdata/rune_facit

Skanningen hittas via filnamnet i facitet (i skanningar/ eller projektroten) och kontrolleras mot dess SHA-256.
Utvecklingsstenar (de reglerna justerades på) redovisas för sig: --dev "Sö 113,Sö 128".
"""
import argparse
import hashlib
import json
import os

import numpy as np
from scipy.spatial import cKDTree

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MATCH_MM = 2.0


def find_scan(mesh: dict, folders=()) -> str:
    name = mesh.get("filename") or ""
    for folder in (*folders, os.path.join(ROOT, "skanningar"), ROOT):
        path = os.path.join(folder, name)
        if name and os.path.exists(path):
            return path
    raise FileNotFoundError(f"Skanningen {name!r} finns inte i skanningar/ eller projektroten.")


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_like_app(path: str):
    """Läser in skanningen som appen gör (api/routers/threed.py, _load_upload): facitets koordinater gäller den
    centrerade modellen."""
    import trimesh

    mesh = trimesh.load(path, force="mesh")
    mesh.apply_translation(-(mesh.bounds[0] + mesh.bounds[1]) / 2.0)
    return mesh


def evaluate(facit: dict, folders=()) -> dict:
    from src.auto_grooves import analyze_grooves

    path = find_scan(facit.get("mesh") or {}, folders)
    want = (facit.get("mesh") or {}).get("sha256")
    if want and sha256(path) != want:
        raise ValueError(f"{path}: kontrollsumman stämmer inte med facitet.")
    par = facit["parameters"]
    r = analyze_grooves(load_like_app(path), par["normal"], up=par.get("up"),
                        spacing_mm=par.get("spacing_mm", 3.0), sensitivity=par.get("sensitivity", 3.0),
                        max_halfwidth_mm=par.get("max_halfwidth_mm", 8.0),
                        resolution_mm=par["resolution_mm"] if par.get("fixed_resolution") else None,
                        harmonize_mm=par.get("harmonize_mm"), runes_only=False)
    slices = [s for s in r["slices"] if s["accepted"] and s.get("point")]
    tree = cKDTree(np.array([s["point"] for s in slices]))
    counts = {"tp": 0, "fp": 0, "fn": 0, "tn": 0, "unmatched": 0}
    by_label: dict[str, dict[str, int]] = {}
    for lab in facit["labels"]:
        if lab["label"] not in ("rune", "ornament", "excluded"):
            continue
        dist, j = tree.query(lab["point"])
        if dist > MATCH_MM:
            counts["unmatched"] += 1
            continue
        truth, pred = lab["label"] == "rune", slices[j].get("feature") == "rune"
        counts[{(True, True): "tp", (False, True): "fp", (True, False): "fn", (False, False): "tn"}[(truth, pred)]] += 1
        b = by_label.setdefault(lab["label"], {})
        feat = slices[j].get("feature") or "?"
        b[feat] = b.get(feat, 0) + 1
    return {"signum": facit.get("signum"), "labeller": facit.get("labeller"), **counts, **scores(counts),
            "by_label": by_label}


def scores(c: dict) -> dict:
    p = c["tp"] / (c["tp"] + c["fp"]) if c["tp"] + c["fp"] else None
    rec = c["tp"] / (c["tp"] + c["fn"]) if c["tp"] + c["fn"] else None
    f1 = 2 * p * rec / (p + rec) if p and rec else None
    return {"precision": p, "recall": rec, "f1": f1}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("facit", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--dev", default="Sö 113,Sö 128", help="stenar som reglerna justerades på (redovisas för sig)")
    ap.add_argument("--scans", action="append", default=[], help="fler mappar att leta efter skanningar i")
    a = ap.parse_args(argv)
    dev = {x.strip() for x in a.dev.split(",") if x.strip()}
    os.makedirs(a.out, exist_ok=True)
    rows = []
    for f in a.facit:
        res = evaluate(json.load(open(f)), a.scans)
        res["development"] = res["signum"] in dev
        rows.append(res)
        fmt = lambda v: "–" if v is None else f"{v:.2f}"  # noqa: E731
        print(f"{res['signum']:16s} precision {fmt(res['precision'])}  träffsäkerhet (recall) {fmt(res['recall'])}  "
              f"F1 {fmt(res['f1'])}  (tp {res['tp']}, fp {res['fp']}, fn {res['fn']}, tn {res['tn']}, "
              f"oparade {res['unmatched']}){'  [utvecklingssten]' if res['development'] else ''}")
    for name, group in (("Utvärderingsstenar", [r for r in rows if not r["development"]]),
                        ("Utvecklingsstenar", [r for r in rows if r["development"]])):
        if group:
            tot = {k: sum(r[k] for r in group) for k in ("tp", "fp", "fn", "tn")}
            s = scores(tot)
            print(f"{name} ({len(group)}): precision {s['precision'] or 0:.2f}, recall {s['recall'] or 0:.2f}, F1 {s['f1'] or 0:.2f}")
    json.dump(rows, open(os.path.join(a.out, "evaluation.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
