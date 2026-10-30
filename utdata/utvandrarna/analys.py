"""Prövningarna H1–H5 i analysplaner/2026-10-30-utvandrarna-och-hemmet.md på handkodningen (kodning.csv,
generationer.csv), med Holm över H1–H4; Danmark och Sverige sekundärt ur forsta_blick.json (reguljära uttryck).
    .venv/bin/python utdata/utvandrarna/analys.py      Skriver resultat.json."""
import csv
import json
import os
import re

from scipy.stats import binomtest, fisher_exact

OUT = os.path.dirname(os.path.abspath(__file__))
THEO = re.compile(r"^(Þór|Þor|Þúr|Thor|Ás|Ôs|Ást|Frey|Frø|Ingi|Yngv|Guð)", re.I)
rows = list(csv.DictReader(open(os.path.join(OUT, "kodning.csv"), encoding="utf-8")))
west = [r for r in rows if not r["signum"].startswith("N ")]
norw = [r for r in rows if r["signum"].startswith("N ")]


def k(rs, col):
    return sum(int(r[col]) for r in rs)


def names(rs):
    out = []
    for r in rs:
        for part in [p for p in r["namn"].split(";") if p]:
            n, o = part.rsplit(":", 1)
            out.append((n, o))
    return out


def fisher(a, na, b, nb, alt):
    odds, p = fisher_exact([[a, na - a], [b, nb - b]], alternative=alt)
    return {"west": [a, na], "norway": [b, nb], "share_west": a / na, "share_norway": b / nb, "or": odds, "p": p}


res = {"n_west": len(west), "n_norway": len(norw)}
res["H1"] = fisher(k(west, "plats_andra_sidan"), len(west), k(norw, "plats_andra_sidan"), len(norw), "less")
res["H2"] = fisher(k(west, "slakt_bakat"), len(west), k(norw, "slakt_bakat"), len(norw), "greater")
res["H2_nordisk"] = fisher(k(west, "slakt_bakat_nordisk"), len(west), k(norw, "slakt_bakat_nordisk"), len(norw), "greater")
wn = [n for n, o in names(west) if o == "n"]
nn = [n for n, o in names(norw) if o == "n"]
res["H3"] = fisher(sum(1 for n in wn if THEO.match(n)), len(wn), sum(1 for n in nn if THEO.match(n)), len(nn), "greater")
res["H3"]["theo_west"] = sorted(n for n in wn if THEO.match(n))
res["H4"] = fisher(k(west, "pris"), len(west), k(norw, "pris"), len(norw), "two-sided")
ps = {h: res[h]["p"] for h in ("H1", "H2", "H3", "H4")}
run = 0
for i, h in enumerate(sorted(ps, key=ps.get)):
    run = max(run, min(1, ps[h] * (len(ps) - i)))
    res[h]["holm"] = run
    res[h]["holds"] = run < 0.05
gen = list(csv.DictReader(open(os.path.join(OUT, "generationer.csv"), encoding="utf-8")))
shift = {"n->n": 0, "g->g": 0, "n->g": 0, "g->n": 0}
for g in gen:
    shift[f"{g['ursprung_förälder']}->{g['ursprung_barn']}"] += 1
res["H5"] = {"pairs": len(gen), **shift}
if len(gen) >= 8 and shift["n->g"] + shift["g->n"]:
    res["H5"]["sign_p"] = binomtest(shift["n->g"], shift["n->g"] + shift["g->n"]).pvalue
res["origins_west"] = {o: sum(1 for _, x in names(west) if x == o) for o in ("n", "g", "?")}
fb = json.load(open(os.path.join(OUT, "forsta_blick.json"), encoding="utf-8"))
res["secondary"] = {c: {"n": fb[c]["n"], "lineage_regex": fb[c]["share_lineage"], "theo": fb[c]["share_theo"],
                        "theo_k": [fb[c]["theo"], fb[c]["names"]], "places_nordic": len(fb[c]["places_nordic"])}
                    for c in ("Danmark", "Sverige")}
json.dump(res, open(os.path.join(OUT, "resultat.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float)
for h in ("H1", "H2", "H2_nordisk", "H3", "H4"):
    r = res[h]
    print(h, r["west"], r["norway"], f"{r['share_west']:.2f} vs {r['share_norway']:.2f}", f"p {r['p']:.3f}",
          f"holm {r.get('holm', float('nan')):.3f}" if "holm" in r else "", r.get("holds", ""))
print("H5", res["H5"], "ursprung väster", res["origins_west"])
print("theo väster", res["H3"]["theo_west"])
