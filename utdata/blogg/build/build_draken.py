"""Artikeln "Draken var ett skepp" – del 5 i serien Nordiska väsen under vikingatiden: ormen och draken.

Bygger på den låsta studien analysplaner/2026-11-21-ormen-och-draken.md (15ce39f); siffrorna ur utdata/draken/matt.json,
kontroll_resultat.json och o4_sigurd.json; varje citat kontrolleras mot texten i korpusen. Formen: fem frågor.
    ../../../.venv/bin/python build_draken.py [--write | --update DOC]"""
import datetime as dt
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_labels  # noqa: E402

SLUG = "draken-var-ett-skepp"
PLAN = "https://github.com/Precatio/runes/blob/main/analysplaner/2026-11-21-ormen-och-draken.md"
RES = "https://github.com/Precatio/runes/blob/main/utdata/draken/resultat.md"
D = os.path.join(ROOT, "utdata", "draken")
M = json.load(open(os.path.join(D, "matt.json"), encoding="utf-8"))
CTRL = json.load(open(os.path.join(D, "kontroll_resultat.json"), encoding="utf-8"))
SIG = json.load(open(os.path.join(D, "o4_sigurd.json"), encoding="utf-8"))

# ======================================================================================================================
# 1. Siffrorna
# ======================================================================================================================
O1 = M["O1"]
PD = O1["prosa|dreki"]
N_PD = sum(PD.values())
assert (N_PD, PD["skepp"], PD["drake"]) == (273, 212, 57)
SHIP_PC = round(100 * PD["skepp"] / N_PD)
assert SHIP_PC == 78
EO = O1["eddadikter|ormr"]
assert (EO["drake"], O1["eddadikter|dreki"]["drake"]) == (7, 1)
PO = O1["prosa|ormr"]
assert PO["drake"] == 48
T1 = M["T1"]["huvud"]
assert T1.get("obestämt") and (T1["edda_n"], T1["prosa_n"]) == (8, 105)
E_PC = round(100 * 1 / 8)
P_PC = round(100 * PD["drake"] / (PD["drake"] + PO["drake"]))
assert (E_PC, P_PC) == (12, 54)
O3 = M["O3_ormslinga"]
O3T = M["O3_totalt"]
assert (O3T["stilbestämda"], O3T["med_ormhuvud"]) == (1038, 780)
ORM_PC = round(100 * O3T["med_ormhuvud"] / O3T["stilbestämda"])
assert ORM_PC == 75
assert M["O3_text"] == []
assert CTRL["lika"] == 50 and len(SIG["stenar"]) == 5
N_ALL = M["träffar"]
assert N_ALL == 412

# ======================================================================================================================
# 2. Citaten
# ======================================================================================================================
K = os.path.join(ROOT, "utdata", "varlden", "korpus")
EDDA = json.load(open(os.path.join(ROOT, "utdata", "Malt", "kallor", "edda.json"), encoding="utf-8"))


def flat(t):
    return " ".join(t.split())


Q = {
    "ketill": ("fornaldarsogur/Ketils_saga_hængs.txt", "Hann hafði lykkju ok sporð sem ormr, en vængi sem dreki"),
    "vaeringar": ("fornaldarsogur/Völsunga_saga.txt", "hann drap þann mikla dreka, er Væringar kalla Fáfni"),
    "skjoldr": ("fornaldarsogur/Völsunga_saga.txt", "skrifaðr á einn dreki"),
    "ormrinn": ("heimskringla/Saga_Ólafs_Tryggvasonar.txt", "Var þat dreki, ok gerr eptir því sem Ormr"),
    "vaengir": ("heimskringla/Saga_Ólafs_Tryggvasonar.txt", "skyldi þat vera fyrir vængi drekans"),
}
EQ = {"nidhogg": ("Völuspá", "Þar kemr inn dimmi dreki fljúgandi, naðr fránn, neðan frá Niðafjöllum"),
      "fafnir": ("Fáfnismál", "Inn fráni ormr")}
for k, (p, s) in Q.items():
    assert s in flat(open(os.path.join(K, p), encoding="utf-8").read()), k
for k, (poem, s) in EQ.items():
    assert s in flat(EDDA[poem]), k


def q(k):
    return Q[k][1] if k in Q else EQ[k][1]


