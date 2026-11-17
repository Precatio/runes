"""Kultplatsernas landskap: dragen per ISOF-socken (låst plan analysplaner/2026-11-17-kultplatsernas-landskap.md,
sha256 55a61e0d). Skriver utdata/asatro/landskap_drag.csv; proven görs i landskap.R.
    .venv/bin/python utdata/asatro/landskap.py"""
import collections
import csv
import hashlib
import json
import math
import os
import sys

import numpy as np
from PIL import Image
from pyproj import Transformer

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import analys as main_plan  # noqa: E402

PLAN = os.path.join(ROOT, "analysplaner", "2026-11-17-kultplatsernas-landskap.md")
SHA = hashlib.sha256(open(PLAN, "rb").read()).hexdigest()
assert SHA.startswith("55a61e0d"), SHA
SAMI = {"Áhkká", "Nammásj", "Unna Sájvva", "Tarradalen"}
Image.MAX_IMAGE_PIXELS = None


def km(a, b):
    return main_plan.km(a, b)


def main():
    t1 = json.load(open(os.path.join(HERE, "resultat_tillagg1.json"), encoding="utf-8"))
    P = main_plan.parishes()
    cult, ting = {}, set()
    for x in t1["namn"]:
        if not x.get("socken") or x["namn"] in SAMI:
            continue
        k = (x["landskap"], main_plan.norm(x["socken"]))
        if x["kategori"] == "kultplats" and cult.get(k) != "säker":
            cult[k] = x["grad"]
        if x["kategori"] == "ting":
            ting.add(k)
    per_land = collections.Counter(l for l, _ in cult)
    lands = sorted(l for l, n in per_land.items() if n >= 3)
    units = []
    for l in lands:
        for p in P[l]:
            units.append({"land": l, "id": p["id"], "name": p["name"], "key": main_plan.norm(p["name"]),
                          "pt": (p["latitude"], p["longitude"])})
    by_land = collections.defaultdict(list)
    for i, u in enumerate(units):
        by_land[u["land"]].append(i)
    pts = np.array([u["pt"] for u in units])

    def nearest(lat, lon, land=None):
        idx = by_land[land] if land else range(len(units))
        idx = list(idx)
        d = (pts[idx, 0] - lat) ** 2 + ((pts[idx, 1] - lon) * math.cos(math.radians(lat))) ** 2
        return idx[int(np.argmin(d))]

    # the size proxy: distance to the nearest other centroid in the province
    for l, idx in by_land.items():
        for i in idx:
            ds = [km(units[i]["pt"], units[j]["pt"]) for j in idx if j != i]
            units[i]["nn_km"] = min(ds) if ds else None
    # remains (Kulturmiljöregistret), by the nearest centroid in the same province
    cnt = collections.defaultdict(collections.Counter)
    for r in csv.DictReader(open(os.path.join(ROOT, "data", "raa", "lamningar.csv"), encoding="utf-8")):
        if r["province"] not in by_land:
            continue
        i = nearest(float(r["lat"]), float(r["lon"]), r["province"])
        t = "färdväg" if r["type"] in ("färdväg", "färdvägssystem") else r["type"]
        cnt[i][t] += 1
    for r in csv.DictReader(open(os.path.join(ROOT, "data", "ortnamn", "kyrkor.csv"), encoding="utf-8")):
        if r.get("year") and int(float(r["year"])) < 1350:
            cnt[nearest(float(r["lat"]), float(r["lon"]))]["kyrka"] += 1
    for r in csv.DictReader(open(os.path.join(ROOT, "data", "ortnamn", "kultnamn.csv"), encoding="utf-8")):
        if r["tier"] == "C":
            cnt[nearest(float(r["lat"]), float(r["lon"]))]["central"] += 1
    # soils within 2 km of the centroid (SGU, 100 m grid)
    meta = json.load(open(os.path.join(ROOT, "utdata", "palm_jordarna", "jordart_100m.json"), encoding="utf-8"))
    grid = np.array(Image.open(os.path.join(ROOT, "utdata", "palm_jordarna", "jordart_100m.tif")))
    tr = Transformer.from_crs("EPSG:4326", "EPSG:3006", always_xy=True)
    R = 20  # cells (2 km)
    yy, xx = np.mgrid[-R:R + 1, -R:R + 1]
    disk = xx ** 2 + yy ** 2 <= R * R
    for u in units:
        e, n = tr.transform(u["pt"][1], u["pt"][0])
        col = int((e - meta["xmin"]) / meta["res"])
        row = int((meta["ymax"] - n) / meta["res"])
        u["soil"] = None
        if R <= row < grid.shape[0] - R and R <= col < grid.shape[1] - R:
            w = grid[row - R:row + R + 1, col - R:col + R + 1][disk]
            land_cells = w[(w >= 1) & (w <= 5)]
            if len(land_cells) >= 100:  # at least a square kilometre of mapped land
                u["soil"] = {c: float(np.mean(land_cells == k)) for k, c in
                             ((1, "lera"), (2, "sand"), (3, "moran"), (5, "berg"))}
    out = os.path.join(HERE, "landskap_drag.csv")
    cols = ["land", "id", "name", "cult", "cult_saker", "half", "nn_km", "gravfalt", "hog", "fornborg", "hamn", "fardvag",
            "bro", "kyrka", "central", "ting", "lera", "sand", "moran", "berg"]
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for l, idx in by_land.items():
            for rank, i in enumerate(sorted(idx, key=lambda j: units[j]["id"])):
                u, c = units[i], cnt[i]
                k = (l, u["key"])
                s = u["soil"] or {}
                w.writerow({"land": l, "id": u["id"], "name": u["name"], "cult": int(k in cult),
                            "cult_saker": int(cult.get(k) == "säker"), "half": "A" if rank % 2 == 0 else "B",
                            "nn_km": round(u["nn_km"], 3) if u["nn_km"] else "",
                            "gravfalt": c["gravfält"], "hog": c["hög"], "fornborg": int(c["fornborg"] > 0),
                            "hamn": int(c["hamnanläggning"] > 0), "fardvag": c["färdväg"], "bro": int(c["bro"] > 0),
                            "kyrka": int(c["kyrka"] > 0), "central": int(c["central"] > 0), "ting": int(k in ting),
                            **{q: (round(s[q], 4) if q in s else "") for q in ("lera", "sand", "moran", "berg")}})
    n = sum(1 for _ in open(out)) - 1
    print(out, n, "socknar;", sum(1 for k in cult if k[0] in lands), "kultsocknar i", lands)


if __name__ == "__main__":
    main()
