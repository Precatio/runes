"""Veckans publiceringar: Viktor godkänner och schemalägger veckans planerade artiklar med ett klick varje måndag.

Planen står i data/publiceringsschema.json (formatet i filens _om): datum och tid i svensk tid, artikelns Firestore-id,
spår och ett engelskt Bluesky-inlägg. Godkännandet går samma väg som Schemalägg i Admin (blog.store_post: kontroller,
säkerhetskopia, publiceringstiden som datum), lägger Bluesky-inlägget i kön (data/bluesky/ko.json) med
publiceringsdagen som datum och skriver in godkand i planen. En artikel som redan är publicerad eller schemalagd, eller
vars tid har passerat, rörs aldrig.

Samma plan finns i Firestore (samlingen publiceringsschema, skickad med scripts/publiceringsschema_sync.py), så att
webbadmin /redaktion kan visa och godkänna veckan från mobilen. Där läggs Bluesky-inlägget i kön via en förfrågan som
GitHub Actions slår in (src/bluesky_queue.py, samma regel som här).
"""
from __future__ import annotations

import datetime as dt
import json
import os
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, ValidationError

from api.auth import require_admin
from api.routers import blog
from src.bluesky_queue import LIMIT, composed_length, queue_bluesky  # noqa: F401 - shared with scripts/ci_publicera.py
from src.bluesky_queue import POST_HOUR

router = APIRouter()
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCHEMA = os.path.join(ROOT, "data", "publiceringsschema.json")
KO = os.path.join(ROOT, "data", "bluesky", "ko.json")
TZ = ZoneInfo("Europe/Stockholm")
# The article's own fields that a scheduling writes back unchanged (blog.PostRequest)
FIELDS = ("slug", "title", "summary", "body", "title_en", "summary_en", "body_en", "month", "author", "topic", "featured",
          "labels")


def publish_time(datum: str, tid: str) -> dt.datetime:
    """The plan's date and time, read as Swedish time (summer or winter time by itself), as an aware UTC time."""
    local = dt.datetime.combine(dt.date.fromisoformat(datum), dt.time.fromisoformat(tid), tzinfo=TZ)
    return local.astimezone(dt.timezone.utc)


def week_of(start: dt.date | None, today: dt.date) -> tuple[dt.date, dt.date]:
    """Monday and Sunday of the week to show: the week of the given date, or by default the coming week (on a Monday,
    the week that starts today)."""
    monday = start - dt.timedelta(days=start.weekday()) if start else today + dt.timedelta(days=(7 - today.weekday()) % 7)
    return monday, monday + dt.timedelta(days=6)


