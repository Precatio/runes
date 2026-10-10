"""Hur många runor behöver mätas? Underlag för gränserna i METHODS.md (avsnitt 2).

Kör den automatiska analysen (bara runor) på skanningar och delar upp spridningen i tre nivåer:
inom en runa, mellan runor på samma sten och mellan stenar. Därur räknas hur tillförlitligt stenens
medelvärde är med n runor, och empiriskt hur ofta en sten känns igen bland de andra utifrån n runor.

    .venv/bin/python -m scripts.rune_sample_size utdata/Rak/referenser_g4/*.json --out utdata/rune_sample_size

Referensfilerna (från scripts.measure_stones) ger filnamn, ytnormal och upp-riktning för varje sten.
"""
import argparse
import base64
import collections
import glob
import json
import os

import numpy as np

METRICS = ["apex_vinkel_deg", "spårdjup_mm", "spårbredd_mm", "djup_bredd_kvot", "asymmetri_deg"]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def measure(refs: list[str], out: str, resolution: float, sensitivity: float):
    import trimesh

    from src.auto_grooves import analyze_grooves
    from src.stats import METRICS as ALL

    for ref in refs:
        d = json.load(open(ref))
        path = os.path.join(out, d["signum"].replace(" ", "_") + ".json")
        if os.path.exists(path):
            continue
        scan = next((p for p in (os.path.join(ROOT, "skanningar", d["file"]), os.path.join(ROOT, d["file"]))
                     if os.path.exists(p)), None)
        if scan is None:
            print(f"{d['signum']}: skanningen saknas, hoppar över")
            continue
        r = analyze_grooves(trimesh.load(scan, process=False), d["parameters"]["normal"], up=d["parameters"].get("up"),
                            resolution_mm=resolution, sensitivity=sensitivity)
        acc = [{k: s[k] for k in (*ALL, "rune_id")} for s in r["slices"] if s["accepted"]]
        json.dump({"signum": d["signum"], "counts": r["counts"], "runes": r["runes"], "slices": acc}, open(path, "w"))
        with open(path.replace(".json", ".png"), "wb") as fh:
            fh.write(base64.b64decode(r["image_base64"].split(",")[1]))
        print(d["signum"], r["counts"]["runes_measured"], "runor,", len(acc), "snitt", flush=True)


def load(out: str, min_runes: int = 8) -> dict:
    stones = {}
    for f in sorted(glob.glob(os.path.join(out, "*.json"))):
        if f.endswith("summary.json"):
            continue
        d = json.load(open(f))
        by = collections.defaultdict(list)
        for s in d["slices"]:
            if s.get("rune_id") is not None and all(np.isfinite(s[m]) for m in METRICS):
                by[s["rune_id"]].append([s[m] for m in METRICS])
        if len(by) >= min_runes:
            stones[d["signum"]] = [np.array(v) for v in by.values()]
    return stones


