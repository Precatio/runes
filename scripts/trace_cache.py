"""Beräknar spårläsarens cache (src/trace_reader.py) för skannade stenar: den tunga djupbildskörningen görs en
gång per sten och sparas i data/cache/traces/. Utan argument tas alla stenar med skanningsreferens
(utdata/Rak/referenser_g4); annars de angivna.
    PYTHONPATH=. .venv/bin/python scripts/trace_cache.py ["Sö 206" ...] [--force]"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import trace_reader as tr  # noqa: E402


def main(argv=None):
    args = [a for a in (argv if argv is not None else sys.argv[1:])]
    force = "--force" in args
    signa = [a for a in args if not a.startswith("--")]
    if not signa:
        signa = sorted(f[:-5].replace("_", " ") for f in os.listdir(tr.REFS) if f.endswith(".json"))
    for s in signa:
        if not force and tr.features(s) is not None:
            print(f"{s}: cache finns", flush=True)
            continue
        t0 = time.time()
        try:
            d = tr.compute_features(s)
            print(f"{s}: {len(d['runes'])} runor, {sum(len(v) for v in d['feats'].values())} bistavsblobbar "
                  f"({time.time() - t0:.0f} s)", flush=True)
        except Exception as e:
            print(f"{s}: FEL {e}", flush=True)


if __name__ == "__main__":
    main()
