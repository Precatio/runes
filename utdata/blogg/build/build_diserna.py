"""Artikeln "Fornnordiska väsen – Valkyriorna göts i Birka" – del 6 i serien: nornorna, diserna och valkyriorna.

Bygger på den låsta studien analysplaner/2026-11-21-diserna.md (63420aa); siffrorna ur utdata/diserna/matt.json, t1.csv,
d4_shm.json och kontroll_resultat.json; varje citat kontrolleras mot texten i korpusen.
    ../../../.venv/bin/python build_diserna.py [--write | --update DOC]"""
import csv
import datetime as dt
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_labels  # noqa: E402

SLUG = "valkyriorna-gots-i-birka"
PLAN = "https://github.com/Precatio/runes/blob/main/analysplaner/2026-11-21-diserna.md"
RES = "https://github.com/Precatio/runes/blob/main/utdata/diserna/resultat.md"
D = os.path.join(ROOT, "utdata", "diserna")
M = json.load(open(os.path.join(D, "matt.json"), encoding="utf-8"))
SHM = json.load(open(os.path.join(D, "d4_shm.json"), encoding="utf-8"))
CTRL = json.load(open(os.path.join(D, "kontroll_resultat.json"), encoding="utf-8"))
T1 = {r["modell"]: r for r in csv.DictReader(open(os.path.join(D, "t1.csv"), encoding="utf-8"))}

# ======================================================================================================================
# 1. Siffrorna
# ======================================================================================================================
assert SHM["typ"] == {"hänge": 6, "gjutform": 33, "annat": 1} and SHM["gjutformar_socken"] == {"Adelsö socken": 33}
G = M["D1_grupp"]
BEINGS = ("norn", "valkyria", "dís", "fylgja")
nE, nS = sum(G["Eddan"].get(k, 0) for k in BEINGS), sum(G["sagorna"].get(k, 0) for k in BEINGS)
assert (nE, nS) == (48, 45)
D5 = M["D5"]
assert (D5["kvinnor"], D5["dis_kvinnor"]) == (629, 24)
SV, GO = D5["svealand"], D5["gotaland"]
assert (SV["dis"], SV["kvinnor"], GO["dis"], GO["kvinnor"]) == (22, 509, 1, 97)
H = T1["huvud"]
f2 = lambda x: f"{float(x):.2f}".replace(".", ",")  # noqa: E731
f1 = lambda x: f"{float(x):.1f}".replace(".", ",")  # noqa: E731
assert (f1(H["glmer_kvot"]), f2(H["glmer_lag"]), f1(H["glmer_hog"])) == ("4,5", "0,58", "35,5")
assert float(H["glmer_p"]) > 0.05
assert CTRL["lika"] == 39 and M["träffar"] == 135
assert len(M["D2_kult"]) == 6
NAMES = dict(M["D5"]["dis_namn"])
assert NAMES["Holmdís"] == 6

# ======================================================================================================================
# 2. Citaten
# ======================================================================================================================
K = os.path.join(ROOT, "utdata", "varlden", "korpus")
EDDA = json.load(open(os.path.join(ROOT, "utdata", "Malt", "kallor", "edda.json"), encoding="utf-8"))


def flat(t):
    return " ".join(t.split())


Q = {"adils": ("heimskringla/Ynglinga_saga.txt", "Aðils konungr var at dísablóti, ok reið hesti um dísarsalinn"),
     "njal": ("islendingasogur/brennu-njals_saga.is.txt", "Eg sé margar fylgjur grimmlegar óvina Gunnars")}
EQ = {"nornir": ("Gylfaginning", "Þessar meyjar skapa mönnum aldr. Þær köllum vér nornir."),
      "valkyrjur": ("Gylfaginning", "Þær sendir Óðinn til hverrar orrustu. Þær kjósa feigð á menn ok ráða sigri."),
      "duga": ("Sigrdrífumál", "biðja þá dísir duga"),
      "skjoldunga": ("Sigurðarkviða_in_meiri", "dís skjöldunga")}
