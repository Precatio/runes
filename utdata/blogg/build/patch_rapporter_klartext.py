"""Klartextmeningar i de publicerade forskningsrapporterna (mallen version 4, 2026-10-31; Viktor: "gör alla saker du
föreslår") och publicering av metodrapporten om ristarförslagen. Skriver bara body och body_en ur byggarnas json efter
kontroll att det enda nya är klartextmeningen; behåller publiceringsdatum och övriga fält, sparar säkerhetskopior och
publicerar webbplatsen. Metodrapporten publiceras som Admin gör det (publiceringstid nu, månad, mönstrens läge).
    .venv/bin/python utdata/blogg/build/patch_rapporter_klartext.py            # klartext + publicera ristarrapporten
    .venv/bin/python utdata/blogg/build/patch_rapporter_klartext.py --utan-ristar   # bara klartexten"""
import datetime as dt
import difflib
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from api.routers import blog  # noqa: E402
from src import site_export  # noqa: E402

LIVE = {"TyFNK0gkwZ6iu8hAfR7i": "rapport_r_for_R.json", "G7k7V4x6soJZ8eTHtHcy": "rapport_familjens_plats.json",
        "sVxpHokkL0cJkADJPN1q": "rapport_monoftong.json"}
DRAFT, DRAFT_FN = "50scPhz0w1PBvuESY67g", "rapport_ristarmodellen.json"
col = blog.firestore().collection(blog.COLLECTION)
now = dt.datetime.now(dt.timezone.utc)


def only_plain_words(old: str, new: str) -> bool:
    """The only change is the plain-words sentence: added lines with it, or a line that now ends with it."""
    a, b = old.split("\n"), new.split("\n")
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        o, n = a[i1:i2], b[j1:j2]
        added = "\n".join(n)
        if tag == "delete" or not ("I klartext" in added or "In plain words" in added):
            return False
        if tag == "replace" and not all(any(x.startswith(y) for x in n) for y in o):
            return False
    return True


for doc, fn in LIVE.items():
    new = json.load(open(os.path.join(ROOT, "utdata", "rapporter", fn), encoding="utf-8"))
    ref = col.document(doc)
    old = ref.get().to_dict()
    assert old and old.get("published") and old["slug"] == new["slug"], doc
    assert only_plain_words(old["body"], new["body"]) and only_plain_words(old["body_en"], new["body_en"]), doc
    blog._backup(ref.id, old)
    ref.set({"body": new["body"], "body_en": new["body_en"], "updatedAt": now}, merge=True)
    print("klartext:", new["slug"], "| publicerad", old.get("publishedAt"))

if "--utan-ristar" not in sys.argv:
    new = json.load(open(os.path.join(ROOT, "utdata", "rapporter", DRAFT_FN), encoding="utf-8"))
    ref = col.document(DRAFT)
    old = ref.get().to_dict()
    assert old and not old.get("published") and old["slug"] == new["slug"] == "ristarforslag-blindprov"
    blog._backup(ref.id, old)
    when = blog.publication_time(None, blog._ts(old.get("publishedAt")), now)
    data = {k: new[k] for k in ("title", "summary", "body", "title_en", "summary_en", "body_en", "labels")}
    data |= {"published": True, "publishedAt": when, "month": when.strftime("%Y-%m"), "updatedAt": now}
    if not old.get("snapshot"):
        data["snapshot"] = blog._snapshot()
    ref.set(data, merge=True)
    print("publicerad:", new["slug"], when)
blog._forget()
print(site_export.publish_now())
