"""Personlig artikel: "När åskan hade ett namn" – om det fina i ett sätt att tyda världen som utgick från naturen omkring:
åskan, träden och djuren, och om det vi inte kan följa (blotet, trälarna). Fornisländsk text efter Guðni Jónssons
utgåva (utdata/Malt/kallor/edda.json, samma som "Korpen som heter Minne"); översättningarna är gjorda för artikeln och så
ordagranna som möjligt. Velandastenen och namnen ur Rundata. Ordet "religion" används inte (Viktors önskan).
    .venv/bin/python utdata/blogg/build/build_naturen.py [--write | --update DOKUMENT-ID]
Skriver utdata/blogg/naturen.json; --write sparar ett nytt opublicerat utkast i Firestore."""
import csv
import datetime as dt
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_labels, commons  # noqa: E402

EDDA = json.load(open(os.path.join(ROOT, "utdata", "Malt", "kallor", "edda.json"), encoding="utf-8"))


def stanza(work, n):
    m = re.search(r"(?<!\d)%d\. (.*?)(?=\s\d{1,3}\. |\Z)" % n, EDDA[work], re.S)
    return " ".join(m.group(1).split())


# ---- källtexterna, ordagrant --------------------------------------------------------------------------
THRYM21 = ("Senn váru hafrar heim of reknir, skyndir at sköklum, skyldu vel renna; björg brotnuðu, brann jörð loga, "
           "ók Óðins sonr í Jötunheima.")
VSP17 = "Unz þrír kvámu ór því liði öflgir ok ástkir æsir at húsi, fundu á landi lítt megandi Ask ok Emblu örlöglausa."
VSP18_END = "önd gaf Óðinn, óð gaf Hænir, lá gaf Lóðurr ok litu góða."
VSP19 = ("Ask veit ek standa, heitir Yggdrasill, hár baðmr, ausinn hvíta auri; þaðan koma döggvar, þærs í dala falla, "
         "stendr æ yfir grænn Urðarbrunni.")
HAV50 = ("Hrörnar þöll, sú er stendr þorpi á, hlýr-at henni börkr né barr; svá er maðr, sá er manngi ann. "
         "Hvat skal hann lengi lifa?")
GRIM44 = ("Askr Yggdrasils, hann er æðstr viða, en Skíðblaðnir skipa, Óðinn ása, en jóa Sleipnir, Bilröst brúa, "
          "en Bragi skalda, Hábrók hauka, en hunda Garmr.")
VAF14 = "Hrímfaxi heitir, er hverja dregr nótt of nýt regin; méldropa fellir hann morgin hvern; þaðan kemr dögg um dala."
RIG8 = ("Hann nam at vaxa ok vel dafna; var þar á höndum hrokkit skinn, kropnir knúar, fingr digrir, fúlligt andlit, "
        "lotr hryggr, langir hælar.")
assert stanza("Þrymskviða", 21) == THRYM21 and stanza("Völuspá", 17) == VSP17 and stanza("Völuspá", 19) == VSP19
assert stanza("Völuspá", 18).endswith(VSP18_END) and stanza("Hávamál", 50) == HAV50 and stanza("Grímnismál", 44) == GRIM44
assert stanza("Vafþrúðnismál", 14).startswith('"' + VAF14) and stanza("Rígsþula", 8) == RIG8
assert stanza("Vafþrúðnismál", 12).startswith('"Skinfaxi heitir, er inn skíra dregr dag of dróttmögu')

RD = json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))
REC = {r["signum"]: r for v in RD.values() if isinstance(v, list) for r in v if isinstance(r, dict) and "signum" in r}
VG150 = '"Þyrvi ræisti stæin æftiR "Ogmund, bonda sinn, miok goðan þegn. "Þorr vigi.'
assert REC["Vg 150"]["normalization"] == VG150 and "Velanda" in REC["Vg 150"]["place"]
VG150_SHOW = VG150.replace('"', "")

# ---- namnen på runstenarna (Rundatas namn per sten, som namnmodulen i R) ----------------------------------
FP = "82193667b35e54a7"
csv.field_size_limit(10 ** 9)
NAMES = list(csv.DictReader(open(os.path.join(ROOT, "data", "cache", "r", "corpus", FP, "names_stones.csv"), encoding="utf-8")))
ANIMAL = {"björn": r"bjorn|biorn", "ulv": r"ulfr?$|^ulf", "örn": r"^arn|^ari$|^orn$", "korp": r"^h?rafn", "orm": r"^orm"}


