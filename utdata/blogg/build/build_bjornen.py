"""Artikeln "Var sjätte runsten bär en björn" – del 4 i serien Nordiska väsen under vikingatiden: björnen.

Bygger på den låsta studien analysplaner/2026-11-21-bjornen.md (1779c2e); siffrorna ur utdata/bjornen/matt.json, t2.csv
och b4_shm.json; varje citat kontrolleras mot texten i korpusen.
    ../../../.venv/bin/python build_bjornen.py [--write | --update DOC]"""
import csv
import datetime as dt
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_labels  # noqa: E402

SLUG = "var-sjatte-runsten-bar-en-bjorn"
PLAN = "https://github.com/Precatio/runes/blob/main/analysplaner/2026-11-21-bjornen.md"
RES = "https://github.com/Precatio/runes/blob/main/utdata/bjornen/resultat.md"
D = os.path.join(ROOT, "utdata", "bjornen")
M = json.load(open(os.path.join(D, "matt.json"), encoding="utf-8"))
B4 = json.load(open(os.path.join(D, "b4_shm.json"), encoding="utf-8"))
T2 = {r["modell"]: r for r in csv.DictReader(open(os.path.join(D, "t2.csv"), encoding="utf-8"))}

# ======================================================================================================================
# 1. Siffrorna
# ======================================================================================================================
TOT = M["B3_totalt"]
assert (TOT["stenar"], TOT["björnnamn"], TOT["vargnamn"]) == (2321, 375, 189)
SHARE = round(100 * TOT["björnnamn"] / TOT["stenar"])
assert SHARE == 16  # "var sjätte"
FORMS = dict(M["B3_former"])
assert (FORMS["Bjôrn"], FORMS["Þorbjôrn"], FORMS["Ásbjôrn"]) == (101, 50, 35)
LAND = M["B3_landskap"]
SKOG, MALAR = M["B3_skog"], M["B3_malar"]
assert (round(SKOG["andel"]), round(MALAR["andel"])) == (12, 19)
H, US = T2["huvud"], T2["utan Småland"]
kv = lambda x: f"{float(x):.2f}".replace(".", ",")  # noqa: E731
ke = lambda x: f"{float(x):.2f}"  # noqa: E731
assert (kv(H["kvot"]), kv(H["lag"]), kv(H["hog"])) == ("0,49", "0,29", "0,81")
assert (kv(US["kvot"]), kv(US["lag"]), kv(US["hog"])) == ("1,18", "0,60", "2,32")
N_LIT = M["träffar"]
assert N_LIT == 137
T1 = M["T1"]["huvud"]
assert (T1["fornaldar_n"], T1["islänninga_n"], round(T1["fornaldar_%"])) == (41, 71, 12) and T1["p"] > 0.05
assert (B4["poster"], B4["föremål"], B4["sammanhang"]["grav"]) == (84, 323, 68)
PER = B4["period"]
P_OLD = PER["äldre järnålder–folkvandringstid"] + PER["vendeltid"]
assert P_OLD == 40 and PER["vikingatid (också delvis)"] == 14
GATE = M["grind"]["viktat_procent"]

# ======================================================================================================================
# 2. Citaten
# ======================================================================================================================
K = os.path.join(ROOT, "utdata", "varlden", "korpus")


def flat(t):
    return " ".join(t.split())


