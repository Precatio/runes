"""Ornamentkoder för förlorade stenar ur 1500–1700-talets teckningar, med bara de fält som källkontrollen godkände per typ
av teckning (kallkontroll.json, "fält_som_får_läsas"). Varje kod märks med källa och tecknare.

    .venv/bin/python utdata/nya_ristare/ornamentik/forlorade.py JOURNAL
Skriver data/cache/hander/ornamentik/orn_koder_forlorade.json  {signum: {"koder": {...}, "källa": ..., "upphov": ...}}.
"""
import json
import os
import subprocess
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)
from utdata.nya_ristare.ornamentik.m2 import consensus  # noqa: E402
from utdata.nya_ristare.ornamentik.overens import agreement, by_stone  # noqa: E402

C = os.path.join(ROOT, "data", "cache", "hander", "ornamentik")
TYP = {"Bautil": "bautil", "Rhezelius": "rhezelius", "Peringskiöld": "peringskiold", "SRI-text": "ovrig"}
use = json.load(open(os.path.join(HERE, "kallkontroll.json"), encoding="utf-8"))["fält_som_får_läsas"]
meta = {s["sig"]: s for b in json.load(open(os.path.join(C, "forlorade_batcher.json"), encoding="utf-8")) for s in b["stones"]}
raw = os.path.join(C, "kodning_forlorade.json")
subprocess.run([sys.executable, os.path.join(HERE, "samla.py"), raw, sys.argv[1]], check=True)
codes = by_stone(raw)
cons = consensus(codes)
out = {}
for s, c in cons.items():
    m = meta.get(s, {})
    ok = use.get(TYP.get(m.get("källa"), "ovrig"), [])
    kept = {f: v for f, v in c.items() if f in ok}
    if kept:
        out[s] = {"koder": kept, "källa": m.get("källa"), "upphov": m.get("upphov")}
json.dump(out, open(os.path.join(C, "orn_koder_forlorade.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
agr = agreement(codes)
print(f"{len(meta)} förlorade stenar, {len(cons)} med bild, {len(out)} med minst en godkänd kod; "
      f"≥3 koder: {sum(1 for v in out.values() if len(v['koder']) >= 3)}")
print("läsarnas kappa:", {f: agr[f]["kappa"] for f in agr})
print("per källa:", dict(Counter(v["källa"] for v in out.values())))
