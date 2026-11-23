"""De döda som går igen – fördjupning 8 i serien Fornnordiska väsen, enligt analysplaner/2026-11-23-de-doda-som-gar-igen.md
(låst d6a533a).

    .venv/bin/python utdata/de_doda/analys.py --samla      # alla träffar → data/cache/de_doda/traffar.csv
    .venv/bin/python utdata/de_doda/analys.py --kontroll   # 40 stratifierade för blind omklassning
    .venv/bin/python utdata/de_doda/analys.py              # V1–V3, T1 → utdata/de_doda/matt.json
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
_spec = importlib.util.spec_from_file_location("vasen_analys", os.path.join(ROOT, "utdata", "vasen", "analys.py"))
vasen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vasen)

PLAN = os.path.join(ROOT, "analysplaner", "2026-11-23-de-doda-som-gar-igen.md")
assert hashlib.sha256(open(PLAN, "rb").read()).hexdigest().startswith("93b258fa"), "planen är ändrad efter låsningen"
A = [re.compile(p, re.I) for p in (
    r"\bdraug(?:r|ur|s|i|a|ar|ana|arnir|um|inn|inum)?\b",
    r"\bhaugbú\w*",
    r"\b(?:aptr|aftr|aftur|apt)gang\w*|\bafturgöng\w*|\baptrgöng\w*",
    r"\b(?:gekk|gengu|ganga|gengi|gangi|gengr|gengur|gengið|genginn)\s+(?:aftur|aftr|aptr|apt)\b",
    r"\breim(?:t|leik\w*|ast\w*)\b",
    r"\buppvakning\w*")]
B_RX = re.compile(r"\bhaug(?:r|ur|s|i|inn|inum|ins|a|ar|um|ana|arnir)?\b", re.I)
RS_RX = re.compile(r"\bhaug\w*|\bhôg\w*")
CLASSES = {"gengångare", "högbo", "grav", "plats", "annan betydelse", "annat"}
ACTIVE = ("gengångare", "högbo")
CACHE = os.path.join(ROOT, "data", "cache", "de_doda")
SEED = 20261123
B = 10000


def group(c):
    if c == "islanningasagor":
        return "isl"
    if c == "fornaldarsagor":
        return "forn"
    if c.startswith("runstenar"):
        return None
    return "övriga"


def texts():
    return [(c, n, t) for c, n, t in vasen.texts()]


def samla():
    os.makedirs(CACHE, exist_ok=True)
    rows = []
    for c, n, t in texts():
        if c.startswith("runstenar"):
            continue
        seen = set()
        for mon, rxs in (("A", A), ("B", [B_RX])):
            for rx in rxs:
                for m in rx.finditer(t):
                    if any(abs(m.start() - s) < 3 for s in seen):
                        continue
                    seen.add(m.start())
                    rows.append({"id": f"{c}|{n}|{m.start()}", "monster": mon, "korpus": c, "grupp": group(c), "text": n,
                                 "form": m.group(0), "kwic": t[max(0, m.start() - 160): m.end() + 160].replace("\n", " ")})
    rows.sort(key=lambda r: (r["korpus"], r["text"], int(r["id"].rsplit("|", 1)[1])))
    with open(os.path.join(CACHE, "traffar.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(len(rows), Counter((r["monster"], r["grupp"]) for r in rows))


def kontroll():
    rows = list(csv.DictReader(open(os.path.join(CACHE, "traffar.csv"), encoding="utf-8")))
    by = defaultdict(list)
    for r in rows:
        by[(r["monster"], r["grupp"])].append(r)
    rnd = random.Random(SEED)
    strata = sorted(by)
    per = {k: max(1, round(40 * len(by[k]) / len(rows))) for k in strata}
    while sum(per.values()) > 40:
        k = max(per, key=lambda x: per[x])
        per[k] -= 1
    while sum(per.values()) < 40:
        k = max(strata, key=lambda x: len(by[x]) - per[x])
        per[k] += 1
    pick = []
    for k in strata:
        pick += rnd.sample(by[k], min(per[k], len(by[k])))
    with open(os.path.join(CACHE, "kontroll_blind.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "form", "kwic"])
        w.writeheader()
        for r in pick:
            w.writerow({"id": r["id"], "form": r["form"], "kwic": r["kwic"]})
    print(len(pick), per)


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
    words = {(c, n): len(t.split()) for c, n, t in texts()}
    res = {"träffar": len(rows), "per_mönster": dict(Counter(r["monster"] for r in rows))}
    res["V1"] = {g: dict(Counter(r["klass"] for r in rows if r["grupp"] == g).most_common()) for g in ("isl", "forn", "övriga")}
    res["V1_mönster"] = {f"{m}|{g}": dict(Counter(r["klass"] for r in rows if r["grupp"] == g and r["monster"] == m).most_common())
                         for m in ("A", "B") for g in ("isl", "forn", "övriga")}
    res["V1_korpus"] = {c: dict(Counter(r["klass"] for r in rows if r["korpus"] == c).most_common())
                        for c in dict.fromkeys(r["korpus"] for r in rows)}
    res["V1_per_10000"] = {c: round(1e4 * sum(1 for r in rows if r["korpus"] == c and r["klass"] in ACTIVE)
                                    / sum(n for (cc, _), n in words.items() if cc == c), 2)
                           for c in dict.fromkeys(c for c, _ in words if not c.startswith("runstenar"))}
    per_text = Counter((r["korpus"], r["text"]) for r in rows if r["klass"] in ACTIVE)
    res["V2"] = [[c, n, k, dict(Counter(r["klass"] for r in rows if r["korpus"] == c and r["text"] == n and r["klass"] in ACTIVE))]
                 for (c, n), k in per_text.most_common(15)]

    def t1(sel=lambda r: True, cap=False):
        u = {"isl": defaultdict(list), "forn": defaultdict(list)}
        for r in rows:
            if r["klass"] in ACTIVE and r["grupp"] in u and sel(r):
                u[r["grupp"]][r["text"]].append(r["klass"] == "högbo")
        if cap:
            u = {g: {t: sorted(set(v)) for t, v in d.items()} for g, d in u.items()}
        F, I = list(u["forn"].values()), list(u["isl"].values())
        nF, nI = sum(map(len, F)), sum(map(len, I))
        out = {"forn_n": nF, "forn_texter": len(F), "isl_n": nI, "isl_texter": len(I)}
        if nF < 10 or nI < 10 or len(F) < 3 or len(I) < 3:
            out["obestämt"] = True
            return out
        sh = lambda us: 100 * sum(sum(x) for x in us) / sum(map(len, us))  # noqa: E731
        rnd = random.Random(SEED)
        d = []
        for _ in range(B):
            a = [F[rnd.randrange(len(F))] for _ in F]
            b = [I[rnd.randrange(len(I))] for _ in I]
            d.append(sh(a) - sh(b))
        out.update({"forn_%": round(sh(F), 1), "isl_%": round(sh(I), 1), "skillnad_pe": round(sh(F) - sh(I), 1),
                    "intervall": ci(d), "p": p_two(d)})
        out["håller"] = out["p"] < 0.05 and not (out["intervall"][0] <= 0 <= out["intervall"][1])
        return out
    res["T1"] = {"huvud": t1(), "bara_A": t1(lambda r: r["monster"] == "A"), "en_per_saga": t1(cap=True)}

    from api.rundata import store
    from src.research_gaps import is_runestone
    res["V3"] = [(r["signum"], m.group(0), (r.get("normalization_ows") or "")[max(0, m.start() - 60): m.end() + 60])
                 for r in store().inscriptions if is_runestone(r)
                 for m in RS_RX.finditer(r.get("normalization_ows") or "")]
    json.dump(res, open(os.path.join(HERE, "matt.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: res[k] for k in ("träffar", "V1", "T1", "V2")}, ensure_ascii=False, indent=1))
    print(len(res["V3"]), "runstensträffar")


if __name__ == "__main__":
    samla() if "--samla" in sys.argv else kontroll() if "--kontroll" in sys.argv else main()
