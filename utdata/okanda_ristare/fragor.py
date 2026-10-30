"""Underlag för avsnittet "Tre frågor till runologerna" (beskrivande, efter artikeln; inga låsta planer, 2026-10-30):
formeln satti stæin i Husabygruppen mot Västergötlands runstenar inom 30 km, och stenarnas texter i de tre grupperna.
Likheten mellan grupperna och de signerade grannstenarna räknas i signerade_grannar.R.
    .venv/bin/python utdata/okanda_ristare/fragor.py      Skriver fragor.json."""
import json
import math
import os
import re
import sys

from scipy.stats import fisher_exact

OUT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(OUT, "..", ".."))
sys.path.insert(0, ROOT)
from api.rundata import store  # noqa: E402
from src.research_gaps import is_runestone, province  # noqa: E402

AN = json.load(open(os.path.join(ROOT, "data", "cache", "r", "corpus", "3f58e9339191761e", "anonymous.json"), encoding="utf-8"))
GROUPS = {g["id"]: g for g in AN["groups"]}
recs = {r["signum"]: r for r in store().inscriptions if is_runestone(r)}


def km(a, b):
    la, lb = math.radians(a["lat"]), math.radians(b["lat"])
    c = math.sin(la) * math.sin(lb) + math.cos(la) * math.cos(lb) * math.cos(math.radians(a["lon"] - b["lon"]))
    return 6371 * math.acos(min(1.0, c))


SATTI = re.compile(r"\bsatt[iu]\b")
grp = GROUPS[13]["stones"]
vg = [r for r in recs.values() if province(r) == "Vg" and r.get("lat")]
local = [r for r in vg if r["signum"] not in grp and min(km(r, recs[g]) for g in grp) <= 30]
g_satti = [s for s in grp if SATTI.search(recs[s]["normalization"] or "")]
l_satti = [r["signum"] for r in local if SATTI.search(r["normalization"] or "")]
odds, p = fisher_exact([[len(g_satti), len(grp) - len(g_satti)], [len(l_satti), len(local) - len(l_satti)]])
res = {"husaby_satti": {"group": len(g_satti), "n_group": len(grp), "local": len(l_satti), "n_local": len(local),
                        "p": p, "stones": g_satti},
       "texts": {k: {s: recs[s]["normalization"] for s in GROUPS[k]["stones"]} for k in (2, 5, 13)}}
json.dump(res, open(os.path.join(OUT, "fragor.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(res["husaby_satti"])
