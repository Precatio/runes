"""Artikeln "Korset utan bönen" (sv + en): i Sotholms härad på Södertörn har runstenarna kors som överallt men nästan
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

# ---- picture ----------------------------------------------------------------------------------------------------------
F269 = "Sö269.jpg"
INFO = commons.commons_info([F269])
assert INFO[F269]["licence"] == "Public domain"
PAGE = "https://commons.wikimedia.org/wiki/File:" + F269

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


title = "Korset utan bönen – i Sotholms härad bad runstenarna nästan aldrig för de döda"
summary = ("På Södertörn höggs kors på runstenarna som överallt annars, men bönen för den döda själen kom nästan aldrig "
           "med: en sten av 43 i Sotholms härad, mot en av fem i resten av Södermanland. Bygdens egna ristare skrev den "
           "aldrig. Den första artikeln i en serie om de gamla gränserna.")

body = f"""Mitt i Handen, söder om Stockholm, står en runsten som en gång stod ensam på en rullstensås där fyra vägar möttes. Den som kom upp från Haningebygden mötte den först. Ristningen är djupt huggen och stilren: en orm som slingrar sig runt stenen, och överst ett kors. Texten lyder:

> *{nz("Sö 269")}*

Anund (?) och … reste denna sten efter Viking, sin fader, Stores son.

Det är allt. Korset talar, men orden ber inte. Ingen *Guð hialpi and hans*, ”Gud hjälpe hans själ”, som så många andra stenar i Mälardalen slutar med. Det gäller inte bara den här stenen. Det gäller nästan alla stenar i Sotholms härad, den gamla bygd som omfattade bland annat Österhaninge, Västerhaninge, Sorunda, Ösmo och Tyresö.

![Runstenen Sö 269 med korset överst]({INFO[F269]['thumb']})
Sö 269 från Söderby malm, i dag i Handen. Korset sitter överst, texten ber inte. Foto: Kenny Lex. Fri från upphovsrätt, via [Wikimedia Commons]({PAGE}).

## Hur vi hittade det

Vi började inte med Sotholm. Vi började med en fråga om gränser. Dagens landskap fanns inte på vikingatiden; då levde man i härader, hundaren och folkland, och vi ville veta om de gamla bygderna skilde sig åt i hur de reste sina stenar. Därför lät vi datorn jämföra varje härad med minst femton runstenar med resten av sitt land, för 27 drag på stenarna: kors, böner, resor, ordval, stavning, vem som reste stenen. Det blev 731 jämförelser i 35 härader.

Med så många jämförelser dyker det upp skillnader av ren slump, och därför räknade vi om alla resultat med en korrektion för antalet prov. Bara sex skillnader klarade den och höll dessutom när vi delade stenarna i två grupper, socken för socken, och gjorde om provet i var och en – syns ett mönster i båda grupperna beror det inte på några enskilda socknar – och när vi tog bort häradets flitigaste ristare. Två av de sex handlade bara om bergarten. En av de andra var Sotholm.

I resten av Södermanland har ungefär en sten av fem en bön eller en kristen formel, {pc(T['share_out'])} procent. I Sotholms härad gäller det en sten av 43. Med tiden hållen konstant är oddsen för en bön ungefär en tolftedel av vad de är i resten av landskapet. Bland mönster minst så här starka i hela genomsökningen väntas högst omkring tre procent vara slumpfynd.

{chart('sv')}

Diagrammet visar också att Sotholm inte är ensamt om att be sällan. Svartlösa och Åker har också få böner, men där är stenarna färre och skillnaden inte säker. Sotholm är det härad där skillnaden är både stor och prövad.

## Korset stod där

Det första man undrar är om folket i Sotholm helt enkelt inte var kristna ännu. Men korset finns där. {K['k_in']} av de {K['n_in']} stenarna har ett kors, {pc(K['share_in'])} procent, mot {pc(K['share_out'])} procent i resten av Södermanland – ingen skillnad att tala om. Roger Wikell, som har studerat bygderna kring Drevviken, skriver att ”Runstenar är därför offensiva kristna markörer” och att den flitige ristaren Amundes stenar ”ofta [har] stora kors”. Han beskriver till och med en gård utan runstenar, Gudö, som ”en hednisk glänta i en skog av kristna runstenar”.

Stenarna i Sotholm bekände alltså färg, men på ett annat sätt än grannarna. Bilden predikade, orden bad inte.

