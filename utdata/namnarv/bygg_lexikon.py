"""Bygger det låsta namnlexikonet lexikon.csv ur lexikon_del1–3.txt (handklassning), runkoppling.txt och
SMP-kontrollens rättelser (planen analysplaner/2026-10-29-namnen-som-levde-kvar.md) och skriver dess SHA-256."""
import csv
import glob
import hashlib
import os

OUT = os.path.dirname(os.path.abspath(__file__))
# Namn som också är vanliga ord: bara förekomster inne i en mening räknas
TVETYDIGA = {"Bo", "Sten", "Karl", "Orm", "Stig", "Inge", "Folke", "Finne", "Dan", "Bonde", "Gisle", "Ebbe", "Sune"}
run = {}
for l in open(os.path.join(OUT, "runkoppling.txt"), encoding="utf-8"):
    if l.startswith("#") or not l.strip():
        continue
    n, keys = l.rstrip("\n").split("|")
    run[n] = keys
rows, seen = [], set()
for f in sorted(glob.glob(os.path.join(OUT, "lexikon_del*.txt"))):
    for l in open(f, encoding="utf-8"):
        if l.startswith("#") or not l.strip():
            continue
        forms, norm, g, o = l.strip().split("|")
        for w in forms.split(","):
            if w in seen:
                continue
            seen.add(w)
            rows.append({"ord": w, "normalform": norm, "kon": g, "ursprung": o,
                         "runsten": run.get(norm, "") if o == "N" else "", "tvetydig": int(norm in TVETYDIGA)})
path = os.path.join(OUT, "lexikon.csv")
with open(path, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
sha = hashlib.sha256(open(path, "rb").read()).hexdigest()
open(os.path.join(OUT, "lexikon.sha256"), "w").write(f"{sha}  lexikon.csv\n")
print(len(rows), "stavningar,", len({r["normalform"] for r in rows}), "namn; SHA-256", sha[:16])