for k, (p, s) in Q.items():
    assert s in flat(open(os.path.join(K, p), encoding="utf-8").read()), k
for k, (poem, s) in EQ.items():
    assert s in flat(EDDA[poem]), k


def q(k):
    return Q[k][1] if k in Q else EQ[k][1]


# ======================================================================================================================
# 3. Bilderna (Wikimedia Commons; licenser kontrollerade 2026-11-21)
# ======================================================================================================================
HANGE = ("https://thumb.wikimedia.org/wikipedia/commons/thumb/d/dd/Pendant%2C_valkyrie_%286881051087%29.jpg/1280px-Pendant%2C_valkyrie_%286881051087%29.jpg",
         "https://commons.wikimedia.org/wiki/File:Pendant,_valkyrie_%286881051087%29.jpg", "Statens historiska museer", "CC BY 2.0")
TJANG = ("https://upload.wikimedia.org/wikipedia/commons/a/a7/Bildsten_800_-_1099_i_Tj%C3%A4ngvide%2C_Gotland_%28cropped%2C_Valkyrie_and_Oden%29.jpg",
         "https://commons.wikimedia.org/wiki/File:Bildsten_800_-_1099_i_Tj%C3%A4ngvide,_Gotland_%28cropped,_Valkyrie_and_Oden%29.jpg", "Statens historiska museer", "CC BY 2.5")
U312 = ("https://upload.wikimedia.org/wikipedia/commons/f/ff/Bautil_98_-_U_312.png",
        "https://commons.wikimedia.org/wiki/File:Bautil_98_-_U_312.png", "Johan Göransson, Bautil (1750)", "CC0")


# ======================================================================================================================
# 4. Diagrammen (procent)
# ======================================================================================================================
LAB = {"norn": ("nornor", "norns"), "valkyria": ("valkyrior", "valkyries"), "dís": ("diser", "dísir"), "fylgja": ("fylgjor", "fylgjur")}


def chart_who(lang):
    sv = lang == "sv"
    rows = [f":::chart {'Vilka av de kvinnliga ödesväsendena texterna nämner' if sv else 'Which of the female beings of fate the texts mention'}"]
    for g, gsv, gen, n in (("Eddan", "Eddan (dikterna och Snorre)", "The Edda (poems and Snorri)", nE), ("sagorna", "Sagorna", "The sagas", nS)):
        rows.append(f"# {gsv if sv else gen}")
        for k in BEINGS:
            x = G[g].get(k, 0)
            hl = "+" if (g, k) in (("Eddan", "norn"), ("sagorna", "fylgja")) else ""
            rows.append(f"{hl}{LAB[k][0 if sv else 1]} | {round(100 * x / n)} | {x}")
    rows.append("Andel av träffarna på väsendena; ordet om en vanlig kvinna, kulten och siarna inte medräknade. Alla ställen lästa för hand. Diagram: Vitki."
                if sv else "Share of the hits on the beings; the word for an ordinary woman, the cult and the seeresses not counted. Every place read by hand. Chart: Vitki.")
    return "\n".join(rows) + "\n:::"


def chart_names(lang):
    sv = lang == "sv"
    rows = [f":::chart {'Andel av de namngivna kvinnorna på runstenarna som har ett namn med -dís' if sv else 'Share of the named women on the runestones with a -dís name'}"]
    for l, e in (("Uppland", "Uppland"), ("Södermanland", "Södermanland"), ("Östergötland", "Östergötland"), ("Västergötland", "Västergötland")):
        x = D5["per_landskap"][l]
        rows.append(f"{'+' if l in ('Uppland', 'Södermanland') else ''}{l if sv else e} | {round(100 * x['dis'] / x['kvinnor'], 1)} | {x['dis']} {'av' if sv else 'of'} {x['kvinnor']}")
    rows.append("Landskap med minst 20 namngivna kvinnor. Diagram: Vitki, ur Samnordisk runtextdatabas och Vitkis personmodell."
                if sv else "Provinces with at least 20 named women. Chart: Vitki, from the Scandinavian Runic-text Database and Vitki's people model.")
    return "\n".join(rows) + "\n:::"


