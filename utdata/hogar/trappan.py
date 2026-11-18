"""Robusthetstrappan för H3 (runstenarna vid de stora högarna). Låst tilläggsplan
analysplaner/2026-11-18-hogarna-trappan.md (sha256 53f11fa6). Läser högarna som analys.py.
    .venv/bin/python utdata/hogar/trappan.py"""
import collections
import csv
import hashlib
import importlib.util
import json
import math
import os
import re
import sys

import numpy as np
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
from src import nordic, places, r_bridge  # noqa: E402

PLAN = os.path.join(ROOT, "analysplaner", "2026-11-18-hogarna-trappan.md")
SHA = hashlib.sha256(open(PLAN, "rb").read()).hexdigest()
assert SHA.startswith("53f11fa6"), SHA
SEED = int(SHA[:8], 16)
spec = importlib.util.spec_from_file_location("hog", os.path.join(HERE, "analys.py"))
A = importlib.util.module_from_spec(spec)
spec.loader.exec_module(A)


def mh(big, y, strata):
    """Mantel–Haenszel odds ratio over strata (integer codes)."""
    k = strata.max() + 1
    a = np.bincount(strata, weights=(big & y), minlength=k)
    b = np.bincount(strata, weights=(big & ~y), minlength=k)
    c = np.bincount(strata, weights=(~big & y), minlength=k)
    d = np.bincount(strata, weights=(~big & ~y), minlength=k)
    n = a + b + c + d
    ok = ((a + b) > 0) & ((c + d) > 0)
    num = np.sum(a[ok] * d[ok] / n[ok])
    den = np.sum(b[ok] * c[ok] / n[ok])
    return num / den if num > 0 and den > 0 else float("nan")


def test(big, y, strata, reps, seed=SEED):
    big, y = np.asarray(big, bool), np.asarray(y, bool)
    _, strata = np.unique(np.asarray(strata), return_inverse=True)
    obs = mh(big, y, strata)
    order0 = np.argsort(strata, kind="stable")
    s_sorted = strata[order0]
    b_sorted = big[order0]
    rng = np.random.default_rng(seed)
    ge = 0
    lo = abs(math.log(obs)) if obs == obs and obs > 0 else float("nan")
    for _ in range(reps):
        o = np.lexsort((rng.random(len(s_sorted)), s_sorted))
        pb = np.empty_like(big)
        pb[order0] = b_sorted[o]
        v = mh(pb, y, strata)
        if v == v and v > 0 and abs(math.log(v)) >= lo - 1e-12:
            ge += 1
    return {"or": obs, "p": (ge + 1) / (reps + 1), "stora": int(big.sum()), "mindre": int((~big).sum()),
            "andel_stora": float(y[big].mean()) if big.any() else None,
            "andel_mindre": float(y[~big].mean()) if (~big).any() else None}


