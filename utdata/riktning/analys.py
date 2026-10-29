"""Ristningens riktning enligt den låsta planen analysplaner/2026-10-29-ristningens-riktning.md.
    .venv/bin/python utdata/riktning/analys.py      Skriver stenar.csv och riktning.json."""
import json
import os
import re
import sys

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

OUT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(OUT, "..", ".."))
sys.path.insert(0, ROOT)
from src import places  # noqa: E402

NPERM = 9999
rng = np.random.default_rng(2026)
STRECK = ["N", "NNÖ", "NÖ", "ÖNÖ", "Ö", "ÖSÖ", "SÖ", "SSÖ", "S", "SSV", "SV", "VSV", "V", "VNV", "NV", "NNV"]
DEG = {s: i * 22.5 for i, s in enumerate(STRECK)}
D = "(" + "|".join(sorted(STRECK, key=len, reverse=True)) + ")"

c = pd.read_csv(os.path.join(ROOT, "data", "cache", "r", "corpus", "3f58e9339191761e", "corpus.csv"), low_memory=False)
c["t50"] = ((c.style_from + c.style_to) / 2 - 1050) / 50
c["pk"] = c.parish.fillna("_" + c.signum)
pi = c.groupby(["province", "pk"]).agg(mt=("t50", "mean"), n=("t50", "size")).reset_index()
pi = pi.sort_values(["province", "mt", "n"], ascending=[True, True, False], na_position="last")
pi["half"] = pi.groupby("province").cumcount().map(lambda r: "A" if r % 2 == 0 else "B")
c = c.merge(pi[["province", "pk", "half"]], on=["province", "pk"]).set_index("signum")

rows = []
for r in json.load(open(os.path.join(ROOT, "data", "raa", "kmr_runstenar.json"), encoding="utf-8"))["records"]:
    b = " ".join(r["fields"].get("Beskrivning", []))
    o = " ".join(r["fields"].get("Orientering", []))
    f = re.findall(r"vetter? mot " + D + r"\b", b)
    sig = [s for s in r["signa"] if s in c.index]
    if len(sig) != 1 or len(set(f)) != 1:
        continue
    s = sig[0]
    if c.loc[s, "moved"] != 0 or c.loc[s, "lost"] != 0 or pd.isna(c.loc[s, "lat"]):
        continue
    m = re.search(r"\b" + D + r" om (?:lands|by|gång|skogs|gammal |gamla )?väg", b + " " + o)
    rows.append({"signum": s, "riktning": DEG[f[0]], "streck": f[0], "province": c.loc[s, "province"],
                 "half": c.loc[s, "half"], "bro": c.loc[s, "cat_bro_vag"], "lat": c.loc[s, "lat"], "lon": c.loc[s, "lon"],
                 "vag_text": (DEG[m.group(1)] + 180) % 360 if m else np.nan})
d = pd.DataFrame(rows)
xy = places._xy(d.lat.to_numpy(float), d.lon.to_numpy(float))


def bearing_to(points, radius):
    t = cKDTree(points)
    dist, idx = t.query(xy)
    dx, dy = points[idx, 0] - xy[:, 0], points[idx, 1] - xy[:, 1]
    b = (np.degrees(np.arctan2(dx, dy)) + 360) % 360
    return np.where(dist <= radius, b, np.nan)


lam = pd.read_csv(os.path.join(ROOT, "data", "raa", "lamningar.csv"))
vm = pd.read_csv(os.path.join(ROOT, "data", "raa", "lamningar_extra", "vägmärke.csv"))
vagp = pd.concat([lam[lam.type.isin(["färdväg", "färdvägssystem"])][["lat", "lon"]], vm[["lat", "lon"]]])
vagxy = places._xy(vagp.lat.to_numpy(float), vagp.lon.to_numpy(float))
by = pd.read_csv(os.path.join(ROOT, "data", "raa", "lamningar_extra", "bytomt_gårdstomt.csv"))
byxy = places._xy(by.lat.to_numpy(float), by.lon.to_numpy(float))
d["vag_reg"] = bearing_to(vagxy, 500)
d["vag"] = d.vag_text.fillna(d.vag_reg)
d["gard"] = bearing_to(byxy, 1000)
d["gard500"] = bearing_to(byxy, 500)
d.to_csv(os.path.join(OUT, "stenar.csv"), index=False)


def rayleigh(deg):
    a = np.radians(deg); n = len(a)
    R = np.hypot(np.cos(a).sum(), np.sin(a).sum())
    p = np.exp(np.sqrt(1 + 4 * n + 4 * (n ** 2 - R ** 2)) - (1 + 2 * n))
    mean = (np.degrees(np.arctan2(np.sin(a).sum(), np.cos(a).sum())) + 360) % 360
    return {"n": n, "R": float(R / n), "medelriktning": float(mean), "p": float(min(1, p))}


def perm(df):
    idx = np.arange(len(df)); out = idx.copy()
    for _, g in df.groupby("province").indices.items():
        out[g] = rng.permutation(g)
    return out


