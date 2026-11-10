"""Skriver /Volumes/2TB/Antigrvity/Runes/zenodo/dataset/OVERSIKT.md: en tabell över rapporternas Zenodo-dataset (antal
filer, storlek, licens, det som lämnats utanför och öppna licensfrågor) ur det senaste bygget (build.py).

    python3 scripts/zenodo_dataset/oversikt.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build import OUT, SUMMARY  # noqa: E402
from spec import TP  # noqa: E402

res = json.load(open(SUMMARY, encoding="utf-8"))
def human(n): return f"{n/1024/1024:.1f} MB" if n >= 1024*1024 else f"{n/1024:.0f} kB"
L = ["# Zenodo datasets for the research reports – overview", "",
     "Prepared 2026-11-10 (local only; nothing uploaded). One folder per report archived on Zenodo "
     "(web/content/report_dois.json). Each folder: `README.md`, `MANIFEST.json`, `zenodo_metadata.json`, "
     "`data_and_code.zip` (upload this with README.md and MANIFEST.json) and `repo/` (the same files unpacked, for review).", "",
     "| Report (slug) | Files | Size (files) | Zip | Licence | Excluded (besides the article builder and figures) | Licence uncertainties |",
     "|---|---|---|---|---|---|---|"]
tot = 0
for r in res:
    tot += r["bytes"]
    exc = "; ".join(x.split(":")[0] for x in r["excluded"][1:]) or "–"
    unc = []
    for u in r["uncertain"]:
        if u.startswith("The package mixes"): unc.append("mixed licences in one record")
        elif u.startswith("Runor"): unc.append("Runor 2020 licence not stated")
        elif u.startswith("Copernicus"): unc.append("Copernicus DEM licence")
        elif "peterson1996" in u: unc.append("Peterson notes withheld (quotations)")
        elif "kallcitat" in u: unc.append("kallcitat_v3.json withheld (quotations)")
        elif "historiska_land" in u: unc.append("historiska_land.json / socknar_land.csv (ISOF + Det medeltida Sverige)")
        else: unc.append(u[:80])
    L.append(f"| {r['slug']} | {r['n']} | {human(r['bytes'])} | {human(r['zip'])} | {r['licence']} | {exc} | {'; '.join(unc)} |")
L += ["", f"Total: {sum(r['n'] for r in res)} files, {human(tot)} unpacked.", "",
      "## Common to all packages", "",
      "- Built with scripts/zenodo_dataset/build.py (spec.py lists the files per report); uploaded with scripts/zenodo_dataset/ladda_upp.py.",
      "- Code is pinned: shared code (`src/`, `r/`, `scripts/`, `METHODS.md`) from the analysis commit the report names; report files from the commit of the archived report version (5281255 for the ten reports of 2026-11-05, deca8d4 for the folkland report, 89a38c9 for version 4 of the carver report). MANIFEST.json gives the commit per file and whether today's working tree differs.",
      "- The frozen corpus is included as `corpus_subset.csv` (signum + the columns the included scripts use, found by searching the code; columns chosen by name pattern such as `trait_cols()` are kept whole). The full file's SHA-256 is in README and MANIFEST. Exception: the strand report ships the whole corpus.csv (5fdfd1e095bfb6fb), because its plan locks that file's SHA-256 (4fca4baf…). No corpus for the trace-reader report, which read data/rundata.json directly.",
      "- Every package is filed as `odbl-1.0` because it contains Rundata-derived per-stone tables; per-file licences (GPL-3.0 code, CC BY 4.0 results and plans) are in README and MANIFEST.",
      "- Article builders (`utdata/blogg/build/build_rapport_*.py`) and report figures are not included; README points to the GitHub repository.",
      "- Third-party inputs referenced, not included: data/rundata.json (in the repo), Kulturmiljöregistret layers (data/raa/*, CC0), Runor 2020 harvest, SGU GeoPackages, Copernicus DEM, ISOF place-name files, OpenStreetMap/Wikidata place files, Natural Earth, the 3D scans (Zenodo 11951255).",
      "- Fitted R model objects (.rds) are not included.", "",
      "## Per report: excluded items and open questions", ""]
for r in res:
    L.append(f"### {r['slug']}\n")
    for x in r["excluded"]:
        L.append(f"- Excluded: {x}")
    for u in r["uncertain"]:
        L.append(f"- Licence: {u}")
    L.append("- Inputs not included: " + ", ".join(f"`{TP[k][0]}`" for k in r["inputs"]))
    L.append("")
open(os.path.join(OUT, "OVERSIKT.md"), "w", encoding="utf-8").write("\n".join(L))
print("\n".join(L[:20]))
