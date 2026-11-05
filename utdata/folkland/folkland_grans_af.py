"""EXPLORATIVT, utanför den låsta planen (2026-11-05): gränsprovet i steg 3 av analysplaner/2026-11-01-upplands-folkland.md
med grannregeln räknad på ALLA socknarnas punkter. folkland.py prövar grannskap på varannan sockenpunkt i varje land
(land_pts[::2], en gallring för tidens skull); med den rättade indelningen (Färingö tingslag i Attundaland, Adelsö i
Fjädrundaland) gränsar Attundaland och Fjädrundaland på Mälaröarna (Adelsö–Munsö), men gallringen missar det. Här samma
regel som i planen – paret med störst skillnad om de gränsar, annars de två grannar med störst skillnad; stenar vars socken
har en socken i det andra landet inom 10 km; Fishers exakta test ensidigt – med alla punkter. Planens eget steg 3 är det i
folkland.json; detta är en känslighetskontroll och redovisas så. Skriver folkland_grans_af.json.
    PYTHONPATH=. .venv/bin/python utdata/folkland/folkland_grans_af.py"""
import io
import json
import os
import sys
from contextlib import redirect_stdout
from itertools import combinations

from scipy.stats import fisher_exact

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
with redirect_stdout(io.StringIO()):
    import folkland as F  # noqa: E402  (the same rows, shares and halves as the locked analysis)

pts = F.land_pts
nb = {(a, b): any(F.km(p[0], p[1], q[0], q[1]) <= 10 for p in pts[a] for q in pts[b]) for a, b in combinations(F.LANDS, 2)}
held = [f for f, v in F.res["step2"].items() if v["holds"]]
out = {"note": "explorativt, utanför planen: steg 3 med grannskap på alla sockenpunkter",
       "neighbours_all_points": {f"{a}-{b}": v for (a, b), v in nb.items()},
       "neighbours_script": F.res["neighbours"], "tests": {}}


def border(r, other):
    return any(F.km(r["pp"][0], r["pp"][1], q[0], q[1]) <= 10 for q in pts[other])


def test(f, a, b):
    k = lambda xs: (sum(r[f] for r in xs), len(xs))  # noqa: E731
    ra = [r for r in F.rows if r["land"] == a and r[f] is not None]
    rb = [r for r in F.rows if r["land"] == b and r[f] is not None]
    (k1, n1), (k2, n2) = k([r for r in ra if border(r, b)]), k([r for r in rb if border(r, a)])
    p = float(fisher_exact([[k1, n1 - k1], [k2, n2 - k2]], alternative="greater")[1]) if n1 and n2 else None
    return {"high": a, "low": b, "border_high": [k1, n1], "border_low": [k2, n2],
            "inner_high": list(k([r for r in ra if not border(r, b)])), "inner_low": list(k([r for r in rb if not border(r, a)])),
            "p": p, "at_border": p is not None and p < 0.05}


for f in held:
    sh = {lnd: F.res["step1"][f]["shares"][lnd][0] / max(1, F.res["step1"][f]["shares"][lnd][1]) for lnd in F.LANDS}
    pairs = sorted(((a, b) for (a, b), v in nb.items() if v), key=lambda ab: -abs(sh[ab[0]] - sh[ab[1]]))
    a, b = pairs[0]
    if sh[a] < sh[b]:
        a, b = b, a
    out["tests"][f] = test(f, a, b)
json.dump(out, open(os.path.join(HERE, "folkland_grans_af.json"), "w"), ensure_ascii=False, indent=1)
print("grannar (alla punkter):", out["neighbours_all_points"])
for f, t in out["tests"].items():
    print(f, t)
