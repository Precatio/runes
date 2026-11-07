"""Citatkontroll för Norgeartikeln: ett citat ska stå i källans textlager på angiven pdf-sida. Textlagren är OCR med
fel (mellanslag inne i ord hos Palm 1992, utan prickar och ringar hos Almgren 1944, förvrängda ord hos Sawyer 1989), så
jämförelsen görs på bokstäverna enbart (gemener, utan diakritiska tecken och mellanrum); för de sämsta lagren godtas en
nästan-träff (minst 85 % lika, difflib) i ett fönster av citatets längd. Källorna i
/Volumes/2TB/Antigrvity/Runes/downloads/norge_lit/ (text/ = pdftotext -layout)."""
import difflib
import re
import unicodedata

SRC = "/Volumes/2TB/Antigrvity/Runes/downloads/norge_lit/"


def letters(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if c.isalnum() and not unicodedata.combining(c))


_cache: dict[str, list[str]] = {}


def pages(path: str) -> list[str]:
    if path not in _cache:
        _cache[path] = [letters(p) for p in open(SRC + path, encoding="utf-8", errors="replace").read().split("\f")]
    return _cache[path]


def where(path: str, quote: str, fuzzy: float | None = None) -> list[int]:
    """The pdf pages (1-based) where the quote stands, exactly by letters or (fuzzy) at least that similar."""
    q = letters(quote)
    hits = [i + 1 for i, p in enumerate(pages(path)) if q in p]
    if hits or not fuzzy:
        return hits
    out = []
    for i, p in enumerate(pages(path)):
        step = max(1, len(q) // 4)
        for k in range(0, max(1, len(p) - len(q) + 1), step):
            w = p[k:k + len(q) + 10]
            m = difflib.SequenceMatcher(None, q, w).find_longest_match(0, len(q), 0, len(w))
            if m.size < len(q) // 4:
                continue
            if difflib.SequenceMatcher(None, q, w).ratio() >= fuzzy:
                out.append(i + 1)
                break
    return out


def check(path: str, quote: str, pdf_page: int, fuzzy: float | None = None) -> None:
    hits = where(path, quote, fuzzy)
    assert pdf_page in hits, (path, quote[:60], pdf_page, hits)
