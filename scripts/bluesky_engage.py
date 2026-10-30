"""Följ en person på Bluesky, gilla ett inlägg och svara kort – från Vitkis konto (BLUESKY_HANDLE/BLUESKY_APP_PASSWORD i .env).
    .venv/bin/python -m scripts.bluesky_engage --find "Namn"                    sök personen och visa senaste inlägg
    .venv/bin/python -m scripts.bluesky_engage --follow DID --like URI --reply URI --text "…"   gör det (visar vad som gjordes)"""
import argparse
import datetime as dt
import os
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


def session():
    handle, pw = os.environ.get("BLUESKY_HANDLE"), os.environ.get("BLUESKY_APP_PASSWORD")
    if not handle or not pw:
        sys.exit("BLUESKY_HANDLE och BLUESKY_APP_PASSWORD saknas i .env")
    s = requests.post(f"{PDS}/com.atproto.server.createSession", json={"identifier": handle, "password": pw}, timeout=30)
    s.raise_for_status()
    d = s.json()
    return {"Authorization": f"Bearer {d['accessJwt']}"}, d["did"]


def get(h, method, **params):
    r = requests.get(f"{PDS}/{method}", headers=h, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def create(h, did, collection, record):
    r = requests.post(f"{PDS}/com.atproto.repo.createRecord", headers=h,
                      json={"repo": did, "collection": collection, "record": record}, timeout=30)
    r.raise_for_status()
    return r.json()


ap = argparse.ArgumentParser()
ap.add_argument("--find")
ap.add_argument("--follow")
ap.add_argument("--like")
ap.add_argument("--reply")
ap.add_argument("--text")
a = ap.parse_args()
h, me = session()
now = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")

if a.find:
    for actor in get(h, "app.bsky.actor.searchActors", q=a.find, limit=5)["actors"]:
        print(f"{actor['did']}  @{actor['handle']}  {actor.get('displayName', '')}  | {(actor.get('description') or '')[:120]!r}")
    top = get(h, "app.bsky.actor.searchActors", q=a.find, limit=1)["actors"]
    if top:
        feed = get(h, "app.bsky.feed.getAuthorFeed", actor=top[0]["did"], limit=25, filter="posts_no_replies")["feed"]
        for item in feed:
            p = item["post"]
            if p["author"]["did"] != top[0]["did"]:
                continue  # a repost
            print(f"\n{p['indexedAt'][:10]}  ♥ {p.get('likeCount', 0)}  {p['uri']}\n  cid {p['cid']}\n  {p['record'].get('text', '')[:300]!r}")
    sys.exit()

done = []
if a.follow:
    out = create(h, me, "app.bsky.graph.follow", {"$type": "app.bsky.graph.follow", "subject": a.follow, "createdAt": now})
    done.append(f"följer {a.follow}")
if a.like:
    posts = get(h, "app.bsky.feed.getPosts", uris=[a.like])["posts"]
    p = posts[0]
    create(h, me, "app.bsky.feed.like", {"$type": "app.bsky.feed.like", "subject": {"uri": p["uri"], "cid": p["cid"]}, "createdAt": now})
    done.append(f"gillade {p['uri']}")
if a.reply:
    if not a.text:
        sys.exit("--text saknas")
    p = get(h, "app.bsky.feed.getPosts", uris=[a.reply])["posts"][0]
    root = p["record"].get("reply", {}).get("root", {"uri": p["uri"], "cid": p["cid"]})
    out = create(h, me, "app.bsky.feed.post", {"$type": "app.bsky.feed.post", "text": a.text, "createdAt": now, "langs": ["en"],
                                             "reply": {"root": root, "parent": {"uri": p["uri"], "cid": p["cid"]}}})
    rkey = out["uri"].rsplit("/", 1)[-1]
    done.append(f"svarade: https://bsky.app/profile/{os.environ['BLUESKY_HANDLE']}/post/{rkey}\n  text: {a.text!r}")
print("\n".join(done) or "inget gjort")
