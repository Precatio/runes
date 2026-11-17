"""Datakvalitet: SRI:s fyndhistorik mot appens egna fält (Viktor 2026-11-17, "punkt 3").

Bara överensstämmelse, inga prov på A1:s frågor (analysplaner/2027-01-A1-*.md): SRI:s läge mot `is_moved`
(tillägg 1: "Oenigheterna listas som ett förslag till Viktor"), SRI:s "försvunnen när bandet skrevs" mot Rundatas
`flags.lost`, och SRI:s läge mot Runor 2020:s `original`. Tabellen innehåller bara våra fält, inga citat.

    .venv/bin/python scripts/sri_kvalitet.py      # skriver utdata/sri_kvalitet/stenar.csv och kör r/sri_kvalitet.R
"""
from __future__ import annotations

import csv
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from api.rundata import store  # noqa: E402
from src import research_gaps as gaps  # noqa: E402
from src import runor, sri_fyndhistorik  # noqa: E402
from src.r_bridge import is_moved  # noqa: E402

UT = os.path.join(ROOT, "utdata", "sri_kvalitet")


def main() -> None:
    os.makedirs(UT, exist_ok=True)
    rows = []
    for r in store().inscriptions:
        if not gaps.is_runestone(r):
            continue
        s = sri_fyndhistorik.for_inscription(r)
        if not s:
            continue
        ru = runor.for_inscription(r) if runor.available() else None
        lost = s.get("lost") or {}
        rows.append({
            "signum": r["signum"], "province": gaps.province(r), "checked_by": s["checked_by"],
            "is_moved": int(is_moved(r)), "rundata_lost": int(bool((r.get("flags") or {}).get("lost"))),
            "runor_original": "" if not ru or ru.get("original_location") is None else int(bool(ru["original_location"])),
            "sri_lage": (s.get("position") or {}).get("value") or "",
            "sri_inmurad": int(bool(s.get("built_in"))),
            "sri_lost_at_edition": int(bool(lost.get("lost_at_edition"))),
            "sri_ever_lost": int(bool(s.get("lost"))),
            "sri_refound": int(bool(s.get("refound"))),
            "sri_same_stone": int(bool(s.get("same_stone"))),
            "place": r.get("place") or "", "placement": r.get("placement") or "",
        })
    p = os.path.join(UT, "stenar.csv")
    with open(p, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(len(rows), "runstenar med SRI-artikel ->", p)
    subprocess.run(["Rscript", "--vanilla", os.path.join(ROOT, "r", "sri_kvalitet.R"), p, UT], check=True)


if __name__ == "__main__":
    main()
