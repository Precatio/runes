"""Studie 1, efterhandskontroll (inte i den låsta planen, tillagd efter att figuren visat att runstavar i slingan på
Vg 50 klassats som långa linjer): bara linjesnitt som ligger minst D mm från varje runsnitt räknas som linjer, så att
felklassade stavar inne i slingan inte blandas in. Samma test som huvudtestet."""
import os, sys
import numpy as np
from scipy.spatial import cKDTree
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))
import s_analys as sa  # noqa: E402
import json  # noqa: E402
A = sa.load("automatisk_korning_alla")
out = {}
for D in (10, 20):
    rows = []
    for key, ds in sa.objects(A).items():
        t = sa.object_type(ds[0])
        if not t:
            continue
        sl = [s for d in ds for s in d["slices"] if s.get("point")]
        runes = [s for s in sl if s.get("feature") == "rune"]
        if len(runes) < 10:
            continue
        tree = cKDTree(np.array([s["point"] for s in runes]))
        orn = [s for s in sl if s.get("feature") == "ornament" and tree.query(s["point"])[0] >= D]
        if len(orn) < 10:
            continue
        r = {"typ": t, "kept": len(orn)}
        for m in sa.MAIN:
            r[m] = float(np.median([s[m] for s in runes])) - float(np.median([s[m] for s in orn]))
        rows.append(r)
    g = [r for r in rows if r["typ"] == "gravmonument"]; s_ = [r for r in rows if r["typ"] == "runsten"]
    res = {"n": [len(g), len(s_)]}
    for m in sa.MAIN:
        obs, p = sa.perm_test([r[m] for r in g], [r[m] for r in s_])
        lo, hi = sa.boot_ci([r[m] for r in g], [r[m] for r in s_])
        res[m] = {"skillnad": obs, "p": p, "ci90": [lo, hi], "median_grav": float(np.median([r[m] for r in g])),
                  "median_runsten": float(np.median([r[m] for r in s_]))}
    v = res["apex_vinkel_deg"]
    res["utfall"] = "mönstret skiljer sig" if v["p"] < 0.05 else ("samma mönster" if -5 <= v["ci90"][0] and v["ci90"][1] <= 5 else "obestämt")
    out[D] = res
    print(f"Avstånd ≥ {D} mm: {len(g)} gravmonument, {len(s_)} runstenar")
    for m in sa.MAIN:
        x = res[m]
        print(f"   {m:16} Δ grav {x['median_grav']:+.2f}, runsten {x['median_runsten']:+.2f}; skillnad {x['skillnad']:+.2f} "
              f"KI [{x['ci90'][0]:+.2f}, {x['ci90'][1]:+.2f}] p {x['p']:.3f}")
    print("   utfall:", res["utfall"])
json.dump(out, open(os.path.join(HERE, "s1_efterhand.json"), "w"), indent=1)
