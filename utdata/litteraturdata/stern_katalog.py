"""Sterns bildkatalog (Stern 2013, Runestone images and visual communication, Appendix 1, PDF-sidorna 333–362) som en
tabell per sten: avdelning (1.A hela vikingatida runstenar med bilder, 1.A tillägg, 1.B skadade/förlorade, 1.C för- och
eftervikingatida), signum, stil, datering, ristare, bild (Sterns ord) och mått. Kolumnerna läses efter rubrikradens lägen
(behålls över sidor utan rubrik); signum tas från postraden själv; fotnoter nederst på sidan hoppas över. Skriver
data/cache/literature/stern2013_bilder.csv (utanför kodförrådet: katalogen är Sterns sammanställning, vi publicerar bara
det vi räknar ur den) och stern_kontroll.txt här för granskning.
    .venv/bin/python utdata/litteraturdata/stern_katalog.py"""
import csv
import os
import re
import subprocess
import sys
from collections import Counter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
from src.signum import fold_signum  # noqa: E402

PDF = os.environ.get("STERN_PDF", "/Volumes/2TB/litteratur/stern2013.pdf")
OUT = os.path.join(ROOT, "data", "cache", "literature", "stern2013_bilder.csv")
HERE = os.path.dirname(os.path.abspath(__file__))
COLS = ["SIGLUM AND PLACE", "REGION", "STYLE", "PERIOD", "CARVER", "IMAGE", "STONE", "STATUS", "MONUMENT TYPE"]
ENTRY = re.compile(r"^\s*(\d{1,3})\.\s+(.*)$")
SIG = re.compile(r"^\[?(DR|N|U|Sö|Ög|Vg|Sm|Öl|G|Vs|Gs|Nä|Hs|M|Bo|D|J|Vr|Vå|IM|E|Sc|Or|Br|DK)\]?\s+([^\s฀]+)")
SECTION = [(re.compile(r"APPENDIX 1\.A"), "1.A"), (re.compile(r"The following memorials should also"), "1.A tillägg"),
           (re.compile(r"APPENDIX 1\.B"), "1.B"), (re.compile(r"APPENDIX 1\.C"), "1.C")]
FOOTNOTE = re.compile(r"^\s{0,6}\d{1,3}\s+(?=[A-Z])(?!\S*\.)")  # "5  Since this stone is not listed …" (not "5. DR 77")
PAGENO = re.compile(r"^\s*\d{1,3}\s*$")

text = subprocess.run(["pdftotext", "-layout", "-f", "333", "-l", "362", PDF, "-"], capture_output=True, text=True).stdout
rows, cur, cols, section = [], None, None, "1.A"
for page in text.split("\f"):
    for line in page.split("\n"):
        for rx, name in SECTION:
            if rx.search(line):
                section = name
        if "SIGLUM AND PLACE" in line and "IMAGE" in line:
            cols = sorted([(c, line.index(c)) for c in COLS if c in line], key=lambda x: x[1])
            continue
        if cols is None or not line.strip():
            continue
        if PAGENO.match(line):
            continue  # the page's number, printed at its top or bottom
        if FOOTNOTE.match(line) and not ENTRY.match(line):
            break  # the page's footnotes: nothing below belongs to the table
        m = ENTRY.match(line)
        if m and SIG.match(m.group(2).strip()):
            if cur:
                rows.append(cur)
            s = SIG.match(m.group(2).strip())
            # pages without their own header are indented differently: shift the columns by where the number stands
            shift = (len(line) - len(line.lstrip())) - cols[0][1]
            cur = {"nr": int(m.group(1)), "section": section, "signum": f"{s.group(1)} {s.group(2)}", "shift": shift,
                   **{c: "" for c in COLS}}
        if cur is None:
            continue
        for i, (c, start) in enumerate(cols):
            start = max(0, start + cur["shift"])
            # the image cell runs to the end of the line (the size or status after it is stripped below), so that a
            # page whose columns sit further right than its header's does not cut the image words
            end = len(line) if c == "IMAGE" or i + 1 == len(cols) else (cols[i + 1][1] + cur["shift"])
            piece = line[start:end].strip() if start < len(line) else ""
            piece = re.sub(r"(?<=[a-zA-Z)])\d{1,3}$", "", piece)  # a footnote marker glued to a word
            if piece:
                cur[c] = (cur[c] + " " + piece).strip()
if cur:
    rows.append(cur)

