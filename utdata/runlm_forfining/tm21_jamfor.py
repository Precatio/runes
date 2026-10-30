"""Jämförelserna i analysplan_tm21.md: A (appens inställning "app" mot textmodel-19:s prov tol02) och B (app3, med
trigram, mot app), parvis per lucka på runstenar, veck 0–4. Träffsäkerhet, vunna/förlorade ord, runan rätt och fel bland
svar ≥ 95 % (den levande kalibreringen, som tm19_ab.py). Skriver tm21_sammanfattning.json och tm21_resultat.md.
    PYTHONPATH=. .venv/bin/python utdata/runlm_forfining/tm21_jamfor.py"""
import json
import os
import sys

sys.path.insert(0, ".")
from src import runlm as rl  # noqa: E402
from src import textmodel as tm  # noqa: E402

F = "utdata/runlm_forfining/"
d = tm._records()
by, G = d["by"], d["G"]
rs = lambda s: rl.object_kind(by[s]) == "runsten"  # noqa: E731
KINDS = ("inne i ord", "helt ord")


def load(prefix):
    out = []
    for k in range(5):
        p = f"{F}{prefix}_f{k}.json"
        if not os.path.exists(p):
            return None
        out.append([x for x in json.load(open(p))["rows"] if rs(x["sig"])])
    return out


def sure(rows):
    n = right = 0
    for x in rows:
        if x["word"] and x["word"] != "<unk>":
            q = tm.calibrate_gap(x["p_word"], x["word"], x["n"], G, x["kind"] == "helt ord")
            if q >= 0.95:
                n += 1
                right += bool(x["word_ok"])
    return n, n - right


def compare(base, new):
    A, B = load(base), load(new)
    if A is None or B is None:
        return None
    res = {"base": base, "new": new, "words": {}, "accuracy": {}, "rune_top1": [0, 0]}
    for kind in KINDS:
        won = lost = n = ok_a = ok_b = 0
        for fa, fb in zip(A, B):
            assert len(fa) == len(fb)
            for x, y in zip(fa, fb):
                assert (x["sig"], x["kind"], x["truth"]) == (y["sig"], y["kind"], y["truth"])
                if x["kind"] != kind:
                    continue
                n += 1
                ok_a += x["word_ok"]; ok_b += y["word_ok"]
                won += y["word_ok"] and not x["word_ok"]
                lost += x["word_ok"] and not y["word_ok"]
        res["words"][kind] = {"won": won, "lost": lost, "n": n}
        res["accuracy"][kind] = {base: round(ok_a / n, 4), new: round(ok_b / n, 4)}
    for fa, fb in zip(A, B):
        for x, y in zip(fa, fb):
            res["rune_top1"][0] += (y["rank"] == 1) and not (x["rank"] == 1)
            res["rune_top1"][1] += (x["rank"] == 1) and not (y["rank"] == 1)
    sa = [sure(f) for f in A]; sb = [sure(f) for f in B]
    res["sure"] = {base: [sum(a for a, _ in sa), sum(e for _, e in sa)], new: [sum(a for a, _ in sb), sum(e for _, e in sb)]}
    return res


A = compare("tol02", "app")
B = compare("app", "app3")
out = {"A": A, "B": B}
if B:
    w = B["words"]
    out["B_holds"] = all(w[k]["won"] > w[k]["lost"] for k in KINDS) and B["sure"]["app3"][1] <= B["sure"]["app"][1]
json.dump(out, open(F + "tm21_sammanfattning.json", "w"), ensure_ascii=False, indent=1)
lines = ["# Resultat: textmodel-21 (analysplan_tm21.md)", ""]
for tag, r in (("A – appens inställning mot provets (tol02 → app)", A), ("B – trigram (app → app3)", B)):
    lines.append(f"## {tag}")
    if not r:
        lines += ["Inte körd ännu.", ""]
        continue
    for k in KINDS:
        acc, wd = r["accuracy"][k], r["words"][k]
        lines.append(f"- {k}: {wd['n']} luckor; rätt {acc[r['base']]:.1%} → {acc[r['new']]:.1%}; vunna {wd['won']}, "
                     f"förlorade {wd['lost']} (netto {wd['won'] - wd['lost']:+d})")
    lines.append(f"- runan rätt: vunna {r['rune_top1'][0]}, förlorade {r['rune_top1'][1]}")
    sb, sn = r["sure"][r["base"]], r["sure"][r["new"]]
    lines.append(f"- svar ≥ 95 %: {sb[0]} med {sb[1]} fel → {sn[0]} med {sn[1]} fel")
    lines.append("")
if "B_holds" in out:
    lines.append(f"**B enligt planens punkt 3: {'HÅLLER' if out['B_holds'] else 'HÅLLER INTE'}.**")
open(F + "tm21_resultat.md", "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
