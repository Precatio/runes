"""Artikeln om runorna på de brittiska öarna: vad de skrev, vem de mindes och vilka de var. Siffrorna låses mot
utdata/brittiska (analys.py, analys.json, kodning.csv); varje citerad inskrift står som i Rundatas fornvästnordiska
normalisering. Porträtten bygger på vad inskrifterna säger; bakgrunden om tid och plats är utskriven som bakgrund.
    ../../../.venv/bin/python build_brittiska.py [--write | --update DOC]"""
import csv
import datetime as dt
import json
import os
import re
import sys
from collections import Counter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from api.rundata import store  # noqa: E402
from src import commons  # noqa: E402

D = os.path.join(ROOT, "utdata", "brittiska")
A = json.load(open(os.path.join(D, "analys.json"), encoding="utf-8"))
K = list(csv.DictReader(open(os.path.join(D, "kodning.csv"), encoding="utf-8")))
pct = lambda k, n: round(100 * k / n)  # noqa: E731
tus = lambda x: f"{int(x):,}".replace(",", " ")  # noqa: E731

# ---- the numbers, locked ---------------------------------------------------------------------------------------------
N_ALL, N_V = A["n"], A["viking"]
assert (N_ALL, N_V) == (149, 84)
AREA_V = Counter(r["omrade"] for r in K)
assert AREA_V == {"Isle of Man": 33, "Irland": 16, "England": 13, "Orkney": 11, "Skottland": 7, "Shetland": 4}
CAT = Counter(r["kategori"] for r in K)
assert CAT == {"minne": 35, "oläsligt": 21, "ristare": 6, "vardag": 6, "namn": 5, "ägare": 4, "futhark": 4, "magi": 3}
BYA = Counter((r["omrade"], r["kategori"]) for r in K)
ISLES = ("Isle of Man", "Skottland", "Shetland", "Orkney")
MEM_ISLES = sum(BYA[(a, "minne")] for a in ISLES)
READ_ISLES = sum(AREA_V[a] for a in ISLES) - sum(BYA[(a, 'oläsligt')] for a in ISLES)
assert BYA[("Isle of Man", "minne")] == 23 and MEM_ISLES == 32 and READ_ISLES == 41 and BYA[("Irland", "minne")] == 1
IR_EVERYDAY = BYA[("Irland", "ägare")] + BYA[("Irland", "vardag")] + BYA[("Irland", "namn")] + BYA[("Irland", "futhark")]
assert IR_EVERYDAY == 10
W = A["women_commemorated"]
MAN, NOR, DEN, SWE = W["Isle of Man"], W["Norge"], W["Danmark"], W["Sverige"]
assert (MAN["women"], MAN["men"]) == (9, 4) and (NOR["women"], NOR["men"]) == (5, 23)
assert (DEN["women"], DEN["men"]) == (7, 126) and (SWE["women"], SWE["men"]) == (43, 1228)
P_NOR = A["women_tests"]["Isle of Man mot Norge"]["p"]
assert 0.002 < P_NOR < 0.004
NAMES = A["name_origins"]
assert NAMES == {"nordiskt": 56, "gaeliskt": 16, "osäkert": 2, "anglosaxiskt": 1}
N_NAMES = sum(NAMES.values())
MIXED = A["mixed"]
assert MIXED == ["IM MM101", "IM MM112", "IM MM130", "IM MM135", "IM MM141"]
ST, NAMED = A["scandinavian_stones"], A["naming_islands"]
assert ST == {"Sverige": 2320, "Danmark": 239, "Norge": 66}
assert NAMED == {"Sverige|England": 28, "Danmark|England": 1, "Norge|England": 1}
SWE_ENG = NAMED["Sverige|England"]

# every quoted inscription as it stands in Rundata's Old West Norse normalisation
OWS = {s: store().get(s)["normalization_ows"] for s in ("IM MM130", "IM MM101", "IM MM99", "IM MM141", "IM MM131",
                                                         "IM MM118", "IM MM138", "IM MM142", "IR 1", "IR 5", "IR 8",
                                                         "IR 12", "E 18", "U 344", "Sm 5", "Sc 2")}
