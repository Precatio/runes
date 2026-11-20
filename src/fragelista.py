"""Öppna frågor i forskningen: frågelistan ur litteraturgenomgången, i Forskningsluckor i den LOKALA appen.

Frågelistan (301 frågor ur Fornvännen 1906–2023 och Futhark 1–15, bedömda efter hur relevant Vitkis bidrag vore för
forskningen) är ett INTERNT styrdokument (PUBLICERINGSPLAN.md, "det vi behåller": hur varje fråga prövas, påstående-
databasen och relevansmotiveringarna stannar hos oss tills studien är publicerad). Den visas därför bara i den lokala
appen: sidan /luckor ligger under web/src/app/(app), som den publika byggen tar bort (.github/workflows/site.yml), och
API:t finns inte på den publika webbplatsen. Svaret innehåller inte relevansmotiveringarna eller hur frågan ska prövas.

Per fråga:
  källor        påståendena som frågan bygger på (utdata/litteraturgenomgang/pastaenden.jsonl), med författare, år,
                tidskrift, tryckt sida (scripts/build_fragelista_sidor.py) och det korta ordagranna citatet
  relevansklass 1 avgörande, 2 betydande, 3 användbar, 4 begränsad (bygg_fragelista.py LEVEL)
  studie        studien i publiceringsplanen (bygg_fragelista.py STUDIER) och dess läge, läst ur planens tabell i
                PUBLICERINGSPLAN.md: körd (planens status nämner resultat), låst plan, eller planerad; analysplanerna
                för studien (analysplaner/<år>-<mån>-<kod>-*.md, låst när en .sha256 ligger bredvid)
  artiklar      publicerade artiklar (web/content/articles.json) som delar minst fem innehållsord med frågan –
                en automatisk ordlikhet, inte en kontrollerad koppling
"""
from __future__ import annotations

import glob
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUESTIONS = os.path.join(ROOT, "utdata", "litteraturgenomgang", "artikelkandidater", "fragelista.jsonl")
CLAIMS = os.path.join(ROOT, "utdata", "litteraturgenomgang", "pastaenden.jsonl")
PAGES = os.path.join(ROOT, "data", "cache", "literature", "fragelista_sidor.json")
PLAN = os.path.join(ROOT, "PUBLICERINGSPLAN.md")
PLANS_DIR = os.path.join(ROOT, "analysplaner")
ARTICLES = os.path.join(ROOT, "web", "content", "articles.json")
REPO = "https://github.com/Precatio/runes/blob/main/analysplaner/"
LEVEL = {1: "avgörande", 2: "betydande", 3: "användbar", 4: "begränsad"}
LEVEL_HELP = {
    1: "Ett svar skulle avgöra en fråga som många andra resultat vilar på.",
    2: "Ett svar skulle ändra hur ett större forskningsfält läser sitt material.",
    3: "Ett svar ger ny kunskap, ofta beskrivande, med data vi redan har.",
    4: "Ett svar har ett begränsat värde för forskningen, eller data saknas.",
}
JOURNAL = {"fornvannen": "Fornvännen", "futhark": "Futhark"}
# Studies whose plans do not carry the study code in the file name (PUBLICERINGSPLAN.md, section 1)
PLAN_FILES = {"B": ["2026-11-10-sjalvkontroll-*.md", "2026-11-10-lerkanten-kontroller.md", "2026-11-10-riktning-vaglinjer.md"]}
MIN_SHARED = 5
NOTE = ("Internt styrdokument (PUBLICERINGSPLAN.md): visas bara i den lokala appen och ska inte publiceras, citeras "
        "eller delas förrän studien bakom frågan är publicerad.")
_STOP = set(("och i på av om för en ett de den det som till med vid mot eller är var vad hur men från runstenarna "
             "stenarna stenar runstenar runsten stenen runstenen vikingatiden vikingatida också egentligen bara andra "
             "mellan efter under genom inte många procent").split())

_cache: dict[str, tuple[float, object]] = {}


def _mtime(path: str) -> float:
    try:
        return os.path.getmtime(path)
    except OSError:
        return 0.0


def _cached(path: str, build):
    m = _mtime(path)
    hit = _cache.get(path)
    if hit and hit[0] == m:
        return hit[1]
    val = build() if m else None
    _cache[path] = (m, val)
    return val


