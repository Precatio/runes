"""Tillägg utöver planen (beskrivande, deklarerat i resultat.md): beror Södermanlands höga enhetlighet på ordmixen?
A per land och ord, och A med samma ordvikter i alla land (varje ords andel av alla par i de sex landen). Läser
stenar.json och resultat.json (via prov.py:s funktioner), skriver kontroll.json.
    .venv/bin/python utdata/gemensam_stavning/kontroll.py"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.argv = [sys.argv[0]]
src = open(os.path.join(HERE, "prov.py"), encoding="utf-8").read()
src = src[:src.index("obs_v, A, T = h1_stat(land)")]  # only the data and the agreement function
exec(compile(src, "prov.py", "exec"))

L = len(lands)
per_word = []
for wi, (idx, code) in enumerate(WORDS):
    keep = WORDS[wi]
    WORDS_save = WORDS[:]
    WORDS[:] = [keep]
    s, t = agreement(land, nby=L)
    WORDS[:] = WORDS_save
    per_word.append((D["common_words"][wi], s, t))
tot_pairs = np.array([t.sum() for _, _, t in per_word])
W = tot_pairs / tot_pairs.sum()
std = {}
for li, k in enumerate(lands):
    num = den = 0.0
    for (w, s, t), wt in zip(per_word, W):
        if t[li] >= 3:
            num += wt * s[li] / t[li]
            den += wt
    std[k] = num / den
rows = []
for w, s, t in per_word:
    if t.sum() < 30:
        continue
    rows.append({"word": w, "pairs": float(t.sum()),
                 **{k: (round(float(s[i] / t[i]), 3) if t[i] >= 3 else None) for i, k in enumerate(lands)}})
rows.sort(key=lambda r: -r["pairs"])
# the spellings of the most frequent words, per land
spell = {}
for w in [r["word"] for r in rows[:8]]:
    spell[w] = {}
    for k in lands:
        from collections import Counter
        cnt = Counter(ST[i]["words"][w] for i in range(N) if land[i] == land_ix[k] and w in ST[i]["words"])
        spell[w][k] = cnt.most_common(4)
out = {"standardised_A": std, "per_word": rows[:25], "spellings_top_words": spell}
json.dump(out, open(os.path.join(HERE, "kontroll.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("A med samma ordvikter:", {k: round(v, 3) for k, v in std.items()})
for r in rows[:12]:
    print(f"{r['word']:12} par {r['pairs']:7.0f}  " + "  ".join(f"{k[:5]} {r[k]}" for k in lands))
for w, d in list(spell.items())[:5]:
    print(w, {k: v[:3] for k, v in d.items()})

# Tillägg 2: monoftongeringen räknas inte som stavningsskillnad (au = u, ai = i), annars samma mått
for wi, (idx, code) in enumerate(WORDS):
    w = D["common_words"][wi]
    sp = [ST[i]["words"][w].replace("au", "u").replace("ai", "i") for i in idx]
    codes = {x: k for k, x in enumerate(sorted(set(sp)))}
    WORDS[wi] = (idx, np.array([codes[x] for x in sp]))
s, t = agreement(land, nby=L)
coll = {k: float(s[i] / t[i]) for i, k in enumerate(lands)}
out["A_without_monophthongisation"] = coll
json.dump(out, open(os.path.join(HERE, "kontroll.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("A utan monoftongeringen (au = u, ai = i):", {k: round(v, 3) for k, v in coll.items()})
