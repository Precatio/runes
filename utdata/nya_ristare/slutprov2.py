"""Slutprov 2 (analysplaner/2026-11-23-nya-ristare-slutprov-2-litteraturen.md, sha 706be174): samma grupper (τ 0,8) mot
facit 2 ur litteraturen – uttalanden om samma hand som båda granskarna bekräftade, utom par som redan finns i facit 1.

    .venv/bin/python utdata/nya_ristare/slutprov2.py
Läser data/cache/hander/lit_granskning.json (arbetsflödets resultat) och lit_granska.json; skriver slutprov2.json.
"""
import hashlib
import itertools
import json
import os
import re
import sys
from collections import Counter, defaultdict

import numpy as np
from scipy.stats import wilcoxon

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
from utdata.nya_ristare.belagg import MAXD, load  # noqa: E402

PLAN = os.path.join(ROOT, "analysplaner", "2026-11-23-nya-ristare-slutprov-2-litteraturen.md")
assert hashlib.sha256(open(PLAN, "rb").read()).hexdigest().startswith("706be174"), "planen är ändrad efter låsningen"
CACHE = os.path.join(ROOT, "data", "cache", "hander")
SIG = re.compile(r"^(U|Sö|Ög|Vg|Sm|Öl|Vs|Nä|Gs|Hs|Ån|Vr|D|M|J|G|DR|N|Bo)\s*(\d+[A-Za-z]?)$")


def norm(s):
    m = SIG.match((s or "").strip())
    return f"{m.group(1)} {m.group(2)}" if m else None


items = json.load(open(os.path.join(CACHE, "lit_granska.json"), encoding="utf-8"))
ver = json.load(open(os.path.join(CACHE, "lit_granskning.json"), encoding="utf-8"))
byfile = {r["fil"]: r for r in ver if r}
same, diff, attr = defaultdict(set), defaultdict(set), defaultdict(set)
stats = Counter()
for i, it in enumerate(items):
    f = os.path.join(CACHE, "lit_granska", f"item_{i:03d}.txt")
    r = byfile.get(os.path.abspath(f)) or byfile.get(f)
    c = it["claim"]
    vs = [v for v in (r or {}).get("granskare", []) if v]
    ok = len(vs) == 2 and all(v["bekraftad"] and v["styrka"] in ("säker", "trolig") for v in vs)
    stats[(c["relation"], ok)] += 1
    if not ok:
        continue
    st = sorted({norm(s) for s in vs[0]["stenar"]} & {norm(s) for s in vs[1]["stenar"]} - {None})
    src = it["källa"]
    if c["relation"] == "samma_hand":
        for a, b in itertools.combinations(st, 2):
            same[(a, b)].add(src)
    elif c["relation"] == "olika_hander":
        # rättelse 2026-11-24: bara två stenar, eller en lista över olika namnbärare; annars gäller uttalandet oftast en
        # sten mot de andra, och alla par blir fel (Stern 2013 om U 855 och Arnfasts stenar)
        if len(st) == 2 or (len(st) > 2 and all("bärare" in v["skal"] for v in vs)):
            for a, b in itertools.combinations(st, 2):
                diff[(a, b)].add(src)
    else:
        for a in st:
            attr[a].add((c.get("ristare") or "").split()[0])
print("granskning:", dict(stats))

st = load()
f1 = json.load(open(os.path.join(CACHE, "facit.json"), encoding="utf-8"))
old_pairs = {tuple(sorted((l["a"], l["b"]))) for l in f1["länkar"]}
g1 = {}
for k, g in enumerate(f1["grupper"]):
    for s in g["stenar"]:
        g1[s] = k
new = {p: v for p, v in same.items() if p not in old_pairs and not (p[0] in g1 and g1.get(p[0]) == g1.get(p[1]))
       and p[0] in st.ix and p[1] in st.ix}
parent = {}


def find(a):
    parent.setdefault(a, a)
    while parent[a] != a:
        parent[a] = parent[parent[a]]
        a = parent[a]
    return a


