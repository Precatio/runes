"""Hämtar Sveriges socknar med läge och härad (eller skeppslag/tingslag) ur Wikidata till data/geo/socknar_harader.json,
för kartlagret med de gamla landen (scripts/build_historiska_land.R). Wikidata: CC0.
    .venv/bin/python scripts/fetch_harader.py"""
import json
import os
import re

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "geo", "socknar_harader.json")
Q = """SELECT ?s ?sLabel ?coord ?h ?hLabel WHERE {
  ?s wdt:P31 wd:Q1523821 .
  OPTIONAL { ?s wdt:P625 ?coord }
  OPTIONAL { ?s wdt:P131 ?h }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "sv". }
}"""
r = requests.get("https://query.wikidata.org/sparql", params={"query": Q, "format": "json"},
                 headers={"User-Agent": "Vitki/1.0 (runestone research; https://vitkirunor.se)"}, timeout=120)
r.raise_for_status()
socknar = {}
for b in r.json()["results"]["bindings"]:
    s = b["s"]["value"].rsplit("/", 1)[1]
    x = socknar.setdefault(s, {"id": s, "namn": b["sLabel"]["value"], "lon": None, "lat": None, "harad": []})
    if "coord" in b and x["lon"] is None:
        m = re.match(r"Point\(([-\d.]+) ([-\d.]+)\)", b["coord"]["value"])
        if m:
            x["lon"], x["lat"] = float(m.group(1)), float(m.group(2))
    h = b.get("hLabel", {}).get("value", "")
    hid = b.get("h", {}).get("value", "").rsplit("/", 1)[-1]
    if re.search(r"(härad|skeppslag|tingslag|bergslag)$", h) and hid not in [y["id"] for y in x["harad"]]:
        x["harad"].append({"id": hid, "namn": h})
rows = sorted(socknar.values(), key=lambda x: x["namn"])
json.dump({"source": "Wikidata (CC0), socknar (Q1523821) med P625 och P131", "socknar": rows}, open(OUT, "w"),
          ensure_ascii=False, indent=0)
print(len(rows), "socknar;", sum(1 for x in rows if x["lon"] is not None), "med läge;",
      sum(1 for x in rows if x["harad"]), "med härad;", sum(1 for x in rows if len(x["harad"]) > 1), "med flera")
