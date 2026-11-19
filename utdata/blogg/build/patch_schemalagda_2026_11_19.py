"""Rättelser i schemalagda (ännu inte live) artiklar efter den automatiska granskningen 2026-11-19 (src/article_lint.py):
sidor i Futhark-citaten (Hundra år II), död länk (Attundaland), pronomen om ristare (Läs om du kan, Perioder, Döda i vita
kläder, Hundra år II), den engelska korthetsrutans rubrik (Jul, Vem höll i mejseln?). Skriver text och sammanfattning ur
byggarnas json, behåller publiceringstiden, med säkerhetskopia.
    .venv/bin/python utdata/blogg/build/patch_schemalagda_2026_11_19.py"""
import datetime as dt
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from api.routers import blog  # noqa: E402
from src import article_lint  # noqa: E402

DOCS = {"fN835GYBvYc3a7ckpvnF": "hundra_ar_2.json", "k176HOYcqRbSNTkIwJIk": "hundra_ar_1.json",
        "zaaTGjAWLaZz7jBamwKm": "attundaland.json", "3DWc4WX5usii0K4zB0Oh": "lasa_runstenar.json",
        "2hcHpU4w5Tqh4DDTYgVb": "jul.json", "3u9KY1cKaK8mzZyNwCwK": "ristarna.json",
        "WNIyUpl9tj2kcaXoytdp": "perioder.json", "pcm3u3oFyziU2vzixpYR": "vita_klader.json"}
col = blog.firestore().collection(blog.COLLECTION)
now = dt.datetime.now(dt.timezone.utc)
for doc, f in DOCS.items():
    new = json.load(open(os.path.join(ROOT, "utdata", "blogg", f), encoding="utf-8"))
    ref = col.document(doc)
    old = ref.get().to_dict()
    assert old and old.get("published") and old["slug"] == new["slug"], doc
    assert blog._ts(old["publishedAt"]) > now, f"{doc} är redan live – patcha inte härifrån"
    blog._backup(doc, old)
    ref.set({k: new[k] for k in ("summary", "body", "summary_en", "body_en") if k in new} | {"updatedAt": now}, merge=True)
    print("uppdaterad", doc, old["slug"], str(old["publishedAt"])[:10])
blog._forget()
