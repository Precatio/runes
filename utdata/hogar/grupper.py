"""Tilläggsplan 2: runstenarna vid de stora högarna med högarnas grupper som enhet. Låst plan
analysplaner/2026-11-18-hogarna-grupper.md (sha256 6870d6cd). Återanvänder testet ur trappan.py.
    .venv/bin/python utdata/hogar/grupper.py"""
import collections
import csv
import hashlib
import importlib.util
import json
import os
import re
import sys

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
from src import nordic, places, r_bridge  # noqa: E402

PLAN = os.path.join(ROOT, "analysplaner", "2026-11-18-hogarna-grupper.md")
SHA = hashlib.sha256(open(PLAN, "rb").read()).hexdigest()
assert SHA.startswith("6870d6cd"), SHA
SEED = int(SHA[:8], 16)
spec = importlib.util.spec_from_file_location("trappan", os.path.join(HERE, "trappan.py"))
TP = importlib.util.module_from_spec(spec)
spec.loader.exec_module(TP)
A = TP.A


def mode(vals):
    c = collections.Counter(vals)
    top = max(c.values())
    return sorted(k for k, v in c.items() if v == top)[0]


def sizeclass(n):
    return "1" if n == 1 else "2-3" if n <= 3 else "4-9" if n <= 9 else "10+"


