"""Maltstenens obegripliga runföljder mot den fornnordiska litteraturen (Viktor 2026-10-30): för varje följd som
modellen läser under 50 % kalibrerad sannolikhet, eller som ett ord den själv byggt (§), söks ord i Eddan, Heimskringla,
fornaldarsagorna, samtidssagorna och islänningasagorna (nutida isländsk stavning, märkt) som kan skrivas så med runor.
Jämförelsen sker på en runnyckel: modellens samma-ord-nyckel (runlm.key) plus runornas sammanfall (k=g, t=d, b=p,
u=v=o=ø, i=e, þ=ð, R=r). Exakt nyckel = samma ord i runstavning; avstånd 1 = en runa skiljer. Dessutom alla tudelningar
där båda delarna är ord. Ingen tolkning läggs till; bara träffar med källa och antal. Skriver liknande_ord.json.
    PYTHONPATH=. .venv/bin/python utdata/Malt/liknande_ord.py"""
import glob
import json
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, ".")
from src import runlm as rl  # noqa: E402

OUT = "utdata/Malt"
SOURCES = {"edda": None, "heimskringla": "utdata/varlden/korpus/heimskringla", "fornaldarsagor": "utdata/varlden/korpus/fornaldarsogur",
           "samtidssagor": "utdata/varlden/korpus/samtidssagor", "islänningasagor (nutida stavning)": "utdata/varlden/korpus/islendingasogur"}
TOK = re.compile(r"[a-záéíóúýæøœǫöåäðþʀ]+", re.I)


def rkey(s):
    k = rl.key(s.lower())
    for a, b in (("g", "k"), ("d", "t"), ("b", "p"), ("v", "u"), ("o", "u"), ("e", "i"), ("R", "r"), ("ą", "u"), ("c", "k"), ("x", "ks")):
        k = k.replace(a, b)
    return re.sub(r"(.)\1+", r"\1", k)


def lev1(a, b):
    """True when a and b differ by one edit (same length ±1)."""
    if abs(len(a) - len(b)) > 1:
        return False
    if len(a) == len(b):
        return sum(x != y for x, y in zip(a, b)) == 1
    s, t = (a, b) if len(a) < len(b) else (b, a)
    i = 0
    while i < len(s) and s[i] == t[i]:
        i += 1
    return s[i:] == t[i + 1:]


# ---- the literature, by rune key -------------------------------------------------------------------------------------
words = defaultdict(lambda: defaultdict(Counter))  # rkey -> source -> Counter(word form)
for src, path in SOURCES.items():
    if src == "edda":
        toks = rl.edda_tokens()
    else:
        toks = []
        for f in glob.glob(os.path.join(path, "*.txt")):
            toks += TOK.findall(open(f, encoding="utf-8").read().lower())
    for w in toks:
        if len(w) >= 2:
            words[rkey(w)][src][w] += 1
by_len = defaultdict(list)
for k in words:
    by_len[len(k)].append(k)


def hits(seq, max_dist):
    k = rkey(seq)
    out = []
    for kk in (by_len[len(k)] + by_len[len(k) - 1] + by_len[len(k) + 1] if max_dist else [k]):
        if kk == k or (max_dist and lev1(k, kk)):
            for src, c in words[kk].items():
                for w, n in c.most_common(3):
                    out.append({"word": w, "n": n, "source": src, "distance": 0 if kk == k else 1})
    return sorted(out, key=lambda h: (h["distance"], -h["n"]))


# ---- the Malt stone's sequences the model does not read well ------------------------------------------------------
D = json.load(open(os.path.join(OUT, "malt_avkodning.json"), encoding="utf-8"))
groups = [x for x in D["reading"]]
targets = [x for x in groups if (x.get("pc") or 0) < 0.5 or str(x.get("word") or "").startswith("§") or not x.get("word")]
res = []
for x in targets:
    seq = x["runes"]
    item = {"runes": seq, "model_word": x.get("word"), "model_p": round(x.get("pc") or 0, 2),
            "whole": hits(seq, max_dist=len(seq) >= 5)[:12], "splits": []}
    for i in range(2, len(seq) - 1):
        a, b = seq[:i], seq[i:]
        ha, hb = hits(a, 0), hits(b, 0)
        if ha and hb:
            item["splits"].append({"a": a, "b": b, "a_words": ha[:3], "b_words": hb[:3]})
    res.append(item)
json.dump({"targets": res, "sources": list(SOURCES), "n_keys": len(words)}, open(os.path.join(OUT, "liknande_ord.json"), "w"),
          ensure_ascii=False, indent=1)
for it in res:
    print(f"\n### {it['runes']}  (modellen: {it['model_word']} {it['model_p']})")
    print("  hela:", [(h['word'], h['n'], h['source'][:5], h['distance']) for h in it['whole'][:8]] or "–")
    for s in it["splits"][:6]:
        print(f"  {s['a']}|{s['b']}:", [(h['word'], h['n'], h['source'][:5]) for h in s['a_words'][:2]], "+",
              [(h['word'], h['n'], h['source'][:5]) for h in s['b_words'][:2]])