Q = {
    "dyr": ("fornaldarsogur/Hrólfs_saga_kraka_ok_kappa_hans.txt", "því at hann sé dýr um daga, en maðr um nætr"),
    "hamr": ("fornaldarsogur/Hrólfs_saga_kraka_ok_kappa_hans.txt", "steypist síðan bjarnarhamrinn yfir hann"),
    "bjorn": ("fornaldarsogur/Hrólfs_saga_kraka_ok_kappa_hans.txt", "björn einn mikill ferr fyrir Hrólfs konungs mönnum"),
    "hrammr": ("fornaldarsogur/Hrólfs_saga_kraka_ok_kappa_hans.txt", "Hann drepr fleiri menn með sínum hrammi en fimm aðrir kappar konungs"),
    "isbjorn": ("islendingasogur/kroka-refs_saga.is.txt", "Það var hvítabjörn fulltíði og vandur ágæta vel"),
    "fylgja": ("fornaldarsogur/Þorsteins_saga_Víkingssonar.txt", "en birnirnir sé fylgjur bræðra hans"),
}
for k, (p, s) in Q.items():
    assert s in flat(open(os.path.join(K, p), encoding="utf-8").read()), k


def q(k):
    return Q[k][1]


# ======================================================================================================================
# 3. Bilderna (Wikimedia Commons; licenser kontrollerade 2026-11-21)
# ======================================================================================================================
SO129 = ("https://thumb.wikimedia.org/wikipedia/commons/thumb/8/83/S%C3%B6_129%2C_Lids_kyrka.JPG/1280px-S%C3%B6_129%2C_Lids_kyrka.JPG",
         "https://commons.wikimedia.org/wiki/File:S%C3%B6_129,_Lids_kyrka.JPG", "Jssfrk", "CC0")
OLAUS = ("https://upload.wikimedia.org/wikipedia/commons/5/5a/Olaus%281555%29-Hist_septentrionalibus-p181-Bjarki%26bear.jpg",
         "https://commons.wikimedia.org/wiki/File:Olaus%281555%29-Hist_septentrionalibus-p181-Bjarki%26bear.jpg", "Olaus Magnus (1555)", "public domain")


# ======================================================================================================================
# 4. Diagrammen (procent)
# ======================================================================================================================
SHOW = ["Uppland", "Västmanland", "Gästrikland", "Södermanland", "Västergötland", "Öland", "Östergötland", "Småland"]
EN = {"Uppland": "Uppland", "Västmanland": "Västmanland", "Gästrikland": "Gästrikland", "Södermanland": "Södermanland",
      "Västergötland": "Västergötland", "Öland": "Öland", "Östergötland": "Östergötland", "Småland": "Småland"}


def chart_names(lang):
    sv = lang == "sv"
    rows = [f":::chart {'Andel runstenar med ett björnnamn, landskap för landskap' if sv else 'Share of runestones with a bear name, province by province'}"]
    for l in SHOW:
        x = LAND[l]
        rows.append(f"{'+' if l in ('Uppland', 'Småland') else ''}{l if sv else EN[l]} | {round(x['andel'])} | {x['björnnamn']} {'av' if sv else 'of'} {x['stenar']}")
    rows.append(f"Landskap med minst 20 runstenar. Hela Sverige: {SHARE} procent har ett björnnamn, {round(100 * TOT['vargnamn'] / TOT['stenar'])} procent ett vargnamn. Diagram: Vitki, ur Samnordisk runtextdatabas."
                if sv else f"Provinces with at least 20 runestones. All of Sweden: {SHARE} per cent have a bear name, {round(100 * TOT['vargnamn'] / TOT['stenar'])} per cent a wolf name. Chart: Vitki, from the Scandinavian Runic-text Database.")
    return "\n".join(rows) + "\n:::"


