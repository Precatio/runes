"""Artikeln "De nämnde aldrig hemmet" (sv + en), del 2 till "Vad berättar runskrifterna på de brittiska öarna?":
vad de vikingatida inskrifterna utanför Norden säger om det gamla hemmet, enligt den låsta planen
analysplaner/2026-10-30-utvandrarna-och-hemmet.md. Siffrorna låses mot utdata/utvandrarna/resultat.json.
    ../../../.venv/bin/python build_utvandrarna.py [--write | --update DOC]"""
import datetime as dt
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import commons  # noqa: E402

U = os.path.join(ROOT, "utdata", "utvandrarna")
R = json.load(open(os.path.join(U, "resultat.json"), encoding="utf-8"))
recs = {r["signum"]: r for r in json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["inscriptions"]}
nz = lambda s: recs[s]["normalization"].replace('"', "").strip()  # noqa: E731
pc = lambda x: round(100 * x)  # noqa: E731
sh = lambda h: pc(R[h]["share_west"])  # noqa: E731
sn = lambda h: pc(R[h]["share_norway"])  # noqa: E731
de = lambda p, en=False: (f"{p:.2f}" if en else f"{p:.2f}".replace(".", ","))  # noqa: E731

# ---- the locked numbers -----------------------------------------------------------------------------------------------
assert (R["n_west"], R["n_norway"]) == (29, 43)
assert R["H1"]["west"] == [0, 29] and R["H1"]["norway"] == [2, 43]  # "bara två" and not R["H1"]["holds"]
assert R["H2"]["west"] == [13, 29] and R["H2"]["norway"] == [12, 43] and not R["H2"]["holds"]
assert R["H2_nordisk"]["west"] == [6, 29]
assert R["H3"]["west"] == [12, 39] and R["H3"]["norway"] == [18, 88] and not R["H3"]["holds"]
assert R["H4"]["west"] == [1, 29] and R["H4"]["norway"] == [2, 43]
assert R["H5"] == {"pairs": 12, "n->n": 6, "g->g": 4, "n->g": 1, "g->n": 1, "sign_p": 1.0}
SE, DK = R["secondary"]["Sverige"], R["secondary"]["Danmark"]
assert SE["theo_k"] == [1001, 5847] and DK["theo_k"] == [63, 584]
assert sorted(set(R["H3"]["theo_west"])) == ["Ástríðr", "Þor-", "Þorbjôrn", "Þorfinnr", "Þorgerðr", "Þorleifr", "Þorsteinn",
                                             "Þorvaldr", "Þórulfr", "Þúríð"] and R["H3"]["theo_west"].count("Þorbjôrn") == 3
WV = [x for x in json.load(open(os.path.join(ROOT, "utdata", "brittiska", "inskrifter.json"), encoding="utf-8"))
      if x["period"] == "V"]
assert len(WV) == 84
for s, frag in [("IM MM99", "Gautr gerði, sonr Bjarnar frá Kolli"), ("IM MM101", "Gautr gerði þenna ok alla í Môn"),
                ("IM MM135", "Þorleifr Hnakki reisti kross þenna ept Fiak, son sinn"),
                ("IM MM112", "Þorsteinn reisti kross þenna ept Ófeig, son Krínáns"),
                ("IM MM118", "Druian, sonr Dufgals"), ("IM MM128", "Þorvaldr reisti kross þe[nna]"),
                ("N 225", "Þórir Harðarsonr reisti stein þenna ept Ásgerði, kván sína, dóttur Gunnars"),
                ("N 184", "þá's Knútr sótti England"), ("N 62", "miðli Ustaholms ok Garða"),
                ("N 223", "Ulfríkr §A sorgþungr g[erði]"), ("N 68", "Sú var mær hônnurst á Haðalandi"),
                ("UA Fv1914;47", "Grani gærði hvalf þessi æftiR Karl/Kal, felaga sinn"),
                ("By NT1984;32", "[Re]ðu(?) sviar þetta a leiun"), ("GR 76", "Á sæ, sæ, sæ, es Ása/ása sat/sát"),
                ("IM MM141", "Jésu Krist"), ("IM MM138", "Hrossketill vélti í tryggu eiðsvara sinn")]:
    assert frag in nz(s), (s, nz(s))