def has(row, pat):
    return any(re.search(pat, n) for n in row["names"].split("|") if n)


N = len(NAMES)
N_ANIMAL = sum(any(has(r, p) for p in ANIMAL.values()) for r in NAMES)
N_BEAR = sum(has(r, ANIMAL["björn"]) for r in NAMES)
N_WOLF = sum(has(r, ANIMAL["ulv"]) for r in NAMES)
N_THOR = sum(has(r, r"^th[ou]r") for r in NAMES)
assert N == 2321 and 1 / 5 < N_ANIMAL / N < 1 / 4 and round(N / N_BEAR) == 7 and 1 / 8 < N_THOR / N < 1 / 7, (N_ANIMAL, N_BEAR, N_THOR)

# ---- bilderna ------------------------------------------------------------------------------------------
WINGE = "Mårten Eskil Winge - Tor's Fight with the Giants - Google Art Project.jpg"
BAGGE = "Yggdrasil.jpg"
VELANDA = commons.wikidata_files(["Vg 150"])["Vg 150"]
INFO = commons.commons_info([WINGE, BAGGE, VELANDA])
assert (INFO[WINGE]["author"], INFO[WINGE]["licence"]) == ("Mårten Eskil Winge", "Public domain")
assert (INFO[BAGGE]["author"], INFO[BAGGE]["licence"]) == ("Oluf Bagge", "Public domain")
assert INFO[VELANDA]["licence"] == "CC BY-SA 3.0"
page = lambda f: "https://commons.wikimedia.org/wiki/File:" + f.replace(" ", "_")  # noqa: E731
IMG_WINGE = (f"![Tor kör över himlen]({INFO[WINGE]['thumb']})\nMårten Eskil Winge, *Tors strid med jättarna* (1872), "
             f"Nationalmuseum. Fri från upphovsrätt, via [Wikimedia Commons]({page(WINGE)}).")
IMG_BAGGE = (f"![Världsträdet Yggdrasil]({INFO[BAGGE]['thumb']})\nVärldsträdet Yggdrasil, tecknat av Oluf Bagge på "
             f"1800-talet. Fri från upphovsrätt, via [Wikimedia Commons]({page(BAGGE)}).")
VEL_CAP = commons.caption({**INFO[VELANDA], "signum": "Vg 150"}, "sv")
assert VEL_CAP.startswith("Vg 150. Foto: ")
IMG_VEL = f"![Runstenen Vg 150]({INFO[VELANDA]['thumb']})\nVelandastenen, Vg 150, i Västergötland. Foto: {VEL_CAP[len('Vg 150. Foto: '):]}"
IMG_WINGE_EN = (f"![Thor drives across the sky]({INFO[WINGE]['thumb']})\nMårten Eskil Winge, *Thor's Fight with the Giants* "
                f"(1872), Nationalmuseum, Stockholm. Public domain, via [Wikimedia Commons]({page(WINGE)}).")
IMG_BAGGE_EN = (f"![The world tree Yggdrasil]({INFO[BAGGE]['thumb']})\nThe world tree Yggdrasil, drawn by Oluf Bagge in the "
                f"19th century. Public domain, via [Wikimedia Commons]({page(BAGGE)}).")
VEL_CAP_EN = commons.caption({**INFO[VELANDA], "signum": "Vg 150"}, "en")
assert VEL_CAP_EN.startswith("Vg 150. Photo: ")
IMG_VEL_EN = f"![The runestone Vg 150]({INFO[VELANDA]['thumb']})\nThe Velanda stone, Vg 150, in Västergötland. Photo: {VEL_CAP_EN[len('Vg 150. Photo: '):]}"
KORPEN = "/artiklar/korpen-som-heter-minne/"
KORPEN_EN = "/en/artiklar/korpen-som-heter-minne/"

title = "När åskan hade ett namn"
summary = ("En personlig artikel om ett sätt att tyda världen som utgick från naturen omkring: åskan som körde över himlen, "
           "träden som människorna gjordes av, hästarna som drog dagen och natten. Och om det vi inte kan följa.")

