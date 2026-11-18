"""Uppdatering av den publicerade artikeln "Kullarna vid skogens rand" (YAhSiMGzlXvPC9ZW31hD), 2026-11-18, på Viktors
begäran ("behöver kapas lite och få ytterligare en koll av hur den flyter"): kortad text, runstenssiffrorna bara stenar på
sin plats (trappan 53f11fa6), exempel som står där de restes, uppdateringsnotis. Skriver text och sammanfattning (sv + en)
ur utdata/blogg/hogar.json (build_hogar.py), behåller publiceringsdatum och publicerar webbplatsen.
    .venv/bin/python utdata/blogg/build/patch_hogar_live.py"""
import datetime as dt
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from api.routers import blog  # noqa: E402
from src import site_export  # noqa: E402

new = json.load(open(os.path.join(ROOT, "utdata", "blogg", "hogar.json"), encoding="utf-8"))
ref = blog.firestore().collection(blog.COLLECTION).document("YAhSiMGzlXvPC9ZW31hD")
old = ref.get().to_dict()
assert old and old["slug"] == "kullarna-vid-skogens-rand" and old.get("published")
assert "Rättad 18 november 2026" in new["body"] and "Corrected 18 November 2026" in new["body_en"]
assert "sökte sig till de stora högarna" not in new["body"].split("*Rättad")[0]
blog._backup(ref.id, old)
ref.set({k: new[k] for k in ("summary", "body", "summary_en", "body_en", "seo_title")} | {"updatedAt": dt.datetime.now(dt.timezone.utc)},
        merge=True)
blog._forget()
print("artikeln uppdaterad; publiceringsdatum oförändrat:", old.get("publishedAt"))
print(site_export.publish_now())
