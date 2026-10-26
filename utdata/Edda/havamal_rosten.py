"""Hávamáls röst: vad som sägs, vem som talar och hur, mot kristen och hednisk dikt i samma versmått.

Jämförelsetexter (edda_karta_texter.csv, samma tokenisering som stilkartan; alla i ljóðaháttr):
  Hávamál (hela, fyra delar) och del I (gästvisdomen, det rådgivande kärnstycket)
  kristna: Hugsvinnsmál (kristen bearbetning av Disticha Catonis, 1200-talet) + Sólarljóð (kristen visionsdikt)
  hedniska dialogdikter: Vafþrúðnismál, Grímnismál, Skírnismál, Lokasenna, Alvíssmál, Sigrdrífumál, Fjölsvinnsmál
Mått med fasta ordlistor (synliga nedan, inte handplockade efter resultatet): kristet ordförråd, gåva/gäld, vänner,
'bättre' (betra), 'om' (ef) och jag-formen (ek). Varje mått prövas med Fishers exakta test mot Hugsvinnsmál och mot de
hedniska dialogerna. Två mått kontrolleras mot sina egna artefakter: Loddfáfnismáls refräng (innehåller två 'ef' per strof)
och trollsångernas formel 'kann ek'. Måtten som inte överlever redovisas som kasserade. Skriver havamal_rosten.json.
    .venv/bin/python utdata/Edda/havamal_rosten.py
"""
import os
_PROJ = str(__import__("pathlib").Path(__file__).resolve().parents[2])  # projektmappen, var den än ligger
import csv
import json
import re
from collections import Counter

from scipy.stats import fisher_exact

ROT = os.path.join(_PROJ, "utdata/Edda")
d = {r["namn"]: r["text"].split() for r in csv.DictReader(open(f"{ROT}/edda_karta_texter.csv"))}
DELAR = ("Hávamál_gnomisk", "Hávamál_kvinnoråd_Gunnlöd", "Hávamál_Loddfáfnismál", "Hávamál_Runatal_Ljóðatal")
HAV = sum((d[k] for k in DELAR), [])
DEL_I = d["Hávamál_gnomisk"]
HUG, SOL = d["Hugsvinnsmál"], d["Sólarljóð"]
HED = sum((d[k] for k in ("Vafþrúðnismál", "Grímnismál", "Skírnismál", "Lokasenna", "Alvíssmál", "Sigrdrífumál",
                          "Fjölsvinnsmál")), [])

# Kristet ordförråd: Gud, synd, själ, änglar, nåd, helvete, djävul, frälsning (utan himinn/heilagt, som även är hedniska,
# och utan bæn, som i Hávamál strof 36 betyder 'tiggeri', inte 'bön')
KRIST = r"^(guð|guði|guðs|drottinn|drottin|drottni|drottins|kristr|krist|synd\w*|sál\w*|englar|engla|helvíti|djöful\w*|miskunn\w*|náð\w*|sálubót)$"
GAVA = r"^(gjöf|gjafar|gjöfum|gjöld|gjalda|gaf|gefa|gefit|gefr|gildi|endrgefendr|viðrgefendr)$"
VAN = r"^(vinr|vin|vini|vina|vinum|vinir|vinar)$"
BETRA = r"^(betra|betri|bazt|bezt)$"
EF, EK = r"^ef$", r"^ek$"

n = lambda w, rx: sum(1 for t in w if re.match(rx, t))  # noqa: E731


def jamfor(a, b, rx):
    x, y = n(a, rx), n(b, rx)
    _, p = fisher_exact([[x, len(a) - x], [y, len(b) - y]])
    return {"a": x, "n_a": len(a), "per100_a": round(100 * x / len(a), 2),
            "b": y, "n_b": len(b), "per100_b": round(100 * y / len(b), 2), "p": float(f"{p:.3g}")}


def tre(a, rx):
    """a mot Hugsvinnsmål och mot de hedniska dialogerna."""
    return {"mot_hugsvinnsmal": jamfor(a, HUG, rx), "mot_hedniska": jamfor(a, HED, rx)}


ut = {"ord": {"Hávamál": len(HAV), "Hávamál_del_I": len(DEL_I), "Hugsvinnsmál": len(HUG), "Sólarljóð": len(SOL),
              "hedniska_dialoger": len(HED)}}
GRUPPER = {"Hávamál": HAV, "Hugsvinnsmál": HUG, "Sólarljóð": SOL, "hedniska_dialoger": HED}