for a, b in new:
    parent[find(a)] = find(b)
groups = defaultdict(set)
for s in parent:
    groups[find(s)].add(s)
groups = [sorted(g) for g in groups.values()]
print(f"facit 2: {len(same)} granskade par om samma hand, {len(new)} nya, {len(groups)} grupper")

N = len(st.sig)
merges = np.load(os.path.join(CACHE, "sammanslagningar_M1.npy"))
lab = np.arange(N)
for i, j, s in merges:
    if s < 0.8:
        break
    lab[lab == lab[int(j)]] = lab[int(i)]
cert = {st.ix[s] for s in st.certain if s in st.ix}
res = []
for g in groups:
    gi = [st.ix[s] for s in g]
    pairs = [(a, b) for k, a in enumerate(gi) for b in gi[k + 1:] if st.D[a, b] <= MAXD]
    if not pairs:
        continue
    obs = float(np.mean([lab[a] == lab[b] for a, b in pairs]))
    ctrl = []
    for a, b in pairs:
        for x, y in ((a, b), (b, a)):
            d = st.D[x, y]
            lo, hi = min(d * 0.75, d - 1000), min(max(d * 1.25, d + 1000), MAXD)
            ok = np.where((st.D[x] >= lo) & (st.D[x] <= hi))[0]
            ok = ok[~np.isin(ok, gi)]
            if len(ok):
                ctrl.append(float(np.mean(lab[ok] == lab[x])))
    if ctrl:
        res.append({"stenar": g, "par": len(pairs), "samma_grupp": obs, "kontroll": float(np.mean(ctrl)),
                    "onämnd": not any(i in cert for i in gi),
                    "källor": sorted({s for a, b in itertools.combinations(g, 2) for s in same.get((a, b), ())})})


def test(rs):
    d = [r["samma_grupp"] - r["kontroll"] for r in rs]
    if len(d) < 5 or not any(d):
        return {"grupper": len(d), "obestämt": True}
    return {"grupper": len(d), "medel_samma": round(float(np.mean([r["samma_grupp"] for r in rs])), 3),
            "medel_kontroll": round(float(np.mean([r["kontroll"] for r in rs])), 3),
            "median_skillnad": round(float(np.median(d)), 3), "bättre": int(sum(x > 0 for x in d)),
            "sämre": int(sum(x < 0 for x in d)), "p": float(wilcoxon(d, alternative="greater").pvalue)}


T1, T2 = test(res), test([r for r in res if r["onämnd"]])
T1["håller"] = bool(T1.get("p") is not None and T1["p"] < 0.05 and T1["medel_samma"] > T1["medel_kontroll"]) if "p" in T1 else False
# falska sammanslagningar: granskade par om olika händer som ändå ligger i samma grupp
dp = [(a, b) for (a, b) in diff if a in st.ix and b in st.ix and st.D[st.ix[a], st.ix[b]] <= MAXD]
false_merge = [(a, b) for a, b in dp if lab[st.ix[a]] == lab[st.ix[b]]]
out = {"plan_sha": "706be174", "granskning": {f"{k[0]}|{'bekräftad' if k[1] else 'ej'}": v for k, v in stats.items()},
       "facit2_par": len(new), "facit2_grupper": len(groups), "T1": T1, "T2": T2,
       "olika_händer_par_inom_30km": len(dp), "av_dem_i_samma_grupp": len(false_merge), "falska": false_merge,
       "grupper": res}
json.dump(out, open(os.path.join(HERE, "slutprov2.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump({"samma_hand": [[a, b, sorted(v)] for (a, b), v in sorted(same.items())],
           "olika_hander": [[a, b, sorted(v)] for (a, b), v in sorted(diff.items())],
           "tillskrivningar": {s: sorted(v) for s, v in attr.items()}},
          open(os.path.join(CACHE, "lit_facit2_granskat.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: out[k] for k in ("facit2_par", "facit2_grupper", "T1", "T2", "olika_händer_par_inom_30km", "av_dem_i_samma_grupp")},
                 ensure_ascii=False, indent=1))
