"""Poängsättning av Maltstenens originalläsningar (R, G, H) ur tolkningar_ord.json.

Tre mått per läsning, inga omdömen: (1) täckning - hur stor del av de huggna grupperna läsningen
ger språkliga ord; (2) beläggsprofil - hur många av orden som är belagda i den vikingatida
runkorpusen (med frekvens), bara i norrön litteratur (eddatexterna), eller obelagda; (3) run-trohet
- ljudklasslikheten mellan den huggna runföljden och läsningens ord (runlm.similarity), där
emendationer och reduktionsläsningar syns som avstånd. Lågt belägg betyder "vilar på ovanligare
språk", inte "fel" - det sägs i artikeln. Andrahandsläsningarna (T/B/S/F) poängsätts aldrig.
Skriver tolkningar_poang.json.
    .venv/bin/python utdata/Malt/poangsatt_tolkningar.py
"""
import json
import math
import re
import statistics
import sys
import unicodedata
from collections import Counter

ROT = "/Volumes/2TB/Antigrvity/Runes/aagaard-research"
sys.path.insert(0, ROT)
from src import runlm as rl  # noqa: E402

MALT = "DR NOR1988;5"
d = json.load(open(f"{ROT}/utdata/Malt/tolkningar_ord.json"))

recs = rl.load_rundata()
V = [r for r in recs if rl.viking(r) and r.get("normalization") and r["signum"] != MALT]
frek = Counter()
for r in V:
    for w in rl.norm_words(r["normalization"]):
        frek[rl.key(rl.normtok(w))] += 1
N_korpus = sum(frek.values())
edda_nycklar = {rl.key(rl.normtok(w)) for w in rl.edda_tokens()}

def stada_ord(s):
    """Utgåvornas normaliserade form → modellens nyckelrymd (längdstreck, ogonek m.m. bort)."""
    s = s.lower().replace("ǫ", "ö").replace("ǿ", "æ").replace("œ", "æ")
    ut = []
    for ch in unicodedata.normalize("NFD", s):
        if unicodedata.category(ch) == "Mn":
            continue
        if ch.isalpha() or ch in "þðæöø":
            ut.append(ch)
    return "".join(ut)

def ordlista(ordfalt):
    """Läsningens ordfält → lista av enskilda ord (alternativ a/b blir en post med båda)."""
    if not ordfalt or ordfalt.startswith("<") or ordfalt.startswith("("):
        return []
    s = re.sub(r"\([^)]*\)", "", ordfalt).strip()  # parentesglosor (eptir, början …) är inte egna ordanspråk
    if "/" in s:  # alternativa läsningar av samma grupp (gull / kuml)
        return [tuple(x.strip() for x in s.split("/"))]
    return [(w,) for w in s.replace("-", "").split() if w]

resultat = {}
for nyckel in ("R", "G", "H"):
    post = d["lasningar"][nyckel]
    rader, sim_rader = [], []
    tackta = sprak_grupper = 0
    for o in post["ord"]:
        grupp = o["runor"]
        if grupp == "fuþorkhniastbmlR":
            continue  # runraden läses lika av alla
        sprak_grupper += 1
        ordf = o.get("ord")
        alternativ = ordlista(ordf or "")
        if not alternativ:
            if ordf and ordf.startswith("("):
                tackta += 1  # gruppen ingår i föregående ord (t.ex. dweragi)
            continue
        tackta += 1
        for alt in alternativ:
            kandidater = []
            for w in alt:
                k = rl.key(rl.normtok(stada_ord(w)))
                f = frek.get(k, 0)
                status = "runbelagd" if f else ("edda" if k in edda_nycklar else "obelagd")
                kandidater.append({"ord": w, "nyckel": k, "status": status, "frekvens": f})
            bast = max(kandidater, key=lambda x: (x["status"] == "runbelagd", x["frekvens"],
                                                  x["status"] == "edda"))
            bast = dict(bast, grupp=grupp, alternativ=len(kandidater) > 1)
            rader.append(bast)
        if grupp not in ("?",):
            huggen = re.sub(r"[()\[\]]", "", grupp)
            anspråk = stada_ord("".join(w for alt in alternativ for w in alt[:1]))
            sim_rader.append({"grupp": grupp, "anspråk": anspråk,
                              "likhet": round(rl.similarity(huggen, anspråk), 3)})
    status_n = Counter(r["status"] for r in rader)
    log_f = [math.log10(r["frekvens"] / N_korpus) for r in rader if r["frekvens"]]
    resultat[nyckel] = {
        "kalla": post["kalla"],
        "tackning": {"grupper_med_ord": tackta, "av": sprak_grupper, "andel": round(tackta / sprak_grupper, 3)},
        "belagg": {"ord_poangsatta": len(rader), **{k: status_n.get(k, 0) for k in ("runbelagd", "edda", "obelagd")},
                   "andel_runbelagd": round(status_n.get("runbelagd", 0) / max(len(rader), 1), 3),
                   "medel_log10_frekvens": round(statistics.mean(log_f), 2) if log_f else None},
        "run_trohet": {"medel": round(statistics.mean(x["likhet"] for x in sim_rader), 3),
                       "varsta": sorted(sim_rader, key=lambda x: x["likhet"])[:4]},
        "ord": rader,
    }
    b = resultat[nyckel]
    print(f"{nyckel}: täckning {b['tackning']['grupper_med_ord']}/{b['tackning']['av']}"
          f" | runbelagda {b['belagg']['runbelagd']}/{b['belagg']['ord_poangsatta']}"
          f" (edda {b['belagg']['edda']}, obelagda {b['belagg']['obelagd']})"
          f" | medellogfrekvens {b['belagg']['medel_log10_frekvens']}"
          f" | run-trohet {b['run_trohet']['medel']}")
    print("   längst från runorna:", [(x['grupp'], x['anspråk'], x['likhet']) for x in b['run_trohet']['varsta']])

json.dump({"om": __doc__.strip().split("\n")[0], "korpus_ord": N_korpus, "lasningar": resultat},
          open(f"{ROT}/utdata/Malt/tolkningar_poang.json", "w"), ensure_ascii=False, indent=1)