# ======================================================================================================================
# 5. Texten
# ======================================================================================================================
title = "Fornnordiska väsen – Valkyriorna göts i Birka"
summary = ("I Birkas svarta jord ligger ett trettiotal lerformar för små kvinnofigurer i silver, som museet kallar valkyrior. "
           "Vi följde nornorna, diserna, valkyriorna och fylgjorna genom Eddan och sagorna – och letade efter dem i Uppsala och i kvinnornas namn på runstenarna.")

body = f"""I Birka, på Björkö i Mälaren, har arkeologerna grävt fram lera med avtryck av en kvinna: en lång kjol, en hårfläta, ibland ett dryckeshorn i handen. Det är gjutformar. I dem göts små hängen i silver. I Statens historiska museers samlingar finns **{SHM['typ']['gjutform']} poster med sådana formar**, och alla kommer från Birka, ur den svarta jorden där staden låg. Museet kallar figurerna *valkyrior*.

Hängena själva hittas i gravar: två på Birka, ett i en hög i Grödinge, två på Öland och ett av silver och guld i Tuna i Alsike, ”Damen i Tuna”. Vilka var de kvinnor som hängena föreställde?

![Valkyriahänge från Birka]({HANGE[0]})
Valkyriahänge i silver ur en grav på Birka (Bj 968). Foto: {HANGE[2]}, {HANGE[3]}, via [Wikimedia Commons]({HANGE[1]}).

Det här är sjätte delen i serien Fornnordiska väsen. Den handlar om de kvinnliga väsen som håller i ödet: nornorna, valkyriorna, diserna och fylgjorna. Vi läste alla {M['träffar']} ställen i den fornnordiska litteraturen där orden står, och klassade dem för hand.

## Fyra sorters kvinnor vid ödets sida

**Nornorna** skapar livet. Hos Snorre heter de Urd, Verdande och Skuld, och de bor vid Urds brunn under världsträdet: *{q('nornir')}* – ”dessa mör skapar människornas liv. Dem kallar vi nornor.”

**Valkyriorna** väljer de döda. *{q('valkyrjur')}* – ”Dem sänder Oden till varje strid. De väljer vilka som ska dö och avgör segern.” I Eddan kan en kungadotter vara valkyria, som Sigrún och Sváfa i Helgedikterna.

**Diserna** är svårast att fånga. De hjälper vid förlossningen – man ska *{q('duga')}*, ”be diserna hjälpa” – och de kan vara ens egna skyddsväsen eller ens fiender. Men i dikterna är *dís* också bara ett fint ord för en kvinna. Brynhild kallas *{q('skjoldunga')}*, ”kungarnas dís”.

**Fylgjorna** följer en människa, ofta i djurskepnad, och syns före döden eller striden. I Njals saga ser en man vid elden: *{q('njal')}* – ”jag ser många grymma fylgjor från Gunnars fiender”.

{chart_who('sv')}

Fördelningen är tydlig. Eddan är nornornas och valkyriornas värld. I sagorna, där människorna lever sina vardagsliv, är det fylgjorna och siarna – de kvinnor som spådde – som tar över. Valkyrian, som är så vanlig i Eddan, nämns bara tre gånger i hela sagamaterialet.

![Valkyria och Oden på Tjängvidestenen]({TJANG[0]})
En kvinna med dryckeshorn möter en ryttare på en åttafotad häst, på bildstenen från Tjängvide på Gotland. Bilden tolkas ofta som en valkyria som tar emot Oden eller en död krigare. Foto: {TJANG[2]}, {TJANG[3]}, via [Wikimedia Commons]({TJANG[1]}).

## Disablotet i Uppsala

Sagorna berättar också om en kult. Sex gånger nämns ett *dísablót*, ett offer till diserna, eller *dísarsalr*, disernas sal. Den mest kända scenen utspelar sig i Uppsala. Ynglinga saga berättar om kung Adils: *{q('adils')}* – ”kung Adils var vid disablotet och red till häst runt disarsalen”. Hästen snavade, kungen föll och slog huvudet mot en sten, och han dog där.

Víga-Glúms saga förlägger ett disablot till vinternätterna på hösten, och Egils saga ett annat till en gård i Norge. Det är sagor skrivna på 1200-talet om tiden kring år 900–1000. De visar vad sagaskrivarna trodde om den gamla tiden, inte hur kulten säkert gick till.

## Diserna i namnen

Om diserna var viktiga i Svealand, borde de kanske synas i kvinnornas namn. Många kvinnonamn bär ordet: Holmdís, Heðindís, Eydís, Freydís, Hjalmdís, och namnet Dís självt. Vi letade efter dem bland alla {D5['kvinnor']} namngivna kvinnor på de svenska runstenarna. {D5['dis_kvinnor']} har ett dísnamn, ungefär en av tjugofem.

![U 312 i Harg, Bautil]({U312[0]})
U 312 i Harg i Uppland: Gunnar lät göra minnesmärket för sin styvdotter Jofurfast, ”Holmdís dotter”. Holmdís är det vanligaste dísnamnet på runstenarna. Träsnitt: {U312[2]}, {U312[3]}, via [Wikimedia Commons]({U312[1]}). Översättning efter Samnordisk runtextdatabas.

{chart_names('sv')}

I Svealand har {SV['dis']} av {SV['kvinnor']} kvinnor ett dísnamn, i Götaland {GO['dis']} av {GO['kvinnor']}. Det ser ut som en skillnad, men den håller inte när man prövar den. Det finns för få namngivna kvinnor på de götiska stenarna. Räknat så att kvinnor i samma bygd inte räknas som oberoende blir kvoten {f1(H['glmer_kvot'])}, men osäkerheten är enorm: den sanna skillnaden kan ligga någonstans mellan {f2(H['glmer_lag'])} och {f1(H['glmer_hog'])} gånger. Det betyder att vi inte vet.

## Det vi inte vet

- **Om figurerna är valkyrior.** Benämningen är museets. Kvinnan med hornet kan vara en valkyria, en disa, en hustru som välkomnar – tolkningarna går isär.
- **Om dísnamnen säger något om tro.** Namnled ärvdes och kombinerades, som Holmdís och Heðindís.
- **Om sagornas disablot speglar 1000-talets kult.** Sagorna skrevs två hundra år senare.
- **Om metoden.** Alla {M['träffar']} ställen klassades för hand med Anthropics språkmodell Claude (Claude Opus). En annan instans av samma modell klassade om 40 av dem utan att se den första klassningen och kom fram till samma sak i 39. Den enda oenigheten var om Sigrúns följe skulle kallas diser eller valkyrior. Varje citat är kontrollerat mot texten. Reglerna låstes i [en analysplan]({PLAN}), och allt finns i [resultatet]({RES}).

:::box Det viktigaste i korthet
- Ett trettiotal gjutformar för de små kvinnofigurerna som kallas valkyrior finns i Statens historiska museer, och alla kommer från Birka. Där tillverkades de.
- Nornor och valkyrior hör till Eddan. I sagornas vardag är det fylgjorna och siarna som syns.
- Ynglinga saga förlägger disablotet till Uppsala, där kung Adils dör vid disarsalen.
- Dísnamn finns på runstenarna, mest i Uppland och Södermanland. Testet: att de är vanligare i Svealand än i Götaland gick inte att visa, eftersom de götiska stenarna har för få namngivna kvinnor.
:::

## Källor

Eddadikterna, Snorres Edda och fornaldarsagorna: heimskringla.no, Guðni Jónssons m.fl. utgåvor; texterna används här bara för räkning och korta citat. Heimskringla: heimskringla.no, Linder & Haggson (1869–72), public domain. Islänningasagorna: sagadb.org (Sveinbjörn Þórðarson), public domain. Tack till heimskringla.no för texterna. Föremålen: Statens historiska museer, samlingar.shm.se (metadata CC0), hämtat 2026-11-21. Runstenarna: Samnordisk runtextdatabas, version 3.1 (2018), Uppsala universitet. Översättningarna är våra egna utom runstenens. Reglerna och skripten: [analysplanen]({PLAN})."""

