"""Artikeln "De gamla landen: Sotholm – det yttre landet på ön Tören" (sv + en), del 1 i serien De gamla landen. Sedan
2026-11-04 i seriens atmosfäriska form (Viktor): landskapet, hur man bodde och levde, borgarna och tinget; runstenarna är en
del av platsen, och bönen som saknas (1 av 43) står kvar som ett inslag. Siffrorna låses mot utdata/gamla_granser/monster.json
(häradsskannern, plan 054c87d5) och utdata/sotholm/sotholm.json (plan 9fa481d3); landskapet mot DMS 2:1 och Wikell 2011.
    ../../../.venv/bin/python build_sotholm.py [--write | --update DOC]   (publicerad: patch_sotholm_live.py)"""
import csv
import datetime as dt
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import commons  # noqa: E402

# the published article rests on the run of 2 November (731 tests); the run with the Mälaren islands in their folkland
# (2026-11-05, 734 tests) is in monster.json, the original is kept as monster_v1.json
M = json.load(open(os.path.join(ROOT, "utdata", "gamla_granser", "monster_v1.json"), encoding="utf-8"))
S = json.load(open(os.path.join(ROOT, "utdata", "sotholm", "sotholm.json"), encoding="utf-8"))
D = json.load(open(os.path.join(ROOT, "utdata", "sotholm", "sotholm_beskrivning.json"), encoding="utf-8"))
ST = list(csv.DictReader(open(os.path.join(ROOT, "utdata", "sotholm", "sotholm_stenar.csv"), encoding="utf-8")))
recs = {r["signum"]: r for r in json.load(open(os.path.join(ROOT, "data", "rundata.json"), encoding="utf-8"))["inscriptions"]}
nz = lambda s: recs[s]["normalization"].replace('"', "").strip()  # noqa: E731
pc = lambda x: round(100 * x)  # noqa: E731

# ---- the locked numbers -----------------------------------------------------------------------------------------------
T = [t for t in M["step3"]["tests"] if t["unit"] == "Sotholms hd|Sö" and t["feature"] == "cat_kristen"][0]
assert T["holds"] and M["step3"]["n_tests"] == 731 and M["step3"]["units"] == 35
assert round(T["q"], 3) == 0.026 and T["n_in"] == 43 and round(T["share_in"] * 43) == 1 and pc(T["share_out"]) == 20
assert [round(h["p"], 3) for h in T["halves"]] == [0.022, 0.003] and T["without_top_carver"]["carver"] == "Amunde"
N_HOLD3 = sum(t.get("holds", False) for t in M["step3"]["tests"])
assert N_HOLD3 == 6
G = S["T1"]["grund"]
assert round(G["or"], 3) == 0.081 and round(1 / G["or"]) == 12
assert round(S["T1"]["a_ristare_slump"]["p"], 2) == 0.45 and not S["T1"]["a_ristare_slump"]["holds"]
E = S["T1"]["e_utan_sotholms_ristare"]
assert (E["k_in"], E["n_in"], pc(E["share_out"]), round(E["p"], 3)) == (1, 18, 20, 0.042) and E["holds"]
assert S["so_carvers"] == ["Amunde", "Björn 2 eller -björn", "Halvdan"]
for k in ("b_pa_plats", "c_daterade", "d_utan_forlorade"):
    assert S["T1"][k]["holds"] and S["T1"][k]["p"] < 0.003
assert (S["T1"]["c_daterade"]["k_in"], S["T1"]["c_daterade"]["n_in"]) == (0, 27)
K = S["T2"]
assert (K["k_in"], K["n_in"], pc(K["share_in"]), pc(K["share_out"]), round(K["p"], 2)) == (25, 43, 58, 52, 0.68)
SV = S["T3"]
assert (SV["k_in"], SV["n_in"], pc(SV["share_out"]), round(SV["p"], 2)) == (5, 40, 21, 0.13)
assert S["T4"]["median_so"] == S["T4"]["median_rest"] == 1030 and round(S["T4"]["p"], 2) == 0.42
PP = S["T4"]["per_period"]["1010–1040"]
assert PP["so"] == [0, 22] and PP["rest"] == [23, 96] and pc(23 / 96) == 24
assert [c for c, _ in D["carvers"][:4]] == ["–", "Amunde", "Halvdan", "Björn 2 eller -björn"]
assert dict(D["carvers"])["Amunde"] == 11 and dict(D["carvers"])["Halvdan"] == 9 and dict(D["carvers"])["Björn 2 eller -björn"] == 5
assert D["christian_stones"] == ["Sö ATA322-4237-2011"]
assert dict(D["parishes"]) == {"Sorunda sn": 12, "Österhaninge sn": 12, "Ösmo sn": 10, "Västerhaninge sn": 8, "Tyresö sn": 1}
# the carvers outside Sotholm (corpus 7b9061c9): never a Christian formula anywhere
CORP = list(csv.DictReader(open(os.path.join(ROOT, "data", "cache", "r", "corpus", "7b9061c9a1c12c73", "corpus.csv"), encoding="utf-8")))
own = lambda name: [r for r in CORP if name in r["carvers_all"].split(";")]  # noqa: E731
assert (sum(r["cat_kristen"] == "1" for r in own("Halvdan")), len(own("Halvdan"))) == (0, 17)
assert (sum(r["cat_kristen"] == "1" for r in own("Amunde")), len(own("Amunde"))) == (0, 13)
SMA = "Sö ATA322-4237-2011"
assert "Guð hialpi and hans" in nz(SMA) and recs[SMA]["place"] == "Småhamra" and recs[SMA]["parish"] == "Österhaninge sn"
assert "Halfdan, faður sinn" in nz(SMA) and recs[SMA]["style"].startswith("Pr2")
assert nz("Sö 268") == "Hialmviðr ræisti stæin at Þorgaut, sun sinn. Amundi risti runaR."
assert nz("Sö 270") == "Farbiorn/Frøybiorn let haggva stæin at Haulf, sun si[nn]. Halfdan hiogg runaR."
assert "at Viking, faður sinn, sun Stora" in nz("Sö 269")
# per-härad shares in Södermanland (n >= 10), for the chart
HAR = {}
for r in ST:
    if r["cat_kristen"] != "":
        HAR.setdefault(r["harad"], []).append(int(float(r["cat_kristen"])))
