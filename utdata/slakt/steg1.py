"""Släktnätverket, steg 1, enligt den låsta planen analysplaner/2026-11-01-slaktnatverket-steg1.md: M0 (appens länkmodell)
och M1 (nollmodell inom häradet, q per avståndsband) på de svenska runstenarna, prövade mot Williams 1990, Jarlabanke och
motsägelserna; beskrivning, känslighet och den utforskande M1b. Skriver steg1.json.
    PYTHONPATH=. .venv/bin/python utdata/slakt/steg1.py"""
import json
import os
import sys
from collections import Counter, defaultdict
from itertools import combinations

import numpy as np

OUT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(OUT, "..", ".."))
sys.path.insert(0, ROOT)
from src import linking as L  # noqa: E402

SEED, N_NULL, CUT = 2026, 2000, L.FDR_CUT
SE = ("U", "Sö", "Ög", "Vg", "Sm", "Öl", "G", "Nä", "Vs", "Gs", "Hs", "M", "J", "D", "Bo", "Vr")
WPROV = {"Ög", "Sö", "Sm", "Vg", "U", "Vs", "Hs"}
JARLABANKE = ("U 127", "U 164", "U 165", "U 212", "U 261")
PLAN = "analysplaner/2026-11-01-slaktnatverket-steg1.md"
assert open(os.path.join(ROOT, PLAN.replace(".md", ".sha256"))).read().startswith("403fa352cc19e0f2")

ins = json.load(open(os.path.join(ROOT, "data", "rundata.json")))["inscriptions"]
ALL = {k: v for k, v in L.stones(ins).items() if k.split(" ")[0] in SE}
assert len(ALL) == 2320
W = json.load(open(os.path.join(OUT, "williams1990_bilaga.json"), encoding="utf-8"))


def band_of(d, edges):
    if d is None:
        return "utan koordinater"
    a, b = edges
    return "A" if d <= a else ("B" if d <= b else "C")


def km_of(st, a, b, cache={}):
    k = (a, b)
    if k not in cache:
        cache[k] = L.km(st[a], st[b])
    return cache[k]


def null_links(st, w, level, n=N_NULL, seed=SEED, single_rare=None):
    """Like L.null_scores but keeps the stones of every null link, so that each can be given its distance band."""
    rng = np.random.default_rng(seed)
    grp = defaultdict(list)
    for sg, s in st.items():
        grp[s["province"] if level == "province" else (s["province"], s.get("district") or s["parish"])].append(sg)
    groups_ = [(sgs, [len(st[sg]["names"]) for sg in sgs], [k for sg in sgs for k in sorted(st[sg]["names"])]) for sgs in grp.values()]
    out, left = [], 0
    for _ in range(n):
        ts = {}
        for sgs, sizes, names in groups_:
            lists, lo = L._draw(sizes, list(names), rng)
            left += lo
            for sg, li in zip(sgs, lists):
                ts[sg] = set(li) | {"plats:" + p for p in st[sg]["places"]}
        ls = L.links(st, w, ts) + (extra_links(st, w, ts, single_rare) if single_rare else [])
        out.append([(x["score"], km_of(st, x["a"], x["b"])) for x in ls])
    return out, left


def extra_links(st, w, ts, rule):
    """M1b: pairs within rule['km'] that share exactly one personal name standing on at most rule['max'] stones."""
    n = Counter(k for t in ts.values() for k in t)
    index = defaultdict(list)
    for sg, t in ts.items():
        for k in t:
            if not k.startswith("plats:") and n[k] <= rule["max"]:
                index[k].append(sg)
    out = []
    for k, sgs in index.items():
        for a, b in combinations(sorted(sgs), 2):
            sh = ts[a] & ts[b]
            if len(sh) == 1 and not any(x.startswith("plats:") for x in sh):
                d = km_of(st, a, b)
                if d is not None and d <= rule["km"]:
                    out.append({"a": a, "b": b, "shared": sorted(sh), "score": round(w.get(k, 0.0), 3)})
    return out


def q_banded(obs, null, edges):
    for x in obs:
        x["band"] = band_of(km_of(ST, x["a"], x["b"]), edges)
    for bd in ("A", "B", "C", "utan koordinater"):
        o = [x for x in obs if x["band"] == bd]
        z = [np.array([s for s, d in rep if band_of(d, edges) == bd]) for rep in null]
        if o:
            L.fdr(o, z, seed=SEED)


def finish(obs, st, sex):
    for x in obs:
        x["contradictions"] = L.contradictions(x, st, sex)
    sure = [x for x in obs if x["q"] < CUT and not x["contradictions"]]
    return sure


