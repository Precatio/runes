"""Den publika webbplatsen (vitkirunor.se, GitHub Pages) byggs utan analysmotor: artiklarna exporteras härifrån till
web/content/articles.json, sökrutans index till web/public/artiklar-sok.json och figurerna till web/public/figurer/
(som WebP, src/blog_figures.py), och GitHub bygger om webbplatsen när de pushas (.github/workflows/site.yml).

Bara artiklar som har gått live exporteras – repot är publikt, så en schemalagd artikel får inte ligga där i förväg. Den
lokala appen publicerar därför webbplatsen själv: en halv minut efter att en publicerad artikel har sparats, ändrats eller
tagits bort (så att snabba ändringar blir en publicering), och när en schemalagd artikels tid har kommit – så länge appen
är igång, och annars när den startar nästa gång. SITE_PUBLISH=0 stänger av det.

En export som ser fel ut (inga artiklar alls, fler än några artiklar som försvinner på en gång, figurer som saknas)
skrivs inte och pushas inte; SITE_PUBLISH_FORCE=1, --force eller Admins knapp med force publicerar ändå.

    .venv/bin/python -m src.site_export            # exportera
    .venv/bin/python -m src.site_export --push     # exportera, committa och pusha (publicera webbplatsen)
    .venv/bin/python -m src.site_export --force    # exportera också när kontrollen stoppar det
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
from collections import Counter, defaultdict

from src import spawn

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT = os.path.join(ROOT, "web", "content", "articles.json")
FIGURES = os.path.join(ROOT, "web", "public", "figurer")
# The search box's index (src/blog_search.py), the same format as GET /api/blog/search_index serves locally
SEARCH = os.path.join(ROOT, "web", "public", "artiklar-sok.json")
FIELDS = ("id", "slug", "title", "summary", "body", "title_en", "summary_en", "body_en", "month", "author", "topic",
          "publishedAt", "updatedAt", "featured", "labels")
FIGURE = re.compile(r"/api/blog/figures/([0-9a-f]{16}\.png)")
# A Commons photo in an article: ![alt](https://upload.wikimedia.org/… or https://thumb.wikimedia.org/…) at the start
# of a line (components/BlogBody.tsx)
PHOTO = re.compile(r"^(!\[[^\]]*\]\()(https://(?:upload|thumb)\.wikimedia\.org/[^)\s]+)(\))", re.M)
# The latest attempt to publish the website, so that Admin can show whether the site got the change
STATUS = os.path.join(ROOT, "data", "cache", "site_publish.json")
# A publication asked for (a saved article) that has not reached the website yet; survives a restart of the server
PENDING = os.path.join(ROOT, "data", "cache", "site_publish_pending.json")
# The sanity check: more articles than this disappearing in one export stops it (a deliberate removal: force)
MAX_REMOVED = 2


def _write_json(path: str, data: dict, **kw) -> None:
    """Writes through a temporary file, so that a reader (or a commit) never sees half a file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, **kw)
        fh.write("\n")
    os.replace(tmp, path)


def _exported_slugs() -> set[str]:
    try:
        with open(CONTENT, encoding="utf-8") as fh:
            return {p["slug"] for p in json.load(fh).get("posts", [])}
    except (OSError, ValueError, KeyError, TypeError):
        return set()


def check(published: list[dict], missing: list[str]) -> str | None:
    """Varför exporten ser fel ut och inte ska skrivas, eller None: inga artiklar alls fast webbplatsen har några (fel
    databas, tom läsning), fler än MAX_REMOVED artiklar som försvinner på en gång, eller figurer som inte finns."""
    before = _exported_slugs()
    gone = sorted(before - {p.get("slug") for p in published})
    if before and not published:
        return (f"Exporten gav inga publicerade artiklar, men webbplatsen har {len(before)}. Läste appen fel databas? "
                "Inget skrevs eller pushades.")
    if len(gone) > MAX_REMOVED:
        return (f"{len(gone)} artiklar skulle försvinna från webbplatsen på en gång ({', '.join(gone[:6])}"
                f"{' …' if len(gone) > 6 else ''}). Inget skrevs eller pushades; är det avsiktligt, publicera med force.")
    if missing:
        return (f"Figurer saknas ({', '.join(missing[:6])}{' …' if len(missing) > 6 else ''}): artiklarna skulle få trasiga "
                "bilder. Inget skrevs eller pushades.")
    return None


