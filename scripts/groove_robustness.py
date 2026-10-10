"""Hur robust är den automatiska spåranalysen? Samma skanning mätt under ändrade förutsättningar (METHODS.md, 1e).

Varje sten mäts nio gånger: som standard (0,6 mm rutnät, känslighet 3), med rutnät 0,4 och 0,8 mm, med ytnormalen
lutad 5° åt två håll, med känslighet 2,5 och 3,5 och med skanningen förenklad till hälften och en fjärdedel av
trianglarna (som en glesare skanner). Sedan jämförs stenens medelvärden (runan som enhet), antalet runor, hur
många mätpunkter som återkommer och måtten på samma ställe.

    .venv/bin/python -m scripts.groove_robustness utdata/Rak/referenser_g4/Sö_128.json … --out utdata/groove_robustness

Det här är inte ett test–omtest med oberoende skanningar av samma sten; det visar hur känsliga resultaten är för
analysens egna val och för skanningens täthet.
"""
import argparse
import collections
import glob
import json
import math
import os
import time

import numpy as np
from scipy.spatial import cKDTree

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
METRICS = ["apex_vinkel_deg", "spårdjup_mm", "spårbredd_mm", "djup_bredd_kvot", "asymmetri_deg", "bottenradie_mm"]
CONDITIONS = ["res0.4", "res0.8", "tilt5_up", "tilt5_side", "sens2.5", "sens3.5", "dec50", "dec75"]


def _rot(v, axis, deg):
    axis = np.asarray(axis, float) / np.linalg.norm(axis)
    v = np.asarray(v, float)
    t = math.radians(deg)
    return v * math.cos(t) + np.cross(axis, v) * math.sin(t) + axis * np.dot(axis, v) * (1 - math.cos(t))


def measure(refs: list[str], out: str):
    import fast_simplification
    import trimesh

    from src.auto_grooves import analyze_grooves
    from src.stats import METRICS as ALL

    for ref in refs:
        d = json.load(open(ref))
        sig = d["signum"]
        path = next((p for p in (os.path.join(ROOT, "skanningar", d["file"]), os.path.join(ROOT, d["file"]))
                     if os.path.exists(p)), None)
        if path is None:
            print(f"{sig}: skanningen saknas, hoppar över")
            continue
        n0, up0 = np.array(d["parameters"]["normal"]), np.array(d["parameters"]["up"])
        conds = {"base": {}, "res0.4": {"resolution_mm": 0.4}, "res0.8": {"resolution_mm": 0.8},
                 "tilt5_up": {"normal": _rot(n0, up0, 5)}, "tilt5_side": {"normal": _rot(n0, np.cross(n0, up0), 5)},
                 "sens2.5": {"sensitivity": 2.5}, "sens3.5": {"sensitivity": 3.5},
                 "dec50": {"decimate": 0.5}, "dec75": {"decimate": 0.75}}
        mesh = None
        for name, c in conds.items():
            fn = os.path.join(out, f"{sig.replace(' ', '_')}__{name}.json")
            if os.path.exists(fn):
                continue
            mesh = mesh if mesh is not None else trimesh.load(path, process=False)
            t = time.time()
            m = mesh
            if "decimate" in c:
                v, f = fast_simplification.simplify(np.asarray(mesh.vertices, np.float32),
                                                    np.asarray(mesh.faces, np.int32), c["decimate"])
                m = trimesh.Trimesh(v, f, process=False)
            r = analyze_grooves(m, c.get("normal", n0), up=up0, resolution_mm=c.get("resolution_mm", 0.6),
                                sensitivity=c.get("sensitivity", 3))
            acc = [{**{k: s[k] for k in ALL}, "rune_id": s.get("rune_id"), "point": s["point"],
                    "direction": s["direction"]} for s in r["slices"] if s["accepted"]]
            json.dump({"signum": sig, "condition": name, "counts": r["counts"], "faces": len(m.faces), "slices": acc},
                      open(fn, "w"))
            print(sig, name, r["counts"]["runes_measured"], "runor,", len(acc), f"snitt, {time.time() - t:.0f} s", flush=True)


def rune_mean(d: dict, m: str) -> float:
    by = collections.defaultdict(list)
    for s in d["slices"]:
        if s.get("rune_id") is not None and np.isfinite(s[m]):
            by[s["rune_id"]].append(s[m])
    return float(np.mean([np.mean(v) for v in by.values()])) if by else float("nan")


