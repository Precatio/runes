"""Sannolikhetsmodellens öppna luckor för Forskningsluckor (METHODS.md 14): de luckor Rundata lämnat oåterställda där
modellens ifyllnad når minst 80 % och ordet är känt, ur den senaste luckinventeringen (scripts/runlm_gaps.py →
utdata/Malt/runlm_luckor.json). Skriver data/textmodel_candidates.json, som appen serverar
(GET /api/research/gaps/textmodel) och som ligger i git, eftersom utdata inte gör det.
    .venv/bin/python scripts/runlm_gaps.py ...                 # inventeringen (tar tid)
    .venv/bin/python scripts/textmodel_candidates.py           # kandidatlistan
"""
import datetime as dt
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
from src.textmodel import VERSION  # noqa: E402

SRC = os.path.join(ROOT, "utdata", "Malt", "runlm_luckor.json")
OUT = os.path.join(ROOT, "data", "textmodel_candidates.json")
RUNDATA_VERSION = "Samnordisk runtextdatabas 3.1 (2018)"
MIN_P = 0.8


def province(sig: str) -> str:
    return sig.split()[0]


def main():
    d = json.load(open(SRC, encoding="utf-8"))
    rows = d["rows"]
    open_rows = [r for r in rows if r["status"] == "ej återställt"]
    cands = [r for r in open_rows if (r.get("p") or 0) >= MIN_P and r.get("word") and r["word"] != "<unk>"]
    cands.sort(key=lambda r: (-r["p"], r["sig"]))
    out = {
        "model_version": VERSION,
        "computed_at": dt.datetime.fromtimestamp(os.path.getmtime(SRC), dt.timezone.utc).isoformat(),
        "rundata_version": RUNDATA_VERSION,
        "min_p": MIN_P,
        "counts": {"gaps_inventoried": len(rows), "open": len(open_rows), "candidates": len(cands),
                   "stones": len({r["sig"] for r in cands})},
        "settings": d.get("settings"),
        "candidates": [{"signum": r["sig"], "province": province(r["sig"]), "carved": r["carved"], "gap": r["gap"],
                        "fill": r.get("fill"), "word": r.get("word"), "p": round(r["p"], 3),
                        "alts": [[a[0], round(a[1], 3)] for a in (r.get("alts") or [])[:2]],
                        "reading": r.get("reading"), "p_reading": round(r["p_reading"], 3) if r.get("p_reading") is not None else None}
                       for r in cands],
    }
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{out['counts']['candidates']} kandidater på {out['counts']['stones']} stenar av {len(open_rows)} öppna luckor → {OUT}")


if __name__ == "__main__":
    main()
