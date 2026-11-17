"""Artikeln "Den goda döden" (sv + en): hur de svenska runstenarna berättar om döden. Låst plan
analysplaner/2026-11-17-den-goda-doden.md (sha b4066e18), resultat utdata/doden/resultat.json (analys.py).
Citaten ur Rundatas normalisering prövas mot data/rundata.json; Nerman 1917 mot tidskrifternas text (sok.sqlite).
    ../../../.venv/bin/python build_doden.py [--write | --update DOC]"""
import datetime as dt
import io
import json
import os
import re
import sqlite3
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_figures, blog_labels, commons  # noqa: E402
from utdata.norge.citat import letters  # noqa: E402

R = json.load(open(os.path.join(ROOT, "utdata", "doden", "resultat.json"), encoding="utf-8"))
assert R["sha"] == "b4066e18"
RD = {r["signum"]: r for r in json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["inscriptions"]}

# ---- the numbers -----------------------------------------------------------------------------------------------------
A = R["A_andel"]
assert (A["k"], A["n"]) == (144, 2321)
S = R["A_satt"]
assert (S["våld"]["n"], S["drunknad"]["n"], S["dopkläder"]["n"], S["sjukdom"]["n"], S["utan sätt"]["n"]) == (37, 6, 6, 2, 93)
ABROAD = sum(v["utomlands"] for v in S.values())
assert ABROAD == 74
assert all(s.startswith("U ") for s in S["dopkläder"]["signa"])
L = R["A_landskap"]
assert (L["G"]["k"], L["G"]["n"], L["Sö"]["k"], L["Sö"]["n"], L["Öl"]["k"], L["Öl"]["n"]) == (7, 42, 42, 363, 0, 154)
B1, B2 = R["B1"], R["B2"]
assert (B1["vald_berom"], B1["vald_n"], B1["ovriga_berom"], B1["ovriga_n"]) == (7, 37, 15, 107)
assert not B1["haller"] and B1["p_holm"] > 0.5
assert (B2["sen_k"], B2["sen_n"], B2["tidig_k"], B2["tidig_n"]) == (27, 480, 68, 586)
assert B2["haller"] and B2["haller_halvor"] and B2["p_holm"] < 0.002 and round(B2["or_mh"], 2) == 0.36
assert B2["utan_U_samma_riktning"] and B2["utan_U"]["p_mh"] > 0.05
pc = lambda k, n: f"{100 * k / n:.0f}"  # noqa: E731
p1 = lambda k, n, sv=True: (f"{100 * k / n:.1f}".replace(".", ",") if sv else f"{100 * k / n:.1f}")  # noqa: E731
assert (p1(68, 586), p1(27, 480)) == ("11,6", "5,6")

# The prayer over time, as published ("Bönen tystnade – men korset stod kvar")
_P = {p["slug"]: p for p in json.load(open(os.path.join(ROOT, "web", "content", "articles.json"), encoding="utf-8"))["posts"]}
assert "Omkring år 1035 bad mer än var tredje runsten Gud om hjälp för den dödes själ. Femtio år senare gjorde bara en av tio det" \
    in _P["2026-10-bonen-tystnade-korset-stod-kvar"]["summary"]

