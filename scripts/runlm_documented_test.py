"""Dokumenterade luckor: ett prov med verkligt facit på verklig skada (planens steg 2, 2026-10-17).

Runor inom hakparentes i Rundatas translitterering är förlorade på stenen men kända från äldre avbildningar. För den som
läser stenen i dag är de luckor, och svaret är dokumenterat, inte gissat av en utgivare. De har fallit bort av fysiska
skäl, inte valts ut för att de är svåra, så provet mäter modellen på skador som de verkliga. Varje sådan följd av 1–4
runor inne i ett ord (utan osäkra runor inom parentes) görs till en lucka, alla på stenen samtidigt, och stenen läses som
i appen (scripts/luckprov.read_stone: modellen för stenens del, panelens inställningar). Facit är de dokumenterade
runorna, och ordet jämförs med Rundatas normalisering. Procenten kalibreras som i panelen (textmodel.calibrate_gap).
Allt redovisas efter föremål, runstenar först.
    .venv/bin/python -m scripts.runlm_documented_test --fold 0 [--out utdata/runlm_forfining/dokumenterade_f0.json]
    .venv/bin/python -m scripts.runlm_documented_test --summary utdata/runlm_forfining/dokumenterade"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import scripts.runlm_gaps as G  # noqa: E402
from scripts.luckprov import read_stone  # noqa: E402
from src import runlm as rl  # noqa: E402
from src import textmodel as tm  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRACKET = re.compile(r"\[([^\]\[]*)\]")


def documented(translit: str) -> tuple[str, int]:
    """The transliteration with each documented run of 1–4 runes inside a word written as lost ('-'), the other
    brackets removed (their runes are read as usual); and how many runs were made lost."""
    n = 0

    def word(w):
        nonlocal n
        outside = re.sub(r"[\[\]()^?.\-]", "", BRACKET.sub("", w))

        def rep(m):
            nonlocal n
            inner = m.group(1)
            if re.fullmatch(r"[a-zþæøRåäöy]{1,4}", inner) and len(outside) >= 2:
                n += 1
                return "-" * len(inner)
            return inner
        return BRACKET.sub(rep, w)
    out = re.sub(r"[^\s:÷'·×+|¶]+", lambda m: word(m.group(0)), translit)
    return out, n


def groups_of(translit: str, lab_ok) -> list[list[str]]:
    """The carved groups of each section, as scripts.runlm_gaps.gaps_of builds them ('-' as '?')."""
    out = []
    for lab, t in rl.sections(translit):
        if not lab_ok(lab):
            continue
        gs = []
        for g in re.split(rl.DIV, rl.clean_translit(t)):
            g = rl.runekey(re.sub(r"\s+", "", g)).replace("-", "?")
            gs.extend(p for p in re.split(r"[^a-zþðæøåöäąR?]+", g) if p)
        out.append(gs)
    return out


def items_for(r):
    """[(groups, gap, carved word, Rundata token, documented runes)] for the stone's documented runs."""
    t2, n = documented(r["transliteration"])
    if not n:
        return []
    r2 = dict(r, transliteration=t2)
    full = BRACKET.sub(lambda m: m.group(1), r["transliteration"])  # the text as read before the loss
    N = dict(rl.sections(r["normalization"]))
    truth_groups = {tuple(g2): g3 for g2, g3 in zip(groups_of(t2, lambda lab: lab in N), groups_of(full, lambda lab: lab in N))}
    out = []
    for groups, gap, w, tok in G.gaps_of(r2):
        g3 = truth_groups.get(tuple(groups))
        if g3 is None or len(g3) != len(groups):
            continue
        truth = g3[gap[0]][gap[1]:gap[2]]
        if "?" in truth or not truth:  # a rune lost before any drawing: not documented
            continue
        out.append((groups, gap, w, tok, truth))
    return out