def main():
    H = list(csv.DictReader(open("/Volumes/2TB/Antigrvity/Runes/downloads/hogar/hogar.csv", encoding="utf-8")))
    P = A.asatro.parishes()
    pc, pland = [], []
    for land, ps in P.items():
        for p in ps:
            pc.append(A.xy(p["latitude"], p["longitude"]))
            pland.append(land)
    ptree = cKDTree(np.array(pc))
    M = []
    for r in H:
        m = A.DIAM.search(re.sub(r"\s+", " ", r["beskrivning"] or ""))
        if not m:
            continue
        x, y = float(r["x"]), float(r["y"])
        M.append({"x": x, "y": y, "diam": float(m.group(1).replace(",", ".")), "lan": r["lan"], "socken": r["socken"],
                  "land": pland[ptree.query([x, y])[1]]})
    assert len(M) == 11072
    half = {}
    for lan in {m["lan"] for m in M}:
        for i, s in enumerate(sorted({m["socken"] for m in M if m["lan"] == lan})):
            half[(lan, s)] = "A" if i % 2 == 0 else "B"
    XY = np.array([[m["x"], m["y"]] for m in M])
    big = np.array([m["diam"] >= 20 for m in M])
    land = np.array([str(m["land"]) for m in M])  # a parish without province is its own stratum ("None"), as in analys.py
    socken = np.array([f'{m["lan"]}|{m["socken"]}' for m in M])
    hv = np.array([half[(m["lan"], m["socken"])] for m in M])

    D = json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["inscriptions"]
    rs = [r for r in D if nordic.is_runestone(r) and nordic.land_of(r) == "sverige" and r.get("lat")]
    insitu = [r for r in rs if not r_bridge.is_moved(r)]
    t_all = cKDTree(np.array([A.xy(r["lat"], r["lon"]) for r in rs]))
    t_in = cKDTree(np.array([A.xy(r["lat"], r["lon"]) for r in insitu]))

    def within(tree, rad):
        return np.array([len(v) > 0 for v in tree.query_ball_point(XY, rad)])

    y_all = within(t_all, 500)
    y_in = within(t_in, 500)
    pl = places.places()
    ch = pl["church"]
    t_ch = cKDTree(places._xy([p["lat"] for p in ch], [p["lon"] for p in ch]))
    near_church = within(t_ch, 1000)
    gf = pl["gravfalt"]
    t_gf = cKDTree(places._xy([p["lat"] for p in gf], [p["lon"] for p in gf]))
    gf1 = within(t_gf, 1000)
    n5 = np.array([len(v) for v in t_in.query_ball_point(XY, 5000)])
    n1 = np.array([len(v) for v in t_in.query_ball_point(XY, 1000)])
    dens = n5 - n1
    q1, q2 = np.quantile(dens, [1 / 3, 2 / 3])
    tert = np.where(dens <= q1, 0, np.where(dens <= q2, 1, 2))
    if q1 == q2:  # ties: fall back to 0 / >0 / top third, stated in the result
        tert = np.where(dens == 0, 0, np.where(dens <= q2, 1, 2))

    R = 10000
    res = {"sha": SHA[:8], "runstenar": len(rs), "pa_plats": len(insitu), "hogar_med_diameter": len(M),
           "stora": int(big.sum()), "kyrkor": len(ch), "tathet_tredjedelar": [float(q1), float(q2)]}
    res["T0"] = test(big, y_all, land, R)
    res["T1"] = test(big, y_in, land, R)
    res["T1_halvor"] = {h: test(big[hv == h], y_in[hv == h], land[hv == h], R) for h in "AB"}
    keep = ~near_church
    res["T2"] = test(big[keep], y_in[keep], land[keep], R)
    res["T2"]["borttagna_hogar"] = int(near_church.sum())
    res["T3"] = test(big, y_in, socken, R)
    res["T4"] = test(big, y_in, np.array([f"{a}|{b}|{c}" for a, b, c in zip(land, tert, gf1)]), R)
    lands = [l_ for l_, n in collections.Counter(land[big]).items() if n >= 10]
    res["T5"] = {}
    for l_ in sorted(lands):
        k = land != l_
        r = test(big[k], y_in[k], land[k], 2000)
        r["kvar_av_stora"] = float(big[k].sum() / big.sum())
        res["T5"][l_] = r
    res["T6"] = {str(rad): test(big, within(t_in, rad), land, R) for rad in (250, 1000)}
    # per province, in situ (descriptive)
    res["per_landskap_pa_plats"] = {l_: {"stora": int((big & (land == l_)).sum()),
                                         "andel_stora": float(y_in[big & (land == l_)].mean()),
                                         "andel_mindre": float(y_in[~big & (land == l_)].mean())}
                                    for l_ in sorted(set(land[big])) if (big & (land == l_)).sum() >= 10}

    ok = lambda r: r["or"] == r["or"] and r["or"] > 1 and r["p"] < 0.05  # noqa: E731
    halves_ok = all(r["or"] > 1 and (r["p"] < 0.05 or r["stora"] < 50) for r in res["T1_halvor"].values())
    t5_ok = all(r["or"] > 1 and (r["p"] < 0.05 or r["kvar_av_stora"] < 2 / 3) for r in res["T5"].values())
    t6_ok = all(r["or"] > 1 for r in res["T6"].values())
    res["steg"] = {"T1": ok(res["T1"]), "T1_halvor": halves_ok, "T2": ok(res["T2"]), "T3": ok(res["T3"]),
                   "T4": ok(res["T4"]), "T5": t5_ok, "T6": t6_ok}
    res["robust"] = all(res["steg"].values())
    json.dump(res, open(os.path.join(HERE, "resultat_trappan.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