for s, frag in [("IM MM130", "Betra er leifa fóstra góðan en son illan"), ("IM MM101", "Gautr gerði þenna ok alla í \"Môn"),
                ("IM MM99", "sonr \"Bjarnar frá \"Kolli"), ("IM MM141", "Þúríð reist rúna[r]"),
                ("IM MM131", "\"Sandulfr hinn \"Svarti reisti kross þenna eptir \"Arinbjôrgu, konu sína"),
                ("IM MM118", "\"Druian, sonr \"Dufgals, reisti kross þenna ept \"Aþmiu[l], konu sín[a]"),
                ("IM MM138", "\"Hrossketill vélti í tryggu eiðsvara sinn"), ("IM MM142", "\"Árni risti rúnar þessar"),
                ("IR 1", "\"Domnall \"Selshôfuð á sverð þetta"), ("IR 5", "\"Ónn á \"Ásu"), ("IR 8", "\"Gnúpr(?) gnúfði(?)"),
                ("IR 12", "Horn hjartar lá á ósi ár"), ("E 18", "\"Óðinn ok \"Heimdallr ok \"Þjálfa, þeir hjálpa þér \"Úlfljót"),
                ("U 344", "En \"Ulfr hefir á \"Englandi þrjú gjald tekit"), ("Sm 5", "manna mestr óníðingr, er á \"Englandi aldri týndi"),
                ("Sc 2", "\"Melbrigða á stilk")]:
    assert frag in OWS[s], (s, frag, OWS[s])
q = lambda s: s.replace('"', "")  # noqa: E731  (Rundata marks names with a leading ")

# ---- pictures, credits pinned ------------------------------------------------------------------------------------------
FILES = {"IM MM130": "Mal Lumkun Cross, Kirk Michael.jpg", "U 344": "U 344, Orkesta.JPG"}
INFO = commons.commons_info(list(FILES.values()))
assert INFO[FILES["U 344"]]["author"] == "Berig" and INFO[FILES["U 344"]]["licence"] == "CC BY 2.5"
assert INFO[FILES["IM MM130"]]["licence"] == "Public domain" and "Kermode" in INFO[FILES["IM MM130"]]["author"]


def picture(key: str, text: str, credit: str) -> str:
    img = INFO[FILES[key]]
    return f"![{key}]({img['thumb']})\n{text} {credit} via [Wikimedia Commons]({img['page']})."


PIC_130 = picture("IM MM130", "Korset i Kirk Michael (IM MM 130), tecknat av P. M. C. Kermode i hans bok om Manx-korsen (1907). En gael, Mallymkun, reste det efter sin fostermor och skrev ett nordiskt ordspråk på det.",
                  "Teckning: P. M. C. Kermode, fri från upphovsrätt,")
PIC_130_EN = picture("IM MM130", "The cross at Kirk Michael (IM MM 130), drawn by P. M. C. Kermode in his book on the Manx crosses (1907). A Gael, Mallymkun, raised it for his foster-mother and put a Norse proverb on it.",
                     "Drawing: P. M. C. Kermode, public domain,")
PIC_344 = picture("U 344", "Ulfs sten i Yttergärde (U 344), nu vid Orkesta kyrka i Uppland. Han tog tre gälder i England och kom hem och berättade det i sten.",
                  "Foto: Berig, CC BY 2.5,")
PIC_344_EN = picture("U 344", "Ulfr's stone from Yttergärde (U 344), now at Orkesta church in Uppland. He took three payments in England, came home and told it in stone.",
                     "Photo: Berig, CC BY 2.5,")

# ---- figures -------------------------------------------------------------------------------------------------------------
def readable(areas):
    return sum(AREA_V[a] - BYA[(a, "oläsligt")] for a in areas)


def row(label, areas, cats, hi=False):
    k, n = sum(BYA[(a, c)] for a in areas for c in cats), readable(areas)
    return f"{'+' if hi else ''}{label} | {pct(k, n)} | {k} av {n}"


EVERYDAY = ("ägare", "namn", "vardag", "futhark")
# every readable inscription falls in one of the chart's rows, so each area adds up to its readable total
assert all(sum(BYA[(a, c)] for a in g for c in ("minne", "ristare", "magi") + EVERYDAY) == readable(g)
           for g in (ISLES, ["Irland"], ["England"]))
assert readable(ISLES) == READ_ISLES and readable(["Irland"]) == 13 and readable(["England"]) == 9
CHART_CAT = f""":::chart Vad de skrev, andel av de läsbara vikingatida runinskrifterna i varje område
# Isle of Man och de skotska öarna
{row("minnesmonument (kors, stenar)", ISLES, ["minne"], True)}
{row("ristarens eller tillverkarens namn", ISLES, ["ristare"])}
{row("ägare, namn, vardag, futhark", ISLES, EVERYDAY)}
# Irland (mest Dublin)
{row("minnesmonument", ["Irland"], ["minne"])}
{row("ägare, namn, vardag, futhark", ["Irland"], EVERYDAY, True)}
{row("ristarens eller tillverkarens namn", ["Irland"], ["ristare"])}
{row("magi och böner", ["Irland"], ["magi"])}
# England
{row("minnesmonument", ["England"], ["minne"])}
{row("ristarens eller tillverkarens namn", ["England"], ["ristare"])}
{row("ägare, namn, vardag, futhark", ["England"], EVERYDAY)}
{row("magi och gudar", ["England"], ["magi"], True)}
Källa: Samnordisk runtextdatabas 3.1, de {N_V} vikingatida inskrifterna från England, Irland, Skottland, Orkney, Shetland och Isle of Man; {CAT['oläsligt']} fragment som inte går att läsa är inte med. Vår kodning, öppen i kodförrådet (utdata/brittiska/kodning.csv). Procent.
:::"""

