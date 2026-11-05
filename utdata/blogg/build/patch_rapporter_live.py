"""För in rättade versioner av publicerade forskningsrapporter (2026-11-05, granskningen inför Zenodo): läser
utdata/rapporter/<fil>.json som byggarna skrev, skriver titel, sammanfattning och text (sv + en) till det publicerade
dokumentet med samma adress, behåller publiceringsdatumet, säkerhetskopierar det gamla (blog._backup) och publicerar
webbplatsen en gång till sist. Bara publicerade rapporter och bara när den nya texten har en högre rapportversion.
    .venv/bin/python utdata/blogg/build/patch_rapporter_live.py rapport_strand.json rapport_riktning.json …  [--torr]"""
import datetime as dt
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from api.routers import blog  # noqa: E402
from src import site_export  # noqa: E402

FIELDS = ("title", "summary", "body", "title_en", "summary_en", "body_en")
version = lambda body: int(re.search(r"Rapportversion (\d+)", body).group(1))  # noqa: E731

files = [a for a in sys.argv[1:] if not a.startswith("--")]
dry = "--torr" in sys.argv
live = {p["slug"]: p for p in blog._all() if "Rapport" in (p.get("labels") or [])}
done = []
for f in files:
    new = json.load(open(os.path.join(ROOT, "utdata", "rapporter", f), encoding="utf-8"))
    old = live[new["slug"]]
    assert old.get("published"), f"{new['slug']} är inte publicerad – utkast skrivs med byggarens --update"
    vo, vn = version(old["body"]), version(new["body"])
    assert vn > vo, f"{new['slug']}: rapportversion {vn} är inte högre än den publicerade {vo}"
    assert "## Ändringslogg" in new["body"] and "## Change log" in new["body_en"], f"{new['slug']} saknar ändringslogg"
    print(f"{new['slug']}: v{vo} → v{vn}{' (torrkörning)' if dry else ''}")
    if dry:
        continue
    ref = blog.firestore().collection(blog.COLLECTION).document(old["id"])
    blog._backup(ref.id, ref.get().to_dict())
    ref.set({k: new[k] for k in FIELDS} | {"updatedAt": dt.datetime.now(dt.timezone.utc)}, merge=True)
    done.append(new["slug"])
blog._forget()
if done:
    print(site_export.publish_now())
