"""Vargarna – fördjupning 7 i serien Fornnordiska väsen, enligt analysplaner/2026-11-22-vargarna.md (låst 6e4e192).

    .venv/bin/python utdata/vargarna/analys.py --samla      # alla vargträffar → data/cache/vargarna/traffar.csv
    .venv/bin/python utdata/vargarna/analys.py --kontroll   # 40 stratifierade för blind omklassning
    .venv/bin/python utdata/vargarna/analys.py              # V1–V4, T1 → utdata/vargarna/matt.json
"""
import csv
import hashlib
import importlib.util
import json
import os
import random
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "utdata", "varlden"))
_spec = importlib.util.spec_from_file_location("vasen_analys", os.path.join(ROOT, "utdata", "vasen", "analys.py"))
vasen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vasen)

PLAN = os.path.join(ROOT, "analysplaner", "2026-11-22-vargarna.md")
assert hashlib.sha256(open(PLAN, "rb").read()).hexdigest().startswith("ea7c37c0"), "planen är ändrad efter låsningen"
WOLF = re.compile(r"\b(?:varg(?:r|ur|s|i|ar|a|um|inn|ana|arnir|anna)?|[uú]lf(?:r|ur|s|i|ar|a|um|inn|ana|arnir|anna)|ylg(?:r|ur|jar|i)|vargynj\w*)\b")
RAVEN = re.compile(r"\b(?:hrafn\w*|hröfn\w*)\b")
EAGLE = re.compile(r"\b(?:örn\w*|arnar\w*|ari)\b")
BERS = re.compile(r"\bberserk\w*|\b[uú]lfheð\w*")
NAMED = re.compile(r"\b(?:Fenri[rs]\w*|Sköll\w*|Hati|Hata|Garm(?:r|s|i)?|Geri|Gera|Freki|Freka)\b")
CLASSES = {"djur", "myt", "fredlös", "förvandling", "kenning", "annat"}
CACHE = os.path.join(ROOT, "data", "cache", "vargarna")
SEED = 20261122
B = 10000


def group(c):
    if c == "eddadikter" or c.endswith("_vers"):
        return "dikt"
    if c.startswith("snorra_edda"):
        return "snorre"
    if c.startswith("runstenar"):
        return None
    return "prosa"


def texts():
    return [(c, n, t) for c, n, t in vasen.texts()]