CHART_W = f""":::chart Andel kvinnor bland dem som monumentet restes efter, när släktskapen anges
+Isle of Man | {pct(MAN['women'], MAN['women'] + MAN['men'])} | {MAN['women']} av {MAN['women'] + MAN['men']} kors
Norge | {pct(NOR['women'], NOR['women'] + NOR['men'])} | {NOR['women']} av {NOR['women'] + NOR['men']} runstenar
Danmark | {pct(DEN['women'], DEN['women'] + DEN['men'])} | {DEN['women']} av {DEN['women'] + DEN['men']}
Sverige | {pct(SWE['women'], SWE['women'] + SWE['men'])} | {SWE['women']} av {tus(SWE['women'] + SWE['men'])}
Källa: Samnordisk runtextdatabas 3.1, vikingatida monument där översättningen anger den dödes släktskap med den som reste det (”his wife”, ”her son” …), samma mått som i vår artikel om kvinnorna på runstenarna. Procent.
:::"""


def en_chart(ch: str) -> str:
    for a, b in [("Vad de skrev, andel av de läsbara vikingatida runinskrifterna i varje område", "What they wrote, share of the readable Viking-age runic inscriptions in each area"),
                 ("# Isle of Man och de skotska öarna", "# The Isle of Man and the Scottish isles"),
                 ("minnesmonument (kors, stenar)", "memorials (crosses, stones)"), ("ristarens eller tillverkarens namn", "the carver's or maker's name"),
                 ("ägare, namn, vardag, futhark", "owner, name, everyday, futhark"), ("# Irland (mest Dublin)", "# Ireland (mostly Dublin)"),
                 ("minnesmonument", "memorials"), ("magi och böner", "magic and prayers"), ("magi och gudar", "magic and gods"),
                 (" av ", " of "),
                 ("Källa: Samnordisk runtextdatabas 3.1, de", "Source: Scandinavian Runic-text Database 3.1, the"),
                 ("vikingatida inskrifterna från England, Irland, Skottland, Orkney, Shetland och Isle of Man;", "Viking-age inscriptions from England, Ireland, Scotland, Orkney, Shetland and the Isle of Man;"),
                 ("fragment som inte går att läsa är inte med. Vår kodning, öppen i kodförrådet", "fragments that cannot be read are left out. Our coding, open in the code repository"), ("kodning.csv). Procent.", "kodning.csv). Per cent."),
                 ("Andel kvinnor bland dem som monumentet restes efter, när släktskapen anges", "Share of women among those the monument was raised for, where the kinship is stated"),
                 ("Källa: Samnordisk runtextdatabas 3.1, vikingatida monument där översättningen anger den dödes släktskap med den som reste det (”his wife”, ”her son” …), samma mått som i vår artikel om kvinnorna på runstenarna. Procent.",
                  "Source: Scandinavian Runic-text Database 3.1, Viking-age monuments where the translation states the dead person's kinship with the one who raised it (“his wife”, “her son” …), the same measure as in our article on the women of the runestones. Per cent."),
                 ("Norge", "Norway"), ("Danmark", "Denmark"), ("Sverige", "Sweden"), (" kors\n", " crosses\n"), ("runstenar", "runestones"),
                 ("# England", "# England")]:
        ch = ch.replace(a, b)
    return ch


for ch in (CHART_CAT, CHART_W):
    assert ch.rstrip().endswith("\n:::"), "a chart must end with its own ::: line"
    assert not re.search(r"[åäö]", en_chart(ch)), en_chart(ch)

# ---- the article ----------------------------------------------------------------------------------------------------------
title = "Där hustrurna fick kors"
summary = (f"På de brittiska öarna finns {N_V} runinskrifter från vikingatiden. Vi har läst dem alla och frågat vilka som "
           "skrev dem och vad de ville säga. På Isle of Man restes vartannat kors efter en kvinna, nordiska och gaeliska namn "
           "står i samma familjer, och svenskarna, som ristade om England hemma, syns nästan inte alls.")

