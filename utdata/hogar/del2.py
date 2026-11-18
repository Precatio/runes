"""Från högen till kyrkogården (del 2): D1 kristna stenar och gravfälten (Uppland, replikering Södermanland), D2 stenarna
vid storhögarna är äldre, D3 ordet kumbl försvinner. Låst plan analysplaner/2026-11-18-fran-hogen-till-kyrkogarden.md
(sha256 361c1000).
    .venv/bin/python utdata/hogar/del2.py"""
import collections
import csv
import hashlib
import json
import math
import os
import re
import sys

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
from src import places  # noqa: E402

PLAN = os.path.join(ROOT, "analysplaner", "2026-11-18-fran-hogen-till-kyrkogarden.md")
SHA = hashlib.sha256(open(PLAN, "rb").read()).hexdigest()
assert SHA.startswith("361c1000"), SHA
SEED = int(SHA[:8], 16)
STYLE = {"RAK": (980, 1015), "Fp": (1010, 1050), "Pr1": (1010, 1050), "Pr2": (1020, 1050), "Pr3": (1045, 1075),
         "Pr4": (1070, 1100), "Pr5": (1100, 1130)}
DIAM = re.compile(r"(\d+(?:[.,]\d+)?)\s*m\s*(?:i\s*)?diam", re.I)
REPS = 10000


def codes(a):
    return np.unique(np.asarray(a).astype(str), return_inverse=True)[1]


def mh(x, y, s):
    k = s.max() + 1
    a = np.bincount(s, weights=(x & y), minlength=k); b = np.bincount(s, weights=(x & ~y), minlength=k)
    c = np.bincount(s, weights=(~x & y), minlength=k); d = np.bincount(s, weights=(~x & ~y), minlength=k)
    n = a + b + c + d
    ok = ((a + b) > 0) & ((c + d) > 0)
    num, den = np.sum(a[ok] * d[ok] / n[ok]), np.sum(b[ok] * c[ok] / n[ok])
    return num / den if num > 0 and den > 0 else float("nan")


def strat_diff(near, year, s):
    """weighted (by n near) mean of within-stratum differences: mean year near − mean year other."""
    tot = w = 0.0
    for k in np.unique(s):
        m = s == k
        a, b = near & m, ~near & m
        if a.sum() and b.sum():
            tot += a.sum() * (year[a].mean() - year[b].mean())
            w += a.sum()
    return tot / w if w else float("nan")


def corr(x, y):
    return float(np.corrcoef(x.astype(float), y.astype(float))[0, 1])


def perm(stat, lab, s, other, reps=REPS, log=False, seed=SEED):
    """two-sided p from permuting the boolean 'lab' within strata s."""
    lab = np.asarray(lab, bool)
    obs = stat(lab, other, s)
    order0 = np.argsort(s, kind="stable")
    ss, ls = s[order0], lab[order0]
    rng = np.random.default_rng(seed)
    t = (lambda v: abs(math.log(v))) if log else abs
    ref = t(obs)
    ge = 0
    for _ in range(reps):
        o = np.lexsort((rng.random(len(ss)), ss))
        pl = np.empty_like(lab)
        pl[order0] = ls[o]
        v = stat(pl, other, s)
        if v == v and (not log or v > 0) and t(v) >= ref - 1e-12:
            ge += 1
    return obs, (ge + 1) / (reps + 1)


def halves(df, key):
    h = {}
    for land in df[key].unique():
        for i, p in enumerate(sorted(df.loc[df[key] == land, "parish"].astype(str).unique())):
            h[(land, p)] = "A" if i % 2 == 0 else "B"
    return np.array([h[(a, str(b))] for a, b in zip(df[key], df["parish"])])


