"""Roden (låst plan analysplaner/2026-11-02-roden.md, sha 59ea6d58): skriver roden_stenar.csv (Upplands runstenar) för roden.R.
    PYTHONPATH=. .venv/bin/python utdata/roden/roden.py"""
import csv
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
from src import linking as L  # noqa: E402
from src import regions  # noqa: E402

corpus = {r["signum"]: r for r in csv.DictReader(open(os.path.join(ROOT, "data", "cache", "r", "corpus", "7b9061c9a1c12c73", "corpus.csv")))}
st = L.stones(json.load(open(os.path.join(ROOT, "data", "rundata.json")))["inscriptions"])
F = ["pm_kors", "cat_kristen", "cat_fard", "msg_dod_borta", "pm_bon", "msg_berom", "cat_bro_vag", "flera_resare", "kvinna_resare"]
rows = []
for f in csv.DictReader(open(os.path.join(ROOT, "utdata", "upptackt_v3", "drag.csv"))):
    x = st.get(f["signum"])
    if not x or x["province"] != "U" or x["lat"] is None:
        continue
    c = corpus.get(f["signum"], {})
    yr = (float(f["style_from"]) + float(f["style_to"])) / 2 if f["style_from"] else None
    per = "odaterad" if yr is None else "–1010" if yr < 1010 else "1010–1040" if yr < 1040 else "1040–1070" if yr < 1070 else "1070–"
    rows.append({"signum": f["signum"], "region": regions.old_region(f["signum"], "U"), "parish": x["parish"] or "",
                 "lat": x["lat"], "lon": x["lon"], "period": per, "carver": c.get("carver", ""),
                 "carvers_all": c.get("carvers_all", ""), "moved": c.get("moved", ""), "lost": c.get("lost", ""),
                 **{k: f.get(k, "") for k in F}})
with open(os.path.join(HERE, "roden_stenar.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
ro = [r for r in rows if r["region"] == "roden"]
print("Uppland", len(rows), "Roden", len(ro), Counter(r["carvers_all"] or "–" for r in ro).most_common(8))
print(Counter(r["parish"] for r in ro).most_common(20))