# Prayers and words for God in the memorial inscriptions (the same urval and pattern as forsta_blick.py, without "cross")
from api.rundata import store  # noqa: E402
PR = re.compile(r"\bGod\b|\bChrist|\bJesus|\bsoul\b|\bspirit\b|\bMary\b|\bholy\b|\bprayer|\bpray", re.I)
MEMO = re.compile(r"in memory of|raised .* (stone|cross)|erected .* cross|made this .* (vault|tomb)|laid this stone", re.I)
SWE = {"U", "Sö", "Ög", "Öl", "Vg", "Sm", "G", "Vs", "Gs", "Nä", "Hs", "M", "Ån", "J", "D", "Vr", "Bo", "Hr"}
_pc = {"west": [0, 0], "Norge": [0, 0], "Sverige": [0, 0]}
for _r in store().inscriptions:
    _p = _r["signum"].split(" ")[0]
    _g = "west" if _p in {"IM", "E", "IR", "Sc", "Or", "Sh"} else "Norge" if _p == "N" else "Sverige" if _p in SWE else None
    _t = _r.get("translation") or _r.get("translation_en") or ""
    if _g and (_r.get("dating") or "").startswith("V") and MEMO.search(_t):
        _pc[_g][1] += 1
        _pc[_g][0] += bool(PR.search(_t))
assert _pc["west"] == [2, 29] and _pc["Norge"] == [5, 43]
PRAY = {"west": _pc["west"][0], "Norge": pc(_pc["Norge"][0] / _pc["Norge"][1]), "Sverige": pc(_pc["Sverige"][0] / _pc["Sverige"][1])}
assert (PRAY["Norge"], PRAY["Sverige"]) == (12, 18)
PART1 = "/artiklar/vad-berattar-runskrifterna-pa-de-brittiska-oarna"
TOR = "/artiklar/tor-foll-hjalten-blev-drang"

# ---- pictures ---------------------------------------------------------------------------------------------------------
THOR_X = "Br Olsen;185A, Andreas.jpg"
SIGURD = "Sigurd on Manx crosses.gif"
BEREZAN = "Berezanj.jpg"
LION = "The Piraeus Lion detail by Asatruar 2011-05-09.jpg"
INFO = commons.commons_info([THOR_X, SIGURD, BEREZAN, LION])
assert INFO[THOR_X]["licence"] == INFO[SIGURD]["licence"] == "Public domain" and "Kermode" in INFO[THOR_X]["author"]
assert INFO[BEREZAN]["licence"] == "CC BY 2.5 se" and INFO[BEREZAN]["author"] == "Pål-Nils Nilsson"
assert INFO[LION]["licence"] == "CC BY-SA 3.0" and INFO[LION]["author"] == "Asatruar"
LIC = {"CC BY 2.5 se": "https://creativecommons.org/licenses/by/2.5/se/deed.en",
       "CC BY-SA 3.0": "https://creativecommons.org/licenses/by-sa/3.0/"}


def pic(f, alt, text, lang):
    i = INFO[f]
    page = "https://commons.wikimedia.org/wiki/File:" + f.replace(" ", "_")
    if i["licence"] == "Public domain":
        cr = ("Fri från upphovsrätt" if lang == "sv" else "Public domain") + f", via [Wikimedia Commons]({page})."
    else:
        cr = (f"{'Foto' if lang == 'sv' else 'Photo'}: {i['author']}, [{i['licence']}]({LIC[i['licence']]}), "
              f"via [Wikimedia Commons]({page}).")
    return f"![{alt}]({i['thumb']})\n{text} {cr}"


def chart_gods(lang):
    sv = lang == "sv"
    of, nm = ("av", "namn") if sv else ("of", "names")
    w, n = R["H3"]["west"], R["H3"]["norway"]
    rows = [":::chart Andel av de nordiska personnamnen i minnesinskrifterna som bär en gud" if sv else
            ":::chart Share of the Norse personal names in the memorial inscriptions that carry a god",
            f"+{'Utvandrarna i väster' if sv else 'The emigrants in the west'} | {pc(w[0] / w[1])} | {w[0]} {of} {w[1]} {nm}",
            f"{'Norge' if sv else 'Norway'} | {pc(n[0] / n[1])} | {n[0]} {of} {n[1]} {nm}",
            f"{'Sverige' if sv else 'Sweden'} | {pc(SE['theo_k'][0] / SE['theo_k'][1])} | {SE['theo_k'][0]:,} {of} {SE['theo_k'][1]:,} {nm}".replace(",", " " if sv else ","),
            f"{'Danmark' if sv else 'Denmark'} | {pc(DK['theo_k'][0] / DK['theo_k'][1])} | {DK['theo_k'][0]} {of} {DK['theo_k'][1]} {nm}",
            ("Källa: vikingatida minnesinskrifter i Samnordisk runtextdatabas; väster och Norge handkodade, Sverige och "
             "Danmark räknade med sökmönster. Namn med Tor-, Ås-, Frey-, Ingi- eller Gud-. Vitkis räkning." if sv else
             "Source: Viking-age memorial inscriptions in the Scandinavian Runic-text Data Base; west and Norway coded by "
             "hand, Sweden and Denmark counted with search patterns. Names with Þór-, Ás-, Frey-, Ingi- or Guð-. Vitki's count.")]
    return "\n".join(rows) + "\n:::"


