"""Statistik för Vitkis repo på GitHub (Precatio/runes) till Admin: stjärnor, forkar, bevakare, nedladdningar av
releaser och – med en token – kloner, besök och varifrån besökarna kommer.

GitHub sparar trafiken (kloner och besök per dag) bara i 14 dagar. Varje hämtning läggs därför till i
data/github/history.json, så att historiken växer så länge Admin öppnas minst varannan vecka.

Token: GITHUB_TOKEN i miljön eller i projektets .env (aldrig i koden). En finkornig token för repot med behörigheten
"Administration: Read-only" räcker. Utan token visas bara det som är offentligt.

Vad som räknas: en klon är en `git clone` eller `git pull` från ett nytt ställe, också från robotar och tjänster;
nedladdningar av källkodens zip-fil räknar GitHub inte. Filer som bifogas en release räknas för sig – det säkraste
måttet på nedladdningar.
"""
from __future__ import annotations

import json
import os
import re
import threading
import time
from datetime import datetime, timezone

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HISTORY = os.path.join(ROOT, "data", "github", "history.json")
API = "https://api.github.com"
MAX_AGE = 3600  # GitHub is asked at most once an hour
_lock = threading.Lock()
_cache: dict = {"at": 0.0, "stats": None}


def repo() -> str:
    return os.environ.get("GITHUB_REPO", "Precatio/runes")


def token() -> str:
    """GITHUB_TOKEN from the environment, or from the project's .env (which is never committed)."""
    t = os.environ.get("GITHUB_TOKEN", "").strip()
    if t:
        return t
    try:
        m = re.search(r'^GITHUB_TOKEN\s*=\s*"?([^"\s]+)"?', open(os.path.join(ROOT, ".env"), encoding="utf-8").read(), re.M)
        return m.group(1) if m else ""
    except OSError:
        return ""


def _get(path: str, tok: str):
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "Vitki"}
    if tok:
        headers["Authorization"] = f"Bearer {tok}"
    r = requests.get(f"{API}/repos/{repo()}{path}", headers=headers, timeout=15)
    r.raise_for_status()
    return r.json()


def _load() -> dict:
    try:
        with open(HISTORY, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {"days": {}}


def _save(h: dict) -> None:
    os.makedirs(os.path.dirname(HISTORY), exist_ok=True)
    tmp = HISTORY + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(h, fh, ensure_ascii=False, indent=0, sort_keys=True)
    os.replace(tmp, HISTORY)


def merge(history: dict, clones: dict | None, views: dict | None) -> dict:
    """GitHub's 14 days into the history, day by day; a day's newest numbers replace older ones for the same day."""
    days = history.setdefault("days", {})
    for kind, data in (("clones", clones), ("views", views)):
        for d in (data or {}).get(kind) or []:
            day = d["timestamp"][:10]
            row = days.setdefault(day, {})
            row[kind] = d.get("count", 0)
            row[f"{kind}_uniques"] = d.get("uniques", 0)
    return history


def _fetch() -> dict:
    tok = token()
    info = _get("", tok)
    releases = _get("/releases?per_page=100", tok)
    out = {
        "repo": repo(), "url": info.get("html_url"),
        "stars": info.get("stargazers_count", 0), "forks": info.get("forks_count", 0),
        "watchers": info.get("subscribers_count", 0), "open_issues": info.get("open_issues_count", 0),
        "created_at": info.get("created_at"), "pushed_at": info.get("pushed_at"),
        "releases": [{"tag": r.get("tag_name"), "name": r.get("name"), "published_at": r.get("published_at"),
                      "downloads": sum(a.get("download_count", 0) for a in r.get("assets") or [])} for r in releases],
        "traffic": {"available": False, "reason": "Lägg GITHUB_TOKEN i .env för kloner och besök (se Admin)."},
    }
    out["release_downloads"] = sum(r["downloads"] for r in out["releases"])
    if not tok:
        return out
    try:
        clones, views = _get("/traffic/clones", tok), _get("/traffic/views", tok)
        referrers, paths = _get("/traffic/popular/referrers", tok), _get("/traffic/popular/paths", tok)
    except requests.HTTPError as e:
        code = e.response.status_code if e.response is not None else "?"
        out["traffic"] = {"available": False,
                          "reason": f"GitHub nekade trafikuppgifterna ({code}); token behöver behörigheten "
                                    "Administration: Read-only för repot."}
        return out
    with _lock:
        h = merge(_load(), clones, views)
        _save(h)
    days = [{"day": d, **v} for d, v in sorted(h["days"].items())]
    out["traffic"] = {
        "available": True,
        "last14": {"clones": clones.get("count", 0), "clone_uniques": clones.get("uniques", 0),
                   "views": views.get("count", 0), "view_uniques": views.get("uniques", 0)},
        "total": {"clones": sum(d.get("clones", 0) for d in days), "views": sum(d.get("views", 0) for d in days),
                  "since": days[0]["day"] if days else None},
        "days": days,
        "referrers": [{"referrer": r["referrer"], "count": r.get("count", 0), "uniques": r.get("uniques", 0)} for r in referrers],
        "paths": [{"path": p["path"], "title": p.get("title"), "count": p.get("count", 0), "uniques": p.get("uniques", 0)}
                  for p in paths[:10]],
    }
    return out


def stats(refresh: bool = False) -> dict:
    """The statistics, from GitHub at most once an hour (refresh=True asks again at once)."""
    if not refresh and _cache["stats"] is not None and time.time() - _cache["at"] < MAX_AGE:
        return _cache["stats"]
    s = _fetch()
    s["fetched_at"] = datetime.now(timezone.utc).isoformat()
    _cache.update(at=time.time(), stats=s)
    return s