HAR = {h: v for h, v in HAR.items() if len(v) >= 10}
assert len(HAR) == 11 and pc(sum(HAR["Daga hd"]) / 13) == 54 and sum(HAR["Sotholms hd"]) == 1
assert (sum(HAR["Svartlösa hd"]), len(HAR["Svartlösa hd"])) == (2, 22) and (sum(HAR["Åkers hd"]), len(HAR["Åkers hd"])) == (1, 15)
# Wikell 2011 (downloaded to /Volumes/2TB/Antigrvity/Runes/downloads/sotholm_lit/rw2011_plain.txt)
WIK = open("/Volumes/2TB/Antigrvity/Runes/downloads/sotholm_lit/rw2011_plain.txt", encoding="utf-8").read().replace("\n", " ")
assert "Runstenar är därför offensiva kristna markörer" in WIK
assert "Amundes stenar i FP har ofta stora kors" in WIK
assert "en hednisk glänta i en skog av kristna runstenar" in WIK
WK = WIK.replace("-  ", "").replace("- ", "")
for k in ("likt gläntor ligger insprängda i skogshavet Hanveden", "Tornberget 111 möh", "Tyresta nationalpark",
          "inskriften Ingelri", "Svärdet dateras till ca år 1000", "Ethelred II och Knut den store",
          "Slutmynt (1035–1042) är för Hardeknut i Lund", "plötslig kolonisation kring 500–600",
          "Amunde har gjort Ingvarsstenen Sö 254, Vansta, Ösmo sn", "ca 75 gravkullar", "den största högen är 16 m bred",
          "björnklor", "sätra och boda", "Såväl sommar som vinter har sjön Drevviken också"):
    assert k in WK or k in WIK, k
assert 1 + 1 + 29 + 6 + 142 + 11 + 3 + 2 == 195  # Norrby hoard, coins and fragments per Wikell: "nästan tvåhundra"
assert "i liði Ingvars" in nz("Sö 254") and "at Tosta" in nz("Sö 254") and recs["Sö 254"]["place"] == "Vansta"

# ---- picture ----------------------------------------------------------------------------------------------------------
F269 = "Sö269.jpg"
INFO = commons.commons_info([F269])
assert INFO[F269]["licence"] == "Public domain"
PAGE = "https://commons.wikimedia.org/wiki/File:" + F269

from src import blog_figures  # noqa: E402
MAP = {lang: blog_figures.freeze(open(os.path.join(ROOT, "utdata", "sotholm", f"karta_toren_{lang}.png"), "rb").read())
       for lang in ("sv", "en")}  # utdata/sotholm/karta_toren.R
BON = "/artiklar/2026-10-bonen-tystnade-korset-stod-kvar"
HN = {"Daga hd": "Daga", "Selebo hd": "Selebo", "Hölebo hd": "Hölebo", "Västerrekarne hd": "Västerrekarne",
      "Österrekarne hd": "Österrekarne", "Oppunda hd": "Oppunda", "Öknebo hd": "Öknebo", "Rönö hd": "Rönö",
      "Svartlösa hd": "Svartlösa", "Åkers hd": "Åker", "Sotholms hd": "Sotholm"}


def chart(lang):
    sv = lang == "sv"
    rows = [":::chart Runstenar med en bön eller kristen formel, per härad i Södermanland" if sv else
            ":::chart Runestones with a prayer or Christian formula, by hundred in Södermanland"]
    for h, v in sorted(HAR.items(), key=lambda x: -sum(x[1]) / len(x[1])):
        rows.append(f"{'+' if h == 'Sotholms hd' else ''}{HN[h]} | {pc(sum(v) / len(v))} | "
                    f"{sum(v)} {'av' if sv else 'of'} {len(v)}")
    rows.append("Källa: Samnordisk runtextdatabas; häradet efter stenens socken i Institutet för språk och folkminnens "
                "ortnamnsregister; härader med minst tio stenar. Diagram: Vitki. Procent." if sv else
                "Source: Scandinavian Runic-text Data Base; the hundred from the stone's parish in the place-name register of "
                "the Institute for Language and Folklore; hundreds with at least ten stones. Chart: Vitki. Percent.")
    return "\n".join(rows) + "\n:::"


