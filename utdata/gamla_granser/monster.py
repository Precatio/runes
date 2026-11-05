"""Nya mönster med den vikingatida indelningen (låst plan analysplaner/2026-11-02-gamla-granser-nya-monster.md,
sha 054c87d5): 1 är folklanden (och Smålands små land) särskilda mot sammanhängande slumpindelningar av samma härader,
2 vad utmärker varje del-region inom sitt landskap, 3 häradsfickor. Skriver monster.json.
Omkörd 2026-11-05 med rättad indelning (deklarerad avvikelse efter låsningen, en datarättelse): stenarnas land ur den
rättade web/public/geo/sten_land.json, och häradet per sten och per ISOF-socken rättat efter Det medeltida Sverige 1:7
(historiska_land.json → parish_medieval: Färingö tingslag i Bro härad, Adelsö i Trögds, Bromma och Spånga i Sollentuna i
stället för ISOF:s "Ingår i Stockholms stad", Ekerö och Brännkyrka i Svartlösa). Rundatas "(nu …)" stryks ur sockennamnet,
och en sten som flyttats långt (Skansen, museum) får sin socken om namnet är unikt och inom 100 km, som i
scripts/assign_sten_land.py. Den första körningen ligger i monster_v1.json.
    PYTHONPATH=. .venv/bin/python utdata/gamla_granser/monster.py"""
import csv
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict

import numpy as np
from scipy.stats import chi2

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
from src import linking as L  # noqa: E402
from src import regions  # noqa: E402

# The same 27 traits and logistic machinery as utdata/folkland/folkland.py (copied: importing it reruns that analysis)
FEATS = ["cat_kristen", "pm_kors", "pm_bon", "pm_sjal", "pm_hednisk", "cat_fard", "msg_dod_borta", "msg_berom",
         "cat_bro_vag", "kvinna_resare", "kvinna_ensam", "flera_resare", "rel_barn", "rel_foralder", "rel_syskon",
         "rel_make", "drengr", "thegn", "pm_signatur", "ord_kumbl", "mat_granit", "pm_stungna", "monoftong", "r_for_R",
         "o_runa", "prep_at", "ord_þennsa"]


def bh(p):
    p = np.asarray(p, float); o = np.argsort(p)
    q = p[o] * len(p) / (np.arange(len(p)) + 1)
    q = np.minimum.accumulate(q[::-1])[::-1]
    out = np.empty_like(q); out[o] = np.minimum(q, 1)
    return out


def loglik(X, y, it=100):
    """Maximum log-likelihood of a logistic regression (Newton–Raphson with a tiny ridge against separation)."""
    b = np.zeros(X.shape[1])
    for _ in range(it):
        eta = np.clip(X @ b, -30, 30)
        mu = 1 / (1 + np.exp(-eta))
        W = mu * (1 - mu) + 1e-9
        H = X.T @ (X * W[:, None]) + 1e-6 * np.eye(X.shape[1])
        step = np.linalg.solve(H, X.T @ (y - mu) - 1e-6 * b)
        step = np.clip(step, -5, 5)
        b += step
        if np.max(np.abs(step)) < 1e-9:
            break
    eta = np.clip(X @ b, -30, 30)
    mu = np.clip(1 / (1 + np.exp(-eta)), 1e-12, 1 - 1e-12)
    return float(np.sum(y * np.log(mu) + (1 - y) * np.log(1 - mu)))


def dummies(vals, levels):
    return np.column_stack([[1.0 if v == lv else 0.0 for v in vals] for lv in levels[1:]]) if len(levels) > 1 else np.zeros((len(vals), 0))


ISOF = "/Volumes/2TB/Antigrvity/Runes/geografi_kallor/isof/"
NPART, ADJ_KM, MIN_SUB, MIN_HARAD = int(os.environ.get("NPART", 999)), 20, 30, 15  # NPART only lowered for timing tests
rng = np.random.default_rng(20261102)
PROVS = ("U", "Sö", "Ög", "Vg", "Sm", "Öl", "G", "Nä", "Vs", "Gs", "Hs", "M", "Bo", "Vr", "D", "J")
FOLK = ["attundaland", "tiundaland", "fjadrundaland", "roden"]


def km(a, b):
    return 111.2 * math.hypot(a[0] - b[0], (a[1] - b[1]) * math.cos(math.radians(a[0])))


