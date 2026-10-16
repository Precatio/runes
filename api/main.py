import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import DEFAULT_EXCLUDED_CONTENT_TYPES, GZipMiddleware
from api.cache import ContentLengthHeader
from api.routers import admin, blog, chat, threed, twod, raa, synthesis, phonetics, rundata, stats, orthography, research, reports, rstats, limitations, docs, textmodel

app = FastAPI(title="Vitki API")


@app.on_event("startup")
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
        except Exception as e:  # Firestore unreachable: the next save plans it
            from api.errors import logger
            logger.warning("Webbplatsens schemaläggning: %r", e)
    threading.Thread(target=site, daemon=True).start()

# Configure CORS for Next.js frontend (comma-separated list in CORS_ORIGINS)
CORS_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",") if o.strip()]

# The last added middleware is the outermost: CORS → gzip → the uncompressed size → the app. JSON compresses to about a
# tenth; images, zip archives and Word files are already compressed and are sent as they are.
app.add_middleware(ContentLengthHeader)
app.add_middleware(GZipMiddleware, minimum_size=1024, compresslevel=5, exclude_content_types=(
    *DEFAULT_EXCLUDED_CONTENT_TYPES, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"))
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Content-Length", "Content-Encoding"],
)

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
app.include_router(admin.router, prefix="/api", tags=["admin"])
app.include_router(blog.router, prefix="/api", tags=["blog"])

@app.get("/")
def read_root():
    return {"message": "Vitki API is running"}
