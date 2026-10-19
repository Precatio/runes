"""Hávamál ur Guðni Jónssons utgåva (Codex Regius-texten, via heimskringla.no; samma fil som runlm:s Edda-
ordförråd) förberedd för R-analysen: en rad per strof med utgåvans sexdelning (I–VI), texten, versmåttsproxyn
(utgåvans kommatering bevarar versgränserna fast radbrytningarna gått förlorade) och andelen ordtyper med
vikingatida runbelägg – orden slås ihop över normaliseringarna med runlm.key, så att steinn och stæinn räknas
som samma ord. Skriver havamal_strofer.csv.
    PYTHONPATH=. .venv/bin/python utdata/Edda/havamal_prep.py"""
import csv
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
from src import runlm as rl  # noqa: E402

raw = json.load(open(os.path.join(ROOT, "utdata/Malt/kallor/edda.json")))["Hávamál"]
raw = raw.split("Hávamál", 1)[1]  # utgåvans sidhuvud bort

# utgåvans delar: romerska siffror I.–VI. står före sin första strof
parts = re.split(r"\s(I{1,3}\.|IV\.|V\.|VI\.)\s", " " + raw)
sections, cur = {}, None
order = []
for piece in parts:
    if re.fullmatch(r"(I{1,3}|IV|V|VI)\.", piece):
        cur = piece.rstrip(".")
        order.append(cur)
    elif cur:
        sections[cur] = sections.get(cur, "") + " " + piece
assert order == ["I", "II", "III", "IV", "V", "VI"], order

# vikingatida runbelägg: alla normaliserade ord i Rundatas vikingatida inskrifter, kanoniserade med runlm.key
recs = [r for r in rl.load_rundata() if rl.viking(r)]
runic = set()
for r in recs:
    for w in rl.norm_words(r.get("normalization") or ""):
        runic.add(rl.key(rl.normtok(w)))

STOP_CHARS = ".,;:!?\"'()[]-–—"
rows = []
for sec in order:
    for m in re.finditer(r"(?<!\d)(\d{1,3})\.\s(.*?)(?=(?<!\d)\d{1,3}\.\s|$)", sections[sec], re.S):
        nr, text = int(m.group(1)), " ".join(m.group(2).split())
        segs = [s.strip() for s in re.split(r"[,;:]", text) if s.strip()]
        toks = [t.strip(STOP_CHARS).lower() for t in text.split()]
        toks = [t for t in toks if t and re.fullmatch(r"[a-zþðæöøáéíóúýœå]+", t)]
        types = {rl.key(t) for t in toks}
        attested = sum(1 for t in types if t in runic)
        rows.append({"nr": nr, "del": sec, "text": text, "n_ord": len(toks), "n_segment": len(segs),
                     "medel_segment": round(sum(len(s.split()) for s in segs) / len(segs), 2) if segs else 0,
                     "ordtyper": len(types), "runbelagda": attested,
                     "andel_runbelagd": round(attested / len(types), 3) if types else 0})
rows.sort(key=lambda r: r["nr"])
assert [r["nr"] for r in rows] == list(range(1, 165)), f"strofnummer: {len(rows)}"
out = os.path.join(ROOT, "utdata", "Edda", "havamal_strofer.csv")
with open(out, "w", encoding="utf-8", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
print(out, len(rows), "strofer | delar:",
      {sec: f"{min(r['nr'] for r in rows if r['del']==sec)}–{max(r['nr'] for r in rows if r['del']==sec)}" for sec in order})
print("andel runbelagda ordtyper per del:",
      {sec: round(sum(r['runbelagda'] for r in rows if r['del']==sec) / max(1, sum(r['ordtyper'] for r in rows if r['del']==sec)), 3) for sec in order})
