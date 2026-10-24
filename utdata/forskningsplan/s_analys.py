"""Steg 0a, studie 1 och studie 2a enligt analysplaner/2026-10-24-skanningarna.md (låst, SHA-256 55bb1048…).
    PYTHONPATH=. .venv/bin/python utdata/forskningsplan/s_analys.py > utdata/forskningsplan/s_analys.txt"""
import glob
import itertools
import json
import os
import random
import re
import sys

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
from api.rundata import store  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
MAIN = ["apex_vinkel_deg", "spårdjup_mm", "spårbredd_mm", "bottenradie_mm"]
ATOS = {"sodermanland", "asmund", "vastergotland", "gravmonument_og_sm"}
S = store()


def load(folder):
    out = []
    for p in sorted(glob.glob(os.path.join(ROOT, "utdata", folder, "*", "*.json"))):
        d = json.load(open(p, encoding="utf-8"))
        if "error" not in d and d.get("slices"):
            out.append(d)
    return out


def rec(d):
    return S.get(d["signum"]) if d.get("signum") else None


def object_type(d):
    r = rec(d)
    obj = ((r or {}).get("object") or "").lower()
    if d["series"] == "gravmonument_og_sm" or "gravhäll" in obj:
        return "gravmonument"
    if not d.get("signum") and d["series"] == "vastergotland" and re.search(r"Ljung|Lundberg|GVMV|ATA", d["file"]):
        return "gravmonument"
    if "runsten" in obj:
        return "runsten"
    return None


def rock(d):
    m = ((rec(d) or {}).get("material") or "").lower()
    if "kalksten" in m or "lersten" in m:
        return "kalksten"
    if "sandsten" in m:
        return "sandsten"
    if any(w in m for w in ("granit", "gnejs", "gråsten", "diabas")):
        return "kristallin"
    return "okänd"


def med(slices, m, feats=None):
    v = [s[m] for s in slices if s.get(m) is not None and (feats is None or s.get("feature") in feats)]
    return float(np.median(v)) if v else None, len(v)


def objects(data):
    """One unit per object: a signum, or a file for objects without one (the Varnhem files)."""
    by = {}
    for d in data:
        by.setdefault(d.get("signum") or d["file"], []).append(d)
    return by


def perm_test(a, b, n=10_000, seed=1):
    """Difference in medians a − b, two-sided permutation p over the group labels."""
    a, b = np.asarray(a), np.asarray(b)
    obs = np.median(a) - np.median(b)
    pool = np.concatenate([a, b])
    rng = np.random.default_rng(seed)
    k = 0
    for _ in range(n):
        rng.shuffle(pool)
        k += abs(np.median(pool[:len(a)]) - np.median(pool[len(a):])) >= abs(obs) - 1e-12
    return float(obs), (k + 1) / (n + 1)


def boot_ci(a, b, level=0.90, n=2000, seed=2):
    rng = np.random.default_rng(seed)
    a, b = np.asarray(a), np.asarray(b)
    diffs = [np.median(rng.choice(a, len(a))) - np.median(rng.choice(b, len(b))) for _ in range(n)]
    lo, hi = np.percentile(diffs, [(1 - level) / 2 * 100, (1 + level) / 2 * 100])
    return float(lo), float(hi)


def bh(ps):
    ps = np.asarray(ps, float)
    order = np.argsort(ps)
    q = np.empty_like(ps)
    prev = 1.0
    for rank, i in reversed(list(enumerate(order, 1))):
        prev = min(prev, ps[i] * len(ps) / rank)
        q[i] = prev
    return q.tolist()


def step0a(P):
    print("== Steg 0a: samma sten i två filer")
    out = {}
    for sig in ("Hs 14", "M 14"):
        ds = [d for d in P if d.get("signum") == sig]
        if len(ds) < 2:
            print(f"{sig}: bara {len(ds)} fil mätt – väntar")
            continue
        series = ds[0]["series"]
        stones = objects([d for d in P if d["series"] == series and d.get("signum") != sig])
        sds = {}
        for m in MAIN:
            vals = [med([s for d in g for s in d["slices"]], m)[0] for g in stones.values()]
            sds[m] = float(np.std([v for v in vals if v is not None], ddof=1))
        row = {}
        for m in MAIN:
            a, b = (med(d["slices"], m) for d in ds[:2])
            diff = abs(a[0] - b[0])
            row[m] = {"filer": [d["file"] for d in ds[:2]], "medianer": [a[0], b[0]], "n": [a[1], b[1]],
                      "skillnad": diff, "sd_mellan_stenar": sds[m], "känsligt": diff > 0.5 * sds[m]}
            print(f"{sig} {m:16} {a[0]:7.2f} (n {a[1]}) mot {b[0]:7.2f} (n {b[1]}): |Δ| {diff:.2f}, "
                  f"SD mellan stenar {sds[m]:.2f} → {'UPPLÖSNINGSKÄNSLIGT' if diff > 0.5 * sds[m] else 'stabilt'}")
        out[sig] = row
    return out


