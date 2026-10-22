"""Jämför två prov av runavkodaren (utdata från scripts/runlm_calibrate.py) ord för ord på samma provstenar:
skillnaden i andelen rätt lästa ord, ett 95-procentigt intervall där stenarna dras om (orden på en sten hänger ihop)
och ett teckentest på de stenar där varianterna skiljer sig.
    .venv/bin/python -m scripts.runlm_compare utdata/Malt/runlm_eval/A_base.json utdata/Malt/runlm_eval/B_aligned.json"""
import json
import math
import random
import sys
from collections import defaultdict


def load(path):
    d = json.load(open(path))
    return d, d["per_word"]


def compare(pa, pb, key=1, n_boot=2000, seed=2026):
    """key 1: same word; key 2: word boundaries. Returns (difference, low, high, stones better, stones worse, p)."""
    _, wa = load(pa)
    _, wb = load(pb)
    assert [w[0] for w in wa] == [w[0] for w in wb], "proven gäller inte samma ord"
    by = defaultdict(lambda: [0, 0, 0])
    for a, b in zip(wa, wb, strict=False):
        s = by[a[0]]
        s[0] += 1; s[1] += a[key]; s[2] += b[key]
    stones = list(by.values())
    n = sum(s[0] for s in stones)
    diff = (sum(s[2] for s in stones) - sum(s[1] for s in stones)) / n
    rng = random.Random(seed)
    boot = []
    for _ in range(n_boot):
        smp = [stones[rng.randrange(len(stones))] for _ in stones]
        boot.append((sum(s[2] for s in smp) - sum(s[1] for s in smp)) / sum(s[0] for s in smp))
    boot.sort()
    better = sum(1 for s in stones if s[2] > s[1]); worse = sum(1 for s in stones if s[2] < s[1])
    m = better + worse
    p = min(1.0, 2 * sum(math.comb(m, k) for k in range(min(better, worse) + 1)) / 2 ** m) if m else 1.0
    return diff, boot[int(0.025 * n_boot)], boot[int(0.975 * n_boot)], better, worse, p


if __name__ == "__main__":
    a, b = sys.argv[1], sys.argv[2]
    for key, name in ((1, "rätt ord"), (2, "rätt ordgränser")):
        d, lo, hi, bt, wr, p = compare(a, b, key)
        print(f"{name}: {d * 100:+.2f} procentenheter (95 %: {lo * 100:+.2f} till {hi * 100:+.2f}); "
              f"stenar bättre {bt}, sämre {wr}, teckentest p = {p:.3g}")