def chart_graves(lang):
    sv = lang == "sv"
    n = B4["poster"]
    groups = [("äldre järnålder–vendeltid", "Early Iron Age to Vendel Period", P_OLD),
              ("bara ”järnålder” eller ”yngre järnålder”", "only “Iron Age” or “Late Iron Age”", PER["Järnålder"] + PER["Yngre järnålder"]),
              ("vikingatid", "Viking Age", PER["vikingatid (också delvis)"]),
              ("medeltid eller odaterat", "Middle Ages or undated", PER["medeltid"] + PER["Odaterad"])]
    assert sum(g[2] for g in groups) == n
    rows = [f":::chart {'Björnklor och björntänder i Statens historiska museers samlingar, efter period' if sv else 'Bear claws and teeth in the collections of the Swedish History Museums, by period'}"]
    for s, e, k in groups:
        rows.append(f"{'+' if s.startswith('äldre') else ''}{s if sv else e} | {round(100 * k / n)} | {k} {'poster' if sv else 'records'}")
    rows.append(f"{n} poster med {B4['föremål']} föremål, {B4['sammanhang']['grav']} av posterna ur gravar. Brända ben registreras ofta inte art för art, så detta är ett minimum. Diagram: Vitki, ur Statens historiska museer (CC0)."
                if sv else f"{n} records with {B4['föremål']} objects, {B4['sammanhang']['grav']} of the records from graves. Burnt bone is often not registered species by species, so this is a minimum. Chart: Vitki, from the Swedish History Museums (CC0).")
    return "\n".join(rows) + "\n:::"


# ======================================================================================================================
# 5. Texten
# ======================================================================================================================
title = "Var sjätte runsten bär en björn – men i sagorna är den sällsynt"
summary = (f"{TOT['björnnamn']} av {TOT['stenar']:,} svenska runstenar har ett namn med björn i: Björn, Torbjörn, Asbjörn. Det är dubbelt så många som vargnamnen. ".replace(",", " ")
           + "I sagorna är björnen däremot ett ovanligt ord, och björnklorna i gravarna är mest äldre än vikingatiden.")

