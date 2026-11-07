"""De norska runstenarna (låst plan analysplaner/2026-11-07-norska-runstenar.md, sha e275168c): H1 lät resa, H2 ihågkomna
kvinnor, H3 jord och arv (Norge mot Sverige, Fisher ensidigt, BH; robust mot svenska stenar ≤ 1050), H4 lät resa och
yrkesristare inom Sverige (Mantel–Haenszel över landskap × stilgrupp). Skriver resultat.json.
    PYTHONPATH=. .venv/bin/python utdata/norge/analys.py"""
import collections
import json
import os
import re
import sys

from scipy.stats import fisher_exact

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
from src import nordic as nd  # noqa: E402
from src.stats import wilson  # noqa: E402

PLAN = "analysplaner/2026-11-07-norska-runstenar.md"
SHA = open(os.path.join(ROOT, PLAN.replace(".md", ".sha256"))).read().split()[0]
assert SHA.startswith("e275168c")

FEMALE = ("wife", "mother", "daughter", "sister", "stepmother", "stepdaughter", "step-daughter", "foster-mother",
          "fostermother", "housewife", "mother-in-law", "daughter-in-law")
MALE = ("father", "son", "brother", "husband", "husbandman", "nephew", "uncle", "kinsman", "partner", "comrade", "lord",
        "foster-son", "fosterson", "foster-father", "fosterfather", "stepson", "stepfather", "son-in-law", "father-in-law",
        "brother-in-law", "grandson", "grandfather")
KIN_WORDS = "|".join(sorted((re.escape(w) for w in FEMALE + MALE), key=len, reverse=True))
KIN = re.compile(r"\b(?:in memory of|for the soul of|after)\b[^.;§]{0,60}?\b(?:his|her|their)\s+(?:\w+\s+)?(" + KIN_WORDS + r")\b", re.I)
LAND = re.compile(r"\ballodial\b|\binherit\w*|\bheirs?\b|\bdivided\b[^.;]{0,40}\bland\b|\bproperty\b|\bestate\b|\bowned all\b", re.I)

rd = json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["inscriptions"]
stones = [r for r in rd if nd.is_runestone(r)]


def country(r):
    L = nd.land_of(r)
    return L if L in ("norge", "danmark") else "sverige"


def province(r):
    return r["signum"].split()[0]


def code(r):
    """The plan's three codes for one stone, or None for an unreadable text."""
    ft = nd.features(r)
    if ft is None:
        return None
    tr = r.get("translation_en") or ""
    kin = [m.group(1).lower() for m in KIN.finditer(tr)]
    first = kin[0] if kin else None  # the first named relation is the commemorated person's
    return {"had": ft["had"], "kin": int(first is not None), "fem": int(first in FEMALE) if first else None,
            "land": int(bool(LAND.search(tr)))}


rows = []
for r in stones:
    c = code(r)
    if c is None:
        continue
    rows.append({"signum": r["signum"], "country": country(r), "prov": province(r), "year": nd.year_of(r),
                 "style": r.get("style") or "ingen", "carvers": [x.get("name") for x in (r.get("carvers") or []) if x.get("name")],
                 **c})


def share(rs, key, cond=None):
    rs = [x for x in rs if (cond is None or cond(x)) and x[key] is not None]
    k, n = sum(x[key] for x in rs), len(rs)
    lo, hi = wilson(k, n)
    return {"k": k, "n": n, "share": k / n if n else None, "ci": [lo, hi]}


def fisher(a, b, alt):
    t = [[a["k"], a["n"] - a["k"]], [b["k"], b["n"] - b["k"]]]
    odds, p = fisher_exact(t, alternative=alt)
    return {"or": odds, "p": p}