title_en = "Old Norse beings – The valkyries were cast at Birka"
summary_en = ("In Birka's black earth lie some thirty clay moulds for small silver female figures, which the museum calls valkyries. "
              "We followed the norns, dísir, valkyries and fylgjur through the Edda and the sagas – and looked for them at Uppsala and in the women's names on the runestones.")

body_en = f"""At Birka, on the island of Björkö in Lake Mälaren, archaeologists have dug up clay bearing the impression of a woman: a long dress, a braid of hair, sometimes a drinking horn in her hand. They are casting moulds. In them small silver pendants were cast. In the collections of the Swedish History Museums there are **{SHM['typ']['gjutform']} records of such moulds**, and all come from Birka, from the black earth where the town stood. The museum calls the figures *valkyries*.

The pendants themselves are found in graves: two at Birka, one in a mound at Grödinge, two on Öland, and one of silver and gold at Tuna in Alsike, “the Lady of Tuna”. Who were the women the pendants depicted?

![Valkyrie pendant from Birka]({HANGE[0]})
Silver valkyrie pendant from a grave at Birka (Bj 968). Photo: {HANGE[2]}, {HANGE[3]}, via [Wikimedia Commons]({HANGE[1]}).

This is the sixth part of the series Old Norse beings. It is about the female beings who hold fate: the norns, the valkyries, the dísir and the fylgjur. We read all {M['träffar']} places in Old Norse literature where the words occur, and classified them by hand.

## Four kinds of women at the side of fate

**The norns** shape life. In Snorri they are called Urðr, Verðandi and Skuld, and they live at Urðr's well beneath the world tree: *{q('nornir')}* – “these maidens shape the lives of men. We call them norns.”

**The valkyries** choose the dead. *{q('valkyrjur')}* – “Odin sends them to every battle. They choose who is to die and decide the victory.” In the Edda a king's daughter can be a valkyrie, like Sigrún and Sváfa in the Helgi poems.

**The dísir** are the hardest to catch. They help at childbirth – one is to *{q('duga')}*, “ask the dísir to help” – and they can be one's own guardians or one's enemies. But in the poems *dís* is also just a fine word for a woman. Brynhildr is called *{q('skjoldunga')}*, “the kings' dís”.

**The fylgjur** follow a person, often in animal shape, and are seen before death or battle. In Njáls saga a man by the fire says: *{q('njal')}* – “I see many grim fylgjur of Gunnarr's enemies”.

{chart_who('en')}

The distribution is clear. The Edda is the world of the norns and valkyries. In the sagas, where people live their everyday lives, it is the fylgjur and the seeresses – the women who prophesied – who take over. The valkyrie, so common in the Edda, is named only three times in the whole saga material.

![Valkyrie and Odin on the Tjängvide stone]({TJANG[0]})
A woman with a drinking horn meets a rider on an eight-legged horse, on the picture stone from Tjängvide on Gotland. The image is often read as a valkyrie receiving Odin or a dead warrior. Photo: {TJANG[2]}, {TJANG[3]}, via [Wikimedia Commons]({TJANG[1]}).

## The dísablót at Uppsala

The sagas also tell of a cult. Six times a *dísablót*, a sacrifice to the dísir, or a *dísarsalr*, the hall of the dísir, is mentioned. The best-known scene takes place at Uppsala. Ynglinga saga tells of King Aðils: *{q('adils')}* – “King Aðils was at the dísablót and rode his horse around the hall of the dísir”. The horse stumbled, the king fell and struck his head on a stone, and he died there.

Víga-Glúms saga places a dísablót at the winter nights in autumn, and Egils saga another at a farm in Norway. These are sagas written in the 13th century about the time around the years 900–1000. They show what the saga writers believed about the old days, not how the cult certainly went.

## The dísir in the names

If the dísir were important in Svealand, they might show in women's names. Many women's names carry the word: Holmdís, Heðindís, Eydís, Freydís, Hjalmdís, and the name Dís itself. We looked for them among all {D5['kvinnor']} named women on the Swedish runestones. {D5['dis_kvinnor']} have a dís name, about one in twenty-five.

![U 312 at Harg, Bautil]({U312[0]})
U 312 at Harg in Uppland: Gunnarr had the landmark made for his stepdaughter Jôfurfast, “Holmdís' daughter”. Holmdís is the commonest dís name on the runestones. Woodcut: {U312[2]}, {U312[3]}, via [Wikimedia Commons]({U312[1]}). Translation after the Scandinavian Runic-text Database.

{chart_names('en')}

In Svealand {SV['dis']} of {SV['kvinnor']} women have a dís name, in Götaland {GO['dis']} of {GO['kvinnor']}. It looks like a difference, but it does not hold when tested. There are too few named women on the Götaland stones. Counted so that women in the same district are not treated as independent, the ratio is {float(H['glmer_kvot']):.1f}, but the uncertainty is enormous: the true difference could lie anywhere between {float(H['glmer_lag']):.2f} and {float(H['glmer_hog']):.1f} times. That means we do not know.

## What we do not know

- **Whether the figures are valkyries.** The name is the museum's. The woman with the horn may be a valkyrie, a dís, a wife welcoming – the readings differ.
- **Whether the dís names say anything about belief.** Name elements were inherited and combined, like Holmdís and Heðindís.
- **Whether the sagas' dísablót reflects the cult of the 11th century.** The sagas were written two hundred years later.
- **On the method.** All {M['träffar']} places were classified by hand with Anthropic's language model Claude (Claude Opus). Another instance of the same model reclassified 40 of them without seeing the first classification and reached the same result in 39. The only disagreement was whether Sigrún's band should be called dísir or valkyries. Every quotation is checked against the text. The rules were locked in [an analysis plan]({PLAN}), and everything is in [the results]({RES}).

:::box The essentials in brief
- Some thirty casting moulds for the small female figures called valkyries are in the Swedish History Museums, and all come from Birka. They were made there.
- Norns and valkyries belong to the Edda. In the everyday world of the sagas it is the fylgjur and the seeresses who appear.
- Ynglinga saga places the dísablót at Uppsala, where King Aðils dies at the hall of the dísir.
- Dís names occur on the runestones, mostly in Uppland and Södermanland. The test: that they are commoner in Svealand than in Götaland could not be shown, because the Götaland stones have too few named women.
:::

## Sources

The Eddic poems, Snorri's Edda and the legendary sagas: heimskringla.no, editions by Guðni Jónsson and others; the texts are used here only for counting and short quotations. Heimskringla: heimskringla.no, Linder & Haggson (1869–72), public domain. The sagas of Icelanders: sagadb.org (Sveinbjörn Þórðarson), public domain. Thanks to heimskringla.no for the texts. The objects: the Swedish History Museums, samlingar.shm.se (metadata CC0), retrieved 2026-11-21. The runestones: Scandinavian Runic-text Database (Samnordisk runtextdatabas), version 3.1 (2018), Uppsala University. The translations are our own except the runestone's. The rules and the scripts: [the analysis plan]({PLAN})."""

# ======================================================================================================================
# 6. Kontroller och skrivning
# ======================================================================================================================
HOLDBACK = re.compile(r"\bAI\b|signifikan|p-värde|p-value|bootstrap|\bHolm\b", re.I)
labels = ["Forskning", "Eddan", "Tro och magi", "Kvinnor och barn"]
assert blog_labels.check(labels) is None, blog_labels.check(labels)
assert title.startswith("Fornnordiska väsen – ") and title_en.startswith("Old Norse beings – ")
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
path = os.path.join(ROOT, "utdata", "blogg", "diserna.json")
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
                 "topic": "Eddan och sagorna|väsen|diserna", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id, SLUG)
    blog._forget()
