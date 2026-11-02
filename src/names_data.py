"""Namnunderlaget till r/names.R (Namn och släkt, plan analysplaner/2026-11-02-namn-och-slakt.md): förälder–barn- och
syskonpar med namnled (som utdata/namngivning/analys.py), en rad per runsten med namnnycklar, och släktlänkarna
sammanfattade. Regionen är den vikingatida (korpusens region_old); halvorna socken för socken inom landskapet i
sockenmedeldateringens ordning (som change.R)."""
from __future__ import annotations

import csv
import json
import math
import os
from collections import Counter, defaultdict
from itertools import combinations

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARENT = {"father", "mother", "förälder till"}
CHILD = {"son", "sons", "daughter"}
SIB = {"brother", "brothers", "sister", "sisters"}


def _halves(rows: list[dict]) -> dict[str, str]:
    """signum → 'A'/'B': whole parishes alternately within each province, in order of their mean dating."""
    acc = defaultdict(list)
    for r in rows:
        y = (float(r["style_from"]) + float(r["style_to"])) / 2 if r.get("style_from") not in (None, "") else None
        acc[(r["province"], r.get("parish") or "_" + r["signum"])].append(y)
    order = defaultdict(list)
    for (prov, pk), ys in acc.items():
        yy = [y for y in ys if y is not None]
        order[prov].append((not yy, sum(yy) / len(yy) if yy else 0.0, -len(ys), pk))
    half = {}
    for prov, items in order.items():
        for i, it in enumerate(sorted(items)):
            half[(prov, it[3])] = "A" if i % 2 == 0 else "B"
    return {r["signum"]: half[(r["province"], r.get("parish") or "_" + r["signum"])] for r in rows}


def write(directory: str, corpus_csv: str) -> dict[str, str]:
    """Skriver names_pairs.csv, names_stones.csv och names_family.json i katalogen; returnerar sökvägarna."""
    from api.rundata import store
    from src import entities
    rows = list(csv.DictReader(open(corpus_csv, encoding="utf-8")))
    recs = {r["signum"]: r for r in store().inscriptions}
    half = _halves(rows)
    pairs, stones, keys_all = [], [], Counter()
    for r in rows:
        x = entities.extract(recs[r["signum"]])
        meta = {"signum": r["signum"], "region": r.get("region_old") or r["province"], "half": half[r["signum"]]}
        names = sorted({p["key"] for p in x["persons"] if p["role"] != "ristare" and p["key"] and not p["key"].endswith("-")})
        for k in names:
            keys_all[k] += 1
        stones.append({**meta, "lat": r.get("lat") or "", "lon": r.get("lon") or "", "names": "|".join(names)})
        kids = defaultdict(set)
        for a, rel, b in x["facts"]:
            if rel in PARENT:
                pairs.append({**meta, "kind": "pc", "a": a, "b": b}); kids[a].add(b)
            elif rel in CHILD:
                pairs.append({**meta, "kind": "pc", "a": b, "b": a}); kids[b].add(a)
            elif rel in SIB:
                pairs.append({**meta, "kind": "sib", "a": min(a, b), "b": max(a, b)})
        for par, ks in kids.items():
            for a, b in combinations(sorted(ks), 2):
                pairs.append({**meta, "kind": "sib", "a": a, "b": b})
    # one pair per parish (as the locked naming analysis), no self-pairs among siblings
    seen, uniq = set(), []
    for p in pairs:
        if not p["a"] or not p["b"] or (p["kind"] == "sib" and p["a"] == p["b"]):
            continue
        key = (p["kind"], p["a"], p["b"], p["signum"].split(" ")[0], p["region"])
        if key in seen:
            continue
        seen.add(key); uniq.append(p)
    vocab = sorted(keys_all)

    def parts(k):
        best, score = None, 0
        for i in range(3, len(k) - 2):           # elements of at least three letters
            pre, suf = k[:i], k[i:]
            npre = sum(1 for o in vocab if o != k and o.startswith(pre))
            nsuf = sum(1 for o in vocab if o != k and o.endswith(suf))
            if npre >= 3 and nsuf >= 3 and min(npre, nsuf) > score:
                best, score = (pre, suf), min(npre, nsuf)
        return best or (k,)
    cache = {}
    for p in uniq:
        for side in ("a", "b"):
            k = p[side]
            if k not in cache:
                cache[k] = "|".join(parts(k))
            p[f"{side}_parts"] = cache[k]
    out = {"pairs": os.path.join(directory, "names_pairs.csv"), "stones": os.path.join(directory, "names_stones.csv"),
           "family": os.path.join(directory, "names_family.json")}
    for path, data in ((out["pairs"], uniq), (out["stones"], stones)):
        with open(path, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(data[0]))
            w.writeheader(); w.writerows(data)
    json.dump(family(rows), open(out["family"], "w", encoding="utf-8"), ensure_ascii=False)
    return out


def family(rows: list[dict]) -> dict:
    """Släktmönstren (beskrivande): de säkra länkarna mellan svenska runstenar (data/links.json) – samma socken, samma
    region och avståndet – och släkterna ur utdata/slakt/steg2a.json per region."""
    by = {r["signum"]: r for r in rows}
    path = os.path.join(ROOT, "data", "links.json")
    if not os.path.exists(path):
        return {}
    L = json.load(open(path, encoding="utf-8"))
    sure = [x for x in L["links"] if x["q"] < L["fdr_cut"] and not x["contradictions"] and x["a"] in by and x["b"] in by]
    km, same_parish, same_region = [], 0, 0
    for x in sure:
        a, b = by[x["a"]], by[x["b"]]
        same_parish += int((a.get("parish") or "") == (b.get("parish") or "") and bool(a.get("parish")))
        same_region += int((a.get("region_old") or a["province"]) == (b.get("region_old") or b["province"]))
        if x.get("km") is not None:
            km.append(float(x["km"]))
    km.sort()
    q = lambda f: round(km[min(len(km) - 1, int(f * (len(km) - 1)))], 1) if km else None  # noqa: E731
    fam_path = os.path.join(ROOT, "utdata", "slakt", "steg2a.json")
    fam_regions = Counter()
    if os.path.exists(fam_path):
        for f in json.load(open(fam_path, encoding="utf-8"))["families"]:
            regs = Counter((by[s].get("region_old") or by[s]["province"]) for s in f["stones"] if s in by)
            if regs:
                fam_regions[regs.most_common(1)[0][0]] += 1
    return {"n_links": len(sure), "same_parish": same_parish, "same_region": same_region,
            "km_median": q(0.5), "km_q1": q(0.25), "km_q3": q(0.75), "families_by_region": dict(fam_regions.most_common()),
            "n_families": sum(fam_regions.values())}
