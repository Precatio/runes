"""Fokusartikeln om de danska runstenarnas budskap (sv + en). Varje tal läses ur utdata/danmark/resultat.json (låst plan
analysplaner/2026-11-17-danska-runstenar.md, sha dd9f1ad3, och tillägg 1 om budskapet, sha 8f32a977), varje runtext ur
Rundata och varje citat ur litteraturen kontrolleras mot källans text (utdata/norge/citat.py; tidskrifterna i
sok.sqlite; litteraturkontrollen i /Volumes/2TB/Antigrvity/Runes/downloads/danmark_lit/litteratur.md).
    ../../../.venv/bin/python build_danmark.py [--write | --update DOC]"""
import datetime as dt
import json
import os
import re
import sqlite3
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import blog_labels, commons  # noqa: E402
from utdata.norge.citat import check, letters  # noqa: E402

R = json.load(open(os.path.join(ROOT, "utdata", "danmark", "resultat.json"), encoding="utf-8"))
assert R["plan"]["analysplaner/2026-11-17-danska-runstenar.md"] == "dd9f1ad3"
RD = {r["signum"]: r for r in json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["inscriptions"]}
TR = json.load(open(os.path.join(ROOT, "utdata", "danmark", "traffar.json"), encoding="utf-8"))

# ---- the numbers ------------------------------------------------------------------------------------------------------
assert R["n"] == {"DK": 239, "SE": 2321}
A, M, B, C = R["A"], R["M"], R["B"], R["C"]
k = lambda d, L: (d[L]["a"], d[L]["n"])  # noqa: E731
pc = lambda d, L, nd=0: round(100 * d[L]["a"] / d[L]["n"], nd) if nd else round(100 * d[L]["a"] / d[L]["n"])  # noqa: E731
M1, M2, M3 = M["M1_foljet"], M["M2_striden"], M["M3_ambetet"]
B1, B2, B3 = B["B1_kyrkan"], B["B2_monumentet"], B["B3_kvinna_reser"]
assert k(M1, "DK") == (17, 134) and k(M1, "SE") == (5, 1360) and M1["haller"] and M1["robust_riktning"]
assert pc(M1, "DK") == 13 and pc(M1, "SE", 1) == 0.4 and M1["holm_p"] < 1e-12  # "färre än ett fall på tusen miljarder"
assert M1["mh"]["per_skikt"] == {"tidig": {"DK": "3/30", "SE": "0/175"}, "mitt": {"DK": "14/72", "SE": "2/277"},
                                 "sen": {"DK": "0/27", "SE": "1/355"}}
assert sorted(x["signum"] for x in TR["M1_foljet"]) == sorted(["DR 1", "DR 3", "DR 62", "DR 66", "DR 68", "DR 81", "DR 125", "DR 127",
                                                               "DR 131", "DR 209", "DR 262", "DR 270", "DR 279", "DR 316", "DR 321",
                                                               "DR 329", "DR 339"])
assert k(M3, "DK") == (14, 239) and k(M3, "SE") == (28, 2321) and M3["haller"] and M3["robust_riktning"]
assert pc(M3, "DK") == 6 and pc(M3, "SE") == 1 and 1 / 1000 < M3["mh"]["p"] < 1 / 700  # "ungefär ett fall på tusen"
assert k(M2, "DK") == (3, 239) and k(M2, "SE") == (31, 2321) and not M2["haller"]
assert k(B2, "DK") == (40, 239) and k(B2, "SE") == (127, 2321) and B2["haller"] and B2["robust_riktning"]
assert pc(B2, "DK") == 17 and pc(B2, "SE") == 5 and 1 / 6000 < B2["mh"]["p"] < 1 / 5000  # "ungefär två fall på tiotusen"
assert k(B3, "DK") == (30, 170) and k(B3, "SE") == (391, 1415) and B3["haller"] and B3["robust_riktning"]
assert pc(B3, "DK") == 18 and pc(B3, "SE") == 28 and 1 / 130 < B3["mh"]["p"] < 1 / 120  # "ungefär åtta fall på tusen"
assert k(B1, "DK") == (71, 239) and k(B1, "SE") == (934, 2321) and not B1["haller"]
PL = C["plats_idag"]
assert (PL["DK"]["museum"]["a"], PL["SE"]["museum"]["a"]) == (48, 127)
for key, dk, se in (("A_hednisk", 8, 7), ("A_kristen", 26, 353), ("A_bon", 22, 297), ("A_titel", 36, 104), ("A_kumbl", 27, 71),
                    ("A_placed", 43, 74), ("A_had", 24, 667), ("A_bro", 4, 119), ("A_fard", 4, 130)):
    assert (A[key]["DK"]["a"], A[key]["SE"]["a"]) == (dk, se), key
    assert A[key]["DK"]["n"] == 239 and A[key]["SE"]["n"] == 2321, key
assert 0.003 < A["A_hednisk"]["mh"]["p"] < 0.005 and round(A["A_hednisk"]["mh"]["or_mh"]) == 5
assert sorted(x["signum"] for x in TR["A_hednisk"]) == ["DR 110", "DR 120", "DR 209", "DR 220", "DR 230", "DR 338", "DR 81", "DR 83"]
BH = C["delomraden"]["dk_bornholm"]
assert (BH["M1_foljet"]["a"], BH["M3_ambetet"]["a"], BH["A_hednisk"]["a"]) == (0, 0, 0)
assert C["dk_per_skikt"] == {"mitt": 111, "tidig": 65, "utan år": 19, "sen": 44}
assert [(x["signum"], x["land"]) for x in TR["C_kung"] if x["land"] == "DK"] == [("DR 3", "DK"), ("DR 4", "DK"), ("DR 41", "DK"), ("DR 42", "DK")]

