"""Ingvarsstenarna enligt den låsta planen analysplaner/2026-11-10-sjalvkontroll-osterled.md.
    ../../../.venv/bin/python ingvarsstenar.py
Skriver ingvarsstenar.csv (signum, landskap, led, utdrag). Granskningen mot texten görs för hand innan någon andel
räknas; borttagna stenar står i GRANSKNING nedan med motivering, och listan fryses sedan (analys.py läser csv:n)."""
import csv
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
VARLDEN = os.path.dirname(HERE)
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import entities  # noqa: E402
from src.research_gaps import province  # noqa: E402

# Handgranskning (fylls i innan andelarna räknas): signum -> motivering för att stenen tas bort ur listan
# (granskat 2026-11-10, innan någon andel räknades; listan är därefter fryst)
GRANSKNING: dict[str, str] = {
    "U 540": "Ingvarr är en av resarna (bröder till den döde, samma krets som U 513); den döde dog i Grekland. "
             "Ingen koppling till tåget i texten: bara en man som heter Ingvarr.",
}
# Kvar efter granskningen, men inte självklara (led b): Ög 30 minns en son som hette Ingvarr och dog i öster – inte
# uppenbart utan koppling till tåget, så stenen står kvar enligt planens breda definition. Sö 179 (Haraldr, Ingvarrs
# bror) är en känd Ingvarsten.

ING = re.compile(r"\bIngvar", re.I)


def load():
    places = list(csv.DictReader(open(os.path.join(VARLDEN, "platser.csv"), encoding="utf-8")))
    region = {p["plats"]: p["region"] for p in places}
    rows = [r for r in csv.DictReader(open(os.path.join(VARLDEN, "platser_per_text.csv"), encoding="utf-8"))
            if r["korpus"] == "runstenar_sverige"]
    recs = json.load(open(os.path.join(ROOT, "data", "rundata.json")))
    recs = recs if isinstance(recs, list) else recs.get("inscriptions", list(recs.values()))
    by = {r["signum"]: r for r in recs}
    return region, rows, by


def main():
    region, rows, by = load()
    out, missing = [], []
    for row in rows:
        rec = by.get(row["text"])
        if rec is None:
            missing.append(row["text"])
            continue
        east = any(int(row[p]) > 0 for p, reg in region.items() if reg == "öster")
        a = "Ingvarståget" in entities.extract(rec)["events"]
        texts = " ".join([rec.get("translation_en") or "", rec.get("normalization") or "", rec.get("normalization_ows") or ""])
        b = bool(ING.search(texts)) and east
        if not (a or b):
            continue
        tr = rec.get("translation_en") or ""
        m = ING.search(tr)
        snip = tr[max(0, m.start() - 90): m.end() + 90] if m else tr[:180]
        led = "a+b" if a and b else "a" if a else "b"
        out.append({"signum": row["text"], "landskap": province(rec), "led": led, "ostlig_plats": int(east),
                    "borttagen": GRANSKNING.get(row["text"], ""), "utdrag": re.sub(r"\s+", " ", snip)})
    with open(os.path.join(HERE, "ingvarsstenar.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    print(f"{len(out)} kandidater, {sum(1 for o in out if not o['borttagen'])} efter granskning; ej kopplade: {missing}")
    for o in out:
        print(o["signum"], o["led"], o["ostlig_plats"], o["borttagen"] or "", "|", o["utdrag"])


if __name__ == "__main__":
    main()