def chart_kin(lang):
    sv = lang == "sv"
    of = "av" if sv else "of"
    a, b, c = R["H2"]["west"], R["H2_nordisk"]["west"], R["H2"]["norway"]
    rows = [":::chart Minnesinskrifter som säger vems son eller dotter någon var" if sv else
            ":::chart Memorial inscriptions that say whose son or daughter someone was",
            f"+{'Väster, alla föräldrar' if sv else 'West, all parents'} | {pc(a[0] / a[1])} | {a[0]} {of} {a[1]}",
            f"{'Väster, bara nordiska föräldrar' if sv else 'West, Norse parents only'} | {pc(b[0] / b[1])} | {b[0]} {of} {b[1]}",
            f"{'Norge' if sv else 'Norway'} | {pc(c[0] / c[1])} | {c[0]} {of} {c[1]}",
            ("Källa: Samnordisk runtextdatabas, handkodad efter en låst plan; Vitkis räkning." if sv else
             "Source: Scandinavian Runic-text Data Base, coded by hand after a locked plan; Vitki's count.")]
    return "\n".join(rows) + "\n:::"


title = "De nämnde aldrig hemmet – runskrifterna på de brittiska öarna, del 2"
summary = ("Ingen av de 84 vikingatida runinskrifterna på de brittiska öarna nämner det gamla landet. Men utvandrarna "
           "lämnade det inte bakom sig: de skrev som man skrev i Norge, de gav barnen namn efter Tor, och på korsen "
           "slukas Oden av Fenrisulven bredvid Kristus.")

