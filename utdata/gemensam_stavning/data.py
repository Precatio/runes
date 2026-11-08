"""Gemensam stavning (analysplaner/2026-11-08-gemensam-stavning.md, sha a49379aa): per sten de vanliga ordens stavning
(normaliserad form → translittererad stavning, src/orthography.features), land, stilgrupp och ristare. Skriver
stenar.json. Vanliga ord = normaliserade former på minst 10 stenar.
    .venv/bin/python utdata/gemensam_stavning/data.py"""
import json
import os
import sys
from collections import Counter

import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
from src import orthography  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS = os.path.join(ROOT, "data", "cache", "r", "corpus", "510ebfb3acc9a229", "corpus.csv")
EXCLUDE = {"Sk", "Hl", "Bl", "Bo"}  # Danish or Norwegian in the Viking age
MIN_STONES = 10
PRO = 10  # professional carver: at least 10 stones

c = pd.read_csv(CORPUS, low_memory=False)
c = c[~c.province.isin(EXCLUDE)]
recs = {r["signum"]: r for r in json.load(open(os.path.join(ROOT, "data", "rundata.json")))["inscriptions"]}
per_carver = Counter(c.carver.dropna())
stones = []
for row in c.itertuples():
    rec = recs.get(row.signum)
    if not rec:
        continue
    v = orthography.features(rec)["variants"]
    if not v:
        continue
    carver = row.carver if isinstance(row.carver, str) else None
    stones.append({"signum": row.signum, "land": row.region_old, "province": row.province,
                   "style": row.style if isinstance(row.style, str) else "utan", "carver": carver,
                   "pro": bool(carver and per_carver[carver] >= PRO), "words": v})
df = Counter(w for s in stones for w in s["words"])
common = sorted(w for w, n in df.items() if n >= MIN_STONES)
for s in stones:
    s["words"] = {w: sp for w, sp in s["words"].items() if w in set(common)}
stones = [s for s in stones if s["words"]]
out = {"plan_sha": "a49379aa", "corpus": "510ebfb3acc9a229", "common_words": common, "stones": stones,
       "n_aligned_stones": len(stones), "n_corpus": int(len(c))}
json.dump(out, open(os.path.join(HERE, "stenar.json"), "w", encoding="utf-8"), ensure_ascii=False)
print(len(c), "stenar i korpusen;", len(stones), "med vanliga ord parade;", len(common), "vanliga ord;",
      sum(len(s["words"]) for s in stones), "ordbelägg")
lands = Counter(s["land"] for s in stones)
print({k: v for k, v in lands.most_common() if v >= 30})
