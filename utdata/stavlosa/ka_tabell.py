"""Runindelningen längs slingan på vanliga stenar: sammanställning av kor_ka.sh (de 37 KÅ-skanningarna, ritade slingor).
Per sten: textens runor (Rundata), runor som analysen hittar och mäter i vanligt läge (gamla streckklassningens
runnummer) och med indelningen längs slingan; mätsnitten är desamma i båda. Skriver ka_tabell.json.
    .venv/bin/python utdata/stavlosa/ka_tabell.py"""
import glob
import json
import math
import os
import statistics

HERE = os.path.dirname(os.path.abspath(__file__))
rows = []
for f in sorted(glob.glob(os.path.join(HERE, "resultat", "So_*__vanligt.json"))):
    g = f.replace("__vanligt.json", "__stavlost.json")
    if not os.path.exists(g):
        continue
    a, b = json.load(open(f)), json.load(open(g))
    assert a["runsnitt"] == b["runsnitt"] and a["godkanda"] == b["godkanda"], a["stem"]
    rows.append({"signum": a["signum"], "stem": a["stem"], "text": a["text_runor"], "snitt": a["runsnitt"],
                 "vanligt_hittade": a["runor_hittade"], "vanligt_matta": a["runor_matta"],
                 "slinga_hittade": b["runor_hittade"], "slinga_matta": b["runor_matta"]})
ok = [r for r in rows if r["text"] >= 10]
lr = lambda x, t: abs(math.log(max(x, 1) / t))  # noqa: E731
summ = {"stenar": len(rows), "med_minst_10_textrunor": len(ok)}
for k in ("vanligt_hittade", "vanligt_matta", "slinga_hittade", "slinga_matta"):
    summ[k] = {"kvot_median": statistics.median(r[k] / r["text"] for r in ok),
               "avvikelse_median_faktor": math.exp(statistics.median(lr(r[k], r["text"]) for r in ok)),
               "inom_25_procent": sum(0.75 <= r[k] / r["text"] <= 1.25 for r in ok)}
json.dump({"summary": summ, "stones": rows}, open(os.path.join(HERE, "ka_tabell.json"), "w"), ensure_ascii=False, indent=1)
print(json.dumps(summ, ensure_ascii=False, indent=1))
for r in rows:
    print(f"{r['signum']:12} text {r['text']:4}  vanligt {r['vanligt_hittade']:4}/{r['vanligt_matta']:4}  slinga {r['slinga_hittade']:4}/{r['slinga_matta']:4}  snitt {r['snitt']}")
