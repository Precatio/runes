"""Tryckta sidor för påståendena bakom frågelistan (Forskningsluckor, kortet Öppna frågor i forskningen; src/fragelista.py).

Frågelistan (utdata/litteraturgenomgang/artikelkandidater/fragelista.jsonl) bygger på påståendena i
utdata/litteraturgenomgang/pastaenden.jsonl, vart och ett med artikelns nyckel och ett ordagrant citat men utan sida.
Skriptet letar upp citatet i artikelns text sida för sida (sökindexet över tidskrifterna,
/Volumes/2TB/Antigrvity/Runes/downloads/tidskrifter/sok.sqlite) och räknar om pdf-sidan till den tryckta
(src/literature.journal_page_offset). Utdata: data/cache/literature/fragelista_sidor.json, påstående → sida. Frågelistan
är ett internt styrdokument (PUBLICERINGSPLAN.md, "det vi behåller"), så filen ligger i den git-ignorerade cachen och
visas bara i den lokala appen.

    .venv/bin/python scripts/build_fragelista_sidor.py
"""
import json
import os
import re
import sqlite3
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from scripts.build_journal_index import SRC, first_page, meta  # noqa: E402
from src import fragelista, literature  # noqa: E402


def norm(s: str) -> str:
    s = re.sub(r"-\s*\n\s*", "", s or "")
    s = re.sub(r"\b(?:\w ){2,}\w\b", lambda m: m.group(0).replace(" ", ""), s)
    return re.sub(r"[^\wåäöæø]+", " ", s.lower()).strip()


def main() -> None:
    claims = fragelista.claims()
    wanted = {cid for q in fragelista.questions_raw() for cid in q.get("pastaenden") or []}
    articles = meta()
    db = sqlite3.connect(os.path.join(SRC, "sok.sqlite"))
    by_key: dict[str, list[str]] = {}
    for cid in wanted:
        c = claims.get(cid)
        if c:
            by_key.setdefault(c["key"], []).append(cid)
    out, found = {}, 0
    for key, cids in by_key.items():
        pages = [(int(p), t or "") for p, t in db.execute("select page, text from pages where key = ?", (key,))]
        if not pages:
            continue
        pages.sort()
        first, cover = first_page(key, articles.get(key) or {})
        offset = literature.journal_page_offset(pages, first, cover)
        normed = [(no, norm(t)) for no, t in pages]
        for cid in cids:
            q = norm(claims[cid].get("quote") or "")
            if len(q) < 12:
                continue
            probe = q[:40]
            hit = next((no for no, t in normed if probe in t), None)
            if hit is None and len(q) > 60:  # a quote across a page break: try its end
                hit = next((no for no, t in normed if q[-40:] in t), None)
            if hit is not None:
                out[cid] = literature.journal_printed(hit, offset, first)
                found += 1
    path = os.path.join(ROOT, "data", "cache", "literature", "fragelista_sidor.json")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump({"built": date.today().isoformat(), "pages": out}, fh, ensure_ascii=False)
    os.replace(tmp, path)
    print(f"{found} av {len(wanted)} påståenden har fått en sida "
          f"({sum(1 for v in out.values() if not v.startswith('pdf'))} med tryckt sida)")


if __name__ == "__main__":
    main()
