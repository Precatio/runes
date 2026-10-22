"""Artikeln "Hemma mellan rikena – Skånes runstenar": en personlig läsning (Viktors röst, som Korpen som heter Minne) av
vad Skånes vikingatida runstenar säger om att höra hemma – bygd, herre, fälagar, hav – och vad som skiljer dem från
Danmarks och de svenska landskapens. Varje siffra hämtas ur utdata/skane/skane.json (skane_stenar.py) och låses med
asserts; varje citerad inskrift står ordagrant i Rundatas normalisering.
    ../../../.venv/bin/python build_skane.py [--write | --update DOC]"""
import datetime as dt
import io
import json
import os
import re
import sys
from collections import Counter

from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from api.rundata import store  # noqa: E402
from src import blog_figures, commons  # noqa: E402

S = json.load(open(os.path.join(ROOT, "utdata", "skane", "skane.json"), encoding="utf-8"))
N, C, L = S["n"], S["compare"], S["lists"]
R = {s["signum"]: s for s in S["skane"]}
pr = lambda x: round(100 * x)  # noqa: E731
sv = lambda n: f"{n:,}".replace(",", " ")  # noqa: E731

# ---- låsningarna -----------------------------------------------------------------------------------
assert N["Skåne"] == 59 and N["Danmark"] == 138 and N["Uppland"] == 1178 and N["Västergötland"] == 131 and N["Södermanland"] == 363
assert S["lost"] == 8 and S["efter_jelling"] == {"Skåne": 50, "Danmark": 50}
H = S["harader"]
assert (H["Vemmenhögs hd"], H["Herrestads hd"], H["Ljunits hd"], H["Torna hd"]) == (9, 8, 7, 7)
sh = lambda k, reg: pr(C[k][reg]["share"])  # noqa: E731
nn = lambda k, reg: C[k][reg]["n"]  # noqa: E731
assert (nn("ræisti/satti själv", "Skåne"), sh("ræisti/satti själv", "Skåne"), sh("ræisti/satti själv", "Uppland"), sh("ræisti/satti själv", "Västergötland"), sh("ræisti/satti själv", "Danmark")) == (41, 69, 8, 73, 51)
assert (nn("lät (let) göra", "Skåne"), sh("lät (let) göra", "Uppland")) == (6, 49)
assert (nn("RAK", "Skåne"), sh("RAK", "Skåne"), nn("kors", "Skåne"), sh("kors", "Uppland"), sh("kors", "Danmark")) == (49, 83, 8, 47, 6)
assert (nn("harþa goþan", "Skåne"), nn("harþa goþan", "Västergötland"), nn("harþa goþan", "Danmark")) == (8, 24, 9)
assert sum(nn("harþa goþan", r) for r in ("Småland", "Östergötland", "Södermanland", "Uppland")) == 1
assert (nn("dræng", "Skåne"), sh("dræng", "Skåne"), sh("dræng", "Danmark"), nn("þegn", "Skåne")) == (9, 15, 4, 5)
assert (nn("felagi", "Skåne"), sh("felagi", "Skåne"), nn("felagi", "Danmark"), nn("felagi", "Västergötland"), nn("felagi", "Uppland"), nn("felagi", "Södermanland")) == (8, 14, 5, 3, 1, 1)
assert sum(nn("felagi", r) for r in ("Småland", "Östergötland", "Bornholm")) == 0
assert L["felagi"] == ["DR 262", "DR 270", "DR 279", "DR 318", "DR 321", "DR 329", "DR 330", "DR 339"]
assert (nn("bortom bygden", "Skåne"), sh("bortom bygden", "Skåne"), sh("bortom bygden", "Danmark"), sh("bortom bygden", "Uppland"), sh("bortom bygden", "Södermanland")) == (8, 14, 1, 2, 6)
assert L["bortom bygden"] == ["DR 259", "DR 266", "DR 279", "DR 295", "DR 330", "DR 334", "DR 337", "DR 344"]
assert (nn("Guð", "Skåne"), L["Guð"], sh("Guð", "Uppland")) == (3, ["DR 259", "DR 337", "DR 345"], 14)
assert L["drottin/hemþegn"] == ["DR 295", "DR 296", "DR 297"] and S["no_king_no_denmark"] == {"kunung": [], "danmark": []}
assert nn("bonda", "Skåne") == 6
# the quoted inscriptions, verbatim in Rundata's normalisation
Q = {295: ("Toka \"Gorms sun, seR hullan drottin. SaR flo ægi at \"Upsalum", "sattu drængiaR æftiR sin broþur sten a biargi støþan runum"),
     296: ("saR was hemþægi \"Toka. Nu skal standa sten a biargi",), 297: ("hemþægi \"Toka",),
     279: ("sin felaga", "SaR flo ægi at \"Upsalum, æn wa mæþ han wapn hafþi"), 262: ("felaga sin, dræng goþan",), 330: ("felaga sin[a]", "drængiaR waRu w[iþa] [un]esiR i wikingu"),
     335: ("æs skip atti mæþ hanum",), 275: ("saR waR skipari",), 334: ("æs nor warþ døþr i wikingu",), 266: ("Han warþ wæstr døþr",),
     259: ("han warþ døþr a \"Gotlandi. \"Guþ hialpi hans sælu",), 337: ("\"Guþ hialpi siol þeRa wæl, æn þeR liggia i \"Lundunum",),
     344: ("swen \"Gunu[lf]s a \"Sweþiuþu",), 291: ("Han waR bæztr bomanna ok mildastr mataR",), 277: ("SaR was þægna fyrstr",),
     280: ("æR atti \"Guþissnapa",), 264: ("a \"Høg[by]",), 315: ("Toki let kirkiu gørwa",), 338: ("Wærþi at ræta(?) hwas of briuti",),
     268: ("harþa goþan dræng",), 314: ("landmænnr goþa",), 282: ("sunu \"Gunna \"HandaR",), 298: ("goþan bonda",)}
