"""Namnexperimentet: vad händer med de dokumenterade luckorna om namnmatcharen (Names.match, name_cands) slås på i
appens inställningar? Diagnosen visade att 22 av 52 facitord som i dag saknas helt bland kandidaterna nås av den
befintliga matcharen – den har bara aldrig varit på (FILL saknar name_cands). Här körs varje sten som har minst en
sådan "frånvarande facit"-miss två gånger med appens kedja (luckprov.read_stone, own_d): utan och med
name_cands=N. ALLA stenens dokumenterade luckor räknas om båda gångerna, så vinster och regressioner syns ihop.
Mäts med riktmärkets regel (rl.same_word). Skriver namn_experiment_f<fald>.json.
    PYTHONPATH=. .venv/bin/python utdata/runlm_forfining/namn_experiment.py --fold K [--cands 40]"""
import argparse
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
import src.runlm as rl  # noqa: E402
import src.textmodel as tm  # noqa: E402
from scripts.luckprov import read_stone  # noqa: E402
from scripts.runlm_documented_test import items_for  # noqa: E402


def gold_of(tok):
    return rl.normtok(tok.replace("[", "").replace("]", "").lstrip("…")) if tok and tok != "..." else None


def rows_for(r, m):
    its = items_for(r)
    by_gap = {(g[gp[0]], tuple(gp)): (g, gp, w, tok, t) for g, gp, w, tok, t in its}
    out = []
    for y in read_stone(r, [(g, gp, w, tok) for g, gp, w, tok, _ in its], own_d=True):
        g, gp, w, tok, t = by_gap[(y["group"], tuple(y["gap"]))]
        gold = gold_of(tok)
        word = (y["word"] or "").lstrip("§")
        out.append({"carved": w, "truth": t, "fill": y["fill"], "word": y["word"], "gold": gold,
                    "p": y.get("p_cal"), "alts": y.get("alts"),
                    "ok": bool(gold and word and word != "<unk>" and rl.same_word(word, gold))})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fold", type=int, required=True)
    ap.add_argument("--cands", type=int, default=40)
    a = ap.parse_args()

    dok = []
    for p in sorted(glob.glob(os.path.join(HERE, "dok5_f*.json"))):
        dok += json.load(open(p))["rows"]
    absent = {x["sig"] for x in dok if x["kind"] == "runsten" and x.get("gold_word") and not x["word_ok"]
              and not any(x.get("alts_ok") or [])}
    d = tm._records()
    stones = [r for r in d["V"] if r["signum"] in absent and tm.fold_of(r["signum"]) == a.fold]
    print(f"fald {a.fold}: {len(stones)} stenar med frånvarande facit", flush=True)
    base_fill = dict(tm.FILL)
    out = []
    for i, r in enumerate(stones):
        tm.FILL = dict(base_fill)
        before = rows_for(r, None)
        tm.FILL = {**base_fill, "name_cands": a.cands}
        after = rows_for(r, None)
        tm.FILL = dict(base_fill)
        out.append({"sig": r["signum"], "before": before, "after": after})
        nb = sum(x["ok"] for x in before)
        na = sum(x["ok"] for x in after)
        print(f"  {r['signum']}: {nb} → {na} rätt av {len(before)}", flush=True)
    json.dump({"fold": a.fold, "cands": a.cands, "stones": out},
              open(os.path.join(HERE, f"namn_experiment_f{a.fold}.json"), "w"), ensure_ascii=False, indent=1)
    print("klart", flush=True)


if __name__ == "__main__":
    main()
