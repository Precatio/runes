"""Studie 1b enligt analysplaner/2026-10-25-studie1b.md (låst, SHA-256 9ea218c7…): runor mot ornamentik inom varje
objekt, med Viktors granskade runslingor som facit (s1b_klassning.py).
    PYTHONPATH=. .venv/bin/python utdata/forskningsplan/s1b_analys.py > utdata/forskningsplan/s1b_analys.txt"""
import glob
import json
import os
import sys
import tempfile

import numpy as np
from scipy.stats import wilcoxon

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))
import s1b_klassning as K  # noqa: E402
import s_analys as sa  # noqa: E402
from src import runmodell as rm  # noqa: E402

RAA = {"sodermanland", "asmund", "vastergotland", "gravmonument_og_sm"}


def classified(edge=1.35, along=25.0) -> list[dict]:
    """All checked files classified with the given edge zone and angle (the plan's values by default)."""
    K.EDGE, K.ALONG_DEG = edge, along
    K.OUT = tempfile.mkdtemp(prefix="s1b_")
    out = []
    for p in sorted(glob.glob(os.path.join(rm.BAND_DIR, "*", "*.json"))):
        r = K.classify(p.split(os.sep)[-2], os.path.basename(p)[:-5])
        if r:
            out.append(r)
    return out


def objects(files: list[dict], orn_all=False) -> list[dict]:
    """Δ per object (files grouped by signum): median(runes) − median(ornament) for the four main measures."""
    by = {}
    for r in files:
        by.setdefault(r["signum"] or r["file"], []).append(r)
    rows = []
    for key, rs in by.items():
        d0 = {"signum": rs[0]["signum"], "series": rs[0]["series"], "file": rs[0]["file"]}
        t = sa.object_type(d0)
        if not t:
            continue
        sl = [s for r in rs for s in r["slices"]]
        runes = [s for s in sl if s["klass"] == "runa"]
        orn = [s for s in sl if s["klass"] == "utanför" and (orn_all or s.get("feature") == "ornament")]
        irr = [s for s in sl if s["klass"] == "utanför" and s.get("feature") == "irregular"]
        row = {"objekt": key, "typ": t, "bergart": sa.rock(d0), "serie": rs[0]["series"], "n_runa": len(runes), "n_orn": len(orn)}
        if len(runes) < 10 or len(orn) < 10:
            row["bort"] = "färre än 10 snitt i runor eller ornamentik"
            rows.append(row)
            continue
        for m in sa.MAIN:
            row[m] = float(np.median([s[m] for s in runes])) - float(np.median([s[m] for s in orn]))
            if len(irr) >= 10:
                row["irr_" + m] = float(np.median([s[m] for s in runes])) - float(np.median([s[m] for s in irr]))
        rows.append(row)
    return rows


def test(rows, label):
    g = [r for r in rows if r["typ"] == "gravmonument" and "bort" not in r]
    s_ = [r for r in rows if r["typ"] == "runsten" and "bort" not in r]
    print(f"\n{label}: {len(g)} gravmonument mot {len(s_)} runstenar")
    if len(g) < 8 or len(s_) < 8:
        print("   för få för test (kräver 8 + 8)")
        return None
    res = {}
    for m in sa.MAIN:
        a, b = [r[m] for r in g], [r[m] for r in s_]
        obs, p = sa.perm_test(a, b)
        lo, hi = sa.boot_ci(a, b)
        res[m] = {"skillnad": obs, "p": p, "ci90": [lo, hi], "median_grav": float(np.median(a)), "median_runsten": float(np.median(b)),
                  "n": [len(a), len(b)]}
    for m, q in zip(sa.MAIN[1:], sa.bh([res[m]["p"] for m in sa.MAIN[1:]])):
        res[m]["q"] = q
    v = res[sa.MAIN[0]]
    res["utfall"] = ("mönstret skiljer sig" if v["p"] < 0.05 else
                     "samma mönster" if -5 <= v["ci90"][0] and v["ci90"][1] <= 5 else "obestämt")
    for m in sa.MAIN:
        x = res[m]
        print(f"   {m:16} median-Δ grav {x['median_grav']:+.2f}, runsten {x['median_runsten']:+.2f}; skillnad {x['skillnad']:+.2f}, "
              f"90 % KI [{x['ci90'][0]:+.2f}, {x['ci90'][1]:+.2f}], p {x['p']:.4f}" + (f", q {x['q']:.4f}" if "q" in x else "  ← huvudtest"))
    print(f"   utfall (V-vinkel): {res['utfall']}")
    return res


if __name__ == "__main__":
    out = {}
    base = classified()
    rows = objects(base)
    out["bortfall"] = [{k: r[k] for k in ("objekt", "typ", "bort")} for r in rows if "bort" in r]
    print("bortfall:", out["bortfall"])
    out["huvud"] = test(rows, "Huvudtest")
    out["objekt"] = [r for r in rows if "bort" not in r]
    out["robust_alla_utanför"] = test(objects(base, orn_all=True), "Robusthet (i) ornamentik = alla snitt utanför")
    for e in (1.2, 1.5):
        out[f"robust_kant_{e}"] = test(objects(classified(edge=e)), f"Robusthet (ii) kantzon {e}")
    for ang in (20.0, 30.0):
        out[f"robust_vinkel_{ang:g}"] = test(objects(classified(along=ang)), f"Robusthet (iii) gränsvinkel {ang:g}°")
    out["robust_mjuk"] = test([r for r in rows if r["typ"] == "gravmonument" or r["bergart"] in ("sandsten", "kalksten")],
                              "Robusthet (iv) bara runstenar i sandsten/kalksten")
    out["robust_raa"] = test([r for r in rows if r["serie"] in RAA], "Robusthet (v) bara Riksantikvarieämbetets serier")
    print("\nKänslighetskontroll: runor mot oregelbundna spår utanför slingorna")
    out["kanslighet"] = {}
    for m in sa.MAIN:
        d = [r["irr_" + m] for r in rows if "irr_" + m in r]
        if len(d) >= 8:
            out["kanslighet"][m] = {"median": float(np.median(d)), "p": float(wilcoxon(d).pvalue), "n": len(d)}
            print(f"   {m:16} median {np.median(d):+.2f}, Wilcoxon p {wilcoxon(d).pvalue:.1e}, {len(d)} objekt")
    json.dump(out, open(os.path.join(HERE, "s1b_analys.json"), "w"), ensure_ascii=False, indent=1)
