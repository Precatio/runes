"""Känslighetsprov utanför den låsta planen (märks så i redovisningen): steg 1 för Uppland utan draget mat_granit,
eftersom bergarten följer berggrunden och inte nödvändigtvis någon gräns människor drog.
    PYTHONPATH=. .venv/bin/python utdata/gamla_granser/monster_kanslighet.py"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "monster.py")).read()
g = {"__name__": "kanslighet", "__file__": os.path.join(HERE, "monster.py")}
exec(compile(src[:src.index('print("steg 1 Uppland")')], "monster_head", "exec"), g)
g["FEATS"].remove("mat_granit")
res = g["partition_test"]([r for r in g["rows"] if r["region"] in g["FOLK"]], g["FOLK"])
json.dump({"note": "utanför planen: steg 1 Uppland utan mat_granit", **res}, open(os.path.join(HERE, "monster_kanslighet.json"), "w"),
          ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False))
