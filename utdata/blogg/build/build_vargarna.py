"""Artikeln "Fornnordiska väsen – Vargarna i Gunnars dröm" – del 7 i serien: vargen (och korpen).

Bygger på den låsta studien analysplaner/2026-11-22-vargarna.md (6e4e192); siffrorna ur utdata/vargarna/matt.json och
kontroll_resultat.json; varje citat kontrolleras mot texten i korpusen.
    ../../../.venv/bin/python build_vargarna.py [--write | --update DOC]"""
import datetime as dt
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_labels  # noqa: E402

SLUG = "vargarna-i-gunnars-drom"
PLAN = "https://github.com/Precatio/runes/blob/main/analysplaner/2026-11-22-vargarna.md"
RES = "https://github.com/Precatio/runes/blob/main/utdata/vargarna/resultat.md"
D = os.path.join(ROOT, "utdata", "vargarna")
M = json.load(open(os.path.join(D, "matt.json"), encoding="utf-8"))
CTRL = json.load(open(os.path.join(D, "kontroll_resultat.json"), encoding="utf-8"))

# ======================================================================================================================
# 1. Siffrorna
# ======================================================================================================================
V1 = M["V1"]
nD, nP = sum(V1["dikt"].values()), sum(V1["prosa"].values())
assert (M["träffar"], nD, nP, sum(V1["snorre"].values())) == (158, 76, 56, 26)
assert (V1["prosa"]["förvandling"], V1["dikt"]["djur"]) == (28, 47)
pc = lambda g, k: round(100 * V1[g].get(k, 0) / sum(V1[g].values()))  # noqa: E731
assert (pc("prosa", "förvandling"), pc("dikt", "djur")) == (50, 62)
H = M["T1"]["huvud"]
assert not H["håller"] and (H["dikt_n"], H["prosa_n"]) == (59, 16)
assert (H["dikt_%"], H["prosa_%"]) == (16.9, 6.2)
assert (CTRL["lika"], CTRL["stickprov"]) == (34, 40)
BS = M["V3"]
assert (BS["fornaldarsagor"]["per_10000"], BS["islanningasagor"]["per_10000"], BS["heimskringla"]["per_10000"]) == (3.92, 1.25, 0.33)
assert len(M["V4_text"]) == 2
N4 = M["V4_namn"]
assert (N4["stenar_med_vargnamn"], N4["stenar"]) == (189, 2321)

# ======================================================================================================================
# 2. Citaten
# ======================================================================================================================
K = os.path.join(ROOT, "utdata", "varlden", "korpus")
EDDA = json.load(open(os.path.join(ROOT, "utdata", "Malt", "kallor", "edda.json"), encoding="utf-8"))


def flat(t):
    return " ".join(t.split())


Q = {"gunnar": ("islendingasogur/brennu-njals_saga.is.txt", "Þar þóttist eg sjá varga mjög marga og sóttu þeir allir að mér"),
     "hjortur": ("islendingasogur/brennu-njals_saga.is.txt", "Hjörtur féll þá þegar dauður niður"),
     "fylgjur": ("fornaldarsogur/Hrólfs_saga_Gautrekssonar.txt", "Þar sem sá varga, þat eru manna fylgjur"),
     "ylgr": ("fornaldarsogur/Völsunga_saga.txt", "sú in sama ylgr væri móðir Siggeirs konungs"),
     "hamir": ("fornaldarsogur/Völsunga_saga.txt", "úlfahamir hengu í húsinu yfir þeim"),
     "ulfhednar": ("islendingasogur/vatnsdaela_saga.is.txt", "þeir berserkir er úlfhéðnar voru kallaðir. Þeir höfðu vargstakka fyrir brynjur"),
     "emjudu": ("heimskringla/Haralds_saga_hins_hárfagra.txt", "Grenjuðu berserkir, guðr var á sinnum, emjuðu úlfhéðnar ok ísarn glumdu"),
     "mannahugir": ("islendingasogur/thordar_saga_hredu.is.txt", "og eru þetta mannahugir"),
     "eyvindur": ("islendingasogur/egils_saga.is.txt", "Eyvindur hafði vegið í véum, og var hann vargur orðinn"),
     "gudbrand": ("heimskringla/Saga_Ólafs_hins_helga.txt", "munu vargar draga þik ok alla yðr, ok hrafnar slíta"),
     "hakonarmal": ("heimskringla/Saga_Hákonar_góða.txt", "Mun úbundinn á ýta sjöt Fenrisúlfr fara, áðr jafngóðr á auða tröð konungmaðr komi")}
