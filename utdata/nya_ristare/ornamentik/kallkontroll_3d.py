"""Källkontroll för djupbilder och ornamentkoder för Hälsingland och Medelpad
(analysplaner/2026-11-25-ornamentik-3d-halsingland-medelpad.md).

    .venv/bin/python utdata/nya_ristare/ornamentik/kallkontroll_3d.py JOURNAL
Skriver kallkontroll_3d.json och lägger Hs/M-koderna i data/cache/hander/ornamentik/orn_koder_utvidgning.json.
"""
import hashlib
import json
import os
import subprocess
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)
from utdata.nya_ristare.ornamentik.m2 import consensus  # noqa: E402
from utdata.nya_ristare.ornamentik.overens import agreement, kappa  # noqa: E402

PLAN = os.path.join(ROOT, "analysplaner", "2026-11-25-ornamentik-3d-halsingland-medelpad.md")
assert hashlib.sha256(open(PLAN, "rb").read()).hexdigest().startswith(open(PLAN + ".sha256").read()[:8]), "planen ändrad"
C = os.path.join(ROOT, "data", "cache", "hander", "ornamentik")
FIELDS = json.load(open(os.path.join(HERE, "m2_utveckling.json"), encoding="utf-8"))["godkända_fält"]
raw = os.path.join(C, "kodning_djup_hsm.json")
subprocess.run([sys.executable, os.path.join(HERE, "samla.py"), raw, sys.argv[1]], check=True)
meta = {s["sig"]: s for b in json.load(open(os.path.join(C, "djup_hsm_batcher.json"), encoding="utf-8")) for s in b["stones"]}
d3, hm = defaultdict(dict), defaultdict(dict)
for r in json.load(open(raw, encoding="utf-8")):
    for s in r["stenar"] or []:
        (d3 if r["batch"].startswith("d") else hm)[s["signum"].strip()][r["coder"]] = s
dc = consensus(d3)
pc = json.load(open(os.path.join(C, "orn_koder.json"), encoding="utf-8"))
res = {}
for f in FIELDS:
    pairs = [(dc[s][f], pc[s][f]) for s in d3 if s in dc and s in pc and f in dc[s] and f in pc[s]]
    k = kappa(pairs)
    res[f] = {"jämförbara": len(pairs), "lika": round(sum(a == b for a, b in pairs) / len(pairs), 2) if pairs else None,
              "kappa": round(k, 2) if k is not None else None,
              "täckning_djupbild": round(sum(1 for s in d3 if s in dc and f in dc[s]) / max(len(d3), 1), 2)}
ok3d = [f for f in FIELDS if res[f]["kappa"] is not None and res[f]["kappa"] >= 0.40 and res[f]["jämförbara"] >= 15]
hc = consensus(hm)
ext_path = os.path.join(C, "orn_koder_utvidgning.json")
ext = json.load(open(ext_path, encoding="utf-8"))
added = {}
for s, c in hc.items():
    allowed = FIELDS if meta.get(s, {}).get("foto") else ok3d
    kept = {f: v for f, v in c.items() if f in allowed}
    if kept:
        ext[s] = kept
        added[s] = {"fält": len(kept), "bild": "foto + djupbild" if meta.get(s, {}).get("foto") else "bara djupbild"}
json.dump(ext, open(ext_path, "w", encoding="utf-8"), ensure_ascii=False)
out = {"plan": os.path.basename(PLAN), "källkontroll_stenar": len(d3), "läsarna_djupbild": {f: agreement(d3)[f]["kappa"] for f in FIELDS},
       "djupbild_mot_plansch": res, "fält_som_får_läsas_ur_djupbild": ok3d,
       "hs_m": {"kodade": len(hc), "med_godkänd_kod": len(added), "stenar": added}}
json.dump(out, open(os.path.join(HERE, "kallkontroll_3d.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for f in FIELDS:
    print(f"  {f:14s} {res[f]}")
print("får läsas ur djupbild:", ok3d)
print("läsarna (djupbild):", out["läsarna_djupbild"])
print("Hs/M:", json.dumps(out["hs_m"], ensure_ascii=False))
