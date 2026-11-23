"""Facit för nya ristare (analysplaner/2026-11-23-nya-ristare-program.md, sha f5ce4fe7): runologernas "samma hand" ur
Runor 2020 och SRI-utgivarnas uttalanden; kontrollen av utläsningen; delningen i utvecklings- och provdel.

    .venv/bin/python utdata/nya_ristare/facit.py
Skriver data/cache/hander/facit.json (utanför git) och utdata/nya_ristare/{delning.json, kontroll_facit.json}.
"""
import glob
import hashlib
import json
import os
import random
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
PLAN = os.path.join(ROOT, "analysplaner", "2026-11-23-nya-ristare-program.md")
assert hashlib.sha256(open(PLAN, "rb").read()).hexdigest().startswith("f5ce4fe7"), "planen är ändrad efter låsningen"
CACHE = os.path.join(ROOT, "data", "cache", "hander")
SEED = 20261123
RD = {r["signum"] for r in json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["inscriptions"]}
SIGRX = re.compile(r"^(U|Sö|Ög|Vg|Sm|Öl|G|Vs|Nä|Gs|Hs|M|D|Vr|Ån|J|Bo|Hl|Bl|Sk|DR|N)\s+(\S+)$")


def norm(s):
    s = re.sub(r"\s+", " ", (s or "").strip())
    m = SIGRX.match(s)
    return f"{m.group(1)} {m.group(2)}" if m else None


def read(path):
    return {json.loads(l)["id"]: json.loads(l) for l in open(path, encoding="utf-8") if l.strip()}


def pairs_of(rec, keep=lambda r: True):
    out = set()
    for r in rec.get("relations") or []:
        if not keep(r):
            continue
        a = norm(r.get("a"))
        for b in r.get("b") or []:
            b = norm(b)
            if a and b and a != b:
                out.add((tuple(sorted((a, b))), r.get("strength"), bool(r.get("rejected"))))
    return out


# ---------------------------------------------------------------- utläsningarna och kontrollen
U = {}
for p in ("sri_utlasning_1.jsonl", "sri_utlasning_2.jsonl"):
    U.update(read(os.path.join(CACHE, p)))
ctx = json.load(open(os.path.join(CACHE, "sri_kontexter.json"), encoding="utf-8"))
assert set(U) == {c["id"] for c in ctx}, "utläsningen saknar ställen"
K = read(os.path.join(CACHE, "sri_utlasning_kontroll.jsonl"))
same = [i for i in K if pairs_of(K[i]) == pairs_of(U[i])]
ctrl = {"stickprov": len(K), "lika": len(same), "procent": round(100 * len(same) / len(K), 1), "krav": 85,
        "oenigheter": [{"id": i, "första": sorted(map(list, pairs_of(U[i]))), "kontroll": sorted(map(list, pairs_of(K[i])))}
                       for i in K if i not in same]}
