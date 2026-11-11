"""Webbplatsens export i GitHub Actions (.github/workflows/publicera.yml): samma export som den lokala appen gör
(src/site_export.py, med samma kontroller), men utan Viktors dator. Körs var 30:e minut, så att schemalagda artiklar
och ändringar från /redaktion når vitkirunor.se också när appen är avstängd.

Skillnader mot den lokala exporten, och varför:
* Figurerna: i CI finns bara de WebP-filer som redan ligger i web/public/figurer (de räknas som befintliga). En artikel
  med en ny R-figur blockeras av kontrollen ("Figurer saknas") tills den lokala appen har exporterat figuren.
* Sidvisningarna ("mest lästa") läses bara en gång om dygnet (VIEWS_HOUR, svensk tid), och skrivs bara när ordningen
  har ändrats märkbart (site_export.views_moved) – annars behålls förra exportens antal. Samlingen site_views är stor,
  och att läsa den var 30:e minut skulle kosta läsningar och ge en commit för varje ny visning.
* Commons-bildernas bredd (src/commons.py, som lokalt cachas i data/cache): för bilder som förra exporten redan hade
  används förra exportens val (960 px-tumnagel eller originalet), och bara nya bilder slås upp på Commons. Annars skulle
  en körning då Commons inte svarar ge tyngre bildadresser och en onödig commit.
* exported_at: ändras ingenting annat än tidsstämpeln behålls den gamla filen, så att en körning utan nyheter inte ger
  någon commit.

Utan behörighet (GOOGLE_APPLICATION_CREDENTIALS pekar inte på en fil) skrivs en kort notis och skriptet avslutas med 0,
så att arbetsflödet är ofarligt innan hemligheten FIREBASE_SERVICE_ACCOUNT finns.

    python scripts/ci_publicera.py [--force]

Skriver changed=true|false till $GITHUB_OUTPUT (om den finns) och en commit-text till
$RUNNER_TEMP/publicera-commit.txt. Avslutas med 1 när kontrollen stoppar exporten eller Firestore inte kan läsas.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
import tempfile
from zoneinfo import ZoneInfo

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

STOCKHOLM = ZoneInfo("Europe/Stockholm")
# The hour (Swedish time) when the views are read; the cron runs at :07 and :37, and only the first run of the hour reads
VIEWS_HOUR = 5


def credentials_present() -> bool:
    path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
    return bool(path) and os.path.isfile(path) and os.path.getsize(path) > 0


def views_due(now: dt.datetime) -> bool:
    """Is this the day's run that reads the page views? The first run in VIEWS_HOUR, Swedish time."""
    local = now.astimezone(STOCKHOLM)
    return local.hour == VIEWS_HOUR and local.minute < 30


def _read(path: str) -> bytes | None:
    try:
        with open(path, "rb") as fh:
            return fh.read()
    except OSError:
        return None


def _posts(raw: bytes | None) -> list[dict]:
    try:
        return json.loads(raw or b"{}").get("posts", [])
    except ValueError:
        return []


def changes(old: list[dict], new: list[dict]) -> dict[str, list[str]]:
    """Which articles came, went or changed between two exports (by slug)."""
    a, b = {p.get("slug"): p for p in old}, {p.get("slug"): p for p in new}
    return {"nya": sorted(s for s in b if s not in a), "borttagna": sorted(s for s in a if s not in b),
            "ändrade": sorted(s for s in b if s in a and a[s] != b[s])}


def keep_timestamp_if_unchanged(path: str, before: bytes | None) -> bool:
    """When the export changed nothing but exported_at, the earlier file is put back (no commit for a run without
    news). Returns whether the articles changed."""
    after = _read(path)
    if before is None or after is None:
        return after != before
    if _posts(before) == _posts(after):
        with open(path, "wb") as fh:
            fh.write(before)
        return False
    return True


_THUMB_960 = re.compile(r"https://upload\.wikimedia\.org/wikipedia/commons/thumb/[0-9a-f]/[0-9a-f]{2}/([^/?#)\s]+)/(\d+)px-\1")
_ORIGINAL = re.compile(r"https://upload\.wikimedia\.org/wikipedia/commons/[0-9a-f]/[0-9a-f]{2}/([^/?#)\s]+\.(?:jpe?g|png|webp))(?=[)\s])", re.I)


