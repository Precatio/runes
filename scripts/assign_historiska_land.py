"""Knyter varje svensk socken till ett av de gamla landen i web/src/lib/historiska_land.json, för kartlagret
(scripts/build_historiska_land.R). Häradet kommer ur Wikidata (data/geo/socknar_harader.json); rättelser: socknarna i
parish_overrides (Vista och Stranda härad efter Wikipedia, eftersom Wikidata blandar ihop Vista härad med Viste i
Västergötland och saknar Stranda), Rundatas härad för socknar som saknar härad i Wikidata, och för resten häradet hos
närmaste socken med härad om den ligger inom 15 km (markerat 'närmast'), annars inget land. Skriver data/geo/socknar_land.csv.
    .venv/bin/python scripts/assign_historiska_land.py"""
import csv
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from src import runlm as rl  # noqa: E402

defs = json.load(open(os.path.join(ROOT, "web", "src", "lib", "historiska_land.json")))
soc = [s for s in json.load(open(os.path.join(ROOT, "data", "geo", "socknar_harader.json")))["socknar"] if s["lon"] is not None]
override = {p: h for h, ps in defs["parish_overrides"].items() for p in ps}
# Rundata's härad per parish name, with the mean position of its stones: parish names repeat across Sweden (Ed, Holm,
# Nora …), so a Rundata härad is used only when its stones lie within 25 km of the parish point
from collections import defaultdict  # noqa: E402
acc = defaultdict(list)
for r in rl.load_rundata():
    if r.get("parish") and r.get("district") and r.get("lat") and r.get("lon"):
        acc[(r["parish"].replace(" sn", "") + " socken", r["district"].replace(" hd", " härad"))].append((r["lat"], r["lon"]))
rd = defaultdict(list)
for (pn, dist), pts in acc.items():
    rd[pn].append((dist, sum(a for a, _ in pts) / len(pts), sum(b for _, b in pts) / len(pts)))


def rd_harad(s):
    for dist, la, lo in rd.get(s["namn"], []):
        if 111.2 * math.hypot(la - s["lat"], (lo - s["lon"]) * math.cos(math.radians(s["lat"]))) <= 25:
            return dist
    return None
by_name, by_id, gotland = {}, {}, {}
for reg in defs["epoch"]["regions"]:
    if "socknar" in reg:                # Gotland's tredingar: listed by parish (Wikipedia), only on Gotland
        for p in reg["socknar"]:
            gotland[p + " socken"] = reg["id"]
        continue
    if "harad_id" in reg:
        for q in reg["harad_id"]:
            by_id[q] = reg["id"]
    else:
        for h in reg["harad"]:
            by_name[h] = reg["id"]
OVERRIDDEN = set(defs["parish_overrides"])


def land_of(harads):
    for h in harads:
        if h["id"] in by_id:
            return by_id[h["id"]]
        if h["namn"] in by_name and h["namn"] not in OVERRIDDEN:
            return by_name[h["namn"]]
    return None


ON_GOTLAND = lambda s: 56.85 <= s["lat"] <= 58.0 and 18.0 <= s["lon"] <= 19.4  # noqa: E731
rows = []
for s in soc:
    if s["namn"] in gotland and ON_GOTLAND(s):
        rows.append({**s, "land": gotland[s["namn"]], "how": "wikipedia"})
    elif s["namn"] in override:
        rows.append({**s, "land": by_name[override[s["namn"]]], "how": "wikipedia"})
    elif s["harad"]:
        rows.append({**s, "land": land_of(s["harad"]), "how": "wikidata"})
    elif rd_harad(s):
        rows.append({**s, "land": by_name.get(rd_harad(s)), "how": "rundata"})
    else:
        rows.append({**s, "land": None, "how": None})
known = [r for r in rows if r["how"]]
for r in rows:
    if r["how"] is None:
        d2 = lambda k: (k["lat"] - r["lat"]) ** 2 + ((k["lon"] - r["lon"]) * math.cos(math.radians(r["lat"]))) ** 2  # noqa: E731
        near = min(known, key=d2)
        km = 111.2 * math.sqrt(d2(near))
        closed = {by_name[h] for h in OVERRIDDEN}            # Vista: the source lists its four parishes, no more
        r["land"], r["how"] = (near["land"], "närmast") if km <= 15 and near["land"] not in closed else (None, "ingen")
with open(os.path.join(ROOT, "data", "geo", "socknar_land.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=["id", "namn", "lon", "lat", "land", "how"])
    w.writeheader()
    for r in rows:
        w.writerow({k: r[k] for k in w.fieldnames})
from collections import Counter
print(Counter(r["how"] for r in rows), Counter(r["land"] for r in rows if r["land"]))
print("närmast inom landen:", [(r["namn"], r["land"]) for r in rows if r["how"] == "närmast" and r["land"]])
