"""Känslighetskontroll 2026-10-31 (efter provet, explorativ): det skarpa provet (led F) utan Sö 113, den sten som
spårläsarens parametrar ställdes in på. Samma parade Wilcoxon-test på p_truth som led_f_summering.py.
    .venv/bin/python utdata/sparlasare/utan_so113.py      Skriver utan_so113.json."""
import glob
import json
import os

import numpy as np
from scipy.stats import wilcoxon

HERE = os.path.dirname(os.path.abspath(__file__))
rows = []
for f in sorted(glob.glob(os.path.join(HERE, "led_f_Sö_*.json"))):
    rows += [r for r in json.load(open(f, encoding="utf-8"))["rows"] if all(r.get(c) for c in ("utan", "skanner", "omflyttad"))]


def summ(rs):
    out = {"n": len(rs), "stones": len({r["sig"] for r in rs})}
    out["means"] = {c: {k: float(np.mean([r[c][k] for r in rs])) for k in ("word_ok", "right", "p_truth")} for c in ("utan", "skanner", "omflyttad")}
    for a, b, alt in (("skanner", "utan", "greater"), ("skanner", "omflyttad", "greater"), ("omflyttad", "utan", "two-sided")):
        d = np.array([r[a]["p_truth"] - r[b]["p_truth"] for r in rs])
        out[f"{a}_vs_{b}"] = {"mean_diff": float(d.mean()), "n_changed": int((d != 0).sum()), "p": float(wilcoxon(d[d != 0], alternative=alt).pvalue)}
    return out


res = {"alla": summ(rows), "utan_So_113": summ([r for r in rows if r["sig"] != "Sö 113"])}
json.dump(res, open(os.path.join(HERE, "utan_so113.json"), "w"), ensure_ascii=False, indent=1)
for k, v in res.items():
    print(k, v["n"], v["stones"], {c: round(v["means"][c]["word_ok"], 3) for c in v["means"]},
          {t: f"{v[t]['p']:.2g}" for t in ("skanner_vs_utan", "skanner_vs_omflyttad", "omflyttad_vs_utan")})
