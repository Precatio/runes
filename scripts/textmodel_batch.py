"""Läser alla vikingatida inskrifter med förlorade runor med panelens modell (src/textmodel.analyze) och sparar
läsningarna i panelens cache (data/cache/textmodel/<version>/), så att panelen visar dem direkt. Varje del (crc32 mod 5)
körs för sig, så att en process bara behöver den modell som inte har sett delens stenar.
    .venv/bin/python -m scripts.textmodel_batch --fold 0      (… --fold 4, gärna samtidigt)
    .venv/bin/python -m scripts.textmodel_batch --summary     (sammanställning när alla delar är klara)
Sammanställningen skrivs till utdata/textmodel_batch/sammanstallning.json."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import runlm as rl  # noqa: E402
from src import textmodel as tm  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "utdata", "textmodel_batch")


def with_gaps():
    """The Viking-age inscriptions with at least one run of lost runes the panel fills (1–4 runes)."""
    d = tm._records()
    out = []
    for r in d["V"]:
        groups, _ = tm.text_groups(r["transliteration"])
        every = [(gi, m.start(), m.end()) for gi, g in enumerate(groups) for m in re.finditer(r"\?+", g)]
        if not every:
            continue
        _, runs, _, _ = rl.merge_runs(groups, every)
        if any(sum(1 for i in range(a, e) if groups[gi][i] == "?") <= tm.MAX_GAP for gi, a, e in runs):
            out.append(r["signum"])
    return out


def run(fold: int):
    sigs = [s for s in with_gaps() if tm.fold_of(s) == fold]
    done = 0
    t0 = time.time()
    for i, s in enumerate(sigs):
        path = os.path.join(tm.CACHE, tm._safe(s) + ".json")
        if os.path.exists(path):
            done += 1
            continue
        try:
            tm.analyze(s)
            done += 1
        except Exception as e:  # one stone must not stop the rest
            print(f"FEL {s}: {e}", flush=True)
        if i % 10 == 0:
            print(f"del {fold}: {i + 1} av {len(sigs)} efter {time.time() - t0:.0f} s", flush=True)
    print(f"del {fold} klar: {done} av {len(sigs)} på {time.time() - t0:.0f} s", flush=True)


def summary():
    os.makedirs(OUT, exist_ok=True)
    sigs = with_gaps()
    rows, missing = [], []
    for s in sigs:
        path = os.path.join(tm.CACHE, tm._safe(s) + ".json")
        if not os.path.exists(path):
            missing.append(s)
            continue
        o = json.load(open(path, encoding="utf-8"))
        for g in o.get("gaps", []):
            top = g["words"][0] if g.get("words") else {"word": None, "p": 0.0}
            rows.append({"signum": s, "carved": g["carved"], "start": g["start"], "end": g["end"], "lost": g["n"],
                         "best": g["best"], "word": top["word"], "p": top["p"], "p_model": top.get("p_model"),
                         "boundary": any(b["gap"] == g["number"] for b in o.get("boundaries", []))})
    bins = Counter("≥0,95" if x["p"] >= 0.95 else "0,80–0,95" if x["p"] >= 0.8 else "0,50–0,80" if x["p"] >= 0.5 else "<0,50"
                   for x in rows if x["word"] and x["word"] != "<unk>")
    out = {"version": tm.VERSION, "stones": len(sigs) - len(missing), "missing": missing, "gaps": len(rows),
           "unknown": sum(1 for x in rows if x["word"] == "<unk>"), "by_confidence": dict(bins),
           "boundaries": sum(x["boundary"] for x in rows), "rows": rows}
    json.dump(out, open(os.path.join(OUT, "sammanstallning.json"), "w"), ensure_ascii=False, indent=1)
    print({k: v for k, v in out.items() if k not in ("rows", "missing")}, "| saknas:", len(missing))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fold", type=int)
    ap.add_argument("--summary", action="store_true")
    a = ap.parse_args()
    if a.summary:
        summary()
    else:
        run(a.fold)