# ---- the inscriptions, verbatim from Rundata's normalization -----------------------------------------------------------
Q = {
    "Sö 179": "ÞæiR foru drængila fiarri at gulli ok austarla ærni gafu, dou sunnarla a \"Særklandi.",
    "U 214": "Hann drunknaði a \"Holms hafi, skræið knarr hans i kaf, þriR æiniR kvamu af.",
    "Sö 318": "Hann §B drunknaði i \"Bagi, harmdauð mykinn.",
    "U 455": "Þau drunknaðu baði.",
    "U 1104": "æftiR \"Sik, es sotdo.",
    "U 614": "Hann vas siukR uti, þa þæiR giald toku a \"Gutlandi.",
    "U 613": "sum do i hvitavaðum. \"Guð hialpi salu hans.",
    "Sö 55": "VaR til \"Ænglands ungR drængR farinn, varð þa hæima at harmi dauðr.",
    "G 111": "Do ung fran oformagum.",
    "U 954": "En \"Sassurr drap hann ok gærði niðingsverk, svæik felaga sinn.",
    "Sö 174": "Þy let fior sitt, flyðu gængiR",
    "G 134": "\"Guð sviki þa, eR hann sviku.",
    "Sö 338": "Hann fioll i orrustu austr i \"Garðum, liðs forungi, landmanna bæztr.",
}
for s, q in Q.items():
    norm = re.sub(r"\s+", " ", RD[s]["normalization"])
    assert q in norm, (s, q)
assert "sik sialfan ok sun sinn" in RD["Sö 55"]["normalization"]  # the father raised the stone for himself and the son

# ---- Nerman 1917, Fornvännen 12 (pdf page → printed page: pdf 5 = p. 229, pdf 6 = p. 230) -------------------------
SOK = sqlite3.connect("/Volumes/2TB/Antigrvity/Runes/downloads/tidskrifter/sok.sqlite")


def jcheck(key, page, *frags):
    text = letters(SOK.execute("select text from pages where key=? and page=?", (key, page)).fetchone()[0])
    for f in frags:
        assert letters(f) in text, (key, page, f)


jcheck("1917_226", 5, "Oden dör sotdöd, märker sig med spjutsudd", "229")
jcheck("1917_226", 6, "dödas av en oxe", "hänges vid Limfjorden", "dör genom fall från hästen vid blotfäst", "brännes inne", "230")

# ---- pictures ----------------------------------------------------------------------------------------------------------
from PIL import Image  # noqa: E402

BILDER = os.path.join(ROOT, "utdata", "blogg", "bilder")


def frozen(path):
    buf = io.BytesIO()
    Image.open(path).convert("RGB").save(buf, "PNG", optimize=True)
    return blog_figures.freeze(buf.getvalue())


STEN = {l: frozen(os.path.join(BILDER, f"sten_U_1104_{l}.png")) for l in ("sv", "en")}
APP = {"sv": (f"![Stensidan för U 1104 i Vitki, med texten om Sik som dog sotdöd]({STEN['sv']})\n"
              "Bild: Vitki, stensidan för U 1104 i Tuna, Uppland, under Inskrifter. Varje sten i artikeln går att öppna så: "
              "runorna som de står, Rundatas normalisering och översättning."),
       "en": (f"![The stone page for U 1104 in Vitki, with the text about Síkr who died from sickness]({STEN['en']})\n"
              "Image: Vitki, the stone page for U 1104 at Tuna, Uppland, under Inscriptions. Every stone in the article can be "
              "opened like this: the runes as they stand, Rundata's normalization and translation.")}
IMGS = {x["signum"]: x for x in commons.stone_images(["Sö 179", "U 214", "U 1036", "Sö 55"])}
for s in ("Sö 179", "U 214", "U 1036", "Sö 55"):
    assert s in IMGS and re.match(r"(CC BY|CC0|Public domain)", IMGS[s]["licence"]), s
PIC = lambda s, lang, extra="": commons.markdown(IMGS[s], lang) + ((" " + extra) if extra else "")  # noqa: E731


