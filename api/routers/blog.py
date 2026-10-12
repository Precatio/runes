"""Månadens fynd: bloggen på /blogg, ett inlägg i månaden om de mest intressanta mönstren och fynden.

Inläggen ligger i Firestore-samlingen `posts` och skrivs och läses bara av servern (Firebase Admin SDK), så att
samlingen kan vara stängd för webbläsarna (firestore.rules). Grundaren skriver och publicerar i Admin; utkastet från
månadens fynd bygger på de mönster som är nya eller har ändrat status sedan förra publicerade inlägget, och på den
största förskjutningen i mönsterkartan. Inget publiceras automatiskt.
"""
from __future__ import annotations

import datetime as dt
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
PUBLIC = ("id", "slug", "title", "summary", "title_en", "summary_en", "month", "author", "publishedAt")


class PostRequest(BaseModel):
    id: str | None = Field(None, max_length=64)
    slug: str = Field(..., min_length=1, max_length=80)
    title: str = Field(..., min_length=1, max_length=160)
    summary: str = Field("", max_length=600)
    body: str = Field(..., min_length=1, max_length=40000)
    title_en: str = Field("", max_length=160)
    summary_en: str = Field("", max_length=600)
    body_en: str = Field("", max_length=40000)
    month: str = Field(..., min_length=7, max_length=7)
    author: str = Field("", max_length=120)
    published: bool = False


def _iso(d: dict) -> dict:
    return {k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in d.items()}


def _all() -> list[dict]:
    try:
        docs = firestore().collection(COLLECTION).stream()
        return [{"id": d.id, **_iso(d.to_dict())} for d in docs]
    except Exception as e:
        raise server_error(e, "Blogginläggen kunde inte hämtas.", status_code=503)


def _published() -> list[dict]:
    posts = [p for p in _all() if p.get("published")]
    return sorted(posts, key=lambda p: (p.get("month") or "", p.get("publishedAt") or ""), reverse=True)


@router.get("/blog/posts")
def list_posts():
    """De publicerade inläggen, nyaste först (utan brödtext)."""
    return {"posts": [{k: p.get(k) for k in PUBLIC} for p in _published()]}


@router.get("/blog/posts/{slug}")
def get_post(slug: str):
    for p in _published():
        if p.get("slug") == slug:
            return {"post": {k: v for k, v in p.items() if k not in ("by", "snapshot", "published")}}
    raise HTTPException(status_code=404, detail="Inlägget finns inte eller är inte publicerat.")


@router.get("/admin/blog/posts")
def admin_posts(_: dict = Depends(require_admin)):
    """Alla inlägg, också utkast, nyaste månaden först."""
    posts = sorted(_all(), key=lambda p: (p.get("month") or "", p.get("updatedAt") or ""), reverse=True)
    return {"posts": [{k: v for k, v in p.items() if k != "snapshot"} for p in posts]}


@router.post("/admin/blog/posts")
def save_post(req: PostRequest, admin: dict = Depends(require_admin)):
    """Sparar ett utkast eller publicerar. Vid första publiceringen sparas mönstrens läge, som nästa utkast jämförs med."""
    if not SLUG.match(req.slug):
        raise HTTPException(status_code=422, detail="Adressen får bara innehålla små bokstäver a–z, siffror och bindestreck.")
    if not MONTH.match(req.month):
        raise HTTPException(status_code=422, detail="Månaden ska anges som ÅÅÅÅ-MM.")
    others = [p for p in _all() if p["id"] != req.id]
    if any(p.get("slug") == req.slug for p in others):
        raise HTTPException(status_code=409, detail=f"Adressen /blogg/{req.slug} används redan av ett annat inlägg.")
    now = dt.datetime.now(dt.timezone.utc)
    data = {**req.model_dump(exclude={"id"}), "updatedAt": now, "by": admin["uid"]}
    try:
        col = firestore().collection(COLLECTION)
        ref = col.document(req.id) if req.id else col.document()
        old = ref.get().to_dict() if req.id else None
        if req.published and not (old or {}).get("publishedAt"):
            data["publishedAt"] = now
            data["snapshot"] = _snapshot()
        if not old:
            data["createdAt"] = now
        ref.set(data, merge=True)
    except HTTPException:
        raise
    except Exception as e:
        raise server_error(e, "Inlägget kunde inte sparas.", status_code=503)
    return {"post": {"id": ref.id, **_iso({k: v for k, v in data.items() if k != "snapshot"})}}


