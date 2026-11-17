"""Artikeln "Asatron i landskapet" (sv + en): kultplatserna, tingen och gudanamnen i Svenskt ortnamnslexikon. Låsta planer
analysplaner/2026-11-17-gudarna-pa-kartan.md (e120282a) och tillägg 1 (f7b339ef); resultat utdata/asatro/resultat.json och
resultat_tillagg1.json; kartan utdata/asatro/karta.py. Citaten ur Nordberg 2018 och Nyman 2022 prövas mot tidskrifternas
text (sok.sqlite), SOL:s korta citat mot den nedladdade lexikontexten (utanför git).
    ../../../.venv/bin/python build_asatro.py [--write | --update DOC]"""
import datetime as dt
import io
import json
import os
import re
import sqlite3
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_figures, blog_labels  # noqa: E402
from utdata.norge.citat import letters  # noqa: E402

A = os.path.join(ROOT, "utdata", "asatro")
M = json.load(open(os.path.join(A, "resultat.json"), encoding="utf-8"))
T = json.load(open(os.path.join(A, "resultat_tillagg1.json"), encoding="utf-8"))
assert M["sha"] == "e120282a" and T["sha"] == "f7b339ef"

# ---- the numbers -----------------------------------------------------------------------------------------------------
B = M["B"]
assert B["n"] == 32 and not B["B1"]["haller"] and not B["B2"]["haller"]
assert round(B["B1"]["p"], 2) == 0.46 and round(B["B2"]["p"], 2) == 0.39
TOR_REG = B["tabell"]["Tor"]
assert len(TOR_REG) == 7 and sum(TOR_REG.values()) == 14
assert (sum(B["tabell"]["Oden"].values()), sum(B["tabell"]["Frö"].values())) == (11, 7)
C1, C2 = T["C1"], T["C2"]
assert C1["haller"] and C1["p_holm"] < 0.005 and not C2["haller"]
S = C1["andel_per_landsdel"]
SH = {r: 100 * v["kult"] / v["n"] for r, v in S.items()}
assert (S["Mälarlanden"]["kult"], S["Mälarlanden"]["n"], S["Norr"]["kult"], S["Norr"]["n"]) == (39, 1091, 15, 1363)
assert (round(SH["Mälarlanden"], 1), round(SH["Norr"], 1)) == (3.6, 1.1)
SAMI = {"Áhkká", "Nammásj", "Unna Sájvva", "Tarradalen"}
sami = [x for x in T["namn"] if x["namn"] in SAMI]
assert len(sami) == 4 and all(x["region"] == "Norr" and x["kategori"] == "kultplats" for x in sami)
NORR_UTAN = 100 * (15 - 4) / 1363
assert round(NORR_UTAN, 1) == 0.8
K = [x for x in T["namn"] if x["kategori"] == "kultplats"]
assert (len(K), sum(x["grad"] == "säker" for x in K)) == (128, 50)
TING = [x for x in T["namn"] if x["kategori"] == "ting"]
assert len(TING) == 52 and sum(1 for x in TING if x["region"] == "Mälarlanden") == 25
VAS = [x for x in T["namn"] if x["kategori"] == "väsen"]
assert len(VAS) == 10 and sum(x["sen"] == "ja" for x in VAS) == 7
assert T["oenig_kategori"] == 12 and T["oenig_grad"] == 3 and T["indata"] == 402
NAMED = {x["namn"]: x for x in K}
for n, land, grad in (("Odensvi", "Västmanland", "säker"), ("Torsvi", "Uppland", "säker"), ("Ullvi", "Västmanland", "säker"),
                      ("Härnevi", "Uppland", "säker"), ("Torsburgen", "Gotland", "säker"), ("Fröslunda", "Uppland", "säker"),
                      ("Gudhem", "Västergötland", "säker"), ("Hellvi", "Gotland", "säker")):
    assert any(x["namn"] == n and x["landskap"] == land and x["grad"] == grad for x in K), n
assert any(x["namn"] == "Torsåker" and x["landskap"] == "Ångermanland" for x in K)
assert any(x["namn"] == "Anundshögen" and x["grad"] == "säker" for x in TING)
assert any(x["namn"] == "Tingstäde" for x in TING)
assert {x["namn"] for x in VAS} >= {"Trollhättan", "Trollaborg", "Vätteryd", "Stalon"}

# ---- SOL, briefly (copyright: read and quoted briefly with source) ---------------------------------------------------
SOL = json.load(open("/Volumes/2TB/Antigrvity/Runes/downloads/asatro/isof_sol/sol_entries.json", encoding="utf-8"))
sol_text = {e["name"]: re.sub(r"\s+", " ", e["text"]) for e in SOL if e["name"] == "Odensvi"}
assert "vi ’helig plats, kultplats’" in sol_text["Odensvi"]

