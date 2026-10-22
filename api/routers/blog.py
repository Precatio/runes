"""Artiklarna på /artiklar (tidigare Månadens fynd): de mest intressanta mönstren och fynden.

Inläggen ligger i Firestore-samlingen `posts` och skrivs och läses bara av servern (Firebase Admin SDK), så att
samlingen kan vara stängd för webbläsarna (firestore.rules). Grundaren skriver och publicerar i Admin; utkastet från
månadens fynd bygger på de mönster som är nya eller har ändrat status sedan förra publicerade inlägget, och på den
största förskjutningen i mönsterkartan. Inget publiceras automatiskt.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.auth import firestore, require_admin
from api.errors import server_error

router = APIRouter()
COLLECTION = "posts"
SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,79}$")
MONTH = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
PUBLIC = ("id", "slug", "title", "summary", "title_en", "summary_en", "month", "author", "publishedAt", "updatedAt", "featured",
          "labels")


class PostRequest(BaseModel):
    id: str | None = Field(None, max_length=64)
    slug: str = Field(..., min_length=1, max_length=80)
    title: str = Field(..., min_length=1, max_length=160)
    summary: str = Field("", max_length=600)
    body: str = Field(..., min_length=1, max_length=40000)
    title_en: str = Field("", max_length=160)
    summary_en: str = Field("", max_length=600)
    body_en: str = Field("", max_length=40000)
    # The month is kept for older articles; it is set from the publication date
    month: str = Field("", max_length=7)
    author: str = Field("", max_length=120)
    published: bool = False
    # A time in the future (ISO 8601) when a published article goes live; empty: now
    publish_at: str | None = Field(None, max_length=40)
    # The R pattern the post is about (src/blog_topics.py), so that the list of topics can show which are written
    topic: str = Field("", max_length=160)
    # "Veckans artikel": shown first and large on the start page and first in the list, whatever its date; one at a time
    featured: bool = False
    # Etiketter ur den fasta listan (src/blog_labels.py): en typ och ett eller flera ämnen
    labels: list[str] = Field(default_factory=list, max_length=8)


def _iso(d: dict) -> dict:
    return {k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in d.items()}


# The posts change only when the founder saves, so they are read from Firestore at most once a minute (and again at once
# after a save or a deletion)
_POSTS: dict = {"at": 0.0, "posts": None}
POSTS_TTL = 60


def _all() -> list[dict]:
    import time
    if _POSTS["posts"] is not None and time.time() - _POSTS["at"] < POSTS_TTL:
        return [dict(p) for p in _POSTS["posts"]]
    try:
        docs = firestore().collection(COLLECTION).stream()
        posts = [{"id": d.id, **_iso(d.to_dict())} for d in docs]
    except Exception as e:
        raise server_error(e, "Blogginläggen kunde inte hämtas.", status_code=503) from e
    _POSTS.update(at=time.time(), posts=posts)
    return [dict(p) for p in posts]


def _forget() -> None:
    _POSTS.update(at=0.0, posts=None)


# Every article as it was before a save overwrote it or a deletion removed it, as JSON on this machine (git-ignored):
# data/backup/posts/<id>/<UTC time>.json. Firestore keeps no history of its own, so this is what undoes a bad save.
BACKUP = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "backup", "posts")


def _backup(post_id: str, doc: dict | None) -> None:
    """Saves the previous version of an article; a failure is logged and never stops the save."""
    if not doc:
        return
    try:
        folder = os.path.join(BACKUP, re.sub(r"[^\w-]", "_", post_id))
        os.makedirs(folder, exist_ok=True)
        stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H%M%S.%fZ")
        with open(os.path.join(folder, f"{stamp}.json"), "w", encoding="utf-8") as fh:
            json.dump({"id": post_id, **_iso(doc)}, fh, ensure_ascii=False, indent=1, default=str)
    except Exception as e:  # noqa: BLE001 - the backup must never block the save
        from api.errors import logger
        logger.warning("Artikeln %s kunde inte säkerhetskopieras före ändringen: %r", post_id, e)


def _ts(v) -> dt.datetime | None:
    """An ISO time (or a datetime) as an aware UTC datetime, or None."""
    if v is None or v == "":
        return None
    if isinstance(v, dt.datetime):
        t = v
    else:
        try:
            t = dt.datetime.fromisoformat(str(v).replace("Z", "+00:00"))
        except ValueError:
            return None
    return (t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)).astimezone(dt.timezone.utc)


def is_live(p: dict, now: dt.datetime | None = None) -> bool:
    """Published and its publication time has come: a scheduled article goes live by itself when the time is reached."""
    if not p.get("published"):
        return False
    t = _ts(p.get("publishedAt"))
    return t is None or t <= (now or dt.datetime.now(dt.timezone.utc))


def _published() -> list[dict]:
    """The live articles, newest first. One that has just gone live (scheduled) is announced to the search engines."""
    now = dt.datetime.now(dt.timezone.utc)
    posts = [p for p in _all() if is_live(p, now)]
    for p in posts:
        if not p.get("announced") and indexnow(p["slug"]):
            try:
                firestore().collection(COLLECTION).document(p["id"]).set({"announced": True}, merge=True)
                _forget()
            except Exception:  # noqa: BLE001 - announced again next time
                pass
    return sorted(posts, key=lambda p: (p.get("publishedAt") or p.get("month") or ""), reverse=True)


def first_photo(body: str | None, alt: bool = False) -> str | None:
    """The article's first photo from Wikimedia Commons (a line of its own, ![…](…)), for the list's thumbnail;
    figures and charts are not used. alt: its alt text (what the photo shows) instead of its address."""
    for m in re.finditer(r"^!\[([^\]]*)\]\((\S+?)\)", body or "", re.M):
        if "wikimedia.org" in m.group(2):
            return (m.group(1) or None) if alt else m.group(2)
    return None


@router.get("/blog/posts")
def list_posts():
    """De publicerade inläggen, nyaste först (utan brödtext, men med första fotot som miniatyr)."""
    return {"posts": [{**{k: p.get(k) for k in PUBLIC}, "image": first_photo(p.get("body")),
                       "image_alt": first_photo(p.get("body"), alt=True)} for p in _published()]}


@router.get("/blog/search_index")
def search_index():
    """Sökindexet för artikelsidans sökruta: ren text per publicerad artikel (src/blog_search.py). Den statiska
    webbplatsen får samma index som /artiklar-sok.json ur exporten."""
    from src.blog_search import build_index
    return {"posts": build_index(_published())}


@router.get("/blog/posts/{slug}")
def get_post(slug: str):
    for p in _published():
        if p.get("slug") == slug:
            return {"post": {k: v for k, v in p.items() if k not in ("by", "snapshot", "published")}}
    raise HTTPException(status_code=404, detail="Artikeln finns inte eller är inte publicerad.")


@router.get("/admin/blog/posts")
def admin_posts(_: dict = Depends(require_admin)):
    """Alla artiklar, också utkast och schemalagda, nyaste först."""
    posts = sorted(_all(), key=lambda p: (p.get("publishedAt") or p.get("updatedAt") or ""), reverse=True)
    return {"posts": [{k: v for k, v in p.items() if k != "snapshot"} for p in posts]}


@router.post("/admin/blog/posts")
def save_post(req: PostRequest, admin: dict = Depends(require_admin)):
    """Sparar ett utkast, publicerar nu eller schemalägger (publish_at): artikeln får publiceringstiden som datum och
    syns först när tiden är nådd. Första gången sparas mönstrens läge, som nästa utkast jämförs med."""
    if not SLUG.match(req.slug):
        raise HTTPException(status_code=422, detail="Adressen får bara innehålla små bokstäver a–z, siffror och bindestreck.")
    if req.month and not MONTH.match(req.month):
        raise HTTPException(status_code=422, detail="Månaden ska anges som ÅÅÅÅ-MM.")
    from src import blog_labels
    if (bad := blog_labels.check(req.labels)):
        raise HTTPException(status_code=422, detail=bad)
    req.labels = blog_labels.ordered(req.labels)
    publish_at = _ts(req.publish_at) if req.publish_at else None
    if req.publish_at and publish_at is None:
        raise HTTPException(status_code=422, detail="Publiceringstiden kunde inte läsas.")
    others = [p for p in _all() if p["id"] != req.id]
    if any(p.get("slug") == req.slug for p in others):
        raise HTTPException(status_code=409, detail=f"Adressen /artiklar/{req.slug} används redan av en annan artikel.")
    now = dt.datetime.now(dt.timezone.utc)
    data = {**req.model_dump(exclude={"id", "publish_at"}), "updatedAt": now, "by": admin["uid"]}
    announce = False
    try:
        col = firestore().collection(COLLECTION)
        ref = col.document(req.id) if req.id else col.document()
        old = (ref.get().to_dict() if req.id else None) or {}
        if req.published:
            data["publishedAt"] = publication_time(publish_at, _ts(old.get("publishedAt")), now)
            data["month"] = data["publishedAt"].strftime("%Y-%m")
            if not old.get("snapshot"):
                data["snapshot"] = _snapshot()
            announce = data["publishedAt"] <= now and not old.get("announced")
        else:
            data["month"] = req.month or old.get("month") or now.strftime("%Y-%m")
        if not old:
            data["createdAt"] = now
        _backup(ref.id, old)
        ref.set(data, merge=True)
        if req.featured:  # only one article of the week
            for p in others:
                if p.get("featured"):
                    col.document(p["id"]).set({"featured": False}, merge=True)
        _forget()
    except HTTPException:
        raise
    except Exception as e:
        raise server_error(e, "Artikeln kunde inte sparas.", status_code=503) from e
    if announce and indexnow(req.slug):
        ref.set({"announced": True}, merge=True)
    # The public website: published or changed articles go out within half a minute, scheduled ones at their time
    from src import site_export
    if req.published or old.get("published"):
        site_export.publish_soon()
    site_export.schedule(_all())
    return {"post": {"id": ref.id, **_iso({k: v for k, v in data.items() if k != "snapshot"})}}


class FeaturedRequest(BaseModel):
    # The article to make the article of the week; empty: none
    id: str | None = Field(None, max_length=64)


@router.post("/admin/blog/featured")
def set_featured(req: FeaturedRequest, _: dict = Depends(require_admin)):
    """Gör en artikel till veckans artikel direkt i listan, utan att öppna den (eller ingen, med tomt id). Bara en åt
    gången; datum och text ändras inte. Webbplatsen publiceras om en halv minut, eftersom startsidan och listan ändras."""
    posts = _all()
    if req.id and not any(p["id"] == req.id for p in posts):
        raise HTTPException(status_code=404, detail="Artikeln finns inte.")
    try:
        col = firestore().collection(COLLECTION)
        for p in posts:
            want = p["id"] == req.id
            if bool(p.get("featured")) != want:
                col.document(p["id"]).set({"featured": want}, merge=True)
        _forget()
    except Exception as e:
        raise server_error(e, "Veckans artikel kunde inte sparas.", status_code=503) from e
    from src import site_export
    site_export.publish_soon()
    return {"featured": req.id or None}


def publication_time(publish_at: dt.datetime | None, before: dt.datetime | None, now: dt.datetime) -> dt.datetime:
    """When a published article goes live: the chosen time (scheduled), the date it already had if it was live before,
    or now (the first time, or when a scheduled article is published at once)."""
    if publish_at is not None:
        return publish_at
    if before is not None and before <= now:
        return before
    return now


def indexnow(slug: str) -> bool:
    """Tells the search engines that use IndexNow (Bing, Yandex, Seznam, Naver …) about a newly published post, the
    blog and the sitemap, in the background. Only when INDEXNOW_KEY is set (in production; the key is served at
    /indexnow-key.txt by the web app) and SITE_URL is a public https address – never from a local machine."""
    import os
    import threading
    key, site = os.environ.get("INDEXNOW_KEY", "").strip(), os.environ.get("SITE_URL", "https://vitkirunor.se").rstrip("/")
    if not key or not site.startswith("https://") or "localhost" in site:
        return False
    host = site.split("://", 1)[1].split("/", 1)[0]
    body = {"host": host, "key": key, "keyLocation": f"{site}/indexnow-key.txt",
            "urlList": [f"{site}/artiklar/{slug}", f"{site}/artiklar", f"{site}/sitemap.xml"]}

    def ping():
        import requests
        from api.errors import logger
        try:
            r = requests.post("https://api.indexnow.org/indexnow", json=body, timeout=10)
            logger.info("IndexNow %s: %s", slug, r.status_code)
        except Exception as e:  # noqa: BLE001 - a failed ping only delays indexing
            logger.warning("IndexNow misslyckades: %r", e)
    threading.Thread(target=ping, daemon=True).start()
    return True


@router.delete("/admin/blog/posts/{post_id}")
def delete_post(post_id: str, _: dict = Depends(require_admin)):
    from src import site_export
    try:
        ref = firestore().collection(COLLECTION).document(post_id)
        old = ref.get().to_dict() or {}
        was_published = bool(old.get("published"))
        _backup(post_id, old)
        ref.delete()
        _forget()
    except Exception as e:
        raise server_error(e, "Inlägget kunde inte tas bort.", status_code=503) from e
    if was_published:
        site_export.publish_soon()
    site_export.schedule(_all())
    return {"id": post_id, "deleted": True}


# ---- utkastet från månadens fynd ----------------------------------------------------------------------------------

RANK = {"mönster att pröva": 0, "bekräftar": 1, "indikation": 2}


def _patterns() -> list[dict]:
    from api.routers import rstats
    return [p for p in rstats.findings()[1] if p.get("status") in RANK]


def _key(p: dict) -> str:
    return f"{p.get('topic')}|{p.get('key')}"


def _snapshot() -> dict[str, str]:
    """Mönstrens status vid publiceringen, så att nästa utkast kan visa vad som är nytt."""
    try:
        return {_key(p): p["status"] for p in _patterns()}
    except Exception:  # noqa: BLE001 - utan R-resultat sparas inget läge
        return {}


def _last_snapshot() -> dict[str, str]:
    try:
        posts = [p for p in _published() if p.get("publishedAt")]
        if not posts:
            return {}
        last = max(posts, key=lambda p: p["publishedAt"])
        doc = firestore().collection(COLLECTION).document(last["id"]).get().to_dict() or {}
        return doc.get("snapshot") or {}
    except Exception:  # noqa: BLE001 - utan Firestore jämförs inget: alla mönster räknas som nya
        return {}


def _first_sentence(text: str) -> str:
    s = re.split(r"(?<=[a-zåäö0-9)])\.\s", text, maxsplit=1)[0]
    s = re.split(r"\s\(|:\s", s, maxsplit=1)[0]
    return s.rstrip(".") if len(s) <= 110 else s[:107].rsplit(" ", 1)[0] + " …"


@lru_cache(maxsize=1)
def _map_shift() -> dict | None:
    """Den största skillnaden i andel före och efter omkring 1050 bland mönsterkartans mönster (minst 50 stenar per period)."""
    from api.rundata import store
    from api.routers.orthography import model
    from src import pattern_map
    data = pattern_map.build(store().inscriptions, model().names)
    keys = [p["key"] for p in data["patterns"]]
    best = None
    for i, p in enumerate(data["patterns"]):
        if p["group"] == "Tro" and p["key"] == "hednisk":
            continue  # för få stenar för en andel
        early = [s["v"][i] for s in data["stones"] if s["y"] is not None and s["y"] < 1050 and s["v"][i] is not None]
        late = [s["v"][i] for s in data["stones"] if s["y"] is not None and s["y"] >= 1050 and s["v"][i] is not None]
        if len(early) < 50 or len(late) < 50:
            continue
        a, b = sum(early) / len(early), sum(late) / len(late)
        if best is None or abs(b - a) > abs(best["late"] - best["early"]):
            best = {"key": keys[i], "label": p["label"], "early": a, "late": b, "n_early": len(early), "n_late": len(late)}
    return best


def _pct(x: float) -> str:
    return f"{round(x * 100)} %"


# The draft's own sentences in both languages; the patterns' texts are translated with the app's catalog (src/i18n.py)
WORDS = {
    "sv": {
        "title": "Månadens mönster",
        "first_summary": "Det första inlägget om de mönster Vitki har hittat i runstenarna – vad vi ser, vad det kan betyda "
                         "och hur det kan prövas.",
        "summary": "{n} mönster är nya eller har ändrat status sedan förra inlägget. Det tydligaste: {lead}.",
        "first_intro": "Det här är det första inlägget om mönstren i Vitkis analyser av de svenska vikingatida runstenarna.",
        "intro": "Här är de mönster som är nya eller har ändrat status sedan förra inlägget.",
        "three": "Varje mönster har tre delar: vad vi ser, en hypotes om vad det kan betyda och hur hypotesen kan prövas.",
        "see": "Vad vi ser.", "hypothesis": "Hypotes.", "test": "Så kan den prövas.", "status": "Status",
        "both": "håller i båda halvorna av korpusen",
        "map": "Månadens karta",
        "shift": "Den största förskjutningen i mönsterkartan gäller {label}: {early} av stenarna före omkring "
                 "1050 ({n_early} stenar) och {late} efter ({n_late} stenar), bland stenar med säker stilgrupp.",
        "outro": "Alla siffror kommer från Vitkis analyser. Vitki är öppen källkod och kan laddas ner från "
                 "[GitHub](https://github.com/Precatio/runes); metoderna beskrivs i "
                 "[METHODS.md](https://github.com/Precatio/runes/blob/main/METHODS.md).",
        "short": "Kort sagt", "sure": "Så säkra är vi",
        "sure_note": "Mönstren är prövade med justering för många test och, där det går, i korpusens två halvor, "
                     "uppdelade socken för socken. Skriv om rutan med egna ord: vad har prövats, och vad kan ändå vara fel?",
    },
    "en": {
        "title": "Patterns of the month",
        "first_summary": "The first post about the patterns Vitki has found in the runestones – what we see, what it may "
                         "mean and how it can be tested.",
        "summary": "{n} patterns are new or have changed status since the last post. The clearest: {lead}.",
        "first_intro": "This is the first post about the patterns in Vitki's analyses of the Swedish Viking Age runestones.",
        "intro": "Here are the patterns that are new or have changed status since the last post.",
        "three": "Each pattern has three parts: what we see, a hypothesis about what it may mean and how the hypothesis "
                 "can be tested.",
        "see": "What we see.", "hypothesis": "Hypothesis.", "test": "How it can be tested.", "status": "Status",
        "both": "holds in both halves of the corpus",
        "map": "The map of the month",
        "shift": "The largest shift in the pattern map concerns {label}: {early} of the stones before about "
                 "1050 ({n_early} stones) and {late} after ({n_late} stones), among stones with a certain style group.",
        "outro": "All numbers come from Vitki's analyses. Vitki is open source and can be downloaded from "
                 "[GitHub](https://github.com/Precatio/runes); the methods are described in "
                 "[METHODS.md](https://github.com/Precatio/runes/blob/main/METHODS.md).",
        "short": "In short", "sure": "How sure we are",
        "sure_note": "The patterns are tested with adjustment for many tests and, where possible, in the two halves of the "
                     "corpus, split parish by parish. Rewrite the box in your own words: what has been tested, and what "
                     "could still be wrong?",
    },
}


def _pick(patterns: list[dict], before: dict[str, str]) -> tuple[list[dict], list[dict]]:
    """The patterns that are new or changed since the last post, the patterns to test first; and the four to write about."""
    changed = [p for p in patterns if before.get(_key(p)) != p["status"]]
    changed.sort(key=lambda p: (RANK[p["status"]], not p.get("replicated"), p.get("topic", "")))
    return changed, changed[:4]


def _write(lang: str, month: str, changed: list[dict], picked: list[dict], first: bool, shift: dict | None) -> dict:
    from src import i18n
    w = WORDS[lang]
    tr = (lambda t: i18n.translate(t)) if lang == "en" else (lambda t: t)
    lead = picked[0] if picked else None
    title = _first_sentence(tr(lead["text"])) if lead else w["title"]
    summary = w["first_summary"] if first else \
        w["summary"].format(n=len(changed), lead=(_first_sentence(tr(lead["text"])) if lead else "").lower())
    parts = [(w["first_intro"] if first else w["intro"]) + " " + w["three"]]
    if picked:
        dot = lambda t: t if t.endswith((".", "!", "?")) else t + "."
        parts.append(f":::box {w['short']}\n" + "\n".join(f"- {dot(_first_sentence(tr(p['text'])))}" for p in picked) + "\n:::")
    for p in picked:
        text = tr(p["text"])
        parts.append(f"## {_first_sentence(text)}")
        parts.append(f"**{w['see']}** {text}")
        if p.get("hypothesis"):
            parts.append(f"**{w['hypothesis']}** {tr(p['hypothesis'])}")
        if p.get("test"):
            parts.append(f"**{w['test']}** {tr(p['test'])}")
        status = tr(p["status"]) + (f", {w['both']}" if p.get("replicated") else "")
        parts.append(f"*{w['status']}: {status}.*")
    if shift:
        parts.append(f"## {w['map']}")
        label = tr(shift["label"])
        parts.append(w["shift"].format(label=label[:1].lower() + label[1:],
                                       early=_pct(shift["early"]), late=_pct(shift["late"]),
                                       n_early=shift["n_early"], n_late=shift["n_late"]))
    if picked:
        sure = []
        for p in picked:
            sig = (p.get("significance") or {}).get("label")
            sure.append(f"- **{_first_sentence(tr(p['text']))}** {tr(p['status']).capitalize()}"
                        + (f", {sig}" if sig else "") + (f", {w['both']}" if p.get("replicated") else "") + ".")
        parts.append(f":::box {w['sure']}\n{w['sure_note']}\n\n" + "\n".join(sure) + "\n:::")
    parts.append(w["outro"])
    return {"title": title, "summary": summary, "body": "\n\n".join(parts)}


def insert_picture(text: str, signum: str, block: str) -> str:
    """Bilden efter första stycket som nämner stenen (inte en bild eller en ruta), annars sist."""
    blocks = (text or "").split("\n\n")
    pat = re.compile(rf"(^|[^\w]){re.escape(signum)}(?!\w)")
    inside = False  # within a :::box or :::chart, which may hold blank lines
    for i, b in enumerate(blocks):
        opens = b.startswith(":::") and b.strip() != ":::"
        closes = b.rstrip().endswith("\n:::") or b.strip() == ":::"
        if not inside and not opens and not b.startswith("![") and pat.search(b):
            return "\n\n".join(blocks[:i + 1] + [block] + blocks[i + 1:])
        inside = (inside or opens) and not closes
    return "\n\n".join([b for b in blocks if b.strip()] + [block])


def with_pictures(draft: dict, images: list[dict], most: int = 2) -> dict:
    """Utkastet med foton av de första stenarna det nämner, på båda språken."""
    out = dict(draft)
    for img in images[:most]:
        out["body"] = insert_picture(out.get("body", ""), img["signum"], img["markdown"])
        if out.get("body_en"):
            out["body_en"] = insert_picture(out["body_en"], img["signum"], img["markdown_en"])
    return out


def build_draft(month: str, patterns: list[dict], before: dict[str, str], shift: dict | None) -> dict:
    """Ett utkast att skriva om, på svenska och engelska: rubrik, ingress, brödtext och underlag."""
    changed, picked = _pick(patterns, before)
    first = not before
    sv, en = (_write(lang, month, changed, picked, first, shift) for lang in ("sv", "en"))
    sources = [f"{p['topic']}: {p['status']}" + (" (nytt)" if _key(p) not in before else f" (tidigare {before[_key(p)]})")
               + f" – {_first_sentence(p['text'])}" for p in picked]
    if shift:
        sources.append(f"Mönsterkartan: {shift['label']} {_pct(shift['early'])} → {_pct(shift['late'])}")
    return {"draft": {"month": month, "slug": _slug(sv["title"])[:80].rstrip("-"), **sv,
                      "title_en": en["title"], "summary_en": en["summary"], "body_en": en["body"]},
            "sources": sources}


def _slug(s: str) -> str:
    import unicodedata
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:60]


def _res() -> dict:
    from api.routers import rstats
    from src import r_bridge
    return (r_bridge.JOB.result(rstats.fingerprint()) or {}) if rstats.corpus_ready() else {}


def _patterns_or_fail() -> list[dict]:
    try:
        patterns = _patterns()
    except Exception as e:  # noqa: BLE001
        raise server_error(e, "Mönstren kunde inte hämtas. Är korpusanalyserna i R beräknade?", status_code=503) from e
    if not patterns:
        raise HTTPException(status_code=409, detail="Korpusanalyserna i R är inte beräknade ännu (Statistik → Beräkna).")
    return patterns


@router.get("/admin/blog/topics")
def topics(_: dict = Depends(require_admin)):
    """Ämnen att välja bland: de utmärkande eller dolda mönster som R-analyserna har hittat och som håller."""
    from src import blog_topics
    patterns = _patterns_or_fail()
    try:
        used = {p.get("topic") for p in _all() if p.get("topic")}
    except HTTPException:
        used = set()
    return {"topics": blog_topics.candidates(patterns, _res(), used)}


def _example_and_mix(pattern: dict, res: dict, kind: str) -> tuple[dict | None, dict | None]:
    """A stone with the pattern and a free photo for the hook, and for a cluster the carvers behind its stones."""
    from api.rundata import store
    from api.routers.orthography import model
    from src import blog_examples, blog_topics, commons
    key = pattern.get("key") or ""
    feat, hs = blog_topics._feature(res, key), blog_topics._hotspot(res, key)
    s, names = store(), model().names
    try:
        if hs:
            cands = blog_examples.candidates(s.inscriptions, hs[0]["key"], None, names, signa=hs[1]["stones"])
        elif kind == "time" and feat:
            rows = [r for r in (feat.get("time") or {}).get("by_style") or [] if r.get("n", 0) >= 20]
            shape = (feat.get("time") or {}).get("shape")
            pick = (max(rows, key=lambda r: r["share"]) if shape == "peak" else rows[-1] if shape == "rises" else rows[0]) if rows else None
            cands = blog_examples.candidates(s.inscriptions, key, feat, names, styles={pick["style"]} if pick else None)
        elif kind == "regional" and feat:
            rows = [r for r in (feat.get("provinces") or {}).get("rows") or [] if (r.get("n_mid") or 0) >= 10]
            top = max(rows, key=lambda r: r.get("share1050") or 0)["province"] if rows else None
            cands = blog_examples.candidates(s.inscriptions, key, feat, names, prov=top)
        else:
            return None, None
        images = commons.stone_images([r["signum"] for r in cands[:20]]) if cands else []
        example = blog_examples.example(cands[:20], images)
    except Exception:  # noqa: BLE001 - the draft works without a photo
        example = None
    mix = blog_examples.carver_mix(s.inscriptions, hs[1]["stones"], hs[0]["key"], None, names) if hs else None
    return example, mix


def _frozen_figure(name: str, labels: dict) -> tuple[str, str] | None:
    """An R figure copied to the blog's own store (src/blog_figures.py), as markdown in Swedish and English."""
    from api.routers import rstats
    from src import blog_figures, i18n
    from src import r_bridge as rb
    data = rb.figure(rb.JOB.directory(rstats.fingerprint()), name)
    d = blog_figures.describe(name, labels, i18n.translate)
    if not data or not d:
        return None
    url = blog_figures.freeze(data)
    return blog_figures.markdown(url, d, "sv"), blog_figures.markdown(url, d, "en")


