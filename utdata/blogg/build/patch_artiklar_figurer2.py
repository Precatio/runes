"""Nya illustrationer i fyra publicerade artiklar (Viktor 2026-11-01: "ja" och "även 4"): signerade stenar med och
utan ristare i "Ristarna som aldrig blev ihågkomna", de fjorton stenarna efter döttrar i "Döttrarna som runstenarna
glömde", maskeringsprovet i "Hur bra är vår sannolikhetsmodell egentligen?" och arvsgången på Hillersjöhällen i "Hon
ärvde efter sitt barn". Ett bildstycke per språk efter ett angivet stycke; allt annat kontrolleras oförändrat.
Behåller publiceringsdatum, sparar säkerhetskopior och publicerar webbplatsen.
    .venv/bin/python utdata/blogg/build/patch_artiklar_figurer2.py [--skriv]"""
import datetime as dt
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from api.routers import blog  # noqa: E402
from src import blog_figures  # noqa: E402

FD = os.path.join(ROOT, "utdata", "blogg", "artikelfigurer")
K = json.load(open(os.path.join(FD, "kartdata.json")))
A = json.load(open(os.path.join(FD, "artikelfigurer.json")))
rist = K["ristare"]
mal = [r for r in rist if r["prov"] in ("U", "Sö")]
assert (len(mal), sum(not r["known"] for r in mal), len(rist) - len(mal), sum(not r["known"] for r in rist) - sum(not r["known"] for r in mal)) == (139, 2, 38, 18)
assert len(K["dottrar"]) == 14 and sum(d["mother"] for d in K["dottrar"]) == 7 and sum(d["signum"].startswith("U ") for d in K["dottrar"]) == 11
M = A["modell"]
assert (M["sure"]["sig"], M["unsure"]["sig"], round(100 * M["sure"]["q"]), round(100 * M["unsure"]["top3"][0][1])) == ("Sm 134", "Sm 64", 98, 26)


def fig(name, lang, caption):
    assert "Vitki" in caption[-260:]
    with open(os.path.join(FD, f"{name}_{lang}.png"), "rb") as fh:
        url = blog_figures.freeze(fh.read())
    return f"![{caption.split('.')[0]}]({url})\n{caption}"


