"""Kodningskontroll för monoftongen i æi-ord (rapporten "Monoftongstavningen blir ovanligare", 2026-10-31).
Projektets regel (src/language_profile.py, ai_alla) räknar ett æi-ord som monoftong när translittereringen saknar
ai/ia/ei/ae. Den fångar också ord med bara a (rastu), utan vokal (sltn) eller dubbelt a (staa), som inte visar en
monoftong. Den stränga kodningen här: diftong om någon vokalgrupp i ordet är ai/ia/ei/ae (som regeln), monoftong om
ordets första vokalgrupp är i eller e, annars osäkert (räknas inte). Skriver stenar.csv (en rad per sten med båda
kodningarna) och kodning.json (fördelningen och ett slumpvis urval om 40 ord).
    .venv/bin/python utdata/monoftong/kodning.py"""
import json
import os
import random
import re
import sys

import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
from src import language_profile as lp, question  # noqa: E402

FP = "e83202e01a5e6d27"
OUT = os.path.dirname(os.path.abspath(__file__))
c = pd.read_csv(os.path.join(ROOT, "data", "cache", "r", "corpus", FP, "corpus.csv"), low_memory=False)
recs = {r["signum"]: r for r in json.load(open(os.path.join(ROOT, "data", "rundata.json")))["inscriptions"]}
rows = [{k: (None if pd.isna(v) else v) for k, v in r.items()}
        for r in c[["signum", "province", "parish", "style_from", "style_to"]].to_dict("records")]
HALF = question.halves(rows)
VOW = re.compile(r"[aeiouyøæåö]+")


def strict(w: str) -> str:
    if re.search(r"ai|ia|ei|ae", w):
        return "diftong"
    g = VOW.findall(w)
    return "monoftong" if g and g[0] in ("i", "e") else "osäkert"


base = c[c.trait_ai_alla.notna() & c.style_from.notna() & c.style_to.notna()].copy()
out, words = [], []
for r in base.itertuples():
    ws = [(n, w) for n, w in lp._case_pairs(recs[r.signum]) if "æi" in n.lower()]
    k = [strict(w) for _, w in ws]
    words += [(r.signum, n, w, ("monoftong" if not re.search(r"ai|ia|ei|ae", w) else "diftong"), s) for (n, w), s in zip(ws, k)]
    known = [s for s in k if s != "osäkert"]
    y_strict = None if not known else int(any(s == "monoftong" for s in known))
    hand = (f"R:{r.carver}" if isinstance(r.carver, str) and r.carver and r.carvers_uncertain == 0
            else f"S:{r.province}:{r.parish if isinstance(r.parish, str) else r.signum}")
    out.append({"signum": r.signum, "province": r.province, "half": HALF[r.signum],
                "t50": round(((r.style_from + r.style_to) / 2 - 1050) / 50, 4), "hand": hand,
                "y_rule": int(r.trait_ai_alla in ("monoftong", "båda")), "y_strict": y_strict,
                "n_words": len(ws), "n_mono_strict": k.count("monoftong"), "n_uncertain": k.count("osäkert")})
st = pd.DataFrame(out)
st.to_csv(os.path.join(OUT, "stenar.csv"), index=False)
wd = pd.DataFrame(words, columns=["signum", "norm", "translit", "rule", "strict"])
random.seed(2026)
sample = random.sample(words, 40)
res = {"n_stones": len(st), "n_words": len(wd),
       "rule_mono_words": int((wd.rule == "monoftong").sum()),
       "strict": wd.strict.value_counts().to_dict(),
       "rule_mono_to_uncertain": int(((wd.rule == "monoftong") & (wd.strict == "osäkert")).sum()),
       "uncertain_examples": wd[wd.strict == "osäkert"].translit.value_counts().head(15).to_dict(),
       "stones_changed": int((st.y_strict.notna() & (st.y_rule != st.y_strict)).sum()),
       "stones_dropped": int(st.y_strict.isna().sum()),
       "sample": [{"signum": s, "norm": n, "translit": w, "rule": a, "strict": b} for s, n, w, a, b in sample]}
json.dump(res, open(os.path.join(OUT, "kodning.json"), "w"), ensure_ascii=False, indent=1)
print({k: v for k, v in res.items() if k != "sample"})