def evaluate(obs, sure, st):
    comp = {}
    for i, g in enumerate(L.groups(sure, st)):
        for sg in g["stones"]:
            comp[sg] = i
    # W1: stones in a sure Williams pair (both runestones in the material)
    gid = defaultdict(set)
    for gi, g in enumerate(W["groups"]):
        for m in g["members"]:
            if m["rundata"] in st:
                gid[m["rundata"]].add(gi)
    S = {s for p in W["pairs"] if p["sure"] and p["a"] in st and p["b"] in st for s in (p["a"], p["b"])}
    members = defaultdict(set)
    for s, gs in gid.items():
        for gi in gs:
            members[gi].add(s)
    hit = sum(1 for s in S if s in comp and any(comp.get(o) == comp[s] for gi in gid[s] for o in members[gi] if o != s))
    w2_links = [x for x in sure if st[x["a"]]["province"] in WPROV and st[x["b"]]["province"] in WPROV]
    w2_hit = sum(1 for x in w2_links if gid[x["a"]] & gid[x["b"]])
    jar = [x for x in obs if x["a"] in JARLABANKE and x["b"] in JARLABANKE]
    jar_sure = sum(1 for x in jar if x["q"] < CUT and not x["contradictions"])
    below = [x for x in obs if x["q"] < CUT]
    pp, noted = L.parsten_pairs(st), L.rundata_noted_pairs(st)
    found = {(x["a"], x["b"]) for x in sure}
    return {"n_candidates": len(obs), "n_sure": len(sure),
            "W1": {"n_stones": len(S), "hit": hit, "share": round(hit / len(S), 4) if S else None},
            "W2": {"n_links": len(w2_links), "hit": w2_hit, "share": round(w2_hit / len(w2_links), 4) if w2_links else None},
            "J": {"pairs": len(jar), "sure": jar_sure, "passed": len(jar) == 10 and jar_sure == 10},
            "K": {"candidates": round(sum(1 for x in obs if x["contradictions"]) / len(obs), 4) if obs else None,
                  "below_cut": len(below), "below_cut_contradicted": sum(1 for x in below if x["contradictions"]),
                  "share": round(sum(1 for x in below if x["contradictions"]) / len(below), 4) if below else None},
            "parsten": {"n": len(pp), "found": len(pp & found)}, "rundata_noted": {"n": len(noted), "found": len(noted & found)},
            "per_band": {bd: {"n_sure": sum(1 for x in sure if x.get("band") == bd)} for bd in ("A", "B", "C", "utan koordinater")}}


def describe(sure, st):
    gs = L.groups(sure, st)
    comp = {sg: i for i, g in enumerate(gs) for sg in g["stones"]}
    pid = lambda sg, k: (("g", comp[sg]) if sg in comp else ("s", sg), k)  # noqa: E731
    on = defaultdict(set)
    for sg, s in st.items():
        for p in s["persons"]:
            if p["role"] != "ristare":
                on[pid(sg, p["key"])].add(sg)
    child = defaultdict(set)
    for sg, s in st.items():
        for a, rel, b in s["facts"]:
            if rel in ("father", "mother"):
                child[pid(sg, a)].add(pid(sg, b))
            elif rel in ("son", "daughter", "sons", "daughters"):
                child[pid(sg, b)].add(pid(sg, a))
    memo = {}

    def depth(v, seen=()):
        if v in memo:
            return memo[v]
        best = 1 + max((depth(c, seen + (v,)) for c in child.get(v, ()) if c not in seen), default=0)
        memo[v] = best
        return best
    gen = max((depth(v) for v in list(child)), default=1)
    by_prov = Counter(st[g["stones"][0]]["province"] for g in gs)
    return {"groups": len(gs), "groups_3plus": sum(1 for g in gs if g["n"] >= 3), "stones_in_groups": sum(g["n"] for g in gs),
            "persons_on_2plus": sum(1 for v in on.values() if len(v) >= 2), "longest_generations": gen,
            "groups_by_province": dict(by_prov.most_common()), "largest": gs[:5]}


