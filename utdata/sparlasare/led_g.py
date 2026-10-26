"""Spårläsaren, led G (2026-10-17): verkliga luckor, hela vägen. På de skannade stenar som har riktiga luckor
(Sö 162, Sö 206, Sö 211, Sö 360, Sö 45) paras de upptäckta runorna mot texten – där en förlorad runa (?) matchar
varje mängd gratis, så att en skadad men upptäckt runa kan hamna på sin plats – och luckorna fylls med appens egen
kedja (textmodel-17, modellen tränad utan stenens fald, panelens inställningar) i två villkor: utan spår och med
spårläsarens mängd på de luckpositioner som fick en upptäckt runa. Facit är utgivarnas återställning i Rundata.
Obs: parningen behövs bara i provbänken; i panelen pekar användaren ut luckan på stenen.
    PYTHONPATH=. .venv/bin/python utdata/sparlasare/led_g.py [signum ...]"""
import json
import math
import os
import sys
from collections import defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import src.runlm as rl  # noqa: E402
import src.textmodel as tm  # noqa: E402
import led_e  # noqa: E402
from led_a import BASE, FUT, rows_of  # noqa: E402
from led_f import expand  # noqa: E402
from scripts.runlm_gaps import gaps_of  # noqa: E402

STONES = ("Sö 162", "Sö 206", "Sö 211", "Sö 360", "Sö 45")


def gap_align(sets, seq):
    """DP as led F's align_pos, but a lost rune (?) matches every set for free – otherwise detected runes are pushed
    away from exactly the positions we care about."""
    n, m = len(sets), len(seq)
    INF = 1e9
    D = np.full((n + 1, m + 1), INF)
    D[0, :] = np.arange(m + 1) * 0.4
    D[:, 0] = np.arange(n + 1) * 0.7
    back = {}
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            c = seq[j - 1][1]
            sub = D[i - 1, j - 1] + (0.0 if (c == "?" or c in sets[i - 1]) else 1.0)
            dele = D[i - 1, j] + 0.7
            ins = D[i, j - 1] + 0.4
            D[i, j] = min(sub, dele, ins)
            back[(i, j)] = "s" if D[i, j] == sub else ("d" if D[i, j] == dele else "i")
    pairs, i, j = [], n, m
    while i > 0 and j > 0:
        mv = back[(i, j)]
        if mv == "s":
            pairs.append((i - 1, seq[j - 1][0]))
            i, j = i - 1, j - 1
        elif mv == "d":
            i -= 1
        else:
            j -= 1
    return float(D[n, m]), pairs[::-1]


def scan_gaps(signum: str, full: str):
    """{absolute text position of a lost rune: (expanded margin set, top distribution)} for the ? positions that got a
    detected rune in the best row alignment."""
    data = led_e.load_features(signum)
    runes, feats = data["runes"], data["feats"]
    probs = {x["id"]: led_e.rune_probs(feats[x["id"]]) for x in runes}
    msets = {}
    for rid, d in probs.items():
        mx = max(d.values())
        msets[rid] = {c for c, p in d.items() if math.log(mx / p) * led_e.TAU <= 0.75}
    seq = [(i, BASE.get(c, c)) for i, c in enumerate(full) if BASE.get(c, c) in FUT or c == "?"]
    rows = rows_of(runes)
    best = None
    for td in (True, False):
        for lr in (True, False):
            order = [x for row in (rows if td else rows[::-1]) for x in (row if lr else row[::-1])]
            cost, pairs = gap_align([msets[x["id"]] for x in order], seq)
            if best is None or cost < best[0]:
                best = (cost, pairs, order)
    _, pairs, order = best
    pd = {pos: i for i, pos in pairs}
    out = {}
    for q in (i for i, c in enumerate(full) if c == "?"):
        if q in pd:
            d = probs[order[pd[q]]["id"]]
            out[q] = (expand(msets[order[pd[q]]["id"]]),
                      sorted(d.items(), key=lambda kv: -kv[1])[:5])
    return out, {"n_detected": len(runes), "n_chars": len(seq), "n_paired": len(pairs)}


