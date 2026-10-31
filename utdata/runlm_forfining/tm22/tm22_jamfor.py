"""Jämförelserna i analysplaner/2026-10-30-litteraturlexikon.md: parvis per lucka mot appens inställning (app_f*),
bara runstenar. --kontroll: kontroll_f0 måste vara app_f0 rad för rad. --steg1: kandidaterna på veck 0, valet av
vikter (störst netto utan fler säkra fel, vid lika det minsta). --steg2: den valda kombinationen på veck 1–4 mot
app_f1–4 och planens gräns. Skriver tm22_sammanfattning.json och tm22_resultat.md.
    PYTHONPATH=. .venv/bin/python utdata/runlm_forfining/tm22/tm22_jamfor.py --kontroll|--steg1|--steg2"""
import argparse
import json
import os
import sys

sys.path.insert(0, ".")
from src import runlm as rl  # noqa: E402
from src import textmodel as tm  # noqa: E402

F = "utdata/runlm_forfining/"
T = F + "tm22/"
KINDS = ("inne i ord", "helt ord")
LIT = {"lit001": 0.01, "lit003": 0.03, "lit01": 0.1}
LEX = {"lex0003": 0.003, "lex001": 0.01}
_d = None


def records():
    global _d
    if _d is None:
        _d = tm._records()
    return _d


def load(path):
    if not os.path.exists(path):
        return None
    by = records()["by"]
    return [x for x in json.load(open(path))["rows"] if rl.object_kind(by[x["sig"]]) == "runsten"]


def sure(rows):
    G = records()["G"]
    n = right = 0
    for x in rows:
        if x["word"] and x["word"] != "<unk>":
            q = tm.calibrate_gap(x["p_word"], x["word"], x["n"], G, x["kind"] == "helt ord")
            if q >= 0.95:
                n += 1
                right += bool(x["word_ok"])
    return n, n - right


def compare(A, B):
    """Paired per gap: won/lost words per kind, rune top-1, sure answers and their errors; short gaps (1–2 runes) apart."""
    res = {"words": {}, "rune_top1": [0, 0], "short": {"won": 0, "lost": 0, "new_errors": 0}}
    assert len(A) == len(B), (len(A), len(B))
    for kind in KINDS:
        won = lost = n = ok_a = ok_b = 0
        for x, y in zip(A, B):
            assert (x["sig"], x["kind"], x["truth"]) == (y["sig"], y["kind"], y["truth"])
            if x["kind"] != kind:
                continue
            n += 1
            ok_a += x["word_ok"]; ok_b += y["word_ok"]
            won += y["word_ok"] and not x["word_ok"]
            lost += x["word_ok"] and not y["word_ok"]
        res["words"][kind] = {"won": won, "lost": lost, "n": n, "acc_base": round(ok_a / n, 4), "acc_new": round(ok_b / n, 4)}
    for x, y in zip(A, B):
        res["rune_top1"][0] += (y["rank"] == 1) and not (x["rank"] == 1)
        res["rune_top1"][1] += (x["rank"] == 1) and not (y["rank"] == 1)
        if x["n"] <= 2:
            res["short"]["won"] += y["word_ok"] and not x["word_ok"]
            res["short"]["lost"] += x["word_ok"] and not y["word_ok"]
            res["short"]["new_errors"] += (x["word_ok"] or not x["word"]) and (y["word"] and y["word"] != "<unk>" and not y["word_ok"])
    sa, sb = sure(A), sure(B)
    res["sure"] = {"base": list(sa), "new": list(sb)}
    net = sum(res["words"][k]["won"] - res["words"][k]["lost"] for k in KINDS)
    res["net"] = net
    res["ok"] = all(res["words"][k]["won"] > res["words"][k]["lost"] for k in KINDS) and sb[1] <= sa[1]
    return res


def fmt(tag, r):
    w = r["words"]
    return (f"- {tag}: inne i ord {w['inne i ord']['acc_base']:.1%} → {w['inne i ord']['acc_new']:.1%} "
            f"(vunna {w['inne i ord']['won']}, förlorade {w['inne i ord']['lost']}); helt ord {w['helt ord']['acc_base']:.1%} → "
            f"{w['helt ord']['acc_new']:.1%} (vunna {w['helt ord']['won']}, förlorade {w['helt ord']['lost']}); netto {r['net']:+d}; "
            f"runan rätt +{r['rune_top1'][0]}/−{r['rune_top1'][1]}; svar ≥ 95 %: {r['sure']['base'][0]} med {r['sure']['base'][1]} fel → "
            f"{r['sure']['new'][0]} med {r['sure']['new'][1]} fel; korta luckor (1–2 runor): vunna {r['short']['won']}, "
            f"förlorade {r['short']['lost']}, nya fel {r['short']['new_errors']}")