# ======================================================================================================================
# 3. Bilderna (Wikimedia Commons; licenser kontrollerade 2026-11-21)
# ======================================================================================================================
DRAVLE = ("https://upload.wikimedia.org/wikipedia/commons/f/fb/U1163_Dr%C3%A4vle_-_kmb.16000300012807.jpg",
          "https://commons.wikimedia.org/wiki/File:U1163_Dr%C3%A4vle_-_kmb.16000300012807.jpg", "Bengt A. Lundberg, Riksantikvarieämbetet", "CC BY 2.5")
GOK = ("https://thumb.wikimedia.org/wikipedia/commons/thumb/2/2c/S%C3%B6_327%2C_G%C3%B6k.JPG/1280px-S%C3%B6_327%2C_G%C3%B6k.JPG",
       "https://commons.wikimedia.org/wiki/File:S%C3%B6_327,_G%C3%B6k.JPG", "Berig", "CC BY 2.5")
OCKELBO = ("https://upload.wikimedia.org/wikipedia/commons/0/05/Gs_19%2C_Ockelbo.jpg",
           "https://commons.wikimedia.org/wiki/File:Gs_19,_Ockelbo.jpg", "Berig", "CC BY 2.5")


# ======================================================================================================================
# 4. Diagrammen (procent)
# ======================================================================================================================
def chart_dreki(lang):
    sv = lang == "sv"
    rows = [f":::chart {'Vad ordet dreki betyder i sagornas prosa' if sv else 'What the word dreki means in the prose of the sagas'}"]
    rest = N_PD - PD["skepp"] - PD["drake"]
    for lsv, len_, k, hl in (("ett skepp", "a ship", PD["skepp"], "+"), ("en drake", "a dragon", PD["drake"], ""),
                             ("en bild, kenning eller annat", "an image, kenning or other", rest, "")):
        rows.append(f"{hl}{lsv if sv else len_} | {round(100 * k / N_PD)} | {k} {'av' if sv else 'of'} {N_PD}")
    rows.append("Alla förekomster lästa och klassade för hand. Diagram: Vitki." if sv else "Every occurrence read and classified by hand. Chart: Vitki.")
    return "\n".join(rows) + "\n:::"


def chart_word(lang):
    sv = lang == "sv"
    rows = [f":::chart {'Hur ofta draken kallas dreki i stället för ormr' if sv else 'How often the dragon is called dreki rather than ormr'}"]
    rows.append(f"{'Eddadikterna' if sv else 'The Eddic poems'} | {E_PC} | 1 {'av' if sv else 'of'} 8")
    rows.append(f"+{'Prosan (Snorre och sagorna)' if sv else 'The prose (Snorri and the sagas)'} | {P_PC} | {PD['drake']} {'av' if sv else 'of'} {PD['drake'] + PO['drake']}")
    rows.append("Bara de ställen där ordet avser draken. Eddadikterna har för få drakar för att jämförelsen ska vara prövad. Diagram: Vitki."
                if sv else "Only the places where the word means the dragon. The Eddic poems have too few dragons for the comparison to be tested. Chart: Vitki.")
    return "\n".join(rows) + "\n:::"


LANDS = [("Uppland", "Uppland"), ("Södermanland", "Södermanland"), ("Öland", "Öland"), ("Östergötland", "Östergötland"),
         ("Västergötland", "Västergötland"), ("Småland", "Småland")]


def chart_slinga(lang):
    sv = lang == "sv"
    rows = [f":::chart {'Runstenar där runslingan är en orm med huvud' if sv else 'Runestones where the rune band is a serpent with a head'}"]
    for l, e in LANDS:
        x = O3[l]
        rows.append(f"{'+' if l == 'Uppland' else ''}{l if sv else e} | {round(x['andel'])} | {x['med_ormhuvud']} {'av' if sv else 'of'} {x['stilbestämda']}")
    rows.append("Andel av stenarna med säker stilgrupp. Stilgruppen bestäms av ormen själv, så diagrammet visar var ormstenarna står, inte när de kom. Diagram: Vitki, ur Samnordisk runtextdatabas."
                if sv else "Share of the stones with a certain style group. The style group is decided by the serpent itself, so the chart shows where the serpent stones stand, not when they came. Chart: Vitki, from the Scandinavian Runic-text Database.")
    return "\n".join(rows) + "\n:::"


