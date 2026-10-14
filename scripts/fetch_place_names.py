"""Ortnamn som kan tyda på förkristen kult, alla jämförbara ortnamn och medeltida kyrkor, för remains.R (METHODS.md 1d).

    python scripts/fetch_place_names.py

Ortnamnen kommer ur OpenStreetMap (© OpenStreetMap-bidragsgivare, ODbL), där Lantmäteriets ortnamn från
terrängkartan finns inlagda. Sveriges utdrag hämtas från Geofabrik (omkring 900 MB) till data/cache/osm/ och
ortnamnen plockas ut med GDAL (ogr2ogr måste finnas). Kyrkorna är Wikidatas kyrkobyggnader i Sverige med ett
uppförandeår före 1350 (CC0); de är långt ifrån alla medeltida kyrkor.

Skriver till data/ortnamn/ (git-ignorerad):
  kultnamn.csv – ortnamn i två nivåer:
      A  teofora namn: ett gudanamn (Tor, Oden/Ons, Frö, Ull, Njärd/När, Härn, Dis) med en sakral eller typisk
         efterled (vi/ve/vid, harg, hov, lunda, åker/åkra, sal/sala, tuna, sunda), t.ex. Torsvi, Odensala, Ullevi,
         Frösö. Singularformen -lund räknas inte (oftast unga villanamn).
      B  sakrala ord utan gudanamn: Vi, Ve, Viby, Harg, Hov, Hof, Hörg, Gudhem. Osäkrare: harg kan betyda stenig mark
         och hov gård eller höjd.
      C  centralorter utan kult, som jämförelse: Husby, Tuna och namn på -tuna utan gudanamn (teofora namn
         markerar ofta centralorter, där eliten kan ha blivit kristen tidigt).
  platser.csv – alla ortnamn av samma slag (by, gård, hemman, ort), som jämförelse
  kyrkor.csv  – medeltida kyrkor ur Wikidata
"""
from __future__ import annotations

import csv
import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "ortnamn")
PBF = os.path.join(ROOT, "data", "cache", "osm", "sweden-latest.osm.pbf")
PBF_URL = "https://download.geofabrik.de/europe/sweden-latest.osm.pbf"
UA = "Vitki runology research (open source)"

# Rural place types: Lantmäteriet's village, hamlet and farm names; urban types (neighbourhoods, blocks) are mostly young
TYPES = {"hamlet", "isolated_dwelling", "farm", "village", "locality", "town", "islet"}
GOD = r"(?:Tors?|Odens?|Ons|Frös?|Frej|Fröj|Ull(?:e|er|s)?|Njärd(?:ar)?|När|Härne?|Dise?)"
SECOND = r"(?:vi|ve|vid|harg|harv|hov|lunda|åker|åkra|sal|sala|tuna|sunda)"
TIER_A = re.compile(rf"^{GOD}-?{SECOND}$|^(?:Ultuna|Frösö|Frösön)$")
TIER_B = re.compile(r"^(?:Vi|Ve|Viby|Vibyn|Harg|Hov|Hof|Hörg|Gudhem)$")
# Central places without cult: royal estates (Husby) and tuna names without a god – a control, since theophoric names
# often mark central places where the elite may have taken up Christianity early
TIER_C = re.compile(r"^(?:Husby|Husaby|Husbyn|Tuna|Tunby)$|^[A-ZÅÄÖ][a-zåäö]+tuna$")
GODS = [("Tor", r"^Tor"), ("Oden", r"^(?:Oden|Ons)"), ("Frö", r"^Frö|^Frej"), ("Ull", r"^Ul"), ("Njärd", r"^(?:Njärd|När)"),
        ("Härn", r"^Härn"), ("Dis", r"^Dis")]

CHURCHES = """SELECT ?item ?coord ?inc WHERE {
  ?item wdt:P31 wd:Q16970; wdt:P17 wd:Q34; wdt:P571 ?inc; wdt:P625 ?coord.
}"""


def places() -> list[dict]:
    if not os.path.exists(PBF):
        os.makedirs(os.path.dirname(PBF), exist_ok=True)
        print("hämtar", PBF_URL, flush=True)
        req = urllib.request.Request(PBF_URL, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=600) as r, open(PBF, "wb") as fh:
            while chunk := r.read(1 << 20):
                fh.write(chunk)
    tmp = os.path.join(os.path.dirname(PBF), "places.csv")
    if os.path.exists(tmp):
        os.remove(tmp)  # the CSV driver does not overwrite
    subprocess.run(["ogr2ogr", "-f", "CSV", tmp, PBF, "points", "-sql",
                    "SELECT osm_id, name, place FROM points WHERE place IS NOT NULL AND name IS NOT NULL",
                    "-lco", "GEOMETRY=AS_XY"], check=True)
    with open(tmp, encoding="utf-8") as fh:
        return [{"name": r["name"], "place": r["place"], "lat": round(float(r["Y"]), 5), "lon": round(float(r["X"]), 5)}
                for r in csv.DictReader(fh) if r["place"] in TYPES]


def churches() -> list[dict]:
    url = "https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": CHURCHES})
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/sparql-results+json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        rows = json.load(r)["results"]["bindings"]
    out = {}
    for x in rows:
        m = re.match(r"[+-]?(\d{3,4})", x["inc"]["value"])
        pt = re.match(r"Point\(([-\d.]+) ([-\d.]+)\)", x["coord"]["value"])
        if not m or not pt or int(m.group(1)) >= 1350:
            continue
        qid = x["item"]["value"].rsplit("/", 1)[-1]
        year = int(m.group(1))
        if qid not in out or year < out[qid]["year"]:
            out[qid] = {"id": qid, "year": year, "lat": round(float(pt.group(2)), 5), "lon": round(float(pt.group(1)), 5)}
    return list(out.values())


def write(name: str, rows: list[dict], fields: list[str]) -> None:
    with open(os.path.join(OUT, name), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} → data/ortnamn/{name}")


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    all_places = places()
    cult = []
    for p in all_places:
        tier = ("A" if TIER_A.match(p["name"]) else "B" if TIER_B.match(p["name"])
                else "C" if TIER_C.match(p["name"]) else None)
        if tier:
            god = next((g for g, rx in GODS if re.match(rx, p["name"])), "") if tier == "A" else ""
            cult.append({**p, "tier": tier, "god": god})
    write("kultnamn.csv", cult, ["name", "tier", "god", "place", "lat", "lon"])
    write("platser.csv", all_places, ["name", "place", "lat", "lon"])
    try:
        write("kyrkor.csv", churches(), ["id", "year", "lat", "lon"])
    except Exception as e:  # noqa: BLE001 - Wikidata svarar inte: kyrkorna hoppas över
        print("kyrkorna kunde inte hämtas:", e, file=sys.stderr)


if __name__ == "__main__":
    main()