# ---- härad per sten via ISOF ------------------------------------------------------------------------------------------
dist = {d["id"]: d["name"] for d in json.load(open(ISOF + "districts.json"))}
isof = [p for p in json.load(open(ISOF + "parishes.json")) if p.get("latitude") and p.get("district_id") in dist]
by_name = defaultdict(list)
for p in isof:
    by_name[p["name"]].append(p)
# rerun 2026-11-05: the medieval härad of the parishes where it differs from ISOF (historiska_land.json → parish_medieval,
# Det medeltida Sverige 1:7), matched on name and place (within 10 km of the parish point); "Bro härad" → ISOF's "Bro hd"
MEDIEVAL = json.load(open(os.path.join(ROOT, "web", "src", "lib", "historiska_land.json"), encoding="utf-8"))["parish_medieval"]["socknar"]


def district(p):
    for m in MEDIEVAL.values():
        if m["namn"] == p["name"].replace(" sn", " socken") and km((m["lat"], m["lon"]), (p["latitude"], p["longitude"])) <= 10:
            return m["harad"].replace(" härad", " hd")
    return dist[p["district_id"]]


assert {district(p) for p in isof if p["name"] in ("Färentuna sn", "Lovö sn", "Adelsö sn", "Spånga sn", "Ekerö sn")} == {
    "Bro hd", "Trögds hd", "Sollentuna hd", "Svartlösa hd"}


def harad_of(x):
    pt = (x["lat"], x["lon"])
    named = by_name.get(re.sub(r"\s*\(nu [^)]*\)", "", x["parish"] or "").strip(), [])
    cand = [p for p in named if km((p["latitude"], p["longitude"]), pt) <= 25]
    if not cand and len(named) == 1 and km((named[0]["latitude"], named[0]["longitude"]), pt) <= 100:
        cand = named    # moved far from its parish (Skansen, a museum); the name is unique (rerun 2026-11-05)
    if cand:
        p = min(cand, key=lambda p: km((p["latitude"], p["longitude"]), pt))
    else:
        p = min(isof, key=lambda p: km((p["latitude"], p["longitude"]), pt))
        if km((p["latitude"], p["longitude"]), pt) > 15:
            return None
    return district(p)


rd = json.load(open(os.path.join(ROOT, "data", "rundata.json")))["inscriptions"]
st = L.stones(rd)
feat = {r["signum"]: r for r in csv.DictReader(open(os.path.join(ROOT, "utdata", "upptackt_v3", "drag.csv")))}
rows = []
for sg, x in st.items():
    if sg not in feat or x["lat"] is None or x["province"] not in PROVS:
        continue
    f = feat[sg]
    yr = (float(f["style_from"]) + float(f["style_to"])) / 2 if f["style_from"] else None
    per = "odaterad" if yr is None else "–1010" if yr < 1010 else "1010–1040" if yr < 1040 else "1040–1070" if yr < 1070 else "1070–"
    rows.append({"signum": sg, "region": regions.old_region(sg, x["province"]), "province": x["province"],
                 "parish": x["parish"] or sg, "harad": harad_of(x), "carver": f.get("carver") or "", "year": yr,
                 "period": per, **{k: (None if f.get(k, "") == "" else int(float(f[k]))) for k in FEATS}})
print("stenar", len(rows), "med härad", sum(1 for r in rows if r["harad"]))

pm = defaultdict(list)
for r in rows:
    pm[(r["province"], r["parish"])].append(r["year"])
half = {}
for prov in {p for p, _ in pm}:
    keys = sorted((k for k in pm if k[0] == prov), key=lambda k: (all(y is None for y in pm[k]), np.mean([y for y in pm[k] if y] or [0]), -len(pm[k]), k[1]))
    for i, k in enumerate(keys):
        half[k] = i % 2
for r in rows:
    r["half"] = half[(r["province"], r["parish"])]


def chi_group(z, f, group):
    """χ² and p for the group term in f ~ period + group (logistic), plus the share per group."""
    z = [r for r in z if r[f] is not None]
    y = np.array([r[f] for r in z], float)
    if len(z) == 0 or y.sum() < 10 or len(y) - y.sum() < 10:
        return None
    pers = sorted({r["period"] for r in z}); grs = sorted({group(r) for r in z})
    if len(grs) < 2:
        return None
    Xr = np.hstack([np.ones((len(z), 1)), dummies([r["period"] for r in z], pers)])
    Xf = np.hstack([Xr, dummies([group(r) for r in z], grs)])
    stat = max(2 * (loglik(Xf, y) - loglik(Xr, y)), 0.0)
    return stat, float(chi2.sf(stat, len(grs) - 1))


