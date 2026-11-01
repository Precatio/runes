"""Maltstenens runmästeriprofil (låst plan analysplaner/2026-11-01-malt-runmasteri.md, sha 8a137566).
Del 1: fyra drag med regler (D1 runrad, D2 mångdubblade runor, D3 dubblering ≥ 4, D4 påstående om runorna) på alla
vikingatida inskrifter; del 2: följs runraden och de andra dragen åt (Fisher, halvor); del 3: underlaget till den blinda
klassningen (24 texter utan signum). Skriver runmasteri.json och runmasteri_blind_underlag.json.
    PYTHONPATH=. .venv/bin/python utdata/Malt/runmasteri.py"""
import json
import os
import random
import re
import sys

from scipy.stats import fisher_exact

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
from src import runlm as rl  # noqa: E402
from runrad_dubblering import stretches, tandems, futhark_spans  # noqa: E402  (same corrected main reading)

MALT = "DR NOR1988;5"
D4RE = re.compile(r"runaR\W+(ret|rett|rettaR)|raða skal|\braði\b|\bræð\b|raðu\b|tæitirun|ævinrun|ginnurun|raginakund|reginkunn")


def norm_plain(r):
    return re.sub(r"[^\w\s]", " ", (r.get("normalization") or "").lower().replace('"', ""))


def traits(r):
    st = stretches(r.get("transliteration"))
    joined = ["".join(s) for s in st]
    d2 = any(re.search(r"((.)\2{2,}){2,}", t) for t in joined)
    return {"D1": bool(futhark_spans(st)), "D2": d2, "D3": bool(tandems(st, 4)),
            "D4": bool(D4RE.search(norm_plain(r))), "runes": sum(len(g) for s in st for g in s)}


rows = [r for r in rl.load_rundata() if rl.viking(r)]
T = {r["signum"]: traits(r) | {"kind": rl.object_kind(r)} for r in rows}
T[MALT]["D2_source"] = "utgåvorna (tecknet ttt); Rundata har ?"
T[MALT]["D2"] = True
prof = sorted(({"signum": s, "n": sum(t[k] for k in ("D1", "D2", "D3", "D4")), **{k: t[k] for k in ("D1", "D2", "D3", "D4", "kind")}}
               for s, t in T.items() if sum(t[k] for k in ("D1", "D2", "D3", "D4")) >= 2), key=lambda x: (-x["n"], x["signum"]))
res = {"plan": "analysplaner/2026-11-01-malt-runmasteri.md", "plan_sha": "8a137566", "malt": T[MALT], "profile_2plus": prof,
       "counts": {k: sum(t[k] for s, t in T.items() if s != MALT and t["runes"] >= 10) for k in ("D1", "D2", "D3", "D4")}}


def test(sigs):
    a = sum(1 for s in sigs if T[s]["D1"] and (T[s]["D2"] or T[s]["D3"] or T[s]["D4"]))
    b = sum(1 for s in sigs if T[s]["D1"]) - a
    c = sum(1 for s in sigs if not T[s]["D1"] and (T[s]["D2"] or T[s]["D3"] or T[s]["D4"]))
    d = sum(1 for s in sigs if not T[s]["D1"]) - c
    p = fisher_exact([[a, b], [c, d]], alternative="greater")[1]
    return {"with_row": [a, a + b], "without_row": [c, c + d], "share_with": a / max(1, a + b), "share_without": c / max(1, c + d), "p": float(p)}


base = sorted((s for s, t in T.items() if s != MALT and t["runes"] >= 10), key=lambda s: (s.split(" ")[0], s))
res["test"] = test(base)
res["test_halves"] = [test(base[i::2]) for i in (0, 1)]
res["test_runestones"] = test([s for s in base if T[s]["kind"] == "runsten"])
res["test_other"] = test([s for s in base if T[s]["kind"] != "runsten"])
h = res["test_halves"]
res["holds"] = bool(res["test"]["p"] < 0.05) and all(x["share_with"] > x["share_without"] for x in h)

# ---- del 3: blind set --------------------------------------------------------------------------------------------
by = {r["signum"]: r for r in rows}
EIGHT = ["DR 239", "DR EM85;371A", "G 110", "GR 76", "U 466", "U 483", "U 522", "U Fv1992;161C"]
assert all(T[s]["D1"] for s in EIGHT)
rng = random.Random(2026)
pool = sorted(s for s, t in T.items() if s != MALT and not t["D1"] and 20 <= t["runes"] <= 200)
others = rng.sample(pool, 16)
items = EIGHT + others
rng.shuffle(items)


def hide(txt):
    return re.sub(r"<[^>]*(fuþ|hnias|tbmlR)[^>]*>", "[runrad]", txt or "")


blind = [{"id": f"t{i + 1:02d}", "normalization": hide(by[s].get("normalization")), "translation_en": hide(by[s].get("translation_en"))}
         for i, s in enumerate(items)]
key = {f"t{i + 1:02d}": s for i, s in enumerate(items)}
json.dump({"items": blind}, open(os.path.join(HERE, "runmasteri_blind_underlag.json"), "w"), ensure_ascii=False, indent=1)
res["blind_key"] = key
json.dump(res, open(os.path.join(HERE, "runmasteri.json"), "w"), ensure_ascii=False, indent=1)
print(json.dumps({k: res[k] for k in ("malt", "counts", "test", "test_halves", "test_runestones", "test_other", "holds")}, ensure_ascii=False, indent=1))
for x in prof:
    print(x)