EQ = {"gudrun": ("Guðrúnarkviða_in_forna", "hrafna gjalla, örnu gjalla æzli fegna, varga þjóta"),
      "geri": ("Grímnismál", "Gera ok Freka seðr gunntamiðr hróðigr Herjaföður"),
      "huginn": ("Grímnismál", "Huginn ok Muninn fljúga hverjan dag Jörmungrund yfir")}
for k, (p, s) in Q.items():
    assert s in flat(open(os.path.join(K, p), encoding="utf-8").read()), k
for k, (poem, s) in EQ.items():
    assert s in flat(EDDA[poem]), k


def q(k):
    return Q[k][1] if k in Q else EQ[k][1]


# ======================================================================================================================
# 3. Bilderna (Wikimedia Commons; licenser kontrollerade 2026-11-22)
# ======================================================================================================================
TORS = ("https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/Torslundapl%C3%A5tarna_-_Historiska_museet_-_618349_HST_-_324349_%28cropped%29.jpg/1280px-Torslundapl%C3%A5tarna_-_Historiska_museet_-_618349_HST_-_324349_%28cropped%29.jpg",
        "https://commons.wikimedia.org/wiki/File:Torslundapl%C3%A5tarna_-_Historiska_museet_-_618349_HST_-_324349_(cropped).jpg",
        "Statens historiska museer", "CC BY 4.0")
SOL = ("https://upload.wikimedia.org/wikipedia/commons/thumb/5/51/The_Wolves_Pursuing_Sol_and_Mani.jpg/1280px-The_Wolves_Pursuing_Sol_and_Mani.jpg",
       "https://commons.wikimedia.org/wiki/File:The_Wolves_Pursuing_Sol_and_Mani.jpg", "John Charles Dollman (1909)", "public domain")
LED = ("https://upload.wikimedia.org/wikipedia/commons/thumb/6/6e/Ledbergsstenen_%C3%96g_181.JPG/1280px-Ledbergsstenen_%C3%96g_181.JPG",
       "https://commons.wikimedia.org/wiki/File:Ledbergsstenen_%C3%96g_181.JPG", "Phlanx", "CC BY 3.0")


# ======================================================================================================================
# 4. Diagrammen (procent)
# ======================================================================================================================
LAB = {"djur": ("djuret", "the animal"), "myt": ("myternas vargar", "the mythic wolves"),
       "förvandling": ("en människa i vargskepnad", "a human in wolf shape"), "fredlös": ("den fredlöse", "the outlaw"),
       "kenning": ("omskrivning", "kenning"), "annat": ("annat", "other")}


def chart_what(lang):
    sv = lang == "sv"
    rows = [f":::chart {'Vad vargen är i dikten och i sagornas prosa' if sv else 'What the wolf is in the poetry and in the saga prose'}"]
    for g, gsv, gen in (("dikt", "Dikten: eddadikterna och skaldeversen", "Poetry: the Eddic poems and the skaldic verse"),
                        ("prosa", "Sagornas prosa", "The saga prose")):
        rows.append(f"# {gsv if sv else gen} ({sum(V1[g].values())} {'ställen' if sv else 'places'})")
        for k in ("djur", "myt", "förvandling", "fredlös", "kenning", "annat"):
            x = V1[g].get(k, 0)
            hl = "+" if (g, k) in (("dikt", "djur"), ("prosa", "förvandling")) else ""
            rows.append(f"{hl}{LAB[k][0 if sv else 1]} | {pc(g, k)} | {x}")
    rows.append("Andel av alla ställen där ordet för varg står. Alla lästa för hand. Snorres Edda räknas för sig. Diagram: Vitki."
                if sv else "Share of all places where the word for wolf occurs. Every place read by hand. Snorri's Edda counted separately. Chart: Vitki.")
    return "\n".join(rows) + "\n:::"


