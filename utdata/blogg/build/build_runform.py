"""Artikeln "Varför ser runorna ut som de gör?" (sv + en), inledningen till runserien. Vitkis eget bidrag: hur många ljud
varje runa fick bära efter övergången från 24 till 16 runor, mätt i hela det svenska runstensmaterialet (låst plan
analysplaner/2026-11-17-runornas-form.md, sha 2fc45b76; utdata/runform/resultat.json). Varje citat kontrolleras mot
källans text (tidskrifterna i sok.sqlite); litteraturkontrollen i /Volumes/2TB/Antigrvity/Runes/downloads/runform_lit/.
    ../../../.venv/bin/python build_runform.py [--write | --update DOC]"""
import datetime as dt
import json
import os
import re
import sqlite3
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_labels, commons  # noqa: E402
from utdata.norge.citat import letters  # noqa: E402

R = json.load(open(os.path.join(ROOT, "utdata", "runform", "resultat.json"), encoding="utf-8"))
assert R["sha"] == "2fc45b76"
RD = {r["signum"]: r for r in json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["inscriptions"]}

# ---- the numbers ------------------------------------------------------------------------------------------------------
Y, O = R["D1"], R["D1b"]
assert Y["ord_anvanda"] == 6424 and O["ord_anvanda"] == 217 and O["inskrifter"] == 284


def share(d, rune, sound):
    return dict(d["runor"][rune]["andelar"]).get(sound, 0.0)


def other(d):
    """Share of all paired runes that stand for another sound than their main one, without þ (þ/ð is the
    normalization's convention, not the carver's choice)."""
    rr = {k: x for k, x in d["runor"].items() if k != "þ"}
    tot = sum(x["n"] for x in rr.values())
    return 1 - sum(x["n"] * x["andelar"][0][1] for x in rr.values()) / tot, tot


OY, NY = other(Y)
OO, NO = other(O)
assert round(100 * OY, 1) == 12.6 and round(100 * OO, 1) == 4.0 and (NY, NO) == (20973, 695)
assert round(100 * share(Y, "k", "g")) == 16 and round(100 * share(Y, "b", "p")) == 25
assert round(100 * share(Y, "u", "o")) == 21 and round(100 * share(Y, "t", "d")) == 8 and round(100 * share(Y, "a", "æ")) == 22
assert round(100 * share(O, "k", "g")) == 3 and share(O, "u", "o") == 0 and share(O, "t", "d") == 0 and round(100 * share(O, "a", "æ")) == 1
assert round(100 * share(O, "e", "e")) == 95 and "b" not in O["runor"]
D3 = R["D3"]
assert D3["pr4_pr5"] == 299 and D3["stenar_med_sakert_stil"] == 1038

# The Ramsund carving, Sö 101: the runes and Rundata's normalization
assert RD["Sö 101"]["transliteration"].startswith("siriþr : kiarþi : bur : þosi")
assert RD["Sö 101"]["normalization"].startswith("\"Sigriðr gærði bro þasi")

# ---- the literature, against the sources (sok.sqlite: key, pdf page) --------------------------------------------------
SOK = sqlite3.connect("/Volumes/2TB/Antigrvity/Runes/downloads/tidskrifter/sok.sqlite")


def jcheck(key, page, *frags):
    text = letters(SOK.execute("select text from pages where key=? and page=?", (key, page)).fetchone()[0])
    for f in frags:
        assert letters(f) in text, (key, page, f)


Q = {"spurk65": "The view of the matter that seems to have the strongest support is 'the Latin theory'",
     "spurk74": "argumentum ex silencio",
     "frid12": "Också horisontella skåror är besvärliga att göra.",
     "frid12b": "När man ristar runor i trä med kniv är det betydligt lättare att rista mot sig än från sig.",
     "frid13": "en kryptisk skrift och ett skriftexperiment",
     "frid205": "Det är lättare att rista vinklar än bågar",
     "aker8": "sker en övergång från den urnordiska 24-typiga runraden till vikingatidens 16-typiga",
     "barnes12": ("I suspect lack of data from the period of transition between the older and younger fuþark would make it "
                  "difficult to judge which theory, if either, had the greater explanatory power"),
     "kall106": ("Det som vi i dag kallar långkvistrunor verkar under vikingatidens två första århundraden ha dominerat i "
                 "Danmark, medan kortkvistrunorna är typiska för Sverige och Norge"),
     "kall114": "som först verkar ha etablerats i slutet av 900-talet",
     "carl40": "kontakten med det skriftkompetenta Rom var avgörande",
     "fw169": "som en lönnskrift",
     "kall135": "medan det i Uppland sannolikt dröjde till efter tiden 1200"}
