"""Beskrivande (efter den låsta planen, inget prov): vilka av de 25 dragen som bär folklandens skillnad i steg 1 – χ² och p
för folklandstermen per drag (drag ~ tidsskikt + folkland) bland Upplands stenar, och andelen per folkland. Underlag för
forskningsrapporten. Skriver monster_drag.json.
    PYTHONPATH=. .venv/bin/python utdata/gamla_granser/monster_drag.py"""
import json
import os
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "monster.py")).read()
g = {"__name__": "drag", "__file__": os.path.join(HERE, "monster.py")}
exec(compile(src[:src.index('print("steg 1 Uppland")')], "monster_head", "exec"), g)
z = [r for r in g["rows"] if r["region"] in g["FOLK"] and r["harad"]]
out = []
for f in g["FEATS"]:
    c = g["chi_group"](z, f, lambda r: r["region"])
    if c is None:
        continue
    sh = {L: (sum(r[f] for r in z if r["region"] == L and r[f] is not None), sum(1 for r in z if r["region"] == L and r[f] is not None)) for L in g["FOLK"]}
    out.append({"feature": f, "chi2": c[0], "p": c[1], "shares": sh})
out.sort(key=lambda o: -o["chi2"])
json.dump({"n_stones": len(z), "regions": dict(Counter(r["region"] for r in z)), "features": out},
          open(os.path.join(HERE, "monster_drag.json"), "w"), ensure_ascii=False, indent=1)
for o in out:
    print(f"{o['feature']:14} χ² {o['chi2']:6.1f} p {o['p']:.4f} " + "  ".join(f"{L[:5]} {k}/{n}" for L, (k, n) in o["shares"].items()))