Inte heller tiden förklarar det. Stenarna i Sotholm är lika gamla som de i resten av landskapet: av de daterade är hälften huggna före och hälften efter omkring år 1030, på båda hållen. Under årtiondena 1010–1040, då de flesta daterade stenarna i Sotholm höggs, har {PP['rest'][0]} av {PP['rest'][1]} stenar i resten av landskapet en bön, {pc(23 / 96)} procent – i Sotholm ingen av {PP['so'][1]}. (Hur bönen senare tystnade också på andra håll har vi skrivit om i [Bönen tystnade – men korset stod kvar]({BON}).)

Och det är inte hela Södertörn. Grannhäraderna Svartlösa och Öknebo har bön på {SV['k_in']} av {SV['n_in']} stenar, färre än landskapet i övrigt ({pc(SV['share_out'])} procent) men inte så få att det går att skilja från slumpen. Gränsen går vid Sotholm.

## Det var bygdens ristare

De flesta stenarna i Sotholm som har en känd ristare är gjorda av tre män: Amunde (elva stenar som tillskrivs honom), Halvdan (nio) och en ristare som Rundata kallar Björn (fem). Amunde och Halvdan signerade stenar här:

> *{nz("Sö 268")}*

Hjälmvid reste stenen efter Torgöt, sin son. Amunde ristade runorna.

> *{nz("Sö 270")}*

Farbjörn lät hugga stenen efter Håulv, sin son. Halvdan högg runorna.

Ingen av dem skrev någonsin en bön, inte heller på de stenar de högg utanför häradet: Halvdan noll av sjutton, Amunde noll av tretton. Här finns svagheten i fyndet, och vi säger den rakt ut. När vi lät varje ristare ha sin egen vana i modellen gick skillnaden inte längre att skilja från slumpen. Vi kan alltså inte säga om det var platsen eller ristarna. Men när vi tog bort alla stenar som Amunde, Halvdan och Björn gjort fanns bara en bön på de arton som blev kvar, mot {pc(E['share_out'])} procent i resten av landskapet, och den skillnaden håller. Fyndet håller också med bara stenar på sin ursprungliga plats, bara daterade stenar och utan stenar som gått förlorade.

Vår tolkning är att det inte går att skilja de två åt, och att det är själva poängen. Bygden hade sina ristare, och ristarna hade bygdens sätt att skriva. I Sotholm fanns en skrivtradition där stenen fick korset men inte bönen, och den höll i flera decennier.

## Undantaget som kom ur jorden

Den enda stenen med en bön i Sotholm hittades 2011, vid Småhamra i Österhaninge:

> *{nz(SMA)}*

Gunnar och Ulv och Sighjälm lät resa stenen efter Halvdan, sin fader. Gud hjälpe hans själ.

Ingen ristare är känd för den. Att undantaget dök upp så sent är en påminnelse om att bilden kan ändras, och det ger oss en förutsägelse att pröva: kommer det fram fler stenar i Sotholm, bör de som Amunde och Halvdan ristat sakna bön, medan stenar av andra händer kan ha den.

## Vad det säger om de gamla gränserna

Det här är den första artikeln i en serie om de gamla gränserna. I Uppland har vi sett att folklandens gränser skiljer runstenarnas sed åt mer än vilka grannbygder som helst gör. Sotholm visar samma sak i liten skala: ett härad var inte bara en rad i en medeltida skattelängd, utan en bygd där man gjorde på sitt eget sätt. På andra sidan häradsgränsen bad var femte sten för den döde. I Sotholm gjorde nästan ingen det.

Vi vet inte varför. Det kan ha varit ristarnas skola, där formeln aldrig lärdes ut. Det kan ha varit familjerna, som ville ha korset men inte bönen. Det kan ha varit en kyrka eller en missionär som undervisade annorlunda just här. Data kan inte avgöra det. Men den som står vid Sö 269 i Handen står vid en sten som valde bort bönen, och kan fundera på vad det betydde för dem som reste den.

:::box Det viktigaste i korthet
- Runstenarna i Sotholms härad på Södertörn bär kors lika ofta som andra sörmländska stenar, men nästan aldrig en bön för den döde.
- Det beror inte på att stenarna är äldre, och det gäller inte hela Södertörn – det är just Sotholm.
- Bygdens egna ristare skrev aldrig bönen, och vi kan inte skilja ristarnas vana från bygdens; troligen är det samma sak.
- Ett härad kunde ha sin egen skrivsed. De gamla bygderna syns i runstenarna, inte bara i de medeltida lagarna.
:::

## Källor