def samla():
    os.makedirs(CACHE, exist_ok=True)
    rows = []
    for c, n, t in texts():
        if c.startswith("runstenar"):
            continue
        for m in WOLF.finditer(t):
            rows.append({"id": f"{c}|{n}|{m.start()}", "korpus": c, "grupp": group(c), "text": n, "form": m.group(0),
                         "kwic": t[max(0, m.start() - 110): m.end() + 110].replace("\n", " ")})
    with open(os.path.join(CACHE, "traffar.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(len(rows), Counter(r["grupp"] for r in rows))


def kontroll():
    rows = list(csv.DictReader(open(os.path.join(CACHE, "traffar.csv"), encoding="utf-8")))
    by = defaultdict(list)
    for r in rows:
        by[r["grupp"]].append(r)
    rnd = random.Random(SEED)
    pick = []
    for g in sorted(by):
        pick += rnd.sample(by[g], min(14, len(by[g])))
    rest = [r for r in rows if r not in pick]
    pick = pick[:40] + (rnd.sample(rest, 40 - len(pick)) if len(pick) < 40 else [])
    with open(os.path.join(CACHE, "kontroll_blind.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "form", "kwic"])
        w.writeheader()
        for r in pick[:40]:
            w.writerow({"id": r["id"], "form": r["form"], "kwic": r["kwic"]})
    print(len(pick[:40]))


def ci(xs):
    s = sorted(xs)
    return [round(s[int(0.025 * len(s))], 1), round(s[int(0.975 * len(s)) - 1], 1)]


def p_two(xs):
    lo = sum(1 for x in xs if x <= 0) / len(xs)
    hi = sum(1 for x in xs if x >= 0) / len(xs)
    return min(1.0, 2 * min(lo, hi))


def main():
    rows = list(csv.DictReader(open(os.path.join(CACHE, "traffar.csv"), encoding="utf-8")))
    cls = {r["id"]: r["klass"] for r in csv.DictReader(open(os.path.join(CACHE, "klassning.csv"), encoding="utf-8"))}
    assert set(cls) == {r["id"] for r in rows} and set(cls.values()) <= CLASSES
    T = {(c, n): t for c, n, t in texts()}
    words = {k: len(t.split()) for k, t in T.items()}
    for r in rows:
        r["klass"] = cls[r["id"]]
    res = {"träffar": len(rows)}
    res["V1"] = {g: dict(Counter(r["klass"] for r in rows if r["grupp"] == g).most_common()) for g in ("dikt", "prosa", "snorre")}
    res["V1_korpus"] = {c: dict(Counter(r["klass"] for r in rows if r["korpus"] == c).most_common())
                        for c in dict.fromkeys(r["korpus"] for r in rows)}
    res["V1_per_10000"] = {c: round(1e4 * sum(1 for r in rows if r["korpus"] == c and r["klass"] in ("djur", "myt", "förvandling"))
                                    / sum(n for (cc, _), n in words.items() if cc == c), 2)
                           for c in dict.fromkeys(c for c, _ in words if not c.startswith("runstenar"))}
    named = Counter()
    bers = defaultdict(Counter)
    for (c, n), t in T.items():
        g = group(c)
        if g is None:
            continue
        for m in NAMED.finditer(t):
            named[(g, m.group(0))] += 1
        for m in BERS.finditer(t):
            bers[c][n] += 1
    res["V2"] = {f"{g}|{k}": v for (g, k), v in sorted(named.items())}
    res["V3"] = {c: {"träffar": sum(v.values()), "per_10000": round(1e4 * sum(v.values()) / sum(n for (cc, _), n in words.items() if cc == c), 2),
                     "vanligaste": v.most_common(5)} for c, v in bers.items()}

    def t1(rx=RAVEN, k=25):
        u = {"dikt": defaultdict(list), "prosa": defaultdict(list)}
        for r in rows:
            if r["klass"] not in ("djur", "myt") or r["grupp"] not in u:
                continue
            t = T[(r["korpus"], r["text"])]
            pos = int(r["id"].rsplit("|", 1)[1])
            win = " ".join(t[:pos].split()[-k:] + t[pos:].split()[1:k + 1])
            u[r["grupp"]][(r["korpus"], r["text"])].append(bool(rx.search(win)))
        Dk, P = list(u["dikt"].values()), list(u["prosa"].values())
        nD, nP = sum(map(len, Dk)), sum(map(len, P))
        out = {"dikt_n": nD, "dikt_texter": len(Dk), "prosa_n": nP, "prosa_texter": len(P)}
        if nD < 10 or nP < 10 or len(Dk) < 3 or len(P) < 3:
            out["obestämt"] = True
            return out
        sh = lambda us: 100 * sum(sum(x) for x in us) / sum(map(len, us))  # noqa: E731
        rnd = random.Random(SEED)
        d = []
        for _ in range(B):
            a = [Dk[rnd.randrange(len(Dk))] for _ in Dk]
            b = [P[rnd.randrange(len(P))] for _ in P]
            d.append(sh(a) - sh(b))
        out.update({"dikt_%": round(sh(Dk), 1), "prosa_%": round(sh(P), 1), "skillnad_pe": round(sh(Dk) - sh(P), 1),
                    "intervall": ci(d), "p": p_two(d)})
        out["håller"] = out["p"] < 0.05 and not (out["intervall"][0] <= 0 <= out["intervall"][1])
        return out
    res["T1"] = {"huvud": t1(), "med_örn": t1(re.compile(RAVEN.pattern + "|" + EAGLE.pattern)), "fönster_10": t1(k=10)}

    from api.rundata import store
    from src.research_gaps import is_runestone
    res["V4_text"] = [(r["signum"], m.group(0)) for r in store().inscriptions if is_runestone(r)
                      for m in WOLF.finditer(r.get("normalization_ows") or "")]
    b = json.load(open(os.path.join(ROOT, "utdata", "bjornen", "matt.json"), encoding="utf-8"))
    res["V4_namn"] = {"stenar_med_vargnamn": b["B3_totalt"]["vargnamn"], "stenar": b["B3_totalt"]["stenar"],
                      "per_landskap": {k: {"vargnamn": v["vargnamn"], "andel": v["varg_andel"]} for k, v in b["B3_landskap"].items()}}
    json.dump(res, open(os.path.join(HERE, "matt.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: res[k] for k in ("V1", "T1", "V2", "V4_text")}, ensure_ascii=False, indent=1)[:3500])


if __name__ == "__main__":
    samla() if "--samla" in sys.argv else kontroll() if "--kontroll" in sys.argv else main()
