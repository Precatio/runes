"""Spårläsaren, led F (2026-10-17): hjälper de skannade spåren språkmodellen att fylla luckor? Det skarpa provet.
På de tre skannade stenarna (Sö 113, Sö 134, Sö 207) maskeras varje helt ord på 2–6 runor, och modellen – tränad utan
stenen – fyller i det under tre villkor: utan spår, med spårläsarens mängder (led E:s marginalmängder för de upptäckta
runor som parats mot ordets positioner, mjuka: trace_eps), och med samma mängder slumpvis omflyttade mellan stenens
positioner (kontroll: hjälper spåren för att de läser stenen, eller bara för att mängder krymper sökrymden?).
Parningen upptäckt runa ↔ textposition görs som i led A–E men behåller textpositionen. I skarp användning pekar
panelen ut var luckan sitter, så parningen behövs bara här, för att få facit.
    cd aagaard-research && PYTHONPATH=. .venv/bin/python utdata/sparlasare/led_f.py"""
import json
import math
import os
import random
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
from src.runlm import (Model, carved_groups, decode, edda_tokens, is_runes, load_rundata, norm_words, normtok,  # noqa: E402
                       restore, runekey, sections, stone_divider_rate, translit_words, viking)
import led_e  # noqa: E402
from led_a import BASE, FUT, rows_of  # noqa: E402

TRACE_EPS = 0.2
STONES = ("Sö 113", "Sö 134", "Sö 207")
# a trace set is read in futhark space; the model fills in runekey space, so each rune lets in its dotted variants
PRE = {}
for ch in list(FUT) + list(BASE):
    PRE.setdefault(BASE.get(ch, ch), set()).add(ch)


def expand(s: set[str]) -> set[str]:
    return set().union(*(PRE.get(c, {c}) for c in s))


def gold(r):
    """As in scripts/runlm_restore_test: the carved groups and the word spans (start, end, runes, normalized word)."""
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


def locate(groups, start, end):
    pos = 0
    for gi, g in enumerate(groups):
        if pos <= start and end <= pos + len(g):
            return gi, start - pos, end - pos
        pos += len(g)
    return None


def align_pos(sets: list[set[str]], seq: list[tuple[int, str]]):
    """DP alignment as led A's align, but the text side carries its position in the model text."""
    n, m = len(sets), len(seq)
    INF = 1e9
    D = np.full((n + 1, m + 1), INF)
    D[0, :] = np.arange(m + 1) * 0.4
    D[:, 0] = np.arange(n + 1) * 0.7
    back = {}
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            sub = D[i - 1, j - 1] + (0.0 if seq[j - 1][1] in sets[i - 1] else 1.0)
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


def scan_sets(signum: str, full_text: str):
    """({position in the stone's rune text: expanded trace set from the scan}, alignment quality) via the best row
    alignment. Quality: margin-set coverage of the true pairing against 20 shuffled texts — on stones with curved
    bands the row ordering can scramble, and then the position mapping (only needed for this test) is unreliable."""
    data = led_e.load_features(signum)
    runes, feats = data["runes"], data["feats"]
    probs = {r["id"]: led_e.rune_probs(feats[r["id"]]) for r in runes}
    margin_sets = {}
    for rid, d in probs.items():
        mx = max(d.values())
        margin_sets[rid] = {c for c, p in d.items() if math.log(mx / p) * led_e.TAU <= 0.75}
    seq = [(i, BASE.get(c, c)) for i, c in enumerate(full_text) if BASE.get(c, c) in FUT]
    rows = rows_of(runes)
    best = None
    for td in (True, False):
        for lr in (True, False):
            order = [r for row in (rows if td else rows[::-1]) for r in (row if lr else row[::-1])]
            cost, pairs = align_pos([margin_sets[r["id"]] for r in order], seq)
            if best is None or cost < best[0]:
                best = (cost, pairs, order)
    _, pairs, order = best
    sets_in_order = [margin_sets[r["id"]] for r in order]
    by_pos = dict(seq)
    cov = float(np.mean([by_pos[pos] in sets_in_order[i] for i, pos in pairs])) if pairs else 0.0
    rng = random.Random(31)
    null = []
    for _ in range(20):
        letters = rng.sample([c for _, c in seq], len(seq))
        _, p2 = align_pos(sets_in_order, list(enumerate(letters)))
        null.append(float(np.mean([letters[pos] in sets_in_order[i] for i, pos in p2])) if p2 else 0.0)
    quality = {"n_detected": len(runes), "n_paired": len(pairs), "coverage": cov,
               "null": float(np.mean(null)), "null_sd": float(np.std(null))}
    return {pos: expand(margin_sets[order[i]["id"]]) for i, pos in pairs}, quality


