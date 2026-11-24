"""Artikeln "Ristarna utan namn – runstenar som kan ha samma okända hand" (populärvetenskap, sv + en).

Bygger på metodrapporten build_rapport_nya_ristare.py och resultaten i utdata/nya_ristare/ (slutprov 1 och 2, låsta planer
2026-11-23); skärmbilderna är tagna i Vitki 2026-11-24 (utdata/blogg/figurer/samma_hand/).
    ../../../.venv/bin/python build_samma_hand.py [--write | --update DOC]"""
import datetime as dt
import io
import json
import os
import re
import sys
from collections import Counter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_figures, blog_labels  # noqa: E402

D = os.path.join(ROOT, "utdata", "nya_ristare")
J = lambda f: json.load(open(os.path.join(D, f), encoding="utf-8"))  # noqa: E731
S1, S2, EX, H3 = J("slutprov_P.json"), J("slutprov2.json"), J("rapport_extra.json"), J("huggteknik.json")
A, O, T1, T2 = S1["alla"], S1["onämnda"], S2["T1"], S2["T2"]
assert (round(100 * A["medel_samma"]), round(100 * A["medel_kontroll"]), round(100 * O["medel_samma"]), round(100 * T1["medel_samma"])) == (42, 7, 69, 46)
assert A["p"] < 0.001 and O["p"] < 0.01 and T1["håller"] and T2["p"] > 0.05 and not H3["H3D"]["håller"]
GRP, LIT = J("grupper.json"), {x["id"]: x for x in J("grupper_litteratur.json")}
OK = [g for g in GRP if g["typ"] == "okänd hand" and g["underlag"] == "gott"]
NEW = [g for g in OK if LIT[g["id"]]["besked"] == "ingen tidigare koppling"]
assert (len(GRP), len(OK), len(NEW)) == (228, 77, 61)
PROV = Counter(k for g in OK for k in g["landskap"])
assert (PROV["Ög"], PROV["Vg"], PROV["Sö"], PROV["U"], PROV["Sm"]) == (24, 15, 10, 10, 9)
G015 = next(g for g in GRP if g["id"] == "G015")
assert G015["stenar"] == ["Ög 16", "Ög 18", "Ög 20", "Ög 234", "Ög 235", "Ög 236", "Ög 237", "Ög 33", "Ög 34", "Ög Fv1959;249"]
assert LIT["G015"]["besked"] == "kopplad tidigare" and LIT["G015"]["sri_runor"][0][:2] == ["Ög 234", "Ög 235"]
assert G015["stil"] == {"RAK": 10}
PREC = round(100 * J("gruppering_utveckling.json")[1]["precision_namngivna"])
assert PREC == 77
RECALL = J("gruppering_utveckling.json")[1]["täckning_namngivna"]
assert round(100 * RECALL) == 9

# ---- skärmbilderna (Vitki, 2026-11-24) ---------------------------------------------------------------------------------
from PIL import Image  # noqa: E402

FIG = {}
for k in ("kort1", "profil"):
    im = Image.open(os.path.join(ROOT, "utdata", "blogg", "figurer", "samma_hand", f"{k}.png")).convert("RGB")
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    FIG[k] = blog_figures.freeze(buf.getvalue())


def chart(sv):
    rows = [":::chart Runologernas stenpar som modellen lägger i samma grupp, procent" if sv
            else ":::chart The runologists' stone pairs the model puts in the same group, percent"]
    for lsv, len_, r in (("Prov 1: alla grupper", "Test 1: all groups", A), ("Prov 1: händer utan namn", "Test 1: hands without a name", O),
                         ("Prov 2: litteraturen", "Test 2: the literature", T1)):
        rows += [f"# {lsv if sv else len_}",
                 f"+{'Runologernas par' if sv else 'The runologists’ pairs'} | {round(100 * r['medel_samma'])} | {r['grupper']} {'grupper' if sv else 'groups'}",
                 f"{'Grannstenar på samma avstånd' if sv else 'Neighbouring stones at the same distance'} | {round(100 * r['medel_kontroll'])} | –"]
    rows.append("Medel per grupp. Proven låstes i förväg. Diagram: Vitki." if sv else "Mean per group. The tests were locked in advance. Chart: Vitki.")
    return "\n".join(rows) + "\n:::"


