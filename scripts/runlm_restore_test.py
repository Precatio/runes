"""Kan runavkodaren (src/runlm.py) fylla i förlorade runor? Maskeringsprov: på provstenar där Rundatas ord täcker
den huggna texten döljs runor som vi känner – dels 1–4 runor inne i ett ord, dels ett helt ord – och modellen fyller
i dem utan att ha tränats på stenen (femfaldigt, samma stenar och delning som scripts/runlm_calibrate.py).
Mäter hur ofta den första fyllnaden är rätt, om rätt fyllnad finns bland de tre första, och om modellens
sannolikhet för sin första fyllnad stämmer med hur ofta den är rätt. Skriver utdata/Malt/runlm_ifyllning.json.
    .venv/bin/python -m scripts.runlm_restore_test [--folds 0 1 2 3 4]"""
import argparse
import json
import os
import random
import re
import sys
import time
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.runlm import (by_object, print_by_object, Model, carved_groups, context, decode, edda_tokens, is_runes, key, load_rundata, norm_words,  # noqa: E402
                       normtok, restore, runekey, sections, translit_words, viking)

ap = argparse.ArgumentParser()
ap.add_argument("--folds", type=int, nargs="*", default=None)
ap.add_argument("--lam_name", type=float, default=0.05)
ap.add_argument("--lam_class", type=float, default=0.0, help="vikt för ordföljd efter ordklass (0 = av)")
ap.add_argument("--lam_doc", type=float, default=0.0, help="vikt för vilka ord som står i samma inskrift (0 = av)")
ap.add_argument("--window", type=int, default=2, help="grupper på var sida om luckan; -1 = hela texten")
ap.add_argument("--char_fills", type=int, default=0, help="fyllnader föreslagna runa för runa (vokal/konsonant)")
ap.add_argument("--context_cands", action="store_true", help="kandidatord vägs efter orden före och efter luckan")
ap.add_argument("--name_cands", type=int, default=0, help="namn ur namnled som passar de bevarade runorna")
ap.add_argument("--adapt", type=float, default=0.0, help="stenens egen stavning ur resten av texten (styrka)")
ap.add_argument("--n_cands", type=int, default=60)
ap.add_argument("--trigram", action="store_true", help="kandidaterna bedöms också efter följder om tre ord")
ap.add_argument("--cache", type=float, default=0.0, help="ord som redan står på stenen (vikt)")
ap.add_argument("--area_lm", action="store_true", help="ordföljd efter trakt (formler per landskap)")
ap.add_argument("--by_word", action="store_true", help="välj ordet (summerat över stavningar), sedan stavningen")
ap.add_argument("--near", type=float, default=0.0, help="namn från stenar i närheten (vikt)")
ap.add_argument("--near_km", type=float, default=20.0)
ap.add_argument("--trace", default="none", choices=["none", "halv", "tredjedel", "blandad"],
                help="vad som syns av de dolda runorna (data/rune_traces.json): halva runan, en tredjedel, eller blandat "
                     "(för varje runa lika ofta inget, en tredjedel eller hälften)")
ap.add_argument("--trace_noise", type=float, default=0.0,
                help="andelen spår som är feltolkade: spåret kommer då från en annan runa än den rätta")
ap.add_argument("--trace_eps", type=float, default=0.0, help="mjuka spår: en runa som strider mot spåret kostar så här mycket")
ap.add_argument("--contexts", action="store_true", help="stavning per epok, trakt, landskap och ristare (steg 3)")
ap.add_argument("--ctx", default="none", choices=["none", "region", "carver"],
                help="stenens plats i stavningsträdet: ingen, till och med landskapet, eller ända till ristaren")
ap.add_argument("--carver_names", type=float, default=0.0, help="namn från ristarens andra stenar (vikt)")
ap.add_argument("--only_carver", action="store_true", help="bara stenar med känd ristare (samma luckor som annars)")
ap.add_argument("--hard", action="store_true", help="bara ord som inte är bland de 50 vanligaste (formelord)")
ap.add_argument("--out", default=None)
args = ap.parse_args()

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MALT = "DR NOR1988;5"
V = [r for r in load_rundata() if viking(r) and r.get("transliteration") and r.get("normalization") and r["signum"] != MALT]
ET = edda_tokens()


def gold(r):
    T = sections(r["transliteration"]); N = dict(sections(r["normalization"]))
    if any(lab not in N for lab, _ in T):
        return None
    ws = []
    for lab, t in T:
        a, b = translit_words(t), norm_words(N[lab])
        if len(a) != len(b):
            return None
        ws.extend((runekey(x), normtok(y)) for x, y in zip(a, b))
    if not ws or not all(is_runes(x.lower()) for x, _ in ws):
        return None
    groups = [runekey(g) for g in carved_groups(r["transliteration"])]
    if "".join(groups) != "".join(x for x, _ in ws):
        return None
    out, pos = [], 0
    for x, y in ws:
        out.append((pos, pos + len(x), x, y)); pos += len(x)
    return groups, out