jcheck("futhark_1_65_381133", 1, Q["spurk65"])            # Spurkland 2010, s. 65
jcheck("futhark_1_65_381133", 10, Q["spurk74"])           # s. 74
jcheck("futhark_6_7_922587", 10, Q["frid12"], Q["frid12b"])  # Fridell 2015, s. 12
jcheck("futhark_6_7_922587", 11, Q["frid13"])             # s. 13
jcheck("futhark_14-15_201_2024379", 5, Q["frid205"])      # Fridell 2025, s. 205
jcheck("futhark_8_7_1333693", 2, Q["aker8"])              # Åkerström 2019, s. 8
jcheck("futhark_4_7_682689", 8, Q["barnes12"])            # Barnes 2013, s. 12
jcheck("futhark_4_102_682693", 8, Q["kall106"])           # Källström 2013, s. 106
jcheck("futhark_4_102_682693", 16, Q["kall114"])          # s. 114
jcheck("futhark_13_5_1847931", 36, Q["carl40"])           # Carlquist 2024, s. 40
jcheck("futhark_11_167_1543732", 3, Q["fw169"])           # Fridell & Williams 2021, s. 169
jcheck("futhark_6_107_922589", 33, Q["kall135"])          # Källström 2015, s. 135

# ---- pictures --------------------------------------------------------------------------------------------------------
INFO = json.load(open(os.path.join(ROOT, "utdata", "blogg", "build", "runform_imgs.json"), encoding="utf-8"))
IMG = {}
for label, f in (("Vimosekammen", "Kam-med-runer-fra-Vimose DO-4148 2000.jpg"),
                 ("Kylverstenen", "Kylverstenen - Historiska museet - DIG 61030.jpg"),
                 ("Ög 136", "Rök runestone (Rök, Ödeshög Municipality, Östergötland, Sweden).jpg"),
                 ("Hs 14", "Hs14 Malsta - kmb.16000300013467.jpg")):
    d = INFO[f]
    assert re.match(r"(CC BY|CC0|Public domain)", d["licence"]), f
    IMG[label] = {**d, "signum": label}
assert IMG["Vimosekammen"]["author"].startswith("Nationalmuseet")
PIC = lambda s, lang: commons.markdown(IMG[s], lang)  # noqa: E731

pc = lambda x: round(100 * x)  # noqa: E731
p1 = lambda x: f"{100 * x:.1f}"  # noqa: E731
f_sv = lambda n: f"{n:,}".replace(",", " ")  # noqa: E731
CHART_SV, CHART_EN = "Diagram: Vitki, efter Rundata (ODbL).", "Chart: Vitki, after Rundata (ODbL)."
ROWS = [("k-runan står för g", "the k-rune stands for g", "k", "g"),
        ("t-runan står för d", "the t-rune stands for d", "t", "d"),
        ("u-runan står för o", "the u-rune stands for o", "u", "o"),
        ("a-runan står för æ", "the a-rune stands for æ", "a", "æ")]


def chart(lang):
    sv = lang == "sv"
    out = [":::chart " + ("Hur ofta en runa står för ett annat ljud än sitt eget" if sv else "How often a rune stands for another sound than its own")]
    for a, b, rune, snd in ROWS:
        out.append("# " + (a if sv else b))
        out.append(f"+{'Yngre futharken' if sv else 'Younger futhark'} | {p1(share(Y, rune, snd))} | "
                   f"{'av' if sv else 'of'} {f_sv(Y['runor'][rune]['n']) if sv else format(Y['runor'][rune]['n'], ',')} {'runor' if sv else 'runes'}")
        out.append(f"{'Äldre futharken' if sv else 'Older futhark'} | {p1(share(O, rune, snd))} | "
                   f"{'av' if sv else 'of'} {O['runor'][rune]['n']} {'runor' if sv else 'runes'}")
    out.append("# " + ("Alla runor utom þ: ett annat ljud än runans eget" if sv else "All runes except þ: another sound than the rune's own"))
    out.append(f"+{'Yngre futharken' if sv else 'Younger futhark'} | {p1(OY)} | {'av' if sv else 'of'} {f_sv(NY) if sv else format(NY, ',')} {'runor' if sv else 'runes'}")
    out.append(f"{'Äldre futharken' if sv else 'Older futhark'} | {p1(OO)} | {'av' if sv else 'of'} {NO} {'runor' if sv else 'runes'}")
    out.append(("Källa: Samnordisk runtextdatabas (Rundata). Yngre futharken: svenska vikingatida runstenar; äldre futharken: "
                "Rundatas urnordiska inskrifter. Varje runa jämförd med Rundatas normalisering, ord för ord. Procent. " + CHART_SV) if sv else
               ("Source: Scandinavian Runic-text Database (Rundata). Younger futhark: Swedish Viking-age runestones; older futhark: "
                "Rundata's Proto-Norse inscriptions. Each rune compared with Rundata's normalization, word by word. Percent. " + CHART_EN))
    return "\n".join(out) + "\n:::"


