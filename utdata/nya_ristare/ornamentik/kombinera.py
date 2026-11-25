"""Gamla teckningar fyller luckor i planschkoderna (analysplaner/2026-11-25-teckningar-fyller-luckor.md).

    .venv/bin/python utdata/nya_ristare/ornamentik/kombinera.py JOURNAL
Skriver data/cache/hander/ornamentik/orn_koder_kombinerade.json {signum: {fält: {"värde", "källa"}}} och
utdata/nya_ristare/ornamentik/kombinera.json (täckning före/efter per stilgrupp).
"""
import json
import os
import subprocess
import sys
from collections import defaultdict

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)
from utdata.nya_ristare.ornamentik.m2 import consensus  # noqa: E402
from utdata.nya_ristare.ornamentik.overens import by_stone  # noqa: E402

C = os.path.join(ROOT, "data", "cache", "hander", "ornamentik")
TYP = {"Bautil": "bautil", "Rhezelius": "rhezelius", "Peringskiöld": "peringskiold", "SRI-text": "ovrig"}
FIELDS = json.load(open(os.path.join(HERE, "m2_utveckling.json"), encoding="utf-8"))["godkända_fält"]
use = json.load(open(os.path.join(HERE, "kallkontroll.json"), encoding="utf-8"))["fält_som_får_läsas"]
meta = {s["sig"]: s for b in json.load(open(os.path.join(C, "luckor_batcher.json"), encoding="utf-8")) for s in b["stones"]}
raw = os.path.join(C, "kodning_luckor.json")
subprocess.run([sys.executable, os.path.join(HERE, "samla.py"), raw, sys.argv[1]], check=True)
draw = consensus(by_stone(raw))
plate = json.load(open(os.path.join(C, "orn_koder.json"), encoding="utf-8"))
comb = {s: {f: {"värde": v, "källa": "SRI-plansch"} for f, v in c.items()} for s, c in plate.items()}
filled = defaultdict(int)
for s, c in draw.items():
    m = meta.get(s, {})
    ok = use.get(TYP.get(m.get("källa"), "ovrig"), [])
    for f, v in c.items():
        if f in ok and f not in comb.get(s, {}):
            comb.setdefault(s, {})[f] = {"värde": v, "källa": f"teckning: {m.get('upphov') or m.get('källa')}"}
            filled[f] += 1
json.dump(comb, open(os.path.join(C, "orn_koder_kombinerade.json"), "w", encoding="utf-8"), ensure_ascii=False)
corp = pd.read_csv(os.path.join(ROOT, "data", "cache", "r", "corpus", "510ebfb3acc9a229", "corpus.csv"), low_memory=False)
style = dict(zip(corp.signum, corp["style"].astype(str).str.replace("\xa0", " ").str.replace(" ", "")))
cov = {}
for g in ["Pr1", "Pr2", "Pr3", "Pr4", "Pr5"]:
    ss = [s for s in plate if style.get(s) == g and plate[s].get("djurhuvud") == "ja"]
    cov[g] = {"stenar": len(ss)}
    for f in ("nackflik", "oga", "svans", "koppel"):
        cov[g][f] = {"före": round(sum(f in plate[s] for s in ss) / max(len(ss), 1), 2),
                     "efter": round(sum(f in comb[s] for s in ss) / max(len(ss), 1), 2)}
out = {"teckningar_kodade": len(draw), "ifyllda_värden": dict(filled), "täckning_per_stilgrupp": cov}
json.dump(out, open(os.path.join(HERE, "kombinera.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False, indent=1))
