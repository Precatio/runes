"""Tillägg till at_rader.csv för tilläggsplan 2 (analysplaner/2026-11-01-folkland-at-trappa.md): antal runor i huvudläsningen,
antal namngivna personer utom ristare, häradet och flyttad. Skriver at_rader2.csv.
    PYTHONPATH=. .venv/bin/python utdata/folkland/at_rader2.py"""
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "utdata", "Malt"))
from src import linking as L  # noqa: E402
from runrad_dubblering import stretches  # noqa: E402

rd = json.load(open(os.path.join(ROOT, "data", "rundata.json")))["inscriptions"]
ins = {r["signum"]: r for r in rd}
st = L.stones(rd)
corp = {r["signum"]: r for r in csv.DictReader(open(os.path.join(ROOT, "data", "cache", "r", "corpus", "605ba7cc0f4e355f", "corpus.csv")))}
rows = list(csv.DictReader(open(os.path.join(HERE, "at_rader.csv"))))
for r in rows:
    sg = r["signum"]
    r["runes"] = sum(len(g) for s in stretches(ins[sg].get("transliteration")) for g in s)
    r["names"] = sum(1 for p in st[sg]["persons"] if p["role"] != "ristare")
    r["district"] = (corp.get(sg) or {}).get("district") or ""
    r["moved"] = (corp.get(sg) or {}).get("moved") or ""
with open(os.path.join(HERE, "at_rader2.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader(); w.writerows(rows)
print(len(rows), sum(1 for r in rows if r["district"]), sum(1 for r in rows if r["moved"] == "1"))