def fill_stone(r, use_traces: bool, scan: dict):
    """The app's own chain (as scripts/luckprov.read_stone, textmodel-17 fold model, panel settings), with the scan's
    sets as soft traces (tm.FILL's trace_eps) at the lost positions the scan reached. One row per gap."""
    items = list(gaps_of(r))
    m = tm.bundle(tm.fold_of(r["signum"]))["model"]
    site = (float(r["lat"]), float(r["lon"])) if r.get("lat") is not None and r.get("lon") is not None else None
    GL = tm._records().get("GL")
    rows = []
    by_groups = defaultdict(list)
    for x in items:
        by_groups[tuple(x[0])].append(x)
    for groups, ys in by_groups.items():
        off = [0]
        for g in groups:
            off.append(off[-1] + len(g))
        runs = [y[1] for y in ys]
        work, spans, cons, member = rl.merge_runs(list(groups), runs)
        n_lost = {sp: sum(1 for i in range(sp[1], sp[2]) if groups[sp[0]][i] == "?") for sp in spans}
        spans = [sp for sp in spans if n_lost[sp] <= tm.MAX_GAP]
        cons = {sp: list(c) for sp, c in cons.items() if sp in spans}
        hard = {sp: [i for i, c in enumerate(cons[sp]) if c is not None] for sp in cons}
        if use_traces:  # hard is already set: the scan's sets stay soft (tm.FILL's trace_eps), only preserved runes pin
            for sp in spans:
                lst = cons.setdefault(sp, [None] * (sp[2] - sp[1]))
                for i in range(sp[1], sp[2]):
                    ap = off[sp[0]] + i
                    if lst[i - sp[1]] is None and groups[sp[0]][i] == "?" and ap in scan:
                        lst[i - sp[1]] = sorted(scan[ap][0])
        if not spans:
            continue
        pos, det = {}, {}
        combos, gaps, marg = rl.restore_all(m, work, only=spans, allowed=cons, hard=hard, positions=pos, site=site,
                                            details=det, **tm.FILL)
        if not combos:
            continue
        best = dict(zip(gaps, combos[0][0]))
        if GL:  # as the app: the word with the highest calibrated probability is the gap's choice
            for n_i, sp in enumerate(gaps):
                wd_full = marg.get(n_i) or {}
                if not wd_full or (pos.get(n_i) and len({max(p_, key=p_.get) for p_ in pos[n_i] if p_}) > 1):
                    continue
                cd = tm.calibrate_words(wd_full, n_lost[sp], GL)
                w_star = max(cd, key=cd.get)
                if w_star == max(wd_full, key=wd_full.get) or cd[w_star] <= 0:
                    continue
                lm = m.lemma(w_star)
                fits = [(p_, f_) for f_, p_, w_ in det.get(n_i, []) if w_ and w_ != "<unk>" and m.lemma(w_) == lm]
                if fits:
                    best[sp] = max(fits)[1]
        for _, gap, w, tok in ys:
            sp = member.get(gap)
            if sp not in best:
                continue
            n = gaps.index(sp)
            words = pos[n][gap[1] - sp[1]] if pos.get(n) else marg.get(n, {})
            cd = tm.calibrate_words(words, n_lost[sp], GL) if GL and words else None
            word = (max(cd, key=cd.get) if cd else max(words, key=words.get)) if words else None
            fill = best[sp][gap[1] - sp[1]:gap[2] - sp[1]]
            restored = rl.normtok(tok.replace("[", "").replace("]", ""))
            agrees = bool(word and word != "<unk>" and (m.lemma(word) == m.lemma(restored) or rl.same_word(word, restored)))
            rows.append({"sig": r["signum"], "carved": w, "rundata": tok, "lost": gap[2] - gap[1],
                         "traced": [off[gap[0]] + i in scan for i in range(gap[1], gap[2])] if use_traces else None,
                         "fill": fill, "word": word, "p": round(words.get(word, 0.0), 4) if word else 0.0,
                         "p_cal": round(cd[word], 4) if cd and word else None,
                         "alts": [(ww, round(pp, 3)) for ww, pp in list(words.items())[:5]], "agrees": agrees})
    return rows


def main(*signums):
    by = {x["signum"]: x for x in rl.load_rundata()}
    out = []
    for s in signums or STONES:
        r = by[s]
        full = "".join(list(gaps_of(r))[0][0]) if list(gaps_of(r)) else ""
        if not full:
            print(f"{s}: inga luckor")
            continue
        scan, q = scan_gaps(s, full)
        qpos = [i for i, c in enumerate(full) if c == "?"]
        print(f"{s}: {q['n_detected']} upptäckta av {q['n_chars']} tecken; {len(scan)} av {len(qpos)} förlorade "
              f"runor fick en upptäckt runa")
        for ap, (ms, top) in sorted(scan.items()):
            print(f"   pos {ap}: mängd {''.join(sorted(ms))}  topp " + " ".join(f"{c} {p:.2f}" for c, p in top))
        res = {"sig": s, "quality": q, "scan": {str(k): [sorted(v[0]), v[1]] for k, v in scan.items()}}
        for lab, use in (("utan", False), ("skanner", True)):
            if use and not scan:
                res[lab] = None
                continue
            rows = fill_stone(r, use, scan)
            res[lab] = rows
            for x in rows:
                print(f"   {lab:8} {x['carved']:10} → {x['word']} (p {x['p']:.3f}, kal {x['p_cal']}) "
                      f"{'RÄTT' if x['agrees'] else 'fel '} mot {x['rundata']}; alt {x['alts'][:3]}")
        out.append(res)
    json.dump(out, open(os.path.join(HERE, "led_g.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(*sys.argv[1:])
