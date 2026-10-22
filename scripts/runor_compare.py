"""Jämför Runor 2020 (data/raa/runor_2020.json, från scripts/fetch_runor.py) med appens Rundata (2018).

    python -m scripts.runor_compare [--out utdata/runor/jamforelse.json]

Svarar på vad Runor tillför: inskrifter som saknas i Rundata, stenar som Runor anger som försvunna eller på sin
ursprungliga plats jämfört med appens flaggor (lost, moved i src/r_bridge.py), anteckningar om skador och läsningar
som har ändrats sedan 2018, särskilt där Runor läser runor som Rundata har som förlorade.
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import re

from api.rundata import store
from src import research_gaps as gaps
from src.r_bridge import is_moved
from src.signum import fold_signum

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "data", "raa", "runor_2020.json")
DAMAGE = re.compile(r"skad|omhugg|sprä?ng|avslag|avslog|slagits|lagad|lagats|sönder|brut|fragment|vittra|flag|"
                    r"spricka|sprucken|kluven|försvunn|ej återfunn|förstörd|huggits|tillhugg|nedgrävd|mur", re.I)
SEP = re.compile(r"[\s·:'×÷+|¶⁓;,.!?\"]|§[A-Z]|\{|\}|\$|=")


from src.runor import runes  # noqa: E402  (samma jämförelse som appen visar)


def lost_count(reading: str) -> int:
    """Förlorade runor: varje - och varje … (en lucka av okänd längd) räknas som en."""
    return len(re.findall(r"-|…", runes(reading)))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=os.path.join(ROOT, "utdata", "runor", "jamforelse.json"))
    a = ap.parse_args(argv)
    runor = json.load(open(SRC, encoding="utf-8"))["inscriptions"]
    ours = store().inscriptions
    by_key = {fold_signum(r["signum"]): r for r in ours}
    for r in ours:
        for alt in re.split(r"[;,]\s*(?=[A-ZÅÄÖ])", r.get("alt_signum") or ""):
            if alt.strip():
                by_key.setdefault(fold_signum(alt.strip()), r)

    matched, missing = [], []
    for x in runor:
        r = by_key.get(fold_signum(x["signum"])) or next(
            (by_key[fold_signum(s)] for s in x["alt_signa"] if fold_signum(s) in by_key), None)
        (matched.append((x, r)) if r else missing.append(x))

    # the R corpus: Swedish Viking-age runestones
    stones = [(x, r) for x, r in matched if gaps.is_runestone(r)]
    moved_x = collections.Counter((int(is_moved(r)), x["original"]) for x, r in stones)
    lost_x = collections.Counter((int(r["flags"]["lost"]), x["extant"]) for x, r in stones)

    changed, more_read, examples = 0, 0, []
    for x, r in matched:
        reading = next((t["reading"] for t in x["readings"] if t.get("reading")), "")
        if not reading or not r.get("transliteration"):
            continue
        if runes(reading) != runes(r["transliteration"]):
            changed += 1
            if lost_count(reading) < lost_count(r["transliteration"]) and len(re.sub(r"-|…", "", runes(reading))) > \
                    len(re.sub(r"-|…", "", runes(r["transliteration"]))):
                more_read += 1
                if len(examples) < 40:
                    examples.append({"signum": x["signum"], "rundata_2018": r["transliteration"], "runor_2020": reading})

    notes = [(x["signum"], n) for x, _ in stones for n in x["notes"]]
    damage = [(s, n) for s, n in notes if DAMAGE.search(n)]
    termini = collections.Counter((x["termini"] or {}).get("tpq") for x, _ in stones)
    period_missing = collections.Counter((x.get("period") or "?") for x in missing)
    prefix_missing = collections.Counter(x["signum"].split(" ")[0] for x in missing)

    out = {
        "runor": len(runor), "matched": len(matched), "missing_in_rundata": len(missing),
        "missing_by_period": dict(period_missing.most_common()), "missing_by_prefix": dict(prefix_missing.most_common(20)),
        "missing_viking_age": [x["signum"] for x in missing if x.get("period") == "V"],
        "swedish_runestones": len(stones),
        "moved_vs_original": {f"moved={m} original={o}": n for (m, o), n in sorted(moved_x.items(), key=str)},
        "lost_vs_extant": {f"lost={l} extant={e}": n for (l, e), n in sorted(lost_x.items(), key=str)},
        "readings_changed": changed, "readings_more_runes": more_read, "more_runes_examples": examples,
        "stones_with_notes": len({s for s, _ in notes}), "damage_notes": len(damage), "damage_examples": damage[:30],
        "tpq_values": dict(termini.most_common(10)),
    }
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(out, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for k, v in out.items():
        if not isinstance(v, list):
            print(f"{k}: {v}")
    print(f"→ {a.out}")


if __name__ == "__main__":
    main()
