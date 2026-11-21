"""Nornorna, diserna och valkyriorna – fördjupning 6 i serien Nordiska väsen, enligt analysplaner/2026-11-21-diserna.md
(låst 63420aa). Litteraturen: samma korpusar som den första väsenstudien; runstenarna: personmodulen.

    .venv/bin/python utdata/diserna/analys.py --samla      # litteraturträffar → data/cache/diserna/traffar.csv
    .venv/bin/python utdata/diserna/analys.py --kontroll   # 40 stratifierade för blind omklassning
    .venv/bin/python utdata/diserna/analys.py              # D1–D3, D5, data till T1 (analys_t1.R) → matt.json
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

PLAN = os.path.join(ROOT, "analysplaner", "2026-11-21-diserna.md")
assert hashlib.sha256(open(PLAN, "rb").read()).hexdigest().startswith("2319c152"), "planen är ändrad efter låsningen"
TERMS = [("dís", re.compile(r"\bdís(?:ir|a|um|ar|ablót\w*|arsal\w*)?\b")),
         ("norn", re.compile(r"\bnorn(?:ir|a|um|ar|ina|irnar|agest\w*)?\b")),
         ("valkyrja", re.compile(r"\bvalkyrj\w*|\bvalkyri\w*")),
         ("fylgja", re.compile(r"\bfylgj(?:u|ur|una|unnar|unni|urnar|an|ukon\w*)\b")),
         ("spákona", re.compile(r"\bspá(?:kon|dís)\w*"))]
NAMED = re.compile(r"\b(?:Urð(?:r|ar)?|Verðand\w*|Skuld|Skögul\w*|Göndul\w*|Hrist|Mist|Sigrdríf\w*)\b")
CLASSES = {"dís", "norn", "valkyria", "fylgja", "kvinna", "kult", "spåkvinna", "annat"}
CACHE = os.path.join(ROOT, "data", "cache", "diserna")
SEED = 20261121
SVEA = {"U", "Sö", "Vs", "Nä"}
GOTA = {"Ög", "Vg", "Sm", "Öl", "Bo", "Ds"}


def group(c):
    if c == "eddadikter" or c.startswith("snorra_edda"):
        return "Eddan"
    if c.startswith("runstenar"):
        return None
    return "sagorna"


def texts():
    return [(c, n, t) for c, n, t in vasen.texts()]


def samla():
    os.makedirs(CACHE, exist_ok=True)
    rows = []
    for c, n, t in texts():
        if c.startswith("runstenar"):
            continue
        found = sorted((m.start(), term, m.group(0)) for term, rx in TERMS for m in rx.finditer(t))
        seen = set()
        for pos, term, w in found:
            if pos in seen:
                continue
            seen.add(pos)
            rows.append({"id": f"{c}|{n}|{pos}", "korpus": c, "grupp": group(c), "text": n, "term": term, "form": w,
                         "kwic": t[max(0, pos - 110): pos + 110].replace("\n", " ")})
    with open(os.path.join(CACHE, "traffar.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(len(rows), Counter((r["grupp"], r["term"]) for r in rows))


def kontroll():
    rows = list(csv.DictReader(open(os.path.join(CACHE, "traffar.csv"), encoding="utf-8")))
    by = defaultdict(list)
    for r in rows:
        by[(r["term"], r["grupp"])].append(r)
    rnd = random.Random(SEED)
    per = max(1, 40 // len(by))
    pick = []
    for k in sorted(by):
        pick += rnd.sample(by[k], min(per, len(by[k])))
    rest = [r for r in rows if r not in pick]
    pick += rnd.sample(rest, max(0, 40 - len(pick)))
    with open(os.path.join(CACHE, "kontroll_blind.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "form", "kwic"])
        w.writeheader()
        for r in pick[:40]:
            w.writerow({"id": r["id"], "form": r["form"], "kwic": r["kwic"]})
    print(len(pick[:40]))


def main():
    rows = list(csv.DictReader(open(os.path.join(CACHE, "traffar.csv"), encoding="utf-8")))
    cls = {r["id"]: r["klass"] for r in csv.DictReader(open(os.path.join(CACHE, "klassning.csv"), encoding="utf-8"))}
    assert set(cls) == {r["id"] for r in rows} and set(cls.values()) <= CLASSES
    for r in rows:
        r["klass"] = cls[r["id"]]
    words = {(c, n): len(t.split()) for c, n, t in texts()}
    corpora = list(dict.fromkeys(c for c, _ in words if not c.startswith("runstenar")))
    res = {"träffar": len(rows)}
    res["D1"] = {c: dict(Counter(r["klass"] for r in rows if r["korpus"] == c).most_common()) for c in corpora}
    res["D1_per_10000"] = {c: round(1e4 * sum(1 for r in rows if r["korpus"] == c and r["klass"] in ("dís", "norn", "valkyria", "fylgja", "kult"))
                                    / sum(n for (cc, _), n in words.items() if cc == c), 2) for c in corpora}
    res["D1_grupp"] = {g: dict(Counter(r["klass"] for r in rows if r["grupp"] == g).most_common()) for g in ("Eddan", "sagorna")}
    res["D2_kult"] = [(r["korpus"], r["text"], r["form"]) for r in rows if r["klass"] == "kult"]
    named = Counter()
    for c, n, t in texts():
        if group(c) == "Eddan":
            named.update(m.group(0) for m in NAMED.finditer(t))
    res["D3_namn_eddan"] = named.most_common()

    # Runstenarna: kvinnorna och -dís
    from api.rundata import store
    from src import entities, people
    from src.research_gaps import PROVINCE_NAMES, is_runestone
    recs = store().inscriptions
    lex = people.lexicon(recs)
    out = []
    for r in recs:
        if not is_runestone(r):
            continue
        prov = r["signum"].split()[0]
        grp = "svealand" if prov in SVEA else "gotaland" if prov in GOTA else "annat"
        text = people._text_genders(r)
        for p in entities.extract(r)["persons"]:
            g = people.gender(p["name"], text, lex)
            if g != "k":
                continue
            out.append({"signum": r["signum"], "landskap": prov, "grupp": grp,
                        "harad": (r.get("district") or "").strip() or f"?{prov}", "namn": p["name"],
                        "dis": int(bool(re.search("dís", p["name"], re.I))), "kon_ur_text": int(p["name"] in text)})
    os.makedirs(CACHE, exist_ok=True)
    with open(os.path.join(CACHE, "kvinnor.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    res["D5"] = {"kvinnor": len(out), "dis_kvinnor": sum(o["dis"] for o in out),
                 "dis_namn": Counter(o["namn"] for o in out if o["dis"]).most_common(20),
                 "per_landskap": {PROVINCE_NAMES.get(k, k): {"kvinnor": v, "dis": sum(o["dis"] for o in out if o["landskap"] == k)}
                                  for k, v in Counter(o["landskap"] for o in out).most_common() if v >= 20},
                 "svealand": {"kvinnor": sum(1 for o in out if o["grupp"] == "svealand"), "dis": sum(o["dis"] for o in out if o["grupp"] == "svealand")},
                 "gotaland": {"kvinnor": sum(1 for o in out if o["grupp"] == "gotaland"), "dis": sum(o["dis"] for o in out if o["grupp"] == "gotaland")}}
    json.dump(res, open(os.path.join(HERE, "matt.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: res[k] for k in ("D1_grupp", "D2_kult", "D3_namn_eddan", "D5")}, ensure_ascii=False, indent=1)[:3500])


if __name__ == "__main__":
    samla() if "--samla" in sys.argv else kontroll() if "--kontroll" in sys.argv else main()
