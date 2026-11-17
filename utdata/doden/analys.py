"""Den goda döden: hur de svenska runstenarna berättar om döden (låst plan analysplaner/2026-11-17-den-goda-doden.md,
sha256 b4066e18). Kodningen först (--kodning skriver bara kodning.csv), sedan del A och proven B1–B2.
    .venv/bin/python utdata/doden/analys.py --kodning
    .venv/bin/python utdata/doden/analys.py"""
import collections
import csv
import hashlib
import json
import math
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
from src import nordic, question  # noqa: E402

PLAN = os.path.join(ROOT, "analysplaner", "2026-11-17-den-goda-doden.md")
SHA = hashlib.sha256(open(PLAN, "rb").read()).hexdigest()
assert SHA.startswith("b4066e18"), SHA
OUT = os.path.dirname(os.path.abspath(__file__))

# ---- the coding (plan: "Kodningen av döden") ---------------------------------------------------------------------------
VERB = re.compile(r"\b(died|drowned|killed|slain|fell|betrayed|burned|burnt|perished|murdered|met (?:his|their) end|"
                  r"lost his life|was dead|were dead|was sick|from sickness)\b", re.I)
MANNER = [("våld", re.compile(r"\b(killed|slain|murdered|fell|betrayed|burned|burnt)\b", re.I)),
          ("drunknad", re.compile(r"\bdrowned\b", re.I)),
          ("sjukdom", re.compile(r"\b(sick|sickness)\b", re.I)),
          ("dopkläder", re.compile(r"\bchristening robes\b", re.I)),
          ("utan sätt", re.compile(r"\b(died|perished|met (?:his|their) end|lost his life|was dead|were dead)\b", re.I))]
# The event is not the commemorated dead's own death (plan): read one by one
NOT_THE_DEAD = {
    "Ög 136": "Röks text: hjältarna i sagan, inte Varins son",
    "Sö 196": "den döde dödade Ôzurr; hans egen död nämns inte",
    "Vg 202": "inte en runsten (dörrbeslag)",
}


def manner(tr: str) -> tuple[str, str] | None:
    """The first death the text describes: (manner, the words), or None. The manner follows the plan's order, read
    in the sentence where the first death verb stands."""
    m = VERB.search(tr)
    if not m:
        return None
    # the sentence (or clause) around the first death verb
    start = max(tr.rfind(".", 0, m.start()), tr.rfind("§", 0, m.start())) + 1
    end = min([i for i in (tr.find(".", m.end()), tr.find("§", m.end())) if i >= 0] or [len(tr)])
    sent = tr[start:end].strip()
    for k, rx in MANNER:
        if rx.search(sent):
            return k, sent
    return "utan sätt", sent


def code(recs):
    rows = []
    for r in recs:
        tr = re.sub(r"\s+", " ", r.get("translation_en") or "")
        got = manner(tr)
        if not got:
            continue
        reason = NOT_THE_DEAD.get(r["signum"])
        k, sent = got
        rows.append({"signum": r["signum"], "sätt": "" if reason else k, "räknas": 0 if reason else 1,
                     "osäker": int(bool(re.search(r"\b(fell|died|killed|drowned)\(\?\)|\(\?\) ?(fell|died)", sent))),
                     "utomlands": (nordic.features(r) or {}).get("fard", 0), "citat": sent[:220], "skäl": reason or ""})
    return rows


def wilson(k, n, z=1.96):
    if n == 0:
        return [None, None]
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(c - h, 4), round(c + h, 4)]


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    adj, run = [0.0] * len(ps), 0.0
    for rank, i in enumerate(order):
        run = max(run, min(1.0, (len(ps) - rank) * ps[i]))
        adj[i] = run
    return adj


