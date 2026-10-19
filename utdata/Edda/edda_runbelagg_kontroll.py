"""Eddatexternas runbelagda ordförråd, storlekskontrollerat.

Den snabba rankingen (edda_runbelagg.json) var längdförvirrad: en längre text hinner samla fler
sällsynta ordtyper och får automatiskt lägre belagd andel. Här dras i stället lika stora ordprov
(utan återläggning) ur varje text, många gånger, och andelen belagda ordTYPER mäts per prov.
Resultat → edda_runbelagg_kontroll.json.
"""
import json
import random
import re
import statistics
import sys

sys.path.insert(0, "/Volumes/2TB/Antigrvity/Runes/aagaard-research")
from src import runlm as rl

BUDGET = 600   # löpord per prov; texter under budgeten redovisas men flaggas
ITER = 300

texter = json.load(open("/Volumes/2TB/Antigrvity/Runes/aagaard-research/utdata/Malt/kallor/edda.json"))
runkeys = set()
for r in rl.load_rundata():
    if rl.viking(r):
        for w in rl.norm_words(r.get("normalization") or ""):
            runkeys.add(rl.key(rl.normtok(w)))

tok = lambda t: re.findall(r"[a-zþðæöøáéíóúýœå]+", t.lower())  # noqa: E731
rng = random.Random(1)
rader = []
for namn, text in texter.items():
    ord_ = [rl.key(w) for w in tok(text)]
    if len(ord_) < 150:
        continue
    kort = len(ord_) < BUDGET
    andelar = []
    for _ in range(ITER if not kort else 1):
        prov = ord_ if kort else rng.sample(ord_, BUDGET)
        typer = set(prov)
        andelar.append(sum(1 for t in typer if t in runkeys) / len(typer))
    rader.append({"dikt": namn, "löpord": len(ord_), "kort": kort,
                  "andel": round(statistics.mean(andelar), 3),
                  "sd": round(statistics.stdev(andelar), 4) if len(andelar) > 1 else None})
rader.sort(key=lambda r: -r["andel"])
json.dump({"budget": BUDGET, "iterationer": ITER, "texter": rader},
          open("/Volumes/2TB/Antigrvity/Runes/aagaard-research/utdata/Edda/edda_runbelagg_kontroll.json", "w"),
          ensure_ascii=False, indent=1)
for r in rader:
    print(f"{r['andel']:.3f}±{r['sd'] or 0:.3f} {'KORT ' if r['kort'] else ''}{r['dikt']} ({r['löpord']})")
