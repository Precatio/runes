"""Rättelse av den publicerade artikeln "Färderna var de ungas" (hW6pf7jhfVSQa9D7rnIu): "ungefär fyra gånger" blir
"tre till fyra gånger" (oddskvot och andel blandades ihop; råa andelar 10,4 % mot 2,7 % = 3,8, modellens 10 mot 3 % =
3,3), och robusthetstrappan läggs till i "Så säkra är vi". Skriver bara text och sammanfattning (sv + en) ur
utdata/blogg/unga.json (build_unga.py), behåller publiceringsdatum, och publicerar webbplatsen.
    .venv/bin/python utdata/blogg/build/patch_unga_live.py"""
import datetime as dt
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from api.routers import blog  # noqa: E402
from src import site_export  # noqa: E402

new = json.load(open(os.path.join(ROOT, "utdata", "blogg", "unga.json"), encoding="utf-8"))
ref = blog.firestore().collection(blog.COLLECTION).document("hW6pf7jhfVSQa9D7rnIu")
old = ref.get().to_dict()
assert old and old["slug"] == new["slug"] == "fardena-var-de-ungas" and old.get("published")
blog._backup(ref.id, old)
ref.set({k: new[k] for k in ("summary", "body", "summary_en", "body_en")} | {"updatedAt": dt.datetime.now(dt.timezone.utc)},
        merge=True)
blog._forget()
print("artikeln uppdaterad; publiceringsdatum oförändrat:", old.get("publishedAt"))
print(site_export.publish_now())
