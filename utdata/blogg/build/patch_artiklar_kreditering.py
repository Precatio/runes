"""Bildtexter i publicerade artiklar som inte sa att Vitki gjort bilden (Viktor 2026-11-01: "Om Vitki har gjort
illustrationen så nämn det"). Ändrar bara de bildtexter som står direkt under egna bilder (/api/blog/figures/) och
saknar Vitki; allt annat kontrolleras oförändrat. Behåller publiceringsdatum, sparar säkerhetskopior, publicerar.
    .venv/bin/python utdata/blogg/build/patch_artiklar_kreditering.py [--skriv]"""
import datetime as dt
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from api.routers import blog  # noqa: E402


def credit(slug: str, lang: str, cap: str) -> str:
    if slug == "erik-skrev-r-och-bygden-skrev-efter":
        a, b = (("Källa: Samnordisk runtextdatabas", "Karta: Vitki, ur Samnordisk runtextdatabas") if lang == "sv" else
                ("Source: Scandinavian Runic-text Data Base", "Map: Vitki, from the Scandinavian Runic-text Data Base"))
        assert cap.count(a) == 1, cap
        return cap.replace(a, b)
    if slug == "runorna-som-fattas":
        chart = "100 procent" in cap or "100 per cent" in cap          # Sö 206-diagrammet
        return cap.rstrip() + (" Diagram: Vitki." if chart else " Illustration: Vitki.")
    raise ValueError(slug)


CAP = re.compile(r"(!\[[^\]]*\]\(/api/blog/figures/[^)]+\)\n)([^\n]*)")
live = {p["slug"]: p for p in blog._all()}
out = {}
for slug in ("runorna-som-fattas", "erik-skrev-r-och-bygden-skrev-efter"):
    p = live[slug]
    for key, lang in (("body", "sv"), ("body_en", "en")):
        changed = []

        def fix(m):
            if "Vitki" in m.group(2):
                return m.group(0)
            new = credit(slug, lang, m.group(2))
            changed.append((m.group(2)[-60:], new[-60:]))
            return m.group(1) + new
        nb = CAP.sub(fix, p[key])
        assert len(changed) in (2, 3) and "Vitki" in nb
        out[(slug, key)] = nb
        for a, b in changed:
            print(f"{slug} [{lang}]: …{a}\n    → …{b}")

if "--skriv" in sys.argv:
    from src import site_export
    col = blog.firestore().collection(blog.COLLECTION)
    now = dt.datetime.now(dt.timezone.utc)
    for slug in ("runorna-som-fattas", "erik-skrev-r-och-bygden-skrev-efter"):
        ref = col.document(live[slug]["id"])
        old = ref.get().to_dict()
        assert old["body"] == live[slug]["body"] and old["body_en"] == live[slug]["body_en"]
        blog._backup(ref.id, old)
        ref.set({"body": out[(slug, "body")], "body_en": out[(slug, "body_en")], "updatedAt": now}, merge=True)
        print("skriven:", slug)
    blog._forget()
    print(site_export.publish_now())