# DMS: Janzon & Rahmqvist 2002, Det medeltida Sverige 2:1, Tören (downloads/sotholm_lit/dms_2_1.pdf, deduplicated text)
DMS = open("/Volumes/2TB/Antigrvity/Runes/downloads/sotholm_lit/dms_dedup.txt", encoding="utf-8").read()
for k in ("Tören är det gamla namnet på den halvö som nu kallas Södertörn", "Övre Tör", "Yttre Tör",
          "Först vid denna tid blev Södertörn en halvö genom Täljesundets", "den höglänta ännu delvis ödsliga skogen Hanveden",
          "Kaggfjärden i sydväst", "Södertörns runstenar har mycket stereotypa texter", "En bön för själen finns bara i två fall",
          "Häradets rätta tingsstad hette vid medeltimedeltidens slut 'Sotholm'", "längst in i Landfj",
          "några av landets tätaste järnåldersbygder växt fram i dalarna", "Tornberget (110,5 m ö h)",
          "Sorunda har 21 ristningar", "Kaj Janzon Sigurd Rahmqvist"):
    assert k in DMS, k
for k in ("28 m lång skeppssättning", "skeppssättning av 50 resta stenar", "storhög, 35-40 m i diameter och 5 m hög",
          "Helgö har rimligen haft stor betydelse som verkstads", "faktori", "I Utö gruvor i Västerhaninge har brutits järnmalm sedan medeltiden",
          "ankringsplats och", "för flottor sedan medeltiden", "Danska itinerariet"):
    assert k in DMS.replace("verkstadsverkstads", "verkstads"), k
assert "Intill högen hittades ett depåfynd av spadformiga ämnesjärn, ett städ och en yxa" in WIK and "daterades till folkvandringstid" in WIK
DR = {r["signum"]: r for r in csv.DictReader(open(os.path.join(ROOT, "utdata", "upptackt_v3", "drag.csv"), encoding="utf-8"))}
def share(h, f, inv=False):
    g = [r["signum"] for r in ST if (r["harad"] in h) != inv and DR[r["signum"]].get(f, "") != ""]
    return sum(int(float(DR[s][f])) for s in g), len(g)
assert share({"Sotholms hd"}, "msg_berom") == (2, 43) and share({"Svartlösa hd"}, "msg_berom") == (1, 22)
BR = share({"Sotholms hd", "Svartlösa hd"}, "msg_berom", inv=True)
assert pc(BR[0] / BR[1]) == 22
assert share({"Svartlösa hd"}, "ord_þennsa") == (6, 22) and share({"Sotholms hd"}, "ord_þennsa") == (2, 43)

# ---- the land as it was lived in (rewrite 2026-11-04: the series is atmospheric, the runestones one part of the place) --
D1 = " ".join(DMS.split())
for k in ("91 fornborgar", "landets rikaste landskap på denna fornlämningstyp", "Sorunda, som har 16", "ligger i bygden",
          "djupt undanskymda berg i skogsmarkerna", "nära sankmarker", "Åtminstone sex, delvis stora borgar",
          "markerat järnålderns skärgårds", "Från norra SorunSorunda går t ex en dalgång genom skogen över mot Haningebygden",
          "Längs denna ligger två fornborgar", "Förekomst av kulturlager i borgarna har inte undersökts",
          "fullkolonisation genom självägande bönder", "i Sorunda 54 och i Ösmo 73", "92 byar i dessa socknar har yngre gravfält",
          "36 byar har ett gravfält", "samma ställen som bondbyarna från historisk tid", "står vid något av halvöns många gravfält",
          "dåtida vägar var också relativt vanligt", "Vid Blista i Sorunda är tre ristningar för tre olika famil",
          "gjorda på en häll utefter en väg", "ristaren Hägvid", "vårdkase, som säkert har haft äldre föregångare",
          "bronsåldersröse vid Fituna i Sorunda", "Husby i Österhaninge, som har ett stort gravfä", "två ca 25 m stora högar",
          "Torp, som är den centrala byn vid Sorunda kyrka", "osammansatt namn av äldre typ",
          "ofta med en brödraskara som vill minnas sin far", "gravfalt finns på Utö, Muskö och Torö"):
    assert k in D1, k
for k in ("tjugotalet småbygder", "För tusen år sedan levde tämligen mycket folk i de spridda småbygderna",
          "Stenen står på krönet av åsen där fyra vägar möts", "så är stenen det första man möter", "Stenen kan tillskrivas Halvdan"):
    assert k in WK, k
SO_P = {"Sorunda sn", "Ösmo sn", "Västerhaninge sn", "Österhaninge sn", "Tyresö sn"}
assert all(recs[s]["place"] == "Blista" and recs[s]["object"] == "bergvägg" for s in ("Sö 219", "Sö 220", "Sö 221"))
assert "Hægviðr gærði stæin" in nz("Sö 219")
PRAY_ROCK = sorted(s for s, r in recs.items() if r["parish"] in SO_P and "hialpi" in r["normalization"] and r["object"] != "runsten")
assert PRAY_ROCK == ["Sö 221", "Sö 255"] and recs["Sö 255"]["place"] == "Vidby" and recs["Sö 255"]["parish"] == "Ösmo sn"
assert all(recs[s]["object"] == "bergvägg" for s in PRAY_ROCK) and "and" not in nz("Sö 221") and "and" not in nz("Sö 255")
BRO = sorted(s for s, r in recs.items() if r["parish"] in SO_P and re.search(r"\bbro\b", r["normalization"]))
assert BRO == ["Sö 252", "Sö Sb1965;19"]
assert recs["Sö 270"]["place"] == "Tyresta" and recs["Sö 270"]["object"] == "bergvägg"

