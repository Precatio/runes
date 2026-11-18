"""Kullarna: storhögarna mot husbyar och tunaorter (H1), kultplatser (H2) och runstenar (H3). Låst plan
analysplaner/2026-11-18-hogarna.md (sha256 089fcfb5). Läser högarna ur
/Volumes/2TB/Antigrvity/Runes/downloads/hogar/hogar.csv.
    .venv/bin/python utdata/hogar/analys.py"""
import collections
import csv
import hashlib
import json
import math
import os
import random
import re
import sys

import numpy as np
from pyproj import Transformer
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "utdata", "asatro"))
import analys as asatro  # noqa: E402
from src import nordic  # noqa: E402

PLAN = os.path.join(ROOT, "analysplaner", "2026-11-18-hogarna.md")
SHA = hashlib.sha256(open(PLAN, "rb").read()).hexdigest()
assert SHA.startswith("089fcfb5"), SHA
SEED = int(SHA[:8], 16)
REPS = 10000
SAMI = {"Áhkká", "Nammásj", "Unna Sájvva", "Tarradalen"}
NOTES = ["Diametern läses som 'N m diam' eller 'N m i diam' (registret skriver oftast det senare; planens exempel nämnde "
         "bara den första formen). Rättat innan något prov räknades."]
DIAM = re.compile(r"(\d+(?:[.,]\d+)?)\s*m\s*(?:i\s*)?diam", re.I)
TR = Transformer.from_crs("EPSG:4326", "EPSG:3006", always_xy=True)


def xy(lat, lon):
    return TR.transform(lon, lat)