# ======================================================================================================================
# 5. Texten
# ======================================================================================================================
title = "Fornnordiska väsen – Draken var ett skepp"
summary = (f"I sagornas prosa betyder ordet dreki ett skepp i {SHIP_PC} procent av fallen. I eddadikterna heter draken nästan alltid ormr. "
           f"Och på runstenarna slingrar sig ormen runt texten på tre av fyra stenar, men nämns aldrig. Vi läste alla {N_ALL} ställen.")

body = f"""Draken är det väsen som alla tror sig känna igen. Men vad kallade de draken, var fanns den, och varifrån kom den? Det här är den femte delen i serien om de nordiska väsendena. Vi läste vartenda ställe där orden *dreki* och *ormr* förekommer i den fornnordiska litteraturen, {N_ALL} stycken, och klassade dem för hand. Det gav fem svar.

## 1. Vad hette draken?

I eddadikterna heter den nästan alltid **ormr**, orm. Sigurd tilltalar Fafner i Fáfnismál: *{q('fafnir')}* – ”du glänsande orm”. Midgårdsormen är en *ormr*, och Tor är *orms einbani*, ormens enda baneman. Av de åtta gånger eddadikterna talar om draken är det bara en gång med ordet **dreki**, i slutet av Völuspá:

> {q('nidhogg')}

”Där kommer den mörka draken flygande, den glänsande ormen, nerifrån Nidafjällen.” Det är Nidhögg, och ens där står *naðr*, huggorm, alldeles intill.

I prosan, hos Snorre och i sagorna, kallas draken *dreki* ungefär lika ofta som *ormr*. I Ketils saga hængs står båda orden i samma mening om odjuret som flyger mot Ketil: *{q('ketill')}* – ”den hade slinga och stjärt som en orm, men vingar som en drake”.

{chart_word('sv')}

## 2. Varför var draken ett skepp?

För att *dreki* i sagorna oftast inte är ett djur alls. Av de {N_PD} gångerna ordet står i sagornas prosa betyder det **ett skepp** {PD['skepp']} gånger, {SHIP_PC} procent: ett långskepp med drakhuvud i stäven. Olav Tryggvason kallade ett av sina skepp Ormen, och i Heimskringla förklaras att seglet, när det var hissat, skulle vara *{q('vaengir')}* – ”drakens vingar”. Om Långormen, som byggdes sedan, står det: *{q('ormrinn')}* – ”det var en drake, och byggd efter den som hette Ormen”.

{chart_dreki('sv')}

Den som läser en kungasaga och möter en *dreki* ska alltså först tänka på ett skepp. Djuret finns i fornaldarsagorna och i några islänningasagor: i Gull-Þóris saga ligger drakar i en grotta bakom ett vattenfall, och Tore själv sägs till sist ha blivit en drake på sina guldkistor, i Yngvars saga ruvar en drake på guld vid en flod i öster, och i Bjarnar saga hugger Björn en drake itu bakom vingarna.

## 3. Var finns draken på runstenarna?

Runstenarnas texter nämner varken *dreki* eller *ormr*, inte en enda gång. Men draken är där ändå – runt texten. På **{ORM_PC} procent** av runstenarna med säker stilgrupp är runslingan en orm med huvud. I Uppland gäller det nästan alla.

{chart_slinga('sv')}

Ormstenarna hör alltså främst hemma i Mälardalen. I Östergötland, Västergötland och Småland är slingan oftast ett band utan huvud. Ett förbehåll: stilgruppen bestäms av ormens form, så siffrorna säger var ormen ristades, inte när den kom.

Fem svenska ristningar visar draken från sagan, Fafner som dödas av Sigurd: Ramsundsberget och Göksten i Södermanland, Drävle i Uppland, Årsunda och Ockelbo i Gästrikland. Ingen av dem nämner draken i texten.

![Drävlestenen, U 1163]({DRAVLE[0]})
U 1163 vid Drävle i Uppland. Runslingan är själv en orm, och Sigurd sticker sitt svärd genom den, enligt Rundata med dvärgen Andvare och valkyrian Sigdriva i bilden. Foto: {DRAVLE[2]}, {DRAVLE[3]}, via [Wikimedia Commons]({DRAVLE[1]}).

![Gökstenen, Sö 327]({GOK[0]})
Gökstenen (Sö 327) i Södermanland, med bilder ur Sigurdsberättelsen. Foto: {GOK[2]}, {GOK[3]}, via [Wikimedia Commons]({GOK[1]}).

## 4. Hur kom draken till Norden?

Här måste vi skilja på det vi har mätt och det forskningen säger.

**Det forskningen säger.** Ordet *dreki* är inte nordiskt. Det är ett lån från latinets *draco*, troligen via fornengelska *draca* eller fornsaxiska *drako*. De nordiska orden för det stora krälande odjuret var *ormr* och *linnormr*. Draken som bevingat, eldsprutande djur är alltså ett ord, och kanske en bild, som kom söderifrån.

**Det vi har mätt.**
- Lånordet är nästan frånvarande i eddadikterna. Där är draken en *ormr*, och det enda undantaget är Nidhögg i Völuspá.
- I den skrivna prosan, nedtecknad på 1200- och 1300-talen, är *dreki* lika vanligt som *ormr* för draken. Ordet har dessutom blivit sagornas vanliga ord för ett stort skepp.
- **Testet:** att lånordet tar över hann inte prövas. Eddadikterna har bara åtta drakar, och planen krävde tio, så riktningen är tydlig men inte bevisad.

En detalj i Völsunga saga är värd att notera. Sagan säger att Sigurd dödade *{q('vaeringar')}* – ”den stora draken, som väringarna kallar Fafner”. Hans sköld var *{q('skjoldr')}* – ”målad med en drake”. Väringarna var de nordbor som tjänade i Konstantinopel. Vad sagaförfattaren menade med att det var *de* som använde namnet vet vi inte, men det knyter draken till nordbornas resor söderut.

![Ockelbostenen, Gs 19]({OCKELBO[0]})
Kopia av den förstörda Ockelbostenen (Gs 19) i Gästrikland, med motiv ur Sigurdssagan. Foto: {OCKELBO[2]}, {OCKELBO[3]}, via [Wikimedia Commons]({OCKELBO[1]}).

## 5. Vad vet vi inte?

- **När ormen kom till runstenarna.** Stilgrupperna, och därmed ormen, används för att datera stenarna. Därför kan vi inte använda dem för att säga när ormen kom.
- **Om lånordet tar över.** Eddadikterna har för få drakar för en prövning.
- **Vad ”väringarna” betyder** i Völsunga saga.
- **Om metoden.** Alla {N_ALL} ställen klassades för hand med Anthropics språkmodell Claude (Claude Opus). En annan instans av samma modell klassade om 50 slumpade ställen utan att se den första klassningen och kom fram till samma sak i alla 50. Varje citat är kontrollerat mot texten. Reglerna låstes i [en analysplan]({PLAN}), och allt finns i [resultatet]({RES}).

:::box Det viktigaste i korthet
- I sagornas prosa betyder *dreki* oftast ett skepp, {SHIP_PC} procent av gångerna. Draken som djur är det mindre vanliga.
- I eddadikterna heter draken nästan alltid *ormr*. Ordet *dreki*, ett lån från latinet, finns där bara en gång.
- Testet: att lånordet tar över hann inte prövas. Eddadikterna har bara åtta drakar, och planen krävde tio, så riktningen är tydlig men inte bevisad.
- På runstenarna nämns draken aldrig i texten, men på tre av fyra stenar är runslingan själv en orm.
- Sigurd och Fafner finns i bild på fem svenska ristningar, men inte i någon runtext.
:::

## Källor

Eddadikterna, Snorres Edda, fornaldarsagorna och samtidssagorna: heimskringla.no, Guðni Jónssons m.fl. utgåvor; texterna används här bara för räkning och korta citat. Heimskringla: heimskringla.no, Linder & Haggson (1869–72), public domain. Islänningasagorna: sagadb.org (Sveinbjörn Þórðarson), public domain. Tack till heimskringla.no för texterna. Runstenarna: Samnordisk runtextdatabas, version 3.1 (2018), Uppsala universitet. Översättningarna är våra egna. Reglerna och skripten: [analysplanen]({PLAN})."""