def main():
    H = list(csv.DictReader(open("/Volumes/2TB/Antigrvity/Runes/downloads/hogar/hogar.csv", encoding="utf-8")))
    P = A.asatro.parishes()
    pc, pland = [], []
    for land, ps in P.items():
        for p in ps:
            pc.append(A.xy(p["latitude"], p["longitude"]))
            pland.append(land)
    ptree = cKDTree(np.array(pc))
    half = {}
    for lan in {r["lan"] for r in H}:
        for i, s in enumerate(sorted({r["socken"] for r in H if r["lan"] == lan})):
            half[(lan, s)] = "A" if i % 2 == 0 else "B"
    M = []
    for r in H:
        m = A.DIAM.search(re.sub(r"\s+", " ", r["beskrivning"] or ""))
        if not m:
            continue
        x, y = float(r["x"]), float(r["y"])
        M.append({"x": x, "y": y, "diam": float(m.group(1).replace(",", ".")), "lan": r["lan"], "socken": r["socken"],
                  "land": str(pland[ptree.query([x, y])[1]]), "half": half[(r["lan"], r["socken"])]})
    assert len(M) == 11072
    XY = np.array([[m["x"], m["y"]] for m in M])
    big = np.array([m["diam"] >= 20 for m in M])

    # groups: single linkage at 1 000 m over all mounds with a diameter
    pairs = cKDTree(XY).query_pairs(1000, output_type="ndarray")
    n = len(M)
    g = coo_matrix((np.ones(len(pairs)), (pairs[:, 0], pairs[:, 1])), shape=(n, n))
    k, lab = connected_components(g, directed=False)
    members = collections.defaultdict(list)
    for i, l_ in enumerate(lab):
        members[l_].append(i)

    D = json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["inscriptions"]
    insitu = [r for r in D if nordic.is_runestone(r) and nordic.land_of(r) == "sverige" and r.get("lat") and not r_bridge.is_moved(r)]
    t_in = cKDTree(np.array([A.xy(r["lat"], r["lon"]) for r in insitu]))
    pl = places.places()
    t_ch = cKDTree(places._xy([p["lat"] for p in pl["church"]], [p["lon"] for p in pl["church"]]))
    t_gf = cKDTree(places._xy([p["lat"] for p in pl["gravfalt"]], [p["lon"] for p in pl["gravfalt"]]))

    def stones_within(idx, rad):
        s = set()
        for v in t_in.query_ball_point(XY[idx], rad):
            s.update(v)
        return s

    G = []
    for l_, idx in members.items():
        idx = np.array(idx)
        s1, s5 = stones_within(idx, 1000), stones_within(idx, 5000)
        G.append({"big": bool(big[idx].any()), "n": len(idx), "size": sizeclass(len(idx)),
                  "land": mode([M[i]["land"] for i in idx]),
                  "socken": mode([f'{M[i]["lan"]}|{M[i]["socken"]}' for i in idx]),
                  "half": mode([M[i]["half"] for i in idx]),
                  "y250": bool(stones_within(idx, 250)), "y500": bool(stones_within(idx, 500)), "y1000": bool(s1),
                  "church": any(len(v) > 0 for v in t_ch.query_ball_point(XY[idx], 1000)),
                  "gf": any(len(v) > 0 for v in t_gf.query_ball_point(XY[idx], 1000)),
                  "dens": "some" if len(s5 - s1) > 0 else "none", "idx": idx})
    gb = np.array([g_["big"] for g_ in G])
    y = np.array([g_["y500"] for g_ in G])
    land = np.array([g_["land"] for g_ in G])
    size = np.array([g_["size"] for g_ in G])
    st1 = np.array([f"{a}|{b}" for a, b in zip(land, size)])
    hv = np.array([g_["half"] for g_ in G])
    R = 10000
    res = {"sha": SHA[:8], "grupper": len(G), "grupper_med_stor": int(gb.sum()),
           "grupper_med_stor_och_sten": int((gb & y).sum()), "grupper_utan_stor_med_sten": int((~gb & y).sum()),
           "storleksklasser": dict(collections.Counter(size[gb])), "storleksklasser_alla": dict(collections.Counter(size))}
    T = lambda b_, y_, s_, reps=R: TP.test(b_, y_, s_, reps, seed=SEED)  # noqa: E731
    res["G1"] = T(gb, y, st1)
    res["G1_halvor"] = {h: T(gb[hv == h], y[hv == h], st1[hv == h]) for h in "AB"}
    keep = ~np.array([g_["church"] for g_ in G])
    res["G2"] = T(gb[keep], y[keep], st1[keep])
    res["G2"]["borttagna_grupper"] = int((~keep).sum())
    res["G3"] = T(gb, y, np.array([f'{g_["socken"]}|{g_["size"]}' for g_ in G]))
    res["G4"] = T(gb, y, np.array([f'{g_["land"]}|{g_["size"]}|{g_["dens"]}|{g_["gf"]}' for g_ in G]))
    lands = [l_ for l_, c_ in collections.Counter(land[gb]).items() if c_ >= 5]
    res["G5"] = {}
    for l_ in sorted(lands):
        kk = land != l_
        r_ = TP.test(gb[kk], y[kk], st1[kk], 2000, seed=SEED)
        r_["kvar_av_grupper_med_stor"] = float(gb[kk].sum() / gb.sum())
        res["G5"][l_] = r_
    res["G6"] = {str(rad): T(gb, np.array([g_[f"y{rad}"] for g_ in G]), st1) for rad in (250, 1000)}
    res["per_landskap"] = {l_: {"grupper_med_stor": int((gb & (land == l_)).sum()), "med_sten": int((gb & (land == l_) & y).sum()),
                                "grupper_utan_stor": int((~gb & (land == l_)).sum()), "utan_stor_med_sten": int((~gb & (land == l_) & y).sum())}
                           for l_ in sorted(set(land[gb])) if (gb & (land == l_)).sum() >= 5}

    # cluster bootstrap of the mound-level T1 odds ratio (resample whole groups within the group's province)
    ym = np.array([len(v) > 0 for v in t_in.query_ball_point(XY, 500)])
    mland = np.unique(np.array([m["land"] for m in M]), return_inverse=True)[1]
    rng = np.random.default_rng(SEED)
    by = collections.defaultdict(list)
    for gi, g_ in enumerate(G):
        by[g_["land"]].append(gi)
    ors = []
    for _ in range(2000):
        pick = []
        for l_, gs in by.items():
            pick.extend(rng.choice(gs, size=len(gs), replace=True))
        idx = np.concatenate([G[gi]["idx"] for gi in pick])
        v = TP.mh(big[idx], ym[idx], mland[idx])
        if v == v:
            ors.append(v)
    res["T1_hog_or"] = TP.mh(big, ym, mland)
    res["T1_klusterbootstrap_95"] = [float(np.quantile(ors, 0.025)), float(np.quantile(ors, 0.975))]

    ok = lambda r: r["or"] == r["or"] and r["or"] > 1 and r["p"] < 0.05  # noqa: E731
    halves_ok = all(r["or"] > 1 and (r["p"] < 0.05 or r["stora_med_sten"] < 20) for r in res["G1_halvor"].values())
    g5_ok = all(r["or"] > 1 and (r["p"] < 0.05 or r["kvar_av_grupper_med_stor"] < 2 / 3) for r in res["G5"].values())
    g6_ok = all(r["or"] > 1 for r in res["G6"].values())
    res["steg"] = {"G1": ok(res["G1"]), "G1_halvor": halves_ok, "G2": ok(res["G2"]), "G3": ok(res["G3"]),
                   "G4": ok(res["G4"]), "G5": g5_ok, "G6": g6_ok}
    res["robust"] = all(res["steg"].values())
    json.dump(res, open(os.path.join(HERE, "resultat_grupper.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
