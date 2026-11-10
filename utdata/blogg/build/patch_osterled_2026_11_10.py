"""Tillägg i den publicerade artikeln "Vikingarnas värld – vilka platser nämner de?" (E8Jl7DqdvZQR8DQuW3aB) efter
självkontrollen 2026-11-10 (analysplaner/2026-11-10-sjalvkontroll-osterled.md, 4d00080; utdata/varlden/sjalvkontroll/):
utan Ingvarsstenarna ser 58 % (49–67) av platserna mot öster, försvagat. Viktor 2026-11-10: "GO". Texten byggs av
build_osterled.py (som nu läser självkontrollen); här skrivs bara body och body_en till den publicerade artikeln, efter
att det publicerade har jämförts med den sparade kopian av förra versionen.
    ../../../.venv/bin/python patch_osterled_2026_11_10.py [--live]"""
import datetime as dt
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from api.routers import blog  # noqa: E402

DOC = "E8Jl7DqdvZQR8DQuW3aB"
new = json.load(open(os.path.join(ROOT, "utdata", "blogg", "osterled.json"), encoding="utf-8"))
ref = blog.firestore().collection(blog.COLLECTION).document(DOC)
live = ref.get().to_dict()
assert live and live.get("published") and live.get("slug") == new["slug"]
for k in ("body", "body_en"):
    assert "Ingvarsstenarna" in new[k] or "Ingvarr stones" in new[k]
    print(k, "redan ändrad" if live[k] == new[k] else f"ändras ({len(live[k])} → {len(new[k])} tecken)")
backup = os.path.join(ROOT, "utdata", "blogg", "osterled_fore_2026-11-10.json")
if not os.path.exists(backup):
    json.dump({k: live[k] for k in ("title", "summary", "body", "title_en", "summary_en", "body_en")}, open(backup, "w"), ensure_ascii=False, indent=1)
if "--live" in sys.argv:
    ref.set({"body": new["body"], "body_en": new["body_en"], "updatedAt": dt.datetime.now(dt.timezone.utc)}, merge=True)
    blog._forget()
    after = ref.get().to_dict()
    assert after["body"] == new["body"] and after["body_en"] == new["body_en"] and after["published"]
    print("publicerade artikeln uppdaterad:", DOC)
