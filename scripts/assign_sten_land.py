"""Varje vikingatida runsten i Uppland och Småland (och gränsstenar i grannlandskapen) knuten till sitt gamla land
(web/src/lib/historiska_land.json) genom socknen: Rundatas sockennamn mot Wikidatas socknar (data/geo/socknar_land.csv)
inom 25 km, annars närmaste socken inom 15 km. Samma regel som utdata/smalanden/smalanden.py, med två tillägg 2026-11-05:
Rundatas "(nu …)" efter sockennamnet stryks ("Spånga sn (nu Sundbyberg)" är Spånga), och en sten som flyttats långt från
sin socken (Skansen, ett museum) knyts till den socken Rundata anger om namnet finns en enda gång i Sverige och inom
100 km (U 419, U 871, Sm 91, Sm 139). Skriver web/public/geo/sten_land.json ({signum: land}) för kartsidans tabell
"Andel per vikingatida land".
    PYTHONPATH=. .venv/bin/python scripts/assign_sten_land.py"""
import csv
import json
import math
import os
import re
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


def parish_name(x):
    """Rundata's parish as a Wikidata parish name: "Spånga sn (nu Sundbyberg)" → "Spånga socken"."""
    return re.sub(r"\s*\(nu [^)]*\)", "", x["parish"] or "").strip().replace(" sn", "") + " socken"


def land_of(x):
    if x["lat"] is None:
        return None
    named = byname.get(parish_name(x), [])
    near = [s for s in named if km(s, x) <= 25]
    if near:
        return min(near, key=lambda s: km(s, x))["land"] or None
    if len(named) == 1 and km(named[0], x) <= 100:   # moved far from its parish (Skansen, a museum); the name is unique
        return named[0]["land"] or None
    s = min(soc, key=lambda s: km(s, x))
    return (s["land"] or None) if km(s, x) <= 15 else None


out = {}
for sg, x in st.items():
    lnd = land_of(x)
    if lnd:
        out[sg] = lnd
json.dump(out, open(os.path.join(ROOT, "web", "public", "geo", "sten_land.json"), "w"), ensure_ascii=False, separators=(",", ":"))
print(len(out), Counter(out.values()).most_common())
