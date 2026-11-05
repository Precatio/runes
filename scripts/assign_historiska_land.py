"""Knyter varje svensk socken till ett av de gamla landen i web/src/lib/historiska_land.json, för kartlagret
(scripts/build_historiska_land.R). Häradet kommer ur ISOF:s ortnamnsregister och Wikidata (data/geo/socknar_harader.json);
rättelser: socknarna i parish_medieval (sockens medeltida härad efter Det medeltida Sverige, där det skiljer sig från
registren – Färingö tingslag i Bro härad, Adelsö i Trögds, Ekerö och Brännkyrka i Svartlösa, Bromma och Spånga i Sollentuna;
markerat 'medeltida', 2026-11-05), socknarna i parish_overrides (Vista och Stranda härad efter Wikipedia, eftersom Wikidata
blandar ihop Vista härad med Viste i Västergötland och saknar Stranda), Rundatas härad för socknar som saknar härad i
Wikidata, och för resten häradet hos närmaste socken med härad om den ligger inom 15 km (markerat 'närmast'), annars inget
land. Skriver data/geo/socknar_land.csv.
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
# ISOF's register (PlaceNameService, CC BY; downloaded to geografi_kallor/isof/) is the first source for a parish's
# härad since 2026-11-02: it agreed with Wikidata for 2 232 parishes and corrected four (Adelöv, Aspö, Håcksvik, Rydaholm)
ISOF = "/Volumes/2TB/Antigrvity/Runes/geografi_kallor/isof/"
isof = {}
if os.path.exists(ISOF + "parishes.json"):
    dist = {d["id"]: d["name"] for d in json.load(open(ISOF + "districts.json"))}
    for p in json.load(open(ISOF + "parishes.json")):
        h = (dist.get(p["district_id"]) or "").replace("N. ", "Norra ").replace("S. ", "Södra ").replace(" hd", " härad") \
            .replace(" sg", " skeppslag").replace(" tg", " tingslag")
        isof.setdefault(p["name"].replace(" sn", " socken"), []).append((p["latitude"], p["longitude"], h))


def isof_land(s):
    """The land by ISOF's härad for a parish at (about) the same place; None when ISOF has no parish there."""
    for la, lo, h in isof.get(s["namn"], []):
        if abs(la - s["lat"]) < 0.2 and abs(lo - s["lon"]) < 0.3:
            if h in ("Östra härad", "Västra härad"):        # Njudung's, not Blekinge's
                return ("njudung", h) if la > 56.6 else (None, h)
            return by_name.get(h), h
    return None


# The medieval härad where it differs from the registers (historiska_land.json → parish_medieval, keyed by Wikidata id, each
# with its page in Det medeltida Sverige): Färingö tingslag was the other half of Bro härad (Attundaland), Adelsö belonged to
# Trögd (Fjädrundaland) and Ekerö to Svartlösa in Södermanland until the 1540s; ISOF puts Bromma, Spånga and Brännkyrka in
# "Ingår i Stockholms stad". A härad outside the lands (Svartlösa) gives no land.
MEDIEVAL = defs.get("parish_medieval", {}).get("socknar", {})
assert all(v["harad"] in by_name or v["harad"] == "Svartlösa härad" for v in MEDIEVAL.values())

rows = []
for s in soc:
    il = isof_land(s) if not (s["namn"] in gotland and ON_GOTLAND(s)) else None
    if s["id"] in MEDIEVAL:
        assert MEDIEVAL[s["id"]]["namn"] == s["namn"], s
        rows.append({**s, "land": by_name.get(MEDIEVAL[s["id"]]["harad"]), "how": "medeltida"})
    elif s["namn"] in gotland and ON_GOTLAND(s):
        rows.append({**s, "land": gotland[s["namn"]], "how": "wikipedia"})
    elif s["namn"] in override:
        rows.append({**s, "land": by_name[override[s["namn"]]], "how": "wikipedia"})
    elif il is not None and il[1] and "Ingår i" not in il[1] and "stad" not in il[1]:
        rows.append({**s, "land": il[0], "how": "isof"})
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
