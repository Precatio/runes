"""Hämtar Kulturmiljöregistrets vägar (färdväg, färdvägssystem, bro, vägmärke) med beskrivning, län och kommun, för
självkontrollen analysplaner/2026-11-10-sjalvkontroll-riktning.md. Samma K-samsök-anrop som
scripts/fetch_raa_remains.py, men beskrivningen (pres:description) och länet (andra ledet i pres:placeLabel) sparas.

    .venv/bin/python utdata/riktning/hamta_vagar.py      Skriver data/raa/lamningar_vag.csv (git-ignorerad)."""
from __future__ import annotations

import csv
import html
import os
import re
import sys
import time

OUT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(OUT, "..", ".."))
sys.path.insert(0, ROOT)
from scripts.fetch_raa_remains import ID, LABEL, PAGE, PAUSE_S, PLACE, POINT, RECORD, TOTAL, fetch  # noqa: E402

TYPES = ["färdväg", "färdvägssystem", "bro", "vägmärke"]
DESC = re.compile(r"<pres:description>(.*?)</pres:description>", re.S)
DEST = os.path.join(ROOT, "data", "raa", "lamningar_vag.csv")


def main() -> None:
    rows = []
    for t in TYPES:
        query = f'serviceName=kmr_lamningar and itemClassName="{t}"'
        start, total = 1, None
        while total is None or start <= total:
            xml = fetch(query, start)
            total = int(TOTAL.search(xml).group(1)) if TOTAL.search(xml) else 0
            for rec in RECORD.findall(xml):
                pt = POINT.search(rec)
                if not pt:
                    continue
                place = [p.strip() for p in html.unescape((PLACE.search(rec) or [None, ""])[1]).split(",")]
                rows.append({"id": (ID.search(rec) or [None, ""])[1], "type": t,
                             "lon": round(float(pt.group(1)), 6), "lat": round(float(pt.group(2)), 6),
                             "lan": place[1] if len(place) >= 5 else "", "kommun": place[2] if len(place) >= 5 else "", "landskap": place[3] if len(place) >= 5 else "",
                             "label": (LABEL.search(rec) or [None, ""])[1],
                             "beskrivning": " ".join(html.unescape((DESC.search(rec) or [None, ""])[1]).split())})
            print(f"{t}: {min(start + PAGE - 1, total)} av {total}", flush=True)
            start += PAGE
            time.sleep(PAUSE_S)
    with open(DEST, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["id", "type", "lon", "lat", "lan", "kommun", "landskap", "label", "beskrivning"])
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} vägar → {DEST}")


if __name__ == "__main__":
    main()
