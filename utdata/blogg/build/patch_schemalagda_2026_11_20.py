"""Förbehållet om familjegrupperna (2026-11-20, Viktors beslut "Ny version med förbehåll"; planen
analysplaner/2026-11-19-sjalvkontroll-tillagg-grupper.md, c1e3d2ab…):

1. Artikeln "Runstenarna stod vid lerans kant – men halva gåtan är olöst" (V4a68EesKrJqKGlGqP2I) är schemalagd
   (publicerad=True, publiceringstid i framtiden). Text och sammanfattning skrivs ur build_palm_jordar.py:s json, med
   säkerhetskopia; publiceringstiden behålls. Som patch_schemalagda_2026_11_19.py.
2. Rapporten "Runstenarna samlas i familjegrupper …" (G7k7V4x6soJZ8eTHtHcy) får en söktitel som inte säger mer än
   rapportversion 5 (titel, sammanfattning och text skrivs av patch_rapporter_live.py), med säkerhetskopia.

Webbplatsen publiceras inte härifrån; patch_rapporter_live.py publicerar den en gång efteråt.
    .venv/bin/python utdata/blogg/build/patch_schemalagda_2026_11_20.py"""
import datetime as dt
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from api.routers import blog  # noqa: E402

col = blog.firestore().collection(blog.COLLECTION)
now = dt.datetime.now(dt.timezone.utc)

# 1. the scheduled clay article
DOC = "V4a68EesKrJqKGlGqP2I"
new = json.load(open(os.path.join(ROOT, "utdata", "blogg", "palm_jordar.json"), encoding="utf-8"))
ref = col.document(DOC)
old = ref.get().to_dict()
assert old and old.get("published") and old["slug"] == new["slug"] == "runstenarna-foljde-leran", DOC
assert blog._ts(old["publishedAt"]) > now, f"{DOC} är redan live – patcha inte härifrån"
assert old["title"] == new["title"] and old["title_en"] == new["title_en"]
blog._backup(DOC, old)
ref.set({k: new[k] for k in ("summary", "body", "summary_en", "body_en")} | {"updatedAt": now}, merge=True)
print("uppdaterad", DOC, old["slug"], str(old["publishedAt"])[:10])

# 2. the search titles of the family-groups report
FAM = "G7k7V4x6soJZ8eTHtHcy"
SEO = {"seo_title": "Runstenar i familjegrupper – namn och gravfält", "seo_title_en": "Runestones in family groups: names and grave fields"}
assert all(len(v) <= 52 for v in SEO.values())
ref = col.document(FAM)
old = ref.get().to_dict()
assert old and old.get("published") and old["slug"] == "familjegrupper-vid-gravfalten"
assert old.get("seo_title") == "Runstenar i familjegrupper vid gravfälten"
blog._backup(FAM, old)
ref.set(SEO | {"updatedAt": now}, merge=True)
print("söktitlar", FAM, SEO)
blog._forget()
