"""Artikeln "De gamla landen: Sotholm – runstenarna som inte bad" (sv + en): i Sotholms härad på Södertörn har runstenarna kors som överallt men nästan
aldrig en bön. Första fokusartikeln om de gamla gränserna (Viktor 2026-11-02). Siffrorna låses mot
utdata/gamla_granser/monster.json (häradsskannern, plan 054c87d5) och utdata/sotholm/sotholm.json (plan 9fa481d3).
    ../../../.venv/bin/python build_sotholm.py [--write | --update DOC]"""
import csv
import datetime as dt
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from src import commons  # noqa: E402

M = json.load(open(os.path.join(ROOT, "utdata", "gamla_granser", "monster.json"), encoding="utf-8"))
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

title = "De gamla landen: Sotholm – runstenarna som inte bad"
summary = ("På vikingatiden var Södertörn en ö som hette Tören, och dess yttre halva, Sotholms härad, reste fler runstenar "
           "än någon annan bygd på ön. Korsen höggs som överallt annars, men bönen för den döda själen kom nästan aldrig "
           "med: en sten av 43, mot en av fem i resten av Södermanland. Första delen i serien De gamla landen.")

body = f"""Föreställ dig att du kommer till Tören från havet, för tusen år sedan. Det är ingen halvö ännu. Vattnet går runt hela landet, och sundet vid Tälje i väster är fortfarande öppet. Från båten ser du först berget: kala, rundslipade hällar som stiger ur vattnet, tallar som håller sig fast i skrevorna, och bakom dem skogen som reser sig mot Hanveden, öns höga mitt. Där inne ligger myrar och mörka skogssjöar mellan bergsryggarna, och det är långt mellan människorna. Ännu på medeltiden kallades den skogen ödslig.

Men följ en av de långa sprickdalarna inåt land, och skogen öppnar sig. I dalbottnen ligger lera, och på leran ligger gårdarna, var och en i sin glänta, med namn som slutar på -sta och -by. I de mindre dalarna går boskapen på bete; där kommer ställena att heta -sätra och -boda. Föreställ dig röken från husen, lukten av gödsel och hö, hundarna som skäller när någon kommer längs stigen. Över gårdarna, på backarna, ligger gravfälten där de gamla vilar under runda kullar. Vid Kumla, på en udde i sjön Drevviken, ligger ett sjuttiotal högar, den största sexton meter bred, väl synliga för den som ror förbi. I en hög vid Vendelsö har man hittat klorna efter en björn – kanske en björnfäll som följde den döde på bålet.

Vägarna går på grusåsarna, torra stråk genom sankmarken, och Drevviken binder ihop bygderna sommar som vinter: med båt när sjön är öppen, över isen när den har lagt sig. Det här är ingen fattig ö. Vid Norrby har ett svärd hamnat i den gyttjiga stranden, ett frankiskt svärd med smedens namn, Ingelri, inlagt i klingan. På samma gårds mark har någon grävt ner sitt silver: nästan tvåhundra mynt och myntbitar, tyska och engelska, präglade för kungar som Ethelred och Knut den store, och som det yngsta ett mynt av Hardeknut, slaget i Lund mellan 1035 och 1042. Det silvret har varit med om något på andra sidan Nordsjön.

Följ vägen söderut mot Sorunda, och landskapet blir större. Vid byn Torp ligger en storhög, trettiofem–fyrtio meter bred och fem meter hög, och strax norr om den en skeppssättning av femtio resta stenar, tjugoåtta meter lång – ett stenskepp på land, riktat mot ingenting annat än sin egen tid. Vid Söderbytorp, intill en hög från folkvandringstiden, har någon en gång lagt ner spadformiga järnämnen, ett städ och en yxa: en smeds förråd, kanske en offergåva. Och på andra sidan Hanveden, i Övre Tör, ligger Helgö, verkstad och handelsplats för trakterna kring hela Mälarviken.

Och nu reser man stenar. Någonstans i bygden hörs järn mot sten. På krönet av en rullstensås, där fyra vägar möts, står en ny sten med en orm som slingrar sig runt kanten och ett kors överst. Den som kommer upp från bygden vid Haninge möter den först. Runorna lyder:

> *{nz("Sö 269")}*

Anund (?) och … reste denna sten efter Viking, sin fader, Stores son.

Det är allt. Korset talar, men orden ber inte. Ingen *Guð hialpi and hans*, ”Gud hjälpe hans själ”, som så många stenar runt Mälaren slutar med. Och så är det med nästan varje sten på den här sidan ön.

![Runstenen Sö 269 med korset överst]({INFO[F269]['thumb']})
Sö 269 från Söderby malm. Korset sitter överst, texten ber inte. Foto: Kenny Lex. Fri från upphovsrätt, via [Wikimedia Commons]({PAGE}).

## Två bygder på en ö

Tören var delad i två bygder, som i de medeltida breven kallas Övre och Yttre Tör: Svartlösa härad i väster och norr, och Sotholms härad i öster och söder. Gränsen mellan dem behövde ingen människa dra. Den följde den höga, ödsliga Hanveden och dess utlöpare, gick genom Kaggfjärden i sydväst och genom Drevviken till Erstaviken i nordöst. Yttre Tör vände sig utåt, mot havet. Vid medeltidens slut samlades häradet till ting på en hög holme längst in i Landfjärden, på Häringes mark, och det är den platsen, Sotholm, som har gett häradet dess namn. Om tinget hölls där redan på vikingatiden vet vi inte.

![Karta över Tören omkring år 1000 med gränsen mellan Övre och Yttre Tör och runstenarna]({MAP['sv']})
**Karta.** Tören omkring år 1000, då Södertörn var en ö. Den streckade linjen är gränsen mellan Övre Tör (Svartlösa härad) och Yttre Tör (Sotholms härad), ungefärlig, dragen efter sockenkyrkornas lägen. Rostfärgade punkter är de tre stenar på ön som ber för den dödes själ. Karta: Vitki, efter SGU:s modell för strandförskjutningen år 1000, Institutet för språk och folkminnens ortnamnsregister och Rundata.

Det var Yttre Tör som reste flest runstenar på ön: Sorunda ensamt har 21 ristningar, sju av dem huggna direkt i berghällen. Längst i söder, vid Vansta i Ösmo, högg ristaren Amunde en av Ingvarsstenarna, efter Tosti som dog i Ingvars följe i öster. Utanför kusten gick skeppen. När en dansk seglingsbeskrivning från medeltiden räknade upp lederna genom skärgården gick en av dem förbi Älvsnabben vid Muskö, där flottor ankrade, och på Utö bröts järnmalm från medeltiden. Det är folket här – Store och hans son Viking, Hjälmvid, Farbjörn, Hallsten – och deras stenar som resten av den här texten handlar om.

## Stenarna som inte bad

Gå runt bland stenarna på Yttre Tör, och mycket känns igen från resten av Mälardalen. Någon har låtit resa en sten efter sin far eller sin son, ristaren har huggit en orm runt kanten, och överst sitter ofta ett kors – på fler än hälften av stenarna, lika ofta som i resten av Södermanland. Folket här hade valt sida. Roger Wikell, som har studerat bygderna kring Drevviken, kallar runstenarna ”offensiva kristna markörer” och påpekar att Amundes stenar ”ofta [har] stora kors”. En gård utan stenar, Gudö, beskriver han som ”en hednisk glänta i en skog av kristna runstenar”.

Men läs orden. I resten av Södermanland slutar ungefär var femte sten med en bön: *Guð hialpi and hans*, Gud hjälpe hans själ. Här gör nästan ingen det. Av de fyrtiotre stenar i häradet som går att läsa ber en enda. Det är inte för att stenarna är äldre än grannarnas – de restes under samma årtionden. Under de år i början av 1000-talet då de flesta höggs bad ungefär var fjärde sten i resten av landskapet. Här ingen.

Bilden predikade. Orden bad inte. (Hur bönen senare tystnade också på andra håll har vi skrivit om i [Bönen tystnade – men korset stod kvar]({BON}).)

## Det har setts förut

Vi var inte först att lägga märke till det. När Kaj Janzon och Sigurd Rahmqvist beskrev Tören i *Det medeltida Sverige* 2002 skrev de att ”Södertörns runstenar har mycket stereotypa texter” och att ”en bön för själen finns bara i två fall”. Det vi har kunnat göra är att räkna efter och se att skillnaden är för stor för att vara en tillfällighet.

Och det gäller troligen hela ön. I Övre Tör, på andra sidan Hanveden, ber också nästan ingen sten: två av tjugotvå. Inte heller berömmer man de döda – ”en god bonde”, ”en dugande man” står på var femte sten i resten av Södermanland men på nästan ingen här. Törens stenar säger vem som reste stenen och efter vem, och sedan tiger de.

Ett litet ord skilde ändå öns två halvor åt. I Övre Tör skrev man ofta ordet för ’denna’ på ett eget sätt, *þennsa*, som man gjorde på andra håll söder om Mälaren. På Yttre Tör nästan aldrig.

## Bygdens ristare

De flesta stenarna här med en känd ristare är gjorda av tre män: Amunde, Halvdan och en ristare som brukar kallas Björn. Två av dem satte sina namn på stenarna:

> *{nz("Sö 268")}*

Hjälmvid reste stenen efter Torgöt, sin son. Amunde ristade runorna.

> *{nz("Sö 270")}*

Farbjörn lät hugga stenen efter Håulv, sin son. Halvdan högg runorna.

Ingen av dem skrev någonsin en bön, inte ens på de stenar de högg utanför häradet. Var det alltså ristarna och inte bygden? Svaret är inte så enkelt. Också bland de stenar som andra händer högg i Sotholm finns bara en enda bön. Bygden hade sina ristare, och ristarna hade bygdens sätt att skriva. Det går inte att skilja dem åt, och kanske är det samma sak: i Yttre Tör fick stenen korset men inte bönen, och så förblev det i flera decennier.

## Undantaget som kom ur jorden

Den enda stenen med en bön i Sotholm hittades 2011, vid Småhamra i Österhaninge:

> *{nz(SMA)}*

Gunnar och Ulv och Sighjälm lät resa stenen efter Halvdan, sin fader. Gud hjälpe hans själ.

Ingen vet vem som högg den. Att undantaget dök upp så sent är en påminnelse om att jorden fortfarande gömmer stenar, och att bilden kan ändras med nästa fynd.

## Ett land för sig

Havet runt ön och skogen mitt i den drog gränserna. Folket i Yttre Tör hade sina ristare och sitt eget sätt att minnas de döda: korset på stenen, namnen på dem som reste den och den dödes namn – men ingen bön. Vi vet inte varför. Det kan ha varit ristarnas skola, där formeln aldrig lärdes ut. Det kan ha varit familjerna, som ville ha korset men inte bönen. Det kan ha varit en präst eller en missionär som undervisade annorlunda just här. Men den som står vid Sö 269 står vid en sten som lät bönen vara, i en bygd som var ett land för sig.

## Så vet vi det

Bakom texten finns en jämförelse av alla härader med minst femton runstenar, där Sotholm var ett av få som skilde sig tydligt från sitt landskap. Skillnaden i böner står sig när stenarna delas i två grupper socken för socken, när bara stenar på sin ursprungliga plats räknas och när de största ristarnas stenar tas bort. Det vi inte kan avgöra är om vanan satt i bygden eller hos ristarna. Att den gällde hela Tören är troligt men inte säkert, eftersom stenarna i Övre Tör är för få. Planerna och beräkningarna finns öppna på GitHub, länkade nedan.

## Källor

- Janzon, Kaj & Rahmqvist, Sigurd 2002. *Det medeltida Sverige* 2. Södermanland 1. Tören: Svartlösa, Sotholm. Riksantikvarieämbetet.
- Wikell, Roger 2011. Att resa runsten eller inte – det är frågan. Tankar kring två vikingamiljöer i norra Haninge. *Situne Dei* 2011, s. 98–105. Sigtuna museum.
- Samnordisk runtextdatabas (Rundata), Institutionen för nordiska språk, Uppsala universitet. Open Database License.
- Institutet för språk och folkminnen, ortnamnsregistret (PlaceNameService), socknar och härader. CC BY.
- Den låsta analysplanen, stenarna och Vitkis beräkningar finns öppet på [GitHub](https://github.com/Precatio/runes) (analysplaner/2026-11-02-sotholm.md och 2026-11-02-gamla-granser-nya-monster.md).
- Sveriges geologiska undersökning (SGU), strandförskjutningsmodell för år 1000 (kartan).
- Bild: Wikimedia Commons, med fotografen i bildtexten."""

