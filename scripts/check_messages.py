"""Facit för budskapsreglerna (src/messages.py): jämför reglerna med två handkodningar och skriver ut överensstämmelsen.

1. Väst: de 55 nordiska inskrifter som nämner en resa västerut (utdata/brittiska/hemma_kodning.csv; utfall dog, resa,
   hem eller utesluten). 'dog' ska ge död borta, 'resa' och 'hem' inte; alla som inte är uteslutna ska ge resa och en
   västlig riktning.
2. Öst: data/messages_facit_ost.csv, handkodad sten för sten ur översättningen: alla svenska runstenar som de gamla
   reglerna (före 2026-10-27) räknade som österfärder (urval 'öst', bland dem de 11 stenar där mannen bara heter
   Ingvarr), och ett tillägg (urval 'tillägg') med österländska platser som de gamla reglerna missade, inrikes färder
   och dödsfall i Norden (Gotland, Danmark, Hedeby, Skåne), resor utan mål och personnamn som liknar platser.
   Båda urvalen kodades medan reglerna rättades, så de mäter inte reglerna utanför urvalet. Det gör urval 'slump':
   33 läsbara runstenar dragna slumpvis (seed 20261027) bland dem som nämner död, resa eller väderstreck och inte
   finns i någon av handkodningarna (två för fragmentariska för reglerna ströks ur dragningen). Helt blint är det
   inte: tolv av dem hade setts när reglerna rättades (de bytte klass).
   Kolumner: resa, dod_borta, dod_uppgift (1/0) och riktning (öst, väst, båda eller tomt).

Till sist en känslighetskoll för läsbarhetsgränsen (MIN_WORDS): andelen stenar med resa per landsdel vid MIN_WORDS och
STRICT_WORDS ord (r/messages.R gör samma koll med modellen).

Överensstämmelsen skrivs också till data/messages_check.json, som r/messages.R läser och sidan Budskap visar (med
md5-summan av src/messages.py, så att en kontroll av äldre regler syns som inaktuell). Kör skriptet igen när reglerna
eller handkodningarna ändras.

  .venv/bin/python scripts/check_messages.py                      # de nuvarande reglerna, skriver data/messages_check.json
  .venv/bin/python scripts/check_messages.py --module ANNAN.py    # en annan version av src/messages.py (skriver inget)
"""
import argparse
import csv
import hashlib
import importlib.util
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
WEST_CSV = os.path.join(ROOT, "utdata", "brittiska", "hemma_kodning.csv")
EAST_CSV = os.path.join(ROOT, "data", "messages_facit_ost.csv")
CHECK_JSON = os.path.join(ROOT, "data", "messages_check.json")
# Budskap som ingen av handkodningarna täcker (bara stickprov när reglerna skrevs)
UNCHECKED = ("gald", "arv", "gard", "egen", "berom")


