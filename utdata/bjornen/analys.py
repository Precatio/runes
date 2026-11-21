"""Björnen – fördjupning 4 i serien Nordiska väsen, enligt analysplaner/2026-11-21-bjornen.md (låst 1779c2e) med den
frysta ordlistan utdata/bjornen/ordlista.csv (sha256 6f79caee…). Samma korpusar som den första väsenstudien.
Träffar med textutdrag i data/cache/bjornen/ (git-ignorerad); här bara summor.

    .venv/bin/python utdata/bjornen/analys.py --grind     # stickproven (term × textgrupp, förvandlingsfönster)
    .venv/bin/python utdata/bjornen/analys.py             # B1–B3, T1, data till T2 (analys_t2.R) → matt.json
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
sys.path.insert(0, os.path.join(ROOT, "utdata", "varlden"))
_spec.loader.exec_module(vasen)

LEX = os.path.join(HERE, "ordlista.csv")
assert hashlib.sha256(open(LEX, "rb").read()).hexdigest().startswith("6f79caee"), "ordlistan är ändrad efter låsningen"
PLAN = os.path.join(ROOT, "analysplaner", "2026-11-21-bjornen.md")
assert hashlib.sha256(open(PLAN, "rb").read()).hexdigest().startswith("863be777"), "planen är ändrad efter låsningen"
TERMS = [dict(r, rx=re.compile(r["regex"])) for r in csv.DictReader(open(LEX, encoding="utf-8"))]
ORDER = [t["term"] for t in TERMS]
TRANS = re.compile(r"\bham(?:r|s|i|inn|rammr|rammir|ramm\w*|hleyp\w*)\b|\b\w*líki\b|\bfylgj(?:u|ur|una|unnar|an)\b")
CACHE = os.path.join(ROOT, "data", "cache", "bjornen")
SEED = 20261121
B = 10000
FOREST = {"Gs", "Hs", "M", "Ån", "J", "D", "Vr", "Sm"}
MALAR = {"U", "Sö", "Vs", "Nä"}
BEAR_NAME = re.compile(r"bj[ôǫöo]rn|bjarn|birn", re.I)
WOLF_NAME = re.compile(r"ulf|úlf", re.I)


def group(c):
    if c == "eddadikter" or c.startswith("snorra_edda"):
        return "Eddan"
    if c.startswith("fornaldarsagor"):
        return "fornaldarsagorna"
    if c.startswith("islanningasagor"):
        return "islänningasagorna"
    if c.startswith("runstenar"):
        return None
    return "övriga"


def collect():
    rows, words, T = [], {}, {}
    for c, n, t in vasen.texts():
        T[(c, n)] = t
        words[(c, n)] = len(t.split())
        found = []
        for term in TERMS:
            for m in term["rx"].finditer(t):
                found.append((m.start(), ORDER.index(term["term"]), term["term"], m.group(0)))
        seen = set()
        for pos, _, term, w in sorted(found):
            if pos in seen:
                continue
            seen.add(pos)
            win = " ".join(t[:pos].split()[-25:] + t[pos:].split()[1:26])
            win10 = " ".join(t[:pos].split()[-10:] + t[pos:].split()[1:11])
            rows.append({"korpus": c, "grupp": group(c), "text": n, "term": term, "ord": w, "pos": pos,
                         "trans": bool(TRANS.search(win)), "trans10": bool(TRANS.search(win10)),
                         "kwic": t[max(0, pos - 80): pos + 80].replace("\n", " "), "win": win})
    return rows, words, T


def grind():
    rows, _, _ = collect()
    os.makedirs(CACHE, exist_ok=True)
    rnd = random.Random(SEED)
    by = defaultdict(list)
    for r in rows:
        if r["grupp"]:
            by[(r["term"], r["grupp"])].append(r)
    with open(os.path.join(CACHE, "grind.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["nr", "term", "grupp", "text", "ord", "kwic"])
        w.writeheader()
        i = 0
        for key in sorted(by):
            for r in (rnd.sample(by[key], 8) if len(by[key]) > 8 else by[key]):
                i += 1
                w.writerow({"nr": i, "term": r["term"], "grupp": r["grupp"], "text": r["text"], "ord": r["ord"], "kwic": r["kwic"]})
    tw = [r for r in rows if r["trans"]]
    with open(os.path.join(CACHE, "grind_forvandling.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["nr", "grupp", "text", "ord", "win"])
        w.writeheader()
        for i, r in enumerate(rnd.sample(tw, min(20, len(tw))), 1):
            w.writerow({"nr": i, "grupp": r["grupp"], "text": r["text"], "ord": r["ord"], "win": r["win"]})
    print({f"{k[0]}|{k[1]}": len(v) for k, v in sorted(by.items())}, "totalt", len(rows), "förvandling", len(tw))


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
    dropped = {tuple(x) for x in gate.get("utan_test", [])}  # [term, grupp]
    corpora = list(dict.fromkeys(c for c, _ in words))
    res = {"träffar": len(rows), "grind": gate}
    res["B1"] = {c: dict(Counter(r["term"] for r in rows if r["korpus"] == c).most_common()) for c in corpora}
    res["B1_per_10000"] = {c: round(1e4 * sum(1 for r in rows if r["korpus"] == c) / sum(n for (cc, _), n in words.items() if cc == c), 2)
                           for c in corpora}
    res["B2_isbjörn"] = [(r["korpus"], r["text"], r["ord"]) for r in rows if r["term"] == "isbjörn"]
    res["förvandling_per_grupp"] = {g: {"n": sum(1 for r in rows if r["grupp"] == g),
                                        "förvandling": sum(1 for r in rows if r["grupp"] == g and r["trans"])}
                                    for g in ("Eddan", "fornaldarsagorna", "islänningasagorna", "övriga")}
    res["förvandling_texter"] = Counter(f"{r['grupp']}|{r['text']}" for r in rows if r["trans"]).most_common(15)

    # T1
    def t1(key="trans"):
        u = {"fornaldarsagorna": defaultdict(list), "islänningasagorna": defaultdict(list)}
        for r in rows:
            if r["grupp"] in u and (r["term"], r["grupp"]) not in dropped:
                u[r["grupp"]][r["text"]].append(r[key])
        F, I = list(u["fornaldarsagorna"].values()), list(u["islänningasagorna"].values())
        nF, nI = sum(map(len, F)), sum(map(len, I))
        out = {"fornaldar_n": nF, "fornaldar_texter": len(F), "islänninga_n": nI, "islänninga_texter": len(I)}
        if nF < 15 or nI < 15:
            out["obestämt"] = True
            return out
        sh = lambda us: 100 * sum(sum(x) for x in us) / sum(map(len, us))  # noqa: E731
        rnd = random.Random(SEED)
        d = [a - b for a, b in zip(boot(F, sh, rnd), boot(I, sh, rnd))]
        out.update({"fornaldar_%": round(sh(F), 1), "islänninga_%": round(sh(I), 1), "skillnad_pe": round(sh(F) - sh(I), 1),
                    "intervall": ci(d), "p": p_two(d)})
        return out
    res["T1"] = {"huvud": t1("trans"), "fönster_10": t1("trans10")}

    # B3 + data till T2
    from api.rundata import store
    from src.research_gaps import PROVINCE_NAMES, is_runestone
    land = json.load(open(os.path.join(ROOT, "web", "public", "geo", "sten_land.json"), encoding="utf-8"))

    def names(r):
        return re.findall(r'"([^\s,.;:()\[\]"]+)', (r.get("normalization_ows") or "").replace("[", "").replace("]", ""))
    stones = [r for r in store().inscriptions if is_runestone(r)]
    out_rows, bear_forms = [], Counter()
    for r in stones:
        nm = names(r)
        bear = [n for n in nm if BEAR_NAME.search(n)]
        bear_forms.update(bear)
        prov = r["signum"].split()[0]
        out_rows.append({"signum": r["signum"], "landskap": prov, "region": land.get(r["signum"], prov),
                         "harad": (r.get("district") or "").strip() or f"?{prov}", "namn": len(nm),
                         "bjorn": int(bool(bear)), "varg": int(any(WOLF_NAME.search(n) for n in nm)),
                         "grupp": "skog" if prov in FOREST else "malar" if prov in MALAR else "annat"})
    os.makedirs(CACHE, exist_ok=True)
    with open(os.path.join(CACHE, "stenar.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0]))
        w.writeheader()
        w.writerows(out_rows)
    by_prov = defaultdict(lambda: [0, 0, 0])
    for o in out_rows:
        by_prov[o["landskap"]][0] += 1
        by_prov[o["landskap"]][1] += o["bjorn"]
        by_prov[o["landskap"]][2] += o["varg"]
    res["B3_landskap"] = {PROVINCE_NAMES.get(k, k): {"stenar": v[0], "björnnamn": v[1], "andel": round(100 * v[1] / v[0], 1),
                                                     "vargnamn": v[2], "varg_andel": round(100 * v[2] / v[0], 1)}
                          for k, v in sorted(by_prov.items(), key=lambda x: -x[1][0]) if v[0] >= 20}
    res["B3_totalt"] = {"stenar": len(out_rows), "björnnamn": sum(o["bjorn"] for o in out_rows),
                        "vargnamn": sum(o["varg"] for o in out_rows)}
    res["B3_former"] = bear_forms.most_common(25)
    for g in ("skog", "malar"):
        xs = [o for o in out_rows if o["grupp"] == g]
        res[f"B3_{g}"] = {"stenar": len(xs), "björnnamn": sum(o["bjorn"] for o in xs),
                          "andel": round(100 * sum(o["bjorn"] for o in xs) / len(xs), 1)}
    json.dump(res, open(os.path.join(HERE, "matt.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: res[k] for k in ("B1_per_10000", "förvandling_per_grupp", "T1", "B3_totalt", "B3_skog", "B3_malar")},
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    grind() if "--grind" in sys.argv else main()
