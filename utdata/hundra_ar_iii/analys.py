"""Hundra år av runfrågor III – måtten M1–M3, M5, M6 enligt analysplaner/2026-11-20-hundra-ar-III.md (låst c5a33b6);
M4 i analys_m4.R. Läser data/cache/hundra_ar_iii/omnamnanden.csv (omnamnanden.py) och skriver
data/cache/hundra_ar_iii/stenar.csv (en rad per runsten, till R) och utdata/hundra_ar_iii/matt.json.
    .venv/bin/python utdata/hundra_ar_iii/analys.py"""
import csv
import json
import os
import re
import sys
from collections import Counter, defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
from api.rundata import store  # noqa: E402
from src import literature  # noqa: E402
from src.research_gaps import is_runestone  # noqa: E402

CACHE = os.path.join(ROOT, "data", "cache", "hundra_ar_iii")
OUT = os.path.join(os.path.dirname(__file__), "matt.json")


def style(r):
    s = (r.get("style") or "").strip()
    if not s or s.startswith("?") or r.get("style_uncertain"):
        return "ingen säker"
    s = re.split(r"\s*-\s*|\s", s)[0].rstrip("?")
    return {"Pr1": "Pr1–Pr2", "Pr2": "Pr1–Pr2"}.get(s, s) if s in ("Pr1", "Pr2", "Pr3", "Pr4", "Pr5", "RAK", "Fp", "KB") else "ingen säker"


def length(r):
    t = r.get("transliteration") or ""
    t = re.sub(r"\([^)]*\)", "", t)
    return len(re.findall(r"[a-zþæøåöäðRʀ]", t, flags=re.I))


def main():
    R = [r for r in store().inscriptions if is_runestone(r)]
    land = Counter(r["signum"].split()[0] for r in R)
    rows = list(csv.DictReader(open(os.path.join(CACHE, "omnamnanden.csv"), encoding="utf-8")))
    J = [x for x in rows if x["source"] != "avhandling"]
    T = [x for x in rows if x["source"] == "avhandling"]
    nj = Counter(x["signum"] for x in J)
    nt = Counter(x["signum"] for x in T)
    out = {"n_stones": len(R), "n_journal_pairs": len(J), "n_thesis_pairs": len(T),
           "n_journal_texts": len({x["text"] for x in J}), "land_stones": dict(land)}

    # M1 per decade (1906–1949 pooled)
    per = defaultdict(list)
    for x in J:
        y = int(x["year"])
        per["1906–1949" if y < 1950 else f"{y // 10 * 10}-talet"].append(x)
    m1 = {}
    for d, xs in per.items():
        c = Counter(x["signum"].split()[0] for x in xs)
        m1[d] = {"texts": len({x["text"] for x in xs}), "pairs": len(xs), "stones": len({x["signum"] for x in xs}),
                 "share": {k: round(c[k] / len(xs), 4) for k in land},
                 "ratio": {k: round((c[k] / len(xs)) / (land[k] / len(R)), 2) for k in land}}
    out["m1"] = m1

    # M2 concentration
    counts = sorted((nj.get(r["signum"], 0) for r in R), reverse=True)
    top = max(1, round(0.05 * len(R)))
    out["m2"] = {"never_journal": sum(1 for c in counts if c == 0), "top5pct_n": top,
                 "top5pct_share": round(sum(counts[:top]) / sum(counts), 4),
                 "median": counts[len(counts) // 2],
                 "top10": [(s, n, next(r["place"] for r in R if r["signum"] == s)) for s, n in nj.most_common(10)],
                 "named_once": sum(1 for c in counts if c == 1)}

    # M3 never named, by group
    def grp(key):
        g = defaultdict(lambda: [0, 0, 0])
        for r in R:
            k = key(r)
            g[k][0] += 1
            g[k][1] += nj.get(r["signum"], 0) == 0
            g[k][2] += nj.get(r["signum"], 0) == 0 and nt.get(r["signum"], 0) == 0
        return {k: {"n": v[0], "never_j": v[1], "never_jt": v[2]} for k, v in sorted(g.items(), key=lambda kv: -kv[1][0])}
    L = [length(r) for r in R]
    q = sorted(L)
    cuts = [q[len(q) // 4], q[len(q) // 2], q[3 * len(q) // 4]]
    quart = lambda n: "Q1" if n <= cuts[0] else "Q2" if n <= cuts[1] else "Q3" if n <= cuts[2] else "Q4"  # noqa: E731
    carver = lambda r: any(c["kind"] in ("S", "A") for c in r["carvers"])  # noqa: E731
    lost = lambda r: bool((r.get("flags") or {}).get("lost"))  # noqa: E731
    out["m3"] = {"landskap": grp(lambda r: r["signum"].split()[0]), "stil": grp(style),
                 "forlorad": grp(lambda r: "förlorad" if lost(r) else "kvar"),
                 "ristare": grp(lambda r: "ristare" if carver(r) else "ingen"),
                 "langd": grp(lambda r: quart(length(r))), "langd_granser": cuts,
                 "alla": grp(lambda r: "alla")}

    # M5 härader
    h = defaultdict(lambda: [0, 0, ""])
    for r in R:
        d = r.get("district") or ""
        if not d:
            continue
        k = f'{r["signum"].split()[0]}|{d}'
        h[k][0] += 1
        h[k][1] += nj.get(r["signum"], 0) == 0
    out["m5"] = sorted([{"landskap": k.split("|")[0], "harad": k.split("|")[1], "n": v[0], "never": v[1]}
                        for k, v in h.items() if v[0] >= 10 and v[1] / v[0] >= 0.8], key=lambda x: -x["n"])
    out["m5_all"] = len([1 for v in h.values() if v[0] >= 10])

    # M6 theses
    cat = [w for w in literature.catalog() if w.get("kind") == "avhandling"]
    by = defaultdict(list)
    for w in cat:
        by[f'{w["year"] // 10 * 10}-talet'].append({"id": w["id"], "author": w["author"], "year": w["year"],
                                                    "title": w["title"], "topic": w.get("topic")})
    th_land = defaultdict(Counter)
    for x in T:
        th_land[x["text"]][x["signum"].split()[0]] += 1
    out["m6"] = {"by_decade": dict(sorted(by.items())), "indexed": {k: dict(v) for k, v in th_land.items()}}

    with open(os.path.join(CACHE, "stenar.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["signum", "landskap", "socken", "stil", "forlorad", "ristare", "langd", "n_j", "n_t"])
        for r in R:
            w.writerow([r["signum"], r["signum"].split()[0], f'{r["signum"].split()[0]}|{r.get("parish") or r["signum"]}',
                        style(r), int(lost(r)), int(carver(r)), length(r), nj.get(r["signum"], 0), nt.get(r["signum"], 0)])
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: out[k] for k in ("n_stones", "n_journal_pairs", "n_thesis_pairs", "n_journal_texts", "m2")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