# ---- part 2: the graves (analysplaner/2026-11-17-kultplatsernas-landskap.md, 55a61e0d) ---------------------------
import csv as _csv  # noqa: E402
import statistics as _st  # noqa: E402
L = json.load(open(os.path.join(A, "resultat_landskap.json"), encoding="utf-8"))
assert L["sha"] == "55a61e0d" and L["kultsocknar"] == 78 and L["socknar"] == 1844
CONF = {(r, x["feature"]): x for r in ("huvud", "bytta") for x in L[r]["kandidater"]}
for f in ("gravfalt", "hog"):
    assert CONF[("huvud", f)]["bekraftat"] and CONF[("bytta", f)]["bekraftat"], f
for f in ("kyrka", "ting", "fornborg"):
    assert not any(CONF.get((r, f), {}).get("bekraftat") for r in ("huvud", "bytta")), f
LD = list(_csv.DictReader(open(os.path.join(A, "landskap_drag.csv"), encoding="utf-8")))
_c = [x for x in LD if x["cult"] == "1"]
_o = [x for x in LD if x["cult"] == "0"]
NO_GRAVE = (100 * sum(x["gravfalt"] == "0" for x in _c) / len(_c), 100 * sum(x["gravfalt"] == "0" for x in _o) / len(_o))
NO_MOUND = (100 * sum(x["hog"] == "0" for x in _c) / len(_c), 100 * sum(x["hog"] == "0" for x in _o) / len(_o))
assert [round(v) for v in NO_GRAVE] == [5, 28] and [round(v) for v in NO_MOUND] == [14, 28]


def _ratio(v):
    by = {}
    for x in LD:
        by.setdefault(x["land"], []).append(int(x[v]))
    obs = sum(int(x[v]) for x in _c)
    exp = sum(_st.mean(by[x["land"]]) for x in _c)
    return obs / exp


R_GRAVE, R_MOUND = _ratio("gravfalt"), _ratio("hog")
assert (round(R_GRAVE, 2), round(R_MOUND, 2)) == (1.33, 1.62)
# ---- part 3: the runestones in the cult parishes (analysplaner/2026-11-17-korset-och-kultplatserna.md, 90e7af35)
KR = json.load(open(os.path.join(A, "resultat_korset.json"), encoding="utf-8"))
assert KR["sha"] == "90e7af35" and not any(KR[k]["haller"] for k in ("K1", "K2", "K3"))
assert round(KR["K1"]["kvot"], 2) == 0.95
HED = {x["signum"]: x for x in KR["hedniska"]}
assert len(HED) == 7 and [s_ for s_, x in HED.items() if x["kultsocken"]] == ["Sö 140", "U 1161"]
_share = KR["K1"]["stenar_i_kultsocknar"] / KR["K1"]["stenar"]
P2 = 1 - (1 - _share) ** 7 - 7 * _share * (1 - _share) ** 6
assert 0.08 < P2 < 0.10  # about one chance in eleven
RD = {r["signum"]: r for r in json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["inscriptions"]}
assert "Siði(?) \"Þorr(?)" in RD["Sö 140"]["normalization"] and "May Þórr(?) safeguard(?)" in RD["Sö 140"]["translation_en"]
assert "Tors fiskafänge" in RD["U 1161"]["other"]
_SOL_TXT = {}
for _e in SOL:
    _SOL_TXT.setdefault(_e["name"], []).append(re.sub(r"\s+", " ", _e["text"]))
assert any("Namnet innehåller efterleden → vi ’helig plats, kultplats’" in t and "växtlighetsgudinna" in t for t in _SOL_TXT["Ludgo"])
assert any("oftast sammanhållits med → al" in t for t in _SOL_TXT["Altuna"])

# ---- the literature (sok.sqlite; pdf page → printed page from the page header) --------------------------------------
SOK = sqlite3.connect("/Volumes/2TB/Antigrvity/Runes/downloads/tidskrifter/sok.sqlite")


def jcheck(key, page, *frags):
    text = letters(SOK.execute("select text from pages where key=? and page=?", (key, page)).fetchone()[0])
    for f in frags:
        assert letters(f) in text, (key, page, f)


NB = "b9e575c4-81bc-4d2c-9972-e12c5f3721c5"
jcheck(NB, 5, "79", "All these deities have a supra-regional,", "almost pan-Scandinavian distribution",
       "cult at Uppsala appear", "to have been significant to all of Svithiod")
jcheck(NB, 7, "81", "People from many parts of Scandinavia regu", "larly visited Uppsala")
jcheck(NB, 2, "Religion was part of culture, and just like culture, it was shaped by the constant circular flow of tradition")
jcheck("111_2023", 13, "Namn och bygd 110 (2022), 13–60", "Eva Nyman")
jcheck("111_2023", 20, "20 Eva Nyman", "Liksom t.ex. Odensvi, Torsvi och Frösvi är Ull(e)vi, fsv. *Ullarvi, typiskt för centrala Sverige")
jcheck("111_2023", 19, "i Ångermanland det nordligaste ortnamn, som säkert innehåller gudanamnet")
_SOL_ALL = {}
for _e in SOL:
    _SOL_ALL.setdefault(_e["name"], []).append(re.sub(r"\s+", " ", _e["text"]))
