"""Jämförelsen i den låsta planen analysplaner/2026-11-02-gamla-granser-statistik.md (sha 13084e18): robusthetstrappan,
ordförrådet och genomsökningen med dagens landskap (korpus FORE) mot de gamla regionerna (korpus EFTER).
    .venv/bin/python utdata/gamla_granser/jamforelse.py FORE EFTER"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
C = os.path.join(ROOT, "data", "cache", "r", "corpus")
fore, efter = sys.argv[1], sys.argv[2]
J = lambda fp, m: json.load(open(os.path.join(C, fp, f"{m}.json"), encoding="utf-8"))  # noqa: E731


def ladder(fp):
    out = {}
    for pid, p in J(fp, "robustness")["patterns"].items():
        rungs = {k: v for k, v in (p.get("rungs") or {}).items() if isinstance(v, dict) and "holds" in v}
        out[pid] = {"every_rung": bool(rungs) and all(v["holds"] for v in rungs.values()),
                    "failing": sorted(k for k, v in rungs.items() if not v["holds"]),
                    "adjusted_or": (rungs.get("adjusted") or {}).get("or"), "adjusted_p": (rungs.get("adjusted") or {}).get("p"),
                    "lopo_without": (rungs.get("lopo") or {}).get("without")}
    return out


a, b = ladder(fore), ladder(efter)
changed = []
for pid in sorted(set(a) | set(b)):
    x, y = a.get(pid), b.get(pid)
    if not x or not y or x["every_rung"] != y["every_rung"] or x["failing"] != y["failing"]:
        changed.append({"pattern": pid, "before": x, "after": y})


def words(fp):
    w = J(fp, "words")
    sig = [r for r in (w.get("region") or []) if r.get("holds")] if isinstance(w.get("region"), list) else []
    return {"n_region_tests": w.get("n_region_tests"), "units": w.get("provinces_tested"), "holds": [(r["word"], r["province"]) for r in sig]}


def scan(fp):
    s = J(fp, "remains").get("scan") or {}
    return {"n_tests": s.get("n_tests"), "n_sig": s.get("n_sig"), "n_replicated": s.get("n_replicated"), "strata": s.get("strata")}


res = {"plan": "analysplaner/2026-11-02-gamla-granser-statistik.md", "before": fore, "after": efter,
       "ladder": {"n": len(b), "every_rung_before": sum(v["every_rung"] for v in a.values()),
                  "every_rung_after": sum(v["every_rung"] for v in b.values()), "changed": changed},
       "words": {"before": words(fore), "after": words(efter)}, "scan": {"before": scan(fore), "after": scan(efter)}}
json.dump(res, open(os.path.join(HERE, "jamforelse.json"), "w"), ensure_ascii=False, indent=1, default=str)
print(json.dumps({k: v for k, v in res["ladder"].items() if k != "changed"}, ensure_ascii=False))
for c in changed:
    print(c["pattern"], "|", c["before"] and (c["before"]["every_rung"], c["before"]["failing"]), "→", c["after"] and (c["after"]["every_rung"], c["after"]["failing"]))
print("ord före", res["words"]["before"]["n_region_tests"], len(res["words"]["before"]["holds"]), "efter", res["words"]["after"]["n_region_tests"], len(res["words"]["after"]["holds"]))
print("ord efter (håller):", res["words"]["after"]["holds"][:40])
print("genomsökning", res["scan"])
