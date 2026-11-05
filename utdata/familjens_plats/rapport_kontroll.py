"""Kontrolluppgifter för rapportversion 3 av rapporten om familjens plats (utdata/blogg/build/build_rapport_familjens_plats.py),
ur filer som inte ligger i git: korpusens frysdatum och när Runor (utgåva 2020) hämtades. Ändrar ingen analys och inga
resultatfiler.
    .venv/bin/python utdata/familjens_plats/rapport_kontroll.py      Skriver rapport_kontroll.json."""
import json
import os

OUT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(OUT, "..", ".."))
FP = "3f58e9339191761e"
done = json.load(open(os.path.join(ROOT, "data", "cache", "r", "corpus", FP, "done.json"), encoding="utf-8"))
assert done["fingerprint"] == FP
runor = json.load(open(os.path.join(ROOT, "data", "raa", "runor_2020.json"), encoding="utf-8"))
out = {"korpus": FP, "korpus_beraknad": done["computed_at"][:10],
       "runor": {"kalla": runor["source"], "utgava": str(runor["edition"]), "hamtad": runor["fetched"]}}
json.dump(out, open(os.path.join(OUT, "rapport_kontroll.json"), "w"), ensure_ascii=False, indent=1)
print(out)
