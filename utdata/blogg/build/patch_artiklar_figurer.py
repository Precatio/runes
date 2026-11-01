"""Rapporternas nya illustrationer i de publicerade artiklar där de passar (Viktor 2026-11-01: "Uppdatera artiklarna
också där det passar"): seriationen sten för sten i "Stilgruppernas mörkertal" och spårläsarens två exempel i
"Runorna som fattas". Lägger bara till ett bildstycke per språk; kontrollerar att allt annat är oförändrat, behåller
publiceringsdatum, sparar säkerhetskopior och publicerar webbplatsen.
    .venv/bin/python utdata/blogg/build/patch_artiklar_figurer.py [--skriv]"""
import datetime as dt
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "utdata", "rapporter", "figurer"))
from api.routers import blog  # noqa: E402
from figur import FIG, bild  # noqa: E402

assert FIG["seriation"]["n"] == 501 and FIG["spar_counts"] == {"n": 157, "wrong_to_right": 10, "right_to_wrong": 0}
assert (FIG["spar"]["gain"]["sig"], FIG["spar"]["loss"]["sig"]) == ("Sö 112", "Sö 319")
SER = {
    "sv": bild("seriation", "sv", "Samma ordning sten för sten: Upplands 501 stildaterade runstenar, ordnade bara efter språk och innehåll, mot Gräslunds stilgrupp. Varje punkt är en sten och det röda strecket mittvärdet i gruppen. Ordningen stiger med stilgrupperna, men en enskild sten kan hamna långt från sin grupp. Diagram: Vitki, ur Samnordisk runtextdatabas; stilgrupperna efter Gräslund (2006)."),
    "en": bild("seriation", "en", "The same order stone by stone: Uppland's 501 style-dated runestones, ordered by language and content alone, against Gräslund's style group. Each dot is a stone and the red bar the middle value of the group. The order rises with the style groups, but a single stone can land far from its group. Chart: Vitki, from the Scandinavian Runic-text Database; the style groups after Gräslund (2006)."),
}
SPA = {
    "sv": bild("spar", "sv", "Vad spåren säger om ett dolt ord, i två av de 157 provorden: det där spåren hjälpte mest (Sö 112) och det där de sänkte sannolikheten för rätt svar mest (Sö 319). Rutorna visar för varje runa vilka av runradens 16 runor skanningen tillåter; rätt runa har en ring. I inget av de 157 orden gjorde spåren ett rätt ord fel, och i tio gjorde de ett fel ord rätt. Illustration: Vitki, ur Laila Kitzler Åhfeldts 3D-skanningar (Riksantikvarieämbetet, Runristandets dynamik; CC BY 4.0) och Samnordisk runtextdatabas."),
    "en": bild("spar", "en", "What the traces say about a hidden word, in two of the 157 test words: the one where the traces helped most (Sö 112) and the one where they lowered the probability of the right answer most (Sö 319). For each rune the boxes show which of the 16 runes of the futhark the scan allows; the right rune is circled. In none of the 157 words did the traces make a right word wrong, and in ten they made a wrong word right. Illustration: Vitki, from Laila Kitzler Åhfeldt's 3D scans (Swedish National Heritage Board, Runristandets dynamik; CC BY 4.0) and the Scandinavian Runic-text Database."),
}
# (slug, språk, ankare: texten som bildstycket läggs in efter, figur, om ankaret avslutar en listpunkt i en längre lista)
PLAN = [
    ("stilgruppernas-morkertal", "sv", "Källa: Vitkis korpusanalys i R (chronology.R)", SER),
    ("stilgruppernas-morkertal", "en", "(chronology.R)", SER),
    ("runorna-som-fattas", "sv", "En runa med fler djupa bistavar än någon runa har, en möjlig bindruna, föreslår inget alls.", SPA),
    ("runorna-som-fattas", "en", "- **Traces from the scans.**", SPA),
]


def insert(body: str, anchor: str, fig: str) -> str:
    """The figure as its own paragraph after the paragraph or list item that holds the anchor."""
    assert body.count(anchor) == 1, anchor
    i = body.index(anchor)
    end = body.find("\n", i)
    end = len(body) if end < 0 else end
    rest = body[end:]
    if rest.startswith("\n\n") or not rest:
        return body[:end] + "\n\n" + fig + rest
    return body[:end] + "\n\n" + fig + "\n\n" + rest.lstrip("\n")   # mitt i en lista: listan fortsätter efter bilden


live = {p["slug"]: p for p in blog._all()}
new = {}
for slug, lang, anchor, fig in PLAN:
    p = live[slug]
    key = "body" if lang == "sv" else "body_en"
    cur = new.get((slug, key), p[key])
    assert "/api/blog/figures/" + fig[lang].split("/api/blog/figures/")[1][:16] not in cur, f"{slug} har redan bilden"
    out = insert(cur, anchor, fig[lang])
    # allt utom bildstycket är oförändrat (en radbrytning i en lista blir två)
    assert out.replace(fig[lang] + "\n\n", "").replace(fig[lang], "").replace("\n\n\n\n", "\n\n").replace("\n\n", "\n") == cur.replace("\n\n", "\n")
    new[(slug, key)] = out
    print(f"{slug} [{lang}]: bild efter ”{anchor[:50]}”; publicerad {p.get('publishedAt')}")

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
