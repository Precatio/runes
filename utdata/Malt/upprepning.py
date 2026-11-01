"""Upprepningar i Maltstenens ristning (låst plan analysplaner/2026-11-01-malt-upprepningar.md, sha 0a087882).
Direkt upprepning XX (|X| ≥ k) inom en skiljeteckengrupp och upprepningstätheten D4 (andelen fyrrunsföljder som finns
minst två gånger i inskriften), Malt mot vikingatida runstenar med 91–204 runor. Inga läsningar av Malt.
    PYTHONPATH=. .venv/bin/python utdata/Malt/upprepning.py"""
import itertools
import json
import os
import re
import sys
from collections import Counter

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
from src import runlm as rl  # noqa: E402

MALT = "DR NOR1988;5"
# copied from scripts/malt_decode.py (which runs its whole analysis on import); asserted against the source below
POINTS = [("B1:23", ["i", ":"]), ("B4 efter 14", [":", ""]), ("B4:1", ["a", "k"]), ("B3:11", ["s", "i"]), ("B5:14", ["i", "a"]), ("B5:22–23", ["ki", "il"])]
SRC = open(os.path.join(ROOT, "scripts", "malt_decode.py")).read()
assert repr(POINTS)[1:-1].replace("'", '"') in SRC.replace("'", '"')
assert '"suaai:titultitul|huaRisi:alistiosa:huaRis" + b1 + "uifrþuR:karþi:afraftasinifauþrkul:finR:fal" + b311 +' in SRC
BEST = (":", ":", "k", "i", "a", "ki")      # malt_avkodning.json "best"
assert json.load(open(os.path.join(HERE, "malt_avkodning.json")))["best"] == list(BEST)


def malt_stream(v):
    b1, b4d, b41, b311, b514, b522 = v
    s = ("suaai:titultitul|huaRisi:alistiosa:huaRis" + b1 + "uifrþuR:karþi:afraftasinifauþrkul:finR:fal" + b311 +
         ":taitirunoR:u" + b41 + "iuinrunoR:suli" + b4d + "alta:huaR|utu:tuuutbilik" + b514 + "kR:tuRra" + b522 + "tuli")
    return [[g for g in s.replace("|", ":").split(":") if g]]   # one unbroken stretch, split into carved groups


def stream(translit):
    """Unbroken stretches, each a list of carved groups (dividers are group boundaries, editors' spaces are not)."""
    parts = [re.sub(r"(\S+)/\S+", r"\1", t) for _, t in rl.sections(translit or "")]
    t = rl.clean_translit(" ".join(parts))
    t = re.sub(rl.DIV, "|", t)
    t = re.sub(r"\s+", "", t)
    out = []
    for stretch in re.split(r"[^a-zþæøR|]+", t):
        groups = [g for g in stretch.split("|") if g]
        if groups:
            out.append(groups)
    return out


def n_runes(st):
    return sum(len(g) for s in st for g in s)


