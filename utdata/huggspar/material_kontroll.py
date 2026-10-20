"""Huggteknikens träffsäkerhet med bergarten under kontroll.

Syntesen (src/synthesis.py) väger in huggtekniken med (träff − slump)/(1 − slump), där slumpen är 1/antal ristare i den
lämna-en-ute-korsvalidering appen gör (src/stats.py evaluate_loo). Ristare och bergart hänger ihop – en ristare högg ofta i
traktens sten – så träffsäkerheten kan komma från materialet. Här räknas samma korsvalidering på de 36 skanningarna ur
Kitzler Åhfeldts Södermanlandsserie (groove-5, utdata/Rak/out_g5/stone_means.csv), med två materialkontroller:
  1. en nollfördelning där ristarnamnen slumpas om INOM bergartsfamilj (bevarar sambandet ristare–material),
  2. en "materialgissare": förutsäger den vanligaste ristaren inom stenens bergartsfamilj (lämna-en-ute).
Två referensurval: appens regel (exakt en säker ristare, S eller A) och Rak-planens ristarlista (delade signaturer tillåtna).
    .venv/bin/python utdata/huggspar/material_kontroll.py
"""
import csv
import json
import os
import sys
from collections import Counter

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
from src.stats import METRICS, evaluate_loo  # noqa: E402

rng = np.random.default_rng(20261020)
rows = list(csv.DictReader(open(os.path.join(ROOT, "utdata/Rak/out_g5/stone_means.csv"))))
meta = {r["signum"]: r for r in json.load(open(os.path.join(ROOT, "utdata/huggspar/ka_stenar_rundata.json")))}
X = {r["signum"]: [float(r[m]) for m in METRICS] for r in rows}
family = {s: ("sandsten" if m["material_ka"] == "sandstone" else "granit/gnejs") for s, m in meta.items()}

# Rak-planens lista (utdata/Rak/rak_analysis.R): ristare med minst två stenar i serien, delade signaturer som en grupp
RAK_CARVER = {"Sö 45": "Traen", "Sö 112": "Traen", "Sö 129": "Traen", "Sö 164": "Traen", "Sö 143": "Tore 1", "Sö 149": "Tore 1",
              "Sö 206": "Äsbjörn", "Sö 208": "Äsbjörn", "Sö 211": "Äskil 1", "Sö 333": "Äskil 1",
              "Sö 160": "Gunnlev 2 & Sigmund", "Sö 162": "Gunnlev 2 & Sigmund"}
APP_CARVER = {s: m["certain"][0] for s, m in meta.items() if len(m["certain"]) == 1}
APP_CARVER = {s: c for s, c in APP_CARVER.items() if Counter(APP_CARVER.values())[c] >= 2}


def groups_of(labels):
    g = {}
    for s, c in labels.items():
        g.setdefault(c, []).append(X[s])
    return g


def loo_acc(labels):
    return evaluate_loo(groups_of(labels))["top1_accuracy"]


def material_guesser(labels):
    """Lämna-en-ute: gissa den vanligaste ristaren bland de övriga stenarna i samma bergartsfamilj."""
    hits = 0
    for s, c in labels.items():
        others = Counter(labels[t] for t in labels if t != s and family[t] == family[s])
        if not others:
            others = Counter(labels[t] for t in labels if t != s)
        hits += others.most_common(1)[0][0] == c
    return hits / len(labels)


def within_material_null(labels, B=2000):
    """Ristarnamnen slumpas om inom bergartsfamilj; hur ofta når slumpen den observerade träffsäkerheten?"""
    obs = loo_acc(labels)
    fams = {}
    for s in labels:
        fams.setdefault(family[s], []).append(s)
    null = []
    for _ in range(B):
        perm = {}
        for f, ss in fams.items():
            cs = [labels[s] for s in ss]
            rng.shuffle(cs)
            perm.update(dict(zip(ss, cs)))
        if min(Counter(perm.values()).values()) < 2:
            continue
        null.append(loo_acc(perm))
    null = np.array(null)
    return obs, float(null.mean()), float((np.sum(null >= obs - 1e-12) + 1) / (len(null) + 1)), len(null)


def plain_null(labels, B=2000):
    """Samma utan hänsyn till material (alla etiketter slumpas fritt)."""
    obs = loo_acc(labels)
    ss = list(labels)
    null = []
    for _ in range(B):
        cs = [labels[s] for s in ss]
        rng.shuffle(cs)
        null.append(loo_acc(dict(zip(ss, cs))))
    null = np.array(null)
    return float(null.mean()), float((np.sum(null >= obs - 1e-12) + 1) / (len(null) + 1))


def report(name, labels):
    k = len(set(labels.values()))
    obs, null_mat, p_mat, nb = within_material_null(labels)
    null_free, p_free = plain_null(labels)
    mg = material_guesser(labels)
    chance = 1 / k
    rel_app = max(0.0, (obs - chance) / (1 - chance))
    rel_mat = max(0.0, (obs - mg) / (1 - mg)) if mg < 1 else 0.0
    fam_by_carver = {c: Counter(family[s] for s in labels if labels[s] == c) for c in set(labels.values())}
    out = {"urval": name, "n_stenar": len(labels), "n_ristare": k, "ristare": {c: dict(v) for c, v in fam_by_carver.items()},
           "traff_loo": round(obs, 3), "slump_app": round(chance, 3), "tillforlitlighet_app": round(rel_app, 3),
           "materialgissare": round(mg, 3), "tillforlitlighet_mot_material": round(rel_mat, 3),
           "null_fri_medel": round(null_free, 3), "p_fri": round(p_free, 4),
           "null_inom_material_medel": round(null_mat, 3), "p_inom_material": round(p_mat, 4), "n_null_inom": nb}
    print(f"\n{name}: {len(labels)} stenar, {k} ristare")
    for c, v in fam_by_carver.items():
        print(f"  {c}: {dict(v)}")
    print(f"  träff (lämna-en-ute) {obs:.2f} | appens slump 1/{k} = {chance:.2f} → tillförlitlighet {rel_app:.2f}")
    print(f"  materialgissaren {mg:.2f} → tillförlitlighet mot material {rel_mat:.2f}")
    print(f"  slumpade etiketter: fritt {null_free:.2f} (p={p_free:.3f}); inom material {null_mat:.2f} (p={p_mat:.3f}, {nb} dragningar)")
    return out


res = {"metrics": METRICS, "app_regel": report("appens regel (exakt en säker ristare)", APP_CARVER),
       "rak_lista": report("Rak-planens lista (delade signaturer som grupp)", RAK_CARVER)}
granite = {s: c for s, c in RAK_CARVER.items() if family[s] != "sandsten"}
granite = {s: c for s, c in granite.items() if Counter(granite.values())[c] >= 2}
res["rak_lista_bara_granit"] = report("Rak-planens lista, bara granit/gnejs", granite)
json.dump(res, open(os.path.join(ROOT, "utdata/huggspar/material_kontroll.json"), "w"), ensure_ascii=False, indent=1)