def chart(sv):
    rows = [("G", "Gotland", "Gotland"), ("Sö", "Södermanland", "Södermanland"), ("Vg", "Västergötland", "Västergötland"),
            ("Sm", "Småland", "Småland"), ("Ög", "Östergötland", "Östergötland"), ("U", "Uppland", "Uppland"),
            ("Öl", "Öland", "Öland")]
    out = [":::chart " + ("Hur ofta stenen berättar hur den döde dog, per landskap" if sv else
                          "How often the stone tells how the dead died, by province")]
    for k, a, b in rows:
        x = L[k]
        n = f"{x['n']:,}".replace(",", " ") if sv else f"{x['n']:,}"
        out.append(f"{'+' if k in ('G', 'Sö') else ''}{a if sv else b} | {p1(x['k'], x['n'], sv)} | "
                   f"{x['k']} {'av' if sv else 'of'} {n}")
    out.append(("Källa: Samnordisk runtextdatabas (Rundata), svenska vikingatida runstenar, landskap med minst 30 stenar. "
                "Procent. Bild: Vitki.") if sv else
               ("Source: Scandinavian Runic-text Database (Rundata), Swedish Viking-Age runestones, provinces with at least 30 "
                "stones. Per cent. Image: Vitki."))
    out.append(":::")
    return "\n".join(out)


SLUG = "den-goda-doden"
title = "Den goda döden – vad runstenarna säger om hur de dog"
title_en = "The good death – what the runestones say about how they died"
seo_title = "Döden på runstenarna: strid, drunkning och sotdöd"
seo_title_en = "Death on the runestones: battle, drowning, sickness"
summary = ("Bara var sextonde runsten berättar hur den döde dog. Men när de gör det får vi höra om svek och strid, om en knarr "
           "som sjönk och om en son som dog i sina vita dopkläder. Vi har läst alla 144 och räknat: det mesta handlar om var "
           "döden kom, inte hur, och efter 1050 tystnar stenarna om döden.")
summary_en = ("Only one runestone in sixteen tells how the dead person died. But when they do, we hear of betrayal and battle, "
              "of a cargo-ship that sank and of a son who died in his white christening robes. We read all 144 and counted: "
              "most of them say where death came, not how, and after 1050 the stones fall silent about death.")