def _figures(names: list[str]) -> tuple[dict[str, str], list[str]]:
    """Writes the website's copy of each figure (WebP, src/blog_figures.py) unless it is already there; returns the
    frozen name → the exported file name, and the figures that could not be found."""
    from api.errors import logger
    from src import blog_figures
    files, missing = {}, []
    for name in names:
        out = blog_figures.site_name(name)
        dst = os.path.join(FIGURES, out)
        if not os.path.exists(dst):  # the names are immutable: an existing copy is already right
            legacy = os.path.join(FIGURES, name)  # an earlier export's PNG, when the frozen figure is not on this machine
            src = blog_figures.path_of(name) or (legacy if os.path.exists(legacy) else None)
            if not src:
                missing.append(name)
                continue
            try:
                blog_figures.to_site(src, dst)
            except Exception as e:  # noqa: BLE001 - the PNG as before rather than no figure
                logger.warning("Webbplatsen: figuren %s kunde inte göras till WebP (%r); PNG:en används", name, e)
                if src != legacy:
                    shutil.copyfile(src, legacy)
                out = name
        files[name] = out
    return files, missing


def _photo_sizes(urls: list[str]) -> dict[str, dict]:
    """The Commons originals' sizes (src/commons.py); empty when Commons cannot be reached, so nothing changes."""
    from src import commons
    try:
        return commons.original_sizes([n for u in urls if (n := commons.original_name(u))])
    except Exception as e:  # noqa: BLE001 - the export never fails on Commons
        from api.errors import logger
        logger.warning("Webbplatsen: bildstorlekarna på Commons kunde inte hämtas (%r); adresserna står kvar", e)
        return {}


def _lighter(published: list[dict], files: dict[str, str]) -> None:
    """The website's addresses in the exported texts (the copy written to articles.json only; Firestore and the local
    app keep their own): the figures' WebP copies, and Commons photos at the width the article column needs."""
    from src import commons
    texts = ("body", "body_en")
    urls = sorted({m.group(2) for p in published for f in texts for m in PHOTO.finditer(p.get(f) or "")})
    sizes = _photo_sizes(urls) if urls else {}
    for p in published:
        for f in texts:
            if p.get(f):
                t = FIGURE.sub(lambda m: f"/figurer/{files[m.group(1)]}" if files.get(m.group(1), "").endswith(".webp")
                               else m.group(0), p[f])
                p[f] = PHOTO.sub(lambda m: m.group(1) + commons.site_photo(m.group(2), sizes) + m.group(3), t)


def export(posts: list[dict], now_iso: str, force: bool = False) -> dict:
    """Skriver de artiklar som har gått live, sökindexet och figurerna; returnerar en sammanfattning. Ser exporten fel
    ut (check) skrivs ingenting, och sammanfattningen har blocked med skälet – utom med force."""
    from api.routers.blog import is_live
    from src import blog_figures
    force = force or os.environ.get("SITE_PUBLISH_FORCE") == "1"
    now = dt.datetime.fromisoformat(now_iso)
    published = [{k: p.get(k) for k in FIELDS} for p in posts if is_live(p, now)]
    published.sort(key=lambda p: p.get("publishedAt") or p.get("month") or "", reverse=True)
    names = sorted({m for p in published for f in ("body", "body_en") for m in FIGURE.findall(p.get(f) or "")})
    gone = [n for n in names if not blog_figures.path_of(n) and not os.path.exists(os.path.join(FIGURES, blog_figures.site_name(n)))
            and not os.path.exists(os.path.join(FIGURES, n))]
    blocked = None if force else check(published, gone)
    if blocked:
        return {"articles": len(published), "figures": len(names), "missing_figures": gone, "blocked": blocked}
    # "Mest lästa": the page views per article, from the site's own counting (src/site_stats.py); when Firestore cannot
    # be read the counts of the previous export stay, so that a failed read never zeroes the order
    views = article_views()
    if views is None:
        views = previous_views()
    for p in published:
        p["views"] = int(views.get(p["slug"], 0))
    os.makedirs(FIGURES, exist_ok=True)
    files, missing = _figures(names)
    _lighter(published, files)
    _write_json(CONTENT, {"exported_at": now_iso, "posts": published}, indent=1)
    from src.blog_search import build_index
    _write_json(SEARCH, {"posts": build_index(published)})
    keep = set(files.values())
    for old in os.listdir(FIGURES):  # figures no published article uses any more, and copies in an older format
        if old.endswith((".png", ".webp")) and old not in keep:
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