cands = [(r, gold(r)) for r in V]
# --hard: only words that are not among the 50 most common (formula words), the kind of gap the editors leave open
FORMULA = set()
if args.hard:
    _fq = Counter(key(normtok(b)) for r in V for _, p in sections(r["normalization"]) for b in norm_words(p))
    FORMULA = {k for k, _ in _fq.most_common(50)}
cands = [(r, g) for r, g in cands if g and len(g[1]) >= 4]
random.Random(2026).shuffle(cands)
K = 5
folds = args.folds if args.folds is not None else list(range(K))
rng = random.Random(15)
trace_rng = random.Random(16)  # its own generator, so that the same runes are hidden with and without traces
TRACES = json.load(open(os.path.join(ROOT, "data", "rune_traces.json")))["allowed"]
HALVES = ["övre halvan", "nedre halvan", "vänster om staven", "höger om staven"]
THIRDS = ["övre tredjedelen", "mellersta tredjedelen", "nedre tredjedelen"]


def trace(runes):
    """For each hidden rune the runes that its simulated visible remains allow (None: nothing visible)."""
    out = []
    for ch in runes:
        mode = args.trace if args.trace != "blandad" else trace_rng.choice(["inget", "tredjedel", "halv"])
        region = (trace_rng.choice(HALVES) if mode == "halv" else trace_rng.choice(THIRDS) if mode == "tredjedel"
                  else None)
        if region and ch in TRACES and args.trace_noise and trace_rng.random() < args.trace_noise:
            ch = trace_rng.choice([c for c in "fuþorkhniastbmlR" if c != ch])  # a misread trace: another rune's remains
        out.append(TRACES[ch][region] if (region and ch in TRACES) else None)
    return out


def locate(groups, start, end):
    """(group index, first, last + 1) of a stretch of the text, or None if it crosses a divider."""
    pos = 0
    for gi, g in enumerate(groups):
        if pos <= start and end <= pos + len(g):
            return gi, start - pos, end - pos
        pos += len(g)
    return None


rows = []
t0 = time.time()
for k in folds:
    test = cands[k::K]
    tset = {r["signum"] for r, _ in test}
    m = Model([r for r in V if r["signum"] not in tset], edda_tokens=ET, aligned=True, lam_name=args.lam_name, lam_class=args.lam_class,
              lam_doc=args.lam_doc, area_lm=args.area_lm,
              **(dict(contexts=True, alpha=100.0, kappa_e=50.0, lm_beta=200.0) if args.contexts else {}))
    for r, (groups, gw) in test:
        for kind in ("inne i ord", "helt ord"):
            if kind == "inne i ord":
                words = [w for w in gw if w[1] - w[0] >= 3 and not (args.hard and key(normtok(w[3])) in FORMULA)]
                if not words:
                    continue
                i, j, runes, gword = rng.choice(words)
                n = rng.randint(1, min(4, j - i - 1))
                a = i + rng.randint(0, j - i - n)
                span = (a, a + n)
            else:
                words = [w for w in gw if 2 <= w[1] - w[0] <= 6 and not (args.hard and key(normtok(w[3])) in FORMULA)]
                if not words:
                    continue
                i, j, runes, gword = rng.choice(words)
                span = (i, j)
            loc = locate(groups, *span)
            if loc is None:
                continue
            gi, g0, g1 = loc
            truth = groups[gi][g0:g1]
            masked = list(groups)
            masked[gi] = groups[gi][:g0] + "?" * (g1 - g0) + groups[gi][g1:]
            allowed = trace(truth) if args.trace != "none" else None
            cpath = context(r)
            carver = cpath[5]
            if args.only_carver and not carver:  # the same gaps are drawn either way; only stones with a carver are filled
                continue
            ctx = m.ctx(cpath if args.ctx == "carver" else cpath[:5]) if (args.contexts and args.ctx != "none") else None
            wd = {}
            res = restore(m, masked, (gi, g0, g1), words=wd, window=None if args.window < 0 else args.window,
                          use_doc=args.lam_doc > 0, char_fills=args.char_fills, context_cands=args.context_cands,
                          name_cands=args.name_cands, adapt=args.adapt, n_cands=args.n_cands, trigram=args.trigram,
                          cache=args.cache, area=context(r)[3] if args.area_lm else None, by_word=args.by_word,
                          site=(float(r["lat"]), float(r["lon"])) if (args.near and r.get("lat") is not None) else None,
                          near_km=args.near_km, lam_near=args.near, allowed=allowed, ctx=ctx,
                          carver=carver, lam_carver=args.carver_names, trace_eps=args.trace_eps)
            fills = [f for f, _ in res]
            p = dict(res)
            # the word read at the gap with the best filling: is it the right word, whatever its spelling?
            word_ok, w_ = False, None
            if fills:
                filled = list(groups)
                filled[gi] = groups[gi][:g0] + fills[0] + groups[gi][g1:]
                _, path, _, _ = decode(m, filled)
                at = sum(len(x) for x in groups[:gi]) + g0
                w_ = next((w for a_, b_, w, _ in path if a_ <= at < b_), None)
                word_ok = bool(w_) and w_ != "<unk>" and m.lemma(w_) == m.lemma(normtok(gword))
            rows.append({"sig": r["signum"], "kind": kind, "n": g1 - g0, "truth": truth, "top": fills[0] if fills else None,
                         "p_top": res[0][1] if res else 0.0, "rank": fills.index(truth) + 1 if truth in fills else None,
                         "p_truth": p.get(truth, 0.0), "word_ok": word_ok, "gold_word": normtok(gword),
                         "dist": [(f, round(q, 6)) for f, q in res[:10]], "word": w_,
                         "is_name": normtok(gword) in {normtok(x) for x in re.findall(r'"(\w+)', r.get("normalization") or "")},
                         "allowed": allowed, "carver": carver,
                         "carver_kind": next((c["kind"] for c in (r.get("carvers") or [])
                                              if isinstance(c, dict) and c.get("name") == carver), None),
                         "p_word": (sum(q for f, q in res if wd.get(f) and wd.get(fills[0]) and
                                        m.lemma(wd[f]) == m.lemma(wd[fills[0]])) if fills else 0.0)})
    print(f"del {k + 1} klar efter {time.time() - t0:.0f} s; {len(rows)} luckor", flush=True)