def tandem(st, k):
    """The longest direct repeat XX with |X| ≥ k inside one carved group, or None."""
    best = None
    for s in st:
        for g in s:
            for L in range(len(g) // 2, k - 1, -1):
                for i in range(len(g) - 2 * L + 1):
                    if g[i:i + L] == g[i + L:i + 2 * L] and len(set(g[i:i + L])) > 1:
                        if best is None or L > len(best):
                            best = g[i:i + L]
                        break
                if best and len(best) >= L:
                    break
    return best


def density(st, n=4):
    """Share of n-rune positions (inside unbroken stretches, across dividers) whose sequence occurs at least twice."""
    grams = []
    for s in st:
        t = "".join(s)
        grams += [t[i:i + n] for i in range(len(t) - n + 1)]
    if not grams:
        return float("nan")
    c = Counter(grams)
    return sum(c[g] >= 2 for g in grams) / len(grams)


rows = [r for r in rl.load_rundata() if rl.viking(r)]
by = {r["signum"]: r for r in rows}
malt_best = malt_stream(BEST)
assert n_runes(malt_best) == 136
res = {"plan": "analysplaner/2026-11-01-malt-upprepningar.md", "plan_sha": "0a087882"}
res["malt"] = {"runes": n_runes(malt_best), "groups": len(malt_best[0]), "T5": tandem(malt_best, 5), "T4": tandem(malt_best, 4),
               "T3": tandem(malt_best, 3), "D3": density(malt_best, 3), "D4": density(malt_best, 4), "D5": density(malt_best, 5)}
combos = [malt_stream(v) for v in itertools.product(*[r for _, r in POINTS])]
res["malt"]["D4_range_64"] = [min(density(c) for c in combos), max(density(c) for c in combos)]
mr = stream(by[MALT]["transliteration"]) if MALT in by else None
res["malt_rundata"] = {"runes": n_runes(mr), "D4": density(mr), "T5": tandem(mr, 5), "translit": by[MALT]["transliteration"]} if mr else None


def country(sg):
    p = sg.split(" ")[0]
    return "DK" if p == "DR" else "N" if p == "N" else "SE"


comp, allobj = [], []
for r in rows:
    if r["signum"] == MALT:
        continue
    st = stream(r.get("transliteration"))
    n = n_runes(st)
    rec = {"signum": r["signum"], "kind": rl.object_kind(r), "country": country(r["signum"]), "runes": n,
           "T5": tandem(st, 5), "T4": tandem(st, 4), "T3": tandem(st, 3)}
    allobj.append(rec)
    if rec["kind"] == "runsten" and 91 <= n <= 204:
        comp.append(rec | {"D3": density(st, 3), "D4": density(st, 4), "D5": density(st, 5)})


def pct(x, xs):
    xs = np.array(xs)
    return float((xs < x).mean())


q2 = {"n": len(comp), "by_country": dict(Counter(c["country"] for c in comp))}
for d in ("D3", "D4", "D5"):
    xs = [c[d] for c in comp]
    q2[d] = {"malt": res["malt"][d], "p95": float(np.percentile(xs, 95)), "median": float(np.median(xs)),
             "percentile": pct(res["malt"][d], xs), "above_p95": res["malt"][d] > np.percentile(xs, 95)}
xs4 = [c["D4"] for c in comp]
q2["D4_all64_above_p95"] = all(density(c) > np.percentile(xs4, 95) for c in combos)
q2["D4_by_country"] = {k: {"n": sum(1 for c in comp if c["country"] == k),
                           "percentile": pct(res["malt"]["D4"], [c["D4"] for c in comp if c["country"] == k])}
                       for k in ("SE", "DK", "N") if any(c["country"] == k for c in comp)}
if mr:
    q2["D4_rundata_translit"] = {"D4": density(mr), "percentile": pct(density(mr), xs4), "above_p95": density(mr) > np.percentile(xs4, 95)}
q2["holds"] = bool(q2["D4"]["above_p95"] and q2["D4_all64_above_p95"])
q2["top"] = sorted(({"signum": c["signum"], "D4": c["D4"], "runes": c["runes"]} for c in comp), key=lambda c: -c["D4"])[:10]
res["q2"] = q2

q1 = {}
for kind in rl.OBJECT_KINDS:
    ys = [a for a in allobj if a["kind"] == kind and a["runes"] >= 10]
    q1[kind] = {"n": len(ys), **{k: sum(1 for a in ys if a[k]) for k in ("T5", "T4", "T3")}}
res["q1"] = q1
res["q1_list"] = [{"signum": a["signum"], "kind": a["kind"], "runes": a["runes"], "X": a["T4"],
                   "normalization": (by[a["signum"]].get("normalization") or "")[:240],
                   "translation_en": (by[a["signum"]].get("translation_en") or "")[:240]}
                  for a in sorted(allobj, key=lambda a: (-len(a["T4"] or ""), a["signum"])) if a["T4"]]

sp = {x["signum"]: x["verdict"] for x in json.load(open(os.path.join(ROOT, "utdata", "sprakprov", "sprakprov.json")))["rows"]}
q3 = {}
for v in ("inte språk", "språklik"):
    ds = [density(stream(by[s]["transliteration"])) for s, vv in sp.items() if vv == v and s in by]
    ds = [d for d in ds if d == d]
    q3[v] = {"n": len(ds), "median_D4": float(np.median(ds)), "malt_percentile": pct(res["malt"]["D4"], ds)}
res["q3_groups"] = q3
json.dump(res, open(os.path.join(HERE, "upprepning.json"), "w"), ensure_ascii=False, indent=1, default=str)
print(json.dumps({k: res[k] for k in ("malt", "q1", "q3_groups")}, ensure_ascii=False, indent=1, default=str))
print(json.dumps({k: v for k, v in q2.items() if k != "top"}, ensure_ascii=False, indent=1, default=str))
print("topp D4:", [(t["signum"], round(t["D4"], 3), t["runes"]) for t in q2["top"]])
print("malt_rundata:", res["malt_rundata"] and {k: res["malt_rundata"][k] for k in ("runes", "D4", "T5")})
for a in res["q1_list"]:
    print(f"{a['signum']:18} {a['kind']:12} {a['runes']:4} {a['X']:10} | {a['normalization'][:90]} | {a['translation_en'][:80]}")