for nr, parts in Q.items():
    for part in parts:
        assert part in R[f"DR {nr}"]["normalization"], (nr, part)
assert R["DR 344"]["dating"] == "V 1050-1100" and sum(1 for s in S["skane"] if "1050" in (s["dating"] or "")) == 1
WOMEN = [("DR 277", "Kata"), ("DR 291", "Tonna"), ("DR 317", "Tofa"), ("DR 293", "Kætilø"), ("DR 271", "Asa")]
for sig, name in WOMEN:
    assert f'"{name}' in R[sig]["normalization"], (sig, name)
# Uppland's stones are mostly later than Skåne's: their style groups
ins = store().inscriptions
U = [r for r in ins if r["signum"].startswith("U ") and r.get("period") == "V" and "runsten" in (r.get("object") or "").lower()]
styled = [r for r in U if r.get("style") and r["style"] != "?"]
late = sum((r.get("style") or "").startswith(("Pr3", "Pr4", "Pr5")) for r in U)
assert len(U) == N["Uppland"] and (len(styled), late) == (804, 556)
U_LATE = pr(late / len(styled))
# The whole North: who names a king or a realm at all
ALL = [r for r in ins if r.get("period") == "V" and "runsten" in (r.get("object") or "").lower()]
nrm = lambda r: (r.get("normalization") or "").replace("ð", "þ")  # noqa: E731
KING = sorted(r["signum"] for r in ALL if re.search(r"kunung|konung", nrm(r), re.I) and r["signum"] != "U 963")  # U 963: the name Næskonungr
DANM = sorted(r["signum"] for r in ALL if re.search(r"Danm[oa]rk", nrm(r)))
SWED = sorted(r["signum"] for r in ALL if re.search(r"Sw[eiæ]þiuþ", nrm(r)))
assert len(ALL) == 2633 and KING == ["DR 3", "DR 4", "DR 41", "DR 42", "DR 66", "Sm 42", "Vg 40", "Ög 136"]
assert DANM == ["DR 133", "DR 41", "DR 42", "U 699", "Öl 1"] and SWED == ["DR 216", "DR 344"]
by_all = {r["signum"]: r for r in ALL}
assert "Swen kunungR satti sten æftiR \"Skarþa, sin hemþæga" in nrm(by_all["DR 3"]) and "æft \"Sigtryg kunung" in nrm(by_all["DR 4"])
assert "skipari \"Haralds kunungs" in nrm(by_all["Sm 42"]) and "eR barþus kunungaR" in nrm(by_all["Vg 40"]) and "þa kunungaR barþusk" in nrm(by_all["DR 66"])
assert "landmanna bæztr i \"Danmarku ok fyrstr" in nrm(by_all["DR 133"]) and "a \"Danmarku i hwitawaþum" in nrm(by_all["U 699"]).replace("hvitavaðum", "hwitawaþum") or "Danmarku i hvitava" in (by_all["U 699"].get("normalization") or "")
assert "han warþ døþr a \"Sweþiuþu" in nrm(by_all["DR 216"])
# The language: the diphthong of stæinn kept (stain) or gone (stin), counted in the transliterations per region
def reg_all(r):
    s_ = r["signum"].split()[0]
    if s_ == "DR":
        d = (r.get("district") or "") + " " + (r.get("municipality") or "")
        if "Skåne" in d:
            return "Skåne"
        return None if ("Bornholm" in d or "Blekinge" in d or "Halland" in d) else "Danmark"
    return {"Vg": "Västergötland", "Ög": "Östergötland", "U": "Uppland", "Sö": "Södermanland"}.get(s_)