body = f"""Den som har stått ute när ett åskväder drar in vet hur det känns. Luften blir tung och stilla, fåglarna tystnar, och sedan kommer mullret, först långt borta och sedan rakt över en. Jag vet vad åskan är: elektricitet som laddas ur mellan moln och mark. Ändå räknar jag sekunderna mellan blixten och knallen, som alla gör, och känner mig liten.

Människorna som reste runstenarna hade ingen meteorologi. De hade åskan, och de gav den ett namn. Det fornnordiska ordet *þórr* betyder åska, och guden och ljudet var samma ord. Vårt *tordön* bär fortfarande hans namn, och *åska* brukar förklaras som ett gammalt ord för gudens färd över himlen.

I Eddadikten om hur Tor hämtar tillbaka sin hammare hör vi hur det lät när han körde:

> {THRYM21}

”Genast drevs bockarna hem och skyndades till skaklarna, de skulle springa väl. Berg brast, jorden brann i lågor, Odens son for till jättarnas land.”

Det är ett åskväder, sett av någon som stod mitt i det: berg som spricker, mark som brinner där blixten slår ned. Det är ingen förklaring i vår mening. Det är ett sätt att göra något obegripligt till någon man kan förhålla sig till, en kraft med ett namn och en vilja.

{IMG_WINGE}

## Människor av trä

Det som slår mig mest när jag läser de gamla dikterna är hur nära människan står resten av världen. I Völuspá skapas inte de första människorna av lera eller ur ett revben. Gudarna hittar dem på stranden, som två träd:

> {VSP17}

”Tills tre kom ur den skaran, starka och kärleksfulla asar, till huset. De fann på land, nästan kraftlösa, Ask och Embla, utan öde.”

Ask är ett träd, och Embla har tolkats som ett annat. Först när gudarna ger dem andning, själ och livets värme blir de människor: *önd gaf Óðinn*, andningen gav Oden. Vi är, enligt den berättelsen, gjorda av samma ved som skogen omkring oss.

Och världen själv är ett träd. Strofen efter berättar om asken Yggdrasil:

> {VSP19}

”En ask vet jag stå, den heter Yggdrasil, ett högt träd, överöst med vit lera. Därifrån kommer daggen som faller i dalarna. Den står alltid grön över Urds brunn.”

Daggen på morgonen kommer från världsträdet. Adam av Bremen, som skrev om svearna på 1070-talet, berättar att det vid templet i Uppsala stod ett väldigt träd som var grönt både vinter och sommar, och att ingen visste vilket slags träd det var.

{IMG_BAGGE}

Träden fick också tala om människan. I Hávamál står:

> {HAV50}

”Granen vissnar som står på den kala kullen, varken bark eller barr skyddar den. Så är det med människan som ingen älskar. Hur länge ska hon leva?”

Den som har sett en ensam tall på ett berg vet vad dikten menar. Naturen var inte bara något man skulle förklara. Den var också något man förklarade sig själv med.

## Hästar, hökar och hundar

I Grímnismál räknar Oden upp det främsta av varje slag:

> {GRIM44}

”Yggdrasils ask är främst av träd, och Skidbladner av skepp, Oden av asar, och av hästar Sleipner, Bivrost av broar, och Brage av skalder, Habrok av hökar, och av hundar Garm.”

Jag tycker om den strofen. Trädet, skeppet, guden, hästen, bron, skalden, höken och hunden står i samma rad, var och en bäst av sitt slag. Världen är inte delad i det heliga och resten. Hästen har en plats bredvid guden.

Dagen och natten var också hästar. Skinfaxe drar dagen över himlen, och hans man lyser upp jorden. Rimfaxe drar natten:

> {VAF14}

”Rimfaxe heter den som drar varje natt över de goda gudarna. Fradga från betslet fäller han varje morgon, därifrån kommer daggen i dalarna.”

Här är daggen skummet från nattens häst. Strax innan kom den från världsträdet. Ingen tycks ha behövt välja mellan förklaringarna. Det var inte en lära som skulle hållas samman, utan försök att förstå, sida vid sida. Korparna Hugin och Munin, som jag skrev om i [Korpen som heter Minne]({KORPEN}), flög ut över världen varje dag och kom tillbaka med det de sett.

Det syns på runstenarna också. Av de {N} runstenarna i Vitkis svenska korpus nämner {N_ANIMAL} någon som bar ett djur i sitt namn, mer än var femte sten: en Björn eller en Torbjörn, en Ulv eller en Gunnulv, en Arnfast, en Orm, en Hrafn. Ungefär var sjunde sten nämner en björn. Man gav sina barn djurens namn, och kanske något av deras styrka.

## Tor på stenarna

När de flesta runstenar restes hade många redan blivit kristna. Ändå nämner {N_THOR} stenar, mer än var åttonde, någon som bar Tor i sitt namn: Torsten, Torbjörn, Tora. Och på en sten i Västergötland, vid Velanda, slutar texten med en bön till åskan:

> {VG150_SHOW}

”Tyrve reste stenen efter Agmund, sin make, en mycket god tägn. Tor helge.”

En kvinna har rest en sten efter sin man och ber den kraft som rör sig i ovädret att skydda den.

{IMG_VEL}

## Det vi inte kan följa

Jag vill inte göra den här världen vackrare än den var. Adam av Bremen berättar att man i Uppsala vart nionde år offrade nio av varje slags hankön, också människor, och hängde kropparna i lunden vid templet. Adam var aldrig där själv och skrev efter vad andra berättat, och forskarna läser honom med försiktighet. Men blotet fanns, och det kostade liv.

Världen var också orättvis på ett sätt som var inbyggt. I Rígsþula föds trälens son, och dikten beskriver honom så här:

> {RIG8}

”Han började växa och trivas väl. På händerna var huden skrynklig, knogarna krokiga, fingrarna tjocka, ansiktet fult, ryggen böjd, hälarna långa.”

Dikten förklarar varför vissa föds till slit och andra till makt, och den tycks tycka att det är i sin ordning. Där kan jag inte följa med.

Men jag kan förstå var det kom ifrån. Det var en hård och oförlåtande värld. En dålig skörd betydde svält, en sträng vinter död, en storm till sjöss att någon aldrig kom hem. Man visste inte varför sjukdomar kom eller varför regnet uteblev. Mot krafter man var maktlös inför försökte man göra det enda som verkade lika starkt: att ge något av värde, till och med liv, för att blidka dem.

## Det jag tar med mig

Vi vet mer i dag. Vi kan förutsäga ovädret, förklara daggen och bota många av sjukdomarna. Det är jag tacksam för. Men något har vi kanske tappat på vägen: uppmärksamheten.

De som levde här före oss såg på åskan, trädet och hästen och frågade vad de betydde. De gav dem namn och platser i världen, bredvid gudarna och inte under dem. De lät flera förklaringar leva sida vid sida, och de mätte sig själva mot granen på kullen. Det var en människas försök att tyda sin omvärld, med de redskap som fanns. Det är där jag tycker att de är som mest sympatiska.

Nästa gång åskan går, räkna sekunderna som vanligt. Men stanna kvar en stund efteråt och lyssna. En gång var det en gud som körde över himlen.

## Källor

- Den poetiska Eddan, efter Guðni Jónssons utgåva (Eddukvæði, 1949), via heimskringla.no: Þrymskviða 21, Völuspá 17–19, Hávamál 50, Grímnismál 44, Vafþrúðnismál 12 och 14, Rígsþula 8. Översättningarna är gjorda för artikeln och så ordagranna som möjligt.
- Adam av Bremen, *Gesta Hammaburgensis ecclesiae pontificum*, bok IV, kap. 26–27, med anteckningen om trädet vid templet i Uppsala (1070-talet).
- Hellquist, E. 1922. *Svensk etymologisk ordbok*, uppslagsordet åska.
- Samnordisk runtextdatabas, version 3.1 (ODbL): Vg 150 och namnen på runstenarna.
- Bilder: se bildtexterna."""