def run(fold: int, out_path: str, own_d: bool = False, name_scale: float = 1.0):
    d = tm._records()
    G_cal = d["G"]
    recs = [r for r in d["V"] if tm.fold_of(r["signum"]) == fold]
    rows = []
    for i, r in enumerate(recs):
        its = items_for(r)
        if not its:
            continue
        by_gap = {(g[gp[0]], tuple(gp)): (g, gp, w, tok, t) for g, gp, w, tok, t in its}
        for x in read_stone(r, [(g, gp, w, tok) for g, gp, w, tok, _ in its], own_d=own_d, name_scale=name_scale):
            g, gp, w, tok, t = by_gap[(x["group"], tuple(x["gap"]))]
            gold = rl.normtok(tok.replace("[", "").replace("]", "").lstrip("…")) if tok and tok != "..." else None
            word = x["word"]
            # textmodel-17: read_stone chooses by the joint calibration and gives its percentage (p_cal)
            p = x["p_cal"] if x.get("p_cal") is not None else (tm.calibrate_gap(x["p"], word, gp[2] - gp[1], G_cal) if word else 0.0)
            rows.append({"sig": r["signum"], "kind": rl.object_kind(r), "carved": w, "lost": gp[2] - gp[1], "truth": t,
                         "fill": x["fill"], "rune_ok": x["fill"] == t, "word": word, "gold_word": gold,
                         "word_ok": bool(gold and word and word != "<unk>" and rl.same_word(word.lstrip("§"), gold)),
                         "p": round(p, 4), "p_model": x["p"], "div_rate": x.get("div_rate"),
                         "alts": x.get("alts"),
                         "alts_ok": [bool(gold and w_ and w_ != "<unk>" and rl.same_word(w_.lstrip("§"), gold)) for w_, _ in x.get("alts") or []]})
        if i % 10 == 0:
            print(f"del {fold}: {i + 1} av {len(recs)} stenar, {len(rows)} luckor", flush=True)
    json.dump({"fold": fold, "rows": rows}, open(out_path, "w"), ensure_ascii=False, indent=1)
    print(f"del {fold} klar: {len(rows)} luckor", flush=True)


def summary(prefix: str):
    rows = [x for k in range(tm.K) if os.path.exists(f"{prefix}_f{k}.json") for x in json.load(open(f"{prefix}_f{k}.json"))["rows"]]
    out = {}
    for kind in rl.OBJECT_KINDS:
        xs = [x for x in rows if x["kind"] == kind]
        if not xs:
            continue
        with_gold = [x for x in xs if x["gold_word"]]
        bins = []
        for lo, hi in ((0, .5), (.5, .8), (.8, .95), (.95, 1.01)):
            ys = [x for x in with_gold if lo <= x["p"] < hi]
            bins.append({"lo": lo, "hi": hi, "n": len(ys), "said": sum(x["p"] for x in ys) / max(1, len(ys)),
                         "right": sum(x["word_ok"] for x in ys) / max(1, len(ys))})
        out[kind] = {"gaps": len(xs), "stones": len({x["sig"] for x in xs}), "rune_ok": sum(x["rune_ok"] for x in xs) / len(xs),
                     "word_n": len(with_gold), "word_ok": sum(x["word_ok"] for x in with_gold) / max(1, len(with_gold)),
                     "bins": bins}
        print(f"{kind}: {len(xs)} luckor på {out[kind]['stones']} föremål; rätt runor {out[kind]['rune_ok']:.1%}; "
              f"rätt ord {out[kind]['word_ok']:.1%} (av {len(with_gold)})")
        print("   säger → rätt:", [(f"{b['said']:.2f}", f"{b['right']:.2f}", b["n"]) for b in bins])
    json.dump(out, open(prefix + "_sammanfattning.json", "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fold", type=int)
    ap.add_argument("--out")
    ap.add_argument("--summary")
    ap.add_argument("--own_d", action="store_true", help="the carver's own divider rate (rl.stone_divider_rate)")
    ap.add_argument("--name_scale", type=float, default=1.0, help="factor on composed names (§) while filling")
    a = ap.parse_args()
    if a.summary:
        summary(a.summary)
    else:
        run(a.fold, a.out or os.path.join(ROOT, "utdata", "runlm_forfining", f"dokumenterade_f{a.fold}.json"), a.own_d, a.name_scale)
