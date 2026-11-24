"""Slutprov 3 (analysplaner/2026-11-24-nya-ristare-ornamentik.md): gör ornamentiken grupperna bättre? Andra användningen
av facits provdel. Körs bara om grinden på utvecklingsdelen höll (m2_utveckling.json) – annars avbryts det.

    .venv/bin/python utdata/nya_ristare/ornamentik/slutprov3.py
Skriver utdata/nya_ristare/ornamentik/slutprov3.json och en rad i utdata/nya_ristare/provdelen_logg.md.
"""
import datetime as dt
import hashlib
import itertools
import json
import os
import sys

import numpy as np
from scipy.stats import wilcoxon

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)
from utdata.nya_ristare.belagg import MAXD, load  # noqa: E402
from utdata.nya_ristare.ornamentik.m2 import labels_at  # noqa: E402

PLAN = os.path.join(ROOT, "analysplaner", "2026-11-24-nya-ristare-ornamentik.md")
assert hashlib.sha256(open(PLAN, "rb").read()).hexdigest().startswith(open(PLAN + ".sha256").read()[:8]), "planen ändrad"
CACHE = os.path.join(ROOT, "data", "cache", "hander")
dev = json.load(open(os.path.join(HERE, "m2_utveckling.json"), encoding="utf-8"))
if not dev["grind_håller"]:
    sys.exit("Grinden på utvecklingsdelen höll inte – provdelen öppnas inte (planen).")

st = load()
N = len(st.sig)
L1 = labels_at(np.load(os.path.join(CACHE, "sammanslagningar_M1_hg.npy")), N, 0.8)
L2 = labels_at(np.load(os.path.join(CACHE, "sammanslagningar_M2.npy")), N, dev["tau2"])
coded = set(json.load(open(os.path.join(CACHE, "ornamentik", "orn_koder.json"), encoding="utf-8")))
cert = {st.ix[s] for s in st.certain if s in st.ix}


def share(lab, pairs):
    return float(np.mean([lab[a] == lab[b] for a, b in pairs]))


def control(lab, gi, pairs):
    ctrl = []
    for a, b in pairs:
        for x, y in ((a, b), (b, a)):
            d = st.D[x, y]
            lo, hi = min(d * 0.75, d - 1000), min(max(d * 1.25, d + 1000), MAXD)
            ok = np.where((st.D[x] >= lo) & (st.D[x] <= hi))[0]
            ok = ok[~np.isin(ok, gi)]
            if len(ok):
                ctrl.append(float(np.mean(lab[ok] == lab[x])))
    return float(np.mean(ctrl)) if ctrl else None


def groups_of(part):
    split = json.load(open(os.path.join(ROOT, "utdata", "nya_ristare", "delning.json"), encoding="utf-8"))
    for g in split["grupper"]:
        if g["del"] != part:
            continue
        gi = [st.ix[s] for s in g["stenar"] if s in st.ix]
        pairs = [(a, b) for k, a in enumerate(gi) for b in gi[k + 1:] if st.D[a, b] <= MAXD]
        if pairs:
            yield g["stenar"], gi, pairs


def paired(rows):
    d = [r["M2"] - r["M1"] for r in rows]
    nz = [x for x in d if x != 0]
    if len(nz) < 5:
        return {"grupper": len(d), "med_skillnad": len(nz), "håller": False, "för_få": True}
    p = float(wilcoxon(nz, alternative="greater").pvalue)
    return {"grupper": len(d), "med_skillnad": len(nz), "bättre": sum(x > 0 for x in nz), "sämre": sum(x < 0 for x in nz),
            "medel_M1": round(float(np.mean([r["M1"] for r in rows])), 3),
            "medel_M2": round(float(np.mean([r["M2"] for r in rows])), 3),
            "medelskillnad": round(float(np.mean(d)), 3), "p": p, "håller": bool(p < 0.05 and np.mean(d) > 0)}


rows, s1 = [], []
for stenar, gi, pairs in groups_of("P"):
    covered = any(st.sig[a] in coded and st.sig[b] in coded for a, b in pairs)
    r = {"stenar": stenar, "par": len(pairs), "avbildat_par": covered, "onämnd": not any(i in cert for i in gi),
         "M1": share(L1, pairs), "M2": share(L2, pairs), "kontroll_M2": control(L2, gi, pairs)}
    s1.append(r)
    if covered:
        rows.append(r)
O1 = paired(rows)
O1_onamnda = paired([r for r in rows if r["onämnd"]])
d2 = [r["M2"] - r["kontroll_M2"] for r in s1 if r["kontroll_M2"] is not None]
p2 = float(wilcoxon(d2, alternative="greater").pvalue)
O2 = {"grupper": len(d2), "medel_samma": round(float(np.mean([r["M2"] for r in s1])), 3),
      "medel_kontroll": round(float(np.mean([r["kontroll_M2"] for r in s1 if r["kontroll_M2"] is not None])), 3), "p": p2}
O2["håller"] = bool(p2 < 0.05 and O2["medel_samma"] > O2["medel_kontroll"])

# beskrivande: litteraturens facit 2 och granskade par om olika händer
lit = json.load(open(os.path.join(CACHE, "lit_facit2_granskat.json"), encoding="utf-8"))
f2 = [(st.ix[a], st.ix[b]) for a, b, _ in lit["samma_hand"] if a in st.ix and b in st.ix and st.D[st.ix[a], st.ix[b]] <= MAXD]
diff = [(st.ix[a], st.ix[b]) for a, b, _ in lit["olika_hander"] if a in st.ix and b in st.ix and st.D[st.ix[a], st.ix[b]] <= MAXD]
beskr = {"facit2_par": len(f2), "facit2_M1": share(L1, f2) if f2 else None, "facit2_M2": share(L2, f2) if f2 else None,
         "olika_händer_par": len(diff), "olika_i_samma_grupp_M1": int(sum(L1[a] == L1[b] for a, b in diff)),
         "olika_i_samma_grupp_M2": int(sum(L2[a] == L2[b] for a, b in diff))}
for name, L in (("M1", L1), ("M2", L2)):
    ids, cnt = np.unique(L, return_counts=True)
    big = set(ids[cnt >= 3])
    beskr[f"grupper_{name}"] = len(big)
    beskr[f"grupper_utan_säker_{name}"] = sum(1 for g in big if not any(L[i] == g for i in cert))
out = {"plan": os.path.basename(PLAN), "tau2": dev["tau2"], "O1": O1, "O1_onämnda": O1_onamnda, "O2": O2,
       "beskrivande": beskr, "grupper": s1}
json.dump(out, open(os.path.join(HERE, "slutprov3.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
with open(os.path.join(ROOT, "utdata", "nya_ristare", "provdelen_logg.md"), "a", encoding="utf-8") as f:
    f.write(f"- {dt.date.today()}: slutprov 3 (plan {os.path.basename(PLAN)}), M2 vid τ₂ = {dev['tau2']} mot M1 vid 0,8: "
            f"O1 {O1}, O2 {O2}\n")
print(json.dumps({k: out[k] for k in ("tau2", "O1", "O1_onämnda", "O2", "beskrivande")}, ensure_ascii=False, indent=1))