title_en = "When the Thunder Had a Name"
summary_en = ("A personal article about a way of reading the world that began with the nature around: the thunder that drove "
              "across the sky, the trees that people were made from, the horses that drew day and night. And about what we "
              "cannot follow.")

body_en = f"""Anyone who has stood outside as a thunderstorm rolls in knows the feeling. The air turns heavy and still, the birds fall silent, and then comes the rumble, first far away and then right overhead. I know what thunder is: electricity discharging between cloud and ground. Still I count the seconds between the flash and the crack, as everyone does, and feel small.

The people who raised the runestones had no meteorology. They had the thunder, and they gave it a name. The Old Norse word *þórr* means thunder, and the god and the sound were the same word. Swedish *tordön*, thunder's din, still carries his name, and *åska*, the Swedish word for thunder, is usually explained as an old word for the god's drive across the sky.

In the Eddic poem about how Thor fetches back his hammer, we hear what it sounded like when he drove:

> {THRYM21}

“At once the goats were driven home and hurried to the shafts; they were to run well. Mountains broke, the earth burned in flames, Odin's son drove to the land of the giants.”

It is a thunderstorm, seen by someone standing in the middle of it: mountains that split, ground that burns where the lightning strikes. It is not an explanation in our sense. It is a way of turning something beyond understanding into someone you can relate to, a force with a name and a will.

{IMG_WINGE_EN}

## People made of wood

What strikes me most in reading the old poems is how close people stand to the rest of the world. In Völuspá the first humans are not made of clay or from a rib. The gods find them on the shore, as two trees:

> {VSP17}

“Until three came out of that host, strong and loving Æsir, to the house. They found on land, nearly powerless, Ask and Embla, without fate.”

Ask is a tree, and Embla has been read as another. Only when the gods give them breath, spirit and the warmth of life do they become people: *önd gaf Óðinn*, breath gave Odin. We are, in that story, made of the same wood as the forest around us.

And the world itself is a tree. The next stanza tells of the ash Yggdrasil:

> {VSP19}

“An ash I know standing, it is called Yggdrasil, a high tree, drenched with white clay. From there comes the dew that falls in the valleys. It stands ever green over Urd's well.”

The morning dew comes from the world tree. Adam of Bremen, who wrote about the Swedes in the 1070s, tells that by the temple at Uppsala stood a huge tree that was green in winter and summer alike, and that no one knew what kind of tree it was.

{IMG_BAGGE_EN}

The trees also spoke of people. Hávamál says:

> {HAV50}

“The fir withers that stands on the bare hill; neither bark nor needles shelter it. So it is with the one whom no one loves. How long shall such a one live?”

Anyone who has seen a lone pine on a rock knows what the poem means. Nature was not only something to explain. It was also something to explain oneself by.

## Horses, hawks and hounds

In Grímnismál, Odin lists the foremost of every kind:

> {GRIM44}

“The ash Yggdrasil is the foremost of trees, and Skíðblaðnir of ships, Odin of the Æsir, and of horses Sleipnir, Bifröst of bridges, and Bragi of poets, Hábrók of hawks, and of hounds Garm.”

I like that stanza. The tree, the ship, the god, the horse, the bridge, the poet, the hawk and the hound stand in one row, each the best of its kind. The world is not divided into the holy and the rest. The horse has a place beside the god.

Day and night were horses too. Skinfaxi draws the day across the sky, and his mane lights up the earth. Hrímfaxi draws the night:

> {VAF14}

“Hrímfaxi is the one who draws each night over the good gods. Foam from the bit he lets fall every morning; from there comes the dew in the valleys.”

Here the dew is the foam of the night's horse. A moment ago it came from the world tree. No one seems to have needed to choose between the explanations. It was not a doctrine to be held together, but attempts to understand, side by side. The ravens Huginn and Muninn, which I wrote about in [The Raven Called Memory]({KORPEN_EN}), flew out over the world every day and came back with what they had seen.

It shows on the runestones too. Of the {N:,} runestones in Vitki's Swedish corpus, {N_ANIMAL} name someone who carried an animal in their name, more than one stone in five: a Björn or a Torbjörn (bear), an Ulv or a Gunnulv (wolf), an Arnfast (eagle), an Orm (serpent), a Hrafn (raven). About one stone in seven names a bear. People gave their children the names of animals, and perhaps something of their strength.

## Thor on the stones

When most runestones were raised, many people had already become Christian. Still, {N_THOR} stones, more than one in eight, name someone who carried Thor in their name: Torsten, Torbjörn, Tora. And on a stone in Västergötland, at Velanda, the text ends with a prayer to the thunder:

> {VG150_SHOW}

“Tyrve raised the stone in memory of Agmund, her husband, a very good thegn. May Thor hallow.”

A woman has raised a stone for her husband and asks the force that moves in the storm to protect it.

{IMG_VEL_EN}

## What we cannot follow

I do not want to make this world more beautiful than it was. Adam of Bremen tells that at Uppsala, every ninth year, nine of every kind of male creature were sacrificed, people too, and the bodies hung in the grove by the temple. Adam never went there himself and wrote from what others told him, and scholars read him with care. But the sacrifice, the *blót*, was real, and it cost lives.

The world was also unjust in a way that was built in. In Rígsþula the thrall's son is born, and the poem describes him like this:

> {RIG8}

“He began to grow and thrive well. On his hands the skin was wrinkled, the knuckles crooked, the fingers thick, the face ugly, the back bent, the heels long.”

The poem explains why some are born to toil and others to power, and it seems to find that right. There I cannot follow.

But I can understand where it came from. It was a hard and unforgiving world. A poor harvest meant hunger, a hard winter death, a storm at sea that someone never came home. No one knew why sickness came or why the rain failed. Against forces they were powerless before, people tried the one thing that seemed as strong: to give something of value, even life, to appease them.

## What I take with me

We know more today. We can forecast the storm, explain the dew and cure many of the sicknesses. I am grateful for that. But perhaps we have lost something along the way: attention.

Those who lived here before us looked at the thunder, the tree and the horse and asked what they meant. They gave them names and places in the world, beside the gods and not beneath them. They let several explanations live side by side, and they measured themselves against the fir on the hill. It was a person's attempt to read the world around them, with the tools there were. That is where I find them most sympathetic.

Next time the thunder rolls, count the seconds as usual. But stay a while afterwards and listen. Once it was a god driving across the sky.

## Sources

- The Poetic Edda, after Guðni Jónsson's edition (Eddukvæði, 1949), via heimskringla.no: Þrymskviða 21, Völuspá 17–19, Hávamál 50, Grímnismál 44, Vafþrúðnismál 12 and 14, Rígsþula 8. The translations are made for this article and are as literal as possible.
- Adam of Bremen, *Gesta Hammaburgensis ecclesiae pontificum*, book IV, ch. 26–27, with the note on the tree by the temple at Uppsala (1070s).
- Hellquist, E. 1922. *Svensk etymologisk ordbok*, under åska.
- Scandinavian Runic-text Database, version 3.1 (ODbL): Vg 150 and the names on the runestones.
- Images: see the captions."""

