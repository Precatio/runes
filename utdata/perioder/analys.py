"""Vendeltid, vikingatid, medeltid (låst plan analysplaner/2026-11-17-perioderna.md, sha b1d1ed08): P1 begreppen i
Fornvännen per decennium, P2 de svenska runinskrifterna per halvsekel och föremålsklass. Skriver resultat.json.
    PYTHONPATH=. .venv/bin/python utdata/perioder/analys.py"""
import collections
import json
import os
import re
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
from src import nordic as nd  # noqa: E402
from utdata.norge.citat import letters  # noqa: E402

assert open(os.path.join(ROOT, "analysplaner/2026-11-17-perioderna.sha256")).read().startswith("b1d1ed08")
res = {"plan": "analysplaner/2026-11-17-perioderna.md", "sha": "b1d1ed08"}

# ---- P1 -----------------------------------------------------------------------------------------------------------------
TERMS = ["vendeltid", "vikingatid", "folkvandringstid", "merovingertid", "yngrejärnålder", "medeltid"]
TL = {t: letters(t) for t in TERMS}
S = sqlite3.connect("/Volumes/2TB/Antigrvity/Runes/downloads/tidskrifter/sok.sqlite")
docs = {k: (y, j) for k, y, j in S.execute("select key, year, journal from docs")}
pages = collections.Counter()
hits = collections.defaultdict(collections.Counter)
first = {}
for key, pg, text in S.execute("select key, page, text from pages"):
    y, j = docs.get(key, (None, ""))
    if "fornv" not in (j or "").lower():
        continue
    m = re.match(r"(\d{4})", str(y or ""))
    if not m:
        continue
    year = int(m.group(1))
    dec = year // 10 * 10
    pages[dec] += 1
    t = letters(text)
    for term, lt in TL.items():
        if lt in t:
            hits[dec][term] += 1
            if term not in first or (year, key, pg) < first[term]:
                first[term] = (year, key, pg)
res["P1"] = {"sidor_per_decennium": dict(sorted(pages.items())),
             "andel": {dec: {t: round(hits[dec][t] / pages[dec], 4) for t in TERMS} for dec in sorted(pages)},
             "forsta": {t: {"ar": v[0], "key": v[1], "sida": v[2]} for t, v in first.items()}}

# ---- P2 -----------------------------------------------------------------------------------------------------------------
rd = json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["inscriptions"]
SE_PREFIX = {"U", "Sö", "Ög", "Vg", "Sm", "Öl", "G", "Vs", "Nä", "Gs", "Hs", "M", "Ån", "J", "D", "Bo", "Vr", "Hälsingland"}
se = [r for r in rd if r["signum"].split()[0] in SE_PREFIX]
STONE = re.compile(r"runsten|block|berghäll|bergvägg|häll i berget|jordfast", re.I)
CHURCH = re.compile(r"grav|kist|dopfunt|klocka|puts|kyrk|portal|altar|kalk|dörr|bänk|fönster|vägg|pelare|mur", re.I)


def klass(r):
    o = r.get("object") or ""
    if STONE.search(o) and not re.search(r"gravhäll", o, re.I):
        return "sten"
    if CHURCH.search(o):
        return "kyrka_grav"
    return "losa"


per = collections.defaultdict(collections.Counter)
utan = collections.Counter()
for r in se:
    y = nd.year_of(r)
    k = klass(r)
    if y is None or not (300 <= y <= 1600):
        utan[(r.get("period") or "?", k)] += 1
        continue
    per[y // 50 * 50][k] += 1
res["P2"] = {"inskrifter": len(se), "per_halvsekel": {b: dict(per[b]) for b in sorted(per)},
             "utan_ar": {f"{p}/{k}": n for (p, k), n in sorted(utan.items())},
             "per_klass_totalt": dict(collections.Counter(klass(r) for r in se))}
json.dump(res, open(os.path.join(HERE, "resultat.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

print("P1 första:", res["P1"]["forsta"])
for dec in sorted(pages):
    print(dec, pages[dec], " ".join(f"{t[:6]}:{100 * res['P1']['andel'][dec][t]:.1f}" for t in TERMS))
print("P2", res["P2"]["inskrifter"], res["P2"]["per_klass_totalt"])
for b in sorted(per):
    print(b, dict(per[b]))
print("utan år", res["P2"]["utan_ar"])
