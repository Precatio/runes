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


def photo_en(signum: str, text: str) -> str:
    img = {**INFO[FILES[signum]], "signum": signum}
    cap = commons.caption(img, "en")
    assert cap.startswith(f"{signum}. Photo: ")
    return f"![The runestone {signum}]({img['thumb']})\n{text} Photo: {cap[len(signum) + 9:]}"


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

MAP_EN = fig("skane_karta.png", "Map of the Viking-age runestones of Skåne",
             f"Skåne's {N['Skåne'] - 1} Viking-age runestones with a known site, on the approximate borders of the realms around 1025: Danish "
             "territory in red, the Geats' in green. Nearly all stand on the plain in the south and west. Map: Vitki, from Rundata 3.1 "
             "(ODbL); borders after Vitki's map of the realms (OpenStreetMap and Natural Earth).")
PH_HAL_EN = photo_en("DR 295", "Hällestad 1 (DR 295), built into the wall of Hällestad church in Torna hundred: “He did not flee at Uppsala.”")
PH_GAR_EN = photo_en("DR 330", "Gårdstånga 2 (DR 330): raised in memory of two partners, “widely renowned on viking raids”.")
PH_SJO_EN = photo_en("DR 279", "The Sjörup stone (DR 279): Saxi placed the stone in memory of his partner Ásbjôrn, who did not flee at Uppsala but fought as long as he had a weapon.")
CHART_EN = f""":::chart Share of the runestones that …
# … were raised or placed by the person named first (not “had raised”)
+Skåne | {sh('ræisti/satti själv', 'Skåne')} | {nn('ræisti/satti själv', 'Skåne')} of {N['Skåne']}
Denmark (Jutland, Funen, Zealand) | {sh('ræisti/satti själv', 'Danmark')} | {nn('ræisti/satti själv', 'Danmark')} of {N['Danmark']}
Västergötland | {sh('ræisti/satti själv', 'Västergötland')} | {nn('ræisti/satti själv', 'Västergötland')} of {N['Västergötland']}
Uppland | {sh('ræisti/satti själv', 'Uppland')} | {nn('ræisti/satti själv', 'Uppland')} of {N['Uppland']:,}
# … name a partner (felagi)
+Skåne | {sh('felagi', 'Skåne')} | {nn('felagi', 'Skåne')} of {N['Skåne']}
Denmark | {sh('felagi', 'Danmark')} | {nn('felagi', 'Danmark')} of {N['Danmark']}
Västergötland | {sh('felagi', 'Västergötland')} | {nn('felagi', 'Västergötland')} of {N['Västergötland']}
Uppland | {sh('felagi', 'Uppland')} | {nn('felagi', 'Uppland')} of {N['Uppland']:,}
# … mention something beyond the district (Uppsala, Gotland, London, viking raids, the west, Sweden)
+Skåne | {sh('bortom bygden', 'Skåne')} | {nn('bortom bygden', 'Skåne')} of {N['Skåne']}
Denmark | {sh('bortom bygden', 'Danmark')} | {nn('bortom bygden', 'Danmark')} of {N['Danmark']}
Södermanland | {sh('bortom bygden', 'Södermanland')} | {nn('bortom bygden', 'Södermanland')} of {N['Södermanland']}
Uppland | {sh('bortom bygden', 'Uppland')} | {nn('bortom bygden', 'Uppland')} of {N['Uppland']:,}
# … carry a cross
+Skåne | {sh('kors', 'Skåne')} | {nn('kors', 'Skåne')} of {N['Skåne']} with a cross
Denmark | {sh('kors', 'Danmark')} | {nn('kors', 'Danmark')} of {N['Danmark']} with a cross
Uppland | {sh('kors', 'Uppland')} | {nn('kors', 'Uppland')} of {N['Uppland']:,} with a cross
Source: Scandinavian Runic-text Database 3.1, Viking-age runestones. Vitki's count; the words counted in the normalisation.
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

title_en = "At Home Between the Realms – the Runestones of Skåne"
summary_en = ("I grew up in Skåne and feel neither Danish nor at home in Stockholm. So I put the question to the people who "
              "lived here a thousand years ago: where did one belong when the stones were raised? Fifty-nine runestones "
              "answer – without naming either king or realm.")

body_en = f"""I grew up in Skåne. I do not feel Danish, and I have never felt that I belong in Stockholm. It is a common Skåne feeling, so common that it is almost a cliché, and I have long wondered how old it is. So I did what I usually do with such questions: I put it to the stones. How did a person who lived here feel when the runestones were raised? Was she part of a realm, or did she only see her own district? She cannot be asked. But what she had cut in stone can be read, and counted.

## Fifty-nine stones, a single generation