# ---- the runic texts, as Rundata has them ----------------------------------------------------------------------------
NORM = lambda s: RD[s]["normalization"]  # noqa: E731
TEXTS = {
    "DR 127": "ÞoriR resþi sten þæssi æftiR \"Karl hin \"Goþa, felaga sin, harþa goþan dræng.",
    "Vg 112": "ÞoriR ræisti stæin þannsi æftiR \"Karl, sinn felaga, harða goðan dræng.",
    "DR 279": "SaR flo ægi at \"Upsalum, æn wa mæþ han wapn hafþi.",
    "DR 66": "þa kunungaR barþusk",
    "DR 1": "þa drængiaR satu um \"Heþaby",
    "DR 3": "\"Swen kunungR satti sten æftiR \"Skarþa, sin hemþæga",
    "DR 40": "\"Tofi \"Bryti resþi sten þænsi æft lika brytia",
    "DR 190": "nøRa goþi",
    "DR 209": "\"Þor wigi þæssi runaR.",
    "DR 230": "satti sten þænsi ok gærþi høg þænsi æft, ok skeþ þæssi",
    "DR 42": "\"Haraldr kunungR baþ gørwa kumbl þøsi æft \"Gorm, faþur sin",
    "DR 133": "han was landmanna bæztr i \"Danmarku ok fyrstr",
}
for s, frag in TEXTS.items():
    assert frag in NORM(s), (s, frag)
assert RD["DR 127"]["place"] == "Hobro 2" and RD["Vg 112"]["place"] == "Ås kyrka" and RD["DR 279"]["place"].startswith("Sjörup")
assert "hallow" in RD["DR 220"]["translation_en"] and "Gotland" in RD["DR 220"]["translation_en"]

# ---- the literature, against the sources -----------------------------------------------------------------------------
SAW, PALM = "text/sawyer_1989_tesseract.txt", "text/palm_1992_runor_och_regionalitet.txt"  # Sawyer: printed = pdf + 184; Palm: pdf − 5
THA = "../danmark_lit/src/thamdrup_1981_kuml.txt"  # pdf 9 = s. 11
Q = {
    "saw192a": "är vanliga på danskt område men sällsynta på andra håll",
    "saw192b": ("domineras av individuellt resta stenar, låg kvinnorepresentation och ett relativt stort inslag av andra än "
                "de närmaste familjemedlemmarna bland stenresarna"),
    "saw193a": "företer i huvudsak likartade mönster med mer",
    "saw193b": "det endast är i Danmark som kungliga personer reser sten",
    "saw192c": "Mönstret kännetecknas vidare av olika slags",
    "saw185": "sådant förekommer i Danmark men är sällsynt på svenskt område, där i stället kristna kors och böner är vanliga",
    "saw188": "hedniska protester mot den nya religionen",
    "palm257": "Ett religiöst innehåll saknas nästan helt i det danska materialet",
    "tha11": "occurs frequently in Danish and Swedish runic inscriptions",
}
for key, path, pdf in (("saw192a", SAW, 8), ("saw192b", SAW, 8), ("saw192c", SAW, 8), ("saw193a", SAW, 9), ("saw193b", SAW, 9),
                       ("saw185", SAW, 1), ("saw188", SAW, 4), ("palm257", PALM, 262), ("tha11", THA, 9)):
    check(path, Q[key], pdf, fuzzy=0.85)
SOK = sqlite3.connect("/Volumes/2TB/Antigrvity/Runes/downloads/tidskrifter/sok.sqlite")


def jcheck(key, page, *frags):
    text = letters(SOK.execute("select text from pages where key=? and page=?", (key, page)).fetchone()[0])
    for f in frags:
        assert letters(f) in text, (key, page, f)


Q["gra183a"] = "Att kvinnor reste runstenar efter män var inte så ovanligt i Danmark"
Q["gra183b"] = "båda i kontakt med imponerande skeppssättningar"
Q["gra184"] = "på nästan hälften av inskrifterna"
Q["jes89"] = "with concentrations in Denmark, Västergötland and Södermanland"
Q["wil71"] = "betecknar en ämbetsinnehavare med betydande ställning"
jcheck("futhark_7_181_1087624", 7, Q["gra183a"], Q["gra183b"])  # Gräslund 2016, s. 183
jcheck("futhark_7_181_1087624", 8, Q["gra184"])                  # s. 184
jcheck("futhark_4_77_682692", 15, Q["jes89"])                    # Jesch 2013, s. 89
jcheck("futhark_4_61_682691", 13, Q["wil71"])                    # Williams 2013, s. 71
jcheck("1984_093", 11, "De två stenarna i Ås och Hobro anses vara", "resta över samma person (Moltke 1976 s.",
       "identiska runstenarna Vgl 112 och", "DR 127 belägna i Ås socken Västergötland")  # Löfving 1984, s. 102

# ---- pictures --------------------------------------------------------------------------------------------------------
INFO = json.load(open(os.path.join(ROOT, "utdata", "blogg", "build", "danmark_imgs.json"), encoding="utf-8"))
IMG = {}
for label, f in (("DR 209", "Denmark-Glavendrup rune stone-front.jpg"), ("DR 3", "Skarthi stone front.jpg"),
                 ("DR 279", "DR279 1 Sjörup.jpg"), ("DR 230", "The Tryggevælde Runic Stone.jpg")):
    d = INFO[f]
    assert re.match(r"(CC BY|CC0|Public domain)", d["licence"]), f
    IMG[label] = {**d, "signum": label}
assert IMG["DR 3"]["author"].startswith("viciarg")
IMG["DR 3"]["author"] = "viciarg"
assert IMG["DR 230"]["author"] == "Kim Bach"
IMG["DR 230"]["author"] = "Kim Bach/Nationalmuseet"  # given by Nationalmuseet (Wikipedia Loves Nationalmuseet 2011)
PIC = lambda s, lang: commons.markdown(IMG[s], lang)  # noqa: E731