body = f"""![Sö 129 vid Lids kyrka]({SO129[0]})
Sö 129, inmurad i stigluckan vid Lids kyrka i Södermanland: ”Björn reste denna sten efter Helge, sin broder.” Foto: {SO129[2]}, {SO129[3]}, via [Wikimedia Commons]({SO129[1]}). Översättning efter Samnordisk runtextdatabas.

Stenen vid Lids kyrka har en av de kortaste texter en runsten kan ha: en man som reste en sten efter sin bror. Mannen hette Björn. Han är inte ensam. Bland de {TOT['stenar']:,} svenska runstenarna från vikingatiden har **{TOT['björnnamn']}** ett namn med björnen i sig, ungefär **var sjätte sten**. Det här är den fjärde delen i serien om de nordiska väsendena, och björnen är det väsen som syns mest på stenarna – men inte i texterna om väsen. Den syns i människornas namn.

## Björnarna på stenarna

Det vanligaste namnet är helt enkelt Björn, {FORMS['Bjôrn']} gånger. Sedan kommer sammansättningarna: Torbjörn ({FORMS['Þorbjôrn']}), Asbjörn ({FORMS['Ásbjôrn']}), Vebjörn, Gerbjörn, Igulbjörn, Kättilbjörn, Sigbjörn, Gunnbjörn och Styrbjörn. Vargen, som är seriens nästa väsen, finns på {TOT['vargnamn']} stenar, hälften så många.

{chart_names('sv')}

Man kunde tro att björnnamnen skulle vara vanligast där björnarna levde, i skogsbygderna. Det är de inte. Vi prövade det med en låst plan: i Gästrikland, Hälsingland, Medelpad, Ångermanland, Jämtland, Dalarna, Värmland och Småland har {round(SKOG['andel'])} procent av stenarna ett björnnamn, i Mälardalen {round(MALAR['andel'])} procent. Räknat så att stenar med många namn inte väger för tungt, och så att stenar i samma härad inte räknas som oberoende, är chansen för ett björnnamn ungefär hälften så stor i skogslandskapen (oddskvot {kv(H['kvot'])}, sannolikt mellan {kv(H['lag'])} och {kv(H['hog'])}).

Men den skillnaden bärs av ett enda landskap. Tar man bort Småland, där bara {LAND['Småland']['andel']:.0f} procent av stenarna har ett björnnamn, försvinner den helt (oddskvot {kv(US['kvot'])}, mellan {kv(US['lag'])} och {kv(US['hog'])}). Det säkra resultatet är alltså enklare: björnnamnen följer inte björnarna. De är vanligast i Uppland och Västmanland.

## Björnen i sagorna

I den fornnordiska litteraturen är björnen förvånansvärt sällsynt. Vår ordlista hittade bara {N_LIT} björnar i hela materialet, eddadikterna, Snorre och alla sagor, mot hundratals jättar. Oftast är björnen ett djur som jagas, som dödar får eller som ges bort. På Island fanns inga brunbjörnar. Där var björnen en isbjörn, som kom drivande på isen eller fördes från Grönland. I Króka-Refs saga skickas en sådan som gåva till kung Harald: *{q('isbjorn')}* – ”det var en fullvuxen isbjörn och mycket väl tämjd.”

I fornaldarsagorna kan björnen vara mer än ett djur. Den kan vara en människas fylgja: när Torsten i Þorsteins saga Víkingssonar tyder en dröm, säger han att det stora djuret är fienden Jökuls fylgja, *{q('fylgja')}* – ”och björnarna är hans bröders fylgjor”. Och den kan vara en människa. I Hrólfs saga kraka förtrollas kungasonen Björn av sin styvmor, och *{q('hamr')}* – ”sedan föll björnhamnen över honom”. Han är *{q('dyr')}* – ”ett djur om dagen, men en människa om natten”. Hans älskade heter Bera, ”björnhona”, och deras son är Bödvar Bjarke.

![Bjarke och björnen hos Olaus Magnus, 1555]({OLAUS[0]})
Bjarke dödar ett odjur och låter Hött dricka dess blod, i Olaus Magnus *Historia de gentibus septentrionalibus* (1555). I sagan är odjuret bevingat; Olaus gjorde det till en björn. Träsnitt: {OLAUS[2]}, {OLAUS[3]}, via [Wikimedia Commons]({OLAUS[1]}).

I sagans sista strid ser fienderna att *{q('bjorn')}* – ”en stor björn går framför kung Rolfs män” – och *{q('hrammr')}*: ”han dödar fler män med sin ram än fem av kungens andra kämpar”. Björnen är Bödvar själv, i björnhamn.

Vi ville veta om fornaldarsagorna oftare än islänningasagorna sätter björnen i ett sådant sammanhang, med ham, skepnad eller fylgja. Det gjorde de i {T1['fornaldar_n']} björnar mot {T1['islänninga_n']}: {round(T1['fornaldar_%'])} procent mot ingen. Men skillnaden räcker inte för att vara säker, och två av träffarna visade sig handla om en drakes ham. Björnen som förvandling är en fornaldarsagornas sak, men det är för få björnar för att visa det med siffror.

## Björnen i graven

Långt före runstenarna lades björnar i gravarna. Björnklor och tåben hittas i brandgravar, där den döde troligen bränts på ett björnskinn. I Statens historiska museers samlingar finns {B4['poster']} sådana poster med {B4['föremål']} föremål, nästan alla ur gravar. De flesta är från järnåldern före vikingatiden.

{chart_graves('sv')}

Seden med björnskinnet i graven tycks alltså ha varit på väg bort när runstenarna restes. Det som levde kvar var namnen.

## Det vi inte vet

- **Ett namn är inte en tro.** Björn och -björn var vanliga namnled som ärvdes och kombinerades. Att var sjätte sten bär ett björnnamn säger något om namnskicket, inte säkert något om vad familjerna tänkte om björnen.
- **Gravfynden är ett minimum.** Brända ben artbestäms ofta inte post för post i museets register, och registret gäller Statens historiska museers samlingar, inte alla museer.
- **Sagornas björnar är få.** {N_LIT} träffar räcker för att se var björnen står, men inte för att jämföra säkert.
- **Om metoden.** Ett stickprov av träffarna lästes för hand, uppdelat efter textgrupp, och {GATE} procent var björnar. Felen var bland annat ”björn” som skaldisk omskrivning för ett skepp. Stickprovet bedömdes med Anthropics språkmodell Claude (Claude Opus), och varje citat är kontrollerat mot texten. Reglerna låstes i [en analysplan]({PLAN}), och allt finns i [resultatet]({RES}).

## Läs själv

Leta upp en runsten nära dig och läs namnen. Med en sannolikhet av ungefär en på sex finns en björn där – en Björn, en Torbjörn eller en Asbjörn. Läs sedan Hrólfs saga kraka och se hur björnen blir människa.

:::box Det viktigaste i korthet
- Var sjätte svensk runsten bär ett namn med björnen i sig, dubbelt så ofta som vargen.
- Björnnamnen är vanligast i Mälardalen, inte där björnarna levde. Skillnaden mot skogslandskapen bärs av Småland.
- I sagorna är björnen sällsynt. I fornaldarsagorna kan den vara en fylgja eller en förtrollad människa, som Bödvar Bjarke.
- Björnskinnet i graven var mest en sed från tiden före vikingarna. Det som levde kvar var namnen.
:::

## Källor

Runstenarna: Samnordisk runtextdatabas, version 3.1 (2018), Uppsala universitet. Gravfynden: Statens historiska museer, samlingar.shm.se (metadata CC0), hämtat 2026-11-21. Islänningasagorna: sagadb.org (Sveinbjörn Þórðarson), public domain. Fornaldarsagorna och eddadikterna: heimskringla.no, Guðni Jónssons m.fl. utgåvor; texterna används här bara för räkning och korta citat. Heimskringla: heimskringla.no, Linder & Haggson (1869–72), public domain. Tack till heimskringla.no för texterna. Översättningarna är våra egna utom runstenens. Reglerna och skripten: [analysplanen]({PLAN})."""

