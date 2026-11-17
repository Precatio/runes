"""SRI:s fyndhistorik per sten (A1, tillägg 1), bredvid Rundata – visas, räknas inte på.

Utplockningen ur Sveriges runinskrifter ligger UTANFÖR repot, eftersom den innehåller korta citat ur utgåvan
(källregeln, METHODS §17): /Volumes/2TB/Antigrvity/Runes/downloads/sri_fakta/<enhet>.jsonl. Finns filerna inte,
visas ingenting (som Runor 2020 i src/runor.py).

Bara de fältgrupper som klarade granskningen visas: läget (läge när bandet skrevs, ursprunglig plats, inmurad),
försvunnen och återfunnen, och samma sten (noterna 7–9). Flyttningarna klarade inte kraven och visas inte.
Not 9:s rättning av "inmurad" (kyrkogårdsmur m.m.) tillämpas via scripts/sri_fakta_kontroll.slutlig.

Fälten används inte i någon beräkning i appen före A1-körningen (analysplaner/2027-01-A1-*.md).
"""
from __future__ import annotations

import json
import os
import re
import sys
import threading
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAKTA = "/Volumes/2TB/Antigrvity/Runes/downloads/sri_fakta"
ARTIKLAR = "/Volumes/2TB/Antigrvity/Runes/downloads/sri_artiklar"
# de slutliga utplockningarna per enhet (not 9): Uppland runda 2, Östergötland och Västergötland runda 2, Öland runda 2
ENHETER = {"sri3": "Viktor", "upp2": "Viktor", "sm": "Viktor", "og2": "Claude", "vg2": "Claude", "ol2": "Claude",
           "msv": "Claude", "got": "Claude"}
VERK = ["sri1", "sri2", "sri3", "sri4", "sri5", "sri6", "sri7", "sri8", "sri9", "sri11", "sri12", "sri13", "sri14a",
        "sri14b", "sri15", "gr3"]
METOD = ("Utplockat ur Sveriges runinskrifter av Anthropics språkmodell Claude (Sonnet), granskat fält för fält av "
         "Claude Opus i stickprov om 40–100 stenar per landskap (95–100 % rätt för de fält som visas här), med en "
         "kontroll av Viktor Kvant eller en oberoende omläsning. Analysplan A1, tillägg 1, noterna 1–9.")

_lock = threading.Lock()
_index: dict | None = None


def _key(signum: str) -> str:
    return re.sub(r"[\s_]+", "", unicodedata.normalize("NFC", signum or ""))


def available() -> bool:
    return os.path.exists(os.path.join(FAKTA, "sri3.jsonl"))


def _load() -> dict:
    global _index
    with _lock:
        if _index is not None:
            return _index
        idx: dict = {}
        if not available():
            _index = idx
            return idx
        sys.path.insert(0, ROOT)
        from scripts.sri_fakta_kontroll import slutlig  # noqa: E402
        works = {w["id"]: w for w in json.load(open(os.path.join(ROOT, "data", "literature", "catalog.json"),
                                                     encoding="utf-8")).get("works") or []}
        verk_av: dict = {}
        for v in VERK:
            p = os.path.join(ARTIKLAR, f"{v}.jsonl")
            if os.path.exists(p):
                for ln in open(p, encoding="utf-8"):
                    verk_av.setdefault(_key(json.loads(ln)["signum"]), v)
        for enhet, kontroll in ENHETER.items():
            p = os.path.join(FAKTA, f"{enhet}.jsonl")
            if not os.path.exists(p):
                continue
            for ln in open(p, encoding="utf-8"):
                if not ln.strip():
                    continue
                r = slutlig(json.loads(ln))
                k = _key(r["signum"])
                w = works.get(verk_av.get(k) or "", {})
                idx[k] = {"row": r, "verk": w.get("title"), "ar": w.get("year"), "url": w.get("url"),
                          "kontroll": kontroll}
        _index = idx
        return idx


def _tvatta(s):
    """Bara blanksteg och radbrytningar jämnas ut. Spärrad text ('a t t h a n') lämnas som den står: ordgränserna i
    spärrningen gick förlorade i OCR:n och går inte att återskapa säkert."""
    if not isinstance(s, str):
        return s
    return re.sub(r"\s+", " ", s).strip()


def _sida(s):
    if not s:
        return None
    s = str(s)
    return f"pdf-sida {s[4:]}" if s.startswith("pdf ") else s


def _post(p: dict | None, varde_key: str = "varde") -> dict | None:
    if not p:
        return None
    return {"value": _tvatta(p.get(varde_key)), "page": _sida(p.get("sida")), "quote": _tvatta(p.get("citat"))}


def for_inscription(rec: dict) -> dict | None:
    """SRI:s uppgifter för en Rundata-post, i den form appen visar; None när utplockningen saknas för stenen."""
    hit = _load().get(_key(rec.get("signum", "")))
    if not hit:
        return None
    r = hit["row"]
    fv = r.get("forsvunnen")
    return {
        "volume": hit["verk"], "year": hit["ar"], "url": hit["url"], "checked_by": hit["kontroll"], "method": METOD,
        "position": _post(r.get("lage_vid_utgavan")),
        "original_place": _post(r.get("ursprunglig_plats_text")),
        "built_in": _post(r.get("inmurad")),
        "built_in_corrected": r.get("inmurad_rattad"),
        "lost": {"lost_at_edition": fv.get("forsvunnen_vid_utgavan"), "year": fv.get("forsvann_ar"),
                 "page": _sida(fv.get("sida")), "quote": _tvatta(fv.get("citat"))} if fv else None,
        "refound": [{"year": a.get("ar"), "place": _tvatta(a.get("plats")), "page": _sida(a.get("sida")),
                     "quote": _tvatta(a.get("citat"))} for a in (r.get("aterfunnen") or []) if a],
        "same_stone": [{"value": _tvatta(s.get("varde")), "page": _sida(s.get("sida")), "quote": _tvatta(s.get("citat"))}
                       for s in (r.get("samma_sten_som") or []) if s],
    }