# Site views counted per article and day at most: about six times the busiest real day so far (8, October 2026), so a
# script that writes views by the thousand (the collection is open for anonymous writes, web/firestore.rules) moves an
# article by at most this much a day. Raise it if real traffic comes near.
VIEWS_PER_DAY = 50


def capped_views(rows: list[dict]) -> dict[str, int]:
    """Sidvisningar per artikel (src/site_stats.views_by_slug), högst VIEWS_PER_DAY per artikel och dag."""
    from src.site_stats import views_by_slug
    days: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        days[str(r.get("day") or "")].append(r)
    out: Counter = Counter()
    for day in days.values():
        for slug, n in views_by_slug(day).items():
            out[slug] += min(n, VIEWS_PER_DAY)
    return dict(out)


def article_views() -> dict[str, int] | None:
    """Sidvisningar per artikel ur samlingen site_views (bara sökväg, dag, tidszon och språk läses; säkra robotar räknas inte), högst VIEWS_PER_DAY per artikel och
    dag; None när Firestore inte kan nås."""
    try:
        from google.cloud.firestore_v1.base_query import FieldFilter

        from api.auth import firestore
        query = firestore().collection("site_views").where(filter=FieldFilter("kind", "==", "view")).select(["path", "kind", "day", "tz", "lang"])
        return capped_views([d.to_dict() or {} for d in query.stream()])
    except Exception as e:  # noqa: BLE001 - the export must not fail on the statistics
        from api.errors import logger
        logger.warning("Webbplatsen: sidvisningarna kunde inte hämtas (%r); föregående antal behålls", e)
        return None


def previous_views() -> dict[str, int]:
    try:
        with open(CONTENT, encoding="utf-8") as fh:
            return {p["slug"]: int(p.get("views") or 0) for p in json.load(fh).get("posts", [])}
    except (OSError, ValueError, KeyError):
        return {}


def views_order(posts: list[dict]) -> list[str]:
    """Artiklarna i den ordning "mest lästa" visar dem: flest visningar först, lika många efter datum."""
    return [p["slug"] for p in sorted(posts, key=lambda p: (int(p.get("views") or 0), p.get("publishedAt") or ""), reverse=True)]


# A new order of "mest lästa" is published only when some article's count has moved by at least this many views (or a
# tenth of its count, if more) since the last export: a single view that breaks a tie gives no commit of its own
VIEWS_MIN_CHANGE = 5


