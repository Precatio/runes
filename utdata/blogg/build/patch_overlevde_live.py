"""Rättelse av den publicerade artikeln "Tor föll, hjälten blev dräng" (OpPovVTSrBDtS3OqP9KL), 2026-10-30: namnregeln
-i → -e för mansnamn (Helgi → Helge, Rúni → Rune, Kári → Kåre) ger 85 levande namn i stället för 82. Skriver bara text
och sammanfattning (sv + en) ur utdata/blogg/overlevde.json (build_overlevde.py), behåller publiceringsdatum, och
publicerar webbplatsen.
    .venv/bin/python utdata/blogg/build/patch_overlevde_live.py"""
import datetime as dt
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from api.routers import blog  # noqa: E402
from src import site_export  # noqa: E402

new = json.load(open(os.path.join(ROOT, "utdata", "blogg", "overlevde.json"), encoding="utf-8"))
ref = blog.firestore().collection(blog.COLLECTION).document("OpPovVTSrBDtS3OqP9KL")
old = ref.get().to_dict()
assert old and old["slug"] == new["slug"] == "tor-foll-hjalten-blev-drang" and old.get("published")
blog._backup(ref.id, old)
ref.set({k: new[k] for k in ("summary", "body", "summary_en", "body_en")} | {"updatedAt": dt.datetime.now(dt.timezone.utc)},
        merge=True)
blog._forget()
print("artikeln uppdaterad; publiceringsdatum oförändrat:", old.get("publishedAt"))
print(site_export.publish_now())
