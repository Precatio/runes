"""Satsdata för ordpars- och ordnätverksanalysen (ordpar.R).

Vikingatida runstenar (standardregeln: enbart runstenar), en rad per sats: normaliseringens ord i
ristad ordning, nyckel-normaliserade (rl.key), personnamn hopslagna till platshållaren NN
(normaliseringen skriver namn med stor bokstav). Satsgräns = skiljetecken i normaliseringen, så
ordpar aldrig räknas över satsgräns. Utdata: ordpar_satser.csv.
"""
import os
_PROJ = str(__import__("pathlib").Path(__file__).resolve().parents[2])  # projektmappen, var den än ligger
import csv
import re
import sys

sys.path.insert(0, _PROJ)
from src import runlm as rl

recs = [r for r in rl.load_rundata() if rl.viking(r) and rl.object_kind(r) == "runsten"
        and r.get("normalization")]

with open(os.path.join(_PROJ, "utdata/ordpar/ordpar_satser.csv"),
          "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["signum", "prefix", "region", "epok", "sats", "ord"])
    n_satser = 0
    for r in recs:
        prefix = r["signum"].split(" ")[0]
        region = rl.AREA_OF.get(re.sub(r"\d.*", "", prefix) if prefix not in rl.AREA_OF else prefix)
        if region is None:
            region = rl.AREA_OF.get(re.match(r"[A-Za-zÖÄÅöäå]+", prefix).group(0), "övrigt")
        norm = re.sub(r"(\S+)/\S+", r"\1", r["normalization"]).replace('"', "").replace("(?)", "")
        for i, sats in enumerate(re.split(r"[.,;:!?]+", norm)):
            ord_ = []
            for tok in sats.split():
                t = re.sub(r"[\[\]()§¬]", "", tok)
                if not re.search(r"[^\W\d_]", t) or "..." in t or "-" in t:
                    continue
                namn = t[:1].isupper()
                ord_.append("NN" if namn else rl.key(rl.normtok(t)))
            if len(ord_) >= 2:
                w.writerow([r["signum"], prefix, region, rl.epoch(r) or "", i, " ".join(ord_)])
                n_satser += 1
print("satser:", n_satser, "| stenar:", len(recs))
