"""Blindprovet och det externa provet för Vitkis ristarförslag (analysplan_forslag.md, punkt 3–4).

Blindprovet: varje runsten med säker ristare i Rundata görs ristarlös medan Stenöversiktens regel räknas
(src/stone_overview.stone), så att ristarnas stilgrupper, bergarter, språkprofiler och landskap räknas utan den;
R-modellens sannolikheter är de korsvaliderade. Förslaget jämförs med Rundatas ristare och med regeln "närmaste
ristare" på samma stenar. Det externa provet jämför förslagen för stenar utan ristare i Rundata 3.1 med Runor 2020.
Skriver utdata/forslag/blindprov.json.
    PYTHONPATH=. .venv/bin/python utdata/forslag/blindprov.py"""
import json
import math
import os
import re
import sys
from collections import Counter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
from scipy.stats import binomtest  # noqa: E402

from api.rundata import store  # noqa: E402
from api.routers.orthography import model as orthography_model  # noqa: E402
from src import stone_overview as so  # noqa: E402
from src.nordic import wilson  # noqa: E402
from src.research_gaps import certain_carvers, has_carver, is_runestone, province  # noqa: E402
from src.signum import fold_signum  # noqa: E402

FP = sys.argv[1] if len(sys.argv) > 1 else "5fdfd1e095bfb6fb"
RDIR = os.path.join(ROOT, "data", "cache", "r", "corpus", FP)
OPEN = json.load(open(os.path.join(RDIR, "attribution.json"), encoding="utf-8"))["open_set"]
THRESHOLD = OPEN["threshold"]
assert THRESHOLD == 0.35

ins = store().inscriptions
m = orthography_model()
ctx = so.context(ins, m, RDIR)
stones = [r for r in ins if is_runestone(r)]
# The final model's first choice for stones of carvers outside its training (within 25 km), as for a carverless stone
small = {x["signum"]: {x["top"]: x["p"]} for x in OPEN["small_carvers"]["stones"]}


def km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


attributed = [r for r in stones if certain_carvers(r)]
located = [(r, (r["lat"], r["lon"])) for r in attributed if r.get("lat") is not None]


def nearest_carver(rec):
    """Ristarna bakom den närmaste andra stenen med säker ristare. Står flera sådana stenar på exakt samma avstånd
    (ofta samma kyrka) räknas alla deras ristare, så att regeln får fördelen av tvivlet."""
    if rec.get("lat") is None:
        return []
    own = (rec["lat"], rec["lon"])
    dist = [(km(own, xy), r) for r, xy in located if r["signum"] != rec["signum"]]
    if not dist:
        return []
    dmin = min(d for d, _ in dist)
    return sorted({c for d, r in dist if d - dmin < 1e-6 for c in certain_carvers(r)})


def blind(rec):
    """Stenöversiktens förslag för stenen med dess egen attribuering dold."""
    saved = rec["carvers"]
    truth = set(certain_carvers(rec))
    home = {c: cnt.copy() for c, cnt in ctx["home"].items()}
    for c in truth:  # the stone's own province no longer counts for its carver
        home[c][province(rec)] -= 1
        if home[c][province(rec)] <= 0:
            del home[c][province(rec)]
    oof = ctx["oof"]
    pred = dict(ctx["pred"])
    if rec["signum"] not in oof and rec["signum"] in small:
        pred[rec["signum"]] = small[rec["signum"]]
    rec["carvers"] = []
    try:
        res = so.stone(rec, {**ctx, "home": home, "pred": pred})
    finally:
        rec["carvers"] = saved
    probs = oof.get(rec["signum"]) or pred.get(rec["signum"]) or {}
    alt = res["alternative"] or {}
    return {"signum": rec["signum"], "province": province(rec), "truth": sorted(truth),
            "signed": any(c["kind"] == "S" and not c["uncertain"] for c in saved),
            "status": res["status"], "suggested": alt.get("carver"), "strength": alt.get("strength"),
            "model_top_p": max(probs.values()) if probs else None,
            "someone_else": (max(probs.values()) < THRESHOLD) if probs else None,
            "nearest": nearest_carver(rec)}


rows = [blind(r) for r in attributed]
universe = ctx["known"] | set(json.load(open(os.path.join(RDIR, "attribution.json"), encoding="utf-8"))["carvers"])


def summary(sel, label):
    n = len(sel)
    right = sum(x["suggested"] in x["truth"] for x in sel)
    hit = lambda x: bool(set(x["nearest"]) & set(x["truth"]))  # noqa: E731
    near = sum(hit(x) for x in sel)
    b = sum(x["suggested"] in x["truth"] and not hit(x) for x in sel)
    c = sum(x["suggested"] not in x["truth"] and hit(x) for x in sel)
    p = binomtest(b, b + c, 0.5).pvalue if b + c else None
    lo, hi = wilson(right, n) if n else (None, None)
    nlo, nhi = wilson(near, n) if n else (None, None)
    return {"label": label, "n": n, "right": right, "precision": right / n if n else None, "ci": [lo, hi],
            "nearest_right": near, "nearest_precision": near / n if n else None, "nearest_ci": [nlo, nhi],
            "vitki_only": b, "nearest_only": c, "mcnemar_p": p}