def diphthong(reg):
    rs = [r for r in ALL if reg_all(r) == reg]
    stain = sum(len(re.findall(r"\bst[ae]in\b", r.get("transliteration") or "")) for r in rs)
    stin = sum(len(re.findall(r"\bst[ie]n\b", r.get("transliteration") or "")) for r in rs)
    return stain, stin


DIP = {reg: diphthong(reg) for reg in ("Danmark", "Skåne", "Västergötland", "Östergötland", "Södermanland", "Uppland")}
assert DIP == {"Danmark": (19, 55), "Skåne": (8, 22), "Västergötland": (13, 69), "Östergötland": (28, 72), "Södermanland": (118, 38), "Uppland": (270, 188)}
mono = lambda reg: pr(DIP[reg][1] / sum(DIP[reg]))  # noqa: E731  share written without the diphthong
# Jelling: Harald's stone DR 42 claims all Denmark
J = next(r for r in ins if r["signum"] == "DR 42")
assert "wan \"Danmork" in J["normalization"] and "dani gærþi kristna" in J["normalization"]

# ---- bilderna ----------------------------------------------------------------------------------------
FILES = commons.wikidata_files(["DR 295", "DR 330", "DR 279"])
INFO = commons.commons_info([FILES[s] for s in FILES])
CREDIT = {"DR 295": ("Bengt A. Lundberg", "CC BY 2.5"), "DR 330": ("Achird", "CC BY-SA 3.0"), "DR 279": ("Ole E. Henriksen", "Public domain")}


def photo(signum: str, text: str) -> str:
    img = {**INFO[FILES[signum]], "signum": signum}
    assert (img["author"], img["licence"]) == CREDIT[signum], (signum, img["author"], img["licence"])
    cap = commons.caption(img, "sv")
    assert cap.startswith(f"{signum}. Foto: ")
    return f"![Runstenen {signum}]({img['thumb']})\n{text} Foto: {cap[len(signum) + 8:]}"


def fig(fil: str, alt: str, text: str, max_w: int = 1600) -> str:
    im = Image.open(os.path.join(ROOT, "utdata", "skane", fil)).convert("RGB")
    if im.width > max_w:
        im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
    out = io.BytesIO()
    im.save(out, "PNG", optimize=True)
    return f"![{alt}]({blog_figures.freeze(out.getvalue())})\n{text}"


MAP = fig("skane_karta.png", "Karta över Skånes vikingatida runstenar",
          f"Skånes {N['Skåne'] - 1} vikingatida runstenar med känd plats, på rikenas ungefärliga gränser omkring 1025: danskt område i rött, "
          "götarnas i grönt. Nästan alla står på slätten i söder och väster. Karta: Vitki, ur Rundata 3.1 (ODbL); gränserna efter "
          "Vitkis rikeskarta (OpenStreetMap och Natural Earth).")