def _see_figures(pattern: dict, res: dict, keys: frozenset, labels: dict, feat: dict | None) -> list[dict]:
    """Bilderna i "Se själv" i stället för länkar in i appen (den publika webbplatsen har bara artiklarna): kartverktygets
    tidsvy av mönstret och förändringsmodellens kurva (src/blog_maps.py). Tomt om R inte är installerat."""
    import os
    from api.routers import rstats
    from src import blog_maps, blog_topics, i18n, r_bridge
    if not rstats.corpus_ready():
        return []
    d = r_bridge.JOB.directory(rstats.fingerprint())
    out = []
    pm, mode = blog_topics.see_maps(pattern, res, keys)
    if pm and mode == "tid":
        m = blog_maps.time_map(os.path.join(d, "corpus.csv"), pm, labels[pm], i18n.translate(labels[pm]))
        if m:
            out.append(m)
    if feat and (feat.get("time") or {}).get("curve") and os.path.exists(os.path.join(d, "change.json")):
        c = blog_maps.curves(os.path.join(d, "change.json"), [feat["key"]], [feat["label"]], [i18n.translate(feat["label"])])
        if c:
            out.append(c)
    return out


def topic_draft(month: str, pattern: dict, res: dict) -> dict:
    """Ett utkast kring ett mönster, på svenska och engelska, i formen från det publicerade inlägget (src/blog_topics.py):
    krok med en sten och dess foto, diagram, kartbild ur R, en första prövning och källor."""
    from src import blog_maps, blog_topics, i18n, pattern_map
    from src.research_gaps import PROVINCE_NAMES
    key = pattern.get("key") or ""
    feat, hs = blog_topics._feature(res, key), blog_topics._hotspot(res, key)
    kind = blog_topics.kind(pattern, res)
    labels = {k: l for k, l, *_ in pattern_map.PATTERNS}
    label = labels.get(hs[0]["key"]) if hs else (feat or {}).get("label")
    keys = frozenset(labels)
    example, mix = _example_and_mix(pattern, res, kind)
    fig_name = blog_topics.figure_for(pattern, res)
    fig = _frozen_figure(fig_name, labels) if fig_name else None
    see = _see_figures(pattern, res, keys, labels, feat)
    common = dict(provinces=PROVINCE_NAMES, map_keys=keys, example=example, mix=mix)
    sv = blog_topics.draft(pattern, res, "sv", label=label, figure=fig[0] if fig else None,
                           see=[blog_maps.markdown(f, "sv") for f in see], **common)
    en = blog_topics.draft(pattern, res, "en", tr=i18n.translate, label=i18n.translate(label) if label else None,
                           figure=fig[1] if fig else None, see=[blog_maps.markdown(f, "en") for f in see], **common)
    sources = [f"{pattern.get('topic')}: {pattern.get('status')} – {blog_topics.first_sentence(pattern['text'])}"]
    if example:
        sources.append(f"Krok och foto: {example['signum']} ({example['place']})")
    if fig_name:
        sources.append(f"Figur ur R: {fig_name}")
    return {"draft": {"month": month, "slug": _slug(sv["title"])[:80].rstrip("-"), **sv,
                      "title_en": en["title"], "summary_en": en["summary"], "body_en": en["body"],
                      "topic": blog_topics.topic_key(pattern)},
            "sources": sources}