def load_module(path: str | None):
    if not path:
        from src import messages
        return messages
    spec = importlib.util.spec_from_file_location("messages_check", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def agreement(name: str, pairs: list[tuple[str, object, object]], show: int = 30) -> tuple[int, int]:
    """pairs: (signum, facit, regel). Skriver andel lika, och för 0/1 även precision och täckning."""
    same = [p for p in pairs if p[1] == p[2]]
    line = f"  {name}: {len(same)} av {len(pairs)} lika"
    if all(p[1] in (0, 1) for p in pairs):
        tp = sum(1 for _, f, r in pairs if f == 1 and r == 1)
        fp = sum(1 for _, f, r in pairs if f == 0 and r == 1)
        fn = sum(1 for _, f, r in pairs if f == 1 and r != 1)
        prec = f"{tp / (tp + fp):.0%}" if tp + fp else "–"
        rec = f"{tp / (tp + fn):.0%}" if tp + fn else "–"
        line += f" (precision {prec}, täckning {rec}; {fp} falska träffar, {fn} missade)"
    print(line)
    diff = [p for p in pairs if p[1] != p[2]]
    for s, f, r in diff[:show]:
        print(f"      {s}: facit {f!r}, regel {r!r}")
    if len(diff) > show:
        print(f"      ... och {len(diff) - show} till")
    return len(same), len(pairs)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--module", help="sökväg till en annan version av src/messages.py")
    args = ap.parse_args()
    m = load_module(args.module)
    report: dict = {"rules_md5": hashlib.md5(open(m.__file__, "rb").read()).hexdigest(), "unchecked": list(UNCHECKED)}
    from api.rundata import store
    recs = store().inscriptions
    by = {r["signum"]: r for r in recs}

    def rule(s):
        r = by[s]
        return m.classify(r), m.direction(r)

    print("Väst (utdata/brittiska/hemma_kodning.csv)")
    rows = [r for r in csv.DictReader(open(WEST_CSV, encoding="utf-8")) if r["utfall"] != "utesluten"]
    missing = [r["signum"] for r in rows if r["signum"] not in by]
    rows = [r for r in rows if r["signum"] in by]
    res = {r["signum"]: rule(r["signum"]) for r in rows}
    report["west"] = {
        "file": os.path.relpath(WEST_CSV, ROOT), "n": len(rows),
        "dod_borta": agreement("död borta", [(r["signum"], int(r["utfall"] == "dog"), res[r["signum"]][0]["dod_borta"])
                                             for r in rows]),
        "resa": agreement("resa", [(r["signum"], 1, res[r["signum"]][0]["resa"]) for r in rows]),
        "riktning": agreement("riktning väster", [(r["signum"], 1, int(res[r["signum"]][1] in ("väst", "båda")))
                                                  for r in rows])}
    if missing:
        print("  saknas i Rundata:", ", ".join(missing))

    print(f"Öst ({os.path.relpath(EAST_CSV, ROOT)})")
    rows = list(csv.DictReader(open(EAST_CSV, encoding="utf-8")))
    missing = [r["signum"] for r in rows if r["signum"] not in by]
    rows = [r for r in rows if r["signum"] in by]
    res = {r["signum"]: rule(r["signum"]) for r in rows}
    report["east"] = {"file": os.path.relpath(EAST_CSV, ROOT), "n": len(rows), "samples": {}}
    for urval in ("alla", "öst", "tillägg", "slump"):
        sub = [r for r in rows if urval == "alla" or r["urval"] == urval]
        print(f" urval {urval} ({len(sub)} stenar)")
        got = {"n": len(sub)}
        for k in ("resa", "dod_borta", "dod_uppgift"):
            got[k] = agreement(k.replace("_", " "), [(r["signum"], int(r[k]), res[r["signum"]][0][k]) for r in sub],
                               show=30 if urval == "alla" else 0)
        trav = [r for r in sub if r["resa"] == "1"]
        got["riktning"] = agreement("riktning (resestenar)", [(r["signum"], r["riktning"], res[r["signum"]][1]) for r in trav],
                                    show=30 if urval == "alla" else 0)
        report["east"]["samples"][urval] = got
    ingvarr = [r for r in rows if "bara namnet" in r["kommentar"]]
    print(f"  bara namnet Ingvarr: {sum(1 for r in ingvarr if res[r['signum']][0]['resa'] == 0)} av {len(ingvarr)}"
          " utan resa enligt regeln")
    if missing:
        print("  saknas i Rundata:", ", ".join(missing))

    print("Känslighet för läsbarhetsgränsen (resa per landsdel, svenska runstenar)")
    keep = m.MIN_WORDS
    try:
        for n in (keep, getattr(m, "STRICT_WORDS", 10)):
            m.MIN_WORDS = n
            out = m.rows(recs)
            parts = []
            for reg in ("Götaland", "Svealand"):
                x = [r for r in out if r["region"] == reg and r["msg_resa"] is not None]
                k = sum(r["msg_resa"] for r in x)
                parts.append(f"{reg} {k}/{len(x)} = {k / len(x):.3f}")
            print(f"  minst {n} ord: " + ", ".join(parts))
    finally:
        m.MIN_WORDS = keep

    if not args.module:
        with open(CHECK_JSON, "w", encoding="utf-8") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
        print(f"Skrev {os.path.relpath(CHECK_JSON, ROOT)}")


if __name__ == "__main__":
    main()
