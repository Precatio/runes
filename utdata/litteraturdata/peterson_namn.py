"""Petersons Nordiskt runnamnslexikon (2007, 5 uppl.; /Volumes/2TB/litteratur/peterson2007_runnamnslexikon.pdf, OCR-läst
med tesseract swe+isl+eng 2026-10-30) som en tabell per uppslag: namnet som Peterson skriver det, kön (mn./kvn.), den
fornvästnordiska formen (raden "Fvn."), artikelblocket (till nästa uppslag) och en jämförelsenyckel som för samman
Petersons runsvenska former med Rundatas normalisering (Biorn = Bjôrn, Froysteinn = Freysteinn, UlfR = Ulfr, OCR:ns
P för Þ). Skriver data/cache/literature/peterson2007_namn.csv (utanför kodförrådet) och peterson_kontroll.txt här.
    .venv/bin/python utdata/litteraturdata/peterson_namn.py"""
import csv
import os
import re
import subprocess
import sys
import unicodedata
from collections import Counter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PDF = os.environ.get("PETERSON_PDF", "/Volumes/2TB/litteratur/peterson2007_runnamnslexikon.pdf")
OUT = os.path.join(ROOT, "data", "cache", "literature", "peterson2007_namn.csv")
HERE = os.path.dirname(os.path.abspath(__file__))
HEAD = re.compile(r"^([^\s].*?) (mn|kvn)\.(?: el\. (mn|kvn)\.)?(.*)$")


def key(n: str) -> str:
    """Samma nyckel för Petersons och Rundatas former: þ/ð, ô/ǫ/ø/œ, æi/ei, j/i, R/r och dubbeltecken förs samman."""
    s = (n.replace("Þ", "th").replace("þ", "th").replace("ð", "d").replace("ô", "o").replace("ǫ", "o").replace("ø", "o")
         .replace("œ", "o").replace("Œ", "o").replace("æi", "ei").replace("Æi", "ei").replace("æ", "e").replace("Æ", "e")
         .replace("ey", "øy").replace("Ey", "øy").replace("ø", "o"))
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c)).lower().replace("j", "i").replace("R", "r")
    return re.sub(r"[^a-z]", "", re.sub(r"(.)\1+", r"\1", s))


lines = subprocess.run(["pdftotext", PDF, "-"], capture_output=True, text=True).stdout.split("\n")
entries, cur = [], None
for line in lines:
    m = HEAD.match(line)
    if m and len(m.group(1)) < 60:
        if cur:
            entries.append(cur)
        cur = {"headword": m.group(1).strip(), "gender": m.group(2), "gender2": m.group(3) or "", "note": m.group(4).strip(),
               "fvn": "", "block": []}
        continue
    if cur is not None:
        if line.startswith("Fvn.") and not cur["fvn"]:
            cur["fvn"] = line[4:].strip()
        cur["block"].append(line)
if cur:
    entries.append(cur)

rows = []
for e in entries:
    variants = [v.strip("”\"*(-– ") for v in re.split(r"\s*/\s*", e["headword"])]
    variants = [v for v in variants if v and not v.startswith("-")]
    keys = set()
    for v in variants:
        keys.add(key(v))
        if re.match(r"^[Pp](?=[oöóiuyeæaå])", v):  # the OCR reads Þ as P in the Þ section
            keys.add(key("Þ" + v[1:]))
    rows.append({"headword": e["headword"], "variants": "|".join(variants), "keys": "|".join(sorted(keys)),
                 "gender": e["gender"], "gender2": e["gender2"], "fvn": e["fvn"],
                 "block": " ".join(x.strip() for x in e["block"] if x.strip())[:1500]})
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)

# coverage against the runestone names of the names study (utdata/overlevde/namn.csv: names on ≥ 3 stones)
lex = {}
for r in rows:
    for k in r["keys"].split("|"):
        lex.setdefault(k, r)
ours = list(csv.DictReader(open(os.path.join(ROOT, "utdata", "overlevde", "namn.csv"), encoding="utf-8")))
hit = [(r, lex[key(r["name"])]) for r in ours if key(r["name"]) in lex]
miss = [r["name"] for r in ours if key(r["name"]) not in lex]
dis = [(r["name"], r["sex"], p["headword"], p["gender"]) for r, p in hit if {"m": "mn", "k": "kvn"}.get(r["sex"]) != p["gender"]]
with open(os.path.join(HERE, "peterson_kontroll.txt"), "w", encoding="utf-8") as fh:
    fh.write(f"{len(rows)} uppslag ({Counter(r['gender'] for r in rows)}); runstensnamn på minst tre stenar som hittas: "
             f"{len(hit)} av {len(ours)}; kön avviker från vår regel: {dis}\nsaknas: {', '.join(miss)}\n")
print(len(rows), "uppslag;", dict(Counter(r["gender"] for r in rows)), f"| träff {len(hit)}/{len(ours)} | könsavvikelser {len(dis)}")
print("saknas:", len(miss), miss[:20])
