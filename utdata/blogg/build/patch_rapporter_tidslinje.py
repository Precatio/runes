"""Tidslinje och formmening i de publicerade forskningsrapporterna (mallen version 3, 2026-10-31; Viktor: "lägg in alla
datumen"). Skriver bara body och body_en ur byggarnas json (utdata/rapporter/rapport_*.json), efter kontroll att allt
utom rubrikraden är oförändrat mot texten som ligger ute; behåller publiceringsdatum, etiketter och övriga fält, sparar
en säkerhetskopia och publicerar webbplatsen.
    .venv/bin/python utdata/blogg/build/patch_rapporter_tidslinje.py"""
import datetime as dt
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from api.routers import blog  # noqa: E402
from src import site_export  # noqa: E402

DOCS = {"cceot7s6OvLQ8AuQ0TSZ": "rapport1_kvinnor.json", "TyFNK0gkwZ6iu8hAfR7i": "rapport_r_for_R.json",
        "ioGAYDIKNNiLctQYtvxa": "rapport_unga.json", "G7k7V4x6soJZ8eTHtHcy": "rapport_familjens_plats.json",
        "sVxpHokkL0cJkADJPN1q": "rapport_monoftong.json"}
col = blog.firestore().collection(blog.COLLECTION)
now = dt.datetime.now(dt.timezone.utc)
for doc, fn in DOCS.items():
    new = json.load(open(os.path.join(ROOT, "utdata", "rapporter", fn), encoding="utf-8"))
    ref = col.document(doc)
    old = ref.get().to_dict()
    assert old and old.get("published") and old["slug"] == new["slug"], doc
    for k in ("body", "body_en"):
        o, n = old[k].split("\n"), new[k].split("\n")
        assert o[1:] == n[1:], (doc, k, "mer än rubrikraden skiljer")
        assert "Tidslinje: " in n[0] or "Timeline: " in n[0], (doc, k)
    blog._backup(ref.id, old)
    ref.set({"body": new["body"], "body_en": new["body_en"], "updatedAt": now}, merge=True)
    print("uppdaterad:", new["slug"], "| publicerad", old.get("publishedAt"))
blog._forget()
print(site_export.publish_now())
