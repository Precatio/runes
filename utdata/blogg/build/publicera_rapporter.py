"""Publicerar opublicerade forskningsrapporter som Admin gör det (publiceringstid nu, månad, mönstrens läge) och
publicerar webbplatsen. Bara utkast med etiketten Rapport; texten ändras inte.
    .venv/bin/python utdata/blogg/build/publicera_rapporter.py DOC [DOC ...]"""
import datetime as dt
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from api.routers import blog  # noqa: E402
from src import site_export  # noqa: E402

col = blog.firestore().collection(blog.COLLECTION)
for doc in sys.argv[1:]:
    ref = col.document(doc)
    old = ref.get().to_dict()
    assert old and not old.get("published") and "Rapport" in (old.get("labels") or []), doc
    now = dt.datetime.now(dt.timezone.utc)
    when = blog.publication_time(None, blog._ts(old.get("publishedAt")), now)
    data = {"published": True, "publishedAt": when, "month": when.strftime("%Y-%m"), "updatedAt": now}
    if not old.get("snapshot"):
        data["snapshot"] = blog._snapshot()
    blog._backup(ref.id, old)
    ref.set(data, merge=True)
    print("publicerad:", old["slug"], when)
blog._forget()
print(site_export.publish_now())
