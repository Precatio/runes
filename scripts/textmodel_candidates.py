"""Sannolikhetsmodellens öppna luckor för Forskningsluckor (METHODS.md 14): de luckor Rundata lämnat oåterställda där
modellens ifyllnad är ett känt ord med minst 50 % KALIBRERAD sannolikhet, ur den senaste luckinventeringen
(scripts/runlm_gaps.py). Källan är den gällande generationens klass3_alla.json (utdata/runlm_forfining/tm19/), samma
inventering körd med appens inställningar (egna skiljetecken, namnkvot, toleranslager).

Procenten: inventeringen ger modellens råa sannolikhet för ordet (p_model). Den kalibreras här med listkalibreringen
(data/runlm_calibration.json, gap_list; src/textmodel.calibrate_words) på exakt det sätt den anpassades
(scripts/runlm_list_calibrate.py): ordet och inventeringens alternativ tillsammans, antalet förlorade runor i luckan,
inte ett helt ord. Fram till 2026-10-23 visade listan den råa siffran under rubriken kalibrerad; den är ofta mycket
högre för namn och ovanliga ord.

Varje rad bär också Rundatas föremål och om det är en runsten (src/research_gaps.is_runestone; appen visar runstenar
som standard och andra föremål bara på begäran), och ett svenskt översättningsutkast av modellens läsning, ord för ord
ur den ordlista som lärts av Rundatas översättningar utan stenen själv (textmodel.bundle för stenens femtedel,
src/rungloss.swedish i strikt läge: ett ord utan svensk motsvarighet står kvar på fornspråk och namn som
de lästs), samma väg som stenanalysens utkast. Skriver data/textmodel_candidates.json, som appen serverar
(GET /api/research/gaps/textmodel) och som ligger i git.
    .venv/bin/python scripts/textmodel_candidates.py [INVENTERING.json]
"""
import datetime as dt
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
from src import research_gaps as gaps  # noqa: E402
from src import rungloss as rg  # noqa: E402
from src import textmodel as tm  # noqa: E402
from src.textmodel import VERSION  # noqa: E402

SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "utdata", "runlm_forfining", "tm19", "klass3_alla.json")
OUT = os.path.join(ROOT, "data", "textmodel_candidates.json")
RUNDATA_VERSION = "Samnordisk runtextdatabas 3.1 (2018)"
MIN_P = 0.5    # calibrated: the list shows every open gap the model fills with at least an even chance
SURE_P = 0.8   # calibrated: the band the page calls "minst 80 %"


def province(sig: str) -> str:
    return sig.split()[0]


def calibrated(r: dict, GL) -> dict:
    """The gap's words with calibrated probabilities (the word and the inventory's alternatives together), computed as
    the list calibration was fitted on these rows."""
    dist = {r["word"]: r["p"]}
    dist.update({w: p for w, p in (r.get("alts") or []) if w not in dist})
    return tm.calibrate_words(dist, len(r.get("fill") or ""), GL, False)


def draft_sv(sig: str, reading: str | None) -> str | None:
    """A Swedish word-for-word draft of the model's reading, from the glossary learned without the stone."""
    if not reading:
        return None
    b = tm.bundle(tm.fold_of(sig))
    return rg.swedish(reading.split(), b["en"], b["da"], b["ows"], strict=True)


def main():
    d = tm._records()
    GL, by = d["GL"], d["by"]
    assert GL, "Listkalibreringen (gap_list) saknas i data/runlm_calibration.json"
    inv = json.load(open(SRC, encoding="utf-8"))
    rows = inv["rows"]
    kind = lambda sig: "runsten" if sig in by and gaps.is_runestone(by[sig]) else "annat"  # noqa: E731
    open_rows = [r for r in rows if r["status"] == "ej återställt"]
    known = [r for r in open_rows if r.get("word") and r["word"] != "<unk>"]
    for r in known:
        r["cal"] = calibrated(r, GL)
        r["p_cal"] = r["cal"].get(r["word"], 0.0)
    cands = sorted((r for r in known if r["p_cal"] >= MIN_P), key=lambda r: (-r["p_cal"], r["sig"]))
    count = lambda xs, k=None: len([r for r in xs if k is None or kind(r["sig"]) == k])  # noqa: E731
    out = {
        "model_version": VERSION,
        "computed_at": dt.datetime.fromtimestamp(os.path.getmtime(SRC), dt.timezone.utc).isoformat(),
        "built_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "rundata_version": RUNDATA_VERSION,
        "min_p": MIN_P, "sure_p": SURE_P, "p_is": "calibrated",
        "counts": {"gaps_inventoried": len(rows), "open": len(open_rows), "candidates": len(cands),
                   "stones": len({r["sig"] for r in cands}), "sure": len([r for r in cands if r["p_cal"] >= SURE_P]),
                   # the same counts for runestones only (the page's default) and for other objects
                   "runsten": {"gaps_inventoried": count(rows, "runsten"), "open": count(open_rows, "runsten"),
                               "candidates": count(cands, "runsten"),
                               "stones": len({r["sig"] for r in cands if kind(r["sig"]) == "runsten"}),
                               "sure": len([r for r in cands if kind(r["sig"]) == "runsten" and r["p_cal"] >= SURE_P])},
                   "annat": {"gaps_inventoried": count(rows, "annat"), "open": count(open_rows, "annat"),
                             "candidates": count(cands, "annat"),
                             "stones": len({r["sig"] for r in cands if kind(r["sig"]) == "annat"}),
                             "sure": len([r for r in cands if kind(r["sig"]) == "annat" and r["p_cal"] >= SURE_P])}},
        "settings": inv.get("settings"),
        "candidates": [{"signum": r["sig"], "province": province(r["sig"]),
                        "object": (by.get(r["sig"]) or {}).get("object"), "runestone": kind(r["sig"]) == "runsten",
                        "carved": r["carved"], "gap": r["gap"], "fill": r.get("fill"), "word": r.get("word"),
                        "p": round(r["p_cal"], 3), "p_model": round(r["p"], 3),
                        # the next words, calibrated together with the first; the model's raw figure beside it
                        "alts": [[a[0], round(r["cal"].get(a[0], 0.0), 3), round(a[1], 3)]
                                 for a in (r.get("alts") or []) if a[0] != "<unk>"][:2],
                        "reading": r.get("reading"),
                        "p_reading": round(r["p_reading"], 3) if r.get("p_reading") is not None else None,
                        "translation_sv": draft_sv(r["sig"], r.get("reading"))}
                       for r in cands],
    }
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    c = out["counts"]
    print(f"{c['candidates']} kandidater (≥{MIN_P:.0%} kalibrerat; {c['sure']} ≥{SURE_P:.0%}) på {c['stones']} inskrifter av "
          f"{len(open_rows)} öppna luckor; runstenar {c['runsten']['candidates']} ({c['runsten']['sure']} ≥{SURE_P:.0%}) → {OUT}")


if __name__ == "__main__":
    main()