f_sv = lambda n: f"{n:,}".replace(",", " ")  # noqa: E731
p1 = lambda d, L: f"{100 * d[L]['a'] / d[L]['n']:.1f}"  # noqa: E731
CHART_SV, CHART_EN = "Diagram: Vitki, efter Rundata (ODbL).", "Chart: Vitki, after Rundata (ODbL)."
ROWS = [("Kamraten eller herren (bland stenar som anger relationen)", "The partner or the lord (among stones that state the relation)", M1),
        ("Ett ämbete: bryte, gode, kungens man, styrman", "An office: steward, priest-chieftain, king's man, captain", M3),
        ("Titeln þegn eller drængr", "The title þegn or drengr", A["A_titel"]),
        ("Minnesmärket är mer än stenen", "The monument is more than the stone", B2),
        ("Hedniska markörer (Tor, förbannelser)", "Pagan markers (Thor, curses)", A["A_hednisk"]),
        ("Kristen text", "Christian text", A["A_kristen"]),
        ("En kvinna reser stenen (bland stenar med känd resare)", "A woman raises the stone (among stones with a known raiser)", B3)]


def chart(lang):
    sv = lang == "sv"
    out = [":::chart " + ("Vad stenarna säger – danska och svenska runstenar" if sv else "What the stones say – Danish and Swedish runestones")]
    for a, b, d in ROWS:
        out.append("# " + (a if sv else b))
        for L, ls, le in (("DK", "Danmark", "Denmark"), ("SE", "Sverige", "Sweden")):
            n = f_sv(d[L]["n"]) if sv else f"{d[L]['n']:,}"
            out.append(f"{'+' if L == 'DK' else ''}{ls if sv else le} | {p1(d, L)} | {d[L]['a']} {'av' if sv else 'of'} {n}")
    out.append(("Källa: Samnordisk runtextdatabas (Rundata), vikingatida runstenar: 239 danska (med Skåne, Halland, Blekinge och "
                "Bornholm) och 2 321 svenska; dragen efter Rundatas översättningar. Andelar utan tidsjustering; jämförelserna i "
                f"texten håller tiden lika. Procent. {CHART_SV}") if sv else
               ("Source: Scandinavian Runic-text Database (Rundata), Viking-age runestones: 239 Danish (including Scania, Halland, "
                "Blekinge and Bornholm) and 2,321 Swedish; features after Rundata's translations. Shares without time adjustment; the "
                f"comparisons in the text hold time constant. Percent. {CHART_EN}"))
    return "\n".join(out) + "\n:::"


from src import nordic as _nd  # noqa: E402
_late = [r for r in RD.values() if _nd.is_runestone(r) and _nd.land_of(r) == "danmark" and _nd.bin_of(_nd.year_of(r)) == "sen"]
LATE_N = len(_late)
LATE_BON = sum(1 for r in _late if _nd.patterns(r, _nd.features(r)).get("bon") == 1)
assert (LATE_N, LATE_BON) == (44, 17) and sum(1 for r in _late if _nd.realm_of(r) == "dk_bornholm") == 38
TITEL_SE_SV = f"{100 * A['A_titel']['SE']['a'] / 2321:.1f}".replace(".", ",")
TITEL_SE_EN = f"{100 * A['A_titel']['SE']['a'] / 2321:.1f}"
SLUG = "i-danmark-mindes-man-kamraten"
title = "I Danmark mindes man kamraten – vad de danska runstenarna säger"
title_en = "In Denmark they remembered the comrade – what the Danish runestones say"
summary = ("Två nästan likadana runstenar, en i Hobro och en i Västergötland, minns samma man: Karl, sin félagi. Det är typiskt "
           "danskt. Vi har jämfört budskapen på 239 danska och 2 321 svenska runstenar från samma tid. De danska minns kamrater "
           "och herrar, nämner ämbeten och hedniska gudar, och säger oftare att minnesmärket är större än stenen.")
summary_en = ("Two almost identical runestones, one at Hobro and one in Västergötland, remember the same man: Karl, his félagi. "
              "That is typically Danish. We have compared the messages on 239 Danish and 2,321 Swedish runestones from the same "
              "time. The Danish ones remember comrades and lords, name offices and pagan gods, and more often say that the "
              "monument is larger than the stone.")