json.dump(ctrl, open(os.path.join(HERE, "kontroll_facit.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("kontroll:", ctrl["lika"], "av", ctrl["stickprov"])

# ---------------------------------------------------------------- omläsningen och avgörandena (kontrollen < 85 %)
def status(rec):
    """Par -> 'in' (säker/trolig, utgivaren), 'möjlig', 'avvisad' eller 'annan'."""
    out = {}
    for (a, b), strength, rej in pairs_of(rec):
        pass
    for r in rec.get("relations") or []:
        a = norm(r.get("a"))
        for b in r.get("b") or []:
            b = norm(b)
            if not a or not b or a == b:
                continue
            k = tuple(sorted((a, b)))
            st_ = ("avvisad" if r.get("rejected") else "annan" if r.get("who") != "utgivaren"
                   else "in" if r.get("strength") in ("säker", "trolig") else "möjlig")
            prio = {"avvisad": 3, "in": 2, "möjlig": 1, "annan": 0}
            if k not in out or prio[st_] > prio[out[k]]:
                out[k] = st_
    return out


FINAL = None
if ctrl["procent"] < 85:
    O = {}
    for p in ("sri_omlasning_1.jsonl", "sri_omlasning_2.jsonl"):
        O.update(read(os.path.join(CACHE, p)))
    assert set(O) == set(U), "omläsningen saknar ställen"
    av = json.load(open(os.path.join(CACHE, "sri_avgorande.json"), encoding="utf-8")) if os.path.exists(
        os.path.join(CACHE, "sri_avgorande.json")) else {}
    FINAL, open_ = {}, []
    for i in U:
        su, so = status(U[i]), status(O[i])
        for k in set(su) | set(so):
            x, y = su.get(k, "ingen"), so.get(k, "ingen")
            key = f"{i}#{k[0]}#{k[1]}"
            if x == y:
                FINAL[key] = x
            elif key in av:
                FINAL[key] = av[key]
            else:
                open_.append({"nyckel": key, "första": x, "omläsning": y})
    json.dump(open_, open(os.path.join(CACHE, "sri_oavgjorda.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    agree = sum(1 for i in U if status(U[i]) == status(O[i]))
    print(f"omläsningen: {agree} av {len(U)} ställen lika; {len(open_)} par att avgöra för hand")
    assert not open_, "avgör paren i data/cache/hander/sri_oavgjorda.json (skriv sri_avgorande.json) innan facit används"

# ---------------------------------------------------------------- länkarna
links, rejected, weak, other = [], [], [], []
if FINAL is not None:
    for key, v in FINAL.items():
        i, a, b = key.split("#")
        if a not in RD or b not in RD:
            continue
        rec = {"a": a, "b": b, "styrka": v, "källa": "SRI", "ställe": i}
        {"in": links, "avvisad": rejected, "möjlig": weak, "annan": other}.get(v, []).append(rec)
for i, rec in (U.items() if FINAL is None else []):
    for (a, b), strength, rej in pairs_of(rec, lambda r: r.get("who") == "utgivaren"):
        if a not in RD or b not in RD:
            continue
        (rejected if rej else links if strength in ("säker", "trolig") else weak).append({"a": a, "b": b, "styrka": strength, "källa": "SRI", "ställe": i})
    for (a, b), strength, rej in pairs_of(rec, lambda r: r.get("who") != "utgivaren"):
        if a in RD and b in RD and not rej:
            other.append({"a": a, "b": b, "styrka": strength, "källa": "SRI (annan forskare)", "ställe": i})

SAME = re.compile(r"^(Samma som|Samma ristare som|Troligen samma|Antagligen samma|Förmodligen samma|Eventuellt samma)", re.I)
PREFIX = re.compile(r"^(U|Sö|Ög|Vg|Sm|Öl|G|Vs|Nä|Gs|Hs|M|D|Vr|Ån|J|Bo|DR|N|Sk|Bl|Hl)$")


def referenced(text, own_prefix):
    m = re.search(r"gjort\s+(.*)$", text) or re.search(r".*\bsom\s+(.*)$", text)
    if not m:
        return []
    body = re.sub(r"ATA\s*[\d/]+", "", m.group(1)).replace(" och ", ",").rstrip(". ")
    out, prefix = [], own_prefix
    for part in [p.strip() for p in body.split(",") if p.strip()]:
        toks = part.split()
        if len(toks) >= 2 and PREFIX.match(toks[0]):
            prefix, part = toks[0], " ".join(toks[1:])
        part = part.strip()
        rg = re.fullmatch(r"(\d+)\s*-\s*(\d+)", part)
        if rg:
            out += [f"{prefix} {k}" for k in range(int(rg.group(1)), int(rg.group(2)) + 1)]
        elif re.fullmatch(r"\d+[A-Za-z]?|Fv\d{4};\d+[A-Za-z]?", part):
            out.append(f"{prefix} {part}")
    return out


for f in glob.glob(os.path.join(ROOT, "data", "cache", "runor", "*.json")):
    d = json.load(open(f, encoding="utf-8"))
    sig = f"{d['signum1']} {d['signum2']}".strip()
    for cv in d.get("carver") or []:
        n = (cv.get("name") or "").strip()
        if SAME.match(n):
            for o in referenced(n, d["signum1"]):
                if sig in RD and o in RD and sig != o:
                    links.append({"a": sig, "b": o, "styrka": "säker" if cv.get("certainty") else "trolig", "källa": "Runor 2020", "ställe": sig})

# ---------------------------------------------------------------- grupperna och delningen
parent = {}


def find(a):
    parent.setdefault(a, a)
    while parent[a] != a:
        parent[a] = parent[parent[a]]
        a = parent[a]
    return a


for l in links:
    parent[find(l["a"])] = find(l["b"])
groups = defaultdict(set)
for s in parent:
    groups[find(s)].add(s)
groups = sorted((sorted(g) for g in groups.values() if len(g) >= 2), key=lambda g: g[0])
rnd = random.Random(SEED)
order = list(range(len(groups)))
rnd.shuffle(order)
dev = set(order[: len(order) // 2])
split = [{"grupp": k, "del": "U" if k in dev else "P", "stenar": g} for k, g in enumerate(groups)]
json.dump({"plan_sha": "f5ce4fe7", "grupper": split, "avvisade_par": sorted({(r["a"], r["b"]) for r in rejected})},
          open(os.path.join(HERE, "delning.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump({"länkar": links, "möjliga": weak, "avvisade": rejected, "annan_forskare": other, "grupper": split},
          open(os.path.join(CACHE, "facit.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(links), "länkar (", Counter(l["källa"] for l in links), ")", len(weak), "möjliga,", len(rejected), "avvisade,",
      len(other), "annan forskare")
print(len(groups), "grupper; storlekar", sorted(Counter(len(g) for g in groups).items()))
print("utveckling", sum(1 for s in split if s["del"] == "U"), "prov", sum(1 for s in split if s["del"] == "P"))
print("landskap", Counter(s.split()[0] for g in groups for s in g).most_common())
