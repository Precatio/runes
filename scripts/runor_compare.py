"""Jämför Runor 2020 (data/raa/runor_2020.json, från scripts/fetch_runor.py) med appens Rundata (2018).

    python -m scripts.runor_compare [--out utdata/runor/jamforelse.json]

Svarar på vad Runor tillför: inskrifter som saknas i Rundata, stenar som Runor anger som försvunna eller på sin
ursprungliga plats jämfört med appens flaggor (lost, moved i src/r_bridge.py), anteckningar om skador och läsningar
som har ändrats sedan 2018, särskilt där Runor läser runor som Rundata har som förlorade.

Signa matchas exakt först (fold_signum slår ihop 'Nä 11' och 'N A11'); läsningar med fler runor räknar bara säkert
lästa runor (inte runor inom parentes), och exemplen som blir fynd per sten är svenska runstenar – andra föremål
redovisas för sig.
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import re

from api.rundata import _exact_key, store
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


UNCERTAIN = re.compile(r"\([^()]*\)")


def sure_runes(reading: str) -> str:
    """De säkert lästa runorna: utan förlorade runor och utan osäkra runor inom parentes (Runor skriver 'k(i)(m)t')."""
    return re.sub(r"-|…", "", runes(UNCERTAIN.sub("", reading)))


def more_runes(runor_reading: str, rundata_reading: str) -> bool:
    """Runor läser fler runor: färre förlorade runor och fler säkert lästa runor än Rundata."""
    return (lost_count(runor_reading) < lost_count(rundata_reading)
            and len(sure_runes(runor_reading)) > len(sure_runes(rundata_reading)))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=os.path.join(ROOT, "utdata", "runor", "jamforelse.json"))
    a = ap.parse_args(argv)
    runor = json.load(open(SRC, encoding="utf-8"))["inscriptions"]
    ours = store().inscriptions
    # The exact signum first: fold_signum drops diacritics, so the Närke 'Nä 11' and the Norwegian 'N A11' share a folded
    # key, and Runor's Närke stones were once compared with Norwegian texts. The folded key is only the fallback.
    by_exact: dict[str, dict] = {}
    by_key: dict[str, dict] = {}
    for r in ours:
        by_exact.setdefault(_exact_key(r["signum"]), r)
        by_key.setdefault(fold_signum(r["signum"]), r)
    for r in ours:
        for alt in re.split(r"[;,]\s*(?=[A-ZÅÄÖ])", r.get("alt_signum") or ""):
            if alt.strip():
                by_key.setdefault(fold_signum(alt.strip()), r)

    def find(signum: str):
        return by_exact.get(_exact_key(signum)) or by_key.get(fold_signum(signum))

    matched, missing = [], []
    for x in runor:
        r = find(x["signum"]) or next((find(s) for s in x["alt_signa"] if find(s)), None)
        (matched.append((x, r)) if r else missing.append(x))

    # the R corpus: Swedish Viking-age runestones
    stones = [(x, r) for x, r in matched if gaps.is_runestone(r)]
    moved_x = collections.Counter((int(is_moved(r)), x["original"]) for x, r in stones)
    lost_x = collections.Counter((int(r["flags"]["lost"]), x["extant"]) for x, r in stones)

    # Readings: all matched objects are counted, but the examples that become findings per stone (src/stone_findings.py)
    # are Swedish runestones only; other objects are listed separately (runestones only by default)
    changed = more_read = changed_rs = more_read_rs = 0
    examples, examples_other = [], []
    for x, r in matched:
        reading = next((t["reading"] for t in x["readings"] if t.get("reading")), "")
        if not reading or not r.get("transliteration"):
            continue
        if runes(reading) != runes(r["transliteration"]):
            stone = gaps.is_runestone(r)
            changed += 1
            changed_rs += stone
            if more_runes(reading, r["transliteration"]):
                more_read += 1
                more_read_rs += stone
                ex = {"signum": r["signum"], "rundata_2018": r["transliteration"], "runor_2020": reading}
                if stone and len(examples) < 40:
                    examples.append(ex)
                elif not stone and len(examples_other) < 40:
                    examples_other.append({**ex, "object": r.get("object") or None})

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
        "readings_changed": changed, "readings_more_runes": more_read,
        "readings_changed_runestones": changed_rs, "readings_more_runes_runestones": more_read_rs,
        "more_runes_examples": examples, "more_runes_examples_other_objects": examples_other,
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
