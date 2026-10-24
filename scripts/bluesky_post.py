"""Inlägg på Bluesky (@vitkirunor.bsky.social) om en publicerad artikel: egen text, länkkort med artikelns titel,
sammanfattning och bild, och språkmärkning. Utan --posta visas bara inlägget; ingenting skickas.

Kontot nås med ett applösenord (Bluesky: Inställningar → Integritet och säkerhet → Applösenord), aldrig med det
vanliga lösenordet. Det ligger i .env som BLUESKY_HANDLE och BLUESKY_APP_PASSWORD och skrivs aldrig ut.
    .venv/bin/python -m scripts.bluesky_post SLUG --text "…" [--en] [--tagg runor --tagg vikingatid]
    .venv/bin/python -m scripts.bluesky_post SLUG --text "…" --posta     # skickar inlägget
    .venv/bin/python -m scripts.bluesky_post --ko [--posta]             # kön: godkända inlägg med datum, ett per körning
Kön körs dagligen av launchd (scripts/se.vitkirunor.bluesky.plist).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys

import requests

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
from dotenv import dotenv_values  # noqa: E402

for f in (".env", "api/.env"):
    p = os.path.join(ROOT, f)
    if os.path.exists(p):
        for k, v in dotenv_values(p).items():
            os.environ.setdefault(k, v or "")

PDS = "https://bsky.social/xrpc"
SITE = "https://vitkirunor.se"
LIMIT = 300  # Bluesky's limit in graphemes; a Swedish text without emoji counts as characters
MAX_THUMB = 1_000_000  # Bluesky's limit for the link card's picture


def thumbnail(url: str) -> tuple[bytes, str] | None:
    """The article page's own share picture (og:image) from the live site, else the site's share picture."""
    try:
        html = requests.get(url, timeout=30).text
        m = re.search(r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"', html)
        for src in ([m.group(1)] if m else []) + [f"{SITE}/delningsbild.png"]:
            r = requests.get(src if src.startswith("http") else SITE + src, timeout=60)
            if r.ok and len(r.content) <= MAX_THUMB and r.headers.get("content-type", "").startswith("image/"):
                return r.content, r.headers["content-type"].split(";")[0]
    except requests.RequestException:
        pass
    return None


def article(slug: str) -> dict:
    from api.routers import blog
    hits = [p for p in blog._all() if p.get("slug") == slug]
    if not hits:
        sys.exit(f"Ingen artikel med adressen {slug}")
    if not hits[0].get("published"):
        sys.exit("Artikeln är inte publicerad; inlägg görs bara om publicerade artiklar.")
    return hits[0]


def facets(text: str) -> list[dict]:
    """Links and #tags in the text, with UTF-8 byte offsets as Bluesky wants them."""
    out = []
    for m in re.finditer(r"https?://\S+|#[\wåäöÅÄÖ]+", text):
        start, end = len(text[:m.start()].encode()), len(text[:m.end()].encode())
        tok = m.group(0)
        feature = ({"$type": "app.bsky.richtext.facet#link", "uri": tok} if tok.startswith("http")
                   else {"$type": "app.bsky.richtext.facet#tag", "tag": tok[1:]})
        out.append({"index": {"byteStart": start, "byteEnd": end}, "features": [feature]})
    return out


KO = os.path.join(ROOT, "data", "bluesky", "ko.json")


def card(slug: str, en: bool) -> tuple[str, str, str]:
    """The link card: the start page ("/") or a published article, in Swedish or English."""
    if slug == "/":
        if en:
            return (f"{SITE}/?via=bluesky", "Vitki – runestones and runic inscriptions",
                    "An open research platform for Sweden's runic inscriptions: statistics on every runestone, 3D "
                    "analysis of carved grooves and a model for lost runes. Open data and open code.")
        return (f"{SITE}/?via=bluesky", "Vitki – runstenar och runinskrifter",
                "En öppen forskningsplattform för Sveriges runinskrifter: statistik över alla runstenar, 3D-analys av "
                "huggspår och en modell för förlorade runor. Öppna data och öppen kod.")
    post = article(slug)
    if en and not post.get("body_en"):
        sys.exit("Artikeln har ingen engelsk utgåva.")
    url = f"{SITE}{'/en' if en else ''}/artiklar/{slug}/?via=bluesky"
    return url, (post["title_en"] if en else post["title"]), (post.get("summary_en") if en else post.get("summary")) or ""


