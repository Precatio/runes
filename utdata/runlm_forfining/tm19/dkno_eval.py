"""Prövningen i analysplan_dkno.md (låst, e5e9f7c3…): slår ihop klass3_dkno_f0–f4 till klass3_dkno.json och prövar
de två kraven på de luckor Rundata har återställt, med samma listkalibrering som scripts/textmodel_candidates.py.
    .venv/bin/python utdata/runlm_forfining/tm19/dkno_eval.py"""
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from src import textmodel as tm  # noqa: E402
from textmodel_candidates import calibrated  # noqa: E402

D = os.path.dirname(os.path.abspath(__file__))
parts = [json.load(open(os.path.join(D, f"klass3_dkno_f{k}.json"), encoding="utf-8")) for k in range(5)]
rows = [r for p in parts for r in p["rows"]]
json.dump({"settings": parts[0]["settings"], "rows": rows}, open(os.path.join(D, "klass3_dkno.json"), "w"), ensure_ascii=False, indent=1)
sv = json.load(open(os.path.join(D, "klass3_alla.json"), encoding="utf-8"))["rows"]
GL = tm._records()["GL"]


def score(rs):
    val = [r for r in rs if r["status"] == "återställt"]
    for r in val:
        r["p_cal"] = calibrated(r, GL).get(r["word"], 0.0) if r.get("word") and r["word"] != "<unk>" else 0.0
    sure = [r for r in val if r["p_cal"] >= 0.8]
    return {"restored": len(val), "agree": sum(bool(r["agrees"]) for r in val) / max(1, len(val)),
            "sure_n": len(sure), "sure_agree": sum(bool(r["agrees"]) for r in sure) / max(1, len(sure)),
            "open": sum(r["status"] == "ej återställt" for r in rs)}


d, s = score(rows), score(sv)
by = {}
for pre in ("DR", "N"):
    by[pre] = score([r for r in rows if r["sig"].split()[0] == pre])
crit1 = d["sure_n"] >= 10 and d["sure_agree"] >= 0.75
crit2 = d["agree"] >= s["agree"] - 0.10
out = {"plan_sha256": "e5e9f7c3e598b698", "dk_no": d, "by_country": by, "sweden": s,
       "criterion_1": crit1, "criterion_2": crit2, "passed": crit1 and crit2}
json.dump(out, open(os.path.join(D, "dkno_resultat.json"), "w"), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False, indent=1))
