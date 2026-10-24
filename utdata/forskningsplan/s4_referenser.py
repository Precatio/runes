"""Studie 4: skanningsreferenser för spårläsaren (src/trace_reader.REFS_AUTO) ur protokollmätningen – en per sten, filen
med flest godkända snitt. Södermanland har redan sina i utdata/Rak/referenser_g4."""
import glob, json, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "utdata", "automatisk_korning", "referenser")
os.makedirs(OUT, exist_ok=True)
best = {}
for p in glob.glob(os.path.join(ROOT, "utdata", "automatisk_korning", "*", "*.json")):
    d = json.load(open(p, encoding="utf-8"))
    if "error" in d or not d.get("signum") or d["series"] == "sodermanland":
        continue
    if d["signum"] not in best or d["counts"]["accepted"] > best[d["signum"]]["counts"]["accepted"]:
        best[d["signum"]] = d
for sg, d in best.items():
    folder = {"medelpad": "medelpad", "gravmonument_og_sm": "gravmonument_og_sm"}.get(d["series"], d["series"])
    ref = {"signum": sg, "file": f"{folder}/{d['file']}", "sha256": d["sha256"],
           "parameters": {"normal": d["normal"], "up": d["parameters"].get("up")}}
    json.dump(ref, open(os.path.join(OUT, sg.replace(" ", "_") + ".json"), "w", encoding="utf-8"), ensure_ascii=False)
print(len(best), "referenser")
