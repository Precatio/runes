"""Landrättelsen 2026-11-05: vilka stenar som bytte (eller fick) vikingatida land när web/public/geo/sten_land.json byggdes om
med sockens medeltida härad efter Det medeltida Sverige 1:7 (web/src/lib/historiska_land.json → parish_medieval) och de
två reglerna i scripts/assign_sten_land.py ("(nu …)" stryks; en sten flyttad långt från sin unika socken knyts till den).
Före = sten_land.json i commit 461dca4 (sista commit före rättelsen), efter = filen i arbetskopian. Räknar stenarna i
dragtabellen (utdata/upptackt_v3/drag.csv, vikingatida runstenar, korpus e83202e0) och alla Rundata-signum. Skriver
landrattelse.json, som forskningsrapporten läser.
    PYTHONPATH=. .venv/bin/python utdata/folkland/landrattelse.py"""
import csv
import json
import os
import subprocess
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
from src import linking as L  # noqa: E402

BEFORE_COMMIT = "461dca4"
before = json.loads(subprocess.run(["git", "-C", ROOT, "show", f"{BEFORE_COMMIT}:web/public/geo/sten_land.json"],
                                   capture_output=True, text=True, check=True).stdout)
after = json.load(open(os.path.join(ROOT, "web", "public", "geo", "sten_land.json"), encoding="utf-8"))
hl = json.load(open(os.path.join(ROOT, "web", "src", "lib", "historiska_land.json"), encoding="utf-8"))
st = L.stones(json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["inscriptions"])
drag = {r["signum"] for r in csv.DictReader(open(os.path.join(ROOT, "utdata", "upptackt_v3", "drag.csv"), encoding="utf-8"))}
FOLK = ["tiundaland", "attundaland", "fjadrundaland", "roden"]
FARINGO = ["Sånga sn", "Lovö sn", "Hilleshögs sn", "Skå sn", "Munsö sn", "Färentuna sn"]


def group(x):
    p = x["parish"] or ""
    return "faringo" if p in FARINGO else "adelso" if p == "Adelsö sn" else "ekero" if p == "Ekerö sn" else "ovriga"


def counts(sl, keep):
    c = Counter(sl.get(sg) or "inget" for sg, x in st.items() if x["province"] == "U" and keep(sg))
    return {k: c[k] for k in FOLK + ["inget"]}


changed = [{"signum": sg, "parish": x["parish"], "before": before.get(sg), "after": after.get(sg), "in_drag": sg in drag}
           for sg, x in sorted(st.items()) if before.get(sg) != after.get(sg)]
dropped = [(sg, x) for sg, x in st.items() if x["province"] == "U" and sg in drag and sg not in before]
out = {
    "before_commit": BEFORE_COMMIT,
    "drag": {"before": counts(before, lambda sg: sg in drag), "after": counts(after, lambda sg: sg in drag)},
    "all_signa": {"before": counts(before, lambda sg: True), "after": counts(after, lambda sg: True)},
    "dropped_before": {"n": len(dropped),
                       "by_group": dict(Counter(group(x) for _, x in dropped)),
                       "faringo_by_parish": dict(Counter(x["parish"] for _, x in dropped if group(x) == "faringo")),
                       "ovriga": sorted(sg for sg, x in dropped if group(x) == "ovriga"),
                       "after": {sg: after.get(sg) for sg, _ in sorted(dropped)}},
    "changed": changed,
    "parish_medieval": {v["namn"]: v["harad"] for v in hl["parish_medieval"]["socknar"].values()},
}
json.dump(out, open(os.path.join(HERE, "landrattelse.json"), "w"), ensure_ascii=False, indent=1)
print(json.dumps({k: out[k] for k in ("drag", "all_signa")}, ensure_ascii=False))
print(json.dumps(out["dropped_before"], ensure_ascii=False))
print(len(changed), "signum bytte land:", [(c["signum"], c["before"], c["after"]) for c in changed if c["before"]])