# ---- steg 1: slumpindelningar -----------------------------------------------------------------------------------------
def harad_points():
    pts = defaultdict(list)
    for p in isof:
        pts[district(p)].append((p["latitude"], p["longitude"]))
    return pts


HP = harad_points()


def partition_test(z, lands):
    units = sorted({r["harad"] for r in z if r["harad"]})
    real = {}
    for u in units:
        real[u] = Counter(r["region"] for r in z if r["harad"] == u).most_common(1)[0][0]
    sizes = Counter(real[u] for u in units)
    blocks = sorted(sizes)
    dmin = {(u, v): min(km(a, b) for a in HP[u] for b in HP[v]) for u in units for v in units if u != v}
    nb = {u: {v for v in units if v != u and dmin[(u, v)] <= ADJ_KM} for u in units}
    for u in units:   # deviation 1: an isolated härad gets its nearest härad as neighbour
        if not nb[u]:
            v = min((v for v in units if v != u), key=lambda v: dmin[(u, v)])
            nb[u].add(v); nb[v].add(u)

    def random_partition():
        while True:
            seeds = rng.choice(units, len(blocks), replace=False)
            asg = {s: b for s, b in zip(seeds, blocks)}
            ok = True
            while len(asg) < len(units):
                open_ = [b for b in blocks if sum(1 for v in asg.values() if v == b) < sizes[b]]
                grow = []
                for b in open_:
                    fr = {v for u, bb in asg.items() if bb == b for v in nb[u] if v not in asg}
                    if fr:
                        grow.append((b, sorted(fr)))
                if not grow:
                    ok = False
                    break
                b, fr = grow[rng.integers(len(grow))]
                asg[fr[rng.integers(len(fr))]] = b
            if ok:
                return asg

    zz = [r for r in z if r["harad"] in real]
    feats = [f for f in FEATS if chi_group(zz, f, lambda r: real[r["harad"]]) is not None]

    def score(asg, sub):
        s, k = 0.0, 0
        for f in feats:
            c = chi_group(sub, f, lambda r: asg[r["harad"]])
            if c:
                s += c[0]; k += c[1] < 0.05
        return s, k

    subsets = {"alla": zz, "A": [r for r in zz if r["half"] == 0], "B": [r for r in zz if r["half"] == 1]}
    obs = {h: score(real, s) for h, s in subsets.items()}
    sims = {h: [] for h in subsets}
    for i in range(NPART):
        asg = random_partition()
        for h, s in subsets.items():
            sims[h].append(score(asg, s))
        if (i + 1) % 100 == 0:
            print("  slumpindelning", i + 1, flush=True)
    out = {"units": len(units), "sizes": dict(sizes), "stones": len(zz), "features": len(feats)}
    for h in subsets:
        chis = np.array([s[0] for s in sims[h]]); ks = np.array([s[1] for s in sims[h]])
        out[h] = {"chi2_real": obs[h][0], "chi2_median_random": float(np.median(chis)),
                  "chi2_p95_random": float(np.percentile(chis, 95)), "p": float((1 + (chis >= obs[h][0]).sum()) / (NPART + 1)),
                  "k_real": int(obs[h][1]), "k_median_random": float(np.median(ks)),
                  "p_k": float((1 + (ks >= obs[h][1]).sum()) / (NPART + 1))}
    out["holds"] = out["alla"]["p"] < 0.05 and out["A"]["p"] < 0.05 and out["B"]["p"] < 0.05
    return out


print("steg 1 Uppland")
step1 = {"uppland": partition_test([r for r in rows if r["region"] in FOLK], FOLK)}
print(json.dumps(step1["uppland"], ensure_ascii=False))
sm_lands = {r["region"] for r in rows if r["province"] == "Sm" and r["region"] != "Sm"}
print("steg 1 Småland", sorted(sm_lands))
step1["smaland"] = partition_test([r for r in rows if r["province"] == "Sm" and r["region"] in sm_lands], sorted(sm_lands))
print(json.dumps(step1["smaland"], ensure_ascii=False))

# ---- kända fynd ---------------------------------------------------------------------------------------------------------
gs = json.load(open(os.path.join(ROOT, "utdata", "granser", "gransskannern.json")))
known_pairs = {(t["feature"], t[k]) for t in gs["tests"] if t["q"] < 0.05 for k in ("a", "b")}