title_en = "One runestone in six carries a bear – but in the sagas it is rare"
summary_en = (f"{TOT['björnnamn']} of {TOT['stenar']:,} Swedish runestones have a name with a bear in it: Bjôrn, Þorbjôrn, Ásbjôrn. That is twice as many as the wolf names. "
              "In the sagas, on the other hand, the bear is a rare word, and the bear claws in the graves are mostly older than the Viking Age.")

body_en = f"""![Sö 129 at Lid church]({SO129[0]})
Sö 129, built into the lychgate at Lid church in Södermanland: “Bjôrn raised this stone in memory of Helgi, his brother.” Photo: {SO129[2]}, {SO129[3]}, via [Wikimedia Commons]({SO129[1]}). Translation after the Scandinavian Runic-text Database.

The stone at Lid church has one of the shortest texts a runestone can have: a man who raised a stone for his brother. The man was called Bjôrn. He is not alone. Among the {TOT['stenar']:,} Swedish runestones of the Viking Age, **{TOT['björnnamn']}** have a name with the bear in it, about **one stone in six**. This is the fourth part of the series on the Norse beings, and the bear is the being most often seen on the stones – but not in the texts about beings. It is seen in people's names.

## The bears on the stones

The commonest name is simply Bjôrn, {FORMS['Bjôrn']} times. Then come the compounds: Þorbjôrn ({FORMS['Þorbjôrn']}), Ásbjôrn ({FORMS['Ásbjôrn']}), Vébjôrn, Geirbjôrn, Ígulbjôrn, Ketilbjôrn, Sigbjôrn, Gunnbjôrn and Styrbjôrn. The wolf, the series' next being, is on {TOT['vargnamn']} stones, half as many.

{chart_names('en')}

One might think the bear names would be commonest where the bears lived, in the forest districts. They are not. We tested it under a locked plan: in Gästrikland, Hälsingland, Medelpad, Ångermanland, Jämtland, Dalarna, Värmland and Småland {round(SKOG['andel'])} per cent of the stones have a bear name, in the Lake Mälaren region {round(MALAR['andel'])} per cent. Counted so that stones with many names do not weigh too heavily, and so that stones in the same hundred are not counted as independent, the chance of a bear name is about half as large in the forest provinces (odds ratio {ke(H['kvot'])}, probably between {ke(H['lag'])} and {ke(H['hog'])}).

But that difference rests on a single province. Remove Småland, where only {LAND['Småland']['andel']:.0f} per cent of the stones have a bear name, and it disappears entirely (odds ratio {ke(US['kvot'])}, between {ke(US['lag'])} and {ke(US['hog'])}). The certain result is therefore simpler: the bear names do not follow the bears. They are commonest in Uppland and Västmanland.

## The bear in the sagas

In Old Norse literature the bear is surprisingly rare. Our word list found only {N_LIT} bears in the whole material, the Eddic poems, Snorri and all the sagas, against hundreds of giants. Most often the bear is an animal that is hunted, that kills sheep or that is given away. Iceland had no brown bears. There the bear was a polar bear, which came drifting on the ice or was brought from Greenland. In Króka-Refs saga one is sent as a gift to King Haraldr: *{q('isbjorn')}* – “it was a full-grown polar bear, and very well trained.”

In the legendary sagas the bear can be more than an animal. It can be a person's fylgja: when Þorsteinn in Þorsteins saga Víkingssonar interprets a dream, he says that the great beast is the fylgja of his enemy Jǫkull, *{q('fylgja')}* – “and the bears are the fylgjur of his brothers”. And it can be a human being. In Hrólfs saga kraka the king's son Bjôrn is bewitched by his stepmother, and *{q('hamr')}* – “then the bear's hide fell over him”. He is *{q('dyr')}* – “a beast by day, but a man by night”. His beloved is called Bera, “she-bear”, and their son is Bǫðvarr Bjarki.

![Bjarki and the bear in Olaus Magnus, 1555]({OLAUS[0]})
Bjarki kills a beast and lets Hǫttr drink its blood, in Olaus Magnus's *Historia de gentibus septentrionalibus* (1555). In the saga the beast is winged; Olaus made it a bear. Woodcut: {OLAUS[2]}, {OLAUS[3]}, via [Wikimedia Commons]({OLAUS[1]}).

In the saga's last battle the enemies see that *{q('bjorn')}* – “a great bear goes before King Hrólfr's men” – and *{q('hrammr')}*: “he kills more men with his paw than five of the king's other champions”. The bear is Bǫðvarr himself, in bear shape.

We wanted to know whether the legendary sagas, more often than the sagas of Icelanders, place the bear in such a context, with a hide, a shape or a fylgja. They did in {T1['fornaldar_n']} bears against {T1['islänninga_n']}: {round(T1['fornaldar_%'])} per cent against none. But the difference is not enough to be certain, and two of the hits turned out to concern a dragon's hide. The bear as a transformation belongs to the legendary sagas, but there are too few bears to show it in figures.

## The bear in the grave

Long before the runestones, bears were laid in the graves. Bear claws and toe bones are found in cremation graves, where the dead person was probably burned on a bearskin. In the collections of the Swedish History Museums there are {B4['poster']} such records with {B4['föremål']} objects, almost all from graves. Most are from the Iron Age before the Viking Age.

{chart_graves('en')}

The custom of the bearskin in the grave thus seems to have been on its way out when the runestones were raised. What lived on were the names.

## What we do not know

- **A name is not a belief.** Bjôrn and -bjôrn were common name elements that were inherited and combined. That one stone in six carries a bear name says something about the naming, not with certainty anything about what the families thought of the bear.
- **The grave finds are a minimum.** Burnt bone is often not identified to species record by record in the museum's register, and the register covers the collections of the Swedish History Museums, not all museums.
- **The sagas' bears are few.** {N_LIT} hits are enough to see where the bear stands, but not to compare with certainty.
- **On the method.** A sample of the hits was read by hand, divided by group of texts, and {GATE} per cent were bears. The errors included “bear” as a skaldic circumlocution for a ship. The sample was judged with Anthropic's language model Claude (Claude Opus), and every quotation is checked against the text. The rules were locked in [an analysis plan]({PLAN}), and everything is in [the results]({RES}).

## Read for yourself

Find a runestone near you and read the names. With a probability of about one in six there is a bear there – a Bjôrn, a Þorbjôrn or an Ásbjôrn. Then read Hrólfs saga kraka and see how the bear becomes a man.

:::box The essentials in brief
- One Swedish runestone in six carries a name with the bear in it, twice as often as the wolf.
- The bear names are commonest in the Lake Mälaren region, not where the bears lived. The difference from the forest provinces rests on Småland.
- In the sagas the bear is rare. In the legendary sagas it can be a fylgja or a bewitched human being, like Bǫðvarr Bjarki.
- The bearskin in the grave was mostly a custom from before the Vikings. What lived on were the names.
:::

## Sources

The runestones: Scandinavian Runic-text Database (Samnordisk runtextdatabas), version 3.1 (2018), Uppsala University. The grave finds: the Swedish History Museums, samlingar.shm.se (metadata CC0), retrieved 2026-11-21. The sagas of Icelanders: sagadb.org (Sveinbjörn Þórðarson), public domain. The legendary sagas and the Eddic poems: heimskringla.no, editions by Guðni Jónsson and others; the texts are used here only for counting and short quotations. Heimskringla: heimskringla.no, Linder & Haggson (1869–72), public domain. Thanks to heimskringla.no for the texts. The translations are our own except the runestone's. The rules and the scripts: [the analysis plan]({PLAN})."""

