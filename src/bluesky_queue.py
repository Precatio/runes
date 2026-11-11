"""Bluesky-kön (data/bluesky/ko.json): hur ett godkänt inlägg läggs in, och hur förfrågningarna från webbadmin slås in.

Samma regel gäller för båda vägarna till kön:
* Veckans publiceringar i den lokala appen (api/routers/blog_week.py) lägger in inlägget direkt när Viktor godkänner.
* /redaktion på webben kan inte skriva i repot. Sidan skapar i stället en förfrågan i Firestore-samlingen
  bluesky_forfragningar (en per adress, web/firestore.rules), och exporten i GitHub Actions (scripts/ci_publicera.py)
  slår in den här med merge_requests.

En förfrågan hanteras en gång. Utfallet skrivs i data/bluesky/webbforfragningar.json, eftersom förfrågan ligger kvar i
Firestore (CI-kontot får bara läsa). Därför kommer ett inlägg som Viktor sedan stryker ur kön inte tillbaka.
"""
from __future__ import annotations

import re

LIMIT = 300  # Bluesky's limit, as in scripts/bluesky_post.py
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def composed_length(b: dict | None) -> int | None:
    """The Bluesky post's length with its tags, counted as scripts/bluesky_post.compose counts it."""
    if not b:
        return None
    tags = b.get("tags") or []
    return len((b.get("text") or "").strip() + ("\n\n" + " ".join(f"#{t}" for t in tags) if tags else ""))


def queue_bluesky(ko: dict, slug: str, datum: str, b: dict) -> bool:
    """Puts the post in the Bluesky queue with the publication day as its date, unless the slug is already there (posted
    or waiting; a removed row does not count). It goes before the waiting posts of the same or a later date, since the
    queue sends one post a day in list order: so it goes out at 18:00 on the publication day and the rest of the queue
    moves on a day. Returns whether it was added."""
    items = ko.setdefault("items", [])
    if any(i.get("slug") == slug and not i.get("removed") for i in items):
        return False
    item = {"date": datum, "slug": slug, "en": True, "text": b["text"].strip(), "tags": list(b.get("tags") or [])}
    at = next((n for n, i in enumerate(items)
               if not i.get("posted") and not i.get("removed") and str(i.get("date", "")) >= datum), len(items))
    items.insert(at, item)
    return True


def request_problem(r: dict) -> str | None:
    """Why a request from /redaktion cannot go into the queue as it is (the rules check the same, more loosely)."""
    if not isinstance(r.get("datum"), str) or not DATE.match(r["datum"]):
        return "datum kan inte läsas"
    if not isinstance(r.get("text"), str) or not r["text"].strip():
        return "texten saknas"
    tags = r.get("tags") or []
    if not isinstance(tags, list) or not all(isinstance(t, str) and t for t in tags):
        return "taggarna kan inte läsas"
    if (n := composed_length(r)) and n > LIMIT:
        return f"texten har {n} tecken; högst {LIMIT}"
    return None


def merge_requests(ko: dict, requests: list[dict], posts: list[dict], handled: dict, now: str) -> list[str]:
    """Slår in förfrågningarna från /redaktion i kön (ko ändras på plats) och noterar utfallet i handled
    ({adress: {"at": tid, "utfall": text}}). Returnerar en rad per förfrågan som hanterades nu.

    En förfrågan som redan står i handled hoppas över. En vars artikel inte är publicerad eller schemalagd (förfrågan
    hann före schemaläggningen, eller artikeln avpublicerades) väntar till nästa körning. Allt annat hanteras en gång:
    det läggs i kön med samma regel som i den lokala appen, eller noteras med skälet."""
    by_slug = {p.get("slug"): p for p in posts if p.get("slug")}
    lines = []
    for r in sorted(requests, key=lambda r: (str(r.get("datum", "")), str(r.get("slug", "")))):
        slug = r.get("slug")
        if not isinstance(slug, str) or not slug or slug in handled:
            continue
        post = by_slug.get(slug)
        if not post or not post.get("published"):
            continue
        if (why := request_problem(r)):
            outcome = f"inte i kön: {why}"
        elif not post.get("body_en"):
            outcome = "inte i kön: artikeln har ingen engelsk utgåva"
        elif queue_bluesky(ko, slug, r["datum"], {"text": r["text"], "tags": r.get("tags") or []}):
            outcome = f"i kön {r['datum']} kl. 18"
        else:
            outcome = "stod redan i kön"
        handled[slug] = {"at": now, "utfall": outcome}
        lines.append(f"{slug}: {outcome}")
    return lines