SIZE = re.compile(r"(?:was\s+)?\d+[.,]\d+(?:\s*x\s*\d+[.,]\d+)+\s*$")
STATUS = re.compile(r"\b(lost(?: fragment)?|damaged|fragment(?:s|ary)?|grave slab|headstone|footstone|lid|lost and damaged)\b", re.I)
# Stern's image words → categories (word boundaries; 'man' alone is not used because of 'Mammen' and place names)
CLASSES = {"skepp": r"\bships?\b", "ryttare": r"\briders?\b", "häst": r"\bhorses?\b", "fågel": r"\bbirds?\b|\braven\b|\beagle\b",
           "mask": r"\bmasks?\b|\bfaces?\b", "fyrfotadjur": r"\bquadrupeds?\b|\bleonine\b|\blupine\b|\bcervine\b|\bcanine\b|\bwolf\b|\bdeer\b|\bstag\b",
           "människa": r"\bhumanoids?\b|\bwarriors?\b|\bwoman\b|\bman\b|\bmen\b|\bfigures?\b|\barchers?\b|\bwrestl", "kors": r"\bcross(?:es)?\b(?!-staff)",
           "sigurd": r"sigur[ðd]r", "kristus": r"\bchrist\b|\bnativity\b|\bmagi\b", "tor": r"\bþ[óo]rr?\b|\bthor\b", "hammare": r"\bhammers?\b",
           "orm_som_bild": r"\bsnakes?\b|\bserpents?\b(?!ine)|\bserpentine\b", "vagn": r"\bwagon\b", "byggnad": r"\bbuilding\b|\bchurch\b"}
out = []
for r in rows:
    image = r["IMAGE"].replace("฀", "").strip()
    size = r["STONE"].strip()
    if SIZE.search(image):  # the size (STONE column) sits at the end of the image cell
        size = size or SIZE.search(image).group(0)
        image = SIZE.sub("", image).strip()
    status = " ".join(dict.fromkeys(m.lower() for m in STATUS.findall(image))) or r["STATUS"].strip()
    classes = {k: int(bool(re.search(rx, image, re.I))) for k, rx in CLASSES.items()}
    out.append({"section": r["section"], "nr": r["nr"], "signum": r["signum"], "signum_key": fold_signum(r["signum"]),
                "place": re.sub(r"^\s*\d{1,3}\.\s*", "", r["SIGLUM AND PLACE"]).replace("฀", "").strip(),
                "region": r["REGION"], "style": r["STYLE"], "period": r["PERIOD"], "carver": r["CARVER"],
                "image": image, "status": status, "monument_type": r["MONUMENT TYPE"].strip(), "size": size, **classes})
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(out[0]))
    w.writeheader()
    w.writerows(out)
with open(os.path.join(HERE, "stern_kontroll.txt"), "w", encoding="utf-8") as fh:
    fh.write(f"{len(out)} poster: " + ", ".join(f"{k} {v}" for k, v in Counter(r['section'] for r in out).items()) + "\n")
    for r in out:
        fh.write(f"{r['section']:11} {r['nr']:4} {r['signum']:16} {r['style'][:12]:12} {r['period'][:20]:20} | {r['image']}\n")
print(len(out), "poster;", dict(Counter(r["section"] for r in out)))
import random  # noqa: E402
random.seed(7)
with open(os.path.join(HERE, "stern_granskning.txt"), "w", encoding="utf-8") as fh:
    fh.write("30 slumpade poster: Sterns bildcell → våra kategorier (granska att kategorierna stämmer)\n\n")
    for r in random.sample(out, 30):
        fh.write(f"{r['section']:11} {r['signum']:14} | {r['image']}\n    → {', '.join(k for k in CLASSES if r[k]) or '(ingen kategori)'}\n")
from api.rundata import store  # noqa: E402
from src.research_gaps import is_runestone  # noqa: E402
S = {r["signum"]: r for r in store().inscriptions}
sv = [r for r in out if r["section"] in ("1.A", "1.A tillägg", "1.B") and r["signum"] in S and is_runestone(S[r["signum"]])
      and (S[r["signum"]].get("dating") or "").startswith("V")]
print(f"svenska vikingatida runstenar med bild (1.A+1.B): {len(sv)}; klasser:", {k: sum(r[k] for r in sv) for k in CLASSES})
print("klasser (alla poster):", {k: sum(r[k] for r in out) for k in CLASSES})
print("utan kategori:", sum(1 for r in out if not any(r[k] for k in CLASSES)), "t.ex.", [r["signum"] + ": " + r["image"][:40] for r in out if not any(r[k] for k in CLASSES)][:6])
print("tomma bilder:", [r["signum"] for r in out if not r["image"]][:12])
words = Counter(w for r in out for w in re.findall(r"[a-zA-Zðæ]+", r["image"].lower()) if len(w) > 2)
print("vanligaste bildord:", words.most_common(30))
