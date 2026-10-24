"""Inlägg på Bluesky (@vitkirunor.bsky.social) om en publicerad artikel: egen text, länkkort med artikelns titel,
sammanfattning och bild, och språkmärkning. Utan --posta visas bara inlägget; ingenting skickas.

Kontot nås med ett applösenord (Bluesky: Inställningar → Integritet och säkerhet → Applösenord), aldrig med det
vanliga lösenordet. Det ligger i .env som BLUESKY_HANDLE och BLUESKY_APP_PASSWORD och skrivs aldrig ut.
    .venv/bin/python -m scripts.bluesky_post SLUG --text "…" [--en] [--tagg runor --tagg vikingatid]
    .venv/bin/python -m scripts.bluesky_post SLUG --text "…" --posta     # skickar inlägget
"""
from __future__ import annotations

import argparse
import datetime as dt
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


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("slug")
    ap.add_argument("--text", required=True, help="inläggets text (länken läggs i länkkortet)")
    ap.add_argument("--en", action="store_true", help="den engelska utgåvan")
    ap.add_argument("--tagg", action="append", default=[], help="hashtagg utan #, kan upprepas")
    ap.add_argument("--posta", action="store_true", help="skicka inlägget (annars visas det bara)")
    a = ap.parse_args(argv)

    post = article(a.slug)
    en = a.en
    if en and not post.get("body_en"):
        sys.exit("Artikeln har ingen engelsk utgåva.")
    url = f"{SITE}{'/en' if en else ''}/artiklar/{a.slug}/?via=bluesky"
    text = a.text.strip() + ("\n\n" + " ".join(f"#{t}" for t in a.tagg) if a.tagg else "")
    if len(text) > LIMIT:
        sys.exit(f"Texten har {len(text)} tecken; Bluesky tillåter {LIMIT}.")
    title = post["title_en"] if en else post["title"]
    desc = (post.get("summary_en") if en else post.get("summary")) or ""
    print(f"--- inlägg ({len(text)}/{LIMIT} tecken, {'engelska' if en else 'svenska'}) ---\n{text}\n"
          f"--- länkkort ---\n{title}\n{desc}\n{url}")
    if not a.posta:
        print("\n(visas bara; lägg till --posta för att skicka)")
        return

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
    rkey = r.json()["uri"].rsplit("/", 1)[-1]
    print(f"\nPostat: https://bsky.app/profile/{handle}/post/{rkey}")


if __name__ == "__main__":
    main()