# 1. kristet ordförråd
ut["kristet"] = {g: {"traffar": n(w, KRIST), "per100": round(100 * n(w, KRIST) / len(w), 2)} for g, w in GRUPPER.items()}

# 2. gåva/gäld och vänner: delas av Hávamál och Hugsvinnsmál, men inte av de hedniska dialogerna
ut["gava"] = tre(HAV, GAVA)
ut["van"] = tre(HAV, VAN)

# 3. 'bättre' (betra): hela dikten och gästvisdomen
ut["betra"] = {"hela": tre(HAV, BETRA), "del_I": tre(DEL_I, BETRA)}

# 4. 'om' (ef): refrängen först bort - KASSERAT om skillnaden försvinner
REF1 = "njóta mundu ef þú nemr þér munu góð ef þú getr".split()
REF2 = "ráðumk þér loddfáfnir en þú ráð nemir".split()


def utan(w, ref):
    out, i, k = [], 0, 0
    while i < len(w):
        if w[i:i + len(ref)] == ref:
            i += len(ref); k += 1
        else:
            out.append(w[i]); i += 1
    return out, k


w1, k1 = utan(HAV, REF1)
w2, k2 = utan(w1, REF2)
ut["ef"] = {"hela": tre(HAV, EF), "utan_refrang": tre(w2, EF), "refranger": [k1, k2],
            "kasserat": "skillnaden mot Hugsvinnsmål försvinner när Loddfáfnismáls refräng tas bort"}

# 5. jaget: hela dikten, gästvisdomen, och vad jaget gör (vittnar eller bedömer)
t_hug = open(f"{ROT}/kallor/hugsvinnsmal_norront.txt", encoding="utf-8").read()
ut["ek"] = {"hela": tre(HAV, EK), "del_I": tre(DEL_I, EK),
            "kann_ek": sum(1 for i in range(len(HAV) - 1) if HAV[i] == "kann" and HAV[i + 1] == "ek"),
            "hugsvinnsmal_bedomer": len(re.findall(r"\b(?:hygg|tel) ek\b", t_hug)),
            "hugsvinnsmal_undervisar": len(re.findall(r"\b(?:hefi ek|kenda ek|ek hefi)\b", t_hug)),
            "del_I_vittnar_strofer": [13, 14, 39, 47, 49, 52, 66, 67, 70, 78]}

# 6. skall (bud): ingen skillnad - redovisas som negativt resultat
SKALL = r"^(skal|skalt|skaltu|skulu|skyli|skyldi|skulum|skuli)$"
ut["skall"] = {"hela": tre(HAV, SKALL)}

json.dump(ut, open(f"{ROT}/havamal_rosten.json", "w"), ensure_ascii=False, indent=1)
print("ord:", ut["ord"])
print("kristet:", {g: (v["traffar"], v["per100"]) for g, v in ut["kristet"].items()})
for namn in ("gava", "van"):
    for mot, v in ut[namn].items():
        print(f"{namn} {mot}: {v['a']}/{v['n_a']} ({v['per100_a']}) vs {v['b']}/{v['n_b']} ({v['per100_b']}) p={v['p']}")
for nyckel in ("hela", "del_I"):
    for mot, v in ut["betra"][nyckel].items():
        print(f"betra {nyckel} {mot}: {v['a']}/{v['n_a']} ({v['per100_a']}) vs {v['b']}/{v['n_b']} ({v['per100_b']}) p={v['p']}")
for nyckel in ("hela", "utan_refrang"):
    for mot, v in ut["ef"][nyckel].items():
        print(f"ef {nyckel} {mot}: {v['a']}/{v['n_a']} ({v['per100_a']}) vs {v['b']}/{v['n_b']} ({v['per100_b']}) p={v['p']}")
for nyckel in ("hela", "del_I"):
    for mot, v in ut["ek"][nyckel].items():
        print(f"ek {nyckel} {mot}: {v['a']}/{v['n_a']} ({v['per100_a']}) vs {v['b']}/{v['n_b']} ({v['per100_b']}) p={v['p']}")
print("kann ek:", ut["ek"]["kann_ek"], "| Hugsvinnsmål bedömer/undervisar:", ut["ek"]["hugsvinnsmal_bedomer"], ut["ek"]["hugsvinnsmal_undervisar"])
v = ut["skall"]["hela"]["mot_hugsvinnsmal"]
print(f"skall hela mot Hugsvinnsmål: {v['per100_a']} vs {v['per100_b']} p={v['p']}")
