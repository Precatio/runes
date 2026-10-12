"""Hämtar lämningar ur Kulturmiljöregistret (RAÄ) via K-samsök: typ, punkt, landskap och RAÄ-nummer.

    python scripts/fetch_raa_remains.py [TYP ...]

Skriver data/raa/lamningar.csv (git-ignorerad). Utan argument hämtas de typer som prövas mot runstenarnas lägen
(METHODS.md 17): gravfält, hög, färdväg, färdvägssystem, bro, fornborg och hamnanläggning. K-samsök är RAÄ:s öppna
API (kulturarvsdata.se); hämtningen tar en sida om 500 poster i taget med en paus mellan anropen.
"""
from __future__ import annotations

import csv
import os
import re
import sys
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.environ.get("RAA_REMAINS", os.path.join(ROOT, "data", "raa", "lamningar.csv"))  # another file with RAA_REMAINS
API = "https://kulturarvsdata.se/ksamsok/api"
TYPES = ["gravfält", "hög", "färdväg", "färdvägssystem", "bro", "fornborg", "hamnanläggning"]
PAGE = 500
PAUSE_S = 1.0

RECORD = re.compile(r"<record>(.*?)</record>", re.S)
POINT = re.compile(r"<gml:Point[^>]*>\s*<gml:coordinates[^>]*>([-\d.]+),([-\d.]+)</gml:coordinates>")
ID = re.compile(r"<pres:id>(.*?)</pres:id>")
LABEL = re.compile(r"<pres:idLabel>(.*?)</pres:idLabel>")
PLACE = re.compile(r"<pres:placeLabel>(.*?)</pres:placeLabel>")
TOTAL = re.compile(r"<totalHits>(\d+)</totalHits>")


def fetch(query: str, start: int) -> str:
    url = API + "?" + urllib.parse.urlencode({"method": "search", "hitsPerPage": PAGE, "startRecord": start,
                                              "recordSchema": "presentation", "query": query})
    req = urllib.request.Request(url, headers={"User-Agent": "Vitki runology research (open source)"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read().decode("utf-8")
        except Exception as e:  # noqa: BLE001 - nätverksfel: försök igen efter en paus
            print(f"  fel ({e}), försöker igen", file=sys.stderr)
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"K-samsök svarar inte: {url}")


def province(place: str) -> str:
    # "Sverige, Östergötland, Norrköping, Östergötland, Kullerstad": land, län, kommun, landskap, socken
    parts = [p.strip() for p in place.split(",")]
    return parts[3] if len(parts) >= 5 else ""


def main(types: list[str]) -> None:
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    rows = []
    for t in types:
        query = f'serviceName=kmr_lamningar and itemClassName="{t}"'
        start, total = 1, None
        while total is None or start <= total:
            xml = fetch(query, start)
            total = int(TOTAL.search(xml).group(1)) if TOTAL.search(xml) else 0
            for rec in RECORD.findall(xml):
                pt = POINT.search(rec)
                if not pt:
                    continue
                place = PLACE.search(rec)
                rows.append({"id": (ID.search(rec) or [None, ""])[1], "type": t, "lon": round(float(pt.group(1)), 6),
                             "lat": round(float(pt.group(2)), 6), "province": province(place.group(1) if place else ""),
                             "label": (LABEL.search(rec) or [None, ""])[1]})
            print(f"{t}: {min(start + PAGE - 1, total)} av {total}", flush=True)
            start += PAGE
            time.sleep(PAUSE_S)
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["id", "type", "lon", "lat", "province", "label"])
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} lämningar → {OUT}")


if __name__ == "__main__":
    main(sys.argv[1:] or TYPES)