def toward(df, target):
    x = df[df[target].notna()].reset_index(drop=True)
    if len(x) < 5:
        return {"n": len(x)}
    f, t = x.riktning.to_numpy(), x[target].to_numpy()
    stat = lambda ff: np.cos(np.radians(ff - t)).mean()
    obs = stat(f)
    sims = np.array([stat(f[perm(x)]) for _ in range(NPERM)])
    within45 = float((np.abs((f - t + 180) % 360 - 180) <= 45).mean())
    return {"n": len(x), "medel_cos": float(obs), "vantat": float(sims.mean()), "andel_inom_45": within45,
            "p": float((1 + (sims >= obs).sum()) / (NPERM + 1))}


def bro_diff(df):
    x = df[df.vag.notna() & df.bro.notna()].reset_index(drop=True)
    lab = (x.bro > 0).to_numpy().astype(int)
    if lab.sum() < 3 or (1 - lab).sum() < 3:
        return {"n": len(x), "n_bro": int(lab.sum())}
    cs = np.cos(np.radians(x.riktning - x.vag)).to_numpy()
    stat = lambda l: cs[l == 1].mean() - cs[l == 0].mean()
    obs = stat(lab); sims = []
    for _ in range(NPERM):
        l2 = lab.copy()
        for _, g in x.groupby("province").indices.items():
            l2[g] = rng.permutation(l2[g])
        sims.append(stat(l2))
    sims = np.array(sims)
    lo, hi = (1 + (sims <= obs).sum()) / (NPERM + 1), (1 + (sims >= obs).sum()) / (NPERM + 1)
    return {"n": len(x), "n_bro": int(lab.sum()), "cos_bro": float(cs[lab == 1].mean()), "cos_ovriga": float(cs[lab == 0].mean()),
            "skillnad": float(obs), "p": float(min(1, 2 * min(lo, hi)))}


def tests(df):
    return {"H1": rayleigh(df.riktning.to_numpy()), "H2": toward(df, "vag"), "H3": toward(df, "gard"), "H4": bro_diff(df)}


res = {h: tests(d if h == "alla" else d[d.half == h].reset_index(drop=True)) for h in ("alla", "A", "B")}
ps = {k: res["alla"][k].get("p", 1.0) for k in ("H1", "H2", "H3", "H4")}
order = sorted(ps, key=ps.get); holm, run = {}, 0.0
for i, k in enumerate(order):
    run = max(run, min(1.0, (len(ps) - i) * ps[k])); holm[k] = run
def sgn(r, k):
    return 1 if k == "H1" else np.sign(r.get("medel_cos", 0) - r.get("vantat", 0)) if k in ("H2", "H3") else np.sign(r.get("skillnad", 0))
status = {k: ("håller" if holm[k] < 0.05 and all(res[h][k].get("p", 1) < 0.05 and sgn(res[h][k], k) == sgn(res["alla"][k], k)
                                                    for h in "AB")
              else "antydan" if holm[k] < 0.05 or ps[k] < 0.05 else "ingen skillnad påvisad") for k in ps}
dt = d.copy()
rob = {"vag_bara_text": toward(dt.assign(vag=dt.vag_text), "vag"), "vag_bara_registrerad": toward(dt.assign(vag=dt.vag_reg), "vag"),
       "gard_500": toward(dt.assign(gard=dt.gard500), "gard"),
       "U_So": tests(dt[dt.province.isin(["U", "Sö"])].reset_index(drop=True))}
desc = {"streck": d.streck.value_counts().reindex(STRECK, fill_value=0).to_dict(),
        "andel_soder": float(d.streck.isin(["S", "SSÖ", "SÖ", "SSV", "SV"]).mean()),
        "per_landskap": {p: rayleigh(g.riktning.to_numpy()) for p, g in d.groupby("province") if len(g) >= 10}}
out = {"plan": "analysplaner/2026-10-29-ristningens-riktning.md", "n": len(d), "n_vag": int(d.vag.notna().sum()),
       "n_vag_text": int(d.vag_text.notna().sum()), "n_gard": int(d.gard.notna().sum()), "resultat": res, "holm": holm,
       "status": status, "robusthet": rob, "beskrivning": desc}
json.dump(out, open(os.path.join(OUT, "riktning.json"), "w"), ensure_ascii=False, indent=1, default=float)
print("stenar", len(d), "väg", out["n_vag"], "(text", out["n_vag_text"], ") gård", out["n_gard"])
for k in ps:
    print(k, status[k], "holm", round(holm[k], 4), {h: {kk: (round(v, 3) if isinstance(v, float) else v) for kk, v in res[h][k].items()} for h in ("alla", "A", "B")})
print("rob", {k: ({kk: (round(v, 3) if isinstance(v, float) else v) for kk, v in r.items()} if k != "U_So" else
                 {t: {kk: (round(v, 3) if isinstance(v, float) else v) for kk, v in rr.items()} for t, rr in r.items()}) for k, r in rob.items()})
print("streck", desc["streck"], "söder", round(desc["andel_soder"], 3)); print({p: (r["n"], round(r["medelriktning"]), round(r["R"], 2), round(r["p"], 4)) for p, r in desc["per_landskap"].items()})