SLUG = "ristarna-utan-namn"
title = "Ristarna utan namn – runstenar som kan ha samma okända hand"
title_en = "The carvers without a name – runestones that may share an unknown hand"
summary = ("Runologerna har länge vetat att många runstenar huggits av samma ristare, också när ingen namngav sig. Nu kan en modell "
           "peka ut sådana grupper – och i ett låst prov hittade den runologernas egna par sex gånger oftare än grannstenarna.")
summary_en = ("Runologists have long known that many runestones were carved by the same carver, even when no one signed. Now a "
              "model can point out such groups – and in a locked test it found the runologists' own pairs six times as often as "
              "neighbouring stones.")

body = f"""Kring Kuddby, Å, Östra Stenby och Söderköping i Östergötland står tio runstenar i den äldsta stilen, med raka runband utan djurhuvuden. Ingen av dem är signerad, och ingen ristare har fått sitt namn knutet till dem. Men runologerna i Riksantikvarieämbetets register har noterat att två av dem, Ög 234 och Ög 235 vid Östra Stenby kyrka, är gjorda av samma hand.

En modell i Vitki lägger nu alla tio i samma grupp. Den tränades aldrig på runologernas bedömning av just de här stenarna.

![Grupp G015 under Ristarna i Vitki]({FIG['kort1']})
Bild: Vitki, gruppen G015 under Ristarna. Märket ”kopplad tidigare” visar att runologerna redan kopplat ihop två av stenarna; ”stabil 100 %” att gruppen höll ihop när modellen tränades om.

## Händerna som saknar namn

Bara en mindre del av de svenska runstenarna har en känd ristare. Några ristare signerade sina stenar – Öpir, Åsmund, Balle – och runologerna har tillskrivit dem många fler. Men de har också sett något annat: stenar som uppenbarligen är gjorda av samma person, fast ingen vet vad hen hette. ”Samme ristare som …”, skriver utgivarna av *Sveriges runinskrifter* gång på gång.

Vitkis gamla ristarmodell kunde inte se de händerna. Den kunde bara välja bland de namngivna ristarna, och när vi prövade den mot runologernas egna grupper gjorde den inte bättre än en gissning efter platsen.

## Att jämföra två stenar i taget

Den nya modellen gör något annat. Den frågar inte ”vem ristade stenen?” utan ”är de här två stenarna gjorda av samma hand?”. Den jämför stavningen och skiljetecknen, hur orden *efter* och *denna* skrivs, stilgruppen, korsets form, de ord om ornamentiken som utgivarna använde, och avståndet. Den lärde sig vad som skiljer samma hand från olika händer på stenar där ristaren är känd. Sedan slår den ihop stenar som liknar varandra till grupper, men bara inom 30 kilometer.

## Provet

Det svåra är att visa att grupperna betyder något. Vi samlade alla runologernas uttalanden om ”samme ristare” i *Sveriges runinskrifter* och Runor 2020 och delade dem slumpvis i två högar. Den ena fick modellen utvecklas på. Den andra låstes in, och reglerna för provet skrevs ned innan den öppnades.

{chart(True)}

När runologerna säger att två stenar har samma hand hamnade de i samma grupp ungefär två gånger av fem. En sten på samma avstånd hamnade där ungefär en gång av femton. För händer utan namn var det ungefär två gånger av tre. Ett andra prov, mot uttalanden i Fornvännen, Futhark och åtta avhandlingar som modellen aldrig hade sett, gav nästan samma resultat.

## Vad modellen hittade

{len(GRP)} grupper har minst tre stenar. {len(OK)} av dem har gott underlag och ingen enda sten med känd ristare. Flest finns i Östergötland ({PROV['Ög']}) och Västergötland ({PROV['Vg']}), där få ristare har namn. I {len(NEW)} av grupperna har ingen av de källor vi har gått igenom kopplat ihop stenarna.

![Stenprofilen i Stenöversikten]({FIG['profil']})
Bild: Vitki, stenprofilen för Ög 234 i Stenöversikten. Under ”Kan ha samma hand som” står gruppens andra stenar; ett klick öppnar dem.

## Det modellen inte säger

- **Grupperna är inte nya ristare.** De är förslag att pröva på stenarna själva, med ornamentik, runformer och huggteknik.
- **Ungefär tre par av fyra stämmer.** Mätt på stenar med känd ristare har omkring {PREC} procent av paren i en grupp samma ristare. Men grupperna är snäva: de flesta av en ristares stenar hamnar inte i samma grupp.
- **Mot litteraturen höll provet inte för händer utan namn.** Där fanns bara sju grupper att pröva.
- **Huggtekniken bekräftade inte grupperna.** På de 18 stenar där vi har 3D-skanningar var stenarna i samma grupp inte tydligt mer lika i huggspåren.
- **Runologernas bedömningar är inte sanningen.** Modellen återskapar vad de har sett, och de har delvis tittat på samma drag.

Hela metoden, båda proven och svagheterna står i en forskningsrapport. Grupperna finns i Vitki under Ristarna, och varje sten i en grupp visar sina grannar i Stenöversikten.

:::box Det viktigaste i korthet
- Många runstenar är gjorda av samma hand utan att någon vet vad ristaren hette.
- En modell som jämför två stenar i taget hittar runologernas egna par ungefär sex gånger oftare än grannstenar på samma avstånd.
- {len(OK)} grupper saknar känd ristare, och i {len(NEW)} har ingen av de genomgångna källorna kopplat ihop stenarna.
- Grupperna är förslag att pröva på stenarna, inte nya ristare.
:::

## Källor

Samnordisk runtextdatabas (Rundata) 3.1, Uppsala universitet. Riksantikvarieämbetet, Runor (2020). *Sveriges runinskrifter*, Riksantikvarieämbetet. Fornvännen (CC BY 4.0) och Futhark. Metoden och proven: Kvant, V. 2026, Runstenar med samma hand, också utan namn (metodrapport, Vitki). Modellen bygger på Anthropics språkmodell Claude (Claude Opus) för läsningen av källorna; varje använt uttalande granskades av två oberoende granskare."""

