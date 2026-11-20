"""Paired comparison per gap against app_f* (runestones only), the four conditions of plans 321c3a6d and fe998288."""
import json

from src import runlm as rl
from src import textmodel as tm

_d = None


def records():
    global _d
    if _d is None:
        _d = tm._records()
    return _d


def load(path):
    by = records()["by"]
    return [x for x in json.load(open(path))["rows"] if rl.object_kind(by[x["sig"]]) == "runsten"]


def same_choices(a_path, b_path):
    a, b = json.load(open(a_path))["rows"], json.load(open(b_path))["rows"]
    dec = lambda r: [(x["sig"], x["kind"], x["truth"], x["word"], x["top"], x["rank"], x["word_ok"]) for x in r]  # noqa: E731
    return len(a) == len(b) and dec(a) == dec(b)


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
        r["alla"]["n"] += 1; r["alla"]["won"] += won; r["alla"]["lost"] += lost  # noqa: E702
        if x.get("is_name"):
            r["namn"]["n"] += 1; r["namn"]["won"] += won; r["namn"]["lost"] += lost  # noqa: E702
            r["namn"]["ok_base"] += bool(x["word_ok"]); r["namn"]["ok_new"] += bool(y["word_ok"])  # noqa: E702
        if x["n"] <= 2:
            r["short"]["new_right"] += won
            r["short"]["new_errors"] += (x["word_ok"] or not x["word"]) and bool(y["word"] and y["word"] != "<unk>" and not y["word_ok"])
    r["sure"] = {"base": list(sure(A)), "new": list(sure(B))}
    return r


def add(a, b):
    return {k: add(v, b[k]) if isinstance(v, dict) else ([p + q for p, q in zip(v, b[k])] if isinstance(v, list) else v + b[k])
            for k, v in a.items()}


def verdict(tot):
    c = {"1_namn": tot["namn"]["won"] > tot["namn"]["lost"], "2_alla": tot["alla"]["won"] - tot["alla"]["lost"] >= 0,
         "3_saker": tot["sure"]["new"][1] <= tot["sure"]["base"][1],
         "4_korta": tot["short"]["new_errors"] <= tot["short"]["new_right"]}
    return {"villkor": c, "haller": all(c.values())}


def line(tot):
    n = tot["namn"]
    return (f"namnluckor {n['n']}: rätt {n['ok_base']} → {n['ok_new']} (vunna {n['won']}, förlorade {n['lost']}); "
            f"alla {tot['alla']['n']}: vunna {tot['alla']['won']}, förlorade {tot['alla']['lost']}; "
            f"≥ 95 %: {tot['sure']['base']} → {tot['sure']['new']}; korta: nya rätt {tot['short']['new_right']}, "
            f"nya fel {tot['short']['new_errors']}")
