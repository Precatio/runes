"""Artikeln "Fornnordiska väsen – De döda som kom hem" – del 8 i serien: de döda som går igen.

Bygger på den låsta studien analysplaner/2026-11-23-de-doda-som-gar-igen.md (d6a533a); siffrorna ur utdata/de_doda/matt.json
och kontroll_resultat.json; varje citat kontrolleras mot texten i korpusen.
    ../../../.venv/bin/python build_de_doda.py [--write | --update DOC]"""
import datetime as dt
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_labels  # noqa: E402

SLUG = "de-doda-som-kom-hem"
PLAN = "https://github.com/Precatio/runes/blob/main/analysplaner/2026-11-23-de-doda-som-gar-igen.md"
RES = "https://github.com/Precatio/runes/blob/main/utdata/de_doda/resultat.md"
D = os.path.join(ROOT, "utdata", "de_doda")
M = json.load(open(os.path.join(D, "matt.json"), encoding="utf-8"))
CTRL = json.load(open(os.path.join(D, "kontroll_resultat.json"), encoding="utf-8"))

# ======================================================================================================================
# 1. Siffrorna
# ======================================================================================================================
V1 = M["V1"]
H = M["T1"]["huvud"]
assert M["träffar"] == 383 and H["håller"]
assert (H["forn_n"], H["isl_n"], H["forn_%"], H["isl_%"]) == (54, 78, 98.1, 53.8)
assert (V1["forn"]["högbo"], V1["forn"]["gengångare"], V1["isl"]["högbo"], V1["isl"]["gengångare"]) == (53, 1, 42, 36)
assert CTRL["lika"] == 39
pc = lambda a, n: round(100 * a / n)  # noqa: E731

# ======================================================================================================================
# 2. Citaten
# ======================================================================================================================
K = os.path.join(ROOT, "utdata", "varlden", "korpus")
EDDA = json.load(open(os.path.join(ROOT, "utdata", "Malt", "kallor", "edda.json"), encoding="utf-8"))
RD = {r["signum"]: r for r in json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["inscriptions"]}


def flat(t):
    return " ".join(t.split())


EY = "islendingasogur/eyrbyggja_saga.is.txt"
Q = {"rad": (EY, "sækja þá menn alla í dyradómi er aftur gengu"),
     "setid": (EY, "Setið er nú meðan sætt er"),
     "vert": (EY, "Verið er nú meðan vært er"),
     "flyjum": (EY, "Fátt hygg eg hér friða enda flýjum nú allir"),
     "tokust": (EY, "eftir það tókust af allar afturgöngur að Fróðá og reimleikar"),
     "hrappr_dyr": ("islendingasogur/laxdaela_saga.is.txt", "skal mig niður setja standanda þar í dyrunum"),
     "hrappr": ("islendingasogur/laxdaela_saga.is.txt", "hann gekk mjög aftur"),
     "glamr": ("islendingasogur/grettis_saga.is.txt", "þessi augu séu þér jafnan fyrir sjónum sem eg ber eftir"),
     "gunnar": ("islendingasogur/brennu-njals_saga.is.txt", "Þeim þótti Gunnar vera kátur og kveða í hauginum"),
     "thrainn": ("fornaldarsogur/Hrómundar_saga_Gripssonar.txt", "Lengi hefi ek lifat í haugi mínum"),
     "hreggvidr": ("fornaldarsogur/Göngu-Hrólfs_saga.txt", "ek byggi haug þenna með köppum mínum")}
EQ = {"vaki": ("Hervararkviða", "Vaki þú, Angantýr, vekr þik Hervör")}
for k, (p, s) in Q.items():
    assert s in flat(open(os.path.join(K, p), encoding="utf-8").read()), k
for k, (poem, s) in EQ.items():
    assert s in flat(EDDA[poem]), k
KARLEVI = "Þrúðar draugr í þessu haugi"
assert KARLEVI.replace("Þ", '"Þ', 1) in RD["Öl 1"]["normalization_ows"]
assert "haug gera eptir" in RD["U 269"]["normalization_ows"] and "haug þenna" in RD["U 135"]["normalization_ows"]


