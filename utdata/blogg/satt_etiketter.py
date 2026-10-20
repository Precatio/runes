"""Etiketter på de artiklar som redan finns (src/blog_labels.py), satta direkt i Firestore – publicerade artiklar ändras
bara den vägen. Körs en gång; nya artiklar får sina etiketter i Admin eller i sitt byggskript.
    .venv/bin/python utdata/blogg/satt_etiketter.py [--skriv]
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from src import blog_labels
from api.routers import blog

ETIKETTER = {
    "2026-10-ristarsignatur-breder-ut-sig": ["Forskning", "Ristare", "Datering och stil"],
    "hur-spraklik-ar-en-runfoljd": ["Metod", "Kryptologi", "Språk och stavning"],
    "den-som-bryter-denna-sten": ["Forskning", "Tro och magi"],
    "stenar-och-stavar": ["Forskning", "Språk och stavning", "Huggspår och 3D"],
    "korpen-som-heter-minne": ["Personligt", "Eddan"],
    "hon-arvde-efter-sitt-barn-kvinnorna-pa-runstenarna": ["Forskning", "Kvinnor och barn", "Formler och syfte"],
    "dottrarna-som-runstenarna-glomde": ["Forskning", "Kvinnor och barn"],
    "reste-sjalv-eller-lat-resa": ["Forskning", "Språk och stavning", "Formler och syfte", "Geografi"],
    "stilgruppernas-morkertal": ["Forskning", "Datering och stil", "Ristare"],
    "2026-10-bonen-tystnade-korset-stod-kvar": ["Forskning", "Tro och magi", "Datering och stil"],
    "runorna-som-fattas": ["Pågående arbete", "Sannolikhetsmodellen"],
    "tor-svarade-korset-och-tystnade": ["Forskning", "Tro och magi"],
    "undantaget-vid-randers": ["Forskning", "Norden", "Tro och magi"],
    "vastgotarna-skrev-som-danskarna": ["Forskning", "Norden", "Språk och stavning"],
    "maltstenen-raknad-i-stallet-for-tolkad": ["Forskning", "Tolkning", "Sannolikhetsmodellen"],
    "erik-skrev-r-och-bygden-skrev-efter": ["Forskning", "Språk och stavning", "Ristare", "Geografi"],
    "vem-talar-i-havamal": ["Forskning", "Eddan"],
    "tegnar-i-soder-boner-i-norr": ["Forskning", "Norden", "Formler och syfte"],
    "prickarna-kom-med-korset": ["Forskning", "Språk och stavning", "Datering och stil"],
    "tyde-den-som-kan-del-2": ["Forskning", "Kryptologi"],
    "mojliga-ristare-utan-namn": ["Forskning", "Ristare"],
}
for slug, labels in ETIKETTER.items():
    assert blog_labels.check(labels) is None, (slug, blog_labels.check(labels))
posts = {p["slug"]: p for p in blog._all()}
saknas = [s for s in posts if s not in ETIKETTER]
print("artiklar utan etikett i listan:", saknas)
col = blog.firestore().collection(blog.COLLECTION)
for slug, labels in ETIKETTER.items():
    p = posts.get(slug)
    if not p:
        print("finns inte:", slug); continue
    labels = blog_labels.ordered(labels)
    if "--skriv" in sys.argv:
        col.document(p["id"]).set({"labels": labels}, merge=True)
    print(("skrev " if "--skriv" in sys.argv else "skulle skriva "), slug, labels)
blog._forget()
