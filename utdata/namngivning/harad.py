"""EXPLORATIVT, utanför den låsta planen (2026-10-31): H1 och H5 med omblandningen inom härad i stället för landskap,
för att se hur mycket av överskottet som är bygdens namnförråd snarare än arv. Paren och måttet som i trappa.py.
    .venv/bin/python utdata/namngivning/harad.py      Skriver harad.json.
Ursprunglig beskrivning: Robusthetsstegen för H1 och H5 (delat namnled, förälder–barn och syskon) enligt den låsta tilläggsplanen
analysplaner/2026-10-31-namnled-trappan.md. Paren, leddelningen och måttet byggs exakt som i analys.py (kopierat nedan).
    .venv/bin/python utdata/namngivning/trappa.py      Skriver trappan.json."""
import json
import os
import sys
from collections import Counter
from itertools import combinations

import numpy as np
import pandas as pd

OUT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(OUT, "..", ".."))
sys.path.insert(0, ROOT)
from src import entities  # noqa: E402

NPERM = 9999
EARLY, LATE = {"RAK", "Fp", "Pr1", "Pr2"}, {"Pr3", "Pr4", "Pr5"}
PARENT = {"father", "mother", "förälder till"}          # a är b:s förälder
CHILD = {"son", "sons", "daughter"}                       # a är b:s barn
SIB = {"brother", "brothers", "sister", "sisters"}
rng = np.random.default_rng(2026)

c = pd.read_csv(os.path.join(ROOT, "data", "cache", "r", "corpus", "3f58e9339191761e", "corpus.csv"), low_memory=False)
recs = {r["signum"]: r for r in json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["inscriptions"]}
# Halvorna socken för socken som i change.R
c["t50"] = ((c.style_from + c.style_to) / 2 - 1050) / 50
c["pk"] = c.parish.fillna("_" + c.signum)
pi = c.groupby(["province", "pk"]).agg(mt=("t50", "mean"), n=("t50", "size")).reset_index()
pi = pi.sort_values(["province", "mt", "n"], ascending=[True, True, False], na_position="last")
pi["half"] = pi.groupby("province").cumcount().map(lambda r: "A" if r % 2 == 0 else "B")
c = c.merge(pi[["province", "pk", "half"]], on=["province", "pk"])

pc, sib, keys_all = [], [], Counter()
for _, s in c.iterrows():
    x = entities.extract(recs[s.signum])
    meta = {"signum": s.signum, "province": s.province, "pk": s.pk, "half": s.half, "style": s["style"],
            "kristen": s.cat_kristen}
    for p in x["persons"]:
        keys_all[p["key"]] += 1
    kids = {}
    for a, rel, b in x["facts"]:
        if rel in PARENT:
            pc.append({**meta, "foralder": a, "barn": b, "rel": rel}); kids.setdefault(a, set()).add(b)
        elif rel in CHILD:
            pc.append({**meta, "foralder": b, "barn": a, "rel": rel}); kids.setdefault(b, set()).add(a)
        elif rel in SIB:
            sib.append({**meta, "a": a, "b": b})
    raisers = {p["key"] for p in x["persons"] if p["role"] == "resare"}
    for p in x["persons"]:   # samma namnnyckel som resare och som död förälder/son: namnet upprepat
        if p["role"] == "minnes" and p["key"] in raisers and p.get("rel") in ("father", "mother", "son"):
            pc.append({**meta, "foralder": p["key"], "barn": p["key"], "rel": p["rel"] + " (samma namn)"})
    for par, ks in kids.items():
        for a, b in combinations(sorted(ks), 2):
            sib.append({**meta, "a": a, "b": b})
pc = pd.DataFrame(pc).drop_duplicates(["foralder", "barn", "pk"])
sib = pd.DataFrame(sib)
sib[["a", "b"]] = np.sort(sib[["a", "b"]].to_numpy(), axis=1)
sib = sib[sib.a != sib.b].drop_duplicates(["a", "b", "pk"])

# ---- namnled ---------------------------------------------------------------------------------------------------------
names = sorted(k for k in keys_all if k and not k.endswith("-"))
def parts(k):
    best, score = None, 0
    for i in range(2, len(k) - 1):
        pre, suf = k[:i], k[i:]
        npre = sum(1 for o in names if o != k and o.startswith(pre))
        nsuf = sum(1 for o in names if o != k and o.endswith(suf))
        if npre >= 3 and nsuf >= 3 and min(npre, nsuf) > score:
            best, score = (pre, suf), min(npre, nsuf)
    return set(best) if best else {k}
PARTS = {k: parts(k) for k in set(pc.foralder) | set(pc.barn) | set(sib.a) | set(sib.b)}
def perm_within(df, strata):
    idx = np.arange(len(df))
    out = idx.copy()
    for _, g in df.groupby(strata).indices.items():
        out[g] = rng.permutation(g)
    return out

JUNK = {"ni", "bbi", "einn"}
PARTS2 = {k: ({p for p in v if len(p) >= 3 and p not in JUNK} or ({k} if len(v) == 1 else set())) for k, v in PARTS.items()}
STYLE = dict(zip(c.signum, c["style"]))
for df in (pc, sib):
    st = df.signum.map(STYLE)
    df["skikt"] = np.where(st.isin(EARLY), "tidig", np.where(st.isin(LATE), "sen", "odaterad"))
pc = pc.reset_index(drop=True); sib = sib.reset_index(drop=True)
NAMES = sorted(set(pc.foralder) | set(pc.barn) | set(sib.a) | set(sib.b)); IX = {k: i for i, k in enumerate(NAMES)}


def matrix(fn):
    return np.array([[fn(x, y) for y in NAMES] for x in NAMES], dtype=float)


M = {"main": matrix(lambda x, y: bool(PARTS[x] & PARTS[y]) or x == y),
     "kort": matrix(lambda x, y: bool(PARTS2[x] & PARTS2[y]) or x == y),
     "bara_led": matrix(lambda x, y: x != y and bool(PARTS[x] & PARTS[y]))}


def test(df, a, b, m="main", strata="province"):
    df = df.reset_index(drop=True)
    ia, ib = df[a].map(IX).to_numpy(), df[b].map(IX).to_numpy()
    S = M[m]
    obs = S[ia, ib].mean()
    sims = np.array([S[ia, ib[perm_within(df, strata)]].mean() for _ in range(NPERM)])
    r = {"par": len(df), "andel": float(obs), "vantat": float(sims.mean()), "p": float((1 + (sims >= obs).sum()) / (NPERM + 1))}
    r["holds"] = bool(r["andel"] > r["vantat"] and r["p"] < 0.05)
    return r


DIST = dict(zip(c.signum, c.district.fillna("_okänt")))
out = {"explorativt": True}
for key, df, a, b in (("H1", pc, "foralder", "barn"), ("H5", sib, "a", "b")):
    df = df.assign(harad=df.signum.map(DIST)).reset_index(drop=True)
    out[key] = {"landskap": test(df, a, b), "harad": test(df, a, b, strata=["province", "harad"]),
                "n_harader": int(df.harad.nunique())}
    print(key, {k: (round(v["andel"], 4), round(v["vantat"], 4), v["p"]) for k, v in out[key].items() if isinstance(v, dict)}, "härader", out[key]["n_harader"])
json.dump(out, open(os.path.join(OUT, "harad.json"), "w"), ensure_ascii=False, indent=1)