def compose(text: str, tags: list[str]) -> str:
    out = text.strip() + ("\n\n" + " ".join(f"#{t}" for t in tags) if tags else "")
    if len(out) > LIMIT:
        sys.exit(f"Texten har {len(out)} tecken; Bluesky tillåter {LIMIT}.")
    return out


def send(text: str, url: str, title: str, desc: str, en: bool) -> str:
    """Posts and returns the post's address on bsky.app."""
    handle, pw = os.environ.get("BLUESKY_HANDLE"), os.environ.get("BLUESKY_APP_PASSWORD")
    if not handle or not pw:
        sys.exit("BLUESKY_HANDLE och BLUESKY_APP_PASSWORD saknas i .env")
    s = requests.post(f"{PDS}/com.atproto.server.createSession", json={"identifier": handle, "password": pw}, timeout=30)
    s.raise_for_status()
    sess = s.json()
    auth = {"Authorization": f"Bearer {sess['accessJwt']}"}
    external = {"uri": url, "title": title, "description": desc}
    if (pic := thumbnail(url)):
        blob = requests.post(f"{PDS}/com.atproto.repo.uploadBlob", data=pic[0],
                             headers={**auth, "Content-Type": pic[1]}, timeout=60)
        blob.raise_for_status()
        external["thumb"] = blob.json()["blob"]
    record = {"$type": "app.bsky.feed.post", "text": text, "langs": ["en" if en else "sv"],
              "createdAt": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
              "embed": {"$type": "app.bsky.embed.external", "external": external}}
    if (f := facets(text)):
        record["facets"] = f
    r = requests.post(f"{PDS}/com.atproto.repo.createRecord", headers=auth, timeout=30,
                      json={"repo": sess["did"], "collection": "app.bsky.feed.post", "record": record})
    r.raise_for_status()
    return f"https://bsky.app/profile/{handle}/post/{r.json()['uri'].rsplit('/', 1)[-1]}"


def queue(post_due: bool):
    """data/bluesky/ko.json: posts the founder has approved, each with a planned date. At most ONE due post is sent per
    run (the earliest), so that a missed day does not send several at once; the post's address is written back."""
    q = json.load(open(KO, encoding="utf-8"))
    today = dt.date.today().isoformat()
    for item in q["items"]:
        text = compose(item["text"], item.get("tags", []))
        url, title, _ = card(item["slug"], item.get("en", False))
        state = item.get("posted") or ("väntar" if item["date"] > today else "ska ut")
        print(f"{item['date']} {item['slug'][:40]:40} {len(text):3}/{LIMIT}  {state}")
    due = [i for i in q["items"] if not i.get("posted") and i["date"] <= today]
    if not post_due or not due:
        return
    item = due[0]
    url, title, desc = card(item["slug"], item.get("en", False))
    item["posted"] = send(compose(item["text"], item.get("tags", [])), url, title, desc, item.get("en", False))
    item["posted_at"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    json.dump(q, open(KO, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("Postat:", item["posted"])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("slug", nargs="?", help="artikelns adress, eller / för startsidan")
    ap.add_argument("--text", help="inläggets text (länken läggs i länkkortet)")
    ap.add_argument("--en", action="store_true", help="den engelska utgåvan")
    ap.add_argument("--tagg", action="append", default=[], help="hashtagg utan #, kan upprepas")
    ap.add_argument("--posta", action="store_true", help="skicka inlägget (annars visas det bara)")
    ap.add_argument("--ko", action="store_true", help="visa kön i data/bluesky/ko.json; med --posta skickas nästa inlägg som är dags")
    a = ap.parse_args(argv)
    if a.ko:
        return queue(a.posta)
    if not a.slug or not a.text:
        ap.error("ange artikelns adress och --text (eller --ko)")
    text = compose(a.text, a.tagg)
    url, title, desc = card(a.slug, a.en)
    print(f"--- inlägg ({len(text)}/{LIMIT} tecken, {'engelska' if a.en else 'svenska'}) ---\n{text}\n"
          f"--- länkkort ---\n{title}\n{desc}\n{url}")
    if not a.posta:
        print("\n(visas bara; lägg till --posta för att skicka)")
        return
    print("\nPostat:", send(text, url, title, desc, a.en))


if __name__ == "__main__":
    main()
