"""Förlorade runor på svenska runstenar: vad fyller sannolikhetsmodellen (src/runlm.py) i, och stämmer det med
Rundata där Rundata har återställt ordet (ofta efter äldre teckningar från tiden innan stenen skadades)?

Varje lucka om 1–4 förlorade runor (Rundatas '-') i ett ord vars övriga runor är bevarade fylls i av modellen.
Ordet i Rundatas normalisering som motsvarar det skadade ordet avgör vad luckan blir:
  * återställt (hakparentes, t.ex. st[æi]n): ett prov – kommer modellen fram till samma ord?
  * inte återställt ('...' eller inget ord): en kandidat – här kan modellen föreslå något nytt.
Stenen som fylls i är aldrig med i modellens träning (femfaldigt över stenarna), eftersom Rundatas normalisering
annars läcker in återställningen. Skriver utdata/Malt/runlm_luckor.json.
    .venv/bin/python -m scripts.runlm_gaps [--max_gaps 1500] [--lam_doc 0.1] [--window -1]"""
import argparse
import json
import os
import random
import re
import sys
import time
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.runlm import (DIV, Model, by_object, print_by_object, clean_translit, context, edda_tokens, is_runes, load_rundata, merge_runs,  # noqa: E402
                       normtok, restore_all, runekey, sections, similarity, viking)


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SWEDISH = set("U Sö Ög Vg Sm Öl G Nä Vs Gs Hs M J Ån Lp D Vr Bo Ds".split())
ALL = load_rundata()
V = [r for r in ALL if viking(r) and r.get("transliteration") and r.get("normalization") and r["signum"] != "DR NOR1988;5"]
SW = [r for r in V if re.match(r"\S+", r["signum"]).group(0) in SWEDISH]
ET = edda_tokens()


def raw_norm_tokens(s):
    """Rundata's normalized words with their brackets kept ('...' marks text that is not restored)."""
    s = re.sub(r"(\S+)/\S+", r"\1", s).replace('"', "").replace("(?)", "")
    return [w for w in re.split(r"[\s,.;:!?]+(?![^\[]*\])", s) if w] + []


def norm_tokens_with_gaps(s):
    s = re.sub(r"(\S+)/\S+", r"\1", s).replace('"', "").replace("(?)", "")
    out = []
    for w in re.split(r"\s+", s):
        w2 = w.strip(",;:!?.")
        if w.startswith("..."):
            out.append("...")
            # a word with its beginning lost ("...f[a]str): the rest is still the word the carved runes belong to
            rest = w2.lstrip(".")
            if rest and re.search(r"[^\W\d_]", rest):
                out.append("…" + rest)  # marked: only the runes inside its brackets are restored (gaps_of)
        elif w2:
            out.append(w2)
    return out


def match_damaged(a_words, b_tokens):
    """Line up carved words (some with lost runes '-') with normalized words; returns {carved index: token or None}."""
    n, m = len(a_words), len(b_tokens)
    NEG = float("-inf")
    best = [[NEG] * (m + 1) for _ in range(n + 1)]
    back = [[None] * (m + 1) for _ in range(n + 1)]
    best[0][0] = 0.0
    for i in range(n + 1):
        for j in range(m + 1):
            v = best[i][j]
            if v == NEG:
                continue
            if i < n and j < m:
                a = a_words[i].replace("-", "")
                b = b_tokens[j].replace("[", "").replace("]", "").replace("…", "")
                sc = (0.3 if b == "..." and a.strip(".") == "" else  # lost text on both sides
                      -0.1 if b == "..." and "-" in a_words[i] else
                      -0.5 if b == "..." else similarity(a, b) - 0.45 if a else -0.2)
                if v + sc > best[i + 1][j + 1]:
                    best[i + 1][j + 1] = v + sc; back[i + 1][j + 1] = (i, j, "m")
            if i + 1 < n and j < m and b_tokens[j] != "...":
                # two carved groups that are one normalized word (austr·uih- = austrveg[i], U 366)
                a2 = (a_words[i] + a_words[i + 1]).replace("-", "")
                b2 = b_tokens[j].replace("[", "").replace("]", "").replace("…", "")
                sc2 = similarity(a2, b2) - 0.45 - 0.3
                if v + sc2 > best[i + 2][j + 1]:
                    best[i + 2][j + 1] = v + sc2; back[i + 2][j + 1] = (i, j, "m2")
            if i < n and v - 0.3 > best[i + 1][j]:
                best[i + 1][j] = v - 0.3; back[i + 1][j] = (i, j, "a")
            if j < m and v - 0.3 > best[i][j + 1]:
                best[i][j + 1] = v - 0.3; back[i][j + 1] = (i, j, "b")
    out, i, j = {}, n, m
    while (i, j) != (0, 0) and back[i][j]:
        pi, pj, kind = back[i][j]
        if kind == "m":
            out[pi] = b_tokens[pj]
        elif kind == "m2":
            out[pi] = out[pi + 1] = b_tokens[pj]
        i, j = pi, pj
    return out