- Samnordisk runtextdatabas (Rundata), Institutionen för nordiska språk, Uppsala universitet. Open Database License.
- Institutet för språk och folkminnen, ortnamnsregistret (PlaceNameService), socknar och härader. CC BY.
- Wikell, Roger 2011. Att resa runsten eller inte – det är frågan. Tankar kring två vikingamiljöer i norra Haninge. *Situne Dei* 2011, s. 98–105. Sigtuna museum.
- Den låsta analysplanen, stenarna och Vitkis beräkningar finns öppet på [GitHub](https://github.com/Precatio/runes) (analysplaner/2026-11-02-sotholm.md och 2026-11-02-gamla-granser-nya-monster.md).
- Bild: Wikimedia Commons, med fotografen i bildtexten."""

title_en = "The cross without the prayer – in the hundred of Sotholm the runestones hardly ever prayed for the dead"
summary_en = ("On Södertörn, crosses were carved on the runestones as everywhere else, but the prayer for the dead "
              "person's soul almost never came with them: one stone of 43 in the hundred of Sotholm, against one in five in "
              "the rest of Södermanland. The district's own carvers never wrote it. The first article in a series on the "
              "old borders.")

body_en = f"""In the middle of Handen, south of Stockholm, stands a runestone that once stood alone on an esker where four roads met. Anyone coming up from the Haninge countryside met it first. The carving is deep and clean: a serpent winding round the stone, and at the top a cross. The text reads:

> *{nz("Sö 269")}*

Anund (?) and … raised this stone in memory of Viking, their father, Store's son.

That is all. The cross speaks, but the words do not pray. There is no *Guð hialpi and hans*, "may God help his soul", with which so many other stones in the Mälaren valley end. And it is not only this stone. It is almost every stone in the hundred of Sotholm, the old district that took in, among others, Österhaninge, Västerhaninge, Sorunda, Ösmo and Tyresö.

![The runestone Sö 269 with the cross at the top]({INFO[F269]['thumb']})
Sö 269 from Söderby malm, now in Handen. The cross sits at the top; the text does not pray. Photo: Kenny Lex. Public domain, via [Wikimedia Commons]({PAGE}).

## How we found it

We did not start with Sotholm. We started with a question about borders. Today's provinces did not exist in the Viking Age; people lived in hundreds and folklands, and we wanted to know whether the old districts differed in how they raised their stones. So we had the computer compare every hundred with at least fifteen runestones with the rest of its land, for 27 features of the stones: crosses, prayers, journeys, choice of words, spelling, who raised the stone. That came to 731 comparisons in 35 hundreds.

With that many comparisons, differences turn up by pure chance, so we recalculated every result with a correction for the number of tests. Only six differences survived it and also held when we split the stones into two groups, parish by parish, and repeated the test in each – a pattern that shows in both groups is not down to a few particular parishes – and when we removed the hundred's most prolific carver. Two of the six were only about the type of rock. One of the others was Sotholm.

In the rest of Södermanland about one stone in five carries a prayer or a Christian formula, {pc(T['share_out'])} percent. In the hundred of Sotholm it is one stone in 43. With time held constant, the odds of a prayer are about a twelfth of what they are in the rest of the province. Among patterns at least this strong in the whole scan, at most about three percent are expected to be chance findings.

{chart('en')}

The chart also shows that Sotholm is not alone in praying rarely. Svartlösa and Åker have few prayers too, but there the stones are fewer and the difference is not certain. Sotholm is the hundred where the difference is both large and tested.

## The cross was there

The first thing one wonders is whether the people of Sotholm simply were not Christian yet. But the cross is there. {K['k_in']} of the {K['n_in']} stones carry a cross, {pc(K['share_in'])} percent, against {pc(K['share_out'])} percent in the rest of Södermanland – no difference worth the name. Roger Wikell, who has studied the settlements around Lake Drevviken, writes that runestones were "offensive Christian markers" and that the prolific carver Amunde's stones "often [have] large crosses". He even describes a farm without runestones, Gudö, as "a heathen glade in a forest of Christian runestones".

So the stones in Sotholm declared their side, but in a different way from their neighbours. The image preached; the words did not pray.

Time does not explain it either. The stones in Sotholm are as old as those in the rest of the province: of the dated stones, half were carved before and half after about the year 1030, in both places. In the decades 1010–1040, when most of the dated stones in Sotholm were carved, {PP['rest'][0]} of {PP['rest'][1]} stones in the rest of the province have a prayer, {pc(23 / 96)} percent – in Sotholm none of {PP['so'][1]}.

Nor is it the whole of Södertörn. The neighbouring hundreds of Svartlösa and Öknebo have a prayer on {SV['k_in']} of {SV['n_in']} stones, fewer than the rest of the province ({pc(SV['share_out'])} percent) but not so few that it can be told apart from chance. The line runs at Sotholm.

## It was the district's carvers

Most of the stones in Sotholm with a known carver were made by three men: Amunde (eleven stones attributed to him), Halvdan (nine) and a carver whom Rundata calls Björn (five). Amunde and Halvdan signed stones here:

> *{nz("Sö 268")}*

Hjälmvid raised the stone in memory of Torgöt, his son. Amunde carved the runes.

> *{nz("Sö 270")}*

Farbjörn had the stone cut in memory of Håulv, his son. Halvdan cut the runes.

None of them ever wrote a prayer, not even on the stones they cut outside the hundred: Halvdan none of seventeen, Amunde none of thirteen. Here lies the weakness of the finding, and we state it plainly. When we let each carver have their own habit in the model, the difference could no longer be told apart from chance. So we cannot say whether it was the place or the carvers. But when we removed every stone made by Amunde, Halvdan and Björn, there was only one prayer on the eighteen that remained, against {pc(E['share_out'])} percent in the rest of the province, and that difference holds. The finding also holds with only stones in their original place, only dated stones, and without stones that have been lost.

Our reading is that the two cannot be told apart, and that this is the point. The district had its carvers, and the carvers had the district's way of writing. In Sotholm there was a writing tradition in which the stone got the cross but not the prayer, and it lasted for several decades.

## The exception that came out of the ground

The only stone with a prayer in Sotholm was found in 2011, at Småhamra in Österhaninge:

> *{nz(SMA)}*

Gunnar and Ulv and Sighjälm had the stone raised in memory of Halvdan, their father. May God help his soul.

No carver is known for it. That the exception turned up so late is a reminder that the picture can change, and it gives us a prediction to test: if more stones come to light in Sotholm, those carved by Amunde and Halvdan should lack the prayer, while stones by other hands may have it.

## What it says about the old borders

This is the first article in a series on the old borders. In Uppland we have seen that the borders of the folklands separate the customs of the runestones more than any neighbouring districts do. Sotholm shows the same thing on a small scale: a hundred was not just a line in a medieval tax roll, but a community that did things its own way. Across the boundary, one stone in five prayed for the dead. In Sotholm almost none did.

We do not know why. It may have been the carvers' school, where the formula was never taught. It may have been the families, who wanted the cross but not the prayer. It may have been a church or a missionary who taught differently just here. The data cannot decide. But whoever stands by Sö 269 in Handen stands by a stone that left out the prayer, and can wonder what that meant to those who raised it.

:::box The essentials in brief
- The runestones of the hundred of Sotholm on Södertörn carry crosses as often as other stones in Södermanland, but almost never a prayer for the dead.
- It is not because the stones are older, and it does not apply to all of Södertörn – it is Sotholm in particular.
- The district's own carvers never wrote the prayer, and we cannot separate the carvers' habit from the district's; most likely they are the same thing.
- A hundred could have its own way of writing. The old districts show in the runestones, not only in the medieval laws.
:::

## Sources

- Scandinavian Runic-text Data Base (Rundata), Department of Scandinavian Languages, Uppsala University. Open Database License.
- Institute for Language and Folklore, place-name register (PlaceNameService), parishes and hundreds. CC BY.
- Wikell, Roger 2011. Att resa runsten eller inte – det är frågan. Tankar kring två vikingamiljöer i norra Haninge. *Situne Dei* 2011, pp. 98–105. Sigtuna Museum. (Quotations translated by us.)
- The locked analysis plan, the stones and Vitki's calculations are open on [GitHub](https://github.com/Precatio/runes) (analysplaner/2026-11-02-sotholm.md and 2026-11-02-gamla-granser-nya-monster.md).
- Image: Wikimedia Commons, with the photographer in the caption."""

for b in (body, body_en):
    assert not re.search(r"^\|", b, re.M), "BlogBody har inga tabeller"
    assert b.count(":::chart") + b.count(":::box") == len(re.findall(r"^:::$", b, re.M)), "varje ruta och diagram ska stängas"
    assert "/karta" not in b and "/statistik" not in b

out = {"slug": "korset-utan-bonen-sotholm", "title": title, "summary": summary, "body": body,
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