body = f"""*{nz('IM MM128')}* – Torvald reste det här korset.

Mer säger inte texten. Korset står i kyrkan i Andreas på Isle of Man, och det restes någon gång på 900-talet av en man vars namn bär guden Tor. På ena sidan står en man med en fågel på axeln, och en varg slukar honom. Bredvid står ett stort kors och en gestalt som har tolkats som Kristus som besegrar Satan. Mannen läses som Oden, som slukas av Fenrisulven vid Ragnarök. Två världar på samma sten, och i texten bara ett namn.

I [första delen]({PART1}) läste vi alla runinskrifter på de brittiska öarna och frågade vilka som skrev dem. Nu frågar vi något annat. Vad sa de som hade lämnat Norden om det de hade lämnat? Märks saknaden, släkten där hemma, de gamla gudarna? Eller lämnade de allt det bakom sig?

{pic(THOR_X, 'Torvalds kors i Andreas', 'Torvalds kors i Andreas (MM128), tecknat av Philip Kermode i Manx Crosses (1907): korsets två sidor och kanten med runorna. Till höger mannen med fågeln och vargen.', 'sv')}

:::box Kort sagt
- Ingen av de {len(WV)} vikingatida runinskrifterna på de brittiska öarna nämner Norden. De platser som nämns är det nya hemmet: Coll i Hebriderna och Man. Men norska minnesstenar nämner också sällan andra sidan havet, så tystnaden är inte märklig.
- Utvandrarna skrev oftare vems son någon var än man gjorde i Norge – men skillnaden kommer helt från de gaeliska fäderna. Det är grannarnas namnskick, inte ett minne av hemmet.
- {sh('H3')} procent av utvandrarnas nordiska namn bär en gud, mot {sn('H3')} procent i Norge. De gamla gudarna levde vidare i namnen också på de kristna korsen.
- I familjerna behöll tio av tolv barn förälderns språk i namnet.
- Utvandrarna lämnade inte hemmet. De tog det med sig utan att nämna det.
:::

## Hemmet som aldrig nämndes

Börja med det enklaste. Vi gick igenom alla {len(WV)} vikingatida runinskrifter på de brittiska öarna och letade efter Norge, Danmark, Sverige, Gotland, Island eller något av folken därifrån. Vi hittade inget.

De platser som nämns ligger i väster. Ristaren Gautr, som vi mötte i första delen, skriver *{nz('IM MM99').split('en ')[-1]}* – Gautr gjorde det, son till Björn från Kollr, alltså ön Coll i Hebriderna. Och på ett annat kors skriver han att han gjorde *þenna ok alla í Môn*, det här och alla på Man. Gautrs släkt kom från en ö i väster, och hans stolthet gäller det nya landet.

Är det märkligt? Vi jämförde med Norge, där de flesta på öarna kom ifrån – det syns på runorna, som är av norsk typ. Av de {R['H1']['norway'][1]} vikingatida minnesstenarna i Norge nämner bara två en plats på andra sidan havet. Den ena står vid Alstad och minns Tórald, som dog *miðli Ustaholms ok Garða* – någonstans i Gårdarike. Den andra, vid Galteland, minns Bjór, som dog i följet *þá's Knútr sótti England*, när Knut angrep England.

Så ser det ut i hela Norden. Man nämner en plats långt borta när någon har dött där. För utvandrarna på Man dog de döda hemma. Hemmet var Man.

{pic(BEREZAN, 'Runstenen från Berezan', 'Stenen från ön Berezan vid Dneprs mynning, i dag i museet i Odessa: Grani gjorde detta valv efter Karl, sin kamrat.', 'sv')}

Österut är det likadant. På ön Berezan i Svarta havet står *Grani gærði hvalf þessi æftiR Karl, felaga sinn* – Grani gjorde detta valv efter Karl, sin kamrat. Det är samma sätt att minnas som på stenarna hemma – en kamrat, *félagi* – men inget om varifrån de kom. I Hagia Sofia i Konstantinopel har någon ristat namnet Halvdan, en annan Árni. På marmorlejonet från Pireus, som i dag står i Venedig, finns en lång slingristning, så sliten att den knappt går att läsa. Mitt i den läser Thorgunn Snædal *sviar* – svear. Det är det enda stället utanför Norden där en vikingatida runtext kanske nämner folket där hemma, och läsningen är osäker.

{pic(LION, 'Pireuslejonet i Venedig', 'Pireuslejonet vid Arsenalen i Venedig. Runslingan på bogen är så vittrad att bara delar går att läsa.', 'sv')}

## Fäderna

Men något berättar inskrifterna i väster om det förflutna. De säger ofta vems son någon var. *Áleifr Ljótulfs sonr* – Olev, Ljotulvs son – reste ett kors efter sin son Ulf i Ballaugh. Där står tre generationer på en sten. *Druian, sonr Dufgals*. *Melbrigði, sonr Aðakáns Smiðs*.

{chart_kin('sv')}

I väster gör {R['H2']['west'][0]} av {R['H2']['west'][1]} minnesinskrifter det, i Norge {R['H2']['norway'][0]} av {R['H2']['norway'][1]}. Det såg först ut som en saknad efter släkten: i det nya landet höll man fast vid vem man härstammade från. Men när vi bara räknade de inskrifter där föräldern har ett nordiskt namn, föll skillnaden bort. Då är det {R['H2_nordisk']['west'][0]} av {R['H2_nordisk']['west'][1]}, färre än i Norge. Hela överskottet kommer från gaeliska fäder – Dufgal, Krínán, Aðakán.

Det är alltså inte ett nordiskt minne av hemmet. Det är grannarnas sed. På gaeliska bar man sin fars namn i sitt eget, *mac* – son till. Nordborna i Norge skrev också så, *Þórir Harðarsonr reisti stein þenna* vid Klepp. Men det var gaelerna på Man som gjorde det oftast.

## Gudarna följde med i namnen

Inte en enda minnesinskrift i väster nämner en hednisk gud i texten. Det enda stället på öarna där gudarna står i text är den lilla sländtrissan från Saltfleetby i England, som vi skrev om i första delen: Oden och Heimdall och Tjalve, som ska hjälpa Ulvljot. Men den är ingen minnessten.

Ändå finns gudarna där. Torvald, Torsten, Torleiv, Torulv, Torfinn, Torgerd, Turid och Astrid – och Torbjörn tre gånger. Av de {R['H3']['west'][1]} nordiska namn som går att läsa i minnesinskrifterna i väster bär {R['H3']['west'][0]} en gud. Det är {sh('H3')} procent. I Norge är det {sn('H3')} procent, i Sverige {pc(SE['theo_k'][0] / SE['theo_k'][1])}.

{chart_gods('sv')}

Vår hypotes var att utvandrarna skulle ha fler gudanamn än man hade hemma. Det håller inte: skillnaden mot Norge är för liten för att säkert skilja från slumpen, med så få namn. Men det viktiga är åt andra hållet. Utvandrarna hade inte *färre*. De reste kristna kors vid kyrkorna, men de gav barnen namn efter Tor lika ofta som man gjorde i Norge – och troligen oftare än i Sverige, även om den jämförelsen bara bygger på sökmönster.

Det knyter an till det vi fann i [artikeln om vikinganamnen]({TOR}): namnen med en gud i är de som har levt längst, ända till i dag. Kyrkan tog Tor ur kulten men inte ur namnen – inte hemma och inte i det nya landet.

## Oden bredvid Kristus

I texterna är utvandrarna inte heller särskilt fromma. Bara {PRAY['west']} av {R['n_west']} minnesinskrifter i väster har en bön eller ett gudsord – den ena är Melbrigðis kors för hans själ, den andra ett kors i Onchan som slutar med *Jésu Krist*. Hemma står en bön på ungefär var åttonde minnessten i Norge ({PRAY['Norge']} procent) och var sjätte i Sverige ({PRAY['Sverige']} procent). Det kristna på Man sitter inte i orden utan i formen: de kallar sina monument *kross*, inte *steinn*, och de reser dem vid kyrkan.

Det hedniska sitter i bilderna. På Torvalds kors står Oden och vargen bredvid Kristus. På andra kors står hjälten Sigurd som dödar draken Fafner och steker hans hjärta. Bilderna finns inte i rundatabasen, så dem har vi inte kunnat räkna. Men de visar att berättelserna följde med, också när orden inte gjorde det.

{pic(SIGURD, 'Sigurd på tre manxska kors', 'Sigurd på tre kors från Isle of Man – Jurby, Malew och Maughold – tecknade av Philip Kermode (1907). På Jurbykorset dödar han draken Fafner, steker hjärtat och har hästen Grane bredvid sig.', 'sv')}

Längst bort är det tydligast. På Grönland har någon omkring år 1000 ristat på en träpinne vid Narsaq: *Á sæ, sæ, sæ es Ása sat* – på havet, havet, havet satt asarna i bakhåll. Läsningen är osäker, och vad versen betyder vet ingen. Men på den yttersta gården i den nordiska världen skrev någon om asarna.

## Två språk i samma familj

På Man levde nordbor och gaeler i samma familjer. Vi tittade på alla ställen där både en förälder och ett barn är namngivna och båda namnen går att bestämma – {R['H5']['pairs']} par. I {R['H5']['n->n'] + R['H5']['g->g']} av dem har barnet ett namn på förälderns språk. Bara två gånger byter namnet språk, en gång åt vardera hållet. Þorleifr Hnakke – Torleiv Nacke – reste ett kors efter sin son Fiak, som har ett gaeliskt namn. Och Ófeigr, med ett nordiskt namn, var son till Krínán, en gael.

Familjerna blandades alltså genom äktenskap – flera av hustrurna på korsen har gaeliska namn, som Aþmiul och Myrgjôl – men varje förälder gav oftast sitt eget språk vidare. Det nordiska försvann inte på en generation.

## Saknaden

Och saknaden? Den syns inte. Utvandrarna prisar sällan sina döda: en enda minnesinskrift i väster har ett omdöme, ordspråket på korset i Kirk Michael om att det är bättre att lämna en god fosterson än en dålig son. Men så är det i Norge också. Där får två av {R['H4']['norway'][1]} döda ett omdöme: Bjalfe var *harða góðan mann*, en mycket god man, och Astrid vid Dynna *mær hônnurst á Haðalandi*, den skickligaste flickan i Hadeland.

Det enda ord för sorg som vi har hittat i hela materialet står hemma i Norge. På en sten i Njærheim har ristaren skrivit sitt namn: *Ulfríkr sorgþungr gerði* – Ulvrik den sorgtyngde gjorde den. Om det är ett binamn eller sorgen den gången vet vi inte. På Man skriver man i stället om svek och tro: *Hrossketill vélti í tryggu eiðsvara sinn*, Hrossketill svek den han hade svurit trohet. Det är det nya landets ord – om de band man hade knutit där.

## Så säkra är vi

:::box Så säkra är vi
- **Det vi visar:** att ingen av de {len(WV)} vikingatida runinskrifterna på de brittiska öarna nämner Norden, att de som anger vems son någon var gör det med gaeliska fäder, och att tio av tolv barn på Man fick ett namn på förälderns språk.
- **Det vi tror:** att utvandrarna skrev som man skrev hemma och inte saknade hemmet i orden – det följde med i namnen, runorna och bilderna.
- **Det vi prövade och som inte höll:** alla fyra jämförelserna med Norge i den låsta planen faller. Väster nämner inte hemmet mer sällan än Norge nämner andra sidan havet, anger inte släkten oftare när de gaeliska fäderna räknas bort, har inte säkert fler gudanamn och prisar inte de döda mer eller mindre.
- **Svagheterna:** talen är små – {R['n_west']} minnesinskrifter i väster och {R['n_norway']} i Norge – och att en skillnad inte går att visa betyder inte att det inte finns någon. Kodningen är vår, med en anmärkning för varje inskrift. Vi såg en första räkning innan planen låstes, och redovisar det i planen. Sverige och Danmark är bara räknade med sökmönster, som i Norge missade hälften av släktuppgifterna. Bilderna på korsen finns inte i databasen.
:::

:::box Det viktigaste i korthet
- Utvandrarna i väster skrev aldrig om det gamla landet. För dem var det nya landet hemma, och de döda dog där.
- De lämnade ändå inte hemmet bakom sig. De skrev med norska runor och norska formler, och de gav barnen namn efter Tor lika ofta som man gjorde i Norge.
- Det nya syns i grannarna: gaeliska fäder, gaeliska hustrur, och kors i stället för stenar – med Oden och Kristus på samma sten.
- Det som följde med var det man inte behövde säga.
:::

## Källor

- Samnordisk runtextdatabas (Rundata), Institutionen för nordiska språk, Uppsala universitet. Open Database License.
- Barnes, Michael P. & Page, R. I. 2006. *The Scandinavian Runic Inscriptions of Britain*. Uppsala.
- Kermode, Philip M. C. 1907. *Manx Crosses*. London. Teckningarna av Torvalds kors och Sigurdskorsen.
- Wikipedia (engelska), artikeln Manx runestones, med Andy Orchard om bilden på Torvalds kors.
- Snædal, Thorgunn: läsningen av Pireuslejonet, efter Rundata.
- Den låsta analysplanen, handkodningen med anmärkning för varje inskrift och Vitkis räkning ligger öppet på [GitHub](https://github.com/Precatio/runes).
- Bilder: Wikimedia Commons, med upphovsperson och licens i bildtexterna."""