@router.get("/admin/blog/figures")
def figures(_: dict = Depends(require_admin)):
    """Korpusanalysens figurer att använda i ett inlägg, kartverktygets kartbilder först (src/blog_figures.py)."""
    from api.routers import rstats
    from src import blog_figures, i18n, pattern_map
    res = _res()
    if not res:
        raise HTTPException(status_code=409, detail="Korpusanalyserna i R är inte beräknade ännu (Statistik → Beräkna).")
    labels = {k: l for k, l, *_ in pattern_map.PATTERNS}
    fp = rstats.fingerprint()
    return {"figures": [{**d, "url": f"/api/r/figure/{fp}/{d['name']}", "group_label": blog_figures.GROUPS[d["group"]]}
                        for d in blog_figures.available(res, labels, i18n.translate)]}


class FigureRequest(BaseModel):
    name: str = Field(..., min_length=5, max_length=120, pattern=r"^[A-Za-z0-9_]+\.png$")


@router.post("/admin/blog/figures")
def freeze_figure(req: FigureRequest, _: dict = Depends(require_admin)):
    """Kopierar en figur till bloggens egna figurer, så att inlägget behåller den när analysen räknas om."""
    from src import pattern_map
    out = _frozen_figure(req.name, {k: l for k, l, *_ in pattern_map.PATTERNS})
    if not out:
        raise HTTPException(status_code=404, detail="Figuren finns inte i den senaste korpusanalysen.")
    return {"markdown": out[0], "markdown_en": out[1]}