def icc_agreement(X: np.ndarray) -> float:
    """ICC(A,1): tvåvägs, absolut överensstämmelse (stenar × villkor)."""
    n, k = X.shape
    g = X.mean()
    msr = k * ((X.mean(1) - g) ** 2).sum() / (n - 1)
    msc = n * ((X.mean(0) - g) ** 2).sum() / (k - 1)
    mse = ((X - X.mean(1, keepdims=True) - X.mean(0, keepdims=True) + g) ** 2).sum() / ((n - 1) * (k - 1))
    return float((msr - mse) / (msr + (k - 1) * mse + k * (msc - mse) / n))


def analyse(out: str, between: dict | None) -> dict:
    runs = collections.defaultdict(dict)
    for f in glob.glob(os.path.join(out, "*__*.json")):
        d = json.load(open(f))
        runs[d["signum"]][d["condition"]] = d
    stones = sorted(s for s in runs if all(c in runs[s] for c in ["base", *CONDITIONS]))
    res = {"stones": stones, "conditions": {}, "icc": {}}
    print(f"{len(stones)} stenar: {', '.join(stones)}")
    print("\nÄndring i stenens medelvärde mot standard: median |Δ| (största)")
    for c in CONDITIONS:
        row = {m: [abs(rune_mean(runs[s][c], m) - rune_mean(runs[s]["base"], m)) for s in stones] for m in METRICS}
        rd, ov, da, dz = [], [], [], []
        for s in stones:
            b, x = runs[s]["base"], runs[s][c]
            rd.append((x["counts"]["runes_measured"] - b["counts"]["runes_measured"]) / b["counts"]["runes_measured"])
            P = np.array([q["point"] for q in b["slices"]])
            Q = np.array([q["point"] for q in x["slices"]])
            dist, j = cKDTree(Q).query(P)
            ov.append(float(np.mean(dist < 3.0)))
            for i in np.where(dist < 1.5)[0]:
                if abs(np.dot(b["slices"][i]["direction"], x["slices"][j[i]]["direction"])) > math.cos(math.radians(20)):
                    da.append(x["slices"][j[i]]["apex_vinkel_deg"] - b["slices"][i]["apex_vinkel_deg"])
                    dz.append(x["slices"][j[i]]["spårdjup_mm"] - b["slices"][i]["spårdjup_mm"])
        res["conditions"][c] = {"stone_mean_abs_change": {m: [float(np.median(v)), float(np.max(v))] for m, v in row.items()},
                                "runes_change": float(np.median(rd)), "points_recurring": float(np.median(ov)),
                                "same_spot_abs_angle": float(np.median(np.abs(da))), "same_spot_abs_depth": float(np.median(np.abs(dz)))}
        r = res["conditions"][c]
        print(f"{c:11s} vinkel {r['stone_mean_abs_change']['apex_vinkel_deg'][0]:.1f}° ({r['stone_mean_abs_change']['apex_vinkel_deg'][1]:.1f})  "
              f"djup {r['stone_mean_abs_change']['spårdjup_mm'][0]:.2f} mm  runor {r['runes_change']:+.0%}  "
              f"återkommande punkter {r['points_recurring']:.0%}  samma ställe: {r['same_spot_abs_angle']:.1f}°, {r['same_spot_abs_depth']:.2f} mm")
    print("\nÖverensstämmelse för stenens medelvärde över alla nio villkor")
    for m in METRICS:
        X = np.array([[rune_mean(runs[s][c], m) for c in ["base", *CONDITIONS]] for s in stones])
        within = float(np.sqrt(np.mean(X.var(1, ddof=1))))
        b = (between or {}).get(m)
        res["icc"][m] = {"icc_a1": icc_agreement(X), "sd_over_conditions": within, "ratio_to_between_stones": within / b if b else None}
        print(f"{m:18s} ICC(A,1) {res['icc'][m]['icc_a1']:.2f}  SD över villkor {within:.3f}"
              + (f"  ({within / b:.0%} av SD mellan stenar)" if b else ""))
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("refs", nargs="*")
    ap.add_argument("--out", required=True)
    ap.add_argument("--between", default=os.path.join(ROOT, "utdata", "rune_sample_size", "summary.json"),
                    help="summary.json från scripts.rune_sample_size (SD mellan stenar)")
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    measure(a.refs, a.out)
    between = None
    if os.path.exists(a.between):
        between = {m: v["sd_between_stones"] for m, v in json.load(open(a.between))["components"].items()}
    json.dump(analyse(a.out, between), open(os.path.join(a.out, "summary.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
