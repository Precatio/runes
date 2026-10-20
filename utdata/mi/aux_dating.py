"""Sannolikhetsmodellens språkdatering som hjälpvariabel för den multipla imputationen (analysplan_mi.md, punkt 2).

För de runstenar som finns i dateringsprovet (utdata/runlm_forfining/datering_tm14.json) används provets
log-sannolikheter, räknade med modellen för den del stenen inte ingick i. Övriga runstenar med minst 10 läsbara runor –
de som saknar datering i både Rundata och ornamentiken, och som därför inte var med i provet – läses med en modell
tränad på alla vikingatida texter, med samma inställningar som provet (scripts/runlm_dating.py). Deras text bär ingen
datering som kan läcka in i modellen. Färre än 10 läsbara runor: ingen hjälpvariabel ("okänd").
Skriver utdata/mi/aux_dating.json: {signum: {"ll": {epok: log p}, "source": "oof" | "alla"}}.
    PYTHONPATH=. .venv/bin/python utdata/mi/aux_dating.py"""
import json
import os
import re
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
from src.runlm import EPOCHS, PHASE, RUNES, Model, carved_groups, context, edda_tokens, load_rundata, posteriors, runekey, viking  # noqa: E402
from src.research_gaps import is_runestone  # noqa: E402

TEST = json.load(open(os.path.join(ROOT, "utdata", "runlm_forfining", "datering_tm14.json")))
S = TEST["settings"]
MALT = "DR NOR1988;5"


def readable(r):
    """Som i scripts/runlm_dating.py: de huggna grupperna utan skadade eller olästa runor (varje lucka en gräns)."""
    groups, signs = [], []
    for g in carved_groups(r["transliteration"]):
        parts = [p for p in re.split(r"[^%s]+" % re.escape("".join(sorted(RUNES))), runekey(g)) if p]
        for k, p in enumerate(parts):
            groups.append(p)
            if k < len(parts) - 1:
                signs.append(len(groups) - 1)
    return groups, signs


recs = load_rundata()
V = [r for r in recs if viking(r) and r.get("transliteration") and r.get("normalization") and r["signum"] != MALT]
out = {x["sig"]: {"ll": x["ll"], "source": "oof"} for x in TEST["rows"]}
todo = [r for r in V if is_runestone(r) and r["signum"] not in out and sum(len(g) for g in readable(r)[0]) >= S["min_runes"]]
print("ur dateringsprovet:", len(out), "– att läsa med modellen för alla:", len(todo), flush=True)
t0 = time.time()
m = Model(V, edda_tokens=edda_tokens(), aligned=True, contexts=True, alpha=S["alpha"], kappa_e=S["kappa_e"],
          lm_beta=S["lm_beta"], lam_name=S["lam_name"], lam_class=S["lam_class"])
print(f"modellen byggd efter {time.time() - t0:.0f} s", flush=True)
for i, r in enumerate(todo):
    groups, signs = readable(r)
    path = context(r)[:5]  # era, phase, epoch, area, region – not the carver, as in the dating test
    out[r["signum"]] = {"ll": {e: posteriors(m, groups, signs, ctx=m.ctx((path[0], PHASE[e], e) + path[3:]))[0] for e in EPOCHS},
                        "source": "alla"}
    if i % 100 == 0:
        print(f"{i + 1} av {len(todo)} efter {time.time() - t0:.0f} s", flush=True)
json.dump(out, open(os.path.join(ROOT, "utdata", "mi", "aux_dating.json"), "w"), indent=0)
print("klart:", len(out), "stenar", flush=True)