SLUG = "varfor-ser-runorna-ut-som-de-gor"
title = "Varför ser runorna ut som de gör?"
title_en = "Why do the runes look the way they do?"
summary = ("Runorna är raka streck, nästan utan vågräta linjer, och under vikingatiden fick 16 runor räcka till ett språk med "
           "betydligt fler ljud. Vi följer runorna från de första fynden omkring år 160 till prickarna på 1000-talet – och mäter, "
           "i hela det svenska runstensmaterialet, vad det kostade när runraden krympte.")
summary_en = ("The runes are straight strokes, almost without horizontal lines, and in the Viking Age 16 runes had to serve a "
              "language with many more sounds. We follow the runes from the first finds around AD 160 to the dots of the "
              "eleventh century – and measure, across the whole Swedish runestone material, what it cost when the rune row shrank.")

body = f"""*siriþr : kiarþi : bur : þosi*

Så står det i början av Ramsundsristningen i Södermanland, berghällen med Sigurd Fafnesbane. Rundata normaliserar det till *Sigriðr gærði bro þasi*, ’Sigrid gjorde denna bro’. Den som läser runorna bokstav för bokstav snubblar genast. Ordet *kiarþi* uttalades ungefär *gärði*: runan k står för ett g, i-runan för ett ä och þ för ett ð. I *bur* står u-runan för ett o.

Det beror inte på att ristaren var slarvig. Det beror på hur runorna var gjorda. Den här artikeln följer runorna från början: var de kom ifrån, varför de består av raka streck, och varför vikingarna skrev med bara 16 tecken. Och vi mäter något som vi inte har sett mätt förut, nämligen hur mycket varje runa fick bära.

## De första runorna

De äldsta säkra runinskrifterna är från andra hälften av 100-talet e.Kr. En benkam från mossen i Vimose på Fyn bär ordet *harja* och dateras arkeologiskt till omkring 160. Lansspetsen från Øvre Stabu i Norge låg i en grav från 175–200 (Spurkland, Futhark 1, 2010, s. 77). Runorna är alltså nästan tvåtusen år gamla, och de dyker först upp i södra Skandinavien, på lösa föremål.

{PIC("Vimosekammen", "sv")} Kammen från Vimose, omkring år 160. Runorna lyder *harja*.

Var de kom ifrån är omdiskuterat, men en förklaring har starkast stöd. Terje Spurkland skriver: ”{Q['spurk65']}” (Futhark 1, 2010, s. 65) – alltså att runorna bygger på det latinska alfabetet. Flera runor liknar latinska bokstäver: f, r, s, b och m. Under 1900-talet föreslogs också grekiska och norditaliska förebilder, och Gad Rausing räknar upp alla tre teorierna (Fornvännen 1992, s. 200). Jonas Carlquist håller det för mycket troligt att ”{Q['carl40']}” (Futhark 13, 2024, s. 40). Vem som gjorde runraden, och var, vet ingen.

## Raka streck

Det första man ser är att runorna består av raka streck. Det finns nästan inga bågar och nästan inga vågräta linjer. Där latinet har ett vågrätt streck, som i F, H, L och T, har runan ett snett.

Den vanligaste förklaringen är träet. Staffan Fridell skriver: ”{Q['frid12b']} {Q['frid12']}” (Futhark 6, 2015, s. 12). Ett vågrätt snitt följer träets fibrer och syns dåligt. Ett snett eller lodrätt snitt går tvärs över dem.

Men det är en förklaring utan direkta bevis. Trä från runornas första århundraden är nästan aldrig bevarat, och de äldsta fynden är av metall och ben. Spurkland påpekar att de som hävdar träteorin har fått lita till ett *{Q['spurk74']}*, ett argument ur tystnad (s. 74). Fridell har senare nyanserat bilden: de sneda strecken passar träet, men att bågar blev vinklar förklaras snarare av metallen – ”{Q['frid205']}” (Futhark 14–15, 2025, s. 205). Runornas form kan alltså vara ett arv från både kniven i träet och stiftet i metallen.

## Runraden

Runorna ordnades i en bestämd följd, futharken, efter de sex första: f, u, þ, a, r, k. Den äldre futharken hade 24 runor i tre grupper. Den äldsta hela runraden finns på Kylverstenen från Gotland, som brukar dateras till omkring år 400. Om den skulle verka magiskt eller var ett minnesstöd är omstritt: Bernard Mees beskriver den traditionella magiska tolkningen (Futhark 7, 2016, s. 15), Carlquist håller ett minnesstöd för troligare (Futhark 13, 2024, s. 9).

{PIC("Kylverstenen", "sv")} Kylverstenen från Gotland, med hela den äldre runraden.

Den äldre futharken användes i hela det germanska området. I England fick den nya runor för nya vokaler och blev den angelsaxiska *futhorc*. I Skandinavien gick det åt andra hållet.

## Från 24 till 16 runor

Omkring år 700 bytte skandinaverna runrad. Hanna Åkerström sammanfattar: ”runt år 700 {Q['aker8']}” (Futhark 8, 2019, s. 8). Det säkraste fyndet från den nya raden är ett kranium från Ribe med en inskrift från omkring 725–750.

Det märkliga är att raden krympte medan språket fick fler ljud. Runor för g, d, p, e och o försvann. Varför är en öppen fråga. Kurt Braunmüller ser en medveten reform, Michael Schulte en gradvis utveckling, och Michael Barnes tror inte att frågan går att avgöra: ”{Q['barnes12']}” (Futhark 4, 2013, s. 12).

## Vad krympningen kostade

Hur mycket fick då varje runa bära? Det har vi mätt. Vi lade varje runa på de svenska vikingatida runstenarna bredvid Rundatas normalisering av samma ord, det vill säga utgivarnas tolkning av hur orden lät. Det blev {f_sv(Y['ord_anvanda'])} ord och drygt {f_sv(NY)} runor. Samma sak gjorde vi med de urnordiska inskrifterna, skrivna med den äldre futharken.

{chart("sv")}

Med den äldre futharken stod en runa nästan alltid för sitt eget ljud: {p1(OO).replace('.', ',')} procent av runorna står för ett annat ljud än runans eget, ungefär en på tjugofem. Med den yngre är det {p1(OY).replace('.', ',')} procent, ungefär en på åtta. k-runan står för ett g var sjätte gång, b-runan för ett p var fjärde, u-runan för ett o var femte och a-runan för ett æ nästan lika ofta. Med den äldre futharken hade g, d, p och o egna runor, och där står k-runan för g bara {pc(share(O, 'k', 'g'))} gånger av hundra.

För läsaren betyder det att varje runtext är en liten gåta. *kiarþi* kan bara läsas som *gærði* om man redan vet vilket ord det borde vara. Det är som att skriva svenska utan g, d och p, och lita på att läsaren förstår.

## Långkvist, kortkvist och stavlösa

Den yngre futharken fanns i flera former. Magnus Källström skriver: ”{Q['kall106']}” (Futhark 4, 2013, s. 106). Kortkvistrunorna har kortare bistavar och är snabbare att rista. Rökstenen i Östergötland, från början av 800-talet, är ristad med dem, och på samma sten står ett avsnitt med den äldre futharkens runor. Det ses allmänt ”{Q['fw169']}”, skriver Fridell och Henrik Williams (Futhark 11, 2021, s. 169) – ett äldre skriftsystem som bara ett fåtal kunde läsa.

{PIC("Ög 136", "sv")}

Längst gick de stavlösa runorna i Hälsingland, där runorna har förlorat sina huvudstavar och bara bistavarna är kvar. Fridell ser dem inte som en snabbskrift utan som ”{Q['frid13']}” (Futhark 6, 2015, s. 13). Det är omdiskuterat. Under senvikingatiden tog långkvistrunorna över också i Sverige, och det är dem vi ser på de flesta runstenarna.

{PIC("Hs 14", "sv")} Malstastenen i Hälsingland, ristad med stavlösa runor.

## Prickarna

Lösningen på den krympta runraden kom inifrån. Ristarna började sätta en prick, ett sting, i en runa för att visa att den stod för ett annat ljud: en stungen i blev e, en stungen k blev g och en stungen u blev y. De stungna runorna verkar enligt Källström ha etablerats i slutet av 900-talet: de är de stungna runorna, ”{Q['kall114']}” (s. 114), och under vikingatiden var det främst e, g och y som användes (s. 116). Prickarna tog alltså tillbaka en del av det som försvann omkring 700.

Under medeltiden byggdes systemet ut till en runrad för latinets alla ljud, men i olika takt. I Västergötland tycks det medeltida systemet ha varit etablerat under senare delen av 1100-talet, ”{Q['kall135']}” (Källström, Futhark 6, 2015, s. 135). På Gotland och i Dalarna levde runorna kvar mycket länge, i Dalarna in på 1800-talet.

## Svagheterna

- **Normaliseringen är en tolkning.** Rundatas normalisering är utgivarnas bedömning av hur orden lät, inte ett oberoende mått på ljuden. Vi har jämfört runorna med den.
- **Bara en del av orden går att para.** Vi jämförde bara avsnitt där runtexten och normaliseringen har lika många ord, och utan osäkra runor och personnamn: {f_sv(Y['ord_anvanda'])} ord. Den äldre futharken bygger på {O['ord_anvanda']} ord ur {O['inskrifter']} inskrifter, och siffrorna där är därför osäkrare.
- **Þ-runan är utelämnad i sammanfattningen.** Normaliseringen skiljer mellan þ och ð på ett sätt som är en konvention, inte ristarens val.
- **Vi har försökt mäta när prickarna slog igenom** stilgrupp för stilgrupp, men Rundatas normalisering skriver de flesta e-ljud som *æ*, och underlaget blev för tunt för att användas.
- **Det mesta i berättelsen är känt.** Ursprunget, formerna och övergången är forskningens resultat, med källor i texten. Vårt bidrag är måttet på hur mycket runorna fick bära.

Det här är första delen i vår serie om runorna, där varje runa får en egen artikel i futharkens ordning, och nästa gång börjar vi med fé, den första.

:::box Det viktigaste i korthet
- Runorna är nästan tvåtusen år gamla. De äldsta säkra fynden är från omkring år 160, i södra Skandinavien, och de flesta forskare menar att de bygger på det latinska alfabetet.
- De raka, sneda strecken förklaras oftast med att runorna ristades med kniv i trä, men belägget är indirekt; metallen kan också ha format dem.
- Omkring år 700 krympte runraden från 24 till 16 tecken, medan språket fick fler ljud. Varför är fortfarande omstritt.
- Vi har mätt vad det kostade: med den yngre futharken står ungefär var åttonde runa för ett annat ljud än sitt eget, mot var tjugofemte med den äldre. k står för g, b för p, u för o. Prickarna på 1000-talet tog tillbaka en del av det som försvann.
:::

## Källor

- Samnordisk runtextdatabas (Rundata), Institutionen för nordiska språk, Uppsala universitet. Open Database License.
- Spurkland, Terje 2010. The Older Fuþark and Roman Script Literacy. *Futhark* 1, s. 65–84.
- Rausing, Gad 1992. On the origin of the runes. *Fornvännen* 87, s. 200–205. CC BY 4.0.
- Carlquist, Jonas 2024. Runskrift på fibulor: Ett tidigt germanskt skriftbruk. *Futhark* 13, s. 5–54. CC BY 4.0.
- Fridell, Staffan 2015. Tendenser i skrifttecknens utveckling: Alfabet och runor. *Futhark* 6, s. 7–19.
- Fridell, Staffan 2025. De äldre runornas bildning. *Futhark* 14–15, s. 201–206. CC BY 4.0.
- Mees, Bernard 2016. The Hogganvik Inscription and Early Nordic Memorialisation. *Futhark* 7, s. 7–28. CC BY 4.0.
- Åkerström, Hanna 2019. Det tidigvikingatida runmaterialet: En inventering. *Futhark* 8, s. 7–88. CC BY 4.0.
- Barnes, Michael P. 2013. What Is Runology, and Where Does It Stand Today? *Futhark* 4, s. 7–30.
- Källström, Magnus 2013. Vikingatida och medeltida skrifttraditioner. *Futhark* 4, s. 102–128.
- Källström, Magnus 2015. Gravhällsfragmentet från Tornby. *Futhark* 6, s. 107–142.
- Fridell, Staffan och Henrik Williams 2021. De äldre runorna på Rökstenen. *Futhark* 11, s. 167–171. CC BY 4.0.
- Futhark 1–6 har licensen CC BY-NC-ND; vi citerar kort med källa. Alla volymer finns fritt på [futhark-journal.com](https://www.futhark-journal.com/).
- Analysplanen (låst före räkningen) och koden finns öppet på [GitHub](https://github.com/Precatio/runes/blob/main/analysplaner/2026-11-17-runornas-form.md).
- Foton: Wikimedia Commons, med fotograf och licens i bildtexterna."""

