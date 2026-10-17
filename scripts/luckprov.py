"""Blindprov och öppna luckor enligt den låsta analysplanen analysplaner/2026-10-16-luckor-blindprov.md.

Varje sten läses av appens modell för stenen (textmodel.bundle: den av fem modeller som inte är tränad på stenen) med
panelens inställningar (textmodel.FILL), utan spår. Luckorna och Rundatas svar tas från scripts/runlm_gaps.gaps_of;
förlorade runor nära varandra fylls tillsammans och varje lucka får ordet där den står.

    .venv/bin/python -m scripts.luckprov [--out utdata/luckartikel]

Skriver del1.json (skannade stenar, återställda luckor) och del2.json (öppna luckor) med urvalet enligt planen.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from collections import Counter, defaultdict

import scripts.runlm_gaps as G
from src import runlm as rl
from src import scan_sources
from src import textmodel as tm

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def formula_words() -> set[str]:
    """The 50 most common words (by key) in the normalizations of SW: everything else is a content word."""
    freq = Counter(rl.key(rl.normtok(b)) for r in G.SW for _, p in rl.sections(r["normalization"]) for b in rl.norm_words(p))
    return {k for k, _ in freq.most_common(50)}


def interpreted(r):
    """Does Rundata read the inscription as language: at least two words that are neither '...' nor futhark?
    (as in scripts/runlm_gaps_report.py)."""
    n = re.sub(r"<[^>]*>", " ", r.get("normalization") or "")
    return sum(1 for _, p in rl.sections(n) for w in rl.norm_words(p) if not w.startswith("...")) >= 2


def status_of(tok):
    return "återställt" if tok and "[" in tok else "ej återställt" if (tok is None or tok == "...") else "oklart"


def read_stone(r, items, own_d=False):
    """Fill the stone's gaps (items: [(groups, gap, carved word, Rundata token)]) with the app's model; one row per gap.
    own_d: the carver's own divider rate (rl.stone_divider_rate over all the stone's sections) instead of the corpus rate."""
    b = tm.bundle(tm.fold_of(r["signum"]))
    m = b["model"]
    site = (float(r["lat"]), float(r["lon"])) if r.get("lat") is not None and r.get("lon") is not None else None
    rows = []
    by_groups = defaultdict(list)
    for x in items:
        by_groups[tuple(x[0])].append(x)
    dr = None
    if own_d:
        allg, ends = [], []
        for key in by_groups:
            allg.extend(key)
            ends.append(len(allg) - 1)
        dr = rl.stone_divider_rate(m, allg, ends)
    for groups, ys in by_groups.items():
        runs = [y[1] for y in ys]
        work, spans, cons, member = rl.merge_runs(list(groups), runs)
        # as in the panel (and the plan): a gap of more than four lost runes, also after merging, is left open
        n_lost = {sp: sum(1 for i in range(sp[1], sp[2]) if groups[sp[0]][i] == "?") for sp in spans}
        spans = [sp for sp in spans if n_lost[sp] <= tm.MAX_GAP]
        cons = {sp: c for sp, c in cons.items() if sp in spans}
        hard = {sp: [i for i, c in enumerate(cons[sp]) if c is not None] for sp in cons}
        if not spans:
            continue
        pos = {}
        combos, gaps, marg = rl.restore_all(m, work, only=spans, allowed=cons, hard=hard, positions=pos, site=site,
                                            div_rate=dr, **tm.FILL)
        if not combos:
            continue
        best = dict(zip(gaps, combos[0][0]))
        for _, gap, w, tok in ys:
            sp = member.get(gap)
            if sp not in best:
                continue
            n = gaps.index(sp)
            words = pos[n][gap[1] - sp[1]] if pos.get(n) else marg.get(n, {})
            word = max(words, key=words.get) if words else None
            fill = best[sp][gap[1] - sp[1]:gap[2] - sp[1]]
            restored = rl.normtok(tok.replace("[", "").replace("]", "")) if status_of(tok) == "återställt" else None
            agrees = None
            if restored:
                agrees = bool(word and word != "<unk>" and (m.lemma(word) == m.lemma(restored) or rl.same_word(word, restored)))
            rows.append({"sig": r["signum"], "interpreted": interpreted(r), "carved": w, "lost": gap[2] - gap[1], "fill": fill, "word": word,
                         "gap": list(gap), "group": groups[gap[0]],
                         "p": round(words.get(word, 0.0), 4) if word else 0.0,
                         "alts": [(ww, round(pp, 3)) for ww, pp in list(words.items())[:5]],
                         "rundata": tok, "status": status_of(tok), "agrees": agrees,
                         "reading": combos[0][2], "p_reading": round(combos[0][1], 4), "div_rate": dr})
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=os.path.join(ROOT, "utdata", "luckartikel"))
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    TOP = formula_words()
    content = lambda w: bool(w) and w != "<unk>" and rl.key(rl.normtok(w)) not in TOP  # noqa: E731
    scanned = {sg for ds in scan_sources.DATASETS for sg in ds["signa"]}
    by_stone = defaultdict(list)
    for r in G.SW:
        for groups, gap, w, tok in G.gaps_of(r):
            if status_of(tok) != "oklart":
                by_stone[r["signum"]].append((groups, gap, w, tok))
    rec = {r["signum"]: r for r in G.SW}

    # Part 1: the scanned stones with restored gaps
    p1 = sorted(sg for sg, xs in by_stone.items() if sg in scanned and any(status_of(x[3]) == "återställt" for x in xs))
    rows1 = []
    for sg in p1:
        xs = [x for x in by_stone[sg] if status_of(x[3]) == "återställt"]
        rows1 += read_stone(rec[sg], xs)
        print("del 1:", sg, flush=True)
    for x in rows1:
        x["content"] = content(rl.normtok(x["rundata"].replace("[", "").replace("]", "")))
    per = defaultdict(lambda: [0, 0])
    for x in rows1:
        if x["content"]:
            per[x["sig"]][0] += x["lost"]; per[x["sig"]][1] += 1
    chosen1 = sorted(per, key=lambda s: (-per[s][0], -per[s][1], s))[0] if per else None
    s1 = {"n": len(rows1), "same_word": sum(bool(x["agrees"]) for x in rows1),
          "content_n": sum(x["content"] for x in rows1), "content_same": sum(bool(x["agrees"]) for x in rows1 if x["content"]),
          "chosen": chosen1, "rows": rows1}
    json.dump(s1, open(os.path.join(a.out, "del1.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"DEL 1: {s1['same_word']} av {s1['n']} luckor samma ord som Rundata; innehållsord {s1['content_same']} av "
          f"{s1['content_n']}; vald sten: {chosen1}", flush=True)

    # Part 2: the open gaps
    p2 = sorted(sg for sg, xs in by_stone.items() if any(status_of(x[3]) == "ej återställt" for x in xs))
    rows2 = []
    for i, sg in enumerate(p2):
        xs = [x for x in by_stone[sg] if status_of(x[3]) == "ej återställt"]
        rows2 += read_stone(rec[sg], xs)
        if i % 10 == 0:
            print(f"del 2: {i + 1} av {len(p2)}", flush=True)
    for x in rows2:
        x["candidate"] = bool(content(x["word"]) and x["p"] >= 0.90)
    per2 = defaultdict(lambda: [0, 0, []])
    for x in rows2:
        if x["candidate"]:
            per2[x["sig"]][0] += x["lost"]; per2[x["sig"]][1] += 1; per2[x["sig"]][2].append(x["p"])
    rank = lambda per: sorted(per, key=lambda s: (-per[s][0], -per[s][1], -sum(per[s][2]) / len(per[s][2]), s))  # noqa: E731
    chosen2 = rank(per2)[0] if per2 else None
    # deviation from the plan, reported as such: inscriptions Rundata does not read as language left out (as in the
    # gap report), since a filling there has nothing to be measured against
    per3 = {s_: v for s_, v in per2.items() if rec[s_] and interpreted(rec[s_])}
    chosen3 = rank(per3)[0] if per3 else None
    s2 = {"n": len(rows2), "stones": len(p2), "candidates": sum(x["candidate"] for x in rows2), "chosen": chosen2,
          "chosen_interpreted_only": chosen3, "ranking": [(s_, per2[s_][0], per2[s_][1]) for s_ in rank(per2)[:10]],
          "rows": rows2}
    json.dump(s2, open(os.path.join(a.out, "del2.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"DEL 2: {s2['n']} öppna luckor på {s2['stones']} stenar; kandidater {s2['candidates']}; vald sten: {chosen2}; "
          f"bara tolkade inskrifter: {chosen3}", flush=True)


if __name__ == "__main__":
    main()