assert any("dialektordet frö ’fruktbar, frodig’" in t for t in _SOL_ALL["Frösunda"])
assert any("mansnamnet Tore" in t for t in _SOL_ALL["Torsby"])
assert any("gudanamnet Oden och → harg" in t for t in _SOL_ALL["Odensala"])
assert any("gudanamnet Ull och → tuna" in t for t in _SOL_ALL["Ultuna"])
assert all(x["sen"] == "ja" for x in VAS if x["namn"] in ("Trollaborg", "Vätteryd"))
assert {k for k, v in B["tabell"]["Frö"].items()} == {"Västra Götaland", "Mälarlanden", "Östra Götaland", "Norska riket"}
assert 1 / C1["p_holm"] > 250

# ---- pictures ----------------------------------------------------------------------------------------------------------
from PIL import Image  # noqa: E402


def frozen(path):
    buf = io.BytesIO()
    Image.open(path).convert("RGB").save(buf, "PNG", optimize=True)
    return blog_figures.freeze(buf.getvalue())


KARTA = {l: frozen(os.path.join(A, f"karta_{l}.png")) for l in ("sv", "en")}
MAP = {"sv": (f"![Karta: kultplatsnamn, tingsnamn och gudanamn i Svenskt ortnamnslexikon]({KARTA['sv']})\n"
              "Bild: Vitki. Till vänster de ortnamn som *Svenskt ortnamnslexikon* tolkar som förkristna kultplatser, och "
              "tingsplatserna; till höger namnen med en gud. Varje namn sitter på sin sockens mittpunkt. De grå prickarna är "
              "alla Sveriges socknar, så att man ser var ett namn hade kunnat finnas. Fyra samiska heliga platser i Lappland är "
              "inte med."),
       "en": (f"![Map: cult-place names, thing names and god names in Svenskt ortnamnslexikon]({KARTA['en']})\n"
              "Image: Vitki. Left: the place names that *Svenskt ortnamnslexikon* interprets as pre-Christian cult places, and "
              "the thing (assembly) places; right: the names with a god. Each name sits on the centre of its parish. The grey "
              "dots are all of Sweden's parishes, so you can see where a name could have been. Four Sami sacred places in "
              "Lapland are not included.")}
ORDER = ["Mälarlanden", "Östra Götaland", "Gotland", "Västra Götaland", "Danska riket", "Norska riket", "Norr"]
EN = {"Mälarlanden": "The Mälar lands", "Östra Götaland": "Eastern Götaland", "Gotland": "Gotland",
      "Västra Götaland": "Western Götaland", "Danska riket": "The Danish realm (Skåne, Blekinge, Halland)",
      "Norska riket": "The Norwegian realm (Bohuslän, Jämtland, Härjedalen)", "Norr": "The north"}
SVL = {"Danska riket": "Det danska riket (Skåne, Blekinge, Halland)",
       "Norska riket": "Det norska riket (Bohuslän, Jämtland, Härjedalen)", "Norr": "Norr"}


def chart(sv):
    out = [":::chart " + ("Hur stor del av ortnamnen som är kultplatser, per landsdel" if sv else
                          "What share of the place names are cult places, by region")]
    for r in ORDER:
        v = S[r]
        pct = f"{SH[r]:.1f}".replace(".", ",") if sv else f"{SH[r]:.1f}"
        n = f"{v['n']:,}".replace(",", " ") if sv else f"{v['n']:,}"
        lab = SVL.get(r, r) if sv else EN[r]
        out.append(f"{'+' if r == 'Mälarlanden' else ''}{lab} | {pct} | {v['kult']} {'av' if sv else 'of'} {n}")
    out.append(("Källa: Svenskt ortnamnslexikon (2016): kultplatsnamn enligt lexikonets tolkning, graderade av två blinda "
                "läsare, av alla lexikonets uppslag i landsdelen. Procent. Bild: Vitki.") if sv else
               ("Source: Svenskt ortnamnslexikon (2016): cult-place names by the lexicon's interpretation, graded by two blind "
                "readers, out of all the lexicon's entries in the region. Per cent. Image: Vitki."))
    out.append(":::")
    return "\n".join(out)


def chart_graves(sv):
    f = lambda v: f"{v:.0f}"  # noqa: E731
    return "\n".join([
        ":::chart " + ("Socknar utan registrerade gravar" if sv else "Parishes without registered graves"),
        "# " + ("Utan gravfält" if sv else "Without a grave field"),
        f"+{'Socken med kultplatsnamn' if sv else 'Parish with a cult-place name'} | {f(NO_GRAVE[0])} | 78 {'socknar' if sv else 'parishes'}",
        f"{'Övriga socknar' if sv else 'Other parishes'} | {f(NO_GRAVE[1])} | {'1 766 socknar' if sv else '1,766 parishes'}",
        "# " + ("Utan gravhög" if sv else "Without a mound"),
        f"+{'Socken med kultplatsnamn' if sv else 'Parish with a cult-place name'} | {f(NO_MOUND[0])} |",
        f"{'Övriga socknar' if sv else 'Other parishes'} | {f(NO_MOUND[1])} |",
        ("Källa: Svenskt ortnamnslexikon (2016) och Riksantikvarieämbetets Kulturmiljöregister; varje gravfält och hög räknad "
         "till den socken vars mittpunkt ligger närmast, i nio landskap. Procent, utan justering; proven i texten håller "
         "landskapet och sockenstorleken lika. Bild: Vitki.") if sv else
        ("Source: Svenskt ortnamnslexikon (2016) and the Swedish National Heritage Board's register of ancient remains; each "
         "grave field and mound counted to the parish whose centre lies nearest, in nine provinces. Per cent, unadjusted; the "
         "tests in the text hold the province and the parish size equal. Image: Vitki."),
        ":::"])


