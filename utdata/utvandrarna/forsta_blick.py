"""Första blick (beskrivande, ingen låst plan, 2026-10-30): vad säger de vikingatida minnesinskrifterna utanför Norden om
det gamla hemmet? Nämnda platser, släkt bakåt (X:s son/dotter), gudanamn i personnamnen, kristna markörer – mot
minnesinskrifterna i Norge, Danmark och Sverige.
    .venv/bin/python utdata/utvandrarna/forsta_blick.py      Skriver forsta_blick.json."""
import json
import os
import re
import sys
from collections import Counter, defaultdict

OUT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(OUT, "..", ".."))
sys.path.insert(0, ROOT)
from api.rundata import store  # noqa: E402

WEST = {"IM": "Isle of Man", "E": "England", "IR": "Irland", "Sc": "Skottland", "Or": "Orkney", "Sh": "Shetland"}
EAST = {"UA": "Berezan", "By": "Bysans", "RU": "Ryssland"}
ATL = {"GR": "Grönland", "IS": "Island", "FR": "Färöarna"}
SWE = {"U", "Sö", "Ög", "Öl", "Vg", "Sm", "G", "Vs", "Gs", "Nä", "Hs", "M", "Ån", "J", "D", "Vr", "Bo", "Hr"}


def region(sig):
    p = sig.split(" ")[0]
    if p == "IM":
        return "Isle of Man"
    if p in WEST:
        return "Övriga brittiska öarna"
    if p in EAST or p in ATL:
        return "Österled och Nordatlanten"
    if p == "N":
        return "Norge"
    if p == "DR":
        return "Danmark"
    if p in SWE:
        return "Sverige"
    return None


MEMO = re.compile(r"in memory of|raised .* (stone|cross)|erected .* cross|made this .* (vault|tomb)|laid this stone", re.I)
THEO = re.compile(r"^(Þór|Þor|Þúr|Thor|Ás|Ôs|Ást|Frey|Frø|Ingi|Yngv|Guð)", re.I)
LINEAGE = re.compile(r"\b[A-ZÁÉÍÓÚÞÆÖØÔ][\w\-]*['’]s (son|daughter|brother['’]s son)\b|\bthe (son|daughter) of [A-ZÁÉÍÓÚÞÆÖØÔ<]", re.U)
CHRIST = re.compile(r"\bGod\b|\bChrist|\bJesus|\bsoul\b|\bspirit\b|\bcross\b|\bMary\b|\bholy\b", re.I)
GODS = re.compile(r"\b(Þórr|Þor\b|Óðinn|Oðinn|Æsir|ása|Ása|Freyr|Frigg|Valhall|Nornir|Æsis|Ôsir)", re.U)
NORDIC_PLACE = re.compile(r"\b(Sweden|Svíþjóð|Denmark|Danmark|Norway|Nóregr|Gotland|Iceland|Ísland|Uppsala|Jutland|Scania|Skáney|Hälsingland|Swedes|Danes|Norwegians|Gautland|Götaland)\b")

s = store()
data = defaultdict(lambda: {"n": 0, "places_nordic": [], "lineage": [], "christ": 0, "names": 0, "theo": 0, "gods": []})
for r in s.inscriptions:
    reg = region(r["signum"])
    if not reg or not (r.get("dating") or "").startswith("V"):
        continue
    tr = r.get("translation") or r.get("translation_en") or ""
    if not MEMO.search(tr):
        continue
    d = data[reg]
    d["n"] += 1
    nz = r.get("normalization") or ""
    if NORDIC_PLACE.search(tr):
        d["places_nordic"].append(r["signum"])
    if LINEAGE.search(tr):
        d["lineage"].append(r["signum"])
    if CHRIST.search(tr):
        d["christ"] += 1
    if GODS.search(nz):
        d["gods"].append(r["signum"])
    names = [n.rstrip("(?)").strip("[]") for n in re.findall(r'"([^\s,.:;§]+)', nz)]
    d["names"] += len(names)
    d["theo"] += sum(1 for n in names if THEO.match(n))
res = {k: {**v, "share_lineage": round(len(v["lineage"]) / v["n"], 3) if v["n"] else None,
           "share_christ": round(v["christ"] / v["n"], 3) if v["n"] else None,
           "share_theo": round(v["theo"] / v["names"], 3) if v["names"] else None} for k, v in data.items()}
json.dump(res, open(os.path.join(OUT, "forsta_blick.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for k in ("Isle of Man", "Övriga brittiska öarna", "Österled och Nordatlanten", "Norge", "Danmark", "Sverige"):
    v = res.get(k)
    if v:
        print(f"{k:28} n={v['n']:4} nordisk plats={len(v['places_nordic']):3} släkt bakåt={len(v['lineage']):3} ({v['share_lineage']})"
              f" kristet={v['share_christ']} gudanamn i pers.namn={v['theo']}/{v['names']} ({v['share_theo']}) gudar i text={v['gods'][:5]}")
        if k not in ("Sverige", "Danmark", "Norge"):
            print("    plats:", v["places_nordic"], "släkt:", v["lineage"])