body = f"""*ÞoriR resþi sten þæssi æftiR Karl hin Goþa, felaga sin, harþa goþan dræng.*

’Tore reste denna sten efter Karl den gode, sin félagi, en mycket god dräng.’

Stenen står i Hobro på Jylland, inte långt från ringborgen Fyrkat. På andra sidan Kattegatt, i Ås socken i Västergötland, står en sten med nästan samma ord: *ÞoriR ræisti stæin þannsi æftiR Karl, sinn felaga, harða goðan dræng.* De två stenarna ”anses vara resta över samma person”, skrev Carl Löfving i Fornvännen 1984 (s. 102), efter Erik Moltke. En man hade alltså två minnesstenar på var sin sida om det som skulle bli riksgränsen, och båda säger samma sak om honom: att han var Tores *félagi*, hans kompanjon, delägare eller vapenbroder.

Det är ett typiskt danskt budskap. Den här artikeln handlar om vad de danska runstenarna säger som de svenska sällan säger. Vi har jämfört alla 239 danska vikingatida runstenar i Samnordisk runtextdatabas, Rundata, med de 2 321 svenska. Till Danmark räknar vi som Rundata hela det dåtida riket, alltså också Skåne, Halland, Blekinge och Bornholm. De danska stenarna är i genomsnitt äldre än de svenska, och därför har vi bara jämfört stenar från samma tid, i tre skikt: före 1000, 1000–1050 och efter 1050. Frågorna och gränserna låstes innan vi räknade.

## Kamraten, inte släkten

På de svenska stenarna är det nästan alltid släkten som minns: söner efter fäder, hustrur efter män, bröder efter bröder. På de danska minns man oftare någon som inte var släkt. Bland de {M1['DK']['n']} danska stenar där det framgår hur resaren och den döde hörde ihop är den döde en kamrat eller en herre på {M1['DK']['a']}, ungefär var åttonde. Bland de svenska är det {M1['SE']['a']} av {f_sv(M1['SE']['n'])}, färre än en på tvåhundra.

{chart("sv")}

Skillnaden finns i alla tre tidsskikten, och den syns lika tydligt på Jylland som i rikets östra del. Om stenarna i själva verket var lika och bara slumpen skilde dem åt, skulle en så stor skillnad komma i färre än ett fall på tusen miljarder.

Flera av kamraterna dog i strid. Sjörupstenen i Skåne minns Asbjörn, Sakses *félagi*: *SaR flo ægi at Upsalum, æn wa mæþ han wapn hafþi*, ’han flydde inte vid Uppsala, utan stred så länge han hade vapen’. En av Århusstenarna minns Ful, som dog *þa kunungaR barþusk*, ’när kungar stred’. Och vid Hedeby reste Torulf, kung Svens hirdman, en sten efter Erik, sin *félagi*, som dog *þa drængiaR satu um Heþaby*, ’när krigare belägrade Hedeby’. Där fanns också den omvända riktningen, herren som minns sin man: *Swen kunungR satti sten æftiR Skarþa, sin hemþæga*, ’kung Sven satte stenen efter Skarde, sin hirdman’.

{PIC("DR 279", "sv")} ”Han flydde inte vid Uppsala.”

Det här har forskningen sett förut. Birgit Sawyer skrev 1989 att just kompanjonstenarna ”{Q['saw192a']}” (Scandia 55, s. 192), och att det danska mönstret ”{Q['saw192b']}” (samma sida). Hon jämförde Danmark med Uppland och Småland. Det vi har lagt till är jämförelsen med hela Sverige och med tiden hållen lika – och skillnaden är större än man kanske anar. Av de fem svenska kamratstenarna står tre i Västergötland, och där står också stenen efter Karl. Västergötland har, med Sawyers ord, mönster med mer ”danska” än ”uppländska” drag (s. 193), och vi har själva visat hur västgötarna skrev som danskarna i [Västgötarna skrev som danskarna](/artiklar/vastgotarna-skrev-som-danskarna).

## Bryten, goden och kungens man

De danska döda hade också oftare ett ämbete. Utöver titlarna *þegn* och *drængr*, som vi återkommer till, nämner {M3['DK']['a']} av de 239 danska stenarna ett ämbete eller en ställning: förvaltaren *bryti*, goden, kungens hirdman, styrmannen, ’den främste av landmännen i Danmark’. Bland de svenska är det {M3['SE']['a']} av {f_sv(M3['SE']['n'])}, och i den siffran ingår dessutom några män som bara hette Jarl. Med tiden hållen lika skulle slumpen ge en så stor skillnad ungefär en gång på tusen.

På Randbølstenen reste en bryte en sten efter en annan brytes maka: *Tofi Bryti resþi sten þænsi æft lika brytia*. Henrik Williams beskriver *bryti* som ett ord som ”{Q['wil71']}” (Futhark 4, 2013, s. 71). På Helnæs på Fyn kallar sig resaren *nøRa goþi*, ’nesbornas gode’, och på Glavendrup minns Ragnhild Alle, som var gode vid helgedomen och þegn i följet.

Också det har Sawyer sett. Hon räknar titlarna, också ”landman”, till kännetecknen för det danska mönstret och tillägger att ”{Q['saw193b']}” (s. 192–193). Stenarna i Jelling är de tydligaste exemplen. *Haraldr kunungR baþ gørwa kumbl þøsi æft Gorm, faþur sin*, ’Harald kung lät göra dessa kummel efter Gorm, sin fader’.

{PIC("DR 3", "sv")} Kung Sven satte stenen efter Skarde, sin hirdman.

## Tor, förbannelsen och korset

Vi har skrivit om de hedniska stenarna i [Tor svarade korset – och tystnade](/artiklar/tor-svarade-korset-och-tystnade). Siffrorna står sig: {A['A_hednisk']['DK']['a']} av de 239 danska stenarna har en hednisk eller rituell markör, mot {A['A_hednisk']['SE']['a']} av de 2 321 svenska, och med tiden hållen lika är det omkring fem gånger vanligare i Danmark. På Glavendrup står *Þor wigi þæssi runaR*, ’Tor vige dessa runor’, och efter det en förbannelse över den som flyttar stenen. På Sønder Kirkeby på Falster ber Sassur Tor att vige runorna efter brodern, som dog på Gotland.

{PIC("DR 209", "sv")} ”Tor vige dessa runor.”

Det motsatta gäller korset. Kristen text står på {round(100 * A['A_kristen']['DK']['a'] / 239)} procent av de danska stenarna och {round(100 * A['A_kristen']['SE']['a'] / 2321)} procent av de svenska. Om magiska besvärjelser och hedniska gudar skrev Sawyer 1989 att ”{Q['saw185']}” (s. 185), och Rune Palm 1992: ”{Q['palm257']}” (s. 257). Undantaget är Bornholm, där kristna böner enligt Lisbeth Imer står ”{Q['gra184']}” (efter Anne-Sofie Gräslunds recension i Futhark 7, s. 184).

Det är därför de danska stenarna har fått rykte om sig att vara hedniska. Men av 239 stenar har bara {A['A_hednisk']['DK']['a']} en hednisk markör. Det typiska danska budskapet är varken hedniskt eller kristet. Det handlar om lojalitet och rang.

## Mer än en sten

De danska inskrifterna säger också oftare att minnesmärket är större än stenen. Ordet *kumbl*, ’kummel, minnesmärke’, står ofta i plural, ’dessa kummel’, och andra stenar talar om en hög, flera stenar eller en skeppssättning. Det gäller {B2['DK']['a']} av de danska stenarna, var sjätte, och {B2['SE']['a']} av de svenska, var tjugonde. Med tiden hållen lika är skillnaden mer än dubbel, och slumpen skulle ge den ungefär två gånger på tiotusen.

På Tryggevælde på Själland *satti sten þænsi ok gærþi høg þænsi æft, ok skeþ þæssi*, Ragnhild ’satte denna sten och gjorde denna hög och detta skepp’ efter sin man Gunnulf. Det är samma Ragnhild som på Glavendrup, och hennes två stenar står, som Gräslund skriver, ”{Q['gra183b']}” (s. 183).

{PIC("DR 230", "sv")} Ragnhild satte stenen och gjorde högen och skeppet.

Vad *kumbl* betyder är omdiskuterat. Ole Thamdrup påpekar att ordet ”{Q['tha11']}” och återger den danske filologen Karl Martin Nielsens tanke att det i plural avser runstenen tillsammans med andra resta stenar (Kuml 1981, s. 11). Judith Jesch räknar *kumbl*, högar och skeppssättningar till kännetecknen för de danska þegn-monumenten (Futhark 4, 2013, s. 89–90). En jämförelse mellan länderna har vi inte hittat.

Titlarna hör hit. *Þegn* och *drængr* står på {round(100 * A['A_titel']['DK']['a'] / 239)} procent av de danska stenarna och {TITEL_SE_SV} procent av de svenska. Judith Jesch har visat att þegn-stenarna samlas i Danmark, Västergötland och Södermanland (s. 89).

## Satte, inte reste – och sällan kvinnor

Också själva resandet beskrivs annorlunda. Danskarna *satte* sina stenar: verbet står på {round(100 * A['A_placed']['DK']['a'] / 239)} procent av de danska stenarna och {round(100 * A['A_placed']['SE']['a'] / 2321)} procent av de svenska. Att någon *lät* resa stenen, som i Uppland, står på {round(100 * A['A_had']['DK']['a'] / 239)} procent av de danska mot {round(100 * A['A_had']['SE']['a'] / 2321)} procent av de svenska.

Kvinnorna reste färre stenar i Danmark. Bland stenar där vi kan avgöra resarens kön har {round(100 * B3['DK']['a'] / B3['DK']['n'])} procent av de danska en kvinna bland resarna, mot {round(100 * B3['SE']['a'] / B3['SE']['n'])} procent av de svenska. Med tiden hållen lika ger slumpen en sådan skillnad ungefär åtta gånger på tusen. Sawyer kom fram till nästan samma andelar 1989, omkring 14 procent i Danmark mot 27 i hela materialet (tabell 1, s. 190). Men de kvinnor som reste stenar i Danmark reste ofta stora minnesmärken: Ragnhild på Glavendrup och Tryggevælde, Asfrid, mor till kung Sigtrygg, vid Hedeby, och Tove, Haralds drottning, som lät göra ett kummel efter sin mor. Gräslund påpekar: ”{Q['gra183a']}” (s. 183).

## Det som inte skilde

Två saker visade ingen skillnad. Döden i strid är lika sällsynt på båda hållen: {M2['DK']['a']} danska stenar och {M2['SE']['a']} svenska berättar uttryckligen att den döde stupade eller stred. Flera av kamraterna dog i strid, men stenar över stupade var inte i sig vanligare i Danmark. Och andelen stenar som i dag står vid en kyrka skiljer sig inte när tiden hålls lika. Däremot står var femte dansk sten på museum, mot var tjugonde svensk.

## Ett budskap med ett slutdatum

Det danska mönstret hör till en viss tid. Kamraterna, ämbetena och de hedniska markörerna finns på stenar från före 1050. Efter 1050, när de flesta danska stenar står på Bornholm, finns ingen av dem: ingen kamrat, inget ämbete, ingen Tor. Då liknar de danska stenarna de svenska: {LATE_BON} av de {LATE_N} sena stenarna har en kristen bön. Den värld som stenarna i Hobro och Ås minns – kungarnas och stormännens följen, där en mans *félagi* var den som reste stenen – var Haralds och Svens värld, och den gick över.

## Svagheterna

- **Dragen är räknade ur Rundatas engelska översättningar.** Alla danska träffar har vi läst en och en. Två av kamratstenarna är tveksamt kodade: Skern 2, där den döde var trogen sin herre men resaren inte anges som hans kamrat, och Glavendrup, där Ragnhilds förhållande till Alle inte står i inskriften. Utan dem är det 15 av 134, och resultatet står sig. Bland de svenska ämbetena ingår några män som hette Jarl, vilket gör skillnaden mindre, inte större.
- **Tiden är grov.** De danska stenarna dateras efter Rundatas danska perioder och de svenska efter stilgrupperna. Tre tidsskikt fångar den stora skillnaden i ålder, men inte allt.
- **Danmark är här hela det dåtida riket,** med Skåne, Halland, Blekinge och Bornholm. Resultaten håller både för Jylland och för den östra delen.
- **Det mesta är känt.** Sawyer såg kamratstenarna, titlarna, de få kvinnorna och kungarna redan 1989. Det vi har lagt till är jämförelsen med hela Sverige, tiden hållen lika, uppdelningen inom Danmark och två nya mått: ämbetena och minnesmärken som är större än stenen. Sawyers bok från 2000 har vi inte kunnat läsa.

Nästa gång du läser en dansk runsten, se efter vem som reste den. Är det en *félagi*, en hirdman eller en kung, har du framför dig ett budskap som nästan aldrig ristades i Uppland.

:::box Det viktigaste i korthet
- De danska runstenarna minns oftare en kamrat eller en herre än släkten: var åttonde mot färre än en på tvåhundra i Sverige, vid samma tid. Birgit Sawyer såg mönstret 1989; skillnaden mot hela Sverige är större än man kanske anar.
- De nämner oftare ämbeten och titlar – bryte, gode, hirdman, þegn – och säger oftare att minnesmärket är större än stenen: en hög, flera stenar eller ett skepp.
- Hedniska markörer är fem gånger vanligare än i Sverige, men finns ändå bara på 8 av 239 stenar. Det typiska danska budskapet handlar om lojalitet och rang, inte om gudarna.
- Mönstret hör till tiden före 1050. Efter det liknar de danska stenarna de svenska.
:::

## Källor

- Samnordisk runtextdatabas (Rundata), Institutionen för nordiska språk, Uppsala universitet. Open Database License.
- Sawyer, Birgit 1989. Det vikingatida runstensresandet i Skandinavien. *Scandia* 55:2, s. 185–202. [Fritt hos Scandia](https://journals.lub.lu.se/scandia/article/view/440).
- Palm, Rune 1992. *Runor och regionalitet. Studier av variation i de nordiska minnesinskrifterna*. Runrön 7. Uppsala. [Fritt på DiVA](https://www.diva-portal.org/smash/record.jsf?pid=diva2:740596).
- Löfving, Carl 1984. Förändringar i maktstrukturen kring östra Skagerrak vid kristendomens införande. *Fornvännen* 79, s. 93–103. CC BY 4.0. [Fri fulltext](http://kulturarvsdata.se/raa/fornvannen/html/1984_093).
- Jesch, Judith 2013. Runes and Words: Runic Lexicography in Context. *Futhark* 4, s. 77–100. CC BY 4.0.
- Williams, Henrik 2013. Runstenarnas sociala dimension. *Futhark* 4, s. 61–76. CC BY 4.0.
- Gräslund, Anne-Sofie 2016. Recension av Lisbeth M. Imer och Roberto Fortuna, *Danmarks runesten: En fortælling* (2016). *Futhark* 7, s. 181–185. [Fri fulltext](https://uu.diva-portal.org/smash/get/diva2:1087624/FULLTEXT01.pdf).
- Thamdrup, Ole 1981. … og gjorde disse mindesmærker … *Kuml* 1981, s. 7–12. [doi:10.7146/kuml.v30i30.107749](https://doi.org/10.7146/kuml.v30i30.107749).
- Analysplanen och tillägget om budskapet (låsta före körningen) och koden finns öppet på [GitHub](https://github.com/Precatio/runes/blob/main/analysplaner/2026-11-17-danska-runstenar.md). Om de hedniska stenarna: [Tor svarade korset – och tystnade](/artiklar/tor-svarade-korset-och-tystnade). Om gränsen: [Västgötarna skrev som danskarna](/artiklar/vastgotarna-skrev-som-danskarna). Om Norge: [Varför har Norge bara 66 runstenar – och Sverige 2 300?](/artiklar/varfor-har-norge-bara-66-runstenar)
- Foton: Wikimedia Commons, med fotograf och licens i bildtexterna."""