PH_HAL = photo("DR 295", "Hällestad 1 (DR 295), inmurad i Hällestads kyrka i Torna härad: ”Han flydde inte vid Uppsala.”")
PH_GAR = photo("DR 330", "Gårdstånga 2 (DR 330): resta efter två fälagar, ”vida kända i viking”.")
PH_SJO = photo("DR 279", "Sjörupsstenen (DR 279): Saxe satte stenen efter sin fälage Esbjörn, som inte flydde vid Uppsala utan slogs så länge han hade vapen.")

CHART = f""":::chart Andel av runstenarna som …
# … restes eller sattes av den som nämns först (inte ”lät resa”)
+Skåne | {sh('ræisti/satti själv', 'Skåne')} | {nn('ræisti/satti själv', 'Skåne')} av {N['Skåne']}
Danmark (Jylland, Fyn, Själland) | {sh('ræisti/satti själv', 'Danmark')} | {nn('ræisti/satti själv', 'Danmark')} av {N['Danmark']}
Västergötland | {sh('ræisti/satti själv', 'Västergötland')} | {nn('ræisti/satti själv', 'Västergötland')} av {N['Västergötland']}
Uppland | {sh('ræisti/satti själv', 'Uppland')} | {nn('ræisti/satti själv', 'Uppland')} av {sv(N['Uppland'])}
# … nämner en fälage (felagi)
+Skåne | {sh('felagi', 'Skåne')} | {nn('felagi', 'Skåne')} av {N['Skåne']}
Danmark | {sh('felagi', 'Danmark')} | {nn('felagi', 'Danmark')} av {N['Danmark']}
Västergötland | {sh('felagi', 'Västergötland')} | {nn('felagi', 'Västergötland')} av {N['Västergötland']}
Uppland | {sh('felagi', 'Uppland')} | {nn('felagi', 'Uppland')} av {sv(N['Uppland'])}
# … nämner något bortom bygden (Uppsala, Gotland, London, viking, västerut, Sverige)
+Skåne | {sh('bortom bygden', 'Skåne')} | {nn('bortom bygden', 'Skåne')} av {N['Skåne']}
Danmark | {sh('bortom bygden', 'Danmark')} | {nn('bortom bygden', 'Danmark')} av {N['Danmark']}
Södermanland | {sh('bortom bygden', 'Södermanland')} | {nn('bortom bygden', 'Södermanland')} av {N['Södermanland']}
Uppland | {sh('bortom bygden', 'Uppland')} | {nn('bortom bygden', 'Uppland')} av {sv(N['Uppland'])}
# … har ett kors
+Skåne | {sh('kors', 'Skåne')} | {nn('kors', 'Skåne')} av {N['Skåne']} med kors
Danmark | {sh('kors', 'Danmark')} | {nn('kors', 'Danmark')} av {N['Danmark']} med kors
Uppland | {sh('kors', 'Uppland')} | {nn('kors', 'Uppland')} av {sv(N['Uppland'])} med kors
Källa: Samnordisk runtextdatabas 3.1, vikingatida runstenar. Vitkis beräkning; orden räknade i normaliseringen.
:::"""

title = "Hemma mellan rikena – Skånes runstenar"
summary = ("Jag växte upp i Skåne och känner mig varken dansk eller hemma i Stockholm. Så jag ställde frågan till dem som bodde "
           "här för tusen år sedan: var hörde man hemma när stenarna restes? Femtionio runstenar svarar – utan att nämna "
           "vare sig kung eller rike.")

