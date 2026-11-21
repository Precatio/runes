"""Ormen och draken – fördjupning 5 i serien Nordiska väsen, enligt analysplaner/2026-11-21-ormen-och-draken.md (låst
15ce39f). Samma korpusar som den första väsenstudien. Träffar och handklassning i data/cache/draken/ (git-ignorerad).

    .venv/bin/python utdata/draken/analys.py --samla      # alla träffar → data/cache/draken/traffar.csv
    .venv/bin/python utdata/draken/analys.py --kontroll   # 50 stratifierade för blind omklassning
    .venv/bin/python utdata/draken/analys.py              # O1–O3, T1 → utdata/draken/matt.json
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

PLAN = os.path.join(ROOT, "analysplaner", "2026-11-21-ormen-och-draken.md")
assert hashlib.sha256(open(PLAN, "rb").read()).hexdigest().startswith("e0a03ad3"), "planen är ändrad efter låsningen"
DREKI = re.compile(r"\bdrek(?:i|a|ar|um|inn|ann|ans|anum|arnir|ana|anna|unum)\b|\bdrekahöf\w*")
ORMR = re.compile(r"\b(?:lin)?orm(?:r|ur|s|i|inn|ar|a|um|arnir|ana|anna|unum|inum|sins)\b")
NAMED = re.compile(r"\b(?:Fáfni\w*|Miðgarðsorm\w*|Jörmungand\w*|Níðhögg\w*|Góin\w*|Móin\w*)")
CLASSES = {"drake", "orm", "skepp", "bild", "kenning", "annat"}
CACHE = os.path.join(ROOT, "data", "cache", "draken")
SEED = 20261121
B = 10000
FAFNIR_POEMS = {"Reginsmál", "Fáfnismál", "Sigrdrífumál"}
FAFNIR_PROSE = {"Völsunga saga", "Norna-Gests þáttr", "Gylfaginning", "Skáldskaparmál"}


def group(c):
    if c == "eddadikter":
        return "eddadikter"
    if c.startswith("runstenar"):
        return None
    if c.endswith("_vers"):
        return "vers"
    return "prosa"


def texts():
    return [(c, n, t) for c, n, t in vasen.texts()]


def samla():
    os.makedirs(CACHE, exist_ok=True)
    rows = []
    for c, n, t in texts():
        for word, rx in (("dreki", DREKI), ("ormr", ORMR)):
            for m in rx.finditer(t):
                rows.append({"id": f"{c}|{n}|{m.start()}", "korpus": c, "grupp": group(c) or "runsten", "text": n, "ordet": word,
                             "form": m.group(0), "kwic": t[max(0, m.start() - 110): m.end() + 110].replace("\n", " ")})
    with open(os.path.join(CACHE, "traffar.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(len(rows), Counter((r["grupp"], r["ordet"]) for r in rows))


def kontroll():
    rows = list(csv.DictReader(open(os.path.join(CACHE, "traffar.csv"), encoding="utf-8")))
    by = defaultdict(list)
    for r in rows:
        by[(r["ordet"], r["grupp"])].append(r)
    rnd = random.Random(SEED)
    keys = sorted(by)
    per = max(1, 50 // len(keys))
    pick = []
    for k in keys:
        pick += rnd.sample(by[k], min(per, len(by[k])))
    rest = [r for r in rows if r not in pick]
    pick += rnd.sample(rest, 50 - len(pick)) if len(pick) < 50 else []
    with open(os.path.join(CACHE, "kontroll_blind.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "form", "kwic"])
        w.writeheader()
        for r in pick[:50]:
            w.writerow({"id": r["id"], "form": r["form"], "kwic": r["kwic"]})
    print(len(pick[:50]))


def boot_diff(A, Bn, stat, rnd):
    out = []
    for _ in range(B):
        a = [A[rnd.randrange(len(A))] for _ in A]
        b = [Bn[rnd.randrange(len(Bn))] for _ in Bn]
        sa, sb = stat(a), stat(b)
        if sa is not None and sb is not None:
            out.append(sa - sb)
    return out


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
    for r in rows:
        r["klass"] = cls[r["id"]]
    res = {"träffar": len(rows)}
    res["O1"] = {f"{g}|{w}": dict(Counter(r["klass"] for r in rows if r["grupp"] == g and r["ordet"] == w).most_common())
                 for g in ("eddadikter", "prosa", "vers", "runsten") for w in ("dreki", "ormr")}
    res["O1_korpus_dreki"] = {c: dict(Counter(r["klass"] for r in rows if r["korpus"] == c and r["ordet"] == "dreki").most_common())
                              for c in dict.fromkeys(r["korpus"] for r in rows)}
    res["O1_drakar_per_text"] = Counter(f"{r['korpus']}|{r['text']}|{r['ordet']}" for r in rows if r["klass"] == "drake").most_common(30)
    # O2
    named = Counter()
    for c, n, t in texts():
        g = group(c) or "runsten"
        for m in NAMED.finditer(t):
            named[(g, re.sub(r"(?<=.{4}).*", "", m.group(0)))] += 1
    res["O2"] = {f"{g}|{k}": v for (g, k), v in sorted(named.items())}

    # T1
    def t1(filter_poem=None, filter_prose=None, skip=()):
        u = {"eddadikter": defaultdict(list), "prosa": defaultdict(list)}
        for r in rows:
            if r["klass"] != "drake" or r["grupp"] not in u or r["korpus"].split("_")[-1] in skip or r["korpus"] in skip:
                continue
            if filter_poem and r["grupp"] == "eddadikter" and r["text"] not in filter_poem:
                continue
            if filter_prose and r["grupp"] == "prosa" and r["text"] not in filter_prose:
                continue
            u[r["grupp"]][r["text"]].append(r["ordet"] == "dreki")
        E, P = list(u["eddadikter"].values()), list(u["prosa"].values())
        nE, nP = sum(map(len, E)), sum(map(len, P))
        out = {"edda_n": nE, "edda_texter": len(E), "prosa_n": nP, "prosa_texter": len(P)}
        if nE < 10 or nP < 10 or len(E) < 3 or len(P) < 3:
            out["obestämt"] = True
            return out
        sh = lambda us: 100 * sum(sum(x) for x in us) / sum(map(len, us)) if sum(map(len, us)) else None  # noqa: E731
        d = boot_diff(P, E, sh, random.Random(SEED))
        out.update({"edda_dreki_%": round(sh(E), 1), "prosa_dreki_%": round(sh(P), 1), "skillnad_pe": round(sh(P) - sh(E), 1),
                    "intervall": ci(d), "p": p_two(d)})
        out["håller"] = out["p"] < 0.05 and not (out["intervall"][0] <= 0 <= out["intervall"][1])
        return out
    res["T1"] = {"huvud": t1(), "bara_fafnir": t1(FAFNIR_POEMS, FAFNIR_PROSE),
                 "utan_snorre": t1(skip=("snorra_edda_gylfaginning", "snorra_edda_skáldskaparmál"))}

    # O3 runstenarna
    from api.rundata import store
    from src.research_gaps import PROVINCE_NAMES, is_runestone
    stones = [r for r in store().inscriptions if is_runestone(r)]
    res["O3_text"] = [(r["signum"], m.group(0)) for r in stones for rx in (DREKI, ORMR)
                      for m in rx.finditer(r.get("normalization_ows") or "")]
    by = defaultdict(lambda: [0, 0])
    for r in stones:
        st = (r.get("style") or "").strip()
        if not st or st.startswith("?") or r.get("style_uncertain"):
            continue
        s0 = re.split(r"\s*-\s*|\s", st)[0].rstrip("?")
        if s0 not in ("RAK", "Fp", "Pr1", "Pr2", "Pr3", "Pr4", "Pr5", "KB"):
            continue
        prov = PROVINCE_NAMES.get(r["signum"].split()[0], r["signum"].split()[0])
        by[prov][0] += 1
        by[prov][1] += s0 in ("Fp", "Pr1", "Pr2", "Pr3", "Pr4", "Pr5")
    res["O3_ormslinga"] = {k: {"stilbestämda": v[0], "med_ormhuvud": v[1], "andel": round(100 * v[1] / v[0], 1)}
                           for k, v in sorted(by.items(), key=lambda x: -x[1][0]) if v[0] >= 15}
    res["O3_totalt"] = {"stilbestämda": sum(v[0] for v in by.values()), "med_ormhuvud": sum(v[1] for v in by.values())}
    json.dump(res, open(os.path.join(HERE, "matt.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: res[k] for k in ("O1", "T1", "O3_totalt")}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    samla() if "--samla" in sys.argv else kontroll() if "--kontroll" in sys.argv else main()
