"""Studie 3: snitten i P-data som CSV för variansuppdelningen i R (s3_varians.R), enligt den låsta planen."""
import csv, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))
from src.research_gaps import certain_carvers  # noqa: E402
import s_analys as sa  # noqa: E402

STAV = {"Hs 10", "Hs 12", "Hs 14", "Hs 15", "M 3", "M 4", "M 7", "M 8", "Sö 164"}
rows, per = [], {}
for key, ds in sa.objects(sa.load("automatisk_korning")).items():
    d0 = ds[0]
    if sa.object_type(d0) != "runsten" or key in STAV:
        continue
    cs = certain_carvers(sa.rec(d0) or {})
    if len(cs) != 1:
        continue
    per.setdefault(cs[0], set()).add(key)
    for d in ds:
        for s in d["slices"]:
            rows.append({"sten": key, "ristare": cs[0], "bergart": sa.rock(d0),
                         "skanner": "ATOS" if d["series"] in sa.ATOS else "HandySCAN",
                         "upplosning": d["parameters"].get("mesh_point_spacing_mm"),
                         **{m: s.get(m) for m in sa.MAIN}})
keep = {c for c, st in per.items() if len(st) >= 2}
rows = [r for r in rows if r["ristare"] in keep]
with open(os.path.join(HERE, "s3_snitt.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader(); w.writerows(rows)
print(len(rows), "snitt;", {c: sorted(per[c]) for c in sorted(keep)})