Skåne has {N['Skåne']} Viking-age runestones in the Scandinavian Runic-text Database, {S['lost']} of them lost and known only from older drawings. Nearly all stand on the plain: in the hundreds of Vemmenhög, Herrestad and Ljunits along the south coast stand {H['Vemmenhögs hd'] + H['Herrestads hd'] + H['Ljunits hd']} of them, in Torna hundred around Lund {H['Torna hd']}. The forest districts in the north have almost none.

{MAP_EN}

The first thing that strikes you is how short a time they span. {S['efter_jelling']['Skåne']} of the {N['Skåne']} are dated to the period after the Jelling stone, that is the decades around the year 1000, while Denmark's other stones are spread over a couple of centuries ({S['efter_jelling']['Danmark']} of {N['Danmark']} are from the same period). Skåne's stones were raised in a single generation – the generation that lived under Harald Bluetooth, Sweyn Forkbeard and Cnut the Great, when Lund was founded as a royal town. One of the stones in Lund says so outright: *Toki let kirkiu gørwa*, Tóki had the church made (DR 315).

## They raised them themselves

How do the stones say what they say? Like the Danes, not like the Swedes. On {nn('ræisti/satti själv', 'Skåne')} of the {N['Skåne']} stones the person named first raised or placed the stone personally – *resþi sten þænsi*, *satti sten þænsi* – and only {nn('lät (let) göra', 'Skåne')} say *had*. In Uppland it is the other way round: there one *had* a stone raised on {sh('lät (let) göra', 'Uppland')} per cent of the stones and raised it oneself on {sh('ræisti/satti själv', 'Uppland')}. Skåne shares its way of speaking with Denmark and with Västergötland, which we have written about before: [Raise It Yourself – or Have It Raised](/en/artiklar/reste-sjalv-eller-lat-resa). The form is Danish too: {nn('RAK', 'Skåne')} of {N['Skåne']} stones are without ornament, plain text bands, and only {nn('kors', 'Skåne')} carry a cross, against nearly every second stone in Uppland.

And they have a particular expression for the one they miss. *Harþa goþan dræng*, “a very good dreng” – a young, able man – stands on {nn('harþa goþan', 'Skåne')} of Skåne's stones. The phrase occurs in Västergötland ({nn('harþa goþan', 'Västergötland')} stones) and in Denmark ({nn('harþa goþan', 'Danmark')}), but in Småland, Östergötland, Södermanland and Uppland together on a single one. *Dræng* stands on {nn('dræng', 'Skåne')} Skåne stones and *þegn* on {nn('þegn', 'Skåne')}; Káta at Rydsgård calls her husband *þægna fyrstr*, first among thegns (DR 277). Nor is it only men who raise: Káta, Tonna, Tófa, Ketiley and Ása stand as raisers on their stones, for husbands and sons.

{CHART_EN}

## The partner

What distinguishes Skåne most is a word that hardly stands on a runestone anywhere else: *felagi*, partner, the one you shared something with – a ship, a cargo, a voyage. {nn('felagi', 'Skåne')} of Skåne's {N['Skåne']} stones are raised for a partner, {sh('felagi', 'Skåne')} per cent. In all the rest of Denmark it is {nn('felagi', 'Danmark')} stones, in Västergötland {nn('felagi', 'Västergötland')}, in Uppland {nn('felagi', 'Uppland')} of {N['Uppland']:,}. Ásbjôrn at Fosie raised his stone for Dvergr, *felaga sin, dræng goþan*. Hals and Freybjôrn at Västra Karaby for Hofi, their partner. Þólfr and Ulfr at Gårdstånga for Ásmundr Lip, their partner.

{PH_GAR_EN}

And the partners travelled. The neighbouring stone at Gårdstånga says of two of them: *þeR drængiaR waRu wiþa unesiR i wikingu* – those drengs were widely renowned on viking raids (DR 330). Faðir at Västra Strö had the runes cut for his brother Ôzurr, *æs nor warþ døþr i wikingu*, who died in the north on a viking raid, and another stone for Bjôrn, *æs skip atti mæþ hanum*, who owned a ship together with him (DR 334, 335). Ásbjôrn at Solberga was someone's *skipari*, seaman (DR 275). Nafni's brother Tóki died in the west (DR 266), Eyndr's brother Auði on Gotland (DR 259), Manni and Sveini *liggia i Lundunum*, lie in London (DR 337), and Hrafn at Simris was Gunnulfr's lad *a Sweþiuþu* – in Sweden (DR 344).

Counting everything that points beyond the district – Uppsala, Gotland, London, viking raids, the west, Sweden – it is mentioned on {nn('bortom bygden', 'Skåne')} of Skåne's {N['Skåne']} stones, {sh('bortom bygden', 'Skåne')} per cent. That is more than anywhere else: Denmark {sh('bortom bygden', 'Danmark')} per cent, Södermanland with its Ingvar stones {sh('bortom bygden', 'Södermanland')}, Uppland {sh('bortom bygden', 'Uppland')}. Skåne's horizon was the sea. Whoever stood on the plain at Vemmenhög and looked south saw not a border but a road.

