"""Från runor till översättningsutkast: hur nära Rundatas översättning kommer modellen? Femfaldigt prov på de 808
provstenarna (samma som scripts/runlm_calibrate.py): ordlistan (src/rungloss.py) och läsmodellen (src/runlm.py)
tränas på fyra delar, och den femte översätts dels från Rundatas normalisering (ordlistans kvalitet), dels hela vägen
från de huggna runorna (läsning + ordlista). Jämförelsen gäller de betydelsebärande engelska orden: hur stor del av
modellens ord som finns i Rundatas översättning (precision) och hur stor del av översättningens ord modellen får med
(täckning). Skriver utdata/Malt/runlm_oversattning.json.
    .venv/bin/python -m scripts.runlm_gloss_test [--folds 0 1 2 3 4]"""
import argparse
import json
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.runlm import Model, carved_groups, decode, edda_tokens, is_runes, load_rundata, norm_words, normtok, runekey, sections, translit_words, viking  # noqa: E402
from src.rungloss import STOP, Glossary, _english  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--folds", type=int, nargs="*", default=None)
ap.add_argument("--lam_name", type=float, default=0.05)
args = ap.parse_args()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MALT = "DR NOR1988;5"
V = [r for r in load_rundata() if viking(r) and r.get("transliteration") and r.get("normalization") and r["signum"] != MALT]
ET = edda_tokens()


def gold_ok(r):
    T = sections(r["transliteration"]); N = dict(sections(r["normalization"]))
    if any(lab not in N for lab, _ in T):
        return False
    ws = []
    for lab, t in T:
        a, b = translit_words(t), norm_words(N[lab])
        if len(a) != len(b):
            return False
        ws.extend(runekey(x) for x in a)
    return bool(ws) and all(is_runes(x.lower()) for x in ws) and len(ws) >= 4 and \
        "".join(runekey(g) for g in carved_groups(r["transliteration"])) == "".join(ws)


cands = [r for r in V if gold_ok(r)]
random.Random(2026).shuffle(cands)
K = 5
folds = args.folds if args.folds is not None else list(range(K))


def content(words):
    return [w for w in words if w not in STOP and w != "…" and len(w) > 1]


def score(hyp, ref):
    h, r_ = content(hyp.lower().split()), set(content(ref))
    hit = sum(1 for w in h if w in r_)
    return hit, len(h), len({w for w in h if w in r_}), len(r_)


rows = []
t0 = time.time()
for k in folds:
    test = cands[k::K]
    tset = {r["signum"] for r in test}
    train = [r for r in V if r["signum"] not in tset]
    gl = Glossary([r for r in train if r.get("translation_en")])
    m = Model(train, edda_tokens=ET, aligned=True, lam_name=args.lam_name)
    for r in test:
        ref = _english(" ".join(p for _, p in sections(r.get("translation_en"))))
        if not ref:
            continue
        gold_words = [normtok(w) for _, p in sections(r["normalization"]) for w in norm_words(p)]
        hyp_gold = gl.translate(gold_words)
        groups = [runekey(g) for g in carved_groups(r["transliteration"])]
        _, path, _, _ = decode(m, groups)
        hyp_runes = gl.translate([w for _, _, w, _ in path])
        rows.append({"sig": r["signum"], "ref": " ".join(ref), "from_norm": hyp_gold, "from_runes": hyp_runes,
                     "s_norm": score(hyp_gold, ref), "s_runes": score(hyp_runes, ref),
                     "sv": gl.translate([w for _, _, w, _ in path], "sv")})
    print(f"del {k + 1} klar efter {time.time() - t0:.0f} s; {len(rows)} inskrifter", flush=True)

out = {"n": len(rows)}
for name in ("norm", "runes"):
    hit = sum(x[f"s_{name}"][0] for x in rows); n_h = sum(x[f"s_{name}"][1] for x in rows)
    cov = sum(x[f"s_{name}"][2] for x in rows); n_r = sum(x[f"s_{name}"][3] for x in rows)
    prec, rec = hit / max(1, n_h), cov / max(1, n_r)
    out[name] = {"precision": prec, "recall": rec, "f1": 2 * prec * rec / max(1e-9, prec + rec)}
    print(f"från {'normaliseringen' if name == 'norm' else 'runorna'}: precision {prec:.1%}, täckning {rec:.1%}, F1 {out[name]['f1']:.1%}")
for x in rows[:12]:
    print(f"  {x['sig']:10} | runor → {x['from_runes'][:90]}\n  {'':10} | Rundata: {x['ref'][:90]}\n  {'':10} | svenska: {x['sv'][:90]}")
out["rows"] = rows
json.dump(out, open(os.path.join(ROOT, "utdata", "Malt", "runlm_oversattning.json"), "w"), ensure_ascii=False, indent=1)