def chart_raven(lang):
    sv = lang == "sv"
    rows = [f":::chart {'Andel av vargarna som har en korp i närheten' if sv else 'Share of the wolves with a raven nearby'}",
            f"{'Dikten' if sv else 'Poetry'} | {H['dikt_%']} | {round(H['dikt_%'] * H['dikt_n'] / 100)} {'av' if sv else 'of'} {H['dikt_n']}",
            f"{'Sagornas prosa' if sv else 'The saga prose'} | {H['prosa_%']} | {round(H['prosa_%'] * H['prosa_n'] / 100)} {'av' if sv else 'of'} {H['prosa_n']}",
            "Vargen som djur eller i myten; ett ord för korp inom 25 ord. Skillnaden går inte att visa: prosan har för få vargar. Diagram: Vitki."
            if sv else "The wolf as an animal or in myth; a word for raven within 25 words. The difference cannot be shown: the prose has too few wolves. Chart: Vitki."]
    return "\n".join(rows) + "\n:::"


assert round(H["dikt_%"] * H["dikt_n"] / 100) == 10 and round(H["prosa_%"] * H["prosa_n"] / 100) == 1

# ======================================================================================================================
# 5. Texten
# ======================================================================================================================
title = "Fornnordiska väsen – Vargarna i Gunnars dröm"
summary = ("I sagorna är vargen nästan aldrig ett djur. Hälften av gångerna är den en människa – oftast en fiende som visar sig i en dröm. "
           "Vi läste alla ställen där vargen står i den fornnordiska litteraturen, och letade efter den på runstenarna.")