@router.get("/blog/figures/{name}")
def blog_figure(name: str):
    """En figur i ett inlägg; den ändras aldrig och kan sparas länge av webbläsare och sökmotorer."""
    from fastapi.responses import FileResponse
    from src import blog_figures
    path = blog_figures.path_of(name)
    if not path:
        raise HTTPException(status_code=404, detail="Figuren finns inte.")
    return FileResponse(path, media_type="image/png", headers={"Cache-Control": "public, max-age=31536000, immutable"})


@router.get("/admin/blog/draft")
def draft(month: str | None = None, topic: str | None = None, _: dict = Depends(require_admin)):
    """Utkast från månadens fynd: kring ett valt ämne (topic, från /admin/blog/topics), eller de mönster som är nya
    eller har ändrat status sedan förra publicerade inlägget."""
    month = month or dt.date.today().strftime("%Y-%m")
    if not MONTH.match(month):
        raise HTTPException(status_code=422, detail="Månaden ska anges som ÅÅÅÅ-MM.")
    patterns = _patterns_or_fail()
    if topic:
        from src import blog_topics
        pattern = next((p for p in patterns if blog_topics.topic_key(p) == topic), None)
        if not pattern:
            raise HTTPException(status_code=404, detail="Ämnet finns inte bland mönstren längre; hämta ämnena igen.")
        out = topic_draft(month, pattern, _res())
        out["note"] = ("Utkastet följer bloggens mall med appens siffror. Skriv om det med egna ord: en krok, vad som är "
                       "nytt för forskningen och en skarp hypotes.")
    else:
        out = build_draft(month, patterns, _last_snapshot(), _map_shift())
        out["note"] = "Utkastet är en sammanställning av appens texter. Skriv om det med egna ord innan du publicerar."
    # Photos of the stones the draft names, from Wikimedia Commons; the draft is useful also without them
    try:
        from src import commons
        signa = commons.signa_in(out["draft"]["body"])[:6]
        images = commons.stone_images(signa) if signa else []
        if images:
            out["draft"] = with_pictures(out["draft"], images)
            out["sources"].append("Foton: " + ", ".join(f"{i['signum']} ({i['author']}, {i['licence']})" for i in images[:2]))
    except Exception:  # noqa: BLE001
        out["note"] += " Fotona kunde inte hämtas."
    return out