def _jsonl(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as fh:
        return [json.loads(ln) for ln in fh if ln.strip()]


def available() -> bool:
    return os.path.exists(QUESTIONS)


def questions_raw() -> list[dict]:
    return _cached(QUESTIONS, lambda: _jsonl(QUESTIONS)) or []


def claims() -> dict[str, dict]:
    keep = ("id", "key", "journal", "year", "authors", "title", "quote", "priority")
    return _cached(CLAIMS, lambda: {c["id"]: {k: c.get(k) for k in keep} for c in _jsonl(CLAIMS)}) or {}


def pages() -> dict[str, str]:
    return (_cached(PAGES, lambda: json.load(open(PAGES, encoding="utf-8"))) or {}).get("pages") or {}


def study_code(label: str | None) -> str | None:
    """"jan–feb 2027 – A1. Flyttade och försvunna stenar" → "A1"; "mar–apr 2029 – Språkets klockor" → "Språkets
    klockor"; spår P och "2029 eller spår P" → None."""
    if not label or "spår P" in label or "Spår P" in label:
        return None
    rest = label.split(" – ", 1)[-1].strip()
    m = re.match(r"([A-Z]\d?)\.\s", rest)
    return m.group(1) if m else rest


def _clean_md(s: str) -> str:
    s = re.sub(r"\*\*|`", "", s)
    return re.sub(r"\s+", " ", s).strip()


def plan_table() -> dict[str, dict]:
    """Studierna i PUBLICERINGSPLAN.md:s tabell för forskningsspåret: kod → period, namn, rapport och status."""
    def build():
        out = {}
        text = open(PLAN, encoding="utf-8").read()
        for ln in text.splitlines():
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            if len(cells) != 6 or not cells[1].startswith("**"):
                continue
            name = re.match(r"\*\*(.+?)\*\*", cells[1])
            if not name:
                continue
            code = study_code("x – " + name.group(1))
            out[code] = {"period": cells[0], "name": _clean_md(cells[1]), "report": _clean_md(cells[4]),
                         "status": _clean_md(cells[5])}
        return out
    return _cached(PLAN, build) or {}


def state(status: str | None) -> str:
    """Studiens läge ur planens statuskolumn: körd, låst plan eller planerad."""
    s = (status or "").lower()
    if re.search(r"\bkörd\b|håller|föll|står sig|försvagat|resultat", s):
        return "körd"
    if "plan låst" in s or "låst" in s:
        return "låst plan"
    return "planerad"


def plans_for(code: str | None) -> list[dict]:
    if not code:
        return []
    pats = PLAN_FILES.get(code) or ([f"20[0-9][0-9]-[0-9][0-9]-{code}-*.md"] if re.fullmatch(r"[A-Z]\d?", code) else [])
    files = sorted({os.path.basename(p) for pat in pats for p in glob.glob(os.path.join(PLANS_DIR, pat))})
    out = []
    for f in files:
        stem = f[:-3]
        locked = any(os.path.exists(os.path.join(PLANS_DIR, x)) for x in (f"{stem}.sha256", f"{f}.sha256"))
        out.append({"file": f, "locked": locked, "url": REPO + f})
    return out


def _tokens(s: str) -> set[str]:
    return {w[:6] for w in re.findall(r"[a-zåäöé]{5,}", (s or "").lower()) if w not in _STOP}


def _posts() -> list[dict]:
    return _cached(ARTICLES, lambda: [{"title": p.get("title"), "slug": p.get("slug"), "month": p.get("month"),
                                       "tokens": _tokens(" ".join(str(p.get(k) or "") for k in ("title", "seo_title", "summary")))}
                                      for p in json.load(open(ARTICLES, encoding="utf-8")).get("posts") or []]) or []


def article_matches(q: dict, posts: list[dict] | None = None, limit: int = 3) -> list[dict]:
    qt = _tokens(f"{q.get('titel', '')} {q.get('fraga', '')}")
    out = []
    for p in posts if posts is not None else _posts():
        shared = qt & p["tokens"]
        if len(shared) >= MIN_SHARED:
            out.append({"title": p["title"], "slug": p["slug"], "url": f"/artiklar/{p['slug']}/", "shared": len(shared)})
    out.sort(key=lambda x: -x["shared"])
    return out[:limit]


def _source(cid: str, c: dict, page: str | None) -> dict:
    authors = c.get("authors") or ""
    author = authors.split(";")[0].split(",")[0].strip() if isinstance(authors, str) else str(authors)
    return {"id": cid, "author": author or None, "year": c.get("year"), "title": c.get("title"),
            "journal": JOURNAL.get(c.get("journal") or "", c.get("journal")), "key": c.get("key"),
            "page": (f"pdf-sida {page[4:]}" if page.startswith("pdf ") else f"s. {page}") if page else None,
            "quote": c.get("quote")}


def questions() -> dict:
    """Frågelistan för kortet, med källor, relevansklass och studiens läge."""
    if not available():
        return {"available": False, "internal": True, "note": NOTE, "questions": []}
    cl, pg, table, posts = claims(), pages(), plan_table(), _posts()
    out = []
    for n, q in enumerate(questions_raw(), start=1):
        code = study_code(q.get("studie"))
        row = table.get(code) if code else None
        sources = []
        for cid in q.get("pastaenden") or []:
            c = cl.get(cid)
            if c:
                sources.append(_source(cid, c, pg.get(cid)))
        # Newest first, and the claims with a printed page before the rest
        sources.sort(key=lambda s: (s["page"] is None or s["page"].startswith("pdf"), -int(str(s["year"] or 0)[:4] or 0)))
        plans = plans_for(code)
        st = state(row["status"]) if row else ("reservlista" if not code else "planerad")
        if st == "planerad" and any(p["locked"] for p in plans):
            st = "låst plan"
        out.append({
            "nr": n, "title": q.get("titel"), "question": q.get("fraga"), "theme": q.get("tema"),
            "level": q.get("relevans"), "level_label": LEVEL.get(q.get("relevans"), ""),
            "study": q.get("studie"), "study_code": code, "study_state": st,
            "study_status": row["status"] if row else None, "study_report": row["report"] if row else None,
            "plans": plans, "articles": article_matches(q, posts),
            "n_claims": len(q.get("pastaenden") or []), "n_texts": q.get("antal_texter"),
            "decades": q.get("decennier_lista") or [], "sources": sources,
        })
    from collections import Counter
    return {"available": True, "internal": True, "note": NOTE, "n": len(out),
            "levels": {LEVEL[k]: v for k, v in sorted(Counter(q["level"] for q in out).items()) if k in LEVEL},
            "level_help": {LEVEL[k]: v for k, v in LEVEL_HELP.items()},
            "states": dict(Counter(q["study_state"] for q in out)),
            "pages_found": sum(1 for q in out for s in q["sources"] if s["page"]),
            "n_sources": sum(len(q["sources"]) for q in out),
            "min_shared": MIN_SHARED, "questions": out}