@router.delete("/admin/blog/posts/{post_id}")
def delete_post(post_id: str, _: dict = Depends(require_admin)):
    try:
        firestore().collection(COLLECTION).document(post_id).delete()
    except Exception as e:
        raise server_error(e, "Inlägget kunde inte tas bort.", status_code=503)
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
        "shift": "Den största förskjutningen i [mönsterkartan]({href}) gäller {label}: {early} av stenarna före omkring "
                 "1050 ({n_early} stenar) och {late} efter ({n_late} stenar), bland stenar med säker stilgrupp.",
        "outro": "Alla siffror kommer från Vitkis analyser och kan granskas i appen under [Forskningsluckor](/luckor) och "
                 "[Statistik](/statistik); metoderna beskrivs i METHODS.md.",
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
        "shift": "The largest shift in the [pattern map]({href}) concerns {label}: {early} of the stones before about "
                 "1050 ({n_early} stones) and {late} after ({n_late} stones), among stones with a certain style group.",
        "outro": "All numbers come from Vitki's analyses and can be checked in the app under [Research gaps](/luckor) "
                 "and [Statistics](/statistik); the methods are described in METHODS.md.",
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
        parts.append(w["shift"].format(href=f"/karta?pattern={shift['key']}&split=1", label=label[:1].lower() + label[1:],
                                       early=_pct(shift["early"]), late=_pct(shift["late"]),
                                       n_early=shift["n_early"], n_late=shift["n_late"]))
    parts.append(w["outro"])
    return {"title": title, "summary": summary, "body": "\n\n".join(parts)}


def build_draft(month: str, patterns: list[dict], before: dict[str, str], shift: dict | None) -> dict:
    """Ett utkast att skriva om, på svenska och engelska: rubrik, ingress, brödtext och underlag."""
    changed, picked = _pick(patterns, before)
    first = not before
    sv, en = (_write(lang, month, changed, picked, first, shift) for lang in ("sv", "en"))
    sources = [f"{p['topic']}: {p['status']}" + (" (nytt)" if _key(p) not in before else f" (tidigare {before[_key(p)]})")
               + f" – {_first_sentence(p['text'])}" for p in picked]
    if shift:
        sources.append(f"Mönsterkartan: {shift['label']} {_pct(shift['early'])} → {_pct(shift['late'])}")
    return {"draft": {"month": month, "slug": f"{month}-{_slug(sv['title'])}"[:80].rstrip("-"), **sv,
                      "title_en": en["title"], "summary_en": en["summary"], "body_en": en["body"]},
            "sources": sources}


def _slug(s: str) -> str:
    import unicodedata
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:60]


@router.get("/admin/blog/draft")
def draft(month: str | None = None, _: dict = Depends(require_admin)):
    """Utkast från månadens fynd: mönstren som är nya eller har ändrat status sedan förra publicerade inlägget."""
    month = month or dt.date.today().strftime("%Y-%m")
    if not MONTH.match(month):
        raise HTTPException(status_code=422, detail="Månaden ska anges som ÅÅÅÅ-MM.")
    try:
        patterns = _patterns()
    except Exception as e:  # noqa: BLE001
        raise server_error(e, "Mönstren kunde inte hämtas. Är korpusanalyserna i R beräknade?", status_code=503)
    if not patterns:
        raise HTTPException(status_code=409, detail="Korpusanalyserna i R är inte beräknade ännu (Statistik → Beräkna).")
    out = build_draft(month, patterns, _last_snapshot(), _map_shift())
    out["note"] = "Utkastet är en sammanställning av appens texter. Skriv om det med egna ord innan du publicerar."
    return out
