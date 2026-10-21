"""Stenöversiktens förslag för runstenar utan ristare i Rundata 3.1 (analysplan_forslag.md, punkt 5), med alla
metodernas besked, R-modellens förstaval och "kanske någon annan", och avstämningen mot Runor 2020 och Wikidata.
Skriver utdata/forslag/nya_forslag.json.
    PYTHONPATH=. .venv/bin/python utdata/forslag/forslagslista.py [korpusversion]"""
import json
import os
import sys
from collections import Counter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
from api.rundata import store  # noqa: E402
from api.routers.orthography import model as orthography_model  # noqa: E402
from src import crosscheck, stone_overview as so  # noqa: E402
from src.research_gaps import has_carver, is_runestone  # noqa: E402

FP = sys.argv[1] if len(sys.argv) > 1 else "5fdfd1e095bfb6fb"
RDIR = os.path.join(ROOT, "data", "cache", "r", "corpus", FP)
THRESHOLD = json.load(open(os.path.join(RDIR, "attribution.json"), encoding="utf-8"))["open_set"]["threshold"]
ins = store().inscriptions
ctx = so.context(ins, orthography_model(), RDIR)
counts, rows = Counter(), []
for r in ins:
    if not is_runestone(r) or has_carver(r):
        continue
    s = so.stone(r, ctx, detail=True)
    counts[s["status"]] += 1
    if s["status"] != "nytt förslag":
        continue
    probs = (s.get("model") or {}).get("probabilities") or {}
    top_p = max(probs.values()) if probs else None
    best = s["alternatives"][0]
    o = s.get("orthography") or {}
    rows.append({"signum": s["signum"], "place": s["place"], "province": s["province"], "lost": bool(r["flags"].get("lost")),
                 "carver": best["carver"], "strength": best["strength"], "model": best["model"], "ortho": best["orthography"],
                 "checks": best["checks"], "check_texts": best.get("check_texts"),
                 "model_top": max(probs, key=probs.get) if probs else None, "model_top_p": top_p,
                 "model_probs": probs, "someone_else": (top_p < THRESHOLD) if top_p is not None else None,
                 "ortho_ranking": o.get("ranking"), "n_words": o.get("n_words"), "ortho_margin": o.get("margin"),
                 "style": r.get("style"), "style_uncertain": r.get("style_uncertain"),
                 "second": s["alternatives"][1]["carver"] if len(s["alternatives"]) > 1 else None,
                 "second_strength": s["alternatives"][1]["strength"] if len(s["alternatives"]) > 1 else None})
rows.sort(key=lambda x: -x["strength"])
cc = crosscheck.check_many([(x["signum"], x["carver"]) for x in rows], workers=4)
for x in rows:
    c = cc.get(x["signum"]) or {}
    x["crosscheck"] = {"status": c.get("status"), "text": (c.get("runor") or {}).get("text"),
                       "references": (c.get("runor") or {}).get("references")}
out = {"corpus": FP, "threshold": THRESHOLD, "counts": dict(counts), "n_unattributed": sum(counts.values()), "rows": rows}
json.dump(out, open(os.path.join(ROOT, "utdata", "forslag", "nya_forslag.json"), "w"), ensure_ascii=False, indent=1)
print("utan ristare:", out["n_unattributed"], dict(counts))
print("nytt förslag:", len(rows), "| kanske någon annan:", sum(x["someone_else"] is True for x in rows),
      "| utan modell:", sum(x["someone_else"] is None for x in rows))
print("ristare:", Counter(x["carver"] for x in rows).most_common())
print("avstämning:", Counter(x["crosscheck"]["status"] for x in rows))
for i, x in enumerate([x for x in rows if x["someone_else"] is not True][:12], 1):
    print(i, x["signum"], x["place"], x["carver"], x["strength"], "| modell", x["model_top"], x["model_top_p"], "| ort",
          (x["ortho_ranking"] or [{}])[0].get("carver"), x["n_words"], "| kontroller", x["checks"], "| förlorad" if x["lost"] else "", "|", x["crosscheck"]["status"])