body = f"""Jag växte upp i Skåne. Jag känner mig inte dansk, och jag har aldrig känt att jag hör hemma i Stockholm. Det är en vanlig skånsk känsla, så vanlig att den nästan är en kliché, och jag har länge undrat hur gammal den är. Så jag gjorde det jag brukar göra med sådana frågor: jag ställde den till stenarna. Hur kände sig en människa som levde här när runstenarna restes? Var hon en del av ett rike, eller såg hon bara sin bygd? Det går inte att fråga henne. Men det går att läsa vad hon lät hugga i sten, och räkna.

## Femtionio stenar, en enda generation

Skåne har {N['Skåne']} vikingatida runstenar i Samnordisk runtextdatabas, {S['lost']} av dem försvunna och kända bara ur äldre avbildningar. Nästan alla står på slätten: i Vemmenhögs, Herrestads och Ljunits härader längs sydkusten står {H['Vemmenhögs hd'] + H['Herrestads hd'] + H['Ljunits hd']} av dem, i Torna härad kring Lund {H['Torna hd']}. Skogsbygderna i norr har nästan inga.

{MAP}

Det första som slår en är hur kort tid de spänner över. {S['efter_jelling']['Skåne']} av de {N['Skåne']} dateras till tiden efter Jellingstenen, alltså årtiondena omkring år 1000, medan Danmarks övriga stenar är spridda över ett par hundra år ({S['efter_jelling']['Danmark']} av {N['Danmark']} är från samma period). Skånes stenar restes i en enda generation – den generation som levde under Harald Blåtand, Sven Tveskägg och Knut den store, när Lund grundades som kunglig stad. En av stenarna i Lund säger det rakt ut: *Toki let kirkiu gørwa*, Toke lät göra kyrkan (DR 315).

## De reste själva

Hur säger stenarna det de säger? Som danskarna, inte som svearna. På {nn('ræisti/satti själv', 'Skåne')} av de {N['Skåne']} stenarna reste eller satte den som nämns först stenen själv – *resþi sten þænsi*, *satti sten þænsi* – och bara {nn('lät (let) göra', 'Skåne')} säger *lät*. I Uppland är det tvärtom: där *lät* man resa på {sh('lät (let) göra', 'Uppland')} procent av stenarna och reste själv på {sh('ræisti/satti själv', 'Uppland')}. Skåne delar sitt sätt att tala med Danmark och med Västergötland, som vi har skrivit om förut: [Västgöten reste själv – upplänningen lät resa](/artiklar/reste-sjalv-eller-lat-resa). Också formen är dansk: {nn('RAK', 'Skåne')} av {N['Skåne']} stenar är utan ornamentik, raka textband, och bara {nn('kors', 'Skåne')} bär ett kors, mot nästan varannan sten i Uppland.

Och så har de ett särskilt uttryck för den de saknar. *Harþa goþan dræng*, ”en mycket god dräng” – en ung, duglig man – står på {nn('harþa goþan', 'Skåne')} av Skånes stenar. Frasen finns i Västergötland ({nn('harþa goþan', 'Västergötland')} stenar) och i Danmark ({nn('harþa goþan', 'Danmark')}), men i Småland, Östergötland, Södermanland och Uppland tillsammans på en enda. *Dræng* står på {nn('dræng', 'Skåne')} skånska stenar och *þegn* på {nn('þegn', 'Skåne')}; Kata vid Rydsgård kallar sin man *þægna fyrstr*, den främste bland tegnar (DR 277). Det är inte bara män som reser: Kata, Tonna, Tofa, Ketiley och Åsa står som resare på sina stenar, efter män och söner.

{CHART}

## Fälagen

Det som utmärker Skåne mest är ett ord som nästan ingen annanstans står på en runsten: *felagi*, fälage, den man delade något med – ett skepp, en last, en resa. {nn('felagi', 'Skåne')} av Skånes {N['Skåne']} stenar är resta efter en fälage, {sh('felagi', 'Skåne')} procent. I hela det övriga Danmark är det {nn('felagi', 'Danmark')} stenar, i Västergötland {nn('felagi', 'Västergötland')}, i Uppland {nn('felagi', 'Uppland')} av {sv(N['Uppland'])}. Esbjörn vid Fosie reste sin sten efter Dverg, *felaga sin, dræng goþan*. Hals och Fröbjörn vid Västra Karaby efter Hove, deras fälage. Tolv och Ulv vid Gårdstånga efter Asmund Läpp, deras fälage.

{PH_GAR}

Och fälagarna for. Grannstenen vid Gårdstånga säger om två av dem: *þeR drængiaR waRu wiþa unesiR i wikingu* – de drängarna var vida kända i viking (DR 330). Fader vid Västra Strö lät hugga runorna efter sin bror Assur, *æs nor warþ døþr i wikingu*, som dog i norr i viking, och en sten till efter Björn, *æs skip atti mæþ hanum*, som ägde skepp tillsammans med honom (DR 334, 335). Esbjörn vid Solberga var någons *skipari*, skeppsman (DR 275). Nafnes bror Toke dog västerut (DR 266), Eynds bror Aude på Gotland (DR 259), Manne och Svenne *liggia i Lundunum*, ligger i London (DR 337), och Ravn vid Simris var Gunnulvs sven *a Sweþiuþu* – i Sverige (DR 344).

Räknar man allt som pekar bortom bygden – Uppsala, Gotland, London, viking, västerut, Sverige – nämns det på {nn('bortom bygden', 'Skåne')} av Skånes {N['Skåne']} stenar, {sh('bortom bygden', 'Skåne')} procent. Det är mer än någon annanstans: Danmark {sh('bortom bygden', 'Danmark')} procent, Södermanland med sina Ingvarsstenar {sh('bortom bygden', 'Södermanland')}, Uppland {sh('bortom bygden', 'Uppland')}. Skånes horisont var havet. Den som stod på slätten vid Vemmenhög och såg söderut såg inte en gräns utan en väg.

## En herre, men ingen kung

Så var hörde man hemma? Ingen av de {N['Skåne']} stenarna nämner en kung. Ingen nämner Danmark. Det ordet står på Jellingstenen, där Harald säger att han vann sig hela Danmark och gjorde danerna kristna – men det är kungens ord, i Jylland. Och det är inte en skånsk egenhet. Av Nordens {sv(len(ALL))} vikingatida runstenar nämner {len(KING)} en kung, och fyra av dem är kungarnas egna: de två Jellingstenarna, kung Svens sten vid Hedeby efter hans hustegn Skarde (DR 3) och Asfrids efter kung Sigtrygg (DR 4). Av de övriga fyra är en Rökstenen, en Tuna i Småland där Assur var *skipari Haralds kunungs*, kung Haralds skeppsman (Sm 42), och två säger bara att mannen dog *när kungar stred* (Vg 40, DR 66). Ordet Danmark står på {len(DANM)} stenar: Jellingstenarna, Skivum på Jylland där den döde var *landmanna bæztr i Danmarku*, den bäste av landmän i Danmark (DR 133), versen på Karlevistenen på Öland och Amnö i Uppland, där Brune dog i Danmark i dopkläder (U 699). Sverige, *Sweþiuþ*, står på {len(SWED)} – båda danska, Tirsted på Lolland och Simris, och båda om någon som var borta där. Riket var ett ord för kungar och för dem som dog utomlands. På Skånes stenar hör människorna hemma hos någon annan: hos en herre.

{PH_HAL}

Vid Hällestads kyrka i Torna härad sitter tre stenar i kyrkväggen. Den första satte Eskil efter *Toka Gorms sun, seR hullan drottin* – Toke Gormsson, honom en huld herre. *SaR flo ægi at Upsalum*: han flydde inte vid Uppsala. Drängarna satte stenen efter sin bror på berget, *støþan runum*, stadgad med runor, och *þeR Gorms Toka gingu næstiR* – de gick närmast Gorms Toke (DR 295). På de två andra kallar sig resarna *hemþægi Toka*, Tokes hustegn, hans hirdman (DR 296, 297). Och tre mil därifrån, vid Sjörup, satte Saxe en sten efter sin fälage Esbjörn, *saR flo ægi at Upsalum æn wa mæþ han wapn hafþi* – han flydde inte vid Uppsala utan slogs så länge han hade vapen (DR 279).

{PH_SJO}

Forskningen brukar knyta de fyra stenarna till slaget på Fyrisvallarna utanför Uppsala omkring 985, där en dansk här stred mot sveakungen. Vad de säger om tillhörighet är tydligt nog utan slaget: skåningarna for till Uppsala för att slåss *mot* svearna, under en skånsk herre, Toke Gormsson, och det som räknades hemma var att man inte flydde. Sverige var det ställe där Ravn var Gunnulvs sven, någon annanstans.

## Samma språk som fienden

En sak till om Uppsala. De som for dit för att slåss mot svearna talade svearnas språk. Hela Norden kallade sitt språk *dǫnsk tunga*, den danska tungan, och på runstenarna är grammatiken och orden desamma från Jylland till Uppland; det som skiljer dem åt är seder – *satti*, *reste själv*, fälagen – inte språket. Det som i dag gör att en skåning och en stockholmare förstår en dansk med nöd och näppe hände nästan helt efter runstenarnas tid: att *kaka* blev *kage* och *gata* blev *gade*, att ändelserna slätades ut och stötljudet kom, allt från 1100- och 1200-talen och framåt.

En enda förändring var på väg, och den syns i runorna. Diftongen i *stæinn* höll på att bli *e*: *stain* blev *stin*. I Danmark skrivs ordet utan diftong på {mono('Danmark')} procent av beläggen, i Skåne på {mono('Skåne')}. Men det gör Västergötland också, på {mono('Västergötland')} procent, och Östergötland på {mono('Östergötland')}. Det är Södermanland ({mono('Södermanland')} procent) och Uppland ({mono('Uppland')}) som håller fast vid *stain*. Gränsen i språket gick alltså inte vid Öresund utan tvärs genom Sverige, mellan götar och svear – samma gräns som stavningen ritade i [Västgötarna skrev som danskarna](/artiklar/vastgotarna-skrev-som-danskarna). En skåning och en västgöte lät likadant omkring år 1000. Den som avvek var upplänningen, och det var ändå ett uttal, inte ett annat språk. Toke Gormssons män och svearna vid Uppsala förstod varandra utan tolk. De var fiender, inte främlingar.

Men herren är inte riket. Det som stenarna håller fast vid är mindre och närmare: fälagen, brodern, fadern, gården. Tume ägde Gudissnapa (DR 280). Folkve ägde Högby (DR 264). Bram vid Sövestad var *bæztr bomanna ok mildastr mataR*, den bäste av bönder och den mest frikostige med mat (DR 291); Olav och Ottar vid Lund var *landmænnr goþa*, goda landmän (DR 314); Stenkel vid Dalby *goþan bonda* (DR 298). Hunnestads stenar står efter Gunne Hands söner (DR 282). Det är så en skåning omkring år 1000 säger var han hör hemma: hos sin herre, bland sina fälagar, på sin gård, i sin by. Riket säger han ingenting om.

## Gud kom till sist – och stenarna tystnade

Tre av stenarna ber: för Aude som dog på Gotland, för Manne och Svenne i London, för Forkunn vid Simris. Tre av {N['Skåne']}, mot var sjunde sten i Uppland. Korsen är åtta. Skånes stenar är nästan helt kvar i den gamla världen, och den nya kommer med dem som dog långt borta – på Gotland, i London – och med Toke som lät göra kyrkan i Lund.

Sedan tar det slut. Bara en av Skånes stenar dateras till tiden efter 1050, Simris 1, medan {U_LATE} procent av Upplands stilbestämda stenar hör till stilgrupperna från just den tiden, Pr3 till Pr5. När Mälardalen reser som mest har Skåne slutat. Den vanliga förklaringen är kyrkan: i Lund växte domkyrkan och gravarna flyttade in under golven, och den som ville bli ihågkommen behövde inte längre en sten vid vägen. Skåne blev kristet, minnet flyttade in i kyrkan, och stenarna var det sista som den gamla bygden sade med egen röst.

## Vad de svarar

Jag frågade stenarna om de kände sig danska. De svarade inte på frågan, och det är svaret. Ingen av dem säger dansk, ingen säger svensk, ingen säger rike. De säger fälage, bror, far, herre, gård, dräng, och de säger Uppsala, Gotland och London. Att höra hemma var att höra till människor – den man följde, den man delade skepp med, den man ärvde jord av – och att ha havet som horisont. Riket var kungens sak, nedskriven på hans sten i Jylland. Bygden var deras.

Jag känner igen mig i det, mer än jag väntade mig. Det är inte så att jag är dansk, och det var inte de heller, i någon mening de själva skulle ha förstått. De var hemma vid Hällestad och Gårdstånga, med vägen mot havet öppen. Frågan om jag hör hemma i Stockholm skulle de ha haft svårt att alls förstå; de hörde hemma hos varandra.

Vill du pröva det själv, gå till Hällestads kyrka. Stenarna sitter i väggen, och den första säger vad tusen år inte har ändrat: att det som räknades var att man inte flydde, och vem man gick närmast.

:::box Det viktigaste i korthet
- Skånes {N['Skåne']} runstenar restes i en enda generation, årtiondena omkring år 1000, och de talar som Danmarks och Västergötlands stenar: den som reste gjorde det själv, utan ornamentik, nästan utan kors, och efter ”en mycket god dräng”.
- Det som utmärker dem är fälagen och havet: inga stenar i Norden nämner så ofta en fälage, och ingen landsdel pekar så ofta bortom bygden – Uppsala, Gotland, London, viking.
- Ingen sten nämner kung eller rike – och det gör nästan ingen runsten i Norden: åtta av 2 633 nämner en kung, fyra av dem kungarnas egna. Tillhörigheten på stenarna är en herre, fälagar, bröder och gården; vid Hällestad och Sjörup är den också att inte ha flytt vid Uppsala, på danskt uppdrag mot svearna – som talade samma språk. Det som gör danska svårt för oss i dag kom först efter runstenarnas tid.
- Stenarna tystnar omkring 1050, när Mälardalens är som flest. Det Skåne sade med egen röst sade det före kyrkan och riket tog över minnet.
:::

:::box Så räknade vi
Vikingatida runstenar (också fragment) i Samnordisk runtextdatabas 3.1; Skåne är de DR-stenar vars härad ligger i Skåne, Danmark de övriga danska utom Bornholm, Blekinge och Halland. Orden är räknade i Rundatas normalisering, med dansk och svensk stavning sammanförd: *felagi*, *dræng*, *þegn*, *harþa goþan*, *let* mot *resþi/satti*, Gud, och platser bortom bygden (Uppsala, Gotland, London, viking, västerut, Sverige). Dateringarna är Rundatas (Jellingstenens tid omkring 965 som gräns). Diftongen är räknad i translittereringarna: *stain* och *stein* mot *stin* och *sten*, alla belägg i varje landskap. Allt är beskrivande – andelar, inga test – och ligger öppet i kodförrådet (utdata/skane). Kartans gränser är Vitkis rikeskarta omkring 1025, ungefärliga.
:::

## Källor

- Samnordisk runtextdatabas, version 3.1 (ODbL).
- Jacobsen, L. & Moltke, E. 1941–42. *Danmarks runeindskrifter.* København.
- Jesch, J. 2001. *Ships and Men in the Late Viking Age: The Vocabulary of Runic Inscriptions and Skaldic Verse.* Woodbridge.
- Sawyer, B. 2000. *The Viking-Age Rune-Stones: Custom and Commemoration in Early Medieval Scandinavia.* Oxford.
- Foton: se bildtexterna."""

