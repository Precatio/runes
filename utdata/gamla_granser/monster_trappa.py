"""Robusthetssteg för folklandsprovet (låst plan analysplaner/2026-11-02-folkland-slumpindelning-trappa.md): samma
slumpindelningsprov som steg 1 i monster.py på fyra urval av Upplands stenar. Skriver monster_trappa.json.
    PYTHONPATH=. .venv/bin/python utdata/gamla_granser/monster_trappa.py"""
import csv
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
src = open(os.path.join(HERE, "monster.py")).read()
head = src[:src.index('print("steg 1 Uppland")')]
corpus = {r["signum"]: r for r in csv.DictReader(open(os.path.join(ROOT, "data", "cache", "r", "corpus", "7b9061c9a1c12c73", "corpus.csv")))}
TOP5 = {"Öpir", "Fot", "Balle", "Åsmund", "Gunnar"}


def base(c):
    return {p.strip().rstrip("0123456789 ").strip() for p in (c.get("carvers_all") or c.get("carver") or "").split(";") if p.strip()}


STEPS = {
    "pa_plats": lambda r, c: c.get("moved") == "0",
    "utan_fem_ristare": lambda r, c: not (base(c) & TOP5),
    "daterade": lambda r, c: r["period"] != "odaterad",
    "utan_forlorade": lambda r, c: c.get("lost") == "0",
}
out = {"plan": "analysplaner/2026-11-02-folkland-slumpindelning-trappa.md", "steps": {}}
for name, keep in STEPS.items():
    g = {"__name__": "trappa", "__file__": os.path.join(HERE, "monster.py")}
    exec(compile(head, "monster_head", "exec"), g)   # fresh rng with the same seed → the same 999 partitions
    z = [r for r in g["rows"] if r["region"] in g["FOLK"] and r["signum"] in corpus and keep(r, corpus[r["signum"]])]
    print("steg", name, "stenar", len(z), flush=True)
    res = g["partition_test"](z, g["FOLK"])
    res["holds"] = res["alla"]["p"] < 0.05
    out["steps"][name] = res
    print(name, json.dumps({k: res[k] for k in ("stones", "features", "alla", "holds")}, ensure_ascii=False), flush=True)
    json.dump(out, open(os.path.join(HERE, "monster_trappa.json"), "w"), ensure_ascii=False, indent=1, default=float)
out["all_hold"] = all(s["holds"] for s in out["steps"].values())
json.dump(out, open(os.path.join(HERE, "monster_trappa.json"), "w"), ensure_ascii=False, indent=1, default=float)
print("alla håller", out["all_hold"])
