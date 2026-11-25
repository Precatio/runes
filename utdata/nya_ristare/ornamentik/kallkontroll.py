"""Källkontroll (analysplaner/2026-11-25-ornamentik-kallkontroll-teckningar.md): återger 1600–1700-talets teckningar
rundjurets drag? Teckningens konsensuskod jämförs med planschfotots (orn_koder.json) per fält och typ av teckning.
Skriver också konsensuskoderna för Gotlands och Ölands planscher (orn_koder_utvidgning.json, utanför det låsta provet).

    .venv/bin/python utdata/nya_ristare/ornamentik/kallkontroll.py
"""
import hashlib
import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)
from utdata.nya_ristare.ornamentik.m2 import consensus  # noqa: E402
from utdata.nya_ristare.ornamentik.overens import agreement, kappa  # noqa: E402

PLAN = os.path.join(ROOT, "analysplaner", "2026-11-25-ornamentik-kallkontroll-teckningar.md")
assert hashlib.sha256(open(PLAN, "rb").read()).hexdigest().startswith(open(PLAN + ".sha256").read()[:8]), "planen ändrad"
C = os.path.join(ROOT, "data", "cache", "hander", "ornamentik")
FIELDS = json.load(open(os.path.join(HERE, "m2_utveckling.json"), encoding="utf-8"))["godkända_fält"]
batches = json.load(open(os.path.join(C, "kallkontroll_batcher.json"), encoding="utf-8"))
typ = {(b["id"], s["sig"]): s.get("typ") for b in batches for s in b["stones"]}
runs = json.load(open(os.path.join(C, "kodning_kallkontroll.json"), encoding="utf-8"))
draw, plate = defaultdict(dict), defaultdict(dict)
dtyp = {}
for r in runs:
    for s in r["stenar"] or []:
        sig = s["signum"].strip()
        if r["batch"].startswith("t"):
            draw[sig][r["coder"]] = s
            dtyp[sig] = typ.get((r["batch"], sig))
        else:
            plate[sig][r["coder"]] = s
dc = consensus(draw)
pc = json.load(open(os.path.join(C, "orn_koder.json"), encoding="utf-8"))
reader = agreement(draw)


def compare(stones):
    out = {}
    for f in FIELDS:
        pairs = [(dc[s][f], pc[s][f]) for s in stones if s in dc and s in pc and f in dc[s] and f in pc[s]]
        k = kappa(pairs)
        n_have = sum(1 for s in stones if s in dc and f in dc[s])
        out[f] = {"jämförbara": len(pairs), "lika": round(sum(a == b for a, b in pairs) / len(pairs), 2) if pairs else None,
                  "kappa": round(k, 2) if k is not None else None,
                  "täckning_teckning": round(n_have / max(len(stones), 1), 2)}
    return out


types = sorted({t for t in dtyp.values() if t})
res = {"alla": compare(list(dtyp))}
for t in types:
    res[t] = compare([s for s, x in dtyp.items() if x == t])
use = {}
for t in types:
    ok = []
    for f in FIELDS:
        r = res[t][f] if res[t][f]["jämförbara"] >= 15 else res["alla"][f]
        if r["kappa"] is not None and r["kappa"] >= 0.40 and r["jämförbara"] >= 15:
            ok.append(f)
    use[t] = ok
ext = consensus(plate)
json.dump(ext, open(os.path.join(C, "orn_koder_utvidgning.json"), "w", encoding="utf-8"), ensure_ascii=False)
json.dump({"plan": os.path.basename(PLAN), "teckningar": len(dtyp), "per_typ": {t: sum(1 for x in dtyp.values() if x == t) for t in types},
           "läsarna_teckningar": reader, "teckning_mot_plansch": res, "fält_som_får_läsas": use,
           "gotland_öland_kodade": len(ext)},
          open(os.path.join(HERE, "kallkontroll.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for t in ["alla"] + types:
    print("==", t)
    for f in FIELDS:
        print(f"  {f:14s} {res[t][f]}")
print("får läsas:", json.dumps(use, ensure_ascii=False))
print("läsarna (teckningar):", {f: reader[f]["kappa"] for f in FIELDS})
print("Gotland/Öland kodade:", len(ext))
