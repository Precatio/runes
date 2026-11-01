"""Rapportversion 2 av fem publicerade forskningsrapporter (Viktor 2026-11-01: "lägg till i samtliga 4" och "Om Vitki
har gjort illustrationen så nämn det"): figurer i vägen, seriationen, familjegrupperna och spårläsaren, och kartornas
bildtexter i rapporten om ʀ. Skriver bara body och body_en ur byggarnas json efter kontroll att (1) den publicerade
texten är exakt version 1 i versionshanteringen och (2) det enda nya är rubrikraden, figurerna med bildtexter, de
ändrade källraderna under kartorna och ändringsloggen. Behåller publiceringsdatum, sparar säkerhetskopior och
publicerar webbplatsen.
    .venv/bin/python utdata/blogg/build/patch_rapporter_figurer.py            # bara kontroll
    .venv/bin/python utdata/blogg/build/patch_rapporter_figurer.py --skriv    # skriv och publicera"""
import datetime as dt
import difflib
import json
import os
import re
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from api.routers import blog  # noqa: E402

FILES = ["rapport_riktning.json", "rapport_seriation.json", "rapport_familjens_plats.json", "rapport_sparlasare.json",
         "rapport_r_for_R.json"]
V1 = "77b3139"   # commit där alla fem json-filerna är version 1
NEW_LINE = re.compile(r"^(!\[[^\]]*\]\(/api/blog/figures/[0-9a-f]{16}\.png\)|Figur 1\. .*Vitki.*|Figure 1\. .*Vitki.*|"
                      r"## Ändringslogg|## Change log|- \*\*Version 2, 2026-11-01\.\*\* .*|)$")


def allowed(old: str, new: str) -> list[str]:
    """Lines in the change that are not allowed; empty when the change is only the version, figures, credits and log."""
    a, b = old.split("\n"), new.split("\n")
    bad = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        if tag == "delete":
            bad += a[i1:i2]
            continue
        for k, line in enumerate(b[j1:j2]):
            if j1 + k == 0 and line.startswith("*Viktor Kvant") and ("Rapportversion 2, 2026-11-01" in line or "Report version 2, 2026-11-01" in line):
                continue
            if NEW_LINE.match(line):
                continue
            if tag == "replace" and ("Karta: Vitki" in line or "Map: Vitki" in line):
                old_line = a[i1 + k] if i1 + k < i2 else ""
                if old_line.replace("Källa: Rundata", "Karta: Vitki, ur Rundata").replace("Source: Rundata", "Map: Vitki, from Rundata") == line:
                    continue
            bad.append(line)
        if tag == "replace":
            for k, line in enumerate(a[i1:i2]):
                if k == 0 and i1 == 0 and line.startswith("*Viktor Kvant"):
                    continue
                if "Källa: Rundata; kustlinjer" in line or "Source: Rundata; coastlines" in line:
                    continue
                bad.append("[borttagen] " + line)
    return bad


live = {p["slug"]: p for p in blog._all()}
col = blog.firestore().collection(blog.COLLECTION)
now = dt.datetime.now(dt.timezone.utc)
todo = []
for fn in FILES:
    new = json.load(open(os.path.join(ROOT, "utdata", "rapporter", fn), encoding="utf-8"))
    v1 = json.loads(subprocess.run(["git", "show", f"{V1}:utdata/rapporter/{fn}"], cwd=ROOT, capture_output=True, text=True, check=True).stdout)
    doc = live.get(new["slug"])
    assert doc and doc.get("published"), f"{new['slug']} är inte publicerad"
    same = doc["body"] == v1["body"] and doc["body_en"] == v1["body_en"]
    bad = allowed(v1["body"], new["body"]) + allowed(v1["body_en"], new["body_en"])
    print(f"{new['slug']}: publicerad = version 1: {same}; otillåtna rader: {len(bad)}; publicerad {doc.get('publishedAt')}")
    for x in bad[:6]:
        print("   ", x[:160])
    assert same and not bad, new["slug"]
    todo.append((doc["id"], new))

if "--skriv" in sys.argv:
    from src import site_export
    for doc_id, new in todo:
        ref = col.document(doc_id)
        old = ref.get().to_dict()
        blog._backup(ref.id, old)
        ref.set({"body": new["body"], "body_en": new["body_en"], "updatedAt": now}, merge=True)
        print("skriven:", new["slug"])
    blog._forget()
    print(site_export.publish_now())
