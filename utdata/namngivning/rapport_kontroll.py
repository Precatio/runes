"""Kontrollsiffror för rapportversion 2 av rapporten om namnleden (utdata/blogg/build/build_rapport_namnled.py), ur filer
som inte ligger i resultatfilerna: korpusens storlek och frysdatum, stilgruppernas årtal och handkontrollen av
människomätningen (src/people.py mot data/people_check.json, urval 2). Ändrar ingen analys och inga resultatfiler.
    .venv/bin/python utdata/namngivning/rapport_kontroll.py      Skriver rapport_kontroll.json."""
import json
import os
import sys

import pandas as pd

OUT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(OUT, "..", ".."))
sys.path.insert(0, ROOT)
from src import people  # noqa: E402

FP = "3f58e9339191761e"
D = os.path.join(ROOT, "data", "cache", "r", "corpus", FP)
c = pd.read_csv(os.path.join(D, "corpus.csv"), low_memory=False)
done = json.load(open(os.path.join(D, "done.json"), encoding="utf-8"))
assert done["fingerprint"] == FP
EARLY, LATE = ["RAK", "Fp", "Pr1", "Pr2"], ["Pr3", "Pr4", "Pr5"]  # som i analys.py
years = {"tidig_fran": int(c[c["style"].isin(EARLY)].style_from.min()), "tidig_till": int(c[c["style"].isin(EARLY)].style_to.max()),
         "sen_fran": int(c[c["style"].isin(LATE)].style_from.min()), "sen_till": int(c[c["style"].isin(LATE)].style_to.max())}

# handkontrollen: den dödes släktrelation (grupp) enligt src/people.py mot den blinda handkodningen i urval 2
chk = json.load(open(os.path.join(ROOT, "data", "people_check.json"), encoding="utf-8"))
ins = json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["inscriptions"]
by = {r["signum"]: r for r in ins}
lex = people.lexicon(ins)
rel_ok = 0
for s, h in chk["kodning2"].items():
    r = people.stone(by[s], lex)
    got = {g for g, _ in people.GROUPS if r[f"rel_{g}"]}
    rel_ok += got == set(filter(None, h["rel"].split("|")))

out = {"korpus": FP, "korpus_beraknad": done["computed_at"][:10], "n_runstenar": len(c), "stilgrupper_ar": years,
       "personkontroll": {"urval": chk["urval2"], "n": len(chk["kodning2"]), "relationsgrupp_ratt": rel_ok,
                          "regel": "src/people.py (den dödes släktrelation till resaren, i grupper)"}}
json.dump(out, open(os.path.join(OUT, "rapport_kontroll.json"), "w"), ensure_ascii=False, indent=1)
print(out)
