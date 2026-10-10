"""Bygger data/stone_dimensions.json: mått för Sveriges vikingatida runstenar ur Kulturmiljöregistret.

Rundata saknar mått. För varje runsten hämtas Kulturmiljöregistrets id via Runor och lämningens beskrivning via
K-samsök, och höjd, bredd, tjocklek och runhöjd läses ut (src/stone_dimensions.py; METHODS.md 9b). Svaren cachas,
så skriptet kan avbrytas och köras igen. Ca tre förfrågningar per sten, med paus mellan dem.

    .venv/bin/python -m scripts.build_stone_dimensions
"""
import argparse
import collections
import datetime
import json
import os
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main(argv=None):
    from src import research_gaps as gaps
    from src import stone_dimensions as sd

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=os.path.join(ROOT, "data", "stone_dimensions.json"))
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args(argv)
    rundata = json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))
    signa = [r["signum"] for r in rundata["inscriptions"] if gaps.is_runestone(r)]

    def one(signum):
        try:
            return signum, sd.dimensions(signum)
        except Exception as e:  # network errors: not cached, so a new run tries again
            return signum, {"status": f"fel: {type(e).__name__}"}

    stones, done = {}, 0
    with ThreadPoolExecutor(a.workers) as pool:
        for signum, d in pool.map(one, signa):
            stones[signum] = d
            done += 1
            if done % 100 == 0:
                print(f"{done}/{len(signa)}", flush=True)
    status = collections.Counter(d["status"] for d in stones.values())
    out = {"meta": {"source": sd.SOURCE, "built": datetime.date.today().isoformat(), "n_runestones": len(signa),
                    "status": dict(status),
                    "n_height": sum(1 for d in stones.values() if d.get("height_m") and not d.get("fragment"))},
           "stones": stones}
    json.dump(out, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(out["meta"], ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
