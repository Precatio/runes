"""Släktnätverket steg 2b (låst plan analysplaner/2026-11-01-slaktnatverket-generationer.md, sha 5fc275f0): den som
reser en sten lever då, så en sten där samma person står som död är rest senare. Följer stilgrupperna den ordningen?
En röst per person (medelrang på minnesstenarna mot resarstenarna), teckentest, sex steg. Skriver generationer.json.
    PYTHONPATH=. .venv/bin/python utdata/slakt/generationer.py"""
import json
import os
import random
import re
import statistics
import sys
from collections import defaultdict
from math import comb

OUT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(OUT, "..", ".."))
sys.path.insert(0, ROOT)
from src import linking as L  # noqa: E402
from src import styles  # noqa: E402

SE = ("U", "Sö", "Ög", "Vg", "Sm", "Öl", "G", "Nä", "Vs", "Gs", "Hs", "M", "J", "D", "Bo", "Vr")
RANK = {"RAK": 0, "Fp": 1, "FP": 1, "Pr1": 1, "Pr2": 2, "Pr3": 3, "Pr4": 4, "Pr5": 5}
SEED, N_PERM = 2026, 9999

rd = json.load(open(os.path.join(ROOT, "data", "rundata.json")))["inscriptions"]
st = {k: v for k, v in L.stones(rd).items() if k.split(" ")[0] in SE}
style_raw = {r["signum"]: r.get("style") for r in rd}


def style_rank(sg, firm_only=False):
    """(rang, mittår) för stenens stilgrupp; None för ?, KB, tomt – och för intervall när bara fasta räknas."""
    s = re.sub(r"\[.*?\]", "", style_raw.get(sg) or "").strip()
    if not s or "?" in s:
        return None
    parts = [p.strip() for p in s.split("-")]
    if not all(p in RANK for p in parts) or (firm_only and len(parts) > 1):
        return None
    mid = [(styles.BY_CODE["Fp" if p == "FP" else p]["from"] + styles.BY_CODE["Fp" if p == "FP" else p]["to"]) / 2
           for p in parts]
    return sum(RANK[p] for p in parts) / len(parts), sum(mid) / len(mid)


links = json.load(open(os.path.join(ROOT, "data", "links.json")))
SURE = [(x["a"], x["b"]) for x in links["links"]
        if x["q"] < links["fdr_cut"] and not x["contradictions"] and x["a"] in st and x["b"] in st]
assert len(SURE) == 61
W = json.load(open(os.path.join(OUT, "williams1990_bilaga.json")))["pairs"]
W_SURE = [(p["a"], p["b"]) for p in W if p["sure"] and p["a"] in st and p["b"] in st]
W_ALL = [(p["a"], p["b"]) for p in W if p["a"] in st and p["b"] in st]


def roles(sg):
    """namnnyckel -> roll på stenen; nycklar med två roller används inte."""
    r = defaultdict(set)
    for p in st[sg]["persons"]:
        if p["key"] in st[sg]["names"]:
            r[p["key"]].add(p["role"])
    return {k: next(iter(v)) for k, v in r.items() if len(v) == 1}


ROLES = {sg: roles(sg) for sg in st}


def nat(sg):
    pre, _, num = sg.partition(" ")
    m = re.match(r"(\d+)", num)
    return (pre, int(m.group(1)) if m else 10 ** 6, num)


def persons(pairs):
    """Personer (union–find över (sten, nyckel) i paren) och släkter (sammanhängande stenar)."""
    up, fam = {}, {}

    def f(d, x):
        d.setdefault(x, x)
        while d[x] != x:
            d[x] = d[d[x]]
            x = d[x]
        return x
    for a, b in pairs:
        fam[f(fam, a)] = f(fam, b)
        for k in set(ROLES[a]) & set(ROLES[b]):
            up[f(up, (a, k))] = f(up, (b, k))
    out = defaultdict(set)
    for node in list(up):
        out[f(up, node)].add(node)
    return [{"nodes": sorted(ns), "family": f(fam, next(iter(ns))[0])} for ns in out.values()], \
        {sg: f(fam, sg) for sg in list(fam)}


def votes(pairs, firm_only=False, rank=None):
    """En röst per person med minst en resarsten och en minnessten, båda med stilgrupp."""
    ps, fam = persons(pairs)
    out = []
    for p in ps:
        r = [(sg, k) for sg, k in p["nodes"] if ROLES[sg][k] == "resare"]
        m = [(sg, k) for sg, k in p["nodes"] if ROLES[sg][k] == "minnes"]
        rr = [(sg, style_rank(sg, firm_only)) for sg, _ in r]
        mm = [(sg, style_rank(sg, firm_only)) for sg, _ in m]
        rr = [(sg, x) for sg, x in rr if x]
        mm = [(sg, x) for sg, x in mm if x]
        if not rr or not mm:
            continue
        rk = rank or {}
        ra = statistics.mean(rk.get(sg, x[0]) for sg, x in rr)
        ma = statistics.mean(rk.get(sg, x[0]) for sg, x in mm)
        out.append({"person": sorted({k for _, k in p["nodes"]}), "family": p["family"],
                    "raised": [sg for sg, _ in rr], "remembered": [sg for sg, _ in mm],
                    "diff": ma - ra, "years": statistics.mean(x[1] for _, x in mm) - statistics.mean(x[1] for _, x in rr),
                    "vote": "senare" if ma > ra else "tidigare" if ma < ra else "lika"})
    return out, fam