class ImagesRequest(BaseModel):
    text: str = Field("", max_length=90000)


@router.post("/admin/blog/images")
def images(req: ImagesRequest, _: dict = Depends(require_admin)):
    """Bilder att välja mellan för de stenar en text nämner: upp till sex fritt licensierade per sten ur Wikidata och
    stenens kategori på Wikimedia Commons, foton före äldre teckningar, med fotograf och licens (src/commons.py).
    Stenar utan någon sådan bild står under missing."""
    from src import commons
    signa = commons.signa_in(req.text)[:30]
    if not signa:
        return {"stones": [], "missing": []}
    try:
        stones = commons.stone_photos(signa)
    except Exception as e:  # noqa: BLE001
        raise server_error(e, "Bilderna kunde inte hämtas från Wikimedia Commons.", status_code=503) from e
    have = {st["signum"] for st in stones}
    return {"stones": stones, "missing": [s for s in signa if s not in have]}


@router.get("/admin/site/publish")
def site_status(_: dict = Depends(require_admin)):
    """Hur det senaste försöket att publicera webbplatsen gick, och om något väntar på att pushas."""
    from src import site_export
    return site_export.status()


@router.post("/admin/site/publish")
def publish_site(force: bool = False, _: dict = Depends(require_admin)):
    """Publicerar webbplatsen vitkirunor.se: exporterar de publicerade artiklarna (också schemalagda) och deras figurer
    och pushar dem till GitHub, som bygger om webbplatsen på några minuter (src/site_export.py). Ser exporten fel ut
    (inga artiklar, flera som försvinner, saknade figurer) publiceras inget och skälet står i note; ?force=true
    publicerar ändå, för en avsiktlig borttagning."""
    from src import site_export
    try:
        out = site_export.publish_now(force=force)
    except Exception as e:  # noqa: BLE001 - git or the disk
        raise server_error(e, "Webbplatsen kunde inte publiceras.", status_code=503) from e
    return out