body_en = f"""*ÞoriR resþi sten þæssi æftiR Karl hin Goþa, felaga sin, harþa goþan dræng.*

‘Þórir raised this stone in memory of Karl the Good, his félagi, a very good valiant man.’

The stone stands at Hobro in Jutland, not far from the ring fortress of Fyrkat. Across the Kattegat, in Ås parish in Västergötland, stands a stone with almost the same words: *ÞoriR ræisti stæin þannsi æftiR Karl, sinn felaga, harða goðan dræng.* The two stones are “considered to have been raised in memory of the same person”, wrote Carl Löfving in Fornvännen in 1984 (p. 102, our translation), after Erik Moltke. One man thus had two memorial stones on either side of what would become the border between the realms, and both say the same thing about him: that he was Þórir's *félagi*, his partner, co-owner or brother-in-arms.

That is a typically Danish message. This article is about what the Danish runestones say that the Swedish ones seldom say. We have compared all 239 Danish Viking-age runestones in the Scandinavian Runic-text Database, Rundata, with the 2,321 Swedish ones. Like Rundata, we count the whole realm of the time as Denmark, including Scania, Halland, Blekinge and Bornholm. The Danish stones are on average older than the Swedish ones, so we have only compared stones from the same time, in three layers: before 1000, 1000–1050 and after 1050. The questions and the thresholds were locked before we counted.

## The comrade, not the kin

On the Swedish stones it is almost always the family that remembers: sons for fathers, wives for husbands, brothers for brothers. On the Danish stones people more often remember someone who was not kin. Among the {M1['DK']['n']} Danish stones where we can see how the raiser and the dead belonged together, the dead is a comrade or a lord on {M1['DK']['a']}, about one in eight. Among the Swedish ones it is {M1['SE']['a']} of {M1['SE']['n']:,}, fewer than one in two hundred.

{chart("en")}

The difference is there in all three layers of time, and it shows as clearly in Jutland as in the eastern part of the realm. If the stones were in fact alike and only chance set them apart, a difference this large would come up in fewer than one case in a trillion.

Several of the comrades died in battle. The Sjörup stone in Scania remembers Ásbjôrn, Saxi's *félagi*: *SaR flo ægi at Upsalum, æn wa mæþ han wapn hafþi*, ‘he did not flee at Uppsala, but fought as long as he had a weapon’. One of the Århus stones remembers Fúl, who died *þa kunungaR barþusk*, ‘when kings fought’. And at Hedeby, Þórulfr, King Sveinn's retainer, raised a stone in memory of Eiríkr, his *félagi*, who died *þa drængiaR satu um Heþaby*, ‘when warriors besieged Hedeby’. The other direction is there too, the lord remembering his man: *Swen kunungR satti sten æftiR Skarþa, sin hemþæga*, ‘King Sveinn placed the stone in memory of Skarði, his retainer’.

{PIC("DR 279", "en")} “He did not flee at Uppsala.”

Research has seen this before. Birgit Sawyer wrote in 1989 that the partner stones are “common in Danish territory but rare elsewhere” (“{Q['saw192a']}”, Scandia 55, p. 192), and that the Danish pattern is dominated by stones raised by individuals, a low share of women and a relatively large share of raisers other than the closest family (same page). She compared Denmark with Uppland and Småland. What we have added is the comparison with the whole of Sweden, with time held constant – and the difference is larger than one might think. Of the five Swedish comrade stones, three stand in Västergötland, and that is where the stone for Karl stands too. Västergötland has, in Sawyer's words, patterns with more “Danish” than “Upplandic” features (p. 193), and we have shown ourselves how the people of Västergötland wrote like the Danes in [The men of Västergötland wrote like the Danes](/en/artiklar/vastgotarna-skrev-som-danskarna).

## The steward, the priest and the king's man

The Danish dead also more often held an office. Besides the titles *þegn* and *drengr*, to which we will return, {M3['DK']['a']} of the 239 Danish stones name an office or rank: the steward *bryti*, the priest-chieftain (*goði*), the king's retainer, the captain, ‘the first and best of landholders in Denmark’. Among the Swedish stones it is {M3['SE']['a']} of {M3['SE']['n']:,}, and that figure even includes a few men who were simply called Jarl. With time held constant, chance would give a difference this large about once in a thousand.

On the Randbøl stone one steward raised a stone in memory of another steward's wife: *Tofi Bryti resþi sten þænsi æft lika brytia*. Henrik Williams describes *bryti* as a word that denotes an office-holder of considerable standing (Futhark 4, 2013, p. 71). At Helnæs on Funen the raiser calls himself *nøRa goþi*, ‘priest-chieftain of the Nes-dwellers’, and at Glavendrup Ragnhildr remembers Alli, priest of the sanctuary and þegn of the retinue.

Sawyer saw this too: the Danish pattern is further marked by various kinds of titles, and she adds that “only in Denmark do royal persons raise stones” (“{Q['saw193b']}”, pp. 192–193). The stones at Jelling are the clearest examples. *Haraldr kunungR baþ gørwa kumbl þøsi æft Gorm, faþur sin*, ‘King Haraldr ordered these monuments made in memory of Gormr, his father’.

{PIC("DR 3", "en")} King Sveinn placed the stone in memory of Skarði, his retainer.

## Thor, the curse and the cross

We have written about the pagan stones in [Thor answered the cross – and fell silent](/en/artiklar/tor-svarade-korset-och-tystnade). The figures stand: {A['A_hednisk']['DK']['a']} of the 239 Danish stones have a pagan or ritual marker, against {A['A_hednisk']['SE']['a']} of the 2,321 Swedish ones, and with time held constant that is about five times as common in Denmark. At Glavendrup it says *Þor wigi þæssi runaR*, ‘may Thor hallow these runes’, followed by a curse on whoever moves the stone. At Sønder Kirkeby on Falster, Sassurr asks Thor to hallow the runes for his brother, who died on Gotland.

{PIC("DR 209", "en")} “May Thor hallow these runes.”

The cross is the opposite. Christian text stands on {round(100 * A['A_kristen']['DK']['a'] / 239)} per cent of the Danish stones and {round(100 * A['A_kristen']['SE']['a'] / 2321)} per cent of the Swedish ones. Sawyer said so in 1989: pagan spells and invocations occur in Denmark but are rare in Swedish territory, where Christian crosses and prayers are common instead (p. 185), and Rune Palm in 1992: “a religious content is almost entirely lacking in the Danish material” (“{Q['palm257']}”, p. 257, our translation). The exception is Bornholm, where according to Lisbeth Imer Christian prayers stand on almost half of the inscriptions (after Anne-Sofie Gräslund's review in Futhark 7, p. 184).

That is why the Danish stones have a reputation for being pagan. But of 239 stones only {A['A_hednisk']['DK']['a']} have a pagan marker. The typical Danish message is neither pagan nor Christian. It is about loyalty and rank.

## More than a stone

The Danish inscriptions also more often say that the monument is larger than the stone. The word *kumbl*, ‘monument’, often stands in the plural, ‘these monuments’, and other stones speak of a mound, several stones or a ship-setting. That holds for {B2['DK']['a']} of the Danish stones, one in six, and {B2['SE']['a']} of the Swedish ones, one in twenty. With time held constant the difference is more than double, and chance would give it about twice in ten thousand.

At Tryggevælde on Zealand, Ragnhildr *satti sten þænsi ok gærþi høg þænsi æft, ok skeþ þæssi*, ‘placed this stone and made this mound and this ship’ in memory of her husband Gunnulfr. It is the same Ragnhildr as at Glavendrup, and both her stones stand in contact with impressive ship-settings, as Gräslund writes (p. 183).

{PIC("DR 230", "en")} Ragnhildr placed the stone and made the mound and the ship.

What *kumbl* means is debated. Ole Thamdrup notes that the word “{Q['tha11']}” and reports the Danish philologist Karl Martin Nielsen's view that in the plural it means the runestone together with other raised stones (Kuml 1981, p. 11). Judith Jesch counts *kumbl*, mounds and ship-settings among the marks of the Danish þegn monuments (Futhark 4, 2013, pp. 89–90). A comparison between the countries we have not found.

The titles belong here. *Þegn* and *drengr* stand on {round(100 * A['A_titel']['DK']['a'] / 239)} per cent of the Danish stones and {TITEL_SE_EN} per cent of the Swedish ones. Jesch has shown that the þegn stones are concentrated “{Q['jes89']}” (p. 89).

## Placed, not raised – and seldom by women

The raising itself is described differently too. The Danes *placed* their stones: the verb stands on {round(100 * A['A_placed']['DK']['a'] / 239)} per cent of the Danish stones and {round(100 * A['A_placed']['SE']['a'] / 2321)} per cent of the Swedish ones. That someone *had* the stone raised, as in Uppland, stands on {round(100 * A['A_had']['DK']['a'] / 239)} per cent of the Danish stones against {round(100 * A['A_had']['SE']['a'] / 2321)} per cent of the Swedish ones.

Women raised fewer stones in Denmark. Among stones where we can tell the raiser's sex, {round(100 * B3['DK']['a'] / B3['DK']['n'])} per cent of the Danish ones have a woman among the raisers, against {round(100 * B3['SE']['a'] / B3['SE']['n'])} per cent of the Swedish ones. With time held constant, chance gives a difference like that about eight times in a thousand. Sawyer arrived at almost the same shares in 1989, about 14 per cent in Denmark against 27 in the whole material (table 1, p. 190). But the women who did raise stones in Denmark often raised great monuments: Ragnhildr at Glavendrup and Tryggevælde, Ásfríðr, mother of King Sigtryggr, at Hedeby, and Tófa, Haraldr's queen, who had a monument made in memory of her mother. Gräslund points out that it was not so unusual in Denmark for women to raise runestones for men (p. 183).

## What did not differ

Two things showed no difference. Death in battle is just as rare on both sides: {M2['DK']['a']} Danish stones and {M2['SE']['a']} Swedish ones say outright that the dead fell or fought. Several of the comrades died in battle, but stones for the fallen were not in themselves more common in Denmark. And the share of stones that stand by a church today does not differ when time is held constant. One in five Danish stones, however, is in a museum today, against one in twenty Swedish ones.

## A message with an end date

The Danish pattern belongs to a particular time. The comrades, the offices and the pagan markers are found on stones from before 1050. After 1050, when most Danish stones stand on Bornholm, none of them is there: no comrade, no office, no Thor. Then the Danish stones look like the Swedish ones: {LATE_BON} of the {LATE_N} late stones have a Christian prayer. The world that the stones at Hobro and Ås remember – the retinues of kings and great men, where a man's *félagi* was the one who raised his stone – was the world of Haraldr and Sveinn, and it passed.

## The weaknesses

- **The features are counted from Rundata's English translations.** We have read every Danish hit one by one. Two of the comrade stones are doubtfully coded: Skern 2, where the dead was loyal to his lord but the raiser is not named as his comrade, and Glavendrup, where Ragnhildr's relation to Alli is not in the inscription. Without them it is 15 of 134, and the result stands. Among the Swedish offices are a few men called Jarl, which makes the difference smaller, not larger.
- **Time is coarse.** The Danish stones are dated by Rundata's Danish periods and the Swedish ones by the style groups. Three layers of time capture the large difference in age, but not everything.
- **Denmark here is the whole realm of the time,** with Scania, Halland, Blekinge and Bornholm. The results hold both for Jutland and for the eastern part.
- **Most of it is known.** Sawyer saw the partner stones, the titles, the few women and the kings as early as 1989. What we have added is the comparison with the whole of Sweden, time held constant, the split within Denmark and two new measures: the offices and monuments larger than the stone. Sawyer's book of 2000 we have not been able to read.

Next time you read a Danish runestone, look at who raised it. If it is a *félagi*, a retainer or a king, you have in front of you a message that was almost never carved in Uppland.

:::box The essentials in brief
- The Danish runestones more often remember a comrade or a lord than the family: one in eight against fewer than one in two hundred in Sweden, at the same time. Birgit Sawyer saw the pattern in 1989; the difference against the whole of Sweden is larger than one might think.
- They more often name offices and titles – steward, priest-chieftain, retainer, þegn – and more often say that the monument is larger than the stone: a mound, several stones or a ship.
- Pagan markers are five times as common as in Sweden, but still stand on only 8 of 239 stones. The typical Danish message is about loyalty and rank, not about the gods.
- The pattern belongs to the time before 1050. After that the Danish stones look like the Swedish ones.
:::

## Sources

- Scandinavian Runic-text Database (Rundata), Department of Scandinavian Languages, Uppsala University. Open Database License.
- Sawyer, Birgit 1989. Det vikingatida runstensresandet i Skandinavien. *Scandia* 55:2, pp. 185–202. [Open at Scandia](https://journals.lub.lu.se/scandia/article/view/440).
- Palm, Rune 1992. *Runor och regionalitet. Studier av variation i de nordiska minnesinskrifterna*. Runrön 7. Uppsala. [Open on DiVA](https://www.diva-portal.org/smash/record.jsf?pid=diva2:740596).
- Löfving, Carl 1984. Förändringar i maktstrukturen kring östra Skagerrak vid kristendomens införande. *Fornvännen* 79, pp. 93–103. CC BY 4.0. [Free full text](http://kulturarvsdata.se/raa/fornvannen/html/1984_093).
- Jesch, Judith 2013. Runes and Words: Runic Lexicography in Context. *Futhark* 4, pp. 77–100. CC BY 4.0.
- Williams, Henrik 2013. Runstenarnas sociala dimension. *Futhark* 4, pp. 61–76. CC BY 4.0.
- Gräslund, Anne-Sofie 2016. Review of Lisbeth M. Imer and Roberto Fortuna, *Danmarks runesten: En fortælling* (2016). *Futhark* 7, pp. 181–185. [Free full text](https://uu.diva-portal.org/smash/get/diva2:1087624/FULLTEXT01.pdf).
- Thamdrup, Ole 1981. … og gjorde disse mindesmærker … *Kuml* 1981, pp. 7–12. [doi:10.7146/kuml.v30i30.107749](https://doi.org/10.7146/kuml.v30i30.107749).
- The analysis plan and the addendum on the message (locked before the run) and the code are open on [GitHub](https://github.com/Precatio/runes/blob/main/analysplaner/2026-11-17-danska-runstenar.md). On the pagan stones: [Thor answered the cross – and fell silent](/en/artiklar/tor-svarade-korset-och-tystnade). On the border: [The men of Västergötland wrote like the Danes](/en/artiklar/vastgotarna-skrev-som-danskarna). On Norway: [Why does Norway have only 66 runestones – and Sweden 2,300?](/en/artiklar/varfor-har-norge-bara-66-runstenar)
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
labels = ["Forskning", "Norden", "Tro och magi", "Formler och syfte", "Kvinnor och barn"]
err = blog_labels.check(labels)
assert err is None, err
out = {"slug": SLUG, "title": title, "summary": summary, "body": body, "title_en": title_en, "summary_en": summary_en,
       "body_en": body_en, "labels": labels}
path = os.path.join(ROOT, "utdata", "blogg", "danmark.json")
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
                 "topic": "Forskning|danmark", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
