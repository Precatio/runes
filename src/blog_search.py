"""Sökindexet för artiklarna: ett slimmat JSON med ren text per publicerad artikel, så att sökrutan på
artikelsidan kan hitta artiklar på vilket ord som helst i dem. Samma index byggs på två vägar: lokalt serveras
det av GET /api/blog/search_index, och för den statiska webbplatsen skriver src/site_export.py det till
web/public/artiklar-sok.json i samma format. Diagramblockens rader är siffror och utelämnas; rutornas text och
bildtexterna är läsbar text och följer med."""
from __future__ import annotations

import re


def plain_text(body: str) -> str:
    """Brödtexten som ren, sökbar text: markdown och diagramblock bort, rutors text och bildtexter kvar."""
    out: list[str] = []
    in_chart = False
    for line in (body or "").splitlines():
        s = line.strip()
        m = re.match(r"^:::(\w+)?", s)
        if m:
            in_chart = s.startswith(":::chart")
            if s == ":::":
                in_chart = False
            continue
        if in_chart:
            continue
        s = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", s)      # bild → alt-text
        s = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", s)       # länk → länktext
        s = re.sub(r"(Foto|Photo):.*?(Wikimedia Commons|Riksantikvarieämbetet)\.?", "", s)  # krediter stör utdragen
        s = re.sub(r"^#+\s*", "", s)
        s = s.replace("*", "").replace("_", " ")
        if s:
            out.append(s)
    return re.sub(r"\s+", " ", " ".join(out)).strip()


def build_index(posts: list[dict]) -> list[dict]:
    """Indexposterna för en lista publicerade artiklar (fälten som sökrutan behöver, gement för sökningen)."""
    from src.blog_labels import ENGLISH
    return [{"slug": p.get("slug"), "title": p.get("title") or "", "title_en": p.get("title_en") or "",
             "labels": list(p.get("labels") or []),
             "labels_en": [ENGLISH.get(x, x) for x in (p.get("labels") or [])],
             "text": plain_text(p.get("body") or "").lower(),
             "text_en": plain_text(p.get("body_en") or "").lower(),
             "summary": (p.get("summary") or "").lower(), "summary_en": (p.get("summary_en") or "").lower()}
            for p in posts]