PLAN = [
    ("ristarna-som-aldrig-blev-ihagkomna", "sv", ":::chart Runstenar med ristarsignatur som saknar ristare i databasen", fig("ristare_karta", "sv",
     "Var ristarna saknas. Varje punkt är en runsten där ristaren signerade enligt Källströms katalog (2007): i Uppland och Södermanland saknar databasen ristaren på 2 av 139 stenar, i övriga Sverige på 18 av 38. Karta: Vitki, ur Källström (2007, Bilaga 1) och Samnordisk runtextdatabas (Rundata 3.1); kustlinjer och sjöar: Natural Earth.")),
    ("ristarna-som-aldrig-blev-ihagkomna", "en", ":::chart Runestones with a carver's signature but no carver in the database", fig("ristare_karta", "en",
     "Where the carvers are missing. Each point is a runestone the carver signed according to Källström's catalogue (2007): in Uppland and Södermanland the database lacks the carver on 2 of 139 stones, in the rest of Sweden on 18 of 38. Map: Vitki, from Källström (2007, Appendix 1) and the Scandinavian Runic-text Database (Rundata 3.1); coastlines and lakes: Natural Earth.")),
    ("dottrarna-som-runstenarna-glomde", "sv", "Mödrarna sörjde sina döttrar som sina söner.", fig("dottrar_karta", "sv",
     "De fjorton runstenarna efter döttrar. Fylld punkt: modern är med och reser stenen; ring: utan modern. Elva av de fjorton står i Uppland. Karta: Vitki, ur Samnordisk runtextdatabas, stenarna efter döttrar genomgångna för hand; kustlinjer och sjöar: Natural Earth.")),
    ("dottrarna-som-runstenarna-glomde", "en", "The fourteen runestones for daughters have a few traits in common.", fig("dottrar_karta", "en",
     "The fourteen runestones for daughters. Filled point: the mother helps raise the stone; ring: without the mother. Eleven of the fourteen stand in Uppland. Map: Vitki, from the Scandinavian Runic-text Database, the stones for daughters read one by one; coastlines and lakes: Natural Earth.")),
    ("hur-bra-ar-var-modell-egentligen", "sv", "Siffrorna kommer från prov där hela stenar hålls undan.", fig("modell_prov", "sv",
     "Så ser provet ut. Två ord ur maskeringsprovet, valda efter en regel: det första säkra svaret (Sm 134) och det första där inget förslag når 50 procent (Sm 64). När modellen är säker har den nästan alltid rätt; när den är osäker säger den det. Illustration: Vitki, ur Vitkis maskeringsprov på Samnordisk runtextdatabas.")),
    ("hur-bra-ar-var-modell-egentligen", "en", "The figures come from tests where whole stones are held out.", fig("modell_prov", "en",
     "What the test looks like. Two words from the masking test, chosen by a rule: the first sure answer (Sm 134) and the first where no proposal reaches 50 per cent (Sm 64). When the model is sure it is nearly always right; when it is unsure it says so. Illustration: Vitki, from Vitki's masking test on the Scandinavian Runic-text Database.")),
    ("hon-arvde-efter-sitt-barn-kvinnorna-pa-runstenarna", "sv", "Vår hypotes är att kvinnan reste stenen när hon stod i mannens ställe.", fig("hillersjo", "sv",
     "Samma Inga på Hillersjöhällen (U 29), som nämner Ragnfast i Snottsta som hennes make. Ragnfast dog och sedan deras son, och Inga ärvde efter sonen; när Inga själv dog ärvde hennes mor Gerlög efter henne. Illustration: Vitki, efter inskriften U 29 i Samnordisk runtextdatabas.")),
    ("hon-arvde-efter-sitt-barn-kvinnorna-pa-runstenarna", "en", "Our hypothesis is that a woman raised the stone when she stood in the man's place.", fig("hillersjo", "en",
     "The same Inga on the Hillersjö rock (U 29), which names Ragnfastr of Snotastaðir as her husband. Ragnfastr died and then their son, and Inga inherited from the son; when Inga herself died her mother Geirlaug inherited from her. Illustration: Vitki, after the inscription U 29 in the Scandinavian Runic-text Database.")),
]


def insert(body, anchor, figure):
    assert body.count(anchor) == 1, anchor
    end = body.find("\n\n", body.index(anchor))
    assert end > 0
    return body[:end] + "\n\n" + figure + body[end:]


live = {p["slug"]: p for p in blog._all()}
new = {}
for slug, lang, anchor, figure in PLAN:
    key = "body" if lang == "sv" else "body_en"
    cur = new.get((slug, key), live[slug][key])
    assert figure.split("](")[1][:40] not in cur, f"{slug} har redan bilden"
    out = insert(cur, anchor, figure)
    assert out.replace("\n\n" + figure, "", 1) == cur
    new[(slug, key)] = out
    print(f"{slug} [{lang}]: efter ”{anchor[:55]}”; publicerad {live[slug].get('publishedAt')}")

if "--skriv" in sys.argv:
    from src import site_export
    col = blog.firestore().collection(blog.COLLECTION)
    now = dt.datetime.now(dt.timezone.utc)
    for slug in sorted({s for s, _ in new}):
        ref = col.document(live[slug]["id"])
        old = ref.get().to_dict()
        assert old["body"] == live[slug]["body"] and old["body_en"] == live[slug]["body_en"]
        blog._backup(ref.id, old)
        ref.set({"body": new[(slug, "body")], "body_en": new[(slug, "body_en")], "updatedAt": now}, merge=True)
        print("skriven:", slug)
    blog._forget()
    print(site_export.publish_now())
