"""Huvudmodulen: utvärdering av piloten enligt analysplaner/2026-11-25-graslund-huvudmodul-pilot.md.

    .venv/bin/python utdata/graslund/huvud/utvardera.py JOURNAL
Skriver utdata/graslund/huvud/pilot.json och data/cache/hander/huvud/huvud_koder_pilot.json.
"""
import json
import os
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)
from utdata.nya_ristare.ornamentik.overens import kappa, norm  # noqa: E402

PILOT2 = "--pilot2" in sys.argv
F = ["huvud_vy", "oga", "nackflik", "lappflik", "mun", "nos", "svans", "fotter"]
label, r1, r2, r3 = {}, {}, {}, defaultdict(dict)
for line in open([a for a in sys.argv[1:] if not a.startswith("--")][0], encoding="utf-8"):
    e = json.loads(line)
    if e.get("type") == "started":
        label[e["key"]] = e.get("label", "")
    elif e.get("type") == "result" and isinstance(e.get("result"), dict):
        lab = label.get(e["key"], "")
        res = e["result"]
        if lab.endswith("-läsare1"):
            r1.update({s["signum"].strip(): s for s in res.get("stenar", [])})
        elif lab.endswith("-läsare2"):
            r2.update({s["signum"].strip(): s for s in res.get("stenar", [])})
        elif lab.endswith("-tredje"):
            for a in res.get("svar", []):
                r3[a["signum"].strip()][a["falt"]] = a["varde"]
final = {}
for s in r1:
    if s not in r2:
        continue
    c = {}
    for f in F:
        votes = [norm(r1[s].get(f)), norm(r2[s].get(f)), norm(r3.get(s, {}).get(f))]
        votes = [v for v in votes if v]
        top = Counter(votes).most_common(1)
        if top and top[0][1] >= 2:
            c[f] = top[0][0]
    final[s] = c
n = len(final)
cov = {f: round(sum(1 for c in final.values() if f in c) / n, 2) for f in F}
kap = {}
for f in F:
    pairs = [(norm(r1[s].get(f)), norm(r2[s].get(f))) for s in final if norm(r1[s].get(f)) and norm(r2[s].get(f))]
    k = kappa(pairs)
    kap[f] = {"par": len(pairs), "kappa": round(k, 2) if k is not None else None,
              "lika": round(sum(a == b for a, b in pairs) / len(pairs), 2) if pairs else None}
v2 = json.load(open(os.path.join(ROOT, "data", "cache", "hander", "ornamentik", "orn_koder.json"), encoding="utf-8"))
mot_v2 = {}
for f in ("huvud_vy", "oga"):
    pairs = [(final[s][f], v2[s][f]) for s in final if f in final[s] and f in v2.get(s, {})]
    mot_v2[f] = {"par": len(pairs), "lika": round(sum(a == b for a, b in pairs) / len(pairs), 2) if pairs else None}


def ok_k(f):
    k = kap[f]["kappa"]
    if k is not None and k >= 0.6:
        return True
    # pilot 2 (planen, bestämt före körningen): dominerar ett värde (≥ 90 % av paren) räcker andel lika ≥ 0,9
    if PILOT2:
        pairs = [(norm(r1[s].get(f)), norm(r2[s].get(f))) for s in final if norm(r1[s].get(f)) and norm(r2[s].get(f))]
        if pairs:
            top = Counter([a for a, _ in pairs] + [b for _, b in pairs]).most_common(1)[0][1] / (2 * len(pairs))
            return top >= 0.9 and (kap[f]["lika"] or 0) >= 0.9
    return False


regel = {"täckning_flikar": cov["nackflik"] >= 0.6 and cov["lappflik"] >= 0.6,
         "kappa_huvud": all(ok_k(f) for f in ("huvud_vy", "oga", "nackflik", "lappflik")),
         "mot_v2": all((mot_v2[f]["lika"] or 0) >= 0.8 for f in mot_v2)}
regel["håller"] = all(regel.values())
out = {"stenar": n, "täckning": cov, "läsare1_mot_2": kap, "mot_v2": mot_v2, "tredje_läsaren_fält": sum(len(v) for v in r3.values()),
       "regel": regel, "fördelning": {f: dict(Counter(c.get(f) for c in final.values() if f in c)) for f in F}}
json.dump(final, open(os.path.join(ROOT, "data", "cache", "hander", "huvud", "huvud_koder_pilot2.json" if PILOT2 else "huvud_koder_pilot.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=0)
json.dump(out, open(os.path.join(HERE, "pilot2.json" if PILOT2 else "pilot.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False, indent=1))
