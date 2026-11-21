"""Rapportversion 2 av folklandsrapporten (Viktor 2026-11-21: "kan vi dra nytta av våra kartor i Vitki över
folklandsgränserna? Vore bra att ha med några illustrerande exempel"): två kartbilder ur Vitki och bilder av
exempelstenarna U 1177 och U 181 i 5.2, och en ändringslogg. Skriver bara body och body_en ur byggarens json efter kontroll
att (1) den publicerade texten är exakt version 1 i versionshanteringen och (2) det enda nya är rubrikraden, bilderna med
bildtexter och ändringsloggen. Behåller publiceringsdatum, sparar en säkerhetskopia och publicerar webbplatsen.
    .venv/bin/python utdata/blogg/build/patch_folkland_v2.py            # bara kontroll
    .venv/bin/python utdata/blogg/build/patch_folkland_v2.py --skriv    # skriv och publicera"""
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

FN = "rapport_folkland.json"
V1 = "deca8d4"   # commit där json-filen är version 1 (den publicerade)
HEAD_V2 = ("*Viktor Kvant, oberoende forskare. Fullt prövat fynd. Rapportversion 2, 2026-11-21.",
           "*Viktor Kvant, independent researcher. Fully tested finding. Report version 2, 2026-11-21.")
NEW_LINE = re.compile(r"^(!\[[^\]]*\]\((/api/blog/figures/[0-9a-f]{16}\.png|https://(upload|thumb)\.wikimedia\.org/\S+)\)|"
                      r"Figur [12]\. .*Bild: Vitki.*|Figure [12]\. .*Image: Vitki.*|U 1(177|81) (i|at) .*Wikimedia Commons.*|"
                      r"## Ändringslogg|## Change log|\*\*Version [12], 2026-11-\d\d\.\*\* .*|)$")


def allowed(old, new):
    a, b = old.split("\n"), new.split("\n")
    bad = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        if tag in ("delete", "replace"):
            for k, line in enumerate(a[i1:i2]):
                if i1 + k == 0 and line.startswith("*Viktor Kvant"):
                    continue
                bad.append("[borttagen] " + line[:120])
        if tag in ("insert", "replace"):
            for k, line in enumerate(b[j1:j2]):
                if j1 + k == 0 and line.startswith(HEAD_V2):
                    continue
                if not NEW_LINE.match(line):
                    bad.append(line[:160])
    return bad


new = json.load(open(os.path.join(ROOT, "utdata", "rapporter", FN), encoding="utf-8"))
v1 = json.loads(subprocess.run(["git", "show", f"{V1}:utdata/rapporter/{FN}"], cwd=ROOT, capture_output=True, text=True, check=True).stdout)
live = {p["slug"]: p for p in blog._all()}
doc = live.get(new["slug"])
assert doc and doc.get("published"), "rapporten är inte publicerad"
same = doc["body"] == v1["body"] and doc["body_en"] == v1["body_en"]
bad = allowed(v1["body"], new["body"]) + allowed(v1["body_en"], new["body_en"])
for t in (new["body"], new["body_en"]):
    for f in re.findall(r"/api/blog/figures/([0-9a-f]{16}\.png)", t):
        assert os.path.exists(os.path.join(ROOT, "data", "blog", "figures", f)), f
print(f"{new['slug']}: publicerad = version 1: {same}; otillåtna rader: {len(bad)}; publicerad {doc.get('publishedAt')}")
for x in bad[:8]:
    print("   ", x)
assert same and not bad

if "--skriv" in sys.argv:
    from src import site_export
    col = blog.firestore().collection(blog.COLLECTION)
    ref = col.document(doc["id"])
    blog._backup(ref.id, ref.get().to_dict())
    ref.set({"body": new["body"], "body_en": new["body_en"], "updatedAt": dt.datetime.now(dt.timezone.utc)}, merge=True)
    blog._forget()
    print("skriven:", new["slug"])
    print(site_export.publish_now())