def load_schema() -> dict:
    try:
        with open(SCHEMA, encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        return {"poster": []}


def _write(path: str, data: dict) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    os.replace(tmp, path)


def in_week(schema: dict, monday: dt.date, sunday: dt.date) -> list[dict]:
    rows = [p for p in schema.get("poster", []) if monday.isoformat() <= str(p.get("datum", "")) <= sunday.isoformat()]
    return sorted(rows, key=lambda p: (p["datum"], p.get("tid", "")))


def refusal(entry: dict, post: dict | None, now: dt.datetime) -> str | None:
    """Why an entry cannot be approved, or None. A published article (live or scheduled) is never touched."""
    if not post:
        return "Artikeln finns inte (fel id i publiceringsschemat?)."
    if post.get("published"):
        t = blog._ts(post.get("publishedAt"))
        return ("Redan schemalagd" if t and t > now else "Redan publicerad") + " – rörs inte."
    try:
        when = publish_time(entry["datum"], entry.get("tid") or "07:00")
    except (KeyError, ValueError):
        return "Datum eller tid i publiceringsschemat kan inte läsas (ÅÅÅÅ-MM-DD och TT:MM)."
    if when <= now:
        return "Publiceringstiden har passerat."
    from src import blog_labels
    if (bad := blog_labels.check(post.get("labels") or [])):
        return f"Etiketterna: {bad}"
    if (n := composed_length(entry.get("bluesky"))) and n > LIMIT:
        return f"Bluesky-texten har {n} tecken; högst {LIMIT}."
    return None


def status(entry: dict, post: dict | None, now: dt.datetime) -> dict:
    """What the week's card shows for one entry."""
    published = bool(post and post.get("published"))
    t = blog._ts(post.get("publishedAt")) if post else None
    state = "saknas" if not post else ("schemalagd" if t and t > now else "publicerad") if published else "utkast"
    try:
        when = publish_time(entry["datum"], entry.get("tid") or "07:00").isoformat()
    except (KeyError, ValueError):
        when = None
    from src import blog_labels
    reason = refusal(entry, post, now)
    return {**{k: entry.get(k) for k in ("datum", "tid", "id", "titel", "spar", "bluesky", "godkand")},
            "publish_at": when, "state": state, "exists": bool(post),
            "publishedAt": post.get("publishedAt") if post else None,
            "slug": (post or {}).get("slug"), "title": (post or {}).get("title"),
            "title_en": bool((post or {}).get("title_en")), "body_en": bool((post or {}).get("body_en")),
            "labels": (post or {}).get("labels") or [],
            "labels_problem": blog_labels.check((post or {}).get("labels") or []) if post else None,
            "bluesky_length": composed_length(entry.get("bluesky")), "bluesky_limit": LIMIT,
            "can_approve": reason is None, "reason": reason}


def _parse_from(value: str | None) -> dt.date | None:
    if not value:
        return None
    try:
        return dt.date.fromisoformat(value)
    except ValueError as e:
        raise HTTPException(status_code=422, detail="from ska anges som ÅÅÅÅ-MM-DD.") from e


def _today() -> dt.date:
    return dt.datetime.now(TZ).date()


@router.get("/admin/blog/week")
def week(start: str | None = Query(None, alias="from"), _: dict = Depends(require_admin)):
    """Veckans planerade publiceringar (måndag–söndag; utan from den kommande veckan) med läget för var och en:
    finns utkastet, är det redan publicerat eller schemalagt, adress, engelsk rubrik, etiketter och Bluesky-textens
    längd."""
    monday, sunday = week_of(_parse_from(start), _today())
    rows = in_week(load_schema(), monday, sunday)
    posts = {p["id"]: p for p in blog._all()} if rows else {}
    now = dt.datetime.now(dt.timezone.utc)
    return {"from": monday.isoformat(), "to": sunday.isoformat(), "week": monday.isocalendar().week,
            "entries": [status(e, posts.get(e.get("id")), now) for e in rows]}


class ApproveRequest(BaseModel):
    start: str = Field(..., alias="from", max_length=10)
    ids: list[str] = Field(default_factory=list, max_length=20)


def _fresh(post_id: str) -> dict | None:
    """The article as it is in Firestore right now (not the minute-old cache), so that no newer text is overwritten."""
    doc = blog.firestore().collection(blog.COLLECTION).document(post_id).get().to_dict()
    return {"id": post_id, **doc} if doc else None


@router.post("/admin/blog/week/approve")
def approve(req: ApproveRequest, admin: dict = Depends(require_admin)):
    """Godkänner veckans valda artiklar: var och en schemaläggs till sin tid i planen (samma väg som Schemalägg, med
    säkerhetskopia), Bluesky-inlägget läggs i kön med publiceringsdagen som datum (om adressen inte redan står där) och
    godkand skrivs i planen. Redan publicerade eller schemalagda artiklar och sådana vars tid har passerat avvisas."""
    monday, sunday = week_of(_parse_from(req.start), _today())
    schema = load_schema()
    rows = {e["id"]: e for e in in_week(schema, monday, sunday)}
    blog._forget()
    now = dt.datetime.now(dt.timezone.utc)
    results, ko, ko_changed, scheduled = [], None, False, 0
    for post_id in dict.fromkeys(req.ids):
        entry = rows.get(post_id)
        if not entry:
            results.append({"id": post_id, "ok": False, "reason": "Står inte i veckans publiceringsschema."})
            continue
        try:
            post = _fresh(post_id)
        except Exception as e:  # noqa: BLE001 - Firestore unreachable: this one fails, the others are tried
            results.append({"id": post_id, "ok": False, "reason": f"Artikeln kunde inte läsas: {e}"})
            continue
        if (why := refusal(entry, post, now)):
            results.append({"id": post_id, "ok": False, "reason": why, "titel": entry.get("titel")})
            continue
        when = publish_time(entry["datum"], entry.get("tid") or "07:00")
        try:
            pr = blog.PostRequest(id=post_id, published=True, publish_at=when.isoformat(),
                                  **{k: post[k] for k in FIELDS if post.get(k) is not None})
            _, data, _ = blog.store_post(pr, admin)
        except ValidationError as e:
            results.append({"id": post_id, "ok": False, "reason": f"Artikeln har ett fel: {e.errors()[0].get('msg')}"})
            continue
        except HTTPException as e:
            results.append({"id": post_id, "ok": False, "reason": str(e.detail)})
            continue
        scheduled += 1
        out = {"id": post_id, "ok": True, "titel": entry.get("titel"), "slug": data["slug"],
               "publishedAt": data["publishedAt"].isoformat(), "bluesky": None}
        if entry.get("bluesky"):
            if not post.get("body_en"):
                out["bluesky"] = "inget inlägg: artikeln har ingen engelsk utgåva"
            else:
                try:
                    if ko is None:
                        with open(KO, encoding="utf-8") as fh:
                            ko = json.load(fh)
                    added = queue_bluesky(ko, data["slug"], entry["datum"], entry["bluesky"])
                    ko_changed |= added
                    out["bluesky"] = f"i kön {entry['datum']} kl. {POST_HOUR}" if added else "stod redan i kön"
                except (OSError, ValueError, KeyError) as e:  # the article is scheduled; the post can be queued by hand
                    out["bluesky"] = f"kön kunde inte läsas ({e}); lägg inlägget i data/bluesky/ko.json för hand"
        entry["godkand"] = dt.datetime.now(TZ).isoformat(timespec="seconds")
        results.append(out)
    if ko_changed:
        _write(KO, ko)
    if scheduled:
        _write(SCHEMA, schema)
        # The public website, as after Schemalägg in Admin: the export now, and a publication when the time comes
        from src import site_export
        site_export.publish_soon()
        site_export.schedule(blog._all())
    return {"from": monday.isoformat(), "results": results}
