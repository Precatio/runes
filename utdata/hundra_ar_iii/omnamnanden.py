"""Hundra år av runfrågor III: vilka svenska runstenar som nämns med signum i tidskrifterna vi har hemma (Fornvännen
1906–2022, Futhark 2010–2025, Namn och bygd 2010–2025, Current Swedish Archaeology 2020–) och i avhandlingarna i
litteraturregistret. Ett omnämnande = en text som nämner stenen minst en gång (inte hur många gånger).

Regeln (låst i analysplaner/2026-11-20-hundra-ar-III.md):
- signumet hittas med samma mönster som appens litteraturregister (src/literature.signum_pattern) och måste finnas i
  Rundata som svensk vikingatida runsten (src/research_gaps.is_runestone);
- ordet "run" (runsten, runinskrift, runor, rune, runic …) måste stå inom 300 tecken från signumet, annars är det
  oftast ett museinummer, en tand (M 2) eller en sidhänvisning;
- ett signum som följs av komma eller punkt och en siffra ("St. H. M. 8,756") är ett inventarienummer;
- spärrad OCR-text ("U 11 s t r ö m", "G 1 o b") räknas inte: ett signum som följs eller föregås av ensamma bokstäver
  med mellanslag emellan stryks.
Texterna läses ur sökindexet /Volumes/2TB/Antigrvity/Runes/downloads/tidskrifter/sok.sqlite (utanför repot).

    .venv/bin/python utdata/hundra_ar_iii/omnamnanden.py [--prov N]   # skriver data/cache/hundra_ar_iii/omnamnanden.csv
"""
import csv
import os
import random
import re
import sqlite3
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
from api.rundata import store  # noqa: E402
from src import literature  # noqa: E402
from src.research_gaps import is_runestone  # noqa: E402
from src.signum import fold_signum  # noqa: E402

DB = "/Volumes/2TB/Antigrvity/Runes/downloads/tidskrifter/sok.sqlite"
OUT = os.path.join(ROOT, "data", "cache", "hundra_ar_iii", "omnamnanden.csv")
RUN = re.compile(r"run", re.I)
SPACED_AFTER = re.compile(r"^\s?[^\W\d_]\s[^\W\d_]\s")
SPACED_BEFORE = re.compile(r"(?:^|\s)[^\W\d_]\s[^\W\d_]\s$")
WINDOW = 300


def stones() -> dict[str, dict]:
    return {fold_signum(r["signum"]): r for r in store().inscriptions if is_runestone(r)}


def mentions(flat: str, rx, keep: dict) -> list[tuple[str, str]]:
    """(folded signum, context) for every accepted mention on one text."""
    out = []
    for m in rx.finditer(flat):
        k = fold_signum(f"{m.group(1)} {m.group(2)}")
        if k not in keep:
            continue
        if SPACED_AFTER.match(flat[m.end():m.end() + 8]) or SPACED_BEFORE.search(flat[max(0, m.start() - 6):m.start()]):
            continue
        if re.match(r"[.,]\d", flat[m.end():m.end() + 2]):  # "St. H. M. 8,756", "U 1.2"
            continue
        if not RUN.search(flat[max(0, m.start() - WINDOW):m.end() + WINDOW]):
            continue
        out.append((k, flat[max(0, m.start() - 90):m.end() + 90]))
    return out


def journals(keep: dict):
    """Rows (journal, key, year, signum) – one per text and stone. Whole Futhark volumes and registers are skipped."""
    db = sqlite3.connect(DB)
    rx = literature.signum_pattern(sorted({r["signum"].split(" ")[0] for r in keep.values()}))
    docs = {k: (j, y) for k, j, y in db.execute("select key, journal, year from docs")}
    texts: dict[str, list[str]] = {}
    for key, page, text in db.execute("select key, page, text from pages order by key, page"):
        if "_hel_" in key or key.endswith("_reg"):
            continue
        texts.setdefault(key, []).append(text or "")
    rows, ctx = [], []
    for key, pages in texts.items():
        flat = re.sub(r"\s+", " ", re.sub(r"-\n\s*", "", "\n".join(pages)))
        seen = set()
        for k, c in mentions(flat, rx, keep):
            ctx.append((docs[key][1], keep[k]["signum"], c))
            if k not in seen:
                seen.add(k)
                rows.append((docs[key][0], key, int(str(docs[key][1])[:4]), keep[k]["signum"]))
    return rows, ctx


def theses(keep: dict):
    """Rows (work, year, signum) from the literature register's dissertations (not the SRI editions)."""
    import json
    idx = json.load(open(literature.INDEX, encoding="utf-8"))
    works = {w["id"]: w for w in literature.catalog()}
    rows = set()
    for k, hits in idx["stones"].items():
        if k not in keep:
            continue
        for h in hits:
            w = works.get(h["work"])
            if w and w.get("kind") == "avhandling":
                rows.add((w["id"], w["year"], keep[k]["signum"]))
    return sorted(rows)


def main(argv):
    keep = stones()
    rows, ctx = journals(keep)
    th = theses(keep)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["source", "text", "year", "signum"])
        w.writerows(rows)
        w.writerows([("avhandling", wid, y, s) for wid, y, s in th])
    print(f"{len(keep)} runstenar; {len(rows)} omnämnanden i tidskrifterna, {len(th)} i avhandlingarna → {OUT}")
    if "--prov" in argv:
        n = int(argv[argv.index("--prov") + 1])
        random.seed(20261120)
        for y, s, c in random.sample(ctx, n):
            print(f"{y} {s} | {c}")


if __name__ == "__main__":
    main(sys.argv[1:])
