"""Litteraturkontrollen och facit 2 (nya ristare): ställen i Fornvännen, Futhark och avhandlingarna där en ristare eller
samma hand nämns nära ett signum. Ställena läses sedan av språkmodellen (arbetsflödet), inte här.

    .venv/bin/python utdata/nya_ristare/litteratur_stallen.py
Skriver data/cache/hander/lit_stallen.json (utanför git: upphovsrättsskyddad text) och en sammanfattning.
"""
import glob
import json
import os
import re
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DL = "/Volumes/2TB/Antigrvity/Runes/downloads/tidskrifter"
OUT = os.path.join(ROOT, "data", "cache", "hander")

import pandas as pd  # noqa: E402

corp = pd.read_csv(os.path.join(ROOT, "data", "cache", "r", "corpus", "510ebfb3acc9a229", "corpus.csv"), low_memory=False)
names = sorted({re.sub(r"\s*\d+$", "", c).strip() for c in corp.carver.dropna() for c in str(c).split(";")
                if len(re.sub(r"\s*\d+$", "", c).strip()) >= 4})
names = [n for n in names if n.lower() not in {"okänd", "ristare"}]
CARVER = re.compile(
    r"samm[ae] (?:run)?ristare|samma hand|samme (?:man|mästare|runmästare|hånd|hand|ristar)|av samme|ristarens hand|"
    r"tillskriv|attribu|ristad av|ristat av|ristats av|huggen av|signer|same (?:rune[- ]?)?carver|same hand|carved by|"
    r"by the same|rune ?carver|runristare|ristaren|derselbe|gleichen? (?:Hand|Ritzer)|Runenmeister|"
    + "|".join(re.escape(n) for n in names), re.I)
SIG = re.compile(r"\b(U|Sö|Ög|Vg|Sm|Öl|Vs|Nä|Gs|Hs|Ån|Vr|D|M|J|G|DR|N)\s?(\d{1,4})\b")
W = 700


def windows(text):
    spans = []
    for m in CARVER.finditer(text):
        a, b = max(0, m.start() - W), min(len(text), m.end() + W)
        if SIG.search(text, a, b):
            if spans and a <= spans[-1][1]:
                spans[-1][1] = b
            else:
                spans.append([a, b])
    return spans


sources = []
for kind in ("fornvannen", "futhark"):
    idx = {}
    p = os.path.join(DL, kind, "index.jsonl")
    if os.path.exists(p):
        for l in open(p, encoding="utf-8"):
            r = json.loads(l)
            idx[r.get("key")] = r
    for f in sorted(glob.glob(os.path.join(DL, kind, "text", "*.txt"))):
        key = os.path.basename(f)[:-4]
        meta = idx.get(key, {})
        sources.append((f"{kind}:{key}", f, {"title": meta.get("title"), "authors": meta.get("authors"), "year": meta.get("year"),
                                               "licence": meta.get("licence")}))
for f in sorted(glob.glob(os.path.join(OUT, "lit", "*.txt"))):
    sources.append((f"avhandling:{os.path.basename(f)[:-4]}", f, {}))

out, per = [], Counter()
for sid, path, meta in sources:
    t = open(path, encoding="utf-8", errors="replace").read()
    t = re.sub(r"-\n\s*", "", t)
    t = re.sub(r"[ \t]+", " ", t)
    for a, b in windows(t):
        seg = t[a:b].replace("\n", " ")
        page = t.count("\f", 0, a) + 1
        out.append({"id": f"{sid}@{a}", "källa": sid, "sida_i_pdf": page, "meta": meta, "text": seg,
                    "signa": sorted({f"{m.group(1)} {m.group(2)}" for m in SIG.finditer(seg)})})
        per[sid.split(":")[0]] += 1
json.dump(out, open(os.path.join(OUT, "lit_stallen.json"), "w", encoding="utf-8"), ensure_ascii=False)
chars = sum(len(x["text"]) for x in out)
print(len(out), "ställen,", chars, "tecken,", dict(per))
grp = json.load(open(os.path.join(HERE, "grupper.json"), encoding="utf-8"))
gs = {s for g in grp for s in g["stenar"]}
hit = [x for x in out if set(x["signa"]) & gs]
print(len(hit), "ställen nämner minst en sten i grupperna;", len({s for x in hit for s in x["signa"] if s in gs}), "av", len(gs), "gruppstenar nämns")