body = f"""Den som skulle resa en sten efter en död hade bara några rader. Vad väljer man att säga om någon man har förlorat? De flesta valde det enkla: vem som reste stenen, efter vem, och hur de hörde ihop. Bara var sextonde svensk runsten, 144 av 2 321, berättar något om hur eller var den döde dog.

Men de 144 är värda att lyssna på. I dem finns svek och strid, en knarr som sjönk, en mor som dog ifrån sina små barn och en son som dog i sina vita dopkläder. Vi har läst dem en och en och räknat på dem. Det tar ett kort avsnitt. Resten är en läsning.

## Döden var en plats

Det första som slår en är hur sällan stenarna säger *hur* någon dog. Av de 144 nämner 93 bara att den döde dog, och oftast var: i Grekland, i England, österut med Ingvar. Hälften av alla, 74, dog utomlands. Döden var för de efterlevande först och främst en plats, långt borta, dit ingen kunde gå och sörja.

Gripsholmsstenen i Södermanland säger det vackrare än någon annan:

> *ÞæiR foru drængila fiarri at gulli ok austarla ærni gafu, dou sunnarla a Særklandi.*

De for som män fjärran efter guld och gav örnen föda i öster, dog söderut i Serkland.

{PIC("Sö 179", "sv", "Stenen restes av Tola efter hennes son Harald, Ingvars bror.")}

Det är inte en berättelse om hur Harald dog. Det är en berättelse om vad han gjorde innan, och om hur långt bort det var.

## Strid och svek

När stenarna säger hur, är det oftast våld: 37 av de 144. Någon föll, dräptes eller sveks. Turingestenen minns en hirdledare som föll i strid i Gårdarike:

> *Hann fioll i orrustu austr i Garðum, liðs forungi, landmanna bæztr.*

Han föll i strid österut i Gårdarike, hirdens ledare, den bäste av landmän.

Men lika ofta som striden nämns sveket. I Söderby i Uppland står att en viss Sassur dräpte Helge:

> *En Sassurr drap hann ok gærði niðingsverk, svæik felaga sinn.*

Men Sassur dräpte honom och gjorde ett nidingsverk, svek sin felag.

På Aspö i Södermanland förklarar en far varför sonen Björn dog på Gotland: *Þy let fior sitt, flyðu gængiR* – därför miste han livet, följet flydde. Och på Gotland ber föräldrarna efter en son som sveks på en utfärd: *Guð sviki þa, eR hann sviku* – Gud svike dem som svek honom. Det är inte bara sorg. Det är en anklagelse, huggen i sten, där alla kunde läsa den.

Skulle man vänta sig att den som dog i strid fick mer beröm än andra? Vi prövade det. Av dem som dog våldsamt får 7 av 37 ett berömmande ord, som god eller bäst, mot 15 av 107 bland övriga döda. Skillnaden är så liten att den lätt kan vara slumpen. Stenarna gör ingen skillnad: den som dog i strid hedras inte mer än den som dog på annat sätt.

## Havet

Sex stenar säger att den döde drunknade. Det låter få, men det är fler än de som säger något om sjukdom. Vallentunastenen berättar om Ingeborgs man:

> *Hann drunknaði a Holms hafi, skræið knarr hans i kaf, þriR æiniR kvamu af.*

Han drunknade i Holms hav, hans knarr gled ned i djupet, bara tre kom därifrån.

{PIC("U 214", "sv", "Stenen står vid Vallentuna kyrka i Uppland.")}

I Näsby i Uppland reste Ingefast en sten efter både far och mor: *Þau drunknaðu baði* – de drunknade båda. Och vid Sund i Södermanland står att Vred drunknade i Bagi, *harmdauð mykinn*, en död till stor sorg.

## Sotdöden

Bara två stenar säger att den döde dog av sjukdom. En av dem står i Tuna i Uppland, där Sik minns med fyra ord: *es sotdo*, som dog sotdöd.

{APP['sv']}

Ordet är intressant, för det är samma ord som de isländska kungasagorna använder. I Ynglingatal och hos Snorre dör de gamla svenska kungarna på de mest olika sätt. Arkeologen Birger Nerman ställde 1917 upp listan: en kung ”dödas av en oxe”, en ”hänges vid Limfjorden”, en ”dör genom fall från hästen vid blotfäst”, flera ”brännes inne” (Fornvännen 12, s. 230). Och Oden själv ”dör sotdöd, märker sig med spjutsudd” (s. 229) – han dör av sjukdom, men ristar sig med ett spjut innan. Sagan gör döden till en berättelse. Runstenen i Tuna gör den till ett faktum, utan ursäkt och utan spjut.

Den andra stenen är nästan lika kort. Husbjörn *vas siukR uti, þa þæiR giald toku a Gutlandi* – var sjuk ute, när de tog gäld på Gotland.

## I vita kläder

Sex stenar, alla i Uppland, säger att den döde dog *i hvitavaðum*, i vita kläder. Det är dopkläderna, de vita kläder den nydöpte bar. Den som dog i dem dog alltså strax efter dopet, ren, som kristen. Det är kanske det närmaste vi kommer en god död i stenarnas egen mening. I Torsätra reste Una en sten efter sin son Östen:

> *sum do i hvitavaðum. Guð hialpi salu hans.*

som dog i vita kläder. Gud hjälpe hans själ.

{PIC("U 1036", "sv", "Tensta kyrka, Uppland: Helga reste stenen efter sin son Andvätt, som var död i vita kläder.")}

## Hemma

Några få säger att döden kom hemma. De är bland de mest gripande. På Gotland står om Heilfus att han *do hæima ok atti dottur æina* – dog hemma och hade en dotter. I Ardre minns Sibba sin hustru Rodtjud: *Do ung fran oformagum* – hon dog ung ifrån omyndiga barn.

Och i Bjudby i Södermanland reste Torsten en sten efter sig själv och sin son Hävne, som hade klarat resan:

> *VaR til Ænglands ungR drængR farinn, varð þa hæima at harmi dauðr.*

Den unge drängen hade farit till England, blev sedan död hemma, till sorg.

{PIC("Sö 55", "sv")}

Det är en omvänd berättelse mot Gripsholmsstenens. Sonen kom hem från England. Det var hemma han dog.

## När stenarna tystnade

{chart(True)}

Hur ofta stenarna berättar om döden skiljer sig mellan landskapen. På Gotland gör var sjätte det, i Södermanland ungefär var nionde, i Uppland var tjugonde. På Öland gör ingen av 154.

Det tydligaste mönstret är tiden. Bland stenar som stilen daterar före 1050 berättar {p1(68, 586)} procent, ungefär var nionde, om döden. Bland de senare bara {p1(27, 480)} procent, var artonde. Med landskapen hållna lika är oddsen för att stenen berättar om döden ungefär en tredjedel så stora efter 1050. Ett så tydligt mönster skulle uppstå av en slump i färre än ett fall på femhundra. Vi delade också stenarna i två grupper, socken för socken, så att båda fick stenar från samma trakter och ungefär samma tid. Mönstret syns i båda, så det beror inte på några enskilda socknar eller ristare. Utan Uppland pekar det åt samma håll men är för svagt för att stå på egna ben.

Varför? Det prövade vi inte. Två förklaringar ligger nära till hands. De stora färderna, med Ingvar och till Grekland, hör till tiden före 1050, och färderna står för hälften av de döda som stenarna berättar om. Och samma sak hände med bönen: omkring år 1035 bad mer än var tredje runsten för den dödes själ, femtio år senare bara var tionde ([Bönen tystnade – men korset stod kvar](/artiklar/2026-10-bonen-tystnade-korset-stod-kvar/)). Kanske flyttade både döden och bönen in i kyrkan, till begravningen och mässan, och stenen fick säga mindre. Båda förklaringarna är läsningar, inte resultat.

## Den goda döden

Vad var då en god död? Stenarna svarar inte på frågan, och kanske är det själva svaret. De berömmer inte den som föll mer än den som dog hemma. De skäms inte för sotdöden. De anklagar den som svek, och de sörjer den som drunknade. Det de oftast vill att vi ska veta är var det hände, och att någon mindes.

Den som läser stenarna i dag kan pröva samma sak: vad skulle du vilja att det stod om dig, om du bara fick fyra ord?

:::box Det viktigaste i korthet
- Bara var sextonde svensk runsten, 144 av 2 321, berättar hur eller var den döde dog. Hälften av dem dog utomlands, och de flesta stenar säger bara var.
- När sättet nämns är det oftast våld, och lika ofta svek som strid. Drunkning, sjukdom och död i dopkläderna nämns på några få stenar.
- Den som dog i strid fick inte mer beröm än andra döda.
- Efter 1050 berättar stenarna om döden ungefär hälften så ofta som före. Kanske för att färderna tog slut, kanske för att döden, liksom bönen, flyttade in i kyrkan – men det har vi inte prövat.
:::

## Så räknade vi

Vi läste alla svenska vikingatida runstenar där Rundatas översättning säger att den döde dog, och sorterade dem efter regler som skrevs ned och låstes innan något räknades: våld (dräptes, föll, sveks, brändes), drunknad, sjukdom, dopkläder och utan sätt. Två prov var bestämda i förväg: om våldsam död får mer beröm, och om de sena stenarna berättar mer sällan om döden. Det första höll inte, det andra höll. En sten, Vg 40, säger att Gunne ”dog i strid när kungar stred” men räknas enligt planens ordlista som utan sätt, eftersom ordet strid inte stod med; det ändrar inget av proven. Planen och koden ligger öppet på GitHub.

## Källor

- Samnordisk runtextdatabas (Rundata), Institutionen för nordiska språk, Uppsala universitet. Open Database License. Normaliseringarna citeras ordagrant; översättningarna till svenska är våra.
- Nerman, Birger 1917. Ynglingasagan i arkeologisk belysning. *Fornvännen* 12, s. 226–261. CC BY 4.0.
- Analysplanen (låst innan något räknades) och koden: [GitHub](https://github.com/Precatio/runes/blob/main/analysplaner/2026-11-17-den-goda-doden.md).
- Foton: Wikimedia Commons, med fotograf och licens i bildtexterna."""

