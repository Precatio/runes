"""Slår upp lexikonets förnamn (A–J) i Sveriges medeltida personnamn (ISOF, häfte 1–17, pdf i data/cache/smp/) och
skriver ut SMP:s ursprungsuppgift bredvid vår klassning, för handkontroll enligt planen
analysplaner/2026-10-29-namnen-som-levde-kvar.md. Skriver smp_kontroll.csv."""
import csv
import glob
import os
import re

import pypdf

OUT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(OUT, "..", ".."))
TXT = os.path.join(ROOT, "data", "cache", "smp", "smp.txt")

if not os.path.exists(TXT):
    with open(TXT, "w", encoding="utf-8") as fh:
        for f in sorted(glob.glob(os.path.join(ROOT, "data", "cache", "smp", "h*.pdf"))):
            for p in pypdf.PdfReader(f).pages:
                fh.write((p.extract_text() or "") + "\n")
text = open(TXT, encoding="utf-8").read()
HEAD = re.compile(r"^([A-ZÅÄÖÆØÞ][A-ZÅÄÖÆØÞ()\-]{1,}),")
heads, pos = [], 0
lines = text.split("\n")
for i, line in enumerate(lines):
    m = HEAD.match(line)
    if m and re.search(r"\b(mn|kvn)\.", (line + " " + (lines[i + 1] if i + 1 < len(lines) else ""))[:220]):
        heads.append((m.group(1).replace("(", "").replace(")", ""), pos))
    pos += len(line) + 1
articles = {}
for i, (h, s) in enumerate(heads):
    e = heads[i + 1][1] if i + 1 < len(heads) else len(text)
    articles.setdefault(h, text[s:e])
xref = {}
for form, h in re.findall(r"([A-ZÅÄÖÆØa-zåäöæøþð()\-]+), se ([A-ZÅÄÖÆØÞ]{2,})", text):
    xref.setdefault(form.replace("(", "").replace(")", "").lower(), h)
ORIGIN = re.compile(r"((?:Nord\.|Lat\.|Grek\.|Hebr\.|Ty\.|Mlty\.|Lty\.|Fty\.|Fra\.|Kelt\.|Eng\.|Slav\.|Fsv\.|Fda\.|Bibl\.|"
                    r"Av |Kortform|Smeknamnsform|Sidoform|Helgon)[^\n]{0,160})")

lex = {}
for f in sorted(glob.glob(os.path.join(OUT, "lexikon_del*.txt"))):
    for l in open(f, encoding="utf-8"):
        if l.startswith("#") or not l.strip():
            continue
        forms, norm, g, o = l.strip().split("|")
        lex.setdefault((norm, o), set()).update(forms.split(","))
rows = []
for (norm, o), forms in sorted(lex.items()):
    cand = [norm.upper()] + [x.upper() for x in forms] + [xref.get(x.lower(), "") for x in forms]
    h = next((c for c in cand if c in articles), "")
    org = ORIGIN.findall(articles[h]) if h else []
    rows.append({"normalform": norm, "var_klass": o, "smp_uppslag": h, "smp_ursprung": " | ".join(org[:3])})
with open(os.path.join(OUT, "smp_kontroll.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
print(len(articles), "artiklar;", sum(1 for r in rows if r["smp_uppslag"]), "av", len(rows), "namn hittade")