nytt = [x for x in rows if x["status"] == "nytt förslag"]
mojligt = [x for x in rows if x["status"] == "möjligt förslag"]
out = {
    "plan_sha256": "5ed0b2f3b147aad4be11b9c377ceb5502b7daf92de01f0bcaa9fba8cc9ab14c7", "corpus": FP,
    "n_attributed": len(rows), "n_in_universe": sum(bool(set(x["truth"]) & universe) for x in rows),
    "status_counts": dict(Counter(x["status"] for x in rows)),
    "nytt": summary(nytt, "nytt förslag"),
    "mojligt": summary(mojligt, "möjligt förslag"),
    "nytt_signed": summary([x for x in nytt if x["signed"]], "nytt förslag, signerade"),
    "nytt_model_named": summary([x for x in nytt if x["someone_else"] is False], "nytt förslag, modellen ger ett namn"),
    "nytt_someone_else": summary([x for x in nytt if x["someone_else"] is True], "nytt förslag, kanske någon annan"),
    "nytt_no_model": summary([x for x in nytt if x["someone_else"] is None], "nytt förslag, utan modell"),
    "outside_universe": {"n": sum(not (set(x["truth"]) & universe) for x in rows),
                         "nytt": sum(x["status"] == "nytt förslag" and not (set(x["truth"]) & universe) for x in rows)},
    "by_strength": [summary([x for x in nytt if lo <= x["strength"] < hi], f"{lo}–{hi}")
                    for lo, hi in ((0.5, 0.6), (0.6, 0.7), (0.7, 1.01))],
    "by_province": {p: summary([x for x in nytt if x["province"] == p], p) for p, _ in Counter(x["province"] for x in nytt).most_common()},
    "rows": rows,
}

# ---- the external test: Runor 2020 against Rundata 3.1 -------------------------------------------------------
R = {}
for r in json.load(open(os.path.join(ROOT, "data", "raa", "runor_2020.json"), encoding="utf-8"))["inscriptions"]:
    R.setdefault(fold_signum(r["signum"]), r)
NOT_A_NAME = re.compile(r"^(samma|troligen|eventuellt|antagligen|kanske|möjligen|imitation|tidigare|en |ett )", re.I)
base = lambda n: re.sub(r"\s+\d+$", "", re.sub(r"\s*\(.*?\)", "", n or "")).strip().lower()  # noqa: E731
ext = []
for rec in stones:
    if has_carver(rec):
        continue
    x = R.get(fold_signum(rec["signum"]))
    cs = (x or {}).get("carvers") or []
    names = [c["name"].strip().rstrip(".") for c in cs if isinstance(c, dict) and c.get("name") and not NOT_A_NAME.match(c["name"].strip())]
    if not names:
        continue
    res = so.stone(rec, ctx)
    alt = res["alternative"] or {}
    ext.append({"signum": rec["signum"], "runor": names, "runor_kind": [(c.get("attribution"), c.get("certain")) for c in cs if isinstance(c, dict)],
                "status": res["status"], "suggested": alt.get("carver"), "strength": alt.get("strength"),
                "agrees": bool(alt.get("carver")) and any(base(alt["carver"]) == base(n) for n in names),
                "in_universe": any(base(n) in {base(u) for u in universe} for n in names)})
out["external"] = {"n": len(ext), "in_universe": sum(e["in_universe"] for e in ext),
                   "with_suggestion": sum(e["status"] in ("nytt förslag", "möjligt förslag") for e in ext),
                   "agree_nytt": sum(e["agrees"] and e["status"] == "nytt förslag" for e in ext),
                   "n_nytt": sum(e["status"] == "nytt förslag" for e in ext),
                   "agree_mojligt": sum(e["agrees"] and e["status"] == "möjligt förslag" for e in ext),
                   "n_mojligt": sum(e["status"] == "möjligt förslag" for e in ext), "rows": ext}

json.dump(out, open(os.path.join(ROOT, "utdata", "forslag", "blindprov.json"), "w"), ensure_ascii=False, indent=1)
for k in ("nytt", "mojligt", "nytt_signed", "nytt_model_named", "nytt_someone_else", "nytt_no_model"):
    s = out[k]
    print(f"{s['label']:38} n {s['n']:4}  rätt {s['right']:4} ({(s['precision'] or 0):.2f}, {s['ci'][0] or 0:.2f}–{s['ci'][1] or 0:.2f})"
          f"  närmaste {s['nearest_right']:4} ({(s['nearest_precision'] or 0):.2f})  bara Vitki {s['vitki_only']} bara närmaste {s['nearest_only']}"
          f"  McNemar p {s['mcnemar_p']}")
print("status:", out["status_counts"], "| utanför Vitkis ristare:", out["outside_universe"])
print("efter styrka:", [(s["label"], s["n"], round(s["precision"] or 0, 2)) for s in out["by_strength"]])
print("externt:", {k: v for k, v in out["external"].items() if k != "rows"})