def main():
    c = pd.read_csv(os.path.join(ROOT, "data", "cache", "r", "corpus", "510ebfb3acc9a229", "corpus.csv"), low_memory=False)
    assert len(c) == 2321
    recs = {r["signum"]: r for r in json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["inscriptions"]}
    unc = np.array([bool(recs[s].get("style_uncertain")) for s in c.signum])
    yr = np.array([sum(STYLE[s]) / 2 if (isinstance(s, str) and s in STYLE and not u) else np.nan for s, u in zip(c["style"], unc)])
    c["year"] = yr
    c["kristen"] = c["cat_kristen"].astype(int) == 1
    c["kumbl"] = c["normalization"].fillna("").str.contains(r"(?:^|[\s\"])kumbl", case=False, regex=True)
    c["paplats"] = (c["moved"] == 0) & (c["lost"] == 0) & c["lat"].notna()
    has = c["lat"].notna().to_numpy()
    xy = np.full((len(c), 2), np.nan)
    xy[has] = places._xy(c.lat[has].to_numpy(float), c.lon[has].to_numpy(float))
    gf = places.places()["gravfalt"]
    gd, _ = cKDTree(places._xy([p["lat"] for p in gf], [p["lon"] for p in gf])).query(xy[has])
    c["gravfalt"] = False
    c.loc[has, "gravfalt"] = gd <= 500
    H = list(csv.DictReader(open("/Volumes/2TB/Antigrvity/Runes/downloads/hogar/hogar.csv", encoding="utf-8")))
    big = []
    for r in H:
        m = DIAM.search(re.sub(r"\s+", " ", r["beskrivning"] or ""))
        if m and float(m.group(1).replace(",", ".")) >= 20:
            big.append((float(r["x"]), float(r["y"])))
    assert len(big) == 2017
    bt = cKDTree(np.array(big))
    c["storhog"] = False
    c.loc[has, "storhog"] = [len(v) > 0 for v in bt.query_ball_point(xy[has], 500)]
    res = {"sha": SHA[:8], "stenar": len(c), "pa_plats": int(c.paplats.sum()), "daterade": int(np.isfinite(yr).sum())}

    # D1
    def d1(prov, reps=REPS):
        d = c[c.paplats & (c.province == prov)].reset_index(drop=True)
        x, y, s = d.kristen.to_numpy(), d.gravfalt.to_numpy(bool), codes(d.district.fillna("?"))
        o, p = perm(lambda lab, yy, ss: mh(lab, yy, ss), x, s, y, reps, log=True)
        hv = halves(d.assign(L=prov), "L")
        hh = {}
        for h in "AB":
            k = hv == h
            oh, ph = perm(lambda lab, yy, ss: mh(lab, yy, ss), x[k], codes(d.district.fillna("?")[k]), y[k], 4000, log=True)
            hh[h] = {"or": oh, "p": ph, "kristna": int(x[k].sum())}
        return {"or": o, "p": p, "n": len(d), "kristna": int(x.sum()),
                "andel_gravfalt": [float(y[x].mean()), float(y[~x].mean())], "halvor": hh}
    res["D1"] = d1("U")  # the corpus codes provinces by signum prefix
    res["D1_sodermanland"] = d1("Sö")

    # D2
    d = c[c.paplats & np.isfinite(c.year)].reset_index(drop=True)
    keep = d.province.isin(d.loc[d.storhog, "province"].unique())
    d = d[keep].reset_index(drop=True)
    near, year, s = d.storhog.to_numpy(bool), d.year.to_numpy(float), codes(d.province)
    o, p = perm(lambda lab, yy, ss: strat_diff(lab, yy, ss), near, s, year)
    hv = halves(d, "province")
    hh = {}
    for h in "AB":
        k = hv == h
        oh, ph = perm(lambda lab, yy, ss: strat_diff(lab, yy, ss), near[k], codes(d.province[k]), year[k], 4000)
        hh[h] = {"diff": oh, "p": ph, "vid_storhog": int(near[k].sum())}
    res["D2"] = {"diff_ar": o, "p": p, "n": len(d), "vid_storhog": int(near.sum()), "halvor": hh,
                 "landskap": sorted(d.province.unique().tolist()),
                 "stilar_vid_storhog": dict(collections.Counter(d.loc[d.storhog, "style"]).most_common()),
                 "exempel": d.loc[d.storhog, ["signum", "style", "place"]].astype(str).values.tolist()}

    # D3
    d = c[np.isfinite(c.year)].reset_index(drop=True)
    kb, year, s = d.kumbl.to_numpy(bool), d.year.to_numpy(float), codes(d.province.fillna("?"))
    o, p = perm(lambda lab, yy, ss: corr(lab, yy), kb, s, year)
    hv = halves(d.assign(province=d.province.fillna("?")), "province")
    hh = {}
    for h in "AB":
        k = hv == h
        oh, ph = perm(lambda lab, yy, ss: corr(lab, yy), kb[k], codes(d.province.fillna("?")[k]), year[k], 4000)
        hh[h] = {"r": oh, "p": ph, "kumbl": int(kb[k].sum())}
    per = {st: {"n": int((d["style"] == st).sum()), "kumbl": float(d.loc[d["style"] == st, "kumbl"].mean()),
                "bon": float((d.loc[d["style"] == st, "trait_bon"] == "ja").sum() / d.loc[d["style"] == st, "trait_bon"].isin(["ja", "nej"]).sum())}
           for st in STYLE if (d["style"] == st).any()}
    res["D3"] = {"r": o, "p": p, "n": len(d), "kumbl": int(kb.sum()), "halvor": hh, "per_stil": per}

    # Holm and verdicts
    ps = {"D1": res["D1"]["p"], "D2": res["D2"]["p"], "D3": res["D3"]["p"]}
    order = sorted(ps, key=ps.get)
    run = 0.0
    for i, k in enumerate(order):
        run = max(run, min(1.0, (3 - i) * ps[k]))
        res[k]["p_holm"] = run

    def ok_h(hh, key, cnt, want_neg):
        return all((hh[h][key] < (1 if key == "or" else 0)) == want_neg and (hh[h]["p"] < 0.05 or hh[h][cnt] < 30) for h in "AB")
    res["D1"]["haller"] = bool(res["D1"]["p_holm"] < 0.05 and res["D1"]["or"] < 1 and ok_h(res["D1"]["halvor"], "or", "kristna", True)
                               and res["D1_sodermanland"]["or"] < 1
                               and (res["D1_sodermanland"]["p"] < 0.05 or res["D1_sodermanland"]["kristna"] < 30))
    res["D2"]["haller"] = bool(res["D2"]["p_holm"] < 0.05 and res["D2"]["diff_ar"] < 0 and ok_h(res["D2"]["halvor"], "diff", "vid_storhog", True))
    res["D3"]["haller"] = bool(res["D3"]["p_holm"] < 0.05 and res["D3"]["r"] < 0 and ok_h(res["D3"]["halvor"], "r", "kumbl", True))
    json.dump(res, open(os.path.join(HERE, "resultat_del2.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