p1 = lambda x, sv=True: f"{x:.1f}".replace(".", ",") if sv else f"{x:.1f}"  # noqa: E731

SLUG = "asatron-i-landskapet"
title = "Asatron i landskapet – gudarnas platser låg bland förfädernas gravar"
title_en = "The old faith in the landscape – the places of the gods lay among the graves of the ancestors"
seo_title = "Asatron i ortnamnen: heliga platser och gravfält"
seo_title_en = "Old Norse religion in place names and graves"
summary = ("Runstenarna är nästan alla kristna, men asatron finns kvar i landskapet: i Odensvi, Torsåker, Ullvi och hundra "
           "andra namn. Vi har gått igenom hela Svenskt ortnamnslexikon och lagt namnen bredvid Riksantikvarieämbetets register "
           "över fornlämningar. De heliga platserna låg tätast kring Mälaren, och de låg där gravarna låg: nästan ingen "
           "socken med ett kultplatsnamn saknar gravfält. Runstenarna följde däremot inte efter.")
summary_en = ("The runestones are almost all Christian, but the old faith survives in the landscape: in Odensvi, Torsåker, "
              "Ullvi and a hundred other names. We went through the whole Swedish place-name dictionary and laid the names "
              "beside the national register of ancient remains. The sacred places lay thickest around Lake Mälaren, and they "
              "lay where the graves lay: hardly any parish with a cult-place name lacks a grave field. The runestones, on "
              "the other hand, did not follow.")

