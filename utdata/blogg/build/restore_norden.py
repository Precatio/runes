"""Återställer den publicerade artikeln "Västgötarna skrev som danskarna" (raderad av misstag 2026-10-18) ur det
senaste bygget (utdata/blogg/norden2.json), och binder samman den med den nya ordförrådsartikeln: en rikskarta ur
appens Jämför länder-vy ("Dansk prägel", rikena omkring 1025) i gränsavsnittet, och en kopplingsruta som pekar på
uppföljaren. Artikelns två gamla figurer ligger kvar i bloggens figurarkiv och kontrolleras före skrivningen.
    ../../../.venv/bin/python restore_norden.py --write
"""
import datetime as dt
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)

d = json.load(open(os.path.join(ROOT, "utdata", "blogg", "norden2.json"), encoding="utf-8"))
assert d["slug"] == "vastgotarna-skrev-som-danskarna"

# figurerna som artikeln redan använder ska finnas kvar i arkivet, liksom den nya kartan
IMG_KARTA = "/api/blog/figures/41f564fbed4b5a97.png"  # Dansk prägel, rikena omkring 1025 (Jämför länder-vyn)
for b in (d["body"], d["body_en"]):
    for fig in re.findall(r"/api/blog/figures/([0-9a-f]{16}\.png)", b):
        assert os.path.exists(os.path.join(ROOT, "data", "blog", "figures", fig)), f"figuren saknas: {fig}"
assert os.path.exists(os.path.join(ROOT, "data", "blog", "figures", os.path.basename(IMG_KARTA)))

MAP_SV = f"""## Syns riksgränsen i runstenarna?

![Mönstret Dansk prägel på kartan, med rikena omkring 1025]({IMG_KARTA})
Mönstret "Dansk prägel" – stenar som är formulerade och stavade mer som danska än som svenska, enligt modellen i den här artikeln – på Vitkis karta, med rikenas ungefärliga gränser omkring 1025: Danmark i rött, götarnas landskap i grönt, Svitjod i brunt, Norge i lila. Blå rutor är andelen runstenar i rutan med mönstret; mörkare är större andel. Prägeln är starkast i det danska området, lyser också väster om Vättern – och tunnas ut mot Mälardalen. Kartan går att utforska själv under Karta → Jämför länder i appen."""

MAP_EN = f"""## Does the realm border show in the runestones?

![The Danish character pattern on the map, with the realms about 1025]({IMG_KARTA})
The pattern "Danish character" – stones phrased and spelled more like Danish than Swedish ones, according to the model of this article – on Vitki's map, with the approximate borders of the realms about 1025: Denmark in red, the Geatish provinces in green, Svitjod in brown, Norway in purple. Blue cells are the share of runestones in the cell carrying the pattern; darker is a larger share. The character is strongest in the Danish area, glows west of Lake Vättern too – and thins out towards the Mälaren valley. The map can be explored under Karta → Jämför länder in the app."""

BOX_SV = """:::box Två mätningar, samma gräns
Den här artikeln har fått en oberoende uppföljare: [Västgöten reste själv – upplänningen lät resa](/artiklar/reste-sjalv-eller-lat-resa). Där mäts inte stavningen utan vilka ord som alls står på stenarna, inom Sverige – och ordvalet pekar åt samma håll: Västergötland reste sina stenar med det enkla verbet *ræisti* och hyllade sina döda som *goðan dræng*, precis som i det danska området, medan Mälardalen *lät resa* och bad för själen. Stavningen vet ingenting om ordvalet och ordvalet ingenting om stavningen, så två oberoende mätningar ritar nu samma gräns.
:::

## Se själv"""

BOX_EN = """:::box Two measurements, the same boundary
This article has an independent sequel: [Raise It Yourself – or Have It Raised](/artiklar/reste-sjalv-eller-lat-resa). There we measure not the spelling but which words stand on the stones at all, within Sweden – and the choice of words points the same way: Västergötland raised its stones with the simple verb *ræisti* and praised its dead as *goðan dræng*, just as in the Danish area, while the Mälaren valley *had its stones raised* and prayed for the soul. The spelling knows nothing of the choice of words and the choice of words nothing of the spelling, so two independent measurements now draw the same boundary.
:::

## See for yourself"""

body = d["body"].replace("## Syns riksgränsen i runstenarna?", MAP_SV, 1)
assert body != d["body"]
body = body.replace("## Se själv", BOX_SV, 1)
body_en = d["body_en"].replace("## Does the realm border show in the runestones?", MAP_EN, 1)
assert body_en != d["body_en"]
body_en = body_en.replace("## See for yourself", BOX_EN, 1)
out = {**d, "body": body, "body_en": body_en}
json.dump(out, open(os.path.join(ROOT, "utdata", "blogg", "norden2_aterstalld.json"), "w"), ensure_ascii=False, indent=1)
print("byggd:", len(body), len(body_en))

if "--write" in sys.argv:
    from api.routers import blog
    col = blog.firestore().collection(blog.COLLECTION)
    assert not [p for p in blog._all() if p.get("slug") == out["slug"]], "Artikeln finns redan"
    now = dt.datetime.now(dt.timezone.utc)
    published_at = dt.datetime(2026, 10, 14, 12, 0, tzinfo=dt.timezone.utc)  # ursprunglig publicering
    ref = col.document()
    ref.set({**out, "published": True, "month": "2026-10", "author": "Viktor Kvant",
             "topic": "Norden|statistik i R", "createdAt": published_at, "updatedAt": now})
    print("återställd och publicerad:", ref.id)
    blog._forget()
