import logging
import os
import shutil
import tempfile
import time
from contextlib import asynccontextmanager

# Temporary files – uploaded 3D files of up to a few GB, R's working files – go to the project's own disk instead of the
# system disk: data/cache/tmp, or VITKI_TMPDIR. Set before the routers are imported, and passed on to R and other
# programs the engine starts (TMPDIR).
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP = os.environ.get("VITKI_TMPDIR") or os.path.join(ROOT, "data", "cache", "tmp")
os.makedirs(TMP, exist_ok=True)
os.environ["TMPDIR"] = TMP
tempfile.tempdir = TMP
# The text model keeps only the two latest fold models in the API (about 400 MB each; scripts keep all five), set
# before src.textmodel is imported with the routers
os.environ.setdefault("TEXTMODEL_BUNDLES", "2")


def clean_tmp(max_age_s: float = 86400) -> None:
    """Removes what a crashed job left in TMP more than a day ago."""
    for name in os.listdir(TMP):
        path = os.path.join(TMP, name)
        try:
            if time.time() - os.path.getmtime(path) > max_age_s:
                shutil.rmtree(path) if os.path.isdir(path) else os.unlink(path)
        except OSError:
            pass


clean_tmp()


def _log_to_stderr() -> None:
    """The app's own messages (publishing to the website, IndexNow, Statistik i R, sign-in) at INFO and above on stderr,
    timestamped, next to uvicorn's: without a handler only warnings got through, so api.log never showed a publish."""
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s", "%Y-%m-%d %H:%M:%S"))
    for name in ("runforskning", "vitki"):
        log = logging.getLogger(name)
        if not log.handlers:
            log.addHandler(handler)
            log.setLevel(logging.INFO)
            log.propagate = False


_log_to_stderr()

from fastapi import FastAPI  # noqa: E402 - after the temporary folder is set
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from starlette.middleware.gzip import DEFAULT_EXCLUDED_CONTENT_TYPES, GZipMiddleware  # noqa: E402
from starlette.middleware.trustedhost import TrustedHostMiddleware  # noqa: E402
from starlette.responses import PlainTextResponse  # noqa: E402
from api.cache import ContentLengthHeader  # noqa: E402
from api.routers import admin, blog, chat, threed, twod, raa, synthesis, phonetics, rundata, stats, orthography, research, reports, rstats, limitations, docs, textmodel, runmodell  # noqa: E402

