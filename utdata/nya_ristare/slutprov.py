"""Slutprovet för grupperna (metoden M1 + UPGMA, τ ur utvecklingsdelen) mot en del av facit.

    .venv/bin/python utdata/nya_ristare/slutprov.py U    # utvecklingsdelen (fritt)
    .venv/bin/python utdata/nya_ristare/slutprov.py P    # provdelen – bara under låst plan, loggas

Per facitgrupp (par inom 30 km): andelen par i samma grupp, mot grannkontrollen (för varje par: stenar på samma avstånd
från a, ± 25 %, minst ± 1 km, högst 30 km, utanför facitgruppen; andelen av dem i a:s grupp; medel). Ensidigt Wilcoxon
över grupperna; alla grupper och bara onämnda (ingen sten med säker ristare).
"""
import datetime as dt
import hashlib
import json
import os
import sys

import numpy as np
from scipy.stats import wilcoxon

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
from utdata.nya_ristare.belagg import MAXD, load  # noqa: E402

DEL = sys.argv[1]
TAU = 0.8
if DEL == "P":
    plan = os.path.join(ROOT, "analysplaner", "2026-11-23-nya-ristare-slutprov-1.md")
    assert hashlib.sha256(open(plan, "rb").read()).hexdigest().startswith(open(plan + ".sha256").read()[:8])
st = load()
N = len(st.sig)
merges = np.load(os.path.join(ROOT, "data", "cache", "hander", "sammanslagningar_M1.npy"))
lab = np.arange(N)
for i, j, s in merges:
    if s < TAU:
        break
    lab[lab == lab[int(j)]] = lab[int(i)]
split = json.load(open(os.path.join(HERE, "delning.json"), encoding="utf-8"))
cert = {st.ix[s] for s in st.certain if s in st.ix}
res = []
for g in split["grupper"]:
    if g["del"] != DEL:
        continue
    gi = [st.ix[s] for s in g["stenar"] if s in st.ix]
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
    if not ctrl:
        continue
    res.append({"stenar": g["stenar"], "par": len(pairs), "samma_grupp": obs, "kontroll": float(np.mean(ctrl)),
                "onämnd": not any(i in cert for i in gi)})


def test(rs):
    d = [r["samma_grupp"] - r["kontroll"] for r in rs]
    if len(d) < 5 or not any(d):
        return {"grupper": len(d), "obestämt": True}
    return {"grupper": len(d), "medel_samma": round(float(np.mean([r["samma_grupp"] for r in rs])), 3),
            "medel_kontroll": round(float(np.mean([r["kontroll"] for r in rs])), 3), "median_skillnad": round(float(np.median(d)), 3),
            "bättre": int(sum(x > 0 for x in d)), "sämre": int(sum(x < 0 for x in d)),
            "p": float(wilcoxon(d, alternative="greater").pvalue)}


out = {"del": DEL, "tau": TAU, "alla": test(res), "onämnda": test([r for r in res if r["onämnd"]]), "grupper": res}
print(json.dumps({k: out[k] for k in ("del", "tau", "alla", "onämnda")}, ensure_ascii=False, indent=1))
json.dump(out, open(os.path.join(HERE, f"slutprov_{DEL}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
if DEL == "P":
    with open(os.path.join(HERE, "provdelen_logg.md"), "a", encoding="utf-8") as f:
        f.write(f"- {dt.date.today()}: slutprov 1 (plan 2026-11-23-nya-ristare-slutprov-1.md), M1 + UPGMA τ = {TAU}: "
                f"alla {out['alla']}, onämnda {out['onämnda']}\n")
