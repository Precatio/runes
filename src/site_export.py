"""Den publika webbplatsen (vitkirunor.se, GitHub Pages) byggs utan analysmotor: artiklarna exporteras härifrån till
web/content/articles.json och deras figurer till web/public/figurer/, och GitHub bygger om webbplatsen när de pushas
(.github/workflows/site.yml).

Bara artiklar som har gått live exporteras – repot är publikt, så en schemalagd artikel får inte ligga där i förväg. Den
lokala appen publicerar därför webbplatsen själv: en halv minut efter att en publicerad artikel har sparats, ändrats eller
tagits bort (så att snabba ändringar blir en publicering), och när en schemalagd artikels tid har kommit – så länge appen
är igång, och annars när den startar nästa gång. SITE_PUBLISH=0 stänger av det.

    .venv/bin/python -m src.site_export            # exportera
    .venv/bin/python -m src.site_export --push     # exportera, committa och pusha (publicera webbplatsen)
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import threading

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT = os.path.join(ROOT, "web", "content", "articles.json")
FIGURES = os.path.join(ROOT, "web", "public", "figurer")
FIELDS = ("id", "slug", "title", "summary", "body", "title_en", "summary_en", "body_en", "month", "author", "topic",
          "publishedAt", "updatedAt")
FIGURE = re.compile(r"/api/blog/figures/([0-9a-f]{16}\.png)")


def export(posts: list[dict], now_iso: str) -> dict:
    """Skriver de artiklar som har gått live och deras figurer; returnerar en sammanfattning."""
    from api.routers.blog import is_live
    from src import blog_figures
    now = dt.datetime.fromisoformat(now_iso)
    published = [{k: p.get(k) for k in FIELDS} for p in posts if is_live(p, now)]
    published.sort(key=lambda p: p.get("publishedAt") or p.get("month") or "", reverse=True)
    os.makedirs(os.path.dirname(CONTENT), exist_ok=True)
    with open(CONTENT, "w", encoding="utf-8") as fh:
        json.dump({"exported_at": now_iso, "posts": published}, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    names = sorted({m for p in published for f in ("body", "body_en") for m in FIGURE.findall(p.get(f) or "")})
    os.makedirs(FIGURES, exist_ok=True)
    missing = []
    for name in names:
        src = blog_figures.path_of(name)
        if src:
            shutil.copyfile(src, os.path.join(FIGURES, name))
        else:
            missing.append(name)
    for old in os.listdir(FIGURES):  # figures no published article uses any more
        if old.endswith(".png") and old not in names:
            os.remove(os.path.join(FIGURES, old))
    return {"articles": len(published), "figures": len(names), "missing_figures": missing}


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=120)


def push() -> dict:
    """Committar och pushar det exporterade (bara artiklarna och figurerna), så att GitHub bygger om webbplatsen."""
    paths = [os.path.relpath(CONTENT, ROOT), os.path.relpath(FIGURES, ROOT)]
    _git("add", "-A", "--", *paths)
    if not _git("diff", "--cached", "--quiet", "--", *paths).returncode:
        return {"pushed": False, "note": "Webbplatsen har redan de senaste artiklarna."}
    c = _git("commit", "-m", "Webbplatsen: artiklarna uppdaterade", "--", *paths)
    if c.returncode:
        return {"pushed": False, "note": (c.stderr or c.stdout).strip()[-400:]}
    p = _git("push")
    if p.returncode:
        return {"pushed": False, "note": "Committat men inte pushat: " + (p.stderr or p.stdout).strip()[-400:]}
    return {"pushed": True, "note": "Pushat till GitHub – webbplatsen byggs om på några minuter."}


# ---- automatic publishing ------------------------------------------------------------------------------------------

_lock = threading.Lock()
_timers: dict[str, threading.Timer] = {}
DEBOUNCE_S = 30


def enabled() -> bool:
    return os.environ.get("SITE_PUBLISH", "1") != "0" and os.path.isdir(os.path.join(ROOT, ".git"))


def publish_now() -> dict:
    """Exporterar och pushar (en i taget)."""
    from api.errors import logger
    from api.routers import blog
    with _lock:
        out = export(blog._all(), dt.datetime.now(dt.timezone.utc).isoformat())
        out.update(push())
    logger.info("Webbplatsen: %s", out)
    return out


def _later(key: str, seconds: float, fn) -> None:
    old = _timers.pop(key, None)
    if old:
        old.cancel()
    t = threading.Timer(max(1.0, seconds), fn)
    t.daemon = True
    _timers[key] = t
    t.start()


def _quietly(fn):
    def run():
        try:
            fn()
        except Exception as e:  # noqa: BLE001 - the next save or start tries again
            from api.errors import logger
            logger.warning("Webbplatsen kunde inte publiceras: %r", e)
    return run


def publish_soon() -> None:
    """Publicerar webbplatsen om en halv minut; en ny ändring före dess skjuter upp den."""
    if enabled():
        _later("soon", DEBOUNCE_S, _quietly(publish_now))


def schedule(posts: list[dict]) -> None:
    """Publicerar webbplatsen när nästa schemalagda artikel går live."""
    if not enabled():
        return
    from api.routers.blog import _ts
    now = dt.datetime.now(dt.timezone.utc)
    times = [t for p in posts if p.get("published") and (t := _ts(p.get("publishedAt"))) and t > now]
    if not times:
        _later("scheduled", 10 ** 9, lambda: None)
        return

    def fire():
        from api.routers import blog
        publish_now()
        schedule(blog._all())
    _later("scheduled", (min(times) - now).total_seconds() + 5, _quietly(fire))


def catch_up(posts: list[dict]) -> None:
    """Vid start: har en artikel gått live sedan webbplatsen senast publicerades (appen var avstängd när en schemalagd
    artikels tid kom), publiceras webbplatsen nu. Planerar sedan nästa schemalagda artikel."""
    if not enabled():
        return
    from api.routers.blog import is_live
    try:
        with open(CONTENT, encoding="utf-8") as fh:
            exported = {p["slug"] for p in json.load(fh).get("posts", [])}
    except (OSError, ValueError):
        exported = set()
    # Only articles that were scheduled (their time after their last save): an article published at once goes out with
    # the save, and one waiting for "Publicera webbplatsen" stays under the editor's control
    from api.routers.blog import _ts
    due = [p for p in posts if is_live(p) and p.get("slug") not in exported
           and (_ts(p.get("publishedAt")) or dt.datetime.min.replace(tzinfo=dt.timezone.utc))
           > (_ts(p.get("updatedAt")) or dt.datetime.max.replace(tzinfo=dt.timezone.utc))]
    if due:
        _quietly(publish_now)()
    schedule(posts)


def main() -> None:
    from api.routers import blog
    out = export(blog._all(), dt.datetime.now(dt.timezone.utc).isoformat())
    if "--push" in sys.argv:
        out.update(push())
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
