"""P0 i analysplaner/2026-11-10-sjalvkontroll-gravfalt.md: originalet (data.py + analys.R) körs om oförändrat, men
skriver till sjalvkontroll/p0/ i stället för att skriva över originalets filer. Bara utdatakatalogen byts.
    .venv/bin/python utdata/familjens_plats/sjalvkontroll/p0.py"""
import json
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
FP = os.path.dirname(HERE)
ROOT = os.path.abspath(os.path.join(FP, "..", ".."))
P0 = os.path.join(HERE, "p0")
os.makedirs(P0, exist_ok=True)

src = open(os.path.join(FP, "data.py"), encoding="utf-8").read()
old = 'OUT = os.path.dirname(os.path.abspath(__file__))'
assert src.count(old) == 1
src = src.replace(old, f'OUT = {P0!r}')
exec(compile(src, os.path.join(FP, "data.py"), "exec"), {"__file__": os.path.join(FP, "data.py"), "__name__": "__main__"})

r = open(os.path.join(FP, "analys.R"), encoding="utf-8").read()
old_r = 'dir <- "utdata/familjens_plats"'
assert r.count(old_r) == 1
rp = os.path.join(P0, "analys_p0.R")
open(rp, "w", encoding="utf-8").write(r.replace(old_r, 'dir <- "utdata/familjens_plats/sjalvkontroll/p0"'))
subprocess.run(["Rscript", rp], cwd=ROOT, check=True)

pub = [t for t in json.load(open(os.path.join(FP, "familjens_plats.json")))["tests"] if t["key"] == "y1_gravfalt"][0]
new = [t for t in json.load(open(os.path.join(P0, "familjens_plats.json")))["tests"] if t["key"] == "y1_gravfalt"][0]
same_csv = open(os.path.join(FP, "stenar.csv"), "rb").read() == open(os.path.join(P0, "stenar.csv"), "rb").read()
m, q = pub["main"], new["main"]
ok = (round(q["share_grupp"] * 100) == 82 and round(q["share_ensam"] * 100) == 55 and round(q["or"], 1) == 2.4
      and f"{q['p']:.1g}" == "0.0002")
out = {"villkor": "82 mot 55 %, OR 2,4, p 0,0002 (avrundat som i resultat.md)", "reproducerar": ok,
       "stenar_csv_identisk": same_csv, "publicerat": m, "omkort": q,
       "identiskt_utfall": all(abs(m[k] - q[k]) < 1e-9 for k in ("share_grupp", "share_ensam", "or", "p"))}
json.dump(out, open(os.path.join(HERE, "p0.json"), "w"), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False, indent=1))