def main(*signums):
    ET = edda_tokens()
    V = [r for r in load_rundata() if viking(r) and r.get("transliteration") and r.get("normalization")
         and r["signum"] != "DR NOR1988;5"]
    by = {r["signum"]: r for r in V}
    rng = random.Random(23)
    rows_out, stones_out = [], {}
    for signum in signums or STONES:
        r = by[signum]
        g = gold(r)
        if g is None:
            print(f"{signum}: Rundatas ord täcker inte texten – hoppar över")
            continue
        groups, gw = g
        full = "".join(groups)
        pos_sets, quality = scan_sets(signum, full)
        stones_out[signum] = quality
        shuffled_positions = list(pos_sets)
        rng.shuffle(shuffled_positions)
        shuf = {p: pos_sets[q] for p, q in zip(sorted(pos_sets), shuffled_positions)}
        m = Model([x for x in V if x["signum"] != signum], edda_tokens=ET, aligned=True, lam_name=0.05)
        dr0 = None
        words = [w for w in gw if 2 <= w[1] - w[0] <= 6]
        print(f"{signum}: {len(words)} ord på 2–6 runor; spårmängder för {len(pos_sets)} av {len(full)} positioner")
        for i, j, runes_, gword in words:
            loc = locate(groups, i, j)
            if loc is None:
                continue
            gi, g0, g1 = loc
            truth = groups[gi][g0:g1]
            masked = list(groups)
            masked[gi] = groups[gi][:g0] + "?" * (g1 - g0) + groups[gi][g1:]
            dr = stone_divider_rate(m, masked)
            conds = {"utan": (None, 0.0),
                     "skanner": ([pos_sets.get(p) for p in range(i, j)], TRACE_EPS),
                     "omflyttad": ([shuf.get(p) for p in range(i, j)], TRACE_EPS)}
            row = {"sig": signum, "truth": truth, "word": gword, "n": j - i}
            for lab, (allowed, eps) in conds.items():
                if lab != "utan" and not any(allowed):
                    row[lab] = None
                    continue
                wd = {}
                res = restore(m, masked, (gi, g0, g1), words=wd, window=2, n_cands=60, div_rate=dr,
                              allowed=allowed, trace_eps=eps)
                fills = [f for f, _ in res]
                word_ok, w_ = False, None
                if fills:
                    filled = list(groups)
                    filled[gi] = groups[gi][:g0] + fills[0] + groups[gi][g1:]
                    _, path, _, _ = decode(m, filled, d=dr)
                    at = sum(len(x) for x in groups[:gi]) + g0
                    w_ = next((w for a_, b_, w, _ in path if a_ <= at < b_), None)
                    word_ok = bool(w_) and w_ != "<unk>" and m.lemma(w_) == m.lemma(normtok(gword))
                row[lab] = {"top": fills[0] if fills else None, "right": fills[:1] == [truth],
                            "word_ok": word_ok, "p_truth": float(dict(res).get(truth, 0.0)),
                            "traced": sum(1 for a in (allowed or []) if a)}
            rows_out.append(row)
            marks = " ".join(f"{lab} {'JA' if row[lab] and row[lab]['word_ok'] else ('–' if row[lab] is None else 'nej')}"
                             for lab in conds)
            print(f"   {truth:8} ({gword}): {marks}")
    tag = "" if not signums else "_" + "_".join(s.replace(" ", "_").replace(";", "-") for s in signums)
    json.dump({"stones": stones_out, "rows": rows_out},
              open(os.path.join(HERE, f"led_f{tag}.json"), "w"), ensure_ascii=False, indent=1)
    for lab in ("utan", "skanner", "omflyttad"):
        xs = [x[lab] for x in rows_out if x.get(lab)]
        if xs:
            print(f"{lab:10} ord rätt {np.mean([x['word_ok'] for x in xs]):.2f}  fyllnad rätt "
                  f"{np.mean([x['right'] for x in xs]):.2f}  medel-P(facit) {np.mean([x['p_truth'] for x in xs]):.3f}  ({len(xs)} ord)")
    both = [x for x in rows_out if x.get("skanner") and x.get("omflyttad")]
    if both:
        print(f"bara ord med spår: utan {np.mean([x['utan']['word_ok'] for x in both]):.2f}  "
              f"skanner {np.mean([x['skanner']['word_ok'] for x in both]):.2f}  "
              f"omflyttad {np.mean([x['omflyttad']['word_ok'] for x in both]):.2f}  ({len(both)} ord)")


if __name__ == "__main__":
    main(*sys.argv[1:])
