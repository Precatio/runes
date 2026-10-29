"""De möjliga okända ristarnas grupper (r/anonymous.R) mot SRI:s och Källströms attribueringar (data/carver_literature.json):
hamnar två stenar som litteraturen knyter till samme ristare i samma grupp oftare än grannar på samma avstånd?
Beskrivande kontroll 2026-10-29 (efter frågan om artikeln stod på säker grund); inget låst test.
    .venv/bin/python utdata/okanda_ristare/sri_par.py      Skriver sri_par.json."""
import csv
import json
import math
import os

import numpy as np
from pyproj import Transformer

OUT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(OUT, "..", ".."))
FP = "3f58e9339191761e"
a = json.load(open(os.path.join(ROOT, "data", "cache", "r", "corpus", FP, "anonymous.json"), encoding="utf-8"))
grp = {s: g["id"] for g in a["groups"] for s in g["stones"]}
C = {r["signum"]: r for r in csv.DictReader(open(os.path.join(ROOT, "data", "cache", "r", "corpus", FP, "corpus.csv"), encoding="utf-8"))}
T = Transformer.from_crs(4326, 3006, always_xy=True)


def xy(s):
    x, y = T.transform(float(C[s]["lon"]), float(C[s]["lat"]))
    return x / 1000, y / 1000


pool = [s for s, r in C.items() if r["lat"] and not r["carver"] and r["has_carver"] == "0" and int(r["n_words"] or 0) >= 5]
P = np.array([xy(s) for s in pool])
prov = np.array([C[s]["province"] for s in pool])
g = np.array([grp.get(s, -1) for s in pool])
lit = json.load(open(os.path.join(ROOT, "data", "carver_literature.json"), encoding="utf-8"))
pairs = []
for at in lit["attributions"]:
    st = at["stones"] + at.get("outside", [])
    for i in range(len(st)):
        for j in range(i + 1, len(st)):
            pairs.append((st[i], st[j], at["source"]))
rows = []
for x, y, src in pairs:
    if x not in pool or y not in pool:
        rows.append({"a": x, "b": y, "source": src, "tested": False})
        continue
    d = math.dist(xy(x), xy(y))
    i = pool.index(x)
    dist = np.hypot(*(P - P[i]).T)
    m = (dist <= max(d, 2)) & (dist > 0) & (prov == prov[i])
    rows.append({"a": x, "b": y, "source": src, "tested": True, "km": round(d, 1),
                 "same_group": grp.get(x, -1) == grp.get(y, -2) and x in grp,
                 "neighbours_same_group": float((g[m] == grp.get(x, -9)).mean()) if m.sum() else None, "n_neighbours": int(m.sum())})
t = [r for r in rows if r["tested"]]
out = {"n_pairs": len(t), "same_group": sum(r["same_group"] for r in t),
       "expected_from_neighbours": round(sum(r["neighbours_same_group"] or 0 for r in t), 2),
       "merged_signed_carvers": [["Vg 181", "Vg 130"]] if grp.get("Vg 181") == grp.get("Vg 130") else [], "pairs": rows}
json.dump(out, open(os.path.join(OUT, "sri_par.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print({k: out[k] for k in ("n_pairs", "same_group", "expected_from_neighbours", "merged_signed_carvers")})
