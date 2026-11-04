"""Uppdatering av den publicerade artikeln "De gamla landen: Sotholm" (04xMEvIJCiBPLwEDzFwB, slug oförändrad).
2026-11-02: kartan över Tören omkring år 1000 (utdata/sotholm/karta_toren.R) inlagd efter avsnittet om de två bygderna.
2026-11-04: omskriven i seriens atmosfäriska form (Viktor) under rubriken "De gamla landen: Sotholm – det yttre landet på
ön Tören": gläntorna, borgarna, tinget och stenarna vid vägen; bönen som saknas står kvar som ett inslag.
Skriver text och sammanfattning (sv + en) ur utdata/blogg/sotholm.json (build_sotholm.py), behåller publiceringsdatum
och publicerar webbplatsen.
    .venv/bin/python utdata/blogg/build/patch_sotholm_live.py"""
import datetime as dt
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from api.routers import blog  # noqa: E402
from src import site_export  # noqa: E402

new = json.load(open(os.path.join(ROOT, "utdata", "blogg", "sotholm.json"), encoding="utf-8"))
ref = blog.firestore().collection(blog.COLLECTION).document("04xMEvIJCiBPLwEDzFwB")
old = ref.get().to_dict()
assert old and old.get("published") and old["slug"] == new["slug"] == "de-gamla-landen-sotholm"
assert new["title"] == "De gamla landen: Sotholm – det yttre landet på ön Tören" and "## Gläntorna" in new["body"]
assert "Tören omkring år 1000, då Södertörn var en ö" in new["body"] and "## Så vet vi det" in new["body"] and "## How we know" in new["body_en"] and ":::box" not in new["body"]
blog._backup(ref.id, old)
ref.set({k: new[k] for k in ("title", "summary", "body", "title_en", "summary_en", "body_en")}
        | {"updatedAt": dt.datetime.now(dt.timezone.utc)}, merge=True)
blog._forget()
print("artikeln uppdaterad; publiceringsdatum oförändrat:", old.get("publishedAt"))
print(site_export.publish_now())