body = f"""Gunnar på Hlidarände rider österut över Tjursån, med bara sin bror Kolskegg och sin unge släkting Hjört i sällskapet. Han blir sömnig, lägger sig att vila och sover oroligt. Hjört vill väcka honom, men Kolskegg säger nej: Gunnar ska få drömma klart.

När Gunnar vaknar berättar han: *{q('gunnar')}* – ”där tyckte jag mig se mycket många vargar, och de anföll mig alla”. Han försvarar sig med båge, svärd och hillebard. Men vargarna får Hjört under sig och sliter upp hans bröst, och en av dem har hjärtat i munnen.

Strax därefter rider de rakt in i ett bakhåll vid Knafahólar. Gunnars fiender har legat och väntat med trettio man. I striden hugger en norrman Hjört i bröstet: *{q('hjortur')}* – ”Hjört föll genast död ned”.

Vargarna i drömmen var männen i bakhållet. Så är det nästan alltid i sagorna. Det här är sjunde delen i serien Fornnordiska väsen, och den handlar om vargen. Vi läste alla {M['träffar']} ställen där ordet för varg står i den fornnordiska litteraturen – i eddadikterna, i Snorres Edda, i sagorna och i skaldeversen – och sorterade dem för hand.

## Två sorters varg

Resultatet blev två helt olika vargar, beroende på om texten är dikt eller prosa.

{chart_what('sv')}

I dikten är vargen ett djur. Den följer hären och äter de fallna, och skalden prisar kungen för att han har ”gett vargen mat”. Av de {nD} ställena i dikterna är {V1['dikt']['djur']} vargen som djur, och nästan alla står på ett slagfält.

I sagornas prosa är vargen något helt annat. Hälften av gångerna, {V1['prosa']['förvandling']} av {nP}, är den en människa. Oftast är det en dröm före ett överfall, som Gunnars. I Gísla saga berättar Gísle efter sin vän Vésteins död att han har drömt två nätter i rad: först om en orm, sedan om en varg som sprang ut från en gård och bet Véstein till döds. I Þórðar saga hreðu drömmer Þórðr om arton vargar, och en av dem är mycket större än de andra. Bonden som han bor hos förstår genast: *{q('mannahugir')}* – ”och det här är människors sinnen”. Samma morgon ligger Össur i bakhåll för honom med arton man. Sagorna förklarar själva vad vargarna betyder. I Hrólfs saga Gautrekssonar berättar drottningen en dröm för kungen och tyder den själv: *{q('fylgjur')}* – ”där jag såg vargar, det är människors fylgjor”.

Fylgjan, det skyddsväsen som följer en människa och syns i drömmar, mötte vi redan i seriens förra del. Hos fienden tar den vargens skepnad.

## En varg i helgedomen

Ordet *vargr* betyder också en människa som har gjort något oförlåtligt. Det kan vara en mördare, en edsbrytare eller en som har dödat inne i en helgedom. I Egils saga dödar Eyvind en man under ett offergille, på helgad mark: *{q('eyvindur')}* – ”Eyvind hade dräpt i helgedomen, och han hade blivit varg”. Han måste genast ge sig av.

Uttrycket *vargr í véum*, ”varg i helgedomen”, finns också i Völsunga saga. Den som blev varg var fredlös och fick jagas som ett djur.

## Ulfhednarna

Vargen kunde också vara en krigare. Vatnsdæla saga berättar om Harald hårfagres skepp i slaget vid Hafrsfjord, där Harald enligt sagorna vann Norge. I fören stod *{q('ulfhednar')}* – ”de bärsärkar som kallades ulfhednar. De hade vargskinn i stället för brynjor.”

![Pressbleck från Torslunda på Öland]({TORS[0]})
En dansande man med hornhjälm och en krigare med vargens huvud och päls, på ett pressbleck från Torslunda på Öland, 500–600-talet. Krigaren brukar tolkas som en ulfhedin. Foto: {TORS[2]}, {TORS[3]}, via [Wikimedia Commons]({TORS[1]}).

Ordet *úlfheðnar* för krigare står bara tre gånger i hela vårt material, och alla tre gångerna handlar det om samma slag, Hafrsfjord. Utom i Vatnsdæla saga står det i Grettis saga och i Torbjörn hornklofes dikt om slaget, som Snorre citerar i Heimskringla: *{q('emjudu')}* – ”bärsärkarna vrålade, striden var i gång, ulfhednarna tjöt och järnet skallade”. Som namn levde ordet längre. På en runsten i Södertälje, Sö 307, har en son som hette Ulvhedin rest stenen efter sin far Torsten.

Vargskinnet finns också utanför Hafrsfjord. I Völsunga saga hittar Sigmund och hans son Sinfjötli ett hus i skogen där två kungasöner ligger och sover, förhäxade, och *{q('hamir')}* – ”vargskinn hängde i huset ovanför dem”. Sigmund och Sinfjötli tar på sig skinnen och blir själva vargar. I samma saga kommer en ylva varje natt och äter upp Sigmunds bröder, en efter en. Somliga säger, står det, *{q('ylgr')}* – ”att samma ylva var kung Siggeirs mor”, i vargskepnad.

Bärsärkarna i allmänhet hör till fornaldarsagornas äventyrsvärld. Där står ordet ungefär {round(BS['fornaldarsagor']['per_10000'] / BS['islanningasagor']['per_10000'])} gånger så tätt som i islänningasagorna, och i Heimskringla, kungasagorna, är de nästan borta.

## Vargarna vid världens slut

Vargarna i myterna finns nästan bara i Eddan. Fenrisvargen ska slita sig vid Ragnarök och sluka Oden. Sköll jagar solen och Hati månen. Garm skäller vid Gnipahålan. Och Oden matar sina två vargar vid bordet: *{q('geri')}* – ”Gere och Freke mättar den stridsvane, ärorike härfadern”.

![Vargarna som jagar sol och måne]({SOL[0]})
Sköll och Hati jagar solen och månen över himlen. Målning: {SOL[2]}, {SOL[3]}, via [Wikimedia Commons]({SOL[1]}).

I sagornas prosa finns inte en enda av dem. I skaldeversen dyker Fenrisvargen upp i några omskrivningar, men som sig själv står han i sagorna bara en gång, i en minnesdikt över Håkon den gode som Snorre citerar i Heimskringla: *{q('hakonarmal')}* – ”obunden ska Fenrisvargen fara mot människornas boningar, innan en lika god kung kommer till den tomma platsen”.

![Ledbergsstenen, Ög 181]({LED[0]})
Ledbergsstenen (Ög 181) i Östergötland. Bilderna av krigare, djur och ett skepp brukar tolkas som Ragnarök, där Oden slukas av Fenrisvargen. Tolkningen är omstridd. Foto: {LED[2]}, {LED[3]}, via [Wikimedia Commons]({LED[1]}).

## Korpen

Korpen följer vargen till slagfältet. I Guðrúnarkviða säger Högne till Gudrun att hon ska se söderut, mot den döde Sigurd. Där ska hon höra *{q('gudrun')}* – ”korparna skrika, örnarna skrika, glada över maten, vargarna yla”. Oden har två korpar, och de är lika kända som hans vargar: *{q('huginn')}* – ”Hugin och Munin flyger varje dag över världen”. I skaldeversen blir korpen den fågel som får de dödas kött. I den här delen följer vi den därför bara som vargens följeslagare.

Vi prövade om korpen står oftare bredvid vargen i dikten än i prosan. Testet: att korpen följer vargen oftare i dikten än i prosan gick inte att visa. I dikten har ungefär var sjätte varg en korp i närheten, i prosan en av {H['prosa_n']}. Men prosan har för få vargar som djur för att skillnaden ska vara säker. Den enda korpen där står i Heimskringla, i en dröm som varnar hövdingen Gudbrand i Dalarna inför striden mot Olav den helige: *{q('gudbrand')}* – ”vargar ska släpa dig och alla dina, och korpar slita”.

{chart_raven('sv')}

## Runstenarna

På runstenarna finns vargen bara i namnen. Ordet för varg står två gånger i de svenska runstenstexterna, och båda gångerna är det slutet av ett namn. Men {N4['stenar_med_vargnamn']} av {N4['stenar']:,} stenar bär ett namn med vargen i: Ulv, Fastulv, Ingulv, Brynjulv. Det är ungefär en sten av tolv. Vanligast är de i Södermanland och Uppland.

Ristarna skrev alltså inte om vargen. De bar den bara i namnen.

## Det vi inte vet

- **Om vargfylgjan är en vikingatida tro.** Den är ett berättargrepp i sagorna, som skrevs på 1200-talet: en dröm före ett överfall.
- **Om ulfhednarna fanns.** Ordet hör till ett enda slag, och pressblecket från Torslunda är flera hundra år äldre än sagorna, och vi vet inte vad det föreställer.
- **Om vargnamnen säger något om tro.** Namnleden ärvdes och kombinerades.
- **Om metoden.** Alla {M['träffar']} ställen klassades för hand med Anthropics språkmodell Claude (Claude Opus). En annan instans av samma modell klassade om 40 av dem utan att se den första klassningen och kom fram till samma sak i {CTRL['lika']}. Det var precis vad vi hade krävt i förväg. Oenigheterna gällde gränsfall i skaldeversen, där ”varg” kan betyda både djuret, den fredlöse och en omskrivning. Testet påverkades inte av dem. Varje citat är kontrollerat mot texten. Reglerna låstes i [en analysplan]({PLAN}), och allt finns i [resultatet]({RES}).

:::box Det viktigaste i korthet
- I dikten är vargen ett djur på slagfältet, i sex fall av tio.
- I sagornas prosa är vargen i hälften av fallen en människa – oftast en fiende som visar sig i en dröm före ett överfall.
- Ordet *vargr* betyder också en fredlös. Den som dräpte i en helgedom blev ”varg i helgedomen”.
- Ulfhednarna, krigarna i vargskinn, nämns bara om ett enda slag: Hafrsfjord.
- Myternas vargar, Fenrisvargen, Sköll och Hati, Gere och Freke, finns nästan bara i Eddan.
- Testet: att korpen följer vargen oftare i dikten än i prosan gick inte att visa, eftersom prosan har för få vargar.
- På runstenarna finns vargen bara i namnen, på {N4['stenar_med_vargnamn']} stenar.
:::

## Källor

Eddadikterna, Snorres Edda och fornaldarsagorna: heimskringla.no, Guðni Jónssons m.fl. utgåvor; texterna används här bara för räkning och korta citat. Heimskringla: heimskringla.no, Linder & Haggson (1869–72), public domain. Islänningasagorna: sagadb.org (Sveinbjörn Þórðarson), public domain. Tack till heimskringla.no för texterna. Runstenarna: Samnordisk runtextdatabas, version 3.1 (2018), Uppsala universitet. Översättningarna är våra egna. Reglerna och skripten: [analysplanen]({PLAN})."""