body_en = f"""Around Kuddby, Å, Östra Stenby and Söderköping in Östergötland stand ten runestones in the oldest style, with straight rune bands and no animal heads. None of them is signed, and no carver has had a name attached to them. But the runologists of the Swedish National Heritage Board's register have noted that two of them, Ög 234 and Ög 235 at Östra Stenby church, were made by the same hand.

A model in Vitki now puts all ten in the same group. It was never trained on the runologists' judgement of these stones.

![Group G015 under The carvers in Vitki]({FIG['kort1']})
Image: Vitki, the group G015 under The carvers (Swedish interface). The badge "kopplad tidigare" (linked before) shows that the runologists have already linked two of the stones; "stabil 100 %" that the group held together when the model was retrained.

## The hands without names

Only a minority of the Swedish runestones have a known carver. Some carvers signed their stones – Öpir, Åsmund, Balle – and the runologists have attributed many more to them. But they have also seen something else: stones evidently made by the same person, although no one knows that person's name. "The same carver as …", the editors of *Sveriges runinskrifter* write again and again.

Vitki's old carver model could not see these hands. It could only choose among the named carvers, and when we tested it against the runologists' own groups it did no better than a guess by place.

## Comparing two stones at a time

The new model does something else. It does not ask "who carved the stone?" but "were these two stones made by the same hand?". It compares the spelling and the word dividers, how the words *eftir* (after) and *þenna* (this) are written, the style group, the shape of the cross, the words the editors used about the ornament, and the distance. It learned what separates the same hand from different hands on stones whose carver is known. Then it joins stones that resemble each other into groups, but only within 30 kilometres.

## The test

The hard part is to show that the groups mean something. We collected all the runologists' statements about "the same carver" in *Sveriges runinskrifter* and Runor 2020 and split them at random into two piles. The model was developed on one. The other was locked away, and the rules for the test were written down before it was opened.

{chart(False)}

When the runologists say two stones have the same hand, they ended up in the same group about two times in five. A stone at the same distance ended up there about one time in fifteen. For hands without a name it was about two times in three. A second test, against statements in Fornvännen, Futhark and eight theses that the model had never seen, gave almost the same result.

## What the model found

{len(GRP)} groups have at least three stones. {len(OK)} of them have good evidence and not a single stone with a known carver. Most are in Östergötland ({PROV['Ög']}) and Västergötland ({PROV['Vg']}), where few carvers have names. In {len(NEW)} of the groups none of the sources we have searched has linked the stones.

![The stone profile in the Stone overview]({FIG['profil']})
Image: Vitki, the stone profile of Ög 234 in the Stone overview (Swedish interface). Under "Kan ha samma hand som" (May share a hand with) are the group's other stones; a click opens them.

## What the model does not say

- **The groups are not new carvers.** They are proposals to be tested on the stones themselves, with ornament, rune forms and carving technique.
- **About three pairs in four are right.** Measured on stones with a known carver, about {PREC} percent of the pairs in a group have the same carver. But the groups are narrow: most of a carver's stones do not end up in the same group.
- **Against the literature the test did not hold for hands without a name.** There were only seven groups to test.
- **The carving technique did not confirm the groups.** On the 18 stones where we have 3D scans, the stones in the same group were not clearly more alike in their grooves.
- **The runologists' judgements are not the truth.** The model reproduces what they have seen, and they have partly looked at the same features.

The whole method, both tests and the weaknesses are in a research report. The groups are in Vitki under The carvers, and every stone in a group shows its neighbours in the Stone overview.

:::box The essentials in brief
- Many runestones were made by the same hand without anyone knowing the carver's name.
- A model that compares two stones at a time finds the runologists' own pairs about six times as often as neighbouring stones at the same distance.
- {len(OK)} groups have no known carver, and in {len(NEW)} none of the searched sources has linked the stones.
- The groups are proposals to be tested on the stones, not new carvers.
:::

## Sources

Scandinavian Runic-text Database (Rundata) 3.1, Uppsala University. Swedish National Heritage Board, Runor (2020). *Sveriges runinskrifter*, Swedish National Heritage Board. Fornvännen (CC BY 4.0) and Futhark. The method and the tests: Kvant, V. 2026, Runestones by the same hand, also without a name (methods report, Vitki). The reading of the sources used Anthropic's language model Claude (Claude Opus); every statement used was reviewed by two independent reviewers."""

