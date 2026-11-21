"""Jättarna – fördjupning 3 i serien Nordiska väsen, enligt analysplaner/2026-11-21-jattarna.md (låst d57af06) med den
frysta ordlistan utdata/jattarna/ordlista.csv (sha256 ce1e6dd8…). Samma korpusar som den första väsenstudien.
Träffar med textutdrag i data/cache/jattarna/ (git-ignorerad); här bara summor.

    .venv/bin/python utdata/jattarna/analys.py --grind     # stickprovet till kvalitetsgrinden
    .venv/bin/python utdata/jattarna/analys.py             # J1–J5, T2–T3 → utdata/jattarna/matt.json
"""
import csv
import glob
import hashlib
import html
import json
import os
import random
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "utdata", "vasen"))
import analys as vasen  # noqa: E402

LEX = os.path.join(HERE, "ordlista.csv")
assert hashlib.sha256(open(LEX, "rb").read()).hexdigest().startswith("ce1e6dd8"), "ordlistan är ändrad efter låsningen"
PLAN = os.path.join(ROOT, "analysplaner", "2026-11-21-jattarna.md")
assert hashlib.sha256(open(PLAN, "rb").read()).hexdigest().startswith("79c2089a"), "planen är ändrad efter låsningen"
TERMS = [dict(r, rx=re.compile(r["regex"])) for r in csv.DictReader(open(LEX, encoding="utf-8"))]
ORDER = [t["term"] for t in TERMS]
CACHE = os.path.join(ROOT, "data", "cache", "jattarna")
SEED = 20261121
B = 10000
NORTH = re.compile(r"\bnorð(?:r|ur|an|ar)\b")
EAST = re.compile(r"\baust(?:r|ur|an|ar)\b")


def group(c):
    if c == "eddadikter" or c.startswith("snorra_edda"):
        return "Eddan"
    if c.startswith("runstenar"):
        return None
    return "sagorna"


def collect():
    rows, words, T = [], {}, {}
    for c, n, t in vasen.texts():
        T[(c, n)] = t
        words[(c, n)] = len(t.split())
        found = []
        for term in TERMS:
            for m in term["rx"].finditer(t):
                found.append((m.start(), ORDER.index(term["term"]), term, m.group(0)))
        seen = set()
        for pos, _, term, w in sorted(found):
            if pos in seen:
                continue
            seen.add(pos)
            rows.append({"korpus": c, "text": n, "term": term["term"], "kon": term["kon"], "ord": w, "pos": pos,
                         "kwic": t[max(0, pos - 70): pos + 70].replace("\n", " ")})
    return rows, words, T