def _warm_caches():
    """Värmer de långsamma svaren i bakgrunden när servern startar: R-kontrollen, R-korpusens version,
    stenöversikten och fyndens tolkningsnivåer. Svaren sparas också på disk, så en omstart läser dem i stället för att räkna om."""
    import threading

    def warm():
        try:
            from api.routers import research, rstats
            from src import r_bridge
            r_bridge.status()
            rstats.fingerprint()
            research._overview(research._fp())
            research._hypotheses()
            research._open_questions()
            research._orthographic_findings()
            # The large answers as ready JSON (api/cache.py), so that the first visitor does not wait for them; the
            # findings also fill the interpretation levels' disk cache
            from api.cache import json_bytes
            req = research.FindingsRequest()
            json_bytes(research.findings_key(req), lambda: research.research_findings(req))
            from api.routers import rundata
            json_bytes(rundata.geo_key(), rundata._geo)
            json_bytes(research.pattern_map_key(), research._pattern_map)
            fp = research._fp()
            json_bytes(research.overview_key(fp), lambda: research._overview(fp))
        except Exception as e:  # warming is an optimisation; requests compute what they need
            from api.errors import logger
            logger.warning("Uppvärmningen av cachen misslyckades: %r", e)
    if os.environ.get("WARM_CACHES", "1") != "0":
        threading.Thread(target=warm, daemon=True).start()

    # Statistik i R: when the data or the analysis code have changed (a new Rundata, a corrected feature), the corpus
    # analyses are computed on their own – after a quiet spell, so that a series of code edits (each restarting the
    # server) does not start a run for every edit. R_AUTORUN=0 turns it off; R_AUTORUN_DELAY is the quiet spell in s.
    def r_autorun():
        import time
        time.sleep(float(os.environ.get("R_AUTORUN_DELAY", "600")))
        try:
            from api.routers import rstats
            if rstats.autorun():
                from api.errors import logger
                logger.info("Statistik i R: ny version av data, korpusanalyserna räknas om (%s)", rstats.fingerprint())
        except Exception as e:
            from api.errors import logger
            logger.warning("Statistik i R: den automatiska körningen kunde inte starta: %r", e)
    if os.environ.get("R_AUTORUN", "1") not in ("0", "false"):
        threading.Thread(target=r_autorun, daemon=True).start()

    # The public website: publish an article whose scheduled time came while the app was off, and plan the next one
    def site():
        try:
            from api.routers import blog
            from src import site_export
            site_export.check_git()
            site_export.catch_up(blog._all())
            site_export.start_view_refresh()
        except Exception as e:  # Firestore unreachable: the next save plans it
            from api.errors import logger
            logger.warning("Webbplatsens schemaläggning: %r", e)
    threading.Thread(target=site, daemon=True).start()

    # The R cache (src/r_cache.py): older corpus versions beyond the newest few, untouched for two weeks, are removed –
    # at most once a day, after the warm-up has computed the current version; never the current results. Not while
    # data/cache/r/prune.json says "hold": true (`python -m src.r_cache --release` lifts it)
    def r_cache_prune():
        import time
        try:
            from src import r_bridge, r_cache
            if not r_bridge.enabled() or not r_cache.due():
                return
            time.sleep(float(os.environ.get("R_CACHE_PRUNE_DELAY", "120")))
            from api.routers import rstats
            out = r_cache.prune_daily(rstats.fingerprint())
            if out and out.get("removed"):
                from api.errors import logger
                logger.info("R-cachen: %d äldre korpusversioner togs bort (%.0f MB)", out["removed"], out["bytes"] / 1e6)
        except Exception as e:  # housekeeping; the next start tries again
            from api.errors import logger
            logger.warning("Städningen av R-cachen misslyckades: %r", e)
    if os.environ.get("R_CACHE_PRUNE", "1") not in ("0", "false"):
        threading.Thread(target=r_cache_prune, daemon=True).start()


@asynccontextmanager
async def _lifespan(_app):
    """At startup: the background work in _warm_caches (a lifespan handler replaces the deprecated on_event)."""
    _warm_caches()
    yield


app = FastAPI(title="Vitki API", lifespan=_lifespan)

# Configure CORS for Next.js frontend (comma-separated list in CORS_ORIGINS)
CORS_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
                if o.strip()]
# The names the engine answers to (comma-separated in ALLOWED_HOSTS). Any other Host header is refused, so that a web page
# whose own name has been pointed at 127.0.0.1 (DNS rebinding) cannot read the engine as its own site. "testserver" is
# the name FastAPI's TestClient uses in the tests.
ALLOWED_HOSTS = [h.strip() for h in os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1,[::1],testserver").split(",")
                 if h.strip()]


