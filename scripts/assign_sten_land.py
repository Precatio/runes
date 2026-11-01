"""Varje vikingatida runsten i Uppland och Småland (och gränsstenar i grannlandskapen) knuten till sitt gamla land
(web/src/lib/historiska_land.json) genom socknen: Rundatas sockennamn mot Wikidatas socknar (data/geo/socknar_land.csv)
inom 25 km, annars närmaste socken inom 15 km. Samma regel som utdata/smalanden/smalanden.py. Skriver
web/public/geo/sten_land.json ({signum: land}) för kartsidans tabell "Andel per vikingatida land".
    PYTHONPATH=. .venv/bin/python scripts/assign_sten_land.py"""
import csv
import json
import math
import os
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from src import linking as L  # noqa: E402

rd = json.load(open(os.path.join(ROOT, "data", "rundata.json")))["inscriptions"]
st = L.stones(rd)
soc = list(csv.DictReader(open(os.path.join(ROOT, "data", "geo", "socknar_land.csv"))))
byname = defaultdict(list)
for s in soc:
    byname[s["namn"]].append(s)


def km(s, x):
    return 111.2 * math.hypot(float(s["lat"]) - x["lat"], (float(s["lon"]) - x["lon"]) * math.cos(math.radians(x["lat"])))


def land_of(x):
    if x["lat"] is None:
        return None
    near = [s for s in byname.get((x["parish"] or "").replace(" sn", "") + " socken", []) if km(s, x) <= 25]
    if near:
        return min(near, key=lambda s: km(s, x))["land"] or None
    s = min(soc, key=lambda s: km(s, x))
    return (s["land"] or None) if km(s, x) <= 15 else None


out = {}
for sg, x in st.items():
    lnd = land_of(x)
    if lnd:
        out[sg] = lnd
json.dump(out, open(os.path.join(ROOT, "web", "public", "geo", "sten_land.json"), "w"), ensure_ascii=False, separators=(",", ":"))
print(len(out), Counter(out.values()).most_common())
