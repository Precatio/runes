"""Kontroll till liknande_ord.py: löses Maltstenens följder upp i litteraturord oftare än omkastade följder av samma
runor? För varje följd (minst 3 runor) blandas runorna 300 gånger; andelen omkastningar som får (a) ett helt ord på
avstånd 0, (b) ett helt ord på avstånd ≤1, (c) någon tudelning där båda delarna är ord, jämförs med den verkliga
följden. Skriver liknande_ord_kontroll.json.
    PYTHONPATH=. .venv/bin/python utdata/Malt/liknande_ord_kontroll.py"""
import contextlib
import importlib.util
import io
import json
import random

spec = importlib.util.spec_from_file_location("lo", "utdata/Malt/liknande_ord.py")
lo = importlib.util.module_from_spec(spec)
with contextlib.redirect_stdout(io.StringIO()):
    spec.loader.exec_module(lo)
rng = random.Random(2026)
N = 300


def profile(seq):
    whole0 = any(h["distance"] == 0 for h in lo.hits(seq, max_dist=len(seq) >= 5))
    whole1 = bool(lo.hits(seq, max_dist=len(seq) >= 5))
    split = any(lo.hits(seq[:i], 0) and lo.hits(seq[i:], 0) for i in range(2, len(seq) - 1))
    return whole0, whole1, split


rows = []
for it in lo.res:
    seq = it["runes"]
    if len(seq) < 3:
        continue
    real = profile(seq)
    sh = [profile("".join(rng.sample(seq, len(seq)))) for _ in range(N)]
    rate = [sum(s[i] for s in sh) / N for i in range(3)]
    rows.append({"runes": seq, "real": real, "shuffled_rate": rate})
    print(f"{seq:8} verklig: helt {int(real[0])} / ≤1 {int(real[1])} / delning {int(real[2])}   "
          f"omkastad: helt {rate[0]:.2f} / ≤1 {rate[1]:.2f} / delning {rate[2]:.2f}")
tot = {"n": len(rows), "real": [sum(r["real"][i] for r in rows) for i in range(3)],
       "shuffled_expected": [round(sum(r["shuffled_rate"][i] for r in rows), 1) for i in range(3)]}
json.dump({"rows": rows, "total": tot}, open("utdata/Malt/liknande_ord_kontroll.json", "w"), ensure_ascii=False, indent=1)
print("SUMMA  verkliga följder med träff:", tot["real"], " väntat för omkastade:", tot["shuffled_expected"], " av", tot["n"])