def gaps_of(r):
    """[(groups with '?' for lost runes, gap (group, start, end), the damaged carved word, Rundata's token)]."""
    out = []
    T = sections(r["transliteration"]); N = dict(sections(r["normalization"]))
    for lab, t in T:
        if lab not in N:
            continue
        tt = clean_translit(t)
        words = [w for w in re.split(rf"\s+|{DIV}", tt) if w]
        toks = norm_tokens_with_gaps(N[lab])
        link = match_damaged(words, toks)
        # the carved groups of this section, '-' as '?', other unread signs as group breaks
        groups = []
        for g in re.split(DIV, tt):
            g = runekey(re.sub(r"\s+", "", g)).replace("-", "?")
            groups.extend(p for p in re.split(r"[^a-zþðæøåöäąR?]+", g) if p)
        flat = "".join(groups)
        pos = 0
        for wi, w in enumerate(words):
            wk = runekey(w).replace("-", "?")
            at = flat.find(wk, pos)
            if at < 0:
                continue
            pos = at + len(wk)
            tok = link.get(wi)
            restored_runs = None
            if tok and tok.startswith("…"):
                # a word with its beginning lost ("...bi[o]rn): only the last runs of lost runes, as many runes as the
                # brackets hold, are restored; the earlier ones belong to the lost beginning (U 508)
                n_br = sum(len(x) for x in re.findall(r"\[([^\]]*)\]", tok))
                restored_runs, cum = set(), 0
                for mm in reversed(list(re.finditer(r"\?+", wk))):
                    if cum + (mm.end() - mm.start()) > n_br:
                        break
                    restored_runs.add(mm.start())
                    cum += mm.end() - mm.start()
            for mm in re.finditer(r"\?+", wk):
                k = mm.end() - mm.start()
                rest = wk.replace("?", "")
                if not (1 <= k <= 4) or len(rest) < 2 or not is_runes(rest.lower()) or "." in w:
                    continue
                s0 = at + mm.start()
                g_pos = 0
                for gi, g in enumerate(groups):
                    if g_pos <= s0 and s0 + k <= g_pos + len(g):
                        t = tok if restored_runs is None else (tok[1:] if mm.start() in restored_runs else "...")
                        out.append((groups, (gi, s0 - g_pos, s0 - g_pos + k), w, t))
                        break
                    g_pos += len(g)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--max_gaps", type=int, default=1500)
    ap.add_argument("--lam_name", type=float, default=0.05)
    ap.add_argument("--lam_class", type=float, default=0.0, help="vikt för ordföljd efter ordklass (0 = av)")
    ap.add_argument("--lam_doc", type=float, default=0.0)
    ap.add_argument("--window", type=int, default=-1)
    ap.add_argument("--char_fills", type=int, default=15)
    ap.add_argument("--context_cands", action="store_true")
    ap.add_argument("--n_cands", type=int, default=100)
    ap.add_argument("--area_lm", action="store_true")
    ap.add_argument("--by_word", action="store_true")
    ap.add_argument("--near", type=float, default=0.0)
    ap.add_argument("--near_km", type=float, default=20.0)
    ap.add_argument("--fold", type=int, default=-1, help="bara denna del (0–4), för att köra delarna parallellt")
    ap.add_argument("--separate", action="store_true", help="fyll varje följd av förlorade runor för sig (som före 2026-10-16)")
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)
    items = []
    for r in SW:
        for groups, gap, w, tok in gaps_of(r):
            status = "återställt" if tok and "[" in tok else "ej återställt" if (tok is None or tok == "...") else "oklart"
            if status != "oklart":
                items.append((r, groups, gap, w, tok, status))
    random.Random(2026).shuffle(items)
    items = items[:args.max_gaps]
    print("luckor:", len(items), Counter(x[5] for x in items), flush=True)

    stones = sorted({x[0]["signum"] for x in items})
    fold = {st: i % 5 for i, st in enumerate(stones)}
    by_stone = {}
    for x in items:
        by_stone.setdefault(x[0]["signum"], []).append(x)
    rows = []
    t0 = time.time()
    for k in range(5):
        if args.fold >= 0 and k != args.fold:
            continue
        test = {st for st in stones if fold[st] == k}
        m = Model([r for r in V if r["signum"] not in test], edda_tokens=ET, aligned=True, lam_name=args.lam_name, lam_class=args.lam_class,
                  lam_doc=args.lam_doc, area_lm=args.area_lm)
        for st in sorted(test):
            xs = by_stone[st]
            r = xs[0][0]
            # the stone's gaps of the same text section are filled together; each section is a text of its own
            by_groups = {}
            for x in xs:
                by_groups.setdefault(tuple(x[1]), []).append(x)
            for groups, ys in by_groups.items():
                runs = [y[2] for y in ys]
                if args.separate:
                    work, spans, cons, member = list(groups), runs, {}, {r: r for r in runs}
                else:  # runs close together in one word are filled as one (merge_runs)
                    work, spans, cons, member = merge_runs(list(groups), runs)
                pos = {}
                combos, gaps, marg = restore_all(
                    m, work, only=spans, allowed=cons, positions=pos, window=None if args.window < 0 else args.window,
                    use_doc=args.lam_doc > 0, char_fills=args.char_fills, context_cands=args.context_cands,
                    n_cands=args.n_cands, by_word=args.by_word, area=context(r)[3] if args.area_lm else None,
                    site=(float(r["lat"]), float(r["lon"])) if (args.near and r.get("lat") is not None) else None,
                    near_km=args.near_km, lam_near=args.near)
                if not combos:
                    continue
                best = dict(zip(gaps, combos[0][0]))
                for _, _, gap, w, tok, status in ys:
                    sp = member.get(gap)
                    if sp not in best:
                        continue
                    n = gaps.index(sp)
                    # the word where this run stands: a gap of two runs filled as one can cover two words
                    words = pos[n][gap[1] - sp[1]] if pos.get(n) else marg.get(n, {})
                    word = max(words, key=words.get) if words else None
                    restored = normtok(tok.replace("[", "").replace("]", "")) if status == "återställt" else None
                    gi, g0, g1 = gap
                    fill = best[sp][g0 - sp[1]:g1 - sp[1]]
                    filled = list(groups)
                    filled[gi] = filled[gi][:sp[1]] + best[sp] + filled[gi][sp[2]:]
                    rows.append({"sig": st, "carved": w, "gap": g1 - g0, "fill": fill, "p": words.get(word, 0.0), "span": list(sp),
                                 "alts": [(ww, round(pp, 3)) for ww, pp in list(words.items())[1:4]], "word": word,
                                 "rundata": tok, "status": status, "reading": combos[0][2], "p_reading": combos[0][1],
                                 "agrees": (m.lemma(word) == m.lemma(restored)) if (restored and word and word != "<unk>") else
                                           (False if restored else None),
                                 "context": " ".join(filled[max(0, gi - 2):gi + 3])})
        print(f"del {k + 1} klar efter {time.time() - t0:.0f} s; {len(rows)} luckor", flush=True)

    val = [x for x in rows if x["status"] == "återställt"]
    print(f"återställda av Rundata: {len(val)}; modellen kommer fram till samma ord i {sum(bool(x['agrees']) for x in val) / max(1, len(val)):.1%}")
    for lo, hi in ((0, 0.5), (0.5, 0.8), (0.8, 0.95), (0.95, 1.01)):
        ys = [x for x in val if lo <= x["p"] < hi]
        print(f"   säkerhet {lo:.2f}–{min(hi, 1):.2f}: n={len(ys)}, samma ord som Rundata {sum(bool(x['agrees']) for x in ys) / max(1, len(ys)):.0%}")
    by_obj = by_object(val, lambda x: x["sig"], {"same": lambda ys: sum(bool(y["agrees"]) for y in ys) / len(ys),
                                                  "sure_right": lambda ys: sum(bool(y["agrees"]) for y in ys if y["p"] >= 0.95) / max(1, sum(y["p"] >= 0.95 for y in ys))},
                       recs=V)
    print_by_object("återställda luckor", by_obj)
    new = sorted([x for x in rows if x["status"] == "ej återställt"], key=lambda x: -x["p"])
    print(f"luckor som Rundata inte återställer: {len(new)}; med modellens säkerhet ≥ 0,9: {sum(x['p'] >= 0.9 for x in new)}")
    for x in new[:25]:
        print(f"  {x['sig']:12} {x['carved']:16} → {x['fill']:5} ord: {x['word']} ({x['p']:.2f}) | {x['context']}")
    json.dump({"settings": vars(args), "by_object": by_obj, "rows": rows}, open(args.out or os.path.join(ROOT, "utdata", "Malt", "runlm_luckor.json"), "w"),
              ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