def sign_p(k, n):
    """Ensidigt exakt teckentest: P(X ≥ k) för X ~ Bin(n, 1/2)."""
    return sum(comb(n, i) for i in range(k, n + 1)) / 2 ** n if n else 1.0


def summary(v):
    later = sum(x["vote"] == "senare" for x in v)
    earlier = sum(x["vote"] == "tidigare" for x in v)
    ties = sum(x["vote"] == "lika" for x in v)
    p = sign_p(later, later + earlier)
    return {"n": len(v), "later": later, "earlier": earlier, "ties": ties, "p": p, "holds": later > earlier and p < 0.05}


PRIMARY = W_SURE + SURE
v0, fam0 = votes(PRIMARY)
res = {"plan": "analysplaner/2026-11-01-slaktnatverket-generationer.md", "plan_sha": "5fc275f0", "corpus": "e83202e01a5e6d27",
       "n_pairs": {"williams_sure": len(W_SURE), "williams_all": len(W_ALL), "app_sure": len(SURE)},
       "primary": summary(v0), "steps": {}}

# 1 halves: families sorted by their smallest signum, alternately
fams = defaultdict(list)
for sg, root in fam0.items():
    fams[root].append(sg)
order = sorted(fams, key=lambda r: nat(min(fams[r], key=nat)))
half = {r: i % 2 for i, r in enumerate(order)}
h = [summary([x for x in v0 if half[x["family"]] == i]) for i in (0, 1)]
res["steps"]["1_halvor"] = {"halves": h, "holds": all(x["holds"] for x in h)}
# 2 Williams only
res["steps"]["2_bara_williams"] = summary(votes(W_SURE)[0])
# 3 without the Jarlabanke family
jr = fam0.get("U 164")
res["steps"]["3_utan_jarlabanke"] = summary([x for x in v0 if x["family"] != jr]) | {
    "family_stones": sorted(fams.get(jr, []), key=nat)}
# 4 firm style groups only
res["steps"]["4_bara_fasta"] = summary(votes(PRIMARY, firm_only=True)[0])
# 5 with Williams's uncertain (bracketed) pairs
res["steps"]["5_med_osakra"] = summary(votes(W_ALL + SURE)[0])
# 6 shuffle the style ranks among the stones used, within province
used = sorted({sg for x in v0 for sg in x["raised"] + x["remembered"]}, key=nat)
obs = res["primary"]["later"] - res["primary"]["earlier"]
by_prov = defaultdict(list)
for sg in used:
    by_prov[st[sg]["province"]].append(sg)
rng = random.Random(SEED)
ge = 0
for _ in range(N_PERM):
    rank = {}
    for sgs in by_prov.values():
        vals = [style_rank(sg)[0] for sg in sgs]
        rng.shuffle(vals)
        rank.update(zip(sgs, vals))
    pv = votes(PRIMARY, rank=rank)[0]
    ge += (sum(x["vote"] == "senare" for x in pv) - sum(x["vote"] == "tidigare" for x in pv)) >= obs
p6 = (ge + 1) / (N_PERM + 1)
res["steps"]["6_omblandning"] = {"observed": obs, "n_stones": len(used), "p": p6, "holds": p6 < 0.05}
res["all_hold"] = res["primary"]["holds"] and all(s["holds"] for s in res["steps"].values())
res["level"] = ("Fullt prövat" if res["all_hold"] else "Delvis prövat") if res["primary"]["holds"] else "negativt"

# descriptive
yrs = sorted(x["years"] for x in v0)
q = statistics.quantiles(yrs, n=4) if len(yrs) >= 4 else None
res["descriptive"] = {"share_ties": res["primary"]["ties"] / res["primary"]["n"],
                      "years_median": statistics.median(yrs), "years_quartiles": q,
                      "by_province": {pr: sum(1 for x in v0 if st[x["raised"][0]]["province"] == pr)
                                      for pr in sorted({st[x["raised"][0]]["province"] for x in v0})}}


def stone(sg):
    return {"signum": sg, "style": style_raw.get(sg), "carvers": st[sg]["carvers"], "parish": st[sg]["parish"]}


name = {(sg, p["key"]): p["name"] for sg in st for p in st[sg]["persons"]}
res["earlier_cases"] = [{"person": name.get((x["raised"][0], x["person"][0]), x["person"][0]),
                         "raised": [stone(s) for s in x["raised"]], "remembered": [stone(s) for s in x["remembered"]]}
                        for x in sorted(v0, key=lambda x: nat(x["raised"][0])) if x["vote"] == "tidigare"]
res["votes"] = [{k: x[k] for k in ("person", "raised", "remembered", "diff", "years", "vote")}
                for x in sorted(v0, key=lambda x: nat(x["raised"][0]))]
json.dump(res, open(os.path.join(OUT, "generationer.json"), "w"), ensure_ascii=False, indent=1)
print(json.dumps({k: res[k] for k in ("n_pairs", "primary", "steps", "all_hold", "level", "descriptive")},
                 ensure_ascii=False, indent=1))
for c in res["earlier_cases"]:
    print("TIDIGARE", c["person"], [(s["signum"], s["style"]) for s in c["raised"]], "->",
          [(s["signum"], s["style"]) for s in c["remembered"]])
