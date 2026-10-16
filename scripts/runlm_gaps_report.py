"""Sammanställer de verkliga luckorna (utdata/Malt/runlm_luckor.json från scripts/runlm_gaps.py) utan att räkna om:
  * hur ofta modellen kommer fram till samma ord som Rundatas utgivare, både strikt (samma lemma) och med samma ord i
    annan böjning eller normalisering räknat som samma (src/runlm.same_word);
  * modellens säkerhet mot hur ofta den stämmer; 'okänt ord' räknas inte som en gissning;
  * de säkra oenigheterna (minst 0,95, ett känt ord, inte samma ord) – kandidater till en andra bedömning;
  * öppna luckor där modellen har ett säkert förslag på ett känt ord.
Inskrifter som Rundata inte tolkar alls (bara '...' eller futhark) lämnas utanför: där finns inget språk att räkna på.
Skriver utdata/Malt/runlm_luckor_rapport.json.
    .venv/bin/python -m scripts.runlm_gaps_report"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.runlm import load_rundata, norm_words, same_word, sections  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# the gap file (scripts/runlm_gaps.py), or several when the parts were run apart (--fold)
paths = [a for a in sys.argv[1:] if a.endswith(".json")] or [os.path.join(ROOT, "utdata", "Malt", "runlm_luckor.json")]
rows = [x for p_ in paths for x in json.load(open(p_))["rows"]]
by = {r["signum"]: r for r in load_rundata()}


def interpreted(sig):
    """Does Rundata read the inscription as language: at least two words that are neither '...' nor futhark?"""
    n = by[sig].get("normalization") or ""
    n = re.sub(r"<[^>]*>", " ", n)
    return sum(1 for _, p in sections(n) for w in norm_words(p) if not w.startswith("...")) >= 2


rows = [x for x in rows if interpreted(x["sig"])]
known = lambda x: bool(x["word"]) and x["word"] != "<unk>"
val = [x for x in rows if x["status"] == "återställt"]
agree = lambda x: bool(x["agrees"]) or (known(x) and same_word(x["word"], x["rundata"]))
out = {"n_restored": len(val), "strict": sum(bool(x["agrees"]) for x in val) / max(1, len(val)),
       "same_word": sum(agree(x) for x in val) / max(1, len(val)), "unknown": sum(not known(x) for x in val)}
print(f"återställda av Rundata: {len(val)}; samma ord strikt {out['strict']:.1%}, samma ord i annan form räknat "
      f"{out['same_word']:.1%}; modellen säger 'okänt ord' i {out['unknown']}")
out["reliability"] = []
for lo, hi in ((0, 0.5), (0.5, 0.8), (0.8, 0.95), (0.95, 1.01)):
    ys = [x for x in val if known(x) and lo <= x["p"] < hi]
    acc = sum(agree(x) for x in ys) / max(1, len(ys))
    out["reliability"].append({"lo": lo, "hi": min(hi, 1), "n": len(ys), "agree": acc})
    print(f"   säkerhet {lo:.2f}–{min(hi, 1):.2f}: n={len(ys)}, samma ord som Rundata {acc:.0%}")


def unique(xs):
    seen = {}
    for x in sorted(xs, key=lambda x: -x["p"]):
        seen.setdefault((x["sig"], x["carved"]), x)
    return [{k: x[k] for k in ("sig", "carved", "fill", "word", "p", "rundata", "context", "alts")} for x in seen.values()]


out["disagreements"] = unique([x for x in val if known(x) and x["p"] >= 0.95 and not agree(x)])
out["open"] = unique([x for x in rows if x["status"] == "ej återställt" and known(x) and x["p"] >= 0.9])
print(f"säkra oenigheter (≥ 0,95, känt ord, inte samma ord): {len(out['disagreements'])}")
for x in out["disagreements"]:
    print(f"  {x['sig']:16} {x['carved']:12} Rundata {x['rundata']:14} modellen {x['word']:12} ({x['p']:.2f})")
print(f"öppna luckor med säkert förslag (≥ 0,9, känt ord): {len(out['open'])}")
for x in out["open"]:
    print(f"  {x['sig']:16} {x['carved']:14} → {x['word']:12} ({x['p']:.2f})")
json.dump(out, open(os.path.join(ROOT, "utdata", "Malt", "runlm_luckor_rapport.json"), "w"), ensure_ascii=False, indent=1)