ap = argparse.ArgumentParser()
ap.add_argument("--kontroll", action="store_true")
ap.add_argument("--steg1", action="store_true")
ap.add_argument("--steg2", action="store_true")
args = ap.parse_args()
S = json.load(open(T + "tm22_sammanfattning.json")) if os.path.exists(T + "tm22_sammanfattning.json") else {}

if args.kontroll:
    # The control (added 2026-10-31 after the first run): the masking test's floats depend on Python's string-hash
    # order (PYTHONHASHSEED differs per process), so a rerun of the SAME code can differ in the 6th decimal on a gap or
    # two (kontroll_f0 vs app_f0: 1 of 324 rows, 0.811929 vs 0.811921, same choices). The strict test is therefore:
    # the committed code and the new code with weight 0, both with PYTHONHASHSEED=0, must be identical row for row;
    # and the control's choices (word, rune string, rank, right/wrong) must equal app_f0's.
    a = json.load(open(F + "app_f0.json"))["rows"]
    b = json.load(open(T + "kontroll_f0.json"))["rows"]
    dec = lambda r: [(x["sig"], x["kind"], x["truth"], x["word"], x["top"], x["rank"], x["word_ok"]) for x in r]  # noqa: E731
    same_choice = len(a) == len(b) and dec(a) == dec(b)
    maxdiff = max(abs(x["p_word"] - y["p_word"]) for x, y in zip(a, b))
    g, n = T + "seed0_gammal_f0.json", T + "seed0_ny_f0.json"
    seeded = (json.load(open(g))["rows"] == json.load(open(n))["rows"]) if os.path.exists(g) and os.path.exists(n) else None
    ok = same_choice and seeded is True
    S["kontroll"] = {"rader": len(a), "samma_val_som_app_f0": same_choice, "storsta_skillnad_p_word": maxdiff,
                     "rader_som_skiljer": sum(x != y for x, y in zip(a, b)), "seed0_gammal_lika_ny": seeded, "godkand": ok}
    json.dump(S, open(T + "tm22_sammanfattning.json", "w"), ensure_ascii=False, indent=1)
    print(f"kontroll: samma val som app_f0 {same_choice}; största skillnad i p_word {maxdiff:.2e}; "
          f"gammal = ny kod med fast seed: {seeded}; {'GODKÄND' if ok else 'INTE GODKÄND'}")
    sys.exit(0 if ok else 1)

if args.steg1:
    A = load(F + "app_f0.json")
    S["steg1"] = {}
    for name in list(LIT) + list(LEX) + ["namn"]:
        B = load(T + f"{name}_f0.json")
        if B is None:
            continue
        S["steg1"][name] = compare(A, B)
    # the choice: literature weight and lexicon weight each separately (plan 3): largest net without more sure errors;
    # at a tie the smallest weight; 0 if no weight helps
    def pick(cands, weights):
        best, best_w = None, 0.0
        for name in cands:
            r = S["steg1"].get(name)
            if not r or r["sure"]["new"][1] > r["sure"]["base"][1] or r["net"] <= 0:
                continue
            if best is None or r["net"] > best or (r["net"] == best and weights[name] < best_w):
                best, best_w = r["net"], weights[name]
        return best_w
    S["val"] = {"lit": pick(LIT, LIT), "lex": pick(LEX, LEX)}
    json.dump(S, open(T + "tm22_sammanfattning.json", "w"), ensure_ascii=False, indent=1)
    for name, r in S["steg1"].items():
        print(fmt(name, r))
    print("val:", S["val"])

if args.steg2:
    A = [x for k in range(1, 5) for x in load(F + f"app_f{k}.json")]
    B = []
    for k in range(1, 5):
        rows = load(T + f"vald_f{k}.json")
        if rows is None:
            print(f"veck {k} saknas"); sys.exit(1)
        B.extend(rows)
    S["steg2"] = compare(A, B)
    S["steg2_haller"] = S["steg2"]["ok"]
    json.dump(S, open(T + "tm22_sammanfattning.json", "w"), ensure_ascii=False, indent=1)
    print(fmt("vald (veck 1–4)", S["steg2"]), "\nhåller (maskeringsprovet):", S["steg2_haller"])