title = "De gamla landen: Sotholm – det yttre landet på ön Tören"
summary = ("På vikingatiden var Södertörn en ö, Tören, och dess yttre halva var ett land för sig: gårdar i skogens gläntor, "
           "gravfält vid varje by, borgar på bergen och en tingsplats längst in i en havsvik. Följ med till Sotholms härad "
           "omkring år 1000. Första delen i serien De gamla landen.")

body = f"""Föreställ dig att du kommer till Tören från havet, för tusen år sedan. Det är ingen halvö ännu. Vattnet går runt hela landet, och sundet vid Tälje i väster är fortfarande öppet. Från båten ser du först berget: kala, rundslipade hällar som stiger ur vattnet, tallar som håller sig fast i skrevorna, och bakom dem skogen som reser sig mot Hanveden, öns höga mitt. Där inne ligger myrar och mörka skogssjöar mellan bergsryggarna, och det är långt mellan människorna. Ännu på medeltiden kallades den skogen ödslig.

Du har kommit till Yttre Tör, öns östra och södra halva, det land som senare ska heta Sotholms härad. Det ser kargt ut från vattnet. Men det bor fler människor här än man skulle tro.

## Gläntorna

Följ en av de långa sprickdalarna inåt land, och skogen öppnar sig. I dalbottnen ligger leran, och på leran ligger gårdarna, var och en i sin glänta, med namn som slutar på -sta och -by. I de mindre dalarna går boskapen på bete; där kommer ställena att heta -sätra och -boda. Arkeologen Roger Wikell räknar ett tjugotal sådana småbygder insprängda i Hanvedens skog, och han skriver att det för tusen år sedan levde ”tämligen mycket folk” i dem. I de två bygder han har studerat närmast tyder gravfälten på att marken togs upp plötsligt, kring 500–600.

Föreställ dig röken från husen, lukten av gödsel och hö, hundarna som skäller när någon kommer längs stigen. Husen själva har nästan aldrig hittats. De stod där de senare byarna kom att stå, och spåren försvann under dem. Men de döda ligger kvar. Över gårdarna, på backarna, ligger gravfälten, och nästan varje by har sitt. I Sorunda, Ösmo och grannsocknen Grödinge har mer än hälften av byarna två gravfält eller fler, och i Sorunda ligger i genomsnitt femtiofyra gravar vid varje by, i Ösmo sjuttiotre. Vid Kumla, på en udde i sjön Drevviken, ligger ett sjuttiotal högar, den största sexton meter bred, väl synliga för den som ror förbi. I en hög vid Vendelsö har man hittat klorna efter en björn – kanske en björnfäll som följde den döde på bålet.

Vem ägde jorden? Kaj Janzon och Sigurd Rahmqvist, som beskrev Tören i *Det medeltida Sverige*, läser gravfälten och de senare skattelängderna tillsammans och ser en bygd som odlades upp av bönder som ägde sin egen jord. Många gårdar, alltså, var och en med sina egna döda på backen ovanför.

## Silvret, järnet och vattnet

Vägarna går på grusåsarna, torra stråk genom sankmarken, och Drevviken binder ihop bygderna sommar som vinter: med båt när sjön är öppen, över isen när den har lagt sig. Det här är ingen fattig ö. Vid Norrby har ett svärd hamnat i den gyttjiga stranden, ett frankiskt svärd med smedens namn, Ingelri, inlagt i klingan. På samma gårds mark har någon grävt ner sitt silver: nästan tvåhundra mynt och myntbitar, tyska och engelska, präglade för kungar som Ethelred och Knut den store, och som det yngsta ett mynt av Hardeknut, slaget i Lund mellan 1035 och 1042. Det silvret har varit med om något på andra sidan Nordsjön.

Följ vägen söderut mot Sorunda, och landskapet blir större. Vid Torp, den gamla byn vid Sorunda kyrka, ligger en storhög, trettiofem–fyrtio meter bred och fem meter hög, och strax norr om den en skeppssättning av femtio resta stenar, tjugoåtta meter lång – ett stenskepp på land. Vid Söderbytorp, intill en hög från folkvandringstiden, har någon en gång lagt ner spadformiga järnämnen, ett städ och en yxa: en smeds förråd, kanske en offergåva. Och bygden når ut i havet. På Utö, Muskö och Torö, långt ute i skärgården, finns gravfält från samma tid som gläntornas.

## Borgarna på bergen

Gå upp på ett av bergen ovanför en by, och du kan stå i en borg: vallar av sten kring ett bergskrön, med branten som skydd där vallen inte behövs. Södermanland har fler sådana fornborgar än något annat landskap i Sverige, och en dryg fjärdedel av dem ligger på Tören – nittioen stycken. Sorunda ensamt har sexton.

De ligger där man behövde dem. Många står i själva bygden, på närmaste lämpliga berg ovanför en by. Andra ligger ensamma på små, undanskymda berg djupt inne i skogen, gärna vid en myr – platser att fly till. Längs kusten i Ösmo och Haninge ligger minst sex borgar så att de kan ha markerat leden genom skärgården, och där en dalgång går genom skogen från norra Sorunda mot Haningebygden ligger två borgar längs vägen. Hur många av dem som användes just på vikingatiden vet ingen. När *Det medeltida Sverige* skrevs hade ingen undersökt vad som finns innanför vallarna. Men de visar ett land där man höll utkik.

På ett röse från bronsåldern vid Fituna i Sorunda står en vårdkase, en hög av ved att tända när fienden kom. Den som står där är senare, men de som har beskrivit den menar att den säkert har haft äldre föregångare. Föreställ dig elden där en mörk höstkväll, och nästa eld som flammar upp på ett berg längre bort.

## Två bygder på en ö

Tören var delad i två bygder, som i de medeltida breven kallas Övre och Yttre Tör: Svartlösa härad i väster och norr, och Sotholms härad i öster och söder. Gränsen mellan dem behövde ingen människa dra. Den följde den höga, ödsliga Hanveden och dess utlöpare, gick genom Kaggfjärden i sydväst och genom Drevviken till Erstaviken i nordöst. Övre Tör hade Helgö, verkstad och handelsplats för trakterna kring hela Mälarviken. Yttre Tör vände sig utåt, mot havet.

Bygden hade sina centrum. Ett var Torp, med storhögen och stenskeppet. Ett annat, kanske yngre, kan ha varit Husby i Österhaninge, där ett stort gravfält användes länge och där grannbyn Hässlingby har två högar på omkring tjugofem meter. Vid medeltidens slut samlades häradet till ting på en hög holme längst in i Landfjärden, på Häringes mark, och det är den platsen, Sotholm, som har gett häradet dess namn. Där bekräftades köp och byten av jord inför bygdens män. Om tinget hölls på holmen redan på vikingatiden vet vi inte.

![Karta över Tören omkring år 1000 med gränsen mellan Övre och Yttre Tör och runstenarna]({MAP['sv']})
**Karta.** Tören omkring år 1000, då Södertörn var en ö. Den streckade linjen är gränsen mellan Övre Tör (Svartlösa härad) och Yttre Tör (Sotholms härad), ungefärlig, dragen efter sockenkyrkornas lägen. Rostfärgade punkter är de tre stenar på ön som ber för den dödes själ. Karta: Vitki, efter SGU:s modell för strandförskjutningen år 1000, Institutet för språk och folkminnens ortnamnsregister och Rundata.

Utanför kusten gick skeppen. När en dansk seglingsbeskrivning från medeltiden räknade upp lederna genom skärgården gick en av dem förbi Älvsnabben vid Muskö, där flottor ankrade, och på Utö bröts järnmalm från medeltiden.

## Stenarna vid vägen

Under 1000-talets första årtionden börjar man resa runstenar på Yttre Tör, fler än någon annanstans på ön. De flesta står nära gårdarna, ofta vid ett av gravfälten, och många vid vägarna. Vid Blista i Sorunda har tre familjer låtit hugga sina minnesord i samma bergvägg längs en väg, och ristaren Hägvid har satt sitt namn på en av dem. Längst i söder, vid Vansta i Ösmo, högg ristaren Amunde en av Ingvarsstenarna, efter Tosti som dog i Ingvars följe i öster.

Följ vägen från Haningebygden norrut, upp på åsen vid Söderby, och du möter en sten där fyra vägar korsar varandra. Den står på krönet, med en orm som slingrar sig runt kanten och ett kors överst, och den som kommer nerifrån bygden ser den först av allt. Runorna lyder:

> *{nz("Sö 269")}*

Anund (?) och … reste denna sten efter Viking, sin fader, Stores son.

![Runstenen Sö 269 med korset överst]({INFO[F269]['thumb']})
Sö 269 från Söderby malm. Korset sitter överst, texten ber inte. Foto: Kenny Lex. Fri från upphovsrätt, via [Wikimedia Commons]({PAGE}).

Så låter de flesta stenarna här. Någon har låtit resa en sten efter sin far eller sin son, ofta en skara bröder tillsammans efter sin far, och sedan tiger stenen. Vägarna nämns aldrig; bara två stenar talar om en bro. Ristarna var bygdens egna. Enligt Wikell kan Sö 269 tillskrivas ristaren Halvdan, vars namn står huggt i berget vid Tyresta:

> *{nz("Sö 270")}*

Farbjörn lät hugga stenen efter Håulv, sin son. Halvdan högg runorna.

Amunde, den andre stora ristaren här, skrev på samma sätt:

> *{nz("Sö 268")}*

Hjälmvid reste stenen efter Torgöt, sin son. Amunde ristade runorna.

## Korset utan bönen

En sak saknas nästan alltid. Korset sitter överst på mer än hälften av stenarna, lika ofta som i resten av Södermanland. Men bönen för den dödes själ, *Guð hialpi and hans*, ”Gud hjälpe hans själ”, står bara på en av fyrtiotre resta stenar. I resten av landskapet står den på ungefär var femte. Kaj Janzon och Sigurd Rahmqvist lade märke till det redan 2002; vi har räknat efter och sett att skillnaden är för stor för att vara en tillfällighet. Konstigt nog finns ett kortare ”Gud hjälpe” i berget på två ställen, vid Blista och vid Vidby i Ösmo. Orden var alltså kända här. På de resta stenarna, de som stod vid vägarna och gravfälten, kom de nästan aldrig med.

Var det ristarna? Varken Amunde eller Halvdan skrev någonsin en bön, inte ens på de stenar de högg utanför häradet. Men också på de stenar som andra händer högg här är bönen lika sällsynt. Bygden hade sina ristare, och ristarna hade bygdens sätt att minnas. Den enda resta stenen med en bön hittades så sent som 2011, vid Småhamra i Österhaninge, och ingen vet vem som högg den:

> *{nz(SMA)}*

Gunnar och Ulv och Sighjälm lät resa stenen efter Halvdan, sin fader. Gud hjälpe hans själ.

(Hur bönen senare tystnade också på andra håll har vi skrivit om i [Bönen tystnade – men korset stod kvar]({BON}).)

## Ett land för sig

Havet runt ön och skogen mitt i den drog gränserna. Innanför dem levde folket i Yttre Tör i sina gläntor, med gravfälten på backen, borgarna på bergen och båtarna i vikarna. De samlades till ting vid sin havsvik, höll utkik från sina berg och reste stenar vid sina vägar. När de minns sina döda skriver de namnen och huggar korset – och lämnar resten osagt. Den som står vid Sö 269 på åsen vid Söderby står mitt i det landet: där vägarna möts, med Hanvedens skog bakom sig och bygden nedanför.

## Så vet vi det

Landskapet, gravfälten, borgarna och tingsplatsen bygger på *Det medeltida Sverige* och Roger Wikells studie av bygderna kring Drevviken, fynden på deras uppgifter. En del av det vi berättar – tingsplatsen vid Sotholm, seglingsleden och gruvan på Utö – är känt först från medeltiden, och borgarna är inte daterade. Bönen har vi mätt: i en jämförelse av alla härader med minst femton runstenar var Sotholm ett av få som skilde sig tydligt från sitt landskap, och skillnaden står sig när stenarna delas i två grupper socken för socken, när bara stenar på sin ursprungliga plats räknas och när de största ristarnas stenar tas bort. Vi räknade bara resta stenar, inte ristningarna i berget, och om vanan satt i bygden eller hos ristarna kan vi inte avgöra. Planerna och beräkningarna finns öppna på GitHub, länkade nedan.

## Källor

- Janzon, Kaj & Rahmqvist, Sigurd 2002. *Det medeltida Sverige* 2. Södermanland 1. Tören: Svartlösa, Sotholm. Riksantikvarieämbetet.
- Wikell, Roger 2011. Att resa runsten eller inte – det är frågan. Tankar kring två vikingamiljöer i norra Haninge. *Situne Dei* 2011, s. 98–105. Sigtuna museum.
- Samnordisk runtextdatabas (Rundata), Institutionen för nordiska språk, Uppsala universitet. Open Database License.
- Institutet för språk och folkminnen, ortnamnsregistret (PlaceNameService), socknar och härader. CC BY.
- Den låsta analysplanen, stenarna och Vitkis beräkningar finns öppet på [GitHub](https://github.com/Precatio/runes) (analysplaner/2026-11-02-sotholm.md och 2026-11-02-gamla-granser-nya-monster.md).
- Sveriges geologiska undersökning (SGU), strandförskjutningsmodell för år 1000 (kartan).
- Bild: Wikimedia Commons, med fotografen i bildtexten."""