def contrast(z_in, z_out, f, top=None):
    z = [dict(r, _g="in") for r in z_in] + [dict(r, _g="ut") for r in z_out]
    c = chi_group(z, f, lambda r: r["_g"])
    if c is None:
        return None
    si = np.mean([r[f] for r in z_in if r[f] is not None] or [np.nan]); so = np.mean([r[f] for r in z_out if r[f] is not None] or [np.nan])
    return {"chi2": c[0], "p": c[1], "share_in": float(si), "share_out": float(so), "n_in": sum(r[f] is not None for r in z_in)}


def judge(tests, groups):
    for t, q in zip(tests, bh([t["p"] for t in tests])):
        t["q"] = float(q)
    for t in tests:
        if t["q"] >= 0.05:
            continue
        zi, zo = groups[t["unit"]]
        up = t["share_in"] > t["share_out"]
        hs = []
        for h in (0, 1):
            c = contrast([r for r in zi if r["half"] == h], [r for r in zo if r["half"] == h], t["feature"])
            hs.append(None if c is None else {"p": c["p"], "same": (c["share_in"] > c["share_out"]) == up})
        t["halves"] = hs
        top = Counter(r["carver"] for r in zi if r["carver"]).most_common(1)
        if top and top[0][1] > 5:
            c = contrast([r for r in zi if r["carver"] != top[0][0]], zo, t["feature"])
            t["without_top_carver"] = {"carver": top[0][0], "n": top[0][1],
                                       **({"p": c["p"], "same": (c["share_in"] > c["share_out"]) == up} if c else {"p": None})}
            ok_c = c is not None and c["p"] < 0.05 and (c["share_in"] > c["share_out"]) == up
        else:
            t["without_top_carver"] = None
            ok_c = True
        t["holds"] = all(h is not None and h["p"] < 0.05 and h["same"] for h in hs) and ok_c


# ---- steg 2: del-regioner mot resten av landskapet --------------------------------------------------------------------
subs = [g for g, n in Counter(r["region"] for r in rows).items() if n >= MIN_SUB and g not in PROVS]
groups2, step2 = {}, []
for g in sorted(subs):
    zi = [r for r in rows if r["region"] == g]
    prov = Counter(r["province"] for r in zi).most_common(1)[0][0]
    zo = [r for r in rows if r["province"] == prov and r["region"] != g]
    groups2[g] = (zi, zo)
    for f in FEATS:
        c = contrast(zi, zo, f)
        if c:
            step2.append({"unit": g, "province": prov, "feature": f, **c, "known": (f, g) in known_pairs})
judge(step2, groups2)

# ---- steg 3: häradsfickor ------------------------------------------------------------------------------------------------
hc = Counter((r["harad"], r["region"]) for r in rows if r["harad"])
groups3, step3 = {}, []
for (h, g), n in sorted(hc.items()):
    if n < MIN_HARAD:
        continue
    zi = [r for r in rows if r["harad"] == h and r["region"] == g]
    zo = [r for r in rows if r["region"] == g and r["harad"] != h]
    if len(zo) < 15:
        continue
    key = f"{h}|{g}"
    groups3[key] = (zi, zo)
    for f in FEATS:
        c = contrast(zi, zo, f)
        if c:
            step3.append({"unit": key, "harad": h, "region": g, "feature": f, **c,
                          "known": f == "ord_þennsa" and g == "Sö"})
judge(step3, groups3)

out = {"plan": "analysplaner/2026-11-02-gamla-granser-nya-monster.md", "plan_sha": "054c87d5", "deviation": "analysplaner/2026-11-02-gamla-granser-nya-monster-avvikelse.md",
       "rerun": "2026-11-05: rättad landindelning och häradsindelning (parish_medieval i historiska_land.json); v1 i monster_v1.json", "step1": step1,
       "step2": {"n_tests": len(step2), "tests": step2}, "step3": {"n_tests": len(step3), "units": len(groups3), "tests": step3}}
json.dump(out, open(os.path.join(HERE, "monster.json"), "w"), ensure_ascii=False, indent=1, default=float)
for name, tests in (("steg 2", step2), ("steg 3", step3)):
    sig = [t for t in tests if t["q"] < 0.05]
    print(name, "prov", len(tests), "q<0,05", len(sig), "håller", sum(t["holds"] for t in sig))
    for t in sorted(sig, key=lambda t: (not t["holds"], t["q"])):
        print(f"  {t['unit']:28} {t['feature']:14} {t['share_in']:.0%} mot {t['share_out']:.0%} q {t['q']:.4f} "
              f"halvor {[(round(h['p'], 3), h['same']) if h else None for h in t['halves']]} "
              f"ristare {t['without_top_carver']} {'HÅLLER' if t['holds'] else ''}{' känt' if t.get('known') else ''}")
