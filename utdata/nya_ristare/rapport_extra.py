"""Kompletterande beskrivande siffror till metodrapporten (granskningen 2026-11-24): sammanslagna andelar, slutprov 1 per
landskap, parsannolikheternas kalibrering, Holm över proven och stabiliteten. Inget prov – provdelens grupper läses ur
slutprov_P.json som redan är kört.
    .venv/bin/python utdata/nya_ristare/rapport_extra.py"""
import json
import os
import sys
from collections import defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
from utdata.nya_ristare.belagg import MAXD, load  # noqa: E402

J = lambda f: json.load(open(os.path.join(HERE, f), encoding="utf-8"))  # noqa: E731
S1, S2, H = J("slutprov_P.json"), J("slutprov2.json"), J("huggteknik.json")
out = {}
# sammanslagna andelar (par, inte medel per grupp)
for name, gs, key in (("slutprov1_alla", S1["grupper"], "samma_grupp"), ("slutprov2_T1", S2["grupper"], "samma_grupp")):
    n = sum(g["par"] for g in gs)
    k = sum(round(g[key] * g["par"]) for g in gs)
    out[name + "_sammanslaget"] = {"par": n, "samma": k, "andel": round(k / n, 3)}
# slutprov 1 per landskap (gruppens landskap = de flesta stenarnas)
by = defaultdict(list)
for g in S1["grupper"]:
    prov = max(set(s.split()[0] for s in g["stenar"]), key=[s.split()[0] for s in g["stenar"]].count)
    by[prov].append(g)
out["slutprov1_per_landskap"] = {p: {"grupper": len(v), "samma": round(float(np.mean([g["samma_grupp"] for g in v])), 2),
                                     "kontroll": round(float(np.mean([g["kontroll"] for g in v])), 3)} for p, v in sorted(by.items(), key=lambda kv: -len(kv[1]))}
# grupper i provdelen som föll bort (inget par inom 30 km bland de 2 314 stenarna)
d = J("delning.json")
out["provdelens_grupper"] = sum(1 for g in d["grupper"] if g["del"] == "P")
out["provdelens_grupper_med_par"] = len(S1["grupper"])
# kalibrering: parsannolikhet mot andel samma ristare, på par av säkra stenar (sannolikheten från en modell som inte sett ristaren)
st = load()
M = np.load(os.path.join(ROOT, "data", "cache", "hander", "parsannolikhet_M1.npy")).astype(float)
cert = {st.ix[s]: c for s, c in st.certain.items() if s in st.ix}
ci = np.array(sorted(cert))
iu = np.triu_indices(len(ci), 1)
A, B = ci[iu[0]], ci[iu[1]]
near = st.D[A, B] <= MAXD
p = M[A, B][near]
y = np.array([cert[a] == cert[b] for a, b in zip(A[near], B[near])])
ok = ~np.isnan(p)
p, y = p[ok], y[ok]
bins = [0, 0.2, 0.4, 0.6, 0.8, 0.9, 1.0001]
cal = []
for lo, hi in zip(bins[:-1], bins[1:]):
    m = (p >= lo) & (p < hi)
    if m.sum():
        cal.append({"från": lo, "till": min(hi, 1.0), "par": int(m.sum()), "medel_p": round(float(p[m].mean()), 3), "andel_samma": round(float(y[m].mean()), 3)})
out["kalibrering"] = cal
out["grundnivå_samma_ristare"] = round(float(y.mean()), 3)
# Holm över de fem förregistrerade proven
ps = {"S1": S1["alla"]["p"], "S2": S1["onämnda"]["p"], "T1": S2["T1"]["p"], "T2": S2["T2"]["p"], "H3D": H["H3D"]["p"]}
order = sorted(ps, key=ps.get)
holm, mx = {}, 0
for i, k in enumerate(order):
    mx = max(mx, min(1.0, (len(ps) - i) * ps[k]))
    holm[k] = round(mx, 5)
out["holm"] = holm
# stabiliteten i appens grupper
hg = json.load(open(os.path.join(ROOT, "data", "cache", "r", "corpus", "510ebfb3acc9a229", "hand_groups.json"), encoding="utf-8"))
stab = [g["stability"] for g in hg["groups"]]
out["stabilitet"] = {"median": round(float(np.median(stab)), 2), "lika_med_1": int(sum(s == 1.0 for s in stab)), "grupper": len(stab)}
json.dump(out, open(os.path.join(HERE, "rapport_extra.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False, indent=1))