# ======================================================================================================================
# 6. Kontroller och skrivning
# ======================================================================================================================
HOLDBACK = re.compile(r"\bAI\b|signifikan|p-värde|p-value|bootstrap|\bHolm\b", re.I)
labels = ["Forskning", "Eddan", "Geografi"]
assert blog_labels.check(labels) is None, blog_labels.check(labels)
for b, lang in ((body, "sv"), (body_en, "en")):
    assert not HOLDBACK.search(b), (lang, HOLDBACK.search(b).group(0))
    assert not re.search(r"^\|", b, re.M)
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M))
    assert "{" not in b and "}" not in b
    assert b.index("Det viktigaste i korthet" if lang == "sv" else "The essentials in brief") < b.index("## Källor" if lang == "sv" else "## Sources")
    imgs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", b)
    assert len(imgs) == 2 and all(re.match(r"https://(upload|thumb)\.wikimedia\.org/", u) for u in imgs), imgs
    caps = [b.splitlines()[i + 1] for i, ln in enumerate(b.splitlines()) if ln.startswith("![")]
    assert all("Wikimedia Commons" in c and re.search(r"CC BY|CC0|public domain", c) for c in caps), caps
    for m in re.finditer(r":::chart[^\n]*\n(.*?)\n:::", b, re.S):
        assert "Diagram: Vitki" in m.group(1) or "Chart: Vitki" in m.group(1)
        for row in m.group(1).splitlines():
            if "|" in row:
                assert 0 <= float(row.split("|")[1].strip()) <= 100, row
    for k in Q:
        assert q(k) in b, (lang, k)

OUT = {"slug": SLUG, "title": title, "summary": summary, "body": body, "title_en": title_en, "summary_en": summary_en,
       "body_en": body_en, "labels": labels}
wc = lambda x: len(re.sub(r"\]\([^)]*\)", "]", x).split())  # noqa: E731
path = os.path.join(ROOT, "utdata", "blogg", "bjornen.json")
json.dump(OUT, open(path, "w"), ensure_ascii=False, indent=1)
print(path, wc(body), "ord sv,", wc(body_en), "words en")

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
                 "topic": "Eddan och sagorna|väsen|björnen", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id, SLUG)
    blog._forget()