body = f"""Den som tar tåget från Stockholm till Uppsala passerar Odensala och Ultuna utan att tänka på det. Namnen är så vanliga att de har slutat betyda något. Men en gång betydde de något mycket bestämt: Odensala var Odens harg, en kultplats, och Ultuna var Ulls tuna.

Vi vet att det fanns en asatro. Det berättar de isländska dikterna, Adam av Bremen och de få runstenar som åkallar Tor. Men runstenarna är sena, och nästan alla är kristna. Den som vill se den gamla tron i Sverige får läsa något annat: landskapet själv, så som det har bevarats i ortnamnen.

## Namnen som minns

Många svenska ortnamn innehåller ord som bara går att förstå om man vet vad människorna trodde på. Det vanligaste är *vi*, som i Odensvi, Torsvi och Ullvi. *Svenskt ortnamnslexikon* förklarar ordet kort: vi ’helig plats, kultplats’ (SOL, art. Odensvi). Andra ord för en kultplats är *harg*, *hov* och *al*, och ibland en lund, en åker eller en ö som har helgats åt en gud.

Vi har gått igenom alla 6 045 uppslag i lexikonet. Ett namn räknas bara om lexikonets egen tolkning säger att det rör en förkristen kultplats eller en gud – det är namnforskarnas läsning, inte vår. Frösunda räknas inte, för lexikonet förklarar det med dialektordet *frö*, bördig. Inte heller Torsby, som har fått sitt namn efter en man som hette Tore. Två läsare gick igenom namnen var för sig, utan att se varandras svar. Kvar blev 128 kultplatser, varav 50 med en säker tolkning, och 52 tingsplatser.

{MAP['sv']}

## Samma gudar överallt

Det första kartan visar är att gudarna fanns i hela landet. Tor finns i alla sju landsdelar vi delade in landet i: från Torsburgen på Gotland till Torsåker i Ångermanland, enligt namnforskaren Eva Nyman det nordligaste svenska ortnamn ”som säkert innehåller gudanamnet” (Namn och bygd 110, s. 19). Oden finns i Götaland, kring Mälaren och i de skånska och halländska bygder som då hörde till det danska riket. Frö finns i Mälarlanden, i Västergötland och Småland, och på Frösön i Storsjön.

Vi prövade om gudarna hörde hemma i olika delar av landet: om Tor hörde till en bygd och Oden till en annan. Det gick inte att se. Med bara 32 namn för de tre stora gudarna kan bara mycket stora skillnader upptäckas, så det betyder inte att tron var likadan överallt. Men det stämmer med vad religionshistorikern Andreas Nordberg skriver, med stöd av Stefan Brink: de gudar som syns i de skandinaviska ortnamnen har en spridning som är ”supra-regional, almost pan-Scandinavian” – över landsgränserna, nästan över hela Skandinavien (Fornvännen 113, s. 79).

## Men de heliga platserna låg tätast kring Mälaren

Gudarna var gemensamma. Platserna där de dyrkades var det inte i samma mått.

{chart(True)}

Av lexikonets namn i Mälarlanden – Uppland, Södermanland, Västmanland och Närke – är {p1(SH['Mälarlanden'])} procent kultplatser. I norr är det {p1(SH['Norr'])} procent, en tredjedel så mycket. Östra Götaland och Gotland ligger däremellan. Talen är räknade mot hur många namn lexikonet har i varje landsdel, så det är inte bara så att Mälardalen har fler namn. Ett så tydligt mönster skulle uppstå av en slump i färre än ett fall på 250.

Och där kultplatserna låg tätast låg också tingen. Av de 52 tingsplatserna i lexikonet ligger 25 i Mälarlanden, bland dem Anundshögen i Västmanland. Kultplatserna och tingen låg tätast i samma landsdel.

Vi prövade också om olika slags kultplatser hörde till olika landsdelar – vi i en, harg i en annan. Det gick inte att se. Vi-namnen finns från Gotland till Västergötland.

## Bland förfädernas gravar

Var i bygden låg då de heliga platserna? För att se det lade vi namnen bredvid något helt annat: Riksantikvarieämbetets register över fornlämningar, där gravfält, högar, fornborgar, hamnar, vägar och broar är inmätta, och kartor över jordarterna och de medeltida kyrkorna. Tretton drag i allt. Vi lät dem tävla på ett sätt som skyddar mot att vi lurar oss själva: vi delade landets socknar i två halvor och letade fritt i den ena. Det som stack ut där låstes, och fick sedan visa sig i den andra halvan, där vi inte hade tittat.

Två drag klarade det, och de klarade det åt båda hållen: gravfälten och gravhögarna.

{chart_graves(True)}

Bara {NO_GRAVE[0]:.0f} procent av socknarna med ett kultplatsnamn saknar registrerade gravfält, mot {NO_GRAVE[1]:.0f} procent av de andra. Räknat mot landskapets genomsnitt har de en tredjedel fler gravfält och {p1(R_MOUND)} gånger så många gravhögar. Det håller när socknens storlek hålls lika – stora socknar har förstås fler gravar – och när bara de namn som lexikonet tolkar säkert räknas.

De heliga platserna låg alltså där de döda låg, i de bygder där människor hade bott och begravt sina föräldrar i generationer. Det säger inte att kulten utövades vid gravarna. Men det säger att gudarnas platser hörde till de gamla, tätt bebodda bygderna, inte till utmarkerna eller de nya gårdarna.

Lika viktigt är det som inte höll. Socknar med ett kultplatsnamn har inte påvisbart oftare en hamn, en väg eller ett Husby, och de ligger inte på någon särskild jord. Fornborgarna, tingen och de tidiga kyrkorna syntes bara i den ena halvan, och det räcker inte.

## Runstenarna följde inte efter

Om de gamla gudarna hade sina platser i de gamla bygderna, borde väl den nya trons första monument ha sökt sig dit? Vi prövade det också, med en plan som låstes innan vi räknade. Svaret är nej, så långt vi kan se. I socknar med ett kultplatsnamn restes inte fler runstenar än i grannsocknarna, de är inte senare, och de har inte säkert oftare en kristen text.

Två stenar är ändå värda att stanna vid. Av de sju svenska runstenar som har hedniska drag står två i en socken med ett kultplatsnamn. Vid Korpbron i Ludgo i Södermanland står en sten som slutar med orden *Siði Þorr*, som Rundata läser som ”Tor vige” – med frågetecken. Ludgo innehåller enligt lexikonet *vi*, helig plats, och kanske namnet på en växtlighetsgudinna. Och i Altuna kyrka i Uppland står stenen där Tor fiskar efter Midgårdsormen, i en socken vars namn oftast förs till *al*, helgedom. Med så få stenar kan det lätt vara en slump, ungefär en chans på elva. Men den som vill se de gamla gudarna i landskapet kan börja där.

## Det namnforskarna redan visste

Det här är inte en upptäckt i den meningen att ingen har sett det förut. Per Vikstrand skrev 2001 en hel avhandling om *Gudarnas platser* i Mälarlandskapen, och Eva Nyman konstaterar att namn som Odensvi, Torsvi, Frösvi och Ullvi är ”typiskt för centrala Sverige” (Namn och bygd 110, s. 20). Att kultplatserna låg i de gamla centralbygderna har de också skrivit. Det nya här är måttet och kombinationen: hela landet räknat med samma lexikon och två läsare, och lagt mot ett helt annat register – de inmätta gravarna – och mot runstenarna. Det namnforskarna har sett i trakt efter trakt syns då som mönster i siffror, och runstenarnas tystnad om de gamla platserna har ingen visat förut.

## Hur hölls tron ihop?

Avstånden var stora och vägarna få. Hur kunde samma gudar dyrkas från Skåne till Ångermanland? Ortnamnen svarar inte på det. Men de pekar ut var svaret kan ligga: där kulten, tinget och marknaden möttes.

Nordberg skriver att tinget, marknaden och kulten i Uppsala ”appear to have been significant to all of Svithiod” – de tycks ha betytt något för hela Svitjod (s. 79). Och han tillägger att ”people from many parts of Scandinavia regularly visited Uppsala”, för att delta i disatinget och för att handla (s. 81). Hans bild av den gamla religionen är inte en kyrka med en lära, utan ett nät av människor som möttes, bytte varor och berättelser och tog dem med sig hem: ”Religion was part of culture, and just like culture, it was shaped by the constant circular flow of tradition” (s. 76).

Här tillåter vi oss en läsning som inte är ortnamnens egen. Kring Mälaren var vattnet väg åt alla håll, och dit kom människor ofta: till tinget, till marknaden, till offret. En tro som hölls ihop av möten, inte av en skrift, borde lämna flest spår just där. Det stämmer med kartan, men kartan kan inte visa att det var så.

## Trollen kom senare

Vi letade också efter namn med troll, jättar, alver och vättar. Lexikonet har tio, och sju av dem är enligt tolkningen medeltida eller yngre, som Trollaborg och Vätteryd. De hör till folktron, som levde kvar långt efter att gudarna hade glömts. Två av dem, i Lappland, innehåller *stalo*, en jätte i samisk folktro. Väsendena berättar mer om de senare århundradena än om asatron.

:::box Det viktigaste i korthet
- Asatron syns i landskapet: 128 ortnamn tolkas av namnforskarna som förkristna kultplatser, och ytterligare några bär en guds namn.
- Gudarna var gemensamma. Tor finns i alla delar av landet, från Gotland till Ångermanland, och vi kunde inte se att olika gudar hörde till olika bygder.
- De heliga platserna låg tätast kring Mälaren, tre gånger tätare än i norr, och där låg också tingen. Tron hade ett centrum.
- De heliga platserna låg där gravarna låg: bara 5 procent av socknarna med ett kultplatsnamn saknar gravfält, mot 28 procent av de andra. Gudarnas platser hörde till de gamla bygderna.
- Runstenarna följde inte efter. Kristendomens första monument restes inte oftare eller senare vid de gamla platserna.
:::

## Så säkra är vi

Lexikonet täcker främst socknar, härader, städer och sjöar, inte enskilda gårdar, och det har fler uppslag i vissa landsdelar än i andra; därför jämförde vi alltid med hur många namn lexikonet har i landsdelen. Ett namns äldsta skriftliga belägg är oftast från 1300-talet och säger inget om när platsen var helig. De två läsarna var oense om 12 av 402 uppslag; där räknades namnet inte. Fyra samiska heliga platser i Lappland räknades i provet som kultplatser; utan dem är andelen i norr ännu lägre, {p1(NORR_UTAN)} procent. Socknarnas gränser fanns inte att tillgå, så varje gravfält och hög räknades till den socken vars mittpunkt ligger närmast. Runstensprovet saknar 270 av 2 321 stenar vars socken inte gick att matcha. Planerna låstes innan något räknades, fyra stycken i följd, och de ligger öppet på GitHub tillsammans med koden.

## Källor

- *Svenskt ortnamnslexikon*, 2:a uppl. 2016, Institutet för språk och folkminnen. Läst och räknat; citeras kort.
- Institutet för språk och folkminnen, Ortnamnsregistret: socknarna och deras mittpunkter. CC BY.
- Riksantikvarieämbetet, Kulturmiljöregistret: gravfält, högar och andra fornlämningar.
- Samnordisk runtextdatabas (Rundata), Uppsala universitet. Open Database License.
- Nordberg, Andreas 2018. Circular flow of tradition in Old Norse religion. *Fornvännen* 113, s. 76 ff. CC BY 4.0.
- Nyman, Eva 2022. Sakrala ortnamn av förkristen nordisk typ i de nordliga delarna av Norge och Sverige. *Namn och bygd* 110, s. 13–60. CC BY 4.0.
- Vikstrand, Per 2001. *Gudarnas platser. Förkristna sakrala ortnamn i Mälarlandskapen*. Uppsala.
- Analysplanerna och koden: [GitHub](https://github.com/Precatio/runes/blob/main/analysplaner/2026-11-17-gudarna-pa-kartan.md)."""