def grind():
    rows, _, _ = collect()
    os.makedirs(CACHE, exist_ok=True)
    rnd = random.Random(SEED)
    by = defaultdict(list)
    for r in rows:
        by[r["term"]].append(r)
    with open(os.path.join(CACHE, "grind.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["nr", "term", "korpus", "text", "ord", "kwic"])
        w.writeheader()
        i = 0
        for term in ORDER:
            for r in (rnd.sample(by[term], 10) if len(by[term]) > 10 else by[term]):
                i += 1
                w.writerow({"nr": i, **{k: r[k] for k in ("term", "korpus", "text", "ord", "kwic")}})
    print({t: len(by[t]) for t in ORDER}, "totalt", len(rows))


def boot(units, stat, rnd):
    return [stat([units[rnd.randrange(len(units))] for _ in units]) for _ in range(B)]


def ci(xs):
    s = sorted(x for x in xs if x is not None)
    return [round(s[int(0.025 * len(s))], 1), round(s[int(0.975 * len(s)) - 1], 1)]


def p_two(xs, null=0.0):
    xs = [x for x in xs if x is not None]
    lo = sum(1 for x in xs if x <= null) / len(xs)
    hi = sum(1 for x in xs if x >= null) / len(xs)
    return min(1.0, 2 * min(lo, hi))


def main():
    rows, words, T = collect()
    gate = json.load(open(os.path.join(HERE, "grind_resultat.json"), encoding="utf-8"))
    dropped = set(gate.get("termer_utan_test", []))
    corpora = list(dict.fromkeys(c for c, _ in words))
    res = {"träffar": len(rows), "grind": gate}

    # J1
    res["J1"] = {c: dict(Counter(r["term"] for r in rows if r["korpus"] == c).most_common()) for c in corpora}
    res["J1_per_10000"] = {c: round(1e4 * sum(1 for r in rows if r["korpus"] == c) / sum(n for (cc, _), n in words.items() if cc == c), 2)
                           for c in corpora}
    # J2
    res["J2_risi_andel"] = {}
    for c in corpora:
        k = Counter(r["term"] for r in rows if r["korpus"] == c)
        tot = k["jötunn"] + k["þurs"] + k["risi"]
        res["J2_risi_andel"][c] = {"risi": k["risi"], "av": tot, "procent": round(100 * k["risi"] / tot, 1) if tot else None}
    # J3
    res["J3_namn"] = {"jättar": Counter(r["ord"] for r in rows if r["term"] == "namngiven jätte").most_common(20),
                      "jättinnor": Counter(r["ord"] for r in rows if r["term"] == "namngiven jättinna").most_common(20)}
    # J4
    res["J4_runstenar"] = [(r["text"], r["ord"]) for r in rows if r["korpus"].startswith("runstenar")]
    # J5
    res["J5_kandidater"] = sol_candidates()
    p = os.path.join(HERE, "j5_lasning.json")
    res["J5_lasning"] = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None

    # T2, T3
    def units(kind, skip_troll=False, k=25, only=None):
        u = {"Eddan": defaultdict(list), "sagorna": defaultdict(list)}
        for r in rows:
            g = group(r["korpus"])
            if g is None or r["term"] in dropped or (skip_troll and r["term"] == "tröll"):
                continue
            if only and g == "sagorna" and not r["korpus"].startswith(only):
                continue
            key = (r["korpus"], r["text"])
            if kind == "kon":
                u[g][key].append(r["kon"] == "f")
            else:
                t = T[key]
                win = " ".join(t[:r["pos"]].split()[-k:] + t[r["pos"]:].split()[1:k + 1])
                n, e = bool(NORTH.search(win)), bool(EAST.search(win))
                if n or e:
                    u[g][key].append(n and not e if (n != e) else None)  # both: counted as neither
        out = {}
        for g in u:
            for key in list(u[g]):
                u[g][key] = [x for x in u[g][key] if x is not None]
                if not u[g][key]:
                    del u[g][key]
        return list(u["Eddan"].values()), list(u["sagorna"].values())

    def share(us):
        n = sum(map(len, us))
        return 100 * sum(sum(x) for x in us) / n if n else None

    def test(kind, **kw):
        E, S = units(kind, **kw)
        nE, nS = sum(map(len, E)), sum(map(len, S))
        out = {"Eddan_n": nE, "Eddan_texter": len(E), "sagorna_n": nS, "sagorna_texter": len(S)}
        if kind == "riktning" and (nE < 20 or nS < 20):
            out["obestämt"] = True
            return out
        rnd = random.Random(SEED)
        bE, bS = boot(E, share, rnd), boot(S, share, rnd)
        d = [a - b for a, b in zip(bE, bS) if a is not None and b is not None]
        out.update({"Eddan_%": round(share(E), 1), "sagorna_%": round(share(S), 1), "skillnad_pe": round(share(E) - share(S), 1),
                    "intervall": ci(d), "p": p_two(d)})
        return out

    def holm(t2, t3):
        ps = sorted((x["p"], name) for name, x in (("T2", t2), ("T3", t3)) if "p" in x)
        prev = 0.0
        for j, (p, name) in enumerate(ps):
            adj = max(prev, min(1.0, (len(ps) - j) * p))
            prev = adj
            x = t2 if name == "T2" else t3
            lo, hi = x["intervall"]
            x["p_holm"] = round(adj, 4)
            x["håller"] = adj < 0.05 and not (lo <= 0 <= hi)

    res["tester"] = {}
    for name, kw in (("huvud", {}), ("utan_tröll", {"skip_troll": True}), ("fönster_10", {"k": 10}),
                     ("bara_fornaldar", {"only": "fornaldarsagor"}), ("bara_islanninga", {"only": "islanningasagor"})):
        t2 = test("kon", **{k: v for k, v in kw.items() if k != "k"})
        t3 = test("riktning", **kw)
        holm(t2, t3)
        res["tester"][name] = {"T2_kvinnor": t2, "T3_norr": t3}
    json.dump(res, open(os.path.join(HERE, "matt.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"J1_per_10000": res["J1_per_10000"], "tester": res["tester"]["huvud"]}, ensure_ascii=False, indent=1))


def sol_candidates():
    rx = re.compile(r"\bjätt\w*|\btroll\w*|\btursa?\w*|\bres(?:e|ar|en)\b", re.I)
    out = []
    for f in sorted(glob.glob("/Volumes/2TB/Antigrvity/Runes/downloads/asatro/isof_sol/_namn_ortnamn_sol_ortnamnslexikon_*.html")):
        txt = html.unescape(re.sub(r"<[^>]+>", "\n", open(f, encoding="utf-8").read()))
        for para in re.split(r"\n\s*\n", txt):
            p = " ".join(para.split())
            for m in rx.finditer(p):
                out.append({"huvud": p[:70], "ord": m.group(0), "kontext": p[max(0, m.start() - 200): m.end() + 150]})
    return out


if __name__ == "__main__":
    grind() if "--grind" in sys.argv else main()