body_en = f"""Whoever was to raise a stone for the dead had only a few lines. What do you choose to say about someone you have lost? Most chose the simple things: who raised the stone, for whom, and how they were related. Only one Swedish runestone in sixteen, 144 of 2,321, says anything about how or where the dead person died.

But those 144 are worth listening to. In them are betrayal and battle, a cargo-ship that sank, a mother who died leaving her small children and a son who died in his white christening robes. We read them one by one and counted. It takes a short section. The rest is a reading.

## Death was a place

The first thing that strikes you is how rarely the stones say *how* someone died. Of the 144, 93 only say that the dead person died, and usually where: in Greece, in England, in the east with Ingvarr. Half of them, 74, died abroad. For those left behind, death was first of all a place, far away, where no one could go to mourn.

The Gripsholm stone in Södermanland says it more beautifully than any other:

> *ÞæiR foru drængila fiarri at gulli ok austarla ærni gafu, dou sunnarla a Særklandi.*

They travelled valiantly far for gold, and in the east gave food to the eagle, died in the south in Serkland.

{PIC("Sö 179", "en", "The stone was raised by Tóla in memory of her son Haraldr, Ingvarr's brother.")}

It is not a story of how Haraldr died. It is a story of what he did before, and of how far away it was.

## Battle and betrayal

When the stones do say how, it is usually violence: 37 of the 144. Someone fell, was killed or was betrayed. The Turinge stone remembers a leader of a retinue who fell in battle in Garðar:

> *Hann fioll i orrustu austr i Garðum, liðs forungi, landmanna bæztr.*

He fell in battle in the east in Garðar, leader of the retinue, the best of landholders.

But betrayal is named as often as battle. At Söderby in Uppland it says that a certain Sassurr killed Helgi:

> *En Sassurr drap hann ok gærði niðingsverk, svæik felaga sinn.*

And Sassurr killed him and did a villainous deed, betrayed his partner.

On Aspö in Södermanland a father explains why his son Bjôrn died on Gotland: *Þy let fior sitt, flyðu gængiR* – that is why he lost his life, his followers fled. And on Gotland the parents of a son betrayed on a voyage pray: *Guð sviki þa, eR hann sviku* – may God betray those who betrayed him. This is not only grief. It is an accusation, cut in stone, where everyone could read it.

Would you expect those who died in battle to get more praise than others? We tested it. Of those who died violently, 7 of 37 get a word of praise, such as good or best, against 15 of 107 among the other dead. The difference is so small it could easily be chance. The stones make no distinction: those who died in battle are not honoured more than those who died in other ways.

## The sea

Six stones say that the dead person drowned. That sounds few, but it is more than those that mention sickness. The Vallentuna stone tells of Ingibjôrg's husband:

> *Hann drunknaði a Holms hafi, skræið knarr hans i kaf, þriR æiniR kvamu af.*

He drowned in Holmr's sea, his cargo-ship slid into the deep, only three came out of it.

{PIC("U 214", "en", "The stone stands at Vallentuna church in Uppland.")}

At Näsby in Uppland Ingifastr raised a stone for both father and mother: *Þau drunknaðu baði* – they both drowned. And at Sund in Södermanland we read that Vreiðr drowned in Bágr, *harmdauð mykinn*, a death of great grief.

## The straw death

Only two stones say that the dead person died of sickness. One of them stands at Tuna in Uppland, where Síkr is remembered in four words: *es sotdo*, who died of sickness.

{APP['en']}

The word is interesting, because it is the word the Icelandic sagas of kings use. In Ynglingatal and in Snorri the old Swedish kings die in the most varied ways. In 1917 the archaeologist Birger Nerman set out the list: one king is killed by an ox, one is hanged at the Limfjord, one dies by falling from his horse at a sacrificial feast, several are burned inside their halls (Fornvännen 12, p. 230). And Odin himself dies of sickness, marking himself with a spear point (p. 229). The saga makes death a story. The stone at Tuna makes it a fact, without excuse and without a spear.

The other stone is almost as short. Húsbjôrn *vas siukR uti, þa þæiR giald toku a Gutlandi* – was sick abroad, when they took payment on Gotland.

## In white clothes

Six stones, all in Uppland, say that the dead person died *i hvitavaðum*, in white clothes. These are the christening robes, the white clothes the newly baptised wore. Whoever died in them died just after baptism, clean, as a Christian. It is perhaps the closest we come to a good death in the stones' own terms. At Torsätra Una raised a stone for her son Eysteinn:

> *sum do i hvitavaðum. Guð hialpi salu hans.*

who died in white clothes. May God help his soul.

{PIC("U 1036", "en", "Tensta church, Uppland: Helga raised the stone for her son Andvéttr, who died in white clothes.")}

## At home

A few say that death came at home. They are among the most moving. On Gotland we read of Heilfúss that he *do hæima ok atti dottur æina* – died at home and had one daughter. At Ardre Sibba remembers his wife Hróðþjóð: *Do ung fran oformagum* – she died young, leaving children not yet grown.

And at Bjudby in Södermanland Þorsteinn raised a stone for himself and his son Hefnir, who had survived the journey:

> *VaR til Ænglands ungR drængR farinn, varð þa hæima at harmi dauðr.*

The young valiant man had travelled to England, then died at home, to grief.

{PIC("Sö 55", "en")}

It is the reverse of the Gripsholm stone. The son came home from England. It was at home that he died.

## When the stones fell silent

{chart(False)}

How often the stones tell of death varies between provinces. On Gotland one in six does, in Södermanland about one in nine, in Uppland one in twenty. On Öland none of 154 does.

The clearest pattern is time. Among stones that the style dates before 1050, {p1(68, 586, False)} per cent, about one in nine, tell of death. Among the later ones only {p1(27, 480, False)} per cent, one in eighteen. With the provinces held equal, the odds that a stone tells of death are about a third as large after 1050. A pattern this clear would arise by chance in fewer than one case in five hundred. We also split the stones into two groups, parish by parish, so that both got stones from the same areas and roughly the same time. The pattern shows in both, so it does not depend on a few parishes or carvers. Without Uppland it points the same way but is too weak to stand on its own.

Why? We did not test that. Two explanations lie close at hand. The great journeys, with Ingvarr and to Greece, belong to the time before 1050, and the journeys account for half of the deaths the stones tell of. And the same thing happened to the prayer: around 1035 more than one runestone in three prayed for the dead person's soul, fifty years later only one in ten ([The prayer fell silent – but the cross remained](/en/artiklar/2026-10-bonen-tystnade-korset-stod-kvar/)). Perhaps both death and prayer moved into the church, to the burial and the mass, and the stone was left to say less. Both explanations are readings, not results.

## The good death

So what was a good death? The stones do not answer the question, and perhaps that is the answer. They do not praise the one who fell more than the one who died at home. They are not ashamed of the straw death. They accuse the one who betrayed, and they mourn the one who drowned. What they most often want us to know is where it happened, and that someone remembered.

Whoever reads the stones today can try the same thing: what would you want it to say about you, if you only had four words?

:::box The essentials in brief
- Only one Swedish runestone in sixteen, 144 of 2,321, tells how or where the dead person died. Half of those died abroad, and most stones say only where.
- When the manner is given it is usually violence, and betrayal as often as battle. Drowning, sickness and death in christening robes appear on a few stones.
- Those who died in battle did not get more praise than the other dead.
- After 1050 the stones tell of death about half as often as before. Perhaps because the journeys ended, perhaps because death, like the prayer, moved into the church – but we have not tested that.
:::

## How we counted

We read every Swedish Viking-Age runestone where Rundata's translation says the dead person died, and sorted them by rules written down and locked before anything was counted: violence (killed, fell, betrayed, burned), drowned, sickness, christening robes and no manner. Two tests were fixed in advance: whether violent death gets more praise, and whether the late stones tell of death less often. The first did not hold, the second did. One stone, Vg 40, says that Gunni "died in battle when kings fought" but counts as no manner under the plan's word list, because the word battle was not on it; it changes neither test. The plan and the code are open on GitHub.

## Sources

- Samnordisk runtextdatabas (Rundata), Department of Scandinavian Languages, Uppsala University. Open Database License. The normalizations are quoted verbatim; the translations are our own, after Rundata's.
- Nerman, Birger 1917. Ynglingasagan i arkeologisk belysning. *Fornvännen* 12, pp. 226–261. CC BY 4.0.
- The analysis plan (locked before anything was counted) and the code: [GitHub](https://github.com/Precatio/runes/blob/main/analysplaner/2026-11-17-den-goda-doden.md).
- Photos: Wikimedia Commons, with photographer and licence in the captions."""

