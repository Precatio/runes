"""Släktnätverket steg 2a (beskrivande, ingen hypotes): släktträden ur appens länkar (data/links.json, avståndsbanden
sedan 2026-11-01). Samma namn på två stenar som en säker länk förenar räknas som samma person; släktbanden kommer ur
varje stens egna fakta (src/entities.extract). En släkt är de stenar som säkra länkar knyter ihop (som linking.groups),
med alla personer på dem. Bara svenska vikingatida runstenar. Skriver steg2a.json.
    PYTHONPATH=. .venv/bin/python utdata/slakt/steg2a.py"""
import json
import os
import sys
from collections import Counter, defaultdict

OUT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(OUT, "..", ".."))
sys.path.insert(0, ROOT)
from src import linking as L  # noqa: E402

SE = ("U", "Sö", "Ög", "Vg", "Sm", "Öl", "G", "Nä", "Vs", "Gs", "Hs", "M", "J", "D", "Bo", "Vr")
PARENT = {"father", "mother", "förälder till"}          # (a, rel, b): a är förälder till b
CHILD = {"son", "sons", "daughter"}                      # (a, rel, b): a är barn till b
SPOUSE = {"husbandman", "husband", "wife", "partner"}
SIB = {"brother", "brothers", "sister", "sisters"}

rd = json.load(open(os.path.join(ROOT, "data", "rundata.json")))["inscriptions"]
st = {k: v for k, v in L.stones(rd).items() if k.split(" ")[0] in SE}
links = json.load(open(os.path.join(ROOT, "data", "links.json")))
sure = [x for x in links["links"] if x["q"] < links["fdr_cut"] and not x["contradictions"] and x["a"] in st and x["b"] in st]
assert len(sure) == 61

parent = {}


def find(x):
    parent.setdefault(x, x)
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x


def union(a, b):
    parent[find(a)] = find(b)


names = {}
for sg, s in st.items():
    for p in s["persons"]:
        if p["role"] != "ristare":
            names[(sg, p["key"])] = p["name"]
            find((sg, p["key"]))
# same person: a shared name on two stones joined by a sure link
for x in sure:
    for k in x["shared"]:
        if not k.startswith("plats:") and (x["a"], k) in names and (x["b"], k) in names:
            union((x["a"], k), (x["b"], k))
# kin edges between persons (after merging)
edges = []
for sg, s in st.items():
    for a, rel, b in s["facts"]:
        if (sg, a) in names and (sg, b) in names:
            edges.append(((sg, a), rel, (sg, b), sg))
fam = {}


def ffind(x):
    fam.setdefault(x, x)
    while fam[x] != x:
        fam[x] = fam[fam[x]]
        x = fam[x]
    return x


for node in names:
    ffind(find(node))
# a family = the stones that sure links join (as linking.groups), with every person on them
for x in sure:
    for k in (x["a"], x["b"]):
        pass
    fam[ffind(("stone", x["a"]))] = ffind(("stone", x["b"]))
groups = defaultdict(set)
for node in names:
    if ("stone", node[0]) in fam:
        groups[ffind(("stone", node[0]))].add(node)
families = []
for root, nodes in groups.items():
    stones = sorted({sg for sg, _ in nodes})
    if len(stones) < 2:
        continue
    persons = defaultdict(set)
    for n in nodes:
        persons[find(n)].add(n)
    pname = {pid: Counter(names[n] for n in ns).most_common(1)[0][0] for pid, ns in persons.items()}
    rels, kids = set(), defaultdict(set)
    for a, rel, b, sg in edges:
        if a in nodes:
            pa, pb = find(a), find(b)
            if pa == pb:
                continue
            rels.add((pname[pa], rel, pname[pb]))
            if rel in PARENT:
                kids[pa].add(pb)
            elif rel in CHILD:
                kids[pb].add(pa)
    memo = {}

    def depth(v, seen=()):
        if v in memo:
            return memo[v]
        memo[v] = 1 + max((depth(c, seen + (v,)) for c in kids.get(v, ()) if c not in seen), default=0)
        return memo[v]
    gen = max([depth(v) for v in list(kids)] or [1])
    multi = [pname[p] for p, ns in persons.items() if len({sg for sg, _ in ns}) >= 2]
    d = [L.km(st[a], st[b]) for i, a in enumerate(stones) for b in stones[i + 1:]]
    d = [x for x in d if x is not None]
    styles = sorted({st[s]["from"] for s in stones if st[s]["from"]})
    families.append({"stones": stones, "n_stones": len(stones), "n_persons": len(persons), "persons_on_2plus": sorted(multi),
                     "generations": gen, "max_km": round(max(d), 1) if d else None,
                     "provinces": sorted({st[s]["province"] for s in stones}), "parishes": sorted({st[s]["parish"] for s in stones}),
                     "relations": sorted(rels), "women": sum(1 for p, ns in persons.items() if any(
                         x["key"] == n[1] and x.get("female") for n in ns for x in st[n[0]]["persons"]))})
families.sort(key=lambda f: (-f["n_stones"], -f["n_persons"]))
gen = Counter(f["generations"] for f in families)
out = {"n_links": len(sure), "n_families": len(families), "stones_in_families": sum(f["n_stones"] for f in families),
       "persons_in_families": sum(f["n_persons"] for f in families),
       "persons_on_2plus": sum(len(f["persons_on_2plus"]) for f in families),
       "by_size": dict(sorted(Counter(f["n_stones"] for f in families).items())), "by_generations": dict(sorted(gen.items())),
       "by_province": dict(Counter(f["provinces"][0] if len(f["provinces"]) == 1 else "flera" for f in families).most_common()),
       "families": families}
json.dump(out, open(os.path.join(OUT, "steg2a.json"), "w"), ensure_ascii=False, indent=1)
print({k: v for k, v in out.items() if k != "families"})
for f in families[:8]:
    print(f["n_stones"], "stenar", f["n_persons"], "personer", f["generations"], "gen", f["max_km"], "km |", ", ".join(f["stones"]), "|", ", ".join(f["persons_on_2plus"][:6]))
