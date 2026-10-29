"""Namngivning i familjen enligt den låsta planen analysplaner/2026-10-29-namngivning-i-familjen.md.
    .venv/bin/python utdata/namngivning/analys.py      Skriver par.csv och namngivning.json."""
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
def initial(k):
    return "th" if k.startswith("th") else "V" if k[0] in "aeiouyøæǫ" else k[0]

def shares(a, b):
    return np.array([bool(PARTS[x] & PARTS[y]) or x == y for x, y in zip(a, b)], dtype=float)
def allit(a, b):
    return np.array([initial(x) == initial(y) for x, y in zip(a, b)], dtype=float)

def perm_within(df, strata):
    idx = np.arange(len(df))
    out = idx.copy()
    for _, g in df.groupby(strata).indices.items():
        out[g] = rng.permutation(g)
    return out

def onesided(df, a, b, fn, strata="province"):
    if len(df) == 0:
        return {"par": 0}
    av, bv = df[a].to_numpy(), df[b].to_numpy()
    obs = fn(av, bv).mean()
    sims = np.array([fn(av, bv[perm_within(df, strata)]).mean() for _ in range(NPERM)])
    return {"par": len(df), "andel": float(obs), "vantat": float(sims.mean()), "p": float((1 + (sims >= obs).sum()) / (NPERM + 1))}

def expected_share(df):
    """Väntad andel delat led per par vid omblandning inom landskap × tidsskikt (1 999 omblandningar)."""
    av, bv = df.foralder.to_numpy(), df.barn.to_numpy()
    acc = np.zeros(len(df))
    for _ in range(1999):
        acc += shares(av, bv[perm_within(df, ["province", "skikt"])])
    return acc / 1999

def diff_test(df, label):
    d = df[df[label].notna()].copy()
    if d[label].nunique() < 2:
        return {"par": len(d)}
    ex = d.obs - d.exp
    lab = d[label].to_numpy().astype(int)
    stat = lambda l: ex[l == 1].mean() - ex[l == 0].mean()
    obs = stat(lab)
    sims = []
    for _ in range(NPERM):
        l2 = lab.copy()
        for _, g in d.reset_index().groupby("province").indices.items():
            l2[g] = rng.permutation(l2[g])
        sims.append(stat(l2))
    sims = np.array(sims)
    lo, hi = (1 + (sims <= obs).sum()) / (NPERM + 1), (1 + (sims >= obs).sum()) / (NPERM + 1)
    return {"par": len(d), "n_1": int(lab.sum()), "overskott_1": float(ex[lab == 1].mean()),
            "overskott_0": float(ex[lab == 0].mean()), "skillnad": float(obs), "p": float(min(1, 2 * min(lo, hi)))}

pc["skikt"] = np.where(pc["style"].isin(EARLY), "tidig", np.where(pc["style"].isin(LATE), "sen", "odaterad"))
pc["sen"] = np.where(pc.skikt == "sen", 1, np.where(pc.skikt == "tidig", 0, np.nan))
pc["kr"] = pc.kristen
pc["obs"] = shares(pc.foralder, pc.barn)
pc["allit"] = allit(pc.foralder, pc.barn)
pc["exp"] = expected_share(pc)
pc.to_csv(os.path.join(OUT, "par.csv"), index=False)

res = {}
for h in ("alla", "A", "B"):
    d = pc if h == "alla" else pc[pc.half == h]
    s = sib if h == "alla" else sib[sib.half == h]
    res[h] = {"H1": onesided(d, "foralder", "barn", shares), "H2": onesided(d, "foralder", "barn", allit),
              "H3": diff_test(d, "sen"), "H4": diff_test(d, "kr"), "H5": onesided(s, "a", "b", shares)}
ps = {k: res["alla"][k].get("p", 1.0) for k in ("H1", "H2", "H3", "H4", "H5")}
order = sorted(ps, key=ps.get); holm, run = {}, 0.0
for i, k in enumerate(order):
    run = max(run, min(1.0, (len(ps) - i) * ps[k])); holm[k] = run
def direction(r, k):
    return np.sign(r["andel"] - r["vantat"]) if k in ("H1", "H2", "H5") else np.sign(r.get("skillnad", 0))
status = {}
for k in ps:
    both = all(res[h][k].get("p", 1) < 0.05 and direction(res[h][k], k) == direction(res["alla"][k], k) for h in "AB")
    status[k] = "håller" if holm[k] < 0.05 and both else "antydan" if holm[k] < 0.05 or ps[k] < 0.05 else "ingen skillnad påvisad"

# ---- beskrivning ---------------------------------------------------------------------------------------------------
shared = Counter(e for a, b in zip(pc.foralder, pc.barn) for e in (PARTS[a] & PARTS[b]) if a != b)
desc = {"par": len(pc), "syskonpar": len(sib), "samma_namn": int((pc.foralder == pc.barn).sum()),
        "vanligaste_arvda_led": shared.most_common(20),
        "per_skikt": pc.groupby("skikt").apply(lambda g: {"par": len(g), "delat": float(g.obs.mean()),
                                                          "vantat": float(g.exp.mean()), "allit": float(g.allit.mean())}).to_dict(),
        "mor_vs_far": pc.assign(mor=pc.rel.str.startswith("mother")).groupby("mor").apply(
            lambda g: {"par": len(g), "delat": float(g.obs.mean()), "vantat": float(g.exp.mean())}).to_dict(),
        "exempel_samma_namn": pc[pc.foralder == pc.barn][["signum", "foralder", "rel"]].to_dict("records"),
        "exempel_delat": pc[(pc.obs == 1) & (pc.foralder != pc.barn)][["signum", "foralder", "barn"]].head(40).to_dict("records")}
out = {"plan": "analysplaner/2026-10-29-namngivning-i-familjen.md", "resultat": res, "holm": holm, "status": status,
       "beskrivning": desc}
json.dump(out, open(os.path.join(OUT, "namngivning.json"), "w"), ensure_ascii=False, indent=1, default=str)
print("par", len(pc), "syskonpar", len(sib), "samma namn", desc["samma_namn"])
for k in ps:
    print(k, status[k], "holm", round(holm[k], 5), {h: {kk: (round(v, 4) if isinstance(v, float) else v) for kk, v in res[h][k].items()} for h in ("alla", "A", "B")})
print("per skikt", desc["per_skikt"]); print("mor/far", desc["mor_vs_far"]); print("led", desc["vanligaste_arvda_led"])
