"""Datafil för statistiken om stavarna på runstenarna (scripts/stavar_stats.R, artikeln "Stenar och stavar"): en rad
per vikingatida runsten i Rundata med translitterering och normalisering (också fragment och försvunna stenar). Skriver utdata/stavar/stavar_data.csv.
    .venv/bin/python -m scripts.stavar_data"""
import csv
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import runlm as rl  # noqa: E402
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.join(ROOT, "utdata", "stavar")
os.makedirs(HERE, exist_ok=True)
MINNE = {"Sö 196", "Vs 1", "U 226", "U 332", "U 849"}          # staf rest som minnesmärke (Zilmer 2005, s. 156)
OSAKER = {"Sö 56"}                                              # "stafa marga": stavar som minnesmärke eller runor
RUNOR = {"Sm 16", "DR 40"}                                      # stafiR runa, þeR stafaR: runorna själva
STYLES = ["RAK", "Fp", "Pr1", "Pr2", "Pr3", "Pr4", "Pr5"]
YEARS = {k: (v[0] + v[1]) / 2 for k, v in rl.STYLE_YEARS.items()}
rows = []
for r in rl.load_rundata():
    if not (rl.viking(r) and r.get("transliteration") and r.get("normalization")):
        continue
    # runestones only (Rundata "runsten", also fragments and lost stones), 2026-10-17: coins, rune sticks and other
    # objects never speak of stones and would dilute the comparison
    if "runsten" not in (r.get("object") or "").lower():
        continue
    n = r["normalization"]
    st = (r.get("style") or "").replace("FP", "Fp").strip()
    core = st.split()[0].rstrip("?,") if st else ""
    core = core if core in STYLES else ""
    prov = r["signum"].split()[0]
    rows.append({"signum": r["signum"], "prov": prov, "malardalen": int(prov in ("U", "Sö", "Vs")),
                 "style": core, "year_mid": YEARS.get(core, ""), "early": (int(core in ("RAK", "Fp", "Pr1")) if core else ""),
                 "staf": "minne" if r["signum"] in MINNE else "osaker" if r["signum"] in OSAKER else "runor" if r["signum"] in RUNOR else "",
                 "plural": int(bool(re.search(r"\bst[æe]in(a|aR|ar|um)\b", n, re.I))),
                 "signed": int(any(c.get("kind") == "S" for c in (r.get("carvers") or []))),
                 "prayer": int(bool(re.search(r"\bhialpi\b|\bhjalpi\b", n, re.I))),
                 "thing": int(bool(re.search(r"þing", n, re.I))),
                 # the monument: U 226 continues U 225 ("gærðu hiar þingstað"), so U 226 counts as naming an assembly
                 # and U 225 is left out of the comparison (one monument, counted once)
                 "thing_mon": ("" if r["signum"] == "U 225" else 1 if r["signum"] == "U 226" else int(bool(re.search(r"þing", n, re.I))))})
with open(os.path.join(HERE, "stavar_data.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader(); w.writerows(rows)
print(len(rows), "inskrifter;", sum(1 for x in rows if x["staf"]), "med staf")
for x in rows:
    if x["staf"]: print(" ", x)
