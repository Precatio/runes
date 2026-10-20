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
import time

from src import spawn

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT = os.path.join(ROOT, "web", "content", "articles.json")
FIGURES = os.path.join(ROOT, "web", "public", "figurer")
FIELDS = ("id", "slug", "title", "summary", "body", "title_en", "summary_en", "body_en", "month", "author", "topic",
          "publishedAt", "updatedAt", "featured", "labels")
FIGURE = re.compile(r"/api/blog/figures/([0-9a-f]{16}\.png)")
# The latest attempt to publish the website, so that Admin can show whether the site got the change
STATUS = os.path.join(ROOT, "data", "cache", "site_publish.json")


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
    # sökrutans index, samma format som GET /api/blog/search_index serverar lokalt
    from src.blog_search import build_index
    with open(os.path.join(ROOT, "web", "public", "artiklar-sok.json"), "w", encoding="utf-8") as fh:
        json.dump({"posts": build_index(published)}, fh, ensure_ascii=False)
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
    return spawn.run(["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=120)  # src/spawn.py: no fork


def _step(name: str, *args: str, tries: int = 1) -> subprocess.CompletedProcess:
    """A git command; when it fails, it is tried again a few times (another git command, such as the editor's, may
    hold the index for a moment) and the failure is logged with git's own message."""
    r = _git(*args)
    for _ in range(tries - 1):
        if not r.returncode:
            break
        time.sleep(2)
        r = _git(*args)
    if r.returncode and not (name == "diff" and r.returncode == 1):
        from api.errors import logger
        logger.warning("Webbplatsen: git %s misslyckades (%s): %s", name, r.returncode, (r.stderr or r.stdout).strip()[-600:])
    return r


def push() -> dict:
    """Committar och pushar det exporterade (bara artiklarna och figurerna), så att GitHub bygger om webbplatsen."""
    paths = [os.path.relpath(CONTENT, ROOT), os.path.relpath(FIGURES, ROOT)]
    a = _step("add", "add", "-A", "--", *paths, tries=8)
    if a.returncode:
        return {"pushed": False, "note": "Kunde inte lägga till artiklarna i git: " + (a.stderr or a.stdout).strip()[-400:]}
    if not _git("diff", "--cached", "--quiet", "--", *paths).returncode:
        return {"pushed": False, "note": "Webbplatsen har redan de senaste artiklarna."}
    c = _step("commit", "commit", "-m", "Webbplatsen: artiklarna uppdaterade", "--", *paths, tries=8)
    if c.returncode:
        return {"pushed": False, "note": "Kunde inte committa artiklarna: " + (c.stderr or c.stdout).strip()[-400:]}
    p = _step("push", "push", tries=2)
    if p.returncode:
        return {"pushed": False, "note": "Committat men inte pushat: " + (p.stderr or p.stdout).strip()[-400:]}
    return {"pushed": True, "note": "Pushat till GitHub – webbplatsen byggs om på några minuter."}


def check_git() -> bool:
    """Vid start: kan appen använda git för webbplatsen? Ett fel loggas med gits eget meddelande."""
    if not enabled():
        return False
    paths = [os.path.relpath(CONTENT, ROOT), os.path.relpath(FIGURES, ROOT)]
    return not _step("add --dry-run", "add", "--dry-run", "-A", "--", *paths).returncode


def record(out: dict) -> dict:
    """Sparar hur det senaste försöket att publicera webbplatsen gick (data/cache/site_publish.json)."""
    out = {**out, "at": dt.datetime.now(dt.timezone.utc).isoformat()}
    try:
        os.makedirs(os.path.dirname(STATUS), exist_ok=True)
        with open(STATUS, "w", encoding="utf-8") as fh:
            json.dump(out, fh, ensure_ascii=False)
    except OSError:
        pass
    return out


def status() -> dict:
    """Det senaste försöket att publicera webbplatsen, och om det finns ändringar som inte har pushats."""
    try:
        with open(STATUS, encoding="utf-8") as fh:
            out = json.load(fh)
    except (OSError, ValueError):
        out = {}
    paths = [os.path.relpath(CONTENT, ROOT), os.path.relpath(FIGURES, ROOT)]
    try:
        r = _git("status", "--porcelain", "--", *paths)
        out["unpushed"] = bool(r.stdout.strip()) if not r.returncode else None
    except (OSError, subprocess.SubprocessError):
        out["unpushed"] = None
    return out


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
        try:
            out = export(blog._all(), dt.datetime.now(dt.timezone.utc).isoformat())
            out.update(push())
        except Exception as e:  # noqa: BLE001 - recorded for Admin, then raised as before
            record({"pushed": False, "note": f"Webbplatsen kunde inte publiceras: {e!r}"})
            raise
    (logger.info if out.get("pushed") or "redan" in out.get("note", "") else logger.warning)("Webbplatsen: %s", out)
    return record(out)


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
