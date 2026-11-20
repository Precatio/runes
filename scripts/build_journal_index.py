"""Litteraturregistrets tidskriftsdel: var Fornvännen (1906–2023), Futhark, Namn och bygd (2010–2025) och Current Swedish
Archaeology (vol. 28–) nämner en runsten. Läser sökindexet över de
hämtade tidskrifterna (utdata/litteraturgenomgang/sokindex.py → /Volumes/2TB/Antigrvity/Runes/downloads/tidskrifter/
sok.sqlite, text sida för sida) och skriver data/cache/literature/journals.json: per sten artiklarna, pdf-sidorna, den
tryckta sidan där den går att räkna ut (src/literature.journal_page_offset) och ett kort utdrag runt varje omnämnande, och
per artikel tidskrift, år, författare, titel och länk. För "Redan känt?" i Forskningsluckor (src/redan_kant.py) står också,
per omnämnande i löptext, de ristarnamn ur Rundata som står som ristare inom 300 tecken från stenens signum (med ett
utdrag) och de andra stenar som nämns inom samma avstånd. Alla fyra är fria (CC BY 4.0, Fornvännen delvis CC0; Futhark vol. 1–6
CC BY-NC-ND). Viktor 2026-11-10: litteraturen per sten i appen, efter litteraturgenomgången.
    .venv/bin/python scripts/build_journal_index.py"""
import json
import os
import re
import sqlite3
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from api.rundata import store  # noqa: E402
from src import literature, redan_kant as rk  # noqa: E402
from src.signum import fold_signum  # noqa: E402

SRC = "/Volumes/2TB/Antigrvity/Runes/downloads/tidskrifter"
OUT = os.path.join(ROOT, "data", "cache", "literature", "journals.json")


def meta() -> dict[str, dict]:
    """Artiklarnas uppgifter ur hämtningarnas index (Arkivsök för Fornvännen, DiVA för Futhark)."""
    out = {}
    namn = {"fornvannen": "Fornvännen", "futhark": "Futhark", "namnochbygd": "Namn och bygd",
            "csa": "Current Swedish Archaeology"}
    for journal in namn:
        p = os.path.join(SRC, journal, "index.jsonl")
        if not os.path.exists(p):
            continue
        for line in open(p, encoding="utf-8"):
            d = json.loads(line)
            a = d.get("authors") or []
            a = a if isinstance(a, list) else [x.split("[")[0].strip() for x in a.split(";")]
            url = d.get("uri") or (f"https://doi.org/{d['doi']}" if d.get("doi") else d.get("fulltext") or d.get("source"))
            assert out.get(d["key"], {}).get("journal", namn[journal]) == namn[journal], f"samma nyckel i två tidskrifter: {d['key']}"
            out[d["key"]] = {"journal": namn[journal], "year": str(d.get("year") or ""),
                             "title": d.get("title") or "", "authors": [x for x in a if x], "url": url,
                             "pages": d.get("pages"), "volume": d.get("volume")}
    return out


def first_page(key: str, meta: dict) -> tuple[int | None, bool]:
    """Artikelns första tryckta sida ur metadata, och om pdf:en har ett omslag före den (Fornvännen)."""
    m = re.fullmatch(r"\d{4}_(\d{1,4})", key)
    if m and meta.get("journal") == "Fornvännen":
        return int(m.group(1)), True
    m = re.match(r"\s*(\d{1,4})", str(meta.get("pages") or ""))
    if m and meta.get("journal") == "Futhark":
        return int(m.group(1)), False
    return None, False


def main():
    s = store()
    signa = {fold_signum(r["signum"]): r["signum"] for r in s.inscriptions}
    rx = literature.signum_pattern(sorted({s.split(" ")[0] for s in signa.values()}))
    bases = sorted({b for r in s.inscriptions for c in r["carvers"] if c["kind"] in ("S", "A")
                    for b in [rk.carver_base(c["name"])] if b})
    names = rk.names_pattern(bases)
    articles = meta()
    db = sqlite3.connect(os.path.join(SRC, "sok.sqlite"))
    by_key: dict[str, list[tuple[int, str]]] = {}
    for key, page, text in db.execute("select key, page, text from pages"):
        # Futharks helvolymer och Fornvännens årsregister dubblerar artiklarna; de hoppas över
        if key not in articles or "_hel_" in key or key.endswith("_reg"):
            continue
        by_key.setdefault(key, []).append((int(page), text or ""))
    stones: dict[str, list[dict]] = {}
    used = set()
    n_printed = n_hits = 0
    for key, pages in by_key.items():
        pages.sort()
        first, cover = first_page(key, articles[key])
        offset = literature.journal_page_offset(pages, first, cover)
        for page, text in pages:
            flat = re.sub(r"\s+", " ", re.sub(r"-\n\s*", "", text))
            hits = [m for m in rx.finditer(flat) if fold_signum(f"{m.group(1)} {m.group(2)}") in signa]
            if not hits:
                continue
            n_words = len(re.findall(r"[A-Za-zÅÄÖåäöÆØæøÞþÐð]{4,}", flat))
            is_list = len({fold_signum(f"{m.group(1)} {m.group(2)}") for m in hits}) / max(n_words, 1) > literature.LIST_RATIO
            printed = literature.journal_printed(page, offset, first)
            seen = set()
            for m in hits:
                k = fold_signum(f"{m.group(1)} {m.group(2)}")
                if k in seen:
                    continue
                seen.add(k)
                hit = {"article": key, "page": f"pdf {page}"}
                if not printed.startswith("pdf"):
                    hit["printed"] = printed
                    n_printed += 1
                n_hits += 1
                if is_list:
                    hit["list"] = True
                else:
                    a, b = max(0, m.start() - literature.SNIPPET), min(len(flat), m.end() + literature.SNIPPET)
                    hit["text"] = ("…" if a else "") + flat[a:b].strip() + ("…" if b < len(flat) else "")
                    # every mention of the stone on the page: carvers named as carvers, and the other stones, nearby
                    carvers: dict[str, str] = {}
                    co: set[str] = set()
                    for mm in rx.finditer(flat):
                        if fold_signum(f"{mm.group(1)} {mm.group(2)}") != k:
                            continue
                        lo, hi = max(0, mm.start() - rk.JOURNAL_WINDOW), mm.end() + rk.JOURNAL_WINDOW
                        window = flat[lo:hi]
                        for base, ex in rk.carver_mentions(window, names, rx, k, window=True).items():
                            carvers.setdefault(base, ex)
                        co |= {fold_signum(f"{x.group(1)} {x.group(2)}") for x in rx.finditer(window)} & signa.keys()
                    co.discard(k)
                    if carvers:
                        hit["carvers"] = carvers
                    if co:
                        hit["co"] = sorted(co)
                stones.setdefault(k, []).append(hit)
                used.add(key)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump({"built": date.today().isoformat(), "n_articles": len({k for k in articles if "_hel_" not in k}),
                   "articles": {k: articles[k] for k in used}, "stones": stones}, fh, ensure_ascii=False)
    os.replace(tmp, OUT)
    print(f"{len(stones)} stenar nämns i {len(used)} artiklar; tryckt sida för {n_printed} av {n_hits} omnämnanden")


if __name__ == "__main__":
    main()