def variance_components(stones: dict) -> dict:
    """Per mått: SD inom runa, SD mellan runor (envägs-ANOVA per sten, poolat) och SD mellan stenar
    (variansen mellan stenarnas medelvärden minus medelvärdenas egen urvalsvarians)."""
    out = {}
    for j, m in enumerate(METRICS):
        w2, b2, icc, se2 = [], [], [], []
        for runes in stones.values():
            g = [r[:, j] for r in runes]
            k, N = len(g), sum(len(x) for x in g)
            grand = np.concatenate(g).mean()
            msb = sum(len(x) * (x.mean() - grand) ** 2 for x in g) / (k - 1)
            msw = sum(((x - x.mean()) ** 2).sum() for x in g) / (N - k)
            n0 = (N - sum(len(x) ** 2 for x in g) / N) / (k - 1)
            vb = max(0.0, (msb - msw) / n0)
            w2.append(msw)
            b2.append(vb)
            icc.append(vb / (vb + msw) if vb + msw > 0 else 0.0)
            se2.append(np.var([x.mean() for x in g], ddof=1) / k)
        means = [np.mean([r[:, j].mean() for r in runes]) for runes in stones.values()]
        out[m] = {"sd_within_rune": float(np.sqrt(np.mean(w2))), "sd_between_runes": float(np.sqrt(np.mean(b2))),
                  "icc": float(np.mean(icc)),
                  "sd_between_stones": float(np.sqrt(max(1e-12, np.var(means, ddof=1) - np.mean(se2))))}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("refs", nargs="*", help="referensfiler från scripts.measure_stones")
    ap.add_argument("--out", required=True)
    ap.add_argument("--resolution", type=float, default=0.6)
    ap.add_argument("--sensitivity", type=float, default=3)
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    measure(a.refs, a.out, a.resolution, a.sensitivity)

    stones = load(a.out)
    slices_per_rune = float(np.median([len(r) for v in stones.values() for r in v]))
    vc = variance_components(stones)
    ns = (5, 10, 15, 20, 30)
    print(f"\n{len(stones)} stenar med minst 8 mätta runor; median {slices_per_rune:.0f} snitt per runa")
    print(f"{'mått':18s} {'SD inom':>8s} {'SD mellan runor':>16s} {'ICC':>5s} {'SD mellan stenar':>17s}")
    for m, v in vc.items():
        print(f"{m:18s} {v['sd_within_rune']:8.3f} {v['sd_between_runes']:16.3f} {v['icc']:5.2f} {v['sd_between_stones']:17.3f}")

    print("\nTillförlitlighet för stenens medelvärde (andel av spridningen mellan stenar som är verklig) och 95 % KI")
    for m, v in vc.items():
        eff2 = v["sd_between_runes"] ** 2 + v["sd_within_rune"] ** 2 / slices_per_rune
        v["reliability"] = {n: v["sd_between_stones"] ** 2 / (v["sd_between_stones"] ** 2 + eff2 / n) for n in ns}
        from scipy.stats import t
        v["ci95_halfwidth"] = {n: float(t.ppf(0.975, n - 1) * np.sqrt(eff2 / n)) for n in ns}
        # Runes per stone to detect a difference of one between-rune SD between two stones (80 % power, α = 0.05)
        v["n_detect_1sd"] = int(np.ceil(2 * (1.96 + 0.84) ** 2 * eff2 / v["sd_between_runes"] ** 2))
        print(f"{m:18s} " + "  ".join(f"n={n}: {v['reliability'][n]:.2f} ±{v['ci95_halfwidth'][n]:.2f}" for n in ns))

    rng = np.random.default_rng(0)
    big = [k for k, v in stones.items() if len(v) >= 30]
    sd = np.array([np.std([np.mean([r[:, j].mean() for r in v]) for v in stones.values()], ddof=1)
                   for j in range(len(METRICS))])
    recognition = {}
    print(f"\nIgenkänning bland {len(stones)} stenar (n runor ur ena halvan mot andra halvans medelvärden), "
          f"prövat på {len(big)} stenar med minst 30 runor")
    for n in (3, 5, 10, 15, 20):
        hits = tot = 0
        for _ in range(200):
            refs, tests = {}, {}
            for k, v in stones.items():
                idx = rng.permutation(len(v))
                half = len(v) // 2
                refs[k] = np.mean([v[i].mean(axis=0) for i in idx[half:]], axis=0) / sd
                if k in big:
                    tests[k] = np.mean([v[i].mean(axis=0) for i in idx[:half][:n]], axis=0) / sd
            for k, x in tests.items():
                hits += min(refs, key=lambda r: np.linalg.norm(refs[r] - x)) == k
                tot += 1
        recognition[n] = hits / tot
        print(f"n = {n:2d}: {hits / tot:.0%}")
    json.dump({"stones": {k: len(v) for k, v in stones.items()}, "slices_per_rune": slices_per_rune,
               "components": vc, "recognition": recognition}, open(os.path.join(a.out, "summary.json"), "w"),
              ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