body_en = f"""Anyone taking the train from Stockholm to Uppsala passes Odensala and Ultuna without a thought. The names are so common that they have stopped meaning anything. But once they meant something quite specific: Odensala was Odin's harg, a cult place, and Ultuna was Ull's tuna.

We know there was an Old Norse faith. The Icelandic poems tell us, Adam of Bremen tells us, and so do the few runestones that call on Thor. But the runestones are late, and almost all of them are Christian. Whoever wants to see the old faith in Sweden has to read something else: the landscape itself, as it has been preserved in the place names.

## The names that remember

Many Swedish place names contain words that can only be understood if you know what people believed. The most common is *vi*, as in Odensvi, Torsvi and Ullvi. *Svenskt ortnamnslexikon*, the Swedish place-name dictionary, explains the word briefly: vi ’helig plats, kultplats’, a holy place, a cult place (SOL, entry Odensvi). Other words for a cult place are *harg*, *hov* and *al*, and sometimes a grove, a field or an island hallowed to a god.

We went through all 6,045 entries in the dictionary. A name counts only if the dictionary's own interpretation says it concerns a pre-Christian cult place or a god – it is the place-name scholars' reading, not ours. Frösunda does not count, because the dictionary explains it with the dialect word *frö*, fertile. Nor does Torsby, named after a man called Tore. Two readers went through the names separately, without seeing each other's answers. What remained were 128 cult places, 50 of them with a secure interpretation, and 52 thing (assembly) places.

{MAP['en']}

## The same gods everywhere

The first thing the map shows is that the gods were found across the whole country. Thor is in all seven regions we divided the country into: from Torsburgen on Gotland to Torsåker in Ångermanland, according to the place-name scholar Eva Nyman the northernmost Swedish place name that certainly contains the god's name (Namn och bygd 110, p. 19). Odin is in Götaland, around Lake Mälaren and in the districts of Skåne and Halland that then belonged to the Danish realm. Frey is in the Mälar lands, in Västergötland and Småland, and on Frösön in Lake Storsjön.

We tested whether the gods belonged to different parts of the country: whether Thor belonged to one district and Odin to another. It could not be seen. With only 32 names for the three great gods, only very large differences can be detected, so this does not mean that the faith was the same everywhere. But it agrees with what the historian of religion Andreas Nordberg writes, citing Stefan Brink: the gods seen in Scandinavian place names have a distribution that is ”supra-regional, almost pan-Scandinavian” (Fornvännen 113, p. 79).

## But the sacred places lay thickest around Lake Mälaren

The gods were shared. The places where they were worshipped were not shared to the same degree.

{chart(False)}

Of the dictionary's names in the Mälar lands – Uppland, Södermanland, Västmanland and Närke – {p1(SH['Mälarlanden'], False)} per cent are cult places. In the north it is {p1(SH['Norr'], False)} per cent, a third as much. Eastern Götaland and Gotland lie in between. The figures are counted against how many names the dictionary has in each region, so it is not simply that the Mälar valley has more names. A pattern this clear would arise by chance in fewer than one case in 250.

And where the cult places lay thickest, the assemblies lay too. Of the 52 thing places in the dictionary, 25 are in the Mälar lands, among them Anundshögen in Västmanland. The cult places and the assemblies lay thickest in the same region.

We also tested whether different kinds of cult place belonged to different regions – vi in one, harg in another. It could not be seen. The vi names run from Gotland to Västergötland.

## Among the graves of the ancestors

Where in the district, then, did the sacred places lie? To see that, we laid the names beside something quite different: the national register of ancient remains, where grave fields, mounds, hillforts, harbours, roads and bridges are surveyed, and maps of the soils and the medieval churches. Thirteen traits in all. We let them compete in a way that guards against fooling ourselves: we split the country's parishes into two halves and searched freely in one. What stood out there was locked, and then had to show itself in the other half, where we had not looked.

Two traits passed, and they passed both ways: the grave fields and the burial mounds.

{chart_graves(False)}

Only {NO_GRAVE[0]:.0f} per cent of the parishes with a cult-place name lack a registered grave field, against {NO_GRAVE[1]:.0f} per cent of the others. Counted against the province's average they have a third more grave fields and {p1(R_MOUND, False)} times as many mounds. It holds when the size of the parish is held equal – large parishes of course have more graves – and when only the names the dictionary interprets with certainty are counted.

So the sacred places lay where the dead lay, in the districts where people had lived and buried their parents for generations. That does not say the cult was practised at the graves. But it says that the places of the gods belonged to the old, densely settled districts, not to the outlands or the new farms.

What did not hold matters just as much. Parishes with a cult-place name do not demonstrably more often have a harbour, a road or a Husby, and they do not lie on any particular soil. The hillforts, the assemblies and the early churches showed only in one half, and that is not enough.

## The runestones did not follow

If the old gods had their places in the old districts, surely the first monuments of the new faith would have sought them out? We tested that too, with a plan locked before we counted. The answer is no, as far as we can see. In parishes with a cult-place name no more runestones were raised than in the neighbouring parishes, they are not later, and they do not with any certainty more often have a Christian text.

Two stones are still worth pausing at. Of the seven Swedish runestones with pagan features, two stand in a parish with a cult-place name. At Korpbron in Ludgo in Södermanland stands a stone that ends with the words *Siði Þorr*, which Rundata reads as ”may Thor hallow” – with a question mark. Ludgo contains, according to the dictionary, *vi*, a holy place, and perhaps the name of a goddess of growth. And in Altuna church in Uppland stands the stone where Thor fishes for the Midgard serpent, in a parish whose name is most often linked to *al*, sanctuary. With so few stones it could easily be chance, about one chance in eleven. But whoever wants to see the old gods in the landscape can start there.

## What the place-name scholars already knew

This is not a discovery in the sense that no one has seen it before. In 2001 Per Vikstrand wrote a whole dissertation on *Gudarnas platser*, the places of the gods, in the Mälar provinces, and Eva Nyman notes that names such as Odensvi, Torsvi, Frösvi and Ullvi are ”typiskt för centrala Sverige”, typical of central Sweden (Namn och bygd 110, p. 20). They have also written that the cult places lay in the old central districts. What is new here is the measure and the combination: the whole country counted with the same dictionary and two readers, and laid against an entirely different register – the surveyed graves – and against the runestones. What the scholars have seen district by district then shows as patterns in numbers, and no one has shown before that the runestones were silent about the old places.

## How was the faith held together?

The distances were great and the roads few. How could the same gods be worshipped from Skåne to Ångermanland? The place names do not answer that. But they point to where the answer may lie: where cult, assembly and market met.

Nordberg writes that the assembly, the market and the cult at Uppsala ”appear to have been significant to all of Svithiod” (p. 79). And he adds that ”people from many parts of Scandinavia regularly visited Uppsala”, to take part in the Disting assembly and to trade (p. 81). His picture of the old religion is not a church with a doctrine, but a web of people who met, exchanged goods and stories and took them home: ”Religion was part of culture, and just like culture, it was shaped by the constant circular flow of tradition” (p. 76).

Here we allow ourselves a reading that is not the place names' own. Around Lake Mälaren the water was a road in every direction, and people came there often: to the assembly, to the market, to the sacrifice. A faith held together by meetings, not by a scripture, ought to leave the most traces just there. That agrees with the map, but the map cannot show that it was so.

## The trolls came later

We also looked for names with trolls, giants, elves and wights. The dictionary has ten, and seven of them are by its interpretation medieval or younger, such as Trollaborg and Vätteryd. They belong to folk belief, which lived on long after the gods had been forgotten. Two of them, in Lapland, contain *stalo*, a giant in Sami folk belief. The beings tell us more about the later centuries than about the old faith.

:::box The essentials in brief
- The old faith can be seen in the landscape: 128 place names are interpreted by the place-name scholars as pre-Christian cult places, and a few more carry a god's name.
- The gods were shared. Thor is in every part of the country, from Gotland to Ångermanland, and we could not see different gods belonging to different districts.
- The sacred places lay thickest around Lake Mälaren, three times as thick as in the north, and that is where the assemblies lay too. The faith had a centre.
- The sacred places lay where the graves lay: only 5 per cent of the parishes with a cult-place name lack a grave field, against 28 per cent of the others. The places of the gods belonged to the old districts.
- The runestones did not follow. The first monuments of Christianity were not raised more often or later at the old places.
:::

## How sure we are

The dictionary covers mainly parishes, hundreds, towns and lakes, not single farms, and it has more entries in some regions than in others; so we always compared with how many names the dictionary has in the region. A name's oldest written record is usually from the fourteenth century and says nothing about when the place was holy. The two readers disagreed on 12 of 402 entries; there the name was not counted. Four Sami sacred places in Lapland were counted as cult places in the test; without them the share in the north is even lower, {p1(NORR_UTAN, False)} per cent. Parish boundaries were not available, so each grave field and mound was counted to the parish whose centre lies nearest. The runestone test lacks 270 of 2,321 stones whose parish could not be matched. The plans were locked before anything was counted, four of them in turn, and they are open on GitHub with the code.

## Sources

- *Svenskt ortnamnslexikon*, 2nd ed. 2016, Institute for Language and Folklore. Read and counted; quoted briefly.
- Institute for Language and Folklore, Place-name register: the parishes and their centres. CC BY.
- Swedish National Heritage Board, Kulturmiljöregistret: grave fields, mounds and other ancient remains.
- Scandinavian Runic-text Database (Rundata), Uppsala University. Open Database License.
- Nordberg, Andreas 2018. Circular flow of tradition in Old Norse religion. *Fornvännen* 113, pp. 76 ff. CC BY 4.0.
- Nyman, Eva 2022. Sakrala ortnamn av förkristen nordisk typ i de nordliga delarna av Norge och Sverige. *Namn och bygd* 110, pp. 13–60. CC BY 4.0.
- Vikstrand, Per 2001. *Gudarnas platser. Förkristna sakrala ortnamn i Mälarlandskapen*. Uppsala.
- The analysis plans and the code: [GitHub](https://github.com/Precatio/runes/blob/main/analysplaner/2026-11-17-gudarna-pa-kartan.md)."""

# ---- checks ----------------------------------------------------------------------------------------------------------
for b, lang in ((body, "sv"), (body_en, "en")):
    assert not re.search(r"^\|", b, re.M), "BlogBody har inga tabeller"
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M)), "varje ruta ska stängas"
    assert "{" not in b and "}" not in b
    assert ("Det viktigaste i korthet" if lang == "sv" else "The essentials in brief") in b
    assert b.index(":::box") < b.index("## Källor" if lang == "sv" else "## Sources")
    imgs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", b)
    assert len(imgs) == 1 and all(re.match(r"/api/blog/figures/[0-9a-f]{16}\.png$", u) for u in imgs), imgs
    assert not re.search(r"\bAI\b", b)
labels = ["Forskning", "Tro och magi", "Geografi"]
err = blog_labels.check(labels)
assert err is None, err
assert len(seo_title) <= 52 and len(seo_title_en) <= 52
out = {"slug": SLUG, "title": title, "summary": summary, "body": body, "title_en": title_en, "summary_en": summary_en,
       "body_en": body_en, "seo_title": seo_title, "seo_title_en": seo_title_en, "labels": labels}
path = os.path.join(ROOT, "utdata", "blogg", "asatro.json")
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
                 "topic": "Forskning|asatro", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