assert not re.search(r"^\|", body, re.M) and "Jag växte upp i Skåne" in body
out = {"slug": "hemma-mellan-rikena-skanes-runstenar", "title": title, "summary": summary, "body": body,
       "title_en": "", "summary_en": "", "body_en": "", "labels": ["Personligt", "Norden", "Formler och syfte"]}
json.dump(out, open(os.path.join(ROOT, "utdata", "blogg", "skane.json"), "w"), ensure_ascii=False, indent=1)
print(os.path.join(ROOT, "utdata", "blogg", "skane.json"), len(body.split()), "ord")

if "--update" in sys.argv or "--write" in sys.argv:
    from api.routers import blog
    col = blog.firestore().collection(blog.COLLECTION)
    now = dt.datetime.now(dt.timezone.utc)
    if "--update" in sys.argv:
        doc = sys.argv[sys.argv.index("--update") + 1]
        ref = col.document(doc)
        old = ref.get().to_dict()
        assert old and old.get("slug") == out["slug"] and not old.get("published"), "Bara opublicerade utkast skrivs över härifrån"
        ref.set({**out, "updatedAt": now}, merge=True)
        print("uppdaterat utkast:", doc)
    else:
        assert not [p for p in blog._all() if p.get("slug") == out["slug"]], "Adressen används redan; skriv över med --update"
        ref = col.document()
        ref.set({**out, "published": False, "month": now.strftime("%Y-%m"), "author": "Viktor Kvant",
                 "topic": "Skåne|personligt", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