# ---- kontroller ---------------------------------------------------------------------------------------------------------
HOLDBACK = re.compile(r"\bAI\b|signifikan|p-värde|p-value|bootstrap|\bHolm\b", re.I)
labels = ["Forskning", "Ristare", "Sannolikhetsmodellen"]
assert blog_labels.check(labels) is None, blog_labels.check(labels)
assert round(A["medel_samma"] / A["medel_kontroll"]) == 6 and T2["grupper"] == 7  # "sex gånger oftare", "sju grupper"
for b, lang in ((body, "sv"), (body_en, "en")):
    assert not HOLDBACK.search(b), (lang, HOLDBACK.search(b).group(0))
    assert not re.search(r"^\s*\|", b, re.M)
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M))
    assert "{" not in b and "}" not in b
    assert b.index("Det viktigaste i korthet" if lang == "sv" else "The essentials in brief") < b.index("## Källor" if lang == "sv" else "## Sources")
    caps = [b.splitlines()[i + 1] for i, ln in enumerate(b.splitlines()) if ln.startswith("![")]
    assert len(caps) == 2 and all(c.startswith("Bild: Vitki" if lang == "sv" else "Image: Vitki") for c in caps)
OUT = {"slug": SLUG, "title": title, "summary": summary, "body": body, "title_en": title_en, "summary_en": summary_en,
       "body_en": body_en, "labels": labels}
path = os.path.join(ROOT, "utdata", "blogg", "samma_hand.json")
json.dump(OUT, open(path, "w"), ensure_ascii=False, indent=1)
print(path, len(body.split()), "ord sv,", len(body_en.split()), "words en")

if "--update" in sys.argv or "--write" in sys.argv:
    from api.routers import blog
    col = blog.firestore().collection(blog.COLLECTION)
    now = dt.datetime.now(dt.timezone.utc)
    if "--update" in sys.argv:
        doc = sys.argv[sys.argv.index("--update") + 1]
        ref = col.document(doc)
        old = ref.get().to_dict()
        assert old and not old.get("published") and old.get("slug") == SLUG, "Bara det opublicerade utkastet skrivs över härifrån"
        ref.set({**OUT, "updatedAt": now}, merge=True)
        print("uppdaterat utkast:", doc, SLUG)
    else:
        assert not [p for p in blog._all() if p.get("slug") == SLUG], "Adressen används redan; skriv över med --update"
        ref = col.document()
        ref.set({**OUT, "published": False, "month": now.strftime("%Y-%m"), "author": "Viktor Kvant",
                 "topic": "Ristare|samma hand", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id, SLUG)
    blog._forget()
