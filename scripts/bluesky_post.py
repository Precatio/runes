"""Inlägg på Bluesky (@vitkirunor.bsky.social) om en publicerad artikel: egen text, länkkort med artikelns titel,
sammanfattning och bild, och språkmärkning. Utan --posta visas bara inlägget; ingenting skickas.

Kontot nås med ett applösenord (Bluesky: Inställningar → Integritet och säkerhet → Applösenord), aldrig med det
vanliga lösenordet. Det ligger i .env som BLUESKY_HANDLE och BLUESKY_APP_PASSWORD och skrivs aldrig ut.
    .venv/bin/python -m scripts.bluesky_post SLUG --text "…" [--en] [--tagg runor --tagg vikingatid]
    .venv/bin/python -m scripts.bluesky_post SLUG --text "…" --posta     # skickar inlägget
    .venv/bin/python -m scripts.bluesky_post --ko [--posta]             # kön: godkända inlägg med datum, ett per körning
    .venv/bin/python -m scripts.bluesky_post --nu SLUG [--posta]        # ett visst inlägg ur kön nu, före sitt datum
Ett inlägg i kön kan ha "credit": en text som postas som svar direkt under inlägget (t.ex. de öppna skanningarnas
skannare, institution, projekt, licens och DOI); svarets adress skrivs i "credit_reply".
Kön körs dagligen kl. 18 – antingen av analysmotorn (api/main.py, tråden bluesky; BLUESKY_AUTOPOST=0 eller
BLUESKY_LOCAL=0 stänger av) eller av GitHub Actions (.github/workflows/bluesky.yml, scripts/ci_bluesky.py). Vilken av
dem som postar står i data/bluesky/postning.json ("postar": "lokal" eller "ci"; posting_place()), så att inget inlägg
går ut två gånger. BLUESKY_ARTICLES=site läser artiklarna ur webbplatsens export (web/content/articles.json) i stället
för ur Firestore – så gör GitHub Actions, som inte behöver någon databasbehörighet för att posta.
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


SITE_ARTICLES = os.path.join(ROOT, "web", "content", "articles.json")
SWITCH = os.path.join(ROOT, "data", "bluesky", "postning.json")


def posting_place() -> str:
    """Where the daily queue is posted from: "lokal" (the analysis engine's thread, the default – also when the switch
    file is missing or unreadable) or "ci" (GitHub Actions)."""
    try:
        with open(SWITCH, encoding="utf-8") as fh:
            return "ci" if json.load(fh).get("postar") == "ci" else "lokal"
    except (OSError, ValueError, AttributeError):
        return "lokal"


def local_posting() -> bool:
    """May the local app's thread post the queue? Not when the switch says GitHub Actions posts, nor with
    BLUESKY_LOCAL=0."""
    return posting_place() == "lokal" and os.environ.get("BLUESKY_LOCAL", "1") not in ("0", "false")


def article(slug: str) -> dict:
    if os.environ.get("BLUESKY_ARTICLES") == "site":
        # The website's export holds only articles that have gone live, which is what a post may link to
        with open(SITE_ARTICLES, encoding="utf-8") as fh:
            hits = [p for p in json.load(fh).get("posts", []) if p.get("slug") == slug]
        if not hits:
            sys.exit(f"Ingen publicerad artikel med adressen {slug} på webbplatsen")
        return {**hits[0], "published": True}
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
    for m in re.finditer(r"https?://\S+|vitkirunor\.se\S*|#[\wåäöÅÄÖ]+", text):
        start, end = len(text[:m.start()].encode()), len(text[:m.end()].encode())
        tok = m.group(0)
        if tok.startswith("vitkirunor.se"):
            tok = "https://" + tok
        feature = ({"$type": "app.bsky.richtext.facet#link", "uri": tok} if tok.startswith("http")
                   else {"$type": "app.bsky.richtext.facet#tag", "tag": tok[1:]})
        out.append({"index": {"byteStart": start, "byteEnd": end}, "features": [feature]})
    return out


KO = os.path.join(ROOT, "data", "bluesky", "ko.json")


MAX_IMAGE = 950_000  # under Bluesky's 1 MB per picture


def picture(path: str) -> tuple[bytes, int, int]:
    """A picture as JPEG under Bluesky's size limit, at most 2000 px on the long side; with its width and height."""
    from io import BytesIO
    from PIL import Image
    im = Image.open(os.path.join(ROOT, path)).convert("RGB")
    im.thumbnail((2000, 2000))
    for q in (90, 82, 74, 66, 58):
        out = BytesIO()
        im.save(out, format="JPEG", quality=q, optimize=True)
        if out.tell() <= MAX_IMAGE:
            return out.getvalue(), im.width, im.height
    sys.exit(f"{path} blir inte mindre än 1 MB")


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
    # a research report has its own section on the site (/forskningsrapporter), an article /artiklar
    section = "forskningsrapporter" if "Rapport" in (post.get("labels") or []) else "artiklar"
    url = f"{SITE}{'/en' if en else ''}/{section}/{slug}/?via=bluesky"
    return url, (post["title_en"] if en else post["title"]), (post.get("summary_en") if en else post.get("summary")) or ""