def q(k):
    return Q[k][1] if k in Q else EQ[k][1]


# ======================================================================================================================
# 3. Bilderna (Wikimedia Commons; licenser kontrollerade 2026-11-23)
# ======================================================================================================================
HERVOR = ("https://upload.wikimedia.org/wikipedia/commons/2/21/Christian-gottlieb-kratzenstein-stub-hervor-henter-sv%C3%A6rdet-hos-angartyr.jpg",
          "https://commons.wikimedia.org/wiki/File:Christian-gottlieb-kratzenstein-stub-hervor-henter-sv%C3%A6rdet-hos-angartyr.jpg",
          "Christian Gottlieb Kratzenstein-Stub (1783–1816)", "public domain")
HOG = ("https://upload.wikimedia.org/wikipedia/commons/d/d8/Uppsala_h%C3%B6gar_-_KMB_-_16000300020892.jpg",
       "https://commons.wikimedia.org/wiki/File:Uppsala_h%C3%B6gar_-_KMB_-_16000300020892.jpg",
       "Jörgen Runeby, Riksantikvarieämbetet", "CC BY 2.5")
KARL = ("https://upload.wikimedia.org/wikipedia/commons/4/4f/Bautil_1071_-_%C3%96l_1.png",
        "https://commons.wikimedia.org/wiki/File:Bautil_1071_-_%C3%96l_1.png", "Johan Göransson, Bautil (1750)", "CC0")


# ======================================================================================================================
# 4. Diagrammet (procent)
# ======================================================================================================================
def chart(lang):
    sv = lang == "sv"
    rows = [f":::chart {'Var de döda möts: i högen eller hemma bland de levande' if sv else 'Where the dead are met: in the mound or at home among the living'}"]
    for g, gsv, gen in (("forn", "Fornaldarsagorna", "The legendary sagas"), ("isl", "Islänningasagorna", "The sagas of Icelanders")):
        n = V1[g]["högbo"] + V1[g]["gengångare"]
        rows.append(f"# {gsv if sv else gen} ({n} {'döda som gör något' if sv else 'active dead'})")
        rows.append(f"{'+' if g == 'forn' else ''}{'i högen' if sv else 'in the mound'} | {pc(V1[g]['högbo'], n)} | {V1[g]['högbo']}")
        rows.append(f"{'+' if g == 'isl' else ''}{'hemma bland de levande' if sv else 'at home among the living'} | {pc(V1[g]['gengångare'], n)} | {V1[g]['gengångare']}")
    rows.append("Sagornas prosa. Alla ställen lästa för hand. Diagram: Vitki." if sv
                else "The prose of the sagas. Every place read by hand. Chart: Vitki.")
    return "\n".join(rows) + "\n:::"


# ======================================================================================================================
# 5. Texten
# ======================================================================================================================
title = "Fornnordiska väsen – De döda som kom hem"
summary = ("På gården Fróðá på Island satt de döda vid elden varje kväll, tills de levande stämde dem inför rätta. "
           "Vi läste alla ställen där de döda går igen i den fornnordiska litteraturen – och fann att de bara kommer hem i islänningasagorna.")