# ---- kontroller ---------------------------------------------------------------------------------------
for b_ in (body, body_en):
    assert "religion" not in b_.lower() and "religiö" not in b_.lower()  # Viktor: not the word for this
    assert not re.search(r"^\|", b_, re.M) and ":::" not in b_  # no tables; a personal essay has no summary box
assert body_en.count("## ") == body.count("## ")
LABELS = ["Personligt", "Tro och magi", "Eddan"]
assert blog_labels.check(LABELS) is None

out = {"slug": "nar-askan-hade-ett-namn", "title": title, "summary": summary, "body": body,
       "title_en": title_en, "summary_en": summary_en, "body_en": body_en, "labels": LABELS}
json.dump(out, open(os.path.join(ROOT, "utdata", "blogg", "naturen.json"), "w"), ensure_ascii=False, indent=1)
print(os.path.join(ROOT, "utdata", "blogg", "naturen.json"), len(body.split()), "ord", len(body_en.split()), "words",
      "| djurnamn", N_ANIMAL, "björn", N_BEAR, "ulv", N_WOLF, "tor", N_THOR)

if {"--update", "--write"} & set(sys.argv):
    from api.routers import blog
    col = blog.firestore().collection(blog.COLLECTION)
    now = dt.datetime.now(dt.timezone.utc)
    if "--write" in sys.argv:
        assert not [p for p in blog._all() if p.get("slug") == out["slug"]], "Adressen används redan; skriv över med --update"
        ref = col.document()
        ref.set({**out, "published": False, "month": now.strftime("%Y-%m"), "author": "Viktor Kvant",
                 "topic": "Personligt|naturen", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    else:
        doc = sys.argv[sys.argv.index("--update") + 1]
        ref = col.document(doc)
        old = ref.get().to_dict()
        assert old and old.get("slug") == out["slug"], "Fel dokument"
        assert not old.get("published"), "Bara opublicerade utkast skrivs över härifrån"
        ref.set({**out, "updatedAt": now}, merge=True)
        print("uppdaterat utkast:", doc)
    blog._forget()
