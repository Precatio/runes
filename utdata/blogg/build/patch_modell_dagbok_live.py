"""Patch av den publicerade artikeln "Hur bra är vår modell egentligen?" (q4oZASaFEZtHMyKGQtBe): text och sammanfattning
(sv + en) ur utdata/blogg/modell_dagbok.json (build_modell_dagbok.py), publiceringsdatum orört, webbplatsen publiceras.
    .venv/bin/python utdata/blogg/build/patch_modell_dagbok_live.py"""
import datetime as dt
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from api.routers import blog  # noqa: E402
from src import site_export  # noqa: E402

new = json.load(open(os.path.join(ROOT, "utdata", "blogg", "modell_dagbok.json"), encoding="utf-8"))
ref = blog.firestore().collection(blog.COLLECTION).document("q4oZASaFEZtHMyKGQtBe")
old = ref.get().to_dict()
assert old and old["slug"] == new["slug"] == "hur-bra-ar-var-modell-egentligen" and old.get("published")
blog._backup(ref.id, old)
ref.set({k: new[k] for k in ("title", "summary", "body", "title_en", "summary_en", "body_en")} | {"updatedAt": dt.datetime.now(dt.timezone.utc)},
        merge=True)
blog._forget()
print("artikeln uppdaterad; publiceringsdatum oförändrat:", old.get("publishedAt"))
print(site_export.publish_now())
