"""Bluesky-kön (data/bluesky/ko.json) postad av GitHub Actions (.github/workflows/bluesky.yml) i stället för av
analysmotorn på Viktors dator: samma inlägg, på samma sätt (scripts/bluesky_post.py: länkkortet med den engelska
delningsbilden, svaret med "credit", posted/posted_at tillbaka i kön), ett inlägg tisdagar och fredagar från kl. 13
svensk tid (Viktor 2026-11-14).

Postar bara när allt detta gäller, annars en kort notis och slut (avslutas med 0):
* BLUESKY_HANDLE och BLUESKY_APP_PASSWORD finns (GitHub-hemligheterna);
* data/bluesky/postning.json säger "postar": "ci" (annars postar den lokala appen; bara en av dem får göra det);
* det är tisdag eller fredag och klockan är 13 eller senare i Stockholm (arbetsflödet körs både 11 och 12 UTC, för
  sommar- och vintertid, och en gång till på eftermiddagen om en körning uteblir);
* inget inlägg ur kön har gått ut i dag, och ett inlägg är dags: dagens (artikeln som publicerades i dag) före äldre.

Innan något postas jämförs med kontots egna inlägg de senaste två veckorna (Blueskys öppna API): finns inlägget redan
där med exakt samma text – postat men inte bokfört, t.ex. för att en push misslyckades – skrivs dess adress in i kön i
stället för att det postas igen.

    python scripts/ci_bluesky.py            # postar om det är dags
    python scripts/ci_bluesky.py --dry-run  # visar bara vad som skulle hända

Skriver changed=true|false till $GITHUB_OUTPUT. Artiklarna läses ur web/content/articles.json (BLUESKY_ARTICLES=site).
"""
from __future__ import annotations

import datetime as dt
import json
import os
import sys
import time
from zoneinfo import ZoneInfo

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

STOCKHOLM = ZoneInfo("Europe/Stockholm")
from src.bluesky_queue import POST_DAY_NAMES, POST_HOUR as HOUR, pick_due, post_day  # noqa: E402
PUBLIC_API = "https://public.api.bsky.app/xrpc"


def _output(**kw: str) -> None:
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a", encoding="utf-8") as fh:
            for k, v in kw.items():
                fh.write(f"{k}={v}\n")


def posted_today(items: list[dict], today: dt.date) -> bool:
    """Has a queue item gone out today (Swedish date)? As the local thread in api/main.py counts it."""
    for i in items:
        at = i.get("posted_at")
        if at:
            try:
                if dt.datetime.fromisoformat(at).astimezone(STOCKHOLM).date() == today:
                    return True
            except ValueError:
                continue
    return False


def due_item(items: list[dict], today: dt.date, limit: int) -> dict | None:
    """The item to send today: one dated today first, otherwise the earliest unposted one whose date has come and that
    fits (src/bluesky_queue.pick_due, as the local poster picks it)."""
    return pick_due(items, today.isoformat(), lambda i: len(composed(i)) <= limit)


def composed(item: dict) -> str:
    text = item["text"].strip()
    return text + ("\n\n" + " ".join(f"#{t}" for t in item["tags"]) if item.get("tags") else "")


def decide(now: dt.datetime, q: dict, place: str, have_secrets: bool, limit: int = 300) -> tuple[str, dict | None]:
    """What this run should do: ("post", item) or ("skip", None) with the reason first. Pure, for the tests."""
    if not have_secrets:
        return "Bluesky-postning i GitHub Actions är inte aktiverad: hemligheterna BLUESKY_HANDLE och " \
               "BLUESKY_APP_PASSWORD saknas (se ADMIN_PA_WEBBEN.md).", None
    if place != "ci":
        return "data/bluesky/postning.json säger att den lokala appen postar kön; GitHub Actions gör ingenting.", None
    local = now.astimezone(STOCKHOLM)
    if not post_day(local.date()):
        return f"Kön postas {POST_DAY_NAMES}; i dag är det inte dags.", None
    if local.hour < HOUR:
        return f"Klockan är {local:%H:%M} i Stockholm; kön postas från {HOUR}:00.", None
    items = q.get("items", [])
    if posted_today(items, local.date()):
        return "Dagens inlägg ur kön har redan gått ut.", None
    item = due_item(items, local.date(), limit)
    if not item:
        return "Inget inlägg i kön är dags i dag.", None
    return "post", item


RECENT_DAYS = 14


def already_on_bluesky(handle: str, text: str, today: dt.date) -> dict | None:
    """The account's own recent post (RECENT_DAYS) with exactly this text, if there is one: posted but not recorded."""
    import requests
    try:
        r = requests.get(f"{PUBLIC_API}/app.bsky.feed.getAuthorFeed",
                         params={"actor": handle, "limit": 50, "filter": "posts_no_replies"}, timeout=30)
        r.raise_for_status()
    except requests.RequestException as e:
        print(f"::warning::Kontots inlägg kunde inte läsas ({type(e).__name__}); postar utan den kontrollen.")
        return None
    for entry in r.json().get("feed", []):
        post = entry.get("post", {})
        rec = post.get("record", {})
        if entry.get("reason") or post.get("author", {}).get("handle") != handle:
            continue  # a repost by the account, or someone else's post
        try:
            created = dt.datetime.fromisoformat(rec.get("createdAt", "").replace("Z", "+00:00")).astimezone(STOCKHOLM)
        except ValueError:
            continue
        if (today - created.date()).days <= RECENT_DAYS and rec.get("text") == text:
            return {"uri": post.get("uri", ""), "createdAt": created}
    return None


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    dry = "--dry-run" in argv
    os.environ["TZ"] = "Europe/Stockholm"  # bluesky_post.queue compares dates with date.today()
    time.tzset()
    os.environ.setdefault("BLUESKY_ARTICLES", "site")
    from scripts import bluesky_post as bp
    handle, pw = os.environ.get("BLUESKY_HANDLE", ""), os.environ.get("BLUESKY_APP_PASSWORD", "")
    with open(bp.KO, encoding="utf-8") as fh:
        q = json.load(fh)
    now = dt.datetime.now(dt.timezone.utc)
    what, item = decide(now, q, bp.posting_place(), bool(handle and pw), bp.LIMIT)
    if what != "post":
        print(f"::notice::{what}")
        _output(changed="false")
        return 0
    today = now.astimezone(STOCKHOLM).date()
    text = composed(item)
    if (seen := already_on_bluesky(handle, text, today)):
        print(f"::warning::{item['slug']} finns redan på Bluesky; adressen skrivs in i kön i stället för ett nytt inlägg.")
        if not dry:
            item["posted"] = f"https://bsky.app/profile/{handle}/post/{seen['uri'].rsplit('/', 1)[-1]}"
            item["posted_at"] = seen["createdAt"].astimezone(dt.timezone.utc).isoformat(timespec="seconds")
            with open(bp.KO, "w", encoding="utf-8") as fh:
                json.dump(q, fh, ensure_ascii=False, indent=1)
        _output(changed="false" if dry else "true")
        return 0
    if dry:
        print(f"Skulle posta {item['slug']} ({len(text)}/{bp.LIMIT}):\n{text}")
        _output(changed="false")
        return 0
    bp.queue(True)
    _output(changed="true")
    return 0


if __name__ == "__main__":
    sys.exit(main())
