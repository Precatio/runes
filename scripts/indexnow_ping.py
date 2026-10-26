"""Tells the search engines that use IndexNow (Bing, Yandex, Seznam, Naver …) which articles on vitkirunor.se are new,
changed or removed. Run by the website's build (.github/workflows/site.yml) after GitHub Pages has published the new
version, so the engines find the pages already live.

What changed is read from web/content/articles.json: the version in the commit before the push against the current one.
An article counts when it is new, removed, or its updatedAt or publishedAt differs (the daily view counts do not count).
Both language editions are sent, with the article lists and the sitemap. Without a previous version (a manual run)
only the lists and the sitemap are sent.

The key is public by design: the engines check that https://vitkirunor.se/<key>.txt holds it (web/public/<key>.txt).
Standard library only, so the build needs no installation.

  python3 scripts/indexnow_ping.py --before <sha> [--dry-run]
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import subprocess
import sys
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ARTICLES = "web/content/articles.json"
SITE = "https://vitkirunor.se"
ENDPOINT = "https://api.indexnow.org/indexnow"


def key() -> str:
    """The key: the one file web/public/<32 hex>.txt whose content is its own name."""
    for p in glob.glob(os.path.join(ROOT, "web", "public", "*.txt")):
        name = os.path.basename(p)[:-4]
        if re.fullmatch(r"[0-9a-f]{32}", name) and open(p, encoding="utf-8").read().strip() == name:
            return name
    raise SystemExit("Ingen IndexNow-nyckel i web/public/")


def _posts(doc: dict | None) -> dict[str, dict]:
    return {p["slug"]: p for p in (doc or {}).get("posts", []) if p.get("slug")}


def changed(old: dict | None, new: dict) -> list[str]:
    """The slugs that are new, removed, or whose updatedAt or publishedAt differs, sorted."""
    a, b = _posts(old), _posts(new)
    out = set(a) ^ set(b)
    for slug in set(a) & set(b):
        if any(a[slug].get(k) != b[slug].get(k) for k in ("updatedAt", "publishedAt")):
            out.add(slug)
    return sorted(out)


def urls(slugs: list[str], new: dict, site: str = SITE) -> list[str]:
    """Each changed article in Swedish, and in English when it has an English edition (or had one, if removed), then the
    article lists and the sitemap."""
    b = _posts(new)
    out = []
    for slug in slugs:
        out.append(f"{site}/artiklar/{slug}/")
        if slug not in b or b[slug].get("body_en"):
            out.append(f"{site}/en/artiklar/{slug}/")
    return out + [f"{site}/artiklar/", f"{site}/en/artiklar/", f"{site}/sitemap.xml"]


def previous(before: str | None) -> dict | None:
    if not before or set(before) == {"0"}:
        return None
    r = subprocess.run(["git", "show", f"{before}:{ARTICLES}"], cwd=ROOT, capture_output=True, text=True)
    return json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--before", default=os.environ.get("BEFORE"))
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    new = json.load(open(os.path.join(ROOT, ARTICLES), encoding="utf-8"))
    old = previous(a.before)
    slugs = changed(old, new) if old is not None else []
    if old is not None and not slugs:
        print("IndexNow: inga nya eller ändrade artiklar.")
        return 0
    k = key()
    body = {"host": SITE.split("://", 1)[1], "key": k, "keyLocation": f"{SITE}/{k}.txt", "urlList": urls(slugs, new)}
    print("IndexNow:", *body["urlList"], sep="\n  ")
    if a.dry_run:
        return 0
    req = urllib.request.Request(ENDPOINT, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            print("IndexNow svarade", r.status)
    except Exception as e:  # noqa: BLE001 - a failed ping only delays indexing; the build has already published
        print(f"::warning::IndexNow misslyckades: {e!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