body_en = f"""*siriþr : kiarþi : bur : þosi*

So begins the Ramsund carving in Södermanland, the rock face with Sigurd the dragon-slayer. Rundata normalizes it as *Sigriðr gærði bro þasi*, ‘Sigríðr made this bridge’. Anyone who reads the runes letter by letter stumbles at once. The word *kiarþi* was pronounced roughly *gærði*: the k-rune stands for a g, the i-rune for an æ and þ for a ð. In *bur* the u-rune stands for an o.

That is not because the carver was careless. It is because of how the runes were made. This article follows the runes from the beginning: where they came from, why they are made of straight strokes, and why the Vikings wrote with only 16 signs. And we measure something we have not seen measured before: how much each rune had to carry.

## The first runes

The oldest certain runic inscriptions date from the second half of the second century AD. A bone comb from the bog at Vimose on Funen carries the word *harja* and is archaeologically dated to around 160. The spearhead from Øvre Stabu in Norway lay in a grave from 175–200 (Spurkland, Futhark 1, 2010, p. 77). The runes are thus almost two thousand years old, and they first appear in southern Scandinavia, on portable objects.

{PIC("Vimosekammen", "en")} The comb from Vimose, around AD 160. The runes read *harja*.

Where they came from is debated, but one explanation has the strongest support. Terje Spurkland writes: “{Q['spurk65']}” (Futhark 1, 2010, p. 65) – that is, the runes are based on the Latin alphabet. Several runes resemble Latin letters: f, r, s, b and m. In the twentieth century Greek and North Italic models were proposed too, and Gad Rausing lists all three theories (Fornvännen 1992, p. 200). Jonas Carlquist holds it very likely that contact with literate Rome was decisive (Futhark 13, 2024, p. 40). Who made the rune row, and where, nobody knows.

## Straight strokes

The first thing one sees is that the runes are made of straight strokes. There are almost no curves and almost no horizontal lines. Where Latin has a horizontal stroke, as in F, H, L and T, the rune has a slanting one.

The usual explanation is wood. Staffan Fridell writes that when you carve runes in wood with a knife it is much easier to cut towards yourself than away from yourself, and that horizontal cuts are troublesome (Futhark 6, 2015, p. 12). A horizontal cut follows the grain and shows poorly. A slanting or vertical cut goes across it.

But it is an explanation without direct proof. Wood from the runes' first centuries is almost never preserved, and the oldest finds are of metal and bone. Spurkland notes that those who argue the wood theory have had to rely on an *{Q['spurk74']}*, an argument from silence (p. 74). Fridell has since refined the picture: the slanting strokes suit wood, but curves turning into angles are better explained by metal – it is easier to carve angles than curves in metal (Futhark 14–15, 2025, p. 205). The shape of the runes may thus be a legacy of both the knife in wood and the point in metal.

## The rune row

The runes were ordered in a fixed sequence, the futhark, after the first six: f, u, þ, a, r, k. The older futhark had 24 runes in three groups. The oldest complete rune row is on the Kylver stone from Gotland, usually dated to around AD 400. Whether it was meant to work as magic or was an aid to memory is debated: Bernard Mees describes the traditional magical reading (Futhark 7, 2016, p. 15), Carlquist thinks an aid to memory more likely (Futhark 13, 2024, p. 9).

{PIC("Kylverstenen", "en")} The Kylver stone from Gotland, with the whole older rune row.

The older futhark was used throughout the Germanic world. In England it gained new runes for new vowels and became the Anglo-Saxon *futhorc*. In Scandinavia things went the other way.

## From 24 to 16 runes

Around 700 the Scandinavians changed their rune row. Hanna Åkerström sums it up: around 700 there was a transition from the Proto-Norse 24-rune row to the Viking Age's 16-rune row (Futhark 8, 2019, p. 8). The surest find with the new row is a skull fragment from Ribe with an inscription from around 725–750.

The strange thing is that the row shrank while the language gained more sounds. Runes for g, d, p, e and o disappeared. Why is an open question. Kurt Braunmüller sees a deliberate reform, Michael Schulte a gradual development, and Michael Barnes doubts that the question can be settled: “{Q['barnes12']}” (Futhark 4, 2013, p. 12).

## What the shrinking cost

How much, then, did each rune have to carry? We have measured it. We set each rune on the Swedish Viking-age runestones beside Rundata's normalization of the same word – the editors' reading of how the words sounded. That came to {Y['ord_anvanda']:,} words and more than {NY:,} runes. We did the same with the Proto-Norse inscriptions, written with the older futhark.

{chart("en")}

With the older futhark a rune almost always stood for its own sound: {p1(OO)} per cent of the runes stand for another sound than the rune's own, about one in twenty-five. With the younger it is {p1(OY)} per cent, about one in eight. The k-rune stands for a g one time in six, the b-rune for a p one time in four, the u-rune for an o one time in five and the a-rune for an æ almost as often. In the older futhark g, d, p and o had runes of their own, and there the k-rune stands for g only {pc(share(O, 'k', 'g'))} times in a hundred.

For the reader this means that every runic text is a small riddle. *kiarþi* can only be read as *gærði* if one already knows which word it ought to be. It is like writing English without g, d and p, and trusting the reader to understand.

## Long-branch, short-twig and staveless

The younger futhark came in several forms. Magnus Källström writes that what we now call long-branch runes seem to have dominated in Denmark in the first two centuries of the Viking Age, while the short-twig runes are typical of Sweden and Norway (Futhark 4, 2013, p. 106). The short-twig runes have shorter side-strokes and are quicker to carve. The Rök stone in Östergötland, from the early ninth century, is carved with them, and the same stone has a passage in the runes of the older futhark. That passage is generally seen as a cipher, write Fridell and Henrik Williams (Futhark 11, 2021, p. 169) – an older writing system that only a few could read.

{PIC("Ög 136", "en")}

Furthest went the staveless runes in Hälsingland, where the runes have lost their main staves and only the side-strokes remain. Fridell sees them not as a shorthand but as “a cryptic script and a writing experiment” (“{Q['frid13']}”, Futhark 6, 2015, p. 13). That is debated. In the late Viking Age the long-branch runes took over in Sweden too, and they are what we see on most runestones.

{PIC("Hs 14", "en")} The Malsta stone in Hälsingland, carved with staveless runes.

## The dots

The answer to the shrunken rune row came from within. Carvers began to put a dot, a prick, in a rune to show that it stood for another sound: a dotted i became e, a dotted k became g and a dotted u became y. According to Källström the dotted runes seem to have been established at the end of the tenth century (p. 114), and in the Viking Age it was mainly e, g and y that were used (p. 116). The dots thus won back part of what was lost around 700.

In the Middle Ages the system was expanded into a rune row for all the sounds of Latin, but at different speeds. In Västergötland the medieval system seems to have been established in the later twelfth century, while in Uppland it probably took until after 1200 (Källström, Futhark 6, 2015, p. 135). On Gotland and in Dalarna the runes lived on very long, in Dalarna into the nineteenth century.

## The weaknesses

- **The normalization is an interpretation.** Rundata's normalization is the editors' judgement of how the words sounded, not an independent measure of the sounds. We have compared the runes with it.
- **Only some of the words can be paired.** We compared only sections where the runic text and the normalization have the same number of words, and without uncertain runes and personal names: {Y['ord_anvanda']:,} words. The older futhark rests on {O['ord_anvanda']} words from {O['inskrifter']} inscriptions, and the figures there are therefore less certain.
- **The þ-rune is left out of the summary.** The normalization distinguishes þ and ð by a convention, not by the carver's choice.
- **We tried to measure when the dots caught on**, style group by style group, but Rundata's normalization writes most e-sounds as *æ*, and the material became too thin to use.
- **Most of the story is known.** The origin, the shapes and the transition are research results, with sources in the text. Our contribution is the measure of how much the runes had to carry.

This is the first part of our series on the runes, where each rune gets an article of its own in the order of the futhark, and next time we begin with fé, the first.

:::box The essentials in brief
- The runes are almost two thousand years old. The oldest certain finds are from around AD 160, in southern Scandinavia, and most scholars think they are based on the Latin alphabet.
- The straight, slanting strokes are usually explained by carving with a knife in wood, but the evidence is indirect; metal may have shaped them too.
- Around 700 the rune row shrank from 24 to 16 signs, while the language gained more sounds. Why is still debated.
- We have measured what it cost: with the younger futhark about one rune in eight stands for another sound than its own, against one in twenty-five with the older. k stands for g, b for p, u for o. The dots of the eleventh century won back part of what was lost.
:::

## Sources

- Scandinavian Runic-text Database (Rundata), Department of Scandinavian Languages, Uppsala University. Open Database License.
- Spurkland, Terje 2010. The Older Fuþark and Roman Script Literacy. *Futhark* 1, pp. 65–84.
- Rausing, Gad 1992. On the origin of the runes. *Fornvännen* 87, pp. 200–205. CC BY 4.0.
- Carlquist, Jonas 2024. Runskrift på fibulor: Ett tidigt germanskt skriftbruk. *Futhark* 13, pp. 5–54. CC BY 4.0.
- Fridell, Staffan 2015. Tendenser i skrifttecknens utveckling: Alfabet och runor. *Futhark* 6, pp. 7–19.
- Fridell, Staffan 2025. De äldre runornas bildning. *Futhark* 14–15, pp. 201–206. CC BY 4.0.
- Mees, Bernard 2016. The Hogganvik Inscription and Early Nordic Memorialisation. *Futhark* 7, pp. 7–28. CC BY 4.0.
- Åkerström, Hanna 2019. Det tidigvikingatida runmaterialet: En inventering. *Futhark* 8, pp. 7–88. CC BY 4.0.
- Barnes, Michael P. 2013. What Is Runology, and Where Does It Stand Today? *Futhark* 4, pp. 7–30.
- Källström, Magnus 2013. Vikingatida och medeltida skrifttraditioner. *Futhark* 4, pp. 102–128.
- Källström, Magnus 2015. Gravhällsfragmentet från Tornby. *Futhark* 6, pp. 107–142.
- Fridell, Staffan and Henrik Williams 2021. De äldre runorna på Rökstenen. *Futhark* 11, pp. 167–171. CC BY 4.0.
- Futhark 1–6 carry the licence CC BY-NC-ND; we quote briefly with the source. All volumes are freely available at [futhark-journal.com](https://www.futhark-journal.com/).
- The analysis plan (locked before the count) and the code are open on [GitHub](https://github.com/Precatio/runes/blob/main/analysplaner/2026-11-17-runornas-form.md).
- Photos: Wikimedia Commons, with photographer and licence in the captions."""

# ---- checks ----------------------------------------------------------------------------------------------------------
for b, lang in ((body, "sv"), (body_en, "en")):
    assert not re.search(r"^\|", b, re.M), "BlogBody har inga tabeller"
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M)), "varje ruta och diagram ska stängas"
    assert "{" not in b and "}" not in b
    assert ("Det viktigaste i korthet" if lang == "sv" else "The essentials in brief") in b
    assert b.index(":::box") < b.index("## Källor" if lang == "sv" else "## Sources")
    imgs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", b)
    assert len(imgs) == 4 and all(re.match(r"https://(upload|thumb)\.wikimedia\.org/", u) for u in imgs), imgs
labels = ["Forskning", "Språk och stavning", "Datering och stil"]
err = blog_labels.check(labels)
assert err is None, err
out = {"slug": SLUG, "title": title, "summary": summary, "body": body, "title_en": title_en, "summary_en": summary_en,
       "body_en": body_en, "labels": labels}
path = os.path.join(ROOT, "utdata", "blogg", "runform.json")
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
                 "topic": "Forskning|runor", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