title_en = "Old Norse beings – The wolves in Gunnarr's dream"
summary_en = ("In the sagas the wolf is hardly ever an animal. Half of the time it is a human being – usually an enemy appearing in a dream. "
              "We read every place where the wolf occurs in Old Norse literature, and looked for it on the runestones.")

body_en = f"""Gunnarr of Hlíðarendi rides east across the Þjórsá, with only his brother Kolskeggr and his young kinsman Hjörtr for company. He grows sleepy, lies down to rest and sleeps uneasily. Hjörtr wants to wake him, but Kolskeggr says no: Gunnarr is to dream his dream to the end.

When Gunnarr wakes he tells them: *{q('gunnar')}* – “there I thought I saw very many wolves, and they all attacked me”. He defends himself with bow, sword and halberd. But the wolves get Hjörtr under them and tear open his breast, and one of them has the heart in its mouth.

Soon afterwards they ride straight into an ambush at Knafahólar. Gunnarr's enemies have lain in wait with thirty men. In the fight a Norwegian strikes Hjörtr in the breast: *{q('hjortur')}* – “Hjörtr fell dead at once”.

The wolves in the dream were the men in the ambush. That is almost always how it is in the sagas. This is the seventh part of the series Old Norse beings, and it is about the wolf. We read all {M['träffar']} places where the word for wolf occurs in Old Norse literature – in the Eddic poems, in Snorri's Edda, in the sagas and in the skaldic verse – and sorted them by hand.

## Two kinds of wolf

The result was two quite different wolves, depending on whether the text is poetry or prose.

{chart_what('en')}

In the poetry the wolf is an animal. It follows the army and eats the fallen, and the skald praises the king for having “fed the wolf”. Of the {nD} places in the poetry, {V1['dikt']['djur']} are the wolf as an animal, and nearly all of them are on a battlefield.

In the saga prose the wolf is something else entirely. Half of the time, {V1['prosa']['förvandling']} of {nP}, it is a human being. Most often it is a dream before an attack, like Gunnarr's. In Gísla saga Gísli tells, after the death of his friend Vésteinn, that he has dreamt two nights running: first of a snake, then of a wolf that ran out of a farm and bit Vésteinn to death. In Þórðar saga hreðu Þórðr dreams of eighteen wolves, one of them far bigger than the rest. The farmer he is staying with understands at once: *{q('mannahugir')}* – “and these are the minds of men”. That same morning Össurr lies in ambush for him with eighteen men. The sagas themselves explain what the wolves mean. In Hrólfs saga Gautrekssonar the queen tells the king a dream and interprets it herself: *{q('fylgjur')}* – “where I saw wolves, those are the fylgjur of men”.

The fylgja, the guardian being that follows a person and is seen in dreams, we met already in the previous part of the series. In the enemy it takes the shape of the wolf.

## A wolf in the sanctuary

The word *vargr* also means a person who has done something unforgivable. It can be a murderer, an oath-breaker or someone who has killed inside a sanctuary. In Egils saga Eyvindr kills a man during a sacrificial feast, on hallowed ground: *{q('eyvindur')}* – “Eyvindr had killed in the sanctuary, and he had become a wolf”. He has to leave at once.

The phrase *vargr í véum*, “a wolf in the sanctuary”, also occurs in Völsunga saga. The one who became a wolf was an outlaw and could be hunted like an animal.

## The úlfheðnar

The wolf could also be a warrior. Vatnsdæla saga tells of Haraldr Fairhair's ship in the battle of Hafrsfjörðr, where according to the sagas Haraldr won Norway. In the prow stood *{q('ulfhednar')}* – “the berserks who were called úlfheðnar. They had wolf skins instead of mail coats.”

![Press plate from Torslunda on Öland]({TORS[0]})
A dancing man in a horned helmet and a warrior with the head and pelt of a wolf, on a press plate from Torslunda on Öland, 6th–7th century. The warrior is often read as an úlfheðinn. Photo: {TORS[2]}, {TORS[3]}, via [Wikimedia Commons]({TORS[1]}).

The word *úlfheðnar* for warriors occurs only three times in all our material, and all three times it is about the same battle, Hafrsfjörðr. Besides Vatnsdæla saga it occurs in Grettis saga and in Þorbjörn hornklofi's poem on the battle, which Snorri quotes in Heimskringla: *{q('emjudu')}* – “the berserks roared, the fight was on, the úlfheðnar howled and the iron rang”. As a name the word lived longer. On a runestone at Södertälje, Sö 307, a son called Ulfheðinn raised the stone in memory of his father Þorsteinn.

The wolf skin also turns up beyond Hafrsfjörðr. In Völsunga saga Sigmundr and his son Sinfjötli find a house in the forest where two king's sons lie asleep under a spell, and *{q('hamir')}* – “wolf skins hung in the house above them”. Sigmundr and Sinfjötli put on the skins and become wolves themselves. In the same saga a she-wolf comes every night and eats Sigmundr's brothers, one by one. Some say, the saga reports, *{q('ylgr')}* – “that this same she-wolf was King Siggeirr's mother”, in wolf shape.

The berserks in general belong to the adventure world of the legendary sagas. There the word occurs about {round(BS['fornaldarsagor']['per_10000'] / BS['islanningasagor']['per_10000'])} times as densely as in the sagas of Icelanders, and in Heimskringla, the kings' sagas, they have almost vanished.

## The wolves at the end of the world

The wolves of the myths are found almost only in the Edda. The Fenris wolf will break loose at Ragnarök and swallow Odin. Sköll chases the sun and Hati the moon. Garmr howls at Gnipahellir. And Odin feeds his two wolves at the table: *{q('geri')}* – “Geri and Freki the battle-wont, glorious father of hosts feeds”.

![The wolves pursuing sun and moon]({SOL[0]})
Sköll and Hati chase the sun and the moon across the sky. Painting: {SOL[2]}, {SOL[3]}, via [Wikimedia Commons]({SOL[1]}).

In the saga prose not a single one of them appears. In the skaldic verse the Fenris wolf turns up in a few kennings, but as himself he appears in the sagas only once, in a memorial poem for Hákon the Good that Snorri quotes in Heimskringla: *{q('hakonarmal')}* – “unbound the Fenris wolf shall go against the dwellings of men, before an equally good king comes to the empty place”.

![The Ledberg stone, Ög 181]({LED[0]})
The Ledberg stone (Ög 181) in Östergötland. Its pictures of warriors, animals and a ship are often read as Ragnarök, where Odin is swallowed by the Fenris wolf. The reading is disputed. Photo: {LED[2]}, {LED[3]}, via [Wikimedia Commons]({LED[1]}).

## The raven

The raven follows the wolf to the battlefield. In Guðrúnarkviða Högni tells Guðrún to look south, towards the dead Sigurðr. There she will hear *{q('gudrun')}* – “the ravens screech, the eagles screech, glad of the food, the wolves howl”. Odin has two ravens, as famous as his wolves: *{q('huginn')}* – “Huginn and Muninn fly every day over the world”. In the skaldic verse the raven becomes the bird that gets the flesh of the dead. In this part we therefore follow it only as the wolf's companion.

We tested whether the raven stands beside the wolf more often in the poetry than in the prose. The test: that the raven follows the wolf more often in the poetry than in the prose could not be shown. In the poetry about one wolf in six has a raven nearby, in the prose one of {H['prosa_n']}. But the prose has too few wolves as animals for the difference to be certain. The only raven there is in Heimskringla, in a dream warning the chieftain Guðbrandr of the Dales before the battle against Saint Óláfr: *{q('gudbrand')}* – “wolves shall drag you and all yours, and ravens tear”.

{chart_raven('en')}

## The runestones

On the runestones the wolf exists only in the names. The word for wolf occurs twice in the Swedish runestone texts, and both times it is the end of a name. But {N4['stenar_med_vargnamn']} of {N4['stenar']:,} stones carry a name with the wolf in it: Ulfr, Fastulfr, Ingulfr, Brynjulfr. That is about one stone in twelve. They are commonest in Södermanland and Uppland.

The carvers, then, did not write about the wolf. They only carried it in the names.

## What we do not know

- **Whether the wolf fylgja is a Viking Age belief.** It is a storytelling device in the sagas, which were written in the 13th century: a dream before an attack.
- **Whether the úlfheðnar existed.** The word belongs to a single battle, and the Torslunda plate is several hundred years older than the sagas, and we do not know what it depicts.
- **Whether the wolf names say anything about belief.** Name elements were inherited and combined.
- **On the method.** All {M['träffar']} places were classified by hand with Anthropic's language model Claude (Claude Opus). Another instance of the same model reclassified 40 of them without seeing the first classification and reached the same result in {CTRL['lika']}. That was exactly what we had required in advance. The disagreements were borderline cases in the skaldic verse, where “wolf” can mean the animal, the outlaw and a kenning. The test was not affected by them. Every quotation is checked against the text. The rules were locked in [an analysis plan]({PLAN}), and everything is in [the results]({RES}).

:::box The essentials in brief
- In the poetry the wolf is an animal on the battlefield, in six cases out of ten.
- In the saga prose the wolf is a human being half of the time – usually an enemy appearing in a dream before an attack.
- The word *vargr* also means an outlaw. Whoever killed in a sanctuary became a “wolf in the sanctuary”.
- The úlfheðnar, the warriors in wolf skins, are named only of a single battle: Hafrsfjörðr.
- The wolves of myth, the Fenris wolf, Sköll and Hati, Geri and Freki, are found almost only in the Edda.
- The test: that the raven follows the wolf more often in the poetry than in the prose could not be shown, because the prose has too few wolves.
- On the runestones the wolf exists only in the names, on {N4['stenar_med_vargnamn']} stones.
:::

## Sources

The Eddic poems, Snorri's Edda and the legendary sagas: heimskringla.no, editions by Guðni Jónsson and others; the texts are used here only for counting and short quotations. Heimskringla: heimskringla.no, Linder & Haggson (1869–72), public domain. The sagas of Icelanders: sagadb.org (Sveinbjörn Þórðarson), public domain. Thanks to heimskringla.no for the texts. The runestones: Scandinavian Runic-text Database (Samnordisk runtextdatabas), version 3.1 (2018), Uppsala University. The translations are our own. The rules and the scripts: [the analysis plan]({PLAN})."""

body = body.replace(f"{N4['stenar']:,}", f"{N4['stenar']:,}".replace(",", " "))
body_en = body_en.replace(f"{N4['stenar']:,}", f"{N4['stenar']:,}".replace(",", " "))

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
path = os.path.join(ROOT, "utdata", "blogg", "vargarna.json")
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
                 "topic": "Eddan och sagorna|väsen|vargen", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id, SLUG)
    blog._forget()