## A lord, but no king

So where did one belong? None of the {N['Skåne']} stones names a king. None names Denmark. That word stands on the Jelling stone, where Harald says that he won himself all of Denmark and made the Danes Christian – but those are the king's words, in Jutland.

And it is not a Skåne peculiarity. Of the North's {len(ALL):,} Viking-age runestones, {len(KING)} name a king, and four of them are the kings' own: the two Jelling stones, King Sweyn's stone at Hedeby for his retainer Skarði (DR 3) and Ásfríðr's for King Sigtryggr (DR 4). Of the other four, one is the Rök stone, one is Tuna in Småland where Ôzurr was *skipari Haralds kunungs*, King Harald's seaman (Sm 42), and two say only that the man died *when kings fought* (Vg 40, DR 66). The word Denmark stands on {len(DANM)} stones: the Jelling stones, Skivum in Jutland where the dead man was *landmanna bæztr i Danmarku*, the best of landholders in Denmark (DR 133), the verse on the Karlevi stone on Öland, and Amnö in Uppland, where Brúni died in Denmark in christening robes (U 699). Sweden, *Sweþiuþ*, stands on {len(SWED)} – both Danish, Tirsted on Lolland and Simris, and both about someone who was away there. The realm was a word for kings and for those who died abroad. On Skåne's stones people belong to someone else: to a lord.

{PH_HAL_EN}

At Hällestad church in Torna hundred three stones sit in the church wall. The first Áskell placed for *Toka Gorms sun, seR hullan drottin* – Tóki Gormr's son, to him a faithful lord. *SaR flo ægi at Upsalum*: he did not flee at Uppsala. The drengs placed the stone for their brother on the hill, *støþan runum*, steadied by runes, and *þeR Gorms Toka gingu næstiR* – they went closest to Gormr's Tóki (DR 295). On the two others the raisers call themselves *hemþægi Toka*, Tóki's house-thegns, his retainers (DR 296, 297). And thirty kilometres away, at Sjörup, Saxi placed a stone for his partner Ásbjôrn, *saR flo ægi at Upsalum æn wa mæþ han wapn hafþi* – he did not flee at Uppsala but fought as long as he had a weapon (DR 279).

{PH_SJO_EN}

Scholars usually connect the four stones with the battle of Fýrisvellir outside Uppsala around 985, where a Danish army fought the king of the Swedes. What they say about belonging is clear enough without the battle: the men of Skåne went to Uppsala to fight *against* the Swedes, under a Skåne lord, Tóki Gormsson, and what counted at home was that one did not flee. Sweden was the place where Hrafn was Gunnulfr's lad, somewhere else.

## The same language as the enemy

One more thing about Uppsala. Those who went there to fight the Swedes spoke the Swedes' language. The whole North called its language *dǫnsk tunga*, the Danish tongue, and on the runestones grammar and words are the same from Jutland to Uppland; what separates them is custom – *satti*, raising it oneself, the partner – not language. What today makes a Skåning or a Stockholmer understand a Dane only with difficulty happened almost entirely after the runestones' time: *kaka* becoming *kage* and *gata* becoming *gade*, the endings being levelled and the glottal stop arriving, all from the twelfth and thirteenth centuries onward.

A single change was under way, and it shows in the runes. The diphthong in *stæinn* was turning into *e*: *stain* was becoming *stin*. In Denmark the word is written without the diphthong in {mono('Danmark')} per cent of the attestations, in Skåne in {mono('Skåne')}. But so it is in Västergötland, in {mono('Västergötland')} per cent, and in Östergötland in {mono('Östergötland')}. It is Södermanland ({mono('Södermanland')} per cent) and Uppland ({mono('Uppland')}) that hold on to *stain*. The line in the language thus ran not at the Sound but straight through Sweden, between Geats and Swedes – the same line that the spelling drew in [The Geats Wrote Like the Danes](/en/artiklar/vastgotarna-skrev-som-danskarna). A man from Skåne and a man from Västergötland sounded alike around the year 1000. The one who differed was the Upplander, and even that was a pronunciation, not another language. Tóki Gormsson's men and the Swedes at Uppsala understood each other without an interpreter. They were enemies, not strangers.

But the lord is not the realm. What the stones hold on to is smaller and closer: the partner, the brother, the father, the farm. Tumi owned Guðissnapi (DR 280). Folkvé owned Haugbýr (DR 264). Bramr at Sövestad was *bæztr bomanna ok mildastr mataR*, the best of farmers and the most generous with food (DR 291); Ólafr and Óttarr at Lund were *landmænnr goþa*, good landholders (DR 314); Steinkell at Dalby *goþan bonda* (DR 298). The Hunnestad stones stand for Gunni Hand's sons (DR 282). That is how a man of Skåne around the year 1000 says where he belongs: with his lord, among his partners, on his farm, in his village. Of the realm he says nothing.