def study1(A):
    print("\n== Studie 1: runor minus ornamentik inom objektet")
    rows = []
    for key, ds in objects(A).items():
        t = object_type(ds[0])
        if not t:
            continue
        sl = [s for d in ds for s in d["slices"]]
        r = {"objekt": key, "typ": t, "bergart": rock(ds[0]), "serie": ds[0]["series"]}
        ok = True
        for m in MAIN:
            (mr, nr), (mo, no) = med(sl, m, {"rune"}), med(sl, m, {"ornament"})
            r[f"n_runa"], r[f"n_orn"] = nr, no
            if nr < 10 or no < 10:
                ok = False
                break
            r[m] = mr - mo
        if ok:
            rows.append(r)
    for t in ("runsten", "gravmonument"):
        print(f"{t}: {sum(r['typ'] == t for r in rows)} objekt med minst 10 snitt i både runor och ornamentik")

    def test(sel, label):
        g = [r for r in sel if r["typ"] == "gravmonument"]
        s_ = [r for r in sel if r["typ"] == "runsten"]
        if len(g) < 8 or len(s_) < 8:
            print(f"{label}: {len(g)} gravmonument, {len(s_)} runstenar – för få för test (kräver 8 + 8), bara beskrivande")
            for m in MAIN:
                if g and s_:
                    print(f"   {m}: median Δ gravmonument {np.median([r[m] for r in g]):.2f}, "
                          f"runstenar {np.median([r[m] for r in s_]):.2f}")
            return None
        res = {}
        for m in MAIN:
            obs, p = perm_test([r[m] for r in g], [r[m] for r in s_])
            lo, hi = boot_ci([r[m] for r in g], [r[m] for r in s_])
            res[m] = {"skillnad": obs, "p": p, "ci90": [lo, hi], "n_grav": len(g), "n_runsten": len(s_)}
        qs = bh([res[m]["p"] for m in MAIN[1:]])
        for m, q in zip(MAIN[1:], qs):
            res[m]["q"] = q
        v = res[MAIN[0]]
        verdict = ("mönstret skiljer sig" if v["p"] < 0.05 else
                   "samma mönster" if -5 <= v["ci90"][0] and v["ci90"][1] <= 5 else "obestämt")
        res["utfall"] = verdict
        print(f"{label}: {len(g)} gravmonument mot {len(s_)} runstenar")
        for m in MAIN:
            x = res[m]
            print(f"   {m:16} skillnad i median-Δ {x['skillnad']:+.2f}, 90 % KI [{x['ci90'][0]:+.2f}, {x['ci90'][1]:+.2f}], "
                  f"p {x['p']:.4f}" + (f", q {x['q']:.4f}" if "q" in x else "  ← huvudtest"))
        print(f"   utfall (V-vinkel): {verdict}")
        return res

    out = {"objekt": rows, "huvud": test(rows, "Huvudtest")}
    soft = [r for r in rows if r["typ"] == "gravmonument" or r["bergart"] in ("sandsten", "kalksten")]
    out["robust_mjuk_bergart"] = test(soft, "Robusthet (i) bara runstenar i sandsten/kalksten")
    out["robust_utan_serie"] = {}
    for ser in sorted({r["serie"] for r in rows}):
        out["robust_utan_serie"][ser] = test([r for r in rows if r["serie"] != ser], f"Robusthet (ii) utan {ser}")
    out["robust_atos"] = test([r for r in rows if r["serie"] in ATOS], "Robusthet (iii) bara ATOS")
    return out


def study2a(A):
    print("\n== Studie 2a: Hälsinglands stavlösa stenar mot övriga")
    stav = {"Hs 10", "Hs 12", "Hs 14", "Hs 15"}
    other = {"Hs 1", "Hs 2", "Hs 3", "Hs 4", "Hs 6", "Hs 9", "Hs 11", "Hs 16", "Hs 21"}
    stones = {k: v for k, v in objects([d for d in A if d["series"] == "halsingland"]).items()}
    out = {}
    for label, keep in (("alla", lambda d: True), ("kristallin", lambda d: rock(d) == "kristallin")):
        vals = {}
        for k, ds in stones.items():
            if k not in stav | other or not keep(ds[0]):
                continue
            sl = [s for d in ds for s in d["slices"]]
            vals[k] = {m: med(sl, m, {"rune", "isolated"}) for m in MAIN}
        a_keys = [k for k in vals if k in stav]
        b_keys = [k for k in vals if k in other]
        res = {"stavlösa": a_keys, "övriga": b_keys}
        print(f"[{label}] stavlösa {sorted(a_keys)}, övriga {sorted(b_keys)}")
        for m in MAIN:
            a = [vals[k][m][0] for k in a_keys if vals[k][m][0] is not None]
            b = [vals[k][m][0] for k in b_keys if vals[k][m][0] is not None]
            if len(a) < 2 or len(b) < 2:
                continue
            obs = np.median(a) - np.median(b)
            pool = a + b
            # Exact: every split of the stones into groups of the same sizes
            ge = tot = 0
            for idx in itertools.combinations(range(len(pool)), len(a)):
                x = [pool[i] for i in idx]
                y = [pool[i] for i in range(len(pool)) if i not in idx]
                tot += 1
                ge += abs(np.median(x) - np.median(y)) >= abs(obs) - 1e-12
            res[m] = {"stavlösa_median": float(np.median(a)), "övriga_median": float(np.median(b)),
                      "skillnad": float(obs), "p_exakt": ge / tot, "n": [len(a), len(b)]}
            print(f"   {m:16} stavlösa {np.median(a):6.2f} mot övriga {np.median(b):6.2f}: {obs:+.2f}, "
                  f"exakt p {ge / tot:.3f}" + ("  ← huvudmått" if m == "spårdjup_mm" else ""))
        out[label] = res
    return out


if __name__ == "__main__":
    random.seed(0)
    P = load("automatisk_korning")
    # --steg0: only step 0a (the A-data pass may still be running; studies 1–2 run once it is complete)
    A = [] if "--steg0" in sys.argv else load("automatisk_korning_alla")
    print(f"P-data {len(P)} filer, A-data {len(A)} filer")
    res = {"steg0a": step0a(P), "studie1": study1(A) if A else None, "studie2a": study2a(A) if A else None}
    json.dump(res, open(os.path.join(HERE, "s_analys.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
