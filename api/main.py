import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import chat, threed, twod, raa, synthesis, phonetics, rundata, stats, orthography

app = FastAPI(title="Runforskning API")

# Configure CORS for Next.js frontend (comma-separated list in CORS_ORIGINS)
CORS_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

@app.get("/")
def read_root():
    return {"message": "Runforskning API is running"}