title_en = "They never mentioned home – the runic inscriptions of the British Isles, part 2"
summary_en = ("None of the 84 Viking-age runic inscriptions in the British Isles mentions the old country. But the emigrants "
              "did not leave it behind: they wrote as people wrote in Norway, they named their children after Thor, and on "
              "the crosses Odin is swallowed by the Fenris wolf next to Christ.")

body_en = f"""*{nz('IM MM128')}* – Þorvaldr raised this cross.

The text says no more. The cross stands in the church at Andreas on the Isle of Man, and it was raised some time in the tenth century by a man whose name carries the god Thor. On one side stands a man with a bird on his shoulder, and a wolf is devouring him. Next to it stand a large cross and a figure that has been read as Christ triumphing over Satan. The man is read as Odin, swallowed by the Fenris wolf at Ragnarök. Two worlds on the same stone, and in the text only a name.

In [the first part](/en{PART1}) we read every runic inscription in the British Isles and asked who wrote them. Now we ask something else. What did those who had left the North say about what they had left? Can we see longing, the family back home, the old gods? Or did they leave all of that behind?

{pic(THOR_X, 'Thorwald’s Cross at Andreas', 'Thorwald’s Cross at Andreas (MM128), drawn by Philip Kermode in Manx Crosses (1907): the two faces of the cross and the edge with the runes. On the right the man with the bird and the wolf.', 'en')}

:::box In short
- None of the {len(WV)} Viking-age runic inscriptions in the British Isles mentions the North. The places named are the new home: Coll in the Hebrides and Man. But Norwegian memorial stones also rarely mention the other side of the sea, so the silence is not remarkable.
- The emigrants said whose son someone was more often than people did in Norway – but the difference comes entirely from the Gaelic fathers. It is the neighbours' naming custom, not a memory of home.
- {sh('H3')} per cent of the emigrants' Norse names carry a god, against {sn('H3')} per cent in Norway. The old gods lived on in the names, also on the Christian crosses.
- In the families, ten of twelve children kept their parent's language in their name.
- The emigrants did not leave home behind. They took it with them without mentioning it.
:::

## The home that was never named

Start with the simplest thing. We went through all {len(WV)} Viking-age runic inscriptions in the British Isles looking for Norway, Denmark, Sweden, Gotland, Iceland or any of the peoples from there. We found nothing.

The places that are named lie in the west. The carver Gautr, whom we met in the first part, writes *{nz('IM MM99').split('en ')[-1]}* – Gautr made it, son of Bjôrn from Kollr, that is, the island of Coll in the Hebrides. And on another cross he writes that he made *þenna ok alla í Môn*, this one and all on Man. Gautr's family came from an island in the west, and his pride concerns the new land.

Is that strange? We compared with Norway, where most of the people on the islands came from – it shows in the runes, which are of the Norwegian type. Of the {R['H1']['norway'][1]} Viking-age memorial stones in Norway, only two mention a place on the other side of the sea. One stands at Alstad and remembers Þóraldr, who died *miðli Ustaholms ok Garða* – somewhere in Garðar, in Russia. The other, at Galteland, remembers Bjórr, who died in the retinue *þá's Knútr sótti England*, when Knútr attacked England.

That is how it is across the North. A place far away is named when someone has died there. For the emigrants on Man, the dead died at home. Home was Man.

{pic(BEREZAN, 'The runestone from Berezan', 'The stone from the island of Berezan at the mouth of the Dnieper, today in the museum in Odesa: Grani made this vault in memory of Karl, his partner.', 'en')}

To the east it is the same. On the island of Berezan in the Black Sea stands *Grani gærði hvalf þessi æftiR Karl, felaga sinn* – Grani made this vault in memory of Karl, his partner. It is the same way of remembering as on the stones at home – a partner, *félagi* – but nothing about where they came from. In Hagia Sophia in Constantinople someone has carved the name Halfdan, another Árni. On the marble lion from Piraeus, which stands in Venice today, there is a long serpent band of runes, so worn that it can hardly be read. In the middle of it Thorgunn Snædal reads *sviar* – Swedes. It is the only place outside the North where a Viking-age runic text may mention the people back home, and the reading is uncertain.

{pic(LION, 'The Piraeus Lion in Venice', 'The Piraeus Lion at the Arsenale in Venice. The runic band on its shoulder is so weathered that only parts can be read.', 'en')}

## The fathers

But the inscriptions in the west do tell of the past in one way. They often say whose son someone was. *Áleifr Ljótulfs sonr* – Áleifr, Ljótulfr's son – raised a cross in memory of his son Ulfr at Ballaugh. Three generations on one stone. *Druian, sonr Dufgals*. *Melbrigði, sonr Aðakáns Smiðs*.

{chart_kin('en')}

In the west {R['H2']['west'][0]} of {R['H2']['west'][1]} memorial inscriptions do so, in Norway {R['H2']['norway'][0]} of {R['H2']['norway'][1]}. At first it looked like longing for kin: in the new land people held on to whom they descended from. But when we counted only the inscriptions where the parent has a Norse name, the difference disappeared. Then it is {R['H2_nordisk']['west'][0]} of {R['H2_nordisk']['west'][1]}, fewer than in Norway. The whole surplus comes from Gaelic fathers – Dufgal, Krínán, Aðakán.

So it is not a Norse memory of home. It is the neighbours' custom. In Gaelic you carried your father's name in your own, *mac* – son of. The Norse in Norway wrote like that too, *Þórir Harðarsonr reisti stein þenna* at Klepp. But it was the Gaels on Man who did it most.

## The gods came along in the names

Not a single memorial inscription in the west names a pagan god in its text. The only place on the islands where the gods stand in writing is the little spindle whorl from Saltfleetby in England, which we wrote about in the first part: Odin and Heimdallr and Þjálfi, who are to help Úlfljót. But it is no memorial.

Yet the gods are there. Þorvaldr, Þorsteinn, Þorleifr, Þórulfr, Þorfinnr, Þorgerðr, Þúríð and Ástríðr – and Þorbjôrn three times. Of the {R['H3']['west'][1]} Norse names that can be read in the memorial inscriptions of the west, {R['H3']['west'][0]} carry a god. That is {sh('H3')} per cent. In Norway it is {sn('H3')} per cent, in Sweden {pc(SE['theo_k'][0] / SE['theo_k'][1])}.

{chart_gods('en')}

Our hypothesis was that the emigrants would have more god-names than people had at home. That does not hold: the difference from Norway is too small to tell safely from chance, with so few names. But what matters points the other way. The emigrants did not have *fewer*. They raised Christian crosses by the churches, but they named their children after Thor as often as people did in Norway – and probably more often than in Sweden, although that comparison rests only on search patterns.

It ties in with what we found in [the article on the Viking names](/en{TOR}): the names with a god in them are the ones that have lived longest, right up to today. The church took Thor out of the cult but not out of the names – not at home and not in the new land.

## Odin next to Christ

In their texts the emigrants are not especially pious either. Only {PRAY['west']} of {R['n_west']} memorial inscriptions in the west have a prayer or a word for God – one is Melbrigði's cross for his soul, the other a cross at Onchan that ends with *Jésu Krist*. At home a prayer stands on about one memorial stone in eight in Norway ({PRAY['Norge']} per cent) and one in six in Sweden ({PRAY['Sverige']} per cent). The Christian element on Man sits not in the words but in the form: they call their monuments *kross*, not *steinn*, and they raise them by the church.

The pagan sits in the images. On Thorwald's Cross Odin and the wolf stand next to Christ. On other crosses the hero Sigurðr kills the dragon Fáfnir and roasts his heart. The images are not in the runic database, so we have not been able to count them. But they show that the stories came along, even when the words did not.

{pic(SIGURD, 'Sigurd on three Manx crosses', 'Sigurðr on three crosses from the Isle of Man – Jurby, Malew and Maughold – drawn by Philip Kermode (1907). On the Jurby cross he kills the dragon Fáfnir, roasts the heart and has the horse Grani beside him.', 'en')}

It is clearest furthest away. In Greenland, around the year 1000, someone carved on a wooden stick at Narsaq: *Á sæ, sæ, sæ es Ása sat* – on the sea, the sea, the sea the Æsir lay in ambush. The reading is uncertain, and no one knows what the verse means. But on the outermost farm of the Norse world, someone wrote about the Æsir.

## Two languages in one family

On Man, Norse and Gaels lived in the same families. We looked at every place where both a parent and a child are named and both names can be identified – {R['H5']['pairs']} pairs. In {R['H5']['n->n'] + R['H5']['g->g']} of them the child has a name in the parent's language. Only twice does the name change language, once in each direction. Þorleifr Hnakki – Þorleifr the Neck – raised a cross in memory of his son Fiak, who has a Gaelic name. And Ófeigr, with a Norse name, was the son of Krínán, a Gael.

The families mixed through marriage – several of the wives on the crosses have Gaelic names, like Aþmiul and Myrgjôl – but each parent mostly passed on their own language. The Norse did not vanish in a generation.

## The longing

And the longing? It does not show. The emigrants rarely praise their dead: a single memorial inscription in the west has a judgement, the proverb on the cross at Kirk Michael that it is better to leave a good foster-son than a bad son. But it is the same in Norway. There, two of {R['H4']['norway'][1]} dead get a judgement: Bjalfi was *harða góðan mann*, a very good man, and Ástríðr at Dynna *mær hônnurst á Haðalandi*, the handiest maiden in Hadeland.

The only word for grief we have found in the whole material stands at home in Norway. On a stone at Njærheim the carver has written his name: *Ulfríkr sorgþungr gerði* – Ulfríkr the Sorrow-stricken made it. Whether that is a byname or the grief of that day, we do not know. On Man people write instead about betrayal and faith: *Hrossketill vélti í tryggu eiðsvara sinn*, Hrossketill betrayed the faith of his sworn confederate. Those are the new land's words – about the bonds made there.

## How sure we are

:::box How sure we are
- **What we show:** that none of the {len(WV)} Viking-age runic inscriptions in the British Isles mentions the North, that those who say whose son someone was do so with Gaelic fathers, and that ten of twelve children on Man got a name in their parent's language.
- **What we believe:** that the emigrants wrote as people wrote at home and did not miss home in their words – it came along in the names, the runes and the images.
- **What we tested and what did not hold:** all four comparisons with Norway in the locked plan fail. The west does not mention home more rarely than Norway mentions the other side of the sea, does not give kin more often once the Gaelic fathers are left out, does not certainly have more god-names and does not praise the dead more or less.
- **The weaknesses:** the numbers are small – {R['n_west']} memorial inscriptions in the west and {R['n_norway']} in Norway – and failing to show a difference does not mean there is none. The coding is ours, with a note for every inscription. We saw a first count before the plan was locked, and say so in the plan. Sweden and Denmark are only counted with search patterns, which in Norway missed half of the kin statements. The images on the crosses are not in the database.
:::

:::box The essentials in brief
- The emigrants in the west never wrote about the old country. For them the new land was home, and the dead died there.
- Even so, they did not leave home behind. They wrote with Norwegian runes and Norwegian formulas, and they named their children after Thor as often as people did in Norway.
- What was new shows in the neighbours: Gaelic fathers, Gaelic wives, and crosses instead of stones – with Odin and Christ on the same stone.
- What came along was what did not need to be said.
:::

## Sources

- Scandinavian Runic-text Data Base (Rundata), Department of Scandinavian Languages, Uppsala University. Open Database License.
- Barnes, Michael P. & Page, R. I. 2006. *The Scandinavian Runic Inscriptions of Britain*. Uppsala.
- Kermode, Philip M. C. 1907. *Manx Crosses*. London. The drawings of Thorwald's Cross and the Sigurd crosses.
- Wikipedia (English), the article Manx runestones, with Andy Orchard on the image on Thorwald's Cross.
- Snædal, Thorgunn: the reading of the Piraeus Lion, after Rundata.
- The locked analysis plan, the coding with a note for every inscription, and Vitki's count are open on [GitHub](https://github.com/Precatio/runes).
- Images: Wikimedia Commons, with creator and licence in the captions."""

for b in (body, body_en):
    assert not re.search(r"^\|", b, re.M), "BlogBody har inga tabeller"
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M)), "varje ruta och diagram ska stängas"

out = {"slug": "de-namnde-aldrig-hemmet", "title": title, "summary": summary, "body": body,
       "title_en": title_en, "summary_en": summary_en, "body_en": body_en,
       "labels": ["Forskning", "Norden", "Tro och magi", "Geografi"]}
from src import blog_labels  # noqa: E402  (Admin avvisar ogiltiga etiketter med 422; samma kontroll här)
assert blog_labels.check(out["labels"]) is None, blog_labels.check(out["labels"])
path = os.path.join(ROOT, "utdata", "blogg", "utvandrarna.json")
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
                 "topic": "Forskning|utvandrarna", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
