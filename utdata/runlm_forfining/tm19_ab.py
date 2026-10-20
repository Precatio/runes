"""A/B för toleranslagret (analysplan_tm19.md, punkt 3): samma luckor som mask4 (textmodel-18), parvis per lucka.
Räknar vunna/förlorade hela ord och runor, och antalet fel bland svar med kalibrerad sannolikhet ≥ 95 % (tm18:s
kalibrering, data/runlm_calibration.json). Veck 0 är urvalsvecket för λ; veck 1–4 är provet.
    PYTHONPATH=. .venv/bin/python utdata/runlm_forfining/tm19_ab.py tol05 [--folds 1 2 3 4]
där tol05 är prefixet på de nya filerna (utdata/runlm_forfining/tol05_f{k}.json)."""
import argparse
import json
import sys

sys.path.insert(0, ".")
from src import runlm as rl  # noqa: E402
from src import textmodel as tm  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("prefix")
ap.add_argument("--folds", type=int, nargs="*", default=[0, 1, 2, 3, 4])
ap.add_argument("--base", default="mask4")
a = ap.parse_args()
F = "utdata/runlm_forfining/"
d = tm._records()
by, G = d["by"], d["G"]
rs = lambda s: rl.object_kind(by[s]) == "runsten"  # noqa: E731


def sure_errors(rows):
    n = 0
    for x in rows:
        if x["word"] and x["word"] != "<unk>":
            q = tm.calibrate_gap(x["p_word"], x["word"], x["n"], G, x["kind"] == "helt ord")
            n += q >= 0.95 and not x["word_ok"]
    return n


tot = {"inne i ord": [0, 0, 0], "helt ord": [0, 0, 0]}  # won, lost, n
rune = [0, 0]
sure = [0, 0]
won_words, lost_words = [], []
for k in a.folds:
    A = [x for x in json.load(open(f"{F}{a.base}_f{k}.json"))["rows"] if rs(x["sig"])]
    B = [x for x in json.load(open(f"{F}{a.prefix}_f{k}.json"))["rows"] if rs(x["sig"])]
    assert len(A) == len(B), (k, len(A), len(B))
    for x, y in zip(A, B):
        assert (x["sig"], x["kind"], x["truth"], x["gold_word"]) == (y["sig"], y["kind"], y["truth"], y["gold_word"]), (k, x["sig"])
        t = tot[x["kind"]]
        t[2] += 1
        if y["word_ok"] and not x["word_ok"]:
            t[0] += 1; won_words.append((x["sig"], x["gold_word"], x["truth"], y.get("word")))
        elif x["word_ok"] and not y["word_ok"]:
            t[1] += 1; lost_words.append((x["sig"], x["gold_word"], x.get("word"), y.get("word")))
        rune[0] += (y["rank"] == 1) and not (x["rank"] == 1)
        rune[1] += (x["rank"] == 1) and not (y["rank"] == 1)
    sure[0] += sure_errors(A); sure[1] += sure_errors(B)
print(f"veck {a.folds}: bas {a.base} mot {a.prefix}")
for kind, (w, l, n) in tot.items():
    print(f"  {kind}: {n} luckor, vunna {w}, förlorade {l} (netto {w - l:+d})")
print(f"  runan rätt (top1): vunna {rune[0]}, förlorade {rune[1]}")
print(f"  fel bland ≥95 %: bas {sure[0]}, ny {sure[1]}")
print("  vunna ord:", won_words[:25])
print("  förlorade ord:", lost_words[:25])
json.dump({"folds": a.folds, "base": a.base, "new": a.prefix, "words": {k: {"won": v[0], "lost": v[1], "n": v[2]} for k, v in tot.items()},
           "rune_top1": {"won": rune[0], "lost": rune[1]}, "sure_errors": {"base": sure[0], "new": sure[1]},
           "won": won_words, "lost": lost_words}, open(f"{F}tm19_ab_{a.prefix}_{'_'.join(map(str, a.folds))}.json", "w"),
          ensure_ascii=False, indent=1)