def bh(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    q, prev = [0.0] * len(ps), 1.0
    for rank, i in reversed(list(enumerate(order, 1))):
        prev = min(prev, ps[i] * len(ps) / rank)
        q[i] = prev
    return q


NO = [x for x in rows if x["country"] == "norge"]
SE = [x for x in rows if x["country"] == "sverige"]
DK = [x for x in rows if x["country"] == "danmark"]
SE_EARLY = [x for x in SE if x["year"] is not None and x["year"] <= 1050]
HYP = {"H1": ("had", "less"), "H2": ("fem", "greater"), "H3": ("land", "greater")}
res = {"plan": PLAN, "plan_sha": SHA, "n": {"norge": len(NO), "sverige": len(SE), "danmark": len(DK), "sverige_tidig": len(SE_EARLY)},
       "stones": {"norge": sum(1 for r in stones if country(r) == "norge"), "sverige": sum(1 for r in stones if country(r) == "sverige"),
                  "danmark": sum(1 for r in stones if country(r) == "danmark")}}
main = {}
for h, (key, alt) in HYP.items():
    a, b, e = share(NO, key), share(SE, key), share(SE_EARLY, key)
    main[h] = {"key": key, "alt": alt, "norge": a, "sverige": b, "sverige_tidig": e, "danmark": share(DK, key),
               "test": fisher(a, b, alt), "early": fisher(a, e, alt),
               "norway_hits": sorted(x["signum"] for x in NO if x[key] == 1)}
qs = bh([main[h]["test"]["p"] for h in HYP])
for h, q in zip(HYP, qs):
    m = main[h]
    m["q"] = q
    m["holds"] = q < 0.05
    m["robust"] = m["holds"] and m["early"]["p"] < 0.05
    # descriptive: against Denmark, Västergötland and each Swedish province with at least 30 readable stones
    provs = collections.Counter(x["prov"] for x in SE)
    m["descriptive"] = {"danmark": fisher(m["norge"], m["danmark"], "two-sided")}
    for p, n in provs.items():
        if n >= 30:
            s = share([x for x in SE if x["prov"] == p], m["key"])
            m["descriptive"][p] = {**s, **fisher(m["norge"], s, "two-sided")}
res["H1_H3"] = main

# H4: within Sweden, "had" and professional carvers (≥ 10 runestones in Rundata), strata province × style group
per_carver = collections.Counter(c for r in stones if country(r) == "sverige" for c in {x.get("name") for x in (r.get("carvers") or []) if x.get("name")})
PRO = {c for c, n in per_carver.items() if n >= 10}
for x in SE:
    x["pro"] = int(any(c in PRO for c in x["carvers"]))
strata = collections.defaultdict(lambda: [0, 0, 0, 0])
for x in SE:
    s = strata[(x["prov"], x["style"])]
    if x["had"]:
        s[0 if x["pro"] else 1] += 1
    else:
        s[2 if x["pro"] else 3] += 1
or_mh, p_mh, used = nd.mantel_haenszel([tuple(v) for v in strata.values()])
had = [x for x in SE if x["had"]]
nohad = [x for x in SE if not x["had"]]
res["H4"] = {"pro_carvers": len(PRO), "or_mh": or_mh, "p": p_mh, "strata_used": used,
             "holds": bool(or_mh and or_mh > 1 and p_mh < 0.05),
             "pro_share_had": share(had, "pro"), "pro_share_not_had": share(nohad, "pro"),
             "pro_share_sweden": share(SE, "pro")}
# descriptive: carvers with several stones in Norway (Rundata's carver field, and signatures in the text)
no_carvers = collections.Counter(c for r in stones if country(r) == "norge" for c in {x.get("name") for x in (r.get("carvers") or []) if x.get("name")})
res["H4"]["norway_carvers"] = dict(no_carvers)
res["H4"]["norway_signed"] = sorted(r["signum"] for r in stones if country(r) == "norge" and nd.features(r) and nd.features(r)["signatur"])
res["H4"]["top_swedish_carvers"] = per_carver.most_common(8)
# the Norwegian codes stone by stone, for the hand check
res["norway_codes"] = {x["signum"]: {k: x[k] for k in ("had", "kin", "fem", "land")} for x in NO}
json.dump(res, open(os.path.join(HERE, "resultat.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float)
for h in HYP:
    m = main[h]
    print(h, m["key"], f"Norge {m['norge']['k']}/{m['norge']['n']}", f"Sverige {m['sverige']['k']}/{m['sverige']['n']}",
          f"tidiga {m['sverige_tidig']['k']}/{m['sverige_tidig']['n']}", f"p {m['test']['p']:.2g} q {m['q']:.2g}",
          f"tidiga p {m['early']['p']:.2g}", "HÅLLER" if m["holds"] else "håller inte", "robust" if m["robust"] else "", m["norway_hits"])
h4 = res["H4"]
print("H4", f"yrkesristare {h4['pro_carvers']}", f"MH OR {h4['or_mh']:.2f} p {h4['p']:.2g} skikt {h4['strata_used']}",
      "HÅLLER" if h4["holds"] else "håller inte", f"andel yrkes bland lät {h4['pro_share_had']['share']:.2f} mot {h4['pro_share_not_had']['share']:.2f}")
print("Norge ristare:", h4["norway_carvers"], "signerade:", h4["norway_signed"])