def compose(text: str, tags: list[str]) -> str:
    out = text.strip() + ("\n\n" + " ".join(f"#{t}" for t in tags) if tags else "")
    if len(out) > LIMIT:
        sys.exit(f"Texten har {len(out)} tecken; Bluesky tillåter {LIMIT}.")
    return out


def send(text: str, url: str, title: str, desc: str, en: bool, images: list[dict] | None = None,
         credit: str | None = None) -> tuple[str, str | None]:
    """Posts and returns the post's address on bsky.app, and the address of the reply with the credit (credit: e.g. the
    open scans' scanner, institution, project, licence and DOI) when there is one."""
    handle, pw = os.environ.get("BLUESKY_HANDLE"), os.environ.get("BLUESKY_APP_PASSWORD")
    if not handle or not pw:
        sys.exit("BLUESKY_HANDLE och BLUESKY_APP_PASSWORD saknas i .env")
    s = requests.post(f"{PDS}/com.atproto.server.createSession", json={"identifier": handle, "password": pw}, timeout=30)
    s.raise_for_status()
    sess = s.json()
    auth = {"Authorization": f"Bearer {sess['accessJwt']}"}
    if images:  # a picture post (up to four, each with its alt text); the link then goes in the text
        embed = {"$type": "app.bsky.embed.images", "images": []}
        for im in images[:4]:
            data, w, h = picture(im["path"])
            blob = requests.post(f"{PDS}/com.atproto.repo.uploadBlob", data=data,
                                 headers={**auth, "Content-Type": "image/jpeg"}, timeout=60)
            blob.raise_for_status()
            embed["images"].append({"image": blob.json()["blob"], "alt": im["alt"], "aspectRatio": {"width": w, "height": h}})
    else:
        external = {"uri": url, "title": title, "description": desc}
        if (pic := thumbnail(url)):
            blob = requests.post(f"{PDS}/com.atproto.repo.uploadBlob", data=pic[0],
                                 headers={**auth, "Content-Type": pic[1]}, timeout=60)
            blob.raise_for_status()
            external["thumb"] = blob.json()["blob"]
        embed = {"$type": "app.bsky.embed.external", "external": external}
    record = {"$type": "app.bsky.feed.post", "text": text, "langs": ["en" if en else "sv"],
              "createdAt": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"), "embed": embed}
    if (f := facets(text)):
        record["facets"] = f
    r = requests.post(f"{PDS}/com.atproto.repo.createRecord", headers=auth, timeout=30,
                      json={"repo": sess["did"], "collection": "app.bsky.feed.post", "record": record})
    r.raise_for_status()
    post = r.json()
    at = lambda uri: f"https://bsky.app/profile/{handle}/post/{uri.rsplit('/', 1)[-1]}"  # noqa: E731
    reply_at = None
    if credit:
        ref = {"uri": post["uri"], "cid": post["cid"]}
        rec = {"$type": "app.bsky.feed.post", "text": credit, "langs": ["en" if en else "sv"],
               "createdAt": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
               "reply": {"root": ref, "parent": ref}}
        if (f := facets(credit)):
            rec["facets"] = f
        c = requests.post(f"{PDS}/com.atproto.repo.createRecord", headers=auth, timeout=30,
                          json={"repo": sess["did"], "collection": "app.bsky.feed.post", "record": rec})
        c.raise_for_status()
        reply_at = at(c.json()["uri"])
    return at(post["uri"]), reply_at


def post_item(q: dict, item: dict) -> None:
    """Sends one queue item (with its credit reply, if any) and writes the addresses back to the queue file."""
    url, title, desc = card(item["slug"], item.get("en", False))
    item["posted"], reply_at = send(compose(item["text"], item.get("tags", [])), url, title, desc, item.get("en", False),
                                    item.get("images"), item.get("credit"))
    if reply_at:
        item["credit_reply"] = reply_at
    item["posted_at"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    json.dump(q, open(KO, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("Postat:", item["posted"], *([reply_at] if reply_at else []))


def now(slug: str, post: bool) -> None:
    """A given queued post now, before its date (the founder's call); the daily queue then skips it."""
    q = json.load(open(KO, encoding="utf-8"))
    hits = [i for i in q["items"] if i["slug"] == slug and not i.get("posted")]
    if not hits:
        sys.exit(f"Inget opostat inlägg i kön med adressen {slug}")
    item = hits[0]
    text = compose(item["text"], item.get("tags", []))
    url, title, _ = card(item["slug"], item.get("en", False))
    print(f"--- {slug} ({len(text)}/{LIMIT}) ---\n{text}\n--- länkkort ---\n{title}\n{url}"
          + (f"\n--- svar ---\n{item['credit']}" if item.get("credit") else ""))
    if post:
        post_item(q, item)


def queue(post_due: bool):
    """data/bluesky/ko.json: posts the founder has approved, each with a planned date. At most ONE due post is sent per
    run (the earliest), so that a missed day does not send several at once; the post's address is written back."""
    q = json.load(open(KO, encoding="utf-8"))
    today = dt.date.today().isoformat()
    bad = []
    for item in q["items"]:
        n = len(item["text"].strip() + ("\n\n" + " ".join(f"#{t}" for t in item.get("tags", [])) if item.get("tags") else ""))
        if n > LIMIT:   # one over-long post must not stop the whole queue (it did 2026-10-31 – 11-02)
            bad.append(item["slug"])
        state = item.get("posted") or ("FÖR LÅNG – hoppas över" if n > LIMIT else "väntar" if item["date"] > today else "ska ut")
        print(f"{item['date']} {item['slug'][:40]:40} {n:3}/{LIMIT}  {state}")
    if bad:
        print("Varning: för långa inlägg i kön (kortas av grundaren eller Claude):", ", ".join(bad), file=sys.stderr)
    due = [i for i in q["items"] if not i.get("posted") and i["date"] <= today and i["slug"] not in bad]
    if not post_due or not due:
        return
    post_item(q, due[0])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("slug", nargs="?", help="artikelns adress, eller / för startsidan")
    ap.add_argument("--text", help="inläggets text (länken läggs i länkkortet)")
    ap.add_argument("--en", action="store_true", help="den engelska utgåvan")
    ap.add_argument("--tagg", action="append", default=[], help="hashtagg utan #, kan upprepas")
    ap.add_argument("--posta", action="store_true", help="skicka inlägget (annars visas det bara)")
    ap.add_argument("--ko", action="store_true", help="visa kön i data/bluesky/ko.json; med --posta skickas nästa inlägg som är dags")
    ap.add_argument("--nu", metavar="SLUG", help="ett visst inlägg ur kön nu (med --posta), före sitt datum")
    a = ap.parse_args(argv)
    if a.nu:
        return now(a.nu, a.posta)
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
    print("\nPostat:", *[x for x in send(text, url, title, desc, a.en) if x])


if __name__ == "__main__":
    main()
