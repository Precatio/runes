"""Jämförelserna i analysplaner/2026-11-20-petersons-namn-i-textmodellen.md (sha 321c3a6d): parvis per lucka mot appens
inställning (app_f0–4), bara runstenar. --kontroll: kontroll_f0 ska ha samma val som app_f0. --prov: namn_f0–4 mot
app_f0–4 och planens fyra villkor; beskrivande: tm22:s namn_f0 mot den nya. Skriver tm23_sammanfattning.json.
    PYTHONPATH=. .venv/bin/python utdata/runlm_forfining/tm23/tm23_jamfor.py --kontroll|--prov"""
import argparse
import json
import os
import sys

sys.path.insert(0, ".")
from src import runlm as rl  # noqa: E402
from src import textmodel as tm  # noqa: E402

F = "utdata/runlm_forfining/"
T = F + "tm23/"
_d = None


def records():
    global _d
    if _d is None:
        _d = tm._records()
    return _d


def load(path):
    by = records()["by"]
    return [x for x in json.load(open(path))["rows"] if rl.object_kind(by[x["sig"]]) == "runsten"]


def sure(rows):
    G = records()["G"]
    n = right = 0
    for x in rows:
        if x["word"] and x["word"] != "<unk>":
            if tm.calibrate_gap(x["p_word"], x["word"], x["n"], G, x["kind"] == "helt ord") >= 0.95:
                n += 1
                right += bool(x["word_ok"])
    return n, n - right


def compare(A, B):
    assert len(A) == len(B), (len(A), len(B))
    r = {"namn": {"won": 0, "lost": 0, "n": 0, "ok_base": 0, "ok_new": 0}, "alla": {"won": 0, "lost": 0, "n": 0},
         "short": {"new_right": 0, "new_errors": 0}}
    for x, y in zip(A, B):
        assert (x["sig"], x["kind"], x["truth"]) == (y["sig"], y["kind"], y["truth"])
        won, lost = bool(y["word_ok"] and not x["word_ok"]), bool(x["word_ok"] and not y["word_ok"])
        r["alla"]["n"] += 1; r["alla"]["won"] += won; r["alla"]["lost"] += lost
        if x.get("is_name"):
            r["namn"]["n"] += 1; r["namn"]["won"] += won; r["namn"]["lost"] += lost
            r["namn"]["ok_base"] += bool(x["word_ok"]); r["namn"]["ok_new"] += bool(y["word_ok"])
        if x["n"] <= 2:
            r["short"]["new_right"] += won
            r["short"]["new_errors"] += (x["word_ok"] or not x["word"]) and bool(y["word"] and y["word"] != "<unk>" and not y["word_ok"])
    r["sure"] = {"base": list(sure(A)), "new": list(sure(B))}
    return r


def add(a, b):
    out = {}
    for k, v in a.items():
        out[k] = add(v, b[k]) if isinstance(v, dict) else ([p + q for p, q in zip(v, b[k])] if isinstance(v, list) else v + b[k])
    return out


ap = argparse.ArgumentParser()
ap.add_argument("--kontroll", action="store_true")
ap.add_argument("--prov", action="store_true")
args = ap.parse_args()
P = T + "tm23_sammanfattning.json"
S = json.load(open(P)) if os.path.exists(P) else {}

if args.kontroll:
    a = json.load(open(F + "app_f0.json"))["rows"]
    b = json.load(open(T + "kontroll_f0.json"))["rows"]
    dec = lambda r: [(x["sig"], x["kind"], x["truth"], x["word"], x["top"], x["rank"], x["word_ok"]) for x in r]  # noqa: E731
    ok = len(a) == len(b) and dec(a) == dec(b)
    S["kontroll"] = {"rader": len(a), "samma_val_som_app_f0": ok, "rader_som_skiljer": sum(x != y for x, y in zip(dec(a), dec(b)))}
    json.dump(S, open(P, "w"), ensure_ascii=False, indent=1)
    print(f"kontroll: samma val som app_f0 {ok}")
    sys.exit(0 if ok else 1)

if args.prov:
    per = {k: compare(load(F + f"app_f{k}.json"), load(T + f"namn_f{k}.json")) for k in range(5)}
    tot = per[0]
    for k in range(1, 5):
        tot = add(tot, per[k])
    c1 = tot["namn"]["won"] > tot["namn"]["lost"]
    c2 = tot["alla"]["won"] - tot["alla"]["lost"] >= 0
    c3 = tot["sure"]["new"][1] <= tot["sure"]["base"][1]
    c4 = tot["short"]["new_errors"] <= tot["short"]["new_right"]
    S["prov"] = {"per_veck": per, "totalt": tot, "villkor": {"1_namn": c1, "2_alla": c2, "3_saker": c3, "4_korta": c4},
                 "haller": c1 and c2 and c3 and c4}
    old = T.replace("tm23", "tm22") + "namn_f0.json"
    if os.path.exists(old):
        S["beskrivande_tm22_mot_tm23_f0"] = compare(load(old), load(T + "namn_f0.json"))
    json.dump(S, open(P, "w"), ensure_ascii=False, indent=1)
    n = tot["namn"]
    print(f"namnluckor {n['n']}: rätt {n['ok_base']} → {n['ok_new']} (vunna {n['won']}, förlorade {n['lost']}); "
          f"alla {tot['alla']['n']}: vunna {tot['alla']['won']}, förlorade {tot['alla']['lost']}; "
          f"≥ 95 %: {tot['sure']['base']} → {tot['sure']['new']}; korta: nya rätt {tot['short']['new_right']}, "
          f"nya fel {tot['short']['new_errors']}; HÅLLER: {S['prov']['haller']}")
