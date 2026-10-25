"""Measures candidate hashtags on Bluesky over the last 30 days: posts, authors, likes, topical relevance and the share of
authors who describe themselves as researchers or heritage professionals (read-only public search)."""
import datetime as dt, json, re, statistics, sys, time
import requests
API = "https://api.bsky.app/xrpc"
TAGS = sys.argv[1].split(",")
since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
TOPIC = re.compile(r"rune|runic|runo|futhark|fuþark|viking|norse|saga|edda|medieval|middle ages|early medieval|scandinav|"
                   r"iceland|archaeolog|excavat|inscription|epigraph|manuscript|anglo-saxon|old english|heritage|museum|"
                   r"runsten|vikinga|fornnordisk|arkeolog|medeltid", re.I)
ACAD = re.compile(r"phd|ph\.d|dr\b|professor|prof\b|lecturer|researcher|research|postdoc|doctoral|academic|universit|"
                  r"archaeolog|historian|medievalist|philolog|linguist|runolog|curator|museum|heritage|scholar|epigraph|"
                  r"forskare|arkeolog|doktorand|lektor", re.I)
prof_cache = {}
def profiles(dids):
    need = [d for d in dids if d not in prof_cache]
    for i in range(0, len(need), 25):
        r = requests.get(f"{API}/app.bsky.actor.getProfiles", params=[("actors", d) for d in need[i:i + 25]], timeout=30)
        for p in r.json().get("profiles", []):
            prof_cache[p["did"]] = (p.get("description") or "") + " " + (p.get("displayName") or "")
        time.sleep(0.3)
    return [prof_cache.get(d, "") for d in dids]
out = {}
for tag in TAGS:
    posts, cursor = [], None
    for _ in range(5):
        params = {"q": f"#{tag}", "limit": 100, "sort": "latest"}
        if cursor: params["cursor"] = cursor
        r = requests.get(f"{API}/app.bsky.feed.searchPosts", params=params, timeout=30)
        if r.status_code != 200: break
        d = r.json(); batch = d.get("posts", []); cursor = d.get("cursor")
        fresh = [p for p in batch if (p.get("indexedAt") or p["record"].get("createdAt", "")) >= since]
        posts += fresh
        if len(fresh) < len(batch): cursor = None  # older than 30 days from here on
        time.sleep(0.4)
        if not cursor: break
    authors = list({p["author"]["did"] for p in posts})
    descs = profiles(authors[:150])
    rel = sum(1 for p in posts if TOPIC.search(p["record"].get("text", ""))) / max(1, len(posts))
    acad = sum(1 for s in descs if ACAD.search(s)) / max(1, len(descs))
    likes = [p.get("likeCount", 0) for p in posts]
    out[tag] = {"posts": len(posts), "capped": len(posts) >= 500, "authors": len(authors), "relevant": round(rel, 2),
                "academic_authors": round(acad, 2), "median_likes": statistics.median(likes) if likes else 0,
                "mean_likes": round(statistics.mean(likes), 1) if likes else 0}
    print(f"#{tag:20} {len(posts):4}{'+' if len(posts) >= 500 else ' '} inlägg {len(authors):4} författare  relevanta {rel:4.0%}  forskare {acad:4.0%}  likes median {out[tag]['median_likes']}", flush=True)
json.dump(out, open("/Volumes/2TB/cache/bluesky/hashtags.json", "w"), indent=1)
