"""Kontroll av blindprovet (blindprov.py) på ett oberoende sätt: för ett slumpvis urval stenar görs attribueringen
osynlig genom en djupkopia av korpusen utan stenens ristare och ett nybyggt sammanhang (stone_overview.context), i
stället för blindprovets tillfälliga ändring och justerade landskap. Status, förslag och styrka ska bli exakt desamma.
Dessutom räknas "närmaste ristare" och McNemars tal om från grunden.
    PYTHONPATH=. .venv/bin/python utdata/forslag/kontroll.py [korpusversion]"""
import copy
import json
import math
import os
import random
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
from scipy.stats import binomtest  # noqa: E402

from api.rundata import store  # noqa: E402
from api.routers.orthography import model as orthography_model  # noqa: E402
from src import stone_overview as so  # noqa: E402
from src.research_gaps import certain_carvers  # noqa: E402

B = json.load(open(os.path.join(ROOT, "utdata", "forslag", "blindprov.json"), encoding="utf-8"))
FP = sys.argv[1] if len(sys.argv) > 1 else B["corpus"]
RDIR = os.path.join(ROOT, "data", "cache", "r", "corpus", FP)
rows = {x["signum"]: x for x in B["rows"]}
ins = store().inscriptions
m = orthography_model()
by = {r["signum"]: i for i, r in enumerate(ins)}
OPEN = json.load(open(os.path.join(RDIR, "attribution.json"), encoding="utf-8"))["open_set"]
small = {x["signum"]: {x["top"]: x["p"]} for x in OPEN["small_carvers"]["stones"]}

rng = random.Random(2026)
sample = rng.sample(sorted(rows), 60)
mismatch = []
for s in sample:
    blind_ins = copy.deepcopy(ins)
    blind_ins[by[s]]["carvers"] = []
    ctx = so.context(blind_ins, m, RDIR)
    if s not in ctx["oof"] and s in small:
        ctx["pred"][s] = small[s]
    res = so.stone(blind_ins[by[s]], ctx)
    alt = res["alternative"] or {}
    x = rows[s]
    if (res["status"], alt.get("carver"), alt.get("strength")) != (x["status"], x["suggested"], x["strength"]):
        mismatch.append((s, (res["status"], alt.get("carver"), alt.get("strength")), (x["status"], x["suggested"], x["strength"])))
print(f"oberoende omräkning: {len(sample) - len(mismatch)} av {len(sample)} stämmer exakt", mismatch[:5])


def km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


# "Närmaste ristare" again, by a plain loop over all inscriptions with a certain carver (any object type is excluded
# by the same rule as blindprov.py: only runestones with a certain carver are in B["rows"])
pts = [(r["signum"], (r["lat"], r["lon"]), c) for r in ins
       if r["signum"] in rows and r.get("lat") is not None for c in certain_carvers(r)]
bad = 0
for s, xy, _ in pts:
    ds = [(km(xy, xy2), c) for s2, xy2, c in pts if s2 != s]
    dmin = min(d for d, _ in ds)
    near = sorted({c for d, c in ds if d - dmin < 1e-6})
    if near != sorted(rows[s]["nearest"]):
        bad += 1
print("närmaste ristare omräknad:", len(pts) - bad, "av", len(pts), "stämmer")

nytt = [x for x in B["rows"] if x["status"] == "nytt förslag"]
right = sum(x["suggested"] in x["truth"] for x in nytt)
hit = lambda x: bool(set(x["nearest"]) & set(x["truth"]))  # noqa: E731
near = sum(hit(x) for x in nytt)
b = sum(x["suggested"] in x["truth"] and not hit(x) for x in nytt)
c = sum(x["suggested"] not in x["truth"] and hit(x) for x in nytt)
print(f"nytt förslag: {right} av {len(nytt)} rätt, närmaste {near}; bara Vitki {b}, bara närmaste {c}, "
      f"McNemar p {binomtest(b, b + c, 0.5).pvalue:.2e}")
assert (right, len(nytt), near, b, c) == (B["nytt"]["right"], B["nytt"]["n"], B["nytt"]["nearest_right"],
                                          B["nytt"]["vitki_only"], B["nytt"]["nearest_only"])
print("sammanfattningen i blindprov.json stämmer med raderna")