body = f"""Föreställ dig en man som går längs kusten på Isle of Man med sina mejslar. Han heter Gautr, och det mesta vi vet om honom har han själv skrivit. Han är son till Bjôrn från Kollr – ön Coll i Hebriderna – och han är stolt nog att säga det i sten. På ett kors i Andreas står *en Gautr gerði, sonr Bjarnar frá Kolli*: men Gautr gjorde det, Bjôrns son från Coll. På ett annat, i Kirk Michael, säger han mer: *Gautr gerði þenna ok alla í Môn* – Gautr gjorde det här och alla på Man.

Det är en skrytsam mening, och den passar honom. Men korset han gjorde den gången var inte hans eget. Det restes av *Melbrigði, sonr Aðakáns Smiðs*, Melbrigði, son till smeden Aðakán. Båda namnen är gaeliska. En gael betalade en nordbo för ett kors med nordiska runor, för sin själs skull.

Scenen med kusten är vår bild. Namnen, orten och skrytet står i stenarna. Det är där den här artikeln börjar. Runorna på de brittiska öarna har ofta lästs som spår av erövrare. Vi ville se vilka människor som faktiskt syns i dem.

## Vad som finns

I Samnordisk runtextdatabas finns {N_ALL} runinskrifter från England, Irland, Skottland, Orkney, Shetland och Isle of Man. {N_V} är från vikingatiden; de flesta av de övriga är de medeltida väggristningarna i gravhögen Maeshowe på Orkney, som vi lämnar åt en annan gång. Av de {N_V} ligger {AREA_V['Isle of Man']} på Isle of Man, {AREA_V['Irland']} i Irland, {AREA_V['England']} i England, {AREA_V['Orkney']} på Orkney, {AREA_V['Skottland']} i Skottland och {AREA_V['Shetland']} på Shetland. {CAT['oläsligt']} är så skadade att de inte går att läsa.

Vi läste resten och delade in dem efter vad de handlar om. Det visade sig inte finnas ett runskrivande på öarna, utan tre.

{CHART_CAT}

## Tre slags människor

**Familjerna på öarna.** På Isle of Man och de skotska öarna är nästan allt som går att läsa minnesmonument: {MEM_ISLES} av {READ_ISLES} inskrifter. Det är kors, inte runstenar, och de står vid kyrkor. Den som reste dem var bofast, kristen och hade en gård att lämna efter sig. *Sandulfr hinn Svarti reisti kross þenna eptir Arinbjôrgu, konu sína* – Sandulf den svarte reste det här korset efter Arinbjôrg, sin hustru. Mer än så säger inte stenen, men binamnet säger något om håret eller humöret, och korset står vid kyrkan i Andreas så att hennes namn ska finnas kvar.

**Folket i Dublin.** I Irland finns ett enda kors. Resten är små saker från staden Dublin, där utgrävningarna vid Fishamble Street och Christ Church Place har gett tusentals föremål från vikingatidens hamnstad. Här skriver man på det som ligger nära till hands: revben, skulderblad, en kam, ett handtag. *Domnall Selshôfuð á sverð þetta* – Domnall Sälhuvud äger det här svärdet, på svärdsremmens ände. En gael med ett nordiskt öknamn. *Ónn á Ásu*, Ónn äger Åsa – på ett revben, och om det är ett skämt eller ett anspråk vet ingen. *Gnúpr gnúfði*, Gnupr hängde med huvudet. *Horn hjartar lá á ósi ár*: hjorthornet låg vid åmynningen. Det är hantverkare och handelsmän som har en stund över, och det är den enda platsen på öarna där runorna låter som vardagsprat.

**De tillfälliga i England.** I England är det annorlunda igen. Där finns ristarnas och tillverkarnas namn, och där finns gudarna. På en sländtrissa från Saltfleetby står *Óðinn ok Heimdallr ok Þjálfa, þeir hjálpa þér Úlfljót* – Oden och Heimdall och Tjalve, de hjälper dig, Ulvljot. Spinning var kvinnors arbete, och Úlfljót kan vara ett kvinnonamn. Någon har spunnit med trissan och bett de gamla gudarna om hjälp. Gravstenen vid St Paul's i London är huggen i skandinavisk stil på Knuts tid, och de flesta engelska inskrifterna har inga minnen av släkt alls. England var platsen dit man kom med en här eller ett skepp och sedan reste igen.

## Hustrurna

På Isle of Man finns {MAN['women'] + MAN['men']} kors där det står vem den döde var för den som reste korset. {MAN['women']} av dem är resta efter en kvinna: sex hustrur, en mor, en fostermor och en dotter. I Skandinavien är kvinnorna få. I Sverige är det {pct(SWE['women'], SWE['women'] + SWE['men'])} procent, ungefär en sten av trettio. I Danmark {pct(DEN['women'], DEN['women'] + DEN['men'])} procent, i Norge {pct(NOR['women'], NOR['women'] + NOR['men'])}.

{CHART_W}

Det är små tal på Man, och därför är det värt att säga vad de betyder. Om korsen på Man följde samma mönster som de norska runstenarna – det land Manx-nybyggarna i huvudsak kom ifrån – skulle en så stor andel kvinnor uppstå av en slump ungefär tre gånger på tusen. Skillnaden mot Sverige och Danmark är ännu större. Det är heller inte tiden som förklarar det: de danska stenarna är lika gamla som Manx-korsen, från 900-talet, och har lika få kvinnor som de svenska.

Druian, Dufgals son, reste ett kors efter sin hustru Aþmiul. Alla tre namnen är gaeliska. Heðinn reste ett efter sin dotter Hlífhildr och lät Árni rista runorna. På ett kors i Onchan står, sist av allt: *Þúríð reist rúnar* – Þuríð ristade runorna. Hon är en av mycket få kvinnor i hela vikingatiden som har satt sitt namn på en runinskrift som den som ristade.

Varför? Det kan vi inte veta, men det finns en ledtråd i vad vi hittade i artikeln om kvinnorna på runstenarna. I Skandinavien handlar stenarna ofta om arv: den som reste stenen visade att han eller hon tog över. Korset på Man är något annat – ett kristet minnesmärke vid kyrkan, rest för själens skull. Det är en hypotes som vi inte har prövat: att kvinnorna syns där monumentet handlar om minnet och inte om arvet.

## Gaeler och nordbor i samma familj

Av de {N_NAMES} personnamn som går att läsa i inskrifterna är {NAMES['gaeliskt']} gaeliska. Det är namn som Melbrigði (Máel Brigte), Dufgal (Dubgall), Malmury (Máel Muire) och Krínán (Crínán). Nästan alla står på Man. I fem av Manx-korsen står gaeliska och nordiska namn i samma familj.

{PIC_130}

Korset i Kirk Michael är det tydligaste exemplet. *Mallymkun reisti kross þenna eptir Malmury fóstra sín, dóttur Dufgals, kona er Aðísl átti* – Mallymkun reste det här korset efter Malmury, sin fostermor (ordet *fóstra* kan också läsas på annat sätt), Dufgals dotter, hustru till Aðísl. Mallymkun och Malmury och Dufgal är gaeliska; Aðísl är nordisk. Och under det, ett ordspråk på norrönt: *Betra er leifa fóstra góðan en son illan*. Bättre att lämna en god fosterson efter sig än en dålig son. Det är skrivet av en gael om en gaelisk kvinna som var gift med en nordbo. Det är också huggit med andra runor än de flesta Manx-korsen – långkvistrunor.

Det är inte ett erövrat folk vi ser här. Det är två folk som gifter sig med varandra, uppfostrar varandras barn och skriver på varandras språk. Det har forskningen sett länge; Michael Barnes och Ray Page har kartlagt namnen. Vad vi lägger till är att samma kors också är de där kvinnorna syns.

## Och svenskarna?

Svenskarna var på de brittiska öarna. Det vet vi, för de berättade det själva – hemma. {SWE_ENG} svenska runstenar nämner England. Ulf i Borresta *hefir á Englandi þrjú gjald tekit*: han har tagit tre gälder i England, först Toste, sedan Torkel, sedan Knut. I Transjö i Småland reste Gautr en sten efter sin son Ketill, *manna mestr óníðingr, er á Englandi aldri týndi*, den minst nidingsaktige av män, som miste livet i England.

{PIC_344}

Men på öarna själva syns de nästan inte. Ingen av de {N_V} inskrifterna nämner Sverige, och ingen kan knytas till en svensk ristare. Runorna på Man och på de skotska öarna är kortkvistrunor av den sort som forskningen knyter till Norge och Hebriderna; Gautr säger själv att han kom från Coll. De engelska har sina rötter i Danmark.

Är svenskarna då överrepresenterade? Bara på hemmaplan, och inte ens där. Räknat per sten nämner de svenska stenarna England ungefär lika ofta som de norska: en av {round(ST['Sverige'] / SWE_ENG)} svenska runstenar, en av {ST['Norge']} norska. Att det finns så många svenska Englandsstenar beror på att det finns så många svenska runstenar. De danska nämner England nästan aldrig – en av {ST['Danmark']} – men många danska runstenar restes före Knuts tid i England.

Bilden som träder fram är enkel. Svenskarna åkte till England som soldater och tog betalt, och de som kom hem reste stenar i Uppland och Småland. Norrmännen och folket från Hebriderna stannade, gifte sig med gaeler och reste kors vid kyrkorna på Man. Det var de som skrev på öarna.

:::box Det viktigaste i korthet
- Runorna på de brittiska öarna kommer från tre olika världar: familjerna på Man och de skotska öarna, som reste kors vid kyrkorna; hamnfolket i Dublin, som skrev om ägande och vardag; och de tillfälliga i England, med ristarnamn och gamla gudar.
- På Isle of Man restes {MAN['women']} av {MAN['women'] + MAN['men']} kors efter en kvinna, mot ungefär en sten av trettio i Sverige. Där syns också en kvinna som ristade runor, Þuríð.
- Gaeliska och nordiska namn står i samma familjer på korsen. Det är inte erövrare vi läser utan blandade familjer.
- Svenskarna berättade om England hemma, på {SWE_ENG} stenar, men lämnade nästan inga spår på öarna. Det var norrmän och folk från Hebriderna som skrev där.
:::

:::box Hur vi räknade
- **Inskrifterna:** alla {N_ALL} runinskrifter i Samnordisk runtextdatabas 3.1 från England, Irland, Skottland, Orkney, Shetland och Isle of Man. Vi räknar de {N_V} som databasen daterar till vikingatiden. Vi har läst varje inskrift och fört den till en kategori: minnesmonument, ristare eller tillverkare, ägare, namn, vardag, futhark, magi, eller oläslig. Kodningen är öppen.
- **Kvinnorna:** samma mått som i vår artikel om kvinnorna på runstenarna: bland monument där översättningen anger den dödes släktskap med den som reste det, andelen där den döde är en kvinna. För Skandinavien räknar vi bara runstenar, för öarna alla minnesmonument, eftersom korsen där fyller samma funktion. Skillnaden mot Norge är prövad med Fishers exakta test.
- **Namnen:** {N_NAMES} personnamn, bestämda som nordiska, gaeliska eller anglosaxiska efter Barnes och Page. Två är osäkra.
- **Svenskarna:** vikingatida runstenar i Sverige, Danmark och Norge vars översättning nämner England, Irland eller Skottland. Bara England nämns.
- **Porträtten:** allt vi säger om personerna står i inskrifterna. Där vi målar en scen runt dem säger vi det.
- **Gränser:** talen från öarna är små, och en del inskrifter är fragment. Att kvinnorna syns där monumentet handlar om minne och inte arv är en hypotes som vi inte har prövat.
:::

## Källor

- Samnordisk runtextdatabas 3.1 (Rundata). Uppsala universitet.
- Barnes, Michael P. & Page, R. I. 2006. *The Scandinavian Runic Inscriptions of Britain*. Runrön 19. Uppsala.
- Barnes, Michael P., Hagland, Jan Ragnar & Page, R. I. 1997. *The Runic Inscriptions of Viking Age Dublin*. Medieval Dublin Excavations 1962–81, Ser. B, vol. 5. Dublin.
- Kermode, P. M. C. 1907. *Manx Crosses*. London.
- Vitkis artikel [Hon ärvde efter sitt barn – kvinnorna på runstenarna](/artiklar/hon-arvde-efter-sitt-barn-kvinnorna-pa-runstenarna/)."""

