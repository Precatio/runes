"""Sotholms härad (låst plan analysplaner/2026-11-02-sotholm.md): skriver sotholm_stenar.csv för sotholm.R och en
beskrivning av stenarna (sotholm_beskrivning.json).
    PYTHONPATH=. .venv/bin/python utdata/sotholm/sotholm.py"""
import csv
import json
import os
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
M = os.path.join(ROOT, "utdata", "gamla_granser", "monster.py")
src = open(M).read()
g = {"__name__": "sotholm", "__file__": M}
exec(compile(src[:src.index('print("steg 1 Uppland")')], "monster_head", "exec"), g)
corpus = {r["signum"]: r for r in csv.DictReader(open(os.path.join(ROOT, "data", "cache", "r", "corpus", "7b9061c9a1c12c73", "corpus.csv")))}
feat = {r["signum"]: r for r in csv.DictReader(open(os.path.join(ROOT, "utdata", "upptackt_v3", "drag.csv")))}
rd = {r["signum"]: r for r in json.load(open(os.path.join(ROOT, "data", "rundata.json")))["inscriptions"]}
EXTRA = ["msg_resa", "msg_berom", "cat_arv", "cat_bro_vag", "msg_dod_borta", "kvinna_resare", "flera_resare"]
rows = []
for r in g["rows"]:
    if r["province"] != "Sö":
        continue
    c = corpus.get(r["signum"], {})
    f = feat[r["signum"]]
    rows.append({"signum": r["signum"], "harad": r["harad"] or "", "parish": r["parish"], "period": r["period"],
                 "year": "" if r["year"] is None else r["year"], "carver": c.get("carver", ""),
                 "carvers_all": c.get("carvers_all", ""), "moved": c.get("moved", ""), "lost": c.get("lost", ""),
                 "cat_kristen": "" if r["cat_kristen"] is None else r["cat_kristen"],
                 "pm_kors": "" if r["pm_kors"] is None else r["pm_kors"],
                 **{k: f.get(k, "") for k in EXTRA}})
with open(os.path.join(HERE, "sotholm_stenar.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader(); w.writerows(rows)
print("Sö-stenar", len(rows), Counter(r["harad"] for r in rows).most_common(12))

so = [r for r in rows if r["harad"] == "Sotholms hd"]
desc = {"n": len(so), "parishes": Counter(r["parish"] for r in so).most_common(),
        "carvers": Counter(r["carvers_all"] or "–" for r in so).most_common(),
        "periods": Counter(r["period"] for r in so).most_common(),
        "christian_stones": [r["signum"] for r in so if r["cat_kristen"] == 1],
        "cross_stones": [r["signum"] for r in so if r["pm_kors"] == 1],
        "shares": {k: [sum(1 for r in so if str(r[k]) in ("1", "1.0")), sum(1 for r in so if str(r[k]) not in ("",))] for k in ["cat_kristen", "pm_kors"] + EXTRA},
        "texts": {r["signum"]: (rd[r["signum"]].get("translation_sv") or rd[r["signum"]].get("translation_en") or "")[:300] for r in so if r["signum"] in rd}}
json.dump(desc, open(os.path.join(HERE, "sotholm_beskrivning.json"), "w"), ensure_ascii=False, indent=1)
print(json.dumps({k: desc[k] for k in ("n", "parishes", "carvers", "periods", "christian_stones", "shares")}, ensure_ascii=False))