def main():
    D = json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["inscriptions"]
    se = [r for r in D if nordic.is_runestone(r) and nordic.land_of(r) == "sverige"]
    assert len(se) == 2321, len(se)
    text = [r for r in se if nordic.features(r) is not None]
    rows = code(se)
    with open(os.path.join(OUT, "kodning.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("kodade:", len(rows), "räknas:", sum(x["räknas"] for x in rows),
          collections.Counter(x["sätt"] for x in rows if x["räknas"]))
    if "--kodning" in sys.argv:
        return

    told = {x["signum"]: x for x in rows if x["räknas"]}
    prov = lambda r: r["signum"].split()[0]  # noqa: E731
    res = {"sha": SHA[:8], "stenar": len(se), "med_text": len(text)}

    # ---- A. descriptive
    k = sum(1 for r in text if r["signum"] in told)
    res["A_andel"] = {"k": k, "n": len(text), "andel": round(k / len(text), 4), "ci": wilson(k, len(text))}
    per = collections.defaultdict(lambda: [0, 0])
    for r in text:
        per[prov(r)][1] += 1
        per[prov(r)][0] += r["signum"] in told
    res["A_landskap"] = {p: {"k": a, "n": n, "andel": round(a / n, 4), "ci": wilson(a, n)}
                         for p, (a, n) in sorted(per.items(), key=lambda x: -x[1][1]) if n >= 30}
    by = collections.defaultdict(list)
    for s, x in told.items():
        by[x["sätt"]].append(s)
    res["A_satt"] = {m: {"n": len(v), "utomlands": sum(told[s]["utomlands"] for s in v),
                         "osakra": sum(told[s]["osäker"] for s in v), "signa": sorted(v)} for m, v in by.items()}

    # ---- the halves (the same parish halves as Pröva en egen fråga)
    prep_rows = [{"signum": r["signum"], "province": prov(r), "parish": r.get("parish"), "style": r.get("style"),
                  "dating": r.get("dating")} for r in text]
    try:
        half = question.halves(prep_rows)
    except Exception:  # mid_year reads the record's own fields; fall back to the records themselves
        half = question.halves([{**r, "province": prov(r)} for r in text])

    def b1(sub):
        strata = collections.defaultdict(lambda: [0, 0, 0, 0])
        a_ = b_ = c_ = d_ = 0
        for r in sub:
            x = told.get(r["signum"])
            if not x:
                continue
            ft = nordic.features(r)
            praise = int(bool(ft["praise"] or ft["titel"]))
            viol = x["sätt"] == "våld"
            idx = (0 if praise else 1) if viol else (2 if praise else 3)
            if viol:
                a_, b_ = a_ + praise, b_ + (1 - praise)
            else:
                c_, d_ = c_ + praise, d_ + (1 - praise)
            t = nordic.bin_of(nordic.year_of(r))
            if t:
                strata[t][idx] += 1
        or_, p, used = nordic.mantel_haenszel([tuple(v) for v in strata.values()])
        return {"vald_berom": a_, "vald_n": a_ + b_, "ovriga_berom": c_, "ovriga_n": c_ + d_,
                "or_mh": or_, "p_mh": p, "skikt": used, "per_skikt": {k: v for k, v in strata.items()}}

    def b2(sub):
        strata = collections.defaultdict(lambda: [0, 0, 0, 0])
        no_year = 0
        for r in sub:
            t = nordic.bin_of(nordic.year_of(r))
            if t is None:
                no_year += 1
                continue
            late = t == "sen"
            y = int(r["signum"] in told)
            idx = (0 if y else 1) if late else (2 if y else 3)
            strata[prov(r)][idx] += 1
        or_, p, used = nordic.mantel_haenszel([tuple(v) for v in strata.values()])
        tot = [sum(v[i] for v in strata.values()) for i in range(4)]
        return {"sen_k": tot[0], "sen_n": tot[0] + tot[1], "tidig_k": tot[2], "tidig_n": tot[2] + tot[3],
                "or_mh": or_, "p_mh": p, "landskap": used, "utan_ar": no_year}

    from scipy.stats import fisher_exact
    B1, B2 = b1(text), b2(text)
    B1["fisher_p"] = float(fisher_exact([[B1["vald_berom"], B1["vald_n"] - B1["vald_berom"]],
                                         [B1["ovriga_berom"], B1["ovriga_n"] - B1["ovriga_berom"]]])[1])
    adj = holm([B1["p_mh"], B2["p_mh"]])
    B1["p_holm"], B2["p_holm"] = adj
    for key, fn, B in (("B1", b1, B1), ("B2", b2, B2)):
        B["halvor"] = {h: fn([r for r in text if half.get(r["signum"]) == h]) for h in ("A", "B")}
    B2["utan_U"] = b2([r for r in text if prov(r) != "U"])

    def holds_half(B, h, key):
        x = B["halvor"][h]
        same = x["or_mh"] is not None and (x["or_mh"] > 1) == (B["or_mh"] > 1)
        small = (x["vald_berom"] + x["ovriga_berom"] < 10) if key == "B1" else (x["sen_k"] + x["tidig_k"] < 10)
        return bool(same and (small or (x["p_mh"] is not None and x["p_mh"] < 0.05)))

    for key, B in (("B1", B1), ("B2", B2)):
        B["haller_halvor"] = all(holds_half(B, h, key) for h in ("A", "B"))
        B["haller"] = bool(B["p_holm"] < 0.05 and B["haller_halvor"])
    B2["utan_U_samma_riktning"] = B2["utan_U"]["or_mh"] is not None and (B2["utan_U"]["or_mh"] > 1) == (B2["or_mh"] > 1)
    res["B1"], res["B2"] = B1, B2
    json.dump(res, open(os.path.join(OUT, "resultat.json"), "w"), ensure_ascii=False, indent=1, default=float)
    print(json.dumps({k: v for k, v in res.items() if k not in ("A_landskap",)}, ensure_ascii=False, indent=1, default=float)[:4000])


if __name__ == "__main__":
    main()