def main():
    H = list(csv.DictReader(open("/Volumes/2TB/Antigrvity/Runes/downloads/hogar/hogar.csv", encoding="utf-8")))
    assert len(H) == 17531
    # province: the nearest ISOF parish centroid
    P = asatro.parishes()
    pc, pland = [], []
    for land, ps in P.items():
        for p in ps:
            pc.append(xy(p["latitude"], p["longitude"]))
            pland.append(land)
    ptree = cKDTree(np.array(pc))
    mounds = []
    for r in H:
        m = DIAM.search(re.sub(r"\s+", " ", r["beskrivning"] or ""))
        d = float(m.group(1).replace(",", ".")) if m else None
        x, y = float(r["x"]), float(r["y"])
        mounds.append({"x": x, "y": y, "diam": d, "lan": r["lan"], "socken": r["socken"],
                       "land": pland[ptree.query([x, y])[1]]})
    # the reference layers
    central = [xy(float(r["lat"]), float(r["lon"])) for r in csv.DictReader(open(os.path.join(ROOT, "data", "ortnamn", "kultnamn.csv"), encoding="utf-8")) if r["tier"] == "C"]
    t1 = json.load(open(os.path.join(ROOT, "utdata", "asatro", "resultat_tillagg1.json"), encoding="utf-8"))
    cult = list({tuple(x["pt"]) for x in t1["namn"] if x["kategori"] == "kultplats" and x.get("pt") and x["namn"] not in SAMI})
    cult = [xy(a, b) for a, b in cult]
    D = json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["inscriptions"]
    rs = [xy(r["lat"], r["lon"]) for r in D if nordic.is_runestone(r) and nordic.land_of(r) == "sverige" and r.get("lat")]
    ct, kt, rt = cKDTree(np.array(central)), cKDTree(np.array(cult)), cKDTree(np.array(rs))
    for m in mounds:
        m["d_central"] = ct.query([m["x"], m["y"]])[0]
        m["d_cult"] = kt.query([m["x"], m["y"]])[0]
        m["rune500"] = int(len(rt.query_ball_point([m["x"], m["y"]], 500)) > 0)
    # halves: within each county, parishes alternately A/B in name order
    half = {}
    for lan in {m["lan"] for m in mounds}:
        for i, s in enumerate(sorted({m["socken"] for m in mounds if m["lan"] == lan})):
            half[(lan, s)] = "A" if i % 2 == 0 else "B"
    for m in mounds:
        m["half"] = half[(m["lan"], m["socken"])]
    sized = [m for m in mounds if m["diam"] is not None]
    res = {"sha": SHA[:8], "noter": NOTES, "hogar": len(mounds), "med_diameter": len(sized),
           "stora_20": sum(m["diam"] >= 20 for m in sized), "stora_30": sum(m["diam"] >= 30 for m in sized),
           "diam_median": float(np.median([m["diam"] for m in sized])),
           "per_landskap": dict(collections.Counter(m["land"] for m in mounds).most_common()),
           "stora_per_landskap": dict(collections.Counter(m["land"] for m in sized if m["diam"] >= 20).most_common())}

    def stats(rows, big):
        """(H1 mean log distance big − small, H2 same for cult, H3 MH log odds ratio for a runestone within 500 m)."""
        out = []
        for key in ("d_central", "d_cult"):
            b = [math.log(max(r[key], 1)) for r, g in zip(rows, big) if g]
            s = [math.log(max(r[key], 1)) for r, g in zip(rows, big) if not g]
            out.append(sum(b) / len(b) - sum(s) / len(s) if b and s else float("nan"))
        st = collections.defaultdict(lambda: [0, 0, 0, 0])
        for r, g in zip(rows, big):
            i = (0 if r["rune500"] else 1) if g else (2 if r["rune500"] else 3)
            st[r["land"]][i] += 1
        num = den = 0.0
        for a, b_, c, d in st.values():
            n = a + b_ + c + d
            if a + b_ and c + d:
                num += a * d / n
                den += b_ * c / n
        out.append(math.log(num / den) if num > 0 and den > 0 else float("nan"))
        return out

    def run(rows, thr, reps):
        big = [r["diam"] >= thr for r in rows]
        obs = stats(rows, big)
        by = collections.defaultdict(list)
        for i, r in enumerate(rows):
            by[r["land"]].append(i)
        rng = random.Random(SEED)
        ge = [0, 0, 0]
        for _ in range(reps):
            perm = big[:]
            for idx in by.values():
                v = [big[i] for i in idx]
                rng.shuffle(v)
                for i, val in zip(idx, v):
                    perm[i] = val
            s = stats(rows, perm)
            for k in range(3):
                ge[k] += abs(s[k]) >= abs(obs[k]) - 1e-12
        return {"stora": sum(big), "mindre": len(big) - sum(big), "stat": obs,
                "p": [(g + 1) / (reps + 1) for g in ge]}

    main_r = run(sized, 20, REPS)
    ps = main_r["p"]
    order = sorted(range(3), key=lambda i: ps[i])
    adj, run_ = [0.0] * 3, 0.0
    for rank, i in enumerate(order):
        run_ = max(run_, min(1.0, (3 - rank) * ps[i]))
        adj[i] = run_
    main_r["p_holm"] = adj
    halves = {h: run([m for m in sized if m["half"] == h], 20, 2000) for h in "AB"}
    alt = {t: run(sized, t, 2000) for t in (15, 30)}
    names = ["H1_husby_tuna", "H2_kultplats", "H3_runsten"]
    res["prov"] = {}
    for k, nm in enumerate(names):
        d0 = math.copysign(1, main_r["stat"][k])
        ok_h = all((math.copysign(1, halves[h]["stat"][k]) == d0) and (halves[h]["p"][k] < 0.05 or halves[h]["stora"] < 50)
                   for h in "AB")
        ok_t = all(math.copysign(1, alt[t]["stat"][k]) == d0 for t in (15, 30))
        res["prov"][nm] = {"stat": main_r["stat"][k], "p": ps[k], "p_holm": adj[k],
                           "halvor": {h: {"stat": halves[h]["stat"][k], "p": halves[h]["p"][k], "stora": halves[h]["stora"]} for h in "AB"},
                           "troskel_15_30": {t: alt[t]["stat"][k] for t in (15, 30)},
                           "haller": bool(adj[k] < 0.05 and ok_h and ok_t)}
    res["stora"], res["mindre"] = main_r["stora"], main_r["mindre"]
    # plain-language helpers: medians and shares
    big = [m for m in sized if m["diam"] >= 20]
    small = [m for m in sized if m["diam"] < 20]
    res["klartext"] = {"median_km_central": [float(np.median([m["d_central"] for m in g])) / 1000 for g in (big, small)],
                       "median_km_cult": [float(np.median([m["d_cult"] for m in g])) / 1000 for g in (big, small)],
                       "andel_runsten_500m": [float(np.mean([m["rune500"] for m in g])) for g in (big, small)]}
    json.dump(res, open(os.path.join(HERE, "resultat.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in res.items() if k not in ("per_landskap",)}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
