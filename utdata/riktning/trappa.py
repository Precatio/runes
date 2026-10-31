"""Robusthetsstegen för H2 (ristningen vänd mot vägen) enligt den låsta tilläggsplanen
analysplaner/2026-10-31-riktning-trappan.md. Samma stenar och samma mått som analys.py (planen 2026-10-29).
    .venv/bin/python utdata/riktning/trappa.py      Skriver trappan.json."""
import json
import os
import re
import sys

import numpy as np
import pandas as pd

OUT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(OUT, "..", ".."))
sys.path.insert(0, ROOT)
from src import robustness  # noqa: E402

NPERM = 9999
rng = np.random.default_rng(2026)
d = pd.read_csv(os.path.join(OUT, "stenar.csv"))
v = d[d.vag.notna()].reset_index(drop=True)
assert (len(d), len(v)) == (219, 123)
c = pd.read_csv(os.path.join(ROOT, "data", "cache", "r", "corpus", "e83202e01a5e6d27", "corpus.csv"), low_memory=False).set_index("signum")
v["parish"] = v.signum.map(lambda s: c.parish.get(s)).fillna("_" + v.signum)
v["carver"] = v.signum.map(lambda s: c.carver.get(s) if c.carvers_uncertain.get(s) == 0 else None)
v["moved_now"] = v.signum.map(lambda s: int(c.moved.get(s, 1) != 0 or c.lost.get(s, 1) != 0))
RUNOR = robustness._runor_moved()
v["moved_runor"] = v.signum.isin(RUNOR).astype(int)
REERECT = re.compile(r"återrest|återupprest|rest upp|restes upp|uppsatt|uppställd|lagad|lagades|lagats|reparerad", re.I)
kmr = {}
for r in json.load(open(os.path.join(ROOT, "data", "raa", "kmr_runstenar.json"), encoding="utf-8"))["records"]:
    t = " ".join(" ".join(r["fields"].get(k, [])) for k in ("Beskrivning", "Placering", "Skadestatus", "Orientering"))
    for s in r["signa"]:
        kmr[s] = kmr.get(s, "") + " " + t
rd = {r["signum"]: f"{r.get('placement') or ''} {r.get('other') or ''}" for r in json.load(open(os.path.join(ROOT, "data", "rundata.json")))["inscriptions"]}
v["reerected"] = v.signum.map(lambda s: int(bool(REERECT.search(kmr.get(s, "") + " " + rd.get(s, "")))))
d["reerected"] = d.signum.map(lambda s: int(bool(REERECT.search(kmr.get(s, "") + " " + rd.get(s, "")))))


def perm_idx(x):
    out = np.arange(len(x))
    for _, g in x.groupby("province").indices.items():
        out[g] = rng.permutation(g)
    return out


def test(x, by_parish=False):
    x = x.reset_index(drop=True)
    f, t = x.riktning.to_numpy(), x.vag.to_numpy()
    groups = x.parish.to_numpy() if by_parish else None

    def stat(ff):
        cs = np.cos(np.radians(ff - t))
        return pd.Series(cs).groupby(groups).mean().mean() if by_parish else cs.mean()
    obs = stat(f)
    sims = np.array([stat(f[perm_idx(x)]) for _ in range(NPERM)])
    return {"n": len(x), "medel_cos": float(obs), "vantat": float(sims.mean()), "p": float((1 + (sims >= obs).sum()) / (NPERM + 1)),
            "andel_inom_45": float((np.abs((f - t + 180) % 360 - 180) <= 45).mean())}


def holds(r):
    return bool(r["medel_cos"] > r["vantat"] and r["p"] < 0.05)


rungs = {}
rungs["huvud"] = test(v)
rungs["halva_A"] = test(v[v.half == "A"])
rungs["halva_B"] = test(v[v.half == "B"])
lopo = {}
for pv in [p for p, n in v.province.value_counts().items() if n >= 10]:
    r = test(v[v.province != pv]); r["andel_kvar"] = r["n"] / len(v); lopo[pv] = r
rungs["socken"] = test(v, by_parish=True)
first = v[v.carver.notna()].sort_values("signum").drop_duplicates("carver")
rungs["en_per_ristare"] = test(pd.concat([first, v[v.carver.isna()]]))
rungs["utan_aterresta"] = test(v[v.reerected == 0])
rungs["utan_flyttade_runor"] = test(v[v.moved_runor == 0])
rungs["dagens_flyttregel"] = test(v[v.moved_now == 0])
rungs["bara_text"] = test(v.assign(vag=v.vag_text)[v.vag_text.notna()])
rungs["bara_registrerad"] = test(v.assign(vag=v.vag_reg)[v.vag_reg.notna()])
for k, r in rungs.items():
    r["holds"] = holds(r)
lopo_ok = all(r["medel_cos"] > r["vantat"] and (r["andel_kvar"] < 2 / 3 or r["p"] < 0.05) for r in lopo.values())
out = {"plan": "analysplaner/2026-10-31-riktning-trappan.md", "rungs": rungs, "lopo": lopo, "lopo_holds": lopo_ok,
       "n_reerected": int(v.reerected.sum()), "n_reerected_alla_219": int(d.reerected.sum()),
       "n_moved_runor": int(v.moved_runor.sum()), "n_moved_now": int(v.moved_now.sum()),
       "n_carvers": int(first.carver.nunique()), "n_parishes": int(v.parish.nunique()),
       "all_hold": bool(all(r["holds"] for r in rungs.values()) and lopo_ok)}
json.dump(out, open(os.path.join(OUT, "trappan.json"), "w"), ensure_ascii=False, indent=1)
for k, r in rungs.items():
    print(f"{k:22s} n {r['n']:4d}  cos {r['medel_cos']:.3f} mot {r['vantat']:.3f}  inom 45° {r['andel_inom_45']:.2f}  p {r['p']:.4f}  {'HÅLLER' if r['holds'] else 'HÅLLER INTE'}")
for pv, r in lopo.items():
    print(f"  utan {pv:3s} n {r['n']:4d} (kvar {r['andel_kvar']:.2f})  cos {r['medel_cos']:.3f} mot {r['vantat']:.3f}  p {r['p']:.4f}")
print("utan ett landskap:", "HÅLLER" if lopo_ok else "HÅLLER INTE", "| återresta", out["n_reerected"], "(av 219:", out["n_reerected_alla_219"], ") Runor-flyttade", out["n_moved_runor"],
      "dagens flyttregel bort", out["n_moved_now"], "| ristare", out["n_carvers"], "socknar", out["n_parishes"], "| ALLA:", out["all_hold"])