out = {"n": len(rows)}
for kind in ("inne i ord", "helt ord"):
    xs = [x for x in rows if x["kind"] == kind]
    by_n = {}
    for n in sorted({x["n"] for x in xs}):
        ys = [x for x in xs if x["n"] == n]
        by_n[n] = {"n": len(ys), "top1": sum(x["rank"] == 1 for x in ys) / len(ys),
                   "top3": sum(1 for x in ys if x["rank"] and x["rank"] <= 3) / len(ys)}
    rel = []
    for lo, hi in ((0, 0.5), (0.5, 0.8), (0.8, 0.95), (0.95, 1.01)):
        ys = [x for x in xs if lo <= x["p_top"] < hi]
        rel.append({"lo": lo, "hi": min(hi, 1), "n": len(ys), "p": sum(x["p_top"] for x in ys) / max(1, len(ys)),
                    "acc": sum(x["rank"] == 1 for x in ys) / max(1, len(ys))})
    out[kind] = {"n": len(xs), "word": sum(x["word_ok"] for x in xs) / max(1, len(xs)),
                 "top1": sum(x["rank"] == 1 for x in xs) / max(1, len(xs)),
                 "top3": sum(1 for x in xs if x["rank"] and x["rank"] <= 3) / max(1, len(xs)),
                 "missing": sum(1 for x in xs if x["rank"] is None) / max(1, len(xs)), "by_n": by_n, "reliability": rel}
    print(f"[{kind}] {len(xs)} luckor: rätt ord {out[kind]['word']:.1%}; rätt runor {out[kind]['top1']:.1%}, bland tre första {out[kind]['top3']:.1%}, "
          f"rätt fyllnad saknas bland kandidaterna {out[kind]['missing']:.1%}")
    print("   efter antal runor:", {n: f"{v['top1']:.0%}/{v['top3']:.0%} (n={v['n']})" for n, v in by_n.items()})
    print("   säkerhet → träff:", [(f"{c['p']:.2f}", f"{c['acc']:.2f}", c["n"]) for c in rel])
    relw = []
    for lo, hi in ((0, 0.5), (0.5, 0.8), (0.8, 0.95), (0.95, 1.01)):
        ys = [x for x in xs if lo <= x.get("p_word", 0) < hi]
        relw.append({"lo": lo, "hi": min(hi, 1), "n": len(ys), "p": sum(x["p_word"] for x in ys) / max(1, len(ys)),
                     "acc": sum(x["word_ok"] for x in ys) / max(1, len(ys))})
    out[kind]["reliability_word"] = relw
    out[kind]["by_object"] = by_object(xs, lambda x: x["sig"], {
        "word": lambda ys: sum(y["word_ok"] for y in ys) / len(ys), "top1": lambda ys: sum(y["rank"] == 1 for y in ys) / len(ys)}, recs=V)
    print_by_object(f"   [{kind}]", out[kind]["by_object"])
    print("   ordets säkerhet → rätt ord:", [(f"{c['p']:.2f}", f"{c['acc']:.2f}", c["n"]) for c in relw])
out["rows"] = rows
json.dump(out, open(args.out or os.path.join(ROOT, "utdata", "Malt", "runlm_ifyllning.json"), "w"), ensure_ascii=False, indent=1)