title_en = "Where wives got crosses"
summary_en = (f"There are {N_V} Viking-age runic inscriptions in the British Isles. We read them all and asked who wrote "
              "them and what they wanted to say. On the Isle of Man every second cross was raised for a woman, Norse and "
              "Gaelic names stand in the same families, and the Swedes, who carved about England at home, hardly show at all.")

body_en = f"""Picture a man walking the coast of the Isle of Man with his chisels. His name is Gautr, and most of what we know about him he wrote himself. He is the son of Bjôrn from Kollr – the island of Coll in the Hebrides – and he is proud enough to say so in stone. On a cross at Andreas stands *en Gautr gerði, sonr Bjarnar frá Kolli*: but Gautr made it, son of Bjôrn from Coll. On another, at Kirk Michael, he says more: *Gautr gerði þenna ok alla í Môn* – Gautr made this one and all in Man.

It is a boastful sentence, and it suits him. But the cross he made that time was not his own. It was raised by *Melbrigði, sonr Aðakáns Smiðs*, Melbrigði, son of Aðakán the Smith. Both names are Gaelic. A Gael paid a Norseman for a cross in Norse runes, for the sake of his soul.

The coast is our picture. The names, the place and the boast are in the stones. That is where this article begins. The runes of the British Isles have often been read as traces of conquerors. We wanted to see which people actually show in them.

## What there is

The Scandinavian Runic-text Database has {N_ALL} runic inscriptions from England, Ireland, Scotland, Orkney, Shetland and the Isle of Man. {N_V} are from the Viking Age; most of the others are the medieval graffiti in the Maeshowe mound on Orkney, which we leave for another time. Of the {N_V}, {AREA_V['Isle of Man']} are on the Isle of Man, {AREA_V['Irland']} in Ireland, {AREA_V['England']} in England, {AREA_V['Orkney']} on Orkney, {AREA_V['Skottland']} in Scotland and {AREA_V['Shetland']} on Shetland. {CAT['oläsligt']} are too damaged to read.

We read the rest and sorted them by what they are about. It turned out there was not one runic writing in the islands, but three.

{en_chart(CHART_CAT)}

## Three kinds of people

**The families of the islands.** On the Isle of Man and the Scottish isles nearly everything that can be read is a memorial: {MEM_ISLES} of {READ_ISLES} inscriptions. They are crosses, not runestones, and they stand at churches. Whoever raised them was settled, Christian and had a farm to leave behind. *Sandulfr hinn Svarti reisti kross þenna eptir Arinbjôrgu, konu sína* – Sandulfr the Black raised this cross for Arinbjôrg, his wife. The stone says no more than that, but the nickname says something about his hair or his temper, and the cross stands at the church in Andreas so that her name would remain.

**The people of Dublin.** In Ireland there is a single cross. The rest are small things from the town of Dublin, where the excavations at Fishamble Street and Christ Church Place have yielded thousands of objects from the Viking-age port. Here people wrote on what was at hand: ribs, shoulder blades, a comb, a handle. *Domnall Selshôfuð á sverð þetta* – Domnall Seal's-head owns this sword, on the end of a sword belt. A Gael with a Norse nickname. *Ónn á Ásu*, Ónn owns Ása – on a rib, and whether it is a joke or a claim nobody knows. *Gnúpr gnúfði*, Gnúpr drooped. *Horn hjartar lá á ósi ár*: the deer's antler lay at the river mouth. These are craftsmen and traders with a moment to spare, and it is the only place in the islands where the runes sound like everyday talk.

**The passers-through in England.** England is different again. There are the carvers' and makers' names, and there are the gods. On a spindle whorl from Saltfleetby stands *Óðinn ok Heimdallr ok Þjálfa, þeir hjálpa þér Úlfljót* – Óðinn and Heimdallr and Þjálfi, they help you, Úlfljót. Spinning was women's work, and Úlfljót may be a woman's name. Someone spun with the whorl and asked the old gods for help. The grave stone at St Paul's in London is cut in Scandinavian style in Knútr's time, and most of the English inscriptions remember no kin at all. England was the place one came to with an army or a ship, and then left again.

## The wives

On the Isle of Man there are {MAN['women'] + MAN['men']} crosses that state who the dead person was to the one who raised the cross. {MAN['women']} of them are raised for a woman: six wives, a mother, a foster-mother and a daughter. In Scandinavia the women are few. In Sweden it is {pct(SWE['women'], SWE['women'] + SWE['men'])} per cent, about one stone in thirty. In Denmark {pct(DEN['women'], DEN['women'] + DEN['men'])} per cent, in Norway {pct(NOR['women'], NOR['women'] + NOR['men'])}.

{en_chart(CHART_W)}

The numbers from Man are small, so it is worth saying what they mean. If the crosses on Man followed the same pattern as the Norwegian runestones – the country the Manx settlers mainly came from – so large a share of women would arise by chance about three times in a thousand. The difference from Sweden and Denmark is larger still. Nor is it the date that explains it: the Danish stones are as old as the Manx crosses, from the tenth century, and have as few women as the Swedish ones.

Druian, son of Dufgal, raised a cross for his wife Aþmiul. All three names are Gaelic. Heðinn raised one for his daughter Hlífhildr and had Árni carve the runes. On a cross at Onchan stands, last of all: *Þúríð reist rúnar* – Þuríð carved the runes. She is one of very few women in the whole Viking Age to put her name to a runic inscription as its carver.

Why? We cannot know, but there is a clue in what we found in the article on the women of the runestones. In Scandinavia the stones are often about inheritance: whoever raised the stone showed that he or she was taking over. The cross on Man is something else – a Christian memorial at the church, raised for the soul's sake. It is a hypothesis we have not tested: that the women show where the monument is about memory and not about inheritance.

## Gaels and Norsemen in one family

Of the {N_NAMES} personal names that can be read in the inscriptions, {NAMES['gaeliskt']} are Gaelic. They are names such as Melbrigði (Máel Brigte), Dufgal (Dubgall), Malmury (Máel Muire) and Krínán (Crínán). Nearly all of them are on Man. On five of the Manx crosses Gaelic and Norse names stand in the same family.

{PIC_130_EN}

The cross at Kirk Michael is the clearest example. *Mallymkun reisti kross þenna eptir Malmury fóstra sín, dóttur Dufgals, kona er Aðísl átti* – Mallymkun raised this cross for Malmury, his foster-mother (the word *fóstra* can also be read otherwise), Dufgal's daughter, the wife of Aðísl. Mallymkun and Malmury and Dufgal are Gaelic; Aðísl is Norse. And below it, a proverb in Old Norse: *Betra er leifa fóstra góðan en son illan*. Better to leave a good foster-son behind than a bad son. It was written by a Gael about a Gaelic woman married to a Norseman. It is also cut in other runes than most of the Manx crosses – long-branch runes.

It is not a conquered people we see here. It is two peoples who marry each other, raise each other's children and write in each other's language. Scholars have seen this for a long time; Michael Barnes and Ray Page have mapped the names. What we add is that the same crosses are also the ones where the women show.

## And the Swedes?

The Swedes were in the British Isles. We know it because they said so themselves – at home. {SWE_ENG} Swedish runestones mention England. Ulfr of Borresta *hefir á Englandi þrjú gjald tekit*: he has taken three payments in England, first from Tosti, then Þorketill, then Knútr. At Transjö in Småland Gautr raised a stone for his son Ketill, *manna mestr óníðingr, er á Englandi aldri týndi*, the least villainous of men, who lost his life in England.

{PIC_344_EN}

But in the islands themselves they hardly show. None of the {N_V} inscriptions mentions Sweden, and none can be tied to a Swedish carver. The runes on Man and on the Scottish isles are short-twig runes of the kind scholars link to Norway and the Hebrides; Gautr says himself that he came from Coll. The English ones have their roots in Denmark.

Are the Swedes over-represented, then? Only at home, and not even there. Per stone, the Swedish stones mention England about as often as the Norwegian ones: one in {round(ST['Sverige'] / SWE_ENG)} Swedish runestones, one in {ST['Norge']} Norwegian. That there are so many Swedish England stones is because there are so many Swedish runestones. The Danish ones hardly ever mention England – one in {ST['Danmark']} – but many Danish runestones were raised before Knútr's time in England.

The picture that emerges is simple. The Swedes went to England as soldiers and took payment, and those who came home raised stones in Uppland and Småland. The Norwegians and the people of the Hebrides stayed, married Gaels and raised crosses at the churches on Man. They were the ones who wrote in the islands.

:::box The essentials in brief
- The runes of the British Isles come from three different worlds: the families of Man and the Scottish isles, who raised crosses at the churches; the port people of Dublin, who wrote about ownership and everyday things; and the passers-through in England, with carvers' names and old gods.
- On the Isle of Man {MAN['women']} of {MAN['women'] + MAN['men']} crosses were raised for a woman, against about one stone in thirty in Sweden. There also stands a woman who carved runes, Þuríð.
- Gaelic and Norse names stand in the same families on the crosses. What we read is not conquerors but mixed families.
- The Swedes told of England at home, on {SWE_ENG} stones, but left hardly any trace in the islands. It was Norwegians and Hebrideans who wrote there.
:::

:::box How we counted
- **The inscriptions:** all {N_ALL} runic inscriptions in the Scandinavian Runic-text Database 3.1 from England, Ireland, Scotland, Orkney, Shetland and the Isle of Man. We count the {N_V} the database dates to the Viking Age. We read every inscription and assigned it to a category: memorial, carver or maker, owner, name, everyday, futhark, magic, or unreadable. The coding is open.
- **The women:** the same measure as in our article on the women of the runestones: among monuments where the translation states the dead person's kinship with the one who raised it, the share where the dead person is a woman. For Scandinavia we count runestones only, for the islands all memorials, since the crosses there serve the same purpose. The difference from Norway is tested with Fisher's exact test.
- **The names:** {N_NAMES} personal names, classed as Norse, Gaelic or Anglo-Saxon after Barnes and Page. Two are uncertain.
- **The Swedes:** Viking-age runestones in Sweden, Denmark and Norway whose translation mentions England, Ireland or Scotland. Only England is mentioned.
- **The portraits:** everything we say about the people is in the inscriptions. Where we paint a scene around them, we say so.
- **Limits:** the numbers from the islands are small, and some inscriptions are fragments. That the women show where the monument is about memory and not inheritance is a hypothesis we have not tested.
:::

## Sources

- Scandinavian Runic-text Database 3.1 (Rundata). Uppsala University.
- Barnes, Michael P. & Page, R. I. 2006. *The Scandinavian Runic Inscriptions of Britain*. Runrön 19. Uppsala.
- Barnes, Michael P., Hagland, Jan Ragnar & Page, R. I. 1997. *The Runic Inscriptions of Viking Age Dublin*. Medieval Dublin Excavations 1962–81, Ser. B, vol. 5. Dublin.
- Kermode, P. M. C. 1907. *Manx Crosses*. London.
- Vitki's article [She inherited from her child – the women on the runestones](/en/artiklar/hon-arvde-efter-sitt-barn-kvinnorna-pa-runstenarna/)."""

for b in (body, body_en):
    assert not re.search(r"^\|", b, re.M)  # BlogBody has no tables
    assert b.count(":::box") == 2 and b.count(":::chart") == 2 and b.count("![") == 2
    blocks = [ln.strip() for ln in b.split("\n") if ln.strip().startswith(":::")]
    assert all(o.startswith(":::") and o != ":::" and c == ":::" for o, c in zip(blocks[::2], blocks[1::2])) and len(blocks) % 2 == 0, blocks
out = {"slug": "dar-hustrurna-fick-kors", "title": title, "summary": summary, "body": body,
       "title_en": title_en, "summary_en": summary_en, "body_en": body_en,
       "labels": ["Forskning", "Kvinnor och barn", "Norden", "Geografi"]}
json.dump(out, open(os.path.join(ROOT, "utdata", "blogg", "brittiska.json"), "w"), ensure_ascii=False, indent=1)
print(os.path.join(ROOT, "utdata", "blogg", "brittiska.json"), len(body.split()), "ord,", len(body_en.split()), "words")

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
                 "topic": "Forskning|brittiska", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
