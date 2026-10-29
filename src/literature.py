"""Litteraturregistret: var avhandlingar och utgåvor om vikingatida runinskrifter nämner en sten.

data/literature/catalog.json listar verken (författare, år, titel, tillgång, filnamn). De verk vars PDF finns i
LITERATURE_DIR (standard /Volumes/2TB/litteratur) indexeras av scripts/build_literature_index.py: texten tas ut sida för
sida (pdftotext), varje runsignum som finns i Rundata letas upp, och för varje träff sparas den tryckta sidan och ett
kort utdrag runt omnämnandet. Indexet ligger i data/cache/literature/index.json och följer inte med kodförrådet, eftersom
det bygger på upphovsrättsskyddade texter; appen visar bara korta utdrag med sidhänvisning.
"""
from __future__ import annotations

import json
import os
import re

from src.signum import fold_signum

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOG = os.path.join(ROOT, "data", "literature", "catalog.json")
INDEX = os.path.join(ROOT, "data", "cache", "literature", "index.json")
DIR = os.environ.get("LITERATURE_DIR", "/Volumes/2TB/litteratur")
SNIPPET = 110  # characters on each side of a mention
LIST_RATIO = 0.3  # distinct signa per word above which a page is a register or list (measured: text ≤ 0.22, registers ≥ 0.47)
_cache: dict[str, tuple[float, dict]] = {}


def _load(path: str) -> dict:
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        return {}
    hit = _cache.get(path)
    if hit and hit[0] == mtime:
        return hit[1]
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    _cache[path] = (mtime, data)
    return data


def catalog() -> list[dict]:
    """Verken, med om de är indexerade och hur många stenar de nämner."""
    idx = _load(INDEX)
    stats = idx.get("works") or {}
    return [{**w, "indexed": w["id"] in stats, "n_stones": (stats.get(w["id"]) or {}).get("n_stones", 0),
             "n_pages": (stats.get(w["id"]) or {}).get("n_pages", 0)} for w in _load(CATALOG).get("works") or []]


def files(work: dict) -> list[str]:
    return [f for f in (work.get("files") or ([work["file"]] if work.get("file") else []))]


def for_stone(signum: str) -> dict:
    """Vad litteraturen i registret säger om stenen: per verk, sidorna och utdragen."""
    idx = _load(INDEX)
    works = {w["id"]: w for w in _load(CATALOG).get("works") or []}
    hits = (idx.get("stones") or {}).get(fold_signum(signum)) or []
    by_work: dict[str, list[dict]] = {}
    for h in hits:
        by_work.setdefault(h["work"], []).append(h)
    out = []
    for wid, hs in by_work.items():
        w = works.get(wid)
        if not w:
            continue
        hs = sorted(hs, key=lambda h: not h.get("entry"))  # the stone's own article in an edition first
        text = [h for h in hs if not h.get("list")]
        lists = [h for h in hs if h.get("list")]
        order = lambda p: (not str(p).isdigit(), int(p) if str(p).isdigit() else 0, str(p))  # noqa: E731
        out.append({"work": {k: w.get(k) for k in ("id", "author", "year", "title", "kind", "series", "url", "access")},
                    "pages": sorted({h["page"] for h in text}, key=order), "n": len(text), "snippets": text[:4],
                    "list_pages": sorted({h["page"] for h in lists}, key=order),
                    "entry_pages": [h["page"] for h in text if h.get("entry")]})
    out.sort(key=lambda x: (x["n"] == 0, x["work"]["kind"] != "avhandling", -x["n"]))
    return {"signum": signum, "works": out, "n_indexed": len(idx.get("works") or {}),
            "built": idx.get("built"), "source_note": "Utdrag ur verken i appens litteraturregister (data/literature/catalog.json)."}