# ---- checks ----------------------------------------------------------------------------------------------------------
for b, lang in ((body, "sv"), (body_en, "en")):
    assert not re.search(r"^\|", b, re.M), "BlogBody har inga tabeller"
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M)), "varje ruta ska stängas"
    assert "{" not in b and "}" not in b
    assert ("Det viktigaste i korthet" if lang == "sv" else "The essentials in brief") in b
    assert b.index(":::box") < b.index("## Källor" if lang == "sv" else "## Sources")
    imgs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", b)
    assert len(imgs) == 5 and all(re.match(r"https://(upload|thumb)\.wikimedia\.org/|/api/blog/figures/[0-9a-f]{16}\.png$", u)
                                  for u in imgs), imgs
    assert not re.search(r"\bAI\b", b)
    assert "utanför Norden" not in b and "outside Scandinavia" not in b
labels = ["Forskning", "Formler och syfte", "Tro och magi"]
err = blog_labels.check(labels)
assert err is None, err
assert len(seo_title) <= 52 and len(seo_title_en) <= 52
out = {"slug": SLUG, "title": title, "summary": summary, "body": body, "title_en": title_en, "summary_en": summary_en,
       "body_en": body_en, "seo_title": seo_title, "seo_title_en": seo_title_en, "labels": labels}
path = os.path.join(ROOT, "utdata", "blogg", "doden.json")
json.dump(out, open(path, "w"), ensure_ascii=False, indent=1)
print(path, len(body.split()), "ord,", len(body_en.split()), "words")

if "--update" in sys.argv or "--write" in sys.argv:
    from api.routers import blog
    col = blog.firestore().collection(blog.COLLECTION)
    now = dt.datetime.now(dt.timezone.utc)
    if "--update" in sys.argv:
        doc = sys.argv[sys.argv.index("--update") + 1]
        ref = col.document(doc)
        old = ref.get().to_dict()
        assert old and not old.get("published"), "Bara opublicerade utkast skrivs över härifrån"
        ref.set({**out, "updatedAt": now}, merge=True)
        print("uppdaterat utkast:", doc)
    else:
        assert not [p for p in blog._all() if p.get("slug") == out["slug"]], "Adressen används redan; skriv över med --update"
        ref = col.document()
        ref.set({**out, "published": False, "month": now.strftime("%Y-%m"), "author": "Viktor Kvant",
                 "topic": "Forskning|döden", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
