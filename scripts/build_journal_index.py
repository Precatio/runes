"""Litteraturregistrets tidskriftsdel: var Fornvännen (1906–2023) och Futhark nämner en runsten. Läser sökindexet över de
hämtade tidskrifterna (utdata/litteraturgenomgang/sokindex.py → /Volumes/2TB/Antigrvity/Runes/downloads/tidskrifter/
sok.sqlite, text sida för sida) och skriver data/cache/literature/journals.json: per sten artiklarna, pdf-sidorna och ett
kort utdrag runt varje omnämnande, och per artikel tidskrift, år, författare, titel och länk. Båda tidskrifterna är fria
under CC BY 4.0. Viktor 2026-11-10: litteraturen per sten i appen, efter litteraturgenomgången.
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
from src import literature  # noqa: E402
from src.signum import fold_signum  # noqa: E402

SRC = "/Volumes/2TB/Antigrvity/Runes/downloads/tidskrifter"
OUT = os.path.join(ROOT, "data", "cache", "literature", "journals.json")


def meta() -> dict[str, dict]:
    """Artiklarnas uppgifter ur hämtningarnas index (Arkivsök för Fornvännen, DiVA för Futhark)."""
    out = {}
    for journal in ("fornvannen", "futhark"):
        for line in open(os.path.join(SRC, journal, "index.jsonl"), encoding="utf-8"):
            d = json.loads(line)
            a = d.get("authors") or []
            a = a if isinstance(a, list) else [x.split("[")[0].strip() for x in a.split(";")]
            url = d.get("uri") or (f"https://doi.org/{d['doi']}" if d.get("doi") else d.get("fulltext"))
            out[d["key"]] = {"journal": "Fornvännen" if journal == "fornvannen" else "Futhark", "year": str(d.get("year") or ""),
                             "title": d.get("title") or "", "authors": [x for x in a if x], "url": url,
                             "pages": d.get("pages"), "volume": d.get("volume")}
    return out


def main():
    signa = {fold_signum(r["signum"]): r["signum"] for r in store().inscriptions}
    rx = literature.signum_pattern(sorted({s.split(" ")[0] for s in signa.values()}))
    articles = meta()
    db = sqlite3.connect(os.path.join(SRC, "sok.sqlite"))
    stones: dict[str, list[dict]] = {}
    used = set()
    for key, page, text in db.execute("select key, page, text from pages"):
        # Futharks helvolymer och Fornvännens årsregister dubblerar artiklarna; de hoppas över
        if key not in articles or "_hel_" in key or key.endswith("_reg"):
            continue
        flat = re.sub(r"\s+", " ", re.sub(r"-\n\s*", "", text or ""))
        hits = [m for m in rx.finditer(flat) if fold_signum(f"{m.group(1)} {m.group(2)}") in signa]
        if not hits:
            continue
        n_words = len(re.findall(r"[A-Za-zÅÄÖåäöÆØæøÞþÐð]{4,}", flat))
        is_list = len({fold_signum(f"{m.group(1)} {m.group(2)}") for m in hits}) / max(n_words, 1) > literature.LIST_RATIO
        seen = set()
        for m in hits:
            k = fold_signum(f"{m.group(1)} {m.group(2)}")
            if k in seen:
                continue
            seen.add(k)
            hit = {"article": key, "page": f"pdf {page}"}
            if is_list:
                hit["list"] = True
            else:
                a, b = max(0, m.start() - literature.SNIPPET), min(len(flat), m.end() + literature.SNIPPET)
                hit["text"] = ("…" if a else "") + flat[a:b].strip() + ("…" if b < len(flat) else "")
            stones.setdefault(k, []).append(hit)
            used.add(key)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump({"built": date.today().isoformat(), "n_articles": len({k for k in articles if "_hel_" not in k}),
                   "articles": {k: articles[k] for k in used}, "stones": stones}, fh, ensure_ascii=False)
    os.replace(tmp, OUT)
    print(f"{len(stones)} stenar nämns i {len(used)} artiklar")


if __name__ == "__main__":
    main()