body = f"""Det är vinter på gården Fróðá på Snæfellsnes, strax efter år 1000. Först dör en fåraherde, och sedan börjar han gå igen. Han kastar en man mot dörren så att mannen dör av det, och den döde följer den döde. Husbonden Þóroddr drunknar med sina män på väg hem med torkad fisk. Från begravningsölet och framåt kommer de in varje kväll, dyblöta, och sätter sig vid långelden. Av trettio människor på gården dör arton under vintern, och fem flyr.

Till slut rider husets son Kjartan till sin morbror Snorre gode för att få råd. Snorre säger åt honum att *{q('rad')}* – ”stämma alla de som gick igen inför en dörrdomstol”.

Så sker. Vid dörren sätts en domstol, och de döda stäms en efter en, som vid tinget. När domen faller över Þórir viðleggr reser han sig och säger *{q('setid')}* – ”man har suttit så länge det gick att sitta” – och går ut. Hans hustru Þorgríma, som kallades trollkunnig, säger *{q('vert')}* – ”man har stannat så länge det gick att stanna”. Sist döms husbonden Þóroddr: *{q('flyjum')}* – ”här är inte mycket frid, tror jag. Nu flyr vi alla.” Prästen bär vigvatten genom husen, och *{q('tokust')}* – ”därefter upphörde alla gengångare och spökerier på Fróðá”.

Det här är åttonde delen i serien Fornnordiska väsen, och den handlar om de döda som går igen. Vi läste alla {M['träffar']} ställen i den fornnordiska litteraturen där orden för den gående döde står – *draugr*, *haugbúi*, *afturganga*, ”gå igen” – och alla ställen där det står *haugr*, gravhög. Varje ställe sorterades för hand: gör den döde något, och i så fall var?

## Två sorters döda

{chart('sv')}

Svaret beror på vilken sorts saga man läser. I fornaldarsagorna, äventyren om forntidens hjältar, möter man nästan alltid de döda i högen: {V1['forn']['högbo']} av {H['forn_n']} gånger. Den enda som går igen ute bland de levande är en hel här, som reser sig på slagfältet i Hrólfs saga kraka.

I islänningasagorna, som berättar om släkterna på Island, är det annorlunda. Ungefär hälften av de döda som gör något kommer hem: till gården, till dörren, till elden. Skillnaden är för stor för att vara en slump, också när man tar hänsyn till att några långa episoder står för många av ställena.

## Hemma på gården

Islänningasagornas döda är grannar som inte vill gå. Hrapp i Laxdæla saga är elak redan när han lever. När han är döende vill han bli begravd i köksdörren, stående: *{q('hrappr_dyr')}* – ”ni ska ställa ner mig stående där i dörren”, så att han kan hålla bättre uppsikt över huset. Det går som han vill. *{q('hrappr')}* – ”han gick mycket igen”, och han dödade det mesta av sitt eget husfolk.

Den mest kända är Glámr i Grettis saga, en fåraherde från Sverige som dör ute i snön på julafton och sedan rider på husets tak om nätterna. Grettir brottas med honom i månskenet och vinner, men innan Grettir hugger av honom huvudet lägger Glámr en förbannelse på honom: *{q('glamr')}* – ”att dessa ögon alltid ska stå framför dig, som jag har”. Grettir kan aldrig mer vara ensam i mörkret.

Gengångarna går igen där människorna bor. När vi läste dem fann vi dem på Island, på Grönland och på Färöarna, och en enda gång i Norge.

## Inne i högen

I fornaldarsagorna och i Eddan är de döda kvar i högen, och den levande måste gå dit. På ön Samsø står Hervör vid sin döde fars hög om natten, mellan gravbål som brinner, och väcker honom: *{q('vaki')}* – ”vakna, Angantýr, Hervör väcker dig”. Hon vill ha svärdet Tyrfing, och till sist ger han henne det.

![Hervör vid Angantýrs hög]({HERVOR[0]})
Hervör hämtar svärdet hos den döde Angantýr. Målning: {HERVOR[2]}, {HERVOR[3]}, via [Wikimedia Commons]({HERVOR[1]}).

Ofta är högen en skattkammare, och den döde sitter på en stol och vaktar guldet. I Hrómundar saga bryter sig Hrómund in i högen där kungen och bärsärken Þráinn sitter. Han får brottas med den döde i mörkret, och den döde säger: *{q('thrainn')}* – ”länge har jag levt i min hög”. I Göngu-Hrólfs saga möter Hrólf den döde kungen Hreggviðr vid hans hög: *{q('hreggvidr')}* – ”jag bebor den här högen med mina kämpar”.

![Högar i Gamla Uppsala]({HOG[0]})
En av högarna i Gamla Uppsala. I sagorna kunde den döde bo kvar i högen, och den som bröt sig in fick ta striden. Foto: {HOG[2]}, {HOG[3]}, via [Wikimedia Commons]({HOG[1]}).

Islänningasagorna har också högbor, på {V1['isl']['högbo']} ställen. Men när vi läste dem bodde nästan alla utomlands, i Norge eller i Helluland långt västerut. Sagornas islänningar fick resa för att möta en högbo. Den enda högbon hemma på Island är Gunnar på Hlíðarendi i Njals saga. Han är inte farlig. En kväll ser en fåraherde och en piga, som driver fåren förbi högen, att *{q('gunnar')}* – ”Gunnar verkade glad och kvad i högen”. Var de döda bor i islänningasagorna har vi inte prövat. Det är en iakttagelse från läsningen.

## Runstenarna

Runstenarna talar aldrig om döda som går igen. Tre stenar nämner en hög. På U 269 i Uppland lät Illugi resa stenar och göra en hög efter sin bror Björn. På U 135 gjorde sönerna en bro och en hög efter sin far.

![Karlevistenen, Öl 1]({KARL[0]})
Karlevistenen (Öl 1) på Öland: ”Dold ligger i denna hög …”. Träsnitt: {KARL[2]}, {KARL[3]}, via [Wikimedia Commons]({KARL[1]}).

Den tredje är Karlevistenen på Öland, rest över dansken Sibbi. Där står det enda substantivet *draugr* på någon runsten: *{KARLEVI}*. Men här betyder ordet inte gengångare. *Þrúðar draugr*, ”Þrúðs träd”, är en skaldisk omskrivning för en krigare. Skaldernas ord för en krigare och sagornas ord för den döde som går igen ser likadana ut, men de används på helt olika sätt.

## Det vi inte vet

- **Om vikingarna trodde så här.** Sagorna skrevs på 1200- och 1300-talen. Skillnaden visar två sätt att berätta: äventyret i högen och oron hemma på gården.
- **Om islänningarna var räddare för sina döda.** Gengångarna kan lika gärna vara ett berättargrepp, en spänning i sagan, som en tro.
- **Varför det blev så.** Kanske för att islänningarna inte hade några högar med gamla kungar att bryta sig in i. Det har vi inte prövat.
- **Om metoden.** Alla {M['träffar']} ställen klassades för hand med Anthropics språkmodell Claude (Claude Opus). En annan instans av samma modell klassade om 40 av dem utan att se den första klassningen och kom fram till samma sak i {CTRL['lika']}. Den enda oenigheten gällde en skaldisk omskrivning. Varje citat är kontrollerat mot texten. Reglerna låstes i [en analysplan]({PLAN}), och allt finns i [resultatet]({RES}).

:::box Det viktigaste i korthet
- I fornaldarsagorna möter man de döda i högen, i {pc(V1['forn']['högbo'], H['forn_n'])} procent av fallen.
- I islänningasagorna kommer ungefär hälften av de döda hem, till gården, dörren och elden.
- Testet: att fornaldarsagornas döda oftare finns i högen än islänningasagornas höll.
- På Fróðá stämdes de döda inför en dörrdomstol, och de gick en efter en.
- Islänningasagornas högbor bor nästan alla utomlands. Den ende på Island är Gunnar, som sjunger glad i sin hög.
- Runstenarna talar aldrig om döda som går igen. Det enda *draugr* på en runsten betyder krigare.
:::

## Källor

Eddadikterna, Snorres Edda och fornaldarsagorna: heimskringla.no, Guðni Jónssons m.fl. utgåvor; texterna används här bara för räkning och korta citat. Heimskringla: heimskringla.no, Linder & Haggson (1869–72), public domain. Islänningasagorna: sagadb.org (Sveinbjörn Þórðarson), public domain. Tack till heimskringla.no för texterna. Runstenarna: Samnordisk runtextdatabas, version 3.1 (2018), Uppsala universitet. Översättningarna är våra egna. Reglerna och skripten: [analysplanen]({PLAN})."""

