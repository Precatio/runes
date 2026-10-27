"""Tabellen som statistik.R läser: de handkodade västerinskrifterna (hemma_kodning.csv) med region, stilgrupp och om
England, London eller Bath nämns uttryckligen. Skriver utdata/brittiska/hemma_tabell.csv.
    .venv/bin/python utdata/brittiska/statistik_data.py && Rscript utdata/brittiska/statistik.R
"""
import csv
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
from api.rundata import store  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
G, S = {"Ög", "Sm", "Vg"}, {"Sö", "U", "Vs", "Gs"}
with open(os.path.join(HERE, "hemma_tabell.csv"), "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["signum", "region", "stil", "utfall", "england"])
    for r in csv.DictReader(open(os.path.join(HERE, "hemma_kodning.csv"), encoding="utf-8")):
        rec, pre = store().get(r["signum"]), r["signum"].split()[0]
        st = rec.get("style") or ""
        w.writerow([r["signum"], "Götaland" if pre in G else "Svealand" if pre in S else "övrigt",
                    "" if not st or st.startswith("?") else "RAK" if st.startswith("RAK") else "senare", r["utfall"],
                    int(bool(re.search(r"\b(england|london|bath)\b", rec.get("translation_en") or "", re.I)))])
print("skrev hemma_tabell.csv")
