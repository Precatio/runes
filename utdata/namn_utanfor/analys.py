"""Steg 3 i analysplaner/2026-10-30-namnen-utanfor-runstenarna.md: varje fornnordiskt namn (ursprung.csv) i en grupp –
runsten, annan runtext, myt, övrigt – och prövningarna P1–P4. Runnamnen översätts med utdata/overlevde/namnregler.py
(med känslighetsprovets á → a och f → v och -i → -e, för att inte missa en runform) och medeltidslexikonet.
    .venv/bin/python utdata/namn_utanfor/analys.py      Skriver grupper.csv och resultat.json."""
import csv
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict

from scipy.stats import mannwhitneyu

OUT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(OUT, "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "utdata", "overlevde"))
from api.rundata import store  # noqa: E402
from namnregler import fold, rules  # noqa: E402
from src import entities  # noqa: E402
from src.research_gaps import is_runestone  # noqa: E402


def key(n):
    """Spelling-blind key for a modern name: Th → T, C → K, W → V (Thorvald = Torvald, Eric = Erik, Siw = Siv)."""
    k = n.lower().replace("th", "t").replace("c", "k").replace("w", "v").replace("q", "k").replace("ph", "f")
    return re.sub(r"[^a-zåäöüé]", "", k)


def forms(name):
    return {key(f) for sex in ("m", "k") for f in rules(name, sex, True)}


lex = defaultdict(set)
for x in csv.DictReader(open(os.path.join(ROOT, "utdata", "namnarv", "lexikon.csv"), encoding="utf-8")):
    if x["runsten"]:
        lex[x["runsten"]].add(key(x["normalform"]))

s = store()
stone_keys, other_keys = defaultdict(set), defaultdict(set)  # modern key -> runic names (for the table)
for r in s.inscriptions:
    if is_runestone(r):
        try:
            persons = [p["name"] for p in entities.extract(r)["persons"] if p.get("name") and not p.get("uncertain")]
        except Exception:  # noqa: BLE001
            persons = []
        for n in persons:
            if n.endswith("-"):  # a name fragment (Þor-) is not a name
                continue
            for k in forms(n) | lex.get(fold(n), set()):
                stone_keys[k].add(n)
    else:
        for n in re.findall(r'"([A-ZÁÉÍÓÚÝÞÆÖØÔÅÄa-zþðæøôáéíóúýåäö\-]+)', r.get("normalization") or ""):
            if len(n) > 2 and not n.endswith("-"):
                for k in forms(n):
                    other_keys[k].add(n)

scb2020, scb1999, sexc = Counter(), Counter(), defaultdict(Counter)
for x in json.load(open(os.path.join(ROOT, "data", "namn", "scb_tilltalsnamn.json"), encoding="utf-8"))["names"]:
    scb2020[x["name"]] += x["n2020"] or 0
    scb1999[x["name"]] += x.get("n1999") or 0
    sexc[x["name"]][x["sex"]] += (x["n2020"] or 0) + (x.get("n1999") or 0)

# Hand review (2026-10-30) of the names the rules did not reach: the same name as on a Swedish runestone, in a later
# sound development (not short or pet forms such as Olle, Kalle, Uffe). Each runic form is checked against the stones.
SAME_AS_STONE = {"Kjell": "Ketill", "Sixten": "Sigsteinn", "Love": "Lófi", "Bror": "Bróðir", "Rolf": "Hrólfr",
                 "Tove": "Tófa", "Tuva": "Tófa", "Gunhild": "Gunnhildr", "Anund": "Ônundr", "Ingegärd": "Ingigerðr",
                 "Inger": "Ingigerðr", "Ingmar": "Ingimarr", "Siri": "Sigríðr", "Estrid": "Ástríðr", "Styrbjörn": "Styrbjôrn",
                 "Öyvind": "Eyvindr", "Einar": "Einarr", "Ejnar": "Einarr", "Egil": "Egill", "Geir": "Geirr",
                 "Sverker": "Sverkir", "Svenning": "Sveinungr", "Gunborg": "Gunnborga", "Gunvor": "Gunnvôr",
                 "Elof": "Eilafr", "Uno": "Uni", "Thyra": "Þyrvé", "Tyra": "Þyrvé"}
# False runic matches found in the review: Tárr is not Tor (å/o swap), and Týr in N B604 is the rune name in a rune row
FALSE_RUNIC = {"Tor": {"Tárr"}, "Tyr": {"Týr"}}
for modern, bad in FALSE_RUNIC.items():
    for d in (stone_keys, other_keys):
        d[key(modern)] -= bad
        if not d[key(modern)]:
            del d[key(modern)]
stone_names = {n for v in stone_keys.values() for n in v}
assert set(SAME_AS_STONE.values()) <= stone_names, set(SAME_AS_STONE.values()) - stone_names
for modern, runic in SAME_AS_STONE.items():
    stone_keys[key(modern)].add(runic)

rows = []
for r in csv.DictReader(open(os.path.join(OUT, "ursprung.csv"), encoding="utf-8")):
    n = r["namn"]
    if r["ursprung"] != "fornnordiskt" or (scb2020[n] < 10 and scb1999[n] < 10):
        continue
    k = key(n)
    if k in stone_keys:
        grp, src = "runsten", sorted(stone_keys[k])[:4]
    elif k in other_keys:
        grp, src = "annan runtext", sorted(other_keys[k])[:4]
    elif r["myt"] == "1":
        grp, src = "myt", []
    else:
        grp, src = "övrigt", []
    sx = sexc[n].most_common(1)[0][0] if sexc[n] else "?"
    rows.append({"namn": n, "grupp": grp, "kön": sx, "n1999": scb1999[n], "n2020": scb2020[n],
                 "tillväxt": round(math.log((scb2020[n] + 5) / (scb1999[n] + 5)), 4), "runform": "|".join(src),
                 "grund": r["grund"]})
with open(os.path.join(OUT, "grupper.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(sorted(rows, key=lambda x: (x["grupp"], -x["n2020"])))

G = defaultdict(list)
for x in rows:
    G[x["grupp"]].append(x)
res = {"n": len(rows), "groups": {g: {"n": len(v), "bearers_2020": sum(x["n2020"] for x in v),
                                      "bearers_1999": sum(x["n1999"] for x in v),
                                      "median_growth": sorted(x["tillväxt"] for x in v)[len(v) // 2],
                                      "names": [x["namn"] for x in sorted(v, key=lambda x: -x["n2020"])]}
                                  for g, v in G.items()}}
gr = lambda xs: [x["tillväxt"] for x in xs]  # noqa: E731
lit, stones = G["myt"] + G["övrigt"], G["runsten"]
res["P2"] = {"a": len(lit), "b": len(stones), "p": mannwhitneyu(gr(lit), gr(stones), alternative="greater").pvalue}
other = G["runsten"] + G["annan runtext"] + G["övrigt"]
res["P3"] = {"a": len(G["myt"]), "b": len(other), "p": mannwhitneyu(gr(G["myt"]), gr(other), alternative="greater").pvalue}
wom, men = [x for x in rows if x["kön"] == "K"], [x for x in rows if x["kön"] == "M"]
res["P4"] = {"a": len(wom), "b": len(men), "p": mannwhitneyu(gr(wom), gr(men), alternative="two-sided").pvalue,
             "median_women": sorted(gr(wom))[len(wom) // 2], "median_men": sorted(gr(men))[len(men) // 2]}
ps = {h: res[h]["p"] for h in ("P2", "P3", "P4")}
run = 0
for i, h in enumerate(sorted(ps, key=ps.get)):
    run = max(run, min(1, ps[h] * (len(ps) - i)))
    res[h]["holm"] = run
    res[h]["holds"] = run < 0.05
json.dump(res, open(os.path.join(OUT, "resultat.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float)
for g, v in res["groups"].items():
    print(f"{g:14} n={v['n']:3} bärare 2020={v['bearers_2020']:8} 1999={v['bearers_1999']:8} median tillväxt={v['median_growth']:+.2f}")
    print("    ", ", ".join(v["names"][:40]))
for h in ("P2", "P3", "P4"):
    print(h, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in res[h].items()})