title_en = "Old Norse beings – The dead who came home"
summary_en = ("At the farm of Fróðá in Iceland the dead sat by the fire every evening, until the living took them to court. "
              "We read every place where the dead walk again in Old Norse literature – and found that they come home only in the sagas of Icelanders.")

body_en = f"""It is winter at the farm of Fróðá on Snæfellsnes, shortly after the year 1000. First a shepherd dies, and then he begins to walk again. He throws a man against the door so that the man dies of it, and the dead follow the dead. The master of the house, Þóroddr, drowns with his men on the way home with dried fish. From the funeral ale onwards they come in every evening, soaking wet, and sit down by the long fire. Of thirty people on the farm eighteen die during the winter, and five flee.

At last the son of the house, Kjartan, rides to his mother's brother Snorri goði for advice. Snorri tells him to *{q('rad')}* – “summon all those who walked again before a door court”.

So it is done. At the door a court is set, and the dead are summoned one by one, as at the assembly. When judgement falls on Þórir viðleggr he rises and says *{q('setid')}* – “we have sat as long as there was sitting to be had” – and goes out. His wife Þorgríma, who was called skilled in magic, says *{q('vert')}* – “we have stayed as long as there was staying to be had”. Last the master Þóroddr is judged: *{q('flyjum')}* – “little peace here, I think. Now we all flee.” The priest carries holy water through the houses, and *{q('tokust')}* – “after that all the revenants and hauntings at Fróðá ceased”.

This is the eighth part of the series Old Norse beings, and it is about the dead who walk again. We read all {M['träffar']} places in Old Norse literature where the words for the walking dead occur – *draugr*, *haugbúi*, *afturganga*, “walk again” – and every place with *haugr*, burial mound. Each place was sorted by hand: does the dead do something, and if so, where?

## Two kinds of dead

{chart('en')}

The answer depends on which kind of saga you read. In the legendary sagas, the adventures of the heroes of old, you nearly always meet the dead in the mound: {V1['forn']['högbo']} of {H['forn_n']} times. The only ones who walk again out among the living are a whole army, rising on the battlefield in Hrólfs saga kraka.

In the sagas of Icelanders, which tell of the families of Iceland, it is different. About half of the dead who do something come home: to the farm, to the door, to the fire. The difference is too large to be chance, even when allowing for a few long episodes accounting for many of the places.

## At home on the farm

The dead of the sagas of Icelanders are neighbours who will not leave. Hrappr in Laxdæla saga is wicked while still alive. When he is dying he wants to be buried in the kitchen door, standing: *{q('hrappr_dyr')}* – “you shall set me down standing there in the doorway”, so that he can keep a better watch over the house. It goes as he wishes. *{q('hrappr')}* – “he walked again a great deal”, and he killed most of his own household.

The best known is Glámr in Grettis saga, a shepherd from Sweden who dies out in the snow on Christmas Eve and then rides the roof of the house at night. Grettir wrestles him in the moonlight and wins, but before Grettir cuts off his head Glámr lays a curse on him: *{q('glamr')}* – “that these eyes, which I have, shall always be before your sight”. Grettir can never again be alone in the dark.

The revenants walk again where people live. When we read them we found them in Iceland, in Greenland and in the Faroes, and only once in Norway.

## Inside the mound

In the legendary sagas and in the Edda the dead stay in the mound, and the living must go there. On the island of Samsø Hervör stands at her dead father's mound at night, between burning grave fires, and wakes him: *{q('vaki')}* – “wake, Angantýr, Hervör wakes you”. She wants the sword Tyrfingr, and at last he gives it to her.

![Hervör at Angantýr's mound]({HERVOR[0]})
Hervör fetches the sword from the dead Angantýr. Painting: {HERVOR[2]}, {HERVOR[3]}, via [Wikimedia Commons]({HERVOR[1]}).

Often the mound is a treasure chamber, and the dead sits on a chair and guards the gold. In Hrómundar saga Hrómundr breaks into the mound where the king and berserk Þráinn sits. He has to wrestle the dead man in the dark, and the dead says: *{q('thrainn')}* – “long have I lived in my mound”. In Göngu-Hrólfs saga Hrólfr meets the dead king Hreggviðr at his mound: *{q('hreggvidr')}* – “I dwell in this mound with my champions”.

![Mounds at Gamla Uppsala]({HOG[0]})
One of the mounds at Gamla Uppsala. In the sagas the dead could live on in the mound, and whoever broke in had to take the fight. Photo: {HOG[2]}, {HOG[3]}, via [Wikimedia Commons]({HOG[1]}).

The sagas of Icelanders have mound-dwellers too, in {V1['isl']['högbo']} places. But when we read them nearly all lived abroad, in Norway or in Helluland far to the west. The saga Icelanders had to travel to meet a mound-dweller. The only mound-dweller at home in Iceland is Gunnarr of Hlíðarendi in Njáls saga. He is not dangerous. One evening a shepherd and a maid, driving sheep past the mound, see that *{q('gunnar')}* – “Gunnarr seemed merry and was chanting verse in the mound”. Where the dead live in the sagas of Icelanders we have not tested. It is an observation from the reading.

## The runestones

The runestones never speak of the dead walking again. Three stones mention a mound. On U 269 in Uppland Illugi had stones raised and a mound made for his brother Bjôrn. On U 135 the sons made a bridge and a mound for their father.

![The Karlevi stone, Öl 1]({KARL[0]})
The Karlevi stone (Öl 1) on Öland: “Hidden lies in this mound …”. Woodcut: {KARL[2]}, {KARL[3]}, via [Wikimedia Commons]({KARL[1]}).

The third is the Karlevi stone on Öland, raised over the Dane Sibbi. There stands the only noun *draugr* on any runestone: *{KARLEVI}*. But here the word does not mean a revenant. *Þrúðar draugr*, “Þrúðr's tree”, is a skaldic kenning for a warrior. The skalds' word for a warrior and the sagas' word for the dead who walks again look the same, but they are used in quite different ways.

## What we do not know

- **Whether the Vikings believed this.** The sagas were written in the 13th and 14th centuries. The difference shows two ways of telling: the adventure in the mound and the unease at home on the farm.
- **Whether the Icelanders were more afraid of their dead.** The revenants may just as well be a storytelling device, a tension in the saga, as a belief.
- **Why it turned out this way.** Perhaps because the Icelanders had no mounds of ancient kings to break into. We have not tested that.
- **On the method.** All {M['träffar']} places were classified by hand with Anthropic's language model Claude (Claude Opus). Another instance of the same model reclassified 40 of them without seeing the first classification and reached the same result in {CTRL['lika']}. The only disagreement concerned a skaldic kenning. Every quotation is checked against the text. The rules were locked in [an analysis plan]({PLAN}), and everything is in [the results]({RES}).

:::box The essentials in brief
- In the legendary sagas you meet the dead in the mound, in {pc(V1['forn']['högbo'], H['forn_n'])} per cent of the cases.
- In the sagas of Icelanders about half of the dead come home, to the farm, the door and the fire.
- The test: that the dead of the legendary sagas are more often found in the mound than those of the sagas of Icelanders held.
- At Fróðá the dead were summoned before a door court, and they left one by one.
- The mound-dwellers of the sagas of Icelanders nearly all live abroad. The only one in Iceland is Gunnarr, who sings merrily in his mound.
- The runestones never speak of the dead walking again. The only *draugr* on a runestone means a warrior.
:::

## Sources

The Eddic poems, Snorri's Edda and the legendary sagas: heimskringla.no, editions by Guðni Jónsson and others; the texts are used here only for counting and short quotations. Heimskringla: heimskringla.no, Linder & Haggson (1869–72), public domain. The sagas of Icelanders: sagadb.org (Sveinbjörn Þórðarson), public domain. Thanks to heimskringla.no for the texts. The runestones: Scandinavian Runic-text Database (Samnordisk runtextdatabas), version 3.1 (2018), Uppsala University. The translations are our own. The rules and the scripts: [the analysis plan]({PLAN})."""

# ======================================================================================================================
# 6. Kontroller och skrivning
# ======================================================================================================================
HOLDBACK = re.compile(r"\bAI\b|signifikan|p-värde|p-value|bootstrap|\bHolm\b", re.I)
labels = ["Forskning", "Eddan", "Tro och magi"]
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
path = os.path.join(ROOT, "utdata", "blogg", "de_doda.json")
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
                 "topic": "Eddan och sagorna|väsen|de döda", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id, SLUG)
    blog._forget()
