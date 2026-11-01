"""Raderna till ristarprovet (analysplaner/2026-11-01-folkland-at-ristare.md): stenarna i Tiundaland och Attundaland ur
folkland.py med prep_at, tidsskikt, gränszon (socken med en socken i det andra landet inom 10 km), socken och ristare.
Skriver at_rader.csv.
    PYTHONPATH=. .venv/bin/python utdata/folkland/at_rader.py"""
import csv
import io
import os
import sys
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
with redirect_stdout(io.StringIO()):
    import folkland as F  # noqa: E402  (runs the folkland analysis quietly; same rows)

feat = F.feat
out = []
for r in F.rows:
    if r["land"] not in ("tiundaland", "attundaland") or r["prep_at"] is None:
        continue
    other = "attundaland" if r["land"] == "tiundaland" else "tiundaland"
    border = any(F.km(r["pp"][0], r["pp"][1], q[0], q[1]) <= 10 for q in F.land_pts[other])
    out.append({"signum": r["signum"], "land": r["land"], "period": r["period"], "border": int(border),
                "parish": r["parish"], "carver": feat[r["signum"]].get("carver") or "", "prep_at": r["prep_at"]})
with open(os.path.join(HERE, "at_rader.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(out[0]))
    w.writeheader(); w.writerows(out)
print(len(out), sum(o["border"] for o in out), sum(1 for o in out if o["carver"]))