def known_photo_sizes(old_posts: list[dict], commons) -> dict[str, dict]:
    """What the previous export decided for each Commons original, as sizes that make commons.site_photo decide the
    same again: a file shown as a thumbnail of the site width was wide and heavy; an original kept as it is was not."""
    from urllib.parse import unquote
    out: dict[str, dict] = {}
    for p in old_posts:
        for f in ("body", "body_en"):
            text = p.get(f) or ""
            for m in _ORIGINAL.finditer(text):
                out.setdefault(unquote(m.group(1)), {"width": 0, "size": 0})
            for m in _THUMB_960.finditer(text):
                if int(m.group(2)) == commons.SITE_WIDTH:
                    out[unquote(m.group(1))] = {"width": commons.SITE_WIDTH + 1, "size": commons.LIGHT + 1}
    return out


def seed_photo_sizes(old_posts: list[dict]) -> None:
    """Commons is asked only about photos the previous export did not have (see the module text)."""
    from src import commons
    known = known_photo_sizes(old_posts, commons)
    lookup = commons.original_sizes

    def sizes(files: list[str], timeout: float = 10) -> dict[str, dict]:
        out = {f: known[f] for f in files if f in known}
        rest = [f for f in files if f not in known]
        return {**out, **(lookup(rest, timeout) if rest else {})}
    commons.original_sizes = sizes


def choose_views(se, now: dt.datetime, old_posts: list[dict]):
    """The views the export should use: the fresh counts once a day when the order of "mest lästa" has moved
    noticeably, otherwise the previous export's counts (and Firestore's site_views is not read at all)."""
    if views_due(now):
        fresh = se.article_views()
        if fresh is not None:
            moved = se.views_moved(old_posts, [{**p, "views": int(fresh.get(p["slug"], 0))} for p in old_posts])
            if moved:
                print("Sidvisningarna: ordningen har ändrats, de nya antalen skrivs.")
                return fresh
            print("Sidvisningarna: ingen märkbar ändring, förra antalen behålls.")
    return se.previous_views()


def _output(**kw: str) -> None:
    path = os.environ.get("GITHUB_OUTPUT")
    if not path:
        return
    with open(path, "a", encoding="utf-8") as fh:
        for k, v in kw.items():
            fh.write(f"{k}={v}\n")


def _summary(text: str) -> None:
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(text + "\n")


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    force = "--force" in argv
    if not credentials_present():
        print("::notice::Webbplatsens CI-export är inte aktiverad: hemligheten FIREBASE_SERVICE_ACCOUNT saknas "
              "(se ADMIN_PA_WEBBEN.md). Inget gjordes.")
        _output(changed="false")
        return 0
    os.environ.setdefault("FIREBASE_PROJECT_ID", "runes-1656b")
    os.environ.setdefault("SITE_PUBLISH", "0")  # nothing in the imported modules may start the local app's timers
    from api.routers import blog
    from src import site_export as se

    before = _read(se.CONTENT)
    old_posts = _posts(before)
    try:
        posts = blog._all()
    except Exception as e:  # noqa: BLE001 - reported plainly; the run fails so the founder sees it
        print(f"::error::Artiklarna kunde inte läsas ur Firestore: {getattr(e, 'detail', None) or type(e).__name__}")
        _output(changed="false")
        return 1
    now = dt.datetime.now(dt.timezone.utc)
    views = choose_views(se, now, old_posts)
    se.article_views = lambda: views  # export() reads the views through this function
    seed_photo_sizes(old_posts)
    out = se.export(posts, now.isoformat(), force=force)
    if out.get("blocked"):
        print(f"::error::Exporten stoppades av kontrollen: {out['blocked']}")
        _summary(f"### Webbplatsen publicerades inte\n\n{out['blocked']}\n\nNya figurer kommer från den lokala appen; "
                 "en avsiktlig borttagning av många artiklar: kör arbetsflödet för hand med force.")
        _output(changed="false")
        return 1
    changed = keep_timestamp_if_unchanged(se.CONTENT, before)
    diff = changes(old_posts, _posts(_read(se.CONTENT)))
    lines = [f"{k}: {', '.join(v)}" for k, v in diff.items() if v]
    print(json.dumps({**out, "articles_changed": changed, **diff}, ensure_ascii=False))
    message = "Webbplatsen: artiklarna uppdaterade (GitHub Actions)" + ("\n\n" + "\n".join(lines) if lines else "")
    with open(os.path.join(os.environ.get("RUNNER_TEMP") or tempfile.gettempdir(), "publicera-commit.txt"), "w", encoding="utf-8") as fh:
        fh.write(message + "\n")
    _summary("### Webbplatsens export\n\n" + (("\n".join(f"- {line}" for line in lines)) if lines else "Inga ändrade artiklar."))
    _output(changed="true" if changed else "false")
    return 0


if __name__ == "__main__":
    sys.exit(main())