## God came last – and the stones fell silent

Three of the stones pray: for Auði who died on Gotland, for Manni and Sveini in London, for Forkunn at Simris. Three of {N['Skåne']}, against every seventh stone in Uppland. The crosses are eight. Skåne's stones remain almost wholly in the old world, and the new one arrives with those who died far away – on Gotland, in London – and with Tóki who had the church made in Lund.

Then it ends. Only one of Skåne's stones is dated after 1050, Simris 1, while {U_LATE} per cent of Uppland's style-dated stones belong to the style groups of precisely that time, Pr3 to Pr5. When the Mälaren valley raises the most, Skåne has stopped. The usual explanation is the church: in Lund the cathedral grew and the graves moved in under its floors, and whoever wanted to be remembered no longer needed a stone by the road. Skåne became Christian, memory moved into the church, and the stones were the last thing the old district said in its own voice.

## What they answer

I asked the stones whether they felt Danish. They did not answer the question, and that is the answer. None of them says Danish, none says Swedish, none says realm. They say partner, brother, father, lord, farm, dreng, and they say Uppsala, Gotland and London. To belong was to belong to people – the one you followed, the one you shared a ship with, the one you inherited land from – and to have the sea as your horizon. The realm was the king's business, written down on his stone in Jutland. The district was theirs.

I recognise myself in that, more than I expected. It is not that I am Danish, and neither were they, in any sense they themselves would have understood. They were at home at Hällestad and Gårdstånga, with the road to the sea open. The question whether I belong in Stockholm they would have found hard to understand at all; they belonged to each other.

If you want to test it yourself, go to Hällestad church. The stones sit in the wall, and the first says what a thousand years have not changed: that what counted was that one did not flee, and whom one went closest to.

:::box The essentials in brief
- Skåne's {N['Skåne']} runestones were raised in a single generation, the decades around the year 1000, and they speak like the stones of Denmark and Västergötland: whoever raised one did it personally, without ornament, almost without crosses, and for “a very good dreng”.
- What distinguishes them is the partner and the sea: no stones in the North name a partner so often, and no region points so often beyond the district – Uppsala, Gotland, London, viking raids.
- No stone names king or realm – and hardly any runestone in the North does: eight of 2,633 name a king, four of them the kings' own. Belonging on the stones is a lord, partners, brothers and the farm; at Hällestad and Sjörup it is also not having fled at Uppsala, on a Danish errand against the Swedes – who spoke the same language. What makes Danish hard for us today came only after the runestones' time.
- The stones fall silent around 1050, when the Mälaren valley's are at their most numerous. What Skåne said in its own voice it said before the church and the realm took over memory.
:::

:::box How we counted
Viking-age runestones (fragments included) in the Scandinavian Runic-text Database 3.1; Skåne is the DR stones whose hundred lies in Skåne, Denmark the other Danish ones except Bornholm, Blekinge and Halland. The words are counted in Rundata's normalisation, with Danish and Swedish spelling merged: *felagi*, *dræng*, *þegn*, *harþa goþan*, *let* against *resþi/satti*, God, and places beyond the district (Uppsala, Gotland, London, viking raids, the west, Sweden). The datings are Rundata's (the time of the Jelling stone, around 965, as the boundary). The diphthong is counted in the transliterations: *stain* and *stein* against *stin* and *sten*, every attestation in each region. Everything is descriptive – shares, no tests – and lies open in the repository (utdata/skane). The map's borders are Vitki's map of the realms around 1025, approximate.
:::

## Sources

- Scandinavian Runic-text Database, version 3.1 (ODbL).
- Jacobsen, L. & Moltke, E. 1941–42. *Danmarks runeindskrifter.* Copenhagen.
- Jesch, J. 2001. *Ships and Men in the Late Viking Age: The Vocabulary of Runic Inscriptions and Skaldic Verse.* Woodbridge.
- Sawyer, B. 2000. *The Viking-Age Rune-Stones: Custom and Commemoration in Early Medieval Scandinavia.* Oxford.
- Photos: see the captions."""

assert not re.search(r"^\|", body, re.M) and "Jag växte upp i Skåne" in body
assert not re.search(r"^\|", body_en, re.M) and "I grew up in Skåne" in body_en and body_en.count("## ") == body.count("## ")
out = {"slug": "hemma-mellan-rikena-skanes-runstenar", "title": title, "summary": summary, "body": body,
       "title_en": title_en, "summary_en": summary_en, "body_en": body_en, "labels": ["Personligt", "Norden", "Formler och syfte"]}
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