def annotate_findings(items: list[dict]) -> list[dict]:
    """Fynden per sten med var litteraturen i registret diskuterar stenen (inte register och listor). Domen ändras inte –
    att en sten nämns betyder inte att fyndet redan är beskrivet – men ett "nytt" fynd får en anmärkning i nyheten med
    verk och sidor att läsa först. Fynden ändras på plats och returneras."""
    cache: dict[str, list[dict]] = {}
    for f in items:
        sig = f.get("signum")
        if not sig:
            continue
        if sig not in cache:
            cache[sig] = [{"id": w["work"]["id"], "author": w["work"]["author"].split(",")[0], "year": w["work"]["year"],
                           "title": w["work"]["title"], "kind": w["work"]["kind"], "pages": w["pages"],
                           "entry_pages": w["entry_pages"]}
                          for w in for_stone(sig)["works"] if w["pages"]]
        works = cache[sig]
        if not works:
            continue
        f["literature"] = {"works": works, "n_works": len(works)}
        if f.get("verdict") == "nytt":
            refs = "; ".join(f"{w['author']} {w['year']} " + ", ".join(page_label(x) for x in w["pages"][:4]).replace(", s. ", ", ")
                             for w in works[:3])
            note = f"stenen diskuteras i litteraturregistret ({refs}) – läs sidorna innan fyndet kallas nytt"
            reasons = f.setdefault("reasons", {}).setdefault("nyhet", [])
            if note not in reasons:
                reasons.append(note)
    return items


def version() -> float:
    """Indexets ändringstid, för cachenycklar."""
    try:
        return os.path.getmtime(INDEX)
    except OSError:
        return 0.0


# --- indexing (scripts/build_literature_index.py) ---

def signum_pattern(prefixes: list[str]) -> re.Pattern:
    """Ett signum i löptext: prefix (U, Sö, Ög, DR …), valfri punkt, mellanslag, nummer eller Fv-signum."""
    alt = "|".join(sorted((re.escape(p) for p in prefixes), key=len, reverse=True))
    return re.compile(rf"(?<![\wÅÄÖåäöÆØæø])({alt})\.?\s?((?:Fv|NOR|ATA|SvS|ÖgFv|ÖgHC|DR|Sl)?\s?\d{{1,4}}(?:;\d{{1,4}})?[A-Z]?)(?![\d\w])")


def printed_page(page_text: str, fallback: int) -> str:
    """Sidans tryckta nummer: en rad med bara ett tal högst upp eller längst ned, eller ett tal först eller sist i ett
    sidhuvud med versaler (SRI: "252 VÄSTERGÖTLAND. VILSKE HÄRAD." eller "… LYSINGS HD. 127"); annars PDF-sidan."""
    lines = [ln.strip() for ln in page_text.splitlines() if ln.strip()]
    for ln in lines[:2][::-1] + lines[-2:][::-1]:
        if re.fullmatch(r"\d{1,4}", ln):
            return ln
    if lines:
        head = lines[0]
        caps = sum(ch.isupper() for ch in head) > 8
        m = re.search(r"\s(\d{1,4})$", head) or re.match(r"^(\d{1,4})\s", head)
        if caps and m:
            return m.group(1)
    return f"pdf {fallback}"


def fill_pages(pages: list[str]) -> list[str]:
    """Sidor utan läsbart nummer (OCR) får numret mellan grannarnas, när sidan före och efter skiljer sig med två."""
    out = list(pages)
    for i in range(1, len(out) - 1):
        a, b = out[i - 1], out[i + 1]
        if out[i].startswith("pdf") and a.isdigit() and b.isdigit() and int(b) - int(a) == 2:
            out[i] = str(int(a) + 1)
    return out


def page_label(p: str) -> str:
    """"342" -> "s. 342", "pdf 40" -> "pdf-sida 40"."""
    return f"pdf-sida {p[4:]}" if p.startswith("pdf ") else f"s. {p}"


# SRI's own article for a stone: "179. Kölaby sn, Stommen." or "233. Östra Stenby kyrka, Östkinds hd."
ENTRY = re.compile(r"^\s*(\d{1,3})\.\s+[A-ZÅÄÖ][^\n]{2,90}?\b(?:sn|socken|kyrka|kyrkogård|hd|stad|landsförs)\b", re.M)
