"""Kontroll UTANFÖR den låsta planen (redovisas så): håller fynden i gravskick och ortnamn när enheten bara jämförs med
resten av sitt landskap INOM SAMMA LÄN? Fornlämningsregistret har inventerats och beskrivits länsvis, och Småland och
Uppland delas av flera län, så en skillnad mellan landen kan vara en skillnad mellan inventeringar. Skriver
lanskontroll.json och lägger till "inom_lan" på varje hållande gravskick-/ortnamnsfynd.
    PYTHONPATH=. .venv/bin/python utdata/landprofiler/lanskontroll.py"""
import csv
import json
import math
import os
from collections import Counter

from scipy.stats import chi2

HERE = os.path.dirname(os.path.abspath(__file__))
SPLIT = {"U", "Sm", "G"}


def g_test(k1, n1, k0, n0):
    def ll(k, n):
        return (k * math.log(k / n) if k else 0) + ((n - k) * math.log((n - k) / n) if n - k else 0)
    return float(chi2.sf(max(2 * (ll(k1, n1) + ll(k0, n0) - ll(k1 + k0, n1 + n0)), 0), 1))


R = json.load(open(os.path.join(HERE, "landprofiler.json")))
tabs = {"gravskick": list(csv.DictReader(open(os.path.join(HERE, "gravar.csv")))),
        "ortnamn": list(csv.DictReader(open(os.path.join(HERE, "namn.csv"))))}
out = []
for t in R["tests"]:
    if not t["holds"] or t["domain"] not in tabs:
        continue
    rows = [r for r in tabs[t["domain"]] if r["province"] == t["province"]]
    zi = [r for r in rows if (r["region"] if t["kind"] == "land" else r["harad"]) == t["unit"]]
    county = Counter(r["county"] for r in zi).most_common(1)[0][0]
    if t["kind"] == "land":
        ctx = rows
    else:
        reg = Counter(r["region"] for r in zi).most_common(1)[0][0]
        ctx = [r for r in rows if r["region"] == reg] if (t["province"] in SPLIT and reg != t["province"]) else rows
    ids = {id(r) for r in zi}
    zi_c = [r for r in zi if r["county"] == county and r[t["feature"]] != ""]
    zo_c = [r for r in ctx if r["county"] == county and id(r) not in ids and r[t["feature"]] != ""]
    f = t["feature"]
    if len(zo_c) < 30 or len(zi_c) < 30:
        t["inom_lan"] = {"county": county, "result": "kan inte prövas", "n_in": len(zi_c), "n_out": len(zo_c)}
    else:
        k1 = sum(int(r[f]) for r in zi_c); k0 = sum(int(r[f]) for r in zo_c)
        p = g_test(k1, len(zi_c), k0, len(zo_c)) if 0 < k1 + k0 < len(zi_c) + len(zo_c) else 1.0
        same = (k1 / len(zi_c) > k0 / len(zo_c)) == (t["share_in"] > t["share_out"])
        t["inom_lan"] = {"county": county, "n_in": len(zi_c), "n_out": len(zo_c), "share_in": k1 / len(zi_c),
                         "share_out": k0 / len(zo_c), "p": p, "result": "håller" if (p < 0.05 and same) else "håller inte"}
    out.append(t)
json.dump(R, open(os.path.join(HERE, "landprofiler.json"), "w"), ensure_ascii=False, indent=0, default=float)
c = Counter((t["domain"], t["inom_lan"]["result"]) for t in out)
print(sorted(c.items()))