title_en = "Old Norse beings – The dragon was a ship"
summary_en = (f"In the prose of the sagas the word dreki means a ship in {SHIP_PC} per cent of cases. In the Eddic poems the dragon is nearly always ormr. "
              f"And on the runestones the serpent winds around the text on three stones in four, but is never named. We read all {N_ALL} places.")

body_en = f"""The dragon is the being everyone thinks they recognise. But what did they call the dragon, where was it, and where did it come from? This is the fifth part of the series on the Norse beings. We read every single place where the words *dreki* and *ormr* occur in Old Norse literature, {N_ALL} of them, and classified them by hand. That gave five answers.

## 1. What was the dragon called?

In the Eddic poems it is nearly always **ormr**, serpent. Sigurðr addresses Fáfnir in Fáfnismál: *{q('fafnir')}* – “you gleaming serpent”. The Midgard Serpent is an *ormr*, and Thor is *orms einbani*, the serpent's sole slayer. Of the eight times the Eddic poems speak of the dragon, only once is it with the word **dreki**, at the end of Völuspá:

> {q('nidhogg')}

“There comes the dark dragon flying, the gleaming serpent, up from Niðafjöll.” It is Níðhöggr, and even there *naðr*, adder, stands right beside it.

In the prose, in Snorri and the sagas, the dragon is called *dreki* about as often as *ormr*. In Ketils saga hængs both words stand in the same sentence about the beast flying at Ketill: *{q('ketill')}* – “it had coils and a tail like a serpent, but wings like a dragon”.

{chart_word('en')}

## 2. Why was the dragon a ship?

Because *dreki* in the sagas is usually not an animal at all. Of the {N_PD} times the word stands in the prose of the sagas, it means **a ship** {PD['skepp']} times, {SHIP_PC} per cent: a longship with a dragon's head on the prow. Óláfr Tryggvason called one of his ships the Serpent, and Heimskringla explains that the sail, when hoisted, was to be *{q('vaengir')}* – “the dragon's wings”. Of the Long Serpent, built later, it says: *{q('ormrinn')}* – “it was a dragon, and built after the one called the Serpent”.

{chart_dreki('en')}

Anyone reading a kings' saga who meets a *dreki* should therefore think first of a ship. The animal is found in the legendary sagas and in a few sagas of Icelanders: in Gull-Þóris saga dragons lie in a cave behind a waterfall, and Þórir himself is said in the end to have become a dragon on his chests of gold, in Yngvars saga a dragon broods on gold by a river in the east, and in Bjarnar saga Björn cuts a dragon in two behind the wings.

## 3. Where is the dragon on the runestones?

The runestone texts mention neither *dreki* nor *ormr*, not once. But the dragon is there all the same – around the text. On **{ORM_PC} per cent** of the runestones with a certain style group, the rune band is a serpent with a head. In Uppland that is true of nearly all of them.

{chart_slinga('en')}

The serpent stones thus belong mainly to the Lake Mälaren region. In Östergötland, Västergötland and Småland the band is usually a band without a head. A caveat: the style group is decided by the serpent's form, so the figures say where the serpent was carved, not when it came.

Five Swedish carvings show the dragon of the saga, Fáfnir slain by Sigurðr: Ramsundsberget and the Gök stone in Södermanland, Drävle in Uppland, Årsunda and Ockelbo in Gästrikland. None of them names the dragon in its text.

![The Drävle stone, U 1163]({DRAVLE[0]})
U 1163 at Drävle in Uppland. The rune band is itself a serpent, and Sigurðr drives his sword through it, according to Rundata with the dwarf Andvari and the valkyrie Sigrdrífa in the picture. Photo: {DRAVLE[2]}, {DRAVLE[3]}, via [Wikimedia Commons]({DRAVLE[1]}).

![The Gök stone, Sö 327]({GOK[0]})
The Gök stone (Sö 327) in Södermanland, with pictures from the Sigurðr story. Photo: {GOK[2]}, {GOK[3]}, via [Wikimedia Commons]({GOK[1]}).

## 4. How did the dragon come to the North?

Here we must separate what we have measured from what research says.

**What research says.** The word *dreki* is not Norse. It is a loan from Latin *draco*, probably via Old English *draca* or Old Saxon *drako*. The Norse words for the great crawling beast were *ormr* and *linnormr*. The dragon as a winged, fire-breathing beast is thus a word, and perhaps an image, that came from the south.

**What we have measured.**
- The loanword is almost absent from the Eddic poems. There the dragon is an *ormr*, and the only exception is Níðhöggr in Völuspá.
- In the written prose, set down in the 13th and 14th centuries, *dreki* is as common as *ormr* for the dragon. The word has also become the sagas' ordinary word for a great ship.
- **The test:** whether the loanword takes over could not be tested. The Eddic poems have only eight dragons, and the plan required ten, so the direction is clear but not proven.

One detail in Völsunga saga is worth noting. The saga says that Sigurðr killed *{q('vaeringar')}* – “the great dragon that the Varangians call Fáfnir”. His shield was *{q('skjoldr')}* – “painted with a dragon”. The Varangians were the Norsemen who served in Constantinople. What the saga writer meant by saying it was *they* who used the name we do not know, but it ties the dragon to the Norsemen's journeys south.

![The Ockelbo stone, Gs 19]({OCKELBO[0]})
Copy of the destroyed Ockelbo stone (Gs 19) in Gästrikland, with motifs from the Sigurðr saga. Photo: {OCKELBO[2]}, {OCKELBO[3]}, via [Wikimedia Commons]({OCKELBO[1]}).

## 5. What do we not know?

- **When the serpent came to the runestones.** The style groups, and therefore the serpent, are used to date the stones. So we cannot use them to say when the serpent came.
- **Whether the loanword takes over.** The Eddic poems have too few dragons for a test.
- **What “the Varangians” means** in Völsunga saga.
- **On the method.** All {N_ALL} places were classified by hand with Anthropic's language model Claude (Claude Opus). Another instance of the same model reclassified 50 random places without seeing the first classification and reached the same result in all 50. Every quotation is checked against the text. The rules were locked in [an analysis plan]({PLAN}), and everything is in [the results]({RES}).

:::box The essentials in brief
- In the prose of the sagas *dreki* usually means a ship, {SHIP_PC} per cent of the time. The dragon as an animal is the less common meaning.
- In the Eddic poems the dragon is nearly always *ormr*. The word *dreki*, a loan from Latin, occurs there only once.
- The test: whether the loanword takes over could not be tested. The Eddic poems have only eight dragons, and the plan required ten, so the direction is clear but not proven.
- On the runestones the dragon is never named in the text, but on three stones in four the rune band itself is a serpent.
- Sigurðr and Fáfnir appear in pictures on five Swedish carvings, but in no runic text.
:::

## Sources

The Eddic poems, Snorri's Edda, the legendary sagas and the contemporary sagas: heimskringla.no, editions by Guðni Jónsson and others; the texts are used here only for counting and short quotations. Heimskringla: heimskringla.no, Linder & Haggson (1869–72), public domain. The sagas of Icelanders: sagadb.org (Sveinbjörn Þórðarson), public domain. Thanks to heimskringla.no for the texts. The runestones: Scandinavian Runic-text Database (Samnordisk runtextdatabas), version 3.1 (2018), Uppsala University. The translations are our own. The rules and the scripts: [the analysis plan]({PLAN})."""