class SameSiteWrites:
    """Refuses (403) a request that changes something – anything but GET, HEAD and OPTIONS – sent by a page on another
    site: its Origin is not one of CORS_ORIGINS, or the browser marks it cross-site. A form or a body-less POST from a
    foreign page needs no preflight, so CORS alone does not stop it from starting R runs or 500 MB uploads. Requests
    without these headers (the Next server, scripts, the tests) are let through, and so are the engine's API pages
    (FastAPI's /docs and /redoc, "Try it out"): an Origin that is the request's own scheme://host:port, for one of the
    allowed host names, not marked cross-site, and a Referer on one of those pages.

    Only the API pages get this exception, not every page the engine serves from its own origin (the R html_map
    figures under /api/r/figure/, say). The trade-off that remains: Swagger UI loads its script from cdn.jsdelivr.net,
    so a compromised copy of that script could write while /docs is open. A browser that sends no Referer
    (Referrer-Policy: no-referrer) cannot use "Try it out"; curl and scripts are unaffected."""

    SAFE = {"GET", "HEAD", "OPTIONS"}
    DOC_PAGES = ("/docs", "/redoc")

    def __init__(self, app, origins, hosts=()):
        self.app = app
        self.origins = set(origins)
        self.hosts = {h.lower() for h in hosts}

    def _own(self, scope, headers: dict) -> str | None:
        """The engine's own origin for this request (scheme://Host), when Host is one of the allowed names."""
        host = headers.get(b"host", b"").decode("latin-1").strip().lower()
        name = host[:host.index("]") + 1] if host.startswith("[") and "]" in host else host.split(":")[0]
        if not name or not ("*" in self.hosts or name in self.hosts):
            return None
        return f"{scope.get('scheme', 'http')}://{host}"

    def _from_doc_page(self, headers: dict, own: str) -> bool:
        """Was the request sent from one of the engine's API pages (DOC_PAGES), going by the Referer?"""
        ref = headers.get(b"referer", b"").decode("latin-1")
        if not ref.lower().startswith(own + "/"):
            return False
        path = ref[len(own):].split("?", 1)[0].split("#", 1)[0]
        return any(path == p or path.startswith(p + "/") for p in self.DOC_PAGES)

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope["method"] not in self.SAFE:
            headers = {k.lower(): v for k, v in scope.get("headers", [])}
            origin = headers.get(b"origin", b"").decode("latin-1")
            site = headers.get(b"sec-fetch-site", b"").decode("latin-1")
            if origin:
                own = self._own(scope, headers)
                ok = origin in self.origins or (site != "cross-site" and own is not None and origin.lower() == own
                                                and self._from_doc_page(headers, own))
            else:
                ok = site != "cross-site"
            if not ok:
                await PlainTextResponse("Cross-site request refused", status_code=403)(scope, receive, send)
                return
        await self.app(scope, receive, send)


# The last added middleware is the outermost: host check → CORS → same-site writes → gzip → the uncompressed size → the
# app. JSON compresses to about a tenth; images, zip archives, Word files and 3D view models (binary STL, which gzip
# barely shrinks at seconds of CPU on a 75 MB model) are sent as they are.
app.add_middleware(ContentLengthHeader)
app.add_middleware(GZipMiddleware, minimum_size=1024, compresslevel=5, exclude_content_types=(
    *DEFAULT_EXCLUDED_CONTENT_TYPES, "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "model/stl"))
app.add_middleware(SameSiteWrites, origins=CORS_ORIGINS, hosts=ALLOWED_HOSTS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Content-Length", "Content-Encoding"],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)

app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(threed.router, prefix="/api/3d", tags=["3d"])
app.include_router(twod.router, prefix="/api/2d", tags=["2d"])
app.include_router(raa.router, prefix="/api/raa", tags=["raa"])
app.include_router(synthesis.router, prefix="/api/synthesis", tags=["synthesis"])
app.include_router(phonetics.router, prefix="/api/phonetics", tags=["phonetics"])
app.include_router(rundata.router, prefix="/api/rundata", tags=["rundata"])
app.include_router(stats.router, prefix="/api/stats", tags=["stats"])
app.include_router(orthography.router, prefix="/api/orthography", tags=["orthography"])
app.include_router(research.router, prefix="/api/research", tags=["research"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
app.include_router(limitations.router, prefix="/api/limitations", tags=["limitations"])
app.include_router(docs.router, prefix="/api/docs", tags=["docs"])
app.include_router(rstats.router, prefix="/api/r", tags=["r"])
app.include_router(textmodel.router, prefix="/api/textmodel", tags=["textmodel"])
app.include_router(runmodell.router, prefix="/api/runmodell", tags=["runmodell"])
app.include_router(admin.router, prefix="/api", tags=["admin"])
app.include_router(blog.router, prefix="/api", tags=["blog"])

@app.get("/")
def read_root():
    return {"message": "Vitki API is running"}