def views_moved(old: list[dict], fresh: list[dict]) -> bool:
    """Har ordningen "mest lästa" ändrats av mer än enstaka visningar sedan webbplatsen senast publicerades?"""
    if views_order(fresh) == views_order(old):
        return False
    before = {p["slug"]: int(p.get("views") or 0) for p in old}
    return any(abs(int(p.get("views") or 0) - before.get(p["slug"], 0)) >= max(VIEWS_MIN_CHANGE, before.get(p["slug"], 0) // 10)
               for p in fresh)


def _paths() -> list[str]:
    """What the app commits for the website: the articles, the search index and the figures."""
    return [os.path.relpath(CONTENT, ROOT), os.path.relpath(SEARCH, ROOT), os.path.relpath(FIGURES, ROOT)]


def push() -> dict:
    """Committar och pushar det exporterade (bara artiklarna, sökindexet och figurerna), så att GitHub bygger om
    webbplatsen."""
    paths = _paths()
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
    return not _step("add --dry-run", "add", "--dry-run", "-A", "--", *_paths()).returncode


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
    try:
        r = _git("status", "--porcelain", "--", *_paths())
        out["unpushed"] = bool(r.stdout.strip()) if not r.returncode else None
    except (OSError, subprocess.SubprocessError):
        out["unpushed"] = None
    out["pending"] = os.path.exists(PENDING)
    return out


# ---- automatic publishing ------------------------------------------------------------------------------------------

_lock = threading.Lock()
_timers: dict[str, threading.Timer] = {}
DEBOUNCE_S = 30


def enabled() -> bool:
    return os.environ.get("SITE_PUBLISH", "1") != "0" and os.path.isdir(os.path.join(ROOT, ".git"))


def _mark_pending() -> None:
    """Notes that the website should be published, so that a restart of the server (uvicorn --reload) before the
    half minute is up does not lose it: catch_up() publishes at the next start."""
    try:
        os.makedirs(os.path.dirname(PENDING), exist_ok=True)
        with open(PENDING, "w", encoding="utf-8") as fh:
            json.dump({"at": dt.datetime.now(dt.timezone.utc).isoformat()}, fh)
    except OSError:
        pass


def _clear_pending() -> None:
    try:
        os.remove(PENDING)
    except OSError:
        pass


def publish_now(force: bool = False) -> dict:
    """Exporterar och pushar (en i taget). Stoppar kontrollen exporten (check) pushas ingenting och skälet visas i
    Admin; force publicerar ändå."""
    from api.errors import logger
    from api.routers import blog
    with _lock:
        try:
            out = export(blog._all(), dt.datetime.now(dt.timezone.utc).isoformat(), force=force)
            if out.get("blocked"):
                out.update(pushed=False, note="Webbplatsen publicerades inte: " + out["blocked"])
            else:
                out.update(push())
        except Exception as e:  # noqa: BLE001 - recorded for Admin, then raised as before
            record({"pushed": False, "note": f"Webbplatsen kunde inte publiceras: {e!r}"})
            raise
        # The request is done when the site has the change, or when the check stopped it (Admin shows why); a failed
        # git step leaves it pending, so that the next start tries again
        if out.get("pushed") or out.get("blocked") or "redan" in out.get("note", ""):
            _clear_pending()
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
    """Publicerar webbplatsen om en halv minut; en ny ändring före dess skjuter upp den. Önskan sparas på disk, så att
    den överlever en omstart av servern."""
    if enabled():
        _mark_pending()
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


VIEWS_REFRESH_S = 24 * 3600


def refresh_views() -> None:
    """En gång om dygnet: har ordningen "mest lästa" ändrats märkbart (views_moved) sedan webbplatsen senast
    publicerades, publiceras den om – annars inte, så att räkningen inte ger en commit om dagen."""
    try:
        with open(CONTENT, encoding="utf-8") as fh:
            posts = json.load(fh).get("posts", [])
    except (OSError, ValueError):
        posts = []
    views = article_views()
    if posts and views is not None:
        fresh = [{**p, "views": int(views.get(p["slug"], 0))} for p in posts]
        if views_moved(posts, fresh):
            publish_now()
    _later("views", VIEWS_REFRESH_S, _quietly(refresh_views))


def start_view_refresh() -> None:
    """Vid start: första kontrollen av ordningen efter en kvart, sedan en gång om dygnet."""
    if enabled():
        _later("views", 15 * 60, _quietly(refresh_views))


def catch_up(posts: list[dict]) -> None:
    """Vid start: har en artikel gått live sedan webbplatsen senast publicerades (appen var avstängd när en schemalagd
    artikels tid kom), publiceras webbplatsen nu; väntade en publicering när servern startades om, görs den om en halv
    minut. Planerar sedan nästa schemalagda artikel."""
    if not enabled():
        return
    from api.routers.blog import is_live
    exported = _exported_slugs()
    # Only articles that were scheduled (their time after their last save): an article published at once goes out with
    # the save, and one waiting for "Publicera webbplatsen" stays under the editor's control
    from api.routers.blog import _ts
    due = [p for p in posts if is_live(p) and p.get("slug") not in exported
           and (_ts(p.get("publishedAt")) or dt.datetime.min.replace(tzinfo=dt.timezone.utc))
           > (_ts(p.get("updatedAt")) or dt.datetime.max.replace(tzinfo=dt.timezone.utc))]
    if due:
        _quietly(publish_now)()
    elif os.path.exists(PENDING):  # a save's publication that a restart interrupted; debounced, as rapid restarts happen
        publish_soon()
    schedule(posts)


def main() -> None:
    from api.routers import blog
    out = export(blog._all(), dt.datetime.now(dt.timezone.utc).isoformat(), force="--force" in sys.argv)
    if "--push" in sys.argv and not out.get("blocked"):
        out.update(push())
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