title_en = "The old lands: Sotholm – the outer land on the island of Tören"
summary_en = ("In the Viking Age Södertörn was an island, Tören, and its outer half was a land of its own: farms in forest "
              "clearings, a grave field by every village, hillforts on the heights and an assembly place at the head of a bay "
              "of the sea. Come along to the hundred of Sotholm around AD 1000. The first part of the series The old lands.")

body_en = f"""Imagine coming to Tören from the sea, a thousand years ago. It is not a peninsula yet. The water runs all the way round the land, and the strait at Tälje in the west is still open. From the boat you see the rock first: bare, ice-smoothed slabs rising out of the water, pines holding on in the cracks, and behind them the forest climbing towards Hanveden, the high middle of the island. In there lie bogs and dark forest lakes between the ridges, and people are few and far between. Even in the Middle Ages that forest was called desolate.

You have come to Outer Tör, the eastern and southern half of the island, the land that will later be called the hundred of Sotholm. From the water it looks barren. But more people live here than you would think.

## The clearings

Follow one of the long fissure valleys inland, and the forest opens. In the valley floor lies the clay, and on the clay lie the farms, each in its own clearing, with names ending in -sta and -by. In the smaller valleys the cattle graze; those places will be called -sätra and -boda. The archaeologist Roger Wikell counts some twenty such small settlements set into the forest of Hanveden, and he writes that a thousand years ago "quite a lot of people" lived in them. In the two settlements he has studied most closely, the grave fields suggest that the land was taken up suddenly, around 500–600.

Imagine the smoke from the houses, the smell of dung and hay, the dogs barking when someone comes along the path. The houses themselves have hardly ever been found. They stood where the later villages would stand, and their traces disappeared beneath them. But the dead remain. Above the farms, on the slopes, lie the grave fields, and nearly every village has one. In Sorunda, Ösmo and the neighbouring parish of Grödinge more than half the villages have two grave fields or more, and in Sorunda there are on average fifty-four graves by each village, in Ösmo seventy-three. At Kumla, on a point in Lake Drevviken, lie some seventy mounds, the largest sixteen metres across, plain to see for anyone rowing past. In a mound at Vendelsö the claws of a bear have been found – perhaps a bearskin that went with the dead on the pyre.

Who owned the land? Kaj Janzon and Sigurd Rahmqvist, who described Tören in *Det medeltida Sverige*, read the grave fields together with the later tax rolls and see a district cleared by farmers who owned their own land. Many farms, then, each with its own dead on the slope above.

## The silver, the iron and the water

The roads run along the gravel ridges, dry paths through the wetland, and Drevviken ties the settlements together summer and winter: by boat when the lake is open, across the ice when it has frozen. This is no poor island. At Norrby a sword has ended up in the muddy shore, a Frankish sword with the smith's name, Ingelri, inlaid in the blade. On the same farm's land someone has buried their silver: nearly two hundred coins and coin fragments, German and English, struck for kings such as Æthelred and Cnut the Great, and as the youngest a coin of Harthacnut, struck in Lund between 1035 and 1042. That silver has seen things on the other side of the North Sea.

Follow the road south towards Sorunda, and the landscape grows larger. At Torp, the old village by Sorunda church, lies a great mound, thirty-five to forty metres across and five metres high, and just north of it a ship setting of fifty standing stones, twenty-eight metres long – a stone ship on land. At Söderbytorp, beside a mound from the Migration Period, someone once laid down spade-shaped iron bars, an anvil and an axe: a smith's store, perhaps an offering. And the settlement reaches out into the sea. On Utö, Muskö and Torö, far out in the archipelago, there are grave fields from the same time as those of the clearings.

## The forts on the hills

Climb one of the hills above a village, and you may stand in a fort: banks of stone round a rocky crest, with the cliff as protection where no bank is needed. Södermanland has more of these hillforts than any other province in Sweden, and over a quarter of them lie on Tören – ninety-one. Sorunda alone has sixteen.

They lie where they were needed. Many stand in the settlement itself, on the nearest suitable hill above a village. Others lie alone on small, hidden hills deep in the forest, often by a bog – places to flee to. Along the coast in Ösmo and Haninge at least six forts lie so that they may have marked the route through the archipelago, and where a valley runs through the forest from northern Sorunda towards the Haninge countryside, two forts lie along the road. How many of them were in use in the Viking Age itself no one knows. When *Det medeltida Sverige* was written, no one had examined what lies inside the banks. But they show a land where people kept watch.

On a Bronze Age cairn at Fituna in Sorunda stands a beacon, a pile of wood to be lit when the enemy came. The one standing there is later, but those who have described it think it surely had older predecessors. Imagine the fire there on a dark autumn evening, and the next fire flaring up on a hill further off.

## Two districts on one island

Tören was divided into two districts, called Upper and Outer Tör in the medieval charters: the hundred of Svartlösa in the west and north, and the hundred of Sotholm in the east and south. No one needed to draw the border between them. It followed the high, desolate Hanveden and its spurs, ran through Kaggfjärden in the south-west and through Drevviken to Erstaviken in the north-east. Upper Tör had Helgö, a workshop and trading place for the lands around the whole bay of Lake Mälaren. Outer Tör faced outwards, towards the sea.

The district had its centres. One was Torp, with the great mound and the stone ship. Another, perhaps younger, may have been Husby in Österhaninge, where a large grave field was in use for a long time and the neighbouring village of Hässlingby has two mounds of about twenty-five metres. At the end of the Middle Ages the hundred gathered for its assembly on a high islet at the inner end of Landfjärden, on the land of Häringe, and it is that place, Sotholm, that gave the hundred its name. There purchases and exchanges of land were confirmed before the men of the district. Whether the assembly met on the islet already in the Viking Age we do not know.

![Map of Tören around AD 1000 with the border between Upper and Outer Tör and the runestones]({MAP['en']})
**Map.** Tören around AD 1000, when Södertörn was an island. The dashed line is the border between Upper Tör (the hundred of Svartlösa) and Outer Tör (the hundred of Sotholm), approximate, drawn after the parish churches. Rust-coloured points are the three stones on the island that pray for the dead person's soul. Map: Vitki, after the Geological Survey of Sweden's shore-displacement model for AD 1000, the place-name register of the Institute for Language and Folklore, and Rundata.

Off the coast the ships went by. When a medieval Danish sailing description listed the routes through the archipelago, one of them ran past Älvsnabben by Muskö, where fleets anchored, and on Utö iron ore was mined from the Middle Ages.

## The stones by the road

In the first decades of the eleventh century people in Outer Tör begin to raise runestones, more than anywhere else on the island. Most stand near the farms, often by one of the grave fields, and many by the roads. At Blista in Sorunda three families have had their words of remembrance cut into the same rock face along a road, and the carver Hägvid has signed one of them. Furthest south, at Vansta in Ösmo, the carver Amunde cut one of the Ingvar stones, in memory of Tosti who died in Ingvar's retinue in the east.

Follow the road north from the Haninge countryside, up onto the ridge at Söderby, and you meet a stone where four roads cross. It stands on the crest, with a serpent winding round its edge and a cross at the top, and whoever comes up from the settlement below sees it before anything else. The runes read:

> *{nz("Sö 269")}*

Anund (?) and … raised this stone in memory of Viking, their father, Store's son.

![The runestone Sö 269 with the cross at the top]({INFO[F269]['thumb']})
Sö 269 from Söderby malm. The cross sits at the top; the text does not pray. Photo: Kenny Lex. Public domain, via [Wikimedia Commons]({PAGE}).

That is how most of the stones here sound. Someone has had a stone raised for a father or a son, often a band of brothers together for their father, and then the stone falls silent. The roads are never mentioned; only two stones speak of a bridge. The carvers were the district's own. According to Wikell, Sö 269 can be attributed to the carver Halvdan, whose name is cut into the rock at Tyresta:

> *{nz("Sö 270")}*

Farbjörn had the stone cut in memory of Håulv, his son. Halvdan cut the runes.

Amunde, the other great carver here, wrote in the same way:

> *{nz("Sö 268")}*

Hjälmvid raised the stone in memory of Torgöt, his son. Amunde carved the runes.

## The cross without the prayer

One thing is almost always missing. The cross sits at the top of more than half the stones, as often as in the rest of Södermanland. But the prayer for the dead person's soul, *Guð hialpi and hans*, "may God help his soul", stands on only one of forty-three raised stones. In the rest of the province it stands on about one in five. Kaj Janzon and Sigurd Rahmqvist noticed it as early as 2002; we have counted again and seen that the difference is too large to be a coincidence. Strangely, a shorter "may God help" is cut into the rock in two places, at Blista and at Vidby in Ösmo. So the words were known here. On the raised stones, the ones that stood by the roads and the grave fields, they almost never came along.

Was it the carvers? Neither Amunde nor Halvdan ever wrote a prayer, not even on the stones they cut outside the hundred. But on the stones that other hands cut here, the prayer is just as rare. The district had its carvers, and the carvers had the district's way of remembering. The only raised stone with a prayer was found as late as 2011, at Småhamra in Österhaninge, and no one knows who carved it:

> *{nz(SMA)}*

Gunnar and Ulv and Sighjälm had the stone raised in memory of Halvdan, their father. May God help his soul.

## A land of its own

The sea around the island and the forest in its middle drew the borders. Inside them the people of Outer Tör lived in their clearings, with the grave fields on the slope, the forts on the hills and the boats in the bays. They gathered for their assembly by their bay of the sea, kept watch from their hills and raised stones by their roads. When they remember their dead they write the names and cut the cross – and leave the rest unsaid. Whoever stands by Sö 269 on the ridge at Söderby stands in the middle of that land: where the roads meet, with the forest of Hanveden behind and the settlement below.

## How we know

The landscape, the grave fields, the forts and the assembly place rest on *Det medeltida Sverige* and on Roger Wikell's study of the settlements around Lake Drevviken, the finds on their accounts. Some of what we tell – the assembly place at Sotholm, the sailing route and the mine on Utö – is known only from the Middle Ages, and the forts are undated. The prayer we have measured: in a comparison of every hundred with at least fifteen runestones, Sotholm was one of the few that differed clearly from its province, and the difference holds when the stones are split into two groups parish by parish, when only stones in their original place are counted, and when the stones of the main carvers are removed. We counted only raised stones, not the inscriptions in the rock, and whether the habit belonged to the district or to the carvers we cannot decide. The plans and calculations are open on GitHub, linked below.

## Sources

- Janzon, Kaj & Rahmqvist, Sigurd 2002. *Det medeltida Sverige* 2. Södermanland 1. Tören: Svartlösa, Sotholm. Swedish National Heritage Board. (Quotations translated by us.)
- Wikell, Roger 2011. Att resa runsten eller inte – det är frågan. Tankar kring två vikingamiljöer i norra Haninge. *Situne Dei* 2011, pp. 98–105. Sigtuna Museum. (Quotations translated by us.)
- Scandinavian Runic-text Data Base (Rundata), Department of Scandinavian Languages, Uppsala University. Open Database License.
- Institute for Language and Folklore, place-name register (PlaceNameService), parishes and hundreds. CC BY.
- The locked analysis plan, the stones and Vitki's calculations are open on [GitHub](https://github.com/Precatio/runes) (analysplaner/2026-11-02-sotholm.md and 2026-11-02-gamla-granser-nya-monster.md).
- Geological Survey of Sweden (SGU), shore-displacement model for AD 1000 (the map).
- Image: Wikimedia Commons, with the photographer in the caption."""

for b in (body, body_en):
    assert not re.search(r"^\|", b, re.M), "BlogBody har inga tabeller"
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M)), "varje ruta och diagram ska stängas"
    assert "/karta" not in b and "/statistik" not in b

out = {"slug": "de-gamla-landen-sotholm", "title": title, "summary": summary, "body": body,
       "title_en": title_en, "summary_en": summary_en, "body_en": body_en,
       "labels": ["Forskning", "Geografi", "Tro och magi", "Ristare", "Formler och syfte"]}
from src import blog_labels  # noqa: E402
assert blog_labels.check(out["labels"]) is None, blog_labels.check(out["labels"])
path = os.path.join(ROOT, "utdata", "blogg", "sotholm.json")
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
                 "topic": "Geografi|sotholm", "createdAt": now, "updatedAt": now})
        print("sparat som opublicerat utkast:", ref.id)
    blog._forget()