title_en = "The old lands: Sotholm – the runestones that did not pray"
summary_en = ("In the Viking Age Södertörn was an island called Tören, and its outer half, the hundred of Sotholm, raised more "
              "runestones than any other district on the island. Crosses were carved as everywhere else, but the prayer for "
              "the dead person's soul almost never came with them: one stone of 43, against one in five in the rest of "
              "Södermanland. The first part of the series The old lands.")

body_en = f"""Imagine coming to Tören from the sea, a thousand years ago. It is not a peninsula yet. The water runs all the way round the land, and the strait at Tälje in the west is still open. From the boat you see the rock first: bare, ice-smoothed slabs rising out of the water, pines holding on in the cracks, and behind them the forest climbing towards Hanveden, the high middle of the island. In there lie bogs and dark forest lakes between the ridges, and people are few and far between. Even in the Middle Ages that forest was called desolate.

But follow one of the long fissure valleys inland, and the forest opens. In the valley floor lies clay, and on the clay lie the farms, each in its own clearing, with names ending in -sta and -by. In the smaller valleys the cattle graze; those places will be called -sätra and -boda. Imagine the smoke from the houses, the smell of dung and hay, the dogs barking when someone comes along the path. Above the farms, on the slopes, lie the grave fields where the old ones rest under round mounds. At Kumla, on a point in Lake Drevviken, lie some seventy mounds, the largest sixteen metres across, plain to see for anyone rowing past. In a mound at Vendelsö the claws of a bear have been found – perhaps a bearskin that went with the dead on the pyre.

The roads run along the gravel ridges, dry paths through the wetland, and Drevviken ties the settlements together summer and winter: by boat when the lake is open, across the ice when it has frozen. This is no poor island. At Norrby a sword has ended up in the muddy shore, a Frankish sword with the smith's name, Ingelri, inlaid in the blade. On the same farm's land someone has buried their silver: nearly two hundred coins and coin fragments, German and English, struck for kings such as Æthelred and Cnut the Great, and as the youngest a coin of Harthacnut, struck in Lund between 1035 and 1042. That silver has seen things on the other side of the North Sea.

Follow the road south towards Sorunda, and the landscape grows larger. At the village of Torp lies a great mound, thirty-five to forty metres across and five metres high, and just north of it a ship setting of fifty standing stones, twenty-eight metres long – a stone ship on land, aimed at nothing but its own time. At Söderbytorp, beside a mound from the Migration Period, someone once laid down spade-shaped iron bars, an anvil and an axe: a smith's store, perhaps an offering. And on the other side of Hanveden, in Upper Tör, lies Helgö, a workshop and trading place for the lands around the whole bay of Lake Mälaren.

And now they are raising stones. Somewhere in the district iron rings against stone. On the crest of an esker, where four roads meet, stands a new stone with a serpent winding round its edge and a cross at the top. Anyone coming up from the Haninge countryside meets it first. The runes read:

> *{nz("Sö 269")}*

Anund (?) and … raised this stone in memory of Viking, their father, Store's son.

That is all. The cross speaks, but the words do not pray. There is no *Guð hialpi and hans*, "may God help his soul", with which so many stones around Lake Mälaren end. And so it is with almost every stone on this side of the island.

![The runestone Sö 269 with the cross at the top]({INFO[F269]['thumb']})
Sö 269 from Söderby malm. The cross sits at the top; the text does not pray. Photo: Kenny Lex. Public domain, via [Wikimedia Commons]({PAGE}).

## Two districts on one island

Tören was divided into two districts, called Upper and Outer Tör in the medieval charters: the hundred of Svartlösa in the west and north, and the hundred of Sotholm in the east and south. No one needed to draw the border between them. It followed the high, desolate Hanveden and its spurs, ran through Kaggfjärden in the south-west and through Drevviken to Erstaviken in the north-east. Outer Tör faced outwards, towards the sea. At the end of the Middle Ages the hundred gathered for its assembly on a high islet at the inner end of Landfjärden, on the land of Häringe, and it is that place, Sotholm, that gave the hundred its name. Whether the assembly met there already in the Viking Age we do not know.

![Map of Tören around AD 1000 with the border between Upper and Outer Tör and the runestones]({MAP['en']})
**Map.** Tören around AD 1000, when Södertörn was an island. The dashed line is the border between Upper Tör (the hundred of Svartlösa) and Outer Tör (the hundred of Sotholm), approximate, drawn after the parish churches. Rust-coloured points are the three stones on the island that pray for the dead person's soul. Map: Vitki, after the Geological Survey of Sweden's shore-displacement model for AD 1000, the place-name register of the Institute for Language and Folklore, and Rundata.

It was Outer Tör that raised the most runestones on the island: Sorunda alone has 21 inscriptions, seven of them cut straight into the bedrock. Furthest south, at Vansta in Ösmo, the carver Amunde cut one of the Ingvar stones, in memory of Tosti who died in Ingvar's retinue in the east. Off the coast the ships went by. When a medieval Danish sailing description listed the routes through the archipelago, one of them ran past Älvsnabben by Muskö, where fleets anchored, and on Utö iron ore was mined from the Middle Ages. It is the people here – Store and his son Viking, Hjälmvid, Farbjörn, Hallsten – and their stones that the rest of this text is about.

## The stones that did not pray

Walk among the stones of Outer Tör, and much is familiar from the rest of the Mälaren valley. Someone has had a stone raised for a father or a son, the carver has cut a serpent round the edge, and at the top there is often a cross – on more than half of the stones, as often as in the rest of Södermanland. The people here had chosen their side. Roger Wikell, who has studied the settlements around Lake Drevviken, calls the runestones "offensive Christian markers" and notes that Amunde's stones "often [have] large crosses". A farm without stones, Gudö, he describes as "a heathen glade in a forest of Christian runestones".

But read the words. In the rest of Södermanland about one stone in five ends with a prayer: *Guð hialpi and hans*, may God help his soul. Here almost none does. Of the forty-three stones in the hundred that can be read, a single one prays. It is not because the stones are older than their neighbours' – they were raised in the same decades. In the years early in the eleventh century when most of them were carved, about one stone in four in the rest of the province prayed. Here none.

The image preached. The words did not pray.

## It has been seen before

We were not the first to notice. When Kaj Janzon and Sigurd Rahmqvist described Tören in *Det medeltida Sverige* in 2002, they wrote that "the runestones of Södertörn have very stereotyped texts" and that "a prayer for the soul occurs in only two cases". What we have been able to do is count again and see that the difference is too large to be a coincidence.

And it probably holds for the whole island. In Upper Tör, on the other side of Hanveden, hardly any stone prays either: two of twenty-two. Nor do the stones praise the dead – "a good farmer", "a capable man" stands on one stone in five in the rest of Södermanland but on almost none here. The stones of Tören say who raised the stone and for whom, and then they fall silent.

One small word did set the island's two halves apart. In Upper Tör people often wrote the word for 'this' in a form of their own, *þennsa*, as they did elsewhere south of Lake Mälaren. In Outer Tör almost never.

## The district's carvers

Most of the stones here with a known carver were made by three men: Amunde, Halvdan and a carver usually called Björn. Two of them put their names on the stones:

> *{nz("Sö 268")}*

Hjälmvid raised the stone in memory of Torgöt, his son. Amunde carved the runes.

> *{nz("Sö 270")}*

Farbjörn had the stone cut in memory of Håulv, his son. Halvdan cut the runes.

None of them ever wrote a prayer, not even on the stones they cut outside the hundred. So was it the carvers and not the district? The answer is not so simple. Among the stones that other hands cut in Sotholm there is also only a single prayer. The district had its carvers, and the carvers had the district's way of writing. They cannot be told apart, and perhaps they are the same thing: in Outer Tör the stone got the cross but not the prayer, and so it stayed for several decades.

## The exception that came out of the ground

The only stone with a prayer in Sotholm was found in 2011, at Småhamra in Österhaninge:

> *{nz(SMA)}*

Gunnar and Ulv and Sighjälm had the stone raised in memory of Halvdan, their father. May God help his soul.

No one knows who carved it. That the exception turned up so late is a reminder that the ground still hides stones, and that the picture can change with the next find.

## A land of its own

The sea around the island and the forest in its middle drew the borders. The people of Outer Tör had their carvers and their own way of remembering the dead: the cross on the stone, the names of those who raised it and the name of the dead – but no prayer. We do not know why. It may have been the carvers' school, where the formula was never taught. It may have been the families, who wanted the cross but not the prayer. It may have been a priest or a missionary who taught differently just here. But whoever stands by Sö 269 stands by a stone that left the prayer out, in a district that was a land of its own.

## How we know

Behind the text lies a comparison of every hundred with at least fifteen runestones, in which Sotholm was one of the few that differed clearly from its province. The difference in prayers holds when the stones are split into two groups parish by parish, when only stones in their original place are counted, and when the stones of the main carvers are removed. What we cannot decide is whether the habit belonged to the district or to the carvers. That it held for the whole of Tören is likely but not certain, since the stones of Upper Tör are too few. The plans and calculations are open on GitHub, linked below.

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