def model(st, level, edges=None, single_rare=None, n=N_NULL):
    global ST
    ST = st
    w = L.weights(st)
    sex = L.name_sex(st)
    obs = L.links(st, w) + (extra_links(st, w, {sg: L._tokens(s) for sg, s in st.items()}, single_rare) if single_rare else [])
    if edges is None:      # M0: one pool, province null, exactly as the app
        null = L.null_scores(st, w, n, seed=SEED, level=level)
        L.fdr(obs, null, seed=SEED)
        for x in obs:
            x["band"] = band_of(km_of(st, x["a"], x["b"]), (2, 10))
        nl = null
    else:
        nl, _ = null_links(st, w, level, n, single_rare=single_rare)
        q_banded(obs, nl, edges)
    sure = finish(obs, st, sex)
    return obs, sure, nl


res = {"plan": PLAN, "n_stones": len(ALL)}
o0, s0, _ = model(ALL, "province")
res["M0"] = evaluate(o0, s0, ALL)
o1, s1, nl1 = model(ALL, "district", (2, 10))
res["M1"] = evaluate(o1, s1, ALL)
res["M1"]["null_mean_per_band"] = {bd: round(float(np.mean([sum(1 for s, d in rep if band_of(d, (2, 10)) == bd) for rep in nl1])), 2)
                                   for bd in ("A", "B", "C", "utan koordinater")}
res["M1"]["obs_per_band"] = dict(Counter(x["band"] for x in o1))
a, b = res["M0"], res["M1"]
crit = {"W1_double": b["W1"]["share"] >= 2 * a["W1"]["share"], "W1_floor": b["W1"]["share"] >= 0.25,
        "W2_not_worse": b["W2"]["share"] >= a["W2"]["share"] - 0.10, "J": b["J"]["passed"], "K": b["K"]["share"] <= 0.05}
res["criteria"] = crit
res["M1_holds"] = all(crit.values())
res["describe_M1"] = describe(s1, ALL)
res["describe_M0"] = describe(s0, ALL)
res["sure_links_M1"] = [{k: x[k] for k in ("a", "b", "shared", "score", "q", "q_lo", "q_hi", "band")} | {"km": km_of(ALL, x["a"], x["b"])} for x in sorted(s1, key=lambda x: x["q"])]
# Sensitivity
sens = {}
for name, edges in (("band_1_5", (1, 5)), ("band_3_15", (3, 15))):
    oo = [dict(x) for x in o1]
    ST = ALL
    q_banded(oo, nl1, edges)
    ss = finish(oo, ALL, L.name_sex(ALL))
    sens[name] = evaluate(oo, ss, ALL)
for name, c in (("common_40", 40), ("common_80", 80)):
    old = L.COMMON
    L.COMMON = c
    oo, ss, _ = model(ALL, "district", (2, 10))
    L.COMMON = old
    sens[name] = evaluate(oo, ss, ALL)
oo, ss, _ = model(ALL, "province", (2, 10))
sens["null_province_banded"] = evaluate(oo, ss, ALL)
import pandas as pd  # noqa: E402
c = pd.read_csv(os.path.join(ROOT, "data", "cache", "r", "corpus", "e83202e01a5e6d27", "corpus.csv"), low_memory=False, usecols=["signum", "moved", "lost"])
stay = set(c.signum[(c.moved == 0) & (c.lost == 0)])
sub = {k: v for k, v in ALL.items() if k in stay}
oo, ss, _ = model(sub, "district", (2, 10))
sens["without_moved"] = evaluate(oo, ss, sub) | {"n_stones": len(sub)}
res["sensitivity"] = sens
# Exploratory M1b
oo, ss, _ = model(ALL, "district", (2, 10), single_rare={"km": 2, "max": 10})
res["M1b_exploratory"] = evaluate(oo, ss, ALL) | {"describe": describe(ss, ALL)}
json.dump(res, open(os.path.join(OUT, "steg1.json"), "w"), ensure_ascii=False, indent=1, default=str)
for k in ("M0", "M1"):
    r = res[k]
    print(k, "kand", r["n_candidates"], "säkra", r["n_sure"], "W1", r["W1"], "W2", r["W2"], "J", r["J"], "K", r["K"]["share"], r["per_band"])
print("kriterier", crit, "M1 håller:", res["M1_holds"])
print("null per band", res["M1"]["null_mean_per_band"], "obs per band", res["M1"]["obs_per_band"])
print("beskrivning M1", {k: v for k, v in res["describe_M1"].items() if k != "largest"})
for k, v in sens.items():
    print(" känslighet", k, "säkra", v["n_sure"], "W1", v["W1"]["share"], "W2", v["W2"]["share"], "J", v["J"]["passed"], "K", v["K"]["share"])
v = res["M1b_exploratory"]; print(" M1b säkra", v["n_sure"], "W1", v["W1"]["share"], "W2", v["W2"]["share"], "K", v["K"]["share"])