# ======================================================================================================================
# 6. Kontroller och skrivning
# ======================================================================================================================
HOLDBACK = re.compile(r"\bAI\b|signifikan|p-värde|p-value|bootstrap|\bHolm\b", re.I)
labels = ["Forskning", "Eddan", "Datering och stil"]
assert blog_labels.check(labels) is None, blog_labels.check(labels)
for b, lang in ((body, "sv"), (body_en, "en")):
    assert not HOLDBACK.search(b), (lang, HOLDBACK.search(b).group(0))
    assert not re.search(r"^\|", b, re.M)
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M))
    assert "{" not in b and "}" not in b
    assert b.index("Det viktigaste i korthet" if lang == "sv" else "The essentials in brief") < b.index("## Källor" if lang == "sv" else "## Sources")
    imgs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", b)
    assert len(imgs) == 3 and all(re.match(r"https://(upload|thumb)\.wikimedia\.org/", u) for u in imgs), imgs
    caps = [b.splitlines()[i + 1] for i, ln in enumerate(b.splitlines()) if ln.startswith("![")]
    assert all("Wikimedia Commons" in c and re.search(r"CC BY|CC0|public domain", c) for c in caps), caps
    for m in re.finditer(r":::chart[^\n]*\n(.*?)\n:::", b, re.S):
        assert "Diagram: Vitki" in m.group(1) or "Chart: Vitki" in m.group(1)
        for row in m.group(1).splitlines():
            if "|" in row:
                assert 0 <= float(row.split("|")[1].strip()) <= 100, row
    for k in list(Q) + list(EQ):
        assert q(k) in b, (lang, k)

OUT = {"slug": SLUG, "title": title, "summary": summary, "body": body, "title_en": title_en, "summary_en": summary_en,
       "body_en": body_en, "labels": labels}
wc = lambda x: len(re.sub(r"\]\([^)]*\)", "]", x).split())  # noqa: E731
path = os.path.join(ROOT, "utdata", "blogg", "draken.json")
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
                 "topic": "Eddan och sagorna|väsen|draken", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id, SLUG)
    blog._forget()
